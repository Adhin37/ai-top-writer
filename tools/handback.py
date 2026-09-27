#!/usr/bin/env python3
"""File a subagent's hand-back, verbatim, from its transcript.

Claude Code refuses a subagent's Write to a "report file" ("Subagents should return findings as
text, not write report files"), so the beta reader hands its report back as text and the showrunner
files it. Retyping it would be a paraphrase waiting to happen, so this tool copies it out of the
subagent's transcript instead:

  * default: the agent's last SubagentHandback message, whole;
  * --report: only its `# Report` block (heading to the end of *Would I click next?*). If the agent
    never handed back a report, it falls back to the content of a refused Write to `*report.md`;
  * --append: add it to the end of OUT instead of replacing OUT, fenced, under a line naming the
    agent by its spawn description. This is how an experiment's working log takes a hand-back
    without the showrunner retyping it.

Usage:
  handback.py AGENT_ID OUT [--report] [--append] [--transcripts DIR]

Transcripts are found at ~/.claude/projects/<project>/<session>/subagents/agent-<AGENT_ID>.jsonl,
where <project> is the repository path with every "/" turned into "-". --transcripts points at a
directory to search instead.
"""
import argparse
import glob
import json
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CLICK_NEXT = re.compile(r"## Would I click next\?[^\n]*\n.*?(?=\n\s*\n---|\n---\s*\n|\Z)", re.S)


def default_transcripts():
    slug = ROOT.replace(os.sep, "-")
    return os.path.join(os.path.expanduser("~/.claude/projects"), slug)


def find_transcript(agent_id, base):
    hits = glob.glob(os.path.join(base, "**", "agent-%s.jsonl" % agent_id), recursive=True)
    if not hits:
        raise FileNotFoundError("no transcript for agent %s under %s" % (agent_id, base))
    return max(hits, key=os.path.getmtime)


def tool_uses(path):
    """Every tool_use block in the transcript, in order."""
    with open(path, encoding="utf-8") as fh:
        for line in fh:
            if not line.strip():
                continue
            try:
                row = json.loads(line)
            except ValueError:
                continue
            msg = row.get("message")
            content = msg.get("content") if isinstance(msg, dict) else None
            if not isinstance(content, list):
                continue
            for block in content:
                if isinstance(block, dict) and block.get("type") == "tool_use":
                    yield block.get("name"), block.get("input") or {}


def last_handback(path):
    msg = None
    for name, inp in tool_uses(path):
        if name == "SubagentHandback" and isinstance(inp.get("message"), str):
            msg = inp["message"]
    return msg


def refused_report(path):
    content = None
    for name, inp in tool_uses(path):
        if name == "Write" and str(inp.get("file_path", "")).endswith("report.md"):
            content = inp.get("content")
    return content


def report_block(text):
    """The `# Report` block of a hand-back, or None."""
    start = text.find("# Report")
    if start < 0:
        return None
    body = text[start:]
    m = CLICK_NEXT.search(body)
    return (body[:m.end()] if m else body).rstrip() + "\n"


def description(path):
    """The spawning call's short label for the agent, from `agent-<id>.meta.json`, or ""."""
    try:
        with open(path[:-len(".jsonl")] + ".meta.json", encoding="utf-8") as fh:
            return str(json.load(fh).get("description") or "")
    except (OSError, ValueError, AttributeError):
        return ""


def log_entry(agent_id, label, text):
    """A hand-back as an experiment log takes it: a naming line, then the text, fenced."""
    fence = "````" if "```" in text else "```"
    name = "**%s** (`%s`)" % (label, agent_id) if label else "`%s`" % agent_id
    return "\n%s, hand-back verbatim:\n\n%s\n%s\n%s\n" % (name, fence, text.rstrip("\n"), fence)


def extract(path, report=False):
    msg = last_handback(path)
    if not report:
        return msg
    block = report_block(msg) if msg else None
    return block or refused_report(path)


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("agent_id")
    ap.add_argument("out")
    ap.add_argument("--report", action="store_true", help="only the `# Report` block")
    ap.add_argument("--append", action="store_true", help="append to OUT, fenced, as a log entry")
    ap.add_argument("--transcripts", help="directory to search for the transcript")
    args = ap.parse_args(argv)
    try:
        path = find_transcript(args.agent_id, args.transcripts or default_transcripts())
    except FileNotFoundError as exc:
        sys.stderr.write("handback: %s\n" % exc)
        return 1
    text = extract(path, args.report)
    if not text:
        sys.stderr.write("handback: agent %s has handed nothing back\n" % args.agent_id)
        return 1
    os.makedirs(os.path.dirname(os.path.abspath(args.out)), exist_ok=True)
    if args.append:
        with open(args.out, "a", encoding="utf-8") as fh:
            fh.write(log_entry(args.agent_id, description(path), text))
    else:
        with open(args.out, "w", encoding="utf-8") as fh:
            fh.write(text if text.endswith("\n") else text + "\n")
    print("%s -> %s (%d words%s)" % (args.agent_id, args.out, len(text.split()),
                                     ", appended" if args.append else ""))
    return 0


if __name__ == "__main__":
    sys.exit(main())
