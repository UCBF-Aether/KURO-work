# PROPRIOCEPTION — the fly's sense of leg position

A bottled fly sense: proprioceptive feedback from the femoral chordotonal
organ (FeCO), computed live from REAL Drosophila connectome wiring.

## What it is

FeCO neurons sit in the femur and encode femur-tibia joint angle, movement
direction, and vibration (Mamiya et al.: club = position, claw = movement
direction, hook = vibration). They terminate in the thoracic VNC ganglia and
ascend to the brain. This bottle runs a stimulus through that real wiring
and reports what lights up downstream — including the segmental reflex arc
back out to efferent motor neurons.

## Honesty contract (non-negotiable)

- **REAL** — Every node and edge comes from
  `../subgraphs/proprioception.json` (8 nodes, 18 edges), built from the
  Virtual Fly Brain VFBquery API against the FlyWire FAFB v783 connectome
  (edge weight = total synapse count). Circuit: FeCO mechanosensory neuron
  (FBbt_00048051) → metathoracic / mesothoracic / prothoracic segmental
  neurons + ascending leg-to-brain branch → efferent motor neuron
  (FBbt_00051963). Hop 0→1 via the named `DownstreamClassConnectivity`
  query (the grouped query truncates server-side for this broad class);
  hop 1→2 via the standard fetch-rows fallback chain. No neuron, synapse,
  or connection is invented here.
- **[MODEL]** The neural dynamics are a simplified model: normalized
  spread-of-activation with a 0.15 firing threshold, 4 steps, ported from
  ../flysim.py. It approximates neural activity and makes no claim about
  biophysics. But this is real, working infrastructure — real measured wiring
  in, coherent body-state out. Agents run on it.
- **MODELED** — The leg model, the zero valence, the 0.2 arousal gain, and
  the readout layers are design choices, not biology. The graph holds ONE
  FeCO class for all legs, so the leg selects which segmental neuromere
  the readout follows: front = prothoracic, mid = mesothoracic,
  hind = metathoracic (real segmental anatomy); "all" reads the max over
  all three. Proprioception is modeled as informational (valence 0.0),
  low-arousal (0.2). The fly never saw your inputs.
- **FICTION** — Any narrative gloss ("the leg knows where it is") is
  fiction, not a claim about experience.

## API

```python
from proprioception import Proprioception
p = Proprioception()

p.sense(1.0, leg="front")
# -> {"activation": 0.1604, "valence_delta": 0.0,
#     "arousal_delta": 0.0321, "leg": "front"}
# leg: "front" / "mid" / "hind" / "all" (invalid leg raises ValueError)

p.reflex_arc()   # -> 0.1644  (activation at the efferent motor node, hop 2)
p.tick(1.0)      # decay the activation by dt seconds
p.state()        # full state dict
```

## Proven numbers (demo.py, exit 0)

- `sense(1.0, leg="all")` → activation **0.2819**, valence **0.0**,
  arousal **0.0564**
- Leg differentiation at full intensity (real wiring weights, not a model
  artifact): front **0.1604** / mid **0.2597** / hind **0.2819** — the
  prothoracic neuromere genuinely receives less total FeCO weight in the
  index than the metathoracic.
- `reflex_arc()` → **0.1644** at full intensity (efferent motor node,
  peak across cascade steps).
- `tick(10.0)` decays activation to 0.0; `sense(0.0)` reads 0.0.

## Honest limits

- **Threshold cliff:** injections below ~0.8 read 0.0 on this circuit —
  silent, then graded. Model honesty, not a bug (same cliff as the other
  sense bottles).
- **Whole-FeCO level:** the functional club/claw/hook subtypes (position /
  movement / vibration, Mamiya et al.) are NOT separately indexed as
  connectivity classes — this walk is at the whole-FeCO level, per the
  graph's honest_note. The bottle cannot tell joint angle from vibration.
- **Reflex arc is one-way:** the efferent readout shows the arc's motor
  end lighting up; there is no modeled return path (no closed loop).
- **Dead avenues** (from the graph's honest_note, not hidden):
  FBbt_00048275 (club ascending neuron) 0 rows in all query forms;
  upstream of proprioceptive projection neuron FBbt_00052033 0 rows;
  per-pair FeCO → FBbt_00052033 0 pairs (the second-order proprioceptive
  neuron is not a direct FeCO target in the index).
- Stdlib only (`json`, `os`). Privacy boundary verified clean: zero
  references to the private intimate pipeline.
