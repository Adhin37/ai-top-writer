#!/usr/bin/env python3
"""Check the knowledge bases' shape, and count what each doc asks of its reader.

Checks (OKF, and this repo's wiring):
  * every `.md` under `kb/` except an `index.md` has frontmatter with a non-empty `type`;
  * every doc in a role's folder is linked from that role's `index.md`, and every link in an index
    resolves;
  * every `.claude/agents/*.md` names a `kb/<role>/prompt.md` that exists, and an agent on a
    Sonnet model runs at effort `high` (warn: below it Sonnet 5.5 loses more than it saves, above
    it Opus at `medium` is cheaper for the same score; docs/experiments/2026-10-04-model-effort.md);
  * no doc carries dated text (a date, a run, plan, session or lesson number; warn): an agent
    reading why a rule exists spends attention on the past, and the history lives in `docs/`;
  * with --novel, no doc names the novel's own proper nouns (its lexicon's Names table, and its
    capitalised terms of art): the last novel leaks into the examples written right after it. A
    near match (one letter off, or the name plus a short ending: Varrow and Harrow, Ness and Nessa)
    is a warn: it runs the other way just as often, an example's noun copied into a new novel;
  * with --nouns, the same sweep for the names in a plain list (a studied book's, from
    tools/study.py): a finding taken from a published book goes in with invented nouns.

Then, as information only, each doc's words and negations ("not", "never", "don't" …). A doc that
grows by adding "don't" lines is getting worse, whatever its length; the count is a trend to watch,
never a limit.

Findings print as `level check: detail`; the exit status is 0 whatever is found.

Usage:
  kb_check.py [--novel NOVEL_DIR ...] [--nouns FILE ...] [--counts]
"""
import argparse
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from lib import mdio  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LINK = re.compile(r"\]\(([^)#\s]+)(?:#[^)]*)?\)")
NEGATION = re.compile(
    r"\b(?:not|never|no|nothing|nobody|none|nor|cannot|can't|won't|don't|doesn't|didn't|isn't|"
    r"aren't|wasn't|weren't|shouldn't|mustn't)\b", re.I)
RESERVED = ("index.md",)
DATED = re.compile(r"\b20\d\d-[01]\d\b|\brun #\d|\bplan 0?\d{1,2}[a-z]?\b|\bsession \d+\b|"
                   r"\blesson \d+", re.I)
SONNET_EFFORT = "high"


def docs(kb):
    for dirpath, _dirs, files in os.walk(kb):
        for name in sorted(files):
            if name.endswith(".md"):
                yield os.path.join(dirpath, name)


def check_types(kb, out):
    for path in docs(kb):
        if os.path.basename(path) in RESERVED:
            continue
        fm, _ = mdio.frontmatter(mdio.read_text(path))
        if not str(fm.get("type") or "").strip():
            out.append(("defect", "type", "%s has no `type` in its frontmatter"
                        % os.path.relpath(path, os.path.dirname(kb))))


def check_indexes(kb, out):
    for bundle in sorted(os.listdir(kb)):
        bdir = os.path.join(kb, bundle)
        if not os.path.isdir(bdir):
            continue
        index = os.path.join(bdir, "index.md")
        rel = "kb/%s" % bundle
        if not os.path.isfile(index):
            out.append(("defect", "index", "%s has no index.md" % rel))
            continue
        links = LINK.findall(mdio.read_text(index))
        for target in links:
            if "://" not in target and not os.path.exists(os.path.join(bdir, target)):
                out.append(("defect", "link", "%s/index.md links %s, which does not exist"
                            % (rel, target)))
        linked = {os.path.normpath(os.path.join(bdir, t)) for t in links}
        for name in sorted(os.listdir(bdir)):
            path = os.path.join(bdir, name)
            if name.endswith(".md") and name not in RESERVED and path not in linked:
                out.append(("warn", "unlinked", "%s/%s is not in its index" % (rel, name)))
    for path in docs(kb):
        if os.path.basename(path) in RESERVED:
            continue
        for target in LINK.findall(mdio.read_text(path)):
            if "://" not in target and not os.path.exists(
                    os.path.join(os.path.dirname(path), target)):
                out.append(("defect", "link", "%s links %s, which does not exist"
                            % (os.path.relpath(path, os.path.dirname(kb)), target)))


def check_agents(agents, root, out):
    if not os.path.isdir(agents):
        return
    for name in sorted(os.listdir(agents)):
        if not name.endswith(".md"):
            continue
        text = mdio.read_text(os.path.join(agents, name))
        m = re.search(r"kb/([\w-]+)/prompt\.md", text)
        if not m:
            out.append(("defect", "agent", "%s names no kb/<role>/prompt.md" % name))
        elif not os.path.isfile(os.path.join(root, m.group(0))):
            out.append(("defect", "agent", "%s names %s, which does not exist"
                        % (name, m.group(0))))
        fm, _ = mdio.frontmatter(text)
        model, effort = str(fm.get("model") or ""), str(fm.get("effort") or "")
        if "sonnet" in model and effort != SONNET_EFFORT:
            out.append(("warn", "effort", "%s runs %s at effort %s: Sonnet runs at %s; a role that "
                        "needs more moves to Opus at medium" % (name, model, effort or "(default)",
                                                                SONNET_EFFORT)))


def check_dated(kb, out):
    for path in docs(kb):
        for i, line in enumerate(mdio.read_text(path).splitlines(), 1):
            m = DATED.search(line)
            if m:
                out.append(("warn", "dated", "%s:%d: %r - history belongs in docs/, not in a "
                            "knowledge base" % (os.path.relpath(path, os.path.dirname(kb)), i,
                                                m.group(0))))


def _table_nouns(text, first_headers):
    """(whole terms, single words) from the first column of tables whose first header is one of
    `first_headers`."""
    terms, words = set(), set()
    for table in mdio.parse_tables(text):
        first = mdio.norm_header(table.headers[0]) if table.headers else ""
        if first not in first_headers:
            continue
        for row in table.rows:
            cell = re.sub(r"\(.*?\)", "", row.first()).strip("* ")
            for part in re.split(r"\s*/\s*", cell):
                ws = [w for w in re.findall(r"[A-Z][\w'-]+", part)
                      if w.lower() not in ("the", "of", "and")]
                if len(ws) > 1:
                    terms.add(" ".join(ws))
                elif ws:
                    words.add(ws[0])
    return terms, words


NUMBER_WORDS = {w.capitalize() for w in (
    "zero one two three four five six seven eight nine ten eleven twelve thirteen fourteen fifteen "
    "sixteen seventeen eighteen nineteen twenty thirty forty fifty sixty seventy eighty ninety "
    "hundred thousand first second third fourth fifth sixth seventh eighth ninth tenth").split()}


def novel_nouns(novel, ordinary=frozenset()):
    """(names, terms): the proper nouns a novel declares. Names are its people and places, matched
    anywhere; terms are its capitalised coinages, whole multi-word terms anywhere and single words
    only mid-sentence, so an ordinary word at the start of a sentence is not a leak. A word split
    off a longer name that is in `ordinary` ("Nine" of "Nine Steps") is a term too."""
    lexicon = mdio.read_text(os.path.join(novel, "bible", "lexicon.md"))
    world = mdio.read_text(os.path.join(novel, "bible", "world.md"))
    names = set()
    name_terms, name_words = _table_nouns(lexicon, ("canonical", "name"))
    split = set()
    for full in name_terms | name_words:
        names.add(full)
        split.update(w for w in full.split() if len(w) >= 4 and w != full)
    place_terms, place_words = _table_nouns(world, ("place", "location", "name"))
    names |= place_terms | {w for w in place_words if len(w) >= 4}
    split -= NUMBER_WORDS                   # "Nine" of "Nine Steps" is any deck's, any day's
    common = {w for w in split if w.lower() in ordinary}
    names |= split - common
    terms, words = _table_nouns(lexicon, ("term",))
    return sorted(names), sorted((terms | words | common) - names)


def file_nouns(path, ordinary=frozenset()):
    """(names, terms) from a plain list, one a line (`#` starts a comment): a studied book's
    people, places and coinages, from tools/study.py. Each line, and each capitalised word of a
    longer one, is a name matched anywhere; a word split off that is in `ordinary` (the knowledge
    base writes it in lower case: "Your" of "Your Name") is a term, matched mid-sentence only."""
    names, terms = set(), set()
    for line in mdio.read_text(path).splitlines():
        line = line.split("#", 1)[0].strip()
        if line:
            names.add(line)
            for w in line.split():
                if len(w) >= 4 and w[:1].isupper() and w != line:
                    (terms if w.lower() in ordinary else names).add(w)
    return sorted(names), sorted(terms - names)


def ordinary_words(kb):
    """The words the knowledge base writes in lower case somewhere."""
    return {w for path in docs(kb) for w in re.findall(r"\b[a-z]{4,}\b", mdio.read_text(path))}


def check_leaks(kb, names, terms, source, out):
    if not names and not terms:
        out.append(("warn", "leak", "no proper nouns found in %s" % source))
        return
    patterns = [(n, re.compile(r"\b%s\b" % re.escape(n))) for n in names]
    for t in terms:
        if " " in t:
            patterns.append((t, re.compile(r"\b%s\b" % re.escape(t))))
        else:   # mid-sentence only: after a lowercase word, a comma or "the"
            patterns.append((t, re.compile(r"(?<=[a-z,;] )%s\b" % re.escape(t))))
    for path in docs(kb):
        text = mdio.read_text(path)
        for noun, rx in patterns:
            for m in rx.finditer(text):
                line = text.count("\n", 0, m.start()) + 1
                out.append(("defect", "leak", "%s line %d names %r, from %s"
                            % (os.path.relpath(path, os.path.dirname(kb)), line, noun, source)))


def _near(a, b):
    """True when two different names are one edit apart (both 5+ letters), or one is the other
    plus at most two letters (both 4+): the copies a new name makes of an old one."""
    if a == b or min(len(a), len(b)) < 4:
        return False
    if abs(len(a) - len(b)) <= 2 and (a.startswith(b) or b.startswith(a)):
        return True
    if min(len(a), len(b)) < 5 or abs(len(a) - len(b)) > 1:
        return False
    if len(a) == len(b):
        return sum(x != y for x, y in zip(a, b)) == 1
    short, long_ = sorted((a, b), key=len)
    return any(long_[:i] + long_[i + 1:] == short for i in range(len(long_)))


def check_near_names(kb, names, source, out):
    singles = {n for n in names if " " not in n and len(n) >= 4}
    texts = [(path, mdio.read_text(path)) for path in docs(kb)]
    # a word the knowledge base uses as a name somewhere (capitalised mid-sentence), not "Borrow"
    # at the head of a sentence
    proper = {m.group(1) for _p, text in texts
              for m in re.finditer(r"(?<=[a-z,;] )([A-Z][a-z]{3,})\b", text)}
    seen = set()
    for path, text in texts:
        for m in re.finditer(r"\b[A-Z][a-z]{3,}\b", text):
            word = m.group(0)
            if word not in proper:
                continue
            for name in singles:
                if (name, word) not in seen and _near(name, word):
                    seen.add((name, word))
                    line = text.count("\n", 0, m.start()) + 1
                    out.append(("warn", "leak", "%s line %d names %r, near %r from %s"
                                % (os.path.relpath(path, os.path.dirname(kb)), line, word,
                                   name, source)))


def counts(kb):
    """(path, words, negations) for every doc, frontmatter left out."""
    rows = []
    for path in docs(kb):
        _fm, body = mdio.split_frontmatter(mdio.read_text(path))
        rows.append((os.path.relpath(path, os.path.dirname(kb)), len(body.split()),
                     len(NEGATION.findall(body))))
    return rows


def run(root=ROOT, novels=(), noun_files=()):
    kb = os.path.join(root, "kb")
    out = []
    check_types(kb, out)
    check_indexes(kb, out)
    check_agents(os.path.join(root, ".claude", "agents"), root, out)
    check_dated(kb, out)
    ordinary = ordinary_words(kb) if novels or noun_files else set()
    for novel in novels:
        names, terms = novel_nouns(novel, ordinary)
        source = os.path.basename(os.path.normpath(novel))
        check_leaks(kb, names, terms, source, out)
        check_near_names(kb, names, source, out)
    for path in noun_files:
        names, terms = file_nouns(path, ordinary)
        check_leaks(kb, names, terms, path, out)
        check_near_names(kb, names, path, out)
    return out


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--novel", action="append", default=[],
                    help="sweep kb/ for this novel's proper nouns (repeatable)")
    ap.add_argument("--nouns", action="append", default=[],
                    help="sweep kb/ for the names in this file, one a line (repeatable)")
    ap.add_argument("--counts", action="store_true", help="print words and negations per doc")
    args = ap.parse_args(argv)
    found = run(novels=args.novel, noun_files=args.nouns)
    order = {"defect": 0, "warn": 1, "note": 2}
    for level, check, detail in sorted(found, key=lambda f: order[f[0]]):
        print("%s %s: %s" % (level, check, detail))
    if args.counts:
        for path, words, neg in counts(os.path.join(ROOT, "kb")):
            print("note counts: %-46s %5d words  %3d negations" % (path, words, neg))
    n = {lv: sum(1 for f in found if f[0] == lv) for lv in order}
    print("%d defect · %d warn%s" % (n["defect"], n["warn"],
                                     " — clean" if not n["defect"] and not n["warn"] else ""))
    return 0


if __name__ == "__main__":
    sys.exit(main())
