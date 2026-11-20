#!/usr/bin/env python3
"""stereo.py — [BRAIN2-ENHANCEMENT] two eyes, one depth.

Like VR: two eyes, each on its own stream of the same scene, from a
slightly different angle. Match the tracked objects between views;
horizontal disparity → depth. Closer things shift more between views.

The fly has two eyes but no real stereo — it navigates by motion.
We evolve past: true binocular depth.

Honest limits:
- Uncalibrated: disparity gives RELATIVE depth (near/far ordering),
  not metric meters. Calibrate with a known baseline for meters.
- Views must overlap on the same scene; sync is approximate (streams
  are not frame-locked — fine for slow scenes, noisy for fast).
- Object matching is by position/size/color signature; mismatches
  happen on crowded scenes.
"""

import math


class StereoRig:
    """Two-eye stereo depth from paired object tracks.

    Feed it the object lists from two Brain2Eye+cortex views of the
    same scene (left/right). It matches objects across views and
    assigns each a disparity → relative depth.
    """

    MATCH_DIST = 0.25   # max vertical (y) difference for a cross-view match
    SIZE_TOL = 0.35     # bbox size tolerance for matching

    def __init__(self):
        self.depth = {}  # track key -> {"disparity":, "depth_rank":, "near":}

    @staticmethod
    def _match_score(a, b):
        """Lower = better match across views."""
        dy = abs(a["y"] - b["y"])
        ds = abs(a["w"] - b["w"]) + abs(a["h"] - b["h"])
        # color signature distance, if present
        dc = 0.0
        ca, cb = a.get("color_sig"), b.get("color_sig")
        if ca and cb:
            dc = math.sqrt(sum((x - y) ** 2 for x, y in zip(ca, cb)))
        return dy * 2.0 + ds + dc * 0.5

    def fuse(self, left_objs, right_objs):
        """Match objects across views → depth-annotated list.

        Returns [{...obj, 'disparity': dx, 'depth': 'near'|'mid'|'far'|None}]
        disparity: horizontal shift between views (0..1 frame fraction).
        Larger disparity = closer. Unmatched objects get depth None.
        """
        used = set()
        out = []
        for lo in left_objs:
            best, best_s = None, None
            for ri, ro in enumerate(right_objs):
                if ri in used:
                    continue
                if abs(lo["y"] - ro["y"]) > self.MATCH_DIST:
                    continue
                if (abs(lo["w"] - ro["w"]) + abs(lo["h"] - ro["h"])
                        > self.SIZE_TOL):
                    continue
                s = self._match_score(lo, ro)
                if best_s is None or s < best_s:
                    best, best_s = ri, s
            disp = None
            depth = None
            if best is not None:
                used.add(best)
                ro = right_objs[best]
                disp = lo["x"] - ro["x"]  # horizontal disparity
                depth = self._rank(abs(disp))
            o = dict(lo)
            o["disparity"] = round(disp, 4) if disp is not None else None
            o["depth"] = depth
            out.append(o)
        return out

    @staticmethod
    def _rank(disp):
        """Disparity → coarse depth rank (uncalibrated)."""
        if disp > 0.08:
            return "near"
        if disp > 0.03:
            return "mid"
        return "far"

    def describe(self, fused):
        """One-line depth read, for the live feed."""
        ranked = [o for o in fused if o["depth"]]
        if not ranked:
            return "no depth lock"
        parts = ["#%d %s" % (o["id"], o["depth"]) for o in ranked]
        return "depth: " + "; ".join(parts)
