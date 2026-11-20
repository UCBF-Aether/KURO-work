#!/usr/bin/env python3
"""cortex.py — the BRAIN² visual cortex: the eye learns to SEE, not just sense.

The hi-res eye (brain2/eye.py) outputs energy fields ("glow"): motion,
color, redness per cell, plus per-packet figure-ground blobs. This module
turns those fields into a live visual scene: PERSISTENT OBJECTS with stable
IDs, velocities, and color signatures, plus a human-legible scene summary.
This is what Muse READS as live sight.

HONESTY CONTRACT:
- [REAL]    The segmentation rides the sealed fly machinery: figure-ground
            comes from the motion field (fly small-field figure detection —
            the fly DOES segment figures from ground on motion) plus color
            contrast. Nothing here claims to be fly biology beyond that.
- [BRAIN2-ENHANCEMENT] Stable object identity across time, velocity
            vectors, color signatures, and the scene summary are AGENT
            inventions. The fly does not do object identity — it has no
            persistent "that thing again." We do, because an agent needs
            to watch a thing move. Labeled as enhancement everywhere.
- [MODELED] Nearest-neighbor association, EMA velocity, confirmation
            gating. Simple, deterministic, no learning.
"""

import math
import time
from datetime import datetime, timezone


def _iso_now():
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


class Tracker:
    """[BRAIN2-ENHANCEMENT] persistent multi-object tracking on figure-ground blobs.

    Association is greedy nearest-neighbor on blob centroids (energy order),
    gated by centroid distance and bbox size similarity. New detections must
    persist for CONFIRM_FRAMES consecutive updates before earning a stable
    ID — single-frame transients (onset flashes, noise pops) never become
    objects. Objects unseen for longer than drop_after_s are dropped.
    Velocities are EMA-smoothed frame-fractions per second.
    """

    CONFIRM_FRAMES = 2     # consecutive detections before an ID is issued
    PENDING_TTL = 3        # unconfirmed candidates expire after N updates
    MATCH_DIST = 0.18      # max centroid distance (0..1 frame fractions)
    SIZE_TOL = 0.30        # max |dw| / |dh| (0..1 frame fractions)
    VEL_ALPHA = 0.6        # EMA smoothing for vx/vy
    MAX_OBJECTS = 12

    def __init__(self, drop_after_s=5.0, match_dist=None, max_objects=None):
        self.drop_after_s = float(drop_after_s)
        self.STILL_VEL = 0.05   # below this speed (norm/s) a track is "still"
        self.STILL_MAX = 100    # still this many frames -> background, drop it
        self.match_dist = match_dist or self.MATCH_DIST
        self.max_objects = max_objects or self.MAX_OBJECTS
        self._next_id = 1
        self._objs = {}     # id -> internal object state
        self._pending = []  # unconfirmed detections [{x,y,w,h,seen,ttl}]

    # -- internal ------------------------------------------------------
    @staticmethod
    def _dist(ax, ay, bx, by):
        return math.hypot(ax - bx, ay - by)

    def _size_ok(self, b, o):
        return (abs(b["w"] - o["w"]) < self.SIZE_TOL
                and abs(b["h"] - o["h"]) < self.SIZE_TOL)

    @staticmethod
    def _pub(o):
        """Public object dict (no internal bookkeeping)."""
        return {"id": o["id"],
                "x": round(o["x"], 3), "y": round(o["y"], 3),
                "w": round(o["w"], 3), "h": round(o["h"], 3),
                "vx": round(o["vx"], 3), "vy": round(o["vy"], 3),
                "energy": round(o["energy"], 3),
                "redness": round(o["redness"], 3),
                "color_sig": [round(float(c), 2) for c in o["color_sig"]],
                "age_frames": o["age_frames"],
                "last_seen": o["last_seen"]}

    # -- public --------------------------------------------------------
    def update(self, blobs, dt=1.0):
        """Associate one frame's blobs; return the live object list.

        blobs: [{x,y,w,h,energy,redness,color_sig}] in 0..1 frame fractions
               (as produced by brain2.eye._blobs).
        dt: seconds since the previous update (velocity denominator).
        Returns: [public object dicts], sorted by energy, cap MAX_OBJECTS.
        """
        now_iso = _iso_now()
        now_t = time.time()
        dt = max(float(dt), 1e-3)

        # 1. match blobs -> existing objects (greedy, blobs arrive energy-sorted)
        remaining = list(blobs)
        matched = set()
        for b in list(remaining):
            best, best_d = None, None
            for oid, o in self._objs.items():
                if oid in matched:
                    continue
                d = self._dist(b["x"], b["y"], o["x"], o["y"])
                if d < self.match_dist and self._size_ok(b, o):
                    if best_d is None or d < best_d:
                        best, best_d = oid, d
            if best is None:
                continue
            o = self._objs[best]
            ivx = (b["x"] - o["x"]) / dt
            ivy = (b["y"] - o["y"]) / dt
            a = self.VEL_ALPHA
            o["vx"] += a * (ivx - o["vx"])
            o["vy"] += a * (ivy - o["vy"])
            # stillness: a track that barely moves is background, not an object
            import math as _math
            if _math.hypot(o["vx"], o["vy"]) < self.STILL_VEL:
                o["still_frames"] = o.get("still_frames", 0) + 1
            else:
                o["still_frames"] = 0
            o.update({"x": b["x"], "y": b["y"], "w": b["w"], "h": b["h"],
                      "energy": b["energy"], "redness": b["redness"],
                      "color_sig": list(b.get("color_sig", [0, 0, 0])),
                      "age_frames": o["age_frames"] + 1,
                      "last_seen": now_iso, "_last_t": now_t})
            matched.add(best)
            remaining.remove(b)

        # 2. match leftovers -> pending candidates (confirmation gating)
        fresh_pending = []
        for b in list(remaining):
            hit = None
            for p in self._pending:
                if self._dist(b["x"], b["y"], p["x"], p["y"]) < self.match_dist:
                    hit = p
                    break
            if hit is None:
                fresh_pending.append({"x": b["x"], "y": b["y"],
                                      "w": b["w"], "h": b["h"],
                                      "seen": 1, "ttl": self.PENDING_TTL,
                                      "b": b})
                remaining.remove(b)
                continue
            hit["seen"] += 1
            hit.update({"x": b["x"], "y": b["y"], "w": b["w"],
                        "h": b["h"], "b": b})
            if (hit["seen"] >= self.CONFIRM_FRAMES
                    and len(self._objs) < self.max_objects):
                oid = self._next_id
                self._next_id += 1
                bb = hit["b"]
                self._objs[oid] = {
                    "id": oid, "x": bb["x"], "y": bb["y"],
                    "w": bb["w"], "h": bb["h"],
                    "vx": 0.0, "vy": 0.0,
                    "energy": bb["energy"], "redness": bb["redness"],
                    "color_sig": list(bb.get("color_sig", [0, 0, 0])),
                    "age_frames": 1, "last_seen": now_iso,
                    "still_frames": 0,
                    "_last_t": now_t}
                self._pending.remove(hit)
            remaining.remove(b)
        for p in self._pending:
            p["ttl"] -= 1
        self._pending = ([p for p in self._pending if p["ttl"] > 0]
                         + fresh_pending)

        # 3. drop objects unseen too long (wall clock — the honesty anchor),
        # or still too long (background latch, e.g. a swaying tree)
        for oid in list(self._objs):
            o = self._objs[oid]
            if now_t - o["_last_t"] > self.drop_after_s:
                del self._objs[oid]
            elif o.get("still_frames", 0) > self.STILL_MAX:
                del self._objs[oid]

        objs = [self._pub(o) for o in self._objs.values()]
        objs.sort(key=lambda o: o["energy"], reverse=True)
        return objs[:self.max_objects]

    def reset(self):
        self._objs.clear()
        self._pending.clear()
        self._next_id = 1


def scene_summary(objects):
    """[BRAIN2-ENHANCEMENT] one-line human-legible scene description.

    This is the sentence Muse reads as live sight. Per-object phrases so
    it stays truthful when objects differ: e.g.
    "3 tracked objects: #1 moving left-to-right mid-frame; #2 static upper;
     #4 moving downward lower".
    """
    if not objects:
        return "no tracked objects"
    parts = []
    for o in objects:
        sp = math.hypot(o["vx"], o["vy"])
        if sp < 0.02:
            mot = "static"
        elif abs(o["vx"]) >= abs(o["vy"]):
            mot = ("moving left-to-right" if o["vx"] > 0
                   else "moving right-to-left")
        else:
            mot = "moving downward" if o["vy"] > 0 else "moving upward"
        y = o["y"]
        zone = "upper" if y < 0.33 else ("mid-frame" if y < 0.66 else "lower")
        parts.append("#%d %s %s" % (o["id"], mot, zone))
    n = len(objects)
    return "%d tracked object%s: %s" % (n, "" if n == 1 else "s",
                                        "; ".join(parts))
