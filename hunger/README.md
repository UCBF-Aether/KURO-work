# HUNGER

An AI agent's **hunger**, running on the REAL *Drosophila* hunger-drive
wiring instead of a scalar reward number — re-grounded 2026-10-14 from the
sweet-taste proxy onto the true interoceptive drive.

Wire `task_started` / `progress` / `task_completed` around work your agent
already does. Nothing else changes. The agent doesn't get `+1` on completion —
it gets the DH44 cascade: DH44 pars intercerebralis hunger neuron → ring
gland projection / gut-innervating / SEZ / gnathal populations, computed live
from real connectome wiring every time.

## The honesty contract

- **[REAL]** Every node and edge comes from `../subgraphs/dh44.json`
  (18 nodes, 21 edges), built from the Virtual Fly Brain VFBquery API against
  the **FlyWire FAFB v783** connectome (class-aggregated connectivity, edge
  weight = total synapse count). No neuron, synapse, or connection is
  invented. DH44 neurons are the fly's actual hunger-sensing cells.
  Previously the default was `../subgraphs/sugar_forward.json` (the SOLVED
  sweet-taste chain, 10 nodes / 18 edges, per-instance CATMAID FAFB
  connectivity cross-validated against the motor-backward trace) — still
  loadable via `Hunger("../subgraphs/sugar_forward.json")`, as is
  `../subgraphs/reward.json` (PAM dopamine → mushroom body).
- **[MODEL]** The neural dynamics are a simplified model: normalized
  spread-of-activation with a 0.15 firing threshold, 4 steps, ported from
  ../flysim.py. It approximates neural activity and makes no claim about
  biophysics. But this is real, working infrastructure — real measured wiring
  in, coherent body-state out. Agents run on it.
- **[MODELED]** The mapping from agent task events to circuit stimulation is a
  design choice, not biology: task progress → graded DH44 injection
  ("wanting"); completion → full-strength injection ("the hit");
  habituation / satiation / refractory are modeled state around the real
  cascade. The drive signal reads the **hop-1 max** (not hop-2): on dh44.json
  the hop-2 fan-out dilutes below the model's firing threshold while hop-1
  (ring gland / gut / SEZ) carries the graded signal — a readout-layer
  choice, documented here; the cascade logic is identical. The fly never saw
  your tasks.
- **[FICTION]** Any narrative gloss ("the machine is hungry") is fiction, not
  a claim about experience.

## API

```python
from hunger import Hunger

core = Hunger()  # default: real DH44 hunger-drive wiring

core.task_started("write", difficulty=0.6)    # agent accepts a task
for chunk in work:                            # agent does its normal work
    do(chunk)
    core.progress(0.25 * (chunk + 1))         # wanting ramps as it nears done
core.task_completed()                         # the hit: DH44 cascade fires
# ... or core.task_failed()                   # no hit; wanting dips x0.4

core.tick()        # advance satiation/habituation/refractory decay
core.state()       # wanting, drive_signal, satiation, hunger, refractory...
```

That's the whole integration: four calls around existing work. `state()`
returns `wanting`, `drive_signal` (DH44 hop-1 readout), `satiation`,
`hunger` (1 − satiation), `refractory_secs_remaining`, `novelty_by_category`,
and `last_spike`. Pass `clock=` a fake clock for deterministic tests (see
`harness.py`), `graph_path=` for another circuit (`readout_hop` defaults to
1 for the DH44 default graph, 2 otherwise). `DriveCore` remains as a
backwards-compatible alias.

Live CLI for humans and agents: `python3 track.py start <category>
[difficulty]` / `progress <0..1>` / `done` / `fail` / `state` / `reset` —
persists to `state.json`, wall-clock based.

## Proven behaviors (`python3 harness.py`)

Deterministic scripted run, ~10 tasks, fake clock. All three check out on
the DH44 drive circuit:

**(a) Habituation — repeated same-category tasks yield shrinking spikes
(graded, no extinction).**
`write` tasks, novelty 1.000 → 0.885 → 0.645, spikes **0.389 → 0.351 →
0.254**. The DH44 hop-1 readout stays graded where the old sugar circuit
extinguished — a circuit difference, documented not hidden.

**(b) Refractory — a task inside the 8 s window is dampened.**
`fetch#1` completed with 7.0 s of refractory left (damper 0.3): injection
**0.248 → spike 0.000**, vs the counterfactual without the damper:
injection **0.827 → spike 0.322**. Same wiring — the window ate the hit.

**(c) Satiation decays back toward hunger.**
After a full hit: satiation **0.273 → 0.233 → … → 0.033 → 0.000**
(0.02/s), hunger back to **1.0**. The next task's injection is multiplied by
(1 − satiation), so a sated machine measurably wants less.

Bonus: `task_failed()` dips wanting ×0.4 (0.650 → 0.260) — modeled aversion.

## Files

- `hunger.py` — `Hunger` (alias `DriveCore`). Stdlib only.
  Importable: `from hunger import Hunger`.
- `track.py` — live CLI tracker (`start`/`progress`/`done`/`fail`/`state`).
- `harness.py` — scripted agent loop proving (a)(b)(c). Exit 0 = all pass.
- `README.md` — this file.

## What's deliberately not here

No reward shaping, no learned value function, no hyperparameters to tune for
"curiosity". Habituation, refractory periods, and satiation fall out of the
wiring plus three modeled scalars — and the one number that matters, the
spike, is computed from synapses a real fly actually has.

## Known limits

- The drive signal reads hop-1 (MODELED choice): on dh44.json the hop-2
  fan-out never crosses the model's 0.15 threshold (peak 0.096 at full
  injection), while hop-1 (ring gland / gut / SEZ) is graded 0.195–0.389.
- `difficulty` is accepted and stored but not consumed by the drive formulas.
- For the full hunger/satiety axis (DH44 wanting + IPC satiety as separate
  circuits), see the sibling bottle `../dh44/` — HUNGER keeps the classic
  single-circuit drive shape with DH44 wiring.
