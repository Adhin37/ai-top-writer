"""A small novel on disk, for the tests of tools/lib, lint, state_check and reading.

The world is invented (the harbour town of the wire-format examples). Each test writes only the
files it is about; `NovelFixture` supplies a plausible default for the rest.
"""
import os
import shutil
import sys
import tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TOOLS = os.path.join(ROOT, "tools")
if TOOLS not in sys.path:
    sys.path.insert(0, TOOLS)

NOVEL_MD = """---
title: "The Long Ebb"
slug: "long-ebb"
narration:
  person: third-limited
  tense: past
  interiority: high
mc:
  name: Nessa Vane
channels:
  speech: '"…"'
  thought: "'…'"
  meta: "[…]"
---

# Premise

A test book.
"""

LEXICON = """# Lexicon

## Names

| canonical | who/what | never write as |
|---|---|---|
| Nessa Vane | the rower | Nesa, Vane's (possessive is fine), Nessa Vain |
| Harbourmaster Quell | the harbour office | Harbormaster, Quel |

## House style

- Numbers: spell out one through twenty; numerals above that. Always numerals for measurements.

## Banned words for this novel

`destiny` · `ancient evil`
"""

VOICES = """# Voices

| character | tier | intel |
|---|---|---|
| Nessa Vane | A | 3 |
| Harbourmaster Quell | B | 2 |
"""

EXTRAS = """# Extras

<!--
Example Person — what — ch 1 — alive
-->

Tam Orrin — boathouse lad — ch 1, 3 — alive
  wants: x | tic: y
"""

PLAN = """# Chapters

| # | title | pov | temp | event | threads | status |
|---|---|---|---|---|---|---|
| 1 | The Tally | Nessa Vane | quiet | Nessa finds the Harrow boy's name on the tally | ~T1 ~T2 | revised |
| 2 | The Bar | Nessa Vane | tense | Nessa rows the boy out past the bar | ^T2 ~T3 | planned |
"""

LEDGER = """# Reader ledger

## Facts
| id | fact, in plain words | due by ch | how it lands | status |
|---|---|---|---|---|
| P1 | premise | 1 | the tally on the boathouse door | landed ch1 |
| F2 | the bar is dry for an hour at the lowest ebb | 2 | she walks it | owed |

## Faces
| id | who | why the reader needs them | on the page by ch | status |
|---|---|---|---|---|
| A1 | Harbourmaster Quell | the opposition needs a face | 1 | partly ch1 — his office, not his reason |

## Promises
| id | what the page promises | made in ch | paid by ch | status |
|---|---|---|---|---|
| R1 | who signed the tally | 1 | 6 | owed |
"""

THREADS = """# Threads

| id | thread | ledger | opened | last | status |
|---|---|---|---|---|---|
| T1 | the tally's early date | R1 | 1 | 1 | open |
| T2 | the Harrow boy | — | 1 | 1 | open |
| T3 | Quell knows she went out | — | — | — | planned |
"""

BLOCK = """=C%(n)04d= day %(n)d, dusk | words %(words)d
ev    Nessa finds the Harrow boy's name on the tally
at    Nessa: the boathouse · Quell: the harbour office
kno   Nessa+ the tally was signed before the boy drowned (the date on it)
thr   %(thr)s
hook  Quell's lamp is lit when she comes back
"""

SCENES = """# Scenes

| ch | scene | who | where | tempo | two-hander |
|---|---|---|---|---|---|
| 1 | 1 | Nessa, Tam | the quay | quiet | yes |
"""

TIMELINE = """# Timeline

| day | ch | where | what happens |
|---|---|---|---|
| 1 | 1 | the quay | the tally is chalked |
"""

CHAPTER = """---
number: %(n)d
title: "%(title)s"
pov: "Nessa Vane"
---

%(body)s
"""

BODY = """The tally was chalked on the boathouse door, and the Harrow boy's name was on it.

"Who put him there?" Nessa said.

Tam shrugged at the door. "Quell did. Same as always."
"""


class NovelFixture(object):
    """A throwaway repo with one novel in it. Use as a context manager."""

    def __init__(self, slug="long-ebb"):
        self.slug = slug

    def __enter__(self):
        self.tmp = tempfile.mkdtemp(prefix="atw-test-")
        self.root = os.path.join(self.tmp, "novels", self.slug)
        for rel, text in (("novel.md", NOVEL_MD), ("bible/lexicon.md", LEXICON),
                          ("bible/cast/_voices.md", VOICES), ("bible/cast/_extras.md", EXTRAS),
                          ("plan/chapters.md", PLAN), ("plan/reader-ledger.md", LEDGER)):
            self.write(rel, text)
        return self

    def __exit__(self, *exc):
        shutil.rmtree(self.tmp, ignore_errors=True)
        return False

    def path(self, *parts):
        return os.path.join(self.root, *parts)

    def write(self, rel, text, newline="\n", bom=False):
        full = self.path(*rel.split("/"))
        os.makedirs(os.path.dirname(full), exist_ok=True)
        with open(full, "w", encoding="utf-8", newline="") as fh:
            fh.write(("﻿" if bom else "") + text.replace("\n", newline))
        return full

    def chapter(self, n, body=BODY, title=None, slug=None, **fields):
        title = title or "Chapter %d" % n
        text = CHAPTER % {"n": n, "title": title, "body": body}
        if fields:
            extra = "".join("%s: %s\n" % kv for kv in fields.items())
            text = text.replace("---\n\n", extra + "---\n\n", 1)
        return self.write("chapters/%04d-%s.md" % (n, slug or "chapter-%d" % n), text)

    def state(self, blocks=(1,), thr="~T1 ~T2", threads=THREADS, scenes=SCENES,
              timeline=TIMELINE, words=None):
        from lib.textstats import Chapter
        out = ["# Continuity", ""]
        for n in blocks:
            path = [p for p in os.listdir(self.path("chapters"))
                    if p.startswith("%04d-" % n)] if os.path.isdir(self.path("chapters")) else []
            w = words if words is not None else (
                Chapter(self.path("chapters", path[0])).words if path else 0)
            out.append(BLOCK % {"n": n, "words": w, "thr": thr})
        self.write("state/continuity.md", "\n".join(out))
        self.write("state/threads.md", threads)
        self.write("state/scenes.md", scenes)
        self.write("state/timeline.md", timeline)

    def novel(self):
        from lib.novel import Novel
        return Novel(self.root)
