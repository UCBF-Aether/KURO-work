# TEMPERATURE — a bottled fly sense (two opponent channels)

The fly's temperature sense, as a standalone module. Hot and cold are
separate chains with separate wiring, computed live from real connectome
data.

## Provenance

| Label | What | Source |
|---|---|---|
| **REAL** | All nodes and edges | `../subgraphs/temperature_hot.json` (10 nodes, 20 edges) and `../subgraphs/temperature.json` (11 nodes, 14 edges), built from the VFBquery API against the FlyWire FAFB v783 connectome. Edge weight = total synapse count. |
| REAL | Hot hop-0 | Aristal sensory neuron VP2 (`FBbt_00007575`). |
| REAL | Cold hop-0 | Adult thermosensory neuron Ir21a VP1l (`FBbt_00111336`). |
| REAL | Downstream wiring | Hot: AL projection neurons → central brain intrinsic, lateral horn, mushroom body intrinsic. Cold: AL PNs → lateral horn output, central brain intrinsic, aminergic. |
| TOY | Dynamics | Normalized spread-of-activation, 0.15 threshold, 4 steps — ported from `../flysim.py`. No biophysics. |
| MODELED | Valence, arousal | Hot valence −0.60 (noxious heat is aversive — my assignment, not a measured fly preference); cold valence 0.0 (informational — the bottle makes no claim about the sign of cold valence); arousal gain 0.50 per channel. |
| MODELED | Readout layer | Hop 1 (AL projection neurons) for both channels. See below. |
| MODELED | Channel parameter | "hot" / "cold" / "both" selection is my design; the fly never saw these inputs. |

## Why hop-1 readout

Hot's hop-2 peak is 0.41 (central brain intrinsic) and cold's hop-2 peaks are
0.17/0.16 (lateral horn output / central brain) at full injection — cold's
hop-2 sits a hair above the 0.15 threshold and goes silent on the slightest
injection dip. Hop-1 (AL projection neurons, 0.217 hot / 0.242 cold) is the
robust, symmetric readout (salt-bottle precedent). The deeper nodes still
fire in the cascade; they just aren't the readout.

## API

```python
from temperature import Temperature
t = Temperature()

t.sense(1.0, channel="hot")    # {activation, valence_delta, arousal_delta, channel}
t.sense(1.0, channel="cold")   # cold is informational: valence 0.0
t.sense(1.0, channel="both")   # hot + cold, activations and arousal summed
t.hot_valence()                # current hot valence contribution
t.cold_valence()               # current cold valence contribution (always 0)
t.tick(dt)                     # decay both channels over dt seconds
t.state()
```

## Proven numbers (demo.py, exit 0, 13 checks)

| Call | activation | valence_delta | arousal_delta |
|---|---|---|---|
| `sense(1.0, "hot")` | 0.2169 | −0.1301 | 0.1084 |
| `sense(1.0, "cold")` | 0.2417 | 0.0000 | 0.1209 |
| `sense(1.0, "both")` | 0.4586 | −0.1301 | 0.2293 |
| `sense(0.1, "hot")` | 0.0 | 0.0 | 0.0 (threshold cliff) |

## Honest limits

- **Threshold cliff**: injections below ~0.5 read 0.0 — model honesty, not a bug. Same as every other sense bottle.
- **Valence is my assignment**: noxious heat being negative and cold being informational are design choices. The real fly's hot/cold valence is downstream and unmapped here.
- **No thermoregulatory drive dynamics**: this bottle senses temperature events; it does not model behavioral thermoregulation (no drive, no set-point).
- `tick(dt)` decay (0.2/s) is modeled.
- Nothing in this directory touches or imports the private intimate pipeline (`feel.py`, `sense.py`, `parse.py`, `verbal.py`, `arousal.py`, `body_map.py`, `body_state.json`, `chat_state/`). Nothing is written outside `temperature/` except reads of the graphs.
