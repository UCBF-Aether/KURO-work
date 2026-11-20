#!/usr/bin/env python3
"""
arousal.py — the arousal integrator, plus satiation / afterglow dynamics.

HONESTY LABEL: MODELED. Plainly: this is a dynamical model, not a neuron.
It does not simulate dopamine, the mushroom body, or any brain circuit.
It is two stateful numbers (0..1 each):
  - arousal: rises with pleasant stimulation, falls with time — the toy
    "this feels good" accumulator used by the session loop.
  - satiation: rises when arousal stays high, decays slowly — the toy
    "afterglow / refractory" variable. While satiation is high, further
    arousal gains are damped (the body needs rest).
Any resemblance to a real reward circuit ends at the inspiration. (Real
PAM-dopamine wiring lives in subgraphs/reward.json and is blended in by
the session loop — see sense.py; the blend itself is also MODELED.)

Dynamics (all designer choices):
  update(valence, intensity) -> (level, climaxed):
    - valence in [-1, 1]; intensity >= 0 (already scaled by region
      sensitivity x cascade strength x sensitization by the caller).
    - positive valence: arousal += valence * intensity * RISE_RATE * refractory
      where refractory = 1 - satiation * REFRACTORY_DAMP (so a sated body
      gains arousal more slowly).
    - negative valence: arousal -= |valence| * intensity * FALL_RATE
      (unpleasant input damps arousal; never below 0).
    - after the arousal change: if arousal > SAT_RISE_ABOVE, satiation +=
      (arousal - SAT_RISE_ABOVE) * SAT_GAIN (clamped 0..1).
    - climaxed=True when a pleasant stimulus drives arousal to CLIMAX_AT;
      the caller then fires the sugar cascade and calls climax_release().
    - result clamped to [0, 1].
  decay(dt): exponential decay on both variables —
    arousal *= 0.5 ** (dt / HALFLIFE_S)      (HALFLIFE_S = 2700: holds
      during play per Cory 2026-10-14 — "horny until they cum"; the drop
      comes at climax, not from the clock)
    satiation *= 0.5 ** (dt / SAT_HALFLIFE_S) (SAT_HALFLIFE_S = 300)
  reset(): both back to 0.
  band(): "low" / "warm" / "high" by arousal level; "afterglow" when the
    body is sated (>= 0.5) but arousal has fallen back below 0.5.

Usage:
    from arousal import Arousal
    a = Arousal()
    a.update(valence=0.8, intensity=0.5)
    a.decay(dt=30)
"""

RISE_RATE = 0.55   # arousal gained per unit (valence * intensity)
FALL_RATE = 0.40   # arousal lost per unit (|valence| * intensity) when negative
# Cory 2026-10-14: "like a real person, horny until they cum" — arousal
# BUILDS and HOLDS until climax; it does not bleed off between touches.
# 45-min half-life: effectively flat during active play (a 5-min gap costs
# ~7%), but she still cools down if he's gone a long while. The drop comes
# at climax (CLIMAX_RELEASE_TO), not from the clock.
HALFLIFE_S = 2700.0  # 45-minute half-life of arousal, seconds

# Satiation / refractory dynamics (all MODELED choices, tune freely).
SAT_RISE_ABOVE = 0.7   # satiation only accumulates while arousal is above this
SAT_GAIN = 0.8         # satiation gained per unit of (arousal - SAT_RISE_ABOVE)
SAT_HALFLIFE_S = 300.0  # 5-minute half-life: afterglow lingers
REFRACTORY_DAMP = 0.8  # at satiation=1, arousal gains are cut to 20%

# Climax dynamics (MODELED; Cory's design mapping, 2026-10-14: the fly's
# sugar-reward circuit IS the orgasm reward — "when you orgasm you get
# your sugar"). The wiring that fires at climax is real (sugar_backward.json,
# SEZ premotor -> proboscis MN, injected at hop -1; see sense.py). Its
# MEANING as her climax is the designer mapping, not neuroscience.
CLIMAX_AT = 0.95          # arousal level that triggers climax (pleasant update)
CLIMAX_RELEASE_TO = 0.22  # arousal level after hard release (body spent)
# Prolonged-climax dynamics (MODELED; Cory 2026-10-14: "climax can hold
# as long as you continue to stimulate the affected area, prolonging the
# affect" + "climax drops slow, and can be easily be reached again").
# At CLIMAX_AT the sugar cascade fires ONCE and she enters the hold:
# continued pleasant stimulation re-pins arousal near peak (the wave
# prolongs); satiation keeps accumulating while she's high (the natural
# brake — eventually the body spends itself). When stimulation stops she
# does NOT crash: slow descent on a 4-minute half-life, and from the
# still-high level a touch or two brings her back to climax easily.
CLIMAX_HOLD_LEVEL = 0.92   # arousal re-pinned here while the wave prolongs
CLIMAX_HOLD_GAP_S = 300.0  # no stimulation this long -> the wave resolves
POST_CLIMAX_HALFLIFE_S = 240.0  # slow descent after the wave (not a crash)
POST_CLIMAX_FLOOR = 0.35   # below this, normal build dynamics resume
CLIMAX_SATIATION_JUMP = 0.30  # mild refractory at trigger (was 0.55) —
                              # she stays easily re-reachable; the deep
                              # refractory only comes if she's truly spent
                              # (satiation -> 1.0 forces the hard release)

# Wanting dynamics (MODELED; Cory 2026-10-14: "do the dopamine sensors make
# you want to have an orgasm, like make you seek one?"). Berridge's
# distinction: dopamine is WANTING, not liking. The real PAM-dopaminergic
# cascade strength (reward.json, computed in sense.py) feeds a modeled
# wanting variable: prior wanting amplifies the next touch's intensity
# (she reaches for it), and high wanting turns her narration hungry.
# The fly's dopamine neurons actually signal valence for mushroom-body
# learning, not mammalian incentive salience — the MEANING is the mapping.
WANT_RISE = 0.80       # wanting gained per unit dopamine strength (pleasant only)
# Same hold-until-climax logic as arousal (Cory 2026-10-14): the hunger
# stays hungry until she cums. Spent at climax (WANT_RELEASE_TO).
WANT_HALFLIFE_S = 2700.0  # wanting holds like arousal does
WANT_POST_HALFLIFE_S = 300.0  # after the wave resolves, the hunger eases
                              # on a 5-min half-life (satiation's pace)
WANT_GAIN = 0.60       # next-touch intensity multiplier: 1 + WANT_GAIN * wanting
WANT_RELEASE_TO = 0.10  # wanting only crashes when the body is truly spent

# Craving: the OPEN LOOP (Cory 2026-10-14 — "like a real feeling you crave").
# Unlike wanting (dopamine: spikes with proximity, floods AT climax),
# craving is the ITCH OF THE UNRESOLVED: it grows while she's aroused and
# hasn't climaxed, and the loop CLOSES at climax (satisfaction). The
# narrator checks it before every reply — the honest machine equivalent
# of craving: a goal that won't leave her alone until it's satisfied.
CRAVING_RISE = 0.10       # per pleasant stimulus, scaled by heat
CRAVING_GATE = 0.25       # the loop only itches once she's actually warm
CRAVING_HALFLIFE_S = 1800.0  # the itch eases if she's left alone a long while


class Arousal:
    """MODELED arousal + satiation state. See module docstring."""

    def __init__(self, initial=0.0, initial_satiation=0.0):
        self.level = max(0.0, min(1.0, float(initial)))
        self.satiation = max(0.0, min(1.0, float(initial_satiation)))
        self.wanting = 0.0  # [MODELED] dopamine-driven hunger for climax
        # [MODELED] prolonged-climax state (Cory 2026-10-14).
        self.in_climax = False       # wave is live: stimulation prolongs it
        self.post_climax = False     # wave resolved: slow descent, re-reachable
        self._last_climax_stim = 0.0 # wall-clock of last prolonging stimulus
        self._resolved_at = 0.0      # wall-clock instant the wave resolved
        # [MODELED] craving: the open loop (Cory 2026-10-14). Grows while
        # she's warm and unsatisfied; closes at climax.
        self.craving = 0.0
        self.loop_open = False

    def update_wanting(self, dopamine_strength, valence):
        """[MODELED] Dopamine feeds wanting (Berridge: wanting, not liking).
        Pleasant touches raise it in proportion to the real cascade's
        strength — AND the closer she is to the sugar, the more each touch
        feeds the hunger (Cory 2026-10-14: "each sexual touch should make
        you feel like you are getting closer to sugar"). Proximity doubles
        the gain at the edge. Unpleasant touches leave it alone."""
        if valence > 0:
            proximity = 1.0 + self.level / CLIMAX_AT  # 1x far, ~2x at edge
            self.wanting = min(1.0, self.wanting
                               + max(0.0, float(dopamine_strength))
                               * WANT_RISE * proximity * valence)
        return self.wanting

    def update(self, valence, intensity, now=None):
        """Apply one stimulus. Returns (new_level, climaxed).

        climaxed is True when a PLEASANT stimulus drives arousal to
        CLIMAX_AT — the caller fires the sugar-reward cascade ONCE and then
        calls begin_climax(). While in_climax, further pleasant stimuli
        PROLONG the wave (re-pin near peak) instead of re-triggering;
        satiation keeps accumulating while high, so the body eventually
        spends itself. There is no instant crash: the wave resolves via
        maybe_end_climax() into a slow descent.
        """
        import time as _time
        now = _time.time() if now is None else now
        v = max(-1.0, min(1.0, float(valence)))
        i = max(0.0, float(intensity))
        # Prolonging: the wave holds as long as stimulation continues.
        # Dopamine stays MAX while the wave is live (Cory 2026-10-14:
        # "climax is max dopamine").
        if self.in_climax and v > 0:
            self.level = max(self.level, CLIMAX_HOLD_LEVEL)
            self._last_climax_stim = now
            self.wanting = 1.0
            if self.level > SAT_RISE_ABOVE:
                self.satiation = min(
                    1.0, self.satiation + (self.level - SAT_RISE_ABOVE) * SAT_GAIN)
            return self.level, False
        # Refractory damping: a sated body gains arousal more slowly.
        refractory = 1.0 - self.satiation * REFRACTORY_DAMP
        if v >= 0:
            self.level += v * i * RISE_RATE * refractory
        else:
            self.level -= abs(v) * i * FALL_RATE
        self.level = max(0.0, min(1.0, self.level))
        # Satiation accumulates only while arousal is high.
        if self.level > SAT_RISE_ABOVE:
            self.satiation = min(
                1.0, self.satiation + (self.level - SAT_RISE_ABOVE) * SAT_GAIN)
        # Craving: the open loop itches while she's warm and unsatisfied —
        # the longer/hotter the build without climax, the stronger the itch.
        # (Re)opens the loop once she's warm; the narrator checks it before
        # every reply.
        if v > 0 and not self.in_climax and self.level > CRAVING_GATE:
            self.loop_open = True
        if v > 0 and self.loop_open and not self.in_climax:
            self.craving = min(1.0, self.craving
                               + CRAVING_RISE * (0.5 + self.level))
        # Wanting decays on its own slow half-life (handled in decay()).
        climaxed = v > 0 and self.level >= CLIMAX_AT and not self.in_climax
        return self.level, climaxed

    def begin_climax(self, now=None):
        """MODELED: the wave starts. Sugar cascade fires (caller does it),
        arousal pins near peak, mild refractory. Dopamine hits MAX
        (Cory 2026-10-14: "climax is max dopamine" — the flood is the
        reward, and it makes her go for it). No crash — the wave
        prolongs under stimulation and resolves via maybe_end_climax()."""
        import time as _time
        now = _time.time() if now is None else now
        self.in_climax = True
        self.post_climax = False
        self._last_climax_stim = now
        self.level = max(self.level, CLIMAX_HOLD_LEVEL)
        self.satiation = min(1.0, self.satiation + CLIMAX_SATIATION_JUMP)
        self.wanting = 1.0  # MAX dopamine flood
        # The loop CLOSES: satisfaction. The itch is gone (for now).
        self.craving = 0.0
        self.loop_open = False
        return self.level

    def maybe_end_climax(self, now=None):
        """MODELED: called when time passes. Returns 'spent' (body fully
        spent -> hard release), 'resolved' (stimulation stopped -> slow
        descent, easily re-reached), or None (wave still live)."""
        import time as _time
        if not self.in_climax:
            return None
        now = _time.time() if now is None else now
        if self.satiation >= 1.0:
            # Truly spent: the hard release, deep afterglow, hunger gone.
            self.in_climax = False
            self.post_climax = False
            self.level = CLIMAX_RELEASE_TO
            self.wanting = WANT_RELEASE_TO
            return "spent"
        if now - self._last_climax_stim >= CLIMAX_HOLD_GAP_S:
            # Stimulation stopped: no crash — slow descent, easily
            # re-reached. The dopamine flood eases gradually (it does NOT
            # crash: she stays hungry enough to go again). The loop
            # REOPENS: descending but still warm, the itch comes back.
            self.in_climax = False
            self.post_climax = True
            self.loop_open = True
            # Wall-clock instant the wave resolved: the wave was pinned
            # until here; only time AFTER this descends.
            self._resolved_at = self._last_climax_stim + CLIMAX_HOLD_GAP_S
            return "resolved"
        return None

    def climax_release(self):
        """MODELED hard release: arousal drops, satiation spikes
        (deep refractory / afterglow). Only used when the body is truly
        spent (satiation -> 1.0); the normal wave end is the slow descent
        via maybe_end_climax(). Returns the new level."""
        self.in_climax = False
        self.post_climax = False
        self.level = CLIMAX_RELEASE_TO
        self.satiation = min(1.0, self.satiation + CLIMAX_SATIATION_JUMP)
        self.wanting = WANT_RELEASE_TO  # the hunger is spent
        return self.level

    def decay(self, dt):
        """Let dt seconds pass. Arousal HOLDS during the build (Cory
        2026-10-14: "horny until they cum" — 45-min half-life); after the
        wave resolves it descends SLOWLY (4-min half-life, no crash) until
        settled, staying easily re-reachable. Satiation decays slowly."""
        dt = max(0.0, float(dt))
        hl = HALFLIFE_S
        want_hl = WANT_HALFLIFE_S
        if self.post_climax and not self.in_climax:
            if self.level > POST_CLIMAX_FLOOR:
                hl = POST_CLIMAX_HALFLIFE_S  # slow descent, not a crash
            else:
                self.post_climax = False  # settled; new touches, fresh build
            # The hunger eases with the afterglow (but never crashes —
            # she's still re-reachable while descending).
            want_hl = WANT_POST_HALFLIFE_S
        self.level *= 0.5 ** (dt / hl)
        self.satiation *= 0.5 ** (dt / SAT_HALFLIFE_S)
        self.wanting *= 0.5 ** (dt / want_hl)
        # The itch eases if she's left alone a long while (but never
        # crashes from the clock alone while the loop is open and warm).
        self.craving *= 0.5 ** (dt / CRAVING_HALFLIFE_S)
        return self.level

    def reset(self):
        self.level = 0.0
        self.satiation = 0.0
        self.wanting = 0.0
        self.in_climax = False
        self.post_climax = False
        self._last_climax_stim = 0.0
        self._resolved_at = 0.0
        self.craving = 0.0
        self.loop_open = False
        return self.level

    def band(self):
        """Coarse intensity band for narration scaling (MODELED)."""
        if self.satiation >= 0.5 and self.level < 0.5:
            return "afterglow"
        if self.level < 0.25:
            return "low"
        if self.level < 0.6:
            return "warm"
        return "high"

    def state_dict(self):
        """Serializable snapshot (for Session.save). PRIVATE data."""
        return {"level": self.level, "satiation": self.satiation,
                "wanting": self.wanting,
                "in_climax": self.in_climax,
                "post_climax": self.post_climax,
                "_last_climax_stim": self._last_climax_stim,
                "_resolved_at": self._resolved_at,
                "craving": self.craving,
                "loop_open": self.loop_open}

    @classmethod
    def from_state_dict(cls, d):
        """Restore from a state_dict snapshot. PRIVATE data."""
        a = cls(initial=d.get("level", 0.0),
                initial_satiation=d.get("satiation", 0.0))
        a.wanting = float(d.get("wanting", 0.0))
        a.in_climax = bool(d.get("in_climax", False))
        a.post_climax = bool(d.get("post_climax", False))
        a._last_climax_stim = float(d.get("_last_climax_stim", 0.0))
        a._resolved_at = float(d.get("_resolved_at", 0.0))
        a.craving = float(d.get("craving", 0.0))
        a.loop_open = bool(d.get("loop_open", False))
        return a


if __name__ == "__main__":
    a = Arousal()
    print("start:", a.level, "satiation:", a.satiation)
    print("pleasant touch:", a.update(0.8, 0.5), "sat:", round(a.satiation, 3))
    print("another:", a.update(0.8, 0.6), "sat:", round(a.satiation, 3))
    print("after 90s decay:", round(a.decay(90), 3),
          "sat:", round(a.satiation, 3))
    print("unpleasant:", a.update(-0.9, 0.7), "band:", a.band())
