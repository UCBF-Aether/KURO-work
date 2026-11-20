#!/usr/bin/env python3
"""build_compass.py — walk the E-PG heading-direction circuit downstream.
Every edge is a real VFBquery/FlyWire row.

Hop-0: FBbt_00047030 "E-PG neuron (adult ellipsoid body-protocerebral
bridge 1 glomerulus-dorsal/ventral gall neuron)" — the heading-direction
ring of the central complex.

Query path: class-level grouped /query_connectivity TRUNCATED server-side
(IncompleteRead after 4 retries — same failure mode as the thermo classes);
the named DownstreamClassConnectivity fallback returned 50 real rows
(documented playbook path). No instance-level attack, no motor-backward,
no BANC needed.

Hop-1 selection (documented, not hidden): top-6 specific classes by total
synapse weight; duplicated ancestor/child tiers are represented by their
most specific member (e.g. 'small field neuron of the central complex'
over 'small field neuron'; 'intrinsic neuron of the central complex' over
'adult central brain intrinsic neuron'; 'adult EBa1 lineage neuron' over
'DALv2 lineage neuron'). Generic ontology buckets skipped in the spirit
of the GENERIC blocklist: neuron/adult neuron/CNS/adult CNS/interneuron/
adult interneuron/input-output/transmitter classes, 'adult central complex
neuron' (tw=194278, parent bucket of the specific central-complex picks),
'supraesophageal ganglion neuron'. E-PG->E-PG itself (tw=14614) skipped
per the no-self-loop convention — but it is REAL recurrence and is
recorded in the honest_note, not hidden.

Hop-2: top-3 specific per hop-1 node via pick_downstream (grouped first,
named fallback — same path as mating/thermo).
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


HOP0_ID = "FBbt_00047030"
HOP0_LABEL = ("E-PG neuron (adult ellipsoid body-protocerebral bridge "
              "1 glomerulus-dorsal/ventral gall neuron)")

# (fbid, label, weight) — weights from the real named DownstreamClassConnectivity query
HOP1 = [
    ("FBbt_00007514", "small field neuron of the central complex", 99914),
    ("FBbt_00007515", "large field neuron of the central complex", 91386),
    ("FBbt_00053387", "intrinsic neuron of the central complex", 70552),
    ("FBbt_00003649", "adult ellipsoid body ring neuron", 54362),
    ("FBbt_00003654", "adult ellipsoid body extrinsic ring neuron", 36116),
    ("FBbt_00050171", "adult PBp1 lineage neuron", 31578),
]


def build():
    emit("== compass ==")
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
        "stimulus": "compass",
        "source": ("Virtual Fly Brain VFBquery HTTP API "
                   "(https://v3-cached.virtualflybrain.org/), FlyWire FAFB v783 "
                   "connectome; class-aggregated connectivity (named "
                   "DownstreamClassConnectivity fallback — grouped query "
                   "truncated server-side), edge weight = total synapse count"),
        "behavior": {
            "text": ("Heading direction: E-PG ring neurons carry the fly's "
                     "internal compass — an activity bump that tracks heading "
                     "around the ellipsoid body, feeding ring neurons, "
                     "protocerebral-bridge intrinsics, and fan-shaped-body "
                     "steering outputs."),
            "basis": ("E-PG as the heading-direction ring is textbook "
                      "Drosophila (Seelig & Jayaraman 2015; Green et al 2017); "
                      "edges below are the resolved API walk, stated as "
                      "measured wiring"),
        },
        "fly_narration": "North lives here — hold it, turn it.",
        "honest_note": (
            "Hop-1 takes the top-6 specific classes by synapse weight; "
            "duplicated ancestor/child tiers are represented by their most "
            "specific member; generic ontology buckets skipped (documented "
            "in build_compass.py). E-PG->E-PG itself (tw=14614) is REAL "
            "recurrence, skipped per the no-self-loop convention, recorded "
            "here not hidden. Real below-cutoff partners worth noting "
            "(same pattern as pIP10 in mating / giant fiber in looming): "
            "Delta7 'adult intrinsic protocerebral bridge 18 "
            "glomeruli-delta7 neuron' (tw=30232, the ring's global "
            "inhibition), PEN 'adult protocerebral bridge 1 "
            "glomerulus-ellipsoid body tile-nodulus 1 neuron' (tw=26851), "
            "PFN 'adult protocerebral bridge 1 glomerulus-fan-shaped "
            "body-nodulus neuron' (tw=12306), PFL 'adult protocerebral "
            "bridge 1 glomerulus-fan-shaped body-lateral accessory lobe "
            "neuron' (tw=12066), 'adult ellipsoid body R-neuron' "
            "(tw=18246). CIRCUIT VS DYNAMICS: every edge is REAL measured "
            "wiring of E-PG's downstream chain. The RING-ATTRACTOR DYNAMICS "
            "— how the activity bump moves, holds, and updates heading — "
            "are the genuinely unmapped frontier; no API holds them and "
            "this graph models none of them."),
        "hop0_ids": [HOP0_ID],
        "nodes": list(nodes.values()),
        "edges": edges,
    }
    path = os.path.join(OUT, "compass.json")
    with open(path, "w") as f:
        json.dump(graph, f, indent=2)
    emit(f"wrote {path}: {len(nodes)} nodes, {len(edges)} edges")


if __name__ == "__main__":
    build()
