#!/usr/bin/env python3
"""build_aggression.py — walk the aIPg aggression (fight) circuit downstream.
Every edge is a real VFBquery/FlyWire row.

Hop-0: FBbt_00110593 "aIPg (adult fruitless aIP-g (male) neuron)" — the
male fru+ aggression command cluster. Class-level grouped
/query_connectivity via FBbt ID died server-side (IncompleteRead,
broad-class truncation — same failure mode as dFB/thermo); the LABEL form
returned 586 real rows on the first try. No instance-level attack, no
motor-backward, no BANC needed.

Hop-1 selection note (documented, not hidden): the walk skips three
high-weight buckets in the same spirit as the GENERIC blocklist —
"Notch OFF hemilineage neuron" (tw=3434) and "Notch ON hemilineage
neuron" (tw=2024) as generic developmental buckets, and "fruitless
expressing neuron" (tw=2054) as the fru parent bucket (its convergence
role is recorded in the honest_note, not graphed). Duplicated
ancestor/child tiers represented by their most specific member.
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


LARVAL_EXCLUDE = {"larval neuron", "larval CNS neuron",
                  "larval interneuron", "larval sensory neuron"}


def pick_downstream_adult(up_query, up_id, up_label, k, log):
    picks = pick_downstream(up_query, up_id, up_label, k + 4, log)
    adult = [(dc, dcid, tw) for dc, dcid, tw in picks
             if dc not in LARVAL_EXCLUDE]
    for dc in [dc for dc, _, _ in picks if dc in LARVAL_EXCLUDE]:
        log.append(f"  (excluded larval class from adult walk: {dc})")
    return adult[:k]


# (fbid, label, weight) — weights from the real label-form grouped query
HOP1 = [
    ("FBbt_00050114", "adult SMPpv2 lineage neuron", 2282),
    ("FBbt_00100706", "CP1 lineage neuron", 2282),
    ("FBbt_00050227", "adult VLPl2 lineage neuron", 2258),
    ("FBbt_00100711", "BLAv2 lineage neuron", 2258),
    ("FBbt_20002916", "adult superior medial protocerebrum neuron 054", 2202),
    ("FBbt_20002074", "adult posterior ventrolateral protocerebrum neuron 016", 2182),
]

HOP0_ID = "FBbt_00110593"
HOP0_LABEL = "aIPg (adult fruitless aIP-g (male) neuron)"


def build():
    emit("== aggression ==")
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
        "stimulus": "aggression",
        "source": "Virtual Fly Brain VFBquery HTTP API "
                  "(https://v3-cached.virtualflybrain.org/), FlyWire FAFB "
                  "v783 connectome; class-aggregated /query_connectivity, "
                  "edge weight = total synapse count",
        "nodes": list(nodes.values()),
        "edges": edges,
        "behavior": {
            "text": "Male aggression command: the fru+ aIPg cluster drives "
                    "fighting behavior — lunging, boxing, wing threat — "
                    "through superior/posterior protocerebrum integration "
                    "populations (SMPpv2, CP1, VLPl2, BLAv2) toward motor "
                    "output.",
            "basis": "aIPg as a male fru+ aggression cluster is textbook "
                     "Drosophila; edges below are the resolved API walk, "
                     "stated as measured wiring",
        },
        "fly_narration": "Mine — lunge, strike, hold.",
        "honest_note": (
            "Hop-1 skips 'Notch OFF hemilineage neuron' (tw=3434) and "
            "'Notch ON hemilineage neuron' (tw=2024) as generic "
            "developmental buckets, and 'fruitless expressing neuron' "
            "(tw=2054) as the fru parent bucket — same spirit as the "
            "GENERIC blocklist. CONVERGENCE WITH MATING: the aggression "
            "chain MEETS the P1 mating chain at FBbt_00016687 'fruitless "
            "expressing neuron' — aIPg feeds it (tw=2054) and P1's "
            "fruitless aSP-a feeds it (tw=63139, mating.json). The fru+ "
            "fight and fru+ courtship systems share this node — the same "
            "node where the pheromone chain also converges. aSPg: no FBbt "
            "class found under that name ('aSPg neuron' / 'fight neuron' "
            "searches return nothing). CL062 (FBbt_20000767, adult clamp "
            "neuron 062 / male wing aggression neuron) exists as a related "
            "aggression class but was not walked — noted, not hidden. "
            "CIRCUIT VS DRIVE: every edge here is REAL measured wiring of "
            "aIPg's downstream chain. The AGGRESSION-DRIVE DYNAMICS — how "
            "aggressive arousal ramps, persists, and arbitrates against "
            "mating/hunger — are the genuinely unmapped frontier; no API "
            "holds them, and nothing here models them."
        ),
        "hop0_ids": [HOP0_ID],
    }
    path = os.path.join(OUT, "aggression.json")
    with open(path, "w") as f:
        json.dump(graph, f, indent=1)
    emit(f" saved {path}: {len(nodes)} nodes, {len(edges)} edges")


if __name__ == "__main__":
    build()
