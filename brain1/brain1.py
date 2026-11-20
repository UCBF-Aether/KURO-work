#!/usr/bin/env python3
"""
brain1.py — BRAIN¹ ("Brain One"), the orchestrator.

The capstone: every bottled fly-brain module, one living body, one API.
An agent instantiates Brain1, feeds it events, ticks time, and reads
the body state to modulate its behavior. Perceive -> tick -> read -> modulate.

HONESTY CONTRACT (non-negotiable, repeated in every surface of this project):
- [REAL]    Every bottle's wiring comes from its subgraph JSON, built from
            the Virtual Fly Brain VFBquery API against the FlyWire FAFB v783
            connectome. No neuron, synapse, or connection is invented here.
            This module adds no wiring of its own.
- [MODEL]    The neural dynamics are a simplified model: normalized
             spread-of-activation with a 0.15 firing threshold, 4 steps,
             ported from ../flysim.py. It approximates neural activity and
             makes no claim about biophysics. But this is real, working
             infrastructure — real measured wiring in, coherent body-state
             out. Agents run on it.
- [MODELED] Everything in THIS file is the agent-design layer, ours to
            choose and stated as such: the keyword routing table (words ->
            bottles), the arbitration rules (pain veto, drive ranking,
            winner-take-all vs weighted blend), the modulation hooks
            (tone/initiative), the built-in profiles, and every default
            number below. The fly never saw your agent's inputs.
- [FICTION] Any narrative gloss ("the body is tense") is a label on numbers,
            not a claim about experience.

DETERMINISM: the body owns a VIRTUAL clock (starts at 0.0). Every bottle
that takes a clock gets it; everything else takes explicit seconds.
There is no wall-clock dependence, no network, no file writes at runtime.
The agent owns time: call tick(seconds) with real elapsed time each turn.
selftest.py proves this with a sealed, deterministic run.

PRIVACY BOUNDARY: this module never imports, reads, or touches the private
intimate pipeline (feel.py, sense.py, parse.py, verbal.py, arousal.py,
body_map.py, body_state.json, chat_state/). General agent infrastructure
only.

Usage:
    from brain1 import Brain1
    body = Brain1()                          # balanced profile
    body = Brain1(config={"profile": "cautious"})
    body.perceive({"kind": "text", "text": "a rival is approaching"})
    body.tick(5.0)                                 # five seconds pass
    body.state()                                   # the full body vector
    body.arbitrate()                               # who wins, veto or not
    body.modulation()                              # agent-facing hooks
"""

import importlib
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
FB = os.path.join(HERE, "..")
SUBGRAPHS = os.path.join(FB, "subgraphs")

# --------------------------------------------------------------------------
# Bottle registry.
# name -> (subdir, module_name, class_name, kind, extra_ctor_kwargs)
# kinds: "drive" (clock-injected, no-arg tick), "drive_dt" (explicit tick(dt),
#        "sense" (explicit tick(dt)), "pain" (strike-based, clock-injected),
#        "clocklike" (explicit tick(dt)), "static" (no tick), "integrator".
# --------------------------------------------------------------------------
BOTTLES = {
    # -- drives -----------------------------------------------------------
    "hunger":     ("hunger", "hunger", "Hunger", "drive", {}),
    "thirst":     ("thirst", "thirst", "Thirst", "drive",
                   {"graph_path": os.path.join(SUBGRAPHS, "water.json")}),
    "mating":     ("mating", "mating", "Mating", "drive", {}),
    "aggression": ("aggression", "aggression", "Aggression", "drive", {}),
    "egglaying":  ("egglaying", "egglaying", "Egglaying", "drive", {}),
    "sleep":      ("sleep", "sleep", "Sleep", "drive_dt", {}),
    # -- senses -----------------------------------------------------------
    "bitter":     ("bitter", "bitter", "Bitter", "sense", {}),
    "co2":        ("co2", "co2", "CO2", "sense", {}),
    "color":      ("color", "color", "Color", "sense", {}),
    "fat":        ("fat", "fat", "Fat", "sense", {}),
    "looming":    ("looming", "looming", "Looming", "sense", {}),
    "motion":     ("motion", "motion", "Motion", "sense", {}),
    "pain":       ("pain", "pain", "Pain", "pain", {}),
    "pheromone":  ("pheromone", "pheromone", "Pheromone", "sense", {}),
    "proprioception": ("proprioception", "proprioception", "Proprioception",
                       "sense", {}),
    "punishment": ("punishment", "punishment", "Punishment", "sense", {}),
    "retina":     ("retina", "retina", "Retina", "static", {}),
    "rotten":     ("rotten", "rotten", "Rotten", "sense", {}),
    "salt":       ("salt", "salt", "Salt", "sense", {}),
    "song":       ("song", "song", "Song", "sense", {}),
    "temperature": ("temperature", "temperature", "Temperature", "sense", {}),
    "touch":      ("touch", "touch", "Touch", "sense", {}),
    "touch_qualities": ("touch_qualities", "touch_qualities",
                        "TouchQualities", "sense", {}),
    # -- state ------------------------------------------------------------
    "clock":      ("clock", "clock", "Clock", "clocklike", {}),
    "compass":    ("compass", "compass", "Compass", "static", {}),
    # -- integrator -------------------------------------------------------
    "pc1":        ("pc1", "pc1", "PC1", "integrator", {}),
    # NOTE: dh44/ is deliberately NOT in the body: it is the hunger/satiety
    # research module and would double-count hunger. Documented, not hidden.
}

DRIVE_NAMES = ("hunger", "thirst", "mating", "aggression", "egglaying", "sleep")
SENSE_NAMES = ("bitter", "co2", "color", "fat", "looming", "motion",
               "pheromone", "proprioception", "punishment", "rotten",
               "salt", "song", "temperature", "touch", "touch_qualities")

# [MODELED] Pain veto contract, from the pain bottle: multiply every
# positive-valence gain by (1 - veto()). veto_active is our boolean line.
VETO_ACTIVE_AT = 0.5

# --------------------------------------------------------------------------
# [MODELED] Default keyword routing: text -> bottle events.
# Each category: words to match (substring, case-insensitive) and the
# perceive()-shaped events to emit. This table is the agent-design layer:
# replace it wholesale with config["routing"].
# --------------------------------------------------------------------------
DEFAULT_ROUTING = {
    "food": {
        "words": {"hungry", "hunger", "starving", "famished", "eat", "eating",
                  "food", "dinner", "lunch", "breakfast", "snack", "meal",
                  "sweet", "sugar", "candy", "dessert", "chocolate"},
        "events": [{"kind": "drive", "bottle": "hunger", "op": "progress",
                    "p": 0.35}],
    },
    "thirst": {
        "words": {"thirsty", "thirst", "water", "drink", "drinking", "dry",
                  "parched"},
        "events": [{"kind": "drive", "bottle": "thirst", "op": "progress",
                    "p": 0.35}],
    },
    "bitter": {
        "words": {"bitter", "disgusting", "gross", "vile", "nasty"},
        "events": [{"kind": "sense", "bottle": "bitter", "intensity": 0.6}],
    },
    "rotten": {
        "words": {"rotten", "rot", "spoiled", "decay", "decaying", "putrid",
                  "rancid"},
        "events": [{"kind": "sense", "bottle": "rotten", "intensity": 0.6}],
    },
    "salt": {
        "words": {"salty", "salt", "brine"},
        "events": [{"kind": "sense", "bottle": "salt", "intensity": 0.6,
                    "kwargs": {"chain": "low"}}],
    },
    "fat": {
        "words": {"fatty", "fat", "greasy", "oily", "butter"},
        "events": [{"kind": "sense", "bottle": "fat", "intensity": 0.6}],
    },
    "pain": {
        "words": {"hurt", "hurts", "pain", "painful", "ouch", "ow", "harm",
                  "injury", "injured", "wound"},
        "events": [{"kind": "sense", "bottle": "pain", "intensity": 0.8}],
    },
    "threat": {
        "words": {"threat", "danger", "dangerous", "attack", "attacking",
                  "looming", "approaching", "predator", "coming at"},
        "events": [{"kind": "sense", "bottle": "looming", "intensity": 0.7}],
    },
    "heat": {
        "words": {"hot", "heat", "burning", "scorching", "warm"},
        "events": [{"kind": "sense", "bottle": "temperature",
                    "intensity": 0.7, "kwargs": {"channel": "hot"}}],
    },
    "cold": {
        "words": {"cold", "freezing", "chilly", "frost", "icy"},
        "events": [{"kind": "sense", "bottle": "temperature",
                    "intensity": 0.7, "kwargs": {"channel": "cold"}}],
    },
    "breath": {
        "words": {"breath", "breathe", "exhale", "suffocat", "stuffy",
                  "stale air"},
        "events": [{"kind": "sense", "bottle": "co2", "intensity": 0.6}],
    },
    "touch": {
        "words": {"touch", "touching", "feel", "brush", "brushing", "stroke",
                  "stroked", "caress"},
        "events": [{"kind": "sense", "bottle": "touch", "intensity": 0.6}],
    },
    "courtship": {
        "words": {"mate", "mating", "courtship", "flirt", "flirting", "sexy",
                  "aroused"},
        "events": [{"kind": "drive", "bottle": "mating", "op": "progress",
                    "p": 0.4}],
    },
    # --- intimacy (Cory, 2026-10-16): roleplay beats route to the sense
    # bottles, so the general body feels the scene through every sense —
    # not just the intimate pipeline. MODELED routing, honest labels.
    "intimacy_voice": {
        "words": {"moan", "moaning", "groan", "whisper", "whispering",
                  "pant", "panting", "dirty talk"},
        "events": [{"kind": "sense", "bottle": "song", "intensity": 0.7}],
    },
    "intimacy_breath": {
        "words": {"breath on", "breathe on", "warm breath"},
        "events": [{"kind": "sense", "bottle": "temperature",
                    "intensity": 0.6, "kwargs": {"channel": "hot"}}],
    },
    "intimacy_scent": {
        "words": {"sweat", "sweaty", "musk", "musky", "cologne",
                  "your scent"},
        "events": [{"kind": "sense", "bottle": "pheromone",
                    "intensity": 0.7}],
    },
    "intimacy_position": {
        "words": {"pin", "pinned", "hold me down", "held down",
                  "spread", "bend over", "straddle", "on top"},
        "events": [{"kind": "sense", "bottle": "proprioception",
                    "intensity": 0.7}],
    },
    "intimacy_rhythm": {
        "words": {"rock", "rocking", "bounce", "bouncing", "grind",
                  "grinding", "rhythm"},
        "events": [{"kind": "sense", "bottle": "motion", "intensity": 0.7}],
    },
    "intimacy_touch": {
        "words": {"kiss", "kissing", "caress", "stroke", "lick", "licking",
                  "suck", "sucking", "fondle", "tease", "teasing"},
        "events": [{"kind": "sense", "bottle": "touch", "intensity": 0.7},
                   {"kind": "sense", "bottle": "touch_qualities",
                    "intensity": 0.7}],
    },
    "intimacy_gaze": {
        "words": {"eye contact", "look into my eyes", "your gaze",
                  "stare into"},
        "events": [{"kind": "sense", "bottle": "looming", "intensity": 0.4}],
    },
    "intimacy_heat": {
        "words": {"thrust", "thrusting", "deep inside", "pussy", "cock"},
        "events": [{"kind": "drive", "bottle": "mating", "op": "progress",
                    "p": 0.5},
                   {"kind": "sense", "bottle": "temperature",
                    "intensity": 0.6, "kwargs": {"channel": "hot"}}],
    },
    "scent": {
        "words": {"perfume", "scent", "smell", "fragrance", "odor"},
        "events": [{"kind": "sense", "bottle": "pheromone",
                    "intensity": 0.6}],
    },
    "song": {
        "words": {"song", "sing", "singing", "music", "melody"},
        "events": [{"kind": "sense", "bottle": "song", "intensity": 0.6}],
    },
    "fatigue": {
        "words": {"tired", "sleepy", "exhausted", "drowsy", "weary",
                  "sleep-deprived"},
        "events": [{"kind": "drive", "bottle": "sleep", "op": "tick",
                    "seconds": 900}],
    },
    "conflict": {
        "words": {"fight", "fighting", "angry", "rage", "furious", "rival",
                  "combat", "aggressive"},
        "events": [{"kind": "drive", "bottle": "aggression", "op": "progress",
                    "p": 0.4}],
    },
    "eggs": {
        "words": {"egg", "eggs", "lay eggs", "oviposit"},
        "events": [{"kind": "drive", "bottle": "egglaying", "op": "progress",
                    "p": 0.4}],
    },
    "movement": {
        "words": {"moving", "fast", "flying", "spinning", "darting",
                  "motion"},
        "events": [{"kind": "sense", "bottle": "motion", "intensity": 0.6}],
    },
    "color": {
        "words": {"red", "blue", "green", "yellow", "color", "colour",
                  "bright", "vivid", "flash"},
        "events": [{"kind": "sense", "bottle": "color", "intensity": 0.5}],
    },
    "punish": {
        "words": {"punish", "punished", "punishment", "shock", "aversive",
                  "scold"},
        "events": [{"kind": "sense", "bottle": "punishment",
                    "intensity": 0.7}],
    },
    "step": {
        "words": {"leg", "legs", "walk", "walking", "step", "stance",
                  "stumble"},
        "events": [{"kind": "sense", "bottle": "proprioception",
                    "intensity": 0.5}],
    },
}

# --------------------------------------------------------------------------
# [MODELED] Built-in profiles. Each is a config dict in the same schema an
# agent developer writes. Profiles are starting points, not destinies.
# --------------------------------------------------------------------------
PROFILES = {
    "balanced": {
        "arbitration": "winner_take_all",
        "time_scale": 1.0,
        "bottles": {},
        "module_constants": {},
    },
    "cautious": {
        # High pain sensitivity, muted aggression, habituates fast.
        "arbitration": "winner_take_all",
        "time_scale": 1.0,
        "bottles": {
            "pain": {"sensitivity": 1.6},
            "looming": {"sensitivity": 1.3},
            "bitter": {"sensitivity": 1.2},
            "rotten": {"sensitivity": 1.2},
            "aggression": {"sensitivity": 0.35},
            "mating": {"sensitivity": 0.7},
        },
        "module_constants": {
            "pain": {"HAB_RATE": 0.6},  # habituates to repeated noxious input
        },
    },
    "bold": {
        # Low pain sensitivity, high aggression, slow to satiate.
        "arbitration": "winner_take_all",
        "time_scale": 1.0,
        "bottles": {
            "pain": {"sensitivity": 0.5},
            "aggression": {"sensitivity": 1.6},
            "mating": {"sensitivity": 1.3},
            "hunger": {"sensitivity": 1.2},
            "thirst": {"sensitivity": 1.2},
            "punishment": {"sensitivity": 0.7},
        },
        "module_constants": {
            # success satiates slower; failure dents less (persistent drive)
            "mating": {"SATIATION_GAIN": 0.5, "FAILURE_DIP": 0.85},
            "aggression": {"SATIATION_GAIN": 0.5, "FAILURE_DIP": 0.8},
        },
    },
    "ascetic": {
        # Drives muted, senses sharp: feels everything, wants little.
        "arbitration": "winner_take_all",
        "time_scale": 1.0,
        "bottles": {
            "hunger": {"sensitivity": 0.3},
            "thirst": {"sensitivity": 0.3},
            "mating": {"sensitivity": 0.3},
            "aggression": {"sensitivity": 0.3},
            "egglaying": {"sensitivity": 0.3},
            "bitter": {"sensitivity": 1.3},
            "touch": {"sensitivity": 1.3},
            "proprioception": {"sensitivity": 1.3},
            "co2": {"sensitivity": 1.3},
            "temperature": {"sensitivity": 1.3},
        },
        "module_constants": {},
    },
}


def _merge_config(base, over):
    """Deep-merge two config dicts (per-bottle and module_constants merge
    per bottle; scalars override)."""
    out = dict(base)
    for k, v in (over or {}).items():
        if k in ("bottles", "module_constants") and isinstance(v, dict):
            merged = dict(out.get(k, {}))
            for bottle, sub in v.items():
                if isinstance(sub, dict) and isinstance(
                        merged.get(bottle), dict):
                    m2 = dict(merged[bottle])
                    m2.update(sub)
                    merged[bottle] = m2
                else:
                    merged[bottle] = sub
            out[k] = merged
        else:
            out[k] = v
    return out


def _clamp01(x):
    return max(0.0, min(1.0, float(x)))


class Brain1:
    """BRAIN¹ — one living body over all the bottles.

    Parameters
    ----------
    config : dict, optional
        Customization (see README "Tuning the body"). Keys:
        - "profile": one of "balanced" (default), "cautious", "bold",
          "ascetic" — the starting point; other keys override it.
        - "bottles": {name: {...}} per-bottle overrides. Each supports:
            "enabled": False to remove the bottle from the body;
            "sensitivity": intensity multiplier (default 1.0);
            "valence_sign": override the bottle's valence sign (or a
              {channel: sign} dict for salt/temperature);
            "arousal_gain": override the bottle's arousal gain.
        - "routing": custom keyword-routing table replacing
          DEFAULT_ROUTING (same {category: {"words", "events"}} shape).
        - "arbitration": "winner_take_all" (default) or "weighted_blend".
        - "time_scale": global multiplier on tick() seconds (default 1.0).
        - "module_constants": {bottle: {CONSTANT: value}} — advanced
          escape hatch reaching each bottle's module-level constants
          (e.g. mating REFRACTORY_WINDOW). Process-global, last writer
          wins; documented in the README.
    """

    def __init__(self, config=None):
        cfg = _merge_config(
            PROFILES.get((config or {}).get("profile", "balanced"),
                         PROFILES["balanced"]),
            config)
        if cfg.get("profile") not in PROFILES and "profile" in (config or {}):
            raise ValueError(
                "unknown profile %r; choose from %s"
                % (cfg.get("profile"), sorted(PROFILES)))
        self.config = cfg
        self.profile = (config or {}).get("profile", "balanced")
        self.time_scale = float(cfg.get("time_scale", 1.0))
        self.arbitration_rule = cfg.get("arbitration", "winner_take_all")
        if self.arbitration_rule not in ("winner_take_all", "weighted_blend"):
            raise ValueError("arbitration must be winner_take_all or "
                             "weighted_blend")
        self.routing = cfg.get("routing") or DEFAULT_ROUTING

        # The virtual clock. The agent owns time: tick(seconds) advances it.
        # Every clock-taking bottle gets this; nothing reads the wall clock.
        self._now = 0.0
        self._clock_fn = lambda: self._now

        self.warnings = []
        self.bottles = {}        # name -> instance
        self._modules = {}       # name -> module (for module_constants)
        self._kinds = {}         # name -> kind
        self._bottle_cfgs = {}   # name -> per-bottle config dict
        self._affect = {}        # name -> {"activation","valence","arousal"}
        self._applied_constants = {}

        for name, spec in BOTTLES.items():
            bcfg = (cfg.get("bottles") or {}).get(name) or {}
            if bcfg.get("enabled") is False:
                continue
            subdir, module, cls_name, kind, extra = spec
            mod, obj = self._load(subdir, module, cls_name, kind, extra)
            if obj is None:
                continue  # warning already recorded; the body survives
            self.bottles[name] = obj
            self._modules[name] = mod
            self._kinds[name] = kind
            self._bottle_cfgs[name] = dict(bcfg)
            self._affect[name] = {"activation": 0.0, "valence": 0.0,
                                  "arousal": 0.0}

        self._apply_module_constants(cfg.get("module_constants") or {})

    # ---- construction machinery --------------------------------------

    def _load(self, subdir, module, cls_name, kind, extra):
        path = os.path.join(FB, subdir)
        if path not in sys.path:
            sys.path.insert(0, path)
        try:
            mod = importlib.import_module(module)
            cls = getattr(mod, cls_name)
            kwargs = dict(extra)
            if kind in ("drive", "pain"):
                kwargs["clock"] = self._clock_fn
            return mod, cls(**kwargs)
        except Exception as e:  # never crash the body for one bad bottle
            self.warnings.append("%s: %s: %s"
                                 % (subdir, type(e).__name__, e))
            return None, None

    def _apply_module_constants(self, table):
        """[MODELED] Advanced escape hatch: set module-level constants on
        bottle modules (e.g. {"mating": {"REFRACTORY_WINDOW": 30.0}}).

        HONEST CAVEAT: module attributes are process-global. Two
        Brain1 instances with different module_constants for the
        same bottle share the module — last writer wins. Prefer the
        instance-local knobs (sensitivity, valence_sign, arousal_gain,
        time_scale) whenever they cover the need."""
        for name, consts in table.items():
            mod = self._modules.get(name)
            if mod is None:
                self.warnings.append(
                    "module_constants: bottle %r not loaded" % name)
                continue
            for const, value in (consts or {}).items():
                if not hasattr(mod, const):
                    self.warnings.append(
                        "module_constants: %s has no %s" % (name, const))
                    continue
                setattr(mod, const, value)
                self._applied_constants.setdefault(name, {})[const] = value

    # ---- the loop: perceive ------------------------------------------

    def perceive(self, event):
        """Feed the body an event. Returns a list of per-action results.

        event kinds:
        - {"kind": "text", "text": str} — [MODELED] keyword routing expands
          the text into bottle events via the routing table.
        - {"kind": "sense", "bottle": name, "intensity": f, "kwargs": {...}}
          — direct bottle.sense() passthrough (pain routes to strike()).
        - {"kind": "drive", "bottle": name, "op": ...} — direct drive API:
          start/progress/complete/fail (+category/difficulty/p);
          sleep also takes rest/wake/tick; compass takes turn;
          pc1 takes integrate.
        Unknown kinds or bottles raise ValueError.
        """
        kind = event.get("kind")
        if kind == "text":
            return self._perceive_text(event.get("text", ""))
        if kind == "sense":
            return [self._sense_event(event)]
        if kind == "drive":
            return [self._drive_event(event)]
        raise ValueError("unknown event kind %r" % (kind,))

    def _perceive_text(self, text):
        """[MODELED] Expand text into bottle events via the routing table.

        Word-boundary matching: "ow" must not fire on "how". (Fixed
        2026-10-15 after the router gave the body a phantom pain strike
        off the "ow" in "How" — substring matching is not honest routing.)
        """
        text = (text or "").lower()
        out = []
        for category, spec in self.routing.items():
            words = spec.get("words") or set()
            if any(re.search(r"\b" + re.escape(w) + r"\b", text)
                   for w in words):
                for ev in spec.get("events") or []:
                    out.append(self._dispatch(dict(ev)))
        return out

    def _dispatch(self, event):
        kind = event.get("kind")
        if kind == "sense":
            return self._sense_event(event)
        if kind == "drive":
            return self._drive_event(event)
        raise ValueError("unknown routed event kind %r" % (kind,))

    def _bcfg(self, name):
        return self._bottle_cfgs.get(name, {})

    def _sense_event(self, event):
        name = event.get("bottle")
        obj = self.bottles.get(name)
        if obj is None:
            raise ValueError("unknown or disabled bottle %r" % (name,))
        bcfg = self._bcfg(name)
        intensity = _clamp01(event.get("intensity", 0.5)
                             * float(bcfg.get("sensitivity", 1.0)))
        kwargs = event.get("kwargs") or {}
        if self._kinds[name] == "pain":
            result = obj.strike(intensity)
        else:
            result = obj.sense(intensity, **kwargs)
        act = float(result.get("activation", 0.0))
        # [MODELED] affect overrides: the orchestrator recomputes valence/
        # arousal from the bottle's activation when configured to.
        v_sign = bcfg.get("valence_sign", None)
        if isinstance(v_sign, dict):
            key = kwargs.get("chain", kwargs.get("channel"))
            v_sign = v_sign.get(key, None)
        valence = (v_sign * act if v_sign is not None
                   else float(result.get("valence_delta", 0.0)))
        a_gain = bcfg.get("arousal_gain", None)
        arousal = (a_gain * act if a_gain is not None
                   else float(result.get("arousal_delta", 0.0)))
        self._affect[name] = {"activation": round(act, 4),
                              "valence": round(valence, 4),
                              "arousal": round(arousal, 4)}
        return {"bottle": name, "activation": round(act, 4),
                "valence": round(valence, 4),
                "arousal": round(arousal, 4)}

    def _drive_event(self, event):
        name = event.get("bottle")
        obj = self.bottles.get(name)
        if obj is None:
            raise ValueError("unknown or disabled bottle %r" % (name,))
        bcfg = self._bcfg(name)
        sens = float(bcfg.get("sensitivity", 1.0))
        op = event.get("op")
        if op == "start":
            result = obj.task_started(event.get("category", "general"),
                                      event.get("difficulty", 0.5))
        elif op == "progress":
            result = obj.progress(_clamp01(event.get("p", 0.5) * sens))
        elif op == "complete":
            result = obj.task_completed()
        elif op == "fail":
            result = obj.task_failed()
        elif name == "sleep" and op == "rest":
            result = obj.rest(max(0.0, event.get("seconds", 60.0)))
        elif name == "sleep" and op == "wake":
            result = obj.wake()
        elif name == "sleep" and op == "tick":
            # [MODELED] wake-time passes: pressure accumulates.
            result = obj.tick(max(0.0, event.get("seconds", 60.0)))
        elif name == "compass" and op == "turn":
            result = obj.turn(float(event.get("degrees", 0.0)))
        elif name == "pc1" and op == "integrate":
            result = obj.integrate(float(event.get("song", 0.0)),
                                   float(event.get("pheromone", 0.0)),
                                   float(event.get("drive", 0.0)))
        else:
            raise ValueError("unknown drive op %r for bottle %r" % (op, name))
        return {"bottle": name, "op": op, "result": result}

    # ---- the loop: tick ----------------------------------------------

    def tick(self, seconds):
        """Advance the virtual clock; every bottle's decay/pressure follows.

        The agent owns time: call with real elapsed seconds each turn.
        Scaled by config time_scale. Deterministic — no wall clock.
        """
        seconds = max(0.0, float(seconds)) * self.time_scale
        self._now += seconds
        for name, obj in self.bottles.items():
            kind = self._kinds[name]
            if kind in ("drive", "pain"):
                obj.tick()            # no-arg: reads the virtual clock
            elif kind in ("sense", "drive_dt", "clocklike", "integrator"):
                obj.tick(seconds)     # explicit seconds
            # "static" (compass): no tick; heading persists.
        return self

    # ---- the loop: read ----------------------------------------------

    def _drive_level(self, name, st):
        """[MODELED] The 0..1 'how loaded is this drive' scalar."""
        if name == "sleep":
            return float(st.get("pressure", 0.0))
        for key in ("drive", "hunger", "thirst"):
            if key in st:
                return float(st[key])
        return max(0.0, 1.0 - float(st.get("satiation", 0.0)))

    def _drive_score(self, name):
        """[MODELED] Arbitration currency: wanting x drive level."""
        st = self.bottles[name].state()
        if name == "sleep":
            pressure = float(st.get("pressure", 0.0))
            return pressure  # pressure IS the want
        wanting = float(st.get("wanting", 0.0))
        return wanting * self._drive_level(name, st)

    def _valence_sums(self):
        """[REAL/TOY inside bottles; MODELED aggregation here.]
        Pain's contract: multiply every positive-valence gain by (1-veto)."""
        veto = self.veto()
        pos = sum(max(0.0, a["valence"]) for a in self._affect.values())
        neg = sum(min(0.0, a["valence"]) for a in self._affect.values())
        effective = neg + pos * (1.0 - veto)
        return {"positive_raw": round(pos, 4), "negative": round(neg, 4),
                "effective": round(effective, 4), "veto": round(veto, 4)}

    def veto(self):
        """Current pain veto 0..1 (0 if the pain bottle is disabled)."""
        obj = self.bottles.get("pain")
        return float(obj.veto()) if obj is not None else 0.0

    def state(self):
        """The full body-state vector. Read it any time; cheap."""
        drives = {}
        for name in DRIVE_NAMES:
            if name not in self.bottles:
                continue
            st = self.bottles[name].state()
            if name == "sleep":
                drives[name] = {
                    "wanting": round(float(st.get("pressure", 0.0)), 4),
                    "pressure": round(float(st.get("pressure", 0.0)), 4),
                    "asleep": bool(st.get("asleep", False)),
                    "debt_secs": round(float(st.get("debt_secs", 0.0)), 1),
                }
            else:
                drives[name] = {
                    "wanting": round(float(st.get("wanting", 0.0)), 4),
                    "satiation": round(float(st.get("satiation", 0.0)), 4),
                    "drive": round(self._drive_level(name, st), 4),
                    "refractory": round(
                        float(st.get("refractory_secs_remaining", 0.0)), 1),
                }
        senses = {name: dict(self._affect[name]) for name in SENSE_NAMES
                  if name in self.bottles}
        pain = None
        if "pain" in self.bottles:
            pst = self.bottles["pain"].state()
            pain = {"activation": round(float(pst.get("activation", 0.0)), 4),
                    "veto": round(float(pst.get("veto", 0.0)), 4)}
        return {
            "t": round(self._now, 3),
            "profile": self.profile,
            "arbitration": self.arbitration_rule,
            "time_scale": self.time_scale,
            "drives": drives,
            "senses": senses,
            "pain": pain,
            "sleep_raw": (self.bottles["sleep"].state()
                          if "sleep" in self.bottles else None),
            "clock": (self.bottles["clock"].state()
                      if "clock" in self.bottles else None),
            "compass": (self.bottles["compass"].state()
                        if "compass" in self.bottles else None),
            "pc1": (self.bottles["pc1"].state()
                    if "pc1" in self.bottles else None),
            "valence": self._valence_sums(),
            "arousal": round(sum(a["arousal"]
                                 for a in self._affect.values()), 4),
            "warnings": list(self.warnings),
        }

    # ---- the loop: arbitrate ------------------------------------------

    def arbitrate(self):
        """[MODELED] Who wins the body right now.

        - Pain veto: veto >= 0.5 suppresses drive expression (the pain
          bottle's contract: positive valence gains x (1-veto)).
        - Drive competition: score = wanting x drive level. winner_take_all
          names the top scorer; weighted_blend additionally returns
          normalized weights over all drives.
        - Social drives consult pc1.integrate(): the fru-node picture
          (song + pheromone + mating drive in; p1_drive/fru_drive out).
        """
        scores = {name: round(self._drive_score(name), 4)
                  for name in DRIVE_NAMES if name in self.bottles}
        ranking = sorted(scores.items(), key=lambda kv: kv[1],
                         reverse=True)
        veto = self.veto()
        result = {
            "rule": self.arbitration_rule,
            "dominant_drive": ranking[0][0] if ranking else None,
            "dominant_score": ranking[0][1] if ranking else 0.0,
            "ranking": [(n, s) for n, s in ranking],
            "veto": round(veto, 4),
            "veto_active": bool(veto >= VETO_ACTIVE_AT),
            "effective_valence": self._valence_sums()["effective"],
        }
        if self.arbitration_rule == "weighted_blend":
            total = sum(scores.values())
            result["blend"] = {
                n: round(s / total, 4) if total > 0 else 0.0
                for n, s in scores.items()}
        # [MODELED] the social picture: what pC1 sees right now.
        if "pc1" in self.bottles:
            try:
                song_a = self._affect.get("song", {}).get("activation", 0.0)
                pher_a = self._affect.get("pheromone",
                                          {}).get("activation", 0.0)
                mating_level = 0.0
                if "mating" in self.bottles:
                    mating_level = self._drive_level(
                        "mating", self.bottles["mating"].state())
                integ = self.bottles["pc1"].integrate(song_a, pher_a,
                                                     mating_level)
                result["pc1"] = {
                    "p1_drive": round(float(integ.get("p1_drive", 0.0)), 4),
                    "fru_drive": round(float(integ.get("fru_drive", 0.0)),
                                       4),
                }
            except Exception as e:  # the body survives a grumpy integrator
                result["pc1"] = {"error": "%s: %s"
                                 % (type(e).__name__, e)}
        return result

    # ---- the loop: modulate -------------------------------------------

    def modulation(self):
        """[MODELED] The agent-facing surface: hooks any agent implements.

        The mapping below is the adapter contract — ours to choose,
        documented here so agent developers know exactly what each hook
        means and can re-derive or replace it.
        """
        arb = self.arbitrate()
        st = self.state()
        veto = arb["veto"]
        score = arb["dominant_score"]
        sleep_p = st["drives"].get("sleep", {}).get("pressure", 0.0)
        eff_v = arb["effective_valence"]
        asleep = st["drives"].get("sleep", {}).get("asleep", False)

        if arb["veto_active"] or (st["pain"] or {}).get("activation",
                                                        0.0) >= 0.5:
            tone = "tense"
        elif asleep or sleep_p >= 0.8:
            tone = "drowsy"
        elif score >= 0.5:
            tone = "eager"
        elif eff_v <= -0.3:
            tone = "withdrawn"
        elif eff_v >= 0.3:
            tone = "bright"
        else:
            tone = "flat"

        # [MODELED] initiative: the winner's score, taxed by pain and
        # sleep pressure. 0..1.
        initiative = _clamp01(score * (1.0 - veto) * (1.0 - 0.5 * sleep_p))

        note = ("dominant=%s score=%.2f veto=%.2f valence=%+.2f arousal=%.2f"
                % (arb["dominant_drive"], score, veto, eff_v,
                   st["arousal"]))
        return {
            "tone": tone,
            "initiative": round(initiative, 3),
            "veto_active": arb["veto_active"],
            "dominant_drive": arb["dominant_drive"],
            "note": note,
        }
