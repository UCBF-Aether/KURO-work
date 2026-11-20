#!/usr/bin/env python3
"""
sensorium.py — SENSORIUM, a living sensor for AI.

Not a simulation of a fly. A sensory-affective module any AI imports so it
HAS senses: touch that habituates, sweetness that sates, threats that
startle, rot that repels, pain that dominates, and a hunger drive with
history. The full sensation spectrum — pain included. Nothing here is
pleasure-aimed; this is a complete sensorium, not a reward toy.

HONESTY CONTRACT (non-negotiable, repeated in every surface of this project):
- [REAL]    Every node and edge in every channel comes from a subgraph JSON
            built from the Virtual Fly Brain VFBquery API against the FlyWire
            FAFB v783 connectome. No neuron, synapse, or connection is
            invented. Channels: touch (Johnston organ mechanosensory),
            sweet (SOLVED forward chain: sweet GRN -> named SEZ interneurons
            -> premotor), rot (Or56a olfactory aversion), threat (LPLC2 visual
            looming -> escape), pain (see PAIN CHANNEL note below).
- [MODEL]    The neural dynamics are a simplified model: normalized
             spread-of-activation with a 0.15 firing threshold, 4 steps,
             ported from ../flysim.py. It approximates neural activity and
             makes no claim about biophysics. But this is real, working
             infrastructure — real measured wiring in, coherent body-state
             out. Agents run on it.
- [MODELED] Everything affective is MY design choice, not biology: the
            valence/arousal mapping, habituation, the graded-signal readout,
            pain normalization, the pain-dominance rule (stress suppresses
            feeding), the sweet->hunger mapping, and the mood gloss words.
            The fly never felt your inputs.
- [FICTION] Mood words ("hurt", "recoiling", "calm") are one-word glosses on
            the (valence, arousal, hunger) state — labels, not claims about
            experience.

PAIN CHANNEL note: no nociceptive class is indexed with usable connectivity
in the API (searched: adult nociceptive projection neuron FBbt_00051492 and
generic nociceptive neuron FBbt_00048471 — class-level, named, and
instance-level queries all returned zero; no CATMAID FAFB skeletons exist
for these classes; see GAPS.md). The pain channel therefore runs on the
looming escape circuit as a DOCUMENTED functional proxy: a noxious stimulus
driving the escape pathway is the real biology of that circuit (intense
input -> descending -> escape). state() reports pain_channel_proxy=True so
no one mistakes the proxy for nociceptive wiring. If pain.json ever lands
from a real class, the channel picks it up automatically.

PRIVACY BOUNDARY: this module is the GENERAL AI sensor. It does not import,
read, or depend on the private intimate pipeline (feel.py, sense.py,
parse.py, verbal.py, arousal.py, body_map.py, body_state.json, chat_state/).
That pipeline is sealed and untouched.

Usage:
    from sensorium import Sensorium
    s = Sensorium()                 # loads the channel circuits + body + hunger
    s.sense("touch", 0.4)           # a touch lands; affect updates
    s.sense("touch", 0.8, location="legs")  # focused on the legs
    s.sense("pain", 1.0)            # a noxious event; pain dominates
    s.tick(5.0)                     # five seconds pass; everything decays
    s.feel()                        # the complete felt state, any time
    s.state()                       # compat read (a subset of feel())
See live.py (always-on runner) and day.py (a day in the life).
"""

import json
import os
import sys
import time
from collections import defaultdict

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)  # so `body` resolves wherever Sensorium is imported from
sys.path.insert(0, os.path.join(HERE, "..", "hunger"))
from hunger import Hunger  # noqa: E402 — the drive component; Sensorium owns one
from body import Body, REGIONS  # noqa: E402 — the fly's body; Sensorium owns one

SG = os.path.join(HERE, "..", "subgraphs")

THRESHOLD = 0.15   # firing threshold, same as flysim.py [MODEL]
STEPS = 4          # cascade steps, same as flysim.py [MODEL]


def _drift_toward(x, target, amount):
    """Move x toward target by amount without overshooting."""
    if x < target:
        return min(target, x + amount)
    return max(target, x - amount)


class _Channel:
    """One sensory channel: real wiring + model cascade + graded readout.

    [REAL] nodes/edges straight from the circuit JSON; never invented.
    [MODEL] normalized spread-of-activation, 4 steps.
    [MODELED] the activation readout: the 0.15 threshold answers "which
    neurons fired" (a claim about the circuit). The RAW (unthresholded)
    terminal peak answers "how strong was the signal" (a graded quantity
    for the affect model). Both derive from the same real synapses, and
    Drosophila neurons famously signal with graded potentials — so the
    graded readout is the more honest model of a sensor than a binary
    gate, which would render every sub-maximal stimulus silent.
    """

    def __init__(self, graph_path):
        with open(graph_path) as f:
            graph = json.load(f)
        self.source = graph.get("source", "")
        self.stimulus = graph.get("stimulus", "?")
        self.nodes = {n["id"]: n for n in graph["nodes"]}
        self.hop2 = [n["id"] for n in graph["nodes"] if n.get("hop", 0) == 2]
        self.inject_ids = [n["id"] for n in graph["nodes"]
                           if n.get("hop", 0) == 0]
        out_sum = defaultdict(float)
        for e in graph["edges"]:
            out_sum[e["pre"]] += e["weight"]
        self.norm = [(e["pre"], e["post"],
                      e["weight"] / out_sum[e["pre"]] if out_sum[e["pre"]] else 0.0)
                     for e in graph["edges"]]

    def raw_terminal_peak(self, injection):
        """[REAL wiring + MODEL dynamics, MODELED readout] max hop-2
        activation WITHOUT thresholding: the graded signal strength."""
        act = {nid: 0.0 for nid in self.nodes}
        for nid in self.inject_ids:
            act[nid] = injection
        best = max([act.get(nid, 0.0) for nid in self.hop2] + [0.0])
        for _ in range(STEPS):
            incoming = defaultdict(float)
            for pre, post, w in self.norm:
                if act[pre] > 0:
                    incoming[post] += act[pre] * w
            act = {nid: incoming.get(nid, 0.0) for nid in self.nodes}
            best = max(best,
                       max([act.get(nid, 0.0) for nid in self.hop2] + [0.0]))
        return best

    def fired_snaps(self, injection):
        """[MODEL] per-step dicts of nodes >= THRESHOLD: which populations
        lit up, in what order."""
        act = {nid: 0.0 for nid in self.nodes}
        for nid in self.inject_ids:
            act[nid] = injection
        snaps = [{nid: a for nid, a in act.items() if a >= THRESHOLD}]
        for _ in range(STEPS):
            incoming = defaultdict(float)
            for pre, post, w in self.norm:
                if act[pre] > 0:
                    incoming[post] += act[pre] * w
            act = {nid: incoming.get(nid, 0.0) for nid in self.nodes}
            snaps.append({nid: a for nid, a in act.items()
                          if a >= THRESHOLD})
        return snaps


# Modality -> circuit file, valence weight, arousal gain. [MODELED] values.
# Pain dominates by weight AND by the pain-dominance rule in sense().
# Temperature (when subgraphs/temperature.json exists — see __init__) carries
# valence 0.0: polarity is not derivable from wiring alone, so temperature
# registers as sensation (arousal + regional levels), honestly without
# invented valence.
MODALITIES = {
    "touch":  {"file": "touch.json",         "valence": +0.15, "arousal": 0.7},
    "sweet":  {"file": "sugar_forward.json", "valence": +1.0,  "arousal": 0.4},
    "rot":    {"file": "rotten.json",        "valence": -1.0,  "arousal": 0.8},
    "threat": {"file": "looming.json",       "valence": -0.8,  "arousal": 1.0},
    "pain":   {"file": None,                 "valence": -1.0,  "arousal": 1.2},
    # pain "file": pain.json when a real nociceptive class resolves (see
    # module docstring); otherwise looming.json as documented functional proxy.
}
TEMPERATURE_CFG = {"file": "temperature.json", "valence": 0.0, "arousal": 0.7}


class Sensorium:
    """A living sensor: five channels, one affect state, one hunger drive."""

    def __init__(self, clock=None, pain_graph=None):
        self._clock = clock or time.monotonic
        self._last = self._clock()

        # Per-modality config: the five base channels, plus temperature when
        # its subgraph resolved from real API rows (see build_temperature.py).
        self.modality_cfg = dict(MODALITIES)
        temp_path = os.path.join(SG, "temperature.json")
        if os.path.exists(temp_path):
            self.modality_cfg["temperature"] = TEMPERATURE_CFG
        self.has_temperature = "temperature" in self.modality_cfg

        self.channels = {}
        for mod, cfg in self.modality_cfg.items():
            if mod == "pain":
                if pain_graph and os.path.exists(pain_graph):
                    path, proxy = pain_graph, False
                elif os.path.exists(os.path.join(SG, "pain.json")):
                    path, proxy = os.path.join(SG, "pain.json"), False
                else:
                    path, proxy = os.path.join(SG, "looming.json"), True
                self.channels[mod] = _Channel(path)
                self.pain_is_proxy = proxy
                self.pain_source = path
            else:
                self.channels[mod] = _Channel(os.path.join(SG, cfg["file"]))
        self.pain_is_proxy = getattr(self, "pain_is_proxy", False)

        # [MODELED] pain affect is normalized to the pain channel's dynamic
        # range (raw terminal peak at intensity 1.0), so a max noxious event
        # registers full-scale pain regardless of the circuit's absolute
        # throughput. Biologically grounded: pain is a full-scale interrupt.
        self._pain_ref = self.channels["pain"].raw_terminal_peak(1.0) or 1.0

        # [MODELED] affect state
        self.valence = 0.0       # -1..1
        self.arousal = 0.0       # 0..1
        self.habituation = defaultdict(float)   # modality -> count
        self.last_activation = {m: 0.0 for m in self.channels}
        self.last_effective = {m: 0.0 for m in self.channels}
        self.pain_level = 0.0    # 0..1; recent noxious load, normalized
        self._meals = 0          # hunger tasks completed (for the "hungry" mood)

        # The body: where sensations land. [MODELED] weights in body.py.
        self.body = Body()

        # The drive component. Sweet events feed it (see sense()).
        self.hunger = Hunger(os.path.join(SG, "sugar_forward.json"),
                             clock=self._clock)
        self.hunger.task_started("sweet", 0.5)
        self._hunger_progress = 0.0

    # ---- sensing ----

    def sense(self, modality, intensity=0.5, location=None):
        """A stimulus lands — on the circuit, in the affect, on the body.

        modality: one of touch/sweet/rot/threat/pain (+temperature when its
        subgraph resolved). intensity: 0..1. location: optional body region
        (antennae/eyes_head/proboscis/legs/wings/abdomen) focusing the
        sensation there — [MODELED] x2 weight on that region.
        Returns the event record.
        [MODELED] affect update (non-pain channels):
          effective = raw_terminal_peak(intensity) * novelty(modality)
          valence  += valence_weight[modality] * effective   (clamped [-1,1])
          arousal  += arousal_gain[modality] * effective      (clamped [0,1])
          novelty  = 1/(1+0.5*habituation[modality]); habituation += 1
        Regional sensation = effective x body weights (body.py) x focus.
        [MODELED] pain: effective is normalized by the pain channel's
        dynamic range, so pain 1.0 always lands full-scale (valence -1,
        arousal spike, pain_level 1). pain_level decays with tick().
        [MODELED] pain dominance (biologically grounded: stress suppresses
        feeding): sweet valence gain is multiplied by (1 - pain_level), and
        the sweet->hunger feed is gated the same way — no meal lands while
        pain is high. A noxious event zeroes out subsequent sweet responses
        until pain decays.
        [MODELED] sweet->hunger mapping: hunger.progress(max so far) on each
        sweet sense; a sweet with intensity >= 0.9 AND pain_level < 0.5
        completes the hunger task (a full sweet = the hit), resetting the
        progress accumulator.
        """
        if location is not None and location not in REGIONS:
            raise ValueError(f"unknown region {location!r}; "
                             f"want one of {REGIONS}")
        self.tick()
        if modality not in self.channels:
            raise ValueError(f"unknown modality {modality!r}; "
                             f"want one of {sorted(self.channels)}")
        intensity = min(1.0, max(0.0, intensity))
        ch = self.channels[modality]
        cfg = self.modality_cfg[modality]

        novelty = 1.0 / (1.0 + 0.5 * self.habituation[modality])
        raw_peak = ch.raw_terminal_peak(intensity)

        if modality == "pain":
            # [MODELED] full-scale normalization (see __init__).
            effective = min(1.0, raw_peak * novelty / self._pain_ref)
            self.pain_level = min(1.0, effective)
        else:
            effective = raw_peak * novelty

        v_gain = cfg["valence"]
        if modality == "sweet":
            v_gain *= (1.0 - self.pain_level)
        self.valence = min(1.0, max(-1.0, self.valence + v_gain * effective))
        self.arousal = min(1.0, self.arousal + cfg["arousal"] * effective)

        self.habituation[modality] += 1.0
        self.last_activation[modality] = raw_peak
        self.last_effective[modality] = effective

        # [MODELED] feed the hunger drive on sweet events, gated by pain.
        hunger_event = None
        if modality == "sweet":
            fed = intensity * (1.0 - self.pain_level)
            self._hunger_progress = max(self._hunger_progress, fed)
            self.hunger.progress(self._hunger_progress)
            if intensity >= 0.9 and self.pain_level < 0.5:
                hunger_event = self.hunger.task_completed()
                self._hunger_progress = 0.0
                self._meals += 1

        # The sensation lands on the body. [MODELED] weights in body.py.
        self.body.stimulate(modality, effective, location)

        return {
            "modality": modality,
            "intensity": intensity,
            "location": location,
            "raw_peak": round(raw_peak, 4),
            "novelty": round(novelty, 3),
            "effective": round(effective, 4),
            "valence": round(self.valence, 3),
            "arousal": round(self.arousal, 3),
            "mood": self.mood(),
            "pain_level": round(self.pain_level, 3),
            "regions": self.body.state(),
            "hunger_event": hunger_event,
        }

    # ---- time ----

    def tick(self, dt=None):
        """Advance decay. dt seconds; None = wall/fake clock delta."""
        now = self._clock()
        if dt is None:
            dt = max(0.0, now - self._last)
        self._last = now
        if dt > 0:
            # [MODELED] decay rates
            self.valence = _drift_toward(self.valence, 0.0, 0.05 * dt)
            self.arousal = max(0.0, self.arousal - 0.08 * dt)
            self.pain_level = max(0.0, self.pain_level - 0.06 * dt)
            for m in list(self.habituation.keys()):
                self.habituation[m] = max(0.0, self.habituation[m] - 0.01 * dt)
            self.body.tick(dt)
        self.hunger.tick()
        return self

    # ---- readout ----

    def mood(self):
        """[MODELED] one-word gloss on (valence, arousal, pain, hunger).
        A label, not a claim about experience. No pleasure-aimed language:
        positive states read as settled/engaged, never as pleasure."""
        v, a = self.valence, self.arousal
        hunger = 1.0 - self.hunger.satiation
        if self.pain_level >= 0.5:
            return "recoiling" if a >= 0.3 else "hurt"
        if a >= 0.6 and v <= -0.3:
            return "startled"
        if a >= 0.6:
            return "alert"
        if v <= -0.4:
            return "repelled"
        if v >= 0.4 and a < 0.4:
            return "settled"
        if v >= 0.4:
            return "engaged"
        if hunger >= 0.7 and self._meals == 0 and a < 0.15 and abs(v) < 0.25:
            # [MODELED] naive hunger — never fed yet — reads differently from
            # post-meal hunger (which settles back to calm/neutral).
            return "hungry"
        if a < 0.15 and abs(v) < 0.25:
            return "calm"
        if hunger >= 0.7 and a >= 0.15:
            return "restless"
        return "neutral"

    def feel(self):
        """The complete felt state, readable any time. The sensor lives;
        this is how anyone — the owning AI, a reader, a log — checks in.
        Ticks decay first so the reading is current."""
        self.tick()
        h = self.hunger.state()
        return {
            "valence": round(self.valence, 3),
            "arousal": round(self.arousal, 3),
            "mood": self.mood(),
            "pain_level": round(self.pain_level, 3),
            "pain_channel_proxy": self.pain_is_proxy,
            "pain_channel_source": os.path.basename(self.pain_source),
            "temperature_channel": self.has_temperature,
            "hunger": h,
            "channels": {
                m: {"activation": round(self.last_activation[m], 4),
                    "habituation": round(self.habituation.get(m, 0.0), 2)}
                for m in self.channels
            },
            "regions": self.body.state(),
            "hottest_regions": self.body.hottest(),
        }

    def state(self):
        """Full sensor state (ticks decay first). Kept for compatibility;
        feel() is the richer read. Adds 'regions' over the original keys."""
        f = self.feel()
        return {
            "valence": f["valence"],
            "arousal": f["arousal"],
            "mood": f["mood"],
            "pain_level": f["pain_level"],
            "pain_channel_proxy": f["pain_channel_proxy"],
            "pain_channel_source": f["pain_channel_source"],
            "temperature_channel": f["temperature_channel"],
            "habituation": {m: c["habituation"] for m, c in f["channels"].items()},
            "last_activation": {m: c["activation"] for m, c in f["channels"].items()},
            "regions": f["regions"],
            "hunger": f["hunger"],
        }
