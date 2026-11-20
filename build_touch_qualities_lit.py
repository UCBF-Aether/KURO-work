#!/usr/bin/env python3
"""build_touch_qualities_lit.py — own-method LITERATURE attack on touch qualities.

GAPS.md §6/§6b: bristle (FBbt_00048508) and campaniform (FBbt_00048057)
mechanosensory classes have ZERO API connectivity in every downstream form
and NO CATMAID skeletons (Neuprint-only). The API route is exhausted.

Own method (fat_lit / song_lit precedent):
  CAMPANIFORM: motor-backward — upstream of the b1 wing motor neuron
    (FBbt_00004066) resolves campaniform classes with REAL synapse weights.
    Independently CONFIRMED by Lesser et al. 2026 eLife (tegula campaniform
    -> b1 monosynaptic, FANC EM).
  BRISTLE: literature-named second-order neurons with no FBbt class yet
    (too new for the ontology):
    - MGT ("Mago-no-Te", thoracic grooming command): posterior macrochaete
      bristle BMNs synapse onto MGT (t-GRASP + FANC EM) — Yoshikawa et al.,
      Curr Biol (bioRxiv 2023.11.19.567707; PMC10690200).
    - CTN (central Tmc-L neurons): wing-margin bristle mechanoreceptors ->
      CTNs drive defensive behavior (ATP/P2X2 + GCaMP) — Nat Commun 2020
      s41467-020-17771-8.

Provenance labels are the whole game: REAL vs LITERATURE-HYPOTHESIS vs
LITERATURE-CONFIRMED. Nothing is presented as measured wiring that isn't.
"""
import json

NODES = [
    # --- campaniform hop 0 (REAL classes) ---
    {"id": "FBbt_00048057", "name": "sensory neuron of campaniform sensillum",
     "hop": 0, "provenance": "REAL",
     "note": "General campaniform class; upstream of b1 resolves it at tw=3572."},
    {"id": "FBbt_00048279", "name": "sensory neuron of wing campaniform sensillum",
     "hop": 0, "provenance": "REAL",
     "note": "Wing campaniform; upstream of b1 at tw=1818."},
    {"id": "FBbt_00048296", "name": "sensory neuron of haltere campaniform sensillum",
     "hop": 0, "provenance": "REAL",
     "note": "Haltere campaniform; upstream of b1 at tw=1754."},
    # --- campaniform hop 1 (REAL class) ---
    {"id": "FBbt_00004066", "name": "b1 motor neuron (wing basalar muscle b1)",
     "hop": 1, "provenance": "REAL",
     "note": "Tonic wing steering motor neuron; monosynaptic target of tegula campaniform sensilla (Lesser et al. 2026)."},
    # --- bristle hop 0 (REAL classes, unindexable downstream) ---
    {"id": "FBbt_00048508", "name": "bristle mechanosensory neuron",
     "hop": 0, "provenance": "REAL",
     "note": "General bristle class; 0 API rows downstream in every form (GAPS.md §6)."},
    {"id": "FBbt_00048273", "name": "sensory neuron of wing bristle",
     "hop": 0, "provenance": "REAL",
     "note": "Wing bristle BMN; the CTN paper stimulated wing-margin bristles."},
    # --- bristle hop 1 (LITERATURE-ONLY: no FBbt class exists) ---
    {"id": "MGT_literature", "name": "Mago-no-Te (MGT) command neuron",
     "hop": 1, "provenance": "LITERATURE-HYPOTHESIS",
     "note": "NO FBbt class (too new for the ontology). Pair of cholinergic command-like neurons for thoracic grooming; posterior macrochaete bristle BMNs synapse onto MGT (t-GRASP + FANC EM)."},
    {"id": "CTN_literature", "name": "central Tmc-L neuron (CTN)",
     "hop": 1, "provenance": "LITERATURE-HYPOTHESIS",
     "note": "NO FBbt class. Central neurons expressing Tmc-L; wing-margin bristle mechanoreceptors drive CTNs (ATP/P2X2 + GCaMP) to mediate defensive behavior."},
]

EDGES = [
    # --- campaniform: REAL API rows (upstream of b1, /run_query UpstreamClassConnectivity) ---
    {"pre": "FBbt_00048057", "post": "FBbt_00004066", "weight": 3572,
     "provenance": "REAL",
     "citation": "VFBquery /run_query UpstreamClassConnectivity of FBbt_00004066 (b1), FlyWire FAFB v783",
     "note": "Class-level downstream of campaniform is broken (0 rows); the upstream query of b1 resolves the same synapse set. Ontology-duplicate labels (mechanosensory neuron tw=3572 etc.) are the same underlying rows, not independent."},
    {"pre": "FBbt_00048279", "post": "FBbt_00004066", "weight": 1818,
     "provenance": "REAL",
     "citation": "VFBquery /run_query UpstreamClassConnectivity of FBbt_00004066, FlyWire FAFB v783",
     "note": "Wing campaniform -> b1."},
    {"pre": "FBbt_00048296", "post": "FBbt_00004066", "weight": 1754,
     "provenance": "REAL",
     "citation": "VFBquery /run_query UpstreamClassConnectivity of FBbt_00004066, FlyWire FAFB v783",
     "note": "Haltere campaniform -> b1."},
    # --- campaniform: LITERATURE-CONFIRMED (independent EM confirmation of the API rows) ---
    {"pre": "FBbt_00048279", "post": "FBbt_00004066", "weight": 1818,
     "provenance": "LITERATURE-CONFIRMED",
     "citation": "Lesser, Moussa & Tuthill, eLife 2026 (bioRxiv 2025.05.29.656810): 'campaniform sensilla on the tegula synapse directly onto the tonic wing b1 motor neuron' (FANC EM reconstructions)",
     "note": "Independent EM confirmation of the API-resolved wing campaniform -> b1 edge. Kept as a separate provenance-labeled edge; same synapse set, not double-counted."},
    # --- bristle: LITERATURE-HYPOTHESIS (no API rows exist anywhere reachable) ---
    {"pre": "FBbt_00048508", "post": "MGT_literature", "weight": 1,
     "provenance": "LITERATURE-HYPOTHESIS",
     "citation": "Yoshikawa, Tang & Simpson, Curr Biol (bioRxiv 2023.11.19.567707; PMC10690200): 'Posterior macrochaete mechanosensory bristle neurons synapse onto MGT' (t-GRASP + FANC/MANC EM); synapse counts in paper Fig 4C (posterior > anterior), not extracted here",
     "note": "Placeholder weight: no synapse counts extracted. MGT has no FBbt class. The API holds zero rows for this edge in any reachable form."},
    {"pre": "FBbt_00048273", "post": "CTN_literature", "weight": 1,
     "provenance": "LITERATURE-HYPOTHESIS",
     "citation": "Nat Commun 2020 s41467-020-17771-8 ('A neural circuit encoding mating states tunes defensive behavior in Drosophila'): wing-margin bristle mechanoreceptors (GMR45E03-Gal4) drive CTNs (ATP/P2X2 stimulation + GCaMP); CTN activation/silencing bidirectionally controls defensive response",
     "note": "Placeholder weight. CTN has no FBbt class. Functional connectivity shown; monosynapticity not proven (same caveat class as vPN1->pC1)."},
]

GRAPH = {
    "name": "touch_qualities_lit",
    "source": "VFBquery/FlyWire FAFB v783 (REAL edges) + primary literature (hypothesis edges)",
    "nodes": NODES,
    "edges": EDGES,
    "honest_note": (
        "PROVENANCE SPLIT — read before using. "
        "CAMPANIFORM: 3 REAL edges (campaniform classes -> b1 motor neuron, measured VFBquery upstream rows, tw=3572/1818/1754) "
        "+ 1 LITERATURE-CONFIRMED edge (independent FANC EM confirmation of wing campaniform -> b1; same synapse set, not double-counted). "
        "BRISTLE: 2 LITERATURE-HYPOTHESIS edges (bristle BMN -> MGT; wing bristle -> CTN), each with its citation; placeholder weight 1; "
        "MGT and CTN have NO FBbt classes (too new for the ontology) and the API holds zero rows for bristle downstream in any reachable form "
        "(GAPS.md §6/§6b: class-level 0 rows, per-pair server death, Neuprint-only instances). "
        "Never present hypothesis edges as measured wiring."
    ),
}

with open("subgraphs/touch_qualities_lit.json", "w") as f:
    json.dump(GRAPH, f, indent=2)
print("wrote subgraphs/touch_qualities_lit.json:",
      len(NODES), "nodes,", len(EDGES), "edges")
