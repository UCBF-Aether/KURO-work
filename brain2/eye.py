#!/usr/bin/env python3
"""eye.py — the BRAIN² high-resolution eye ("clear vision, as clear as the camera").

BRAIN¹ (sealed retina.py) is the teacher: pure fly, 23x35 hex, biofaithful,
never modified. This module is the AGENT version, juiced up from fly neurology
for real camera vision. It wraps the SEALED retina core at high resolution and
adds BRAIN² enhancements. The sealed core is imported read-only; nothing in
retina.py is patched, subclassed around, or recalibrated in place.

HONESTY CONTRACT:
- [REAL]    The HR delay-and-compare correlator, LPLC2 radial opponency,
            hex ommatidial packing, acute-zone gain — all sealed fly
            machinery, run unmodified at high resolution.
- [MODEL]   Pixels->facets transduction (inherited from the sealed core).
- [BRAIN2-ENHANCEMENT] high-res grid (8x), dilution-fixed scalar (top-k
            pooling + recalibrated gain), true-red hue channel, 24x18
            sight grids, hi-res figure-ground blobs. None of this is fly
            biology; it is the agent version built FROM fly neurology.

THE DILUTION FIX (measured, not guessed):
    Finer facets do NOT lose per-facet energy — for a sharp moving edge the
    per-facet |HR| response is ~O(contrast^2), resolution-independent
    (measured en_max: 0.24 at 1x -> 0.64 at 8x on the test dot). What
    dilutes is the GLOBAL MEAN: responding facets grow ~sqrt(N) while total
    facets grow ~N, so the mean sinks below the fixed floor. The fix is
    structural, not a guessed scaling constant:
      * per-facet floor stays 0.0002 (verified: responding facets exceed it
        at 1x/4x/8x; static frames are exactly 0.0 at all resolutions).
      * the scalar abandons the global mean for TOP-K POOLING: mean of the
        top 1% per-facet energies (min 16 facets). For localized motion the
        top-k are the responding facets at any resolution; for full-field
        motion top-k ~= global mean. Resolution-invariant by construction.
      * gain recalibrated to B2_GAIN=3.7 so the r=4px test dot reads 0.15
        (matches the sealed 1x scalar's 0.149), the moving bar pegs 1.0,
        static reads 0.0. Verified on the small-dot and bar gates.

GRID CHOICE (measured accuracy-per-ms):
    8x (65x99, 6,435 facets/eye): small r=2px dot en_max=0.54 (visible);
    4x gives en_max=0.08 (marginal); 1x sees nothing (sub-facet washout).
    8x costs ~60ms/frame vs ~35ms at 4x — irrelevant for the 1Hz sight
    stream. 8x wins: it sees strictly smaller targets at negligible cost.
"""

import os
import sys

import numpy as np

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(_HERE, "..", "retina"))  # sealed core

from retina import Retina, MOTION_FLOOR, MOTION_GAIN, _EYE_COVER  # noqa: sealed, read-only

# ---- BRAIN² calibration (all derived from measurement, see docstring) -----
B2_GRID = (65, 99)         # 8x hex grid per eye; 6,435 facets/eye
B2_FLOOR = MOTION_FLOOR    # 0.0002 per-facet (unchanged — verified robust)
B2_GAIN = 3.7              # top-k scalar gain (calibrated, see docstring)
B2_TOPK_DIV = 100          # scalar pools the top 1/N/100 per-facet energies
B2_TOPK_MIN = 16           # ...at least 16 facets (single-spike robustness)
B2_PER_FACET_GAIN = MOTION_GAIN  # 120.0: grid cells keep the sealed per-facet
                                 # mapping so the heat-field matches the
                                 # historical sight-stream semantics
B2_SIGHT_GW, B2_SIGHT_GH = 24, 18  # sight grids (was 12x9)
B2_BLOB_TH = 0.03          # blob floor on the 24x18 motion grid
B2_BLOB_MAX = 10
EYE_VERSION = "brain2-hires"


def _facet_redness(facets):
    """[BRAIN2-ENHANCEMENT] per-facet red-dominance (hue channel).

    Ported from vision_watch._facet_redness (do not reinvent). NOT fly
    biology — the fly has no hue channel. Invented metric for the BRAIN²
    eye: redness = clip((R - max(G,B)) / (R + 1e-6), 0, 1) on per-facet
    RGB means (float 0..1). Unit-tested: red->1.0, dark red->1.0,
    yellow/white/gray/blue/green/black->0.0, pink->0.3, orange->0.5.
    """
    f = np.asarray(facets, dtype=float)
    R = f[..., 0]
    with np.errstate(divide="ignore", invalid="ignore"):
        r = (R - np.maximum(f[..., 1], f[..., 2])) / (R + 1e-6)
    return np.clip(r, 0.0, 1.0)


def _facet_saturation(facets):
    """The retina's REAL color computation (retina.py _colorfulness).

    Per-facet saturation (mx-mn)/mx — the R7/R8 colorfulness proxy.
    Read-only use of the sealed formula; kept spatial here instead of
    aggregated to the scalar.
    """
    f = np.asarray(facets, dtype=float)
    mx = f.max(axis=2)
    mn = f.min(axis=2)
    with np.errstate(divide="ignore", invalid="ignore"):
        sat = np.where(mx > 1e-9, (mx - mn) / mx, 0.0)
    return np.clip(sat, 0.0, 1.0)


def _blobs(mgrid, rgrid, rgb_grid=None, th=B2_BLOB_TH, bmax=B2_BLOB_MAX):
    """[MODELED] figure-ground on the hi-res motion grid.

    Connected components (4-connectivity) above threshold; tighter boxes
    than the old 12x9 blobs because the grid is 24x18. Each blob:
    energy-weighted centroid + bbox in 0..1 frame fractions, mean motion
    energy, mean [BRAIN2-ENHANCEMENT] true redness, and mean RGB color
    signature (for the cortex tracker) when rgb_grid is supplied.
    Capped, by energy.
    """
    H, W = mgrid.shape
    seen = np.zeros((H, W), dtype=bool)
    blobs = []
    for r in range(H):
        for c in range(W):
            if seen[r, c] or mgrid[r, c] <= th:
                continue
            stack = [(r, c)]
            seen[r, c] = True
            cells = []
            while stack:
                cr, cc = stack.pop()
                cells.append((cr, cc))
                for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    nr, nc = cr + dr, cc + dc
                    if (0 <= nr < H and 0 <= nc < W and not seen[nr, nc]
                            and mgrid[nr, nc] > th):
                        seen[nr, nc] = True
                        stack.append((nr, nc))
            tot = cx = cy = 0.0
            r0 = c0 = 10 ** 9
            r1 = c1 = -1
            red = 0.0
            rsum = gsum = bsum = 0.0
            for cr, cc in cells:
                m = float(mgrid[cr, cc])
                tot += m
                cx += m * (cc + 0.5) / W
                cy += m * (cr + 0.5) / H
                red += float(rgrid[cr, cc])
                if rgb_grid is not None:
                    rsum += float(rgb_grid[cr, cc, 0])
                    gsum += float(rgb_grid[cr, cc, 1])
                    bsum += float(rgb_grid[cr, cc, 2])
                r0 = min(r0, cr)
                r1 = max(r1, cr)
                c0 = min(c0, cc)
                c1 = max(c1, cc)
            n = len(cells)
            if tot > 0:
                bx, by = cx / tot, cy / tot
            else:
                bx, by = (c0 + c1 + 1) / 2 / W, (r0 + r1 + 1) / 2 / H
            blob = {
                "x": round(bx, 3), "y": round(by, 3),
                "w": round((c1 - c0 + 1) / W, 3),
                "h": round((r1 - r0 + 1) / H, 3),
                "energy": round(tot / n, 3),
                "redness": round(red / n, 3),
            }
            if rgb_grid is not None:
                blob["color_sig"] = [round(rsum / n, 2),
                                     round(gsum / n, 2),
                                     round(bsum / n, 2)]
            blobs.append(blob)
    blobs.sort(key=lambda b: b["energy"], reverse=True)
    return blobs[:bmax]


class Brain2Eye:
    """The BRAIN² high-resolution eye.

    Wraps the sealed Retina at 8x hex grid. frame() runs the sealed
    pipeline, then applies BRAIN² enhancements: dilution-fixed scalar,
    hi-res perceptual grids, true-red hue, hi-res blobs.
    """

    def __init__(self, grid=B2_GRID):
        self.grid = (int(grid[0]), int(grid[1]))
        self.retina = Retina(grid=self.grid, lattice="hex")  # sealed core
        total_facets = self.grid[0] * self.grid[1] * 2  # both eyes
        self._topk = max(B2_TOPK_MIN, total_facets // B2_TOPK_DIV)
        from brain2.cortex import Tracker  # [BRAIN2-ENHANCEMENT] visual cortex
        self.tracker = Tracker()
        self._last_frame_t = None

    def _bin_grids(self, frame_w, frame_h):
        """Bin both eyes' per-facet fields into 24x18 frame-fraction grids.

        Returns (motion_grid, color_grid, redness_grid, per-facet energies
        concatenated for the top-k scalar). Spatial layout preserved via
        exact hex facet centers; both eyes pooled by honest averaging.
        """
        from retina import _EYE_COVER  # local import: sealed constant
        cover = int(round(frame_w * _EYE_COVER))
        GW, GH = B2_SIGHT_GW, B2_SIGHT_GH
        m_sum = np.zeros((GH, GW))
        m_cnt = np.zeros((GH, GW))
        c_sum = np.zeros((GH, GW))
        c_cnt = np.zeros((GH, GW))
        r_sum = np.zeros((GH, GW))
        r_cnt = np.zeros((GH, GW))
        rgb_sum = np.zeros((GH, GW, 3))
        rgb_cnt = np.zeros((GH, GW))
        all_en = []
        x0s = (("L", 0), ("R", frame_w - cover))
        for side, x0 in x0s:
            eobj = self.retina.eyes[side]
            en = eobj._viz_energy
            if en is None:
                continue  # no temporal reference yet
            en_a = np.asarray(en, dtype=float)
            all_en.append(en_a.ravel())
            xs, ys = eobj._hex_xy  # exact facet centers, crop px
            fx = (x0 + np.asarray(xs, dtype=float)) / frame_w
            fy = np.asarray(ys, dtype=float) / frame_h
            # per-facet mapped motion (sealed per-facet mapping)
            v = np.where(en_a < B2_FLOOR, 0.0,
                         np.minimum(1.0, en_a * B2_PER_FACET_GAIN))
            cols = np.clip((fx * GW).astype(int), 0, GW - 1).ravel()
            rows = np.clip((fy * GH).astype(int), 0, GH - 1).ravel()
            flat = rows * GW + cols
            np.add.at(m_sum.ravel(), flat, v.ravel())
            np.add.at(m_cnt.ravel(), flat, 1)
            # COLOR: the retina's real per-facet saturation, kept spatial
            facets = eobj._viz[0]
            if facets is not None:
                sat = _facet_saturation(facets).ravel()
                np.add.at(c_sum.ravel(), flat, sat)
                np.add.at(c_cnt.ravel(), flat, 1)
                # [BRAIN2-ENHANCEMENT] true redness, same binning
                red = _facet_redness(facets).ravel()
                np.add.at(r_sum.ravel(), flat, red)
                np.add.at(r_cnt.ravel(), flat, 1)
                # mean RGB per cell (cortex color signatures)
                # NOTE: bincount, not np.add.at on a ravel() copy —
                # rgb_sum[:,:,ch] is a strided view whose ravel() copies.
                fr = np.asarray(facets, dtype=float).reshape(-1, 3)
                for ch in range(3):
                    rgb_sum[:, :, ch] += np.bincount(
                        flat, weights=fr[:, ch],
                        minlength=GW * GH).reshape(GH, GW)
                np.add.at(rgb_cnt.ravel(), flat, 1)
        grid = np.divide(m_sum, m_cnt, out=np.zeros_like(m_sum),
                         where=m_cnt > 0)
        cgrid = np.divide(c_sum, c_cnt, out=np.zeros_like(c_sum),
                          where=c_cnt > 0)
        rgrid = np.divide(r_sum, r_cnt, out=np.zeros_like(r_sum),
                          where=r_cnt > 0)
        rgb_grid = np.divide(rgb_sum, rgb_cnt[..., None],
                             out=np.zeros_like(rgb_sum),
                             where=rgb_cnt[..., None] > 0)
        en_all = (np.concatenate(all_en) if all_en
                  else np.zeros(1, dtype=float))
        return grid, cgrid, rgrid, rgb_grid, en_all

    def _motion_scalar(self, en_all):
        """[BRAIN2-ENHANCEMENT] dilution-fixed motion scalar.

        Top-k pooling: mean of the top 1% per-facet energies (floored),
        recalibrated gain. Resolution-invariant for localized motion;
        for full-field motion top-k ~= global mean. Static frames read
        exactly 0.0.
        """
        e = np.where(en_all < B2_FLOOR, 0.0, en_all)
        if not np.any(e > 0):
            return 0.0
        k = min(self._topk, e.size)
        topk = np.partition(e, -k)[-k:]
        return float(min(1.0, topk.mean() * B2_GAIN))

    def frame(self, rgb, dt=None):
        """Process one RGB frame (H,W,3 uint8) through the juiced eye.

        Runs the sealed hi-res retina pipeline, then BRAIN² enhancements.
        The visual cortex (brain2/cortex.py) tracks figure-ground blobs
        into persistent objects with stable IDs and velocities.
        dt: seconds since previous frame for the tracker (default: wall
        clock, clamped to [0.05, 2.0]s; pass explicitly in tests).
        Returns:
          motion_grid_hi  24x18 per-facet mapped motion (spatial field)
          redness_grid_hi 24x18 true-red hue ([BRAIN2-ENHANCEMENT])
          color_grid_hi   24x18 fly saturation (sealed formula, spatial)
          motion_mean     dilution-fixed scalar (top-k pooled)
          looming, contraction, color  sealed hi-res scalars (gates verified)
          blobs           figure-ground on the 24x18 motion field
          objects         [BRAIN2-ENHANCEMENT] tracked objects: stable IDs,
                          velocities, color signatures (the cortex output)
          scene_summary   [BRAIN2-ENHANCEMENT] one-line human-legible scene
          loom_xy         motion argmax while looming fires, else None
          eye_version     "brain2-hires"
        First frame (no temporal reference) returns all zeros.
        """
        import time as _time
        arr = np.asarray(rgb)
        out = self.retina.frame(arr)  # sealed hi-res pipeline
        h, w = arr.shape[0], arr.shape[1]
        grid, cgrid, rgrid, rgb_grid, en_all = self._bin_grids(w, h)
        motion_mean = self._motion_scalar(en_all)
        grid_r = [[round(float(x), 2) for x in row] for row in grid]
        cgrid_r = [[round(float(x), 2) for x in row] for row in cgrid]
        rgrid_r = [[round(float(x), 2) for x in row] for row in rgrid]
        blobs = _blobs(grid, rgrid, rgb_grid)
        # cortex: persistent objects + human-legible scene
        now_t = _time.time()
        if dt is None:
            dt = (now_t - self._last_frame_t) if self._last_frame_t else 1.0
            dt = min(2.0, max(0.05, dt))
        self._last_frame_t = now_t
        from brain2.cortex import scene_summary as _scene_summary
        objects = self.tracker.update(blobs, dt=dt)
        loom_xy = None
        if out.get("looming", 0.0) > 0:
            k = int(np.argmax(grid))
            r, c = k // B2_SIGHT_GW, k % B2_SIGHT_GW
            loom_xy = [round((c + 0.5) / B2_SIGHT_GW, 3),
                       round((r + 0.5) / B2_SIGHT_GH, 3)]
        from datetime import datetime, timezone
        return {
            "ts": datetime.now(timezone.utc).isoformat(timespec="seconds"),
            "motion_grid_hi": grid_r,
            "redness_grid_hi": rgrid_r,
            "color_grid_hi": cgrid_r,
            "motion_mean": round(motion_mean, 4),
            "looming": round(float(out.get("looming", 0.0)), 4),
            "contraction": round(float(out.get("contraction", 0.0)), 4),
            "color": round(float(out.get("color", 0.0)), 4),
            "blobs": blobs,
            "objects": objects,
            "scene_summary": _scene_summary(objects),
            "loom_xy": loom_xy,
            "eye_version": EYE_VERSION,
        }

    def state(self):
        """Transducer state."""
        gw, gh = self.grid
        return {
            "eye_version": EYE_VERSION,
            "grid": self.grid,
            "facets_per_eye": gw * gh,
            "total_facets": gw * gh * 2,
            "topk": self._topk,
            "gain": B2_GAIN,
            "floor": B2_FLOOR,
            "frames": self.retina._frames,
        }
