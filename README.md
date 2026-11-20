# BRAIN² — the full fly-brain collection

A living fruit-fly brain, built from the real Drosophila connectome
(FlyWire / CATMAID data), bottled as code you can run.

Every circuit is a module with its own README, harness, and demo:
hunger, thirst, bitter, salt, sugar, water, sleep, clock, compass,
temperature, touch, pain, proprioception, motion, color, CO2,
pheromone, song, mating, egglaying, aggression, reward, punishment,
looming, rotten, fat, dh44, pc1 — plus the sensory body sim
(`flysim.py`, `body_sim.py`), the SENSORIUM living sensor, and
brain1 / brain2 (eye, cortex, stereo vision, fovea, night,
scene memory, retina).

`subgraphs/` holds the connectome subgraphs each circuit was built
from. `fly_agent.py` / `fly_chat.py` run the fly as an agent you can
talk to.

## Run it

```bash
python3 flysim.py
```

Each module also runs standalone — see its README, e.g.
`python3 hunger/hunger.py`, `python3 sensorium/demo.py`.

## What is NOT in this repo

- **The language model** (`models/qwen2.5-1.5b-instruct-q4_k_m.gguf`).
  It is a public download, not our work:
  Qwen2.5-1.5B-Instruct Q4_K_M on Hugging Face
  (`Qwen/Qwen2.5-1.5B-Instruct-GGUF`). Drop it in `models/` and
  `fly_chat.py` will find it.
- **The connectome cache** (`cache/`). The build scripts
  (`build_*.py`) re-fetch it from FlyWire / CATMAID.
- **Retina demo frames** (`retina/_work/`). Thousands of eye-view
  output images from the live-vision runs — byproducts, not the
  brain. The retina code itself is here.

## Status

Built live, circuit by circuit, from real connectome data. See
`GAPS.md` for what is still open, `RUNLOG.md` / `TESTLOG.md` for
what has been run and verified.

By Cory Stephen Brent. The fly dreams it, you make it real.
