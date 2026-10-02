#!/usr/bin/env python3
"""Check that a novel's state files agree with its chapters, its plan and each other.

Bookkeeping only: one block per accepted chapter, in chapter order, with its keys; every thread id
a block or a plan row uses has a row in `state/threads.md`; a planned thread the chapter skipped;
the scene log and timeline cover every chapter; the reader ledger's statuses are in the form the
clerk writes. Formats: `docs/novel-format.md`.

Findings print as `level check: detail` (`defect`, `warn`, `note`), then a count line that ends in
`clean` when there is no defect and no warn. It reports and never gates: the exit status is 0
unless the novel cannot be found.

Usage:
  state_check.py NOVEL_DIR
  state_check.py NOVEL_DIR --last N     (print the last N continuity blocks, and nothing else)
"""
import argparse
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from lib import mdio  # noqa: E402
from lib.novel import BLOCK_KEYS, BLOCK_REQUIRED, Novel, thread_refs  # noqa: E402

THREAD_STATUS = ("planned", "open", "paid", "subverted", "dropped")
LEDGER_STATUS = re.compile(r"^(?:owed|landed ch\s?\d+|partly ch\s?\d+|moved to ch\s?\d+)\b", re.I)
YES_NO = ("yes", "no")


def first_int(text):
    m = re.search(r"\d+", str(text or ""))
    return int(m.group(0)) if m else None


class Findings(object):
    def __init__(self):
        self.found = []

    def add(self, level, check, detail):
        self.found.append((level, check, detail))

    def lines(self):
        order = {"defect": 0, "warn": 1, "note": 2}
        out = ["%s %s: %s" % f for f in sorted(self.found, key=lambda f: order[f[0]])]
        n = {lv: sum(1 for f in self.found if f[0] == lv) for lv in order}
        tail = "%d defect · %d warn · %d note" % (n["defect"], n["warn"], n["note"])
        return out + [tail + (" — clean" if not n["defect"] and not n["warn"] else "")]


def check_blocks(nov, out):
    blocks = nov.blocks()
    chapters = {c.number: c for c in nov.chapters() if c.number}
    seen = set()
    for prev, cur in zip(blocks, blocks[1:]):
        if cur.number <= prev.number:
            out.add("defect", "blocks", "C%04d is written after C%04d; blocks are appended in "
                    "chapter order" % (cur.number, prev.number))
    for b in blocks:
        tag = "C%04d" % b.number
        if b.number in seen:
            out.add("defect", "blocks", "two blocks for chapter %d" % b.number)
        seen.add(b.number)
        keys = b.keys()
        for key in BLOCK_REQUIRED:
            if key not in keys:
                out.add("defect", "blocks", "%s has no `%s` line" % (tag, key))
        for key in keys:
            if key not in BLOCK_KEYS:
                out.add("warn", "blocks", "%s: `%s` is not a block key (%s)"
                        % (tag, key, " ".join(BLOCK_KEYS)))
        for n, text in b.stray:
            out.add("warn", "blocks", "%s line %d is not `key value`: %r" % (tag, n, text[:60]))
        ch = chapters.get(b.number)
        if ch is None:
            out.add("warn", "blocks", "%s has no chapter file" % tag)
        elif b.words is not None and b.words != ch.words:
            out.add("warn", "blocks", "%s says words %d, the chapter measures %d"
                    % (tag, b.words, ch.words))
        if not b.field("day"):
            out.add("warn", "blocks", "%s header has no `day`" % tag)
    for n in sorted(chapters):
        if n not in seen:
            out.add("defect", "blocks", "chapter %d is accepted and has no block" % n)


def check_threads(nov, out):
    rows = nov.threads()
    declared = {}
    for r in rows:
        tid = r.first().strip("* ")
        declared[tid] = r
        status = r.get("status").strip().lower()
        if status not in THREAD_STATUS:
            out.add("warn", "threads", "%s status `%s` is not one of %s"
                    % (tid, status, " ".join(THREAD_STATUS)))
    last_op = {}
    for b in nov.blocks():
        for op, tid in b.threads():
            last_op[tid] = max(last_op.get(tid, 0), b.number)
            if tid not in declared:
                out.add("defect", "threads", "C%04d uses %s, which has no row in "
                        "state/threads.md" % (b.number, tid))
            elif op == "v" and declared[tid].get("status").strip().lower() not in (
                    "paid", "subverted"):
                out.add("warn", "threads", "C%04d pays %s, and its row still says `%s`"
                        % (b.number, tid, declared[tid].get("status")))
    missing = {}
    for row in nov.plan_rows():
        for _op, tid in thread_refs(row.get("threads")):
            if tid not in declared:
                missing.setdefault(tid, first_int(row.first()))
    for tid, n in sorted(missing.items()):
        out.add("warn", "threads", "plan row %s names %s, which has no row in state/threads.md"
                % (n, tid))
    for tid, r in sorted(declared.items()):
        status = r.get("status").strip().lower()
        last = first_int(r.get("last"))
        if tid in last_op:
            if status == "planned":
                out.add("warn", "threads", "%s is `planned`, and ch %d operated on it"
                        % (tid, last_op[tid]))
            if last is not None and last < last_op[tid]:
                out.add("warn", "threads", "%s says last ch %d; ch %d operated on it"
                        % (tid, last, last_op[tid]))


def check_plan(nov, out):
    for ch in nov.chapters():
        row, block = nov.plan_row(ch.number), nov.block(ch.number)
        if row is None or block is None:
            continue
        planned = {tid for _op, tid in thread_refs(row.get("threads"))}
        done = {tid for _op, tid in block.threads()}
        skipped = planned - done
        if skipped:
            out.add("warn", "plan", "row %d plans %s; C%04d's `thr` does not touch %s"
                    % (ch.number, " ".join(sorted(planned)), ch.number,
                       " ".join(sorted(skipped))))
        extra = done - planned
        if extra:
            out.add("note", "plan", "C%04d touches %s, which row %d does not plan"
                    % (ch.number, " ".join(sorted(extra)), ch.number))


def check_scenes_and_timeline(nov, out):
    numbers = [b.number for b in nov.blocks()]
    scene_rows = nov.scenes()
    have = {}
    for r in scene_rows:
        n = first_int(r.get("ch"))
        have[n] = have.get(n, 0) + 1
        if n not in numbers:
            out.add("warn", "scenes", "a scene row for ch %s, which has no block" % r.get("ch"))
        two = r.get("two-hander").strip().lower()
        if two not in YES_NO:
            out.add("warn", "scenes", "ch %s scene %s: two-hander is `%s`, not yes or no"
                    % (r.get("ch"), r.get("scene"), two))
    for n in numbers:
        if n not in have:
            out.add("warn", "scenes", "ch %d has a block and no scene rows" % n)
    days = {first_int(r.get("ch")) for r in nov.timeline()}
    for n in numbers:
        if n not in days:
            out.add("warn", "timeline", "ch %d has a block and no timeline row" % n)


def check_ledger(nov, out):
    last = nov.last_chapter
    ledger = nov.ledger()
    for kind, due_col in (("facts", "due by ch"), ("faces", "on the page by ch"),
                          ("promises", "paid by ch")):
        for r in ledger[kind]:
            rid, status = r.first().strip("* "), r.get("status").strip()
            if not LEDGER_STATUS.match(status):
                out.add("warn", "ledger", "%s status `%s` is not owed / landed chN / partly chN "
                        "/ moved to chN" % (rid, status[:40]))
                continue
            landed = re.match(r"^(?:landed|partly) ch\s?(\d+)", status, re.I)
            if landed and int(landed.group(1)) > last:
                out.add("warn", "ledger", "%s says `%s`, past the last accepted chapter (%d)"
                        % (rid, status[:30], last))
            due = first_int(r.get(due_col))
            if status.lower().startswith("owed") and due is not None and due <= last and last:
                out.add("note", "ledger", "%s is still owed; due by ch %d" % (rid, due))


def run(nov):
    out = Findings()
    if not os.path.isfile(nov.path("state", "continuity.md")):
        out.add("note", "blocks", "no state/continuity.md yet")
    check_blocks(nov, out)
    check_threads(nov, out)
    check_plan(nov, out)
    check_scenes_and_timeline(nov, out)
    check_ledger(nov, out)
    return out


def last_blocks(nov, n):
    """The text of the last n blocks, as written."""
    lines = mdio.read_text(nov.path("state", "continuity.md")).split("\n")
    blocks = nov.blocks()[-n:] if n else []
    out = []
    for b in blocks:
        end = max([ln for ln, _k, _v in b.lines] + [ln for ln, _t in b.stray] + [b.line_no])
        out.append("\n".join(lines[b.line_no - 1:end]))
    return "\n\n".join(out)


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("novel")
    ap.add_argument("--last", type=int, metavar="N", help="print the last N blocks")
    args = ap.parse_args(argv)
    nov = Novel(args.novel)
    if not nov.exists():
        sys.stderr.write("state_check: no novel.md in %s\n" % args.novel)
        return 1
    if args.last is not None:
        print(last_blocks(nov, args.last) or "(no blocks yet)")
        return 0
    print("\n".join(run(nov).lines()))
    return 0


if __name__ == "__main__":
    sys.exit(main())
