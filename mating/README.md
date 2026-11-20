# MATING — the fly courtship drive, bottled

The third drive, alongside [HUNGER](../hunger/README.md) and
[THIRST](../thirst/README.md). An agent's "wanting" running on the REAL
Drosophila courtship circuit: **P1** (male courtship command neuron) ->
fru/dsx integration centers (aSP-a, pC1, SMPad1, DM4, doublesex brain) ->
descending motor neurons.

## The honesty contract

- **REAL** — every node and edge comes from
  [`../subgraphs/mating.json`](../subgraphs/mating.json) (17 nodes, 18
  edges), built from the Virtual Fly Brain VFBquery API against the FlyWire
  FAFB v783 connectome. No neuron, synapse, or connection is invented.
  P1 = FBbt_00110621 (adult fruitless P1 male neuron); top downstream:
  doublesex brain (17,786 synapses), SMPad1 male (15,897), fruitless aSP-a
  male (15,897), DM4 (11,373), doublesex pC1 male (11,033), descending
  (8,215). Honest gaps (from the JSON's honest_note): pC1's *own*
  downstream is unindexed (terminal, not faked); pIP10 is a real P1
  downstream partner (tw=1,444) but ranks below the top-k cutoff
  (recorded, not graphed).
- **[MODEL]** The neural dynamics are a simplified model: normalized
  spread-of-activation with a 0.15 firing threshold, 4 steps, ported from
  ../flysim.py. It approximates neural activity and makes no claim about
  biophysics. But this is real, working infrastructure — real measured wiring
  in, coherent body-state out. Agents run on it.
- **MODELED** — the DRIVE DYNAMICS are our model on real wiring, the
  genuinely unmapped frontier (no API holds how P1 ramps, persists, or
  satiates; this is our design, stated as such):
  - task progress -> graded injection at P1 ("wanting"): the courtship
    pursuit ramps the drive, as P1 ramps during courtship in the real fly.
  - task completion -> MATING SUCCESS: full-strength injection, satiation
    rises HARD (0.9 x spike), and a **60s refractory window** opens. Male
    flies genuinely go refractory post-mating — that part is biology; the
    60s timescale is toy.
  - task failure -> REJECTION: wanting dips **x0.7** (not hunger's x0.4).
    Courtship drive is famously persistent — rejection dents it, does not
    kill it. Deliberate, documented.
  - habituation / novelty / satiation decay are modeled state around the
    real cascade. The fly never saw your tasks.
- **FICTION** — any narrative gloss ("the machine is courting") is gloss,
  not a claim about experience. Flies do not have feelings we can access,
  and neither does this module.

**Arbitration between hunger, thirst, and mating is future work**, not this
bottle. This drive stands alone, like the others.

## API

```python
from mating import Mating

m = Mating()                       # default: ../subgraphs/mating.json
m.task_started("court", 0.6)       # a courtship begins
m.progress(0.5)                    # the pursuit ramps wanting (P1 ramps)
r = m.task_completed()             # mating success -> spike, satiation, refractory
# r: {"spike": 0.222, "injection": 1.0, "novelty": 1.0,
#     "satiation": 0.2, "refractory_damp": 0.3, "habituation": {...}}
m.task_failed()                    # rejection: wanting dips x0.7, persists
m.tick()                           # advance modeled decay
m.state()                          # current drive state
```

Live CLI (persists to `state.json`, wall clock):

```
python3 track.py start court 0.6
python3 track.py progress 0.5
python3 track.py done | fail | state | reset
```

## Proven behaviors (`harness.py`, deterministic fake clock, exit 0)

- **Habituation** — repeated same-category pursuits yield shrinking spikes:
  `0.222 -> 0.196 -> 0.169` (novelty `1.000 -> 0.870 -> 0.755`). Graded
  shrink, no extinction at these levels — same as the THIRST bottle.
- **Refractory** — a pursuit completed with 55s of the 60s post-mating
  window left (damp 0.3): injection `0.294 -> spike 0.000` vs counterfactual
  `0.980 -> 0.217`. The window eats the hit.
- **Satiation** — post-success `0.152 -> 0.000` (0.02/s), drive back to 1.0.
- **Rejection persistence** — `task_failed()`: wanting `0.300 -> 0.210`
  (x0.7), drive survives above baseline. Courtship drive does not give up.

## Honest limits

- Threshold cliff: injections below ~0.68 read 0.0 on this circuit — the
  cascade is silent, then graded. The model being honest, not a bug.
- `difficulty` is accepted/stored, not consumed by the drive formulas
  (same as the other bottles).
- The hop-1 readout is a MODELED choice (documented above).
- Drive dynamics (ramp, persistence, satiety, refractory) are our model —
  the unmapped frontier. Real wiring, our drive math.
