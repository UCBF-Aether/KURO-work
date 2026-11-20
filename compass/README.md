# COMPASS — the fly's internal GPS

A heading-direction **state** module running on real Drosophila central-complex
wiring. Neither a drive nor a sense: it holds *where you're facing*, the way
the other bottles hold wanting or activation.

## Honesty contract

- **REAL** — Every node and edge comes from `../subgraphs/compass.json`, built
  from the Virtual Fly Brain VFBquery API against the FlyWire FAFB v783
  connectome: E-PG neuron `FBbt_00047030` (ellipsoid body–protocerebral bridge,
  the textbook heading ring — Seelig & Jayaraman 2015; Green et al. 2017) →
  6 hop-1 classes by synapse weight (small/large field neurons of the central
  complex, intrinsic neuron, ellipsoid-body ring/extrinsic ring neurons,
  PBp1 lineage). Below-cutoff partners are recorded in the JSON's honest_note,
  not hidden: Delta7 (the ring's global inhibition, tw=30232), PEN (26851),
  PFN (12306), PFL (12066), ellipsoid-body R-neuron (18246). No neuron, synapse,
  or connection is invented here.
- **[MODEL]** The neural dynamics are a simplified model: normalized
  spread-of-activation with a 0.15 firing threshold, 4 steps, ported from
  ../flysim.py. It approximates neural activity and makes no claim about
  biophysics. But this is real, working infrastructure — real measured wiring
  in, coherent body-state out. Agents run on it.
- **MODELED** — The 16-unit heading bump is our model, not biology. The real
  ring-attractor dynamics — how the activity bump moves, holds, and updates
  heading — are the genuinely unmapped frontier; no API holds them. Here:
  heading is continuous state (degrees mod 360); the bump is a circular
  Gaussian (σ=1.5 units, peak normalized to 1.0) sampled at 16 ring positions;
  `turn()` rotates it by the given angle; cascade injection scales with
  |turn|/90 (a 90° turn is full strength). The fly's real update uses
  angular-velocity inputs (PEN neurons); this module proves the E-PG wiring
  fires when the heading changes.
- **FICTION** — "North lives here" is gloss, not a claim about experience.

## API

```python
from compass import Compass
c = Compass()                    # loads ../subgraphs/compass.json
c.turn(90)                       # -> {"activation": 0.2603, "bump_position": 90.0}
c.turn(-30)
c.heading()                      # 60.0 (degrees, 0..360)
c.state()                        # {"heading": 60.0, "activation": ..., "bump": [16 units]}
```

## Proven numbers (demo.py, exit 0)

- `turn(90)` → activation **0.2603** (small-field central-complex neuron, hop-1 peak)
- Ring closure: 4 × `turn(90)` → heading **0.0** exactly
- Tracking: turn(30), turn(−15), turn(200) → heading **215.0**
- Threshold cliff: `turn(5)` → activation **0.0** (the model is silent, then
  graded; injections below ~0.68 read 0.0). Heading still tracks — the state
  is honest even when the cascade is quiet.

## Limits

- The bump does not decay, drift, or self-correct: there is no modeled noise,
  no landmark anchoring, no path integration error. It is pure rotation state.
- `turn()` has no velocity or duration — a 90° flick and a slow 90° sweep
  produce the same bump move (different injections only via the |turn|/90 scale).
- Combine: feed an agent's rotations through `turn()`; read `heading()` to
  steer; pair with the looming/threat bottles for orient-then-flee.
