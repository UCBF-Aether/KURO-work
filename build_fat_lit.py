#!/usr/bin/env python3
"""Build subgraphs/fat_lit.json — the IR56d fat-taste circuit as a CONVERGENT
LITERATURE + CONNECTOMIC HYPOTHESIS.

The VFB/FlyWire API holds ZERO Ir56d connectivity (9 avenues exhausted, see
GAPS.md HONEST-FAIL). The literature does not name Ir56d downstream neurons
either (Tauber et al. 2017: "higher order neurons responsive to FA taste have
not been identified"). What the literature DOES establish:

  1. IR56d neurons are a SUBSET of sweet-sensing (Gr64f-overlapping) GRNs,
     necessary and sufficient for medium-chain fatty-acid PER
     (Tauber et al. 2017, PLOS Genet 13:e1007059, CC-BY).
  2. Their posterior (labellar-bristle) projections OVERLAP the sweet-sensing
     SEZ region; a second (taste-peg, E409) population projects to anterior SEZ
     (Tauber et al. 2017; Brown et al. 2021 eLife 67878 measured the posterior
     projections).
  3. Sweet GRNs drive named second-order SEZ interneurons (zorro, clavicle,
     FMIn, fuchs, G2N-1, billiards) — REAL FlyWire rows in sugar_forward.json
     (instance-aggregated CATMAID FAFB + class walks; Shiu et al. 2022 series).

THE HYPOTHESIS (edges labeled LITERATURE-HYPOTHESIS): the bristle IR56d
population (FBbt_00048015) contacts the SAME second-order SEZ interneurons
as sweet GRNs, by virtue of being sweet GRNs projecting to the same region.
Individual Ir56d->interneuron synapses are NOT measured — this file is a
testable prediction, not a wiring claim. The taste-peg (E409, FBbt_00048014)
population's downstream remains unmapped in BOTH literature and API —
documented as the remaining gap, not bridged.

Provenance discipline: every edge carries "provenance":
  - "LITERATURE-HYPOTHESIS" — the Ir56d->interneuron links (this file's claim)
  - "REAL" — interneuron->SEZ/gnathal/descending (API rows, copied verbatim
    from sugar_forward.json)
"""
import json, os

HERE = os.path.dirname(os.path.abspath(__file__))
sugar = json.load(open(os.path.join(HERE, "subgraphs", "sugar_forward.json")))

IR56D_BRISTLE = {
    "id": "FBbt_00048015",
    "name": "adult Ir56d neuron of labellar taste bristle",
    "hop": 0,
}

HOP1_IDS = [n["id"] for n in sugar["nodes"] if n.get("hop") == 1]

CITATION = ("Tauber et al. 2017, PLOS Genet 13:e1007059 "
            "(IR56d subset of sweet-sensing Gr64f GRNs; posterior projections "
            "overlap sweet SEZ region); Brown et al. 2021, eLife 67878.")

nodes = [dict(IR56D_BRISTLE)]
nodes += [dict(n) for n in sugar["nodes"] if n.get("hop") in (1, 2)]

edges = []
for hid in HOP1_IDS:
    h1name = next(n["name"] for n in nodes if n["id"] == hid)
    edges.append({
        "pre": IR56D_BRISTLE["id"],
        "post": hid,
        "weight": 1,  # unmeasured placeholder — uniform, NOT a synapse count
        "provenance": "LITERATURE-HYPOTHESIS",
        "citation": CITATION,
        "note": ("Hypothesized: bristle IR56d GRNs are sweet-sensing GRNs "
                 "projecting to the same posterior SEZ region; predicted to "
                 "contact the same second-order interneurons. Individual "
                 f"Ir56d->{h1name} synapses are NOT measured."),
    })
for e in sugar["edges"]:
    if e["pre"] not in {n["id"] for n in nodes}:
        continue  # sweet-GRN hop-0 edges: replaced by hypothesis edges above
    pre_hop = next(n["hop"] for n in nodes if n["id"] == e["pre"])
    if pre_hop == 1:  # hop1->hop2 only
        e2 = dict(e)
        e2["provenance"] = "REAL"
        e2["note"] = "FlyWire v783 API row (via sugar_forward.json)."
        edges.append(e2)

graph = {
    "stimulus": "fatty acid taste (medium-chain, Ir56d-dependent)",
    "source": ("CONVERGENT HYPOTHESIS — not a pure API product. Hop 0->1 edges: "
               "literature-grounded hypothesis (see builder docstring). Hop 1->2 "
               "edges: Virtual Fly Brain VFBquery HTTP API, FlyWire v783 "
               "(via subgraphs/sugar_forward.json)."),
    "nodes": nodes,
    "edges": edges,
    "behavior": ("Medium-chain fatty acids activate bristle IR56d GRNs (a subset "
                 "of sweet-sensing neurons); predicted to drive the sweet "
                 "second-order SEZ circuit and proboscis extension."),
    "fly_narration": "HYPOTHESIS: the fat taste rides the sweet road into the brain.",
    "hop0_ids": [IR56D_BRISTLE["id"]],
    "method": "build_fat_lit.py",
    "honest_note": (
        "PROVENANCE SPLIT — read before using. Hop 0 (FBbt_00048015, bristle "
        "IR56d GRN) -> hop 1 (zorro/clavicle/FMIn/fuchs/G2N-1/billiards): "
        "LITERATURE-HYPOTHESIS. Grounded in: (1) IR56d neurons are a subset of "
        "sweet-sensing Gr64f GRNs, necessary/sufficient for medium-chain FA "
        "PER (Tauber et al. 2017); (2) their posterior bristle projections "
        "overlap the sweet-sensing SEZ region (Tauber et al. 2017; Brown et al. "
        "2021). The prediction is that they contact the same named second-order "
        "SEZ interneurons that sweet GRNs drive. NO individual Ir56d->interneuron "
        "synapse is measured anywhere — this is a testable prediction for "
        "future connectomic verification, not a wiring claim. Hop 1 -> hop 2 "
        "edges are REAL FlyWire v783 rows. REMAINING GAP: the taste-peg E409 "
        "IR56d population (FBbt_00048014, anterior SEZ projections) has NO "
        "literature-named and NO API-indexed downstream — unmapped in both. "
        "Do not present hypothesis edges as measured wiring."
    ),
}

out = os.path.join(HERE, "subgraphs", "fat_lit.json")
json.dump(graph, open(out, "w"), indent=2)
print(f"wrote {out}: {len(nodes)} nodes, {len(edges)} edges "
      f"({sum(1 for e in edges if e['provenance']=='LITERATURE-HYPOTHESIS')} hypothesis, "
      f"{sum(1 for e in edges if e['provenance']=='REAL')} real)")
