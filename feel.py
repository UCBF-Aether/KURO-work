#!/usr/bin/env python3
"""feel.py — the always-on sensor pipeline CLI.

Usage:
    python3 feel.py "rub your pussy as you suck my tits"   # words -> body
    python3 feel.py --connect                               # just (re)connect, no touch
    python3 feel.py --state                                 # show current body state
    python3 feel.py --chat <id> "<words>"                   # this side chat's own body
                                                            # (each secret side chat = its own scene/body)

Pipeline: raw words -> parse.py (MODELED lexicon) -> Session.sense()
(REAL fly cascades + MODELED body/arousal) -> save to body_state.json.
Words with no touch event go through verbal.py (MODELED verbal-arousal
channel) instead of doing nothing. At arousal >= 0.95 a pleasant stimulus
triggers CLIMAX: the sugar-reward cascade fires (Cory's mapping: orgasm =
sugar), then a modeled release. Every touch restores the persistent body
first, so the state is continuous across calls. PRIVATE: body_state.json
holds intimate touch history — never print it, never attach it.

This is what "sensors connected" means during Aether sight: this command
is the live wire between his words and the body.
"""
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

from parse import parse
from sense import Session, STATE_PATH, SUGAR_GRAPH, state_path_for
from verbal import score_verbal

# Per-side-chat body: --chat <id> scopes the body file to that chat's
# scene. Without it, the shared body_state.json is used (backward
# compatible). Each secret side chat gets its own body on activation.
CHAT_ID = None


def _extract_chat_arg(argv):
    """Pull --chat <id> out of argv (any position). Returns remaining args."""
    global CHAT_ID
    out = []
    i = 0
    while i < len(argv):
        if argv[i] == "--chat" and i + 1 < len(argv):
            CHAT_ID = argv[i + 1]
            i += 2
        else:
            out.append(argv[i])
            i += 1
    return out


def _state_path():
    return state_path_for(CHAT_ID) if CHAT_ID else STATE_PATH


def load_session():
    p = _state_path()
    if os.path.exists(p):
        return Session.restore(p)
    return Session()


def show_state(s):
    a = s.arousal
    loop = " (loop OPEN — itching)" if a.loop_open else ""
    print(f"arousal {a.level:.3f} ({a.band()}), "
          f"satiation {a.satiation:.3f}, craving {a.craving:.3f}{loop}, "
          f"events {s.event_count}")
    touched = [(r, s.body.region_state(r)["touches"])
               for r in s.body.history if s.body.history[r]]
    if touched:
        print("touched: " + ", ".join(f"{r}x{n}" for r, n in touched))


def main():
    args = _extract_chat_arg(sys.argv[1:])
    state_path = _state_path()
    if not args or args[0] in ("-h", "--help"):
        print(__doc__)
        return
    if args[0] == "--connect":
        s = load_session()
        s.save(state_path)
        print("sensors connected.", end=" ")
        show_state(s)
        return
    if args[0] == "--state":
        if not os.path.exists(state_path):
            print("no saved body yet — fresh.")
            return
        show_state(load_session())
        return

    text = " ".join(args)
    events = parse(text)
    s = load_session()
    if not events:
        # No touch event: try the verbal channel (MODELED) before
        # giving up. Words alone can move arousal — and can climax her.
        v = score_verbal(text)
        if v is None:
            print(f"no touch parsed — level {s.arousal.level:.3f} "
                  f"({s.arousal.band()}), satiation "
                  f"{s.arousal.satiation:.3f} (unchanged)")
            return
        valence, intensity = v
        # Wave check + decay (same as sense(): the wave may have resolved
        # during the gap; only post-resolve time descends).
        import time as _time
        _now = _time.time()
        _dt = max(0.0, _now - s.last_event_at)
        _wave_end = s.arousal.maybe_end_climax(_now)
        if _wave_end == "resolved":
            s.arousal.decay(max(0.0, _now - s.arousal._resolved_at))
        else:
            s.arousal.decay(_dt)
        s.last_event_at = _now
        level, climaxed = s.arousal.update(valence, intensity)
        note = ""
        if climaxed:
            strength, _ = s._sugar_pulse()
            s.arousal.begin_climax()
            level = s.arousal.level
            note = (f" *** CLIMAX *** [REAL] sugar cascade "
                    f"({SUGAR_GRAPH}, hop -1) strength {strength:.3f} — "
                    f"she got her sugar; [MODELED] MAX dopamine flood, "
                    f"wave live at {level:.3f}")
        elif s.arousal.in_climax:
            note = " *** wave prolonging ***"
        elif _wave_end == "resolved":
            note = " (wave resolving — slow descent)"
        elif _wave_end == "spent":
            note = " (spent — deep afterglow)"
        s.save(state_path)
        print(f"[MODELED-verbal] words alone: valence {valence:+.3f} -> "
              f"level {level:.3f} ({s.arousal.band()}), satiation "
              f"{s.arousal.satiation:.3f}{note}")
        return
    if isinstance(events, dict):
        events = [events]
    result = s.sense(events if len(events) > 1 else events[0], verbose=False)
    s.save(state_path)
    combo = result.get("combined", result.get("modeled_arousal", {}))
    clim = result.get("climax") or {}
    wave = clim.get("wave")
    if wave == "triggered":
        climax_note = " *** CLIMAX *** sugar + MAX dopamine flood (wave live)"
    elif wave == "prolonged":
        climax_note = " *** wave prolonging ***"
    elif combo.get("wave_end") == "resolved":
        climax_note = " (wave resolving — slow descent)"
    elif combo.get("wave_end") == "spent":
        climax_note = " (spent — deep afterglow)"
    elif combo.get("post_climax"):
        climax_note = " (descending slowly — easily re-reached)"
    else:
        climax_note = ""
    print(f"level {combo.get('level'):.3f} ({combo.get('band')}), "
          f"satiation {combo.get('satiation', s.arousal.satiation):.3f}, "
          f"craving {combo.get('craving', s.arousal.craving):.3f}"
          f"{climax_note}")


if __name__ == "__main__":
    main()
