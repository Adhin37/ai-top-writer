#!/usr/bin/env python3
"""Export chapters as prose only, into a neutral reading folder.

The beta reader and the judge must read what a subscriber reads and nothing else. A chapter file
carries frontmatter, and frontmatter is where intent leaks: skilled-writer run #6's chapter 1 said
in its `delivers:` field what the reader was meant to understand, and the "blind" reader read it.
So readers never open a chapter file. They open an export:

  * YAML frontmatter removed; HTML comments (authoring notes) removed;
  * the chapter's title kept as a heading, because a subscriber sees the title (--no-title drops it);
  * written as `chNN.md` (or --as NAME) into a folder whose name says nothing about the novel.

Usage:
  export_prose.py SOURCE [SOURCE ...] --reading-dir DIR [--as NAME] [--start N] [--no-title]
  export_prose.py --print-id NOVEL_DIR

SOURCE is a chapter file, or a chapters directory (its `NNNN-*.md` files, in order; names starting
with `_` are skipped). The chapter number comes from frontmatter `number`, else the file name's
leading digits, else a counter starting at --start.

--print-id prints the neutral folder id for a novel: `r` + the first 6 hex digits of sha1(slug),
where slug is novel.md's `slug:` or the directory name. Use it as `reading/<id>/`.
"""
import argparse
import hashlib
import os
import re
import sys

FRONTMATTER = re.compile(r"\A---[ \t]*\n(.*?)\n---[ \t]*(?:\n|\Z)", re.S)
COMMENT = re.compile(r"<!--.*?-->\n?", re.S)
CHAPTER_FILE = re.compile(r"^\d+.*\.md$")


def split_frontmatter(text):
    """(fields, body). Fields are the top-level `key: value` lines, quotes stripped."""
    m = FRONTMATTER.match(text)
    if not m:
        return {}, text
    fields = {}
    for line in m.group(1).splitlines():
        if not line or line[0] in " \t#-":
            continue
        key, sep, value = line.partition(":")
        if not sep:
            continue
        value = value.strip()
        if len(value) >= 2 and value[0] == value[-1] and value[0] in "\"'":
            value = value[1:-1]
        fields[key.strip()] = value
    return fields, text[m.end():]


def prose(text, keep_title=True):
    """The text a reader should see: title heading (optional) and body, nothing else."""
    fields, body = split_frontmatter(text)
    body = COMMENT.sub("", body).strip("\n")
    title = fields.get("title", "").strip()
    if keep_title and title:
        return "# %s\n\n%s\n" % (title, body)
    return body + "\n"


def chapter_number(path, fields):
    raw = fields.get("number", "")
    if raw.isdigit():
        return int(raw)
    m = re.match(r"^(\d+)", os.path.basename(path))
    return int(m.group(1)) if m else None


def expand(sources):
    files = []
    for src in sources:
        if os.path.isdir(src):
            names = sorted(n for n in os.listdir(src)
                           if CHAPTER_FILE.match(n) and not n.startswith("_"))
            files.extend(os.path.join(src, n) for n in names)
        else:
            files.append(src)
    return files


def novel_id(novel_dir):
    slug = os.path.basename(os.path.normpath(novel_dir))
    cfg = os.path.join(novel_dir, "novel.md")
    if os.path.isfile(cfg):
        with open(cfg, encoding="utf-8") as fh:
            fields, _ = split_frontmatter(fh.read())
        slug = fields.get("slug") or slug
    return "r" + hashlib.sha1(slug.encode("utf-8")).hexdigest()[:6]


def export(sources, reading_dir, as_name=None, start=1, keep_title=True):
    """Write each source's prose into reading_dir. Returns the paths written."""
    parts = os.path.normpath(reading_dir).replace(os.sep, "/").split("/")
    if "novels" in parts:
        raise ValueError("refusing to export into a novel directory (%s): a reader's folder must "
                         "sit outside novels/" % reading_dir)
    files = expand(sources)
    if not files:
        raise ValueError("no chapter files found in %s" % ", ".join(sources))
    if as_name and len(files) != 1:
        raise ValueError("--as names one output, and %d sources were given" % len(files))
    os.makedirs(reading_dir, exist_ok=True)
    written, counter = [], start
    for path in files:
        with open(path, encoding="utf-8") as fh:
            text = fh.read()
        fields, _ = split_frontmatter(text)
        if as_name:
            name = as_name if as_name.endswith(".md") else as_name + ".md"
        else:
            num = chapter_number(path, fields)
            if num is None:
                num = counter
            counter = num + 1
            name = "ch%02d.md" % num
        out = os.path.join(reading_dir, name)
        with open(out, "w", encoding="utf-8") as fh:
            fh.write(prose(text, keep_title))
        written.append(out)
    return written


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("sources", nargs="*", help="chapter files or chapters directories")
    ap.add_argument("--reading-dir", help="the neutral folder to write into, e.g. reading/r1a2b3c")
    ap.add_argument("--as", dest="as_name", help="output file name, for a single source")
    ap.add_argument("--start", type=int, default=1, help="first number for unnumbered sources")
    ap.add_argument("--no-title", action="store_true", help="drop the title heading")
    ap.add_argument("--print-id", metavar="NOVEL_DIR", help="print the neutral id for a novel")
    args = ap.parse_args(argv)

    if args.print_id:
        print(novel_id(args.print_id))
        return 0
    if not args.sources or not args.reading_dir:
        ap.error("give SOURCE(s) and --reading-dir, or --print-id NOVEL_DIR")
    try:
        written = export(args.sources, args.reading_dir, args.as_name, args.start,
                         not args.no_title)
    except (ValueError, OSError) as exc:
        sys.stderr.write("export_prose: %s\n" % exc)
        return 1
    for path in written:
        print(path)
    return 0


if __name__ == "__main__":
    sys.exit(main())
