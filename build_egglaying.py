#!/usr/bin/env python3
"""build_egglaying.py — walk downstream from oviDN (oviposition descending
neurons) using ONLY real VFBquery/FlyWire connectivity. Saves
subgraphs/egglaying.json.

Hop 0: FBbt_00049919 "oviposition descending neuron oviDN" (aggregate class;
the 12-instance aggregate of oviDNa/b/d/v/x). The ID-form grouped query
truncates server-side (IncompleteRead) — the LABEL form returns 421 real
rows. Subtype queries are weak (oviDNa: server death in label form;
oviDNb: 29 rows, all weak) — so the aggregate class is the honest hop-0,
per the playbook's most-informative-class convention.

Every kept edge is a real API row. Nothing is invented.
"""

import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from build_graphs import fetch_rows, norm_row, GENERIC

# Documented skips (same spirit as the GENERIC blocklist; see GAPS.md):
# - Notch hemilineage classes are developmental lineage buckets, not
#   functional populations (proprioception-build precedent).
# - FBbt_00059247 "adult visual neuropil intrinsic neuron": its VFB term
#   description states its synapses are RESTRICTED to the optic lobes /
#   ocellar ganglia — it cannot be downstream of SEZ output or VNC
#   classes. Same class-aggregation artifact as the proprioception build
#   (documented in GAPS.md); skipped with this reason, not hidden.
SKIP_IDS = {
    "FBbt_00049539",  # Notch ON hemilineage neuron
    "FBbt_00049540",  # Notch OFF hemilineage neuron
    "FBbt_00049541",  # Notch ON hemilineage secondary neuron
    "FBbt_00049542",  # Notch OFF hemilineage secondary neuron
    "FBbt_00047106",  # Notch ON hemilineage primary neuron
    "FBbt_00047105",  # Notch OFF hemilineage primary neuron
    "FBbt_00059247",  # adult visual neuropil intrinsic neuron (artifact, see above)
    "FBbt_00003775",  # medulla intrinsic columnar neuron (optic-lobe artifact family)
    "FBbt_00013789",  # narrow field transmedullary neuron (optic-lobe artifact family)
    # Optic-lobe-restricted classes appearing as downstream of SEZ-output /
    # brain classes: same class-aggregation artifact family as FBbt_00059247
    # (columnar/medulla classes are optic-lobe intrinsic by definition and
    # cannot be downstream of subesophageal output neurons).
    "FBbt_00110137",  # optic lobe wide-field columnar neuron
    "FBbt_00053385",  # medulla intrinsic neuron
    "FBbt_00110136",  # optic lobe narrow field columnar neuron
    "FBbt_00111640",  # medulla columnar neuron
}

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "subgraphs")
HOP0_ID = "FBbt_00049919"
HOP0_LABEL = "oviposition descending neuron oviDN"


def pick(up_query, up_id, up_label, k):
    """Top-k specific downstream classes, deduped by class id (max weight)."""
    rows, prov = fetch_rows(up_query, up_id, up_label, [])
    if rows is None:
        print(f"  !! all query forms failed for {up_label} — GAP")
        return []
    best = {}
    for r in rows:
        n = norm_row(r, prov)
        if not n:
            continue
        dc, dcid, tw = n
        if dcid == up_id or dc in GENERIC or tw <= 0:
            continue
        if dcid in SKIP_IDS:
            continue  # documented skip (see SKIP_IDS note above)
        if dcid not in best or tw > best[dcid][0]:
            best[dcid] = (tw, dc)
    cands = sorted(((tw, dc, dcid) for dcid, (tw, dc) in best.items()),
                   reverse=True)
    print(f"  {up_label}: {len(rows)} raw rows [{prov}], "
          f"{len(cands)} specific unique candidates")
    for tw, dc, dcid in cands[:k + 3]:
        print(f"      cand: {dc} [{dcid}] tw={tw}")
    return [(dc, dcid, tw) for tw, dc, dcid in cands[:k]]


def main():
    nodes = {}
    edges = []
    seen_edge = set()

    def add_node(nid, label, hop):
        if nid not in nodes:
            nodes[nid] = {"id": nid, "name": label, "type": label,
                          "hop": hop}

    def add_edge(pre, post, w):
        if (pre, post) not in seen_edge:
            seen_edge.add((pre, post))
            edges.append({"pre": pre, "post": post, "weight": w})

    add_node(HOP0_ID, HOP0_LABEL, 0)
    print("hop 1:")
    hop1 = pick(HOP0_LABEL, HOP0_ID, HOP0_LABEL, 6)
    for dc, dcid, tw in hop1:
        add_node(dcid, dc, 1)
        add_edge(HOP0_ID, dcid, tw)

    print("hop 2:")
    for dc, dcid, tw in hop1:
        for d2, d2id, tw2 in pick(dcid, dcid, dc, 3):
            add_node(d2id, d2, 2)
            add_edge(dcid, d2id, tw2)

    graph = {
        "stimulus": "egglaying",
        "source": "Virtual Fly Brain VFBquery HTTP API "
                  "(https://v3-cached.virtualflybrain.org/), "
                  "FlyWire FAFB v783 connectome; class-aggregated "
                  "/query_connectivity, edge weight = total synapse count",
        "nodes": list(nodes.values()),
        "edges": edges,
        "behavior": {
            "text": "Egg laying: oviposition descending neurons (oviDNs) "
                    "command the abdominal motor circuits that drive "
                    "ovipositor movements and egg deposition.",
            "basis": "textbook Drosophila oviposition circuit (oviDNs -> "
                     "abdominal/VNC motor); stated as known biology",
        },
        "fly_narration": "Time.",
        "hop0_ids": [HOP0_ID],
    }
    path = os.path.join(OUT, "egglaying.json")
    with open(path, "w") as f:
        json.dump(graph, f, indent=1)
    print(f"saved {path}: {len(nodes)} nodes, {len(edges)} edges")


if __name__ == "__main__":
    main()
