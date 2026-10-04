#!/usr/bin/env python3
"""A new novel from `novels/_template/`, and the check that init filled it.

`new` copies the template to `novels/<slug>/`, sets `slug:` in `novel.md`, and makes `chapters/`
and `work/init/`. It refuses a directory that exists: the slug is permanent, and there is no undo
under `novels/`. The planner fills every file during init (`kb/planner/init.md`).

`check` reports whether init is done: every file the template has, no `{{…}}` placeholder left,
the config keys the roles read, a premise of three to seven sourced facts, every premise fact in
the ledger, the antagonist's face on the page by `opening.contract_by_ch`, ten to fifteen chapter
rows with a temperature and a hook, the protagonist's profile, a thread board for the plan's
ids, and no name word shared with another novel beside it (cold planners draw the same names).
Findings print as `level check: detail` (`defect`, `warn`, `note`), then a count line that ends
in `clean` when there is no defect and no warn. It reports and never gates: the exit status is 0
unless the novel cannot be found.

Usage:
  scaffold.py new SLUG               create novels/SLUG/ and print its path
  scaffold.py check NOVEL_DIR
"""
import argparse
import os
import re
import shutil
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from lib import mdio  # noqa: E402
from lib.novel import Novel, thread_refs  # noqa: E402
from state_check import Findings, due_chapter, first_int  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TEMPLATE = os.path.join(ROOT, "novels", "_template")
SLUG = re.compile(r"^[a-z0-9][a-z0-9-]{0,59}$")
PLACEHOLDER = re.compile(r"\{\{")
SKIP = (".gitkeep",)
REQUIRED_KEYS = ("title", "slug", "platform", "exposition", "genre", "narration.person",
                 "narration.tense", "pov.mode", "pov.pov_characters", "tone.register",
                 "tone.warmth", "mc.name", "opening.promise", "opening.contract_by_ch",
                 "content.rating", "content.romance")
TEMPS = ("fast", "tense", "loud", "warm", "funny", "bleak", "procedural", "quiet")
HOOKS = ("reveal", "arrival", "decision", "question", "threat", "reversal", "cliff", "quiet")
BLURB_WORDS = (60, 120)
PREMISE_FACTS = (3, 7)
PLAN_ROWS = (10, 15)
ROUNDS = 7
ROUND_FILE = re.compile(r"^round-(\d+)[a-z]?\.md$")


def template_files(template=TEMPLATE):
    """Every file the template has, as paths relative to it."""
    out = []
    for dirpath, _dirs, files in os.walk(template):
        for name in sorted(files):
            if name not in SKIP:
                out.append(os.path.relpath(os.path.join(dirpath, name), template))
    return sorted(out)


def new(slug, novels_dir=None, template=TEMPLATE):
    """Copy the template to novels_dir/slug and return the new path. Raises ValueError."""
    if not SLUG.match(slug or ""):
        raise ValueError("a slug is lowercase letters, digits and hyphens, at most 60, and does "
                         "not start with a hyphen or an underscore: %r" % slug)
    novels_dir = novels_dir or os.path.join(ROOT, "novels")
    dest = os.path.join(novels_dir, slug)
    if os.path.exists(dest):
        raise ValueError("%s exists; a novel is never overwritten" % dest)
    for rel in template_files(template):
        target = os.path.join(dest, rel)
        os.makedirs(os.path.dirname(target), exist_ok=True)
        shutil.copyfile(os.path.join(template, rel), target)
    for sub in ("chapters", os.path.join("work", "init")):
        os.makedirs(os.path.join(dest, sub), exist_ok=True)
    cfg = os.path.join(dest, "novel.md")
    text = mdio.read_text(cfg).replace('slug: "{{slug}}"', 'slug: "%s"' % slug, 1)
    with open(cfg, "w", encoding="utf-8") as fh:
        fh.write(text)
    return dest


# ------------------------------------------------------------------------------- check

def body_section(text, heading):
    """The words under a `# heading` of novel.md's body, heading excluded."""
    sec = mdio.section(mdio.frontmatter(text)[1], heading, level=1)
    return "\n".join(sec.split("\n")[1:]).strip()


def check_files(nov, out, template):
    for rel in template_files(template):
        if not os.path.isfile(nov.path(rel)):
            out.add("defect", "files", "%s is missing (the template has it)" % rel)
    for dirpath, _dirs, files in os.walk(nov.root):
        rel_dir = os.path.relpath(dirpath, nov.root)
        if rel_dir.split(os.sep)[0] in ("work", "chapters"):
            continue
        for name in sorted(files):
            if not name.endswith(".md"):
                continue
            path = os.path.join(dirpath, name)
            for n, line in enumerate(mdio.read_text(path).split("\n"), 1):
                if PLACEHOLDER.search(line):
                    out.add("defect", "placeholder", "%s:%d %s" % (
                        os.path.relpath(path, nov.root), n, line.strip()[:70]))


def check_config(nov, out):
    for key in REQUIRED_KEYS:
        value = nov.get(key)
        if value in (None, "", [], {}):
            out.add("defect", "config", "novel.md has no `%s`" % key)
    if str(nov.get("exposition") or "") not in ("", "clear", "gradual"):
        out.add("warn", "config", "exposition is `%s`; the roles read clear or gradual"
                % nov.get("exposition"))
    text = nov.text("novel.md")
    blurb = body_section(text, "blurb")
    n = len(blurb.split())
    if not blurb:
        out.add("defect", "config", "novel.md has no blurb under `# Blurb`")
    elif not BLURB_WORDS[0] <= n <= BLURB_WORDS[1]:
        out.add("note", "config", "the blurb measures %d words (a listing takes %d–%d)"
                % (n, BLURB_WORDS[0], BLURB_WORDS[1]))
    anchor = body_section(text, "style anchor")
    if not anchor:
        out.add("defect", "config", "novel.md has no sample under `# Style anchor`")
    else:
        out.add("note", "config", "the style anchor measures %d words" % len(anchor.split()))


def premise_ids(nov):
    t = mdio.table_with(nov.text("bible", "premise.md"), "id", "fact, in plain words",
                       "source")
    return t.rows if t else []


def check_premise(nov, out):
    text = nov.text("bible", "premise.md")
    breath = mdio.section(text, "in one breath")
    if len(breath.split("\n")) < 2 or not "\n".join(breath.split("\n")[1:]).strip():
        out.add("defect", "premise", "bible/premise.md has no `In one breath`")
    rows = premise_ids(nov)
    if not PREMISE_FACTS[0] <= len(rows) <= PREMISE_FACTS[1]:
        out.add("warn", "premise", "%d load-bearing facts; a premise holds %d to %d"
                % (len(rows), PREMISE_FACTS[0], PREMISE_FACTS[1]))
    for r in rows:
        if not r.get("source").strip(" —-"):
            out.add("defect", "premise", "%s has no source: a fact with no source is invented"
                    % r.first())


def check_ledger(nov, out):
    ledger = nov.ledger()
    facts = {r.first().strip("* "): r for r in ledger["facts"]}
    clear = str(nov.get("exposition") or "clear") == "clear"
    for p in premise_ids(nov):
        pid = p.first().strip("* ")
        row = facts.get(pid)
        if row is None:
            out.add("defect", "ledger", "premise fact %s has no row under Facts" % pid)
            continue
        due = due_chapter(row.get("due by ch"))
        if clear and due != 1:
            out.add("defect", "ledger", "%s is due by ch %s; with exposition clear every premise "
                    "fact is due by ch 1" % (pid, due))
    for r in ledger["facts"]:
        if not r.get("how it lands").strip(" —-"):
            out.add("warn", "ledger", "%s has no `how it lands`" % r.first())
    contract = first_int(nov.get("opening.contract_by_ch")) or 3
    faces = [due_chapter(r.get("on the page by ch")) for r in ledger["faces"]]
    if not ledger["faces"]:
        out.add("defect", "ledger", "no Faces rows: the antagonist needs a face on the page")
    elif not any(d is not None and d <= contract for d in faces):
        out.add("defect", "ledger", "no face is due on the page by ch %d (opening.contract_by_ch)"
                % contract)


def check_plan(nov, out):
    rows = nov.plan_rows()
    if not PLAN_ROWS[0] <= len(rows) <= PLAN_ROWS[1]:
        out.add("warn", "plan", "%d chapter rows; init plans %d to %d"
                % (len(rows), PLAN_ROWS[0], PLAN_ROWS[1]))
    temps, hooks = [], []
    for r in rows:
        tag = "ch %s" % r.first()
        if not r.get("event").strip(" —-"):
            out.add("defect", "plan", "%s has no event" % tag)
        temp, hook = r.get("temp").strip().lower(), r.get("hook").strip().lower()
        if temp not in TEMPS:
            out.add("warn", "plan", "%s temp `%s` is not one of %s" % (tag, temp, ", ".join(TEMPS)))
        if hook not in HOOKS:
            out.add("warn", "plan", "%s hook `%s` is not one of %s" % (tag, hook, ", ".join(HOOKS)))
        temps.append(temp)
        hooks.append(hook)
    for i in range(len(temps) - 2):
        if temps[i] and temps[i] == temps[i + 1] == temps[i + 2]:
            out.add("note", "plan", "chs %s–%s are all `%s`" % (rows[i].first(),
                                                              rows[i + 2].first(), temps[i]))
    for i in range(max(0, len(hooks) - 4)):
        window = hooks[i:i + 5]
        for kind in sorted(set(window)):
            if kind and window.count(kind) > 2:
                out.add("note", "plan", "`%s` ends %d of chs %s–%s" % (
                    kind, window.count(kind), rows[i].first(), rows[i + 4].first()))
    board = {r.first().strip("* ") for r in nov.threads()}
    named = sorted({tid for r in rows for _op, tid in thread_refs(r.get("threads"))},
                   key=lambda t: int(t[1:]))
    for tid in named:
        if tid not in board:
            out.add("defect", "threads", "%s is in the plan and not on state/threads.md" % tid)


def check_cast(nov, out):
    mc = str(nov.get("mc.name") or "")
    cast = nov.path("bible", "cast")
    names = []
    for fn in sorted(os.listdir(cast)) if os.path.isdir(cast) else []:
        if fn.endswith(".md") and not fn.startswith("_"):
            names.append(str(mdio.frontmatter(nov.text("bible", "cast", fn))[0].get("name") or ""))
    if mc and mc not in names:
        out.add("defect", "cast", "no profile in bible/cast/ has `name: %s`" % mc)
    if len([n for n in names if n]) < 2:
        out.add("warn", "cast", "%d profile(s); init writes at least the protagonist's and the "
                "antagonist's" % len(names))
    t = mdio.table_with(nov.text("bible", "cast", "_voices.md"), "character")
    voiced = {r.first().strip("* ") for r in (t.rows if t else [])}
    if mc and mc not in voiced:
        out.add("warn", "cast", "%s has no row in bible/cast/_voices.md" % mc)
    if not mdio.table_with(nov.text("bible", "lexicon.md"), "canonical", "never write as"):
        out.add("warn", "lexicon", "bible/lexicon.md has no Names table with `never write as`")


def name_words(nov):
    """{word: full name}: the capitalised words of the lexicon's Names rows. Rows that start with
    `the` are places and bodies (`the Middle Ward`), whose words are ordinary nouns."""
    t = mdio.table_with(nov.text("bible", "lexicon.md"), "canonical")
    out = {}
    for row in t.rows if t else []:
        name = re.sub(r"\(.*?\)", "", row.first()).strip("*` ").strip()
        if name.lower().startswith("the ") or PLACEHOLDER.search(name):
            continue
        for w in re.findall(r"\b[A-Z][a-z]{2,}\b", name):
            out.setdefault(w, name)
    return out


def check_shared_names(nov, out):
    """A name word this novel shares with another novel in the same directory. Each planner is a
    fresh spawn of the same model, so their first draws converge; two books with the same Pell
    read as one machine's books."""
    mine = name_words(nov)
    parent = os.path.dirname(nov.root)
    for other in sorted(os.listdir(parent)) if mine else []:
        o = Novel(os.path.join(parent, other))
        if other.startswith("_") or o.root == nov.root or not o.exists():
            continue
        theirs = name_words(o)
        for w in sorted(set(mine) & set(theirs)):
            out.add("warn", "names", "%s (%s) is also in %s (%s)" % (w, mine[w], other, theirs[w]))


def check_interview(nov, out):
    """The rounds asked (`work/init/round-N.md`, `round-Nb.md` for a re-ask) and answered."""
    init = nov.path("work", "init")
    files = sorted(f for f in (os.listdir(init) if os.path.isdir(init) else [])
                   if ROUND_FILE.match(f))
    if not files:
        out.add("note", "interview", "no round files in work/init/")
        return
    asked = sorted({int(ROUND_FILE.match(f).group(1)) for f in files})
    unanswered = [f for f in files
                  if not mdio.section(mdio.read_text(os.path.join(init, f)), "answers", level=2)]
    missing = [str(n) for n in range(1, ROUNDS + 1) if n not in asked]
    if missing:
        out.add("warn", "interview", "round(s) %s never asked" % ", ".join(missing))
    for f in unanswered:
        out.add("warn", "interview", "work/init/%s has no `## Answers`" % f)
    out.add("note", "interview", "%d round file(s): %s" % (len(files), ", ".join(files)))


def check(nov, template=TEMPLATE):
    out = Findings()
    check_files(nov, out, template)
    check_config(nov, out)
    check_premise(nov, out)
    check_ledger(nov, out)
    check_plan(nov, out)
    check_cast(nov, out)
    check_shared_names(nov, out)
    check_interview(nov, out)
    return out


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("new")
    p.add_argument("slug")
    p = sub.add_parser("check")
    p.add_argument("novel")
    args = ap.parse_args(argv)
    if args.cmd == "new":
        try:
            print(os.path.relpath(new(args.slug), os.getcwd()))
        except ValueError as e:
            sys.stderr.write("scaffold: %s\n" % e)
            return 1
        return 0
    nov = Novel(args.novel)
    if not nov.exists():
        sys.stderr.write("scaffold: no novel.md in %s\n" % args.novel)
        return 1
    print("\n".join(check(nov).lines()))
    return 0


if __name__ == "__main__":
    sys.exit(main())
