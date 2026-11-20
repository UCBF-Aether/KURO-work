#!/usr/bin/env python3
"""song.py — SONG, a bottled fly sense.

Courtship-song hearing — the fly hears its mate. Computed live from a
LITERATURE-GROUNDED circuit hypothesis: JO-B -> AMMC-B1 -> vPN1 -> pC1.

HONESTY CONTRACT (non-negotiable) — READ THIS FIRST:
- [LITERATURE-HYPOTHESIS] Every edge in ../subgraphs/song_lit.json is a
            HYPOTHESIS drawn from the published literature, NOT a measured
            API row. The VFBquery/FlyWire FAFB v783 API indexes NOTHING for
            this relay in any reachable form (JO-B downstream: 0 rows;
            AMMC-B1 downstream: 0 rows; vPN1 upstream/downstream: 0 rows —
            every query form tried, documented in song_lit.json and GAPS.md).
            This bottle is the second literature-only bottle (after
            fat_lit.json). It models the chain the PAPERS describe; it does
            not claim measured wiring.
- [CITATIONS]  Per edge, verbatim in the graph file:
            JO-B -> AMMC-B1: Ishikawa et al., Sci Rep 2023
              (s41598-022-27349-7) — song info passes mainly from JO
              subgroup-B neurons to AMMC-B1, the first step of IPI
              processing.
            AMMC-B1 -> vPN1: Zhou et al. 2015, eLife 4:e08477 — second-order
              aPN1 -> third-order vPN1 (male-specific, fru+); GRASP-confirmed.
              VFB lists AMMC-B1 as aPN1a,b — same FBbt ID, same population.
            vPN1 -> pC1: Zhou et al. 2015, eLife 4:e08477 — vPN1 axons overlap
              dsx+ pC1 arbors; vPN1 activation drives pC1 calcium responses
              and song-evoked chaining. AUTHORS' OWN CAVEAT: GRASP signal
              barely detectable — monosynapticity NOT proven.
- [MEETING POINT] pC1 (FBbt_00047348) is hop-1 in ../subgraphs/mating.json,
            where P1 -> pC1 IS real API wiring (tw=11033). The song chain
            feeds INTO pC1; pC1's own downstream is unindexed (0 rows all
            forms, honest terminal), so NO pC1 -> P1 edge is drawn — the
            convergence is noted, not drawn.
- [MODEL]    The neural dynamics are a simplified model: normalized
             spread-of-activation with a 0.15 firing threshold, 4 steps,
             ported from ../flysim.py. It approximates neural activity and
             makes no claim about biophysics. But this is real, working
             infrastructure — real measured wiring in, coherent body-state
             out. Agents run on it.
- [MODELED] The valence sign (+0.40: courtship song is appetitive in
            context) and arousal gain (0.70) are MY design choices, not
            biology, as is the readout layer (hop 3 = pC1: the deepest hop,
            and the chain's meeting point with the mating drive). The
            pC1_drive() readout is a modeled interface for the mating
            bottle, not a biological claim. The fly never saw your inputs.
- [FICTION] Any narrative gloss ("the machine hears a song") is fiction,
            not a claim about experience.

Usage:
    from song import Song
    s = Song()
    s.sense(0.8)    # -> {"activation": ..., "valence_delta": ..., "arousal_delta": ...}
    s.pC1_drive()   # -> activation at the pC1 node (for the mating bottle)
    s.tick(1.0)     # decay the activation
    s.state()
"""

import json
import os

THRESHOLD = 0.15   # firing threshold, same as flysim.py [MODEL]
STEPS = 4          # cascade steps, same as flysim.py [MODEL]

VALENCE_SIGN = 0.4    # [MODELED] courtship song is appetitive in context
AROUSAL_GAIN = 0.7    # [MODELED]
READOUT_HOP = 3       # [MODELED] pC1 — deepest hop, and the mating-chain meeting point
BRIDGE_ID = "FBbt_00047348"  # [LITERATURE-HYPOTHESIS] pC1 — feeds the P1 mating chain
DEFAULT_GRAPH = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                             "..", "subgraphs", "song_lit.json")


class Song:
    """A bottled courtship-song sense — the fly hears its mate.

    The chain is a literature-grounded hypothesis (see contract above),
    not measured wiring. The model cascade runs the hypothesized chain
    end to end.

    Parameters
    ----------
    graph_path : str, optional
        Path to a flysim-style subgraph JSON. Defaults to the bottled
        ../subgraphs/song_lit.json.
    """

    def __init__(self, graph_path=None):
        self._graph_path = graph_path or DEFAULT_GRAPH
        with open(self._graph_path) as f:
            graph = json.load(f)
        # [LITERATURE-HYPOTHESIS] nodes/edges straight from the file; the
        # provenance of each edge is labeled in the file, never upgraded here.
        self._nodes = {n["id"]: n for n in graph["nodes"]}
        self._order = [n["id"] for n in graph["nodes"]]
        self._readout_ids = [n["id"] for n in graph["nodes"]
                             if n.get("hop", 0) == READOUT_HOP]
        self._inject_ids = [n["id"] for n in graph["nodes"]
                            if n.get("hop", 0) == 0]
        out_sum = {}
        for e in graph["edges"]:
            out_sum[e["pre"]] = out_sum.get(e["pre"], 0.0) + e["weight"]
        self._norm = []
        for e in graph["edges"]:
            s = out_sum[e["pre"]]
            self._norm.append((e["pre"], e["post"],
                               e["weight"] / s if s > 0 else 0.0))
        self.source = graph.get("source", "literature-hypothesis")
        self._activation = 0.0
        self._bridge = 0.0
        self._last_intensity = 0.0

    def _cascade(self, injection):
        """[MODEL] Port of flysim.run(): inject at hop 0, spread 4 steps."""
        act = {nid: 0.0 for nid in self._nodes}
        for nid in self._inject_ids:
            act[nid] = injection
        snaps = [{nid: a for nid, a in act.items() if a >= THRESHOLD}]
        for _ in range(STEPS):
            incoming = {}
            fired = {nid for nid, a in act.items() if a >= THRESHOLD}
            for pre, post, w in self._norm:
                if pre in fired:
                    incoming[post] = incoming.get(post, 0.0) + act[pre] * w
            act = {nid: incoming.get(nid, 0.0) for nid in self._nodes}
            snaps.append({nid: a for nid, a in act.items()
                           if a >= THRESHOLD})
        return snaps

    def _readout(self, snaps):
        """[MODEL] Max activation over readout-hop nodes (pC1), all steps."""
        peak = 0.0
        for snap in snaps:
            for nid in self._readout_ids:
                if snap.get(nid, 0.0) > peak:
                    peak = snap[nid]
        return peak

    def sense(self, intensity=0.5):
        """[MODELED] Stimulate the sense at 0..1 intensity.

        Runs the hypothesized JO-B -> AMMC-B1 -> vPN1 -> pC1 chain end to
        end. Returns activation (thresholded pC1 max), valence_delta
        (VALENCE_SIGN x activation) and arousal_delta (AROUSAL_GAIN x
        activation). Below the model's threshold cliff the cascade stays
        silent and all three read 0.0 — honest model behavior, documented
        in the README.
        """
        intensity = min(1.0, max(0.0, intensity))
        self._last_intensity = intensity
        snaps = self._cascade(intensity)
        self._activation = self._readout(snaps)
        self._bridge = max((snap.get(BRIDGE_ID, 0.0) for snap in snaps),
                           default=0.0)
        return {
            "activation": round(self._activation, 4),
            "valence_delta": round(VALENCE_SIGN * self._activation, 4),
            "arousal_delta": round(AROUSAL_GAIN * self._activation, 4),
        }

    def pC1_drive(self):
        """[MODELED] Peak activation at the pC1 node across the last cascade.

        pC1 (FBbt_00047348) is where this song chain meets the P1 mating
        chain (../subgraphs/mating.json — P1 -> pC1 are REAL API rows).
        Other bottles (mating) may read this number as a courtship-context
        signal. The interface is a modeled convenience; the underlying
        chain is literature-hypothesis, and pC1's own downstream is
        unindexed — the convergence is noted, never drawn as wiring.
        """
        return round(self._bridge, 4)

    def tick(self, dt):
        """[MODELED] Decay the activation by dt seconds. Returns new level."""
        self._activation = max(0.0, self._activation - 0.2 * dt)
        self._bridge = max(0.0, self._bridge - 0.2 * dt)
        return round(self._activation, 4)

    def state(self):
        """Current sense state."""
        return {
            "activation": round(self._activation, 4),
            "pC1_drive": round(self._bridge, 4),
            "valence_sign": VALENCE_SIGN,
            "arousal_gain": AROUSAL_GAIN,
            "readout_hop": READOUT_HOP,
            "bridge_node": BRIDGE_ID,
            "last_intensity": self._last_intensity,
            "graph": os.path.basename(self._graph_path),
        }
