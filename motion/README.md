# MOTION — bottled fly motion vision

The fly sees movement. T4 (ON-edge) and T5 (OFF-edge) direction-selective
detectors drive the lobula plate tangential (LPTC) wide-field system —
computed live from REAL Drosophila connectome wiring.

## Honesty contract (non-negotiable)

- **REAL** — Every node and edge comes from `../subgraphs/motion.json`
  (11 nodes, 27 edges), built from the Virtual Fly Brain VFBquery API
  against the FlyWire FAFB v783 connectome. T4 = FBbt_00003731, T5 =
  FBbt_00003736. The textbook T4/T5 → LPTC pathway landed on real rows
  (T4→LPTC tw=282410, T5→LPTC tw=529105); both synapse onto the SAME
  shared LPTC classes. Hop-2 reaches secondary and columnar classes.
  No neuron, synapse, or connection is invented here.
- **[MODEL]** The neural dynamics are a simplified model: normalized
  spread-of-activation with a 0.15 firing threshold, 4 steps, ported from
  ../flysim.py. It approximates neural activity and makes no claim about
  biophysics. But this is real, working infrastructure — real measured wiring
  in, coherent body-state out. Agents run on it.
- **MODELED** — Direction selection ("on"/"off"/"both") is an interface
  choice: it injects at the T4 node, the T5 node, or both. Valence 0.00
  is a design choice (motion is informational, not valenced — unlike
  taste or pain). Arousal gain 0.40 is a design choice. Readout at hop 1
  (lobula plate tangential/intrinsic/giant, wide-field columnar, visual
  neuropil intrinsic): the deepest hop that carries graded signal above
  threshold at full injection — hop 2 never clears the model's threshold
  on this circuit (same documented precedent as the THIRST/DH44/bitter
  bottles). The fly never saw your inputs.
- **FICTION** — Any narrative gloss is fiction, not a claim about
  experience.

## API

```python
from motion import Motion
s = Motion()
s.sense(0.8, direction="on")    # T4 ON-edge detectors
s.sense(0.8, direction="off")   # T5 OFF-edge detectors
s.sense(0.8)                    # both (default)
s.tick(1.0)                     # decay activation by dt seconds
s.state()                       # current sense state
```

`sense()` returns `{activation, valence_delta, arousal_delta, direction}`.
`valence_delta` is always 0.0 by design; `arousal_delta` = 0.40 ×
activation.

## Proven numbers (`demo.py`, 15 checks, exit 0)

- `sense(1.0, "on")` → activation **0.4705**, valence 0.0, arousal 0.1882
- `sense(1.0, "off")` → activation **0.4389**, valence 0.0, arousal 0.1756
- `sense(1.0, "both")` → activation **0.9094**, valence 0.0, arousal 0.3638
- Ring: four right turns are the compass bottle's job — this bottle
  reports movement, not heading.

## Honest limits

- **Threshold cliff**: injections below ~0.68 read 0.0 — the cascade is
  silent, then graded. Model being honest, not a bug.
- **Readout at hop 1** (MODELED, documented): hop 2 dies below the
  model's 0.15 threshold on this circuit — reading there would make the
  bottle nearly silent. Hop 1 (the LPTC classes) is where the circuit
  actually speaks.
- **No direction selectivity in the dynamics**: the model does not compute
  preferred directions or opponent motion — "on"/"off" selects which
  hop-0 population is injected, on the same shared wiring. Real
  direction tuning is not modeled.
- `sense()` takes no duration or velocity — a single intensity number.
- stdlib only (`json`, `os`, `sys`). Zero references to the private
  intimate pipeline.
