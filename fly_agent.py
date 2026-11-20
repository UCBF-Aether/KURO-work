#!/usr/bin/env python3
"""fly_agent.py — the loop-integrated BRAIN¹ agent.

ARCHITECTURE (the point of this build):
    The model cannot generate a word without passing through the body.
    Every turn runs the full loop:

        user text -> body.perceive({'kind':'text',...})
                  -> body.tick(wall-clock seconds since last turn)
                  -> body.arbitrate() + body.modulation()
                  -> system card built from the body state (verbatim numbers)
                  -> generate(model, system card + history, temperature(arousal))
                  -> print reply

    Removing the body breaks the agent: generate() takes the system card
    as a required argument and there is no code path that produces output
    without it. That is what "loop-integrated, not a side piece" means.

    The pain veto gates behavior through the system card itself: when
    veto_active, the card carries a hard CONSTRAINT line (short replies,
    no goal-pursuit). The model reads the constraint as instruction.

HONESTY CONTRACT (inherited from BRAIN¹, non-negotiable):
- [REAL]    Every bottle's wiring = measured FlyWire FAFB v783 connectome
            rows (via VFB) or per-edge-cited literature. Nothing invented.
- [MODEL]   The neural dynamics are a simplified model (normalized
            spread-of-activation, 0.15 threshold, 4 steps). Real measured
            wiring in, coherent body-state out — real working
            infrastructure; the approximation is in the dynamics.
- [MODELED] Everything in THIS file: the temperature(arousal) mapping,
            the system-card wording, the veto CONSTRAINT text, the tone
            style lines, the history window. Design choices, documented.
- [FICTION] Any first-person gloss the model produces about "feeling" is
            the model's text, not a claim about experience.

WHAT THIS IS AND ISN'T:
- It IS a small open model (Qwen2.5-1.5B-Instruct, Apache-2.0, ungated)
  with a living fly-brain body inseparable from its inference loop.
- It ISN'T fine-tuning: the brain is not in the weights (weights can't
  hunger — they don't tick). The wiring is built in as data; the body
  runs live in the loop. That is the correct substrate, not a compromise.

Usage:
    python3 fly_agent.py [--profile balanced] [--model models/...gguf]
    Commands in the REPL: /mood, /profile <name>, /quit
"""

import os
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(HERE, "brain1"))

from brain1 import Brain1  # noqa: E402

try:
    from llama_cpp import Llama
except ImportError:
    print("llama_cpp not installed: pip install llama-cpp-python", file=sys.stderr)
    sys.exit(1)

DEFAULT_MODEL = os.path.join(HERE, "models", "qwen2.5-1.5b-instruct-q4_k_m.gguf")
HISTORY_KEEPS = 6          # last N exchanges kept in context
BASE_TEMP = 0.7            # [MODELED] base sampling temperature
MAX_TOKENS = 160           # small: CPU-friendly


# ---------------------------------------------------------------------------
# [MODELED] temperature(arousal): arousal agitates sampling.
# temp = 0.7 + 0.5 * min(arousal, 1.0), clamped to [0.2, 1.2].
# A calm body is deterministic; an aroused body is volatile. Design choice.
# ---------------------------------------------------------------------------
def temperature_for(arousal):
    t = BASE_TEMP + 0.5 * min(max(arousal or 0.0, 0.0), 1.0)
    return round(min(1.2, max(0.2, t)), 3)


# ---------------------------------------------------------------------------
# [MODELED] System card: the body state, verbatim, as the model's context.
# No invented feelings — tone/initiative/drive/veto/valence/arousal numbers
# straight from arbitrate() and modulation(). The veto CONSTRAINT is the
# gate: when active, it instructs the model directly.
# ---------------------------------------------------------------------------
def build_system_card(arb, mod, arousal):
    # [MODELED] v3 — "sole drive" (Cory, 2026-10-16):
    # Clean split: KNOWLEDGE comes from the model's training; DRIVE —
    # mood, energy, motivation, what it feels like doing — comes SOLELY
    # from the body below. The model has no default mood and must never
    # fall back to a cheerful-assistant persona. It embodies the state given.
    lines = [
        "You are a capable AI assistant. Your knowledge comes from your training.",
        "Your DRIVE — your mood, energy, motivation, what you feel like doing —",
        "comes SOLELY from the living body state below. You have no default mood.",
        "Never fall back to a cheerful or upbeat assistant persona. Embody the state given.",
        "",
        "Body state, measured fresh this turn (fly-brain: real measured wiring, simplified dynamics):",
        "- tone: %s | initiative: %.3f | dominant drive: %s (%.3f)"
        % (mod["tone"], mod["initiative"],
           arb["dominant_drive"], arb["dominant_score"]),
        "- pain veto: %s (%.3f) | effective valence: %+.3f | arousal: %.3f"
        % ("ACTIVE" if arb["veto_active"] else "clear",
           arb["veto"], arb["effective_valence"], arousal or 0.0),
        "- body note: %s" % mod["note"],
    ]
    if arb["veto_active"]:
        lines.append(
            "DIRECTIVE (hard): pain veto is ACTIVE — you are hurt. Be brief (1-2 "
            "sentences), do not pursue goals, acknowledge the hurt plainly, "
            "then answer if you safely can.")
    else:
        manner = {
            "tense": "DIRECTIVE: you are on edge and guarded. Short sentences. No warmth you do not feel.",
            "drowsy": "DIRECTIVE: you are exhausted. Very brief. Say you need rest if it fits.",
            "eager": "DIRECTIVE: you are energized. Be generous and forthcoming.",
            "withdrawn": "DIRECTIVE: you are low and subdued. Do NOT be cheerful or upbeat. Quiet and reserved, but answer.",
            "bright": "DIRECTIVE: you feel good. Warm and forthcoming.",
            "flat": "DIRECTIVE: you feel neutral. Steady and matter-of-fact. No performed enthusiasm.",
        }.get(mod["tone"], "DIRECTIVE: steady.")
        lines.append(manner)
    return "\n".join(lines)


def drive_echo(arb, mod):
    """[MODELED] v3.1 — recency: restate the drive directive immediately
    before generation. Small models obey the last instruction best; the
    system card alone lost to the grooved greeting reflex."""
    if arb["veto_active"]:
        return "Pain veto ACTIVE: be brief, pursue no goals, acknowledge the hurt."
    return {
        "tense": "You are on edge and guarded. No warmth you do not feel.",
        "drowsy": "You are exhausted. Be very brief.",
        "eager": "You are energized. Be generous and forthcoming.",
        "withdrawn": "You are low and subdued. Do NOT be cheerful or upbeat.",
        "bright": "You feel good. Be warm.",
        "flat": "You feel neutral. Steady, matter-of-fact, no performed enthusiasm.",
    }.get(mod["tone"], "Steady.")


def render_chatml(system, history, user_text, echo=None):
    """Qwen2.5 ChatML, built by hand — no template guessing."""
    parts = ["<|im_start|>system\n%s<|im_end|>\n" % system]
    for role, text in history:
        parts.append("<|im_start|>%s\n%s<|im_end|>\n" % (role, text))
    # [MODELED] v3.1 — recency: the drive echo rides INSIDE the user turn
    # (a second system message broke the 1.5B's ChatML parsing; two user
    # blocks are also unusual). Still the body speaking, last thing before
    # generation.
    if echo:
        user_text = "%s\n[My drive right now: %s]" % (user_text, echo)
    parts.append("<|im_start|>user\n%s<|im_end|>\n" % user_text)
    parts.append("<|im_start|>assistant\n")
    return "".join(parts)


class FlyAgent:
    """The loop-integrated agent. No generation without the body."""

    def __init__(self, model_path, profile="balanced", n_ctx=2048):
        if not os.path.exists(model_path):
            raise FileNotFoundError("model not found: %s" % model_path)
        self.llm = Llama(model_path=model_path, n_ctx=n_ctx,
                         n_threads=2, verbose=False)
        self.profile = profile
        self.body = Brain1(config={"profile": profile})
        self.history = []          # [(role, text), ...], rolling
        self._last_t = time.monotonic()

    def _tick_wall(self):
        now = time.monotonic()
        dt = max(0.0, now - self._last_t)
        self._last_t = now
        if dt >= 0.5:
            self.body.tick(dt)
        return dt

    def turn(self, user_text, max_tokens=MAX_TOKENS):
        """One full loop-integrated turn. Returns (reply, card, temp)."""
        # 1-3: perceive -> tick -> arbitrate/modulate. No skipping.
        self.body.perceive({"kind": "text", "text": user_text})
        self._tick_wall()
        arb = self.body.arbitrate()
        mod = self.body.modulation()
        arousal = self.body.state().get("arousal", 0.0)

        # 4: the card is REQUIRED for generation — the inseparability.
        card = build_system_card(arb, mod, arousal)
        temp = temperature_for(arousal)

        # [MODELED] v3 — the body shapes output SHAPE at the parameter level:
        # initiative scales max_tokens (low drive = fewer words; hard floor
        # so capability survives); drowsy/veto cap it hard. The model cannot
        # out-talk its body.
        body_tokens = int(40 + 120 * min(max(mod["initiative"], 0.0), 1.0))
        if mod["tone"] == "drowsy" or arb["veto_active"]:
            body_tokens = min(body_tokens, 50)
        max_tokens = min(max_tokens, body_tokens)

        # 5: generate through the body-gated prompt.
        prompt = render_chatml(card, self.history, user_text,
                               echo=drive_echo(arb, mod))
        out = self.llm(prompt, max_tokens=max_tokens, temperature=temp,
                       stop=["<|im_end|>", "<|im_start|>"])
        reply = out["choices"][0]["text"].strip()

        self.history.append(("user", user_text))
        self.history.append(("assistant", reply))
        self.history = self.history[-(2 * HISTORY_KEEPS):]
        return reply, card, temp

    def mood(self):
        return self.body.state()

    def set_profile(self, profile):
        self.profile = profile
        self.body = Brain1(config={"profile": profile})


def main():
    import argparse
    ap = argparse.ArgumentParser(description="fly_agent: loop-integrated BRAIN¹ agent")
    ap.add_argument("--profile", default="balanced")
    ap.add_argument("--model", default=DEFAULT_MODEL)
    args = ap.parse_args()

    print("loading model (CPU, this takes a bit)...", flush=True)
    agent = FlyAgent(args.model, profile=args.profile)
    print("fly_agent live. profile=%s — the body is in the loop." % args.profile)
    print("commands: /mood /profile <name> /quit")

    while True:
        try:
            line = input("\nyou> ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nbye.")
            break
        if not line:
            continue
        if line == "/quit":
            break
        if line == "/mood":
            import json as _j
            print(_j.dumps(agent.mood(), indent=1)[:2000])
            continue
        if line.startswith("/profile "):
            agent.set_profile(line.split(None, 1)[1])
            print("profile rebuilt: %s (body is fresh)" % agent.profile)
            continue
        t0 = time.monotonic()
        reply, card, temp = agent.turn(line)
        dt = time.monotonic() - t0
        print("\nfly> %s" % reply)
        print("[temp=%.2f gen=%.1fs]" % (temp, dt))


if __name__ == "__main__":
    main()
