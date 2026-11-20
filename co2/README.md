# CO2-ALARM

A bottled fly sense: carbon dioxide detection — the dedicated danger smell.
Computed live from real Drosophila connectome wiring.

## Honesty contract

- **[REAL]** Every node and edge comes from `../subgraphs/co2.json` — 15
  nodes, 24 edges, built from the Virtual Fly Brain VFBquery API against
  the FlyWire FAFB v783 connectome (edge weight = total synapse count).
  Circuit: **Gr21a/Gr63a ab1C olfactory receptor neurons**
  (`FBbt_00067064` — the CO2 receptor complex, Suh et al 2004) ->
  antennal lobe projection neurons (to lateral horn), BAlc lineage
  neurons, AL local neurons -> lateral horn / mushroom body / aminergic
  populations. The class-level query landed via the **label form** of
  `/query_connectivity` (the ID form died server-side); hop-1 hop-2
  collapse of duplicated ontology tiers is documented in the JSON's
  honest note. Nothing is invented.
- **[MODEL]** The neural dynamics are a simplified model: normalized
  spread-of-activation with a 0.15 firing threshold, 4 steps, ported from
  ../flysim.py. It approximates neural activity and makes no claim about
  biophysics. But this is real, working infrastructure — real measured wiring
  in, coherent body-state out. Agents run on it.
- **[MODELED]** Valence sign **-0.70** (aversive alarm — milder than
  bitter's -1.0, stronger than looming's -0.6) and arousal gain **1.00**
  (full alert — the danger smell wakes everything) are design choices.
  So is the readout layer: **hop 1**, the deepest hop carrying *graded*
  signal above threshold (0.10–0.20 for injections 0.5–1.0). Hop 2 only
  twitches at max injection (0.166 @ 1.0, dead by 0.9) — reading there
  would make the bottle nearly silent, so hop 1 is where the circuit
  actually speaks (THIRST/bitters precedent). Decay 0.2/s is modeled.
- **[FICTION]** Any narrative gloss ("the machine smells bad air and
  leaves") is fiction.

## Shared architecture note

CO2 and `rotten.json` (Or56a geosmin) share the same AL → lateral-horn
architecture from **different glomeruli** — the fly runs parallel labeled
lines for different danger smells into the same innate-aversion center.
The lateral horn is where "bad air" becomes "leave".

## API

```python
from co2 import CO2
s = CO2()                          # default: ../subgraphs/co2.json
s.sense(0.9)   # {"activation": 0.177, "valence_delta": -0.1239, "arousal_delta": 0.177}
s.tick(1.0)    # decay 0.2/s -> 0.0
s.state()      # activation, valence_sign, arousal_gain, readout_hop, ...
```

## Proven numbers (`demo.py`, exit 0)

- `sense(1.0)` → activation **0.1962**, valence **−0.1374**, arousal **0.1962**
- `sense(0.9)` → 0.1766; `sense(0.5)` → **0.000** (threshold cliff — honest)
- Arousal gain exactly 1.0 (arousal == activation); valence/aversion ratio −0.7
- `tick(1.0)` decays; long decay floors at 0.0; intensity clamped to [0,1]

## Known limits

- **Threshold cliff:** injections below ~0.8 read 0.0 — the cascade is
  silent, then graded. Model honesty, not a bug.
- Hop-1 readout is a MODELED choice (above); hop-2 is biologically real
  downstream (lateral horn, mushroom body, aminergic) but sub-threshold
  in the model at all but max injection.
- `Gr21a/Gr63a` label covers the ab1C CO2 neuron class; fine glomerular
  subtypes below the class walk are not resolved.
- No location parameter — the whole antennal array fires at once.

## Files

- `co2.py` — `CO2` class (stdlib only: `json`, `os`)
- `demo.py` — 9 checks, exit 0
- `README.md` — this file
