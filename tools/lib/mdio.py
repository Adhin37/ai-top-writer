"""Markdown files as data: YAML frontmatter, pipe tables, `## ` sections.

Standard library only. The formats here are regular enough that a short parser is enough: pipe
tables with fixed columns, and a frontmatter block that nests two levels deep and uses quoted
scalars that may run over several lines (`novel.md` does both).

Every reader degrades rather than raises. A config that fails to parse does not look like a parse
failure downstream; it looks like a novel with no protagonist.
"""

import os
import re

# --------------------------------------------------------------------------- files


def read_text(path):
    """A file as UTF-8 with `\\n` newlines and no BOM, or '' if it does not exist.

    A BOM left in place stops `\\A---` from matching, and the file reads as having no frontmatter.
    """
    if not os.path.isfile(path):
        return ""
    with open(path, encoding="utf-8", errors="replace") as fh:
        text = fh.read()
    if text.startswith("﻿"):
        text = text[1:]
    return text.replace("\r\n", "\n").replace("\r", "\n")


# --------------------------------------------------------------- frontmatter + YAML

_FM = re.compile(r"\A---[ \t]*\n(.*?)\n---[ \t]*(?:\n|\Z)", re.S)


def split_frontmatter(text):
    """(frontmatter text, body). No frontmatter: ('', text)."""
    m = _FM.match(text)
    if not m:
        return "", text
    return m.group(1), text[m.end():]


def _strip_comment(s):
    """Drop a trailing `# comment` that is not inside quotes."""
    quote = None
    for i, ch in enumerate(s):
        if quote:
            if ch == quote and (i == 0 or s[i - 1] != "\\"):
                quote = None
        elif ch in "\"'":
            quote = ch
        elif ch == "#" and (i == 0 or s[i - 1] in " \t"):
            return s[:i]
    return s


def _split_inline(s):
    """Split the inside of `[a, "b, c"]` on commas outside quotes."""
    out, buf, quote = [], "", None
    for ch in s:
        if quote:
            if ch == quote:
                quote = None
            buf += ch
        elif ch in "\"'":
            quote = ch
            buf += ch
        elif ch == ",":
            out.append(buf)
            buf = ""
        else:
            buf += ch
    if buf.strip():
        out.append(buf)
    return out


def _scalar(v):
    """A YAML scalar as str, int, float, bool, None or a list."""
    v = v.strip()
    if not v:
        return ""
    if len(v) > 1 and v[0] == v[-1] and v[0] in "\"'":
        return v[1:-1]
    low = v.lower()
    if low == "true":
        return True
    if low == "false":
        return False
    if low in ("null", "~"):
        return None
    if re.fullmatch(r"-?\d+", v):
        return int(v)
    if re.fullmatch(r"-?\d+\.\d+", v):
        return float(v)
    if v.startswith("[") and v.endswith("]"):
        inner = v[1:-1].strip()
        return [_scalar(x) for x in _split_inline(inner)] if inner else []
    return v


def _unterminated_quote(v):
    v = v.strip()
    if not v or v[0] not in "\"'":
        return False
    return not (len(v) > 1 and v.endswith(v[0]))


_NEXT_KEY = re.compile(r"^[ \t]*(?:-\s|[A-Za-z0-9_.\-]+:(?:\s|$))")


def parse_yaml(text):
    """A minimal YAML reader for frontmatter.

    Handles nested maps, `- ` lists, inline `[a, b]` lists, `#` comments outside quotes, and quoted
    scalars over several lines. Not anchors, block scalars or flow maps. Three things it does on
    purpose, each a silent failure once:
      * tabs count as indentation, so a tab-indented `mc:` keeps its children;
      * an unclosed quote stops at the next line that is plainly a key, instead of swallowing the
        rest of the file;
      * a map nested inside a list item is skipped, never raised on, and its keys do not leak into
        the map around it.
    """
    root = {}
    stack = [(-1, root)]
    lines = text.expandtabs(2).split("\n")
    i = 0
    while i < len(lines):
        raw = lines[i]
        i += 1
        if not raw.strip() or raw.lstrip().startswith("#"):
            continue
        indent = len(raw) - len(raw.lstrip(" "))
        line = _strip_comment(raw).rstrip()
        stripped = line.strip()
        if not stripped:
            continue
        while len(stack) > 1 and indent <= stack[-1][0]:
            stack.pop()
        container = stack[-1][1]

        if stripped.startswith("- "):
            val = stripped[2:].strip()
            if isinstance(container, list):
                while _unterminated_quote(val) and i < len(lines) and not _NEXT_KEY.match(lines[i]):
                    val += " " + lines[i].strip()
                    i += 1
                container.append(_scalar(val))
            continue

        m = re.match(r"^([A-Za-z0-9_.\-]+):\s*(.*)$", stripped)
        if not m:
            continue
        key, val = m.group(1), m.group(2)
        if val == "":
            nxt = next((l for l in lines[i:] if l.strip() and not l.lstrip().startswith("#")), None)
            child = [] if (nxt and nxt.strip().startswith("- ")) else {}
            if isinstance(container, dict):
                container[key] = child
            stack.append((indent, child))
            continue
        while _unterminated_quote(val) and i < len(lines) and not _NEXT_KEY.match(lines[i]):
            val += " " + _strip_comment(lines[i]).strip()
            i += 1
        if isinstance(container, dict):
            container[key] = _scalar(val)
    return root


def frontmatter(text):
    """(parsed frontmatter dict, body)."""
    fm, body = split_frontmatter(text)
    return (parse_yaml(fm) if fm else {}), body


def dig(data, dotted, default=None):
    """dig(cfg, "mc.name") -> the value, or default."""
    cur = data
    for part in dotted.split("."):
        if not isinstance(cur, dict) or part not in cur:
            return default
        cur = cur[part]
    return cur


# ------------------------------------------------------------------- pipe tables


def norm_header(h):
    return re.sub(r"[^a-z0-9#]", "", h.lower())


class Row(object):
    __slots__ = ("cells", "line_no", "raw", "headers")

    def __init__(self, cells, line_no, raw, headers):
        self.cells = cells
        self.line_no = line_no
        self.raw = raw
        self.headers = headers

    def get(self, name, default=""):
        """A cell by header name: case, spaces and punctuation ignored."""
        want = norm_header(name)
        for idx, h in enumerate(self.headers):
            if norm_header(h) == want:
                return self.cells[idx] if idx < len(self.cells) else default
        return default

    def first(self):
        return self.cells[0] if self.cells else ""

    def __repr__(self):
        return "Row(%r)" % (self.cells,)


class Table(object):
    def __init__(self, headers, rows, line_no, heading):
        self.headers = headers
        self.rows = rows
        self.line_no = line_no
        self.heading = heading

    def has(self, *names):
        heads = {norm_header(h) for h in self.headers}
        return all(norm_header(n) in heads for n in names)


def _cells(line):
    s = line.strip()
    if s.startswith("|"):
        s = s[1:]
    if s.endswith("|") and not s.endswith("\\|"):
        s = s[:-1]
    return [c.strip() for c in re.split(r"(?<!\\)\|", s)]


_SEP = re.compile(r"^\|?\s*:?-+:?\s*(\|\s*:?-+:?\s*)*\|?$")


def parse_tables(text):
    """Every pipe table in the text, each tagged with the nearest heading above it."""
    tables, heading = [], ""
    lines = text.split("\n")
    i = 0
    while i < len(lines):
        line = lines[i]
        if line.startswith("#"):
            heading = line.lstrip("#").strip()
        elif (line.strip().startswith("|") and i + 1 < len(lines)
              and _SEP.match(lines[i + 1].strip())):
            headers = _cells(line)
            start, rows = i + 1, []
            i += 2
            while i < len(lines) and lines[i].strip().startswith("|"):
                rows.append(Row(_cells(lines[i]), i + 1, lines[i], headers))
                i += 1
            tables.append(Table(headers, rows, start, heading))
            continue
        i += 1
    return tables


def table_with(text, *names):
    """The first table that has all these columns. Column names are load-bearing; headings get
    edited."""
    for table in parse_tables(text):
        if table.has(*names):
            return table
    return None


def section(text, heading_substr, level=None):
    """The first section whose heading contains `heading_substr`, heading line included, up to the
    next heading of the same or a shallower level. '' if there is none."""
    want = heading_substr.lower()
    lines = text.split("\n")
    start, start_level = None, 0
    for idx, line in enumerate(lines):
        m = re.match(r"^(#{1,6})\s+(.*)$", line)
        if not m:
            continue
        lv, title = len(m.group(1)), m.group(2)
        if start is None:
            if want in title.lower() and (level is None or lv == level):
                start, start_level = idx, lv
        elif lv <= start_level:
            return "\n".join(lines[start:idx]).rstrip()
    return "\n".join(lines[start:]).rstrip() if start is not None else ""
