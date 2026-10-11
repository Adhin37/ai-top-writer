#!/usr/bin/env python3
"""The live usage of the 5-hour and 7-day windows, as claude.ai and `/usage` show them.

Claude Code's `/usage` reads them from Anthropic's usage endpoint with the account's own login.
This does the same: it reads the login's access token from Claude Code's credentials file and
sends it to that endpoint only, never anywhere else; it never prints, saves or refreshes the token
(Claude Code refreshes it). An expired token, no credentials file (macOS keeps them in the
Keychain), no network, or an answer it cannot read: no reading, and no warning. Nothing guesses
in its place: an estimate from the transcripts once paused a run at 96% that was at 73%.

The reading is saved to docs/sessions/usage-live.json in the status line's shape plus
`"source": "live"`, and reused for MAX_AGE_S; a failure is remembered for RETRY_S, so a hook that
runs after every tool call does not wait on the network each time.

Usage:
  live.py            the two windows, from a fresh fetch
  live.py --json     the saved reading, as JSON
"""
import argparse
import datetime as dt
import json
import os
import sys
import time
import urllib.request

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), *[os.pardir] * 4))
SAVED = os.path.join("docs", "sessions", "usage-live.json")
URL = "https://api.anthropic.com/api/oauth/usage"
BETA = "oauth-2025-04-20"
TIMEOUT_S = 4
MAX_AGE_S = 120
RETRY_S = 300
WINDOWS = (("five_hour", "5-hour"), ("seven_day", "7-day"))


def credentials_path():
    base = os.environ.get("CLAUDE_CONFIG_DIR") or os.path.expanduser("~/.claude")
    return os.path.join(base, ".credentials.json")


def token(path=None, now=None):
    """The login's access token, or None when there is none or it has expired."""
    try:
        with open(path or credentials_path(), encoding="utf-8") as fh:
            oauth = json.load(fh).get("claudeAiOauth") or {}
    except (OSError, ValueError, AttributeError):
        return None
    tok, expires = oauth.get("accessToken"), oauth.get("expiresAt")
    if not isinstance(tok, str) or not tok:
        return None
    if isinstance(expires, (int, float)) and expires / 1000 <= (now or time.time()):
        return None
    return tok


def _epoch(value):
    if not isinstance(value, str) or not value:
        return None
    try:
        return dt.datetime.fromisoformat(value.replace("Z", "+00:00")).timestamp()
    except ValueError:
        return None


def shape(answer, now):
    """The endpoint's answer in the status line's shape; None when it holds neither window."""
    limits = {}
    for key, _label in WINDOWS:
        window = answer.get(key) if isinstance(answer, dict) else None
        pct = window.get("utilization") if isinstance(window, dict) else None
        if isinstance(pct, (int, float)) and not isinstance(pct, bool):
            limits[key] = {"used_percentage": pct, "resets_at": _epoch(window.get("resets_at"))}
    if not limits:
        return None
    return {"updated": now, "source": "live", "rate_limits": limits}


def fetch(tok, opener=urllib.request.urlopen):
    req = urllib.request.Request(URL, headers={"Authorization": "Bearer " + tok,
                                               "anthropic-beta": BETA,
                                               "User-Agent": "claude-code"})
    with opener(req, timeout=TIMEOUT_S) as resp:
        return json.load(resp)


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


def reading(root=ROOT, now=None, max_age=MAX_AGE_S, creds=None, opener=urllib.request.urlopen):
    """The live reading, fetched when the saved one is older than `max_age`; None without one."""
    now = now or time.time()
    path = os.path.join(root, SAVED)
    last = _load(path) or {}
    checked = last.get("checked") if isinstance(last.get("checked"), (int, float)) else 0
    if "rate_limits" in last and 0 <= now - checked <= max_age:
        return last
    if last.get("error") and 0 <= now - checked <= RETRY_S:
        return None
    tok = token(creds, now)
    try:
        if not tok:
            raise ValueError("no unexpired login in %s" % (creds or credentials_path()))
        found = shape(fetch(tok, opener), now)
        if not found:
            raise ValueError("the answer holds no window")
    except Exception as exc:                        # noqa: BLE001 - any failure: no reading
        _save(path, {"checked": now, "error": "%s: %s" % (type(exc).__name__, exc)})
        return None
    found["checked"] = now
    _save(path, found)
    return found


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--json", action="store_true", help="print the reading as JSON")
    args = ap.parse_args(argv)
    found = reading(max_age=0) if not args.json else reading()
    if not found:
        saved = _load(os.path.join(ROOT, SAVED)) or {}
        print("no live reading: %s" % saved.get("error", "unknown"))
        return 1
    if args.json:
        print(json.dumps(found))
        return 0
    for key, label in WINDOWS:
        window = found["rate_limits"].get(key)
        if window:
            resets = window.get("resets_at")
            print("%s: %s%%, resets %s" % (label, window["used_percentage"], time.strftime(
                "%H:%M on %Y-%m-%d", time.localtime(resets)) if resets else "-"))
    return 0


if __name__ == "__main__":
    sys.exit(main())
