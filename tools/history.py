#!/usr/bin/env python3
"""The book across chapters: what no check of one chapter can see, as findings for a critic.

Four detectors, ported from skilled-writer's `cmd_history.py` and tuned on runs #5 to #7, where
readers and judges named each pattern:

  * **motif** - a phrase or image that recurs whole across chapters: "Old ones hold their shape"
    four times in five chapters, all three of run #7's judges named it. Every use is counted, so a
    callback can be weighed against how often it has already come back. A phrase the bible also
    holds is marked: it travelled from a bible line into the prose. Owner: the line editor.
  * **signature** - a three-to-five-word phrase with no name or lexicon word in it, used across
    chapters or in several mouths: the author's tic rather than a character's. Owner: the line
    editor.
  * **two-hander** - the share of recent conversations carried by two named speakers or fewer,
    and the longest run of them in a row. Owner: the story editor.
  * **tempo** - from `state/scenes.md`: runs of one tempo across scenes, chapters, openings and
    endings; and from `plan/chapters.md`, runs of one planned `temp`. Owner: the story editor.

Findings print as `level check: detail` under the role that owns them. `warn` is a run past the
shape a reader named; `note` is a count to read. Nothing here gates: the exit status is 0 whatever
it finds, unless the novel cannot be found. Fewer than three chapters have no shape to report.

Usage:
  history.py NOVEL_DIR [--draft FILE] [--chapter N] [--upto N] [--out FILE] [--json]

--draft adds a chapter in progress as chapter N (the one after the last accepted chapter, or
--chapter), so a round's critics see the book with this draft in it. --upto stops at chapter N.
"""
import argparse
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from lib import mdio  # noqa: E402
from lib.novel import resolve  # noqa: E402
from lib.textstats import Chapter  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MIN_CHAPTERS = 3
WINDOW = 5                  # chapters looked back over for scene shape and tempo
TALK_TURNS = 4              # a scene with fewer spoken turns is not a conversation
TALK_MIN = 6                # conversations needed before a share is a shape (runs #5, #6: 8-9)
TALK_SHARE = 0.7            # run #5 read 7 of 9, run #6 6 of 8; both readers named it
TALK_RUN = 3                # two-handers in a row: the knowledge base's own example
TEMPO_SCENES = 4            # scenes in a row at one tempo
TEMPO_CHAPTERS = 3          # chapters in a row with one main tempo, one opening, one ending, one temp
MOTIF_N = 4                 # words in the window a motif is found by
MOTIF_GAP = 12              # words between two pieces of one use: a clause put in the middle
MOTIF_USES = 3              # a motif is used this often, in two chapters or more
MOTIF_WARN = (3, 4)         # chapters and uses at which a motif is a warn: both of run #7's judged
                            # refrains sat at 3 chapters and 4 uses
SHOWN = 8                   # notes of one check shown before "+n more"
LEVELS = ("warn", "note")
OWNERS = (("line editor", ("motif", "signature")),
          ("story editor", ("two-hander", "tempo", "temp")))

# Words too common to make a phrase anybody's. A phrase needs content words to be a signature.
COMMON = frozenset(
    "a an the of to in on at by for with and or but not no nor is was were be been being it its "
    "his her hers their he she they i you we us that this these those there then than as so if "
    "when what which who whom whose from into out up down over under about after before just "
    "only very too also had has have do did does would could should will can may might must one "
    "him them me my your our said says say that's it's he'd she'd i'm don't didn't wasn't isn't "
    "s t d ll re ve m".split())
# Words that carry no image of their own: a motif needs two words outside COMMON and these.
MOTIF_STOP = frozenset(
    "own back went go goes going gone come came took take put get got still like every other again "
    "around through away off onto toward towards across against behind beside between while until "
    "where here now once ever never more most some any all each both way turned looked look made "
    "make knew know thought two three first last long time day days year years thing things "
    "nothing something anything left right hand hands".split())
SENTENCE_END = set(".!?\"'“”‘’—:\n")
WORD = re.compile(r"[A-Za-z][A-Za-z']*")


class Report(object):
    def __init__(self):
        self.items = []         # (level, check, detail)

    def add(self, level, check, detail):
        self.items.append((level, check, detail))

    def lines(self, title):
        out = [title]
        for owner, checks in OWNERS:
            mine = [i for i in self.items if i[1] in checks]
            if not mine:
                continue
            out.append("")
            out.append("## for the %s" % owner)
            mine.sort(key=lambda i: (LEVELS.index(i[0]), checks.index(i[1])))
            out.extend("%s %s: %s" % i for i in mine)
        counts = dict((lv, sum(1 for i in self.items if i[0] == lv)) for lv in LEVELS)
        out.append("")
        out.append("%d warn · %d note - findings to weigh, not gates" % (counts["warn"],
                                                                        counts["note"]))
        return out


def runs(numbers):
    """[1,2,3,7,9,10] -> '1-3, 7, 9-10'."""
    nums = sorted(set(numbers))
    if not nums:
        return "-"
    out, start, prev = [], nums[0], nums[0]
    for n in nums[1:]:
        if n == prev + 1:
            prev = n
            continue
        out.append(str(start) if start == prev else "%d-%d" % (start, prev))
        start = prev = n
    out.append(str(start) if start == prev else "%d-%d" % (start, prev))
    return ", ".join(out)


def where(chapters):
    """[1, 1, 3, 5] -> 'ch 1 (2), 3, 5'."""
    counts = {}
    for c in chapters:
        counts[c] = counts.get(c, 0) + 1
    return "ch " + ", ".join("%d (%d)" % (c, n) if n > 1 else str(c)
                             for c, n in sorted(counts.items()))


def longest_run(seq):
    """(value, start index, length) of the longest run of equal, non-empty values in seq."""
    best, i = (None, 0, 0), 0
    while i < len(seq):
        j = i
        while j + 1 < len(seq) and seq[j + 1] == seq[i]:
            j += 1
        if seq[i] and j - i + 1 > best[2]:
            best = (seq[i], i, j - i + 1)
        i = j + 1
    return best


# ------------------------------------------------------------------ the book


def setting_words(nov):
    """Lower-case words of the lexicon's names and terms: a world term recurs because the world
    does, so a phrase holding one is setting, not voice."""
    out = set()
    for term in nov.lexicon_terms():
        out.update(w.lower() for w in re.findall(r"[A-Za-z']{3,}", term))
    return out


def tokens(ch):
    """(word, proper, spoken, offset) for every word in a chapter's body."""
    body = ch.body.replace("’", "'")
    ranges = ch.speech_ranges
    out = []
    for m in WORD.finditer(body):
        word = m.group(0)
        before = body[:m.start()].rstrip()[-1:]
        proper = word[:1].isupper() and bool(before) and before not in SENTENCE_END
        spoken = any(s <= m.start() < e for s, e in ranges)
        out.append((word.lower().strip("'"), proper, spoken, m.start()))
    return out


def book(nov, draft=None, number=None, upto=None):
    """The chapters in order, up to `upto`; a draft stands in for its chapter number, by default
    the one after the last chapter kept."""
    chapters = [c for c in nov.chapters()
                if c.number is not None and (not upto or c.number <= upto)]
    if draft:
        ch = Chapter(draft, channels=nov.channels)
        n = number or ((max([c.number for c in chapters]) + 1) if chapters else 1)
        ch.meta["number"] = n
        chapters = [c for c in chapters if c.number != n] + [ch]
    return sorted(chapters, key=lambda c: c.number)


# ------------------------------------------------------------------ motif


def bible_text(nov):
    """(path, line number, lower-cased words) for every line of the bible."""
    out = []
    base = nov.path("bible")
    for dirpath, _dirs, files in os.walk(base):
        for fn in sorted(files):
            if not fn.endswith(".md"):
                continue
            path = os.path.join(dirpath, fn)
            for i, line in enumerate(mdio.read_text(path).split("\n"), 1):
                words = [w.lower().strip("'") for w in WORD.findall(line.replace("’", "'"))]
                if len(words) >= MOTIF_N:
                    out.append((os.path.relpath(path, nov.root), i, words))
    return out


def motifs(chapters, setting, bible=()):
    """([(text, [chapter per use], bible source)], covered): phrases that come back whole, and the
    (chapter, word index) of every word inside one of their uses.

    Every MOTIF_N-word window used in two chapters or more is a seed. Seeds that overlap at any one
    place belong to one motif, so a long refrain and a shortened echo of it count as one thing
    used several times. A motif needs two words that are neither common nor setting, so "the
    Survey Office long room" is a place and not a refrain.
    """
    seen = {}               # window -> [(chapter index, token index)]
    toks = [tokens(c) for c in chapters]
    for ci, ts in enumerate(toks):
        for i in range(len(ts) - MOTIF_N + 1):
            key = tuple(t[0] for t in ts[i:i + MOTIF_N])
            seen.setdefault(key, []).append((ci, i))
    seeds = {}
    for key, places in seen.items():
        if len(set(ci for ci, _ in places)) < 2:
            continue
        content = [w for w in key if w not in COMMON and w not in MOTIF_STOP
                   and w not in setting]
        if len(content) < 2:
            continue
        seeds[key] = places
    # Union the seeds that overlap at any place, then merge each motif's places into uses.
    parent = dict((k, k) for k in seeds)

    def find(k):
        while parent[k] != k:
            parent[k] = parent[parent[k]]
            k = parent[k]
        return k

    owner = {}
    for key, places in seeds.items():
        for ci, i in places:
            for j in range(i, i + MOTIF_N):
                other = owner.setdefault((ci, j), key)
                if other != key:
                    parent[find(key)] = find(other)
    groups = {}
    for key, places in seeds.items():
        groups.setdefault(find(key), set()).update(places)
    out, covered = [], set()
    for places in groups.values():
        uses = []           # [chapter index, first token, last token]
        for ci, i in sorted(places):
            # A clause put in the middle ("the clearers' foreman had told his horse, outside the
            # Dennets' gate") leaves one use.
            if uses and uses[-1][0] == ci and i <= uses[-1][2] + MOTIF_GAP:
                uses[-1][2] = max(uses[-1][2], i + MOTIF_N - 1)
            else:
                uses.append([ci, i, i + MOTIF_N - 1])
        if len(uses) < MOTIF_USES or len(set(u[0] for u in uses)) < 2:
            continue
        extend(uses, toks)
        for u in uses:
            covered.update((chapters[u[0]].number, j) for j in range(u[1], u[2] + 1))
        ci, a, b = max(uses, key=lambda u: u[2] - u[1])
        body = chapters[ci].body
        text = re.sub(r"\s+", " ", body[toks[ci][a][3]:toks[ci][b][3] + len(toks[ci][b][0])])
        words = [t[0] for t in toks[ci][a:b + 1]]
        source = ""
        grams = set(tuple(words[k:k + MOTIF_N]) for k in range(len(words) - MOTIF_N + 1))
        for path, line, bwords in bible:
            if any(tuple(bwords[k:k + MOTIF_N]) in grams
                   for k in range(len(bwords) - MOTIF_N + 1)):
                source = "%s:%d" % (path, line)
                break
        out.append((text, [chapters[u[0]].number for u in uses], source))
    out.sort(key=lambda m: (-len(m[1]), -len(set(m[1])), m[0]))
    return out, covered


def extend(uses, toks):
    """Grow each use, word by word, while another use goes on with the same word: a refrain's
    tail ("you'd never know. Then they go all at once") has no seed of its own, being all common
    words, and is still the refrain."""
    for step in (1, -1):
        for u in uses:
            k = 1
            while True:
                at = (u[2] if step > 0 else u[1]) + step * k
                if not 0 <= at < len(toks[u[0]]):
                    break
                word = toks[u[0]][at][0]
                if not any(v is not u and 0 <= (v[2] if step > 0 else v[1]) + step * k
                           < len(toks[v[0]])
                           and toks[v[0]][(v[2] if step > 0 else v[1]) + step * k][0] == word
                           for v in uses):
                    break
                k += 1
            if step > 0:
                u[2] += k - 1
            else:
                u[1] -= k - 1


def check_motifs(chapters, rep, setting, bible):
    found, covered = motifs(chapters, setting, bible)
    notes = 0
    for text, chs, source in found:
        warn = len(set(chs)) >= MOTIF_WARN[0] and len(chs) >= MOTIF_WARN[1]
        if not warn:
            notes += 1
            if notes > SHOWN:
                continue
        shown = text if len(text) <= 90 else text[:89].rstrip() + "…"
        rep.add("warn" if warn else "note", "motif", "\"%s\" x%d in %s%s" % (
            shown, len(chs), where(chs), (" - also in %s" % source) if source else ""))
    if notes > SHOWN:
        rep.add("note", "motif", "+%d more, in fewer chapters" % (notes - SHOWN))
    return found, covered


# --------------------------------------------------------------- signature


def signatures(chapters, setting, covered=()):
    """[(phrase, chapters, uses, spoken only)] - ported whole from skilled-writer.

    Two ways to qualify, both on 3-5 word phrases with no proper noun and no lexicon word in them,
    and never a three-word phrase that opens on an article. Either two or more content words, used
    in three chapters or three times across two; or spoken only, across two chapters, three times
    (four when a single content word carries it, as run #5's "not an answer" did). A use inside
    a motif's use is the motif's, and is not counted here.
    """
    uses = {}
    for ch in chapters:
        toks = tokens(ch)
        for n in (3, 4, 5):
            for i in range(len(toks) - n + 1):
                gram = toks[i:i + n]
                if any(t[1] for t in gram):
                    continue
                words = tuple(t[0] for t in gram)
                if n == 3 and words[0] in ("the", "a", "an"):
                    continue
                if setting.intersection(words):
                    continue
                if not any(w not in COMMON for w in words):
                    continue
                if (ch.number, i) in covered:
                    continue
                uses.setdefault(words, []).append((ch.number, gram[0][2]))
    hits = []
    for words, places in uses.items():
        chs = sorted(set(c for c, _s in places))
        content = sum(1 for w in words if w not in COMMON)
        spoken_only = all(s for _c, s in places)
        wide = content >= 2 and (len(chs) >= 3 or (len(chs) >= 2 and len(places) >= 3))
        mouths = spoken_only and len(chs) >= 2 and len(places) >= (3 if content >= 2 else 4)
        if wide or mouths:
            hits.append((" ".join(words), chs, len(places), spoken_only))
    # A shorter phrase inside a longer hit over the same chapters is the same tic.
    hits.sort(key=lambda h: -len(h[0]))
    kept = []
    for h in hits:
        if any(h[0] in k[0] and set(h[1]) <= set(k[1]) for k in kept):
            continue
        kept.append(h)
    kept.sort(key=lambda h: (not h[3], -len(h[0].split()), -len(h[1]), -h[2], h[0]))
    return kept


def check_signatures(chapters, rep, setting, covered):
    kept = signatures(chapters, setting, covered)
    for phrase, chs, n, spoken in kept[:SHOWN]:
        rep.add("note", "signature", "\"%s\" x%d in ch %s%s" % (
            phrase, n, ", ".join(str(c) for c in chs), " (spoken only)" if spoken else ""))
    if len(kept) > SHOWN:
        rep.add("note", "signature", "+%d more, rarer" % (len(kept) - SHOWN))
    return kept


# -------------------------------------------------------------- two-hander


def conversations(chapters, names):
    """[(chapter, scene, speakers)] for every scene with TALK_TURNS spoken turns or more."""
    out = []
    for ch in chapters:
        who = ch.scene_speakers(list(names))
        for s, (turns, speakers) in enumerate(zip(ch.scene_turns(), who), 1):
            if turns >= TALK_TURNS:
                out.append((ch.number, s, speakers))
    return out


def check_two_handers(chapters, rep, names):
    recent = chapters[-WINDOW:]
    talk = conversations(recent, names)
    if not talk:
        return []
    pairs = [(c, s) for c, s, who in talk if len(who) <= 2]
    span = "ch %d-%d" % (recent[0].number, recent[-1].number)
    share = len(pairs) / float(len(talk))
    level = "warn" if len(talk) >= TALK_MIN and share >= TALK_SHARE else "note"
    rep.add(level, "two-hander", "%d of %d conversations in %s have at most two named speakers "
            "(a floor: a turn with no name beside it counts nobody)%s"
            % (len(pairs), len(talk), span,
               (": " + ", ".join("c%d s%d" % p for p in pairs)) if pairs else ""))
    flags = [len(who) <= 2 for _c, _s, who in talk]
    _v, start, length = longest_run(flags)
    if length >= TALK_RUN:
        a, b = talk[start], talk[start + length - 1]
        rep.add("warn", "two-hander", "%d two-handers in a row, c%d s%d to c%d s%d"
                % (length, a[0], a[1], b[0], b[1]))
    return talk


# ------------------------------------------------------------------- tempo


def check_tempo(nov, chapters, rep):
    numbers = [c.number for c in chapters][-WINDOW:]
    rows = [r for r in nov.scenes() if str(r.get("ch")).strip().isdigit()
            and int(r.get("ch")) in numbers]
    by_ch = {}
    for r in rows:
        tempo = r.get("tempo").strip().lower()
        by_ch.setdefault(int(r.get("ch")), []).append(tempo)
    logged = [n for n in numbers if n in by_ch]
    if logged:
        flat = [(n, t) for n in logged for t in by_ch[n]]
        tally = {}
        for _n, t in flat:
            tally[t] = tally.get(t, 0) + 1
        rep.add("note", "tempo", "scenes in ch %s: %s" % (runs(logged), ", ".join(
            "%s %d" % kv for kv in sorted(tally.items(), key=lambda kv: (-kv[1], kv[0])))))
        value, start, length = longest_run([t for _n, t in flat])
        if length >= TEMPO_SCENES:
            rep.add("warn", "tempo", "%d scenes in a row at %s, ch %d to ch %d"
                    % (length, value, flat[start][0], flat[start + length - 1][0]))
        main = []
        for n in logged:
            counts = {}
            for t in by_ch[n]:
                counts[t] = counts.get(t, 0) + 1
            top = sorted(counts.items(), key=lambda kv: -kv[1])
            main.append(top[0][0] if len(top) == 1 or top[0][1] > top[1][1] else "")
        for label, seq in (("mostly", main), ("open", [by_ch[n][0] for n in logged]),
                           ("end", [by_ch[n][-1] for n in logged])):
            value, start, length = longest_run(seq)
            if length >= TEMPO_CHAPTERS:
                rep.add("warn", "tempo", "%d chapters in a row %s %s: ch %d-%d" % (
                    length, label, value, logged[start], logged[start + length - 1]))
    planned = []
    for n in numbers:
        row = nov.plan_row(n)
        planned.append(row.get("temp").strip().lower() if row else "")
    value, start, length = longest_run(planned)
    if length >= TEMPO_CHAPTERS:
        rep.add("warn", "temp", "the plan sets %d chapters in a row at %s: ch %d-%d"
                % (length, value, numbers[start], numbers[start + length - 1]))
    for n, temp in zip(numbers, planned):
        if temp and n in by_ch and temp not in by_ch[n]:
            rep.add("note", "temp", "ch %d was planned %s and played %s"
                    % (n, temp, ", ".join(by_ch[n])))
    return by_ch


# --------------------------------------------------------------------- run


def history(nov, draft=None, number=None, upto=None):
    """(Report, data) for the book as it stands."""
    rep = Report()
    chapters = book(nov, draft, number, upto)
    data = {"novel": nov.slug, "chapters": [c.number for c in chapters],
            "draft": next((c.number for c in chapters if draft and c.path == draft), None)}
    if len(chapters) < MIN_CHAPTERS:
        return rep, data
    setting = setting_words(nov)
    found, covered = check_motifs(chapters, rep, setting, bible_text(nov))
    data["motifs"] = [{"text": t, "chapters": c, "bible": s} for t, c, s in found]
    sigs = check_signatures(chapters, rep, setting, covered)
    data["signatures"] = [{"phrase": p, "chapters": c, "uses": n, "spoken": s}
                          for p, c, n, s in sigs]
    talk = check_two_handers(chapters, rep, nov.speakers())
    data["conversations"] = [{"ch": c, "scene": s, "speakers": sorted(w)} for c, s, w in talk]
    data["tempo"] = check_tempo(nov, chapters, rep)
    data["findings"] = [{"level": lv, "check": c, "detail": d} for lv, c, d in rep.items]
    return rep, data


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("novel")
    ap.add_argument("--draft", help="a chapter in progress, counted as chapter N")
    ap.add_argument("--chapter", type=int, help="the draft's chapter number")
    ap.add_argument("--upto", type=int, help="leave out chapters after N")
    ap.add_argument("--out", help="also write the report to this file")
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args(argv)
    nov = resolve(args.novel, ROOT)
    if nov is None:
        sys.stderr.write("history: no novel at %s\n" % args.novel)
        return 1
    if args.draft and not os.path.isfile(args.draft):
        sys.stderr.write("history: no such draft: %s\n" % args.draft)
        return 1
    rep, data = history(nov, args.draft, args.chapter, args.upto)
    chs = data["chapters"]
    if args.json:
        text = json.dumps(data, indent=1)
    elif len(chs) < MIN_CHAPTERS:
        text = "history %s: %d chapter(s) - nothing across chapters to report before ch %d" % (
            nov.slug, len(chs), MIN_CHAPTERS)
    else:
        drafted = data.get("draft")
        text = "\n".join(rep.lines("history %s - ch %s%s" % (
            nov.slug, runs(chs), (" (ch %d is the draft)" % drafted) if drafted else "")))
    sys.stdout.write(text + "\n")
    if args.out:
        os.makedirs(os.path.dirname(os.path.abspath(args.out)), exist_ok=True)
        with open(args.out, "w", encoding="utf-8") as fh:
            fh.write(text + "\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
