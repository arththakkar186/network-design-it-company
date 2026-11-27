# 01 · Requirements

## Business scenario

NorthBridge Technologies (fictional) is an IT consulting company growing from one rented floor to a
three-floor head office, and it is opening a small branch office in another city. The brief was to design a
network that:

- supports today's staff with room to grow about 50% over three years,
- keeps departments apart for security and compliance,
- keeps running when one core switch or uplink fails,
- gives staff and guests Wi-Fi without exposing internal systems,
- connects the branch securely to head-office services, and
- uses the hubs and switches already owned where it is safe to do so, with a clear upgrade path.

## Users and devices

| Area | Location | Staff | Wired desks | Phones | Wi-Fi devices (est.) |
|---|---|---:|---:|---:|---:|
| Administration, finance, HR | HQ floor 1 | 15 | 10 | 15 | 30 |
| Sales | HQ floor 1 | 15 | 10 | 15 | 35 |
| Engineering / consultants | HQ floors 2-3 | 75 | 32 | 40 | 170 |
| IT operations | HQ floor 3 | 6 | 6 | 6 | 15 |
| Training lab (shared PCs) | HQ floor 3 | n/a | 6-10 behind hub | 0 | 0 |
| Servers and infrastructure | HQ server room | n/a | 12 servers, 4 iLO, 1 WLC | 0 | 0 |
| Guests | HQ all floors | n/a | 0 | 0 | 50 |
| Branch staff | Branch | 25 | 20 | 20 | 40 |

Desk counts are lower than staff counts because most consultants work from laptops on Wi-Fi.
This is why the corporate Wi-Fi subnet is a /23.

## Functional requirements

| ID | Requirement | How the design meets it |
|---|---|---|
| FR-1 | Separate departments into their own broadcast domains | 10 VLANs at HQ, 3 at the branch ([IP plan](ip-address-plan.md)) |
| FR-2 | Central DHCP and DNS from Windows Server | DC01/DC02 with `ip helper-address` on every client SVI, including the branch over VPN |
| FR-3 | Shared file, intranet and mail services | FS01, WEB01, MAIL01 in the server VLAN |
| FR-4 | Wired and wireless access on every floor | One access switch per floor, 2 APs per floor, central WLC |
| FR-5 | Guest internet that cannot reach internal networks | Guest SSID on VLAN 80 with the `INTERNET-ONLY-IN` ACL |
| FR-6 | IP telephony | Voice VLAN 60 / 160 and QoS trust |
| FR-7 | Branch reaches HQ services securely | GRE over IPsec, OSPF over the tunnel |
| FR-8 | Inbound internet email | Static PAT for TCP/25 to MAIL01, allowed through the zone-based firewall |
| FR-9 | Reuse the existing hub for the training lab | Hub on its own isolated, internet-only VLAN 90 |

## Non-functional requirements

| ID | Requirement | Target | Design response |
|---|---|---|---|
| NFR-1 | Availability | No single core switch or core uplink failure takes users offline | Dual cores, dual-homed access, HSRP, uplink tracking |
| NFR-2 | Convergence | Under 3 seconds for a core failure at Layer 2 | Rapid-PVST+ (802.1w), HSRP with default timers |
| NFR-3 | Scalability | 50% growth without readdressing | VLSM with spare space in every /24, a /16 per site |
| NFR-4 | Security | Least privilege between segments, hardened management plane | [Security design](04-security-design.md) |
| NFR-5 | Manageability | Central logging, time, monitoring and authentication | Syslog/NTP/SNMPv3 to MON01, RADIUS to NPS01 |
| NFR-6 | Cost | Fit a small-business budget | Catalyst 2960 access, 3650 core, ISR 4000 edge ([BOM](08-bill-of-materials.md)) |
| NFR-7 | Documentation | Another technician can operate it | This repository |

## Constraints and assumptions

- One internet connection per site (a second ISP is listed as a future improvement).
- The server room is on floor 1. Each floor has a small IDF closet within 90 m of every desk (TIA-568 limit).
- The existing hub is a 10/100 half-duplex device. It will not be used for anything business-critical.
- The design and testing were done in Cisco Packet Tracer, so feature choices stay within what Packet
  Tracer supports for the 2960, 3650 and ISR 4000 series.
- Out of scope: firewall high availability, a second data centre, IPv6 (the IPv6 plan is described as future work in [02](02-architecture.md#future-improvements)).
