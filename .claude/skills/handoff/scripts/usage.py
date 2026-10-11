#!/usr/bin/env python3
"""Estimate the 5-hour and 7-day usage windows from the transcripts, where no status line runs.

Claude Code gives the live usage of the windows to a status-line command only
(statusline.py, beside it), and the VS Code panel runs none: there, the hooks never see a reading and
the handoff warning never fires. The transcripts hold what is needed to estimate it:

  - every model call's tokens, in every project's transcripts and its agents' (all of them draw on
    the same windows); weighted at list price, they make a cost in dollars;
  - every rejection at a limit (`quotaLimits`: the window, and when it resets). A rejection marks a
    window spent in full, so the cost inside it, from the window's start to the rejection, is that
    window's cap. Caps drift with the model mix, so the estimate uses the last few.

The window's own start is the first call after the last one ended, rounded down to ten minutes
(a known reset, when one is on file, wins); the 7-day window is anchored on its last known reset
and rolls on a week at a time. Usage outside these transcripts (claude.ai, another machine) is
invisible, so the cap is taken low: the smallest of the recent caps, outliers below half their
median left out. The estimate errs early.

Each scan reads only what a transcript gained since the last one (docs/sessions/usage-cache.json).
`estimate()` writes docs/sessions/usage-estimate.json, in the status line's shape plus
`"source": "estimate"`, and reuses it for MAX_AGE_S.

Usage:
  usage.py                 the estimate per window, and the caps it rests on
  usage.py --rebuild       forget the cache and rescan every transcript
"""
import argparse
import datetime as dt
import glob
import json
import os
import statistics
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import checkpoint  # noqa: E402

PROJECTS = os.path.join(os.environ.get("CLAUDE_CONFIG_DIR") or os.path.expanduser("~/.claude"),
                        "projects")
CACHE = "usage-cache.json"
ESTIMATE = "usage-estimate.json"
MAX_AGE_S = 60
KEEP_S = 8 * 86400                  # calls older than the longest window are dropped
SPAN_S = {"five_hour": 5 * 3600, "seven_day": 7 * 86400}
ROUND_S = 600                       # a 5-hour window starts on a ten-minute mark
RECENT_CAPS = 4
KEPT_CAPS = 12
# list price per million tokens: input, output. Cache writes cost 1.25x input (5 min) or 2x (1 h),
# cache reads 0.1x. An unknown family (synthetic rows) costs nothing.
PRICE = (("opus", 5, 25), ("fable", 5, 25), ("sonnet", 3, 15), ("haiku", 1, 5))


def cost(model, usage):
    """One call's cost in dollars at list price."""
    model = model or ""
    rate = next(((i, o) for fam, i, o in PRICE if fam in model), None)
    if not rate or not isinstance(usage, dict):
        return 0.0
    i, o = rate
    num = lambda k: usage.get(k) if isinstance(usage.get(k), (int, float)) else 0  # noqa: E731
    split = usage.get("cache_creation") if isinstance(usage.get("cache_creation"), dict) else {}
    hour = split.get("ephemeral_1h_input_tokens") or 0
    five = max(num("cache_creation_input_tokens") - hour, 0)
    return (num("input_tokens") * i + five * i * 1.25 + hour * i * 2
            + num("cache_read_input_tokens") * i * 0.1 + num("output_tokens") * o) / 1e6


def transcripts(projects):
    return (glob.glob(os.path.join(projects, "*", "*.jsonl"))
            + glob.glob(os.path.join(projects, "*", "*", "subagents", "*.jsonl")))


def _load(path):
    try:
        with open(path, encoding="utf-8") as fh:
            data = json.load(fh)
    except (OSError, ValueError):
        return None
    return data if isinstance(data, dict) else None


def _save(path, data):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    tmp = "%s.%d.tmp" % (path, os.getpid())
    with open(tmp, "w", encoding="utf-8") as fh:
        json.dump(data, fh)
    os.replace(tmp, path)


def _empty():
    return {"files": {}, "calls": {}, "rejects": {}, "caps": {k: {} for k in SPAN_S}}


def _read_new(path, offset):
    """The complete lines a file gained past `offset`, and the offset after them."""
    try:
        size = os.path.getsize(path)
    except OSError:
        return [], offset
    if size < offset:                               # rewritten: read it again
        offset = 0
    if size == offset:
        return [], offset
    with open(path, "rb") as fh:
        fh.seek(offset)
        data = fh.read()
    end = data.rfind(b"\n") + 1
    return data[:end].decode("utf-8", "replace").splitlines(), offset + end


def scan(cache, projects, now):
    """Fold what the transcripts gained into the cache; compute the caps of new rejections."""
    for path in transcripts(projects):
        lines, cache["files"][path] = _read_new(path, cache["files"].get(path, 0))
        for line in lines:
            try:
                row = json.loads(line)
            except ValueError:
                continue
            if not isinstance(row, dict) or row.get("type") != "assistant":
                continue
            t = checkpoint.when(row.get("timestamp"))
            if not t:
                continue
            quota = row.get("quotaLimits")
            if isinstance(quota, dict) and quota.get("status") == "rejected":
                kind, resets = quota.get("rateLimitType"), quota.get("resetsAt")
                if kind in SPAN_S and isinstance(resets, (int, float)):
                    key = "%s:%d" % (kind, resets)
                    first = cache["rejects"].get(key, [kind, resets, t.timestamp()])
                    first[2] = min(first[2], t.timestamp())
                    cache["rejects"][key] = first
                continue
            msg = row.get("message") if isinstance(row.get("message"), dict) else {}
            if msg.get("id") and isinstance(msg.get("usage"), dict):
                # a streamed message repeats its id; the last row carries the final count
                key = "%s/%s" % (msg["id"], row.get("requestId") or "")
                cache["calls"][key] = [t.timestamp(), cost(msg.get("model"), msg["usage"])]
    for key, (kind, resets, hit) in list(cache["rejects"].items()):
        caps = cache["caps"].setdefault(kind, {})
        if str(int(resets)) not in caps:
            start = resets - SPAN_S[kind]
            spent = sum(c for t, c in cache["calls"].values() if start <= t <= hit)
            if spent > 0:
                caps[str(int(resets))] = round(spent, 4)
    for kind, caps in cache["caps"].items():
        for old in sorted(caps, key=float)[:-KEPT_CAPS]:
            del caps[old]
    cache["rejects"] = {k: v for k, v in cache["rejects"].items() if now - v[2] <= KEEP_S}
    cache["calls"] = {k: v for k, v in cache["calls"].items() if now - v[0] <= KEEP_S}
    return cache


def cap(caps):
    """The cap the estimate divides by: low, so the warning comes early. None without caps."""
    recent = [v for _, v in sorted(caps.items(), key=lambda kv: float(kv[0]))][-RECENT_CAPS:]
    if not recent:
        return None
    floor = statistics.median(recent) / 2
    return min(v for v in recent if v >= floor)


def window(kind, times, resets, now):
    """The current window of `kind` as (start, resets_at); None when no window is open."""
    span = SPAN_S[kind]
    if kind == "seven_day":
        if not resets:
            return now - span, None
        end = max(resets)
        while end <= now:
            end += span
        return end - span, end
    end = None
    for t in sorted(times):
        if t > now:
            break
        if end is None or t >= end:
            known = [r for r in resets if r - span <= t < r]
            end = known[0] if known else (t // ROUND_S) * ROUND_S + span
    if end is None or end <= now:
        return None
    return end - span, end


def compute(cache, now):
    """The estimate, in the status line's shape."""
    limits, detail = {}, {}
    times = [t for t, _ in cache["calls"].values()]
    for kind in SPAN_S:
        known = [r for k, r, _ in cache["rejects"].values() if k == kind]
        known += [float(r) for r in cache["caps"].get(kind, {})]
        found = window(kind, times, known, now)
        divisor = cap(cache["caps"].get(kind, {}))
        if not divisor:
            continue
        if found is None:
            limits[kind] = {"used_percentage": 0, "resets_at": None}
            detail[kind] = {"spent": 0, "cap": divisor}
            continue
        start, resets = found
        spent = sum(c for t, c in cache["calls"].values() if start <= t <= now)
        limits[kind] = {"used_percentage": round(100 * spent / divisor, 1), "resets_at": resets}
        detail[kind] = {"spent": round(spent, 2), "cap": divisor, "start": start}
    return {"updated": now, "source": "estimate", "rate_limits": limits, "detail": detail}


def estimate(root=checkpoint.ROOT, projects=PROJECTS, now=None, max_age=MAX_AGE_S):
    """The estimate, recomputed when the last one is older than `max_age` seconds."""
    now = now or time.time()
    out = os.path.join(root, checkpoint.SESSIONS, ESTIMATE)
    last = _load(out)
    if last and isinstance(last.get("updated"), (int, float)) and 0 <= now - last["updated"] \
            <= max_age:
        return last
    if not os.path.isdir(projects):
        return None
    cache_path = os.path.join(root, checkpoint.SESSIONS, CACHE)
    cache = _load(cache_path) or _empty()
    if not all(isinstance(cache.get(k), dict) for k in _empty()):
        cache = _empty()
    scan(cache, projects, now)
    _save(cache_path, cache)
    result = compute(cache, now)
    _save(out, result)
    return result


def _reset(at, kind):
    t = checkpoint.when(at)
    if not t:
        return "-"
    return checkpoint.hm(t) + (" on %s" % checkpoint.day(t) if kind == "seven_day" else "")


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--rebuild", action="store_true", help="forget the cache and rescan")
    ap.add_argument("--projects", default=PROJECTS)
    args = ap.parse_args(argv)
    if args.rebuild:
        for name in (CACHE, ESTIMATE):
            try:
                os.remove(os.path.join(checkpoint.ROOT, checkpoint.SESSIONS, name))
            except OSError:
                pass
    result = estimate(projects=args.projects, max_age=0)
    if not result:
        print("no transcripts under %s" % args.projects)
        return 1
    cache = _load(os.path.join(checkpoint.ROOT, checkpoint.SESSIONS, CACHE)) or _empty()
    for kind, label in (("five_hour", "5-hour"), ("seven_day", "7-day")):
        win, det = result["rate_limits"].get(kind), result["detail"].get(kind)
        caps = cache["caps"].get(kind, {})
        print("%s: %s" % (label, "no cap yet (no rejection on file)" if not win else
                          "%s%% ($%.2f of a $%.2f cap), resets %s" % (
                              win["used_percentage"], det["spent"], det["cap"],
                              _reset(win["resets_at"], kind))))
        if caps:
            print("  caps: " + ", ".join(
                "%s $%.0f" % (dt.datetime.fromtimestamp(float(r)).strftime("%m-%d %H:%M"), v)
                for r, v in sorted(caps.items(), key=lambda kv: float(kv[0]))))
    return 0


if __name__ == "__main__":
    sys.exit(main())
