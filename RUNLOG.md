# RUNLOG — flysim.py cascade summaries (all real-connectome subgraphs)

Model: normalized spread-of-activation, firing threshold 0.15, 4 timesteps.
TOY dynamics — see flysim.py header and GAPS.md. Every node/edge below is a
real VFBquery/FlyWire FAFB v783 row.

---

## sugar — sweet-sensing gustatory receptor neuron (FBbt_00049614)
Forward graph (`sugar.json`): 1 node, 0 edges (downstream connectivity NOT
indexed — see GAPS.md §1).

- step 0: injected at sweet-sensing GRN (act 1.00)
- steps 1–4: cascade died out (no outgoing edges)
- motor output: none resolved (forward)
- known biology: proboscis extension response toward sugar (textbook PER)
- FLY: "Sweet on the tongue — reach out."

Motor-backward graph (`sugar_backward.json`): 7 nodes, 17 edges — real
UpstreamClassConnectivity chain: SEZ/gnathal/descending premotor → proboscis
MN mn1. Run with `flysim.py subgraphs/sugar_backward.json --inject-hop -1`.

- step 0: injected at hop -1 premotor layer (SEZ, gnathal ganglion,
  descending neurons — act 1.00 each)
- step 1 fired: proboscis MN mn1 (act 2.00, convergent drive), plus
  recurrent premotor (0.9–1.1)
- steps 2–3: MN keeps firing (1.14 → 0.79), premotor reverberates
- motor output: proboscis motor neuron mn1
- known biology: SEZ premotor drive → proboscis extension (textbook)
- FLY: "Sweet command received — reach out."
- missing link (documented, not invented): sweet-GRN → SEZ sensory input

## looming — LPLC2 looming detector (FBbt_00111763)
Graph: 14 nodes, 24 edges.

- step 0: injected at LPLC2 (act 1.00)
- step 1 fired: adult descending neuron (0.19), adult VPNd1 lineage (0.18),
  BLD6 lineage (0.18), optic lobe wide-field columnar (0.17)
- step 2 fired: adult descending neuron (0.17, recurrent)
- steps 3–4: cascade died out
- motor output: adult descending neuron
- known biology: escape — looming drives descending/giant-fiber system,
  jump-and-flight takeoff (textbook)
- FLY: "Shadow swelling — MOVE."
- note: LPLC2→giant fiber edge verified real (275 pairs, tw 5680) but rank 48
  by weight, below top-k cutoff — recorded in GAPS.md §1b

## rotten — Or56a aversive olfactory receptor neuron (FBbt_00067063)
Graph: 12 nodes, 24 edges.

- step 0: injected at Or56a ORN (act 1.00)
- step 1 fired: adult ALl1 lineage (0.20), BAlc lineage (0.20),
  Notch OFF hemilineage (0.19), BAlc Notch OFF hemilineage (0.19)
  [antennal lobe circuitry]
- step 2 fired: adult central brain intrinsic neuron (0.21)
- steps 3–4: cascade died out
- motor output: adult central brain intrinsic neuron (+ VNC/thoracic at 0.16–0.24
  in the touch graph's shared motor pools)
- known biology: olfactory aversion — turn away from geosmin (textbook
  Or56a → antennal lobe → lateral horn / mushroom body)
- FLY: "Rot in the air — turn away."

## touch — Johnston organ neuron (FBbt_00100000)
Graph: 10 nodes, 12 edges.

- step 0: injected at Johnston organ neuron (act 1.00)
- step 1 fired: adult subesophageal sensory interneuron (0.39),
  subesophageal zone neuron (0.31), gnathal ganglion neuron (0.31)
- step 2 fired: adult VNC neuron (0.24), thoracic neuron (0.21),
  adult visual neuropil intrinsic neuron (0.20), secondary neuron (0.16)
- steps 3–4: cascade died out
- motor output: adult VNC neuron, thoracic neuron (motor circuits)
- known biology: startle — antennal mechanosensory → SEZ/AMMC → descending →
  brace/groom/escape (textbook Johnston's organ pathway)
- FLY: "The world jolts — brace."

---

## Files
- subgraphs/sugar.json (forward, honest gap), subgraphs/sugar_backward.json
  (motor-backward, 7 nodes / 17 real edges), subgraphs/looming.json,
  subgraphs/rotten.json, subgraphs/touch.json
- flysim.py (simulator; --inject-hop for backward graphs),
  vfb.py (cached API client), build_graphs.py (forward walker),
  build_sugar_backward.py (motor-backward tracer)
- GAPS.md (honest gaps), build.log (per-hop candidate audit trail)
- cache/ (raw API responses for reproducibility)

## 2026-10-17 — Cory's vision law
For actual looking, plain vision is the sight: the raw frame, no extras.
Motion glow, tracked boxes, redness overlays are analysis, not seeing.
The eye-view render is a diagnostic, not what the eyes see.
