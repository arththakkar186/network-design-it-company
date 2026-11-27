# 11 · Design Decisions

Short ADR-style records of the main choices.

### ADR-01: Collapsed core instead of three-tier
**Context**: One building with three floors and about 120 users. **Decision**: Two L3 core switches act as both
core and distribution. **Consequences**: Lower cost and fewer devices. If the company grows to several buildings,
a separate core layer can be added above the current pair without readdressing.

### ADR-02: Layer 2 access with dual-homed trunks (not routed access)
**Context**: Routed access (L3 to the edge) removes STP but needs L3-capable access switches and means a VLAN cannot span floors.
**Decision**: L2 access on 2960s, with STP root and HSRP aligned per VLAN. **Consequences**: Cheaper access switches,
and Engineering can span floors 2 and 3. STP is still needed, but Rapid-PVST+ converges fast enough.

### ADR-03: HSRP rather than VRRP or GLBP
**Decision**: HSRPv2 with per-VLAN active roles split between the cores. **Why**: Cisco-only network, well
supported in Packet Tracer, and the load sharing comes from splitting VLANs. GLBP's per-host load balancing would
have conflicted with the STP alignment rule.

### ADR-04: OSPF single area
**Decision**: OSPF area 0 everywhere. **Why**: An open standard, fast convergence and a small LSDB. EIGRP would work but ties the design to Cisco. Static routes would not adapt to failures.

### ADR-05: GRE over IPsec for the branch
**Decision**: GRE tunnel with an IPsec profile instead of a crypto-map VPN. **Why**: OSPF needs multicast, and a
tunnel interface can be a routing adjacency. **Trade-off**: About 24 bytes more overhead, handled by MTU/MSS settings.

### ADR-06: Local internet breakout at the branch
**Decision**: The branch uses its own ISP for internet and the tunnel only for HQ subnets. **Why**: Less HQ bandwidth used and lower latency to SaaS. **Trade-off**: The branch needs its own firewall policy (ZBF on R-BR).

### ADR-07: Zone-based firewall on the ISR instead of a separate ASA
**Decision**: IOS ZBF. **Why**: Budget, and one less device. **Revisit**: When remote-access VPN, IPS or URL filtering is needed, a dedicated next-generation firewall is the next step.

### ADR-08: Third octet matches VLAN ID
**Decision**: `10.<site>.<vlan>.0`. **Why**: Faster troubleshooting, because anyone can tell the VLAN from an address. **Trade-off**: Address space cannot be packed tightly, which does not matter inside a /16.

### ADR-09: Keep the existing hub, isolated
**Decision**: Use the hub only for the training lab, on its own internet-only VLAN with half duplex forced. See [09](09-hubs-vs-switches.md).

### ADR-10: Configs generated from a single source of truth (2026 addition)
**Decision**: Every config is rendered from `design/network.json`, checked by `validate.py` and unit tests, and checked again in CI.
**Why**: The original 2021 configs were typed by hand into each device, separately from the IP plan document, so the two could drift apart.
Generating both from one file removes that whole class of error, and every change shows up as a reviewable diff.
