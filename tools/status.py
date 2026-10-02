#!/usr/bin/env python3
"""Where a novel stands, from its files: chapters, the next plan row, the reader's latest
click-next, ledger debt, open promises and threads, and the state check's verdict.

`--debt` prints only what the ledger owes against what the plan can deliver, for `/plan`: rows
still owed past their chapter, and rows due beyond the last planned chapter. Whether the row due
in a chapter actually carries the debt is the planner's judgement, not this tool's.

Read-only. The exit status is 0 unless the novel cannot be found.

Usage:
  status.py NOVEL_DIR
  status.py NOVEL_DIR --debt
"""
import argparse
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import export_prose  # noqa: E402
import state_check  # noqa: E402
from lib import mdio  # noqa: E402
from lib.novel import Novel  # noqa: E402
from state_check import due_chapter, first_int  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
COLD_AFTER = 5          # chapters untouched before an open thread is listed as cold
DUE_COLS = {"facts": "due by ch", "faces": "on the page by ch", "promises": "paid by ch"}


def clip(text, n=90):
    text = re.sub(r"\s+", " ", str(text or "")).strip()
    return text if len(text) <= n else text[:n - 1].rstrip() + "…"


def landed(status):
    return str(status or "").strip().lower().startswith("landed")


def describe(kind, row):
    if kind == "faces":
        return row.get("who")
    if kind == "promises":
        return row.get("what the page promises")
    fact = row.get("fact, in plain words")
    return fact


def last_round(nov, n):
    """(K, notes header) for chapter n's last notes file, or (None, '')."""
    work = nov.path("work", "ch%04d" % n)
    rounds = []
    for name in os.listdir(work) if os.path.isdir(work) else []:
        m = re.match(r"^notes-r(\d+)\.md$", name)
        if m:
            rounds.append(int(m.group(1)))
    if not rounds:
        return None, ""
    k = max(rounds)
    for line in mdio.read_text(os.path.join(work, "notes-r%d.md" % k)).split("\n"):
        if line.startswith("verdict"):
            return k, line.strip()
    return k, ""


def click_next(nov, n, reading_root):
    """The reader's click-next line for chapter n's last round: from the round's report, else from
    the story editor's notes header. '' when neither exists."""
    k, header = last_round(nov, n)
    if k is None:
        return ""
    rid = export_prose.novel_id(nov.root)
    report = os.path.join(reading_root, "%s-ch%02d-r%d" % (rid, n, k), "report.md")
    sec = mdio.section(mdio.read_text(report), "would i click next")
    lines = [l.strip() for l in sec.split("\n")[1:] if l.strip()]
    if lines:
        return "ch %d r%d: %s" % (n, k, clip(lines[0], 140))
    m = re.search(r"click-next\s+(\S+)", header)
    return "ch %d r%d: %s (from the notes; no report filed)" % (n, k, m.group(1)) if m else ""


def debt(nov):
    """Lines: what the ledger owes against what the plan can deliver."""
    last = nov.last_chapter
    planned = [first_int(r.first()) for r in nov.plan_rows() if first_int(r.first())]
    horizon = max(planned or [last])
    out = []
    ledger = nov.ledger()
    for kind in ("facts", "faces", "promises"):
        for r in ledger[kind]:
            rid, status = r.first().strip("* "), r.get("status").strip()
            if landed(status):
                continue
            cell = r.get(DUE_COLS[kind]).strip()
            due = due_chapter(cell)
            what = clip(describe(kind, r), 60)
            if due is not None and due <= last:
                out.append("overdue  %s due ch %d, %s: %s" % (rid, due, clip(status, 40), what))
            elif due is not None and due > horizon:
                out.append("beyond   %s due ch %d, past the last planned row (ch %d): %s"
                           % (rid, due, horizon, what))
            elif due is None:
                out.append("beyond   %s due \"%s\", no chapter yet: %s" % (rid, clip(cell, 30),
                                                                         what))
    return out or ["clean: every owed row is due ahead of the last chapter and inside the plan "
                   "(ch %d)" % horizon]


def report(nov, reading_root):
    last = nov.last_chapter
    out = ["%s — %s" % (nov.title, os.path.relpath(nov.root, ROOT))]
    chapters = [c for c in nov.chapters() if c.number]
    if chapters:
        cur = nov.chapter(last)
        words = sum(c.words or 0 for c in chapters)
        out.append("chapters  %d accepted · last ch %d \"%s\" · %s words in all"
                   % (len(chapters), last, cur.title if cur else "?", format(words, ",")))
    else:
        out.append("chapters  none accepted yet")

    rows = nov.plan_rows()
    ahead = [r for r in rows if (first_int(r.first()) or 0) > last]
    nxt = nov.plan_row(last + 1)
    if nxt is not None:
        out.append("next      ch %d \"%s\": %s" % (last + 1, nxt.get("title"),
                                                   clip(nxt.get("event"), 110)))
    else:
        out.append("next      ch %d has no plan row: /plan first" % (last + 1))
    out.append("plan      %d row(s) ahead of the last chapter" % len(ahead))

    if last:
        out.append("reader    %s" % (click_next(nov, last, reading_root) or
                                     "no round found for ch %d" % last))

    ledger = nov.ledger()
    owed, due_next = [], []
    for kind in ("facts", "faces"):
        for r in ledger[kind]:
            rid, status = r.first().strip("* "), r.get("status").strip()
            due = due_chapter(r.get(DUE_COLS[kind]))
            if landed(status) or due is None:
                continue
            if due <= last:
                owed.append("  %s due ch %d, %s: %s" % (rid, due, clip(status, 50),
                                                        clip(describe(kind, r), 60)))
            elif due == last + 1:
                due_next.append(rid)
    n_rows = len(ledger["facts"]) + len(ledger["faces"])
    out.append("ledger    %d fact and face rows · %d past due and not landed · due ch %d: %s"
               % (n_rows, len(owed), last + 1, ", ".join(due_next) or "none"))
    out.extend(owed)

    promises = [r for r in ledger["promises"] if not landed(r.get("status"))]
    overdue = [r for r in promises if (due_chapter(r.get("paid by ch")) or 10 ** 6) <= last]
    out.append("promises  %d open · %d past their chapter" % (len(promises), len(overdue)))
    for r in promises:
        paid = due_chapter(r.get("paid by ch"))
        flag = "  past due" if r in overdue else ""
        out.append("  %s made ch %s, paid by %s: %s%s" % (
            r.first().strip("* "), r.get("made in ch") or "?",
            "ch %d" % paid if paid else clip(r.get("paid by ch"), 30) or "?",
            clip(r.get("what the page promises"), 70), flag))

    threads = nov.threads()
    opened = [r for r in threads if r.get("status").strip().lower() == "open"]
    planned = [r for r in threads if r.get("status").strip().lower() == "planned"]
    cold = [r.first().strip("* ") for r in opened
            if last and (first_int(r.get("last")) or 0) <= last - COLD_AFTER]
    out.append("threads   %d open · %d planned · cold (untouched %d+ chapters): %s"
               % (len(opened), len(planned), COLD_AFTER, ", ".join(cold) or "none"))

    out.append("state     %s" % state_check.run(nov).lines()[-1])
    return out


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("novel")
    ap.add_argument("--debt", action="store_true", help="the ledger against the plan, only")
    ap.add_argument("--reading", default=os.path.join(ROOT, "reading"), help=argparse.SUPPRESS)
    args = ap.parse_args(argv)
    nov = Novel(args.novel)
    if not nov.exists():
        sys.stderr.write("status: no novel.md in %s\n" % args.novel)
        return 1
    print("\n".join(debt(nov) if args.debt else report(nov, args.reading)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
