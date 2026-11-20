# SALT — two opponent channels, one bottle

Salt taste is an opponent system, so it gets one bottle with two chains:
**LOW** salt attracts (feeding/approach), **HIGH** salt repels (withdrawal).

## Honesty contract

- **REAL** — Every node and edge comes from `../subgraphs/salt.json`
  (26 nodes, 40 edges), built from the Virtual Fly Brain VFBquery API
  against the FlyWire FAFB v783 connectome. Edge weight = total synapse
  count. The `chain` field on nodes/edges separates the two chains.
  - LOW chain (FBbt_00100043, low salt-sensing GRN): real named-query
    rows, standard top-k walk → SEZ output, gustatory projection,
    SLP gustatory projection (SLP GPN1), SEZ, gnathal — the feeding
    pathway.
  - HIGH chain (FBbt_00052561, high salt-sensing GRN): every direct
    query form was dead (grouped ID 0 rows, grouped label 0 rows, named
    0 rows, 0 instances, sibling DL class also dead). Its hop-1 is
    derived by **subtraction**: parent class FBbt_00049615 (salt-sensing
    neuron, 50 real named rows) minus the resolved low-salt child's rows;
    the remainder (VNC/ascending/prothoracic tier, usnea, DNg103) is the
    high-salt siblings' signal. All underlying rows are real API rows;
    the **attribution** to high-salt is the documented method, not a
    measured label. Full provenance in `../GAPS.md`.
- **[MODEL]** The neural dynamics are a simplified model: normalized
  spread-of-activation with a 0.15 firing threshold, 4 steps, ported from
  ../flysim.py. It approximates neural activity and makes no claim about
  biophysics. But this is real, working infrastructure — real measured wiring
  in, coherent body-state out. Agents run on it.
- **MODELED** — Valence signs (+0.40 low / −0.60 high) and arousal gain
  (0.50) are design choices, not biology. So is the readout layer:
  **hop 1 for both chains** — low's feeding populations (SEZ output,
  gustatory projection, SLP GPN1) and high's withdrawal populations
  (prothoracic, ascending, DNg103) both sit at hop 1. Low's hop 2 does
  carry signal (0.20) but includes optic-lobe classes from a broad hop-1
  node — noise for a feeding readout. The `chain` selection parameter
  itself is modeled.
- **FICTION** — Any narrative gloss ("leans in", "pulls back") is
  fiction.

## API

```python
from salt import Salt
s = Salt()
s.sense(0.8, chain="low")   # {"activation", "valence_delta" (+), "arousal_delta", "chain"}
s.sense(0.8, chain="high")  # {"activation", "valence_delta" (-), "arousal_delta", "chain"}
s.tick(1.0)                 # decay activation by dt seconds
s.state()                   # {"activation", "last_chain", ...}
```

`sense()` raises `ValueError` on an unknown chain. Intensity is clamped
to [0, 1].

## Proven numbers (demo.py, exit 0)

- `sense(1.0, "low")` → activation **0.3007**, V **+0.1203**, A 0.1503;
  top terminal **FBbt_00049858** (adult SEZ output neuron) — feeding.
- `sense(1.0, "high")` → activation **0.2990**, V **−0.1794**, A 0.1495;
  top terminal **FBbt_20008184** (adult ANXXX433) — motor/withdrawal.
- Chain subgraphs are node-disjoint (0 shared nodes); `tick(30)` → 0.0.

## Honest limits

- Threshold cliff: injections below ~0.5 read 0.0 on both chains —
  the cascade is silent, then graded. Model honesty, not a bug.
- High-chain attribution is subtraction-derived (see REAL above) —
  do not present it as directly measured high-salt wiring.
- The two chains share no nodes in this graph, but in the real fly
  both start at labellar GRNs; the opponent computation downstream
  (SEZ integration of low vs high) is not modeled here.
- stdlib only (`json`, `os`). Nothing outside `salt/` except reads
  of `../subgraphs/salt.json` and the `bitter/` house pattern.
