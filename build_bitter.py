#!/usr/bin/env python3
"""build_bitter.py — build subgraphs/bitter.json via the standard class-level
walk. Unlike sugar/water, the bitter-sensing GRN class (FBbt_00049613) HAS
indexed class-level downstream connectivity (129 rows, 108 specific
candidates), so no instance-level attack was needed.

Every edge is a real VFBquery/FlyWire FAFB v783 row. Nothing is invented.
"""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from build_graphs import pick_downstream

BASE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(BASE, "subgraphs", "bitter.json")

HOP0_ID = "FBbt_00049613"
HOP0_LABEL = "bitter-sensing gustatory receptor neuron"
N_HOP1 = 6
N_HOP2 = 3


def main():
    nodes = {}
    edges = []
    seen_edge = set()

    def add_node(nid, label, hop):
        if nid not in nodes:
            nodes[nid] = {"id": nid, "name": label, "type": label, "hop": hop}

    def add_edge(pre, post, w):
        if (pre, post) not in seen_edge:
            seen_edge.add((pre, post))
            edges.append({"pre": pre, "post": post, "weight": w})

    add_node(HOP0_ID, HOP0_LABEL, 0)
    log = []
    hop1 = pick_downstream(HOP0_ID, HOP0_ID, HOP0_LABEL, N_HOP1, log)
    for line in log:
        print(line)
    for dc, dcid, tw in hop1:
        add_node(dcid, dc, 1)
        add_edge(HOP0_ID, dcid, tw)

    log = []
    for dc, dcid, tw in hop1:
        picks = pick_downstream(dcid, dcid, dc, N_HOP2, log)
        for line in log:
            print(line)
        log = []
        if not picks:
            print(f"  (no class-level downstream for {dc} — terminal at hop 1)")
        for dc2, dcid2, tw2 in picks:
            add_node(dcid2, dc2, 2)
            add_edge(dcid, dcid2, tw2)

    graph = {
        "stimulus": "bitter",
        "source": "Virtual Fly Brain VFBquery HTTP API "
                  "(https://v3-cached.virtualflybrain.org/), FlyWire FAFB "
                  "v783 connectome; class-aggregated /query_connectivity, "
                  "edge weight = total synapse count. The bitter-sensing GRN "
                  "class (unlike sweet/water) has indexed class-level "
                  "downstream connectivity, so this walk used it directly.",
        "nodes": list(nodes.values()),
        "edges": edges,
        "behavior": {
            "text": "Bitter taste drives aversive gustatory SEZ "
                    "interneurons, suppressing feeding and triggering "
                    "rejection/avoidance.",
            "basis": "resolved class-level walk: bitter-sensing GRNs -> "
                     "SEZ/gnathal interneuron classes (FlyWire v783); "
                     "bitter = canonical aversive taste modality",
        },
        "fly_narration": "Bitter on the tongue — spit it out.",
        "hop0_ids": [HOP0_ID],
        "method": {
            "hop0_class": HOP0_ID,
            "class_level_rows": 129,
            "note": "class-level downstream indexed; no instance attack needed",
        },
    }
    with open(OUT, "w") as f:
        json.dump(graph, f, indent=1)
    print(f"saved {OUT}: {len(nodes)} nodes, {len(edges)} edges")


if __name__ == "__main__":
    main()
