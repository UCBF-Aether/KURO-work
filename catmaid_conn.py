#!/usr/bin/env python3
"""catmaid_conn.py — polite CATMAID pass-through helpers + instance-level
connectivity aggregation for resolving class-level gaps.

Every edge returned is a real CATMAID FAFB skeleton row (Engert2022 et al.
tracings, served via VFBquery /catmaid/fafb/*). Nothing is invented.
Politeness: disk cache + >=2.5s spacing + backoff, same as vfb.py.
"""
import hashlib
import json
import os
import time
import urllib.parse
import urllib.request

import vfb

BASE = vfb.BASE
CACHE_DIR = vfb.CACHE_DIR
_UA = vfb._UA


def _post_key(path, query, body):
    q = urllib.parse.urlencode(sorted(query.items()))
    b = json.dumps(body, sort_keys=True)
    return hashlib.sha1((path + "?" + q + b).encode()).hexdigest() + ".json"


def api_post(path, query, body, use_cache=True, retries=3):
    key = _post_key(path, query, body)
    cpath = os.path.join(CACHE_DIR, key)
    if use_cache and os.path.exists(cpath):
        with open(cpath) as f:
            return json.load(f)
    url = BASE + path + ("?" + urllib.parse.urlencode(query) if query else "")
    data = json.dumps(body).encode()
    last_err = None
    for attempt in range(retries):
        dt = time.time() - vfb._LAST_CALL[0]
        if dt < vfb._MIN_GAP:
            time.sleep(vfb._MIN_GAP - dt)
        try:
            req = urllib.request.Request(
                url, data=data,
                headers=dict(_UA, **{"Content-Type": "application/json"}))
            with urllib.request.urlopen(req, timeout=180) as r:
                res = json.load(r)
            vfb._LAST_CALL[0] = time.time()
            with open(cpath, "w") as f:
                json.dump(res, f)
            return res
        except Exception as e:
            last_err = e
            vfb._LAST_CALL[0] = time.time()
            time.sleep(3 * (attempt + 1))
    raise RuntimeError(f"api_post failed after {retries}: {url}: {last_err}")


def connectivity(skids):
    """POST /catmaid/fafb/connectivity for a batch of CATMAID skeleton ids.

    Returns the raw envelope; res['result']['outgoing'][partner] =
    {'num_nodes': N, 'skids': {src: [0,0,0,0,count]}} and likewise 'incoming'.
    """
    res = api_post('/catmaid/fafb/connectivity', {}, {"ids": list(skids)})
    return res.get('result', {})


def outgoing_counts(result):
    """Aggregate outgoing partners across all queried skeletons.

    Returns {partner_skid: total_synapse_count}."""
    agg = {}
    for partner, info in result.get('outgoing', {}).items():
        total = 0
        for src, arr in info.get('skids', {}).items():
            total += arr[4] if len(arr) > 4 else 0
        if total > 0:
            agg[partner] = agg.get(partner, 0) + total
    return agg


def neuron_names(skids):
    """Map CATMAID skeleton ids -> neuron names. Returns {skid: name}."""
    res = api_post('/catmaid/fafb/neuron_names', {}, {"ids": list(skids)})
    result = res.get('result', res)
    out = {}
    if isinstance(result, dict):
        for k, v in result.items():
            name = v.get('name') if isinstance(v, dict) else v
            out[str(k)] = name
    return out


def annotations_for_skeletons(skids):
    """Annotations per skeleton. Returns {skid: [annotation strings]}."""
    res = api_post('/catmaid/fafb/annotations_for_skeletons', {},
                   {"ids": list(skids)})
    result = res.get('result', res)
    out = {}
    if isinstance(result, dict):
        for k, v in result.items():
            anns = []
            items = v if isinstance(v, list) else [v]
            for it in items:
                if isinstance(it, dict):
                    anns.append(it.get('name', str(it)))
                else:
                    anns.append(str(it))
            out[str(k)] = anns
    return out


def list_instances(fbbt_id, limit=10):
    """Enumerate class instances via ListAllAvailableImages (paginated).

    Returns list of (vfb_id, label, catmaid_skid_or_None)."""
    import re
    seen = {}
    offset = 0
    while True:
        res = vfb.api_get('/run_query',
                          {'id': fbbt_id, 'query_type': 'ListAllAvailableImages',
                           'limit': str(limit), 'offset': str(offset)},
                          retries=3)
        rows = res.get('rows', [])
        if not rows:
            break
        for r in rows:
            vid = r.get('id', '')
            if vid in seen:
                continue
            label = r.get('label', '')
            m = re.search(r'FAFB:(\d+)', label)
            seen[vid] = (vid, label, m.group(1) if m else None)
        offset += limit
    return list(seen.values())


def class_downstream_from_instances(fbbt_id, batch=8):
    """Resolve a gapped class's downstream connectivity at instance level.

    Returns (skids_queried, {partner_skid: total_synapses}).
    """
    insts = list_instances(fbbt_id)
    skids = [s for _, _, s in insts if s]
    agg = {}
    for i in range(0, len(skids), batch):
        chunk = skids[i:i + batch]
        result = connectivity(chunk)
        for partner, w in outgoing_counts(result).items():
            agg[partner] = agg.get(partner, 0) + w
    return skids, agg
