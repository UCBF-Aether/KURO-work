# DH44 — the true interoceptive drive

An AI agent's **hunger**, running on the REAL *Drosophila* hunger/satiety
axis instead of a scalar reward number — and instead of the sweet-taste proxy
that HUNGER v1 used.

Two real circuits, one drive:
- **DH44** (`../subgraphs/dh44.json`, 18 nodes / 21 edges): the fly's pars
  intercerebralis hunger-sensing neurons → ring gland projection /
  gut-innervating / SEZ / gnathal / Ms PI / serotonergic populations.
  Task progress injects here ("wanting").
- **IPC** (`../subgraphs/ipc.json`, 19 nodes / 23 edges): insulin-producing
  cells → ring gland / gut / SEZ / CB0991 / DM2 / DPMpm1. Task completion
  injects here — in real biology insulin signaling opposes the DH44 hunger
  drive, so completion lands as **satiety**, not sugar.

Wire `task_started` / `progress` / `task_completed` around work your agent
already does. Nothing else changes.

## The honesty contract

- **[REAL]** Every node and edge comes from `dh44.json` and `ipc.json`,
  built from the Virtual Fly Brain VFBquery API against the **FlyWire
  FAFB v783** connectome (class-aggregated connectivity, edge weight =
  total synapse count). No neuron, synapse, or connection is invented.
- **[MODEL]** The neural dynamics are a simplified model: normalized
  spread-of-activation with a 0.15 firing threshold, 4 steps, ported from
  ../flysim.py. It approximates neural activity and makes no claim about
  biophysics. But this is real, working infrastructure — real measured wiring
  in, coherent body-state out. Agents run on it.
- **[MODELED]** The mapping from agent task events to circuit stimulation is
  a design choice, not biology:
  - progress → graded DH44 injection ("wanting");
  - completion → full IPC injection ("the satiety hit"; IPC opposes DH44
    hunger in real biology);
  - the drive readout is the **hop-1 max** (not hop-2): on these circuits
    the hop-2 fan-out dilutes below the model's firing threshold, while hop-1
    (ring gland / gut / SEZ populations) carries the graded signal. A
    readout-layer choice, documented here — the cascade logic is
    byte-identical to the other bottles.
  - habituation / satiation / refractory are modeled state around the real
    cascades. The fly never saw your tasks.
- **[FICTION]** Any narrative gloss ("the machine is hungry") is fiction, not
  a claim about experience.

## API

```python
from dh44 import Dh44

core = Dh44()  # DH44 drive + IPC satiety, real fly wiring

core.task_started("write", difficulty=0.6)    # agent accepts a task
for chunk in work:                            # agent does its normal work
    do(chunk)
    core.progress(0.25 * (chunk + 1))         # wanting ramps as it nears done
core.task_completed()                         # satiety hit: IPC cascade fires
# ... or core.task_failed()                   # no satiety; wanting dips x0.4

core.tick()        # advance satiation/habituation/refractory decay
core.state()       # wanting, drive_signal, satiation, hunger, refractory...
```

`state()` returns `wanting`, `drive_signal` (DH44 hop-1 readout),
`satiation`, `hunger` (1 − satiation), `refractory_secs_remaining`,
`novelty_by_category`, `last_spike` (IPC readout), plus `drive_circuit` and
`satiety_circuit` filenames. Pass `clock=` a fake clock for deterministic
tests (see `harness.py`). Custom graphs via
`Dh44(drive_graph=..., satiety_graph=...)`.

Live CLI: `python3 track.py start <category> [difficulty]` /
`progress <0..1>` / `done` / `fail` / `state` / `reset`.

## Proven behaviors (`python3 harness.py`)

Deterministic scripted run, ~10 tasks, fake clock. All three check out:

**(a) Habituation — repeated same-category tasks yield shrinking satiety
spikes (graded, no extinction).**
`write` tasks, novelty 1.000 → 0.885 → 0.645, spikes **0.475 → 0.428 →
0.309**. The IPC hop-1 readout stays graded where HUNGER's sugar circuit
extinguishes — a circuit difference, documented not hidden.

**(b) Refractory — a task inside the 8 s window is dampened.**
Completed with 7.0 s of refractory left (damper 0.3): injection **0.230 →
spike 0.000**, vs the counterfactual without the damper: injection **0.768
→ spike 0.364**. Same wiring — the window ate the hit.

**(c) Satiation decays back toward hunger.**
After a full hit: satiation **0.332 → 0.292 → … → 0.012 → 0.000**
(0.02/s), hunger back to **1.00**.

Bonus: `task_failed()` dips wanting ×0.4 — modeled aversion.

## Files

- `dh44.py` — `Dh44`. Stdlib only. Importable: `from dh44 import Dh44`.
- `track.py` — live CLI tracker.
- `harness.py` — scripted agent loop proving (a)(b)(c). Exit 0 = all pass.
- `README.md` — this file.

## What's deliberately not here

No reward shaping, no learned value function, no hyperparameters to tune for
"curiosity". Habituation, refractory periods, and satiation fall out of the
wiring plus three modeled scalars — and the two numbers that matter (the
wanting readout, the satiety spike) are computed from synapses a real fly
actually has.
