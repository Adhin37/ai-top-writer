"""A novel directory (`docs/novel-format.md`), read lazily: config, chapters, plan rows, the reader
ledger, the state files, cast names and the lexicon.

One object, so no tool re-guesses a path or re-parses a table. Tables are found by their columns,
never by the heading above them: headings get edited, column names are load-bearing.
"""

import os
import re

from . import mdio
from .textstats import Channels, load_chapters

# A thread id in a plan row or a block's `thr` line, with its operation: `~` open, `^` advance,
# `v` pay, `x` drop. `vT5` is one token, so the id is not required to start on a word boundary.
THREAD_REF = re.compile(r"(?:^|(?<=[^A-Za-z0-9]))([~^vx]?)(T\d+)\b")
BLOCK_HEAD = re.compile(r"^=C(\d+)=(.*)$")
BLOCK_LINE = re.compile(r"^([a-z]+)\s+(.*)$")
BLOCK_KEYS = ("ev", "at", "kno", "has", "cost", "thr", "hook")
BLOCK_REQUIRED = ("ev", "at", "kno", "thr", "hook")
# A walk-on's line in bible/cast/_extras.md: `<Name> — <what> — ch <appearances> — <status>`.
ROSTER_LINE = re.compile(r"^([^—\n|#<]{2,60}?)\s+—.*?—\s*ch\b")
# One step of a Pressure row's trail: `ch3 grew — she logs six seals under Kell's code`.
# The lever (L) sets, grows, holds or shrinks; the clock (C) sets, comes nearer, holds or goes later.
PRESSURE_WORDS = ("set", "grew", "held", "shrank", "nearer", "later")
PRESSURE_STEP = re.compile(r"\bch\s?(\d+)\s+(%s)\b([^·|]*)" % "|".join(PRESSURE_WORDS), re.I)


def thread_refs(text):
    """[(op, id)] for every thread reference in a cell or line."""
    return THREAD_REF.findall(str(text or ""))


class Block(object):
    """One chapter's continuity block in state/continuity.md."""

    def __init__(self, number, header, line_no):
        self.number = number
        self.header = header
        self.line_no = line_no
        self.lines = []          # (line number, key, value)
        self.stray = []          # (line number, text) that is not `key value`

    def keys(self):
        out = {}
        for _n, key, value in self.lines:
            out.setdefault(key, []).append(value)
        return out

    def get(self, key, default=""):
        vals = self.keys().get(key)
        return vals[0] if vals else default

    def field(self, name):
        """A header field, `name value`, from the `|`-separated header."""
        for part in self.header.split("|"):
            part = part.strip()
            if part.startswith(name + " "):
                return part[len(name) + 1:].strip()
        return ""

    @property
    def words(self):
        v = self.field("words").replace(",", "")
        return int(v) if v.isdigit() else None

    def threads(self):
        return thread_refs(" ".join(self.keys().get("thr", [])))


class Novel(object):
    def __init__(self, root):
        self.root = os.path.normpath(root)
        self._cache = {}

    # ------------------------------------------------------------------ files

    def path(self, *parts):
        return os.path.join(self.root, *parts)

    def text(self, *parts):
        if parts not in self._cache:
            self._cache[parts] = mdio.read_text(self.path(*parts))
        return self._cache[parts]

    def exists(self):
        return os.path.isfile(self.path("novel.md"))

    @property
    def cfg(self):
        if "cfg" not in self._cache:
            self._cache["cfg"] = mdio.frontmatter(self.text("novel.md"))[0]
        return self._cache["cfg"]

    def get(self, dotted, default=None):
        return mdio.dig(self.cfg, dotted, default)

    @property
    def slug(self):
        return str(self.get("slug") or os.path.basename(self.root))

    @property
    def title(self):
        return str(self.get("title") or self.slug)

    # --------------------------------------------------------------- chapters

    @property
    def channels(self):
        if "channels" not in self._cache:
            self._cache["channels"] = Channels.from_config(self.cfg)
        return self._cache["channels"]

    def chapters(self):
        if "chapters" not in self._cache:
            self._cache["chapters"] = load_chapters(self.path("chapters"), self.channels)
        return self._cache["chapters"]

    def chapter(self, number):
        return next((c for c in self.chapters() if c.number == number), None)

    @property
    def last_chapter(self):
        return max([c.number for c in self.chapters() if c.number] or [0])

    # ------------------------------------------------------------------- plan

    def plan_rows(self):
        t = mdio.table_with(self.text("plan", "chapters.md"), "#", "title", "event")
        return t.rows if t else []

    def plan_row(self, number):
        for row in self.plan_rows():
            digits = re.sub(r"\D", "", row.first())
            if digits and int(digits) == number:
                return row
        return None

    def ledger(self):
        """{"facts": rows, "faces": rows, "promises": rows} from plan/reader-ledger.md."""
        text = self.text("plan", "reader-ledger.md")
        out = {}
        for kind, cols in (("facts", ("id", "due by ch", "status")),
                           ("faces", ("id", "who", "status")),
                           ("promises", ("id", "made in ch", "status"))):
            t = mdio.table_with(text, *cols)
            out[kind] = t.rows if t else []
        return out

    def pressure(self):
        """The ledger's Pressure rows: [(id, what, [(chapter, step, clause)])], from the trail
        `ch1 set — <clause> · ch2 grew — <clause>`. Empty when the ledger has no Pressure table."""
        t = mdio.table_with(self.text("plan", "reader-ledger.md"), "id", "by chapter")
        out = []
        for r in (t.rows if t else []):
            trail = [(int(m.group(1)), m.group(2).lower(), m.group(3).strip(" —-"))
                     for m in PRESSURE_STEP.finditer(r.get("by chapter"))]
            out.append((r.first().strip("* "), r.get("what the reader tracks"), trail))
        return out

    # ------------------------------------------------------------------ state

    def blocks(self):
        """Every continuity block, in file order."""
        if "blocks" in self._cache:
            return self._cache["blocks"]
        out, cur = [], None
        for n, line in enumerate(self.text("state", "continuity.md").split("\n"), 1):
            m = BLOCK_HEAD.match(line)
            if m:
                cur = Block(int(m.group(1)), m.group(2).strip(), n)
                out.append(cur)
                continue
            if cur is None or not line.strip():
                continue
            if line.startswith("#") or line.strip().startswith("```"):
                cur = None
                continue
            km = BLOCK_LINE.match(line.strip())
            if km:
                cur.lines.append((n, km.group(1), km.group(2).strip()))
            else:
                cur.stray.append((n, line.strip()))
        self._cache["blocks"] = out
        return out

    def block(self, number):
        return next((b for b in self.blocks() if b.number == number), None)

    def _state_table(self, name, *cols):
        t = mdio.table_with(self.text("state", name), *cols)
        return t.rows if t else []

    def threads(self):
        return self._state_table("threads.md", "id", "thread", "status")

    def scenes(self):
        return self._state_table("scenes.md", "ch", "who")

    def timeline(self):
        return self._state_table("timeline.md", "day", "ch")

    # ---------------------------------------------------------------- the cast

    def speakers(self):
        """Every name that can speak: the voice matrix, the cast profiles, the walk-on roster."""
        names = []
        t = mdio.table_with(self.text("bible", "cast", "_voices.md"), "character")
        for row in (t.rows if t else []):
            names.append(row.first().strip("* "))
        cast = self.path("bible", "cast")
        if os.path.isdir(cast):
            for fn in sorted(os.listdir(cast)):
                if fn.endswith(".md") and not fn.startswith("_"):
                    name = mdio.frontmatter(self.text("bible", "cast", fn))[0].get("name")
                    if name:
                        names.append(str(name))
        in_comment = False
        for line in self.text("bible", "cast", "_extras.md").split("\n"):
            if "<!--" in line:
                in_comment = "-->" not in line.split("<!--", 1)[1]
                continue
            if in_comment:
                in_comment = "-->" not in line
                continue
            m = ROSTER_LINE.match(line)
            if m:
                names.append(m.group(1).strip())
        seen, out = set(), []
        for n in names:
            if n and n not in seen:
                seen.add(n)
                out.append(n)
        return out

    # ---------------------------------------------------------------- lexicon

    def lexicon_variants(self):
        """[(wrong spelling, canonical)] from every lexicon table with a `never write as` column.
        A variant that is only a word of its own canonical name, or its possessive, is skipped: it
        cannot be told apart from a correct use."""
        out = []
        for table in mdio.parse_tables(self.text("bible", "lexicon.md")):
            if not table.has("never write as"):
                continue
            for row in table.rows:
                canonical = re.sub(r"\(.*?\)", "", row.first()).strip("* ").strip()
                parts = set(re.split(r"[\s/]+", canonical))
                for raw in row.get("never write as").split(","):
                    variant = re.sub(r"\(.*?\)", "", raw).strip().strip("`\"'")
                    base = re.sub(r"['\u2019]s$", "", variant)
                    if variant and base not in parts and variant != canonical:
                        out.append((variant, canonical))
        return out

    def lexicon_terms(self):
        """The first cell of every lexicon table row: every name and coined term the book uses."""
        out = []
        for table in mdio.parse_tables(self.text("bible", "lexicon.md")):
            for row in table.rows:
                term = re.sub(r"\(.*?\)", "", row.first()).strip("*` ").strip()
                if term:
                    out.append(term)
        return out

    def banned_words(self):
        """The backticked words in the lexicon's `Banned words` section."""
        sec = mdio.section(self.text("bible", "lexicon.md"), "banned words")
        return re.findall(r"`([^`]+)`", sec)

    def number_style(self):
        """The lexicon's `Numbers:` line, or ''."""
        m = re.search(r"^\s*[-*]\s*Numbers:\s*(.+(?:\n\s{2,}\S.*)*)",
                      self.text("bible", "lexicon.md"), re.M)
        return re.sub(r"\s+", " ", m.group(1)).strip() if m else ""


def resolve(arg, repo_root="."):
    """A Novel from a path or a slug, or None."""
    for p in (arg, os.path.join(repo_root, arg), os.path.join(repo_root, "novels", arg)):
        if p and os.path.isfile(os.path.join(p, "novel.md")):
            return Novel(p)
    return None


def novel_of(path):
    """The Novel a file inside `novels/<slug>/` belongs to, or None."""
    cur = os.path.abspath(path if os.path.isdir(path) else os.path.dirname(path))
    while cur and cur != os.path.dirname(cur):
        if os.path.isfile(os.path.join(cur, "novel.md")):
            return Novel(cur)
        cur = os.path.dirname(cur)
    return None
