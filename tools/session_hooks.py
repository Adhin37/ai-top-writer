#!/usr/bin/env python3
"""Hooks that keep a session's handoff current and bring the next session back to it.

Registered in `.claude/settings.json`. Reads the hook payload on stdin; prints a JSON reply only
when it has context to give the model; always exits 0, because a hook that breaks a session gets
switched off.

  Stop, SubagentStop, StopFailure, SessionEnd, PreCompact
      rebuild docs/sessions/<session>.md with tools/checkpoint.py - at every turn's end, and at the
      429 that stops a session at its usage limit (StopFailure).
  SessionStart (main session)
      if a session stopped at a limit, or ended with agents still running, and nobody has resumed
      it yet: point the model at its handoff. After an auto-compaction (source "compact"): point
      it at this session's handoff and at `tools/room.py where`, which the summary may have lost.
  UserPromptSubmit (main session)
      the same for this session's own handoff (a "continue" after the reset), and the usage check.
  PostToolUse (main session)
      the usage check: when the 5-hour window reaches PAUSE_AT, tell the model once per window to
      start no new chapter (kb/showrunner/loop.md, "Pause at a chapter boundary"); when the 5-hour
      or 7-day window reaches THRESHOLD, once per window, to hand off. The reading comes from tools/statusline.py, which only the terminal CLI
      runs; with no fresh reading there is no warning, and the handoff is still rebuilt every turn.
"""
import glob
import json
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import checkpoint  # noqa: E402

REBUILD = {"Stop", "SubagentStop", "StopFailure", "SessionEnd", "PreCompact"}
THRESHOLD = 95
PAUSE_AT = 80           # the 5-hour window: finish the step, start no new chapter
FRESH_S = 600
WINDOWS = {"five_hour": "5-hour", "seven_day": "7-day"}
SPAN_S = {"five_hour": 5 * 3600, "seven_day": 7 * 86400}


def fresh(usage, now):
    """True when a status-line reading is a dict written in the last FRESH_S seconds."""
    if not isinstance(usage, dict):
        return False
    updated = usage.get("updated")
    if not isinstance(updated, (int, float)) or isinstance(updated, bool):
        return False
    return now - updated <= FRESH_S


def sessions_dir(root):
    return os.path.join(root, checkpoint.SESSIONS)


def _load(path, default):
    try:
        with open(path, encoding="utf-8") as fh:
            return json.load(fh)
    except (OSError, ValueError):
        return default


def _stop_line(front):
    at = checkpoint.when(front.get("stopped_at"))
    line = "stopped at %s on %s (%s)" % (checkpoint.hm(at), checkpoint.day(at),
                                         front.get("reason") or front.get("status"))
    resets = checkpoint.when(front.get("resets_at"))
    if resets:
        line += ", limit resets %s" % checkpoint.hm(resets)
    return line + ", with %s agent(s) in flight" % (front.get("in_flight") or "0")


def open_handoffs(root):
    """Handoffs that still need resuming, newest stop first: [(session_id, frontmatter)]."""
    out = []
    for path in glob.glob(os.path.join(sessions_dir(root), "*.md")):
        front, _ = checkpoint.read_frontmatter(path)
        if checkpoint.needs_resume(front):
            out.append((os.path.basename(path)[:-3], front))
    far_past = checkpoint.when(0)
    return sorted(out, key=lambda kv: checkpoint.when(kv[1].get("stopped_at")) or far_past,
                  reverse=True)


def refresh_stale(root, transcripts):
    """Rebuild any handoff whose transcript moved on after it was written - a session whose
    StopFailure hook never ran still gets its 429 recorded."""
    for path in glob.glob(os.path.join(sessions_dir(root), "*.md")):
        sid = os.path.basename(path)[:-3]
        transcript = os.path.join(transcripts, sid + ".jsonl")
        try:
            stale = os.path.getmtime(transcript) > os.path.getmtime(path)
        except OSError:
            continue
        if stale:
            checkpoint.build(sid, transcripts, root)


def pointer(root, session_id):
    """SessionStart: the newest handoff that still needs resuming, if any."""
    waiting = open_handoffs(root)
    if not waiting:
        return None
    sid, front = waiting[0]
    rel = os.path.join(checkpoint.SESSIONS, sid + ".md")
    if sid == session_id:
        text = "This session %s. Its handoff is %s." % (_stop_line(front), rel)
    else:
        text = "An earlier session, \"%s\", %s. Its handoff is %s." % (
            front.get("title", sid), _stop_line(front), rel)
    text += (" Tell the user in your first reply. To continue that work, follow the handoff "
             "skill's resume procedure.")
    if len(waiting) > 1:
        text += " (%d older handoffs are also unresumed in %s.)" % (len(waiting) - 1,
                                                                     checkpoint.SESSIONS)
    return text


def own_pointer(root, session_id):
    """UserPromptSubmit: this session was stopped by a limit and has not been resumed."""
    front, _ = checkpoint.read_frontmatter(checkpoint.handoff_path(root, session_id))
    if front.get("status") != "stopped" or not checkpoint.needs_resume(front):
        return None
    return ("This session %s. Before carrying on, follow the handoff skill's resume procedure "
            "with %s." % (_stop_line(front),
                          os.path.join(checkpoint.SESSIONS, session_id + ".md")))


def usage_warning(root, now=None):
    """Once per window and level: usage has reached PAUSE_AT or THRESHOLD, per a fresh
    status-line reading."""
    now = now or time.time()
    usage = _load(os.path.join(sessions_dir(root), "usage.json"), {})
    if not fresh(usage, now):
        return None
    limits = usage.get("rate_limits") if isinstance(usage.get("rate_limits"), dict) else {}
    warned_path = os.path.join(sessions_dir(root), "warned.json")
    warned = _load(warned_path, {})
    warned = warned if isinstance(warned, dict) else {}
    levels = [(key, key, THRESHOLD) for key in WINDOWS] + [("five_hour:pause", "five_hour",
                                                             PAUSE_AT)]
    for mark, key, at in levels:
        window = limits.get(key) if isinstance(limits.get(key), dict) else {}
        pct = window.get("used_percentage")
        if not isinstance(pct, (int, float)) or pct < at:
            continue
        resets = checkpoint.when(window.get("resets_at"))
        # no reset time: one warning per window-length span, not one ever
        stamp = checkpoint.iso(resets) or "unknown-%d" % int(now // SPAN_S[key])
        if warned.get(mark) == stamp:
            continue
        warned[mark] = stamp
        if at == THRESHOLD:
            warned[key + ":pause"] = stamp          # past the hand-off, the pause is moot
        os.makedirs(sessions_dir(root), exist_ok=True)
        with open(warned_path, "w", encoding="utf-8") as fh:
            json.dump(warned, fh)
        when = " (resets %s)" % checkpoint.hm(resets) if resets else ""
        if at == PAUSE_AT:
            return ("Usage: the 5-hour window is at %d%%%s. Finish the step in hand and start no "
                    "new chapter: kb/showrunner/loop.md, \"Pause at a chapter boundary\"."
                    % (pct, when))
        return ("Usage: the %s limit is at %d%%%s. Use the handoff skill now: spawn no new "
                "agent, and write the handoff note." % (WINDOWS[key], pct, when))
    return None


def after_compact(session_id):
    """SessionStart after a compaction: where the facts the summary may have dropped are."""
    return ("The context was just compacted. This session's handoff, rebuilt before it, is %s: "
            "the agents in flight and their ids, your last words, the user's messages. In a "
            "writing run, `python3 tools/room.py where novels/<slug>` says the chapter and step "
            "from the files." % os.path.join(checkpoint.SESSIONS, session_id + ".md"))


def rebuild(payload, root):
    event, session_id = payload.get("hook_event_name"), str(payload.get("session_id") or "")
    transcript = payload.get("transcript_path")
    if session_id and transcript and os.path.exists(transcript):
        failure = str(payload.get("error") or "api error") if event == "StopFailure" else None
        checkpoint.build(session_id, os.path.dirname(transcript), root, event=event,
                         failure=failure)


def handle(payload, root=checkpoint.ROOT):
    """The context to give the model, or None."""
    event = payload.get("hook_event_name")
    session_id = str(payload.get("session_id") or "")
    if event in REBUILD:
        rebuild(payload, root)
        return None
    if payload.get("agent_id"):
        return None
    if event == "SessionStart":
        if payload.get("source") == "compact" and session_id:
            return after_compact(session_id)
        if payload.get("transcript_path"):
            refresh_stale(root, os.path.dirname(payload["transcript_path"]))
        return pointer(root, session_id)
    if event == "UserPromptSubmit":
        parts = [own_pointer(root, session_id), usage_warning(root)]
        return " ".join(p for p in parts if p) or None
    if event == "PostToolUse":
        return usage_warning(root)
    return None


def main():
    try:
        payload = json.loads(sys.stdin.read() or "{}")
        if not isinstance(payload, dict):
            return 0
        context = handle(payload)
    except Exception as exc:                        # fail open, but say why
        sys.stderr.write("session_hooks: %s\n" % exc)
        return 0
    if context:
        print(json.dumps({"hookSpecificOutput": {"hookEventName": payload["hook_event_name"],
                                                 "additionalContext": context}}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
