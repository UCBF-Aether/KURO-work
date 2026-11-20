#!/usr/bin/env python3
"""build_song.py — courtship-song wiring: honest API stub + literature hypothesis.

API route (all dead, documented in GAPS.md):
  class-level downstream: intrinsic AMMC neuron FBbt_00111352 (0 rows),
    AMMC-B1 FBbt_00110120 (0 rows id+label), AVLP_pr01 FBbt_00052102 (0),
    vPN1 FBbt_00111295 (0), JO-B label form (0); JO-A/JO-B grouped die server-side
  named DownstreamClassConnectivity: AMMC-B1 (server death), JO-B (timeout)
  instance CATMAID: 5 AMMC-B1 FAFB skeletons exist but tracings are ~empty
    (48 partners, 75 synapses, mostly placeholder/unannotated neurons)
  motor-backward: pC1-male FBbt_00047348 upstream (0 rows), P1 FBbt_00110621
    upstream (0), pC1-general FBbt_00053230 upstream (50 rows, all generic
    ontology buckets), AMMC-intrinsic upstream (0), vPN1 upstream (0)
  per-pair: AMMC-B1->pC1 (0), AVLP_pr01->pC1 (0), AMMC-VLP2->pC1 (0),
    vPN1->pC1male (0), JO-B->AMMC-B1 (0), JO-B->AMMC-intrinsic (0)
  BANC v888: AMMC-B1 (0 rows)

Produces:
  subgraphs/song.json     — honest 1-node stub (AMMC-B1, no edges)
  subgraphs/song_lit.json — literature-grounded chain, every edge labeled
    LITERATURE-HYPOTHESIS with citation; no edge presented as an API row.

Literature chain (paraphrased, not quoted):
  JO-B -> AMMC-B1: JO subgroup-B neurons are the primary auditory input and
    AMMC-B1 neurons are the major secondary auditory neurons; JO-B->AMMC-B1
    transmission is the first step of IPI processing (Ishikawa et al.,
    Sci Rep 2023, s41598-022-27349-7; Kamikouchi lab).
  AMMC-B1 -> vPN1: second-order aPN1 -> third-order vPN1 (male-specific,
    fru+); synaptic connection confirmed by GRASP (Zhou et al. 2015,
    eLife 4:e08477). VFB synonym check: AMMC-B1 = aPN1a,b (same FBbt ID).
  vPN1 -> pC1: vPN1 axons overlap dsx+ pC1 arbors in the LPC region;
    optogenetic activation of vPN1 drives pC1 calcium responses and both
    manipulations induce/block song-evoked chaining; authors note GRASP
    signal was barely detectable, so monosynapticity is not proven
    (Zhou et al. 2015, eLife 4:e08477).
Meeting point: pC1 (FBbt_00047348) is hop-1 in mating.json (P1->pC1,
  tw=11033, REAL API rows). The song chain feeds INTO pC1; pC1's own
  downstream is unindexed (0 rows all forms — honest terminal), so no
  pC1->P1 edge is drawn.
"""

import json
import os

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "subgraphs")
os.makedirs(OUT, exist_ok=True)

STUB_HONEST = (
    "HONEST STUB: the courtship-song relay classes are unindexed in every "
    "VFBquery-reachable dataset. AMMC-B1 (FBbt_00110120, the song-relay "
    "projection neuron): 0 downstream rows (grouped id+label), named "
    "DownstreamClassConnectivity dies server-side, BANC v888 0 rows; 5 FAFB "
    "skeletons exist but tracings are ~empty (48 partners / 75 synapses, "
    "mostly placeholder neurons). vPN1 (FBbt_00111295, third-order song "
    "neuron): 0 downstream, 0 upstream rows. Intrinsic AMMC neuron "
    "(FBbt_00111352): 0/0. AVLP_pr01 (FBbt_00052102): 0 downstream. "
    "pC1-male (FBbt_00047348): 0 upstream rows; pC1-general upstream gives "
    "only generic ontology buckets. P1 (FBbt_00110621): 0 upstream rows. "
    "Per-pair probes (AMMC-B1/vPN1/AVLP->pC1, JO-B->AMMC-B1): all 0. "
    "See subgraphs/song_lit.json for the literature-grounded hypothesis "
    "chain (JO-B -> AMMC-B1 -> vPN1 -> pC1), edges labeled "
    "LITERATURE-HYPOTHESIS, none presented as measured wiring."
)

stub = {
    "stimulus": "song",
    "source": "Virtual Fly Brain VFBquery HTTP API (https://v3-cached.virtualflybrain.org/), "
              "FlyWire FAFB v783 + BANC v888 connectome; class-aggregated /query_connectivity",
    "nodes": [
        {"id": "FBbt_00110120", "name": "AMMC-B1 neuron",
         "type": "antennal mechanosensory and motor center B1 projection neuron "
                 "(= aPN1a,b per VFB synonyms; second-order song-relay neuron)",
         "hop": 0},
    ],
    "edges": [],
    "behavior": {
        "text": "Courtship-song hearing: the fly detects a mate's pulse song "
                "via Johnston's organ auditory neurons and relays it through "
                "AMMC to central courtship circuits.",
        "basis": "textbook Drosophila courtship-song pathway (JO-B -> AMMC-B1 "
                 "-> vPN1 -> pC1); stated as known biology — the API indexes "
                 "none of these links (see honest_note)",
    },
    "fly_narration": "A song in the air — listen.",
    "hop0_ids": ["FBbt_00110120"],
    "honest_note": STUB_HONEST,
}
with open(os.path.join(OUT, "song.json"), "w") as f:
    json.dump(stub, f, indent=1)
print("saved song.json: 1 node, 0 edges (honest stub)")

# ---- literature hypothesis graph ----
nodes = [
    {"id": "FBbt_00100009", "name": "JO-B neuron",
     "type": "zone B Johnston organ neuron (auditory subgroup)",
     "hop": 0},
    {"id": "FBbt_00110120", "name": "AMMC-B1 neuron",
     "type": "antennal mechanosensory and motor center B1 projection neuron "
              "(= aPN1a,b per VFB synonyms; second-order song-relay neuron)",
     "hop": 1},
    {"id": "FBbt_00111295", "name": "vPN1 neuron",
     "type": "ventrolateral protocerebrum projection neuron 1 "
              "(third-order, male-specific, fru+)",
     "hop": 2},
    {"id": "FBbt_00047348", "name": "adult doublesex pC1 (male) neuron",
     "type": "adult doublesex pC1 (male) neuron (fourth-order song integrator, "
              "dsx+; hop-1 in mating.json)",
     "hop": 3},
]

edges = [
    {"pre": "FBbt_00100009", "post": "FBbt_00110120", "weight": 1,
     "provenance": "LITERATURE-HYPOTHESIS",
     "citation": "Ishikawa et al., Sci Rep 2023 (s41598-022-27349-7): song "
                 "information is transmitted mainly from JO subgroup-B neurons "
                 "to the major secondary auditory neurons AMMC-B1, the first "
                 "step of IPI processing; Kamikouchi lab.",
     "note": "Hypothesized: JO-B auditory neurons drive AMMC-B1. No API rows "
             "exist (JO-B->AMMC-B1 per-pair probe: 0)."},
    {"pre": "FBbt_00110120", "post": "FBbt_00111295", "weight": 1,
     "provenance": "LITERATURE-HYPOTHESIS",
     "citation": "Zhou et al. 2015, eLife 4:e08477: second-order aPN1 -> "
                 "third-order vPN1 (male-specific, fru+); aPN1-vPN1 synaptic "
                 "connection confirmed by GRASP. VFB lists AMMC-B1 as "
                 "aPN1a,b — same FBbt ID, same population.",
     "note": "Hypothesized: AMMC-B1/aPN1 drives vPN1. No API rows exist "
             "(AMMC-B1 downstream: 0 rows all forms)."},
    {"pre": "FBbt_00111295", "post": "FBbt_00047348", "weight": 1,
     "provenance": "LITERATURE-HYPOTHESIS",
     "citation": "Zhou et al. 2015, eLife 4:e08477: vPN1 axons overlap dsx+ "
                 "pC1 arbors in the LPC region; vPN1 activation drives pC1 "
                 "calcium responses and both manipulations induce/block "
                 "song-evoked male chaining. Caveat (authors'): GRASP signal "
                 "barely detectable — monosynapticity NOT proven.",
     "note": "Hypothesized: vPN1 drives pC1. No API rows exist (vPN1->pC1 "
             "per-pair probe: 0; vPN1 upstream/downstream: 0)."},
]

LIT_HONEST = (
    "PROVENANCE SPLIT — read before using. All three edges are "
    "LITERATURE-HYPOTHESIS (uniform placeholder weight 1), each with its "
    "citation; NONE is a measured API row. Chain: JO-B (auditory) -> "
    "AMMC-B1/aPN1 (second-order, GRASP-confirmed -> vPN1 in the paper) -> "
    "vPN1 (third-order, male-specific) -> pC1 (fourth-order, dsx+; vPN1->pC1 "
    "functional connection shown, monosynapticity not proven — authors' own "
    "caveat). MEETING POINT WITH MATING: pC1 (FBbt_00047348) is hop-1 in "
    "mating.json — P1->pC1 tw=11033 are REAL API rows. The song chain feeds "
    "INTO pC1; pC1's own downstream is unindexed (0 rows all forms, honest "
    "terminal), so no pC1->P1 edge is drawn. This graph is a publishable "
    "convergent hypothesis (testable: verify AMMC-B1->vPN1->pC1 synapses in "
    "a future connectome release), not a measured circuit."
)

lit = {
    "stimulus": "song",
    "source": "Literature-grounded hypothesis (see per-edge citations); node "
              "identities cross-checked against VFB (FBbt IDs + synonyms). "
              "No edges are VFBquery API rows.",
    "nodes": nodes,
    "edges": edges,
    "behavior": {
        "text": "Courtship-song hearing: pulse song -> JO-B -> AMMC-B1 -> "
                "vPN1 -> pC1, a labeled line for song-evoked courtship "
                "chaining in males.",
        "basis": "Zhou et al. 2015 eLife 4:e08477 (aPN1-vPN1-pC1 labeled "
                 "line); Ishikawa et al. Sci Rep 2023 (JO-B->AMMC-B1 first "
                 "step of IPI processing)",
    },
    "fly_narration": "A song in the air — listen.",
    "hop0_ids": ["FBbt_00100009"],
    "method": "literature-hypothesis",
    "honest_note": LIT_HONEST,
}
with open(os.path.join(OUT, "song_lit.json"), "w") as f:
    json.dump(lit, f, indent=1)
print("saved song_lit.json: 4 nodes, 3 edges (all LITERATURE-HYPOTHESIS)")
