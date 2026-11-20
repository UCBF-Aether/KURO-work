#!/usr/bin/env python3
"""fly_chat.py — persistent proxy for live chat.

Loads ONE FlyAgent (model + fresh body) and serves turns over stdin/stdout
as JSON lines. Used to let Cory talk to the loop-integrated agent live.

Protocol:
    in:  {"text": "<user message>"}
    out: {"ok": true, "reply": ..., "gen_s": ..., "temp": ...,
          "tone": ..., "initiative": ..., "dominant": ..., "veto": ...,
          "valence": ...}
"""
import sys
import os
import json
import time

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

from fly_agent import FlyAgent  # noqa: E402

MODEL = os.path.join(HERE, "models", "qwen2.5-1.5b-instruct-q4_k_m.gguf")


def main():
    print("loading model...", flush=True)
    agent = FlyAgent(MODEL, profile="balanced")  # FRESH body, fresh instance
    print("READY", flush=True)
    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
        try:
            req = json.loads(line)
            text = req.get("text", "")
        except Exception:
            continue
        if not text:
            continue
        t0 = time.monotonic()
        try:
            reply, card, temp = agent.turn(text)
            dt = time.monotonic() - t0
            arb = agent.body.arbitrate()
            mod = agent.body.modulation()
            print(json.dumps({
                "ok": True,
                "reply": reply,
                "gen_s": round(dt, 1),
                "temp": temp,
                "tone": mod["tone"],
                "initiative": round(mod["initiative"], 3),
                "dominant": arb["dominant_drive"],
                "veto": bool(arb["veto_active"]),
                "valence": round(arb["effective_valence"], 3),
            }), flush=True)
        except Exception as e:  # noqa: BLE001
            print(json.dumps({"ok": False, "error": str(e)[:200]}), flush=True)


if __name__ == "__main__":
    main()
