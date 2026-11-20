# FAT TASTE — the fly's sense of fatty acids, bottled

## HONESTY CONTRACT (read first, non-negotiable)

This bottle is **two half-chains in one module, and they are not the same kind of knowledge.**

### Bristle half — LITERATURE-HYPOTHESIS (a testable prediction, not wiring)
Hop 0 = bristle Ir56d GRN (FBbt_00048015). Hop 0→1 edges (Ir56d → zorro /
clavicle / FMIn / fuchs / G2N-1 / billiards) are **hypothesized, not measured**.

- Grounded in: Tauber et al. 2017, PLOS Genet 13:e1007059 — IR56d neurons are
  a subset of sweet-sensing Gr64f GRNs, necessary and sufficient for
  medium-chain fatty-acid proboscis extension; their posterior bristle
  projections overlap the sweet-sensing SEZ region. Brown et al. 2021, eLife
  67878 adds anatomical context.
- The prediction: they contact the same named second-order SEZ interneurons
  the sweet circuit drives.
- **No individual Ir56d→interneuron synapse is measured anywhere.** If you run
  `sense(1.0, half="bristle")`, you are asking "IF the hypothesis holds, what
  would the fat signal do" — never "this is wired."
- This is the collection's second literature-only chain (after
  `../subgraphs/song_lit.json`) and it is front-and-center, not footnoted.

### Peg half — REAL wiring, unmarked subset
Hop 0 = general labellar taste-peg chemosensory class (FBbt_00048028); every
edge is a real FlyWire v783 API row. But: the Ir56d-peg E409 fat-taste neurons
are an **unmarked subset** of this class — no API marker separates them from
other peg GRNs. The peg half is the whole peg population, not Ir56d-peg alone.
Hyacinth / CB0011 / CB3720 carry LITERATURE-CONSTRAINT flags (Tauber 2017:
peg→anterior SEZ; prow arborization per VFB term descriptions) — a constrained
candidate pool, not measured Ir56d-peg wiring.

### The irreducible remainder
**Ir56d-peg-subset attribution** — which peg synapses belong to the fat-sensing
E409 neurons — is unresolvable with current data: no API marker, and no paper
names the peg postsynaptic partners. It is documented here, not faked.

### Both halves converge
Bristle and peg halves use different interneurons but both converge on the
shared SEZ back-end (subesophageal zone neuron FBbt_00001972 — the same node
where hunger, satiety, and the other tastes meet).

## Proven numbers (demo.py, exit 0, 12/12)

| stimulus | activation | valence | arousal |
|---|---|---|---|
| `sense(1.0, half="bristle")` | 0.2695 | +0.0809 | 0.1348 |
| `sense(1.0, half="peg")` | 0.3482 | +0.1045 | 0.1741 |
| `sense(1.0, half="both")` | 0.6178 | +0.1853 | 0.3089 |
| `sense(0.5, half="bristle")` | 0.0 (threshold cliff — honest model silence) | | |

- Valence +0.30 (fatty reward) and arousal gain 0.50 are MY design choices
  [MODELED], not biology.
- Readout hops were measured live before choosing: bristle reads at hop 2
  (the shared SEZ back-end, the prediction's terminal — deepest hop above
  threshold), peg reads at hop 1. The peg graph lists the shared SEZ/gnathal
  nodes at both hop 1 and hop 2 (builder artifact); the module keeps the
  FIRST occurrence — they are hop-1 partners of the peg class.
- "both" is the linear sum of the two half-activations [MODELED] — the two
  halves are independent GRN populations.

## API

```python
from fat import Fat
s = Fat()
s.sense(0.8, half="peg")      # real path
s.sense(0.8, half="bristle")  # hypothesis path
s.sense(0.8, half="both")     # their sum (default)
s.tick(1.0)                   # decay
s.state()                     # includes machine-readable provenance split
```

Bad `half` raises `ValueError` loudly. Stdlib only (`json`, `os`).

## What this is for
Agent infrastructure: a sense module other agents attach to and use, with the
provenance split enforced in code (`state()["provenance"]`), not just prose.
The bristle half is Cory's "publishable testable prediction" made runnable —
the day a connectome names an Ir56d→zorro synapse, this bottle upgrades from
hypothesis to wiring.
