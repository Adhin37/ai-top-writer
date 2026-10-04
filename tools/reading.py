#!/usr/bin/env python3
"""The beta reader's serial memory: one reading folder per novel, and a fresh view of it per round.

`reading/<id>/` holds everything the reader did for one novel; `<id>` is neutral (`export_prose.py
--print-id`), and `tools/clean.py` maps it back to its novel. `reading/<id>/shelf/` is the reader's
shelf: the accepted chapters, prose only, as `ch01.md` … `chNN.md`, and `notes.md`, the reader's
memory in its own words.

A draft is never read in the shelf itself. Each round gets its own folder, `reading/<id>/chNN-rK/`,
holding a copy of the notes, the last two accepted chapters and the draft as `pending/chNN.md`.
The round's fresh reader updates the notes there, and the report is filed there. So no round's
reader sees an earlier round, and a draft-round reader's beliefs never reach the shelf: after
ACCEPT the clerk copies the accepted round's notes onto the shelf, byte for byte.

Usage:
  reading.py id NOVEL
  reading.py round NOVEL N DRAFT K     build reading/<id>/chNN-rK/ and print its path
  reading.py accept NOVEL N ROUND_DIR  chapter N's file onto the shelf; the round's notes become
                                       the reader's memory
  reading.py fresh NOVEL N             reading/<id>/fresh-chNN/: ch01 … chNN, no notes, for a
                                       reader who re-reads everything (every 10 chapters)
  reading.py adopt NOVEL FRESH_DIR     a fresh reader's notes replace the running ones

NOVEL is the novel directory. Notes over 800 words are reported, never cut: the reader compresses
its own memory.
"""
import argparse
import os
import re
import shutil
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import export_prose  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
NOTES_CAP = 800
REREAD_EVERY = 10


def folder(novel, root=ROOT):
    """reading/<id>/: everything the reader did for this novel."""
    return os.path.join(root, "reading", export_prose.novel_id(novel))


def shelf(novel, root=ROOT):
    return os.path.join(folder(novel, root), "shelf")


def round_dir(novel, n, k, root=ROOT):
    return os.path.join(folder(novel, root), "ch%02d-r%d" % (n, k))


def fresh_dir(novel, n, root=ROOT):
    return os.path.join(folder(novel, root), "fresh-ch%02d" % n)


def chapter_file(novel, n):
    """The accepted chapter N's file in `chapters/`, or None."""
    d = os.path.join(novel, "chapters")
    for name in sorted(os.listdir(d)) if os.path.isdir(d) else []:
        m = re.match(r"^(\d+)-.*\.md$", name)
        if m and int(m.group(1)) == n:
            return os.path.join(d, name)
    return None


def words(path):
    with open(path, encoding="utf-8") as fh:
        return len(fh.read().split())


def notes_line(path):
    n = words(path)
    over = " — over %d; the next reader compresses it" % NOTES_CAP if n >= NOTES_CAP else ""
    return "notes %s: %d words%s" % (os.path.relpath(path, ROOT), n, over)


def build_round(novel, n, draft, k, root=ROOT):
    """reading/<id>/chNN-rK/, rebuilt from scratch. Returns its path."""
    base = shelf(novel, root)
    out = round_dir(novel, n, k, root)
    if os.path.isdir(out):
        shutil.rmtree(out)
    os.makedirs(out)
    notes = os.path.join(base, "notes.md")
    if os.path.isfile(notes):
        shutil.copyfile(notes, os.path.join(out, "notes.md"))
    for prev in (n - 2, n - 1):
        src = os.path.join(base, "ch%02d.md" % prev)
        if prev > 0 and os.path.isfile(src):
            shutil.copyfile(src, os.path.join(out, "ch%02d.md" % prev))
    export_prose.export([draft], os.path.join(out, "pending"), as_name="ch%02d.md" % n)
    return out


def accept(novel, n, round_dir, root=ROOT):
    """Put chapter N on the shelf and make the round's notes the reader's memory. Returns lines
    to print."""
    src = chapter_file(novel, n)
    if src is None:
        raise ValueError("no accepted chapter %d in %s/chapters" % (n, novel))
    base = shelf(novel, root)
    written = export_prose.export([src], base, as_name="ch%02d.md" % n)
    out = ["chapter %s" % os.path.relpath(written[0], root)]
    notes = os.path.join(round_dir, "notes.md")
    if os.path.isfile(notes):
        shutil.copyfile(notes, os.path.join(base, "notes.md"))
        out.append(notes_line(os.path.join(base, "notes.md")))
    else:
        out.append("warn: %s has no notes.md; the reader's memory is unchanged" % round_dir)
    if n % REREAD_EVERY == 0:
        out.append("due: a fresh reader re-reads ch01–ch%02d before chapter %d "
                   "(reading.py fresh)" % (n, n + 1))
    return out


def build_fresh(novel, n, root=ROOT):
    base = shelf(novel, root)
    out = fresh_dir(novel, n, root)
    if os.path.isdir(out):
        shutil.rmtree(out)
    os.makedirs(out)
    for i in range(1, n + 1):
        src = os.path.join(base, "ch%02d.md" % i)
        if not os.path.isfile(src):
            raise ValueError("the shelf has no ch%02d.md" % i)
        shutil.copyfile(src, os.path.join(out, "ch%02d.md" % i))
    return out


def adopt(novel, fresh_dir, root=ROOT):
    notes = os.path.join(fresh_dir, "notes.md")
    if not os.path.isfile(notes):
        raise ValueError("%s has no notes.md" % fresh_dir)
    dst = os.path.join(shelf(novel, root), "notes.md")
    shutil.copyfile(notes, dst)
    return notes_line(dst)


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("id").add_argument("novel")
    r = sub.add_parser("round")
    for a in ("novel", "n", "draft", "k"):
        r.add_argument(a)
    a_ = sub.add_parser("accept")
    for a in ("novel", "n", "round_dir"):
        a_.add_argument(a)
    f = sub.add_parser("fresh")
    f.add_argument("novel")
    f.add_argument("n")
    d = sub.add_parser("adopt")
    d.add_argument("novel")
    d.add_argument("fresh_dir")
    args = ap.parse_args(argv)
    try:
        if args.cmd == "id":
            print(export_prose.novel_id(args.novel))
        elif args.cmd == "round":
            out = build_round(args.novel, int(args.n), args.draft, int(args.k))
            print(os.path.relpath(out, ROOT))
            for dirpath, _dirs, files in sorted(os.walk(out)):
                for name in sorted(files):
                    print("  " + os.path.relpath(os.path.join(dirpath, name), out))
        elif args.cmd == "accept":
            print("\n".join(accept(args.novel, int(args.n), args.round_dir)))
        elif args.cmd == "fresh":
            print(os.path.relpath(build_fresh(args.novel, int(args.n)), ROOT))
        else:
            print(adopt(args.novel, args.fresh_dir))
    except (ValueError, OSError) as exc:
        sys.stderr.write("reading: %s\n" % exc)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
