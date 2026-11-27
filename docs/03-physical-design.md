# 03 · Physical Design

## Building layout

```
 FLOOR 3  ┌────────────────────────────────────────────────────────────┐
          │ Engineering (12 desks)   │ IT-OPS (6)  │ Training lab      │
          │                          │             │ [HUB] 6-10 PCs    │
          │        (AP-F3-1)         │  [IDF-3]    │     (AP-F3-2)     │
          └──────────────────────────┴──────┬──────┴───────────────────┘
                                            │ riser: 2x Cat6A + 2 spare
 FLOOR 2  ┌─────────────────────────────────┼──────────────────────────┐
          │ Engineering (20 desks)          │                          │
          │        (AP-F2-1)           [IDF-2]          (AP-F2-2)      │
          └─────────────────────────────────┼──────────────────────────┘
                                            │ riser: 2x Cat6A + 2 spare
 FLOOR 1  ┌───────────────┬─────────────────┼──────────┬───────────────┐
          │ Reception /   │ Sales (10)      │ [IDF-1]  │ SERVER ROOM   │
          │ Admin-HR (10) │                 │          │ (MDF)         │
          │  (AP-F1-1)    │    (AP-F1-2)    │          │ R-EDGE, CORE1 │
          │               │                 │          │ CORE2, ACC-DC │
          └───────────────┴─────────────────┴──────────┴───────────────┘
```

- **MDF (main distribution frame)**: the server room on floor 1. It has the ISP demarcation point, R-EDGE, both
  core switches, the server access switch, servers, WLC and UPS. It has its own cooling and a locked door with badge access.
- **IDFs (intermediate distribution frames)**: one wall-mount rack per floor, stacked vertically so the riser
  runs are short. Each IDF is within 90 m cable length of every outlet it serves (TIA-568 horizontal limit).
  Floor 1's IDF is separate from the MDF so user cabling stays out of the server room.

## Rack elevations

**MDF, 42U floor rack (rack 1: network) and 42U rack (rack 2: servers)**

| U | Rack 1 (network) | Rack 2 (servers) |
|---:|---|---|
| 42 | Fibre/copper patch panel: ISP demarc | Patch panel, 24-port Cat6 |
| 41 | Cable manager | Cable manager |
| 40 | R-EDGE (ISR 4331) | ACC-DC-01 (2960-24TT) |
| 39 | Cable manager | Cable manager |
| 38 | CORE1 (Catalyst 3650-24TS) | WLC01 (2504) |
| 37 | CORE2 (Catalyst 3650-24TS) | (spare) |
| 36 | Cable manager | KVM / console server |
| 35 | Patch panel: risers to IDF-1/2/3 | |
| 30-20 | (growth) | DC01, DC02, NPS01, FS01, WEB01, MAIL01, MON01 (1U-2U each) |
| 4-1 | UPS 3 kVA (rack-mount) + PDU | UPS 3 kVA + PDU |

**IDF, 12U wall-mount (same on every floor)**

| U | Device |
|---:|---|
| 12 | 24-port Cat6 patch panel (desks) |
| 11 | Cable manager |
| 10 | Access switch (2960-24TT) |
| 9 | Cable manager |
| 8 | Riser patch panel (uplinks to MDF) |
| 1-2 | 1 kVA line-interactive UPS |

## Structured cabling

| Run | Medium | Standard | Notes |
|---|---|---|---|
| Desk to IDF (horizontal) | Cat6 U/UTP, plenum | TIA-568-C, T568B termination | Max 90 m permanent link + 10 m patch cords |
| IDF to MDF (riser) | Cat6A (2 used + 2 spare per floor) | 10GBASE-T ready | Gigabit uplinks today, 10 Gb later without re-cabling |
| AP drops | Cat6 | | Ceiling mount, mid-span PoE injector or PoE switch at refresh |
| Core interlink | Cat6 patch, 2 m | | Two ports, labelled Po1-A and Po1-B |
| ISP handoff | As provided by the ISP | | Demarcation documented in the runbook |

**Labelling scheme**: `<floor>-<rack>-<panel>-<port>`, for example `F2-R1-P1-17` for floor 2, IDF rack 1, panel 1, port 17.
The same label goes on the wall plate, the patch panel and the switch port description.

**Colour code for patch cords**

| Colour | Use |
|---|---|
| Blue | User data |
| Yellow | IP phones / voice |
| Green | Uplinks / trunks |
| Red | Routed links and WAN |
| Orange | Training-lab hub |
| Grey | Management / iLO |

## Port maps

Generated configs carry the same information as interface descriptions; this table is the cabling view.

### ACC-F1-01 (floor 1)

| Ports | Use | VLAN (data / voice) |
|---|---|---|
| Fa0/1-10 | Admin-HR desks | 20 / 60 |
| Fa0/11-20 | Sales desks | 30 / 60 |
| Fa0/21-22 | APs | 10 |
| Fa0/23-24 | Unused, shut | 999 |
| Gi0/1 | Uplink → CORE1 Gi1/0/2 | trunk |
| Gi0/2 | Uplink → CORE2 Gi1/0/2 | trunk |

### ACC-F2-01 (floor 2)

| Ports | Use | VLAN |
|---|---|---|
| Fa0/1-20 | Engineering desks | 40 / 60 |
| Fa0/21-22 | APs | 10 |
| Fa0/23-24 | Unused, shut | 999 |
| Gi0/1 / Gi0/2 | Uplinks → CORE1 / CORE2 Gi1/0/3 | trunk |

### ACC-F3-01 (floor 3)

| Ports | Use | VLAN |
|---|---|---|
| Fa0/1-12 | Engineering desks | 40 / 60 |
| Fa0/13-18 | IT-OPS desks | 25 / 60 |
| Fa0/19 | **Training-lab hub** (100 Mb half duplex) | 90 |
| Fa0/20-21 | APs | 10 |
| Fa0/22-24 | Unused, shut | 999 |
| Gi0/1 / Gi0/2 | Uplinks → CORE1 / CORE2 Gi1/0/4 | trunk |

### ACC-DC-01 (server room)

| Ports | Use | VLAN |
|---|---|---|
| Fa0/1-12 | Servers | 50 |
| Fa0/13 | WLC01 | trunk 10, 70, 80 |
| Fa0/14-17 | iLO / iDRAC | 10 |
| Fa0/18-24 | Unused, shut | 999 |
| Gi0/1 / Gi0/2 | Uplinks → CORE1 / CORE2 Gi1/0/5 | trunk |

### CORE1 and CORE2 (identical port plan)

| Port | Connects to |
|---|---|
| Gi1/0/1 | R-EDGE (routed /30) |
| Gi1/0/2-5 | ACC-F1-01, ACC-F2-01, ACC-F3-01, ACC-DC-01 |
| Gi1/0/23-24 | Po1 to the other core |
| Gi1/0/6-22 | Spare (growth: more IDFs, 10 Gb modules) |

## Power and environment

- Each rack has a UPS sized for **at least 30 minutes** at full load. The MDF UPS units have network cards so MON01 receives SNMP traps on power events.
- Server-room temperature target is 18-27 °C (ASHRAE). An environmental sensor alerts above 30 °C.
- The demarcation point and MDF are on a dedicated 20 A circuit.
