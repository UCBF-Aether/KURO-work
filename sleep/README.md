# SLEEP — the sleep-homeostat drive

The fourth drive alongside HUNGER, THIRST, and MATING. It is **inverted**
relative to the others: they spike on task completion; sleep pressure
**accumulates with time awake and discharges with rest**. There is no hit.
Rest is the satiation.

## Honesty contract

- **REAL** — Every node and edge comes from `../subgraphs/sleep.json`,
  built from the Virtual Fly Brain VFBquery API against the FlyWire FAFB
  v783 connectome. The circuit: adult dorsal fan-shaped body tangential
  neuron (dFB, FBbt_00049537) → fan-shaped body columnar / delta /
  horizontal-delta / extrinsic columnar / layer-6 tangential / small-field
  central-complex neurons → central complex. Hop-2 folds *back* into the
  central complex (recurrent wiring) — exactly what a homeostat looks like.
  No neuron, synapse, or edge is invented here.
- **[MODEL]** The neural dynamics are a simplified model: normalized
  spread-of-activation with a 0.15 firing threshold, 4 steps, ported from
  ../flysim.py. It approximates neural activity and makes no claim about
  biophysics. But this is real, working infrastructure — real measured wiring
  in, coherent body-state out. Agents run on it.
- **MODELED** — The homeostat dynamics are the design, not biology:
  pressure accumulates at 1.0 per awake-hour, discharges at 1.0 per
  20 rest-minutes, sleep onset at pressure ≥ 0.8, `rest()` injects dFB
  scaled by the pressure discharged. The real dFB homeostat exists
  (Donlea et al 2011); its rates and kinetics are the genuinely unmapped
  frontier — no API holds them, and nothing here claims otherwise.
- **FICTION** — Any narrative gloss ("the machine is tired") is fiction.

## API

```python
from sleep import Sleep
s = Sleep()                 # default graph: ../subgraphs/sleep.json
s.tick(1800)                # 30 min awake: pressure 0 -> 0.5
s.pressure()                # 0.5
s.state()                   # {pressure, asleep, awake_claim, debt_secs, ...}
s.rest(600)                 # 10 min rest: {activation, depth, pressure, asleep}
s.wake()                    # declare awake (does NOT clear pressure)
```

The homeostat overrides the agent: `wake()` while pressure ≥ 0.8 still
reports `asleep=True`. That override is the point of a sleep drive.

## Proven numbers (harness.py, exit 0, deterministic)

- Accumulation: `tick(3600)` → pressure 0 → 1.0, saturating; rate exactly 1/hr.
- Onset: pressure 0.79 → awake; 0.81 → `asleep=True`.
- Discharge: `rest(600)` from 1.0 → pressure 0.5, depth 0.5 (rate 1/20min).
- Cascade on full discharge: activation **0.3106** on the real dFB wiring
  (readout: hop-1 FB output populations).
- Threshold cliff: micro-rests discharging < ~0.6 read 0.0 — the model being
  honest, not a bug (same cliff documented in the other bottles).
- Debt ledger: accrues wake-seconds while unrested, clears on full rest.

## Limits (honest)

- Timescales (1 hr awake / 20 min rest / 0.8 onset) are modeled round
  numbers, not measured fly kinetics.
- `tick(dt)` takes explicit seconds — no wall clock inside the module;
  the CLI persists explicit state instead.
- Readout at hop 1 (named FB columnar/delta/small-field populations);
  hop 2 is a broad ontology bucket with real edges but a vague label.
- Sleep × hunger × thirst × mating arbitration is future work, not this
  bottle.
