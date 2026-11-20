#!/usr/bin/env python3
"""vfb.py — polite, cached client for the Virtual Fly Brain VFBquery HTTP API.

Every number this module returns comes from https://v3-cached.virtualflybrain.org/
(no login, no key). Responses are cached on disk so re-runs are free and the
shared service is hit as lightly as possible.
"""

import hashlib
import json
import os
import time
import urllib.parse
import urllib.request

BASE = "https://v3-cached.virtualflybrain.org"
CACHE_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "cache")
os.makedirs(CACHE_DIR, exist_ok=True)

_UA = {"User-Agent": "flybrain-sim-toy/1.0 (educational connectome toy)"}
_LAST_CALL = [0.0]
_MIN_GAP = 2.5  # be polite: well under 1 query/sec; service is flaky under load


def _cache_key(path, params):
    q = urllib.parse.urlencode(sorted(params.items()))
    return hashlib.sha1((path + "?" + q).encode()).hexdigest() + ".json"


def api_get(path, params, use_cache=True, retries=4):
    key = _cache_key(path, params)
    cpath = os.path.join(CACHE_DIR, key)
    if use_cache and os.path.exists(cpath):
        with open(cpath) as f:
            return json.load(f)
    url = BASE + path + "?" + urllib.parse.urlencode(params)
    last_err = None
    for attempt in range(retries):
        # politeness gap
        dt = time.time() - _LAST_CALL[0]
        if dt < _MIN_GAP:
            time.sleep(_MIN_GAP - dt)
        try:
            req = urllib.request.Request(url, headers=_UA)
            with urllib.request.urlopen(req, timeout=180) as r:
                data = json.load(r)
            _LAST_CALL[0] = time.time()
            with open(cpath, "w") as f:
                json.dump(data, f)
            return data
        except Exception as e:  # transient network/API flakiness: back off
            last_err = e
            _LAST_CALL[0] = time.time()
            time.sleep(3 * (attempt + 1))
    raise RuntimeError(f"api_get failed after {retries} tries: {url}: {last_err}")


def search(query, limit=10):
    res = api_get("/search", {"query": query, "limit": str(limit)})
    return res.get("rows", [])


def term_info(fbbt_id):
    return api_get("/get_term_info", {"id": fbbt_id})


def downstream_classes(upstream_label):
    """Class-aggregated synaptic connectivity downstream of one neuron type.

    Returns rows: downstream_class, downstream_class_id, total_weight
    (summed synapse count), pairwise_connections, average_weight, ...
    """
    res = api_get("/query_connectivity",
                  {"upstream_type": upstream_label, "group_by_class": "true"})
    return res.get("connections", [])


def named_downstream(fbbt_id, limit=50):
    """Slower named-query variant (kept as fallback)."""
    res = api_get("/run_query", {"id": fbbt_id,
                                 "query_type": "DownstreamClassConnectivity",
                                 "limit": str(limit)})
    return res.get("rows", [])
