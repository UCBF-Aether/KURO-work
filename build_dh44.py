#!/usr/bin/env python3
"""build_dh44.py — walk the true interoceptive drive circuits: DH44 hunger
neurons and IPC satiety neurons. Every edge is a real VFBquery/FlyWire row.

Hop-1 selection note (documented, not hidden): DH44's and IPC's top weight
tier is an ontology-duplicated synapse set (identical total_weight across
many ancestor labels — one underlying connectivity counted under 11 labels
for DH44, 14 for IPC). Taking top-k blindly would fill hop 1 with arbitrary
ancestors. Instead hop 1 takes the most specific member of the duplicated
tier (ring gland projection = the hormonal output) plus the following
weight-ranked specific classes. All weights below are real API values.
"""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from build_graphs import pick_downstream, GENERIC

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "subgraphs")
LOGF = os.path.join(os.path.dirname(OUT), "build.log")


def emit(line):
    print(line, flush=True)
    with open(LOGF, "a") as f:
        f.write(line + "\n")


# Documented heuristic (same spirit as the GENERIC blocklist): larval classes
# are real API rows but belong to a different life stage; this is an adult
# drive circuit, so they are excluded from the walk and noted, not hidden.
LARVAL_EXCLUDE = {"larval neuron", "larval CNS neuron",
                  "larval interneuron", "larval sensory neuron"}


def pick_downstream_adult(up_query, up_id, up_label, k, log):
    picks = pick_downstream(up_query, up_id, up_label, k + 4, log)
    adult = [(dc, dcid, tw) for dc, dcid, tw in picks
             if dc not in LARVAL_EXCLUDE]
    dropped = [dc for dc, _, _ in picks if dc in LARVAL_EXCLUDE]
    for dc in dropped:
        log.append(f"  (excluded larval class from adult walk: {dc})")
    return adult[:k]


CONFIGS = {
    "dh44": {
        "hop0": ("FBbt_00047132", "DH44 neuron of pars intercerebralis"),
        # (fbid, label, weight) — weight from the real grouped query
        "hop1": [
            ("FBbt_00059246", "adult ring gland projection neuron", 252),
            ("FBbt_00052149", "gut-innervating neuron", 235),
            ("FBbt_00001972", "subesophageal zone neuron", 72),
            ("FBbt_00052032", "gnathal ganglion neuron", 58),
            ("FBbt_00058024", "adult Ms cell of pars intercerebralis", 17),
            ("FBbt_00005133", "serotonergic neuron", 13),
        ],
        "behavior": {
            "text": "Hunger drive: DH44 neurosecretory cells of the pars "
                    "intercerebralis signal nutrient need — hormonal output "
                    "via the ring gland, gut motility modulation, and direct "
                    "drive onto the SEZ feeding center shared with the taste "
                    "circuits.",
            "basis": "DH44 as hunger-promoting PI neurosecretory cells is "
                     "textbook Drosophila physiology; edges below are the "
                     "resolved API walk, stated as measured wiring",
        },
        "fly_narration": "Empty — seek.",
        "honest_note": (
            "Hop-1: the tw=252 tier is an ontology-duplicated synapse set "
            "(11 ancestor labels, one underlying connectivity); represented "
            "by its most specific member (ring gland projection). DH44->SEZ "
            "(FBbt_00001972) is the SAME node class anchoring the "
            "sweet/water/bitter taste circuits — drive and taste converge "
            "on shared wiring. Larval classes excluded from this adult "
            "walk as a documented heuristic (same spirit as the GENERIC "
            "blocklist)."
        ),
    },
    "ipc": {
        "hop0": ("FBbt_00110107", "adult insulin producing cell of brain"),
        "hop1": [
            ("FBbt_00059246", "adult ring gland projection neuron", 206),
            ("FBbt_00052149", "gut-innervating neuron", 206),
            ("FBbt_00001972", "subesophageal zone neuron", 7),
            ("FBbt_20004678", "adult CB0991 neuron", 7),
            ("FBbt_00050123", "adult DM2 lineage neuron", 4),
            ("FBbt_00052205", "DPMpm1 lineage neuron", 4),
        ],
        "behavior": {
            "text": "Satiety signaling: adult insulin-producing cells of the "
                    "pars intercerebralis counter hunger — same output "
                    "architecture as DH44 (ring gland, gut, SEZ), the "
                    "opposing arm of the drive.",
            "basis": "IPCs/DILPs as satiety signals opposing DH44 hunger "
                     "drive is textbook Drosophila physiology; edges below "
                     "are the resolved API walk",
        },
        "fly_narration": "Enough — rest.",
        "honest_note": (
            "Grouped /query_connectivity truncates for this class "
            "(IncompleteRead); hop-1 comes from the named "
            "DownstreamClassConnectivity fallback (40 rows). The tw=206 "
            "tier is ontology-duplicated like DH44's; represented by most "
            "specific members. IPC->SEZ (FBbt_00001972) converges on the "
            "same node as DH44 and the taste circuits. Larval classes "
            "excluded from this adult walk as a documented heuristic."
        ),
    },
}


def build(name, cfg):
    emit(f"== {name} ==")
    hop0_id, hop0_label = cfg["hop0"]
    nodes = {hop0_id: {"id": hop0_id, "name": hop0_label,
                       "type": hop0_label, "hop": 0}}
    edges = []
    seen_edge = set()
    frontier = []
    for nid, label, tw in cfg["hop1"]:
        nodes[nid] = {"id": nid, "name": label, "type": label, "hop": 1}
        if (hop0_id, nid) not in seen_edge:
            seen_edge.add((hop0_id, nid))
            edges.append({"pre": hop0_id, "post": nid, "weight": tw})
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
        "stimulus": name,
        "source": "Virtual Fly Brain VFBquery HTTP API "
                  "(https://v3-cached.virtualflybrain.org/), FlyWire FAFB "
                  "v783 connectome; class-aggregated /query_connectivity "
                  "(IPC via named DownstreamClassConnectivity fallback); "
                  "edge weight = total synapse count",
        "nodes": list(nodes.values()),
        "edges": edges,
        "behavior": cfg["behavior"],
        "fly_narration": cfg["fly_narration"],
        "honest_note": cfg["honest_note"],
        "hop0_ids": [hop0_id],
    }
    path = os.path.join(OUT, f"{name}.json")
    with open(path, "w") as f:
        json.dump(graph, f, indent=1)
    emit(f" saved {path}: {len(nodes)} nodes, {len(edges)} edges")


if __name__ == "__main__":
    which = sys.argv[1:] or list(CONFIGS)
    for name in which:
        try:
            build(name, CONFIGS[name])
        except Exception as e:
            emit(f"== {name} == FAILED: {e}")
