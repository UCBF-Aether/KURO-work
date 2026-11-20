# BITTER

A bottled fly sense: **bitter taste — aversive gustation**, computed live from real *Drosophila*
connectome wiring.

## The honesty contract

- **[REAL]** Every node and edge comes from `../subgraphs/bitter.json`
  (14 nodes, 24 edges), built from the Virtual Fly Brain VFBquery
  API against the **FlyWire FAFB v783** connectome (edge weight = total synapse
  count). Circuit: bitter-sensing GRN -> CB0159 / SEZ / gnathal interneurons. No neuron, synapse, or connection is invented.
- **[MODEL]** The neural dynamics are a simplified model: normalized
  spread-of-activation with a 0.15 firing threshold, 4 steps, ported from
  ../flysim.py. It approximates neural activity and makes no claim about
  biophysics. But this is real, working infrastructure — real measured wiring
  in, coherent body-state out. Agents run on it.
- **[MODELED]** The valence sign (-1.00) and arousal gain (0.6)
  are design choices, not biology. So is the readout layer: activation is
  read at hop 1 because that is the deepest hop that carries signal
  above the model's threshold on this circuit (hop 2 never crosses threshold on this circuit — the signal lives at the second-order layer, as in the THIRST bottle).
- **[FICTION]** Any narrative gloss is fiction, not a claim about experience.

## API

```python
from bitter import Bitter

s = Bitter()
s.sense(0.8)   # -> {"activation": ..., "valence_delta": ..., "arousal_delta": ...}
s.tick(1.0)    # decay the activation
s.state()      # activation, signs, gains, graph
```

`valence_delta = -1.00 x activation`; `arousal_delta = 0.6 x activation`.

## Numbers (`python3 demo.py`, all checks pass)

- `sense(1.0)` -> `{'activation': 0.2606, 'valence_delta': -0.2606, 'arousal_delta': 0.1563}`
- All 6 demo checks pass (`python3 bitter/demo.py`, exit 0):
  cascade fires on real wiring; valence sign correct;
  arousal non-negative and proportional; monotonic with
  intensity; `tick()` decays; zero stimulus reads zero.
- Threshold cliff: injections below ~0.8 read 0.0 on this
  circuit (documented model behavior).

## Known limits

- The model's 0.15 threshold plus fan-out means weak injections read 0.0 —
  the cascade is silent below the cliff, then graded. That's the model being
  honest, not a bug.
- `tick(dt)` decay (0.2/s linear) is modeled.
