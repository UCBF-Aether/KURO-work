#!/usr/bin/env python3
"""retry_color_hop2.py — retry the color-vision hop-2 walk now that the API recovered.

Targets: the 8 hop-1 nodes in subgraphs/color.json that have no hop-2 edges:
  - 3 broad classes previously skipped: 59247, 47096, 53385
  - Dm8 (00013774) downstream retry
  - 4 nodes that GAPped in the first pass: 00005127, 00003767, 00053639, 00110136

Method: standard fallback chain (grouped id -> grouped label -> named
DownstreamClassConnectivity), top-3 specific per node, larval exclusion,
skip candidates already in the graph / generic tiers / self-loops.
Appends to the file; never rewrites history.
"""
import json
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from build_graphs import pick_downstream
from build_color import pick_downstream_adult

HERE = os.path.dirname(os.path.abspath(__file__))
PATH = os.path.join(HERE, "subgraphs", "color.json")
LOGF = os.path.join(HERE, "build.log")

RETRY_TARGETS = [
    ("FBbt_00059247", "adult visual neuropil intrinsic neuron"),
    ("FBbt_00047096", "secondary neuron"),
    ("FBbt_00053385", "medulla intrinsic neuron"),
    ("FBbt_00005127", "optic lobe amacrine neuron"),
    ("FBbt_00003767", "distal medullary amacrine neuron"),
    ("FBbt_00013774", "distal medullary amacrine neuron Dm8"),
    ("FBbt_00053639", "distal medullary amacrine neuron Dm8b"),
    ("FBbt_00110136", "optic lobe narrow field columnar neuron"),
]


def emit(line):
    print(line, flush=True)
    with open(LOGF, "a") as f:
        f.write(line + "\n")


def main():
    with open(PATH) as f:
        g = json.load(f)
    nodes = {n["id"]: n for n in g["nodes"]}
    edges = g["edges"]
    seen_edge = {(e["pre"], e["post"]) for e in edges}
    results = {}

    for nid, label in RETRY_TARGETS:
        emit(f"== color hop-2 retry: {label} ({nid}) ==")
        log = []
        picks = pick_downstream_adult(nid, nid, label, 3, log)
        for line in log:
            emit(line)
        kept = []
        for dc, dcid, tw in picks:
            if dcid in nodes:
                emit(f"  (skip {dc} — already in graph)")
                continue
            kept.append((dc, dcid, tw))
        if not kept:
            emit(f"  (no new specific downstream for {label} — stays terminal)")
            results[nid] = "terminal"
            continue
        for dc, dcid, tw in kept:
            nodes[dcid] = {"id": dcid, "name": dc, "type": dc, "hop": 2}
            if (nid, dcid) not in seen_edge:
                seen_edge.add((nid, dcid))
                edges.append({"pre": nid, "post": dcid, "weight": tw})
                emit(f"  + {label} -> {dc} [{dcid}] tw={tw}")
        results[nid] = f"{len(kept)} new hop-2 nodes"
        time.sleep(2.5)  # politeness between nodes

    # update honest_note with dated retry record (append, don't rewrite)
    note = g.get("honest_note", "")
    landed = [f"{nid} ({r})" for nid, r in results.items() if r != "terminal"]
    stuck = [nid for nid, r in results.items() if r == "terminal"]
    retry_note = (
        "\n\nHOP-2 RETRY 2026-10-15 (API recovered): retried the 8 hop-1 nodes "
        "that had no hop-2 edges. "
        + ("Landed: " + "; ".join(landed) + ". " if landed else "")
        + ("Still terminal (all query forms failed or no specific downstream): "
           + ", ".join(stuck) + ". " if stuck else "")
        + "Dm8's own downstream was retried with the full fallback chain."
    )
    g["honest_note"] = note + retry_note
    g["nodes"] = list(nodes.values())
    g["edges"] = edges
    with open(PATH, "w") as f:
        json.dump(g, f, indent=2)
    emit(f"wrote {PATH}: {len(nodes)} nodes, {len(edges)} edges")
    emit("RETRY SUMMARY: " + "; ".join(f"{k}={v}" for k, v in results.items()))


if __name__ == "__main__":
    main()
