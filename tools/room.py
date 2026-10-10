#!/usr/bin/env python3
"""The loop's deterministic steps, one call each, and the exact dispatch for what comes next.

Each showrunner turn re-reads its whole context, so every tool call it makes costs a turn. This
tool folds what a step runs (the reading view, the history report, filing the reader's report,
checks) into one call, and prints the hand-off texts of `kb/showrunner/loop.md`, filled in, for the
showrunner to send unchanged. It prints paths and short findings, never a file's content.

Steps (NOVEL is the novel directory, N the chapter, K the round):

  room.py beats NOVEL N              before the chapter: plan row, threads, the usage pause; the
                                     planner's beats task (step 1). With no reader's memory before
                                     a chapter N > 1, a fresh re-read of ch01-N-1 comes first
  room.py round NOVEL N K            after DRAFT READY: the round's reading folder, the history
                                     report (ch 3 on); the beta reader and continuity editor (step
                                     3). It never rebuilds a folder the reader worked in (--force)
  room.py judge NOVEL N K READER_ID  after both are back: files the reader's report, checks the
                                     continuity file; the story editor (step 4), and the two
                                     dispatches its verdict chooses between. Before a revision it
                                     copies draft-rK to draft-r(K+1), which the writer edits
  room.py clerk NOVEL N K            after POLISHED (K the accepted round): the notes cap; the
                                     clerk, or the reader's compression first (step 6)
  room.py fold NOVEL N               after CLERK DONE: state check, the fold count, the every-10
                                     re-read, the usage pause; the planner's fold and N+1's beats.
                                     When `judge` started N+1's beats at ACCEPT (beside the line
                                     editor), the fold continues that planner, then the writer
  room.py adopt NOVEL N READER_ID    after the every-10 fresh reader: files its report, adopts its
                                     notes
  room.py canon NOVEL PLANNER_ID     after a planner's hand-back with `gap canon` lines (fan
                                     fiction): the canon researcher's lookup, then the planner
                                     continued to finish its task
  room.py where NOVEL                which chapter and step the files say the room is at

Every step takes `--log LOG` (an experiment's working log) and `--agent ID`, repeatable: the
hand-backs of those agents are appended to LOG verbatim (tools/handback.py), followed by the
dispatches this step prints and the one its previous step's branch sent (`judge` and `adopt` add
the reader's id themselves; `fold` logs the next chapter's warm beats with the fold). `--transcripts
DIR` points tools/handback.py elsewhere (tests).

A dispatch prints as `@ spawn <agent type> as "<description>"` or `@ continue <name>` (SendMessage
to that agent's id), then its text on the next line. Spawn the dispatches of one step together.

Exit status: 0, or 2 with a `STOP:` line when the step cannot go on, or 1 on a bad call.
"""
import argparse
import json
import os
import re
import subprocess
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import export_prose  # noqa: E402
import handback  # noqa: E402
import reading  # noqa: E402
import status  # noqa: E402
import wire  # noqa: E402
from session_hooks import PAUSE_AT, fresh  # noqa: E402
from lib import mdio  # noqa: E402
from lib.novel import Novel  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TOOLS = os.path.dirname(os.path.abspath(__file__))
USAGE = os.path.join(ROOT, "docs", "sessions", "usage.json")
HISTORY_FROM = 3
MAX_ROUND = 2
AHEAD = "ahead.txt"     # judge: the next chapter's planner was offered at ACCEPT (fold continues it)
# Rounds 1 and 2 continue the round-0 continuity editor, which already holds the bible and the state,
# instead of a fresh one. False spawns a fresh one every round.
WARM_CONTINUITY = True
# Rounds 1 and 2 continue the round-0 story editor, which holds the beat sheet, the ledger and its
# own notes, so it grades the revision against what it asked for. False spawns a fresh one.
WARM_STORY_EDITOR = True


class Stop(Exception):
    """A step cannot go on; the message says why."""


# ---------------------------------------------------------------- names and paths


class Chapter(object):
    def __init__(self, novel, n, root=ROOT):
        self.novel = os.path.relpath(os.path.abspath(novel), root)
        self.nov = Novel(os.path.join(root, self.novel))
        self.root = root
        self.n = n
        self.id = export_prose.novel_id(self.nov.root)
        self.work = "%s/work/ch%04d" % (self.novel, n)

    def rel(self, path):
        return os.path.relpath(path, self.root)

    def abs(self, rel):
        return os.path.join(self.root, rel)

    def wfile(self, name):
        return "%s/%s" % (self.work, name)

    def round_dir(self, k):
        return "reading/%s/ch%02d-r%d" % (self.id, self.n, k)

    @property
    def title_slug(self):
        row = self.nov.plan_row(self.n)
        title = row.get("title") if row is not None else ""
        if not title:
            head = mdio.read_text(self.abs(self.wfile("beats.md"))).split("\n", 1)[0]
            m = re.search(r'"([^"]+)"', head)
            title = m.group(1) if m else ""
        slug = re.sub(r"[^a-z0-9]+", "-", title.strip().lower()).strip("-")
        if not slug:
            raise Stop("chapter %d has no title in plan/chapters.md or its beat sheet" % self.n)
        return slug

    @property
    def chapter_file(self):
        return "%s/chapters/%04d-%s.md" % (self.novel, self.n, self.title_slug)

    def last_notes(self):
        """The previous chapter's last notes file, or None."""
        prev = os.path.join(self.root, self.novel, "work", "ch%04d" % (self.n - 1))
        ks = [int(m.group(1)) for m in (re.match(r"^notes-r(\d+)\.md$", f)
                                        for f in (os.listdir(prev) if os.path.isdir(prev) else []))
              if m]
        return self.rel(os.path.join(prev, "notes-r%d.md" % max(ks))) if ks else None


def dispatch(kind, agent, text, label=None):
    """kind: spawn | continue."""
    head = "@ spawn %s as \"%s\"" % (agent, label) if kind == "spawn" else "@ continue %s" % agent
    return (head, text)


def render(lines, dispatches, then=None):
    out = list(lines)
    for head, text in dispatches:
        out += ["", head, text]
    if then:
        out += ["", then]
    return "\n".join(out)


# ---------------------------------------------------------------- dispatch texts (loop.md)


def planner_beats(c, warm=True):
    """Warm: planner-chNN, spawned for the previous chapter's fold, continued. Otherwise a
    fresh planner (chapter 1, a new session, or no fold)."""
    text = "Task: beats for chapter %d." % c.n
    notes = "reading/%s/shelf/notes.md" % c.id
    if c.n > 1 and os.path.isfile(c.abs(notes)):
        text += " Reader's notes: %s." % notes
    prev = c.last_notes()
    if c.n > 1 and prev:
        text += " Editor's notes for the planner: %s." % prev
    if not warm:
        return dispatch("spawn", "planner", "Novel: %s. %s" % (c.novel, text),
                        "planner-ch%02d" % c.n)
    return dispatch("continue", "planner-ch%02d" % c.n, text)


def writer(c):
    return dispatch("spawn", "writer", "Novel: %s. Chapter %d. Beat sheet: %s. Write %s."
                    % (c.novel, c.n, c.wfile("beats.md"), c.wfile("draft-r0.md")),
                    "writer-ch%02d" % c.n)


def revise(c, k):
    return dispatch("continue", "writer-ch%02d" % c.n, "Notes: %s. Revise draft-r%d.md in place: "
                    "it is a copy of draft-r%d.md." % (c.wfile("notes-r%d.md" % k), k + 1, k))


def readers(c, k):
    folder = c.round_dir(k)
    return [
        dispatch("spawn", "beta-reader", "Your reading folder is %s/. Report on chapter %d, "
                 "pending/ch%02d.md." % (folder, c.n, c.n), "beta-reader ch%02d r%d" % (c.n, k)),
        continuity(c, k),
    ]


def continuity(c, k, warm=None):
    text = "Chapter %d, round %d. Draft: %s. Lint: %s. Write %s." % (
        c.n, k, c.wfile("draft-r%d.md" % k), c.wfile("lint-r%d.txt" % k),
        c.wfile("continuity-r%d.md" % k))
    if k > 0 and (WARM_CONTINUITY if warm is None else warm):
        return dispatch("continue", "continuity-ch%02d" % c.n, text + " Your last file: %s."
                        % c.wfile("continuity-r%d.md" % (k - 1)))
    return dispatch("spawn", "continuity-editor", "Novel: %s. %s" % (c.novel, text),
                    "continuity-ch%02d" % c.n)


def story_editor(c, k, warm=None):
    files = ("Draft: %s. Writer's facts: %s. Reader's report: %s/report.md. Continuity: %s. "
             "Write %s." % (c.wfile("draft-r%d.md" % k), c.wfile("facts-r%d.md" % k),
                            c.round_dir(k), c.wfile("continuity-r%d.md" % k),
                            c.wfile("notes-r%d.md" % k)))
    hist = " History: %s." % c.wfile("history-r%d.txt" % k) if c.n >= HISTORY_FROM else ""
    if k > 0 and (WARM_STORY_EDITOR if warm is None else warm):
        return dispatch("continue", "story-editor-ch%02d" % c.n, "Chapter %d, round %d. %s%s Your "
                        "last notes: %s." % (c.n, k, files, hist, c.wfile("notes-r%d.md" % (k - 1))))
    text = "Novel: %s. Chapter %d, round %d. %s" % (c.novel, c.n, k, files)
    if c.n > 1:
        text += " Reader's memory before this chapter: reading/%s/shelf/notes.md." % c.id
    return dispatch("spawn", "story-editor", text + hist, "story-editor-ch%02d" % c.n)


def line_editor(c, k):
    text = ("Novel: %s. Polish %s into %s. Lint: %s. Continuity: %s."
            % (c.novel, c.wfile("draft-r%d.md" % k), c.chapter_file,
               c.wfile("lint-r%d.txt" % k), c.wfile("continuity-r%d.md" % k)))
    if c.n >= HISTORY_FROM:
        text += " History: %s." % c.wfile("history-r%d.txt" % k)
    return dispatch("spawn", "line-editor", text, "line-editor ch%02d" % c.n)


def compress(c, k, words):
    return dispatch("continue", "beta-reader ch%02d r%d" % (c.n, k),
                    "Your notes.md measures %d words by count, over the %d your memory holds. "
                    "Compress it to about 700, in your own words: keep what you are unsure of and "
                    "what you expect; drop what you no longer need." % (words, reading.NOTES_CAP))


def clerk(c, k):
    return dispatch("spawn", "clerk", "Novel: %s. Chapter %d: %s. Notes: %s. Facts: %s. Beats: %s. "
                    "Accepted round: %s/." % (c.novel, c.n, c.chapter_file,
                                              c.wfile("notes-r%d.md" % k),
                                              c.wfile("facts-r%d.md" % k), c.wfile("beats.md"),
                                              c.round_dir(k)),
                    "clerk ch%02d" % c.n)


def planner_fold(c, warm=False):
    """Warm: planner-ch(N+1), spawned at ACCEPT for N+1's beats, continued after them."""
    text = "Task: fold chapter %d. Fold file: %s." % (c.n, c.wfile("fold.md"))
    if warm:
        return dispatch("continue", "planner-ch%02d" % (c.n + 1), text + " Then check your beat "
                        "sheet for chapter %d against what you folded." % (c.n + 1))
    return dispatch("spawn", "planner", "Novel: %s. %s" % (c.novel, text),
                    "planner-ch%02d" % (c.n + 1))


def planner_ahead(c, k):
    """At ACCEPT of chapter N: a fresh planner for N+1's beats, while N is polished."""
    nxt = c.n + 1
    return dispatch("spawn", "planner", "Novel: %s. Task: beats for chapter %d. Chapter %d is "
                    "accepted and not yet in state/: its text is %s. Reader's notes: %s/notes.md. "
                    "Editor's notes for the planner: %s." % (
                        c.novel, nxt, c.n, c.wfile("draft-r%d.md" % k), c.round_dir(k),
                        c.wfile("notes-r%d.md" % k)), "planner-ch%02d" % nxt)


def researcher_lookup(novel, gaps):
    return dispatch("spawn", "canon-researcher", "Novel: %s. Task: lookup.\n%s"
                    % (novel, "\n".join(gaps)), "canon lookup")


def fresh_reader(c, folder):
    return dispatch("spawn", "beta-reader", "Your reading folder is %s/. There are no notes: read "
                    "every chapter in order from ch01, then report on chapter %d."
                    % (folder, c.n), "beta-reader fresh ch%02d" % c.n)


# ---------------------------------------------------------------- checks


def _bytes(path):
    with open(path, "rb") as fh:
        return fh.read()


def unwritten(c, k):
    """draft-rK is still the copy of draft-r(K-1) that `judge` made for the writer to revise."""
    new, old = c.abs(c.wfile("draft-r%d.md" % k)), c.abs(c.wfile("draft-r%d.md" % (k - 1)))
    return (k > 0 and os.path.isfile(new) and os.path.isfile(old)
            and not os.path.isfile(c.abs(c.wfile("facts-r%d.md" % k)))
            and _bytes(new) == _bytes(old))


def ahead_blocked(c):
    """Why chapter N+1's beats cannot start at N's ACCEPT, or None."""
    nxt = Chapter(c.abs(c.novel), c.n + 1, c.root)
    if c.n % reading.REREAD_EVERY == 0:
        return "the every-%d re-read comes first" % reading.REREAD_EVERY
    if nxt.nov.plan_row(nxt.n) is None:
        return "no plan row for chapter %d" % nxt.n
    if overdue(nxt.nov):
        return "the ledger has rows past due"
    if os.path.isfile(nxt.abs(nxt.wfile("beats.md"))):
        return "chapter %d already has a beat sheet" % nxt.n
    if usage_pause():
        return "the usage window is nearly spent"
    return None


def overdue(nov):
    """The ledger's rows still owed past their chapter (`status.py --debt`), as lines."""
    return [l for l in status.debt(nov) if l.startswith("overdue")]


def run_tool(args, root=ROOT):
    p = subprocess.run([sys.executable] + args, cwd=root, capture_output=True, text=True)
    return p.returncode, (p.stdout or "") + (p.stderr or "")


def usage_pause(path=USAGE, now=None):
    """A line when the 5-hour window is past PAUSE_AT by a fresh status-line reading, else None."""
    try:
        with open(path, encoding="utf-8") as fh:
            usage = json.load(fh)
    except (OSError, ValueError):
        return None
    now = now or time.time()
    if not fresh(usage, now):
        return None
    limits = usage.get("rate_limits")
    window = (limits if isinstance(limits, dict) else {}).get("five_hour") or {}
    pct = window.get("used_percentage") if isinstance(window, dict) else None
    if not isinstance(pct, (int, float)) or pct < PAUSE_AT:
        return None
    resets = window.get("resets_at")
    when = ""
    if isinstance(resets, (int, float)) and not isinstance(resets, bool):
        when = " (resets %s)" % time.strftime("%H:%M", time.localtime(resets))
    elif isinstance(resets, str) and resets:
        when = " (resets %s)" % resets
    return ("PAUSE: the 5-hour window is at %d%%%s. Start no new chapter: loop.md, "
            "\"Pause at a chapter boundary\"." % (pct, when))


def wire_defects(path):
    found = wire.check_file(path)
    return ["%s %s: %s" % f for f in found if f[0] == "defect"]


def file_report(c, k, agent_id, transcripts=None):
    out = c.round_dir(k) + "/report.md"
    args = [os.path.join(TOOLS, "handback.py"), agent_id, out, "--report"]
    if transcripts:
        args += ["--transcripts", transcripts]
    code, text = run_tool(args, c.root)
    if code != 0:
        raise Stop(text.strip() or "the reader's report could not be filed")
    return text.strip()


def append_log(log, agents, sent, transcripts=None, root=ROOT):
    """Append the agents' hand-backs, then the dispatches sent, to LOG. Returns lines to print."""
    if not log:
        return []
    out = []
    for agent_id in agents:
        args = [os.path.join(TOOLS, "handback.py"), agent_id, log, "--append"]
        if transcripts:
            args += ["--transcripts", transcripts]
        code, text = run_tool(args, root)
        out.append(("log " if code == 0 else "warn log: ") + text.strip())
    if sent:
        os.makedirs(os.path.dirname(os.path.join(root, log)) or ".", exist_ok=True)
        with open(os.path.join(root, log), "a", encoding="utf-8") as fh:
            for head, text in sent:
                fh.write("\nShowrunner, %s, verbatim:\n\n```\n%s\n```\n" % (head[2:], text))
        out.append("log %d dispatch(es) -> %s" % (len(sent), log))
    return out


# ---------------------------------------------------------------- steps


def step_beats(c):
    lines = ["ch %d · step 1 beats" % c.n]
    if c.nov.plan_row(c.n) is None:
        raise Stop("chapter %d has no plan row in plan/chapters.md: run kb/showrunner/plan.md "
                   "first" % c.n)
    if not os.path.isfile(c.nov.path("state", "threads.md")):
        raise Stop("state/threads.md is missing: the planner's ledger task writes it first")
    late = overdue(c.nov)
    if late:
        raise Stop("the ledger has rows past due: run kb/showrunner/plan.md first\n  "
                   + "\n  ".join(late))
    pause = usage_pause()
    if pause:
        lines.append(pause)
    if c.n > 1 and not os.path.isfile(c.abs("reading/%s/shelf/notes.md" % c.id)):
        prev = Chapter(c.abs(c.novel), c.n - 1, c.root)
        try:
            folder = c.rel(reading.build_fresh(c.abs(c.novel), prev.n, c.root))
        except ValueError as exc:
            raise Stop(str(exc))
        lines.append("warn: the reader has no memory before chapter %d (no reading/%s/shelf/"
                     "notes.md): a fresh reader re-reads ch01-ch%02d first" % (c.n, c.id, prev.n))
        return lines, [fresh_reader(prev, folder)], (
            "then, with its report back: python3 tools/room.py adopt %s %d <agent id>, then "
            "python3 tools/room.py beats %s %d again" % (c.novel, prev.n, c.novel, c.n)), []
    then = ("then: read %s and approve it (loop.md step 1), then send the writer:"
            % c.wfile("beats.md"))
    return lines, [planner_beats(c, warm=False)], then, [writer(c)]


def step_round(c, k, force=False):
    draft = c.wfile("draft-r%d.md" % k)
    if not os.path.isfile(c.abs(draft)):
        raise Stop("no draft: %s" % draft)
    if k > 0 and not os.path.isfile(c.abs(c.wfile("facts-r%d.md" % k))):
        raise Stop("%s has no facts-r%d.md: the writer has not finished the revision%s" % (
            draft, k, " (the draft is still the unrevised copy)" if unwritten(c, k) else ""))
    try:
        folder = reading.build_round(c.abs(c.novel), c.n, c.abs(draft), k, c.root, force)
    except ValueError as exc:
        raise Stop(str(exc))
    lines = ["ch %d · round %d · step 3 read and check" % (c.n, k),
             "reading %s/ (%s)" % (c.rel(folder), ", ".join(sorted(
                 os.path.relpath(os.path.join(d, f), folder)
                 for d, _s, fs in os.walk(folder) for f in fs)))]
    lint = c.wfile("lint-r%d.txt" % k)
    code, text = run_tool([os.path.join(TOOLS, "lint.py"), draft, "--novel", c.novel, "--out",
                           lint], c.root)
    lines.append(("lint %s" % lint) if os.path.isfile(c.abs(lint))
                 else "warn lint: %s" % text.strip()[-300:])
    if c.n >= HISTORY_FROM:
        hist = c.wfile("history-r%d.txt" % k)
        code, text = run_tool([os.path.join(TOOLS, "history.py"), c.novel, "--draft", draft,
                               "--out", hist], c.root)
        lines.append(("history %s" % hist) if code == 0 else "warn history: %s" % text.strip())
    came = [writer(c)] if k == 0 else [revise(c, k - 1)]
    return lines, readers(c, k), ("then, with both back: python3 tools/room.py judge %s %d %d "
                                  "<beta-reader agent id>" % (c.novel, c.n, k)), came


def step_judge(c, k, reader_id, transcripts=None):
    lines = ["ch %d · round %d · step 4 judge" % (c.n, k), "filed " + file_report(c, k, reader_id,
                                                                              transcripts)]
    cont = c.wfile("continuity-r%d.md" % k)
    if not os.path.isfile(c.abs(cont)):
        raise Stop("no continuity file: %s" % cont)
    lines += wire_defects(c.abs(cont))
    branches = ["", "then, on NOTES READY:"]
    if k < MAX_ROUND:
        old, new = c.wfile("draft-r%d.md" % k), c.wfile("draft-r%d.md" % (k + 1))
        if not os.path.isfile(c.abs(new)):
            with open(c.abs(new), "wb") as fh:
                fh.write(_bytes(c.abs(old)))
            lines.append("copied %s -> %s, for a revision in place" % (old, new))
        head, text = revise(c, k)
        branches += ["  REVISE  -> %s" % head, "  " + text,
                     "              and on DRAFT READY: python3 tools/room.py round %s %d %d"
                     % (c.novel, c.n, k + 1)]
    head, text = line_editor(c, k)
    if k < MAX_ROUND:
        text += " (draft-r%d.md beside it is the unrevised copy for a REVISE; leave it.)" % (k + 1)
    branches += ["  %s -> %s" % ("ACCEPT" if k < MAX_ROUND else "either", head), "  " + text]
    blocked = ahead_blocked(c)
    if blocked:
        branches.append("              (chapter %d's beats wait for room.py fold: %s)"
                        % (c.n + 1, blocked))
    else:
        head, text = planner_ahead(c, k)
        with open(c.abs(c.wfile(AHEAD)), "w", encoding="utf-8") as fh:
            fh.write("%s offered at round %d for chapter %d's beats\n" % (head[2:], k, c.n + 1))
        branches += ["           in the same message, if chapter %d is in this run: %s"
                     % (c.n + 1, head), "  " + text,
                     "              and on PLANNER DONE beats: read %s and approve it (loop.md "
                     "step 1)" % Chapter(c.abs(c.novel), c.n + 1, c.root).wfile("beats.md")]
    branches.append("              and on POLISHED: python3 tools/room.py clerk %s %d %d"
                    % (c.novel, c.n, k))
    return lines, [story_editor(c, k)], "\n".join(branches[1:]), []


def step_clerk(c, k):
    lines = ["ch %d · accepted round %d · step 6 after the chapter" % (c.n, k)]
    if not os.path.isfile(c.abs(c.chapter_file)):
        raise Stop("no polished chapter: %s" % c.chapter_file)
    came = [line_editor(c, k)]
    if unwritten(c, k + 1):
        os.remove(c.abs(c.wfile("draft-r%d.md" % (k + 1))))
        lines.append("removed draft-r%d.md, the unrevised copy" % (k + 1))
    notes = c.round_dir(k) + "/notes.md"
    if not os.path.isfile(c.abs(notes)):
        lines.append("warn: %s is missing; the reader's memory will not change" % notes)
        words = 0
    else:
        words = reading.words(c.abs(notes))
        lines.append("notes %s: %d words" % (notes, words))
    if words > reading.NOTES_CAP:
        return lines, [compress(c, k, words)], ("then: python3 tools/room.py clerk %s %d %d again "
                                                "(it counts afresh)" % (c.novel, c.n, k)), came
    return lines, [clerk(c, k)], ("then, on CLERK DONE: python3 tools/room.py fold %s %d"
                                  % (c.novel, c.n)), came


def step_fold(c, cold=False):
    lines = ["ch %d · step 6 fold" % c.n]
    code, text = run_tool([os.path.join(TOOLS, "state_check.py"), c.novel], c.root)
    found = [l for l in text.splitlines() if l.startswith(("defect", "warn"))]
    lines.append("state_check %s" % ("clean" if code == 0 and not found
                                     else "%d defect, %d warn" % (
                                         sum(l.startswith("defect") for l in found),
                                         sum(l.startswith("warn") for l in found))))
    lines += ["  " + l for l in found]
    fold = c.wfile("fold.md")
    count = 0
    if os.path.isfile(c.abs(fold)):
        for f in wire.check_file(c.abs(fold)):
            m = re.match(r"new: (\d+), stale: (\d+)", f[2])
            if m:
                count = int(m.group(1)) + int(m.group(2))
        lines.append("fold %s: %d line(s) for the bible" % (fold, count))
    else:
        lines.append("warn: no %s" % fold)
    nxt = Chapter(c.abs(c.novel), c.n + 1, c.root)
    dispatches = []
    if c.n % reading.REREAD_EVERY == 0:
        try:
            folder = c.rel(reading.build_fresh(c.abs(c.novel), c.n, c.root))
        except ValueError as exc:
            raise Stop(str(exc))
        lines.append("due: the every-%d re-read, before chapter %d" % (reading.REREAD_EVERY,
                                                                       c.n + 1))
        dispatches.append(fresh_reader(c, folder))
        then = ("then, with its report back: python3 tools/room.py adopt %s %d <agent id>"
                % (c.novel, c.n))
    else:
        then = None
    pause = usage_pause()
    if pause:
        lines.append(pause)
    have_beats = os.path.isfile(nxt.abs(nxt.wfile("beats.md")))
    if have_beats or (not cold and os.path.isfile(c.abs(c.wfile(AHEAD)))):
        # The beats ran at ACCEPT (room.py judge): fold into that planner, then the writer. Its
        # beat sheet may still be in progress: the fold waits for its PLANNER DONE beats.
        if count:
            dispatches.append(planner_fold(c, warm=True))
            if not have_beats:
                lines.append("planner-ch%02d is still on chapter %d's beats: send the fold on its "
                             "PLANNER DONE beats. If it was never sent (chapter %d is not in the "
                             "run): python3 tools/room.py fold %s %d --cold"
                             % (nxt.n, nxt.n, nxt.n, c.novel, c.n))
        head = ("on PLANNER DONE fold, with the beat sheet approved" if count
                else "with the beat sheet approved")
        then = "\n".join(([then] if then else []) + [
            "then, for chapter %d (when it is in the run), %s, send the writer:" % (nxt.n, head)])
        k, _ = last_round(c)
        return lines, dispatches, then + render([], [writer(nxt)]), [planner_ahead(c, k or 0)]
    if count:
        dispatches.append(planner_fold(c))
    beats = ["", "then, for chapter %d (when it is in the run):" % nxt.n]
    late, warm = overdue(nxt.nov), []
    if nxt.nov.plan_row(nxt.n) is None:
        beats.append("  no plan row for chapter %d: kb/showrunner/plan.md first" % nxt.n)
    if late:
        beats += ["  the ledger has rows past due: kb/showrunner/plan.md first, then "
                  "room.py beats"] + ["    " + l for l in late]
    blocked = len(beats) > 2
    if count and not blocked:
        warm = [planner_beats(nxt)]
        beats += ["  %s" % warm[0][0], "  " + warm[0][1]]
    elif not blocked:
        beats.append("  python3 tools/room.py beats %s %d (no fold: the planner is spawned "
                     "fresh)" % (c.novel, nxt.n))
    then = "\n".join(([then] if then else []) + beats[1:])
    return lines, dispatches, then, warm


def step_adopt(c, reader_id, transcripts=None):
    folder = "reading/%s/fresh-ch%02d" % (c.id, c.n)
    out = folder + "/report.md"
    args = [os.path.join(TOOLS, "handback.py"), reader_id, out, "--report"]
    if transcripts:
        args += ["--transcripts", transcripts]
    code, text = run_tool(args, c.root)
    if code != 0:
        raise Stop(text.strip())
    line = reading.adopt(c.abs(c.novel), c.abs(folder), c.root)
    return ["ch %d · the every-%d re-read" % (c.n, reading.REREAD_EVERY), "filed " + text.strip(),
            "adopted " + line], [], None, []


# ---------------------------------------------------------------- where


def step_canon(novel, agent_id, transcripts=None):
    """The planner's `gap canon` lines, verbatim, to a canon researcher; the planner after it."""
    try:
        path = handback.find_transcript(agent_id, transcripts or handback.default_transcripts())
    except FileNotFoundError as exc:
        raise Stop(str(exc))
    gaps = wire.canon_gaps(handback.last_handback(path) or "")
    if not gaps:
        raise Stop("agent %s handed back no `gap canon` line" % agent_id)
    planner = handback.description(path) or agent_id
    lines = ["canon lookup · %d question(s) from %s" % (len(gaps), planner)]
    after = dispatch("continue", planner, "Canon looked up: %s/bible/canon.md. Finish the task."
                     % novel)
    return lines, [researcher_lookup(novel, gaps)], "then, on CANON DONE:", [after]


def _read_or_none(path):
    return mdio.read_text(path) if os.path.isfile(path) else None


def last_round(c):
    ks = []
    work = c.abs(c.work)
    for name in os.listdir(work) if os.path.isdir(work) else []:
        m = re.match(r"^notes-r(\d+)\.md$", name)
        if m:
            ks.append(int(m.group(1)))
    if not ks:
        return None, None
    k = max(ks)
    m = re.search(r"\bverdict\s+(\w+)", mdio.read_text(c.abs(c.wfile("notes-r%d.md" % k))))
    return k, m.group(1) if m else None


def where(novel, root=ROOT):
    """(chapter, step line): what the files say comes next."""
    nov = Novel(os.path.join(root, os.path.relpath(os.path.abspath(novel), root)))
    n = nov.last_chapter
    if n:
        c = Chapter(novel, n, root)
        if not os.path.isfile(c.abs(c.wfile("fold.md"))):
            k, _ = last_round(c)
            return n, ("step 6: the chapter is polished; the clerk has not written fold.md -> "
                       "python3 tools/room.py clerk %s %d %d" % (c.novel, n, k or 0))
        fresh = reading.fresh_dir(c.abs(c.novel), n, root)
        shelf_notes = os.path.join(reading.shelf(c.abs(c.novel), root), "notes.md")
        if os.path.isdir(fresh) and _read_or_none(os.path.join(fresh, "notes.md")) != \
                _read_or_none(shelf_notes):
            return n, ("re-read: %s is not adopted -> python3 tools/room.py adopt %s %d "
                       "<beta-reader agent id> once the fresh reader is back"
                       % (os.path.relpath(fresh, root), c.novel, n))
    c = Chapter(novel, n + 1, root)
    if not os.path.isfile(c.abs(c.wfile("beats.md"))):
        return c.n, ("step 1: no beat sheet -> python3 tools/room.py beats %s %d"
                     % (c.novel, c.n))
    drafts = [int(m.group(1)) for m in (re.match(r"^draft-r(\d+)\.md$", f)
                                        for f in os.listdir(c.abs(c.work))) if m]
    drafts = [k for k in drafts if not unwritten(c, k)]
    if not drafts:
        return c.n, ("step 2: beats written, no draft -> approve %s, then the writer (after the "
                     "planner's fold of chapter %d, if room.py fold printed one)"
                     % (c.wfile("beats.md"), c.n - 1))
    k = max(drafts)
    kn, verdict = last_round(c)
    if kn != k:
        if not os.path.isfile(c.abs(c.round_dir(k) + "/report.md")):
            if os.path.isdir(c.abs(c.round_dir(k))):
                return c.n, ("step 3: draft-r%d is out with the readers -> python3 tools/room.py "
                             "judge %s %d %d <beta-reader agent id> once both are back"
                             % (k, c.novel, c.n, k))
            return c.n, ("step 3: draft-r%d has no reading folder -> python3 tools/room.py round "
                         "%s %d %d" % (k, c.novel, c.n, k))
        return c.n, ("step 4: round %d is read; no notes -> the story editor (room.py judge "
                     "printed its dispatch)" % k)
    if verdict == "REVISE" and k < MAX_ROUND:
        return c.n, ("step 4: REVISE at round %d -> continue writer-ch%02d for draft-r%d"
                     % (k, c.n, k + 1))
    return c.n, ("step 5: %s at round %d -> the line editor into %s"
                 % (verdict or "no verdict", k, c.chapter_file))


# ---------------------------------------------------------------- main


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("step", choices=("beats", "round", "judge", "clerk", "fold", "adopt",
                                     "canon", "where"))
    ap.add_argument("novel")
    ap.add_argument("rest", nargs="*", help="N, K, the agent id: as the step needs")
    ap.add_argument("--log", help="append hand-backs and dispatches to this working log")
    ap.add_argument("--agent", action="append", default=[], help="an agent whose hand-back "
                    "goes into --log (repeatable)")
    ap.add_argument("--force", action="store_true", help="round: rebuild a reading folder the "
                    "reader has already worked in (its work is lost)")
    ap.add_argument("--cold", action="store_true", help="fold: chapter N+1's planner was not "
                    "sent at ACCEPT; spawn a fresh one for the fold")
    ap.add_argument("--transcripts", help="directory holding the transcripts (tests)")
    ap.add_argument("--root", default=ROOT, help=argparse.SUPPRESS)
    args = ap.parse_args(argv)
    if not os.path.isfile(os.path.join(args.novel, "novel.md")):
        sys.stderr.write("room: no novel.md in %s\n" % args.novel)
        return 1
    try:
        if args.step == "where":
            n, line = where(args.novel, args.root)
            print("ch %d · %s" % (n, line))
            return 0
        need = {"beats": 1, "round": 2, "judge": 3, "clerk": 2, "fold": 1, "adopt": 2,
                "canon": 1}
        if len(args.rest) != need[args.step]:
            raise Stop("%s takes %d argument(s) after NOVEL" % (args.step, need[args.step]))
        if args.step == "canon":
            novel = os.path.relpath(os.path.abspath(args.novel), args.root)
            lines, sends, then, after = step_canon(novel, args.rest[0], args.transcripts)
            lines += append_log(args.log, list(args.agent) + [args.rest[0]], sends,
                                args.transcripts, args.root)
            print(render(lines, sends, render([then], after)))
            return 0
        c = Chapter(args.novel, int(args.rest[0]), args.root)
        k = int(args.rest[1]) if args.step in ("round", "judge", "clerk") else None
        if args.step == "beats":
            lines, sends, then, after = step_beats(c)
            came, then = [], render([then], after)
        elif args.step == "round":
            lines, sends, then, came = step_round(c, k, args.force)
        elif args.step == "judge":
            lines, sends, then, came = step_judge(c, k, args.rest[2], args.transcripts)
        elif args.step == "clerk":
            lines, sends, then, came = step_clerk(c, k)
        elif args.step == "fold":
            lines, sends, then, came = step_fold(c, args.cold)
        else:
            lines, sends, then, came = step_adopt(c, args.rest[1], args.transcripts)
        agents = list(args.agent)
        if args.step in ("judge", "adopt") and args.rest[-1] not in agents:
            agents.append(args.rest[-1])            # the reader's whole hand-back, too
        logged = sends + came if args.step == "fold" else came + sends
        lines += append_log(args.log, agents, logged, args.transcripts, args.root)
    except Stop as exc:
        print("STOP: %s" % exc)
        return 2
    except (ValueError, OSError) as exc:
        sys.stderr.write("room: %s\n" % exc)
        return 1
    print(render(lines, sends, then))
    return 0


if __name__ == "__main__":
    sys.exit(main())
