# PHEROMONE — a bottled fly sense

Courtship/social smell — the mating drive's nose. Computed live from real
Drosophila connectome wiring: **Or47b olfactory receptor neuron
(FBbt_00067056)** → antennal lobe projection neurons → lateral horn + the
fruitless-expressing bridge node **FBbt_00016687**, where this chain meets
the P1 courtship chain (`../subgraphs/mating.json`).

## Honesty contract (non-negotiable)

- **REAL** — Every node and edge comes from `../subgraphs/pheromone.json`
  (15 nodes, 21 edges; edge weight = total synapse count), built from the
  Virtual Fly Brain VFBquery API against the FlyWire FAFB v783 connectome.
  Key real edges: Or47b → AL projection (15,332), Or47b → lateral-horn-bound
  projection (13,811), Or47b → fruitless-expressing bridge (13,133).
  No neuron, synapse, or connection is invented here.
- **Documented dead avenues** — Or88a (the other famous pheromone receptor)
  was unindexable in every query form; ppk23/ppk29 (gustatory pheromone
  neurons) do not exist as adult classes. This bottle is **Or47b, honestly
  labeled** — not "the pheromone system."
- **[MODEL]** The neural dynamics are a simplified model: normalized
  spread-of-activation with a 0.15 firing threshold, 4 steps, ported from
  ../flysim.py. It approximates neural activity and makes no claim about
  biophysics. But this is real, working infrastructure — real measured wiring
  in, coherent body-state out. Agents run on it.
- **MODELED** — The valence sign **(+0.50**: courtship-relevant odors are
  appetitive in the right context), the arousal gain (**0.80**), the decay
  (0.2/s), and the readout layer are MY design choices, not biology. The
  readout is at **hop 1** — the deepest hop that carries signal above
  threshold at full injection (hop-1 peak 0.2594; hop-2 peaks at 0.1463,
  just below the 0.15 threshold — same documented precedent as the THIRST
  and DH44 bottles: read where the circuit actually speaks).
  `courtship_bridge()` is a modeled interface for the mating bottle; the
  underlying edge is real, the interface is a convenience.
- **FICTION** — Any narrative gloss ("the machine catches a scent") is
  fiction, not a claim about experience.

## API

```python
from pheromone import Pheromone
s = Pheromone()

s.sense(0.8)
# {"activation": 0.2075, "valence_delta": 0.1038, "arousal_delta": 0.166}

s.courtship_bridge()   # peak activation at FBbt_00016687 (for the mating bottle)
s.tick(1.0)            # decay the activation; returns new level
s.state()              # full state dict
```

`courtship_bridge()` returns the peak activation at the fruitless-expressing
node across the last cascade — the shared node where this pheromone chain
converges with the P1 mating chain. The mating bottle may read it as a
courtship-context signal; the bottle never reaches back.

## Proven numbers (`demo.py`, exit 0)

| check | result |
|---|---|
| cascade fires | `sense(1.0)` → activation **0.2594** |
| bridge nonzero | `courtship_bridge()` → **0.2222** at full intensity |
| valence sign | +0.1297 (positive, appetitive-in-context) |
| arousal | +0.2075 |
| threshold cliff | `sense(0.1)` → 0.0000 (silent below the cliff — honest model, not a bug) |
| decay | 30s tick → 0.0, bridge decays too |

## Known limits

- **Threshold cliff**: injections below ~0.6 read 0.0 on this circuit —
  the cascade is silent, then graded. Model being honest, not a bug.
- **Or47b only**: Or88a and ppk23/29 are documented dead avenues above.
- **Context-free valence**: +0.50 assumes a receptive context. In a
  hostile or wrong-sex context the real biology would differ; the bottle
  does not model context — documented, not hidden.
- `courtship_bridge()` reflects the last `sense()` call; a fresh bottle
  reads 0.0 until stimulated.
- stdlib only (`json`, `os`, `sys`). Zero references to the private
  intimate pipeline.
