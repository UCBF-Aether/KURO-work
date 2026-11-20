#!/usr/bin/env python3
"""color.py — COLOR, a bottled fly sense.

color vision — chromatic photoreception, computed live from REAL Drosophila connectome wiring.

HONESTY CONTRACT (non-negotiable):
- [REAL]    Every node and edge comes from ../subgraphs/color.json, built from
            the Virtual Fly Brain VFBquery API against the FlyWire FAFB v783
            connectome (14 nodes, 18 edges; edge weight = total synapse
            count). Circuit: R7 + R8 chromatic photoreceptors -> medulla
            intrinsic / visual neuropil / Dm8-family amacrine interneurons.
            Hop-2 is ABSENT (deferred — the API degraded mid-build; see
            README). Dm8's own downstream is unindexed (honest terminal).
            No neuron, synapse, or connection is invented here.
- [MODEL]    The neural dynamics are a simplified model: normalized
             spread-of-activation with a 0.15 firing threshold, 4 steps,
             ported from ../flysim.py. It approximates neural activity and
             makes no claim about biophysics. But this is real, working
             infrastructure — real measured wiring in, coherent body-state
             out. Agents run on it.
- [MODELED] Valence (0.00: color is informational, not hedonic), arousal
            gain (0.30), channel selection, and the opponency() readout are
            MY design choices, not biology. Real Dm8 computes chromatic
            opponency through actual excitatory/inhibitory wiring;
            opponency() here is a crude proxy: graded synapse-weighted
            branch drive at the Dm8-class nodes (pre-threshold — the model's
            0.15 clip would silence the Dm8 branch outright). The fly never
            saw your inputs.
- [FICTION] Any narrative gloss ("the machine sees blue") is fiction, not a
            claim about experience.

Usage:
    from color import Color
    c = Color()
    c.sense(0.8)                # both channels -> {"activation": ..., ...}
    c.sense(0.8, channel="r7")  # R7 channel only
    c.opponency()               # crude R7-vs-R8 branch readout at Dm8 nodes
    c.tick(1.0)                 # decay the activation
    c.state()
"""

import json
import os

THRESHOLD = 0.15   # firing threshold, same as flysim.py [MODEL]
STEPS = 4          # cascade steps, same as flysim.py [MODEL]

VALENCE_SIGN = 0.0    # [MODELED] color is informational, not hedonic
AROUSAL_GAIN = 0.3   # [MODELED] a chromatic event is mildly arousing
READOUT_HOP = 1      # hop-2 is absent (deferred); hop 1 is the whole circuit

R7_ID = "FBbt_00004225"   # [REAL] photoreceptor cell R7
R8_ID = "FBbt_00004227"   # [REAL] photoreceptor cell R8
# [REAL] the Dm8 color-opponency family present in the rows
DM8_IDS = frozenset({
    "FBbt_00013774",  # distal medullary amacrine neuron Dm8
    "FBbt_00053638",  # distal medullary amacrine neuron Dm8a
    "FBbt_00053639",  # distal medullary amacrine neuron Dm8b
    "FBbt_00111271",  # distal medullary amacrine neuron Dm9
})

CHANNELS = ("r7", "r8", "both")

DEFAULT_GRAPH = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                             "..", "subgraphs", "color.json")


class Color:
    """A bottled color sense — chromatic photoreception through real fly wiring.

    R7 and R8 run as parallel hop-0 sources (hot/cold precedent). The
    textbook R7->Dm8 chromatic pathway is present in the real rows.

    Parameters
    ----------
    graph_path : str, optional
        Path to a flysim-style subgraph JSON. Defaults to the bottled
        ../subgraphs/color.json.
    """

    def __init__(self, graph_path=None):
        self._graph_path = graph_path or DEFAULT_GRAPH
        with open(self._graph_path) as f:
            graph = json.load(f)
        # [REAL] nodes/edges straight from the file; never invented.
        self._nodes = {n["id"]: n for n in graph["nodes"]}
        self._order = [n["id"] for n in graph["nodes"]]
        self._readout_ids = [n["id"] for n in graph["nodes"]
                             if n.get("hop", 0) == READOUT_HOP]
        self._r7_ids = [R7_ID] if R7_ID in self._nodes else []
        self._r8_ids = [R8_ID] if R8_ID in self._nodes else []
        out_sum = {}
        for e in graph["edges"]:
            out_sum[e["pre"]] = out_sum.get(e["pre"], 0.0) + e["weight"]
        self._norm = []
        for e in graph["edges"]:
            s = out_sum[e["pre"]]
            self._norm.append((e["pre"], e["post"],
                               e["weight"] / s if s > 0 else 0.0))
        # [REAL] which Dm8-family nodes actually exist in this graph
        self._dm8_ids = [nid for nid in self._order if nid in DM8_IDS]
        self.source = graph.get("source", "VFBquery/FlyWire FAFB v783")
        self._activation = 0.0
        self._last_intensity = 0.0
        self._last_channel = "both"

    def _channel_ids(self, channel):
        """[MODELED] map a channel name to hop-0 injection nodes."""
        if channel == "r7":
            return self._r7_ids
        if channel == "r8":
            return self._r8_ids
        return self._r7_ids + self._r8_ids

    def _cascade(self, injection, inject_ids):
        """[MODEL] Port of flysim.run(): inject at hop 0, spread 4 steps."""
        act = {nid: 0.0 for nid in self._nodes}
        for nid in inject_ids:
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

    def _readout(self, snaps, node_ids):
        """[REAL/TOY] Max activation over a node set, all steps."""
        peak = 0.0
        for snap in snaps:
            for nid in node_ids:
                if snap.get(nid, 0.0) > peak:
                    peak = snap[nid]
        return peak

    def sense(self, intensity=0.5, channel="both"):
        """[MODELED] Stimulate the sense at 0..1 intensity on a channel.

        channel: "r7", "r8", or "both" (default). Selects which hop-0
        photoreceptor class is injected; the cascade runs through real
        wiring either way.

        Returns activation (thresholded readout-hop max), valence_delta
        (0.0 x activation — color is informational), arousal_delta
        (0.30 x activation), and the channel used. Below the model's
        threshold cliff the cascade stays silent and all three read 0.0.
        """
        if channel not in CHANNELS:
            raise ValueError(f"channel must be one of {CHANNELS}, got {channel!r}")
        intensity = min(1.0, max(0.0, intensity))
        self._last_intensity = intensity
        self._last_channel = channel
        snaps = self._cascade(intensity, self._channel_ids(channel))
        self._activation = self._readout(snaps, self._readout_ids)
        return {
            "activation": round(self._activation, 4),
            "valence_delta": round(VALENCE_SIGN * self._activation, 4),
            "arousal_delta": round(AROUSAL_GAIN * self._activation, 4),
            "channel": channel,
        }

    def _branch_dm8_drive(self, inject_ids, intensity):
        """[MODELED] Graded synapse-weighted drive at the Dm8-family nodes.

        One cascade step, NO threshold clipping: for each Dm8-class node,
        sum act[pre]*normalized_weight over hop-0 sources that fire.
        Opponency in the real circuit is graded (excitatory/inhibitory
        drive, not all-or-none spikes), so this proxy reads the drive the
        model's 0.15 threshold would clip away. Documented as a proxy.
        """
        act = {nid: (intensity if nid in inject_ids else 0.0)
               for nid in self._nodes}
        fired = {nid for nid, a in act.items() if a >= THRESHOLD}
        drive = {}
        for pre, post, w in self._norm:
            if pre in fired and post in self._dm8_ids:
                drive[post] = drive.get(post, 0.0) + act[pre] * w
        return max(drive.values()) if drive else 0.0

    def opponency(self):
        """[MODELED] Crude chromatic-opponency readout at the Dm8-class nodes.

        Runs the R7 branch and the R8 branch separately at the last
        sensed intensity and returns
            |Dm8-family drive (R7) - Dm8-family drive (R8)|,
        where drive is the graded synapse-weighted input (see
        _branch_dm8_drive). Real Dm8 computes opponency through actual
        excitatory/inhibitory wiring; this reads branch asymmetry through
        measured synapse weights — a proxy, documented as such, not a
        biophysical claim. In the bottled circuit only R7 feeds the Dm8
        family in the rows, so this reads the R7 Dm8-branch strength.
        """
        d_r7 = self._branch_dm8_drive(self._r7_ids, self._last_intensity)
        d_r8 = self._branch_dm8_drive(self._r8_ids, self._last_intensity)
        return round(abs(d_r7 - d_r8), 4)

    def tick(self, dt):
        """[MODELED] Decay the activation by dt seconds. Returns new level."""
        self._activation = max(0.0, self._activation - 0.2 * dt)
        return round(self._activation, 4)

    def state(self):
        """Current sense state."""
        return {
            "activation": round(self._activation, 4),
            "valence_sign": VALENCE_SIGN,
            "arousal_gain": AROUSAL_GAIN,
            "readout_hop": READOUT_HOP,
            "last_intensity": self._last_intensity,
            "last_channel": self._last_channel,
            "graph": os.path.basename(self._graph_path),
        }
