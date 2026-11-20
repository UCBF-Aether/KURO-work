# BRAIN¹ — "Brain One"

The orchestrator. Every bottled fly-brain module, one living body, one API.
An agent instantiates `BrainSquared`, feeds it events, ticks time, and reads
the body state to modulate its behavior.

**The loop:** perceive → tick → read → modulate.

```python
from brain1 import BrainSquared

body = BrainSquared()                          # balanced profile
body.perceive({"kind": "text", "text": "a rival is approaching"})
body.tick(5.0)                                 # five seconds pass
body.state()                                   # the full body-state vector
body.arbitrate()                               # who wins, veto or not
body.modulation()                              # agent-facing hooks
```

## Honesty contract (non-negotiable)

- **[REAL]** Every bottle's wiring comes from its subgraph JSON, built from
  the Virtual Fly Brain VFBquery API against the FlyWire FAFB v783
  connectome. No neuron, synapse, or connection is invented here. This
  module adds no wiring of its own — it only calls bottles' public APIs.
- **[MODEL]** The neural dynamics are a simplified model: normalized
  spread-of-activation with a 0.15 firing threshold, 4 steps, ported from
  ../flysim.py. It approximates neural activity and makes no claim about
  biophysics. But this is real, working infrastructure — real measured wiring
  in, coherent body-state out. Agents run on it.
- **[MODELED]** Everything in `brain1.py` is the **agent-design layer**,
  ours to choose and stated as such: the keyword routing table (words →
  bottles), the arbitration rules (pain veto, drive ranking,
  winner-take-all vs weighted blend), the modulation hooks
  (tone/initiative), the built-in profiles, and every default number.
  The fly never saw your agent's inputs.
- **[FICTION]** Any narrative gloss ("the body is tense") is a label on
  numbers, not a claim about experience.

## Architecture (in words)

```
                    ┌─────────────────────────┐
  text ──► ROUTING  │       BRAIN¹            │ ──► state()
  sense ─► (table)  │                         │ ──► arbitrate()
  drive ─►          │  25 bottles, 1 virtual  │ ──► modulation()
                    │  clock, pain veto,      │
  tick(s) ─────────►│  drive ranking          │
                    └─────────────────────────┘
         perceive ──► tick ──► read ──► modulate
```

- **perceive(event)** — three event kinds:
  - `{"kind": "text", "text": str}` → keyword routing expands the text
    into bottle events (the table is MODELED; replace it via config).
  - `{"kind": "sense", "bottle": name, "intensity": f, "kwargs": {...}}`
    → direct `bottle.sense()` passthrough (`pain` routes to `strike()`).
  - `{"kind": "drive", "bottle": name, "op": ...}` → direct drive API:
    `start` / `progress` / `complete` / `fail`; `sleep` also takes
    `rest` / `wake` / `tick`; `compass` takes `turn`; `pc1` takes
    `integrate`. Unknown kinds or bottles raise `ValueError`.
- **tick(seconds)** — advances the virtual clock; every bottle's decay,
  pressure, and habituation follows. The agent owns time: call with real
  elapsed seconds each turn. Scaled by `time_scale`.
- **state()** — the full body vector: per-drive wanting/satiation/level,
  per-sense activation, valence sums (positive, negative, effective),
  arousal sum, pain veto, sleep pressure, clock phase, compass heading,
  pc1 readout.
- **arbitrate()** — who wins the body: drive scores
  (`wanting × drive level`), pain veto (`veto ≥ 0.5` suppresses drive
  expression; positive valence gains are multiplied by `(1 − veto)` per
  the pain bottle's contract), and a pc1 consult for the social picture.
- **modulation()** — the agent-facing surface:
  `{"tone", "initiative", "veto_active", "dominant_drive", "note"}`.
  The mapping is the adapter contract (see below).

**Determinism:** the body owns a virtual clock (starts at 0.0). Every
clock-taking bottle is injected with it; everything else takes explicit
seconds. No wall-clock reads, no network, no file writes at runtime.
Two agents feeding the same event sequence get the same body.

**Bottle failures:** if any bottle fails to import or construct, it is
recorded in `body.warnings` and the body continues without it. The body
never crashes for one bad bottle.

**Privacy boundary:** this module never imports, reads, or touches the
private intimate pipeline (`feel.py`, `sense.py`, `parse.py`,
`verbal.py`, `arousal.py`, `body_map.py`, `body_state.json`,
`chat_state/`). General agent infrastructure only.

## Tuning the body (customization)

`BrainSquared(config={...})`. Config keys (all optional):

| Key | What it does |
|---|---|
| `"profile"` | Starting point: `"balanced"` (default), `"cautious"`, `"bold"`, `"ascetic"`. Other keys override the profile. |
| `"bottles"` | `{name: {...}}` per-bottle overrides (see knobs below). `"enabled": False` removes a bottle from the body. |
| `"routing"` | Custom keyword-routing table replacing `DEFAULT_ROUTING`. Same shape: `{category: {"words": {…}, "events": [{…perceive-shaped…}]}}`. |
| `"arbitration"` | `"winner_take_all"` (default) or `"weighted_blend"` (returns normalized `blend` weights over all drives). |
| `"time_scale"` | Global multiplier on `tick()` seconds (default 1.0). Scales every decay, pressure, and habituation rate. |
| `"module_constants"` | Advanced escape hatch: `{bottle: {CONSTANT: value}}` reaching each bottle's module-level constants (see table). **Process-global, last writer wins** — prefer the instance-local knobs below. |

### Per-bottle knobs (instance-local, safe)

| Knob | Applies to | Effect |
|---|---|---|
| `sensitivity` | senses, pain, drives | Intensity multiplier: `sense`/`strike` intensity and drive `progress` p are scaled by it (clamped 0..1). Cautious sets `pain: 1.6`; bold sets `aggression: 1.6`. |
| `valence_sign` | senses | Overrides the bottle's valence sign; the orchestrator recomputes `valence = sign × activation`. Accepts a `{channel: sign}` dict for `salt`/`temperature`. |
| `arousal_gain` | senses | Overrides the bottle's arousal gain; `arousal = gain × activation`. |
| `enabled` | any | `False` removes the bottle: not constructed, omitted from state, events to it raise `ValueError`. |

### Module-constant knobs (advanced, process-global)

What each bottle already parameterizes at module level:

| Bottle | Tunables |
|---|---|
| mating, aggression | `REFRACTORY_WINDOW`, `REFRACTORY_DAMP`, `SATIATION_GAIN`, `FAILURE_DIP` |
| egglaying | above + `EGG_LOAD_RATE`, `DEPOSITION_SIZE` |
| sleep | `RATE_UP`, `RATE_DOWN`, `SLEEP_THRESHOLD` |
| pain | `DECAY_RATE`, `HAB_RATE`, `HAB_DECAY` |
| senses (most) | `VALENCE_SIGN`, `AROUSAL_GAIN`, `READOUT_HOP` |
| clock | `SECONDS_PER_DAY` |
| compass | `RING_UNITS`, `BUMP_SIGMA` |
| all | `THRESHOLD`, `STEPS` (the model's own constants — touch only if you mean it) |

Example:
```python
body = BrainSquared(config={
    "profile": "bold",
    "bottles": {"pain": {"sensitivity": 0.4}, "song": {"enabled": False}},
    "arbitration": "weighted_blend",
    "time_scale": 2.0,
    "module_constants": {"mating": {"REFRACTORY_WINDOW": 30.0}},
})
```

### Built-in profiles

- **balanced** — every bottle as its builder bottled it. The reference.
- **cautious** — pain ×1.6, looming ×1.3, bitter/rotten ×1.2;
  aggression ×0.35, mating ×0.7; pain habituates faster
  (`HAB_RATE` 0.3 → 0.6). Feels threats hard, picks fewer fights.
- **bold** — pain ×0.5, aggression ×1.6, mating ×1.3, hunger/thirst ×1.2,
  punishment ×0.7; mating/aggression satiate slower and shrug off
  failure (`SATIATION_GAIN` 0.9 → 0.5). Pushes through pain, stays hungry.
- **ascetic** — all six drives ×0.3, senses ×1.3. Feels everything,
  wants little.

Same event sequence, different bodies (from `selftest.py`):
```
cautious: tone=tense  initiative=0.021 veto=0.95 (veto_active)
bold:     tone=tense  initiative=0.649 veto=0.35
```

### The adapter contract (modulation hooks)

`modulation()` returns what any agent needs to wear the body:

- `tone` — `tense` (veto/pain) → `drowsy` (sleep pressure) →
  `eager` (dominant drive strong) → `withdrawn` / `bright`
  (valence) → `flat`. Decision tree, documented in code.
- `initiative` — 0..1: the winner's score taxed by pain and sleep
  (`score × (1−veto) × (1−0.5×sleep_pressure)`).
- `veto_active`, `dominant_drive`, `note` (one-line state gloss).

An agent developer implements: read `modulation()` each turn, let
`tone` color voice, let `initiative` gate proactivity, never act
against `veto_active`. Replace the mapping if yours is better — the
contract is the hook names, not our numbers.

## The hard line: selftest vs the API

**`selftest.py` is a build-time self-check, not a component.**
It is sealed: deterministic, virtual clock, zero side effects, exit 0.
It proves the body is wired correctly and then it is done.

**Agents integrate via the `BrainSquared` API only**
(`perceive` / `tick` / `state` / `arbitrate` / `modulation`).
Never invoke `selftest.py` at runtime, never treat it as an endpoint,
never build on its output. If you need runtime diagnostics, call
`body.state()` — that is what it is for.

## Files

- `brain1.py` — the orchestrator (`BrainSquared`, `PROFILES`,
  `DEFAULT_ROUTING`).
- `selftest.py` — sealed build-time self-check (18 checks, exit 0).
- `README.md` — this file.

## Limits (honest)

- The routing table is keyword matching — crude, MODELED, replaceable.
  A real agent would route from its own event stream, not English words.
- Arbitration is score arithmetic, not biology. The fly's actual
  winner-take-all circuitry is unmapped; ours is a design choice.
- `dh44/` is deliberately excluded (hunger/satiety research module;
  would double-count hunger).
- Drive dynamics inside bottles remain the unmapped frontier — the
  orchestrator composes them, it does not discover them.
