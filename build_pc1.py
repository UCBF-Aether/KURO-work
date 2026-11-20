#!/usr/bin/env python3
"""build_pc1.py — walk the pC1 courtship-integration output downstream.

CLOSES THE LOOP: pC1 (FBbt_00047348, doublesex pC1 male) is the convergence
node of the whole social brain — mating.json has P1->pC1 (tw=11,033, REAL),
song_lit.json ends AT pC1, pheromone/aggression converge on the fru node
pC1 also feeds. pC1's own downstream returned 0 rows during the mating
build (API degradation); the retry now returns 1,469 real rows.

Hop-0: FBbt_00047348 "adult doublesex pC1 (male) neuron".

Method: class-level grouped /query_connectivity via FBbt ID — worked on
the retry (1,469 rows, 900 unique classes after dedup). No fallback needed.

Hop-1 selection (documented, not hidden): top-6 specific classes by total
synapse weight + P1 as a deliberate 7th (pheromone-walk precedent: kept
deliberately because it is the prize edge). Duplicated tiers represented
by their most specific member:
- 'fruitless expressing neuron' FBbt_00016687: 87,164 (kept deliberately —
  the triple-convergence node; pC1 feeds back into the fru system)
- doublesex tier (34,237 x2): 'adult brain doublesex neuron' FBbt_00053229
  (more specific than 'adult doublesex neuron')
- SMPad1 tier (29,129 / 26,553): 'adult SMPad1 (male) lineage neuron'
  FBbt_00050245 (male-specific)
- aSP-a tier (26,553 x2): 'adult fruitless aSP-a (male) neuron'
  FBbt_00110595 (male-specific)
- DM4 tier (22,374 x2): 'adult DM4 lineage neuron' FBbt_00050254
  (mating-walk precedent)
- 'adult descending neuron' FBbt_00047511: 14,529 (pC1's direct motor output)
- DELIBERATE 7th: 'adult fruitless P1 (male) neuron' FBbt_00110621 (5,863)
  — THE LOOP-CLOSER: pC1->P1 is measured wiring, below the top-6 cutoff
  (same pattern as pIP10 in mating / giant fiber in looming)
Skipped as parent buckets (mating-walk precedent): 'sexually-dimorphic
neuron' FBbt_00051203 (47,894).

Hop-2: top-3 specific per hop-1 node via pick_downstream (grouped first,
named fallback).
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


HOP0_ID = "FBbt_00047348"
HOP0_LABEL = "adult doublesex pC1 (male) neuron"

# (fbid, label, weight) — weights from the real grouped /query_connectivity
HOP1 = [
    ("FBbt_00016687", "fruitless expressing neuron", 87164),
    ("FBbt_00053229", "adult brain doublesex neuron", 34237),
    ("FBbt_00050245", "adult SMPad1 (male) lineage neuron", 26553),
    ("FBbt_00110595", "adult fruitless aSP-a (male) neuron", 26553),
    ("FBbt_00050254", "adult DM4 lineage neuron", 22374),
    ("FBbt_00047511", "adult descending neuron", 14529),
    ("FBbt_00110621", "adult fruitless P1 (male) neuron", 5863),  # deliberate 7th
]


def build():
    emit("== pc1 ==")
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
        picks = pick_downstream(q, nid, label, 3, log)
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
        "stimulus": "pc1",
        "source": ("Virtual Fly Brain VFBquery HTTP API "
                   "(https://v3-cached.virtualflybrain.org/), FlyWire FAFB v783 "
                   "connectome; class-aggregated connectivity (grouped "
                   "/query_connectivity, 1,469 rows on retry — the 0-row "
                   "result during the mating build was API degradation), "
                   "edge weight = total synapse count"),
        "behavior": {
            "text": ("Courtship integration output: pC1 (doublesex, male) is "
                     "the convergence node of the social brain — courtship "
                     "song (JO-B->AMMC-B1->vPN1->pC1) and the P1 mating drive "
                     "(P1->pC1) meet here. pC1 fans out to the fru courtship "
                     "system, back to P1 itself, and directly to descending "
                     "motor neurons."),
            "basis": ("pC1 as the courtship-integration center is textbook "
                      "Drosophila (Zhou et al 2015; Ishikawa et al 2023); "
                      "edges below are the resolved API walk, stated as "
                      "measured wiring"),
        },
        "fly_narration": "She sings, he hears — and the circuit answers.",
        "honest_note": (
            "THE LOOP CLOSES. pC1->P1 (tw=5,863) is REAL measured wiring: "
            "the song chain (song_lit.json) ends at pC1, and pC1 drives P1 "
            "(mating.json) — courtship hearing feeds the mating drive "
            "through measured synapses, not just literature. pC1->pIP10 "
            "(tw=1,796) is also real (below top-k, recorded here). "
            "pC1->descending (tw=14,529) is pC1's direct motor output. "
            "pC1->fruitless-expressing (tw=87,164) feeds BACK into the "
            "fru system — the triple-convergence node is both upstream "
            "and downstream of pC1 (recurrent within the fru courtship "
            "system). Hop-1 takes top-6 specific + P1 as deliberate 7th; "
            "duplicated tiers by most specific member; 'sexually-dimorphic "
            "neuron' (47,894) skipped as parent bucket (mating precedent). "
            "CIRCUIT VS DYNAMICS: every edge is REAL measured wiring of "
            "pC1's output chain. How pC1 integrates song + pheromone + "
            "internal state into a courtship decision is the unmapped "
            "frontier; no API holds it and this graph models none of it."),
        "nodes": list(nodes.values()),
        "edges": edges,
    }
    with open(os.path.join(OUT, "pc1.json"), "w") as f:
        json.dump(graph, f, indent=2)
    emit(f"pc1.json: {len(nodes)} nodes, {len(edges)} edges")
    return graph


if __name__ == "__main__":
    build()
