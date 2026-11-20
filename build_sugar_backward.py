#!/usr/bin/env python3
"""build_sugar_backward.py — trace UPSTREAM from proboscis motor neurons to
recover real edges for the sugar pathway's motor end.

The sweet-GRN forward walk is empty (see GAPS.md §1). This builds the
complementary motor-backward chain: proboscis MN <- premotor <- central.
All edges are real /run_query UpstreamClassConnectivity rows.
The sensory->SEZ link remains the documented missing piece.
"""

import json
import os
import re
from vfb import api_get
from build_graphs import GENERIC, emit, LOGF

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "subgraphs")


def parse_upstream(row):
    m = re.match(r"\[(.*?)\]\((FBbt_\d+)\)", row.get("upstream_class") or "")
    if not m:
        return None
    return m.group(1), m.group(2), (row.get("total_weight") or 0)


def upstream_of(fbbt_id, k, log):
    res = api_get("/run_query",
                  {"id": fbbt_id, "query_type": "UpstreamClassConnectivity",
                   "limit": "40"}, retries=3)
    rows = res.get("rows", [])
    cands = []
    for r in rows:
        p = parse_upstream(r)
        if not p:
            continue
        label, fid, tw = p
        if fid == fbbt_id or label in GENERIC or tw <= 0:
            continue
        cands.append((tw, label, fid))
    cands.sort(reverse=True)
    log.append(f"  upstream of {fbbt_id}: {len(rows)} rows, "
               f"{len(cands)} specific")
    for tw, label, fid in cands[:k + 2]:
        log.append(f"      up: {label} [{fid}] tw={tw}")
    return [(label, fid, tw) for tw, label, fid in cands[:k]]


def main():
    emit("== sugar motor-backward ==")
    # Start from two proboscis motor neuron classes (mn1 and mn9-like).
    # mn1 = proboscis muscle 1 motor neuron.
    log = []
    nodes = {}
    edges = []
    seen_edge = set()

    def add_node(nid, label, layer):
        if nid not in nodes:
            nodes[nid] = {"id": nid, "name": label, "type": label,
                          "hop": layer}

    # layer -1: direct upstream of proboscis MNs (the motor end)
    motor_ids = [("FBbt_00051181", "proboscis motor neuron mn1")]
    for mid, mlabel in motor_ids:
        add_node(mid, mlabel, 0)
    frontier = [(mid, mlabel) for mid, mlabel in motor_ids]

    # backward hop 1: top 5 upstream of MNs
    b1 = []
    for mid, mlabel in frontier:
        try:
            ups = upstream_of(mid, 5, log)
        except Exception as e:
            log.append(f"  !! upstream query failed for {mlabel}: {e}")
            continue
        for line in log:
            emit(line)
        log = []
        for ulabel, ufid, tw in ups:
            add_node(ufid, ulabel, -1)
            if (ufid, mid) not in seen_edge:
                seen_edge.add((ufid, mid))
                edges.append({"pre": ufid, "post": mid, "weight": tw})
            b1.append((ufid, ulabel))

    # backward hop 2: top 3 upstream of each hop-1 node
    seen = set()
    b1 = [(i, l) for i, l in b1 if not (i in seen or seen.add(i))]
    emit(f" backward hop 2: expanding {len(b1)} nodes, top-3 each")
    for ufid, ulabel in b1:
        try:
            ups = upstream_of(ufid, 3, log)
        except Exception as e:
            log.append(f"  !! upstream query failed for {ulabel}: {e}")
            for line in log:
                emit(line)
            log = []
            continue
        for line in log:
            emit(line)
        log = []
        if not ups:
            emit(f"  (no specific upstream for {ulabel} — GAP)")
        for ul2, f2, tw in ups:
            add_node(f2, ul2, -2)
            if (f2, ufid) not in seen_edge:
                seen_edge.add((f2, ufid))
                edges.append({"pre": f2, "post": ufid, "weight": tw})

    backward = {
        "direction": "motor-backward",
        "note": "Traced UPSTREAM from proboscis motor neurons via real "
                "UpstreamClassConnectivity rows. Hop 0 = proboscis MN (motor "
                "end); hop -1/-2 = progressively further upstream. The "
                "sweet-GRN -> SEZ sensory link is NOT in this chain (see "
                "GAPS.md §1); this chain covers the motor half of the sugar "
                "pathway.",
        "nodes": list(nodes.values()),
        "edges": edges,
    }
    path = os.path.join(OUT, "sugar_backward.json")
    with open(path, "w") as f:
        json.dump(backward, f, indent=1)
    emit(f" saved {path}: {len(nodes)} nodes, {len(edges)} edges")


if __name__ == "__main__":
    main()
