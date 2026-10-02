#!/usr/bin/env python3
"""What a session cost, per role: tokens, thinking, cache, dollars and model time, and what the
showrunner's context carried.

Claude Code's own transcripts, read as measurements. Kept from them: usage, timestamps, model
names, tool names, and the label in a subagent's `agent-*.meta.json`. Of text it keeps only
*lengths* (the size of each hand-back entering the showrunner), never the text itself.

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

An agent's last response, the one that calls `SubagentHandback`, is written before its usage
lands, so its output and thinking are missing from the transcript. It is reported apart, as
*unrecorded*: tokens estimated from the hand-back's length, a lower bound, never added to the
recorded totals.

Usage:
  trace.py SESSION [--transcripts DIR] [--since ISO] [--until ISO] [--match REGEX]
                   [--agents] [--json]

SESSION is a session id or its prefix. --match keeps only subagents whose spawn description
matches (and leaves the showrunner out, since it cannot be split by run).
"""
import argparse
import glob
import json
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
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
SYNTHETIC = ("<synthetic>",)
HANDBACK_MARK = "[Subagent hand-back]"
HANDBACK_TOOLS = ("Agent", "Task", "SendMessage")
FINAL_TOOL = "SubagentHandback"
STALE = 8.0     # a final response recording fewer tokens than chars / STALE never got its usage
CHARS_PER_TOKEN = 4.0
TS = re.compile(r"^(\d{4})-(\d\d)-(\d\d)T(\d\d):(\d\d):(\d\d)(\.\d+)?")


def default_transcripts():
    slug = ROOT.replace(os.sep, "-")
    return os.path.join(os.path.expanduser("~/.claude/projects"), slug)


def seconds(stamp):
    """Seconds since the epoch from an ISO timestamp (UTC), or None."""
    import calendar
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


def has_mark(content):
    if isinstance(content, str):
        return HANDBACK_MARK in content
    if isinstance(content, list):
        return any(isinstance(b, dict) and HANDBACK_MARK in str(b.get("text", ""))
                   for b in content)
    return False


class Response(object):
    """One billable API request, assembled from every row that shares its id."""

    def __init__(self):
        self.model = ""
        self.timestamp = ""
        self.input = self.write_5m = self.write_1h = self.read = 0
        self.output = self.thinking = 0
        self.model_s = 0.0
        self.handback_chars = 0

    def absorb(self, row, usage):
        self.timestamp = self.timestamp or row.get("timestamp") or ""
        self.model = self.model or (row.get("message") or {}).get("model") or ""
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
    def unrecorded(self):
        """Output tokens missing from a final response whose usage never landed (a lower bound)."""
        if not self.handback_chars or self.output >= self.handback_chars / STALE:
            return 0.0
        return max(0.0, self.handback_chars / CHARS_PER_TOKEN - self.output)

    def unrecorded_cost(self):
        return self.unrecorded * RATES.get(self.model, (0.0, 0.0, 0.0))[1] / MILLION

    def cost(self):
        """(output $, cache-write $, cache-read $, input $). An unpriced model costs 0."""
        rin, rout, rread = RATES.get(self.model, (0.0, 0.0, 0.0))
        return (self.output * rout / MILLION,
                (self.write_5m * WRITE_5M + self.write_1h * WRITE_1H) * rin / MILLION,
                self.read * rread / MILLION,
                self.input * rin / MILLION)


class Transcript(object):
    """One transcript file: the showrunner, or one subagent."""

    def __init__(self, path):
        self.path = path
        self.responses = []
        self.handbacks = []     # (timestamp, tokens) - the showrunner's only
        self.role = "showrunner"
        self.description = ""
        self.agent_id = ""
        self.tool_s = 0.0
        meta = path[:-len(".jsonl")] + ".meta.json"
        if "/subagents/" in path.replace(os.sep, "/"):
            self.role = "subagent"
            self.agent_id = os.path.basename(path)[len("agent-"):-len(".jsonl")]
            try:
                with open(meta, encoding="utf-8") as fh:
                    data = json.load(fh)
                self.role = str(data.get("agentType") or "subagent")
                self.description = str(data.get("description") or "")
            except (OSError, ValueError):
                pass
        self._read()

    def _read(self):
        groups, order, names, events = {}, [], {}, []
        for row in rows(self.path):
            if row.get("isSidechain") and self.role == "showrunner":
                continue
            message = row.get("message") if isinstance(row.get("message"), dict) else {}
            content = message.get("content")
            blocks = content if isinstance(content, list) else []
            stamp = row.get("timestamp") or ""
            kind = row.get("type")
            if kind in ("assistant", "user") and stamp:
                events.append((stamp, kind, message.get("id") or "",
                               [b.get("id") for b in blocks
                                if isinstance(b, dict) and b.get("type") == "tool_use"],
                               [b.get("tool_use_id") for b in blocks
                                if isinstance(b, dict) and b.get("type") == "tool_result"]))
            if kind == "user" and self.role == "showrunner":
                if has_mark(content):
                    self.handbacks.append((stamp, text_length(content) / CHARS_PER_TOKEN))
                for b in blocks:
                    if (isinstance(b, dict) and b.get("type") == "tool_result"
                            and names.get(b.get("tool_use_id")) in HANDBACK_TOOLS):
                        self.handbacks.append(
                            (stamp, text_length(b.get("content")) / CHARS_PER_TOKEN))
            if kind == "attachment" and self.role == "showrunner":
                queued = row.get("attachment") if isinstance(row.get("attachment"), dict) else {}
                if has_mark(queued.get("prompt")):
                    self.handbacks.append((stamp, text_length(queued["prompt"]) / CHARS_PER_TOKEN))
            if kind != "assistant":
                continue
            for b in blocks:
                if isinstance(b, dict) and b.get("type") == "tool_use":
                    names[b.get("id")] = b.get("name")
            usage = message.get("usage") or {}
            if not usage or message.get("model") in SYNTHETIC:
                continue
            key = (row.get("requestId") or "", message.get("id") or "")
            if not any(key):
                key = (row.get("uuid") or str(len(order)),)
            if key not in groups:
                groups[key] = Response()
                order.append(key)
            groups[key].absorb(row, usage)
            groups[key].handback_chars += sum(
                len(json.dumps(b.get("input"))) for b in blocks
                if isinstance(b, dict) and b.get("type") == "tool_use"
                and b.get("name") == FINAL_TOOL)
        self.responses = [groups[k] for k in order]
        by_id = dict((k[1], groups[k]) for k in order if len(k) == 2 and k[1])
        self._timing(events, by_id)

    def _timing(self, events, by_id):
        """Model seconds per response, and tool seconds, from timestamps and ids alone.

        A response runs from the last user-side row before it (the message or tool result it
        answers) to its own last row: rows are written as content blocks complete, so stopping
        at the first row would drop the text and tool calls streamed after the thinking.
        """
        events.sort(key=lambda e: e[0])
        last_user, start, end, pending = None, {}, {}, {}
        for stamp, kind, mid, uses, results in events:
            t = seconds(stamp)
            if t is None:
                continue
            if kind == "assistant":
                if mid and mid not in start and last_user is not None:
                    start[mid] = last_user
                if mid:
                    end[mid] = t
                last_user = None
                for tid in uses:
                    pending[tid] = t
            else:
                for tid in results:
                    if tid in pending:
                        self.tool_s += max(0.0, t - pending.pop(tid))
                last_user = t
        for mid, t0 in start.items():
            if mid in by_id:
                by_id[mid].model_s = max(0.0, end[mid] - t0)


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


def within(stamp, since, until):
    return not ((since and stamp < since) or (until and stamp > until))


def summarise(paths, since=None, until=None, match=None):
    """Per-role totals, per-agent rows and the showrunner's context, as a plain dict."""
    pattern = re.compile(match) if match else None
    roles, agents = {}, []
    showrunner = None
    for path in paths:
        t = Transcript(path)
        if pattern and (t.role == "showrunner" or not pattern.search(t.description)):
            continue
        rs = [r for r in t.responses if within(r.timestamp, since, until)]
        if not rs:
            continue
        row = {"role": t.role, "agent": t.agent_id, "description": t.description,
               "spawns": 1, "responses": len(rs), "model_s": sum(r.model_s for r in rs),
               "output": sum(r.output for r in rs), "thinking": sum(r.thinking for r in rs),
               "input": sum(r.input for r in rs), "cache_read": sum(r.read for r in rs),
               "cache_write": sum(r.write_5m + r.write_1h for r in rs),
               "models": sorted(set(r.model for r in rs))}
        parts = [r.cost() for r in rs]
        row["output_usd"] = sum(p[0] for p in parts)
        row["cache_write_usd"] = sum(p[1] for p in parts)
        row["cache_read_usd"] = sum(p[2] for p in parts)
        row["cost"] = sum(sum(p) for p in parts)
        row["unrecorded"] = sum(r.unrecorded for r in rs)
        row["unrecorded_usd"] = sum(r.unrecorded_cost() for r in rs)
        agents.append(row)
        total = roles.setdefault(t.role, dict((k, 0) for k in row if k not in
                                              ("role", "agent", "description", "models")))
        for k in total:
            total[k] += row[k]
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
            }
    unpriced = {}
    for a in agents:
        for m in a["models"]:
            if m not in RATES and m not in SYNTHETIC:
                unpriced[m] = unpriced.get(m, 0) + a["responses"]
    return {"roles": roles, "agents": agents, "showrunner": showrunner,
            "total": sum(r["cost"] for r in roles.values()),
            "unrecorded_usd": sum(r["unrecorded_usd"] for r in roles.values()),
            "unpriced": unpriced}


def render(result, show_agents=False):
    out = []
    head = ("%-14s %6s %6s %8s %9s %6s %10s %10s %9s %9s %9s %9s"
            % ("role", "spawns", "resp", "model s", "output", "think", "c.write", "c.read",
               "out $", "write $", "read $", "cost $"))
    out.append(head)
    order = sorted(result["roles"].items(), key=lambda kv: -kv[1]["cost"])
    for role, r in order:
        think = 100.0 * r["thinking"] / r["output"] if r["output"] else 0.0
        out.append("%-14s %6d %6d %8.0f %9d %5.0f%% %10d %10d %9.2f %9.2f %9.2f %9.2f"
                   % (role, r["spawns"], r["responses"], r["model_s"], r["output"], think,
                      r["cache_write"], r["cache_read"], r["output_usd"], r["cache_write_usd"],
                      r["cache_read_usd"], r["cost"]))
    out.append("%-14s %s %9.2f" % ("total", " " * 110, result["total"]))
    for model, n in sorted(result.get("unpriced", {}).items()):
        # A model with no rate would cost 0 and look cheap: say so rather than fall silent.
        out.append("warn: no rate for %s (agents with %d responses on it); their cost is "
                   "counted as $0 - add it to RATES" % (model, n))
    missing = [(role, r) for role, r in order if r["unrecorded"]]
    if missing:
        out.append("unrecorded final responses, a lower bound from hand-back length: "
                   + " · ".join("%s ~%.1fk tokens $%.2f" % (role, r["unrecorded"] / 1000,
                                                           r["unrecorded_usd"])
                                for role, r in missing)
                   + " · total $%.2f" % result["unrecorded_usd"])
    s = result["showrunner"]
    if s:
        out.append("")
        out.append("showrunner context: mean %.0fk, peak %.0fk tokens over %d responses"
                   % (s["context_mean"] / 1000, s["context_peak"] / 1000, s["responses"]))
        share = 100.0 * s["handback_rereads"] / s["cache_read_tokens"] if s["cache_read_tokens"] else 0
        out.append("hand-backs in: %d, ~%.1fk tokens, ~%.1fM re-read tokens (%.0f%% of its cache reads)"
                   % (s["handbacks"], s["handback_tokens"] / 1000,
                      s["handback_rereads"] / MILLION, share))
    if show_agents:
        out.append("")
        for a in sorted(result["agents"], key=lambda a: (a["role"], a["description"])):
            think = 100.0 * a["thinking"] / a["output"] if a["output"] else 0.0
            out.append("%-14s %-40s %4d resp %6.0f s %7d out %4.0f%% think  $%6.2f"
                       % (a["role"], (a["description"] or a["agent"])[:40], a["responses"],
                          a["model_s"], a["output"], think, a["cost"]))
    out.append("")
    out.append("rates, $/MTok in/out/read: " + " · ".join(
        "%s %g/%g/%g" % (m, *RATES[m]) for m in sorted(RATES)
        if any(m in a["models"] for a in result["agents"])))
    return "\n".join(out)


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("session")
    ap.add_argument("--transcripts", help="directory holding the session transcripts")
    ap.add_argument("--since", help="ISO timestamp (UTC); responses before it are left out")
    ap.add_argument("--until", help="ISO timestamp (UTC); responses after it are left out")
    ap.add_argument("--match", help="regex on a subagent's spawn description")
    ap.add_argument("--agents", action="store_true", help="one line per agent as well")
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args(argv)
    try:
        paths = transcripts_for(args.session, args.transcripts or default_transcripts())
    except (FileNotFoundError, ValueError) as exc:
        sys.stderr.write("trace: %s\n" % exc)
        return 1
    result = summarise(paths, args.since, args.until, args.match)
    print(json.dumps(result, indent=1) if args.json else render(result, args.agents))
    return 0


if __name__ == "__main__":
    sys.exit(main())
