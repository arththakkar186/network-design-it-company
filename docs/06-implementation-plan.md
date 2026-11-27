# 06 · Implementation Plan

## Phases

| Phase | Work | Exit criteria |
|---|---|---|
| 0. Prepare | Order hardware ([BOM](08-bill-of-materials.md)), confirm ISP handoff, label cabling, build the IP plan in IPAM | Hardware received, cabling certified (Fluke report), design signed off |
| 1. Stage | Bench-build every device in the IT room from `configs/`, replacing `CHANGE_ME` from the password vault, and generate SSH keys | All devices reachable by SSH on a bench management network |
| 2. Core and edge | Rack R-EDGE, CORE1, CORE2; bring up OSPF and Po1; ISP internet working | Tests T-01 to T-08 pass |
| 3. Servers | Connect ACC-DC-01, build DC01/DC02 (AD, DNS, DHCP scopes), NPS01, MON01 | DHCP leases on a test VLAN, syslog/NTP working |
| 4. Floors | Install one floor per evening: access switch, patching, APs | Floor tests T-09 to T-20 pass |
| 5. Wireless and voice | WLC01, SSIDs, NPS policies, phones | Tests T-21 to T-25 pass |
| 6. Branch | Ship pre-staged R-BR and SW-BR-01; local technician cables them; bring up the VPN | Tests T-26 to T-30 pass |
| 7. Hand over | Final test run, config backup, documentation, runbook walk-through | Sign-off |

## Build order and why

1. **Edge before core**: the cores need the OSPF default route from R-EDGE before users can reach anything.
2. **Core before access**: STP roots and HSRP must exist before access switches connect. Otherwise
   an access switch with a lower bridge ID could briefly become root.
3. **Servers before users**: users arriving before DHCP works would get APIPA (169.254.x.x) addresses.
4. **One floor at a time**: it limits the blast radius and leaves time to fix issues before the next floor.

## Applying a config

```text
1. Console in (9600 8N1) and wipe:      write erase / delete flash:vlan.dat / reload
2. Paste the rendered config from configs/<site>/<device>.cfg
3. Set real secrets (from the vault, never the repo):
       enable algorithm-type scrypt secret <vault>
       username netadmin privilege 15 algorithm-type scrypt secret <vault>
       radius server NPS01 / key <vault>
       crypto isakmp key <vault> address <peer>
       snmp-server user nms NETOPS v3 auth sha <vault> priv aes 128 <vault>
4. crypto key generate rsa modulus 2048
5. copy running-config startup-config
6. Run the device's tests from 07-test-plan.md
```

## Cutover (moving from the old flat network)

- Cutover window: Friday 18:00 to Saturday 12:00.
- The old flat `192.168.1.0/24` network stays up on its own switch until the cutover is signed off.
- DHCP scopes use short leases (4 h) for the first week so changes spread quickly; later they move to 8 days.
- Printers and other static devices get reservations in their new VLANs before the cutover.

## Rollback

| If | Then |
|---|---|
| Core or OSPF problems in phase 2 | Re-patch the ISP handoff to the old router (labelled spare cable), which restores internet in under 5 minutes |
| A floor fails testing | Re-patch that floor's desks to the old flat switch and keep the other floors on the new network |
| VPN does not come up | The branch keeps working with local internet and SaaS; fix it remotely using the out-of-band LTE modem on R-BR's console |

## Change control after go-live

All changes go through `design/network.json`: edit, run `tools/validate.py`, run `tools/render.py`, review the diff
of the generated configs in a pull request, run the tests in CI, then apply the reviewed config lines in a change window.
The repository stays the single record of the intended state.
