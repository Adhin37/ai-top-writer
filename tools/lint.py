#!/usr/bin/env python3
"""A mechanical sweep over one chapter's prose, as a report a critic reads.

Per-chapter checks only: the frontmatter, the four channels (thought marks, thought tags, meta
blocks, markup, scene breaks), house-style sentence shapes and stock phrases, phrases the chapter
repeats, number forms, spellings against the lexicon, and EQ-Bench's slop index as a reference
figure (`lib/slop.py`). What recurs *across* chapters is the line
editor's reading and, later, plan 06's detectors.

Findings print as `level check: detail`, where level is `defect` (the file's format is broken, or
the lexicon forbids a spelling), `warn` (probably wrong; look) or `note` (a count or a place to
look). There are no budgets and no thresholds: nothing here decides whether a chapter ships. The
exit status is 0 whatever it finds, unless a file cannot be read.

Usage:
  lint.py CHAPTER [CHAPTER ...] [--novel DIR] [--out FILE] [--stats]

CHAPTER is a chapter or draft file. The novel (for channels, lexicon and cast) is found from the
file's path, or given with --novel. --out also writes the report to FILE. --stats prints only the
measurements: words, speech share, scenes and who speaks in each.
"""
import argparse
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from lib import novel as novel_mod  # noqa: E402
from lib import slop  # noqa: E402
from lib.textstats import Chapter, DEFAULT_CHANNELS  # noqa: E402

LEVELS = ("defect", "warn", "note")
CHAPTER_FIELDS = ("number", "title", "pov", "words")
BREAK_LINE = re.compile(r"^[ \t]*[*\-_~=·•][ \t*\-_~=·•]*$", re.M)
WELL_FORMED_BREAK = "* * *"


def _rx(pairs, flags=re.I):
    return [(re.compile(p, flags), label) for p, label in pairs]


# Markup: nothing but the four channels belongs in a prose body.
MARKUP = _rx([
    (r"^\s{0,3}#{1,6}\s", "a markdown heading"),
    (r"^\s{0,3}[-+]\s+\S", "a list bullet"),
    (r"^\s{0,3}\*\s+\S(?!.*\*\s*$)", "a list bullet"),
    (r"^\s{0,3}\d+\.\s+\S", "a numbered list"),
    (r"\*\*[^*\n]+\*\*", "bold"),
    (r"(?<!\*)\*(?!\s)[^*\n]+(?<!\s)\*(?!\*)", "italics"),
    (r"(?<![\w_])_(?!\s)[^_\n]+(?<!\s)_(?![\w_])", "italics"),
    (r"\[[^\]\n]*\]\([^)\n]*\)", "a markdown link"),
    (r"^\s{0,3}>\s", "a blockquote"),
    (r"^\s{0,3}```", "a code fence"),
])

# A direct thought tagged with a thinking verb: the marks already say whose thought it is.
THOUGHT_TAG_AFTER = re.compile(
    r"^\s*,?\s*(?:he|she|they|I|we|[A-Z][a-z]+)\s+(?:thought|wondered|told (?:himself|herself|"
    r"themselves|myself))\b")
THOUGHT_TAG_BEFORE = re.compile(
    r"\b(?:thought|wondered|told (?:himself|herself|themselves|myself))[,:]?\s*$")
# Thought marks around narration: no speaker in it, in the narrator's past tense.
FIRST_SECOND_PERSON = re.compile(
    r"\b(?:i|me|my|mine|myself|we|us|our|ours|you|your|yours)\b|\b(?:i|we|you)['’]"
    r"(?:m|re|ve|ll|d)\b", re.I)
PRESENT = re.compile(r"\b(?:is|are|am|has|have|do|does|can|shall|will)\b|['’](?:s|re|m|ve|"
                     r"ll)\b", re.I)
PAST = re.compile(r"\b(?:was|were|had|been|did|would|could|should)\b|['’]d\b", re.I)

# Sentence shapes that are good once and a narrator's single setting at density. Narration only:
# a character may talk in antitheses as a fingerprint.
_FRAGMENT_NEGATION = (
    r"(?:^|(?<=[.!?])|(?<=\n\n))[\"“”\s]*(?:Not|No)\b"
    r"(?![^.!?\n]*\b(?:is|are|was|were|am|be|been|being|has|have|had|do|does|did|will|"
    r"would|can|could|shall|should|may|might|must)\b)"
    r"(?:\s+[\w'’-]+){0,5}\s*[.!?]")
HOUSE_STYLE = _rx([
    (r",\s+which was\s+(?:exactly\b|its own\b|not (?:an?|the)\b)", "`, which was X` closer"),
    (r"\bits own kind of\b", "`its own kind of X`"),
    (r",\s+not\s+(?!to\b|be\b|have\b|only\b|just\b|yet\b)\w+", "`X, not Y` antithesis"),
    (r",\s+never\s+(?:a|an|the)\b", "`X, never a Y` antithesis"),
    (_FRAGMENT_NEGATION, "`Not X.` fragment"),
    (r"\bA (?:beat|pause)\.", "`A beat.` stage direction"),
    (r"\bthe kind of \w+ (?:that|who|a|an|you|one|people)\b", "`the kind of X that`"),
    (r"\bnot (?:because|out of|from)\b[^.;]{2,40}\bbut (?:because|out of|from)\b",
     "`not because X but because Y`"),
    (r"\bsomething (?:in|about) (?:his|her|their|the) (?:face|eyes|voice|expression)\b",
     "`something in her face`"),
    (r"\b(?:turning|holding|carrying|weighing|folding)\b[^.]{0,40}\b(?:years?|arithmetic|"
     r"silence|grief|doubt|history|guilt|memory)\b[^.]{0,25}\bin (?:his|her|their) hands\b",
     "an abstract noun held as an object"),
])
# Stock phrases: cut on sight, anywhere.
STOCK = _rx([
    (r"\ba testament to\b", "a testament to"),
    (r"\bsomething shifted\b", "something shifted"),
    (r"\bthe weight of .{1,30} settled\b", "the weight of X settled"),
    (r"\ba moment that stretched\b", "a moment that stretched"),
    (r"\bcould ?n[o'’]t shake the feeling\b", "couldn't shake the feeling"),
    (r"\blittle did (?:he|she|they|we|i) know\b", "little did X know"),
    (r"\bfor the first time in a long time\b", "for the first time in a long time"),
    (r"\b(?:a )?silence stretched between\b", "a silence stretched between them"),
    (r"\bair was thick with tension\b", "the air was thick with tension"),
    (r"\bchill ran down (?:his|her|their|the)\b", "a chill ran down"),
    (r"\btime seemed to slow\b", "time seemed to slow"),
    (r"\bbreath (?:he|she|they|i) did ?n[o'’]t know\b", "a breath X didn't know"),
    (r"\bthis changes everything\b", "this changes everything"),
    (r"\bexpressions? changed drastically\b", "expression changed drastically"),
    (r"\bin the next (?:instant|moment)\b", "in the next instant"),
])

NUMBER_WORDS = ("one two three four five six seven eight nine ten eleven twelve thirteen "
                "fourteen fifteen sixteen seventeen eighteen nineteen twenty thirty forty fifty "
                "sixty seventy eighty ninety hundred thousand").split()
NUMBER_WORD_RE = r"(?:%s)(?:-(?:%s))?" % ("|".join(NUMBER_WORDS), "|".join(NUMBER_WORDS[:9]))
NUMBER_UNIT = re.compile(r"\b(\d+(?:,\d{3})*|%s)\s+([a-z]+)\b" % NUMBER_WORD_RE, re.I)
SMALL = 20                      # the usual line between spelled-out and digit numbers
NOT_UNITS = {"of", "and", "or", "to", "the", "a", "in", "on", "at", "for", "more", "times",
             "was", "were", "had", "his", "her", "their", "its", "who", "that", "than"}

ECHO_WINDOW = 4
ECHO_MIN = 3


def _clip(text, n=70):
    text = re.sub(r"\s+", " ", text).strip()
    return text if len(text) <= n else text[:n - 1].rstrip() + "…"


class Report(object):
    def __init__(self):
        self.found = []           # (level, check, line or None, detail)

    def add(self, level, check, detail, line=None):
        self.found.append((level, check, line, detail))

    def lines(self):
        order = {lv: i for i, lv in enumerate(LEVELS)}
        out = []
        for level, check, line, detail in sorted(
                self.found, key=lambda f: (order[f[0]], f[1], f[2] or 0)):
            where = "line %d " % line if line else ""
            out.append("%s %s: %s%s" % (level, check, where, detail))
        counts = " · ".join("%d %s" % (sum(1 for f in self.found if f[0] == lv), lv)
                            for lv in LEVELS)
        return out + [counts]


# ------------------------------------------------------------------- the checks


def check_frontmatter(ch, rep):
    if not ch.frontmatter_text:
        rep.add("defect", "frontmatter", "none; a chapter file opens with number, title, pov")
        return
    for key in ("number", "title", "pov"):
        if ch.meta.get(key) in (None, ""):
            rep.add("defect", "frontmatter", "`%s` missing" % key, 1)
    extra = [k for k in ch.meta if k not in CHAPTER_FIELDS]
    if extra:
        rep.add("warn", "frontmatter", "%s: anything in a chapter file can reach a reader; intent "
                "lives in the beat sheet" % ", ".join("`%s`" % k for k in extra), 1)
    recorded = ch.meta.get("words")
    if isinstance(recorded, int) and recorded != ch.words:
        rep.add("warn", "frontmatter", "`words: %d`, the body measures %d" % (recorded, ch.words),
                1)
    m = re.match(r"^(\d+)", ch.name)
    num = ch.meta.get("number")
    if m and isinstance(num, int) and int(m.group(1)) != num:
        rep.add("defect", "frontmatter", "`number: %d` but the file name says %s"
                % (num, m.group(1)), 1)


def check_channels(ch, rep, interiority=""):
    outside = ch.outside_speech
    thoughts = ch.thoughts()
    if thoughts:
        rep.add("note", "thoughts", "%d direct thought(s), lines %s" % (
            len(thoughts), ", ".join(str(ch.line_of(t.start())) for t in thoughts)))
    elif str(interiority).lower() not in ("", "low"):
        rep.add("note", "thoughts", "no direct thoughts; narration.interiority is `%s`"
                % interiority)
    for t in thoughts:
        tail = outside[t.end():t.end() + 40]
        head = outside[max(0, t.start() - 30):t.start()]
        if THOUGHT_TAG_AFTER.match(tail) or THOUGHT_TAG_BEFORE.search(head):
            rep.add("warn", "thought-tag", "a direct thought tagged with a thinking verb; the "
                    "marks already attribute it: %s" % _clip(t.group(0) + tail), ch.line_of(t.start()))
        inner = t.group(1)
        if not (FIRST_SECOND_PERSON.search(inner) or PRESENT.search(inner)) and PAST.search(inner):
            rep.add("note", "thought-person", "thought marks around past-tense narration with "
                    "nobody speaking in it: %s" % _clip(inner), ch.line_of(t.start()))
    for line, text in ch.unterminated_thoughts():
        rep.add("defect", "channel-collision", "a thought mark opens and never closes: %s"
                % _clip(text), line)

    paras = ch.paragraphs()
    meta_open = ch.channels.meta_open
    if paras and paras[0][1][:1] in meta_open:
        rep.add("warn", "meta", "the chapter opens on a meta block", ch.line_of(paras[0][0]))
    prev = False
    for off, text in paras:
        is_meta = text[:1] in meta_open and text.rstrip()[-1:] in ch.channels.meta_close
        if is_meta and prev:
            rep.add("warn", "meta", "two meta blocks in a row", ch.line_of(off))
        prev = is_meta

    for off, text in paras:
        if BREAK_LINE.match(text.strip()):
            continue
        for sub_off, line in _para_lines(off, text):
            for rx, label in MARKUP:
                m = rx.search(line)
                if m:
                    rep.add("defect", "markup", "%s in the prose: %s" % (label, _clip(m.group(0))),
                            ch.line_of(sub_off))
                    break
    for m in BREAK_LINE.finditer(ch.body):
        if m.group(0).strip() != WELL_FORMED_BREAK:
            rep.add("warn", "scene-break", "`%s`; a scene break is `%s`"
                    % (m.group(0).strip(), WELL_FORMED_BREAK), ch.line_of(m.start()))


def _para_lines(off, text):
    pos = 0
    for line in text.split("\n"):
        yield off + pos, line
        pos += len(line) + 1


def check_house_style(ch, rep):
    outside = ch.outside_speech
    hits = []
    for rx, label in HOUSE_STYLE:
        for m in rx.finditer(outside):
            hits.append((m.start(), label))
    for off, label in sorted(hits):
        rep.add("note", "house-style", "%s: %s" % (label, _clip(_around(ch.body, off))),
                ch.line_of(off))
    if hits and ch.words:
        rep.add("note", "house-style", "%d in %d words (%.1f per 1,000), narration only"
                % (len(hits), ch.words, len(hits) * 1000.0 / ch.words))
    for rx, label in STOCK:
        for m in rx.finditer(ch.body):
            rep.add("warn", "stock", "`%s`: %s" % (label, _clip(_around(ch.body, m.start()))),
                    ch.line_of(m.start()))


def _around(body, off, before=15, after=55):
    start = max(0, off - before)
    start = body.rfind(" ", 0, start) + 1 if start else 0
    return body[start:off + after]


def check_echo(ch, rep):
    for phrase, n in ch.echoed_phrases(ECHO_WINDOW, ECHO_MIN):
        rep.add("note", "echo", "\"%s\" %d times" % (phrase, n))


def check_slop(ch, rep, top=8):
    """EQ-Bench's slop index (`lib/slop.py`), with the most frequent hits: a reference figure."""
    index, tokens, hits = slop.score(ch.body)
    if tokens:
        rep.add("note", "slop", "EQ-Bench slop index %.1f per 1,000 words: %s" % (
            index, ", ".join("%s %d" % (g, n) for g, n in hits.most_common(top)) or "no hits"))


def _unit(word):
    w = word.lower()
    return w[:-1] if len(w) > 3 and w.endswith("s") and not w.endswith("ss") else w


def _value(num):
    if num[0].isdigit():
        return int(num.replace(",", ""))
    first = num.lower().split("-")[0]
    return NUMBER_WORDS.index(first) + 1 if NUMBER_WORDS.index(first) < 20 else 21


def check_numerals(ch, rep, style=""):
    """A unit counted in digits in one place and in words in another, within the same range (both
    small or both large), is drift whatever the house style is. Everything else is listed for the
    critic to hold against the lexicon's style line."""
    forms = {}                    # (unit, small?) -> {"digits": [(line, text)], "words": [...]}
    for m in NUMBER_UNIT.finditer(ch.body):
        num, unit = m.group(1), m.group(2)
        if unit.lower() in NOT_UNITS:
            continue
        kind = "digits" if num[0].isdigit() else "words"
        key = (_unit(unit), _value(num) <= SMALL)
        forms.setdefault(key, {"digits": [], "words": []})[kind].append(
            (ch.line_of(m.start()), m.group(0)))
    for (unit, small), got in sorted(forms.items()):
        if got["digits"] and got["words"]:
            sample = sorted(got["words"][:3] + got["digits"][:3])
            rep.add("warn", "numerals", "`%s` counted both ways%s: %s" % (
                unit, " (twenty or under)" if small else " (over twenty)",
                "; ".join("line %d \"%s\"" % (l, t) for l, t in sample[:6])))
    digits = sorted(l_t for got in forms.values() for l_t in got["digits"])
    if digits:
        rep.add("note", "numerals", "in digits: %s%s" % (
            ", ".join("\"%s\" (%d)" % (t, l) for l, t in digits[:12]),
            " … %d more" % (len(digits) - 12) if len(digits) > 12 else ""))
    if style and forms:
        rep.add("note", "numerals", "the lexicon's style: %s" % _clip(style, 160))


def check_lexicon(ch, rep, variants=(), banned=()):
    for variant, canonical in variants:
        for m in re.finditer(r"(?<![\w'’])%s(?![\w'’])" % re.escape(variant), ch.body):
            rep.add("defect", "lexicon", "\"%s\"; the lexicon spells it %s"
                    % (variant, canonical), ch.line_of(m.start()))
    for word in banned:
        for m in re.finditer(r"\b%s\b" % re.escape(word), ch.body, re.I):
            rep.add("warn", "lexicon", "\"%s\" is on the lexicon's banned list: %s"
                    % (m.group(0), _clip(_around(ch.body, m.start()))), ch.line_of(m.start()))


def stats(ch, speakers=()):
    """The measurements, as note lines."""
    rep = Report()
    scenes = ch.section_words()
    rep.add("note", "stats", "%d words · speech %.0f%% · %d scene(s): %s · %d direct thought(s)"
            % (ch.words, ch.speech_share, len(scenes), " / ".join(str(n) for n in scenes),
               len(ch.thoughts())))
    if speakers:
        who = ch.scene_speakers(list(speakers))
        rep.add("note", "stats", "speakers by scene (named turns only, a floor): %s" % " · ".join(
            "%d) %s" % (i + 1, ", ".join(sorted(s)) or "none named") for i, s in enumerate(who)))
    return rep


def lint(path, nov=None):
    """The report for one chapter file, as a Report."""
    nov = nov or novel_mod.novel_of(path)
    channels = nov.channels if nov else DEFAULT_CHANNELS
    ch = Chapter(path, channels=channels)
    rep = stats(ch, nov.speakers() if nov else ())
    check_frontmatter(ch, rep)
    check_channels(ch, rep, nov.get("narration.interiority", "") if nov else "")
    check_house_style(ch, rep)
    check_echo(ch, rep)
    check_slop(ch, rep)
    check_numerals(ch, rep, nov.number_style() if nov else "")
    if nov:
        check_lexicon(ch, rep, nov.lexicon_variants(), nov.banned_words())
    return rep


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("chapters", nargs="+")
    ap.add_argument("--novel", help="the novel directory, if it cannot be found from the path")
    ap.add_argument("--out", help="also write the report to this file")
    ap.add_argument("--stats", action="store_true", help="only the measurements")
    args = ap.parse_args(argv)
    nov = novel_mod.Novel(args.novel) if args.novel else None
    out = []
    for path in args.chapters:
        if not os.path.isfile(path):
            sys.stderr.write("lint: no such file: %s\n" % path)
            return 1
        n = nov or novel_mod.novel_of(path)
        if args.stats:
            rep = stats(Chapter(path, channels=n.channels if n else DEFAULT_CHANNELS),
                        n.speakers() if n else ())
        else:
            rep = lint(path, n)
        if len(args.chapters) > 1:
            out.append("== %s" % path)
        out.extend(rep.lines()[:-1] if args.stats else rep.lines())
    text = "\n".join(out) + "\n"
    sys.stdout.write(text)
    if args.out:
        os.makedirs(os.path.dirname(os.path.abspath(args.out)), exist_ok=True)
        with open(args.out, "w", encoding="utf-8") as fh:
            fh.write(text)
    return 0


if __name__ == "__main__":
    sys.exit(main())
