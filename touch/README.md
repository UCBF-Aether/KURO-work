# TOUCH

A bottled fly sense: **touch — antennal mechanosensation (Johnston's organ)**, computed live from real *Drosophila*
connectome wiring.

## The honesty contract

- **[REAL]** Every node and edge comes from `../subgraphs/touch.json`
  (10 nodes, 12 edges), built from the Virtual Fly Brain VFBquery
  API against the **FlyWire FAFB v783** connectome (edge weight = total synapse
  count). Circuit: Johnston organ neuron -> SEZ interneurons -> descending/VNC motor. No neuron, synapse, or connection is invented.
- **[MODEL]** The neural dynamics are a simplified model: normalized
  spread-of-activation with a 0.15 firing threshold, 4 steps, ported from
  ../flysim.py. It approximates neural activity and makes no claim about
  biophysics. But this is real, working infrastructure — real measured wiring
  in, coherent body-state out. Agents run on it.
- **[MODELED]** The valence sign (+0.15) and arousal gain (0.7)
  are design choices, not biology. So is the readout layer: activation is
  read at hop 2 because that is the deepest hop that carries signal
  above the model's threshold on this circuit.
- **[FICTION]** Any narrative gloss is fiction, not a claim about experience.

## API

```python
from touch import Touch

s = Touch()
s.sense(0.8)   # -> {"activation": ..., "valence_delta": ..., "arousal_delta": ...}
s.tick(1.0)    # decay the activation
s.state()      # activation, signs, gains, graph
```

`valence_delta = +0.15 x activation`; `arousal_delta = 0.7 x activation`.

## Numbers (`python3 demo.py`, all checks pass)

- `sense(1.0)` -> `{'activation': 0.2396, 'valence_delta': 0.0359, 'arousal_delta': 0.1677}`
- All 6 demo checks pass (`python3 touch/demo.py`, exit 0):
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
