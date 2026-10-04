#!/usr/bin/env python3
"""Fetch a fan wiki's pages through its MediaWiki API, as readable text, for the canon researcher.

Fan wikis (Fandom, Wikipedia, most standalone wikis) run MediaWiki, whose `api.php` is the route
they give to programs. Fandom's HTML pages sit behind a bot challenge; its API answers. This tool
uses the API only, names itself honestly in its user agent, waits between requests, honours a
`robots.txt` it can read, and never tries to get past a refusal: a page it cannot have is reported
`blocked`, and the researcher says so.

  search WIKI QUERY...            titles and one line each, best match first
  category WIKI NAME              the pages in a category (`Characters`, `Episodes`)
  page WIKI TITLE... --out DIR    each page as DIR/<Title>.md, from the API's rendered page: the
                                  infobox as `key: value` lines (ages, status, affiliations live
                                  there), then the body as text, with navboxes, references,
                                  galleries and edit links dropped. A page already in DIR is not
                                  fetched again (--refresh does)

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
    return "\n".join(lines).rstrip() + "\n", len(box)


def safe_name(title):
    return re.sub(r"[^\w.-]+", "_", title).strip("_")[:120] + ".md"


# ------------------------------------------------------------------------------- the CLI

def arg(s):
    return urllib.parse.unquote(s).replace("_", " ")


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
    p.add_argument("--limit", type=int, default=500)
    p = sub.add_parser("page")
    p.add_argument("wiki")
    p.add_argument("titles", nargs="+")
    p.add_argument("--out", required=True)
    p.add_argument("--refresh", action="store_true")
    args = ap.parse_args(argv)
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
