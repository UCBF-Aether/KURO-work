#!/usr/bin/env python3
"""build_temperature.py — resolve the thermosensory channel from real API rows.

Hop 0: FBbt_00111336 "adult thermosensory neuron Ir21a VP1l" (cold-sensing;
class-level grouped queries die server-side, but the named
DownstreamClassConnectivity query works with retries). Hop 1: top-5
specific downstream classes (GENERIC blocklist skipped). Hop 2: standard
class walk, top-3 each. Output: subgraphs/temperature.json.

Every edge is a real VFBquery/FlyWire v783 row. Nothing invented.
"""
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import vfb
from build_graphs import GENERIC, pick_downstream

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                   "subgraphs", "temperature.json")

HOP0_ID = "FBbt_00111336"
HOP0_LABEL = "adult thermosensory neuron Ir21a VP1l"


def named_downstream(fbbt_id, limit=40, retries=8):
    """Named DownstreamClassConnectivity with generous retries (the grouped
    form dies server-side for this class; the named form truncates
    intermittently but succeeds on retry)."""
    res = vfb.api_get("/run_query",
                      {"id": fbbt_id, "query_type": "DownstreamClassConnectivity",
                       "limit": str(limit)},
                      retries=retries)
    return res.get("rows", [])


def main():
    log = []
    rows = named_downstream(HOP0_ID)
    log.append(f"hop0 {HOP0_LABEL}: {len(rows)} named rows")
    cands = []
    for r in rows:
        m = re.match(r"\[(.*?)\]\((FBbt_\d+)\)", r.get("downstream_class") or "")
        if not m:
            continue
        label, fid = m.group(1), m.group(2)
        if fid == HOP0_ID or label in GENERIC:
            continue
        tw = r.get("total_weight") or 0
        if tw > 0:
            cands.append((tw, label, fid))
    cands.sort(reverse=True)
    for tw, label, fid in cands[:8]:
        log.append(f"    cand: {label} [{fid}] tw={tw}")
    hop1 = [(label, fid, tw) for tw, label, fid in cands[:5]]

    nodes = {HOP0_ID: {"id": HOP0_ID, "name": HOP0_LABEL,
                       "type": HOP0_LABEL, "hop": 0}}
    edges = []
    seen_edge = set()
    hop2_ids = []
    for label, fid, tw in hop1:
        nodes[fid] = {"id": fid, "name": label, "type": label, "hop": 1}
        if (HOP0_ID, fid) not in seen_edge:
            seen_edge.add((HOP0_ID, fid))
            edges.append({"pre": HOP0_ID, "post": fid, "weight": tw})
        picks = pick_downstream(fid, fid, label, 3, log)
        for line in log:
            print(line)
        log = []
        for dc, dcid, dtw in picks:
            if dcid not in nodes:
                nodes[dcid] = {"id": dcid, "name": dc, "type": dc, "hop": 2}
                hop2_ids.append(dcid)
            if (fid, dcid) not in seen_edge:
                seen_edge.add((fid, dcid))
                edges.append({"pre": fid, "post": dcid, "weight": dtw})

    graph = {
        "stimulus": "temperature",
        "source": ("Virtual Fly Brain VFBquery HTTP API "
                   "(https://v3-cached.virtualflybrain.org/), FlyWire FAFB v783 "
                   "connectome. Hop 0->1: named DownstreamClassConnectivity rows "
                   "for FBbt_00111336 (adult thermosensory neuron Ir21a VP1l); "
                   "hop 1->2: class-aggregated /query_connectivity. "
                   "Edge weight = total synapse count."),
        "nodes": list(nodes.values()),
        "edges": edges,
        "behavior": {
            "text": ("Thermal sensing: aristal/antennal thermosensory neurons "
                     "(Ir21a cold cells) drive downstream circuits for thermal "
                     "preference and avoidance; the fly moves toward preferred "
                     "temperature."),
            "basis": ("textbook Drosophila thermosensation (aristal hot/cold "
                      "neurons -> posterior antennal lobe); stated as known "
                      "biology, resolved circuit below shows how far the API "
                      "could trace it"),
        },
        "fly_narration": "Cold on the arista \u2014 shift.",
        "hop0_ids": [HOP0_ID],
    }
    with open(OUT, "w") as f:
        json.dump(graph, f, indent=1)
    print(f"saved {OUT}: {len(nodes)} nodes, {len(edges)} edges")


if __name__ == "__main__":
    main()
