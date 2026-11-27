# 09 · Hubs vs Switches

The brief asked for a design that included both hubs and switches. This document explains how each
device works, why the hub is confined to the training lab, and how the design limits its weaknesses.

## How they differ

| | Hub (Layer 1) | Switch (Layer 2) |
|---|---|---|
| Forwarding | Repeats every bit out of every other port | Learns source MACs into a CAM table and forwards each frame only to the destination port |
| Collision domain | **One shared domain for all ports** | One per port (each port is its own collision domain) |
| Broadcast domain | One | One per VLAN |
| Duplex | Half duplex only (CSMA/CD) | Full duplex per port |
| Bandwidth | Shared, e.g. 100 Mb/s split among every device | Dedicated per port, e.g. 100 Mb/s each way to every device |
| Security | Every device sees every frame, so sniffing is trivial | Unicast frames are only seen by the destination |
| Management | None | VLANs, STP, port security, QoS, monitoring |

```
HUB: one collision domain                 SWITCH: one collision domain per port
 PC1 ─┐                                    PC1 ── [port1] ┐
 PC2 ─┼── [ HUB ] ── uplink                PC2 ── [port2] ┼─ CAM table ── uplink
 PC3 ─┘   every frame to every port        PC3 ── [port3] ┘  frame only to its destination
```

## Collision domains in this design

| Segment | Collision domains | Broadcast domains |
|---|---|---|
| Each switch port (desks, servers, APs) | 1 per port, full duplex, so collisions effectively never happen | Per VLAN |
| Training lab behind the hub | **1 shared by all lab PCs and the switch port Fa0/19** | VLAN 90 |
| Whole HQ | About 100 in use | 10 (one per VLAN) |

With 8 lab PCs on a 100 Mb/s half-duplex hub, the effective throughput per PC under load is roughly
100 / 8 ≈ 12 Mb/s, less after collisions and back-off. That is fine for training exercises and web
browsing, and not acceptable for production work. This is why business users never connect to a hub.

## Why keep the hub at all

1. The coursework required it, and the company already owned one.
2. It is useful for teaching: lab students can run Wireshark on any lab PC and see every other PC's traffic,
   which shows directly why switches replaced hubs.
3. With the controls below, it costs nothing and puts nothing at risk.

## How the design contains the hub

| Risk | Control |
|---|---|
| Duplex mismatch (switch auto-negotiates full, hub is half) causes late collisions and CRC errors | `speed 100` + `duplex half` forced on Fa0/19 |
| Many MACs appear on one switch port | `port-security maximum 12`, so the lab works but a flood is still capped |
| Lab PCs are shared and unmanaged | VLAN 90 has the `INTERNET-ONLY-IN` ACL, so it cannot reach any internal subnet |
| Sniffing | Only lab traffic is on the hub; no business traffic ever crosses it |
| Someone daisy-chains another hub or switch | BPDU guard err-disables the port if a switch sends BPDUs; port security caps MACs |
| Broadcast storms | Contained to VLAN 90, so other VLANs are unaffected |

## Upgrade path

Replacing the hub with a small managed switch needs **no** design change: VLAN 90, its addressing, ACL and
the Fa0/19 uplink stay the same. Only remove `speed 100` / `duplex half` from Fa0/19 and convert it into a
trunk or keep it as an access port.
