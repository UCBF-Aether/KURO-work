#!/usr/bin/env python3
"""Build subgraphs/fat_peg.json — the TASTE-PEG half of fat taste, attacked via
the general peg-GRN class (own method).

BACKGROUND (see GAPS.md HONEST-FAIL + RESOLVED-VIA-LITERATURE-HYPOTHESIS):
- Ir56d peg neurons (E409, FBbt_00048014) have ZERO indexed connectivity in any
  API form, and the literature names no downstream partners either.
- BUT the general "labellar taste peg chemosensory neuron" class
  (FBbt_00048028) HAS indexed downstream (named DownstreamClassConnectivity,
  100-row cap; grouped query returns only 5 rows).
- Tauber et al. 2017: peg Ir56d projections target ANTERIOR SEZ (vs posterior
  for bristles). So: walk the general peg class -> real peg-GRN downstream,
  then narrow by the anatomical constraint — hop-1 neurons arborizing in the
  prow (the anterior SEZ neuropil, standard Drosophila brain nomenclature)
  are the Ir56d-peg CANDIDATE pool.

PROVENANCE DISCIPLINE (the whole game):
- hop0->hop1, hop1->hop2 edges: "REAL" (VFBquery/FlyWire v783 API rows).
- "anterior_candidate": true on hop-1 nodes with documented prow arborization
  (VFB term descriptions: Sterne et al. 2021; Schlegel et al. 2024 /
  Dorkenwald et al. 2024) — a LITERATURE-CONSTRAINT annotation, NOT wiring.
- What is NOT claimed: that any of this is Ir56d-PEG-SPECIFIC wiring. No API
  marker distinguishes Ir56d peg GRNs from other peg GRNs. The candidate pool
  is a constrained hypothesis, not a measurement.

ANTERIOR NARROWING RESULTS:
- hyacinth (FBbt_00051898): dendritic+axonal arborization in PROW and flange
  (Sterne et al. 2021) — strongest anterior claim. Included as 7th hop-1
  node: 49 synapses below the top-6 weight cutoff, documented here.
- CB0011 (FBbt_20003871): postsynapses in gnathal ganglia AND PROW
  (Schlegel et al. 2024).
- CB3720 (FBbt_20007145): postsynapses in gnathal ganglia and PROW
  (Schlegel et al. 2024).
- rattle (FBbt_00051932): gnathal-ganglion arborization; receives
  sugar-sensing GRN input (Shiu et al. 2022) — sugar-linked, kept for the
  sweet-overlap question, NOT anterior-flagged.
- CB0137 (FBbt_20003973): gnathal ganglia postsynapses only.

SWEET-SET OVERLAP: none of zorro/clavicle/FMIn/fuchs/G2N-1/billiards appear
in the peg top-k. The peg pool is a DIFFERENT interneuron set than the
bristle sweet set — but rattle IS sugar-linked (Shiu 2022), and BOTH pools
converge on SEZ neuron FBbt_00001972 -> the same motor populations.
"""
import json, os

HERE = os.path.dirname(os.path.abspath(__file__))
hop2 = json.load(open('/tmp/peg_hop2.json'))

PEG = {"id": "FBbt_00048028", "name": "labellar taste peg chemosensory neuron", "hop": 0}

# (id, name, hop0->hop1 weight, anterior_candidate, note)
HOP1 = [
    ("FBbt_00001972", "subesophageal zone neuron", 3545, False,
     "Shared SEZ convergence node (sweet/water/bitter/DH44/IPC too)."),
    ("FBbt_00052032", "gnathal ganglion neuron", 2926, False,
     "Shared gnathal terminal class."),
    ("FBbt_20003871", "adult CB0011 neuron", 1534, True,
     "ANTERIOR CANDIDATE: postsynapses in gnathal ganglia and prow "
     "(Schlegel et al. 2024 / Dorkenwald et al. 2024)."),
    ("FBbt_00051932", "adult rattle subesophageal neuron", 636, False,
     "Sugar-linked: receives sugar-sensing GRN input, drives proboscis "
     "extension (Shiu et al. 2022). Gnathal-ganglion arborization."),
    ("FBbt_20003973", "adult CB0137 neuron", 616, False,
     "Gnathal-ganglia postsynapses (Schlegel et al. 2024)."),
    ("FBbt_20007145", "adult CB3720 neuron", 486, True,
     "ANTERIOR CANDIDATE: postsynapses in gnathal ganglia and prow "
     "(Schlegel et al. 2024)."),
    ("FBbt_00051898", "adult hyacinth subesophageal neuron", 437, True,
     "ANTERIOR CANDIDATE (strongest): dendritic+axonal arborization in prow "
     "AND flange, bilateral (Sterne et al. 2021). Included 7th: 49 synapses "
     "below the top-6 weight cutoff — documented, not hidden."),
]

# hop1 id -> [(label, id, weight)] (REAL API rows; see /tmp/peg_hop2.json)
HOP2 = {
    "FBbt_00001972": [("adult VNC neuron", "FBbt_00059289", 960507),
                      ("thoracic neuron", "FBbt_00059290", 846534),
                      ("secondary neuron", "FBbt_00059291", 668777)],
    "FBbt_00052032": [("adult VNC neuron", "FBbt_00059289", 959022),
                      ("thoracic neuron", "FBbt_00059290", 845190),
                      ("secondary neuron", "FBbt_00059291", 632276)],
    "FBbt_20003871": [("chemosensory system neuron", "FBbt_00007696", 2277),
                      ("gustatory system neuron", "FBbt_00007695", 2189),
                      ("chemosensory neuron", "FBbt_00005922", 2168)],
    "FBbt_00051932": [("subesophageal zone neuron", "FBbt_00001972", 4496),
                      ("gnathal ganglion neuron", "FBbt_00052032", 4496),
                      ("adult descending neuron", "FBbt_00047511", 2043)],
    "FBbt_20003973": [("subesophageal zone neuron", "FBbt_00001972", 1884),
                      ("gnathal ganglion neuron", "FBbt_00052032", 1864),
                      ("adult descending neuron", "FBbt_00047511", 1220)],
    "FBbt_20007145": [("TRdm lineage neuron", "FBbt_00100671", 339),
                      ("subesophageal zone neuron", "FBbt_00001972", 279),
                      ("gnathal ganglion neuron", "FBbt_00052032", 258)],
    # hyacinth: API returned FBbt_00001972 twice (tw 2567 + 1775, same class —
    # response duplication quirk); deduped to the max, documented here.
    "FBbt_00051898": [("subesophageal zone neuron", "FBbt_00001972", 2567),
                      ("TRdm lineage neuron", "FBbt_00100671", 1881)],
}

CIT_ANTERIOR = ("Tauber et al. 2017, PLOS Genet 13:e1007059 (taste-peg Ir56d "
                "projections target anterior SEZ); prow = anterior SEZ "
                "neuropil (standard Drosophila brain nomenclature); "
                "arborization from VFB term descriptions (Sterne et al. 2021; "
                "Schlegel et al. 2024; Dorkenwald et al. 2024).")

nodes = [dict(PEG)]
edges = []
for nid, name, w, ant, note in HOP1:
    n = {"id": nid, "name": name, "hop": 1, "anterior_candidate": ant,
         "candidate_note": note}
    if ant:
        n["constraint_provenance"] = "LITERATURE-CONSTRAINT"
        n["constraint_citation"] = CIT_ANTERIOR
    nodes.append(n)
    edges.append({"pre": PEG["id"], "post": nid, "weight": w,
                  "provenance": "REAL",
                  "note": "FlyWire v783 class-level row (peg-class walk)."})
seen = set()
for pre, trips in HOP2.items():
    for label, nid, w in trips:
        if nid not in seen:
            seen.add(nid)
            nodes.append({"id": nid, "name": label, "hop": 2})
        edges.append({"pre": pre, "post": nid, "weight": w,
                      "provenance": "REAL",
                      "note": "FlyWire v783 class-level row."})

graph = {
    "stimulus": "fatty acid taste, taste-peg (E409/Ir56d) population — own-method attack",
    "source": ("Virtual Fly Brain VFBquery HTTP API (https://v3-cached.virtualflybrain.org/), "
               "FlyWire FAFB v783; peg-class walk (named DownstreamClassConnectivity, 100-row cap) "
               "+ anatomical narrowing. Builder: build_fat_peg.py."),
    "nodes": nodes,
    "edges": edges,
    "honest_note": (
        "PROVENANCE SPLIT — read before using. Hop 0->1 and hop 1->2 edges are REAL "
        "FlyWire v783 API rows from the general taste-peg GRN class walk "
        "(FBbt_00048028; Ir56d-peg E409 neurons are an unmarked SUBSET of this class). "
        "The 'anterior_candidate' flags on CB0011 / CB3720 / hyacinth are a "
        "LITERATURE-CONSTRAINT (Tauber 2017: peg->anterior SEZ; prow arborization per "
        "VFB term descriptions) — a constrained candidate pool, NOT measured "
        "Ir56d-peg wiring. Ir56d-peg-subset attribution is UNRESOLVABLE: no API marker "
        "distinguishes Ir56d peg GRNs from other peg GRNs. Sweet second-order set "
        "(zorro/clavicle/FMIn/fuchs/G2N-1/billiards) does NOT appear in the peg top-k — "
        "the peg pool is a different interneuron set — BUT rattle receives sugar-GRN "
        "input (Shiu et al. 2022), and both pools converge on SEZ neuron "
        "FBbt_00001972 -> identical motor populations (VNC/thoracic/secondary). "
        "CB0011 hop-2 is bucket-heavy (system-level classes passed the GENERIC "
        "blocklist; documented, same treatment as bitter). Hyacinth API returned "
        "FBbt_00001972 twice (tw 2567/1775); deduped to max."),
    "behavior": ("Taste-peg GRNs (including the Ir56d/E409 fat-taste subset) drive "
                 "SEZ interneurons converging on the shared SEZ->motor pathway; the "
                 "anterior (prow) subset is the Ir56d-peg candidate pool."),
}

out = os.path.join(HERE, "subgraphs", "fat_peg.json")
json.dump(graph, open(out, "w"), indent=1)
print(f"wrote {out}: {len(nodes)} nodes, {len(edges)} edges")
