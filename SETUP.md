# FlyBrain² — Setup

A living fruit-fly brain, built from the real Drosophila connectome.
This is how to run it.

## What you need

- Python 3.10 or newer
- About 2 GB free (the language model)
- Internet the first time (to fetch the connectome cache and the model)

## Steps

1. Clone the repo:
   `git clone https://github.com/UCBF-Aether/KURO-work.git`
2. Download the language model — Qwen2.5-1.5B-Instruct Q4_K_M from
   Hugging Face (`Qwen/Qwen2.5-1.5B-Instruct-GGUF`) — and put the
   `.gguf` file in `models/`. It is a public download, not our work.
3. Run the whole brain:
   `python3 flysim.py`
4. Or run one circuit on its own — each module runs standalone:
   `python3 hunger/hunger.py`
   `python3 sensorium/demo.py`
   `python3 retina/retina.py`

## What is where

- `flysim.py`, `vfb.py` — the body sim and the fly itself
- `brain1/`, `brain2/` — eye, cortex, stereo vision, fovea, night, scene memory
- `hunger/`, `thirst/`, `bitter/`, `salt/`, `sugar/`, `water/`, `sleep/`,
  `clock/`, `compass/`, `temperature/`, `touch/`, `pain/`,
  `proprioception/`, `motion/`, `color/`, `co2/`, `pheromone/`,
  `song/`, `mating/`, `egglaying/`, `aggression/`, `reward/`,
  `punishment/`, `looming/`, `rotten/`, `fat/`, `dh44/`, `pc1/` — the drives
- `sensorium/` — the living sensor
- `subgraphs/` — the connectome subgraphs each circuit was built from
- `cache/` — fetched FlyWire / CATMAID data. The `build_*.py` scripts
  re-fetch it if it is missing.
- `public/` — the public page

## If it does not work

- `python3 --version` — it must be 3.10 or newer.
- Missing model: `fly_chat.py` will tell you. Put the `.gguf` in `models/`.
- Missing cache: run the `build_*.py` script for that circuit.
- See `GAPS.md` for what is still open, `RUNLOG.md` / `TESTLOG.md` for
  what has been run and verified.

Free, from KUROworks. If it made you think, a donation keeps the lights on.
