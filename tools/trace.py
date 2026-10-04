#!/usr/bin/env python3
"""What a session cost, per role and per chapter: tokens, thinking, cache, dollars, model and tool
time, effort, cache expiries, injected context, the knowledge-base docs each role opened, and what
the showrunner's context carried.

Claude Code's own transcripts, read as measurements. Kept from them: usage, timestamps, model
names, effort, tool names, the paths a Read opened, a spawn's description and the chapter its
prompt names, and the label in a subagent's `agent-*.meta.json`. Of other text it keeps only
*lengths* (hand-backs, injected context) and, for the roles that end on a status line, whether
their final message parses (`tools/wire.py`).

Accounting, ported from skilled-writer's `swlib/transcripts.py`: Claude Code writes one row per
content block, and every row of a response repeats that response's usage. Summing rows bills one
request several times over. So rows are grouped into a response by (requestId, message.id), the
input-side fields are taken once, and `output_tokens` - a streaming counter - is taken as the
group's maximum, as is its thinking share (`output_tokens_details.thinking_tokens`).

Scope is one session: `<transcripts>/<session>.jsonl` (the showrunner) and every subagent under
`<transcripts>/<session>/subagents/`. A hand-back enters the showrunner as an `Agent` or
`SendMessage` tool result, or as a `[Subagent hand-back]` agent message: a user row when it opens
a turn, a `queued_command` attachment row when it lands mid-turn. Its size is counted in
tokens as characters / 4, an estimate; *re-reads* multiply it by the showrunner responses that
came after it, since each of them read it again from cache.

**Unrecorded output.** A response's usage is sometimes written before its last tokens land: an
agent's final response (the one that calls `SubagentHandback`) always, and some long tool calls
(the clerk's edits, a reader's report). Where the recorded output is far below what the response's
visible text and tool input measure, the difference is reported apart, as *unrecorded*: estimated
from that length, a lower bound (the thinking behind it cannot be recovered), and never added to the
recorded totals. Claude Code's own count, the session's last `cost-state` row, has every token: the
*cross-check* line sets the trace's per-model totals beside it.

**Per chapter.** Every spawn and continuation the showrunner sends names its chapter (`chapter N`,
`work/chNNNN/`, or `chNN` in the description) and often its round. Each agent response belongs to
the dispatch that started it, so a planner continued warm from one chapter's fold into the next
chapter's beats is split between the two. The showrunner's responses, and work no dispatch names a
chapter for (`/plan`), go to the chapter whose window they fall in; between two chapters, to the
next one; before the first, `pre`; after the last, `post`.

**Cache expiries.** A request sent longer after the transcript's previous request than its cache
lives (5 minutes for an agent, an hour for the showrunner, read off its cache writes), and that
writes more than it reads, has re-written its context: its cache-write tokens are counted.

**Injected context.** Attachment rows Claude Code adds to a context that no role asked for: IDE
diagnostics, MCP server instructions, other hooks' context, and the harness's own (environment,
git status, reminders). Sized in characters; whether each kind reaches the model is Claude Code's.

**Docs opened.** The `kb/` files each role opened: from `docs/sessions/<session>.reads.tsv` when
`tools/guard.py` logged the session (exact), else from the Read calls in the transcripts.

Usage:
  trace.py SESSION [--transcripts DIR] [--since ISO] [--until ISO] [--match REGEX]
                   [--agents] [--chapters] [--docs] [--json]

SESSION is a session id or its prefix. --match keeps only subagents whose spawn description
matches (and leaves the showrunner out, since it cannot be split by run).
"""
import argparse
import calendar
import glob
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import wire  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SESSIONS = os.path.join(ROOT, "docs", "sessions")
MILLION = 1000000.0

# $ per million tokens: input, output, cache read. The rates plan 01's write-up used (from the
# claude-api skill); a cache write costs 1.25x input for 5 minutes, 2x for an hour.
RATES = {
    "claude-fable-5-1": (10.00, 50.00, 0.25),
    "claude-opus-5-5": (4.00, 20.00, 0.20),
    "claude-opus-5": (5.00, 25.00, 0.50),
    "claude-sonnet-5-5": (2.00, 10.00, 0.20),
    "claude-sonnet-5": (2.00, 10.00, 0.20),
    "claude-haiku-4-5": (1.00, 5.00, 0.10),
}
WRITE_5M, WRITE_1H = 1.25, 2.00
TTL_5M, TTL_1H = 300.0, 3600.0
SYNTHETIC = ("<synthetic>",)
HANDBACK_MARK = "[Subagent hand-back]"
HANDBACK_TOOLS = ("Agent", "Task", "SendMessage")
DISPATCH_TOOLS = ("Agent", "Task", "SendMessage")
FINAL_TOOL = "SubagentHandback"
STALE = 8.0     # a response recording fewer tokens than chars / STALE never got its full usage
CHARS_PER_TOKEN = 4.0
TS = re.compile(r"^(\d{4})-(\d\d)-(\d\d)T(\d\d):(\d\d):(\d\d)(\.\d+)?")
# Roles whose final message is one status line (kb/shared/wire.md).
STATUS_ROLES = ("planner", "writer", "story-editor", "line-editor", "continuity-editor", "clerk")
CHAPTER_IN_TEXT = (re.compile(r"\b[Cc]hapter (\d+)\b"), re.compile(r"/ch(\d{4})/"))
CHAPTER_IN_DESC = re.compile(r"\bch ?(\d+)\b")
ROUND = (re.compile(r"\bround (\d+)\b"), re.compile(r"\bdraft-r(\d+)\b"),
         re.compile(r"(?:^|\s)r(\d+)$"))
DIAGNOSTICS = "<ide_diagnostics>"
NOT_INJECTED = ("queued_command", "prompt_snapshot")     # hand-backs; the system prompt record
META_KEYS = ("type", "toolUseID", "hookName", "hookEvent", "uuid", "addedNames")


def default_transcripts():
    slug = ROOT.replace(os.sep, "-")
    return os.path.join(os.path.expanduser("~/.claude/projects"), slug)


def seconds(stamp):
    """Seconds since the epoch from an ISO timestamp (UTC), or None."""
    m = TS.match(str(stamp or ""))
    if not m:
        return None
    whole = calendar.timegm(tuple(int(x) for x in m.groups()[:6]) + (0, 0, 0))
    return whole + (float(m.group(7)) if m.group(7) else 0.0)


def rows(path):
    try:
        fh = open(path, encoding="utf-8", errors="replace")
    except OSError:
        return
    with fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            try:
                row = json.loads(line)
            except ValueError:
                continue
            if isinstance(row, dict):
                yield row


def text_length(content):
    """Characters in a message or tool result's text, whatever shape it arrived in."""
    if isinstance(content, str):
        return len(content)
    if isinstance(content, list):
        return sum(text_length(b.get("text", b.get("content", ""))) if isinstance(b, dict)
                   else text_length(b) for b in content)
    return 0


def string_length(value, skip=META_KEYS):
    """Characters in every string inside a JSON value, leaving out bookkeeping keys."""
    if isinstance(value, str):
        return len(value)
    if isinstance(value, list):
        return sum(string_length(v) for v in value)
    if isinstance(value, dict):
        return sum(string_length(v) for k, v in value.items() if k not in skip)
    return 0


def has_mark(content):
    if isinstance(content, str):
        return HANDBACK_MARK in content
    if isinstance(content, list):
        return any(isinstance(b, dict) and HANDBACK_MARK in str(b.get("text", ""))
                   for b in content)
    return False


def kb_path(path):
    """`kb/...` from a path a Read opened, or None."""
    m = re.search(r"(?:^|/)(kb/[^\s]+)$", str(path or "").replace(os.sep, "/"))
    return m.group(1) if m else None


def injected_kind(attachment):
    kind = str(attachment.get("type") or "")
    if kind == "hook_additional_context":
        return "ide_diagnostics" if DIAGNOSTICS in json.dumps(attachment) else "hook"
    if kind == "mcp_instructions_delta":
        return "mcp"
    return "harness"


class Response(object):
    """One billable API request, assembled from every row that shares its id."""

    def __init__(self):
        self.model = ""
        self.timestamp = ""
        self.effort = ""
        self.input = self.write_5m = self.write_1h = self.read = 0
        self.output = self.thinking = 0
        self.model_s = self.tool_s = 0.0
        self.start = self.end = None        # request sent, last row written (epoch seconds)
        self.gap = None                     # seconds since this transcript's previous request
        self.ttl = TTL_5M
        self.content_chars = 0
        self.final = False
        self.reads = []
        self.chapter = None
        self.sends = None                   # the chapter a showrunner response dispatched for

    def absorb(self, row, usage):
        self.timestamp = self.timestamp or row.get("timestamp") or ""
        self.model = self.model or (row.get("message") or {}).get("model") or ""
        self.effort = self.effort or str(row.get("effort") or "")
        self.input = usage.get("input_tokens") or 0
        self.read = usage.get("cache_read_input_tokens") or 0
        made = usage.get("cache_creation") or {}
        if "ephemeral_5m_input_tokens" in made or "ephemeral_1h_input_tokens" in made:
            self.write_5m = made.get("ephemeral_5m_input_tokens") or 0
            self.write_1h = made.get("ephemeral_1h_input_tokens") or 0
        else:
            self.write_5m, self.write_1h = usage.get("cache_creation_input_tokens") or 0, 0
        self.output = max(self.output, usage.get("output_tokens") or 0)
        details = usage.get("output_tokens_details") or {}
        self.thinking = max(self.thinking, details.get("thinking_tokens") or 0)

    @property
    def context(self):
        return self.input + self.read + self.write_5m + self.write_1h

    @property
    def writes(self):
        return self.write_5m + self.write_1h

    @property
    def expired(self):
        """Sent after its cache had lapsed, and it missed: it wrote more than it read. (A request
        just past the TTL by this clock can still hit, since the cache's own clock started a few
        seconds later.)"""
        return self.gap is not None and self.gap > self.ttl and self.writes > self.read

    @property
    def stale(self):
        """Its usage was written before the response ended: a final response always is."""
        return self.final or self.unrecorded > 0

    @property
    def unrecorded(self):
        """Output tokens missing from a response whose usage never landed (a lower bound)."""
        if not self.content_chars or self.output >= self.content_chars / STALE:
            return 0.0
        return max(0.0, self.content_chars / CHARS_PER_TOKEN - self.output)

    def rates(self):
        return RATES.get(self.model, (0.0, 0.0, 0.0))

    def unrecorded_cost(self):
        return self.unrecorded * self.rates()[1] / MILLION

    def write_cost(self):
        return (self.write_5m * WRITE_5M + self.write_1h * WRITE_1H) * self.rates()[0] / MILLION

    def cost(self):
        """(output $, cache-write $, cache-read $, input $). An unpriced model costs 0."""
        rin, rout, rread = self.rates()
        return (self.output * rout / MILLION, self.write_cost(), self.read * rread / MILLION,
                self.input * rin / MILLION)


class Transcript(object):
    """One transcript file: the showrunner, or one subagent."""

    def __init__(self, path):
        self.path = path
        self.responses = []
        self.handbacks = []     # (timestamp, tokens) - the showrunner's only
        self.dispatches = []    # the showrunner's spawns and continuations, as dicts
        self.injected = []      # (timestamp, kind, chars, attachment type)
        self.finals = []        # (timestamp, text): what SubagentHandback carried
        self.compactions = []   # (timestamp, trigger, tokens before): the context summarised
        self.cost_state = None  # Claude Code's own count, the showrunner's last cost-state row
        self.role = "showrunner"
        self.description = ""
        self.agent_id = ""
        self.tool_use_id = ""
        meta = path[:-len(".jsonl")] + ".meta.json"
        if "/subagents/" in path.replace(os.sep, "/"):
            self.role = "subagent"
            self.agent_id = os.path.basename(path)[len("agent-"):-len(".jsonl")]
            try:
                with open(meta, encoding="utf-8") as fh:
                    data = json.load(fh)
                self.role = str(data.get("agentType") or "subagent")
                self.description = str(data.get("description") or "")
                self.tool_use_id = str(data.get("toolUseId") or "")
            except (OSError, ValueError):
                pass
        self._read()

    @property
    def tool_s(self):
        return sum(r.tool_s for r in self.responses)

    def _read(self):
        groups, order, names, events = {}, [], {}, []
        main = self.role == "showrunner"
        for row in rows(self.path):
            if row.get("isSidechain") and main:
                continue
            kind = row.get("type")
            if kind == "cost-state" and main:
                self.cost_state = row
                continue
            if kind == "system" and row.get("subtype") == "compact_boundary":
                meta = row.get("compactMetadata") if isinstance(row.get("compactMetadata"),
                                                                dict) else {}
                self.compactions.append((row.get("timestamp") or "", str(meta.get("trigger")
                                                                         or "?"),
                                         meta.get("preTokens") or 0))
                continue
            message = row.get("message") if isinstance(row.get("message"), dict) else {}
            content = message.get("content")
            blocks = content if isinstance(content, list) else []
            stamp = row.get("timestamp") or ""
            if kind in ("assistant", "user") and stamp:
                events.append((stamp, kind, message.get("id") or "",
                               [b.get("id") for b in blocks
                                if isinstance(b, dict) and b.get("type") == "tool_use"],
                               [b.get("tool_use_id") for b in blocks
                                if isinstance(b, dict) and b.get("type") == "tool_result"]))
            if kind == "user" and main:
                if has_mark(content):
                    self.handbacks.append((stamp, text_length(content) / CHARS_PER_TOKEN))
                for b in blocks:
                    if (isinstance(b, dict) and b.get("type") == "tool_result"
                            and names.get(b.get("tool_use_id")) in HANDBACK_TOOLS):
                        self.handbacks.append(
                            (stamp, text_length(b.get("content")) / CHARS_PER_TOKEN))
            if kind == "attachment":
                att = row.get("attachment") if isinstance(row.get("attachment"), dict) else {}
                if main and has_mark(att.get("prompt")):
                    self.handbacks.append((stamp, text_length(att["prompt"]) / CHARS_PER_TOKEN))
                if att.get("type") not in NOT_INJECTED:
                    self.injected.append((stamp, injected_kind(att), string_length(att),
                                          str(att.get("type") or "")))
            if kind != "assistant":
                continue
            sends = None
            for b in blocks:
                if isinstance(b, dict) and b.get("type") == "tool_use":
                    names[b.get("id")] = b.get("name")
                    if main and b.get("name") in DISPATCH_TOOLS:
                        self.dispatches.append(dispatch(stamp, b))
                        sends = self.dispatches[-1]["chapter"]
            usage = message.get("usage") or {}
            if not usage or message.get("model") in SYNTHETIC:
                continue
            key = (row.get("requestId") or "", message.get("id") or "")
            if not any(key):
                key = (row.get("uuid") or str(len(order)),)
            if key not in groups:
                groups[key] = Response()
                order.append(key)
            r = groups[key]
            r.absorb(row, usage)
            r.sends = sends if sends is not None else r.sends
            for b in blocks:
                if not isinstance(b, dict):
                    continue
                if b.get("type") == "text":
                    r.content_chars += len(b.get("text") or "")
                elif b.get("type") == "tool_use":
                    r.content_chars += len(json.dumps(b.get("input")))
                    ti = b.get("input") if isinstance(b.get("input"), dict) else {}
                    if b.get("name") == FINAL_TOOL:
                        r.final = True
                        msg = ti.get("message")
                        self.finals.append((stamp, msg if isinstance(msg, str)
                                            else json.dumps(b.get("input"))))
                    elif b.get("name") == "Read" and ti.get("file_path"):
                        r.reads.append(str(ti["file_path"]))
        self.responses = [groups[k] for k in order]
        by_id = dict((k[1], groups[k]) for k in order if len(k) == 2 and k[1])
        self._timing(events, by_id)
        writes_1h = sum(r.write_1h for r in self.responses)
        writes_5m = sum(r.write_5m for r in self.responses)
        ttl = TTL_1H if writes_1h > writes_5m else TTL_5M
        prev = None
        for r in sorted(self.responses, key=lambda r: r.start or 0):
            r.ttl = ttl
            if r.start is not None and prev is not None:
                r.gap = r.start - prev
            prev = r.start if r.start is not None else prev

    def _timing(self, events, by_id):
        """Model and tool seconds per response, and when each request went out, from timestamps
        and ids alone.

        A response runs from the last user-side row before it (the message or tool result it
        answers) to its own last row: rows are written as content blocks complete, so stopping
        at the first row would drop the text and tool calls streamed after the thinking. A tool's
        seconds, from its call to its result, belong to the response that called it.
        """
        events.sort(key=lambda e: e[0])
        last_user, start, first, end, pending = None, {}, {}, {}, {}
        for stamp, kind, mid, uses, results in events:
            t = seconds(stamp)
            if t is None:
                continue
            if kind == "assistant":
                if mid and mid not in first:
                    first[mid] = t
                    if last_user is not None:
                        start[mid] = last_user
                if mid:
                    end[mid] = t
                last_user = None
                for tid in uses:
                    pending[tid] = (t, mid)
            else:
                for tid in results:
                    if tid in pending:
                        t0, owner = pending.pop(tid)
                        if owner in by_id:
                            by_id[owner].tool_s += max(0.0, t - t0)
                last_user = t
        for mid, r in by_id.items():
            if mid in first:
                r.start = start.get(mid, first[mid])
                r.end = end[mid]
            if mid in start:
                r.model_s = max(0.0, end[mid] - start[mid])


def dispatch(stamp, block):
    """A spawn or continuation the showrunner sent: who to, and which chapter and round."""
    ti = block.get("input") if isinstance(block.get("input"), dict) else {}
    text = str(ti.get("prompt") or ti.get("message") or "")
    desc = str(ti.get("description") or ti.get("summary") or "")
    chapter = None
    for rx in CHAPTER_IN_TEXT:
        m = rx.search(text)
        if m:
            chapter = int(m.group(1))
            break
    if chapter is None:
        m = CHAPTER_IN_DESC.search(desc)
        chapter = int(m.group(1)) if m and block.get("name") != "SendMessage" else None
    rnd = None
    for rx, src in zip(ROUND, (text, text, desc)):
        m = rx.search(src)
        if m:
            rnd = int(m.group(1))
            break
    return {"t": seconds(stamp), "id": block.get("id") or "", "tool": block.get("name"),
            "to": str(ti.get("to") or ti.get("recipient") or ""), "description": desc,
            "chapter": chapter, "round": rnd}


def transcripts_for(session, base):
    """The showrunner's transcript and its subagents', for a session id or prefix."""
    mains = sorted(glob.glob(os.path.join(base, session + "*.jsonl")))
    if not mains:
        raise FileNotFoundError("no session %s under %s" % (session, base))
    if len(mains) > 1:
        raise ValueError("session prefix %s is ambiguous: %s"
                         % (session, ", ".join(os.path.basename(m) for m in mains)))
    main = mains[0]
    subs = sorted(glob.glob(os.path.join(main[:-len(".jsonl")], "subagents", "**", "*.jsonl"),
                            recursive=True))
    return [main] + subs


def session_id(paths):
    return os.path.basename(paths[0])[:-len(".jsonl")] if paths else ""


def within(stamp, since, until):
    return not ((since and stamp < since) or (until and stamp > until))


# ---------------------------------------------------------------- chapters


def assign_chapters(transcripts):
    """Set `chapter` on every response: a chapter number, "pre" or "post". Returns the rounds
    seen per chapter."""
    main = next((t for t in transcripts if t.role == "showrunner"), None)
    dispatches = sorted(main.dispatches if main else [], key=lambda d: d["t"] or 0)
    by_tool_use = dict((t.tool_use_id, t) for t in transcripts if t.tool_use_id)
    by_agent = dict((t.agent_id, t) for t in transcripts if t.agent_id)
    sent = {}               # transcript path -> its dispatches, in order
    rounds = {}
    for d in dispatches:
        t = by_tool_use.get(d["id"]) if d["tool"] != "SendMessage" else by_agent.get(d["to"])
        if t is not None:
            sent.setdefault(t.path, []).append(d)
        if d["chapter"] is not None and d["round"] is not None:
            rounds.setdefault(d["chapter"], set()).add(d["round"])
    windows = {}            # chapter -> [open, close]
    for d in dispatches:
        if d["chapter"] is not None and d["t"] is not None:
            w = windows.setdefault(d["chapter"], [d["t"], d["t"]])
            w[0] = min(w[0], d["t"])
    loose = []
    for t in transcripts:
        mine = sent.get(t.path, [])
        fallback = CHAPTER_IN_DESC.search(t.description) if t.role != "showrunner" else None
        for r in t.responses:
            r.chapter = None
            when = r.start if r.start is not None else seconds(r.timestamp)
            if t.role == "showrunner":
                r.chapter = r.sends
            else:
                started = [d for d in mine if d["t"] is not None and when is not None
                           and d["t"] <= when + 1]
                if started:
                    r.chapter = started[-1]["chapter"]
                elif not mine and fallback:
                    r.chapter = int(fallback.group(1))
            if r.chapter is None:
                loose.append((r, when))
            elif r.chapter in windows and (r.end or when):
                windows[r.chapter][1] = max(windows[r.chapter][1], r.end or when)
    order = sorted(windows.items(), key=lambda kv: kv[1][0])
    for r, when in loose:
        r.chapter = "post" if order else "pre"
        if when is None or not order:
            continue
        if when < order[0][1][0]:
            r.chapter = "pre"
            continue
        for i, (n, (opened, closed)) in enumerate(order):
            nxt = order[i + 1][1][0] if i + 1 < len(order) else None
            if opened <= when <= closed:
                r.chapter = n
                break
            if when > closed and nxt is not None and when < nxt:
                r.chapter = order[i + 1][0]
                break
    return dict((n, sorted(v)) for n, v in rounds.items())


def chapter_key(label):
    return (0, 0) if label == "pre" else (2, 0) if label == "post" else (1, label)


# ---------------------------------------------------------------- docs log


def reads_log(session, sessions_dir=SESSIONS):
    """[(timestamp, agent id, role, path)] from the guard's log for a session, or None."""
    path = os.path.join(sessions_dir, session + ".reads.tsv")
    if not session or not os.path.isfile(path):
        return None
    out = []
    with open(path, encoding="utf-8", errors="replace") as fh:
        for line in fh:
            parts = line.rstrip("\n").split("\t")
            if len(parts) >= 5:
                out.append((parts[0], parts[2], parts[3], parts[4]))
    return out


def kb_docs(root=ROOT):
    """Every doc in the knowledge bases, as `kb/<role>/<doc>.md`."""
    out = []
    for path in sorted(glob.glob(os.path.join(root, "kb", "*", "*.md"))):
        out.append(os.path.relpath(path, root).replace(os.sep, "/"))
    return out


# --------------------------------------------------------------- summarise


def summarise(paths, since=None, until=None, match=None, log=None):
    """Per-role and per-chapter totals, per-agent rows, the showrunner's context, and the
    cross-check against Claude Code's own count, as a plain dict."""
    pattern = re.compile(match) if match else None
    transcripts = [Transcript(p) for p in paths]
    rounds = assign_chapters(transcripts)
    log = reads_log(session_id(paths)) if log is None else log
    roles, agents, chapters = {}, [], {}
    showrunner, expiries, finals, docs = None, [], {}, {}
    by_agent = dict((t.agent_id, t.role) for t in transcripts if t.agent_id)
    for t in transcripts:
        if pattern and (t.role == "showrunner" or not pattern.search(t.description)):
            continue
        rs = [r for r in t.responses if within(r.timestamp, since, until)]
        if not rs:
            continue
        row = totals(rs)
        row.update({"role": t.role, "agent": t.agent_id, "description": t.description,
                    "spawns": 1, "models": sorted(set(r.model for r in rs))})
        injected = [(s, k, n, a) for s, k, n, a in t.injected if within(s, since, until)]
        row["injected"] = dict((k, sum(n for _s, kk, n, _a in injected if kk == k))
                               for k in sorted(set(i[1] for i in injected)))
        row["injected_n"] = dict((k, sum(1 for i in injected if i[1] == k))
                                 for k in row["injected"])
        row["compactions"] = sum(1 for c in t.compactions if within(c[0], since, until))
        row["effort"] = {}
        for r in rs:
            row["effort"][r.effort or "?"] = row["effort"].get(r.effort or "?", 0) + 1
        agents.append(row)
        total = roles.setdefault(t.role, {"injected": {}, "injected_n": {}, "effort": {}})
        for k, v in row.items():
            if isinstance(v, (int, float)) and not isinstance(v, bool):
                total[k] = total.get(k, 0) + v
            elif k in ("injected", "injected_n", "effort"):
                for kk, vv in v.items():
                    total[k][kk] = total[k].get(kk, 0) + vv
        for r in rs:
            if r.expired:
                expiries.append({"role": t.role, "agent": t.agent_id, "at": r.timestamp,
                                 "gap_s": r.gap, "tokens": r.writes, "usd": r.write_cost(),
                                 "chapter": r.chapter})
            per = chapters.setdefault(r.chapter, {})
            cell = per.setdefault(t.role, totals([]))
            for k, v in totals([r]).items():
                cell[k] += v
        if t.role in STATUS_ROLES:
            f = finals.setdefault(t.role, {"clean": 0, "extra": 0, "broken": 0, "models": [],
                                           "not_clean": []})
            for stamp, text in t.finals:
                if not within(stamp, since, until):
                    continue
                found = wire.check_handback(text)
                kind = ("broken" if any(x[0] == "defect" for x in found)
                        else "extra" if found else "clean")
                f[kind] += 1
                f["models"] = sorted(set(f["models"]) | set(row["models"]) - set(SYNTHETIC))
                if kind != "clean":
                    f["not_clean"].append("%s (%s)" % (t.description or t.agent_id, kind))
        if t.role == "showrunner":
            contexts = [r.context for r in rs]
            stamps = [r.timestamp for r in rs]
            hb = [(s, n) for s, n in t.handbacks if within(s, since, until)]
            showrunner = {
                "responses": len(rs),
                "context_mean": sum(contexts) / len(contexts),
                "context_peak": max(contexts),
                "handbacks": len(hb),
                "handback_tokens": sum(n for _, n in hb),
                "handback_rereads": sum(n * sum(1 for s in stamps if s > stamp)
                                        for stamp, n in hb),
                "cache_read_tokens": row["cache_read"],
                "compactions": [{"at": c[0], "trigger": c[1], "tokens": c[2]}
                                for c in t.compactions if within(c[0], since, until)],
            }
        if log is None:
            for r in rs:
                for p in r.reads:
                    kb = kb_path(p)
                    if kb:
                        docs.setdefault(t.role, {}).setdefault(kb, set()).add(t.agent_id or "main")
    if log is not None:
        for stamp, agent, role, path in log:
            kb = kb_path(path)
            if kb and within(stamp, since, until) and (not pattern or agent in by_agent):
                docs.setdefault(role or by_agent.get(agent, "showrunner"), {}).setdefault(
                    kb, set()).add(agent or "main")
    unpriced = {}
    for a in agents:
        for m in a["models"]:
            if m not in RATES and m not in SYNTHETIC:
                unpriced[m] = unpriced.get(m, 0) + a["responses"]
    whole = not (since or until or match)
    main = next((t for t in transcripts if t.role == "showrunner"), None)
    return {"roles": roles, "agents": agents, "showrunner": showrunner,
            "total": sum(r["cost"] for r in roles.values()),
            "unrecorded_usd": sum(r["unrecorded_usd"] for r in roles.values()),
            "unpriced": unpriced,
            "chapters": dict((str(k), v) for k, v in chapters.items()),
            "rounds": dict((str(k), v) for k, v in rounds.items()),
            "expiries": expiries,
            "finals": finals,
            "docs": dict((role, dict((p, len(s)) for p, s in d.items()))
                         for role, d in docs.items()),
            "docs_source": "guard log" if log is not None else "transcripts",
            "crosscheck": crosscheck(transcripts, main.cost_state if main else None)
            if whole else None}


def totals(rs):
    """Sums over responses, the numbers every table shares."""
    parts = [r.cost() for r in rs]
    expired = [r for r in rs if r.expired]
    return {"responses": len(rs), "model_s": sum(r.model_s for r in rs),
            "tool_s": sum(r.tool_s for r in rs),
            "output": sum(r.output for r in rs), "thinking": sum(r.thinking for r in rs),
            "input": sum(r.input for r in rs), "cache_read": sum(r.read for r in rs),
            "cache_write": sum(r.writes for r in rs),
            "output_usd": sum(p[0] for p in parts), "cache_write_usd": sum(p[1] for p in parts),
            "cache_read_usd": sum(p[2] for p in parts), "cost": sum(sum(p) for p in parts),
            "unrecorded": sum(r.unrecorded for r in rs),
            "unrecorded_usd": sum(r.unrecorded_cost() for r in rs),
            "expiries": len(expired), "expiry_tokens": sum(r.writes for r in expired),
            "expiry_usd": sum(r.write_cost() for r in expired)}


def crosscheck(transcripts, state):
    """Per model, this trace's totals beside Claude Code's own (the last `cost-state` row); and
    per role, its cost with each model's missing output allotted to the roles on that model.

    The allotment is an estimate in two parts. The visible part of the gap goes by each role's
    estimated unrecorded output (what its stale responses wrote). The thinking part, which nothing
    in a transcript measures, goes evenly to every stale response.
    """
    if not state:
        return None
    mine, per_role = {}, {}
    for t in transcripts:
        for r in t.responses:
            pr = per_role.setdefault(t.role, {"usd": 0.0, "models": {}})
            pr["usd"] += sum(r.cost())
            pm = pr["models"].setdefault(r.model, {"stale": 0, "unrecorded": 0.0})
            pm["stale"] += 1 if r.stale else 0
            pm["unrecorded"] += r.unrecorded
            m = mine.setdefault(r.model, {"input": 0, "output": 0, "thinking": 0, "read": 0,
                                          "write": 0, "usd": 0.0, "unrecorded": 0.0})
            m["input"] += r.input
            m["output"] += r.output
            m["thinking"] += r.thinking
            m["read"] += r.read
            m["write"] += r.writes
            m["usd"] += sum(r.cost())
            m["unrecorded"] += r.unrecorded
    out = {}
    for model, theirs in (state.get("modelUsage") or {}).items():
        m = mine.get(model) or mine.get(re.sub(r"-\d{8}$", "", model)) or {}
        out[model] = {
            "cc_usd": theirs.get("costUSD") or 0.0, "trace_usd": m.get("usd", 0.0),
            "cc_output": theirs.get("outputTokens") or 0, "trace_output": m.get("output", 0),
            "cc_thinking": theirs.get("thinkingTokens") or 0,
            "trace_thinking": m.get("thinking", 0),
            "unrecorded": m.get("unrecorded", 0.0),
            "input_side_equal": (
                (theirs.get("inputTokens") or 0) == m.get("input", 0)
                and (theirs.get("cacheReadInputTokens") or 0) == m.get("read", 0)
                and (theirs.get("cacheCreationInputTokens") or 0) == m.get("write", 0)),
        }
    for model, m in out.items():
        m["in_transcripts"] = model in mine or re.sub(r"-\d{8}$", "", model) in mine
        rate = RATES.get(model, RATES.get(re.sub(r"-\d{8}$", "", model), (0, 0, 0)))[1]
        gap = max(0, m["cc_output"] - m["trace_output"])
        thinking = min(gap, max(0, m["cc_thinking"] - m["trace_thinking"]))
        stale = sum(pr["models"].get(model, {}).get("stale", 0) for pr in per_role.values())
        seen = sum(pr["models"].get(model, {}).get("unrecorded", 0) for pr in per_role.values())
        for pr in per_role.values():
            pm = pr["models"].get(model)
            if not pm:
                continue
            tokens = ((gap - thinking) * pm["unrecorded"] / seen if seen else 0) + (
                thinking * pm["stale"] / stale if stale else 0)
            pr["allotted"] = pr.get("allotted", 0.0) + tokens * rate / MILLION
    total = sum(pr["usd"] + pr.get("allotted", 0.0) for pr in per_role.values())
    traced = sum(pr["usd"] for pr in per_role.values())
    roles = dict((role, {"usd": pr["usd"], "allotted": pr.get("allotted", 0.0),
                         "share": pr["usd"] / traced if traced else 0.0,
                         "share_allotted": (pr["usd"] + pr.get("allotted", 0.0)) / total
                         if total else 0.0})
                 for role, pr in per_role.items())
    return {"cc_total_usd": state.get("totalCostUSD") or 0.0, "models": out, "roles": roles}


# ------------------------------------------------------------------ render


def minutes(s):
    s = int(s or 0)
    return "%dh%02dm" % (s // 3600, s % 3600 // 60) if s >= 3600 else "%dm%02ds" % (s // 60, s % 60)


def render(result, show_agents=False, show_chapters=False, show_docs=False):
    out = []
    head = ("%-17s %6s %6s %8s %7s %9s %6s %10s %10s %9s %9s %9s %9s"
            % ("role", "spawns", "resp", "model s", "tool s", "output", "think", "c.write",
               "c.read", "out $", "write $", "read $", "cost $"))
    out.append(head)
    order = sorted(result["roles"].items(), key=lambda kv: -kv[1]["cost"])
    for role, r in order:
        think = 100.0 * r["thinking"] / r["output"] if r["output"] else 0.0
        out.append("%-17s %6d %6d %8.0f %7.0f %9d %5.0f%% %10d %10d %9.2f %9.2f %9.2f %9.2f"
                   % (role, r["spawns"], r["responses"], r["model_s"], r["tool_s"], r["output"],
                      think, r["cache_write"], r["cache_read"], r["output_usd"],
                      r["cache_write_usd"], r["cache_read_usd"], r["cost"]))
    out.append("%-17s %s %9.2f" % ("total", " " * 116, result["total"]))
    for model, n in sorted(result.get("unpriced", {}).items()):
        # A model with no rate would cost 0 and look cheap: say so rather than fall silent.
        out.append("warn: no rate for %s (agents with %d responses on it); their cost is "
                   "counted as $0 - add it to RATES" % (model, n))
    out.append("")
    out.append("effort, responses at each level: " + " · ".join(
        "%s %s" % (role, ", ".join("%s %d" % kv for kv in sorted(r["effort"].items())))
        for role, r in order))
    missing = [(role, r) for role, r in order if r["unrecorded"]]
    if missing:
        out.append("unrecorded output, a lower bound from what the responses wrote: "
                   + " · ".join("%s ~%.1fk tokens $%.2f" % (role, r["unrecorded"] / 1000,
                                                           r["unrecorded_usd"])
                                for role, r in missing)
                   + " · total $%.2f" % result["unrecorded_usd"])
    expired = [(role, r) for role, r in order if r["expiries"]]
    if expired:
        out.append("cache expiries, requests sent after the cache lapsed (5 min for an agent, "
                   "1 h for the showrunner), their writes re-written: "
                   + " · ".join("%s %d, %.0fk tokens $%.2f" % (role, r["expiries"],
                                                             r["expiry_tokens"] / 1000,
                                                             r["expiry_usd"])
                                for role, r in expired)
                   + " · total $%.2f" % sum(r["expiry_usd"] for _role, r in expired))
        pauses = [e for e in result["expiries"] if e["role"] == "showrunner"]
        for e in pauses:
            out.append("  showrunner at %s, after %s: %.0fk tokens re-written, $%.2f"
                       % (e["at"][:16].replace("T", " "), minutes(e["gap_s"]),
                          e["tokens"] / 1000, e["usd"]))
    inj = [(role, r) for role, r in order if r["injected"]]
    if inj:
        out.append("injected context, characters no role asked for (count): " + " · ".join(
            "%s %s" % (role, ", ".join("%s %.1fk (%d)" % (k, n / 1000.0, r["injected_n"][k])
                                       for k, n in sorted(r["injected"].items(),
                                                          key=lambda kv: -kv[1])))
            for role, r in inj))
    fin = result.get("finals") or {}
    if fin:
        out.append("final messages that are one status line: " + " · ".join(
            "%s %d of %d (%s)%s" % (role, f["clean"], f["clean"] + f["extra"] + f["broken"],
                                    ", ".join(f["models"]) or "?",
                                    ("; not: " + ", ".join(f["not_clean"])) if f["not_clean"]
                                    else "")
            for role, f in sorted(fin.items()) if f["clean"] + f["extra"] + f["broken"]))
    docs = result.get("docs") or {}
    if docs:
        own = kb_docs()
        line = []
        for role, opened in sorted(docs.items()):
            mine = [p for p in own if p.startswith("kb/%s/" % role)]
            if mine:
                line.append("%s %d of %d" % (role, sum(1 for p in mine if p in opened),
                                             len(mine)))
        out.append("kb docs opened, of the role's own (from the %s; --docs lists them): %s"
                   % (result.get("docs_source"), " · ".join(line)))
    s = result["showrunner"]
    if s:
        out.append("")
        out.append("showrunner context: mean %.0fk, peak %.0fk tokens over %d responses"
                   % (s["context_mean"] / 1000, s["context_peak"] / 1000, s["responses"]))
        share = 100.0 * s["handback_rereads"] / s["cache_read_tokens"] if s["cache_read_tokens"] else 0
        out.append("hand-backs in: %d, ~%.1fk tokens, ~%.1fM re-read tokens (%.0f%% of its cache reads)"
                   % (s["handbacks"], s["handback_tokens"] / 1000,
                      s["handback_rereads"] / MILLION, share))
        comp = s.get("compactions") or []
        if comp:
            out.append("compactions: %d, at %s (the summarising call is not a response in the "
                       "transcript; the cross-check counts it)" % (len(comp), ", ".join(
                           "%s %s %.0fk" % (c["at"][11:16], c["trigger"], c["tokens"] / 1000)
                           for c in comp)))
    sub = [(role, r["compactions"]) for role, r in order
           if role != "showrunner" and r.get("compactions")]
    if sub:
        out.append("compacted mid-task, a role's judgement on a summary: " + " · ".join(
            "%s %d" % kv for kv in sub))
    cc = result.get("crosscheck")
    if cc:
        out.append("")
        out.append("cross-check, Claude Code's own count (cost-state) $%.2f against this trace's "
                   "$%.2f:" % (cc["cc_total_usd"], result["total"]))
        for model, m in sorted(cc["models"].items(), key=lambda kv: -kv[1]["cc_usd"]):
            if not m["in_transcripts"]:
                out.append("  %-26s $%7.2f in Claude Code's count, no response in the transcripts "
                           "(its own calls: titles, summaries)" % (model, m["cc_usd"]))
                continue
            gap = m["cc_output"] - m["trace_output"]
            out.append("  %-26s $%7.2f vs $%7.2f · input side %s · output %dk vs %dk: %dk "
                       "unrecorded (thinking %dk of it), %.0fk estimated from what was written"
                       % (model, m["cc_usd"], m["trace_usd"],
                          "equal" if m["input_side_equal"] else "DIFFERS",
                          m["cc_output"] / 1000, m["trace_output"] / 1000, gap / 1000,
                          (m["cc_thinking"] - m["trace_thinking"]) / 1000,
                          m["unrecorded"] / 1000))
        out.append("  share of the cost by role, as traced -> with each model's gap allotted "
                   "(visible output by what each role wrote, thinking evenly per stale response): "
                   + " · ".join("%s %.1f%% -> %.1f%% (+$%.2f)" % (role, 100 * r["share"],
                                                                100 * r["share_allotted"],
                                                                r["allotted"])
                                for role, r in sorted(cc["roles"].items(),
                                                      key=lambda kv: -kv[1]["usd"])))
    if show_chapters:
        out.append("")
        out.extend(render_chapters(result))
    if show_docs and docs:
        out.append("")
        own = kb_docs()
        for role, opened in sorted(docs.items()):
            out.append("%s opened: %s" % (role, ", ".join(
                "%s%s" % (p[3:], " x%d" % n if n > 1 else "")
                for p, n in sorted(opened.items()))))
            never = [p for p in own if p.startswith("kb/%s/" % role) and p not in opened]
            if never:
                out.append("%s never opened: %s" % (role, ", ".join(p[3:] for p in never)))
    if show_agents:
        out.append("")
        for a in sorted(result["agents"], key=lambda a: (a["role"], a["description"])):
            think = 100.0 * a["thinking"] / a["output"] if a["output"] else 0.0
            out.append("%-17s %-40s %4d resp %6.0f s %6.0f tool s %7d out %4.0f%% think  $%6.2f"
                       % (a["role"], (a["description"] or a["agent"])[:40], a["responses"],
                          a["model_s"], a["tool_s"], a["output"], think, a["cost"]))
    out.append("")
    out.append("rates, $/MTok in/out/read: " + " · ".join(
        "%s %g/%g/%g" % (m, *RATES[m]) for m in sorted(RATES)
        if any(m in a["models"] for a in result["agents"])))
    return "\n".join(out)


def render_chapters(result):
    """Cost per role per chapter, then the room's time, rounds and the showrunner's turns."""
    chapters = result["chapters"]
    labels = sorted(chapters, key=lambda k: chapter_key(int(k) if k.isdigit() else k))
    roles = {}
    for per in chapters.values():
        for role, cell in per.items():
            roles[role] = roles.get(role, 0) + cell["cost"]
    cols = sorted(roles, key=lambda r: -roles[r])
    out = ["per chapter, $ by role (pre: before chapter 1's first dispatch; post: after the last)"]
    out.append("%-5s %6s " % ("ch", "rounds") + " ".join("%9s" % c[:9] for c in cols)
               + " %9s %9s %9s %7s %8s %8s"
               % ("total", "room", "expiry $", "turns", "room m.s", "room t.s"))
    for label in labels:
        per = chapters[label]
        room = [c for r, c in per.items() if r != "showrunner"]
        rnds = result["rounds"].get(label) or []
        out.append("%-5s %6s " % (label, len(rnds) if rnds else "-")
                   + " ".join("%9.2f" % per[c]["cost"] if c in per else "%9s" % "-" for c in cols)
                   + " %9.2f %9.2f %9.2f %7d %8.0f %8.0f"
                   % (sum(c["cost"] for c in per.values()), sum(c["cost"] for c in room),
                      sum(c["expiry_usd"] for c in per.values()),
                      per.get("showrunner", {}).get("responses", 0),
                      sum(c["model_s"] for c in room), sum(c["tool_s"] for c in room)))
    return out


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("session")
    ap.add_argument("--transcripts", help="directory holding the session transcripts")
    ap.add_argument("--since", help="ISO timestamp (UTC); responses before it are left out")
    ap.add_argument("--until", help="ISO timestamp (UTC); responses after it are left out")
    ap.add_argument("--match", help="regex on a subagent's spawn description")
    ap.add_argument("--agents", action="store_true", help="one line per agent as well")
    ap.add_argument("--chapters", action="store_true", help="the per-chapter table as well")
    ap.add_argument("--docs", action="store_true", help="the kb docs each role opened, and not")
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args(argv)
    try:
        paths = transcripts_for(args.session, args.transcripts or default_transcripts())
    except (FileNotFoundError, ValueError) as exc:
        sys.stderr.write("trace: %s\n" % exc)
        return 1
    result = summarise(paths, args.since, args.until, args.match)
    print(json.dumps(result, indent=1) if args.json
          else render(result, args.agents, args.chapters, args.docs))
    return 0


if __name__ == "__main__":
    sys.exit(main())
