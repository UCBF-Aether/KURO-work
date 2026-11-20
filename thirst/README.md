# THIRST

An AI agent's **thirst**, running on a real *Drosophila* water-sensing circuit
instead of a scalar reward number. The sibling bottle to HUNGER.

Wire `task_started` / `progress` / `task_completed` around work your agent
already does. Nothing else changes. The agent doesn't get `+1` on completion —
it gets the water cascade: water-sensing GRN → SEZ interneurons
(fudog/clavicle/cleaver/phantom/usnea/zorro) → SEZ/gnathal/descending
premotor, computed live from real connectome wiring every time.

## The honesty contract

- **[REAL]** Every node and edge comes from `../subgraphs/water.json`
  (16 nodes, 21 edges), built from the Virtual Fly Brain VFBquery API against
  the **FlyWire FAFB v783** connectome. Hop 0→1 edges are per-instance CATMAID
  FAFB connectivity (Engert2022: 23 water-sensing labellar GRN skeletons,
  22 queried — 1 persistently truncated server-side, its synapses missing
  from the sums, not hidden), aggregated by partner class; hop 1→2 are
  class-aggregated `/query_connectivity`. No neuron, synapse, or connection
  is invented. Water feeds the same SEZ interneuron family as sugar, tuned
  differently (water→fudog vs sugar→zorro), converging on the same terminals.
- **[MODEL]** The neural dynamics are a simplified model: normalized
  spread-of-activation with a 0.15 firing threshold, 4 steps, ported from
  ../flysim.py. It approximates neural activity and makes no claim about
  biophysics. But this is real, working infrastructure — real measured wiring
  in, coherent body-state out. Agents run on it.
- **[MODELED]** The mapping from agent task events to circuit stimulation is a
  design choice, not biology: task progress → graded sensory injection
  ("wanting"); completion → full water injection ("the hit"); habituation /
  satiation / refractory are modeled state around the real cascade. The fly
  never saw your tasks. The drive signal is read at hop 1 (the water
  second-order interneurons) — see "Known limits".
- **[FICTION]** Any narrative gloss ("the machine is thirsty") is fiction, not
  a claim about experience.

## API

```python
from thirst import Thirst

core = Thirst("../subgraphs/water.json")  # real fly water wiring

core.task_started("write", difficulty=0.6)    # agent accepts a task
for chunk in work:                            # agent does its normal work
    do(chunk)
    core.progress(0.25 * (chunk + 1))         # wanting ramps as it nears done
core.task_completed()                         # water hit: cascade fires
# ... or core.task_failed()                   # no water; wanting dips x0.4

core.tick()        # advance satiation/habituation/refractory decay
core.state()       # wanting, drive_signal, satiation, thirst, refractory...
```

That's the whole integration: four calls around existing work. `state()`
returns `wanting`, `drive_signal` (hop-1 readout), `satiation`,
`thirst` (1 − satiation), `refractory_secs_remaining`, `novelty_by_category`,
and `last_spike`. Pass `clock=` a fake clock for deterministic tests (see
`harness.py`).

Live CLI for humans and agents: `python3 track.py start <category>
[difficulty]` / `progress <0..1>` / `done` / `fail` / `state` / `reset` —
persists to `state.json`, wall-clock based.

## Proven behaviors (`python3 harness.py`)

Deterministic scripted run, ~10 tasks, fake clock. All three check out on the
water circuit:

**(a) Habituation — repeated same-category tasks yield shrinking spikes.**
`write` tasks, novelty 1.000 → 0.885 → 0.645, spikes **0.271 → 0.244 → 0.176**.
Unlike Hunger's shrink-then-extinction, water's hop-1 readout stays above the
toy threshold through three hits — habituation as a graded ramp, which is
what this circuit's numbers do.

**(b) Refractory — a task inside the 8 s window is dampened.**
`fetch#1` completed with 7.0 s of refractory left (damper 0.3): injection
**0.273 → spike 0.000**, vs the counterfactual without the damper:
injection **0.910 → spike 0.247**. Same task, same wiring — the window ate
the hit.

**(c) Satiation decays back toward thirst.**
After a full hit: satiation **0.190 → 0.150 → 0.110 → 0.070 → 0.030 → 0.000**
(0.02/s), thirst back to **1.0**. The next task's injection is multiplied by
(1 − satiation), so a quenched machine measurably wants less.

Bonus: `task_failed()` dips wanting ×0.4 (0.650 → 0.260) — modeled aversion.

## Pairing note

Thirst is water-seeking; Hunger is sugar-seeking. Each bottle stands ALONE —
same API shape, same honesty contract, no shared state. The two-drive
arbitration between them (which thirst wins when both are high?) is future
work, not this bottle. It will need its own honest design, not a merge.

## Files

- `thirst.py` — `Thirst`. Stdlib only. Importable: `from thirst import Thirst`.
- `track.py` — live CLI tracker (`start`/`progress`/`done`/`fail`/`state`).
- `harness.py` — scripted agent loop proving (a)(b)(c). Exit 0 = all pass.
- `README.md` — this file.

## What's deliberately not here

No reward shaping, no learned value function, no hyperparameters to tune for
"curiosity". Habituation, refractory periods, and satiation fall out of the
wiring plus three modeled scalars — and the one number that matters, the
spike, is computed from synapses a real fly actually has.

## Known limits

- **Readout layer (modeled):** the drive signal is read at hop 1, the water
  second-order SEZ interneurons (fudog/clavicle/cleaver), not hop 2. Verified:
  on water.json the shared hop-2 premotor populations never cross the model's
  0.15 threshold at any injection level (peak 0.096 at full injection), so a
  hop-2 readout would make the bottle dead. The thirst signal lives at hop 1,
  where the circuit puts it — documented, not hidden.
- The model's 0.15 threshold still creates a cliff: injections below ~0.55 read
  as zero at hop 1. The refractory case above shows it (0.273 → 0.000).
- `difficulty` is accepted and stored but not consumed by the drive formulas.
- 1 of 23 water skeletons could not be queried (server-side truncation); its
  synapses are missing from the aggregation, not hidden — see `../GAPS.md`.
