# 02 · Architecture

## Topology choice: collapsed core

A full three-tier design (core, distribution, access) is meant for campuses with many buildings. For one
three-floor building, the core and distribution layers are combined into a **collapsed core** made of two
Layer 3 switches. This keeps hierarchical design benefits (clear roles, predictable failure domains,
summarisation at one point) and saves two to four switches.

```
                 Internet
                    |
                 R-EDGE  ---- GRE/IPsec ----  R-BR --- SW-BR-01
                 /     \
         (routed)       (routed)
             /             \
         CORE1 ==Po1==  CORE2          <- collapsed core / distribution (L3, HSRP, STP roots)
          | \  \ \     / / /  |
          |  \  \  \ /  / /   |
       ACC-F1 ACC-F2 ACC-F3 ACC-DC     <- access (L2 only, dual-homed)
                       |
                      HUB (lab)
```

## Layer roles

| Layer | Devices | Does | Does not |
|---|---|---|---|
| Edge | R-EDGE, R-BR | Internet, NAT, firewall, VPN, default route | Inter-VLAN routing for HQ users |
| Core / distribution | CORE1, CORE2 | Inter-VLAN routing (SVIs), HSRP gateways, STP roots, ACLs between segments, DHCP relay, OSPF | Connect end users |
| Access | ACC-*, SW-BR-01 | Connect users, phones, APs and servers; port security, DHCP snooping, DAI, PoE/QoS trust | Route |

## Redundancy model

Every access switch has one trunk to each core switch. That forms a triangle loop per access switch, which Spanning
Tree resolves. The design avoids the classic mistake of letting STP and HSRP pick roots and gateways independently.

**Rule: for every VLAN, the STP root bridge and the HSRP active gateway are the same switch.**

| VLANs | HSRP active (priority 110) | STP root (priority 24576) | Standby / secondary root |
|---|---|---|---|
| 10, 20, 40, 60, 80 | CORE1 | CORE1 | CORE2 (100 / 28672) |
| 25, 30, 50, 70, 90 | CORE2 | CORE2 | CORE1 (100 / 28672) |

Why it matters: if CORE1 were the STP root for VLAN 30 while CORE2 was its gateway, frames from a
Sales PC would go up to CORE1 and then across the core interlink to reach CORE2. That wastes the interlink
and adds a hop. With the roots aligned, each access switch's forwarding uplink for a VLAN goes straight
to that VLAN's gateway, and the other uplink is blocked but ready.

Splitting VLANs between the cores also **shares the load**: both uplinks of every access switch carry traffic,
each for half of the VLANs.

### Uplink tracking

Each core tracks its routed uplink to R-EDGE (`track 1 interface ... line-protocol`). If CORE1 loses its
uplink, its HSRP priority drops from 110 to 90, below CORE2's 100, so CORE2 takes over as gateway. Hosts
do not black-hole traffic at a core that has no path out. `preempt delay minimum 60` makes a recovering
core wait for OSPF and STP to settle before it takes the active role back.

### Core interlink

Two Gigabit ports are bundled into **Port-channel 1 with LACP** (`mode active`). The bundle carries all
VLANs, HSRP hellos between the cores, and STP. Losing one member link causes no outage.

## Routing

- **OSPF process 1, single area 0.** The network is small, so multi-area design would add complexity without benefit.
- **R-EDGE** runs `default-information originate` from its static default to the ISP, so the cores learn
  the internet path from OSPF and there is no static route on any switch.
- **Passive by default.** OSPF only forms adjacencies on the routed core uplinks and the tunnel
  (`passive-interface default`). User VLANs are advertised but never send hellos, so a rogue router on a user
  port cannot inject routes.
- Point-to-point network type on the /30 uplinks and the tunnel removes DR/BDR election and speeds up adjacencies.
- `auto-cost reference-bandwidth 10000` (10 Gb/s) makes OSPF cost tell the difference between 100 Mb, 1 Gb and 10 Gb links.
- Both cores advertise every HQ VLAN, so R-EDGE has **two equal-cost paths** back into the LAN (ECMP).
- The **branch** keeps a static default route (AD 1) to its own ISP. It also receives HQ's OSPF default
  (AD 110), but that route is only used if the static route is removed. This gives **local internet breakout**
  while everything for `10.10.0.0/16` goes over the tunnel.

## WAN / site-to-site VPN

| Item | Value |
|---|---|
| Transport | GRE tunnel (Tunnel0) protected by an IPsec profile, transport mode |
| IKE | IKEv1 main mode, AES-256, SHA-256, DH group 14, pre-shared key, 24 h lifetime, DPD keepalives |
| IPsec | ESP AES-256 / SHA-256 HMAC, PFS group 14 |
| Why GRE | Plain policy-based IPsec cannot carry multicast, so OSPF could not run over it. GRE can, so new branch subnets are learned automatically |
| MTU | `ip mtu 1400` and `ip tcp adjust-mss 1360` stop fragmentation from GRE (24 B) plus ESP (50-60 B) overhead |
| NAT exemption | The NAT ACLs deny HQ-to-branch traffic, so tunnel traffic is never translated |

## Traffic flows

**1. Sales PC (VLAN 30, floor 1) to file server FS01 (VLAN 50)**
PC → ACC-F1-01 → forwarding uplink toward CORE2 (STP root and HSRP active for VLAN 30) → CORE2 routes VLAN 30 to VLAN 50 →
down the trunk to ACC-DC-01 → FS01. The return path also goes through CORE2, because CORE2 is active for VLAN 50 too.

**2. Engineering laptop on corporate Wi-Fi to the internet**
Laptop → AP (CAPWAP tunnel inside VLAN 10) → WLC01 → WLC bridges the client onto VLAN 70 → CORE2 (gateway) →
OSPF default → R-EDGE → ZBF inspects INSIDE→OUTSIDE → PAT to 203.0.113.2 → ISP.

**3. Branch user to MAIL01**
PC (VLAN 120) → SW-BR-01 → R-BR sub-interface .120 → OSPF route to 10.10.50.0/26 via Tunnel0 → encrypted →
R-EDGE → OSPF ECMP to CORE1/CORE2 → MAIL01.

**4. Internet mail to MAIL01**
Sender → 203.0.113.2:25 → static PAT to 10.10.50.40:25 → ZBF OUTSIDE→INSIDE policy allows only TCP/25 to that host → MAIL01.

**5. Guest phone to the intranet (blocked)**
Guest (VLAN 80) → CORE1 SVI → `INTERNET-ONLY-IN` denies any destination in 10/8, 172.16/12 or 192.168/16 → dropped and logged.

## Failure scenarios

| Failure | What happens | User impact |
|---|---|---|
| One access uplink | RSTP unblocks the alternate uplink | About 1 s for affected VLANs |
| CORE1 fails completely | CORE2 becomes HSRP active for every VLAN (about 10 s with default timers) and STP root for every VLAN | Brief interruption for CORE1-active VLANs |
| CORE1 to R-EDGE link | Track drops CORE1 priority to 90 and CORE2 takes over; OSPF reconverges on R-EDGE | About 10 s |
| One Po1 member | LACP rebalances over the remaining link | None |
| R-EDGE or HQ ISP | No internet at HQ, no VPN; LAN still works | Single point of failure (see future improvements) |
| R-BR or branch ISP | Branch is isolated | Single point of failure |
| DC01 | DC02 serves DNS, and DHCP failover (load-balance mode) hands out leases | None |

## Future improvements

1. Second ISP and a second edge router with HSRP or BGP multihoming, which removes the edge single point of failure.
2. Branch backup over LTE, with DMVPN when there are more sites.
3. Replace the hub with a managed switch. The lab VLAN design stays the same ([09](09-hubs-vs-switches.md)).
4. 802.1X on wired ports using the NPS server that already does WPA2-Enterprise.
5. Dual-stack IPv6: a /48 per site, a /64 per VLAN, the VLAN ID in the fourth hextet, OSPFv3.
6. WPA3-Enterprise when the AP fleet is refreshed.
