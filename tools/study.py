#!/usr/bin/env python3
"""A genre study: the top books of a genre read by subagents, their findings folded into kb/.

The protocol, the reader's questionnaire and the synthesis rules are in docs/genre-study.md. This
tool holds the deterministic steps, so a study survives a usage-limit reset: every step is read off
the files, never off a session's memory. STUDY is the study's folder, e.g. research/fanfic
(gitignored: it holds the books' text).

  study.py init STUDY --genre G      folders, books.md (the picks) and progress.md (decisions log)
  study.py intake STUDY              each book's saved chapters (EPUB, a folder of saved pages,
                                     or one text file) -> source/<slug>/chNN.md, prose only;
                                     prints words per chapter and flags gaps and stubs
  study.py next STUDY                the step the files say is next, and its exact dispatches
  study.py status STUDY              one row per book: source, notes, summary, names
  study.py names STUDY               the books' names.txt, merged into STUDY/names.txt for
                                     `kb_check.py --nouns`

A dispatch prints as in tools/room.py: `@ spawn <agent type> · <model> as "<description>"`, then
its text on the next line. Spawn the dispatches of one step together, in the background. Run `next`
only when no study agent is in flight: it cannot see agents, only their files.

Exit status: 0, or 2 with a `STOP:` or `PAUSE:` line when the study waits on something, or 1 on a
bad call.
"""
import argparse
import os
import posixpath
import re
import sys
import zipfile
from html.parser import HTMLParser
from xml.etree import ElementTree

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from room import dispatch, render, usage_pause  # noqa: E402
from lib import mdio  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PROTOCOL = "docs/genre-study.md"
STUB = 300          # words: below this a chapter is a lock page, a teaser or a broken save
BATCH = 5           # readers spawned at once
BUDGET = 60000      # words of source one reader spawn reads; a longer book takes several spawns

BOOKS_TEMPLATE = """---
genre: {genre}
chapters: 10
doc: docs/experiments/{date}-{genre}-study.md
---
# Books

The picks, in rank order per platform. `src` is the saved file or folder, relative to this study
folder (inbox/...). `first`: the EPUB item that is chapter 1, when intake guesses wrong (blank:
auto). Selection rules and how to save: docs/genre-study.md.

| slug | platform | rank | title | url | fandom | type | src | first |
|---|---|---|---|---|---|---|---|---|
"""

PROGRESS_TEMPLATE = """# Progress — {genre} study

Where the study stands comes from the files: `python3 tools/study.py next {study}`. This log holds
what the files cannot: each decision and its reason (picks, skips, intake fixes, review verdicts).

## Decisions
"""


class Stop(Exception):
    pass


# ---------------------------------------------------------------------------- the study's files


def config(study):
    path = os.path.join(study, "books.md")
    if not os.path.isfile(path):
        raise Stop("no books.md in %s: run `study.py init`" % study)
    text = mdio.read_text(path)
    fm, _body = mdio.frontmatter(text)
    table = mdio.table_with(text, "slug", "src")
    books = []
    for row in (table.rows if table else []):
        slug = row.get("slug").strip("` ")
        if not slug:
            continue
        books.append({h: row.get(h).strip() for h in
                      ("platform", "rank", "title", "url", "fandom", "type", "src", "first")})
        books[-1]["slug"] = slug
    return {"genre": str(fm.get("genre", "")), "chapters": int(fm.get("chapters", 10) or 10),
            "doc": str(fm.get("doc", "")), "books": books}


def chapter_files(folder, n):
    return [os.path.join(folder, "ch%02d.md" % i) for i in range(1, n + 1)]


def first_missing(folder, n):
    for i, path in enumerate(chapter_files(folder, n), 1):
        if not os.path.isfile(path):
            return i
    return None


def book_state(study, book, n):
    src = os.path.join(study, "source", book["slug"])
    notes = os.path.join(study, "notes", book["slug"])
    return {
        "source": sum(os.path.isfile(p) for p in chapter_files(src, n)),
        "notes": sum(os.path.isfile(p) for p in chapter_files(notes, n)),
        "next_note": first_missing(notes, n),
        "summary": os.path.isfile(os.path.join(notes, "summary.md")),
        "names": os.path.isfile(os.path.join(notes, "names.txt")),
    }


# ---------------------------------------------------------------------------- html to prose


BLOCK = {"p", "div", "br", "h1", "h2", "h3", "h4", "h5", "h6", "li", "blockquote", "tr", "hr",
         "section", "article", "table", "pre"}
SKIP = {"script", "style", "noscript", "nav", "header", "footer", "button", "form", "svg",
        "select", "iframe"}
VOID = {"br", "hr", "img", "meta", "link", "input", "wbr", "source", "col", "area", "base"}
# The chapter's own text, by platform: Royal Road, Webnovel, then any saved page's main text.
CONTENT = ("chapter-content", "cha-words", "chapter-inner", "cha-content")
AUTHOR = ("author-note", "m-thou", "cha-thou", "author-thoughts")
HIDDEN = re.compile(r"\.([\w-]+)\s*\{[^}]*display\s*:\s*none", re.I)


class Prose(HTMLParser):
    """Paragraphs from a chapter page. When the page has a chapter container (CONTENT), only its
    text and the author's notes (AUTHOR, marked) are kept; the classes the page's own <style>
    hides are dropped (Royal Road hides a planted line in every chapter)."""

    def __init__(self, hidden=()):
        super().__init__(convert_charrefs=True)
        self.hidden = set(hidden)
        self.stack = []             # (tag, kind) kind: skip | content | author | None
        self.paras = []             # (where, text) where: content | author | page
        self.buf, self.title, self._in_title = [], "", False
        self.heads, self._head = {}, None     # the first h1 and h2 seen: chapter, then book
        self.has_content = False

    def _where(self):
        kinds = [k for _t, k in self.stack]
        if "skip" in kinds:
            return "skip"
        for k in reversed(kinds):
            if k in ("content", "author"):
                return k
        return "page"

    def _flush(self):
        text = re.sub(r"\s+", " ", "".join(self.buf)).strip()
        self.buf = []
        if text:
            self.paras.append((self._where(), text))

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        classes = set((a.get("class") or "").split())
        style = (a.get("style") or "").replace(" ", "").lower()
        if tag in BLOCK:
            self._flush()
        if tag == "title":
            self._in_title = True
        if tag in ("h1", "h2") and tag not in self.heads:
            self._head = tag
            self.heads[tag] = []
        if tag in VOID:
            return
        kind = None
        if (tag in SKIP or classes & self.hidden or "display:none" in style
                or a.get("aria-hidden") == "true" or any("comment" in c for c in classes)):
            kind = "skip"
        elif any(c in classes for c in AUTHOR) or any(c.startswith(AUTHOR) for c in classes):
            kind = "author"
        elif any(c in classes for c in CONTENT):
            kind = "content"
            self.has_content = True
        self.stack.append((tag, kind))

    def handle_endtag(self, tag):
        if tag in BLOCK:
            self._flush()
        if tag == "title":
            self._in_title = False
        if tag == self._head:
            text = re.sub(r"\s+", " ", "".join(self.heads[tag])).strip()
            if text:
                self.heads[tag] = text
            else:
                del self.heads[tag]           # an empty one: the next of its kind may count
            self._head = None
        if tag in VOID:
            return
        for i in range(len(self.stack) - 1, -1, -1):
            if self.stack[i][0] == tag:
                del self.stack[i:]
                break

    def handle_data(self, data):
        if self._in_title:
            self.title += data
            return
        if self._where() == "skip":
            return
        if self._head:
            self.heads[self._head].append(data)
        if self.stack and self.stack[-1][0] == "td":
            data = data + " | "
        self.buf.append(data)

    def result(self):
        self._flush()
        keep = ("content", "author") if self.has_content else ("content", "author", "page")
        out = []
        for where, text in self.paras:
            if where not in keep:
                continue
            out.append("> [A/N] " + text if where == "author" else text)
        heading = next((self.heads[h] for h in ("h1", "h2")
                        if isinstance(self.heads.get(h), str)), "")
        return (heading or self.title.strip()), out


def html_prose(html):
    """(title, paragraphs) of one chapter page."""
    hidden = set()
    for style in re.findall(r"<style[^>]*>(.*?)</style>", html, re.S | re.I):
        hidden.update(HIDDEN.findall(style))
    p = Prose(hidden)
    p.feed(html)
    p.close()
    title, paras = p.result()
    if paras and title and paras[0] == title:
        paras = paras[1:]
    return title, paras


# ---------------------------------------------------------------------------- sources


def _natural(name):
    return [int(t) if t.isdigit() else t.lower() for t in re.split(r"(\d+)", name)]


def epub_items(path):
    """(title, paragraphs) for each spine item, in reading order."""
    with zipfile.ZipFile(path) as z:
        container = ElementTree.fromstring(z.read("META-INF/container.xml"))
        rootfile = next(e.get("full-path") for e in container.iter()
                        if e.tag.endswith("rootfile"))
        opf = ElementTree.fromstring(z.read(rootfile))
        base = posixpath.dirname(rootfile)
        manifest = {e.get("id"): e.get("href") for e in opf.iter() if e.tag.endswith("}item")
                    or e.tag == "item"}
        items = []
        for ref in (e for e in opf.iter() if e.tag.endswith("itemref")):
            href = manifest.get(ref.get("idref"))
            if not href:
                continue
            name = posixpath.normpath(posixpath.join(base, href.split("#")[0]))
            items.append(html_prose(z.read(name).decode("utf-8", "replace")))
        return items


FRONT = re.compile(r"^(cover|title page|information|table of contents|contents|toc)\b", re.I)


def first_chapter(items):
    """The index of chapter 1 among EPUB items: the first one that is not front matter and has
    at least STUB words."""
    for i, (title, paras) in enumerate(items):
        if FRONT.match(title or "") or (paras and FRONT.match(paras[0])):
            continue
        if sum(len(p.split()) for p in paras) >= STUB:
            return i
    return 0


CHAPTER_HEAD = re.compile(r"^\s*(#+\s+.*|(chapter|ch\.)\s*\d+.*|prologue\b.*)$", re.I)


def text_items(path):
    """One text file split at its chapter headings (`# ...`, `Chapter 3 ...`, `Prologue`)."""
    items, title, paras, buf = [], None, [], []
    for line in mdio.read_text(path).splitlines() + [""]:
        if CHAPTER_HEAD.match(line):
            if buf:
                paras.append(" ".join(buf))
                buf = []
            if title is not None or paras:
                items.append((title or "", paras))
            title, paras = line.strip().lstrip("#").strip(), []
        elif line.strip():
            buf.append(line.strip())
        elif buf:
            paras.append(" ".join(buf))
            buf = []
    if title is not None or paras:
        items.append((title or "", paras))
    return items


def dir_items(path):
    items = []
    for name in sorted(os.listdir(path), key=_natural):
        full = os.path.join(path, name)
        low = name.lower()
        if low.endswith((".html", ".htm", ".xhtml")):
            items.append(html_prose(mdio.read_text(full)))
        elif low.endswith((".txt", ".md")):
            items.extend(text_items(full) or [])
    return items


def load_items(path):
    if os.path.isdir(path):
        return dir_items(path)
    low = path.lower()
    if low.endswith(".epub"):
        return epub_items(path)
    if low.endswith((".html", ".htm", ".xhtml")):
        return [html_prose(mdio.read_text(path))]
    if low.endswith((".txt", ".md")):
        return text_items(path)
    raise ValueError("cannot read %s: an .epub, a folder, or a .html/.txt/.md file" % path)


def intake(study):
    cfg = config(study)
    n, lines = cfg["chapters"], []
    if not cfg["books"]:
        raise Stop("books.md lists no books yet (step S1, docs/genre-study.md)")
    for book in cfg["books"]:
        slug = book["slug"]
        if not book["src"]:
            lines.append("%s: no src yet" % slug)
            continue
        src = book["src"] if os.path.isabs(book["src"]) else os.path.join(study, book["src"])
        if not os.path.exists(src):
            lines.append("%s: src %s does not exist" % (slug, book["src"]))
            continue
        items = load_items(src)
        if src.lower().endswith(".epub"):
            first = int(book["first"]) - 1 if book["first"].isdigit() else first_chapter(items)
            skipped = [t or "(untitled)" for t, _p in items[:first]]
            items = items[first:]
            if skipped:
                lines.append("%s: front matter skipped: %s" % (slug, "; ".join(skipped)))
        out = os.path.join(study, "source", slug)
        os.makedirs(out, exist_ok=True)
        for i, (title, paras) in enumerate(items[:n], 1):
            words = sum(len(p.split()) for p in paras)
            with open(os.path.join(out, "ch%02d.md" % i), "w", encoding="utf-8") as fh:
                fh.write("# %s\n\n%s\n" % (title or "Chapter %d" % i, "\n\n".join(paras)))
            flag = "  STUB? (under %d words: locked, a teaser or a broken save)" % STUB \
                if words < STUB else ""
            lines.append("%s ch%02d %5d words  %s%s" % (slug, i, words, title, flag))
        if len(items) < n:
            lines.append("%s: only %d of %d chapters in %s" % (slug, len(items), n, book["src"]))
    return lines


# ---------------------------------------------------------------------------- dispatch texts


def words(path):
    return len(mdio.read_text(path).split()) if os.path.isfile(path) else 0


def reading_range(study, slug, start, n, budget=BUDGET):
    """The last chapter this spawn reads: from `start`, as many as fit in `budget` words (one at
    least)."""
    total, end = 0, start
    for i in range(start, n + 1):
        total += words(os.path.join(study, "source", slug, "ch%02d.md" % i))
        if total > budget and i > start:
            break
        end = i
    return end


def reader_text(study, cfg, book, start, end=None):
    """start: the first chapter without notes; None when only summary.md or names.txt is left.
    end: the last chapter this spawn reads (default: the book's last)."""
    n = cfg["chapters"]
    end = end or n
    notes = os.path.join(study, "notes", book["slug"])
    if start is None:
        task = ("Your notes for every chapter exist: read them and write what is missing of "
                "summary.md and names.txt.")
        line = "READ %s ch01-%02d" % (book["slug"], n)
    else:
        task = ("Read chapters %d to %d this time." % (start, end) if (start, end) != (1, n)
                else "Read all %d chapters." % n)
        if start > 1:
            task += (" Your notes for chapters 1-%d exist: read them first and do not redo them."
                     % (start - 1))
        if end < n:
            task += (" Stop after chapter %d's notes: another spawn reads on from your notes, and "
                     "writes summary.md and names.txt." % end)
        line = "READ %s ch%02d-%02d" % (book["slug"], start, end)
    return ("You are a reader in a genre study. Read %s, section \"Reader\": your procedure, "
            "the questionnaire and the files you write. Your book: %s (%s, rank %s; fandom: %s; "
            "type: %s). Its chapters: %s/ch01.md to ch%02d.md. Write to %s/. %s End on one line: "
            "`%s`."
            % (PROTOCOL, book["title"] or book["slug"], book["platform"], book["rank"],
               book["fandom"] or "-", book["type"] or "-",
               os.path.join(study, "source", book["slug"]), n, notes, task, line))


def synthesis_text(study, cfg):
    return ("You write a genre study's synthesis. Read %s, section \"Synthesis\": what you read, "
            "the rules, and the document's shape. Study: %s (books.md lists the %d picks; "
            "progress.md the decisions so far). Genre: %s. Write %s. End on one line: "
            "`SYNTHESIS %s rows=<n>`." % (PROTOCOL, study, len(cfg["books"]), cfg["genre"],
                                         cfg["doc"], cfg["doc"]))


def apply_text(study, cfg):
    return ("Apply a genre study's accepted proposals to the knowledge bases. Read %s, section "
            "\"Apply\". Study document: %s (only rows whose verdict is `accept`). Study folder: %s. "
            "End on one line: `APPLIED <n> rows`." % (PROTOCOL, cfg["doc"], study))


def proposals(doc_text):
    table = mdio.table_with(doc_text, "id", "finding", "verdict")
    return table.rows if table else []


def step(study, root=ROOT, usage=None):
    """(lines, dispatches, then): the step the files say is next."""
    cfg = config(study)
    n, books = cfg["chapters"], cfg["books"]
    if not books:
        raise Stop("S1: books.md lists no picks. Paste or save the two lists, pick per "
                   "docs/genre-study.md \"Selection\", and save the chapters into %s/inbox/"
                   % study)
    states = {b["slug"]: book_state(study, b, n) for b in books}
    short = [b["slug"] for b in books if states[b["slug"]]["source"] < n]
    if len(short) == len(books):
        raise Stop("S2: no book has its %d chapters in source/. Save them into %s/inbox/, then "
                   "run `python3 tools/study.py intake %s`" % (n, study, study))
    waiting = ("Waiting on source (save, then `study.py intake`): %s." % ", ".join(short)
               if short else None)
    pause = usage_pause(usage) if usage else usage_pause()
    if pause:
        pause = (pause.split(". Start")[0] + ". Spawn nothing new: write the handoff note "
                 "(.claude/skills/handoff) and run `study.py next` after the reset.")
    unread = [b for b in books if b["slug"] not in short
              and not (states[b["slug"]]["next_note"] is None and states[b["slug"]]["summary"]
                       and states[b["slug"]]["names"])]
    if unread:
        if pause:
            raise Pause(pause)
        sends = []
        for b in unread[:BATCH]:
            start = states[b["slug"]]["next_note"]
            end = reading_range(study, b["slug"], start, n) if start else None
            label = "read %s" % b["slug"] if not start or (start, end) == (1, n) \
                else "read %s ch%02d-%02d" % (b["slug"], start, end)
            sends.append(dispatch("spawn", "general-purpose · sonnet",
                                  reader_text(study, cfg, b, start, end), label))
        lines = ["S3: reading — %d of %d books still to read; spawning %d."
                 % (len(unread), len(books) - len(short), len(sends))]
        if waiting:
            lines.append(waiting)
        return lines, sends, ("When all of them are back (`next` cannot see agents in flight), "
                              "run `python3 tools/study.py next %s`." % study)
    if short:
        raise Stop("S3: every saved book is read. %s The synthesis waits for them, or drop their "
                   "rows from books.md (and log why in progress.md)." % waiting)
    doc = os.path.join(root, cfg["doc"]) if cfg["doc"] else ""
    if not doc:
        raise Stop("books.md has no `doc:` path for the study document")
    if not os.path.isfile(doc):
        if pause:
            raise Pause(pause)
        return (["S4: all %d books read; the synthesis is next." % len(books)],
                [dispatch("spawn", "general-purpose · opus", synthesis_text(study, cfg),
                          "%s synthesis" % cfg["genre"])],
                "When it is back, review its proposal table (S5).")
    rows = proposals(mdio.read_text(doc))
    if not rows:
        raise Stop("S4: %s has no proposal table (columns id, finding, …, verdict)" % cfg["doc"])
    open_rows = [r.get("id") for r in rows if not r.get("verdict").strip()]
    if open_rows:
        return (["S5: review — %d of %d proposal rows have no verdict: %s"
                 % (len(open_rows), len(rows), ", ".join(open_rows)),
                 "The main session marks each `accept` or `reject — <reason>` (%s, \"Review\"), "
                 "and logs the reasons in %s/progress.md." % (PROTOCOL, study)], [], None)
    if not mdio.section(mdio.read_text(doc), "Applied"):
        accepted = [r for r in rows if r.get("verdict").strip().lower().startswith("accept")]
        if pause:
            raise Pause(pause)
        return (["S6: apply — %d accepted rows. Continue the synthesis agent warm with this text "
                 "if it is still in this session; otherwise spawn it." % len(accepted)],
                [dispatch("spawn", "general-purpose · opus", apply_text(study, cfg),
                          "%s apply" % cfg["genre"])],
                "When it is back, run `python3 tools/study.py names %s`, then `python3 "
                "tools/kb_check.py --nouns %s/names.txt` and the tests." % (study, study))
    return (["DONE: the study is applied. Checks: `python3 tools/study.py names %s`, `python3 "
             "tools/kb_check.py --nouns %s/names.txt`, `python3 -m unittest discover tests`."
             % (study, study)], [], None)


class Pause(Exception):
    pass


def names(study):
    cfg = config(study)
    out, seen = [], set()
    for b in cfg["books"]:
        path = os.path.join(study, "notes", b["slug"], "names.txt")
        if not os.path.isfile(path):
            continue
        out.append("# %s" % b["slug"])
        for line in mdio.read_text(path).splitlines():
            line = line.split("#", 1)[0].strip()
            if line and line not in seen:
                seen.add(line)
                out.append(line)
    # the titles too: a kb doc names no studied book
    out.append("# titles")
    out += [b["title"] for b in cfg["books"] if b["title"] and b["title"] not in seen]
    path = os.path.join(study, "names.txt")
    with open(path, "w", encoding="utf-8") as fh:
        fh.write("\n".join(out) + "\n")
    return path, len([l for l in out if not l.startswith("#")])


def status(study):
    cfg = config(study)
    n = cfg["chapters"]
    lines = ["%-28s %-9s %6s %6s %7s %5s" % ("book", "platform", "source", "notes", "summary",
                                             "names")]
    for b in cfg["books"]:
        s = book_state(study, b, n)
        lines.append("%-28s %-9s %3d/%-2d %3d/%-2d %7s %5s"
                     % (b["slug"], b["platform"], s["source"], n, s["notes"], n,
                        "yes" if s["summary"] else "-", "yes" if s["names"] else "-"))
    return lines


def init(study, genre, date):
    for sub in ("inbox", "source", "notes"):
        os.makedirs(os.path.join(study, sub), exist_ok=True)
    made = []
    for name, text in (("books.md", BOOKS_TEMPLATE), ("progress.md", PROGRESS_TEMPLATE)):
        path = os.path.join(study, name)
        if not os.path.exists(path):
            with open(path, "w", encoding="utf-8") as fh:
                fh.write(text.format(genre=genre, date=date, study=study))
            made.append(path)
    return made


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("cmd", choices=("init", "intake", "next", "status", "names"))
    ap.add_argument("study")
    ap.add_argument("--genre", help="init: the genre's key, as in novel.md (fanfic, litrpg, …)")
    ap.add_argument("--date", help="init: the study document's date (default: today)")
    args = ap.parse_args(argv)
    try:
        if args.cmd == "init":
            if not args.genre:
                raise ValueError("init needs --genre")
            import datetime
            made = init(args.study, args.genre, args.date or datetime.date.today().isoformat())
            print("\n".join(made) or "%s exists; nothing made" % args.study)
        elif args.cmd == "intake":
            print("\n".join(intake(args.study)))
        elif args.cmd == "status":
            print("\n".join(status(args.study)))
        elif args.cmd == "names":
            path, count = names(args.study)
            print("%s: %d names" % (path, count))
        else:
            lines, sends, then = step(args.study)
            print(render(lines, sends, then))
    except Stop as exc:
        print("STOP: %s" % exc)
        return 2
    except Pause as exc:
        print(exc)
        return 2
    except (ValueError, OSError, KeyError, zipfile.BadZipFile, ElementTree.ParseError) as exc:
        sys.stderr.write("study: %s\n" % exc)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
