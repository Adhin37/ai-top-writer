#!/usr/bin/env python3
"""What each novel left outside novels/, and how to remove it with the novel.

A novel's data is not all in `novels/<slug>/`. The beta reader's folder, `reading/<id>/`, sits
outside it on purpose (the reader's path must not name the novel, and a working role grepping the
novel must not find the reader's reports), and an experiment's `bench/<exp>/` is named for the
experiment, not the novel. This tool maps both back:

  * `reading/<id>/` belongs to the novel whose `export_prose.novel_id` is `<id>`;
  * `bench/<exp>/` belongs to the novels its files name as `novels/<slug>/` (a frozen copy,
    `<slug>--<exp>-<arm>`, counts for `<slug>`);
  * `novels/<slug>--*/` are frozen copies of `<slug>` (`tools/bench.py freeze`).

Usage:
  clean.py                     every folder in reading/ and bench/, with the novel it belongs to;
                               `?` when no novel in novels/ claims it (its novel was deleted)
  clean.py NOVEL [--delete]    everything NOVEL owns: the novel, its frozen copies, their reading
                               folders, and the bench folders that name no other novel; --delete
                               removes them, otherwise it only lists them

Session handoffs in docs/sessions/ belong to a session, not a novel, and are left alone.
"""
import argparse
import os
import re
import shutil
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import export_prose  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
NAMED = re.compile(r"novels/([a-z0-9][a-z0-9-]*?)(?:--[\w-]+)?(?![\w-])")
BIG = 8 * 1024 * 1024       # a file this large is not a key or a log; skip it


def _dirs(path):
    return sorted(n for n in os.listdir(path)
                  if os.path.isdir(os.path.join(path, n))) if os.path.isdir(path) else []


def novels(root=ROOT):
    """{folder name: reading id} for every novel and frozen copy in novels/."""
    base = os.path.join(root, "novels")
    return {n: export_prose.novel_id(os.path.join(base, n)) for n in _dirs(base)
            if not n.startswith("_")}


def bench_owners(folder):
    """The novels a bench folder's text files name, as base slugs. Every file that reads as text
    counts: a folder that names another novel anywhere is shared, never deleted with this one."""
    found = set()
    for dirpath, _dirs_, files in os.walk(folder):
        for name in files:
            path = os.path.join(dirpath, name)
            try:
                if os.path.getsize(path) > BIG:
                    continue
                with open(path, encoding="utf-8") as fh:
                    found.update(NAMED.findall(fh.read()))
            except (OSError, UnicodeDecodeError):
                continue
    return sorted(s for s in found if s != "_template")


def survey(root=ROOT):
    """[(path, owners)] for every folder in reading/ and bench/; owners is a list of novel
    folder names (reading) or base slugs (bench), empty when nothing claims it."""
    by_id = {}
    for name, rid in novels(root).items():
        by_id.setdefault(rid, []).append(name)
    out = []
    for name in _dirs(os.path.join(root, "reading")):
        out.append(("reading/%s" % name, by_id.get(name, [])))
    for name in _dirs(os.path.join(root, "bench")):
        out.append(("bench/%s" % name, bench_owners(os.path.join(root, "bench", name))))
    return out


def owned(novel, root=ROOT):
    """(paths NOVEL owns, bench paths it shares with other novels), repo-relative."""
    slug = os.path.basename(os.path.normpath(novel))
    mine = [n for n in novels(root) if n == slug or n.startswith(slug + "--")]
    paths, shared = [], []
    for name in mine:
        paths.append("novels/%s" % name)
        rid = export_prose.novel_id(os.path.join(root, "novels", name))
        if os.path.isdir(os.path.join(root, "reading", rid)):
            paths.append("reading/%s" % rid)
    for path, owners in survey(root):
        if path.startswith("bench/") and slug in owners:
            (paths if owners == [slug] else shared).append(path)
    return paths, shared


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("novel", nargs="?", help="a novel directory, or its slug")
    ap.add_argument("--delete", action="store_true", help="remove what NOVEL owns")
    ap.add_argument("--root", default=ROOT, help=argparse.SUPPRESS)
    args = ap.parse_args(argv)
    if not args.novel:
        for path, owners in survey(args.root):
            print("%-28s %s" % (path, ", ".join(owners) or "?"))
        return 0
    slug = os.path.basename(os.path.normpath(args.novel))
    if slug.startswith("_"):
        print("clean.py: %s is the template" % slug, file=sys.stderr)
        return 1
    paths, shared = owned(slug, args.root)
    if not paths:
        print("clean.py: nothing belongs to %s" % slug, file=sys.stderr)
        return 1
    for path in paths:
        if args.delete:
            shutil.rmtree(os.path.join(args.root, path))
        print("%s %s" % ("deleted" if args.delete else "owns   ", path))
    for path in shared:
        print("shared  %s (names other novels too; kept)" % path)
    return 0


if __name__ == "__main__":
    sys.exit(main())
