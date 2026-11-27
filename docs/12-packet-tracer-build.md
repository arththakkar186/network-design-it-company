# 12 · Packet Tracer Build Guide

How to rebuild and test the design in Cisco Packet Tracer 8.x.

## 1. Place devices

| Device | PT model | Notes |
|---|---|---|
| ISP | 2911 router (acts as both ISPs) | G0/0 203.0.113.1/30, G0/1 198.51.100.1/30, Loopback 8.8.8.8/32 to simulate the internet |
| R-EDGE, R-BR | ISR4331, ISR4321 | Turn on the `securityk9` licence: `license boot level securityk9` then reload |
| CORE1, CORE2 | 3650-24PS | Add the AC power supply module in the Physical tab |
| Access | 2960-24TT ×5 | |
| Hub | Hub-PT | Connect to ACC-F3-01 Fa0/19, plus 3 lab PCs |
| WLC | WLC-2504 | |
| APs | LAP-PT ×2 (enough to test) | Powered from a PoE injector or Power Adapter |
| Servers | Server-PT ×4 | DC01 (DHCP + DNS), FS01, MAIL01 (EMAIL), MON01 (Syslog + NTP) |
| Clients | PC-PT, Laptop-PT, IP Phone 7960, Smartphone | |

## 2. Cable

Follow the port maps in [03-physical-design.md](03-physical-design.md). Use straight-through copper for
switch-to-host and router-to-switch links, and crossover for hub-to-switch (or let PT auto-detect).

## 3. Load configs

Open each device's CLI and paste its file from `configs/`. Packet Tracer does not support some commands. They are
rejected harmlessly, but note the substitutes:

| Not in Packet Tracer | Substitute for the lab |
|---|---|
| `algorithm-type scrypt` | `enable secret <pw>` / `username netadmin secret <pw>` |
| `radius server` block / AAA RADIUS group | `aaa authentication login default local` |
| `login block-for` | Supported on routers, ignored on some switches |
| `ip arp inspection` (2960 in PT) | Partially supported; test T-18 is verified on a real IOS image |
| `zone security` (ZBF) | Supported on ISR4331 with securityk9 in PT 8.x |
| `snmp-server ... v3` | Use `snmp-server community` only in the lab, never in production |
| `standby version 2` | Supported |

## 4. Configure server services

- **DC01 DHCP**: one pool per VLAN. Example for Sales: pool `SALES`, gateway 10.10.30.1, DNS 10.10.50.10, start 10.10.30.21, mask 255.255.255.0.
  Guest pool DNS: 8.8.8.8 (the ISP loopback).
- **DC01 DNS**: A records `fs01`, `web01`, `mail01` under `corp.northbridge.example`.
- **MAIL01**: EMAIL service, domain `corp.northbridge.example`, users `alice` and `bob`. Configure the PC email clients to test SMTP/POP3 inside the LAN.
- **MON01**: turn on Syslog and NTP.

## 5. Wireless

On the WLC, create WLANs `NB-CORP` (VLAN 70, WPA2-Enterprise to RADIUS 10.10.50.12, or WPA2-PSK in PT if the RADIUS server is not built) and `NB-GUEST` (VLAN 80).
Configure the DHCP pool for VLAN 10 with **option 43 / WLC address 10.10.10.20** so LAPs join.

## 6. Run the tests

Work through [07-test-plan.md](07-test-plan.md). In simulation mode, filter on ICMP, DHCP, OSPF and HSRP to watch:

- DHCP DORA being relayed by the core SVI,
- an HSRP state change when you power off CORE2,
- every frame flooded to all lab PCs at the hub, compared with unicast-only delivery on switch ports.

The last one is the clearest demonstration of [09-hubs-vs-switches.md](09-hubs-vs-switches.md).
