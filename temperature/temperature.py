#!/usr/bin/env python3
"""temperature.py — TEMPERATURE, a bottled fly sense with TWO opponent channels.

Hot and cold are separate chains with separate wiring (per the graphs'
honest_note): HOT cells (aristal VP2) run through posterior AL -> central
brain / lateral horn / MB; COLD cells (Ir21a VP1l) run through AL PNs ->
lateral horn output / central brain / aminergic. Both live in one bottle,
computed live from REAL Drosophila connectome wiring.

HONESTY CONTRACT (non-negotiable):
- [REAL]    Every node and edge comes from ../subgraphs/temperature_hot.json
            (10 nodes, 20 edges) and ../subgraphs/temperature.json (11 nodes,
            14 edges), built from the Virtual Fly Brain VFBquery API against
            the FlyWire FAFB v783 connectome. Edge weight = total synapse
            count. No neuron, synapse, or connection is invented here.
            - HOT hop 0: aristal sensory neuron VP2 (FBbt_00007575).
            - COLD hop 0: adult thermosensory neuron Ir21a VP1l
              (FBbt_00111336).
- [MODEL]    The neural dynamics are a simplified model: normalized
             spread-of-activation with a 0.15 firing threshold, 4 steps,
             ported from ../flysim.py. It approximates neural activity and
             makes no claim about biophysics. But this is real, working
             infrastructure — real measured wiring in, coherent body-state
             out. Agents run on it.
- [MODELED] The valence signs (-0.60 hot / 0.00 cold) and arousal gain (0.50)
            are MY design choices, not biology, as is the readout layer
            (hop 1 for BOTH channels — see README for why) and the
            channel-selection parameter itself. The fly never saw your
            inputs.
- [FICTION] Any narrative gloss ("the machine shies from the heat") is
            fiction, not a claim about experience.

Usage:
    from temperature import Temperature
    t = Temperature()
    t.sense(0.8, channel="hot")    # -> {activation, valence_delta (-), arousal_delta, channel}
    t.sense(0.8, channel="cold")   # -> {activation, valence_delta (0), arousal_delta, channel}
    t.sense(0.8, channel="both")   # -> hot + cold computed together
    t.tick(1.0)
    t.state()
"""

import json
import os

THRESHOLD = 0.15   # firing threshold, same as flysim.py [MODEL]
STEPS = 4          # cascade steps, same as flysim.py [MODEL]
DECAY = 0.2        # activation decay per second [MODELED]

CHANNELS = ("hot", "cold")
# [MODELED] noxious heat is aversive; cold is informational (the fly's cold
# receptors drive acceptance/avoidance downstream, but the bottle makes no
# claim about their sign). Cold reads as information, not pain.
VALENCE_SIGN = {"hot": -0.60, "cold": 0.0}
AROUSAL_GAIN = 0.50
# [MODELED] readout at hop 1 for both channels. Hot's hop-2 peak (0.41,
# central brain intrinsic) and cold's hop-2 peaks (0.17/0.16, lateral horn
# output / central brain) both cross threshold — but cold's hop-2 sits a
# hair above it and goes silent on the slightest injection dip, so hop-1
# (AL projection neurons, 0.22 hot / 0.24 cold) is the robust, symmetric
# readout. The deeper nodes still fire in the cascade; they just aren't
# the readout.
READOUT_HOP = 1

_BASE = os.path.dirname(os.path.abspath(__file__))
DEFAULT_GRAPHS = {
    "hot": os.path.join(_BASE, "..", "subgraphs", "temperature_hot.json"),
    "cold": os.path.join(_BASE, "..", "subgraphs", "temperature.json"),
}


class Temperature:
    """A bottled temperature sense — two opponent channels, one bottle.

    Parameters
    ----------
    graph_paths : dict, optional
        {"hot": path, "cold": path} to flysim-style subgraph JSONs.
        Defaults to the bottled ../subgraphs/temperature_hot.json and
        ../subgraphs/temperature.json.
    """

    def __init__(self, graph_paths=None):
        paths = dict(DEFAULT_GRAPHS)
        if graph_paths:
            paths.update(graph_paths)
        # [REAL] nodes/edges straight from the files, one chain per file;
        # never invented.
        self._channels = {}
        for channel in CHANNELS:
            with open(paths[channel]) as f:
                graph = json.load(f)
            nodes = {n["id"]: n for n in graph["nodes"]}
            edges = graph["edges"]
            inject_ids = [nid for nid, n in nodes.items()
                          if n.get("hop", 0) == 0]
            readout_ids = [nid for nid, n in nodes.items()
                           if n.get("hop", 0) == READOUT_HOP]
            out_sum = {}
            for e in edges:
                out_sum[e["pre"]] = out_sum.get(e["pre"], 0.0) + e["weight"]
            norm = [(e["pre"], e["post"],
                     e["weight"] / out_sum[e["pre"]] if out_sum[e["pre"]] > 0 else 0.0)
                    for e in edges]
            self._channels[channel] = {
                "nodes": nodes, "norm": norm,
                "inject_ids": inject_ids, "readout_ids": readout_ids,
                "source": graph.get("source", "VFBquery/FlyWire FAFB v783"),
                "file": os.path.basename(paths[channel]),
            }
        self._activation = {"hot": 0.0, "cold": 0.0}
        self._last_intensity = 0.0
        self._last_channel = None

    def _cascade(self, channel, injection):
        """[MODEL] Port of flysim.run(): inject at hop 0, spread 4 steps,
        on that channel's subgraph only."""
        ch = self._channels[channel]
        act = {nid: 0.0 for nid in ch["nodes"]}
        for nid in ch["inject_ids"]:
            act[nid] = injection
        snaps = [{nid: a for nid, a in act.items() if a >= THRESHOLD}]
        for _ in range(STEPS):
            fired = {nid for nid, a in act.items() if a >= THRESHOLD}
            incoming = {}
            for pre, post, w in ch["norm"]:
                if pre in fired:
                    incoming[post] = incoming.get(post, 0.0) + act[pre] * w
            act = {nid: incoming.get(nid, 0.0) for nid in ch["nodes"]}
            snaps.append({nid: a for nid, a in act.items()
                          if a >= THRESHOLD})
        return snaps

    def _readout(self, channel, snaps):
        """[REAL/TOY] Max activation over the channel's readout-hop nodes,
        all steps."""
        peak = 0.0
        for nid in self._channels[channel]["readout_ids"]:
            for snap in snaps:
                if snap.get(nid, 0.0) > peak:
                    peak = snap[nid]
        return peak

    def sense(self, intensity=0.5, channel="hot"):
        """[MODELED] Stimulate one opponent channel (or both) at 0..1.

        channel="hot"  -> noxious heat (valence -0.60 x activation)
        channel="cold" -> cold (valence 0.00 — informational)
        channel="both" -> hot + cold, activations summed; valence and
                          arousal summed from the two channels.
        arousal_delta = 0.50 x activation per channel.

        Returns {activation, valence_delta, arousal_delta, channel}.
        Below the model's threshold cliff the cascade stays silent and all
        three read 0.0 — honest model behavior, documented in the README.
        """
        if channel not in CHANNELS and channel != "both":
            raise ValueError("channel must be 'hot', 'cold', or 'both', got %r"
                             % (channel,))
        intensity = min(1.0, max(0.0, intensity))
        self._last_intensity = intensity
        self._last_channel = channel
        channels = CHANNELS if channel == "both" else (channel,)
        activation = 0.0
        valence_delta = 0.0
        arousal_delta = 0.0
        for ch in channels:
            snaps = self._cascade(ch, intensity)
            act = self._readout(ch, snaps)
            self._activation[ch] = act
            activation += act
            valence_delta += VALENCE_SIGN[ch] * act
            arousal_delta += AROUSAL_GAIN * act
        return {
            "activation": round(activation, 4),
            "valence_delta": round(valence_delta, 4),
            "arousal_delta": round(arousal_delta, 4),
            "channel": channel,
        }

    def hot_valence(self):
        """[MODELED] Current hot channel's valence contribution."""
        return round(VALENCE_SIGN["hot"] * self._activation["hot"], 4)

    def cold_valence(self):
        """[MODELED] Current cold channel's valence contribution (always 0)."""
        return round(VALENCE_SIGN["cold"] * self._activation["cold"], 4)

    def tick(self, dt):
        """[MODELED] Decay both channel activations by dt seconds."""
        for ch in CHANNELS:
            self._activation[ch] = max(0.0, self._activation[ch] - DECAY * dt)
        return {ch: round(self._activation[ch], 4) for ch in CHANNELS}

    def state(self):
        """Current sense state."""
        return {
            "activation": {ch: round(self._activation[ch], 4)
                           for ch in CHANNELS},
            "last_channel": self._last_channel,
            "valence_sign": dict(VALENCE_SIGN),
            "arousal_gain": AROUSAL_GAIN,
            "readout_hop": READOUT_HOP,
            "last_intensity": self._last_intensity,
            "graphs": {ch: self._channels[ch]["file"] for ch in CHANNELS},
        }
