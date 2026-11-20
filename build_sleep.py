#!/usr/bin/env python3
"""build_sleep.py — walk the dFB sleep-homeostat circuit downstream.
Every edge is a real VFBquery/FlyWire row.

Hop-0: FBbt_00049537 "adult dorsal fan-shaped body tangential neuron"
(the dFB sleep-homeostat neurons: build sleep pressure while awake,
discharge it in sleep — Donlea et al 2011 / Ueno et al 2012 territory).

Hop-0 method note: class-level grouped /query_connectivity DIED
server-side (IncompleteRead, ~1.4MB response truncated after 4 retries —
dFB is a broad class with many downstream partners). The named
DownstreamClassConnectivity fallback returned 50 real rows (limit=50).

Hop-1 selection (documented, not hidden): top-6 most-specific classes.
Skipped as generic buckets, same spirit as the GENERIC blocklist and the
mating walk's parent-bucket skips: ontology parents (neuron, adult
neuron, CNS neuron x2, interneuron x2, adult central complex neuron,
small field neuron [parent], large field neuron x2, fan-shaped body
tangential neuron, adult central brain intrinsic neuron, intrinsic
neuron of the central complex, input/output neuron, supraesophageal
ganglion neuron), transmitter buckets (dopaminergic/adult dopaminergic
97495, aminergic/adult aminergic 128356, cholinergic/adult cholinergic
126256 — cholinergic already in GENERIC), and self (FBbt_00049537
tw=135378, skipped per the no-self-loop convention). Duplicated
ancestor/child tiers represented by the most specific member (e.g.
"small field neuron of the central complex" over "small field neuron",
"adult fan-shaped body horizontal delta neuron" over "fan-shaped body
intrinsic neuron").
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


# Same documented heuristic as build_mating.py: larval classes are real
# rows but wrong life stage for an adult sleep circuit.
LARVAL_EXCLUDE = {"larval neuron", "larval CNS neuron",
                  "larval interneuron", "larval sensory neuron"}


# Duplicated-tier redirect (documented, same spirit as the mating walk's
# most-specific-member rule): "small field neuron" (FBbt_00003633) is the
# ontology parent of the hop-1 node "small field neuron of the central
# complex" (FBbt_00007514). Hop-2 edges to the parent are redirected to the
# already-present specific child instead of adding the parent as a node.
REDIRECT = {"FBbt_00003633": "FBbt_00007514"}


def pick_downstream_adult(up_query, up_id, up_label, k, log):
    picks = pick_downstream(up_query, up_id, up_label, k + 4, log)
    adult = [(dc, dcid, tw) for dc, dcid, tw in picks
             if dc not in LARVAL_EXCLUDE]
    for dc in [dc for dc, _, _ in picks if dc in LARVAL_EXCLUDE]:
        log.append(f"  (excluded larval class from adult walk: {dc})")
    return adult[:k]


# (fbid, label, weight) — weights from the real named query (limit=50)
HOP1 = [
    ("FBbt_00007514", "small field neuron of the central complex", 307745),
    ("FBbt_00049820", "fan-shaped body columnar neuron", 307486),
    ("FBbt_00003636", "adult fan-shaped body delta neuron", 217252),
    ("FBbt_00007523", "adult fan-shaped body horizontal delta neuron", 176242),
    ("FBbt_00049822", "fan-shaped body extrinsic columnar neuron", 90232),
    ("FBbt_00007536", "adult fan-shaped body layer 6 tangential neuron", 70267),
]

HOP0_ID = "FBbt_00049537"
HOP0_LABEL = "adult dorsal fan-shaped body tangential neuron"


def build():
    emit("== sleep ==")
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
            dcid = REDIRECT.get(dcid, dcid)
            if dcid not in nodes:
                nodes[dcid] = {"id": dcid, "name": dc, "type": dc, "hop": 2}
            if (nid, dcid) not in seen_edge:
                seen_edge.add((nid, dcid))
                edges.append({"pre": nid, "post": dcid, "weight": tw})

    graph = {
        "stimulus": "sleep",
        "source": "Virtual Fly Brain VFBquery HTTP API "
                  "(https://v3-cached.virtualflybrain.org/), FlyWire FAFB "
                  "v783 connectome; class-aggregated connectivity, edge "
                  "weight = total synapse count",
        "nodes": list(nodes.values()),
        "edges": edges,
        "behavior": {
            "text": "Sleep homeostasis: the dorsal fan-shaped body (dFB) "
                    "neurons accumulate sleep pressure during wakefulness "
                    "and discharge it during sleep, gating arousal through "
                    "fan-shaped body columnar, delta, and extrinsic output "
                    "circuits of the central complex.",
            "basis": "dFB as the sleep homeostat is textbook Drosophila "
                     "(Donlea et al 2011; Ueno et al 2012); edges below "
                     "are the resolved API walk, stated as measured "
                     "wiring",
        },
        "fly_narration": "Heavy — let go, drift down.",
        "honest_note": (
            "Hop-0 grouped /query_connectivity died server-side "
            "(IncompleteRead, ~1.4MB truncated); hop-1 weights come from "
            "the named DownstreamClassConnectivity query (50 rows). "
            "Hop-1 skips ontology parents, transmitter buckets, and self "
            "as documented in the builder docstring; duplicated tiers "
            "represented by most specific member. One hop-2 pick "
            "('small field neuron' FBbt_00003633) was the ontology parent "
            "of the hop-1 node 'small field neuron of the central "
            "complex' — its edges were redirected to the specific child "
            "rather than adding the parent as a node. The other hop-2 "
            "node ('adult central complex neuron' FBbt_00049819) is a "
            "broad parent bucket kept as the top non-duplicate candidate "
            "— real edges, broad label. CIRCUIT VS HOMEOSTAT: "
            "every edge here is REAL measured wiring of dFB's downstream "
            "command chain within the central complex. The HOMEOSTAT "
            "DYNAMICS — pressure accumulation rate, discharge kinetics, "
            "arousal gating — are the genuinely unmapped frontier; no API "
            "holds them, and nothing here models them."
        ),
        "hop0_ids": [HOP0_ID],
    }
    path = os.path.join(OUT, "sleep.json")
    with open(path, "w") as f:
        json.dump(graph, f, indent=1)
    emit(f" saved {path}: {len(nodes)} nodes, {len(edges)} edges")


if __name__ == "__main__":
    build()
