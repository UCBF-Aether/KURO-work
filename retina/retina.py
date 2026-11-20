#!/usr/bin/env python3
"""retina.py — RETINA v5, the binocular fly eye front end (BRAIN¹).

Two compound eyes (23x35 hex ommatidia each — the real count), frontal
binocular overlap, and a fovea-like acute zone. Frames in, sense
intensities out, driving the REAL visual bottles (motion, color,
looming) through a MODELED retina. Biofaithful: no finer-than-fly
grids, no invented color, no rewired circuits.

v5 (2026-10-16): DIRECTION REMOVED by design (Cory's call — the eyes
need to SEE and DETECT motion, not find its direction). Motion is a
scalar UNSIGNED energy: mean of |local motion| across the eye. The
Hassenstein-Reichardt correlator stays (the detection mechanism);
the pooled vector, band arrows, flow_dir, and motion_dir are gone.

HONESTY CONTRACT (non-negotiable):
- [REAL]    Two compound eyes, ~800 ommatidia each. Frontal binocular
            overlap (~20-30% of each eye's facets see the frontal field
            in the fly). A frontal acute zone (fovea-like enlarged
            ommatidia — the fly's high-acuity region). The
            Hassenstein-Reichardt delay-and-compare correlator, the
            textbook mechanism of the Drosophila optic lobe (the T4/T5
            direction-selective cells our motion bottle is wired from
            implement it). Downstream, the motion / color / looming
            bottles run on measured FlyWire FAFB v783 connectome wiring
            — nothing invented there.
- [MODEL]   The neural dynamics inside those bottles are the standard
            simplified model (0.15 threshold, 4 steps).
- [REAL]    The looming architecture: LPLC2-style radial motion
            opponency — outward-vs-inward motion energy computed per
            tiled receptive-field template from the local direction-
            selective flow (Klapoetke et al.: LPLC2 is selective for
            radial expansion, [LITERATURE-CONSTRAINT]).
- [MODELED] EVERYTHING about transduction: pixels -> facet luminance
            (block averaging), R1-6 as broadband luma, RGB -> fly color
            (RGB has no UV channel; blue/green proxies only, honestly
            approximate), the radial-opponency pooling weights (uniform),
            template count (3x3 per eye), dominance/growth thresholds and
            streak length, the exact overlap fraction (0.25), the
            acute-zone gain ramp shape and peak (1.5x), facet layout,
            1-frame delay, and all gains/thresholds below. The motion
            readout — mean of |local HR response| across the eye — is
            a design simplification: the eye reports HOW MUCH motion,
            not which way. The fly never saw your camera.
- [FICTION] Any gloss ("the machine opens its eyes") is fiction, not a
            claim about experience.

Usage:
    from retina import Retina
    r = Retina()                       # two hex eyes, 805 facets each
    out = r.frame(rgb_uint8_frame)     # -> {"motion","color",
                                       #     "looming","contraction"}
    r.eye_outputs()                    # -> {"L": {...}, "R": {...}}
    motion_bottle.sense(out["motion"])
    color_bottle.sense(out["color"], channel="both")
    looming_bottle.sense(out["looming"])
    r.state()
"""

import numpy as np

# ---- module constants (all [MODELED] transduction choices) ----------------
GRID_W, GRID_H = 30, 26          # square-lattice ommatidia grid per eye;
                                 # 30*26 = 780 ~= one fly eye (~800)
HEX_GW, HEX_GH = 23, 35          # hex-lattice grid per eye: offset rows,
                                 # regular hexagons (6 equidistant
                                 # neighbors); 23*35 = 805 ~= one eye.
                                 # Chosen so neighbor distance is uniform:
                                 # row spacing = col pitch * sqrt(3)/2.
HEX_SQRT3_2 = 0.8660254037844386  # sqrt(3)/2, hex row spacing factor
MOTION_FLOOR = 0.0002            # dead zone on mean |HR| response (kills float noise;
                              # calibrated: synthetic dot ~0.004, traffic
                              # peaks ~0.0007, static-feed noise ~0.00017 —
                              # identical frames are exactly 0.0, so the
                              # synthetic static gate is unaffected)
MOTION_GAIN = 120.0             # scales mean |HR| -> 0..1 intensity.
                              # v5 RECALIBRATION: the unsigned readout sums
                              # incoherent local flicker that the old pooled
                              # vector canceled, so the gain comes down ~7x
                              # (was 800). Measured: synthetic bar 0.069 ->
                              # 1.0 (clip); textured car 0.0062 -> 0.74;
                              # I-95 traffic p10/p90 0.0025/0.0073 ->
                              # 0.30/0.88 (real dynamic range, not pegged).
                              # Static identical frames are exactly 0.0.
# ---- LPLC2-style radial opponency (v4) ------------------------------------
LOOM_TEMPLATES = 3              # per-eye radial template grid is NxN (the
                                # fly tiles LPLC2 RFs across the visual
                                # field; radial opponency is per-RF, not
                                # global — [MODELED] N=3, [REAL] tiling.
                                # Smaller RFs handle partial visibility:
                                # a translating object fully inside an RF
                                # cancels via opponency.)
LOOM_DOM_MIN = 4.0              # min outward/inward energy dominance for a
                                # template to count (translation residuals
                                # reach ~3.0; true expansion is 10+)
LOOM_R_MAX = 0.55               # max angular spread R of the outward flow
                                # (0=radial/all directions, 1=clustered).
                                # True expansion: R<=0.43; translation and
                                # entry: R>=0.53. Kills partial-visibility
                                # entry/translation structurally.
LOOM_ENERGY_FLOOR = 1e-6        # below this, outward energy is float noise
LOOM_GROWTH_MIN = 0.08          # (retained for documentation; firing is by
                                # sustained candidacy, intensity by magnitude)
LOOM_RADIAL_GAIN = 1.0          # (retained for documentation)
LOOM_MAG_GAIN = 0.25            # scales outward energy -> 0..1 intensity
                                # (calibrated: the looming BOTTLE's real
                                # wiring needs intensity>=0.806 to fire
                                # (max hop0->hop1 weight 0.1861 x 0.15
                                # threshold); eyeloop scene (c) out_e~2-4
                                # -> 0.5-1.0; sealed disc out_e~12 -> 1.0)
LOOM_STREAK_MIN = 3             # consecutive candidate frames required
LOOM_CONTRACTION_GAIN = 0.03    # scales inward energy -> contraction 0..1

# ---- v2 biofaithful constants ---------------------------------------------
OVERLAP_SHARED = 0.25           # [MODELED mapping of REAL anatomy] fraction
                                # of each eye's facets in the frontal
                                # binocular overlap (~20-30% in the fly)
ACUTE_GAIN = 1.5                # [MODELED] peak motion-gain multiplier at
                                # the acute zone (the zone itself — frontal
                                # enlarged ommatidia — is REAL fly anatomy)

_LUMA = np.array([0.299, 0.587, 0.114], dtype=np.float64)  # R1-6 proxy


def _favg1d(v, n_out, axis):
    """Fractional block-average of float array v along axis -> n_out bins.

    Exact (edge-weighted) averaging for non-integer bin widths, via
    interpolated cumulative sums. Deterministic.
    """
    n_in = v.shape[axis]
    edges = np.linspace(0, n_in, n_out + 1)
    v = np.moveaxis(v, axis, -1)
    cs = np.concatenate(
        [np.zeros(v.shape[:-1] + (1,)), np.cumsum(v, axis=-1)], axis=-1)
    i0 = np.floor(edges).astype(int)
    f = edges - i0
    i1 = np.minimum(i0 + 1, n_in)
    c = (np.take(cs, i0, axis=-1) * (1 - f)
         + np.take(cs, i1, axis=-1) * f)
    out = np.diff(c, axis=-1) / np.maximum(np.diff(edges), 1e-9)
    return np.moveaxis(out, -1, axis)

# Each eye's window as a fraction of frame width, derived so the frontal
# overlap holds OVERLAP_SHARED of each eye's facets:
#   2*COVER - OVERLAP = 1  with OVERLAP = OVERLAP_SHARED*COVER
#   => COVER = 1/(2-OVERLAP_SHARED)  ~= 0.571
_EYE_COVER = 1.0 / (2.0 - OVERLAP_SHARED)


def _box3(m):
    """3x3 box filter (valid-masked mean), numpy only. Merges adjacent
    opponent HR dipole pairs into net regional flow."""
    mp = np.pad(m, 1, mode="constant")
    return (mp[:-2, :-2] + mp[:-2, 1:-1] + mp[:-2, 2:]
            + mp[1:-1, :-2] + mp[1:-1, 1:-1] + mp[1:-1, 2:]
            + mp[2:, :-2] + mp[2:, 1:-1] + mp[2:, 2:]) / 9.0


class _Eye:
    """One compound eye: its acute-zone gain maps and temporal state."""

    def __init__(self, side, grid=(GRID_W, GRID_H)):
        # side "L"/"R"; frontal = toward frame center (+x edge for L,
        # -x edge for R).
        self.side = side
        gw, gh = self.grid = (int(grid[0]), int(grid[1]))
        # Acute-zone gain ramp: 1.0 (periphery) -> ACUTE_GAIN (frontal),
        # normalized to mean 1.0 so the calibrated MOTION_FLOOR/MOTION_GAIN
        # still hold. [REAL] the acute zone; [MODELED] ramp shape + peak.
        if side == "L":
            ramp = np.linspace(1.0, ACUTE_GAIN, gw)
        else:
            ramp = np.linspace(ACUTE_GAIN, 1.0, gw)
        g = np.tile(ramp, (gh, 1))
        gx = (g[:, :-1] + g[:, 1:]) / 2.0   # pair gains for HR correlator
        gy = (g[:-1, :] + g[1:, :]) / 2.0
        self._gain_x = gx / gx.mean()
        self._gain_y = gy / gy.mean()
        self._gain_facet = g / g.mean()  # per-facet gain (hex lattice path)
        self._pitch = (1.0, 1.0)  # (px per col, px per row); set on downsample
        self._win = (1.0, 1.0)    # eye window (w, h) in px; set on downsample
        self._prev_lum = None
        # LPLC2 radial-opponency temporal state
        self._loom_streak = 0      # consecutive candidate expansion frames
        self._loom_cstreak = 0     # consecutive candidate contraction frames
        self._loom_nfire = 0       # templates passing dominance this frame
        self._viz = (None, None, None)  # (facets, lum, prev_lum) for viz
        self._viz_energy = None  # per-facet |local motion| map for viz
                                 # (heat-glow); motion, not direction
        self._last = {"motion": 0.0, "color": 0.0,
                      "looming": 0.0, "contraction": 0.0}


class Retina:
    """The binocular fly eye front end: frames in, sense intensities out.

    Parameters
    ----------
    grid : (w, h), optional
        Ommatidia grid per eye. Default follows ``lattice``.
    lattice : "square" | "hex", optional
        Facet packing. "square" = 30x26 axis-aligned grid (780 facets).
        "hex" = 23x35 offset-row hexagonal packing (805 facets, 6
        equidistant neighbors — the real ommatidial geometry). The
        hex path runs a 3-axis Hassenstein-Reichardt correlator
        (0/60/120 deg), the square path the 2-axis version. Biofaithful:
        do not exceed the real facet count.
    """

    def __init__(self, grid=None, lattice="hex"):
        if lattice not in ("square", "hex"):
            raise ValueError("lattice must be 'square' or 'hex'")
        self.lattice = lattice
        if grid is None:
            grid = (HEX_GW, HEX_GH) if lattice == "hex" else (GRID_W, GRID_H)
        gw, gh = int(grid[0]), int(grid[1])
        if gw < 2 or gh < 2:
            raise ValueError("grid must be at least 2x2")
        self.grid = (gw, gh)
        self.eyes = {"L": _Eye("L", self.grid),
                     "R": _Eye("R", self.grid)}
        self._frames = 0
        self._last = {"motion": 0.0, "color": 0.0,
                      "looming": 0.0, "contraction": 0.0}
        self._eye_last = {s: dict(self._last) for s in ("L", "R")}

    # ---- the eyes -----------------------------------------------------
    def _split(self, w):
        """[MODELED] Frame columns per eye with frontal overlap.

        Left eye: [0, COVER*w); right eye: [w-COVER*w, w). The middle
        OVERLAP_SHARED of each eye's window sees the same frontal field.
        """
        cover = int(round(w * _EYE_COVER))
        return (0, cover), (w - cover, w)

    def _downsample_region(self, rgb, x0, x1, eye):
        """[MODELED] Block-average one eye's window onto its grid.

        Square lattice: fractional (edge-weighted) averaging so the
        window covers EXACTLY [x0, x1) — no truncated pixels.
        Hex lattice: exact 2x square grid, then bilinear sampling at
        the offset-row hex facet centers (real packing geometry; the
        luminance field is sampled, not the bin shape, that matters).
        Sets eye._pitch = (px per col, px per row) for correlator
        unit vectors.
        """
        h = rgb.shape[0]
        gw, gh = self.grid
        if x1 - x0 < gw or h < gh:
            raise ValueError(
                "eye window %dx%d too small for %dx%d grid"
                % (x1 - x0, h, gw, gh))
        crop = rgb[:, x0:x1, :].astype(np.float64)
        eye._win = (float(x1 - x0), float(h))
        if self.lattice == "hex":
            return self._hex_sample(crop, eye)
        gx = _favg1d(crop, gw, axis=1)
        gxy = _favg1d(gx, gh, axis=0)
        eye._pitch = ((x1 - x0) / gw, h / gh)
        return gxy / 255.0  # -> float 0..1, shape (gh, gw, 3)

    def _hex_sample(self, crop, eye):
        """[MODELED] Sample the crop's luminance field at hex facet centers.

        Offset rows (odd rows shifted +half pitch); row spacing =
        pitch*sqrt(3)/2 so all 6 neighbors are equidistant — the real
        ommatidial packing. Deterministic bilinear interpolation from
        an exact 2x square grid (no dropped pixels).
        Returns float (gh, gw, 3); also stores centers on the eye for viz.
        """
        h, w, _ = crop.shape
        gw, gh = self.grid
        pw = w / gw
        ph = pw * HEX_SQRT3_2
        # exact 2x grid, then bilinear sample
        g2 = _favg1d(crop, 2 * gh, axis=0)
        g2 = _favg1d(g2, 2 * gw, axis=1)  # (2gh, 2gw, 3)
        js = np.arange(gw, dtype=np.float64)[None, :].repeat(gh, axis=0)
        ii = np.arange(gh, dtype=np.float64)[:, None].repeat(gw, axis=1)
        xs = (js + 0.5 + 0.5 * (ii % 2)) * pw
        ys = (ii + 0.5) * ph
        # recentre vertically so the lattice spans the crop
        ys += ((h - (gh - 1) * ph) / 2.0) - 0.5 * ph
        # map to 2x-grid coords
        gx = np.clip(xs / w * (2 * gw) - 0.5, 0, 2 * gw - 1.001)
        gy = np.clip(ys / h * (2 * gh) - 0.5, 0, 2 * gh - 1.001)
        x0i = gx.astype(int)
        y0i = gy.astype(int)
        x1i = np.minimum(x0i + 1, 2 * gw - 1)
        y1i = np.minimum(y0i + 1, 2 * gh - 1)
        fx = (gx - x0i)[..., None]
        fy = (gy - y0i)[..., None]
        f00 = g2[y0i, x0i]
        f10 = g2[y0i, x1i]
        f01 = g2[y1i, x0i]
        f11 = g2[y1i, x1i]
        out = (f00 * (1 - fx) * (1 - fy) + f10 * fx * (1 - fy)
               + f01 * (1 - fx) * fy + f11 * fx * fy)
        eye._pitch = (pw, ph)
        eye._hex_xy = (xs, ys)  # facet centers in crop px, for viz
        return out / 255.0

    def _luminance(self, facets):
        """[MODELED] Broadband R1-6 proxy from RGB."""
        return facets @ _LUMA  # (gh, gw)

    def _colorfulness(self, facets):
        """[MODELED] Mean per-facet saturation as color intensity.

        Honest approximation: RGB carries no UV, so this is a saturation
        proxy for the R7/R8 (blue/green-ish) pathway, not true fly color.
        """
        mx = facets.max(axis=2)
        mn = facets.min(axis=2)
        with np.errstate(divide="ignore", invalid="ignore"):
            sat = np.where(mx > 1e-9, (mx - mn) / mx, 0.0)
        return float(np.clip(sat.mean(), 0.0, 1.0))

    def _flow_field(self, lum, prev, eye):
        """Per-lattice local HR flow field.

        Returns {"local_vx","local_vy","local_valid"}: the per-facet
        opponent-correlator vectors that feed BOTH the unsigned motion
        readout and the LPLC2 looming computation. No pooled vectors,
        no bands — direction machinery was removed by design (v5).
        """
        if self.lattice == "hex":
            return self._hex_flow(lum, prev, eye)
        return self._square_flow(lum, prev, eye)

    def _square_flow(self, lum, prev, eye):
        """2-axis HR on the square lattice (local field only)."""
        rx = ((prev[:, :-1] * lum[:, 1:] - lum[:, :-1] * prev[:, 1:])
              * eye._gain_x)
        ry = ((prev[:-1, :] * lum[1:, :] - lum[:-1, :] * prev[1:, :])
              * eye._gain_y)
        gh, gw = lum.shape
        # per-facet local vectors: average adjacent pair responses
        vx = np.zeros_like(lum)
        vy = np.zeros_like(lum)
        vx[:, 1:] += rx / 2.0
        vx[:, :-1] += rx / 2.0
        vy[1:, :] += ry / 2.0
        vy[:-1, :] += ry / 2.0
        valid = np.ones_like(lum, dtype=bool)
        valid[:, 0] = valid[:, -1] = False
        valid[0, :] = valid[-1, :] = False
        return {"local_vx": vx, "local_vy": vy, "local_valid": valid}

    def _hex_flow(self, lum, prev, eye):
        """3-axis HR on the hex lattice (local field only).

        [REAL mechanism] Nearest-neighbor opponent correlators along the
        3 lattice axes (0/60/120 deg) - the real ommatidial packing gives
        6 equidistant neighbors; local 2D vector reconstructed as
        v = (2/3) * sum_k r_k u_k. [MODELED] 1-frame delay, gain map.
        """
        gh, gw = lum.shape
        pw, ph = eye._pitch
        even = ((np.arange(gh) % 2) == 0)[:, None]  # (gh,1) bool
        odd_col = ~even[:, 0]  # (gh,) bool
        # axis H (+x): neighbor (i, j+1)
        nH = np.roll(lum, -1, axis=1)
        nHp = np.roll(prev, -1, axis=1)
        vH = np.ones((gh, gw), dtype=bool)
        vH[:, -1] = False
        # axis D1 (up-right): even rows (i-1,j); odd rows (i-1,j+1)
        r1 = np.roll(lum, 1, axis=0)
        r1p = np.roll(prev, 1, axis=0)
        nD1 = np.where(even, r1, np.roll(r1, -1, axis=1))
        nD1p = np.where(even, r1p, np.roll(r1p, -1, axis=1))
        vD1 = np.ones((gh, gw), dtype=bool)
        vD1[0, :] = False
        vD1[odd_col, -1] = False
        # axis D2 (down-right): even rows (i+1,j); odd rows (i+1,j+1)
        r2 = np.roll(lum, -1, axis=0)
        r2p = np.roll(prev, -1, axis=0)
        nD2 = np.where(even, r2, np.roll(r2, -1, axis=1))
        nD2p = np.where(even, r2p, np.roll(r2p, -1, axis=1))
        vD2 = np.ones((gh, gw), dtype=bool)
        vD2[-1, :] = False
        vD2[odd_col, -1] = False
        rH = np.where(vH, prev * nH - lum * nHp, 0.0)
        rD1 = np.where(vD1, prev * nD1 - lum * nD1p, 0.0)
        rD2 = np.where(vD2, prev * nD2 - lum * nD2p, 0.0)
        # physical unit vectors (regular hex => 0/60/120 deg axes)
        uD1 = np.array([0.5 * pw, -ph])
        uD1 = uD1 / np.linalg.norm(uD1)
        uD2 = np.array([0.5 * pw, ph])
        uD2 = uD2 / np.linalg.norm(uD2)
        vx = (2.0 / 3.0) * (rH + rD1 * uD1[0] + rD2 * uD2[0])
        vy = (2.0 / 3.0) * (rD1 * uD1[1] + rD2 * uD2[1])
        g = eye._gain_facet
        vx = vx * g
        vy = vy * g
        valid = vH & vD1 & vD2
        return {"local_vx": vx, "local_vy": vy, "local_valid": valid}

    def _hr_motion(self, flow):
        """[REAL mechanism] Hassenstein-Reichardt delay-and-compare,
        weighted by the eye's acute-zone gain map, read out as UNSIGNED
        motion energy (v5).

        For each adjacent facet pair, preferred-minus-null:
            resp_x = prev[x,y]*lum[x+1,y] - lum[x,y]*prev[x+1,y]
        Motion intensity = mean of |local motion vector| across valid
        facets. Unsigned: opposing traffic adds instead of cancelling —
        the eye reports HOW MUCH motion, not which way (design
        simplification, Cory's call). For uniform motion this equals the
        old pooled-vector magnitude, so the MOTION_FLOOR/MOTION_GAIN
        calibration holds unchanged. The opponent multiplication is the
        fly's algorithm; the delay (1 frame), neighbor spacing, acute
        gain ramp, and the unsigned readout are [MODELED].
        Returns intensity 0..1.
        """
        vx, vy, valid = (flow["local_vx"], flow["local_vy"],
                         flow["local_valid"])
        if not valid.any():
            return 0.0
        energy = float(np.hypot(vx[valid], vy[valid]).mean())
        if energy < MOTION_FLOOR:
            return 0.0
        return float(np.clip(energy * MOTION_GAIN, 0.0, 1.0))

    def _loom_field(self, flow, eye):
        """Per-template radial motion energies (the LPLC2 computation).

        [REAL mechanism] For each of the LOOM_TEMPLATES^2 tiled radial
        templates (cf. LPLC2 receptive fields tiling the visual field),
        project every facet's local flow vector onto the outward-from-
        template-center direction: outward energy vs inward energy, the
        opponent pair LPLC2 integrates. [MODELED] template count (3x3),
        uniform facet weights, 1-facet central exclusion zone.
        Returns {"out_e","in_e","opp","dom","R_out","R_in"} over templates.
        R_out/R_in are the energy-weighted angular spread of outward /
        inward flow (0 = radial in all directions, 1 = clustered) — true
        expansion is radial; a partially-visible translating edge is
        clustered. [MODELED] like the rest of the pooling.
        """
        vx, vy, valid = (flow["local_vx"], flow["local_vy"],
                         flow["local_valid"])
        gh, gw = vx.shape
        pw, ph = eye._pitch
        win_w, win_h = eye._win
        # merge adjacent opponent HR dipole pairs into net regional flow
        # (3x3). The radial CORRELATION (below) integrates over the whole
        # template and is inherently robust to texture chaos — heavier
        # smoothing washes out the signal. [MODELED] width.
        vm = valid.astype(float)
        vx = _box3(vx * vm) / np.maximum(_box3(vm), 1e-9)
        vy = _box3(vy * vm) / np.maximum(_box3(vm), 1e-9)
        valid = _box3(vm) > 0.5
        if self.lattice == "hex":
            xs, ys = eye._hex_xy  # facet centers, crop px
        else:
            xs = (np.arange(gw, dtype=np.float64)[None, :].repeat(gh, 0)
                  * pw)
            ys = (np.arange(gh, dtype=np.float64)[:, None].repeat(gw, 1)
                  * ph)
        pitch = 0.5 * (pw + ph)
        n = LOOM_TEMPLATES
        cxs = (np.arange(n, dtype=np.float64) + 0.5) / n * win_w
        cys = (np.arange(n, dtype=np.float64) + 0.5) / n * win_h
        outs, ins, r_outs, r_ins = [], [], [], []
        th = np.arctan2(vy, vx)
        cth, sth = np.cos(th), np.sin(th)
        for cy in cys:
            for cx in cxs:
                dx = xs - cx
                dy = ys - cy
                rr = np.hypot(dx, dy)
                m = valid & (rr > pitch)
                if not m.any():
                    outs.append(0.0)
                    ins.append(0.0)
                    r_outs.append(1.0)
                    r_ins.append(1.0)
                    continue
                ux = dx / np.maximum(rr, 1e-9)
                uy = dy / np.maximum(rr, 1e-9)
                rad = np.where(m, vx * ux + vy * uy, 0.0)
                wo = np.maximum(rad, 0.0)
                wi = np.maximum(-rad, 0.0)
                to = float(wo[m].sum())
                ti = float(wi[m].sum())
                outs.append(to)
                ins.append(ti)
                if to > 1e-12:
                    rx = float((wo * cth)[m].sum()) / to
                    ry = float((wo * sth)[m].sum()) / to
                    r_outs.append(float(np.hypot(rx, ry)))
                else:
                    r_outs.append(1.0)
                if ti > 1e-12:
                    rx = float((wi * cth)[m].sum()) / ti
                    ry = float((wi * sth)[m].sum()) / ti
                    r_ins.append(float(np.hypot(rx, ry)))
                else:
                    r_ins.append(1.0)
        outs = np.array(outs)
        ins = np.array(ins)
        return {"out_e": outs, "in_e": ins, "opp": outs - ins,
                "dom": outs / (ins + 1e-12),
                "R_out": np.array(r_outs), "R_in": np.array(r_ins)}

    def _looming(self, flow, eye):
        """[REAL mechanism] LPLC2-style radial motion opponency, per eye.

        Klapoetke et al.: LPLC2 responds selectively to radial expansion
        (centrifugal motion in its receptive field), not translation.
        We compute, per tiled radial template, outward-vs-inward motion
        energy from the existing per-facet HR flow field and apply
        opponent subtraction. Looming = a template with strongly
        outward-dominant energy and a RADIALLY spread outward flow
        (not a clustered translating edge), SUSTAINED over frames — a
        continuously expanding flow field is an approach. Intensity
        scales with outward energy magnitude (bigger/closer = stronger).
        [LITERATURE-CONSTRAINT] the radial-opponency architecture;
        [MODELED] template count, smoothing, gains, thresholds, streak
        length. The old dark-area proxy and its centroid veto are
        retired — opponency kills entry and translation structurally.
        Returns (looming 0..1, contraction 0..1). Contraction (sustained
        inward-dominant radial flow — a receding object) is its own
        reported signal, not a loom.
        """
        f = self._loom_field(flow, eye)
        outs, ins = f["out_e"], f["in_e"]
        k_exp = int(np.argmax(f["opp"]))
        k_con = int(np.argmin(f["opp"]))
        out_e, in_e = float(outs[k_exp]), float(ins[k_exp])
        in_c, out_c = float(ins[k_con]), float(outs[k_con])
        dom_e = out_e / (in_e + 1e-12)
        dom_c = in_c / (out_c + 1e-12)
        looming, contraction = 0.0, 0.0
        # expansion channel: dominant, radial, and SUSTAINED
        # (a continuously expanding flow field IS an approach; the old
        # per-frame growth requirement missed slow approaches, so firing
        # is by sustained candidacy and intensity scales with the
        # outward energy magnitude)
        if (dom_e >= LOOM_DOM_MIN and out_e >= LOOM_ENERGY_FLOOR
                and f["R_out"][k_exp] <= LOOM_R_MAX):
            eye._loom_nfire = int(((f["dom"] >= LOOM_DOM_MIN)
                                   & (f["out_e"] >= LOOM_ENERGY_FLOOR)
                                   & (f["R_out"] <= LOOM_R_MAX)).sum())
            eye._loom_streak += 1
            if eye._loom_streak >= LOOM_STREAK_MIN:
                looming = float(np.clip(out_e * LOOM_MAG_GAIN, 0.0, 1.0))
        else:
            eye._loom_streak = 0
            eye._loom_nfire = 0
        # contraction channel: sustained inward-dominant radial flow
        # (a receding object's inward energy shrinks as it shrinks, so
        # growth is the wrong signature — sustained dominance is)
        if (dom_c >= LOOM_DOM_MIN and in_c >= LOOM_ENERGY_FLOOR
                and f["R_in"][k_con] <= LOOM_R_MAX):
            eye._loom_cstreak += 1
            if eye._loom_cstreak >= LOOM_STREAK_MIN:
                contraction = float(np.clip(in_c * LOOM_CONTRACTION_GAIN,
                                            0.0, 1.0))
        else:
            eye._loom_cstreak = 0
        return looming, contraction

    def _fuse(self):
        """Fuse the two eyes: motion = stronger eye (either eye seeing
        motion is motion), color/looming/contraction = max. No direction
        anywhere — the output is four unsigned intensities (v5)."""
        L = self._eye_last["L"]
        R = self._eye_last["R"]
        return {"motion": max(L["motion"], R["motion"]),
                "color": max(L["color"], R["color"]),
                "looming": max(L["looming"], R["looming"]),
                "contraction": max(L["contraction"], R["contraction"])}

    # ---- public API ---------------------------------------------------
    def frame(self, rgb):
        """Process one RGB frame (H,W,3 uint8).

        One frame in; split internally into the two eyes with frontal
        overlap. Returns the FUSED {"motion": 0..1, "color": 0..1,
        "looming": 0..1, "contraction": 0..1} — unsigned intensities for
        the existing bottles' sense() API. Per-eye outputs via
        eye_outputs(). First frame returns all zeros (no temporal
        reference yet); identical consecutive frames return all zeros.
        """
        arr = np.asarray(rgb)
        if arr.ndim != 3 or arr.shape[2] != 3:
            raise ValueError("frame must be (H,W,3), got shape %r"
                             % (arr.shape,))
        if arr.dtype != np.uint8:
            arr = np.clip(arr, 0, 255).astype(np.uint8)
        h, w, _ = arr.shape
        (x0L, x1L), (x0R, x1R) = self._split(w)
        for side, (x0, x1) in (("L", (x0L, x1L)), ("R", (x0R, x1R))):
            eye = self.eyes[side]
            facets = self._downsample_region(arr, x0, x1, eye)
            lum = self._luminance(facets)
            color = self._colorfulness(facets)
            if eye._prev_lum is None:
                # no temporal reference: store and report nothing
                eye._prev_lum = lum
                eye._viz = (facets, lum, None)
                eye._viz_energy = None
                eye._last = {"motion": 0.0, "color": color,
                             "looming": 0.0, "contraction": 0.0}
            else:
                flow = self._flow_field(lum, eye._prev_lum, eye)
                motion = self._hr_motion(flow)
                looming, contraction = self._looming(flow, eye)
                eye._viz = (facets, lum, eye._prev_lum)
                eye._viz_energy = np.hypot(flow["local_vx"],
                                           flow["local_vy"])
                eye._prev_lum = lum
                eye._last = {"motion": motion, "color": color,
                             "looming": looming,
                             "contraction": contraction}
        self._eye_last = {s: dict(self.eyes[s]._last) for s in ("L", "R")}
        self._last = self._fuse()
        self._frames += 1
        return dict(self._last)

    def eye_outputs(self):
        """Per-eye outputs from the last frame(): {"L": {...}, "R": {...}}.

        For binocular checks and debugging. The fused output of frame()
        is what feeds the bottles.
        """
        return {s: dict(v) for s, v in self._eye_last.items()}

    def last_fields(self):
        """Per-eye (facets, luminance, prev_luminance) grids for viz.

        Returns {"L": (facets, lum, prev), "R": (...)}; facets is
        (gh, gw, 3) float RGB — what each eye "sees". Entries are None
        until frames have been seen. Visualization only — not part of
        the transduction path.
        """
        return {s: self.eyes[s]._viz for s in ("L", "R")}

    def state(self):
        """Current transducer state."""
        gw, gh = self.grid
        return {
            "eyes": 2,
            "grid": self.grid,
            "facets_per_eye": gw * gh,
            "total_facets": 2 * gw * gh,
            "overlap_shared": OVERLAP_SHARED,
            "frames": self._frames,
            "last": dict(self._last),
        }
