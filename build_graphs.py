#!/usr/bin/env python3
"""build_graphs.py — walk 2-4 hops downstream from each sensory class using
ONLY real VFBquery/FlyWire connectivity. Saves one JSON subgraph per stimulus.

Selection rule: at each hop, rank candidate downstream classes by total_weight
(summed synapse count) and follow the strongest; skip generic ontology
superclasses (documented blocklist below) and the query class itself.
Every kept edge is a real API row. Nothing is invented.
"""

import json
import os
from vfb import downstream_classes

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "subgraphs")
os.makedirs(OUT, exist_ok=True)

# Generic ontology superclasses: excluded from the walk because they aggregate
# thousands of weak pairs and would drown out specific circuit classes.
# (Documented heuristic — the underlying edges are still real; we simply
# choose not to branch into the generic buckets.)
GENERIC = {
    "neuron", "adult neuron",
    "CNS neuron", "adult CNS neuron",
    "interneuron", "adult interneuron",
    "primary neuron", "primary interneuron",
    "sensory neuron", "adult sensory neuron", "sensory system neuron",
    "projection neuron", "input/output neuron",
    "cholinergic neuron", "adult cholinergic neuron",
    "GABAergic neuron", "adult GABAergic neuron",
    "glutamatergic neuron", "adult glutamatergic neuron",
    "visual system neuron", "visual projection neuron",
    "adult visual projection neuron",
    "optic lobe neuron", "adult optic lobe neuron",
    "optic lobe columnar neuron", "adult optic lobe columnar neuron",
    "optic lobe intrinsic neuron", "adult optic lobe intrinsic neuron",
    "optic lobe intrinsic columnar neuron",
    "optic lobe tangential neuron",
    "transmedullary neuron", "transmedullary Y neuron",
    "lobula complex columnar neuron", "lobula columnar neuron",
    "lobula plate-lobula columnar neuron LPLC",  # parent incl. LPLC2 itself
    "supraesophageal ganglion neuron",
}

STIMULI = {
    "sugar": {
        # "q" = the upstream_type string sent to the API (label or FBbt id).
        # Sweet-GRN connectivity is not indexed (see GAPS.md): 0 rows.
        "hop0": [("FBbt_00049614", "sweet-sensing gustatory receptor neuron",
                  "FBbt_00049614")],
        "branch": [5, 3],
        "behavior": {
            "text": "Proboscis extension response: the fly extends its proboscis "
                    "toward the sweet stimulus to feed.",
            "basis": "textbook Drosophila PER (sweet GRNs -> SEZ -> proboscis "
                     "motor neurons); stated as known biology, resolved circuit "
                     "below shows how far the API could trace it",
        },
        "fly_narration": "Sweet on the tongue \u2014 reach out.",
    },
    "looming": {
        # NOTE: FBbt_00111763 as upstream_type consistently truncates the
        # response stream; the label "LPLC2" resolves to the same class
        # (357 rows, verified) and is used instead.
        "hop0": [("FBbt_00111763",
                  "lobula plate-lobula columnar neuron LPLC2",
                  "LPLC2")],
        "branch": [6, 3],
        "behavior": {
            "text": "Escape: visual looming drives the giant-fiber system and "
                    "descending neurons, triggering jump-and-flight takeoff.",
            "basis": "textbook Drosophila escape circuit (LPLC2/LC4 -> giant "
                     "fiber -> jump/flight motor neurons)",
        },
        "fly_narration": "Shadow swelling \u2014 MOVE.",
    },
    "rotten": {
        "hop0": [("FBbt_00067063",
                  "adult olfactory receptor neuron Or56a",
                  "FBbt_00067063")],
        "branch": [6, 3],
        "behavior": {
            "text": "Olfactory aversion: the fly turns and moves away from the "
                    "geosmin (mold/rot) odor source.",
            "basis": "textbook Or56a (geosmin) aversive olfactory pathway: "
                     "ORN -> antennal lobe -> lateral horn / mushroom body",
        },
        "fly_narration": "Rot in the air \u2014 turn away.",
    },
    "touch": {
        "hop0": [("FBbt_00100000", "Johnston organ neuron",
                  "FBbt_00100000")],
        "branch": [6, 3],
        "behavior": {
            "text": "Startle: antennal mechanosensory input drives central "
                    "interneurons and descending neurons; the fly braces, "
                    "grooms, or initiates escape.",
            "basis": "textbook Johnston's organ -> AMMC/AVLP -> descending "
                     "pathway",
        },
        "fly_narration": "The world jolts \u2014 brace.",
    },
}

def fetch_rows(up_query, up_id, up_label, log):
    """Fetch class-aggregated downstream rows.
    1) fast /query_connectivity grouped (id, then label);
    2) slow but reliable named DownstreamClassConnectivity via /run_query.
    Returns (rows, provenance) or (None, None) on persistent failure."""
    from vfb import api_get
    queries = [up_query] if up_query == up_label else [up_query, up_label]
    for q in queries:
        try:
            res = api_get("/query_connectivity",
                          {"upstream_type": q, "group_by_class": "true"},
                          retries=2)
            if q != up_query:
                log.append(f"  (fell back to label query for {up_label})")
            return res.get("connections", []), "grouped"
        except Exception as e:
            log.append(f"  !! grouped query failed for {up_label} via {q!r}: "
                       f"{type(e).__name__}")
    # fallback: named query (slow ~60-100s, but reliable for broad classes)
    try:
        log.append(f"  (trying named DownstreamClassConnectivity for {up_label})")
        res = api_get("/run_query",
                      {"id": up_id, "query_type": "DownstreamClassConnectivity",
                       "limit": "40"}, retries=2)
        log.append(f"  (named query worked for {up_label})")
        return res.get("rows", []), "named"
    except Exception as e:
        log.append(f"  !! named query also failed for {up_label}: "
                   f"{type(e).__name__}")
    return None, None


def norm_row(r, provenance):
    """Normalize grouped vs named row formats to (label, fbbt_id, weight)."""
    import re
    if provenance == "named":
        m = re.match(r"\[(.*?)\]\((FBbt_\d+)\)", r.get("downstream_class") or "")
        if not m:
            return None
        label, fid = m.group(1), m.group(2)
    else:
        label, fid = r.get("downstream_class"), r.get("downstream_class_id")
    if not label or not fid:
        return None
    return label, fid, (r.get("total_weight") or 0)


def pick_downstream(up_query, up_id, up_label, k, log):
    """Rank specific downstream classes by total synapse weight."""
    rows, prov = fetch_rows(up_query, up_id, up_label, log)
    if rows is None:
        log.append(f"  (all query forms failed for {up_label} — GAP)")
        return []
    cands = []
    for r in rows:
        n = norm_row(r, prov)
        if not n:
            continue
        dc, dcid, tw = n
        if dcid == up_id:
            continue  # skip self-loops
        if dc in GENERIC:
            continue
        if tw <= 0:
            continue
        cands.append((tw, dc, dcid))
    cands.sort(reverse=True)
    log.append(f"  {up_label} ({up_id}): {len(rows)} raw rows [{prov}], "
               f"{len(cands)} specific candidates")
    for tw, dc, dcid in cands[:k + 3]:
        log.append(f"      cand: {dc} [{dcid}] tw={tw}")
    return [(dc, dcid, tw) for tw, dc, dcid in cands[:k]]


LOGF = os.path.join(os.path.dirname(OUT), "build.log")


def emit(line):
    print(line, flush=True)
    with open(LOGF, "a") as f:
        f.write(line + "\n")


def build(stimulus, cfg):
    emit(f"== {stimulus} ==")
    nodes = {}   # id -> node dict
    edges = []   # (pre, post, weight)
    seen_edge = set()

    def add_node(nid, label, hop):
        if nid not in nodes:
            nodes[nid] = {"id": nid, "name": label, "type": label,
                          "hop": hop}

    frontier = []
    for nid, label, q in cfg["hop0"]:
        add_node(nid, label, 0)
        frontier.append((q, nid, label))

    log = []
    for hop, k in enumerate(cfg["branch"], start=1):
        nxt = []
        emit(f" hop {hop}: expanding {len(frontier)} nodes, top-{k} each")
        for q, nid, label in frontier:
            picks = pick_downstream(q, nid, label, k, log)
            for line in log:
                emit(line)
            log = []
            if not picks:
                emit(f"  (no specific downstream for {label} — GAP)")
            for dc, dcid, tw in picks:
                add_node(dcid, dc, hop)
                if (nid, dcid) not in seen_edge:
                    seen_edge.add((nid, dcid))
                    edges.append({"pre": nid, "post": dcid, "weight": tw})
                nxt.append((dcid, dcid, dc))
        # dedupe frontier preserving order
        seen = set()
        frontier = [(qq, i, l) for qq, i, l in nxt
                    if not (i in seen or seen.add(i))]

    graph = {
        "stimulus": stimulus,
        "source": "Virtual Fly Brain VFBquery HTTP API (https://v3-cached.virtualflybrain.org/), "
                  "FlyWire FAFB v783 connectome; class-aggregated /query_connectivity, "
                  "edge weight = total synapse count",
        "nodes": list(nodes.values()),
        "edges": edges,
        "behavior": cfg["behavior"],
        "fly_narration": cfg["fly_narration"],
        "hop0_ids": [nid for nid, _, _ in cfg["hop0"]],
    }
    path = os.path.join(OUT, f"{stimulus}.json")
    with open(path, "w") as f:
        json.dump(graph, f, indent=1)
    emit(f" saved {path}: {len(nodes)} nodes, {len(edges)} edges")


def main():
    import sys
    which = sys.argv[1:] or list(STIMULI)
    for stim in which:
        try:
            build(stim, STIMULI[stim])
        except Exception as e:
            emit(f"== {stim} == FAILED: {e}")





if __name__ == "__main__":
    main()
