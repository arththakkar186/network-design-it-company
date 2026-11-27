# 07 · Test Plan

Each test has an ID, the command to run, and the expected result. Results are recorded in the table at
the end of each phase. The design was tested in Cisco Packet Tracer. Where a command is not supported
in Packet Tracer, that is noted.

## Edge and core (phase 2)

| ID | Test | Command (device) | Expected |
|---|---|---|---|
| T-01 | Internet reachability | `ping 203.0.113.1` (R-EDGE) | 5/5 success |
| T-02 | OSPF adjacencies | `show ip ospf neighbor` (R-EDGE) | CORE1 and CORE2 in FULL state; after phase 6 also R-BR over Tunnel0 |
| T-03 | Default route learned | `show ip route 0.0.0.0` (CORE1) | `O*E2 0.0.0.0/0 via 10.10.255.1` |
| T-04 | Core interlink | `show etherchannel summary` (CORE1) | `Po1(SU)` with Gi1/0/23 and Gi1/0/24 flagged `(P)` |
| T-05 | HSRP roles | `show standby brief` (CORE1) | Active for 10,20,40,60,80; Standby for 25,30,50,70,90 |
| T-06 | HSRP roles | `show standby brief` (CORE2) | Mirror of T-05 |
| T-07 | STP root alignment | `show spanning-tree root` (CORE1) | CORE1 is root for 10,20,40,60,80 |
| T-08 | ECMP into LAN | `show ip route 10.10.30.0` (R-EDGE) | Two equal-cost paths via 10.10.255.2 and 10.10.255.6 |

## Access layer (phase 4, per floor)

| ID | Test | Command | Expected |
|---|---|---|---|
| T-09 | Trunks | `show interfaces trunk` (ACC-F1-01) | Gi0/1 and Gi0/2 trunking, native 999, allowed list as designed |
| T-10 | Blocked uplink | `show spanning-tree vlan 30` (ACC-F1-01) | Gi0/2 (to CORE2) Root port/FWD; Gi0/1 Alternate/BLK |
| T-11 | VLAN assignment | `show vlan brief` | Ports in the correct VLANs; unused ports in 999 |
| T-12 | DHCP lease | PC on Fa0/12 → `ipconfig /renew` | 10.10.30.21+ address, gateway 10.10.30.1, DNS 10.10.50.10/11 |
| T-13 | Inter-VLAN routing | Sales PC `ping 10.10.50.20` | Success |
| T-14 | Default gateway VIP | Sales PC `arp -a` | 10.10.30.1 → `0000.0c9f.f01e` (HSRPv2 virtual MAC for group 30) |
| T-15 | Unused port shut | `show interfaces status` | Fa0/23-24 `disabled` |
| T-16 | Port security | Connect a 4th MAC behind a desk port | `show port-security interface Fa0/1` → violation count increments; traffic from the extra MAC dropped |
| T-17 | BPDU guard | Connect a switch to a desk port | Port `err-disabled (bpduguard)`, recovers after 300 s once removed |
| T-18 | DHCP snooping | Rogue DHCP server on a desk port | Clients still get leases from DC01; `show ip dhcp snooping statistics` shows drops (not supported in Packet Tracer; verified with an IOS lab image) |
| T-19 | Hub segment | Lab PC → `ipconfig /renew`, `ping 8.8.8.8` | 10.10.90.x lease; internet works |
| T-20 | Hub isolation | Lab PC → `ping 10.10.50.20` | Fails; `show access-lists INTERNET-ONLY-IN` hit count increases |

## Wireless and voice (phase 5)

| ID | Test | Expected |
|---|---|---|
| T-21 | APs joined | WLC GUI → Wireless → All APs shows 6 APs registered |
| T-22 | CORP auth | Domain laptop joins NB-CORP with AD credentials → address in 10.10.70.0/23 |
| T-23 | CORP denied for non-members | Account not in "Wi-Fi Users" → NPS event 6273 (denied) |
| T-24 | Guest isolation | Guest device gets 10.10.80.x; cannot ping 10.10.50.10 or another guest client |
| T-25 | Voice VLAN | Phone gets 10.10.60.x; `show cdp neighbors` lists the phone; `show mls qos interface Fa0/1` shows trust cos |

## Branch and VPN (phase 6)

| ID | Test | Command | Expected |
|---|---|---|---|
| T-26 | IKE SA | `show crypto isakmp sa` (R-BR) | `QM_IDLE` with peer 203.0.113.2 |
| T-27 | IPsec SA counters | `show crypto ipsec sa` | encaps/decaps counters increase during T-29 |
| T-28 | OSPF over tunnel | `show ip route ospf` (R-BR) | HQ 10.10.x.0 routes via Tunnel0 |
| T-29 | Branch to HQ service | Branch PC `ping 10.10.50.40`, open `\\FS01` | Success |
| T-30 | Local breakout | Branch PC `tracert 8.8.8.8` | First hop 10.20.20.1, second hop 198.51.100.1 (not via HQ) |
| T-31 | Branch DHCP over VPN | Branch PC renew | 10.20.20.21+ from DC01 |

## Failover (phase 7)

| ID | Test | Expected |
|---|---|---|
| T-32 | Continuous ping from a Sales PC to 8.8.8.8, then shut CORE2 | Under 5 pings lost; CORE1 becomes active for VLAN 30 (`%HSRP-5-STATECHANGE`) |
| T-33 | Unplug ACC-F2-01 Gi0/1 | Under 2 pings lost (RSTP) |
| T-34 | Shut CORE1 Gi1/0/1 (uplink) | CORE1 priority 110 → 90, CORE2 active for all VLANs, internet keeps working |
| T-35 | Remove one Po1 member | No loss; Po1 stays up with one member |
| T-36 | Stop DC01 | New leases served by DC02 (failover); DNS resolves through 10.10.50.11 |

## Security spot checks

| ID | Test | Expected |
|---|---|---|
| T-37 | Telnet to any device | Connection refused |
| T-38 | SSH from a Sales PC to CORE1 | Refused (VTY ACL); logged |
| T-39 | SSH from IT-OPS with an AD account | Accepted (RADIUS); accounting record on NPS01 |
| T-40 | External port scan of 203.0.113.2 | Only TCP/25 open |
