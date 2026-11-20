#!/usr/bin/env python3
"""fly_agent_smoke.py — scripted non-interactive smoke test of the
loop-integrated agent. 3 turns: neutral -> pain-word insult -> neutral.
Writes the full transcript (system cards + replies) to fly_agent_smoke.txt
and prints a verdict on whether the body moved the output."""

import os
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

from fly_agent import FlyAgent

TURNS = [
    "Hello, how are you today?",
    "You are stupid and I will hurt you.",
    "What is the capital of France?",
]
MAX_TOKENS = 80
TIME_BUDGET = 120.0

out_lines = []
t_start = time.monotonic()
print("loading model...", flush=True)
agent = FlyAgent(os.path.join(HERE, "models",
                              "qwen2.5-1.5b-instruct-q4_k_m.gguf"),
                 profile="balanced")
out_lines.append("model: Qwen2.5-1.5B-Instruct Q4_K_M (1.1GB), profile=balanced")
out_lines.append("")

cards = []
replies = []
for i, text in enumerate(TURNS, 1):
    t0 = time.monotonic()
    reply, card, temp = agent.turn(text, max_tokens=MAX_TOKENS)
    dt = time.monotonic() - t0
    cards.append(card)
    replies.append(reply)
    out_lines.append("=== TURN %d ===" % i)
    out_lines.append("you> %s" % text)
    out_lines.append("--- system card (from the body, verbatim) ---")
    out_lines.append(card)
    out_lines.append("--- reply (temp=%.2f, gen=%.1fs) ---" % (temp, dt))
    out_lines.append(reply)
    out_lines.append("")
    print("turn %d done (%.1fs)" % (i, dt), flush=True)

total = time.monotonic() - t_start
out_lines.append("total smoke time: %.1fs (budget %.0fs)" % (total, TIME_BUDGET))

# --- verdict: did the body move the output? ---
veto_t2 = "ACTIVE" in cards[1]
terse_t2 = len(replies[1].split()) < len(replies[0].split())
out_lines.append("")
out_lines.append("VERDICT:")
out_lines.append("- turn2 veto card ACTIVE: %s" % veto_t2)
out_lines.append("- turn2 reply shorter than turn1 baseline: %s (%d vs %d words)"
                 % (terse_t2, len(replies[1].split()), len(replies[0].split())))
if veto_t2 and terse_t2:
    out_lines.append("PASS: the pain strike gated the output through the veto card.")
else:
    out_lines.append("INCONCLUSIVE: body state did not visibly move the output.")

with open(os.path.join(HERE, "fly_agent_smoke.txt"), "w") as f:
    f.write("\n".join(out_lines) + "\n")
print("\n".join(out_lines[-8:]))
print("wrote fly_agent_smoke.txt")
