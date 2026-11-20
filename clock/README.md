# CLOCK — the fly's sense of time

A circadian **state** module (like the compass, neither drive nor sense):
holds time-of-day on real LNv pacemaker wiring. Tick it alongside everything
else; read `is_night()` to gate sleep pressure, `time_of_day()` to schedule
feeding.

## Honesty contract

- **REAL** — every node and edge comes from `../subgraphs/clock.json`,
  built from the Virtual Fly Brain VFBquery API against the FlyWire FAFB
  v783 connectome: LNv neuron `FBbt_00004046` (657 grouped rows, first try)
  → pacemaker / SLPpl1 / visual neuropil / accessory medulla / DN period /
  LHd2 populations. The specific subclasses s-LNv (`FBbt_00003764`) and
  l-LNv (`FBbt_00003763`) are unindexed (0 rows, every form) — recorded in
  the JSON's honest_note, not hidden. No neuron, synapse, or connection is
  invented here.
- **[MODEL]** The neural dynamics are a simplified model: normalized
  spread-of-activation with a 0.15 firing threshold, 4 steps, ported from
  ../flysim.py. It approximates neural activity and makes no claim about
  biophysics. But this is real, working infrastructure — real measured wiring
  in, coherent body-state out. Agents run on it.
- **MODELED** — the circadian phase is OUR model, not biology. The REAL
  24-hour molecular oscillator (per/tim feedback loops, PDF cycling,
  phase-response curves) is the genuinely unmapped frontier; no API holds
  it. Specifically modeled here:
  - phase in [0, 1), advancing dt/86400 per tick; phase 0 = dawn, 0.5 = dusk
  - PDF-output curve `pdf = max(0, sin(2*pi*phase))` — a smooth day/night
    envelope peaking at mid-day. The real PDF cycle peaks near dawn under
    molecular-clock control; this curve is a stand-in.
  - night DEFINED as phase in [0.5, 1.0) — a convention, not a finding
  - cascade injection scales with pdf, so the LNv chain fires hardest at
    mid-day and goes quiet at night
- **FICTION** — narrative one-liners ("dawn lives here") are gloss, not
  claims about experience.

## API

```python
from clock import Clock
c = Clock()                    # default: ../subgraphs/clock.json
c.tick(3600)                   # advance 1 hour -> {activation, phase, pdf}
c.phase()                      # 0..1, 0 = dawn
c.time_of_day()                # hours since dawn [0, 24)
c.is_night()                   # True when phase in [0.5, 1.0)
c.state()                      # {phase, pdf, activation}
```

## Proven numbers (`demo.py`, exit 0)

- Cascade fires on real wiring: `activation = 0.2105` at mid-day
  (adult pacemaker neuron, the top hop-1 node by synapse weight)
- Phase advances exactly 1.0 per 86400s; wraps cleanly
- `pdf = 1.0` at mid-day (phase 0.25), `0.0` at mid-night (phase 0.75)
- `time_of_day()` 6.0 at mid-day, 18.0 at mid-night
- Threshold cliff: the cascade goes quiet at night by design (pdf = 0 →
  injection 0) — the phase state stays honest while the wiring sleeps

## Known limits

- No entrainment: light doesn't reset the phase (no light-input wiring in
  the graph); the clock free-runs from wherever it starts.
- No dawn/dusk anticipation, no temperature compensation — the real clock's
  signature tricks, all unmapped.
- `tick()` takes explicit seconds; no wall clock inside the module.
- Combine: `sleep.tick()` pressure should gate on `clock.is_night()`;
  feeding windows on `clock.time_of_day()` — arbitration across modules
  is future work, not this bottle.

Stdlib only (`json`, `math`, `os`). The private intimate pipeline was
never touched or imported.
