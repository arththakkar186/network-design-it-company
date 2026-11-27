# 08 · Bill of Materials

Prices are rough 2021 planning estimates in CAD. They are not quotes.

## Network hardware

| Qty | Item | Role | Unit (est.) | Total |
|---:|---|---|---:|---:|
| 1 | Cisco ISR 4331 + SEC licence | R-EDGE: NAT, ZBF, IPsec | 3,800 | 3,800 |
| 1 | Cisco ISR 4321 + SEC licence | R-BR | 2,200 | 2,200 |
| 2 | Cisco Catalyst 3650-24TS (IP Base) | CORE1, CORE2 | 4,500 | 9,000 |
| 5 | Cisco Catalyst 2960-24TT-L | ACC-F1/F2/F3/DC, SW-BR-01 | 900 | 4,500 |
| 1 | Cisco 2504 WLC (25 AP licence) | WLC01 | 2,000 | 2,000 |
| 6 | Cisco Aironet 1832i | Floor APs | 450 | 2,700 |
| 6 | PoE injector (802.3at) | AP power (non-PoE access switches) | 60 | 360 |
| 1 | Existing 10/100 hub | Training lab (reused) | 0 | 0 |
| | | | **Subtotal** | **24,560** |

## Infrastructure

| Qty | Item | Total |
|---:|---|---:|
| 2 | 42U floor rack with side panels | 2,400 |
| 3 | 12U wall-mount rack | 900 |
| 2 | 3 kVA rack UPS with network card | 3,600 |
| 3 | 1 kVA line-interactive UPS | 900 |
| 7 | 24-port Cat6 patch panel | 700 |
| 1 | Cabling: about 90 Cat6 drops + 12 Cat6A risers, installed and certified | 18,000 |
| 1 | Patch cords (colour-coded), cable managers, labels | 800 |
| | **Subtotal** | **27,300** |

## Servers (Windows Server 2019)

| Qty | Item | Total |
|---:|---|---:|
| 2 | 1U server (DC01, DC02) | 7,000 |
| 1 | Virtualisation host for NPS01, WEB01, MAIL01, MON01 (VMs) | 9,000 |
| 1 | File server with RAID 6 (FS01) | 6,500 |
| 1 | Windows Server Standard licensing + CALs (estimate) | 6,000 |
| | **Subtotal** | **28,500** |

## Summary

| Category | Total (CAD) |
|---|---:|
| Network hardware | 24,560 |
| Infrastructure and cabling | 27,300 |
| Servers and licensing | 28,500 |
| Contingency (10%) | 8,036 |
| **Project total** | **88,396** |

Recurring: SmartNet support about 12% of hardware a year, plus two business internet circuits.

## Packet Tracer equivalents

| Production | Packet Tracer model |
|---|---|
| ISR 4331 / 4321 | ISR4331 / ISR4321 |
| Catalyst 3650-24TS | 3650-24PS |
| Catalyst 2960-24TT | 2960-24TT |
| WLC 2504 | WLC-2504 |
| Aironet 1832i | LAP-PT / 3702i |
| Hub | Hub-PT |
| Servers | Server-PT (DHCP, DNS, HTTP, EMAIL services) |
