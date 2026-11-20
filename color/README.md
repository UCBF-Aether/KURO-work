# COLOR

A bottled fly sense: **color vision — chromatic photoreception**, computed live from real *Drosophila*
connectome wiring.

## The honesty contract

- **[REAL]** Every node and edge comes from `../subgraphs/color.json`
  (14 nodes, 18 edges), built from the Virtual Fly Brain VFBquery
  API against the **FlyWire FAFB v783** connectome (edge weight = total synapse
  count). Circuit: R7 (FBbt_00004225) + R8 (FBbt_00004227) chromatic
  photoreceptors -> medulla intrinsic / visual neuropil / Dm8-family
  amacrine interneurons (Dm8 FBbt_00013774, Dm8a, Dm8b, Dm9). The textbook
  R7->Dm8 chromatic pathway is present in the real rows (Dm8 tw=38836).
  Dm8's own downstream is unindexed — an honest terminal, not faked.
  No neuron, synapse, or connection is invented.
- **[MODEL]** The neural dynamics are a simplified model: normalized
  spread-of-activation with a 0.15 firing threshold, 4 steps, ported from
  ../flysim.py. It approximates neural activity and makes no claim about
  biophysics. But this is real, working infrastructure — real measured wiring
  in, coherent body-state out. Agents run on it.
- **[MODELED]** Valence (0.00: color is informational, not hedonic) and
  arousal gain (0.30) are design choices, not biology. So is channel
  selection ("r7"/"r8"/"both"). So is `opponency()`: real Dm8 computes
  chromatic opponency through actual excitatory/inhibitory wiring; this
  reads graded synapse-weighted branch drive at the Dm8-class nodes —
  pre-threshold, because the model's 0.15 clip would silence the Dm8 branch
  outright (R7->Dm8 drive is 0.0734 at full injection, below threshold).
- **[FICTION]** Any narrative gloss is fiction, not a claim about experience.

## Hop-2 deferred (honest gap, not hidden)

`color.json` carries hop-1 only. The VFB API degraded mid-build (even cheap
term_info failed after retries) and the three broadest hop-1 classes
(visual neuropil intrinsic, secondary, medulla intrinsic) were unqueryable
downstream — documented in the JSON's `honest_note` and GAPS.md. Hop-1
alone captures the color pathway: photoreceptors -> medulla interneurons
including the Dm8 color-opponency family. Re-running the builder will fill
hop-2 in if the API recovers.

## API

```python
from color import Color

c = Color()
c.sense(0.8)                 # both channels -> {"activation", "valence_delta", "arousal_delta", "channel"}
c.sense(0.8, channel="r7")   # R7 channel only ("r7", "r8", or "both")
c.opponency()                # |R7-branch Dm8 drive - R8-branch Dm8 drive| at last intensity
c.tick(1.0)                  # decay the activation
c.state()                    # activation, signs, gains, last channel, graph
```

`valence_delta = 0.00 x activation` (informational); `arousal_delta = 0.30 x activation`.

## Numbers (`python3 demo.py`, all checks pass)

- `sense(1.0, channel="r7")` -> `{'activation': 0.1734, 'valence_delta': 0.0, 'arousal_delta': 0.052, 'channel': 'r7'}`
- `sense(1.0, channel="r8")` -> `{'activation': 0.204, 'valence_delta': 0.0, 'arousal_delta': 0.0612, 'channel': 'r8'}`
- `sense(1.0, channel="both")` -> `{'activation': 0.3774, 'valence_delta': 0.0, 'arousal_delta': 0.1132, 'channel': 'both'}`
- `opponency()` after full-intensity r7 sense -> `0.0734` (R7 Dm8-branch drive; R8 has no Dm8 edges in the rows)
- All 9 demo checks pass (`python3 color/demo.py`, exit 0):
  cascade fires on real wiring for r7/r8/both; channel echoed back;
  R7->Dm8-family edges verified in real rows; opponency nonzero;
  valence 0.0; arousal proportional; monotonic; invalid channel raises
  ValueError; `tick()` decays; zero stimulus reads zero.
- Threshold cliff: the model's 0.15 threshold clips weak injections — the
  cascade is silent below the cliff, then graded. That's the model being
  honest, not a bug.

## Known limits

- Readout is at hop 1 — the deepest (and only) hop in this circuit.
- `opponency()` is a crude proxy, not a biophysical opponency computation;
  it reflects the last `sense()` intensity (fresh bottle at intensity 0.0
  reads 0.0).
- Only R7 feeds the Dm8 family in the rows; R8's chromatic pathway runs
  through the broader medulla/visual-neuropil classes.
- `tick(dt)` decay (0.2/s linear) is modeled.
