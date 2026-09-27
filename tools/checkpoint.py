#!/usr/bin/env python3
"""Write a session's handoff - what it was doing, which agents were in flight - from its transcripts.

A session that hits the 5-hour usage limit stops mid-work: background agents die with HTTP 429,
and after the reset the prompt cache is cold. Everything a resume needs is already on disk, in the
transcripts Claude Code keeps under ~/.claude/projects/<project>/: the user's messages, the
session's last words, every agent's spawn prompt, how each agent ended, and what it wrote. This
tool reads them and writes docs/sessions/<session-id>.md, spending no model tokens. The hooks in
tools/session_hooks.py run it at the end of every turn and at the 429; the `handoff` skill says
how a session resumes from the file.

Two parts of the file are kept across rebuilds: the `<!-- note -->` block, which the session writes
itself when usage nears the limit, and `closed_at`, set by --close once the work is resumed.

Usage:
  checkpoint.py [SESSION_ID] [--transcripts DIR] [--out PATH]    (default: the newest session)
  checkpoint.py --close SESSION_ID
"""
import argparse
import datetime as dt
import glob
import json
import os
import re
import subprocess
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from handback import default_transcripts  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SESSIONS = os.path.join("docs", "sessions")
WRITE_TOOLS = {"Write", "Edit", "MultiEdit", "NotebookEdit"}
IN_FLIGHT = {"running", "failed", "killed"}
HUMAN_CAP = 1500
LAST_WORDS = 3
FILES_CAP = 40
WRAPPERS = re.compile(r"<(ide_opened_file|ide_selection|system-reminder)>.*?</\1>", re.S)
AGENT_ID = re.compile(r"agentId: ([\w-]+)")
ERROR_TYPE = re.compile(r"error type (\w+)")
NOTE = re.compile(r"<!-- note -->\n?(.*?)<!-- /note -->", re.S)


# ---------------------------------------------------------------- reading transcripts

def rows(path):
    with open(path, encoding="utf-8") as fh:
        for line in fh:
            if not line.strip():
                continue
            try:
                row = json.loads(line)
            except ValueError:
                continue
            if isinstance(row, dict):
                yield row


def blocks(row):
    msg = row.get("message")
    content = msg.get("content") if isinstance(msg, dict) else None
    return [b for b in content if isinstance(b, dict)] if isinstance(content, list) else []


def text_of(row):
    """A user or assistant row's text: a string content, or its text blocks joined."""
    msg = row.get("message")
    content = msg.get("content") if isinstance(msg, dict) else None
    if isinstance(content, str):
        return content
    return "\n\n".join(b.get("text", "") for b in blocks(row) if b.get("type") == "text")


def when(value):
    """An aware local datetime from an ISO string or epoch seconds; None if neither."""
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        return dt.datetime.fromtimestamp(value).astimezone()
    if isinstance(value, str) and value:
        try:
            t = dt.datetime.fromisoformat(value.replace("Z", "+00:00"))
        except ValueError:
            return None
        return (t if t.tzinfo else t.astimezone()).astimezone()
    return None


def iso(t):
    return t.isoformat(timespec="minutes") if t else ""


def hm(t):
    return t.strftime("%H:%M") if t else "?"


def day(t):
    return t.strftime("%Y-%m-%d") if t else "?"


def _tool_result_text(block):
    content = block.get("content")
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        return "\n".join(c.get("text", "") for c in content if isinstance(c, dict))
    return ""


def _notification(text):
    def tag(name):
        m = re.search(r"<%s>(.*?)</%s>" % (name, name), text, re.S)
        return m.group(1).strip() if m else ""
    return tag("task-id"), tag("status"), tag("summary")


def _is_human(row):
    if row.get("type") != "user" or row.get("isMeta") or row.get("isCompactSummary"):
        return False
    origin = row.get("origin")
    if isinstance(origin, dict):
        return origin.get("kind") == "human"
    if any(b.get("type") == "tool_result" for b in blocks(row)):
        return False
    return not text_of(row).lstrip().startswith("<task-notification>")


def read_main(path):
    """What the main session's transcript says, in one pass."""
    s = {"title": "", "human": [], "said": [], "spawns": {}, "events": [], "writes": [],
         "last_ok": None, "last_error": None, "context_tokens": 0, "names": {},
         "messages": {}}
    pending = {}                                    # tool_use id -> (name, input, time)
    for row in rows(path):
        t = when(row.get("timestamp"))
        kind = row.get("type")
        if kind == "ai-title" and row.get("aiTitle"):
            s["title"] = row["aiTitle"]
        elif kind == "assistant":
            if row.get("isApiErrorMessage") or row.get("error"):
                quota = row.get("quotaLimits") if isinstance(row.get("quotaLimits"), dict) else {}
                s["last_error"] = {"time": t, "error": str(row.get("error") or "api error"),
                                   "window": quota.get("rateLimitType"),
                                   "resets": when(quota.get("resetsAt"))}
                continue
            s["last_ok"], s["last_error"] = t, None
            usage = (row.get("message") or {}).get("usage") or {}
            tokens = sum(usage.get(k) or 0 for k in ("input_tokens", "cache_creation_input_tokens",
                                                      "cache_read_input_tokens"))
            s["context_tokens"] = tokens or s["context_tokens"]
            said = text_of(row).strip()
            if said:
                s["said"] = (s["said"] + [(t, said)])[-LAST_WORDS:]
            for b in blocks(row):
                if b.get("type") == "tool_use":
                    inp = b.get("input") if isinstance(b.get("input"), dict) else {}
                    pending[b.get("id")] = (b.get("name"), inp, t)
                    if b.get("name") == "Agent":
                        s["spawns"][b.get("id")] = inp
        elif kind == "user":
            text = text_of(row)
            if _is_human(row):
                text = WRAPPERS.sub("", text).strip()
                if text:
                    s["human"].append((t, text))
            elif text.lstrip().startswith("<task-notification>"):
                task, status, summary = _notification(text)
                s["events"].append((task, "notified", t, status, summary))
            elif isinstance(origin := row.get("origin"), dict) and origin.get("kind") == "peer" \
                    and "[Subagent hand-back]" in text:
                s["events"].append((str(origin.get("from") or ""), "handed back", t, "completed", ""))
            for b in blocks(row):
                if b.get("type") != "tool_result" or b.get("tool_use_id") not in pending:
                    continue
                name, inp, _ = pending.pop(b.get("tool_use_id"))
                failed = bool(b.get("is_error"))
                result = _tool_result_text(b)
                if name == "Agent":
                    m = AGENT_ID.search(result)
                    if m:
                        aid = m.group(1)
                        if inp.get("name"):
                            s["names"][inp["name"]] = aid
                        if "Async agent launched" in result:
                            s["events"].append((aid, "launched", t, "running", ""))
                        else:
                            s["events"].append((aid, "returned", t, "completed", ""))
                elif name == "SendMessage" and not failed:
                    to = str(inp.get("to") or "")
                    aid = s["names"].get(to, to)
                    s["events"].append((aid, "messaged", t, "running", ""))
                    if isinstance(inp.get("message"), str):
                        s["messages"][aid] = inp["message"]
                elif name in WRITE_TOOLS and not failed:
                    path_ = inp.get("file_path") or inp.get("notebook_path")
                    if path_:
                        s["writes"].append((path_, t))
    return s


def read_agent(path):
    """One agent's transcript: what it wrote, and how its latest assignment ended."""
    a = {"writes": [], "recent": [], "handed_back": False, "error": None, "last": None}
    if not os.path.exists(path):
        return a
    pending = {}
    for row in rows(path):
        t = when(row.get("timestamp")) or a["last"]
        a["last"] = t
        kind = row.get("type")
        if kind == "user":
            text = text_of(row)
            if isinstance((row.get("message") or {}).get("content"), str) \
                    and not text.lstrip().startswith("<system-reminder>"):
                a["handed_back"], a["error"], a["recent"] = False, None, []   # new assignment
            for b in blocks(row):
                if b.get("type") == "tool_result" and b.get("tool_use_id") in pending:
                    name, inp = pending.pop(b.get("tool_use_id"))
                    if name in WRITE_TOOLS and not b.get("is_error"):
                        path_ = inp.get("file_path") or inp.get("notebook_path")
                        if path_:
                            a["writes"].append((path_, t))
                            a["recent"].append(path_)
        elif kind == "assistant":
            if row.get("isApiErrorMessage") or row.get("error"):
                a["error"] = str(row.get("error") or "api error")
                continue
            for b in blocks(row):
                if b.get("type") == "tool_use":
                    inp = b.get("input") if isinstance(b.get("input"), dict) else {}
                    pending[b.get("id")] = (b.get("name"), inp)
                    if b.get("name") == "SubagentHandback":
                        a["handed_back"] = True
    return a


def agents(session_dir, main):
    """Every agent the session spawned, with its status and what it wrote."""
    out = []
    for meta_path in sorted(glob.glob(os.path.join(session_dir, "subagents", "agent-*.meta.json"))):
        aid = os.path.basename(meta_path)[len("agent-"):-len(".meta.json")]
        try:
            with open(meta_path, encoding="utf-8") as fh:
                meta = json.load(fh)
        except (OSError, ValueError):
            meta = {}
        spawn = main["spawns"].get(meta.get("toolUseId"), {})
        status, summary, changed = "running", "", None
        for task, _, t, st, summ in main["events"]:
            if task == aid and st:
                status, summary, changed = st, summ, t
        work = read_agent(meta_path[:-len(".meta.json")] + ".jsonl")
        if status == "running" and work["error"]:
            status, summary, changed = "failed", work["error"], work["last"]
        elif status == "running" and work["handed_back"]:
            status = "completed"
        m = ERROR_TYPE.search(summary)
        summary = m.group(1) if m else summary[:100]
        out.append({
            "id": aid, "type": meta.get("agentType") or spawn.get("subagent_type") or "?",
            "task": spawn.get("name") or meta.get("description") or spawn.get("description") or "",
            "description": meta.get("description") or spawn.get("description") or "",
            "background": meta.get("requestShape") == "background" or bool(
                spawn.get("run_in_background")),
            "prompt": spawn.get("prompt") or "", "status": status, "summary": summary,
            "changed": changed, "writes": work["writes"],
            "recent": work["recent"], "message": main["messages"].get(aid, ""),
            "handed_back": work["handed_back"],
        })
    return out


def in_flight(agent, main):
    """Running, or ended badly after the session last spoke - so nobody has acted on it yet."""
    if agent["status"] == "running":
        return True
    if agent["status"] not in IN_FLIGHT:
        return False
    return not main["last_ok"] or not agent["changed"] or agent["changed"] > main["last_ok"]


# ---------------------------------------------------------------- the handoff file

def handoff_path(root, session_id):
    return os.path.join(root, SESSIONS, session_id + ".md")


def read_frontmatter(path):
    """`key: value` pairs of a handoff's frontmatter, and its note block."""
    try:
        with open(path, encoding="utf-8") as fh:
            text = fh.read()
    except OSError:
        return {}, ""
    front = {}
    if text.startswith("---\n"):
        for line in text[4:].split("\n---", 1)[0].splitlines():
            key, sep, value = line.partition(":")
            if sep:
                front[key.strip()] = value.strip()
    m = NOTE.search(text)
    return front, (m.group(1) if m else "")


def git_status(root):
    try:
        out = subprocess.run(["git", "status", "--short"], cwd=root, capture_output=True,
                             text=True, timeout=5).stdout
    except (OSError, subprocess.SubprocessError):
        return ""
    lines = out.splitlines()
    return "\n".join(lines[:FILES_CAP] + (["... %d more" % (len(lines) - FILES_CAP)]
                                          if len(lines) > FILES_CAP else []))


def rel(path, root):
    p = os.path.normpath(path if os.path.isabs(path) else os.path.join(root, path))
    return p[len(root) + 1:] if p.startswith(root + os.sep) else p


def fence(text):
    run = max([len(m) for m in re.findall(r"`{3,}", text)] + [2])
    return "`" * (run + 1)


def quote(text, cap=None):
    if cap and len(text) > cap:
        text = text[:cap].rstrip() + " [...]"
    return "\n".join("> " + line if line else ">" for line in text.splitlines())


def state(main, event, now, failure=None):
    """(status, reason, stopped_at, resets_at) from the transcript and the hook that asked.
    `failure` is StopFailure's error, for when the 429 has not reached the transcript yet."""
    err = main["last_error"] or (failure and {"time": now, "error": failure, "window": None,
                                              "resets": None})
    if err:
        if err["error"] == "rate_limit":
            reason = "usage limit" + (", %s window" % err["window"] if err["window"] else "")
        else:
            reason = "API error: %s" % err["error"]
        return "stopped", reason, err["time"] or now, err["resets"]
    if event == "SessionEnd":
        return "ended", "session closed", now, None
    return "working", "", None, None


def render(session_id, main, crew, root, event=None, now=None, note="", closed_at="",
           failure=None):
    now = now or dt.datetime.now().astimezone()
    status, reason, stopped_at, resets = state(main, event, now, failure)
    flying = [a for a in crew if in_flight(a, main)]
    title = main["title"] or "untitled session"
    out = ["---", "session: %s" % session_id, "title: %s" % title.replace("\n", " "),
           "status: %s" % status, "reason: %s" % reason, "stopped_at: %s" % iso(stopped_at),
           "resets_at: %s" % iso(resets), "in_flight: %d" % len(flying),
           "context_tokens: %d" % main["context_tokens"], "updated: %s" % iso(now),
           "closed_at: %s" % closed_at, "---", "", "# Handoff - %s" % title, ""]

    if status == "working":
        out.append("**Working** as of %s %s. %d agent(s) in flight." % (day(now), hm(now),
                                                                         len(flying)))
    else:
        line = "**%s** at %s on %s: %s" % (status.capitalize(), hm(stopped_at), day(stopped_at),
                                            reason)
        if resets:
            line += ", resets %s (%s)" % (hm(resets), day(resets))
        out.append(line + ". %d agent(s) in flight." % len(flying))
    out += ["Resuming this session re-reads about %dk tokens of context, uncached; a fresh "
            "session starts from this file. How to resume: the `handoff` skill."
            % round(main["context_tokens"] / 1000), ""]

    body = note.strip("\n")
    out += ["## Note", "", "<!-- note -->"] + ([body] if body.strip() else []) + [
        "<!-- /note -->", ""]

    out += ["## Agents in flight", ""]
    if flying:
        out += ["| agent | type | task | mode | status | written since its last instruction "
                "| handed back |",
                "|---|---|---|---|---|---|---|"]
        for a in flying:
            status_ = a["status"] + (" - %s" % a["summary"] if a["summary"] else "")
            files = ", ".join("`%s`" % p for p in dict.fromkeys(rel(p, root) for p in a["recent"]))
            out.append("| %s | %s | %s | %s | %s | %s | %s |" % (
                a["id"], a["type"], a["task"].replace("|", "/"),
                "background" if a["background"] else "foreground",
                status_.replace("|", "/").replace("\n", " "), files or "-",
                "yes" if a["handed_back"] else "no"))
    else:
        out.append("None.")
    done = len(crew) - len(flying)
    if done:
        out += ["", "%d other agent(s) finished earlier in this session." % done]
    out.append("")

    out += ["## Task - the user's messages, verbatim", ""]
    for i, (t, text) in enumerate(main["human"], 1):
        out += ["%d. *%s %s*" % (i, day(t), hm(t)), "", quote(text, HUMAN_CAP), ""]
    if not main["human"]:
        out += ["None found.", ""]

    out += ["## Last words - the session's last messages", ""]
    for t, text in main["said"]:
        out += ["*%s*" % hm(t), "", quote(text, HUMAN_CAP), ""]

    writes = {}
    for path_, t in main["writes"]:
        writes[rel(path_, root)] = ("showrunner", t)
    for a in crew:
        for path_, t in a["writes"]:
            writes[rel(path_, root)] = ("%s %s" % (a["type"], a["id"][:7]), t)
    order = sorted(writes.items(), key=lambda kv: kv[1][1] or now)
    out += ["## Files written this session", ""]
    if len(order) > FILES_CAP:
        out += ["%d earlier files not shown." % (len(order) - FILES_CAP), ""]
        order = order[-FILES_CAP:]
    if order:
        out += ["| path | by | when |", "|---|---|---|"]
        out += ["| `%s` | %s | %s %s |" % (p, who, day(t), hm(t)) for p, (who, t) in order]
    else:
        out.append("None.")
    status_lines = git_status(root)
    if status_lines:
        out += ["", "`git status --short`:", "", "```", status_lines, "```"]
    out.append("")

    if flying:
        out += ["## Spawn prompts - verbatim, to re-spawn an agent in a fresh session", ""]
        for a in flying:
            f = fence(a["prompt"] + a["message"])
            out += ["### %s - %s, \"%s\"" % (a["id"], a["type"], a["description"]), "",
                    f, a["prompt"], f, ""]
            if a["message"]:
                out += ["Its latest instruction, by SendMessage:", "", f, a["message"], f, ""]
    return "\n".join(out).rstrip("\n") + "\n"


def build(session_id, transcripts, root=ROOT, out=None, event=None, now=None, failure=None):
    """Rebuild one session's handoff. Returns the path written."""
    main_path = os.path.join(transcripts, session_id + ".jsonl")
    main = read_main(main_path)
    crew = agents(os.path.join(transcripts, session_id), main)
    out = out or handoff_path(root, session_id)
    front, note = read_frontmatter(out)
    text = render(session_id, main, crew, root, event, now, note, front.get("closed_at", ""),
                  failure)
    os.makedirs(os.path.dirname(out), exist_ok=True)
    tmp = "%s.%d.tmp" % (out, os.getpid())         # Stop and SubagentStop can rebuild at once
    with open(tmp, "w", encoding="utf-8") as fh:
        fh.write(text)
    os.replace(tmp, out)
    return out


def close(session_id, root=ROOT, now=None):
    """Mark a handoff resumed: hooks stop pointing at it until it stops again."""
    path = handoff_path(root, session_id)
    with open(path, encoding="utf-8") as fh:
        text = fh.read()
    stamp = iso(now or dt.datetime.now().astimezone())
    text, n = re.subn(r"(?m)^closed_at:.*$", "closed_at: %s" % stamp, text, count=1)
    if not n:
        raise ValueError("%s has no closed_at line" % path)
    with open(path, "w", encoding="utf-8") as fh:
        fh.write(text)
    return path


def needs_resume(front):
    """True if a handoff stopped (or ended with agents running) after it was last closed."""
    stopped = front.get("status") == "stopped" or (
        front.get("status") == "ended" and front.get("in_flight", "0") not in ("", "0"))
    if not stopped:
        return False
    closed, at = when(front.get("closed_at")), when(front.get("stopped_at"))
    return not closed or not at or at > closed


def newest_session(transcripts):
    hits = glob.glob(os.path.join(transcripts, "*.jsonl"))
    if not hits:
        raise FileNotFoundError("no session transcripts under %s" % transcripts)
    return os.path.basename(max(hits, key=os.path.getmtime))[:-len(".jsonl")]


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("session", nargs="?", help="session id (default: the newest session)")
    ap.add_argument("--transcripts", help="the project's transcript directory")
    ap.add_argument("--out", help="write here instead of docs/sessions/<session>.md")
    ap.add_argument("--close", metavar="SESSION", help="mark this session's handoff resumed")
    args = ap.parse_args(argv)
    try:
        if args.close:
            print("closed: %s" % close(args.close))
            return 0
        transcripts = args.transcripts or default_transcripts()
        session = args.session or newest_session(transcripts)
        print(build(session, transcripts, out=args.out))
    except (OSError, ValueError) as exc:
        sys.stderr.write("checkpoint: %s\n" % exc)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
