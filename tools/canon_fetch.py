#!/usr/bin/env python3
"""Fetch a fan wiki's pages through its MediaWiki API, as readable text, for the canon researcher.

Fan wikis (Fandom, Wikipedia, most standalone wikis) run MediaWiki, whose `api.php` is the route
they give to programs. Fandom's HTML pages sit behind a bot challenge; its API answers. This tool
uses the API only, names itself honestly in its user agent, waits between requests, honours a
`robots.txt` it can read, and never tries to get past a refusal: a page it cannot have is reported
`blocked`, and the researcher says so.

  search WIKI QUERY...            titles and one line each, best match first
  category WIKI NAME              the pages in a category (`Characters`, `Episodes`), 100 at most
                                  (--limit)
  page WIKI TITLE... --out DIR    each page as DIR/<Title>.md, from the API's rendered page: the
                                  infobox as `key: value` lines (ages, status, affiliations live
                                  there), then the body as text, with navboxes, references,
                                  galleries and edit links dropped. A page already in DIR is not
                                  fetched again (--refresh does). A transcript gets a
                                  `## Scene N — <speakers>` heading at each scene
  toc FILE...                     each heading with its line range and size: Read one section with
                                  offset = the first line, limit = the line count. Given several
                                  files, one line each (its size and heading count); --full for all
  grep PATH WORDS... [--context N]
                                  each paragraph holding every word, under its file and nearest
                                  heading, with its line number; capped (--max, at most 100; context
                                  at most 3), the rest counted
  restyle DIR                     add the scene headings to transcripts saved before they existed

WIKI is a host (`<name>.fandom.com`, a standalone wiki) or an `api.php` URL. Wikipedia's robots.txt
shuts its API to programs like this one, so the tool refuses it: read Wikipedia with WebFetch.
Titles take underscores for spaces, and `%28` `%29` for brackets: the guard lets a role's shell
pass no quotes and no brackets. The cache under `novels/<slug>/work/canon/src/` is the researcher's evidence: the
dossier cites it.

Exit status: 0; 1 on a bad call; 3 when every page or request was refused or failed.
"""
import argparse
import json
import os
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
import urllib.robotparser
from html.parser import HTMLParser

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from lib import mdio  # noqa: E402

USER_AGENT = ("ai-top-writer-canon/0.1 (fan-fiction research; MediaWiki API only; "
              "python-urllib)")
PAUSE = 1.0             # seconds between requests to the same wiki
TIMEOUT = 30

_last = {}


# ------------------------------------------------------------------------------- the API

def api_url(wiki):
    if "://" in wiki:
        return wiki
    host = wiki.strip("/")
    path = "/w/api.php" if host.endswith(("wikipedia.org", "wikimedia.org", "wiktionary.org",
                                          "wikiquote.org")) else "/api.php"
    return "https://%s%s" % (host, path)


def page_url(api, title):
    base = api.rsplit("/", 2)[0] if api.endswith("/w/api.php") else api.rsplit("/", 1)[0]
    return "%s/wiki/%s" % (base, urllib.parse.quote(title.replace(" ", "_")))


class Refused(Exception):
    """The wiki would not serve this request (a status, a robots rule, a challenge page)."""


def robots_allows(api, cache={}):
    """False only when a robots.txt we could read disallows the API for us."""
    parts = urllib.parse.urlsplit(api)
    root = "%s://%s" % (parts.scheme, parts.netloc)
    if root not in cache:
        rp = urllib.robotparser.RobotFileParser()
        try:
            req = urllib.request.Request(root + "/robots.txt", headers={"User-Agent": USER_AGENT})
            with urllib.request.urlopen(req, timeout=TIMEOUT) as resp:
                body = resp.read().decode("utf-8", "replace")
            rp.parse(body.splitlines() if "<html" not in body[:500].lower() else [])
            cache[root] = rp
        except (urllib.error.URLError, OSError, ValueError):
            cache[root] = None          # unreadable: the API's own answer decides
    rp = cache[root]
    return rp is None or rp.can_fetch(USER_AGENT, api)


def get(api, params, opener=None):
    """One API call, JSON back. Raises Refused."""
    if not robots_allows(api):
        raise Refused("robots.txt disallows %s for this tool" % api)
    wait = PAUSE - (time.time() - _last.get(api, 0))
    if wait > 0:
        time.sleep(wait)
    query = dict(params, format="json", formatversion="2")
    req = urllib.request.Request(api + "?" + urllib.parse.urlencode(query),
                                 headers={"User-Agent": USER_AGENT})
    try:
        with (opener or urllib.request.urlopen)(req, timeout=TIMEOUT) as resp:
            body = resp.read().decode("utf-8", "replace")
    except urllib.error.HTTPError as exc:
        raise Refused("HTTP %d from %s" % (exc.code, api))
    except (urllib.error.URLError, OSError) as exc:
        raise Refused("%s: %s" % (api, exc))
    finally:
        _last[api] = time.time()
    try:
        data = json.loads(body)
    except ValueError:
        raise Refused("%s answered with a page, not the API (a bot challenge?)" % api)
    if isinstance(data, dict) and data.get("error"):
        raise Refused("%s: %s" % (api, data["error"].get("info") or data["error"]))
    return data


def search(api, query, limit=10, opener=None):
    data = get(api, {"action": "query", "list": "search", "srsearch": query,
                     "srlimit": str(limit)}, opener)
    return [(r.get("title", ""), strip_html(r.get("snippet", "")))
            for r in data.get("query", {}).get("search", [])]


def category(api, name, limit=500, opener=None):
    name = name if name.lower().startswith("category:") else "Category:" + name
    out, cont = [], {}
    while len(out) < limit:
        data = get(api, dict({"action": "query", "list": "categorymembers", "cmtitle": name,
                              "cmlimit": str(min(500, limit - len(out)))}, **cont), opener)
        out += [m.get("title", "") for m in data.get("query", {}).get("categorymembers", [])]
        cont = data.get("continue") or {}
        if not cont:
            break
    return out


def parse(api, title, opener=None):
    """(resolved title, rendered HTML, categories). Follows redirects. Raises Refused or KeyError."""
    try:
        data = get(api, {"action": "parse", "page": title, "prop": "text|categories",
                         "redirects": "1", "disablelimitreport": "1", "disableeditsection": "1"},
                   opener)
    except Refused as exc:
        if "missingtitle" in str(exc) or "doesn't exist" in str(exc):
            raise KeyError(title)
        raise
    page = data.get("parse") or {}
    if "text" not in page:
        raise KeyError(title)
    text = page["text"]
    if isinstance(text, dict):                  # formatversion 1
        text = text.get("*", "")
    cats = [c.get("category", c.get("*", "")).replace("_", " ")
            for c in page.get("categories", []) if not c.get("hidden")]
    return page.get("title", title), text, cats


# ------------------------------------------------------------------------------- the page

SKIP_TAGS = {"script", "style", "figure", "noscript", "audio", "video", "map"}
SKIP_CLASSES = {"navbox", "reference", "references", "reflist", "mw-references-wrap",
                "mw-editsection", "toc", "gallery", "wikia-gallery", "noprint", "thumb",
                "mw-empty-elt", "printfooter", "error", "edit-infobox", "smwttcontent",
                "popupformlink"}
VOID = {"br", "img", "hr", "meta", "link", "input", "wbr", "source", "col", "area", "base",
        "track", "embed", "param"}
BLOCK = {"p", "div", "li", "dd", "dt", "blockquote", "tr", "table", "ul", "ol", "dl", "section",
         "h1", "h2", "h3", "h4", "h5", "h6", "pre", "center"}


def strip_html(s):
    return re.sub(r"<[^>]+>", "", s).replace("&quot;", '"').replace("&amp;", "&").strip()


def squeeze(s):
    return re.sub(r"\s+", " ", s).strip()


class Page(HTMLParser):
    """A rendered wiki page as (infobox pairs, text lines). The infobox is a Fandom portable
    infobox (`aside.portable-infobox`) or a classic `table.infobox`; navboxes, references,
    galleries and edit links are dropped."""

    def __init__(self):
        HTMLParser.__init__(self, convert_charrefs=True)
        self.stack, self.lines, self.buf, self.prefix = [], [], [], ""
        self.box, self.label, self.cap, self.capbuf = [], None, None, []

    def skipping(self):
        return any("skip" in f for _t, f in self.stack)

    def in_box(self):
        return any("box" in f for _t, f in self.stack)

    def flush(self):
        line = squeeze("".join(self.buf)).strip(" |")
        if line:
            self.lines.append(self.prefix + line)
        self.buf, self.prefix = [], ""

    def handle_starttag(self, tag, attrs):
        if tag in VOID:
            if tag == "br" and not self.skipping():
                (self.capbuf if self.cap else self.buf).append("; " if self.cap else " ")
            return
        cls = set((dict(attrs).get("class") or "").split())
        flags = set()
        if self.skipping():
            pass
        elif tag in SKIP_TAGS or cls & SKIP_CLASSES:
            flags.add("skip")
        elif "portable-infobox" in cls or (tag == "table" and "infobox" in cls):
            self.flush()
            flags.add("box")
        elif self.in_box():
            kind = None
            if "pi-data-label" in cls or (tag == "th" and not self.cap):
                kind = "label"
            elif "pi-data-value" in cls or (tag == "td" and not self.cap):
                kind = "value"
            elif "pi-title" in cls:
                kind = "title"
            elif "pi-header" in cls:
                kind = "header"
            if kind and not self.cap:
                self.cap, self.capbuf = kind, []
                flags.add("cap")
            elif tag == "li" and self.cap and self.capbuf:
                self.capbuf.append("; ")
        else:
            if tag in BLOCK:
                self.flush()
                if re.match(r"^h[1-6]$", tag):
                    self.prefix = "#" * max(2, int(tag[1])) + " "
                    flags.add("head")
                elif tag == "li":
                    self.prefix = "- "
            elif tag in ("td", "th") and self.buf:
                self.buf.append(" | ")
        self.stack.append((tag, flags))

    def handle_endtag(self, tag):
        idx = next((i for i in range(len(self.stack) - 1, -1, -1) if self.stack[i][0] == tag),
                   None)
        if idx is None:
            return
        while len(self.stack) > idx:
            t, flags = self.stack.pop()
            if "cap" in flags:
                self.end_capture()
            if "head" in flags:
                self.lines.append("")
            if t in BLOCK and not self.skipping() and not self.in_box():
                self.flush()

    def end_capture(self):
        text = squeeze("".join(self.capbuf)).strip(" ;")
        kind, self.cap, self.capbuf = self.cap, None, []
        if not text:
            return
        if kind == "label":
            if self.label:                      # a label with no value: a header row
                self.box.append(("§", self.label))
            self.label = text
        elif kind == "value":
            self.box.append((self.label or "", text))
            self.label = None
        elif kind == "title":
            self.box.append(("name", text))
        else:
            self.box.append(("§", text))

    def handle_data(self, data):
        if self.skipping():
            return
        if self.cap:
            self.capbuf.append(data)
        elif not self.in_box():
            self.buf.append(data)

    def result(self):
        self.flush()
        text = "\n".join(self.lines)
        return self.box, re.sub(r"\n{3,}", "\n\n", text).strip()


def render(title, url, html, cats, fetched):
    page = Page()
    page.feed(html)
    page.close()
    box, text = page.result()
    lines = ["# %s" % title, "", "source: %s" % url, "fetched: %s" % fetched]
    if cats:
        lines.append("categories: %s" % ", ".join(cats))
    if box:
        lines.append("")
        lines.append("## Infobox")
        for key, value in box:
            lines.append(("### %s" % value) if key == "§" else
                         ("%s: %s" % (key, value)) if key else value)
    lines += ["", text]
    out = "\n".join(lines).rstrip() + "\n"
    if is_transcript(title, cats):
        out = add_scenes(out)
    return out, len(box)


# ------------------------------------------------------------------------------- transcripts

# A change of place or time, in a stage direction. "Cut to" alone is usually a camera cut inside a
# scene; it breaks a scene only once the scene has run SCENE_CHARS (some transcripts use nothing
# else).
SCENE_MARK = re.compile(r"\bscene\s+(?:changes|cuts|shifts|switches|transitions|returns)\b"
                        r"|\bfades?\s+(?:to|from|in|out)\b|\bflashback\b", re.I)
CUT = re.compile(r"\bcut(?:s)?\s+(?:back\s+)?to\b", re.I)
SPEAKER = re.compile(r"^([^|\[\]]{1,40}?) \| ")
HEADER = re.compile(r"^(?:source|fetched|categories): ")
SCENE_CHARS = 3000
MAX_SPEAKERS = 6


def is_transcript(title, cats):
    return (title.lower().startswith("transcript:")
            or any(c.lower().endswith("transcripts") for c in cats))


def add_scenes(text):
    """A saved transcript with a `## Scene N — <speakers>` heading at each scene: after the header
    block (`# Title`, `source:`…), up to the page's first `##` heading (Cast, Locations). A page
    that already has scene headings comes back unchanged."""
    lines = text.split("\n")
    if any(l.startswith("## Scene ") for l in lines):
        return text
    start = 1 if lines and lines[0].startswith("# ") else 0
    while start < len(lines) and (not lines[start].strip() or HEADER.match(lines[start])):
        start += 1
    end = next((i for i in range(start, len(lines)) if lines[i].startswith("## ")), len(lines))
    body = lines[start:end]
    scenes, cur, size = [], [], 0
    for line in body:
        stage = bool(line.strip()) and not SPEAKER.match(line)
        if cur and size and stage and (SCENE_MARK.search(line) or
                                       (size >= SCENE_CHARS and CUT.search(line))):
            scenes.append(cur)
            cur, size = [], 0
        cur.append(line)
        size += len(line)
    if cur:
        scenes.append(cur)
    out = []
    for n, scene in enumerate(scenes, 1):
        out += [scene_heading(n, scene), ""] + scene + [""]
    text = "\n".join(lines[:start] + [""] + out + lines[end:])
    return re.sub(r"\n{3,}", "\n\n", text)


def scene_heading(n, scene):
    who = []
    for line in scene:
        m = SPEAKER.match(line)
        if m and m.group(1).strip() not in who:
            who.append(m.group(1).strip())
    names = ", ".join(who[:MAX_SPEAKERS])
    if len(who) > MAX_SPEAKERS:
        names += " +%d" % (len(who) - MAX_SPEAKERS)
    return "## Scene %d — %s" % (n, names or "no dialogue")


# ------------------------------------------------------------------------------- reading

HEADING = mdio.HEADING
headings = mdio.headings
size = mdio.size
toc = mdio.toc


def md_files(path):
    if os.path.isfile(path):
        return [path]
    return sorted(os.path.join(d, f) for d, _s, fs in os.walk(path) for f in fs
                  if f.endswith(".md"))


GREP_CONTEXT = 3        # lines either side of a hit, at most
GREP_MAX = 100          # hits, at most


def clip(text, pat, width):
    """`text` cut to `width` characters around `pat`'s first match (or from the start)."""
    if len(text) <= width:
        return text
    at = pat.search(text).start() if pat else 0
    lo = max(0, min(at - width // 3, len(text) - width))
    return ("…" if lo else "") + text[lo:lo + width] + "…"


def grep(path, words, context=0, limit=40, width=400):
    """(output lines, hits past the cap). A paragraph is a line; it matches when it holds every
    word, case ignored. A long paragraph is cut to `width` characters around its first match."""
    pats = [re.compile(r"\b" + re.escape(w), re.I) for w in words]
    rows, shown, extra, extra_files = [], 0, 0, set()
    for f in md_files(path):
        with open(f, encoding="utf-8") as fh:
            lines = fh.read().split("\n")
        head, printed_file, last = "", False, -1
        for i, line in enumerate(lines):
            m = HEADING.match(line)
            if m:
                head = line
                continue
            if not all(p.search(line) for p in pats):
                continue
            if shown >= limit:
                extra += 1
                extra_files.add(f)
                continue
            if not printed_file:
                rows.append("== %s" % f)
                printed_file = True
            rows.append("   [%s]" % (head or "top"))
            for j in range(max(0, i - context), min(len(lines), i + context + 1)):
                if j <= last or not lines[j].strip():
                    continue
                text = clip(lines[j], pats[0] if j == i else None, width)
                rows.append("%6d%s %s" % (j + 1, ":" if j == i else "-", text))
                last = j
            shown += 1
    return rows, extra, len(extra_files)


def restyle(path):
    done = []
    for f in md_files(path):
        with open(f, encoding="utf-8") as fh:
            text = fh.read()
        head = text.split("\n")[:6]
        title = head[0][2:] if head[0].startswith("# ") else ""
        cats = next((l[len("categories: "):].split(", ") for l in head
                     if l.startswith("categories: ")), [])
        if not is_transcript(title, cats):
            continue
        new = add_scenes(text)
        if new != text:
            with open(f, "w", encoding="utf-8") as fh:
                fh.write(new)
            done.append((f, sum(1 for l in new.split("\n") if l.startswith("## Scene "))))
    return done


def safe_name(title):
    return re.sub(r"[^\w.-]+", "_", title).strip("_")[:120] + ".md"


# ------------------------------------------------------------------------------- the CLI

def arg(s):
    return urllib.parse.unquote(s).replace("_", " ")


def read_cmd(args):
    """The commands on saved pages: no network."""
    if args.cmd == "toc":
        if len(args.files) > 1 and not args.full:
            # one line a file: a whole cache's headings would be the page-sized read toc replaces
            for f in args.files:
                rows = toc(f)
                print("%s, %d heading(s)" % (rows[0], len(rows) - 1))
            print("one line a file: toc FILE for its headings")
            return 0
        for f in args.files:
            print("\n".join(toc(f)))
        return 0
    if args.cmd == "grep":
        context, cap = min(args.context, GREP_CONTEXT), min(args.max, GREP_MAX)
        if (context, cap) != (args.context, args.max):
            print("(--context %d, --max %d at most)" % (GREP_CONTEXT, GREP_MAX))
        args.context, args.max = context, cap
        rows, extra, files = grep(args.path, [arg(w) for w in args.words], args.context,
                                  args.max)
        print("\n".join(rows) if rows else "no paragraph holds all of: %s" % " ".join(args.words))
        if extra:
            print("… %d more hit(s) in %d file(s) past the cap of %d: add a word, or grep one file"
                  % (extra, files, args.max))
        return 0
    done = restyle(args.dir)
    for f, n in done:
        print("restyled %s (%d scenes)" % (f, n))
    print("%d transcript(s) restyled" % len(done))
    return 0


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("search")
    p.add_argument("wiki")
    p.add_argument("query", nargs="+")
    p.add_argument("--limit", type=int, default=10)
    p = sub.add_parser("category")
    p.add_argument("wiki")
    p.add_argument("name")
    p.add_argument("--limit", type=int, default=100)
    p = sub.add_parser("page")
    p.add_argument("wiki")
    p.add_argument("titles", nargs="+")
    p.add_argument("--out", required=True)
    p.add_argument("--refresh", action="store_true")
    p = sub.add_parser("toc")
    p.add_argument("files", nargs="+")
    p.add_argument("--full", action="store_true", help="every file's headings, not one line each")
    p = sub.add_parser("grep")
    p.add_argument("path")
    p.add_argument("words", nargs="+")
    p.add_argument("--context", type=int, default=0)
    p.add_argument("--max", type=int, default=40)
    p = sub.add_parser("restyle")
    p.add_argument("dir")
    args = ap.parse_args(argv)
    if args.cmd in ("toc", "grep", "restyle"):
        return read_cmd(args)
    api = api_url(args.wiki)
    try:
        if args.cmd == "search":
            for title, snippet in search(api, " ".join(arg(q) for q in args.query), args.limit):
                print("%s · %s" % (title.replace(" ", "_"), snippet[:140]))
            return 0
        if args.cmd == "category":
            members = category(api, arg(args.name), args.limit)
            print("%d page(s) in %s" % (len(members), arg(args.name)))
            print("\n".join(m.replace(" ", "_") for m in members))
            if len(members) >= args.limit:
                print("… stopped at --limit %d: search the wiki for a name instead" % args.limit)
            return 0
    except Refused as exc:
        print("blocked %s" % exc)
        return 3
    os.makedirs(args.out, exist_ok=True)
    got = 0
    for raw in args.titles:
        title = arg(raw)
        path = os.path.join(args.out, safe_name(title))
        if os.path.isfile(path) and not args.refresh:
            print("cached %s -> %s" % (title, path))
            got += 1
            continue
        try:
            resolved, html, cats = parse(api, title)
        except Refused as exc:
            print("blocked %s · %s" % (title, exc))
            continue
        except KeyError:
            print("missing %s (no such page; try search)" % title)
            continue
        path = os.path.join(args.out, safe_name(resolved))
        out, box = render(resolved, page_url(api, resolved), html, cats,
                          time.strftime("%Y-%m-%d"))
        with open(path, "w", encoding="utf-8") as fh:
            fh.write(out)
        print("page %s -> %s (%d words, infobox %d)" % (resolved, path, len(out.split()), box))
        got += 1
    return 0 if got or not args.titles else 3


if __name__ == "__main__":
    sys.exit(main())
