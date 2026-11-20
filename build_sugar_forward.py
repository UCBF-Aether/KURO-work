#!/usr/bin/env python3
"""build_sugar_forward.py — build sugar_forward.json: the RESOLVED sweet-GRN
forward walk.

Method (see GAPS.md RESOLVED §1): class-level downstream queries for
FBbt_00049614 "sweet-sensing gustatory receptor neuron" return 0 rows, but
the class has 33 CATMAID FAFB instances (Engert2022). We queried downstream
partners PER INSTANCE via the CATMAID pass-through
(/catmaid/fafb/connectivity, POST), summed synapse counts per partner
skeleton across all instances, mapped partner skeletons to neuron names
(neuron_names) and then to FBbt classes (VFB search), and aggregated by
class. Hop 2 uses the standard class-level walk (build_graphs).

Every edge is a real API row. Nothing is invented.
"""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from build_graphs import pick_downstream, GENERIC  # noqa: F401

BASE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(BASE, "subgraphs", "sugar_forward.json")

HOP0_ID = "FBbt_00049614"
HOP0_LABEL = "sweet-sensing gustatory receptor neuron"

# partner skeleton -> (FBbt class id, class label); verified via VFB search
# on the CATMAID neuron name (see GAPS.md). Skids not listed here (mostly
# other sweet-GRN instances = lateral GRN-GRN links, same class as hop 0)
# are skipped, following the walk's no-self-loop convention.
PARTNER_CLASS = {
    "7899212": ("FBbt_00052223", "adult zorro subesophageal neuron"),   # Zorro R
    "7574284": ("FBbt_00052223", "adult zorro subesophageal neuron"),   # Zorro L
    "8952676": ("FBbt_00051880", "adult FMIn subesophageal neuron"),    # FMIN
    "10150139": ("FBbt_00051867", "adult clavicle subesophageal neuron"),  # Clavicle
    "7929209": ("FBbt_00052227", "adult fuchs subesophageal neuron"),  # Fuchs
    "17249809": ("FBbt_00052232", "adult dandelion subesophageal neuron"),  # Dandelion
    "15079937": ("FBbt_00051850",
                 "G2N-1 (adult gustatory second-order neuron type 1)"),
    "7983275": ("FBbt_00051883", "adult fudog subesophageal neuron"),  # Fudog R
    "8606542": ("FBbt_00052228", "adult billiards subesophageal neuron"),
    "17579359": ("FBbt_00052230", "adult specter subesophageal neuron"),
    "14890522": ("FBbt_00051956", "adult usnea subesophageal neuron"),
    "16238926": ("FBbt_00051932", "adult rattle subesophageal neuron"),
    "8275570": ("FBbt_00052229", "adult quasimodo subesophageal neuron"),
    "16762541": ("FBbt_00051927", "adult phantom subesophageal neuron"),
}

AGG_PATH = "/tmp/sugar_agg.json"
N_HOP1 = 6
N_HOP2 = 3


def main():
    agg = json.load(open(AGG_PATH))
    inst_agg = agg["agg"]
    n_skeletons = len(agg.get("done", agg.get("skids", [])))

    # aggregate partner synapse counts by FBbt class
    by_class = {}
    for skid, w in inst_agg.items():
        m = PARTNER_CLASS.get(str(skid))
        if not m:
            continue
        fid, label = m
        if fid not in by_class:
            by_class[fid] = {"label": label, "weight": 0, "skids": []}
        by_class[fid]["weight"] += w
        by_class[fid]["skids"].append(str(skid))

    ranked = sorted(by_class.items(), key=lambda kv: -kv[1]["weight"])
    print(f"skeletons aggregated: {n_skeletons}")
    for fid, info in ranked:
        print(f"  {info['weight']:5d} {info['label'][:55]} [{fid}] "
              f"skids={len(info['skids'])}")

    nodes = {}
    edges = []
    seen_edge = set()

    def add_node(nid, label, hop):
        if nid not in nodes:
            nodes[nid] = {"id": nid, "name": label, "type": label, "hop": hop}

    def add_edge(pre, post, w):
        if (pre, post) not in seen_edge:
            seen_edge.add((pre, post))
            edges.append({"pre": pre, "post": post, "weight": w})

    add_node(HOP0_ID, HOP0_LABEL, 0)
    hop1 = [(fid, info) for fid, info in ranked[:N_HOP1]]
    for fid, info in hop1:
        add_node(fid, info["label"], 1)
        add_edge(HOP0_ID, fid, info["weight"])

    log = []
    for fid, info in hop1:
        picks = pick_downstream(fid, fid, info["label"], N_HOP2, log)
        for line in log:
            print(line)
        log = []
        if not picks:
            print(f"  (no class-level downstream for {info['label']} — "
                  f"terminal at hop 1)")
        for dc, dcid, tw in picks:
            add_node(dcid, dc, 2)
            add_edge(fid, dcid, tw)

    graph = {
        "stimulus": "sugar (forward)",
        "source": "Virtual Fly Brain VFBquery HTTP API "
                  "(https://v3-cached.virtualflybrain.org/). Hop 0->1 edges: "
                  "per-instance CATMAID FAFB connectivity (Engert2022) via "
                  "/catmaid/fafb/connectivity, synapse counts summed across "
                  f"{n_skeletons} sweet-GRN skeletons and aggregated by "
                  "partner FBbt class (partner skeletons mapped via "
                  "neuron_names + VFB search). Hop 1->2 edges: class-"
                  "aggregated /query_connectivity (FlyWire FAFB v783). "
                  "Edge weight = total synapse count.",
        "nodes": list(nodes.values()),
        "edges": edges,
        "behavior": {
            "text": "Sweet taste drives gustatory second-order SEZ "
                    "interneurons (Zorro, Clavicle, Fuchs, FMIN, Dandelion, "
                    "G2N-1 and others), which converge on SEZ, gnathal and "
                    "descending premotor populations driving proboscis "
                    "extension.",
            "basis": "resolved forward walk: sweet-GRN instances -> named "
                     "SEZ interneuron classes (CATMAID FAFB, Engert2022) -> "
                     "SEZ/gnathal/descending classes (FlyWire v783)",
        },
        "fly_narration": "Sweet on the tongue — reach out.",
        "hop0_ids": [HOP0_ID],
        "method": {
            "hop0_class": HOP0_ID,
            "instance_aggregation": {
                "n_skeletons_queried": n_skeletons,
                "endpoint": "/catmaid/fafb/connectivity (POST)",
                "partner_mapping": "neuron_names -> VFB search -> FBbt class",
            },
        },
    }
    with open(OUT, "w") as f:
        json.dump(graph, f, indent=1)
    print(f"saved {OUT}: {len(nodes)} nodes, {len(edges)} edges")


if __name__ == "__main__":
    main()
