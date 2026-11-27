# 10 · Operations Runbook

## Daily and weekly checks

| When | Check | How |
|---|---|---|
| Daily | Syslog for `%HSRP-5-STATECHANGE`, `%LINEPROTO-5-UPDOWN` on uplinks, `%PM-4-ERR_DISABLE`, `%PORT_SECURITY`, `%SW_DAI` | MON01 saved search |
| Daily | VPN up | MON01 alerts if the SNMP tunnel interface status goes down |
| Weekly | Config backup | `archive` / scheduled `copy run tftp:` to MON01; compare with the generated configs in this repo |
| Weekly | Err-disabled ports | `show interfaces status err-disabled` on access switches |
| Monthly | Rotate the guest PSK | WLC → WLANs → NB-GUEST |
| Monthly | DHCP scope use | Alert above 80% for any scope |
| Quarterly | Failover tests T-32 to T-36 | In a change window |
| Quarterly | Review and remove stale sticky MACs | `clear port-security sticky` on vacated desks |

## Common tasks

**Add a new desk on floor 2**
1. Patch the wall jack to the next free port on ACC-F2-01.
2. If the port is in the unused range, move it into the Engineering group in `design/network.json`, then run validate and render, and get the diff reviewed.
3. Apply the interface lines and `no shutdown`.

**Move a user to another department**: change the port's access VLAN (one port only), then `clear port-security sticky interface <if>`.

**Add a new VLAN**: add it to `design/network.json` (id, name, subnet, HSRP active core), then run validate (checks for overlaps) and render. The VLAN, SVI, HSRP, OSPF network and trunk allowed lists are updated on every device automatically. Add a DHCP scope on DC01.

## Troubleshooting

| Symptom | Likely cause | Check | Fix |
|---|---|---|---|
| PC has a 169.254.x.x address | DHCP not reaching the server | `show ip dhcp snooping binding`, `show run int vlan X` for the helper | Check the helper, snooping trust on uplinks, scope exhausted? |
| PC gets an IP but no internet | Gateway or ACL | `ping` the VIP, `show standby brief`, `show access-lists` | |
| Port down, LED amber | err-disabled | `show interfaces status err-disabled` | Find the cause (BPDU guard / port security), remove it, `shutdown` / `no shutdown` |
| Slow lab PCs | Hub collisions / duplex | `show interfaces fa0/19` for collisions, late collisions | Confirm half duplex on both ends |
| Branch cannot reach HQ | VPN | `show crypto isakmp sa`, `show ip ospf neighbor` on R-BR | Check the ISP, the PSK, ACL-VPN-PEER and ZBF self-zone drops |
| Traffic going across Po1 unexpectedly | STP root and HSRP active not aligned | `show spanning-tree root` vs `show standby brief` | Re-render from the design and reapply STP priorities |
| Phones in the data VLAN | CDP not reaching the phone | `show cdp neighbors`, `show run int` | Make sure the voice VLAN is set; check phone firmware |

## Escalation

| Level | Who | When |
|---|---|---|
| 1 | Service desk | User issues, port moves |
| 2 | IT-OPS network admin | Err-disable, VLAN, DHCP, Wi-Fi |
| 3 | Network engineer / vendor TAC | Core, OSPF, VPN, hardware failure |
| ISP | Circuit provider | Demarcation point down |

## Backup and recovery

- Running configs are backed up nightly to MON01 and kept for 90 days.
- The generated configs in this repo are the **intended** state. A nightly comparison flags drift.
- A replacement device is configured from `configs/<device>.cfg` plus secrets from the vault, as in the implementation plan.
