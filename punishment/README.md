# PUNISHMENT

A bottled fly sense: **aversive reinforcement — PPL1 dopamine, the dark twin of reward**,
computed live from real *Drosophila* connectome wiring.

## The honesty contract

- **[REAL]** Every node and edge comes from `../subgraphs/punishment.json`
  (14 nodes, 25 edges), built from the Virtual Fly Brain VFBquery
  API against the **FlyWire FAFB v783** connectome (edge weight = total synapse
  count). Circuit: PPL1-gamma1pedc (FBbt_00100243) + PPL1-alpha3 (FBbt_00110320),
  a documented merged hop 0 (see the JSON's `honest_note` for why: the generic
  PPL1 class queries fail server-side; hop 0 merges the two canonical aversive
  PPL1 DANs whose connectivity is indexed) -> mushroom body intrinsic /
  extrinsic / output neurons -> central brain / lateral horn / dopaminergic
  populations. No neuron, synapse, or connection is invented.
- **[MODEL]** The neural dynamics are a simplified model: normalized
  spread-of-activation with a 0.15 firing threshold, 4 steps, ported from
  ../flysim.py. It approximates neural activity and makes no claim about
  biophysics. But this is real, working infrastructure — real measured wiring
  in, coherent body-state out. Agents run on it.
- **[MODELED]** The valence sign (-1.00) and arousal gain (0.80)
  are design choices, not biology. So is the readout layer: activation is
  read at hop 2 because that is the deepest hop that carries signal
  above the model's threshold on this circuit (hop 1 peaks 0.3965, hop 2
  peaks 0.1956 — both above threshold; hop 2 wins by the deepest-hop rule).
  The `opponent()` contrast note is a documented statement of mushroom body
  compartment organization, not a computed quantity.
- **[FICTION]** Any narrative gloss ("never again") is fiction, not a claim about experience.

## The opponent organization (PAM vs PPL1)

The mushroom body is tiled into compartments, each co-innervated by
dopaminergic neurons (DANs) and mushroom body output neurons (MBONs).
**PAM**-cluster DANs (the reward bottle's circuit) innervate **appetitive**
compartments and drive approach learning; **PPL1**-cluster DANs (this bottle)
innervate **aversive** compartments and drive avoidance learning. Same MB
architecture, opponent valence — reward and punishment are the two halves
of one teaching signal. Call `opponent()` to get the documented contrast.

## API

```python
from punishment import Punishment

p = Punishment()
p.sense(0.8)   # -> {"activation": ..., "valence_delta": ..., "arousal_delta": ...}
p.opponent()   # -> {"punishment": ..., "note": "PAM (reward) and PPL1 ..."}
p.tick(1.0)    # decay the activation
p.state()      # activation, signs, gains, graph
```

`valence_delta = -1.00 x activation`; `arousal_delta = 0.80 x activation`.

## Numbers (`python3 demo.py`, all checks pass)

- `sense(1.0)` -> `{'activation': 0.1956, 'valence_delta': -0.1956, 'arousal_delta': 0.1564}`
- All 8 demo checks pass (`python3 punishment/demo.py`, exit 0):
  cascade fires on real wiring; valence sign correct (negative);
  arousal non-negative and proportional; MB compartments reached
  (hop-1 peak 0.3965, MB-node peak 0.3965); monotonic with intensity;
  `tick()` decays; `opponent()` carries the contrast note;
  zero stimulus reads zero.
- Threshold cliff: injections below ~0.8 read 0.0 on this
  circuit (documented model behavior).

## Known limits

- The model's 0.15 threshold plus fan-out means weak injections read 0.0 —
  the cascade is silent below the cliff, then graded. That's the model being
  honest, not a bug.
- `tick(dt)` decay (0.2/s linear) is modeled.
- The drive/reinforcement dynamics (how PPL1 depresses an MB compartment's
  output over repeated pairings — the actual learning rule) are the
  genuinely unmapped frontier; no API holds them, and this bottle models
  none of them. It senses punishment events; it does not learn.
