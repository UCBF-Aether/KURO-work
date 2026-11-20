#!/usr/bin/env python3
"""build_mating.py — walk the P1 courtship command circuit downstream.
Every edge is a real VFBquery/FlyWire row.

Hop-0: FBbt_00110621 "adult fruitless P1 (male) neuron" (fru-P / fru-P1 /
adult male fruitless pMP-e / pMP4 neuron). Class-level grouped
/query_connectivity returned 568 real rows on the first try — no
instance-level attack, no motor-backward, no BANC needed.

Hop-1 selection note (documented, not hidden): the walk skips two
high-weight ontology superclasses ("fruitless expressing neuron"
tw=51702, "sexually-dimorphic neuron" tw=25724) in the same spirit as the
GENERIC blocklist — they are parent buckets of the fru courtship system,
not specific circuit classes. Duplicated ancestor/child tiers are
represented by their most specific member (e.g. "adult brain doublesex
neuron" over "adult doublesex neuron", "adult doublesex pC1 (male)
neuron" over "adult doublesex pC1 neuron", "adult fruitless aSP-a (male)
neuron" over the non-male parent, "adult SMPad1 (male) lineage neuron"
over the non-male parent).
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


# Same documented heuristic as build_dh44.py: larval classes are real rows
# but wrong life stage for an adult courtship circuit.
LARVAL_EXCLUDE = {"larval neuron", "larval CNS neuron",
                  "larval interneuron", "larval sensory neuron"}


def pick_downstream_adult(up_query, up_id, up_label, k, log):
    picks = pick_downstream(up_query, up_id, up_label, k + 4, log)
    adult = [(dc, dcid, tw) for dc, dcid, tw in picks
             if dc not in LARVAL_EXCLUDE]
    for dc in [dc for dc, _, _ in picks if dc in LARVAL_EXCLUDE]:
        log.append(f"  (excluded larval class from adult walk: {dc})")
    return adult[:k]


# (fbid, label, weight) — weights from the real grouped query
HOP1 = [
    ("FBbt_00053229", "adult brain doublesex neuron", 17786),
    ("FBbt_00050245", "adult SMPad1 (male) lineage neuron", 15897),
    ("FBbt_00110595", "adult fruitless aSP-a (male) neuron", 15897),
    ("FBbt_00050254", "adult DM4 lineage neuron", 11373),
    ("FBbt_00047348", "adult doublesex pC1 (male) neuron", 11033),
    ("FBbt_00047511", "adult descending neuron", 8215),
]

HOP0_ID = "FBbt_00110621"
HOP0_LABEL = "adult fruitless P1 (male) neuron"


def build():
    emit("== mating ==")
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

    log = []
    for q, nid, label in frontier:
        picks = pick_downstream_adult(q, nid, label, 3, log)
        for line in log:
            emit(line)
        log = []
        if not picks:
            emit(f"  (no specific downstream for {label} — GAP)")
        for dc, dcid, tw in picks:
            if dcid not in nodes:
                nodes[dcid] = {"id": dcid, "name": dc, "type": dc, "hop": 2}
            if (nid, dcid) not in seen_edge:
                seen_edge.add((nid, dcid))
                edges.append({"pre": nid, "post": dcid, "weight": tw})

    graph = {
        "stimulus": "mating",
        "source": "Virtual Fly Brain VFBquery HTTP API "
                  "(https://v3-cached.virtualflybrain.org/), FlyWire FAFB "
                  "v783 connectome; class-aggregated /query_connectivity, "
                  "edge weight = total synapse count",
        "nodes": list(nodes.values()),
        "edges": edges,
        "behavior": {
            "text": "Male courtship command: the P1 cluster ramps during "
                    "courtship and drives the courtship ritual — visual "
                    "tracking, song production, and copulation attempt — "
                    "through fru/dsx integration centers (aSP-a, pC1, "
                    "SMPad1, DM4) down to descending motor neurons.",
            "basis": "P1 as the male courtship command cluster is textbook "
                     "Drosophila (von Philipsborn 2011; Kohatsu 2011); "
                     "edges below are the resolved API walk, stated as "
                     "measured wiring",
        },
        "fly_narration": "Her — follow, sing, reach.",
        "honest_note": (
            "Hop-1 skips two high-weight ontology superclasses "
            "('fruitless expressing neuron' tw=51702, 'sexually-dimorphic "
            "neuron' tw=25724) as generic parent buckets, same spirit as "
            "the GENERIC blocklist; duplicated ancestor/child tiers are "
            "represented by their most specific member. pIP10 "
            "(FBbt_00110854) IS a real downstream partner (tw=1444) but "
            "ranks below the top-k cutoff — same pattern as the giant "
            "fiber in the looming walk. The doublesex pC1 (male) neuron "
            "at hop 1 is the courtship integration center the spec asked "
            "about — it landed cleanly, no extra query needed. CIRCUIT "
            "VS DRIVE: every edge here is REAL measured wiring of P1's "
            "downstream command chain. The DRIVE DYNAMICS — how P1 "
            "activity ramps, persists, and satiates, and how it arbitrates "
            "against hunger/thirst — are the genuinely unmapped frontier; "
            "no API holds them, and nothing here models them."
        ),
        "hop0_ids": [HOP0_ID],
    }
    path = os.path.join(OUT, "mating.json")
    with open(path, "w") as f:
        json.dump(graph, f, indent=1)
    emit(f" saved {path}: {len(nodes)} nodes, {len(edges)} edges")


if __name__ == "__main__":
    build()
