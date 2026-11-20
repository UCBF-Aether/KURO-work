#!/usr/bin/env python3
"""build_pheromone.py — walk the pheromone-sensing circuit downstream.
Every edge is a real VFBquery/FlyWire row.

Hop-0: FBbt_00067056 "adult olfactory receptor neuron Or47b" — the male
courtship pheromone receptor neuron (VA1v glomerulus ORN). Class-level
grouped /query_connectivity truncates server-side (IncompleteRead in
every form: label, id); the named DownstreamClassConnectivity query
returned 50 real rows (392 Or47b neurons, 260 connected).

Hop-1 selection (documented, not hidden): most specific member of each
ontology-duplicated tier (same convention as build_dh44.py /
build_mating.py):
- "adult antennal lobe projection neuron" over "antennal lobe projection
  neuron" (both tw=15332)
- "adult antennal lobe projection neuron to lateral horn" over "adult
  lateral horn input neuron" (both tw=13811)
- "adult antennal lobe local neuron" over "antennal lobe local neuron" /
  "local neuron" (all tw=6500)
- "fruitless expressing neuron" (tw=13133) is broad but kept deliberately:
  it is the pheromone -> courtship-system bridge and the documented
  convergence node with mating.json (P1's chain reaches the same class).

DEAD AVENUES (documented, not hidden):
- Or88a (FBbt_00067057, VA1d glomerulus ORN): class-level grouped
  (label + id), named DownstreamClassConnectivity, instance enumeration,
  and CATMAID annotation search ALL fail server-side (IncompleteRead /
  connection closed / 0 entities). The class index entry appears poisoned;
  nothing reachable exposes its connectivity.
- ppk23/ppk29 gustatory pheromone neurons: no adult FBbt neuron class
  exists (VFB search returns only the gene and L1EM larval instances).
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


# (fbid, label, weight) — weights from the real named query (limit 50)
HOP1 = [
    ("FBbt_00067123", "adult antennal lobe projection neuron", 15332),
    ("FBbt_00053398", "adult antennal lobe projection neuron to lateral horn", 13811),
    ("FBbt_00016687", "fruitless expressing neuron", 13133),
    ("FBbt_00007390", "adult antennal lobe local neuron", 6500),
    ("FBbt_00059245", "adult central brain intrinsic neuron", 6500),
    ("FBbt_00100660", "BAlc lineage neuron", 3839),
]

HOP0_ID = "FBbt_00067056"
HOP0_LABEL = "adult olfactory receptor neuron Or47b"


def build():
    emit("== pheromone ==")
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
        "stimulus": "pheromone",
        "source": "Virtual Fly Brain VFBquery HTTP API "
                  "(https://v3-cached.virtualflybrain.org/), FlyWire FAFB "
                  "v783 connectome; named DownstreamClassConnectivity "
                  "(/run_query) for hop 0->1, class-aggregated "
                  "/query_connectivity for hop 1->2; "
                  "edge weight = total synapse count",
        "nodes": list(nodes.values()),
        "edges": edges,
        "behavior": {
            "text": "Courtship and social smell: Or47b pheromone receptor "
                    "neurons (VA1v glomerulus) drive antennal lobe "
                    "projection neurons to the lateral horn and feed the "
                    "fruitless courtship system — the sensory front end of "
                    "the P1 mating-drive circuit.",
            "basis": "Or47b as the male courtship pheromone ORN projecting "
                     "via VA1v to higher olfactory centers is textbook "
                     "Drosophila (Dweck 2015; Kohl 2013); edges below are "
                     "the resolved API walk, stated as measured wiring",
        },
        "fly_narration": "Her scent — follow it.",
        "honest_note": (
            "Or47b grouped class-level queries truncate server-side in "
            "every form; hop 0->1 edges are from the named "
            "DownstreamClassConnectivity query (50 rows, real). Hop-1 "
            "takes the most specific member of each ontology-duplicated "
            "tier (documented above). 'fruitless expressing neuron' is "
            "broad but kept deliberately — it is the pheromone -> "
            "courtship bridge. CONVERGENCE WITH MATING: this chain MEETS "
            "the P1 chain (mating.json) at FBbt_00016687 'fruitless "
            "expressing neuron' — Or47b feeds it (tw=13133) and P1's "
            "aSP-a feeds it (tw=63139). The pheromone sense and the "
            "mating drive share a node: smell enters the courtship "
            "system here. Or88a (VA1d, FBbt_00067057) is unindexable in "
            "every query form tried (grouped label/id, named, instance "
            "enumeration, CATMAID annotation search) — server-side "
            "truncation, documented dead avenue, not faked. ppk23/ppk29 "
            "gustatory pheromone neurons have no adult FBbt class (VFB "
            "search returns only the gene + L1EM larval instances)."
        ),
        "hop0_ids": [HOP0_ID],
    }
    path = os.path.join(OUT, "pheromone.json")
    with open(path, "w") as f:
        json.dump(graph, f, indent=1)
    emit(f" saved {path}: {len(nodes)} nodes, {len(edges)} edges")


if __name__ == "__main__":
    build()
