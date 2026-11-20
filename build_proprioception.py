#!/usr/bin/env python3
"""build_proprioception.py — FeCO proprioceptive feedback forward walk.

Hop 0: FBbt_00048051 "mechanosensory neuron of femoral chordotonal organ"
(FeCO neuron — leg proprioceptors sensing femur-tibia joint angle/movement).

Method: class-level grouped /query_connectivity truncates server-side for
this broad class (IncompleteRead ~800KB, 4 retries); the named
DownstreamClassConnectivity fallback (limit=50) returned 50 real rows.
Hop-1 = top-6 specific classes skipping ontology parents, transmitter
buckets, and Notch hemilineage developmental buckets (documented
heuristic, same spirit as the GENERIC blocklist in build_graphs.py).
Hop-2 = top-3 specific per hop-1 node via the fetch_rows fallback chain.

Dead avenues (documented, not hidden):
- FBbt_00048275 "femoral chordotonal club ascending neuron": 0 rows in
  named, grouped-ID, and grouped-label forms — honest dead class.
- UpstreamClassConnectivity of FBbt_00052033 "adult proprioceptive
  projection neuron" (= adult proprioceptive second-order neuron):
  0 rows — its inputs are unindexed.
- Per-pair FeCO -> FBbt_00052033: 0 pairs — the second-order
  proprioceptive neuron is NOT a direct FeCO target in the index.
- Per-pair FeCO -> "adult ascending neuron": response ~2.7MB, truncates
  server-side; the named grouped edge (tw=52445) stands instead.
"""

import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from build_graphs import fetch_rows, norm_row, GENERIC

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                   "subgraphs", "proprioception.json")
LOG = []

HOP0_ID = "FBbt_00048051"
HOP0_LABEL = "mechanosensory neuron of femoral chordotonal organ"

# extra skips for this walk: developmental lineage/hemilineage buckets
# (which aggregate many distinct adult cell types — same spirit as the
# GENERIC blocklist) + broad parents. NOTE: the first build used the
# strings "Notch ON/OFF hemilineage neuron" which did NOT match the
# actual row labels "... hemilineage secondary neuron", so the buckets
# slipped through and hop-2 degraded into bucket-hopping, including a
# biologically implausible pick (adult visual neuropil intrinsic neuron,
# synapses restricted to the optic lobes, as top downstream of a VNC
# hemilineage class — almost certainly a class-aggregation artifact).
# Rebuilt with exact strings; the artifact class is skipped with this
# documented reason.
SKIP = set(GENERIC) | {
    "secondary neuron", "adult secondary neuron",
    "Notch ON hemilineage neuron", "Notch OFF hemilineage neuron",
    "Notch ON hemilineage secondary neuron",
    "Notch OFF hemilineage secondary neuron",
    "Notch ON hemilineage primary neuron",
    "Notch OFF hemilineage primary neuron",
    "NB3-5 lineage neuron", "NB2-2 lineage neuron",
    "NB4-2 lineage neuron", "NB6-2 lineage neuron",
    "MNB lineage neuron",
    "lineage 10 secondary neuron", "lineage 9 secondary neuron",
    "lineage 0 secondary neuron", "lineage 19 secondary neuron",
    "hemilineage 9A secondary neuron", "hemilineage 0A secondary neuron",
    "hemilineage 19A secondary neuron",
    "thoracic neuron", "adult thoracic neuron",
    "adult VNC neuron", "VNC neuron",
    "sensory system neuron", "PNS neuron",
    "primary neuron", "primary interneuron",
    # aggregation artifact for this walk (see note above):
    "adult visual neuropil intrinsic neuron",
}


def pick(rows, prov, up_id, k, label):
    cands = []
    for r in rows:
        n = norm_row(r, prov)
        if not n:
            continue
        dc, dcid, tw = n
        if dcid == up_id:
            continue
        if dc in SKIP or tw <= 0:
            continue
        cands.append((tw, dc, dcid))
    cands.sort(reverse=True)
    LOG.append(f"{label}: {len(rows)} raw rows [{prov}], "
               f"{len(cands)} specific candidates")
    for tw, dc, dcid in cands[:k + 3]:
        LOG.append(f"    cand: {dc} [{dcid}] tw={tw}")
    return [(dc, dcid, tw) for tw, dc, dcid in cands[:k]]


def main():
    rows, prov = fetch_rows(HOP0_ID, HOP0_ID, HOP0_LABEL, LOG)
    assert rows, "hop-0 fetch failed entirely"
    hop1 = pick(rows, prov, HOP0_ID, 6, f"hop1 of {HOP0_LABEL}")

    nodes = {HOP0_ID: {"id": HOP0_ID, "name": HOP0_LABEL,
                       "type": HOP0_LABEL, "hop": 0}}
    edges = []
    seen_edge = set()

    def add_edge(pre, post, w):
        if (pre, post) not in seen_edge and w > 0:
            seen_edge.add((pre, post))
            edges.append({"pre": pre, "post": post, "weight": w})

    for dc, dcid, tw in hop1:
        nodes[dcid] = {"id": dcid, "name": dc, "type": dc, "hop": 1}
        add_edge(HOP0_ID, dcid, tw)

    for dc, dcid, tw in hop1:
        rows2, prov2 = fetch_rows(dcid, dcid, dc, LOG)
        if not rows2:
            LOG.append(f"  {dc}: honest hop-1 terminal")
            continue
        for dc2, dcid2, tw2 in pick(rows2, prov2, dcid, 3, f"hop2 of {dc}"):
            if dcid2 == HOP0_ID:
                continue
            if dcid2 not in nodes:
                nodes[dcid2] = {"id": dcid2, "name": dc2,
                                "type": dc2, "hop": 2}
            add_edge(dcid, dcid2, tw2)

    g = {
        "stimulus": "leg proprioception (femoral chordotonal organ — "
                    "femur-tibia joint angle and movement)",
        "source": "Virtual Fly Brain VFBquery HTTP API, FlyWire v783. "
                  "Hop 0->1: named DownstreamClassConnectivity (grouped "
                  "query truncates server-side for this broad class). "
                  "Hop 1->2: fetch_rows fallback chain (grouped -> named).",
        "nodes": list(nodes.values()),
        "edges": edges,
        "behavior": {
            "text": "Proprioceptive feedback: FeCO club/claw/hook neurons "
                    "encode femur-tibia joint angle, movement direction and "
                    "vibration; they terminate in the thoracic VNC ganglia "
                    "and ascend to the brain. Known biology (textbook).",
            "basis": "Mamiya et al. FeCO functional types (club=position, "
                     "claw=movement direction, hook=vibration); stated as "
                     "known biology, NOT as a simulation result.",
        },
        "fly_narration": "The leg knows where it is.",
        "honest_note": (
            "REAL measured FlyWire v783 rows throughout. Hop-1 skips "
            "ontology parents, transmitter buckets, and Notch hemilineage "
            "developmental buckets (documented heuristic). Dead avenues: "
            "FBbt_00048275 (club ascending neuron) 0 rows all forms; "
            "upstream of adult proprioceptive projection neuron "
            "FBbt_00052033 0 rows; per-pair FeCO->FBbt_00052033 0 pairs "
            "(the second-order proprioceptive neuron is not a direct "
            "FeCO target in the index). The functional club/claw/hook "
            "subtypes (Mamiya et al.) are not separately indexed as "
            "connectivity classes — this walk is at the whole-FeCO level."
        ),
    }
    with open(OUT, "w") as f:
        json.dump(g, f, indent=1)
    print(f"wrote {OUT}: {len(nodes)} nodes, {len(edges)} edges")
    for line in LOG:
        print(line)


if __name__ == "__main__":
    main()
