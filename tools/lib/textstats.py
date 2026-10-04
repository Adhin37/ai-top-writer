"""A chapter's prose, measured: the four channels, words, scenes, sentences, repeated phrases.

Three properties of English prose that a naive parser gets wrong, each once a real miscount:

1. **Speech over several paragraphs** opens a quote on each paragraph and closes only on the last.
   Pairing quote marks greedily reads the middle paragraphs as narration. So a speech span never
   crosses a paragraph break: an unclosed quote runs to the end of its paragraph and no further.
2. **Curly marks.** `'` and `‘…’` are one channel to a reader. Each channel accepts both forms.
3. **Leading-apostrophe elisions** (`'twas`, `'em`, `'99`) are words, not opened thoughts.

The marks come from `novel.md` → `channels:`, so changing that block changes what is measured.
"""

import os
import re

from . import mdio

_DOUBLE_OPEN = ('"', "“")
_DOUBLE_CLOSE = ('"', "”")
_SINGLE_OPEN = ("'", "‘")
_SINGLE_CLOSE = ("'", "’")

_ELISIONS = ("twas", "tis", "twere", "em", "im", "er", "n", "cause", "bout", "round", "til",
             "till", "tween", "neath", "gainst", "fore", "way", "kay", "nother")
_ELISION_RE = re.compile(r"^(?:%s)\b|^\d{2}\b" % "|".join(_ELISIONS), re.I)

_PARA_SPLIT = re.compile(r"\n[ \t]*\n")
SENTENCE_END = re.compile(r"[.!?]+[\"”'’)\]]*(?:\s+|$)")
BREAK = re.compile(r"^\s*\*\s\*\s\*\s*$", re.M)
WORD = re.compile(r"[a-z0-9’']+")


def _family(ch, opening):
    if ch in _DOUBLE_OPEN or ch in _DOUBLE_CLOSE:
        return set(_DOUBLE_OPEN if opening else _DOUBLE_CLOSE)
    if ch in _SINGLE_OPEN or ch in _SINGLE_CLOSE:
        return set(_SINGLE_OPEN if opening else _SINGLE_CLOSE)
    return {ch}


def _marks(spec, default_open, default_close):
    """'"…"' -> ({'"', '“'}, {'"', '”'}). A malformed spec falls back to the defaults."""
    s = str(spec or "").strip()
    if s[:1] in ("'", '"') and s[-1:] == s[:1] and len(s) > 2:
        s = s[1:-1].strip()
    if len(s) < 2:
        return _family(default_open, True), _family(default_close, False)
    return _family(s[0], True), _family(s[-1], False)


def _cls(chars):
    return "[%s]" % "".join(sorted(re.escape(c) for c in chars))


class Channels(object):
    """The marks that carry speech, direct thought and meta. Free indirect is unmarked."""

    def __init__(self, speech=None, thought=None, meta=None):
        self.speech_open, self.speech_close = _marks(speech, '"', '"')
        self.thought_open, self.thought_close = _marks(thought, "'", "'")
        self.meta_open, self.meta_close = _marks(meta, "[", "]")
        self.speech_marks = self.speech_open | self.speech_close
        closes = "".join(sorted(re.escape(c) for c in self.thought_close))
        lead = _cls(set(" \t(") | self.speech_open | {"—", "–"})
        trail = _cls(set(" \t.,;:!?)") | self.speech_close | {"—", "–"})
        # Opens at a boundary, closes before punctuation or space; an apostrophe with a letter on
        # both sides stays inside, so 'Start with what you're sure of.' is one thought.
        self.thought_re = re.compile(
            r"(?:(?<=^)|(?<=%s))%s((?:[^%s\n]|(?<=\w)%s(?=\w))+?)%s(?=%s|$)"
            % (lead, _cls(self.thought_open), closes, _cls(self.thought_close),
               _cls(self.thought_close), trail), re.M)
        self.meta_re = re.compile(
            _cls(self.meta_open) + r"[^%s\n]*" % "".join(sorted(re.escape(c)
                                                               for c in self.meta_close))
            + _cls(self.meta_close))
        self.unterminated_re = re.compile(
            r"(?:^|[\s(\[\-])(%s)([^%s]{2,})$" % (_cls(self.thought_open), closes))

    @classmethod
    def from_config(cls, cfg):
        ch = (cfg or {}).get("channels") or {}
        return cls(speech=ch.get("speech"), thought=ch.get("thought"), meta=ch.get("meta"))


DEFAULT_CHANNELS = Channels()


def paragraph_ranges(text):
    """(start, end) of every paragraph, blank-line separated."""
    out, pos = [], 0
    for m in _PARA_SPLIT.finditer(text):
        out.append((pos, m.start()))
        pos = m.end()
    out.append((pos, len(text)))
    return out


def find_speech_spans(text, channels=DEFAULT_CHANNELS):
    """(start, end) of every speech span, never crossing a paragraph break."""
    opens, closes, marks = channels.speech_open, channels.speech_close, channels.speech_marks
    spans = []
    for pstart, pend in paragraph_ranges(text):
        start = None
        for i in range(pstart, pend):
            c = text[i]
            if c not in marks:
                continue
            if start is None:
                if c in closes and c not in opens:
                    continue                      # a stray closer opens nothing
                start = i
            elif c in opens and c not in closes:
                spans.append((start, i))          # a new opener: the last one never closed
                start = i
            else:
                spans.append((start, i + 1))
                start = None
        if start is not None:
            spans.append((start, pend))
    return spans


def blank_ranges(text, ranges):
    """The text with each range turned to spaces; offsets and newlines kept."""
    if not ranges:
        return text
    buf = list(text)
    for start, end in ranges:
        for i in range(start, end):
            if buf[i] != "\n":
                buf[i] = " "
    return "".join(buf)


def words(text):
    return len(text.split())


class Chapter(object):
    """One chapter file: frontmatter, body, and measurements of the body."""

    def __init__(self, path, channels=None, text=None):
        self.path = path
        self.name = os.path.basename(path)
        self.channels = channels or DEFAULT_CHANNELS
        text = mdio.read_text(path) if text is None else text
        fm, body = mdio.split_frontmatter(text)
        self.frontmatter_text = fm
        self.meta = mdio.parse_yaml(fm) if fm else {}
        self.body = body
        self.body_start_line = text[:len(text) - len(body)].count("\n") + 1
        self._line_starts = None
        self._spans = None
        self._outside = None

    @property
    def number(self):
        n = self.meta.get("number")
        if isinstance(n, int):
            return n
        m = re.match(r"^(\d+)", self.name)
        return int(m.group(1)) if m else None

    @property
    def title(self):
        return str(self.meta.get("title") or "")

    @property
    def words(self):
        """Body words, as `wc -w` counts them."""
        return words(self.body)

    def line_of(self, offset):
        """The file's line number for an offset into the body."""
        if self._line_starts is None:
            self._line_starts = [0] + [m.end() for m in re.finditer(r"\n", self.body)]
        lo, hi = 0, len(self._line_starts) - 1
        while lo < hi:
            mid = (lo + hi + 1) // 2
            if self._line_starts[mid] <= offset:
                lo = mid
            else:
                hi = mid - 1
        return self.body_start_line + lo

    # ---------------------------------------------------------------- channels

    @property
    def speech_ranges(self):
        if self._spans is None:
            self._spans = find_speech_spans(self.body, self.channels)
        return self._spans

    @property
    def speech_spans(self):
        return [self.body[s:e] for s, e in self.speech_ranges]

    @property
    def speech_words(self):
        return sum(words(s) for s in self.speech_spans)

    @property
    def speech_share(self):
        total = self.words
        return self.speech_words * 100.0 / total if total else 0.0

    @property
    def outside_speech(self):
        """The body with speech blanked out, offsets and line breaks kept."""
        if self._outside is None:
            self._outside = blank_ranges(self.body, self.speech_ranges)
        return self._outside

    def thoughts(self):
        return list(self.channels.thought_re.finditer(self.outside_speech))

    def metas(self):
        return list(self.channels.meta_re.finditer(self.outside_speech))

    def unterminated_thoughts(self):
        """(line, text) for each line that opens a thought mark and never closes it."""
        out = []
        for i, line in enumerate(self.outside_speech.split("\n")):
            m = self.channels.unterminated_re.search(line)
            if m and not _ELISION_RE.match(m.group(2)):
                out.append((self.body_start_line + i, line.strip()))
        return out

    def nested_thought_in_speech(self):
        """'…' pairs inside a speech span: an ordinary nested quotation, counted apart."""
        return sum(len(self.channels.thought_re.findall(s)) for s in self.speech_spans)

    # -------------------------------------------------------------- structure

    def paragraphs(self):
        """(offset, text) for every non-empty paragraph."""
        out = []
        for start, end in paragraph_ranges(self.body):
            chunk = self.body[start:end]
            if chunk.strip():
                out.append((start + len(chunk) - len(chunk.lstrip()), chunk.strip()))
        return out

    def sentences(self):
        """(offset, text) for every sentence."""
        out, start = [], 0
        for m in SENTENCE_END.finditer(self.body):
            chunk = self.body[start:m.end()]
            if chunk.strip():
                out.append((start + len(chunk) - len(chunk.lstrip()), chunk.strip()))
            start = m.end()
        tail = self.body[start:].strip()
        if tail:
            out.append((start, tail))
        return out

    def narration_sentences(self):
        """Sentences with no speech in them."""
        ranges = self.speech_ranges
        return [(off, seg) for off, seg in self.sentences()
                if not any(s < off + len(seg) and off < e for s, e in ranges)]

    def scene_breaks(self):
        return len(BREAK.findall(self.body))

    def scene_bounds(self):
        """(start, end) of each scene, split on `* * *`."""
        edges = [0] + [m.end() for m in BREAK.finditer(self.body)] + [len(self.body)]
        return [(edges[i], edges[i + 1]) for i in range(len(edges) - 1)]

    def section_words(self):
        """Words per scene, in order, break lines left out."""
        return [words(BREAK.sub("", self.body[a:b])) for a, b in self.scene_bounds()]

    def speech_paragraphs(self):
        """(start, end, spans, around) for each paragraph with speech; `around` is the paragraph's
        text outside the quotes, where a speaker's name is."""
        out, ranges = [], self.speech_ranges
        for start, end in paragraph_ranges(self.body):
            spans = [(s, e) for s, e in ranges if start <= s < end]
            if not spans:
                continue
            around, cursor = "", start
            for s, e in spans:
                around += self.body[cursor:s]
                cursor = e
            around += self.body[cursor:end]
            out.append((start, end, spans, around))
        return out

    def scene_speakers(self, names):
        """For each scene, the set of `names` that speak in it: a turn counts for a speaker when
        exactly one name's token appears outside its quotes. A floor: an untagged turn names
        nobody. `names` is a list of full names; a token shared by two names identifies neither."""
        shared = {}
        for name in names:
            for t in set(re.split(r"[^\w']+", name)):
                if len(t) >= 3:
                    shared[t] = shared.get(t, 0) + 1
        tokens = {n: [t for t in re.split(r"[^\w']+", n)
                      if len(t) >= 3 and t[:1].isupper() and shared.get(t) == 1] for n in names}
        tokens = {n: ts for n, ts in tokens.items() if ts}
        paras = self.speech_paragraphs()
        out = []
        for start, end in self.scene_bounds():
            speakers = set()
            for pstart, _pend, _spans, around in paras:
                if not start <= pstart < end:
                    continue
                hits = [n for n, ts in tokens.items()
                        if any(re.search(r"\b%s\b" % re.escape(t), around) for t in ts)]
                if len(hits) == 1:
                    speakers.add(hits[0])
            out.append(speakers)
        return out

    def scene_turns(self):
        """Spoken turns per scene: the paragraphs with speech in them."""
        starts = [p[0] for p in self.speech_paragraphs()]
        return [sum(1 for s in starts if a <= s < b) for a, b in self.scene_bounds()]

    def echoed_phrases(self, window=4, minimum=3):
        """(phrase, count) for each `window`-word phrase used `minimum`+ times. Overlapping windows
        of one repetition are reported once."""
        ws = WORD.findall(self.body.lower().replace("’", "'"))
        counts = {}
        for i in range(len(ws) - window + 1):
            key = tuple(ws[i:i + window])
            counts[key] = counts.get(key, 0) + 1
        hits = sorted(((n, k) for k, n in counts.items() if n >= minimum), reverse=True)
        kept = []
        for n, key in hits:
            if any(key[1:] == k[:-1] or key[:-1] == k[1:] for _n, k in kept):
                continue
            kept.append((n, key))
        return [(" ".join(k), n) for n, k in kept]


def load_chapters(chapters_dir, channels=None):
    """Every `NNNN-*.md` chapter in a directory, in file-name order."""
    if not os.path.isdir(chapters_dir):
        return []
    return [Chapter(os.path.join(chapters_dir, n), channels=channels)
            for n in sorted(os.listdir(chapters_dir))
            if re.match(r"^\d+.*\.md$", n) and not n.startswith("_")]
