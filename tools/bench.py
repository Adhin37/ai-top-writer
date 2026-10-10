#!/usr/bin/env python3
"""Plan 06c's cheap comparisons: one role replayed on a frozen round, scored by agreement first.

  bench.py rounds NOVEL                    what each round of each chapter found and changed, from
                                           the files on disk (no spawn): verdict, notes,
                                           click-next, continuity findings, paragraphs the next
                                           draft changed, the notes file's size
  bench.py freeze NOVEL N K EXP ARM --role ROLE [--agent TYPE]
                                           a copy of NOVEL as it stood when round K of chapter N
                                           reached ROLE (continuity-editor, story-editor,
                                           line-editor, clerk; planner: before chapter N's
                                           beats, K ignored), at novels/<slug>--<exp>-<arm>/;
                                           prints the role's dispatch, as TYPE if given (an arm's
                                           variant, `<role>--<arm>`)
  bench.py arm ROLE ARM [--effort LEVEL] [--model MODEL] [--remove]
                                           writes .claude/agents/<role>--<arm>.md, the role's agent
                                           file with only effort or model changed (the Agent tool
                                           can override a model, not an effort); it registers at
                                           the next session start, and the guard holds it to the
                                           role's rules. --remove deletes it
  bench.py pair EXP NAME A=FILE B=FILE     two blind folders for the judge, X and Y swapped between
                                           them; appends the key to bench/EXP/key.md (the judge
                                           cannot open it) and prints both judge dispatches
  bench.py panel FOLDER [--agents A,B,C]   the benchmark's judge panel on one blind folder (mode 1):
                                           one dispatch per judge, by default two of `judge` (Opus 5)
                                           and one `judge--fable` (Fable 5.1), so the verdict is not
                                           three copies of one model's taste. Report each score with
                                           its model, and the spread beside the mean
  bench.py agree notes A B                 two notes files: the verdict, and notes matched by the
                                           quote on their `where` line
  bench.py agree continuity A B [--catch QUOTE]...
                                           two continuity files: findings matched by quote, and
                                           which of the known catches each one made

A frozen copy is as faithful as the files allow: chapters from N on, later rounds and the role's
own outputs are removed; state blocks, scene rows, timeline rows and threads opened from chapter N
on are cut, and ledger rows the clerk marked from chapter N on are `owed` again; the reader's
memory is the one the previous chapter accepted. **The bible keeps the folds of chapter N and
later**, which may hide a contradiction a fold settled: every arm, the
baseline replay included, reads the same copy, so compare arms with each other, and with the run's
own file only as a second reference. Copies live under novels/ (gitignored) because the roles may
write only there; delete them when the experiment is written up.

Reports and never gates: exit 0, or 1 on a bad call.
"""
import argparse
import difflib
import os
import random
import re
import shutil
import string
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import export_prose  # noqa: E402
import room  # noqa: E402
import wire  # noqa: E402
from lib import mdio  # noqa: E402

ROOT = room.ROOT
ROLES = ("continuity-editor", "story-editor", "line-editor", "clerk", "planner")
ARM_ROLES = ROLES + ("judge",)
PANEL = ("judge", "judge--fable", "judge")
MATCH_WORDS = 5     # a run of this many words in common makes two quotes the same passage

# what each role writes in round K; the copy must not hold it
OUTPUTS = {
    "continuity-editor": ("continuity-r{k}.md", "lint-r{k}.txt", "history-r{k}.txt",
                          "notes-r{k}.md"),
    "story-editor": ("notes-r{k}.md",),
    "line-editor": (),
    "clerk": ("fold.md",),
    "planner": (),          # chapter n's beats: its whole work folder goes (below)
}


# ---------------------------------------------------------------- rounds (lever 1, from disk)


def paragraphs(path):
    _, body = mdio.frontmatter(mdio.read_text(path))
    return [p.strip() for p in re.split(r"\n\s*\n", body) if p.strip()]


def changed(a, b):
    """(paragraphs of b that are new or rewritten, paragraphs in b)."""
    pa, pb = paragraphs(a), paragraphs(b)
    sm = difflib.SequenceMatcher(None, pa, pb, autojunk=False)
    same = sum(blk.size for blk in sm.get_matching_blocks())
    return len(pb) - same, len(pb)


def header(path):
    text = mdio.read_text(path)
    head = " ".join(wire.sections(text).get("", []))
    get = lambda key: (re.search(r"\b%s\s+(\S+)" % re.escape(key), head) or [None, "?"])[1]
    notes = sum(1 for l in wire.sections(text).get("Notes", []) if wire.NOTE_HEAD.match(l.strip()))
    return get("verdict"), notes, get("click-next"), get("owed"), len(text.split())


def findings(path):
    if not os.path.isfile(path):
        return None
    return sum(1 for l in mdio.read_text(path).splitlines() if wire.FINDING.match(l.strip()))


def rounds(novel):
    work = os.path.join(novel, "work")
    lines = ["ch  r  verdict  notes  click  owed   cont  changed   notes-words"]
    for ch in sorted(d for d in os.listdir(work) if re.match(r"^ch\d{4}$", d)):
        d = os.path.join(work, ch)
        ks = sorted(int(m.group(1)) for m in (re.match(r"^notes-r(\d+)\.md$", f)
                                               for f in os.listdir(d)) if m)
        for k in ks:
            verdict, notes, click, owed, size = header(os.path.join(d, "notes-r%d.md" % k))
            cont = findings(os.path.join(d, "continuity-r%d.md" % k))
            nxt = os.path.join(d, "draft-r%d.md" % (k + 1))
            diff = "%d/%d" % changed(os.path.join(d, "draft-r%d.md" % k), nxt) \
                if os.path.isfile(nxt) else "-"
            lines.append("%-3d %-2d %-8s %-6d %-6s %-6s %-5s %-9s %d"
                         % (int(ch[2:]), k, verdict, notes, click, owed,
                            "-" if cont is None else cont, diff, size))
    lines.append("changed: paragraphs of the next round's draft that are new or rewritten, "
                 "of its total")
    return "\n".join(lines)


# ---------------------------------------------------------------- freeze


def _cut_blocks(text, n):
    """continuity.md without the blocks of chapter n and later."""
    out, keep = [], True
    for line in text.split("\n"):
        m = re.match(r"^=C(\d+)=", line)
        if m:
            keep = int(m.group(1)) < n
        elif line.startswith("#"):
            keep = True
        if keep:
            out.append(line)
    return "\n".join(out).rstrip("\n") + "\n"


def _cut_rows(text, col, n):
    """A state table without rows whose `col` column is a chapter >= n."""
    out, idx = [], None
    for line in text.split("\n"):
        cells = [c.strip() for c in line.strip().strip("|").split("|")] if line.startswith("|") \
            else None
        if not cells:
            idx = None                  # the table ended; the next one has its own header
        elif idx is None and col in cells:
            idx = cells.index(col)
        elif cells and idx is not None and idx < len(cells) and cells[idx].isdigit() \
                and int(cells[idx]) >= n:
            continue
        out.append(line)
    return "\n".join(out)


def _cut_ledger(text, n):
    """The reader ledger with every status the clerk wrote at chapter n or later back to `owed`."""
    def back(m):
        return "| owed |" if int(m.group(1)) >= n else m.group(0)
    return re.sub(r"\|\s*\w+ ch(\d+)\b[^|\n]*\|(?=\s*$)", back, text, flags=re.M)


def _write(path, text):
    with open(path, "w", encoding="utf-8") as fh:
        fh.write(text)


def _round_of(name):
    m = re.search(r"-r(\d+)\.\w+$", name)
    return int(m.group(1)) if m else None


def freeze(novel, n, k, exp, arm, role, root=ROOT):
    """Copy novel to novels/<slug>--<exp>-<arm>/ as it stood when round k of chapter n reached
    role. Returns (the copy's repo-relative path, the source chapter)."""
    for name in (exp, arm):
        if not re.match(r"^[a-z0-9]+(-[a-z0-9]+)*$", name or ""):
            raise ValueError("%r: experiment and arm names are lowercase words joined by one `-`"
                             % name)
    src = room.Chapter(novel, n, root)
    slug = os.path.basename(src.novel)
    dest_rel = "novels/%s--%s-%s" % (slug, exp, arm)
    dest = os.path.join(root, dest_rel)
    if os.path.exists(dest):
        raise ValueError("%s exists; delete it to freeze again" % dest_rel)
    shutil.copytree(src.abs(src.novel), dest)

    cfg = os.path.join(dest, "novel.md")
    text = mdio.read_text(cfg)
    text, count = re.subn(r'(?m)^slug:\s*.*$', 'slug: "%s--%s-%s"' % (slug, exp, arm), text, 1)
    if not count:
        text = text.replace("---\n", '---\nslug: "%s--%s-%s"\n' % (slug, exp, arm), 1)
    _write(cfg, text)

    keep_chapter = n if role == "clerk" else n - 1
    chapters = os.path.join(dest, "chapters")
    for name in os.listdir(chapters) if os.path.isdir(chapters) else []:
        m = re.match(r"^(\d+)", name)
        if m and int(m.group(1)) > keep_chapter:
            os.remove(os.path.join(chapters, name))

    work = os.path.join(dest, "work")
    own = set(p.format(k=k) for p in OUTPUTS[role])
    for name in os.listdir(work):
        m = re.match(r"^ch(\d{4})$", name)
        if m and int(m.group(1)) > n:
            shutil.rmtree(os.path.join(work, name))
    wdir = os.path.join(work, "ch%04d" % n)
    for name in os.listdir(wdir) if role == "planner" else ():
        os.remove(os.path.join(wdir, name))
    for name in os.listdir(wdir):
        r = _round_of(name)
        if name in own or (r is not None and r > k) or (name == "fold.md" and role != "clerk"):
            os.remove(os.path.join(wdir, name))

    state = os.path.join(dest, "state")
    cut_from = n                    # the clerk writes chapter n's state; nobody else sees it
    for name, fn in (("continuity.md", lambda t: _cut_blocks(t, cut_from)),
                     ("scenes.md", lambda t: _cut_rows(t, "ch", cut_from)),
                     ("timeline.md", lambda t: _cut_rows(t, "ch", cut_from)),
                     ("threads.md", lambda t: _cut_rows(t, "opened", cut_from))):
        path = os.path.join(state, name)
        if os.path.isfile(path):
            _write(path, fn(mdio.read_text(path)))

    ledger = os.path.join(dest, "plan", "reader-ledger.md")
    if os.path.isfile(ledger):
        _write(ledger, _cut_ledger(mdio.read_text(ledger), cut_from))

    c = room.Chapter(dest_rel, n, root)
    memory = _memory_before(src, n)
    if memory:
        shelf = c.abs("reading/%s/shelf" % c.id)
        os.makedirs(shelf, exist_ok=True)
        shutil.copy(memory, os.path.join(shelf, "notes.md"))
    if role in ("story-editor", "clerk"):
        old = src.abs(src.round_dir(k))
        if os.path.isdir(old):
            shutil.copytree(old, c.abs(c.round_dir(k)))
    return dest_rel, c


def _memory_before(src, n):
    """The reader's notes as the previous chapter's accepted round left them, or None."""
    if n < 2:
        return None
    prev = room.Chapter(src.novel, n - 1, src.root)
    k, _ = room.last_round(prev)
    path = prev.abs(prev.round_dir(k)) + "/notes.md" if k is not None else None
    return path if path and os.path.isfile(path) else None


def role_dispatch(c, k, role, agent=None):
    if role == "continuity-editor":
        d = room.continuity(c, k, warm=False)       # a frozen round replays fresh
    elif role == "planner":
        d = room.planner_beats(c, warm=False)
    elif role == "story-editor":
        d = room.story_editor(c, k, warm=False)     # a frozen round replays fresh
    elif role == "line-editor":
        d = room.line_editor(c, k)
    else:
        d = room.clerk(c, k)
    head, text = d
    m = re.search(r" History: (\S+)\.", text)
    if m and not os.path.isfile(c.abs(m.group(1))):
        text = text.replace(m.group(0), "")     # a run older than the history report (plan 06)
    if agent:
        head = head.replace("@ spawn %s " % role, "@ spawn %s " % agent, 1)
    return head, text


# ---------------------------------------------------------------- arm


ARM_NOTE = "Experiment arm only, never in the loop (tools/bench.py arm). "


def arm(role, name, effort=None, model=None, remove=False, root=ROOT):
    """Write (or remove) the agent file of an experiment's variant of role. Returns its path."""
    if not re.match(r"^[a-z0-9][a-z0-9-]*$", name or ""):
        raise ValueError("an arm's name is lowercase letters, digits and hyphens: %r" % name)
    agents = os.path.join(root, ".claude", "agents")
    path = os.path.join(agents, "%s--%s.md" % (role, name))
    if "%s--%s" % (role, name) in PANEL:
        raise ValueError("%s--%s is the judge panel's, not an experiment's arm" % (role, name))
    if remove:
        if os.path.isfile(path):
            os.remove(path)
        return path
    if not (effort or model):
        raise ValueError("an arm changes effort or model; give --effort or --model")
    text = mdio.read_text(os.path.join(agents, role + ".md"))
    head, sep, body = text[4:].partition("\n---\n")
    if not text.startswith("---\n") or not sep:
        raise ValueError("%s.md has no frontmatter" % role)
    lines = head.split("\n")
    for key, value in (("effort", effort), ("model", model)):
        if value:
            lines = [l for l in lines if not l.startswith(key + ":")] + ["%s: %s" % (key, value)]
    lines = ["name: %s--%s" % (role, name) if l.startswith("name:") else
             l.replace("description: ", "description: " + ARM_NOTE, 1) for l in lines]
    with open(path, "w", encoding="utf-8") as fh:
        fh.write("---\n%s\n---\n%s" % ("\n".join(lines), body))
    return path


# ---------------------------------------------------------------- pair


def _blind_name(root, exp):
    rng = random.SystemRandom()
    while True:
        name = "".join(rng.choice(string.ascii_lowercase) for _ in range(4))
        if not os.path.exists(os.path.join(root, "bench", exp, "blind", name)):
            return name


def pair(exp, name, a, b, root=ROOT):
    """a, b: (label, file). Two folders, X/Y swapped; returns [(folder, x_label, y_label)]."""
    out = []
    for x, y in ((a, b), (b, a)):
        folder = "bench/%s/blind/%s" % (exp, _blind_name(root, exp))
        os.makedirs(os.path.join(root, folder))
        for slot, (label, path) in (("X", x), ("Y", y)):
            export_prose.export([path], os.path.join(root, folder), as_name=slot)
        out.append((folder, x[0], y[0]))
    key = os.path.join(root, "bench", exp, "key.md")
    new = not os.path.isfile(key)
    with open(key, "a", encoding="utf-8") as fh:
        if new:
            fh.write("# Key — %s\n\nThe judges cannot open this file (tools/guard.py).\n\n"
                     "| pair | folder | X | Y | sources |\n|---|---|---|---|---|\n" % exp)
        for folder, xl, yl in out:
            fh.write("| %s | %s | %s | %s | %s=%s, %s=%s |\n"
                     % (name, folder, xl, yl, a[0], os.path.relpath(a[1], root), b[0],
                        os.path.relpath(b[1], root)))
    return out


def judge_dispatch(folder):
    return room.dispatch("spawn", "judge", "Mode 2 — compare. Your folder is %s/. Read X first, "
                         "then Y." % folder, "judge %s" % os.path.basename(folder))


def panel(folder, agents=PANEL, root=ROOT):
    """The mode-1 dispatches for a judge panel on folder; refuses an agent with no agent file."""
    folder = folder.rstrip("/")
    if not os.path.isdir(os.path.join(root, folder)) or "/blind/" not in "/%s/" % folder:
        raise ValueError("%s: want a folder under bench/<experiment>/blind/" % folder)
    for a in agents:
        if not os.path.isfile(os.path.join(root, ".claude", "agents", a + ".md")):
            role, _, name = a.partition("--")
            raise ValueError("no .claude/agents/%s.md; write it with `bench.py arm %s %s --model "
                             "MODEL` and start a new session" % (a, role, name or "?"))
    return [room.dispatch("spawn", a, "Mode 1 — read. Your folder is %s/." % folder,
                          "judge read %d (%s)" % (i, a)) for i, a in enumerate(agents, 1)]


# ---------------------------------------------------------------- agree


def _norm(text):
    return re.sub(r"[^a-z0-9' ]+", " ", text.lower().replace("’", "'")).split()


def same_passage(q1, q2, n=MATCH_WORDS):
    """True if two quotes share a run of n words (or one short quote is inside the other)."""
    a, b = _norm(q1), _norm(q2)
    if not a or not b:
        return False
    need = min(n, len(a), len(b))
    sm = difflib.SequenceMatcher(None, a, b, autojunk=False)
    return max(blk.size for blk in sm.get_matching_blocks()) >= need


def note_items(text):
    """[(id, headline, [quotes on its where line])] from a notes file."""
    items, cur = [], None
    for line in wire.sections(text).get("Notes", []):
        s = line.strip()
        if wire.NOTE_HEAD.match(s):
            cur = [s.split()[0], s.split(" ", 1)[1] if " " in s else "", []]
            items.append(cur)
        elif cur is not None and s.startswith("where"):
            cur[2] += wire.QUOTE.findall(s)
    return [tuple(i) for i in items]


def finding_items(text):
    """[(id, kind, [quotes from the draft])] from a continuity file."""
    out = []
    for line in text.splitlines():
        m = wire.FINDING.match(line.strip())
        if m:
            first = m.group(3).split(" | ")[0]
            out.append(("F" + m.group(1), m.group(2), wire.QUOTE.findall(first) or [first]))
    return out


def match(xs, ys):
    """Greedy one-to-one pairing of items whose quotes are the same passage."""
    pairs, used = [], set()
    for x in xs:
        for j, y in enumerate(ys):
            if j not in used and any(same_passage(a, b) for a in x[2] for b in y[2]):
                pairs.append((x, y))
                used.add(j)
                break
    only_x = [x for x in xs if x not in [p[0] for p in pairs]]
    only_y = [y for j, y in enumerate(ys) if j not in used]
    return pairs, only_x, only_y


def agree_notes(a, b):
    ta, tb = mdio.read_text(a), mdio.read_text(b)
    va, vb = header(a)[0], header(b)[0]
    pairs, oa, ob = match(note_items(ta), note_items(tb))
    lines = ["verdict  %s · %s · %s" % (va, vb, "same" if va == vb else "DIFFERENT")]
    lines += _matched(pairs, oa, ob, lambda i: "%s %s" % (i[0], i[1]))
    return "\n".join(lines)


def agree_continuity(a, b, catches=()):
    fa, fb = finding_items(mdio.read_text(a)), finding_items(mdio.read_text(b))
    pairs, oa, ob = match(fa, fb)
    lines = _matched(pairs, oa, ob, lambda i: "%s %s \"%s\"" % (i[0], i[1], i[2][0][:60]))
    for q in catches:
        hit = lambda fs: next((f[0] for f in fs if any(same_passage(q, x) for x in f[2])), "-")
        lines.append("catch    \"%s\" · A %s · B %s" % (q[:60], hit(fa), hit(fb)))
    return "\n".join(lines)


def _matched(pairs, oa, ob, show):
    total = len(pairs) + len(oa) + len(ob)
    lines = ["matched  %d of %d (A %d, B %d)" % (len(pairs), total, len(pairs) + len(oa),
                                                  len(pairs) + len(ob))]
    lines += ["both     %s = %s" % (show(x)[:70], show(y)[:70]) for x, y in pairs]
    lines += ["A only   %s" % show(x)[:100] for x in oa]
    lines += ["B only   %s" % show(y)[:100] for y in ob]
    return lines


# ---------------------------------------------------------------- main


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("rounds")
    p.add_argument("novel")
    p = sub.add_parser("freeze")
    for name in ("novel", "n", "k", "exp", "arm"):
        p.add_argument(name, type=int if name in ("n", "k") else str)
    p.add_argument("--role", required=True, choices=ROLES)
    p.add_argument("--agent", help="the agent type to dispatch, e.g. story-editor--medium")
    p = sub.add_parser("arm")
    p.add_argument("role", choices=ARM_ROLES)
    p.add_argument("arm")
    p.add_argument("--effort", choices=("low", "medium", "high", "xhigh", "max"))
    p.add_argument("--model")
    p.add_argument("--remove", action="store_true")
    p = sub.add_parser("pair")
    p.add_argument("exp")
    p.add_argument("name")
    p.add_argument("a")
    p.add_argument("b")
    p = sub.add_parser("panel")
    p.add_argument("folder")
    p.add_argument("--agents", help="comma-separated agent types (default: %s)" % ",".join(PANEL))
    p = sub.add_parser("agree")
    p.add_argument("kind", choices=("notes", "continuity"))
    p.add_argument("a")
    p.add_argument("b")
    p.add_argument("--catch", action="append", default=[])
    ap.add_argument("--root", default=ROOT, help=argparse.SUPPRESS)
    args = ap.parse_args(argv)
    try:
        if args.cmd == "rounds":
            print(rounds(args.novel))
        elif args.cmd == "freeze":
            dest, c = freeze(args.novel, args.n, args.k, args.exp, args.arm, args.role, args.root)
            print("frozen   %s (chapter %d, round %d, for the %s)" % (dest, args.n, args.k,
                                                                    args.role))
            print(room.render([], [role_dispatch(c, args.k, args.role, args.agent)]).lstrip())
        elif args.cmd == "arm":
            path = arm(args.role, args.arm, args.effort, args.model, args.remove, args.root)
            print("%s   %s%s" % ("removed" if args.remove else "written", os.path.relpath(path,
                  args.root), "" if args.remove else " (registers at the next session start)"))
        elif args.cmd == "pair":
            sides = []
            for spec in (args.a, args.b):
                label, _, path = spec.partition("=")
                if not path or not os.path.isfile(path):
                    raise ValueError("%r: want LABEL=FILE, with the file on disk" % spec)
                sides.append((label, os.path.abspath(path)))
            folders = pair(args.exp, args.name, sides[0], sides[1], args.root)
            print(room.render(["key      bench/%s/key.md" % args.exp],
                              [judge_dispatch(f) for f, _, _ in folders]))
        elif args.cmd == "panel":
            agents = tuple(a.strip() for a in args.agents.split(",")) if args.agents else PANEL
            print(room.render([], panel(args.folder, agents, args.root)).lstrip())
        elif args.kind == "notes":
            print(agree_notes(args.a, args.b))
        else:
            print(agree_continuity(args.a, args.b, args.catch))
    except (ValueError, OSError, room.Stop) as e:
        print("bench.py: %s" % e, file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
