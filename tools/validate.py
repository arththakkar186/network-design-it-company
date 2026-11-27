#!/usr/bin/env python3
"""Validate design/network.json before any config is rendered.

Checks addressing (overlaps, containment, gateway/host collisions), VLAN
consistency, switch port allocation and redundancy rules. Exit code 0 when
clean, 1 when any error is found. Standard library only.

    python3 tools/validate.py
"""
from __future__ import annotations

import ipaddress
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from render import load  # noqa: E402

PORT_RE = re.compile(r"^(FastEthernet|GigabitEthernet)(\d+/)(\d+)(?:-(\d+))?$")


def expand(rng: str) -> set[str]:
    m = PORT_RE.match(rng)
    if not m:
        raise ValueError(f"cannot parse port range {rng!r}")
    kind, slot, lo, hi = m.group(1), m.group(2), int(m.group(3)), int(m.group(4) or m.group(3))
    return {f"{kind}{slot}{n}" for n in range(lo, hi + 1)}


def validate(d: dict) -> list[str]:
    errors: list[str] = []
    seen_nets: list[tuple[str, ipaddress.IPv4Network]] = []

    def add_net(label: str, cidr: str, within: str | None = None):
        try:
            n = ipaddress.ip_network(cidr, strict=True)
        except ValueError as e:
            errors.append(f"{label}: {e}")
            return None
        if within and not n.subnet_of(ipaddress.ip_network(within)):
            errors.append(f"{label}: {cidr} is outside site supernet {within}")
        for other, on in seen_nets:
            if n.overlaps(on):
                errors.append(f"{label}: {cidr} overlaps {other} ({on})")
        seen_nets.append((label, n))
        return n

    used_ips: dict[str, str] = {}

    def claim(ip: str, owner: str):
        if ip in used_ips:
            errors.append(f"IP {ip} assigned twice: {used_ips[ip]} and {owner}")
        used_ips[ip] = owner

    # ---------------------------------------------------------------- HQ
    hq = d["sites"]["hq"]
    ids, names = set(), set()
    vlan_nets: dict[int, ipaddress.IPv4Network] = {}
    for v in hq["vlans"]:
        if v["id"] in ids:
            errors.append(f"HQ VLAN id {v['id']} duplicated")
        if v["name"] in names:
            errors.append(f"HQ VLAN name {v['name']} duplicated")
        if not 2 <= v["id"] <= 1001:
            errors.append(f"HQ VLAN {v['id']} outside normal range 2-1001")
        ids.add(v["id"]); names.add(v["name"])
        n = add_net(f"HQ VLAN {v['id']} {v['name']}", v["subnet"], hq["supernet"])
        if n:
            vlan_nets[v["id"]] = n
            if n.num_addresses < 8:
                errors.append(f"HQ VLAN {v['id']}: /{n.prefixlen} too small for HSRP (.1 VIP, .2, .3)")
            for i, who in ((1, "HSRP VIP"), (2, "CORE1"), (3, "CORE2")):
                claim(str(n.network_address + i), f"VLAN {v['id']} {who}")
        if v.get("hsrp_active") not in ("CORE1", "CORE2"):
            errors.append(f"HQ VLAN {v['id']}: hsrp_active must be CORE1 or CORE2")
    actives = {v["hsrp_active"] for v in hq["vlans"]}
    if actives != {"CORE1", "CORE2"}:
        errors.append("HSRP active roles are not shared across both cores (no load sharing)")
    if hq["blackhole_vlan"]["id"] in ids:
        errors.append("Blackhole VLAN must not be a routed VLAN")
    for name in hq["acl_policy"]:
        if name not in names:
            errors.append(f"acl_policy refers to unknown VLAN {name}")

    for link in hq["routed_links"]:
        n = add_net(f"routed link {link['name']}", link["subnet"], hq["supernet"])
        for end in ("a", "b"):
            ip = ipaddress.ip_address(link[end]["ip"])
            if n and ip not in n:
                errors.append(f"{link['name']}: {ip} not in {n}")
            claim(str(ip), f"{link[end]['device']} {link[end]['intf']}")
    for dev, ip in hq["loopbacks"].items():
        add_net(f"loopback {dev}", f"{ip}/32", hq["supernet"])
        claim(ip, f"{dev} Loopback0")

    mgmt = next(v for v in hq["vlans"] if v["name"] == "MGMT")
    mgmt_net = ipaddress.ip_network(mgmt["subnet"])
    for sw in hq["access_switches"]:
        ip = ipaddress.ip_address(sw["mgmt_ip"])
        if ip not in mgmt_net:
            errors.append(f"{sw['name']}: management IP {ip} not in MGMT {mgmt_net}")
        claim(str(ip), f"{sw['name']} Vlan10")
        ports: set[str] = set()
        for g in sw["port_groups"]:
            try:
                p = expand(g["range"])
            except ValueError as e:
                errors.append(f"{sw['name']}: {e}")
                continue
            clash = ports & p
            if clash:
                errors.append(f"{sw['name']}: ports assigned twice: {sorted(clash)}")
            ports |= p
            for key in ("vlan", "voice"):
                if key in g and g[key] not in ids:
                    errors.append(f"{sw['name']} {g['range']}: {key} VLAN {g[key]} is not defined")
            for vid in g.get("vlans", []):
                if vid not in ids:
                    errors.append(f"{sw['name']} {g['range']}: trunk VLAN {vid} is not defined")
        expected = expand("FastEthernet0/1-24")
        if ports != expected:
            missing = sorted(expected - ports, key=lambda s: int(s.split("/")[-1]))
            extra = sorted(ports - expected)
            if missing:
                errors.append(f"{sw['name']}: ports not allocated (allocate or mark unused): {missing}")
            if extra:
                errors.append(f"{sw['name']}: ports that do not exist on a 24-port 2960: {extra}")
        if set(sw["uplinks"]) != {"CORE1", "CORE2"}:
            errors.append(f"{sw['name']}: must be dual-homed to CORE1 and CORE2")
    core_ports: dict[tuple[str, str], str] = {}
    for sw in hq["access_switches"]:
        for core, port in sw["core_ports"].items():
            key = (core, port)
            if key in core_ports:
                errors.append(f"{core} {port} used by {core_ports[key]} and {sw['name']}")
            core_ports[key] = sw["name"]

    for s in hq["servers"]:
        ip = ipaddress.ip_address(s["ip"])
        if not any(ip in n for n in vlan_nets.values()):
            errors.append(f"server {s['name']} {ip} is not inside any HQ VLAN")
        claim(str(ip), f"server {s['name']}")

    for key, val in d["services"].items():
        for ip in (val if isinstance(val, list) else [val]):
            if not any(s["ip"] == ip for s in hq["servers"]):
                errors.append(f"service {key} points at {ip}, which is not a defined server")

    # ---------------------------------------------------------------- branch
    br = d["sites"]["branch"]
    for v in br["vlans"]:
        n = add_net(f"branch VLAN {v['id']} {v['name']}", v["subnet"], br["supernet"])
        if n:
            claim(str(n.network_address + 1), f"R-BR .{v['id']}")
    add_net("loopback R-BR", f"{br['router']['loopback']}/32", br["supernet"])
    sw = br["switch"]
    ports = set()
    for g in sw["port_groups"]:
        p = expand(g["range"])
        if ports & p:
            errors.append(f"{sw['name']}: ports assigned twice")
        ports |= p
    if ports != expand("FastEthernet0/1-24"):
        errors.append(f"{sw['name']}: not all 24 access ports are allocated")

    if ipaddress.ip_network(hq["supernet"]).overlaps(ipaddress.ip_network(br["supernet"])):
        errors.append("HQ and branch supernets overlap; the VPN cannot route between them")

    # ---------------------------------------------------------------- WAN
    t = d["wan"]["tunnel"]
    tn = add_net("tunnel", t["subnet"])
    for k in ("hq_ip", "branch_ip"):
        if tn and ipaddress.ip_address(t[k]) not in tn:
            errors.append(f"tunnel {k} {t[k]} not in {tn}")
    for side in ("hq_public", "branch_public"):
        p = d["wan"][side]
        iface = ipaddress.ip_interface(f"{p['ip']}/{p['prefix']}")
        if ipaddress.ip_address(p["gateway"]) not in iface.network:
            errors.append(f"{side}: gateway {p['gateway']} not in {iface.network}")
        doc = [ipaddress.ip_network(x) for x in ("192.0.2.0/24", "198.51.100.0/24", "203.0.113.0/24")]
        if not any(iface.ip in n for n in doc):
            errors.append(f"{side}: {iface.ip} is not an RFC 5737 documentation address (keep the repo free of real IPs)")
    return errors


def main() -> int:
    errors = validate(load())
    if errors:
        print(f"{len(errors)} problem(s) in design/network.json:")
        for e in errors:
            print(f"  - {e}")
        return 1
    print("design/network.json is valid")
    return 0


if __name__ == "__main__":
    sys.exit(main())
