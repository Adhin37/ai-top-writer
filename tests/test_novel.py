"""tools/lib/novel.py - a novel's files read as data: config, plan, ledger, blocks, cast, lexicon."""
import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from novel_fixture import NovelFixture  # noqa: E402
from lib import novel as novel_mod  # noqa: E402


class NovelTest(unittest.TestCase):
    def test_config_and_channels(self):
        with NovelFixture() as fx:
            nov = fx.novel()
            self.assertEqual(nov.slug, "long-ebb")
            self.assertEqual(nov.get("mc.name"), "Nessa Vane")
            self.assertIn("“", nov.channels.speech_open)

    def test_plan_rows_and_thread_refs(self):
        with NovelFixture() as fx:
            row = fx.novel().plan_row(2)
            self.assertEqual(row.get("title"), "The Bar")
            self.assertEqual(novel_mod.thread_refs(row.get("threads")), [("^", "T2"), ("~", "T3")])
            self.assertEqual(novel_mod.thread_refs("vT5 xT6 T7 (T8) AT9"),
                             [("v", "T5"), ("x", "T6"), ("", "T7"), ("", "T8")])

    def test_the_ledger_is_found_by_its_columns(self):
        with NovelFixture() as fx:
            ledger = fx.novel().ledger()
            self.assertEqual([r.first() for r in ledger["facts"]], ["P1", "F2"])
            self.assertEqual(ledger["faces"][0].get("status")[:9], "partly ch")
            self.assertEqual(ledger["promises"][0].first(), "R1")

    def test_blocks(self):
        with NovelFixture() as fx:
            fx.chapter(1)
            fx.state(blocks=(1,))
            fx.write("state/continuity.md", fx.novel().text("state", "continuity.md")
                     + "Stray line, no key\n")
            nov = fx.novel()
            b = nov.block(1)
            self.assertEqual(b.field("day"), "1, dusk")
            self.assertEqual(b.words, nov.chapter(1).words)
            self.assertEqual(b.get("ev")[:5], "Nessa")
            self.assertEqual(b.threads(), [("~", "T1"), ("~", "T2")])
            self.assertEqual(len(b.stray), 1)

    def test_speakers_come_from_the_matrix_and_the_roster_not_the_comment(self):
        with NovelFixture() as fx:
            names = fx.novel().speakers()
            self.assertEqual(names, ["Nessa Vane", "Harbourmaster Quell", "Tam Orrin"])

    def test_lexicon(self):
        with NovelFixture() as fx:
            nov = fx.novel()
            variants = dict(nov.lexicon_variants())
            self.assertEqual(variants.get("Nesa"), "Nessa Vane")
            self.assertEqual(variants.get("Harbormaster"), "Harbourmaster Quell")
            self.assertNotIn("Vane's", variants)   # a word of the canonical name, stripped of 's
            self.assertEqual(nov.banned_words(), ["destiny", "ancient evil"])
            self.assertTrue(nov.number_style().startswith("spell out one through twenty"))

    def test_novel_of_a_draft(self):
        with NovelFixture() as fx:
            draft = fx.write("work/ch0002/draft-r0.md", "x")
            self.assertEqual(novel_mod.novel_of(draft).root, fx.root)


if __name__ == "__main__":
    unittest.main()
