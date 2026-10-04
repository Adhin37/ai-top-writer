"""tools/scaffold.py - a new novel from the template, and the check that init filled it.

The filled novel is invented: a sealed habitat where every breath is billed by job grade.
"""
import os
import shutil
import sys
import tempfile
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "tools"))

import scaffold  # noqa: E402
from lib import mdio  # noqa: E402
from lib.novel import Novel  # noqa: E402

NOVEL_MD = """---
title: "Thirty Days of Air"
slug: "%(slug)s"
platform: "royalroad"
exposition: %(exposition)s
genre: "scifi"
subgenre: "working-class survival"

narration:
  person: "third-limited"
  tense: "past"
  distance: "close"
  interiority: "medium"

pov:
  mode: "single"
  pov_characters: ["Tovi Brand"]
  switch_granularity: "never"

tone:
  register: "grounded"
  warmth: "measured"

channels:
  speech: '"…"'
  thought: "'…'"
  meta: "[…]"

mc:
  name: "Tovi Brand"
  foreknowledge: ""

opening:
  promise: "A fitter stripped of her air grade has thirty days to earn it back."
  contract_by_ch: %(contract)s

content:
  rating: "teen"
  romance: "none"
  hard_limits: []

optional:
  no-harem: on
  romance-arc: off
---

# Blurb

On the Ansel Stack there is no outside, and every breath is billed. Your job grade decides how much
of it is paid for. Tovi Brand reported a leaking air main. For that, her supervisor struck her
grade, and she has thirty days of air on credit. On day thirty-one, she goes down-well. The only
crews hiring the ungraded are the deep crews. Nobody on the Stack has ever met anyone who came
back from one.

# Style anchor

The meter on Tovi's wrist clicked at shift change, the way it did for everyone. This time the
number went red.
"""

PREMISE = """---
type: reference
title: Premise
---
# Premise

## In one breath
On the Ansel Stack every breath is billed by job grade. Tovi Brand has just lost hers.

## Load-bearing facts
| id | fact, in plain words | source |
|---|---|---|
| P1 | The Stack is sealed and all air comes from Deck Nine | bible/world.md §The central rule |
| P2 | Your job grade decides how much of your air is paid for | bible/society.md §labour |
| P3 | Tovi Brand, a pipe-fitter, has just lost her grade | bible/cast/tovi-brand.md |
"""

LEDGER = """# Reader ledger

## Facts
| id | fact, in plain words | due by ch | how it lands | status |
|---|---|---|---|---|
| P1 | premise | 1 | she tells the new hire, clamping the main | owed |
| P2 | premise | %(p2)s | her meter ticks over at shift change | owed |
| P3 | premise | 1 | Kell strikes it in front of the crew | owed |

## Faces
| id | who | why the reader needs them | on the page by ch | status |
|---|---|---|---|---|
| A1 | Supervisor Kell | the opposition needs a face | %(face)s | owed |

## Promises
| id | what the page promises | made in ch | paid by ch | status |
|---|---|---|---|---|
| R1 | why Kell struck her grade | 1 | 8 | owed |
"""

ROW = "| %d | Chapter %d | Tovi Brand | %s | %s | a goal | an obstacle | a turn | Tovi does a thing %d | a cost | a keep | %s |"
TEMPS = ["tense", "quiet", "fast", "warm", "bleak", "procedural", "tense", "loud", "quiet", "warm"]
HOOKS = ["decision", "question", "reveal", "arrival", "threat", "reversal", "decision", "cliff",
         "quiet", "question"]


def plan(temps=TEMPS, hooks=HOOKS, threads=("~T1", "^T1", "~T2")):
    rows = [ROW % (n, n, temps[n - 1], hooks[n - 1], n, threads[(n - 1) % len(threads)])
            for n in range(1, len(temps) + 1)]
    return ("# Chapters\n\n| # | title | pov | temp | hook | goal | obstacle | turn | event | cost "
            "| keeps | threads |\n|---|---|---|---|---|---|---|---|---|---|---|---|\n"
            + "\n".join(rows) + "\n")


THREADS = """# Thread board

| id | thread | ledger | opened | last | status |
|---|---|---|---|---|---|
| T1 | why Kell struck her | R1 | — | — | planned |
| T2 | the deep crews | — | — | — | planned |
"""

PROFILE = """---
name: "%s"
role: %s
first_appears: 1
---
# %s

seen      the Stack reads her as a pair of hands
"""

FILLED = {
    "bible/world.md": "# World\n\n## The central rule\nAir is billed by the shift.\n",
    "bible/society.md": "# Society\n\n- labour: grade decides air\n",
    "bible/lexicon.md": ("# Lexicon\n\n## Names\n| canonical | who or what | never write as |\n"
                         "|---|---|---|\n| Tovi Brand | the fitter | Tovy |\n"),
    "bible/cast/_voices.md": ("# Voice matrix\n\n| character | intel | eq |\n|---|---|---|\n"
                              "| Tovi Brand | 3 | 2 |\n| Kell | 3 | 4 |\n"),
    "bible/cast/_extras.md": "# Walk-ons\n\nnone yet\n",
    "bible/cast/tovi-brand.md": PROFILE % ("Tovi Brand", "protagonist", "Tovi Brand"),
    "bible/cast/kell.md": PROFILE % ("Kell", "antagonist", "Kell"),
    "plan/arcs.md": "# Arc plan\n\n## The ending\nShe comes back up.\n",
    "plan/timeline.md": "# The world's clock\n\nKell watches before he moves.\n",
    "state/threads.md": THREADS,
}


class Fixture(object):
    """A temporary novels/ directory with one novel scaffolded from the real template."""

    def __init__(self, filled=True, slug="thirty-days", **fields):
        self.filled, self.slug = filled, slug
        self.fields = {"slug": slug, "exposition": "clear", "contract": 3, "p2": 1, "face": 1}
        self.fields.update(fields)

    def __enter__(self):
        self.tmp = tempfile.mkdtemp(prefix="atw-scaffold-")
        self.root = scaffold.new(self.slug, novels_dir=self.tmp)
        if self.filled:
            self.write("novel.md", NOVEL_MD % self.fields)
            self.write("bible/premise.md", PREMISE)
            self.write("plan/reader-ledger.md", LEDGER % self.fields)
            self.write("plan/chapters.md", plan())
            for rel, text in FILLED.items():
                self.write(rel, text)
            for n in range(1, scaffold.ROUNDS + 1):
                self.write("work/init/round-%d.md" % n, "# Round %d\n\n1. q\n\n## Answers\n1. rec\n"
                           % n)
        return self

    def __exit__(self, *exc):
        shutil.rmtree(self.tmp, ignore_errors=True)
        return False

    def write(self, rel, text):
        path = os.path.join(self.root, *rel.split("/"))
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w", encoding="utf-8") as fh:
            fh.write(text)

    def check(self):
        return scaffold.check(Novel(self.root))

    def found(self):
        return self.check().found


def has(found, level, text):
    return any(lv == level and text in detail for lv, _c, detail in found)


class NewTest(unittest.TestCase):
    def test_copies_every_template_file_and_sets_the_slug(self):
        with Fixture(filled=False) as fx:
            for rel in scaffold.template_files():
                self.assertTrue(os.path.isfile(os.path.join(fx.root, rel)), rel)
            self.assertEqual(Novel(fx.root).get("slug"), "thirty-days")
            self.assertTrue(os.path.isdir(os.path.join(fx.root, "chapters")))
            self.assertTrue(os.path.isdir(os.path.join(fx.root, "work", "init")))
            self.assertFalse(os.path.exists(os.path.join(fx.root, "chapters", ".gitkeep")))

    def test_never_overwrites_a_novel(self):
        with Fixture(filled=False) as fx:
            with self.assertRaises(ValueError):
                scaffold.new("thirty-days", novels_dir=fx.tmp)

    def test_refuses_a_bad_slug(self):
        tmp = tempfile.mkdtemp(prefix="atw-scaffold-")
        try:
            for slug in ("_template", "Thirty Days", "-x", "", "a/b"):
                with self.subTest(slug=slug):
                    with self.assertRaises(ValueError):
                        scaffold.new(slug, novels_dir=tmp)
        finally:
            shutil.rmtree(tmp, ignore_errors=True)


class TemplateAgreesWithTheToolsTest(unittest.TestCase):
    """The template's tables and keys are found by the columns the tools read."""

    def test_template_tables_and_keys(self):
        nov = Novel(scaffold.TEMPLATE)
        for key in scaffold.REQUIRED_KEYS:
            with self.subTest(key=key):
                self.assertNotIn(nov.get(key), (None, "", [], {}))
        self.assertEqual(len(nov.plan_rows()), 1)
        self.assertEqual(len(scaffold.premise_ids(nov)), 1)
        ledger = nov.ledger()
        for kind in ("facts", "faces", "promises"):
            self.assertEqual(len(ledger[kind]), 1, kind)
        self.assertIsNotNone(mdio.table_with(nov.text("state", "threads.md"), "id", "thread",
                                             "status"))
        self.assertIsNotNone(mdio.table_with(nov.text("bible", "cast", "_voices.md"),
                                             "character"))
        self.assertIsNotNone(mdio.table_with(nov.text("bible", "lexicon.md"), "canonical",
                                             "never write as"))
        self.assertTrue(nov.number_style())

    def test_a_fresh_scaffold_is_full_of_placeholders(self):
        with Fixture(filled=False) as fx:
            found = fx.found()
            self.assertTrue(has(found, "defect", "novel.md:"))
            self.assertFalse(fx.check().lines()[-1].endswith("clean"))


class CheckTest(unittest.TestCase):
    def test_a_filled_novel_is_clean(self):
        with Fixture() as fx:
            lines = fx.check().lines()
            self.assertTrue(lines[-1].endswith("clean"), lines)

    def test_a_placeholder_left_behind(self):
        with Fixture() as fx:
            fx.write("bible/society.md", "# Society\n\n- money: {{what costs what}}\n")
            self.assertTrue(has(fx.found(), "defect", "bible/society.md:3"))

    def test_a_missing_file(self):
        with Fixture() as fx:
            os.remove(os.path.join(fx.root, "plan", "timeline.md"))
            self.assertTrue(has(fx.found(), "defect", "plan/timeline.md is missing"))

    def test_a_premise_fact_due_after_chapter_one(self):
        with Fixture(p2=2) as fx:
            self.assertTrue(has(fx.found(), "defect", "P2 is due by ch 2"))
        with Fixture(p2=2, exposition="gradual") as fx:
            self.assertFalse(has(fx.found(), "defect", "P2"))

    def test_a_premise_fact_with_no_ledger_row(self):
        with Fixture() as fx:
            fx.write("plan/reader-ledger.md", (LEDGER % fx.fields).replace(
                "| P3 | premise | 1 | Kell strikes it in front of the crew | owed |\n", ""))
            self.assertTrue(has(fx.found(), "defect", "premise fact P3 has no row"))

    def test_the_antagonist_arrives_too_late(self):
        with Fixture(face=5) as fx:
            self.assertTrue(has(fx.found(), "defect", "no face is due on the page by ch 3"))
        with Fixture(face=5, contract=5) as fx:
            self.assertFalse(has(fx.found(), "defect", "no face"))

    def test_a_thread_not_on_the_board(self):
        with Fixture() as fx:
            fx.write("plan/chapters.md", plan(threads=("~T1", "~T9")))
            self.assertTrue(has(fx.found(), "defect", "T9 is in the plan"))

    def test_rows_out_of_vocabulary_and_samey(self):
        with Fixture() as fx:
            temps = ["tense", "tense", "tense"] + TEMPS[3:]
            hooks = ["the door shuts"] + HOOKS[1:]
            fx.write("plan/chapters.md", plan(temps=temps, hooks=hooks))
            found = fx.found()
            self.assertTrue(has(found, "warn", "ch 1 hook `the door shuts`"))
            self.assertTrue(has(found, "note", "chs 1–3 are all `tense`"))

    def test_no_profile_for_the_protagonist(self):
        with Fixture() as fx:
            os.remove(os.path.join(fx.root, "bible", "cast", "tovi-brand.md"))
            self.assertTrue(has(fx.found(), "defect", "no profile in bible/cast/ has `name: Tovi"))

    def test_interview_rounds(self):
        with Fixture() as fx:
            os.remove(os.path.join(fx.root, "work", "init", "round-4.md"))
            fx.write("work/init/round-6b.md", "# Round 6, again\n\n1. say it back\n")
            found = fx.found()
            self.assertTrue(has(found, "warn", "round(s) 4 never asked"))
            self.assertTrue(has(found, "warn", "round-6b.md has no `## Answers`"))

    def test_a_name_another_novel_uses(self):
        with Fixture() as fx:
            other = os.path.join(fx.tmp, "other-book")
            os.makedirs(os.path.join(other, "bible"))
            for rel, text in (("novel.md", "---\nslug: other-book\n---\n"),
                              ("bible/lexicon.md", "## Names\n| canonical | who |\n|---|---|\n"
                               "| Kell Arden | a clerk |\n| the Brand Yard | a place |\n")):
                with open(os.path.join(other, *rel.split("/")), "w", encoding="utf-8") as fh:
                    fh.write(text)
            found = fx.found()
            self.assertFalse(has(found, "warn", "Brand"))
            self.assertFalse(has(found, "warn", "Tovi"))
            fx.write("bible/lexicon.md", FILLED["bible/lexicon.md"] + "| Kell | the boss | |\n")
            self.assertTrue(has(fx.found(), "warn", "Kell (Kell) is also in other-book (Kell Arden)"))

    def test_style_anchor_and_blurb(self):
        with Fixture() as fx:
            text = NOVEL_MD % fx.fields
            fx.write("novel.md", text.split("# Style anchor")[0])
            self.assertTrue(has(fx.found(), "defect", "no sample under `# Style anchor`"))


if __name__ == "__main__":
    unittest.main()
