# TOUCH QUALITIES — bottled fly sense

Campaniform + bristle mechanosensation: the fly's sense of strain, vibration,
and touch — computed live from real connectome wiring plus literature-bridged
bristle pathways.

## Honesty contract

- **[REAL]** The campaniform path is measured wiring: 3 edges
  (campaniform classes → b1 wing motor neuron, tw = 3572 / 1818 / 1754),
  resolved by UpstreamClassConnectivity of b1 on FlyWire FAFB v783 via the
  VFBquery API. One more edge in the graph carries provenance
  **LITERATURE-CONFIRMED** — an independent eLife 2026 (Lesser, Moussa &
  Tuthill; FANC EM) confirmation of wing campaniform → b1. It is the SAME
  synapse set and is **never double-counted** (excluded from the cascade).
- **[LITERATURE-HYPOTHESIS]** The bristle path: bristle BMN → Mago-no-Te
  (MGT) grooming command (Yoshikawa, Tang & Simpson, Curr Biol — t-GRASP +
  FANC/MANC EM) and wing bristle → CTN defensive neuron (Nat Commun 2020
  s41467-020-17771-8 — ATP/P2X2 stimulation + GCaMP). Placeholder weight 1.
  MGT and CTN have **no FBbt classes** (too new for the ontology); the API
  holds zero rows for bristle downstream in any reachable form (GAPS.md
  §6/§6b). Never present these edges as measured wiring.
- **[MODEL]** The neural dynamics are a simplified model: normalized
  spread-of-activation with a 0.15 firing threshold, 4 steps, ported from
  ../flysim.py. It approximates neural activity and makes no claim about
  biophysics. But this is real, working infrastructure — real measured wiring
  in, coherent body-state out. Agents run on it.
- **[MODELED]** Valence 0.00 (touch quality is informational), arousal gain
  0.30, the `quality` selector, the `"both"` sum rule, and `tick()` decay
  (0.2/s). The fly never saw your inputs.
- **[FICTION]** Any narrative gloss is fiction.

## API

```python
from touch_qualities import TouchQualities
q = TouchQualities()
q.sense(1.0, quality="campaniform")  # REAL wiring -> b1
q.sense(1.0, quality="bristle")      # hypothesis edges -> MGT/CTN
q.sense(1.0, quality="both")         # sum across the two pathways
q.motor_drive()   # activation at the b1 motor neuron (reflex readout)
q.tick(dt)        # decay
q.state()         # current state + provenance note
```

`sense()` returns `{activation, valence_delta, arousal_delta, quality}`.

## Proven numbers (demo.py, exit 0, 13 checks)

| call | activation | valence | arousal | note |
|---|---|---|---|---|
| campaniform 1.0 | 3.0 | 0.0 | 0.9 | 3 campaniform classes converge on b1 |
| bristle 1.0 | 1.0 | 0.0 | 0.3 | hypothesis edges, placeholder weight |
| both 1.0 | 4.0 | 0.0 | 1.2 | 3.0 + 1.0, sum across disjoint pathways |
| campaniform 0.5 | 1.5 | 0.0 | 0.45 | linear above threshold |
| campaniform 0.1 | 0.0 | 0.0 | 0.0 | threshold cliff — honest model behavior |

`motor_drive()` → 3.0 after campaniform, 0.0 after bristle (that path does
not reach b1). `tick(10)` → 3.0 → 1.0. Invalid quality raises `ValueError`.

## Honest limits

- **Bristle is the literature's best guess, not a measurement.** If future
  ontologies give MGT/CTN FBbt classes with real connectivity, swap the
  hypothesis edges for REAL ones.
- **Whole-sensillum level:** club/claw/hook campaniform subtypes (Mamiya et
  al.) are not separately indexed — the bottle cannot tell joint strain
  from haltere oscillation.
- **Threshold cliff:** silent below ~0.15 injection, then graded — toy
  honesty, same as the other sense bottles.
- The campaniform → b1 link was found *backward* (upstream query of b1):
  class-level downstream of campaniform returns 0 rows. Same synapse set,
  read from the other side.

## Files

- `touch_qualities.py` — the `TouchQualities` class (stdlib only)
- `demo.py` — acceptance demo, exit 0
- `README.md` — this file
- Wiring: `../subgraphs/touch_qualities_lit.json`
