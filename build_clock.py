#!/usr/bin/env python3
"""build_clock.py — walk the circadian clock (LNv) output circuit downstream.
Every edge is a real VFBquery/FlyWire row.

Hop-0: FBbt_00004046 "LNv neuron" (lateral neurons ventral — the PDF
pigment-dispersing-factor clock cells, the fly's master pacemaker
output). Class-level grouped /query_connectivity returned 657 rows on
the first try (no fallback needed). More specific subclasses
(FBbt_00003764 s-LNv Pdf neuron, FBbt_00003763 l-LNv) returned 0 rows
in every form — genuinely empty, not truncated — so the walk uses the
general LNv class, which is where the indexed connectivity lives.

Hop-1 selection (documented, not hidden): top-6 deduped specific
classes by summed total_weight (raw rows carry per-dataset duplicates;
summed per FBbt id). Paired classes with identical summed weights
(pacemaker/adult pacemaker 3307/3307, SLPpl1/DPLl1 3294/3294) are
treated as duplicated tiers of one synapse set — represented by the
most specific member, same spirit as the mating/CO2 walks. Skipped as
generic buckets per the GENERIC blocklist; 'secondary neuron'
(FBbt_00047096) and 'Notch ON hemilineage' tiers skipped as
non-specific; self (FBbt_00004046) skipped per no-self-loop.
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


# (fbid, label, weight) — deduped summed weights from the grouped query
HOP1 = [
    ("FBbt_00100163", "adult pacemaker neuron", 3307),
    ("FBbt_00050230", "adult SLPpl1 lineage neuron", 3294),
    ("FBbt_00059247", "adult visual neuropil intrinsic neuron", 2804),
    ("FBbt_00053404", "accessory medulla neuron", 2559),
    ("FBbt_00003628", "adult DN period neuron", 1907),
    ("FBbt_00050117", "adult LHd2 lineage neuron", 1838),
]

HOP0_ID = "FBbt_00004046"
HOP0_LABEL = "LNv neuron"


def build():
    emit("== clock ==")
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
        "stimulus": "clock",
        "source": "Virtual Fly Brain VFBquery HTTP API "
                  "(https://v3-cached.virtualflybrain.org/), FlyWire FAFB "
                  "v783 connectome; class-aggregated connectivity, edge "
                  "weight = total synapse count",
        "nodes": list(nodes.values()),
        "edges": edges,
        "behavior": {
            "text": "Circadian time: the LNv pacemaker neurons broadcast "
                    "pigment-dispersing factor (PDF) to clock-to-clock "
                    "targets (pacemaker neurons, DN period neurons), the "
                    "accessory medulla hub, and output regions (superior "
                    "lateral protocerebrum, visual neuropils), gating "
                    "daily rhythms of sleep, feeding, and courtship.",
            "basis": "LNv as the PDF master pacemaker is textbook "
                     "Drosophila (Renn et al 1999; Helfrich-Forster); "
                     "edges below are the resolved API walk, stated as "
                     "measured wiring",
        },
        "fly_narration": "Dawn, dusk — the wheel turns on time.",
        "honest_note": (
            "Hop-0 = general LNv class FBbt_00004046 (657 grouped rows, "
            "first try). The specific subclasses s-LNv Pdf "
            "(FBbt_00003764) and l-LNv (FBbt_00003763) returned 0 rows in "
            "every query form (grouped id/label, named) — genuinely "
            "empty, not truncated — so the walk uses the general class "
            "where the indexed connectivity lives. Hop-1 weights are "
            "deduped sums per FBbt id (raw rows carry per-dataset "
            "duplicates); paired identical-weight classes "
            "(pacemaker/adult pacemaker, SLPpl1/DPLl1) treated as "
            "duplicated tiers, most specific member kept. CIRCUIT VS "
            "OSCILLATOR: every edge here is REAL measured wiring of the "
            "LNv output chain. The OSCILLATOR DYNAMICS — the 24h "
            "molecular clock, PDF cycling, phase — are the genuinely "
            "unmapped frontier; no API holds them, and nothing here "
            "models them."
        ),
        "hop0_ids": [HOP0_ID],
    }
    path = os.path.join(OUT, "clock.json")
    with open(path, "w") as f:
        json.dump(graph, f, indent=1)
    emit(f" saved {path}: {len(nodes)} nodes, {len(edges)} edges")


if __name__ == "__main__":
    build()
