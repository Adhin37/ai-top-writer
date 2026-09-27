#!/usr/bin/env python3
"""Status line: the model and the usage windows, and a copy of the usage for the hooks.

Claude Code gives a status-line command the live usage of the 5-hour and 7-day windows
(`rate_limits.<window>.used_percentage`, `resets_at`); no hook payload carries them. This script
prints them and saves them to docs/sessions/usage.json, where tools/session_hooks.py reads them to
warn the session before the limit.

The terminal CLI runs the status line; the VS Code panel does not appear to, and then usage.json is
never written and the warning never fires. The handoff itself does not depend on it.
"""
import datetime as dt
import json
import os
import sys
import time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
USAGE = os.path.join(ROOT, "docs", "sessions", "usage.json")
LABELS = (("five_hour", "5h"), ("seven_day", "7d"))


def reset_time(value):
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        return dt.datetime.fromtimestamp(value).strftime("%H:%M")
    if isinstance(value, str) and value:
        try:
            return dt.datetime.fromisoformat(value.replace("Z", "+00:00")).astimezone() \
                .strftime("%H:%M")
        except ValueError:
            return None
    return None


def line(payload):
    model = payload.get("model") if isinstance(payload.get("model"), dict) else {}
    parts = [model.get("display_name") or model.get("id") or "Claude"]
    limits = payload.get("rate_limits") if isinstance(payload.get("rate_limits"), dict) else {}
    for key, label in LABELS:
        window = limits.get(key) if isinstance(limits.get(key), dict) else {}
        pct = window.get("used_percentage")
        if isinstance(pct, (int, float)):
            part = "%s %d%%" % (label, pct)
            resets = reset_time(window.get("resets_at")) if key == "five_hour" else None
            parts.append(part + (" (resets %s)" % resets if resets else ""))
    return " · ".join(parts)


def save(payload, path=USAGE):
    limits = payload.get("rate_limits")
    if not isinstance(limits, dict) or not limits:
        return
    os.makedirs(os.path.dirname(path), exist_ok=True)
    tmp = "%s.%d.tmp" % (path, os.getpid())
    with open(tmp, "w", encoding="utf-8") as fh:
        json.dump({"updated": time.time(), "rate_limits": limits}, fh)
    os.replace(tmp, path)


def main():
    try:
        payload = json.loads(sys.stdin.read() or "{}")
        payload = payload if isinstance(payload, dict) else {}
        save(payload)
    except (ValueError, OSError):
        payload = {}
    print(line(payload))
    return 0


if __name__ == "__main__":
    sys.exit(main())
