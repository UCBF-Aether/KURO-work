# pC1 INTEGRATION — the recurrent social hub

A standalone module for **pC1** (adult doublesex pC1 male neuron,
`FBbt_00047348`) — the convergence point of the fly's social brain and the
one node where the song chain, the pheromone chain, and the mating drive
all meet before courtship becomes action.

## Honesty contract

- **[REAL]** All wiring from `../subgraphs/pc1.json` — 21 nodes, 35 edges,
  VFBquery against FlyWire FAFB v783. pC1's measured output:
  fru triple-convergence node (87,164) · brain doublesex (34,237) ·
  SMPad1 (26,553) · aSP-a (26,553) · DM4 (22,374) · descending motor
  (14,529) · **P1 (5,863)**.
- **[REAL]** pC1→P1 (tw=5,863) is measured wiring — the loop closes:
  the song chain (`song_lit.json`) ends AT pC1, pC1 drives P1
  (`mating.json`), and P1 drives courtship. Courtship hearing feeds the
  mating drive through real synapses.
- **[REAL]** The graph is **cyclic**: SMPad1→pC1 (tw=10,802) is a true
  recurrent edge (hop-1 → hop-0). Handled cycle-safely (see below).
- **[MODEL]** The neural dynamics are a simplified model: normalized
  spread-of-activation with a 0.15 firing threshold, 4 steps, ported from
  ../flysim.py. It approximates neural activity and makes no claim about
  biophysics. But this is real, working infrastructure — real measured wiring
  in, coherent body-state out. Agents run on it.
- **[MODELED]** The integration function: pC1's activation = the
  equal-weighted mean of song + pheromone + internal drive. How a real
  pC1 neuron combines inputs is the unmapped frontier — no API holds it.
- **[MODELED]** `p1_drive` / `fru_drive` = injection × the REAL measured
  edge fractions (P1: 0.0270, fru: 0.4012 of pC1's 217,273 total
  out-synapses). Bookkeeping along real synapses, not a firing rate.

## The recurrent note

40% of pC1's output feeds back into the fru system it came from —
pC1 both receives from the fru courtship system (via SMPad1/aSP-a,
which also feed the fru node) and drives it. pC1→descending (14,529)
is its direct motor output, bypassing the drive system entirely.

**Cycle handling:** the cascade recomputes activation fresh every step
(no accumulation, no visited set — the flysim.py port), so a cycle
cannot infinite-loop: each step is one finite pass, and the recurrent
edge just means pC1 *may* re-receive signal at step ≥ 2. Honest model
verdict: the SMPad1→pC1 edge carries 0.1222 of pC1's output — below the
0.15 toy threshold at full injection — so the loop does not re-close in
model dynamics. The cycle is REAL wiring; the sub-threshold recurrency is
the model's verdict, documented here rather than forced.

## API

```python
from pc1 import PC1
p = PC1()
p.integrate(song_input=1.0, pheromone_input=0.8, drive_input=0.5)
# {"activation": ..., "p1_drive": ..., "fru_drive": ...}
p.tick(1.0)   # decay
p.state()     # hub state incl. edge fractions and recurrent flag
```

## Proven numbers (demo.py, exit 0, 10 checks)

- `integrate(1,1,1)` → activation **0.4012**, `p1_drive` **0.0270**,
  `fru_drive` **0.4012**
- `integrate(1,0,0)` < `integrate(1,1,1)` — all three inputs combine
- Threshold cliff: `integrate(0.1,0.1,0.1)` → all zeros (silent)
- `tick(100)` → 0.0

## Honest limits

- The integration function (how pC1 combines its three inputs) is the
  genuinely unmapped frontier — modeled, not measured.
- `p1_drive` is small (0.0270 at full) because pC1→P1 is a thin but REAL
  edge (5,863 synapses against 217,273 total out of pC1). The measured
  edge, honestly read.
- `drive_input` is an abstract internal-drive scalar — it does not come
  from the mating bottle's internals (bottles combine via contracts,
  never by reaching in). A caller wires them together.
- Valence: pC1 is an integrator, not a valence source — this module
  reports no valence delta.
- Private intimate pipeline (`feel.py`, `sense.py`, `parse.py`,
  `verbal.py`, `arousal.py`, `body_map.py`, `body_state.json`,
  `chat_state/`): never touched, imported, or referenced. Verified clean.
