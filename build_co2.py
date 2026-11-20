#!/usr/bin/env python3
"""build_co2.py — walk the CO2-alarm circuit downstream.
Every edge is a real VFBquery/FlyWire row.

Hop-0: FBbt_00067064 "adult olfactory receptor neuron Gr21a/63a" (the
ab1C CO2 neuron, Gr21a+Gr63a co-expressing). Class-level
/query_connectivity via the ID died server-side; the LABEL fallback
returned 126 real rows on the first try — no instance-level attack, no
motor-backward, no BANC needed.

Hop-1 dedup note (documented, not hidden): the grouped rows carry
duplicated ancestor/child tiers of the same synapse sets (identical
weights). Following the mating-walk precedent, each tier is represented
by its MOST SPECIFIC member:
- projection tier tw=15822: "antennal lobe projection neuron" 07422,
  "adult lateral horn input neuron" 49427, "adult antennal lobe
  projection neuron" 67123 -> kept 53398 "adult antennal lobe projection
  neuron to lateral horn"
- lineage tier tw=15248: "adult ALl1 lineage neuron" 50025 ->
  kept 00100660 "BAlc lineage neuron"
- local tier tw=13155: "local neuron" 51493, "antennal lobe local
  neuron" 52874 -> kept 07390 "adult antennal lobe local neuron"
- Notch ON tier tw=12220: "Notch ON hemilineage neuron" 49539 ->
  kept 49912 "BAlc Notch ON hemilineage neuron"
- l2LN tier tw=11032: "adult local interneuron of the lateral ALl1
  neuroblast" 07394 -> kept 51501 "adult antennal lobe local neuron l2LN"
"adult central brain intrinsic neuron" 59245 (tw=13155) is a distinct class.
"""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from build_graphs import pick_downstream

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "subgraphs")
LOGF = os.path.join(os.path.dirname(OUT), "build.log")


def emit(line):
    print(line, flush=True)
    with open(LOGF, "a") as f:
        f.write(line + "\n")


# Larval classes are real rows but wrong life stage for an adult
# olfactory circuit (documented precedent: dh44, mating walks).
LARVAL_EXCLUDE = {"larval neuron", "larval CNS neuron",
                  "larval interneuron", "larval sensory neuron",
                  "larval olfactory system neuron"}


def pick_downstream_adult(up_query, up_id, up_label, k, log):
    picks = pick_downstream(up_query, up_id, up_label, k + 4, log)
    adult = [(dc, dcid, tw) for dc, dcid, tw in picks
             if dc not in LARVAL_EXCLUDE]
    for dc in [dc for dc, _, _ in picks if dc in LARVAL_EXCLUDE]:
        log.append(f"  (excluded larval class from adult walk: {dc})")
    return adult[:k]


# (fbid, label, weight) — weights from the real grouped query (label form)
HOP1 = [
    ("FBbt_00053398", "adult antennal lobe projection neuron to lateral horn", 15822),
    ("FBbt_00100660", "BAlc lineage neuron", 15248),
    ("FBbt_00007390", "adult antennal lobe local neuron", 13155),
    ("FBbt_00059245", "adult central brain intrinsic neuron", 13155),
    ("FBbt_00049912", "BAlc Notch ON hemilineage neuron", 12220),
    ("FBbt_00051501", "adult antennal lobe local neuron l2LN", 11032),
]

HOP0_ID = "FBbt_00067064"
HOP0_LABEL = "adult olfactory receptor neuron Gr21a/63a"


def build():
    emit("== co2 ==")
    nodes = {HOP0_ID: {"id": HOP0_ID, "name": HOP0_LABEL,
                       "type": HOP0_LABEL, "hop": 0}}
    edges = []
    seen_edge = set()
    frontier = []
    for nid, label, tw in HOP1:
        nodes[nid] = {"id": nid, "name": label, "type": label, "hop": 1}
        if (HOP0_ID, nid) not in seen_edge:
            seen_edge.add((HOP0_ID, nid))
            edges.append({"pre": HOP0_ID, "post": nid, "weight": tw})
        frontier.append((nid, nid, label))

    for q, nid, label in frontier:
        log = []
        picks = pick_downstream_adult(q, nid, label, 3, log)
        for line in log:
            emit(line)
        if not picks:
            emit(f"  (no specific downstream for {label} — GAP)")
        for dc, dcid, tw in picks:
            if dcid not in nodes:
                nodes[dcid] = {"id": dcid, "name": dc, "type": dc, "hop": 2}
            if (nid, dcid) not in seen_edge:
                seen_edge.add((nid, dcid))
                edges.append({"pre": nid, "post": dcid, "weight": tw})

    graph = {
        "stimulus": "co2",
        "source": "Virtual Fly Brain VFBquery HTTP API "
                  "(https://v3-cached.virtualflybrain.org/), FlyWire FAFB "
                  "v783 connectome; class-aggregated /query_connectivity "
                  "(label form — the ID form died server-side), "
                  "edge weight = total synapse count",
        "nodes": list(nodes.values()),
        "edges": edges,
        "behavior": {
            "text": "CO2 alarm: the dedicated danger smell. Gr21a/Gr63a "
                    "ab1C neurons detect carbon dioxide and drive aversion "
                    "through antennal lobe projection neurons to the "
                    "lateral horn — the innate-aversion center — in "
                    "parallel with local inhibitory shaping.",
            "basis": "Gr21a/Gr63a as the CO2 receptor complex in ab1C "
                     "neurons is textbook Drosophila (Suh et al 2004); "
                     "edges below are the resolved API walk, stated as "
                     "measured wiring",
        },
        "fly_narration": "Bad air — leave.",
        "honest_note": (
            "Hop-1 collapses duplicated ontology tiers of identical "
            "synapse sets to their most specific member (mating-walk "
            "precedent; full mapping in build_co2.py docstring). The "
            "grouped /query_connectivity via the FBbt ID died "
            "server-side; the label form returned 126 real rows. "
            "Hop-2 walks use the standard top-3 heuristic with larval "
            "exclusion; hop-2 nodes that return no specific downstream "
            "are logged as GAPs, not faked. Sibling circuit: rotten.json "
            "(Or56a aversion) shares the AL->lateral-horn architecture "
            "but different glomerular origin."
        ),
        "hop0_ids": [HOP0_ID],
    }
    path = os.path.join(OUT, "co2.json")
    with open(path, "w") as f:
        json.dump(graph, f, indent=1)
    emit(f" saved {path}: {len(nodes)} nodes, {len(edges)} edges")


if __name__ == "__main__":
    build()
