#!/usr/bin/env python3
"""PreToolUse hook: which role may read and write which paths.

Registered once in `.claude/settings.json` for Read|Grep|Glob|Write|Edit|MultiEdit|NotebookEdit|Bash.
It reads the hook payload on stdin, and exits 2 with a reason on stderr to refuse a call (0 allows it).

Who is calling: a payload with no `agent_id` is the main session (the showrunner); otherwise
`agent_type` names the role. Roles not in ROLES are not judged — the guard fails open on anything it
was not written for, because a guard that blocks work it was never meant to judge gets switched off.

Two kinds of role:
  * **cold** roles (beta reader, judge) read only an allowlist. Everything else — the bible, the
    plan, the author's intent — is exactly what they must not see. Their searches must be scoped.
  * **working** roles read everything except a denylist (other roles' rubrics, experiment arms,
    maintainer docs). This is routing, not a sandbox: it keeps the writer from writing toward the
    reader's questionnaire and the planner from designing toward the judge. A working role's search
    must not reach a denied folder: `Grep` over the project root, or over `kb/`, is refused
    (ripgrep skips gitignored `reading/` and `bench/`, but not `kb/judge/` or `docs/`).
Every role writes only its allowlist. An experiment's variant of a role, `<role>--<arm>` (an agent
file that changes only effort or model, `tools/bench.py`), is held to its role's rules.

Bash: the cold roles are given none, which is their real wall. A working role that has Bash (clerk,
continuity editor) may run only the project's tools, `python3 tools/<name>.py ...`, optionally piped
into `head` or `tail`; `cat reading/...` or `python3 -c` would walk around every rule above. A role
whose spec has `bash` runs only the tools it names (the canon researcher: `canon_fetch.py`, `scaffold.py`).
The main session may do anything, except write under novels/ while a `.test-run` file exists at
the project root (a benchmark run measures the room, not the showrunner).

Every Read it allows is appended to `docs/sessions/<session>.reads.tsv` (time, session, agent id,
role, path), so `tools/trace.py` knows exactly which `kb/` docs each role opened. The log never
blocks a call: if it cannot be written, the call goes ahead unlogged.
"""
import datetime
import json
import os
import re
import sys

COMMON_DENY = ["bench/**", "docs/**", "kb/judge/**"]
CRITIC_KBS = ["kb/beta-reader/**", "kb/story-editor/**", "kb/line-editor/**",
              "kb/continuity-editor/**", "kb/shared/grading.md"]

ROLES = {
    "beta-reader": {
        "read_only": ["reading/**", "kb/beta-reader/**"],
        "write": ["reading/**"],
        "why": "a beta reader knows only the pages in its reading folder - anything else is "
               "context a real reader would not have",
    },
    "judge": {
        "read_only": ["bench/*/blind/**", "kb/judge/**", "kb/shared/grading.md"],
        "write": [],
        "why": "a judge reads only the blind copies it was pointed at",
    },
    "writer": {
        "read_deny": COMMON_DENY + ["reading/**"] + CRITIC_KBS,
        "write": ["novels/*/work/**", "novels/*/chapters/**"],
        "why": "the writer works from the beat sheet, the bible and the editor's notes - not from "
               "the reader's questionnaire or the critics' rubrics",
    },
    "planner": {
        "read_deny": COMMON_DENY + ["kb/beta-reader/**", "kb/shared/grading.md"],
        "write": ["novels/*/novel.md", "novels/*/bible/**", "novels/*/plan/**",
                  "novels/*/state/**", "novels/*/work/**"],
        "why": "the planner designs the story, not toward the reader's questionnaire or the judge",
    },
    "story-editor": {
        "read_deny": COMMON_DENY,
        "write": ["novels/*/work/**"],
        "why": "the story editor's notes go to work/; experiment arms and maintainer docs are not "
               "part of the loop",
    },
    "line-editor": {
        "read_deny": COMMON_DENY + ["reading/**", "kb/beta-reader/**"],
        "write": ["novels/*/work/**", "novels/*/chapters/**"],
        "why": "the line editor polishes the accepted draft; reader reports are the story "
               "editor's input",
    },
    "continuity-editor": {
        "read_deny": COMMON_DENY + ["reading/**", "kb/beta-reader/**"],
        "write": ["novels/*/work/**"],
        "why": "the continuity editor checks the draft against the bible and state",
    },
    "clerk": {
        "read_deny": COMMON_DENY,
        "write": ["novels/*/state/**", "novels/*/plan/**", "novels/*/work/**", "reading/**"],
        "why": "the clerk writes state after a chapter is accepted",
    },
    "canon-researcher": {
        "read_deny": COMMON_DENY + ["reading/**"] + CRITIC_KBS,
        "write": ["novels/*/bible/canon.md", "novels/*/work/canon/**"],
        "bash": ["canon_fetch", "scaffold"],
        "why": "the canon researcher records what the source work says, in bible/canon.md; the "
               "story is the planner's",
    },
}

WRITE_TOOLS = {"Write", "Edit", "MultiEdit", "NotebookEdit"}
SEARCH_TOOLS = {"Grep", "Glob"}
GLOB_CHARS = re.compile(r"[*?\[{]")
# A working role's Bash: one project tool, optionally piped into head or tail. No other shell syntax.
TOOL_CMD = re.compile(r"^python3\s+(?:\S*/)?tools/([\w-]+)\.py(?:\s+[^\s;&|`$<>(){}\\]+)*"
                      r"(?:\s+2>&1)?"
                      r"(?:\s*\|\s*(?:head|tail)(?:\s+-n)?(?:\s+-?\d+)?)*\s*$")


def _glob_re(pattern):
    """`**` any depth, `*` one segment, `?` one character. Anchored."""
    out, i = [], 0
    while i < len(pattern):
        if pattern.startswith("**", i):
            out.append(".*")
            i += 2
        elif pattern[i] == "*":
            out.append("[^/]*")
            i += 1
        elif pattern[i] == "?":
            out.append("[^/]")
            i += 1
        else:
            out.append(re.escape(pattern[i]))
            i += 1
    return re.compile("^" + "".join(out) + "$")


def matches(pattern, rel):
    """True if the repo-relative path `rel` falls under `pattern`. `dir/**` also matches `dir`."""
    if _glob_re(pattern).match(rel):
        return True
    if pattern.endswith("/**") and _glob_re(pattern[:-3]).match(rel):
        return True
    return False


def project_root(payload):
    cwd = payload.get("cwd")
    return os.path.realpath(os.environ.get("CLAUDE_PROJECT_DIR")
                            or (cwd if isinstance(cwd, str) and cwd else os.getcwd()))


def relpath(path, root):
    """Repo-relative POSIX path, "" for the root itself, None for anything outside the project.
    Symlinks, `..` and a leading `//` are resolved first, so an alias cannot pass for an outsider."""
    p = path if os.path.isabs(path) else os.path.join(root, path)
    p = os.path.realpath(p)
    root = os.path.realpath(root)
    if p == root:
        return ""
    if p.startswith(root + os.sep):
        return p[len(root) + 1:].replace(os.sep, "/")
    return None


def _static_prefix(pattern):
    """The part of a glob before its first wildcard segment: `reading/r1/*.md` -> `reading/r1`."""
    segs = []
    for seg in pattern.replace(os.sep, "/").split("/"):
        if GLOB_CHARS.search(seg):
            break
        segs.append(seg)
    return "/".join(segs)


def _path_arg(ti, *keys):
    for key in keys:
        val = ti.get(key)
        if isinstance(val, str) and val:
            return val
    return None


def _search_targets(tool, ti):
    """A search with no path searches the working directory, so its target is the root itself.
    A Glob searches `path` joined with the pattern's fixed part: `reading/r1/*.md` with no path is
    scoped to reading/r1, and `**/*.md` is not scoped at all."""
    base = _path_arg(ti, "path") or ""
    pattern = _path_arg(ti, "pattern") if tool == "Glob" else None
    if not pattern:
        return [("search", base or ".")]
    prefix = _static_prefix(pattern)
    if os.path.isabs(pattern):
        out = [("search", prefix or os.sep)]
    else:
        out = [("search", os.path.join(base or ".", prefix) if prefix else (base or "."))]
    if ".." in pattern.replace(os.sep, "/").split("/"):
        out.append(("search", os.sep))  # climbs out of wherever it starts: judge it as outside
    return out


def targets(payload):
    """(kind, path) pairs this call touches; kind is 'read' or 'write'."""
    tool = str(payload.get("tool_name") or "")
    ti = payload.get("tool_input") or {}
    if not isinstance(ti, dict):
        return []
    if tool in WRITE_TOOLS:
        path = _path_arg(ti, "file_path", "notebook_path")
        return [("write", path)] if path else []
    if tool == "Read":
        path = _path_arg(ti, "file_path")
        return [("read", path)] if path else []
    if tool in SEARCH_TOOLS:
        return _search_targets(tool, ti)
    if tool == "Bash":
        cmd = ti.get("command")
        return [("bash", cmd if isinstance(cmd, str) else "")]
    return []


def _showrunner_verdict(payload, root):
    """The main session is free, except under novels/ while a test run is armed."""
    if not os.path.exists(os.path.join(root, ".test-run")):
        return None
    for kind, path in targets(payload):
        if kind != "write":
            continue
        rel = relpath(path, root)
        if rel is not None and matches("novels/**", rel):
            return ("`%s`: a test run is armed (.test-run exists), and the showrunner writes "
                    "nothing under novels/ during a run - a chapter repaired by hand measures the "
                    "showrunner, not the room" % rel)
    return None


def _denied_below(spec, rel):
    """A denied folder inside the searched one: `kb/judge/**` lies below `kb` and below the root."""
    for pattern in spec["read_deny"]:
        fixed = _static_prefix(pattern)
        if fixed and (rel == "" or fixed.startswith(rel + "/")):
            return fixed
    return None


def _one_target(spec, kind, rel, shown):
    if kind == "bash":
        m = None if "read_only" in spec else TOOL_CMD.match(shown.strip())
        if not m:
            return "`%s`: your shell runs the project's tools only (python3 tools/<name>.py)" % (
                shown.strip()[:80])
        if "bash" in spec and m.group(1) not in spec["bash"]:
            return "`%s`: your shell runs %s only" % (
                shown.strip()[:80], ", ".join("tools/%s.py" % t for t in spec["bash"]))
        return None
    if kind == "write":
        if rel is None or not any(matches(p, rel) for p in spec["write"]):
            return "`%s` is not yours to write" % shown
        return None
    if "read_only" in spec:
        if rel == "":
            return "this search is unscoped"
        if rel is None or not any(matches(p, rel) for p in spec["read_only"]):
            return "`%s` is not yours to open" % shown
        return None
    if rel is not None and any(matches(p, rel) for p in spec["read_deny"]):
        return "`%s` is not yours to open" % shown
    if kind == "search":
        if rel is None:
            return "this search leaves the project"
        below = _denied_below(spec, rel)
        if below:
            return "this search reaches `%s`; scope it to the folder you need" % below
    return None


def role_of(agent_type):
    """The role an agent type answers to: `story-editor--medium` is the story editor."""
    return str(agent_type or "").strip().split("--", 1)[0]


def verdict(payload):
    """None to allow, or the reason the call is refused."""
    root = project_root(payload)
    if not payload.get("agent_id"):
        return _showrunner_verdict(payload, root)
    spec = ROLES.get(role_of(payload.get("agent_type")))
    if spec is None:
        return None                     # a role this guard was not written for
    for kind, path in targets(payload):
        rel = None if kind == "bash" else relpath(path, root)
        what = _one_target(spec, kind, rel, path if kind == "bash" or rel is None else rel)
        if what:
            return "%s - %s" % (what, spec["why"])
    return None


def log_read(payload):
    """Append an allowed Read to the session's read log. Never raises."""
    try:
        if payload.get("tool_name") != "Read":
            return
        path = _path_arg(payload.get("tool_input") or {}, "file_path")
        session = re.sub(r"[^\w.-]", "", str(payload.get("session_id") or ""))
        if not path or not session:
            return
        root = project_root(payload)
        rel = relpath(path, root)
        role = str(payload.get("agent_type") or "").strip() if payload.get("agent_id") else ""
        stamp = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%fZ")
        out = os.path.join(root, "docs", "sessions", session + ".reads.tsv")
        os.makedirs(os.path.dirname(out), exist_ok=True)
        with open(out, "a", encoding="utf-8") as fh:
            fh.write("\t".join((stamp, session, str(payload.get("agent_id") or ""),
                                role or "showrunner", rel if rel is not None else path)) + "\n")
    except Exception:       # a log must never stop the call it records
        pass


def main():
    try:
        payload = json.loads(sys.stdin.read() or "{}")
    except (ValueError, TypeError):
        return 0
    if not isinstance(payload, dict):
        return 0
    why = verdict(payload)
    if why:
        sys.stderr.write("Blocked: %s.\nIf your task genuinely needs it, say so in your report "
                         "and carry on with what you have.\n" % why)
        return 2
    log_read(payload)
    return 0


if __name__ == "__main__":
    sys.exit(main())
