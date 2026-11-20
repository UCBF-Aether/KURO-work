#!/usr/bin/env python3
"""build_color.py — walk the color-vision circuit downstream.
Every edge is a real VFBquery/FlyWire v783 row.

Hop-0: R7 (FBbt_00004225 "photoreceptor cell R7") and R8 (FBbt_00004227
"photoreceptor cell R8") — the two chromatic photoreceptor classes, run
as parallel sources (same hot/cold precedent as temperature.json).

Query path: grouped /query_connectivity died server-side for BOTH
classes via ID form and label form (same failure mode as CO2,
temperature-hot, mating hop-2). The named DownstreamClassConnectivity
fallback worked for both: R7 -> 40 rows (18 specific), R8 -> 566 rows
(445 specific). No instance-level attack, no motor-backward, no BANC.

R8 SUBTYPE-ROW DEDUP (documented, not hidden): R8's named rows split
the class into subtype rows — "photoreceptor cell R8" (main),
"photoreceptor cell R8 of yellow ommatidium", "...pale ommatidium",
"dorsal margin photoreceptor cell R8" — each reporting the same
downstream classes with different weights (e.g. 59247 appears 4x:
235944 / 88452 / 75270 / 12407). The main-class row ("photoreceptor
cell R8", tw=235944 for 59247) is the class-level aggregate and is
what this graph uses; subtype rows are NOT summed (that would
double-count against the class aggregate). R7's rows had no subtype
split (single upstream class).

Hop-1 dedup (documented): the 49542/49540 pair ("Notch OFF hemilineage
secondary neuron" / "Notch OFF hemilineage neuron", identical weights)
is an ancestor/child duplicated tier — kept the most specific, 49542
(mating-walk precedent).

THE COLOR PATH: R7 -> Dm8 (FBbt_00013774, tw=38836) plus Dm8a/Dm8b/Dm9
is the textbook chromatic opponency circuit, and it is present in the
real rows — not assumed.
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
                  "larval interneuron", "larval sensory neuron",
                  "larval olfactory system neuron"}


def pick_downstream_adult(up_query, up_id, up_label, k, log):
    picks = pick_downstream(up_query, up_id, up_label, k + 4, log)
    adult = [(dc, dcid, tw) for dc, dcid, tw in picks
             if dc not in LARVAL_EXCLUDE]
    for dc in [dc for dc, _, _ in picks if dc in LARVAL_EXCLUDE]:
        log.append(f"  (excluded larval class from adult walk: {dc})")
    return adult[:k]


R7 = "FBbt_00004225"
R8 = "FBbt_00004227"

# (fbid, label, r7_weight or None, r8_weight or None)
# weights = total synapse count from the real named-query rows
HOP1 = [
    ("FBbt_00059247", "adult visual neuropil intrinsic neuron", 91690, 235944),
    ("FBbt_00047096", "secondary neuron", 73349, 202161),
    ("FBbt_00053385", "medulla intrinsic neuron", 71918, 169659),
    ("FBbt_00049542", "Notch OFF hemilineage secondary neuron", 66607, 156700),
    ("FBbt_00005127", "optic lobe amacrine neuron", 66169, 89291),
    ("FBbt_00003767", "distal medullary amacrine neuron", 66110, 89291),
    ("FBbt_00013774", "distal medullary amacrine neuron Dm8", 38836, None),
    ("FBbt_00053638", "distal medullary amacrine neuron Dm8a", 19865, None),
    ("FBbt_00053639", "distal medullary amacrine neuron Dm8b", 18537, None),
    ("FBbt_00111271", "distal medullary amacrine neuron Dm9", 15733, None),
    ("FBbt_00110136", "optic lobe narrow field columnar neuron", None, 131323),
    ("FBbt_00007368", "aminergic neuron", None, 82066),
]


# Broad classes whose downstream is unqueryable (documented GAPs, not
# hidden): grouped /query_connectivity returns 0 rows via the label form
# (59247, 47096) or hangs through all retries (53385); the named
# DownstreamClassConnectivity fallback also hangs for 53385.
HOP2_SKIP = {"FBbt_00059247", "FBbt_00047096", "FBbt_00053385"}


def build():
    emit("== color ==")
    nodes = {
        R7: {"id": R7, "name": "photoreceptor cell R7",
             "type": "photoreceptor cell R7", "hop": 0},
        R8: {"id": R8, "name": "photoreceptor cell R8",
             "type": "photoreceptor cell R8", "hop": 0},
    }
    edges = []
    seen_edge = set()
    frontier = []
    for nid, label, w7, w8 in HOP1:
        nodes[nid] = {"id": nid, "name": label, "type": label, "hop": 1}
        for src, w in ((R7, w7), (R8, w8)):
            if w and (src, nid) not in seen_edge:
                seen_edge.add((src, nid))
                edges.append({"pre": src, "post": nid, "weight": w})
        frontier.append((nid, nid, label))

    for q, nid, label in frontier:
        if nid in HOP2_SKIP:
            emit(f"  (skipping hop-2 for {label} — broad class: grouped "
                 f"returns 0 rows or hangs, named hangs; honest GAP)")
            continue
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
        "stimulus": "color",
        "source": "Virtual Fly Brain VFBquery HTTP API "
                  "(https://v3-cached.virtualflybrain.org/), FlyWire FAFB "
                  "v783 connectome; named DownstreamClassConnectivity "
                  "(grouped /query_connectivity died server-side for both "
                  "R7 and R8, ID and label forms); edge weight = total "
                  "synapse count",
        "nodes": list(nodes.values()),
        "edges": edges,
        "honest_note": (
            "R7 and R8 run as parallel hop-0 sources (hot/cold precedent). "
            "The textbook R7->Dm8 chromatic pathway is PRESENT in the real "
            "rows (Dm8 tw=38836, Dm8a/Dm8b/Dm9 also land). R8's named rows "
            "split into subtype rows (yellow/pale/dorsal-margin); only the "
            "main-class aggregate row is used per downstream class — "
            "subtype rows are not summed (would double-count). The "
            "49542/49540 duplicated tier is represented by its most "
            "specific member (49542). Dm8's own downstream failed ALL "
            "query forms (grouped x2, named x1) — honest hop-1 terminal, "
            "not faked. Hop-2 nodes that dilute below the model cascade's "
            "0.15 threshold are real edges with toy-quiet readouts."
        ),
        "behavior": {
            "text": "Color vision: R7/R8 chromatic photoreceptors drive "
                    "medulla interneurons — including the Dm8 amacrine "
                    "family that computes chromatic opponency — fanning "
                    "into columnar and intrinsic visual pathways toward "
                    "the central brain.",
            "basis": "R7/R8 as the chromatic photoreceptors and Dm8 as "
                     "their color-opponency target is textbook Drosophila "
                     "(Heath et al; Dm8 pools R7 input for UV-vs-visible "
                     "comparisons). All edges here are measured FlyWire "
                     "synapse counts.",
        },
    }
    path = os.path.join(OUT, "color.json")
    with open(path, "w") as f:
        json.dump(graph, f, indent=2)
    emit(f"wrote {path}: {len(nodes)} nodes, {len(edges)} edges")


if __name__ == "__main__":
    build()
