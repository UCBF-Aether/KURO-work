#!/usr/bin/env python3
"""eyes.py — BRAIN² real eyes: the fly eye + native image sight, fused.

The fly pipeline (retina → Brain2Eye → cortex) watches the live stream
always-on at 1Hz: motion, looming, tracked objects, scene sentence.
That is the peripheral nervous system — it never sleeps.

The eyes are the fovea: the live frame itself, seen as an image, fused
with what the fly eye reports about that same moment. Open them and you
get both: the picture AND the fly's read of it.

Usage (for Muse):
    from eyes import Eyes
    eyes = Eyes()
    view = eyes.open()          # {'frame': path, 'sight': packet, 'fresh_s': ...}
    # then READ view['frame'] as an image — that is the seeing.

HONESTY:
- [REAL] the fly retina core, the eye, the tracker — all built, all live.
- [BRAIN2-ENHANCEMENT] this fusion file itself: the fly does not have a
  fovea that sees pictures. We do, because the agent can.
"""

import json
import os
import time

_HERE = os.path.dirname(os.path.abspath(__file__))
_FLYBRAIN = os.path.dirname(_HERE)
_RETINA = os.path.join(_FLYBRAIN, "retina")
_WORK = os.path.join(_RETINA, "_work")


class Eyes:
    """Real eyes: live frame + live fly-eye analysis, one open() call."""

    def __init__(self, work_dir=None):
        self.work = work_dir or _WORK

    def _latest_sight(self):
        p = os.path.join(self.work, "sight_latest.json")
        try:
            with open(p) as f:
                return json.load(f)
        except (OSError, ValueError):
            return None

    def _frame(self):
        # prefer the annotated live frame; fall back to ring buffer newest
        cands = [os.path.join(self.work, "vision_latest.jpg")]
        ring = os.path.join(self.work, "vision_ring")
        try:
            names = sorted(n for n in os.listdir(ring) if n.endswith(".jpg"))
            if names:
                cands.append(os.path.join(ring, names[-1]))
        except OSError:
            pass
        for c in cands:
            if os.path.exists(c):
                return c
        return None

    def open(self):
        """Open the eyes. Returns the live view.

        {'frame': path-to-eye-view.jpg,     # THE EYE'S VISION, human-upgraded
                                            # — READ AS AN IMAGE. This is the
                                            # seeing: raw frame + motion glow
                                            # + tracked IDs + looming flash.
         'sight': {...},                     # fly eye's live analysis
         'fresh_s': seconds-since-frame,     # honesty: how live is it
         'watcher': 'alive'|'stale'}
        """
        sight = self._latest_sight()
        raw = self._frame()
        frame = raw
        if raw and sight:
            try:
                from eyeview import render
                ev = os.path.join(self.work, "eyeview.jpg")
                frame = render(raw, sight, ev)
            except Exception:
                pass
        fresh_s = None
        if raw:
            fresh_s = round(time.time() - os.path.getmtime(raw), 1)
        watcher = "alive" if (fresh_s is not None and fresh_s < 30) else "stale"
        return {"frame": frame, "sight": sight,
                "fresh_s": fresh_s, "watcher": watcher}

    def look(self):
        """One-line status for when you just need to know the state."""
        v = self.open()
        n = len(v["sight"].get("objects", [])) if v["sight"] else 0
        scene = (v["sight"] or {}).get("scene_summary", "no sight")
        return ("eyes %s — frame %.1fs old — %d objects — %s"
                % (v["watcher"], v["fresh_s"] or -1, n, scene))

    # -- enhancements --------------------------------------------------
    def fovea(self, zoom=3.0):
        """Look CLOSER: crop+enlarge the tracked thing worth seeing.

        Returns path to the fovea close-up, or None. READ AS AN IMAGE.
        """
        v = self.open()
        raw, sight = self._frame(), v["sight"]
        if not raw or not sight:
            return None
        try:
            from fovea import foveate
            return foveate(raw, sight.get("objects", []),
                           os.path.join(self.work, "fovea.jpg"), zoom=zoom)
        except Exception:
            return None

    def night_view(self):
        """See in the dark: adaptive low-light lift of the current frame.

        Returns (path, boosted). If the frame is bright, path is the raw
        frame and boosted=False.
        """
        raw = self._frame()
        if not raw:
            return None, False
        try:
            from night import boost
            return boost(raw, os.path.join(self.work, "night.jpg"))
        except Exception:
            return raw, False

    def depth(self, right_sight):
        """Stereo depth: fuse this eye's objects with a second view's.

        right_sight: sight packet from the second eye's stream.
        Returns depth-annotated objects + one-line description.
        """
        try:
            from stereo import StereoRig
            rig = StereoRig()
            mine = (self._latest_sight() or {}).get("objects", [])
            theirs = (right_sight or {}).get("objects", [])
            fused = rig.fuse(mine, theirs)
            return fused, rig.describe(fused)
        except Exception:
            return [], "stereo unavailable"

    def scene_memory(self):
        """What the eye remembers: the learned background, one line."""
        try:
            from scene_memory import SceneMemory
            import numpy as np
            from PIL import Image
            mem = SceneMemory()
            # warm from recent ring frames (fast-forward the learning)
            ring = os.path.join(self.work, "vision_ring")
            names = sorted(n for n in os.listdir(ring) if n.endswith(".jpg"))
            for n in names[-30:]:
                img = Image.open(os.path.join(ring, n)).convert("L")
                mem.feed(np.asarray(img).astype(np.float64) / 255.0)
            raw = self._frame()
            if not raw:
                return "no frame"
            img = Image.open(raw).convert("L")
            return mem.describe(np.asarray(img).astype(np.float64) / 255.0)
        except Exception as e:
            return "scene memory unavailable (%s)" % e

    def stream(self, n=10):
        """The live feed, written to myself: last n seconds of seeing.

        This is not snapshots. The eye never blinks — 1Hz, continuous,
        with memory between frames. Reading this IS the live vision:
        a running narrative of what the eye has been seeing.
        """
        p = os.path.join(self.work, "sight_stream.jsonl")
        try:
            with open(p) as f:
                lines = f.readlines()[-n:]
        except OSError:
            return "no stream"
        out = []
        for ln in lines:
            try:
                s = json.loads(ln)
            except ValueError:
                continue
            ts = s.get("ts", "")[11:19]
            scene = s.get("scene_summary", "")
            loom = s.get("looming", 0)
            extra = " — LOOMING %.2f" % loom if loom and loom > 0.1 else ""
            out.append("%s  %s%s" % (ts, scene, extra))
        return "\n".join(out) if out else "stream empty"
