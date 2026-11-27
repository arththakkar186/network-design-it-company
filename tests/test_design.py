import copy
import re
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))

import render  # noqa: E402
import validate  # noqa: E402


class TestValidate(unittest.TestCase):
    def setUp(self):
        self.d = render.load()

    def test_design_is_valid(self):
        self.assertEqual(validate.validate(self.d), [])

    def test_detects_overlapping_subnet(self):
        d = copy.deepcopy(self.d)
        d["sites"]["hq"]["vlans"][1]["subnet"] = "10.10.10.0/25"   # inside MGMT
        self.assertTrue(any("overlaps" in e for e in validate.validate(d)))

    def test_detects_duplicate_ip(self):
        d = copy.deepcopy(self.d)
        d["sites"]["hq"]["access_switches"][1]["mgmt_ip"] = d["sites"]["hq"]["access_switches"][0]["mgmt_ip"]
        self.assertTrue(any("assigned twice" in e for e in validate.validate(d)))

    def test_detects_undefined_vlan_on_port(self):
        d = copy.deepcopy(self.d)
        d["sites"]["hq"]["access_switches"][0]["port_groups"][0]["vlan"] = 777
        self.assertTrue(any("777" in e for e in validate.validate(d)))

    def test_detects_unallocated_ports(self):
        d = copy.deepcopy(self.d)
        d["sites"]["hq"]["access_switches"][0]["port_groups"].pop()   # drop the unused range
        self.assertTrue(any("not allocated" in e for e in validate.validate(d)))

    def test_detects_single_homed_switch(self):
        d = copy.deepcopy(self.d)
        del d["sites"]["hq"]["access_switches"][0]["uplinks"]["CORE2"]
        self.assertTrue(any("dual-homed" in e for e in validate.validate(d)))

    def test_rejects_real_public_ip(self):
        d = copy.deepcopy(self.d)
        d["wan"]["hq_public"].update(ip="8.8.8.2", gateway="8.8.8.1")
        self.assertTrue(any("RFC 5737" in e for e in validate.validate(d)))


class TestRender(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.d = render.load()
        cls.cfg = render.render_all(cls.d)

    def test_every_device_rendered(self):
        names = {Path(k).stem for k in self.cfg}
        expected = {"R-EDGE", "CORE1", "CORE2", "R-BR", "SW-BR-01"} | {
            s["name"] for s in self.d["sites"]["hq"]["access_switches"]}
        self.assertEqual(names, expected)

    def test_render_is_deterministic(self):
        self.assertEqual(self.cfg, render.render_all(render.load()))

    def test_committed_configs_are_current(self):
        self.assertEqual(render.main(["--check"]), 0)

    def test_no_secrets_only_placeholders(self):
        for name, text in self.cfg.items():
            for line in text.splitlines():
                if re.search(r"\b(secret|key|password)\b", line) and "CHANGE_ME" not in line:
                    # allowed: lines that name a key without a value
                    self.assertRegex(line, r"(crypto key generate|keepalive|authentication pre-share|service password-encryption)",
                                     f"{name}: possible secret in '{line}'")

    def test_no_telnet(self):
        for name, text in self.cfg.items():
            self.assertNotIn("transport input telnet", text, name)
            self.assertIn("transport input ssh", text, name)

    def test_every_access_vlan_is_defined(self):
        for name, text in self.cfg.items():
            defined = set(re.findall(r"^vlan (\d+)$", text, re.M))
            if not defined:
                continue  # routers
            used = set(re.findall(r"switchport (?:access|voice) vlan (\d+)", text))
            self.assertLessEqual(used, defined, name)

    def test_hsrp_on_every_core_svi(self):
        for core in ("CORE1", "CORE2"):
            text = self.cfg[f"hq/{core}.cfg"]
            svis = re.findall(r"^interface Vlan(\d+)\n((?: .*\n)+)", text, re.M)
            routed = [(v, body) for v, body in svis if v != "1"]
            self.assertEqual(len(routed), len(self.d["sites"]["hq"]["vlans"]))
            for vid, body in routed:
                self.assertIn(f"standby {vid} ip", body, f"{core} Vlan{vid}")

    def test_hsrp_priorities_are_complementary(self):
        for v in self.d["sites"]["hq"]["vlans"]:
            p1 = re.search(rf"standby {v['id']} priority (\d+)", self.cfg["hq/CORE1.cfg"]).group(1)
            p2 = re.search(rf"standby {v['id']} priority (\d+)", self.cfg["hq/CORE2.cfg"]).group(1)
            self.assertNotEqual(p1, p2, f"VLAN {v['id']} has equal HSRP priority on both cores")

    def test_guest_and_lab_are_filtered(self):
        text = self.cfg["hq/CORE1.cfg"]
        for vid in (80, 90):
            body = re.search(rf"^interface Vlan{vid}\n((?: .*\n)+)", text, re.M).group(1)
            self.assertIn("ip access-group INTERNET-ONLY-IN in", body)

    def test_unused_ports_shut_in_blackhole(self):
        for name, text in self.cfg.items():
            for block in re.findall(r"description UNUSED.*?\n!", text, re.S):
                self.assertIn("switchport access vlan 999", block)
                self.assertIn("shutdown", block)


if __name__ == "__main__":
    unittest.main()
