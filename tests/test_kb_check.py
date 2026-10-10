"""tools/kb_check.py - the knowledge bases' shape, the leak sweep, and the counts."""
import os
import shutil
import sys
import tempfile
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "tools"))

import kb_check  # noqa: E402

DOC = "---\ntype: howto\ntitle: X\n---\n# X\n\nDo it. Never not do it.\n"
LEXICON = """# Lexicon

## Names

| canonical | who/what | never write as |
|---|---|---|
| Nessa Vane | the rower | Nesa |

## Terms of art

| term | meaning |
|---|---|
| the Long Ebb | the night the sea gives back its drowned |
| the Tally | the list of the drowned |
"""
WORLD = """# World

| place | what |
|---|---|
| Merrow | the harbour town |
"""


class KbCheckTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.kb = os.path.join(self.tmp, "kb")
        self.write("kb/writer/index.md", "# Writer\n\n| doc | when |\n|---|---|\n"
                   "| [prompt.md](prompt.md) | always |\n| [a.md](a.md) | always |\n")
        self.write("kb/writer/prompt.md", DOC)
        self.write("kb/writer/a.md", DOC)
        self.write(".claude/agents/writer.md", "---\nname: writer\n---\nRead `kb/writer/prompt.md`.\n")

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def write(self, rel, text):
        path = os.path.join(self.tmp, rel)
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w", encoding="utf-8") as fh:
            fh.write(text)
        return path

    def found(self, novels=()):
        return [(lv, check) for lv, check, _d in kb_check.run(self.tmp, novels)]

    def test_a_clean_tree(self):
        self.assertEqual(self.found(), [])

    def test_a_doc_with_no_type(self):
        self.write("kb/writer/a.md", "# X\n\nNo frontmatter.\n")
        self.assertIn(("defect", "type"), self.found())

    def test_an_unlinked_doc_and_a_broken_link(self):
        self.write("kb/writer/b.md", DOC)
        self.write("kb/writer/a.md", DOC + "\nSee [gone](gone.md).\n")
        found = self.found()
        self.assertIn(("warn", "unlinked"), found)
        self.assertIn(("defect", "link"), found)

    def test_an_agent_pointing_at_a_missing_prompt(self):
        self.write(".claude/agents/clerk.md", "---\nname: clerk\n---\nRead `kb/clerk/prompt.md`.\n")
        self.assertIn(("defect", "agent"), self.found())

    def test_a_sonnet_agent_off_high_effort(self):
        self.write(".claude/agents/clerk.md", "---\nname: clerk\nmodel: claude-sonnet-5-5\n"
                   "effort: medium\n---\nRead `kb/writer/prompt.md`.\n")
        self.assertIn(("warn", "effort"), self.found())
        self.write(".claude/agents/clerk.md", "---\nname: clerk\nmodel: claude-sonnet-5-5\n"
                   "effort: high\n---\nRead `kb/writer/prompt.md`.\n")
        self.assertNotIn(("warn", "effort"), self.found())

    def test_dated_text(self):
        self.write("kb/writer/a.md", DOC + "\nAs run #7 showed on 2026-10-03.\n")
        self.assertIn(("warn", "dated"), self.found())

    def test_the_leak_sweep(self):
        novel = os.path.join(self.tmp, "novels", "tide")
        self.write("novels/tide/bible/lexicon.md", LEXICON)
        self.write("novels/tide/bible/world.md", WORLD)
        names, terms = kb_check.novel_nouns(novel)
        self.assertIn("Nessa", names)
        self.assertIn("Merrow", names)
        self.assertIn("Long Ebb", terms)
        self.assertEqual(self.found([novel]), [])
        self.write("kb/writer/a.md", DOC + "\nTally the boats. She checked the Tally twice.\n"
                   "Nessa rowed out on the Long Ebb from Merrow.\n")
        details = [d for lv, c, d in kb_check.run(self.tmp, [novel]) if c == "leak"]
        self.assertEqual(len(details), 4, details)   # Tally mid-sentence, Nessa, Long Ebb, Merrow
        self.assertFalse(any("line 8 names 'Tally'" in d for d in details), details)

    def test_a_common_word_split_off_a_name_is_a_term(self):
        novel = os.path.join(self.tmp, "novels", "tide")
        self.write("novels/tide/bible/lexicon.md", LEXICON.replace("Nessa Vane", "Nine Vane", 1))
        self.write("novels/tide/bible/world.md", WORLD)
        self.write("kb/writer/a.md", DOC + "\nDeck Nine was quiet. The vane turned, a Vane spun.\n")
        names, terms = kb_check.novel_nouns(novel, kb_check.ordinary_words(
            os.path.join(self.tmp, "kb")))
        self.assertIn("Nine Vane", names)
        self.assertNotIn("Nine", names)
        self.assertIn("Vane", terms)         # the knowledge base writes "vane" in lower case
        details = [d for lv, c, d in kb_check.run(self.tmp, [novel]) if c == "leak"]
        self.assertEqual(len(details), 1, details)    # "a Vane": mid-sentence, a term's leak

    def test_a_near_name_is_a_warn_and_a_sentence_head_is_not(self):
        novel = os.path.join(self.tmp, "novels", "tide")
        self.write("novels/tide/bible/lexicon.md", LEXICON)
        self.write("novels/tide/bible/world.md", WORLD)
        self.write("kb/writer/a.md", DOC + "\nThe boy from Merrows waved to Nessia.\n"
                   "Nessas of the world. Merrowed paths.\n")
        warns = sorted(d.split(" names ")[1] for lv, c, d in kb_check.run(self.tmp, [novel])
                       if (lv, c) == ("warn", "leak"))
        self.assertEqual(warns, ["'Merrows', near 'Merrow' from tide",
                                 "'Nessia', near 'Nessa' from tide"])
        for a, b in (("Ness", "Nessa"), ("Varrow", "Harrow"), ("Barrow", "Harrow")):
            self.assertTrue(kb_check._near(a, b), (a, b))
        for a, b in (("Pell", "Bell"), ("Nessa", "Nessa"), ("Ash", "Ashe"), ("Tovi", "Tovianne")):
            self.assertFalse(kb_check._near(a, b), (a, b))

    def test_the_sweep_from_a_noun_list(self):
        nouns = self.write("study/names.txt", "# a studied book\nOrlan Vey\nthe Greywater\n\n")
        self.assertEqual(kb_check.file_nouns(nouns), (["Greywater", "Orlan", "Orlan Vey",
                                                       "the Greywater"], []))
        self.assertEqual(kb_check.file_nouns(nouns, {"orlan"}),
                         (["Greywater", "Orlan Vey", "the Greywater"], ["Orlan"]))
        self.write("kb/writer/a.md", DOC + "\nOrlan crossed the bridge.\nThe Greywaters ran.\n")
        found = [(lv, d.split(" names ")[1]) for lv, c, d
                 in kb_check.run(self.tmp, noun_files=[nouns]) if c == "leak"]
        self.assertEqual(sorted(found), [("defect", "'Orlan', from %s" % nouns),
                                         ("warn", "'Greywaters', near 'Greywater' from %s"
                                          % nouns)])

    def test_a_noun_list_word_the_kb_uses_in_lower_case_is_mid_sentence_only(self):
        nouns = self.write("study/names.txt", "Grand Plan\nOrlan Vey\n")
        self.write("kb/writer/a.md", DOC + "\nPlan the chapter; the plan comes first.\n"
                   "Orlan left, and then Plan B.\n")
        found = sorted(d.split(" names ")[1] for lv, c, d
                       in kb_check.run(self.tmp, noun_files=[nouns]) if lv == "defect")
        self.assertEqual(found, ["'Orlan', from %s" % nouns, "'Plan', from %s" % nouns])

    def test_counts(self):
        rows = dict((p, (w, n)) for p, w, n in kb_check.counts(self.kb))
        self.assertEqual(rows["kb/writer/a.md"], (8, 2))   # "#" counts as a word

    def test_the_repository_is_clean(self):
        found = [f for f in kb_check.run() if f[0] in ("defect", "warn")]
        self.assertEqual(found, [])


if __name__ == "__main__":
    unittest.main()
