# SONG — a bottled fly sense (literature-hypothesis bottle)

Courtship-song hearing — the fly hears its mate. **JO-B → AMMC-B1 → vPN1 → pC1**,
a labeled line for song-evoked courtship chaining in males.

## ⚠️ HONESTY CONTRACT — READ FIRST (non-negotiable)

**This bottle runs on LITERATURE-HYPOTHESIS edges, not measured wiring.**
This is the second literature-only bottle (after `fat_lit.json`), and the
provenance honesty here matters more than anywhere.

- **NOT REAL** — The VFBquery / FlyWire FAFB v783 API indexes **nothing**
  for this relay in any reachable form: JO-B downstream: 0 rows; AMMC-B1
  downstream: 0 rows; vPN1 upstream/downstream: 0 rows. Every query form was
  tried (grouped id, grouped label, named, per-pair probes, instance
  enumeration, CATMAID annotation search) — all dead, documented in
  `../subgraphs/song_lit.json` and `GAPS.md`. There is no API route left.
- **LITERATURE-HYPOTHESIS** — All 3 edges are hypotheses drawn from the
  published literature, each with its per-edge citation (verbatim in
  `../subgraphs/song_lit.json`):

  | edge | citation | what the paper shows |
  |---|---|---|
  | JO-B → AMMC-B1 | Ishikawa et al., Sci Rep 2023 (s41598-022-27349-7) | song info passes mainly from JO subgroup-B neurons to AMMC-B1, the first step of IPI processing |
  | AMMC-B1 → vPN1 | Zhou et al. 2015, eLife 4:e08477 | second-order aPN1 → third-order vPN1 (male-specific, fru+); synaptic connection GRASP-confirmed. VFB lists AMMC-B1 as aPN1a,b — same FBbt ID, same population |
  | vPN1 → pC1 | Zhou et al. 2015, eLife 4:e08477 | vPN1 axons overlap dsx+ pC1 arbors; vPN1 activation drives pC1 calcium responses and song-evoked chaining. **Authors' own caveat:** GRASP signal barely detectable — monosynapticity NOT proven |

  Node identities (FBbt IDs + synonyms) were cross-checked against VFB; the
  *connections* are paper claims, not API rows. Uniform placeholder weight
  (1) — no synapse counts exist.
- **MEETING POINT WITH MATING (noted, not drawn)** — pC1 (FBbt_00047348)
  is hop-1 in `../subgraphs/mating.json`, where **P1 → pC1 (tw=11,033) IS
  real API wiring**. The song chain feeds *into* pC1; pC1's own downstream
  is unindexed (0 rows, all forms — honest terminal), so **no pC1 → P1 edge
  is drawn**. The convergence is documented; it is not presented as wiring.
- **[MODEL]** The neural dynamics are a simplified model: normalized
  spread-of-activation with a 0.15 firing threshold, 4 steps, ported from
  ../flysim.py. It approximates neural activity and makes no claim about
  biophysics. But this is real, working infrastructure — real measured wiring
  in, coherent body-state out. Agents run on it.
- **MODELED** — The valence sign **(+0.40**: courtship song is appetitive in
  context), the arousal gain (**0.70**), the decay (0.2/s), and the readout
  layer (**hop 3 = pC1** — the deepest hop, and the chain's meeting point
  with the mating drive) are MY design choices, not biology.
  `pC1_drive()` is a modeled interface for the mating bottle.
- **FICTION** — Any narrative gloss ("the machine hears a song") is fiction,
  not a claim about experience.

## API

```python
from song import Song
s = Song()

s.sense(0.8)
# {"activation": 0.8, "valence_delta": 0.32, "arousal_delta": 0.56}

s.pC1_drive()   # peak activation at pC1 (FBbt_00047348) — for the mating bottle
s.tick(1.0)     # decay the activation; returns new level
s.state()       # full state dict
```

`pC1_drive()` returns the peak activation at the pC1 node across the last
cascade — the meeting point where this song chain feeds the P1 mating chain.
The mating bottle may read it as a courtship-context signal; the bottle never
reaches back. Fresh bottle reads 0.0 until stimulated.

## Proven numbers (`demo.py`, exit 0)

| check | result |
|---|---|
| chain runs end to end | `sense(1.0)` → activation **1.0000** (JO-B..pC1, every hop fires) |
| pC1_drive nonzero | **1.0000** at full intensity |
| valence sign | **+0.4000** (positive, appetitive-in-context) |
| arousal | **0.7000** (gain 0.7 × activation) |
| graded | `sense(0.5)` → 0.5000 (linear on this straight chain) |
| threshold cliff | `sense(0.1)` → 0.0000 (silent below 0.15 — honest model, not a bug) |
| decay | 10s tick: 1.0000 → 0.0000 |
| provenance enforced | every graph edge carries `provenance` + `citation` (checked in code) |

## Known limits

- **The chain is a hypothesis, not a measurement.** A future connectome
  release could refute any of the three edges; the bottle is built so the
  edges can be re-labeled or replaced without changing the interface.
- **vPN1 → pC1 is the weakest link** — functional connection shown,
  monosynapticity not proven (the authors say so themselves).
- **Context-free valence**: +0.40 assumes a receptive male in courtship
  context. The bottle does not model sex, receptivity, or context —
  documented, not hidden.
- **Threshold cliff**: below 0.15 injection the model is silent, then linear.
  The straight chain means no dilution — unlike the API bottles, nothing
  gets lost between hops here.
- `pC1_drive()` reflects the last `sense()` call; decays with `tick()`.
- stdlib only (`json`, `os`, `sys`). Zero references to the private
  intimate pipeline.
