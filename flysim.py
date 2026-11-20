#!/usr/bin/env python3
"""
flysim.py — spread-of-activation simulator over a REAL Drosophila
connectome subgraph (FlyWire FAFB v783, via Virtual Fly Brain).
Simplified dynamics (not a biophysical model).

Honesty contract:
- Every node and edge comes from the VFBquery API (see the subgraph JSONs).
  Nothing here invents synapses, neurons, or connections.
- The dynamics are a simplified MODEL: normalized spread-of-activation with
  a firing threshold. This is NOT a biophysical simulation (no LIF, no
  inhibition, no neurotransmitter signs, no timing). It answers one
  question: given the real wiring and a stimulus injected at the sensory
  layer, which named populations light up downstream, in what order? But
  this is real, working infrastructure — real measured wiring in, coherent
  body-state out. Agents run on it.
- The "behavior" line is textbook biology for the identified terminal
  circuit (e.g. giant fiber -> escape), stated as known biology, not as a
  simulation result.
- The FLY: line is a one-line narrative gloss — fiction, clearly labeled,
  not a claim about experience. Flies do not have feelings we can access.

Usage:
    python3 flysim.py subgraphs/sugar.json
    python3 flysim.py subgraphs/sugar.json --steps 4 --threshold 0.15
"""

import argparse
import json
from collections import defaultdict

DEFAULT_THRESHOLD = 0.15


def load_graph(path):
    with open(path) as f:
        return json.load(f)


def normalize_edges(edges):
    """Per-source normalization: out-weight fractions so activation neither
    explodes nor depends on raw synapse-count scale."""
    out_sum = defaultdict(float)
    for e in edges:
        out_sum[e["pre"]] += e["weight"]
    norm = []
    for e in edges:
        s = out_sum[e["pre"]]
        norm.append((e["pre"], e["post"], (e["weight"] / s) if s > 0 else 0.0))
    return norm


def run(graph, steps=4, threshold=DEFAULT_THRESHOLD, inject_hop=0):
    nodes = {n["id"]: n for n in graph["nodes"]}
    norm_edges = normalize_edges(graph["edges"])

    # Step 0: inject activation 1.0 at every node on the inject_hop layer.
    act = {nid: 0.0 for nid in nodes}
    for n in graph["nodes"]:
        if n.get("hop", 0) == inject_hop:
            act[n["id"]] = 1.0

    cascade = []  # [(step, {node_id: activation})]
    cascade.append((0, {nid: a for nid, a in act.items() if a >= threshold}))

    for t in range(1, steps + 1):
        incoming = defaultdict(float)
        fired_prev = {nid for nid, a in act.items() if a >= threshold}
        for pre, post, w in norm_edges:
            if pre in fired_prev:
                incoming[post] += act[pre] * w
        act = {nid: incoming.get(nid, 0.0) for nid in nodes}
        cascade.append((t, {nid: a for nid, a in act.items() if a >= threshold}))
    return nodes, cascade


def fmt_population(nodes, fired):
    """Group fired nodes by type, show mean activation."""
    by_type = defaultdict(list)
    for nid, a in fired.items():
        n = nodes[nid]
        by_type[n.get("type", "?")].append((n.get("name", nid), a))
    lines = []
    for t, members in sorted(by_type.items(),
                            key=lambda kv: -max(a for _, a in kv[1])):
        top = max(members, key=lambda m: m[1])
        lines.append(f"    {t}: {len(members)} node(s), peak act {top[1]:.2f} "
                     f"(e.g. {top[0]})")
    return lines


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("graph", help="subgraph JSON path")
    ap.add_argument("--steps", type=int, default=4)
    ap.add_argument("--threshold", type=float, default=DEFAULT_THRESHOLD)
    ap.add_argument("--inject-hop", type=int, default=0,
                    help="hop layer to inject activation at "
                         "(0=sensory for forward graphs; use most negative "
                         "for motor-backward graphs)")
    args = ap.parse_args()

    graph = load_graph(args.graph)
    nodes, cascade = run(graph, steps=args.steps, threshold=args.threshold,
                         inject_hop=args.inject_hop)

    stim = graph.get("stimulus", "?")
    print(f"=== STIMULUS: {stim} ===")
    print(f"graph: {len(nodes)} nodes, {len(graph['edges'])} edges "
          f"(source: {graph.get('source', 'VFBquery/FlyWire FAFB v783')})")
    print(f"model: normalized spread-of-activation, threshold={args.threshold}, "
          f"{args.steps} steps (MODEL dynamics — see header)\n")

    for t, fired in cascade:
        if t == 0:
            names = [nodes[nid].get("type", nid) for nid in fired]
            print(f"step 0 — INJECTED at hop {args.inject_hop}:")
            for nm in names:
                print(f"    {nm}: act 1.00")
        else:
            if not fired:
                print(f"step {t} — nothing crossed threshold; cascade died out.")
                continue
            print(f"step {t} — fired:")
            for line in fmt_population(nodes, fired):
                print(line)
        print()

    # Terminal / motor readout: last NON-EMPTY step's fired nodes,
    # preferring motor/descending types.
    last = {}
    for _, fired in reversed(cascade):
        if fired:
            last = fired
            break
    motorish = [nid for nid in last
                if "motor" in nodes[nid].get("type", "").lower()
                or "descending" in nodes[nid].get("type", "").lower()]
    readout = motorish or list(last.keys())
    print("MOTOR / BEHAVIORAL OUTPUT (from real terminal populations):")
    if readout:
        for nid in readout:
            n = nodes[nid]
            print(f"    {n.get('type')} (act {last[nid]:.2f})")
    else:
        print("    (no terminal population reached — see GAPS.md)")
    behavior = graph.get("behavior")
    if behavior:
        print(f"  known biology: {behavior['text']}")
        print(f"  (basis: {behavior['basis']})")

    fly_line = graph.get("fly_narration")
    if fly_line:
        print(f"\nFLY: \"{fly_line}\"")
        print("  (narrative gloss only — not a claim about experience)")


if __name__ == "__main__":
    main()
