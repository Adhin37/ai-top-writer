"""tools/state_check.py - the state files against the chapters, the plan and each other.

Adapted from skilled-writer's tests/test_state.py, for the new block and thread formats.
"""
import contextlib
import io
import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from novel_fixture import THREADS, NovelFixture  # noqa: E402
import state_check  # noqa: E402


def findings(fx):
    return [(lv, check, detail) for lv, check, detail in state_check.run(fx.novel()).found]


def has(found, level, text):
    return any(lv == level and text in d for lv, _c, d in found)


class CleanTest(unittest.TestCase):
    def test_a_consistent_novel_is_clean(self):
        with NovelFixture() as fx:
            fx.chapter(1)
            fx.state()
            lines = state_check.run(fx.novel()).lines()
            self.assertTrue(lines[-1].endswith("clean"), lines)

    def test_state_survives_a_novel_with_no_chapters(self):
        with NovelFixture() as fx:
            self.assertTrue(state_check.run(fx.novel()).lines())


class BlocksTest(unittest.TestCase):
    def test_a_chapter_without_a_block(self):
        with NovelFixture() as fx:
            fx.chapter(1)
            fx.chapter(2)
            fx.state(blocks=(1,))
            self.assertTrue(has(findings(fx), "defect", "chapter 2 is accepted and has no block"))

    def test_blocks_out_of_order_and_doubled(self):
        with NovelFixture() as fx:
            fx.chapter(1)
            fx.chapter(2)
            fx.state(blocks=(2, 1, 1))
            got = findings(fx)
            self.assertTrue(has(got, "defect", "C0001 is written after C0002"))
            self.assertTrue(has(got, "defect", "two blocks for chapter 1"))

    def test_missing_keys_unknown_keys_and_words(self):
        with NovelFixture() as fx:
            fx.chapter(1)
            fx.state(words=999)
            text = fx.novel().text("state", "continuity.md")
            fx.write("state/continuity.md", text.replace("hook  ", "mood  "))
            got = findings(fx)
            self.assertTrue(has(got, "defect", "C0001 has no `hook` line"))
            self.assertTrue(has(got, "warn", "`mood` is not a block key"))
            self.assertTrue(has(got, "warn", "says words 999"))


class ThreadsTest(unittest.TestCase):
    def test_a_block_thread_with_no_row_is_a_defect(self):
        with NovelFixture() as fx:
            fx.chapter(1)
            fx.state(thr="~T1 ~T2 ~T9")
            self.assertTrue(has(findings(fx), "defect", "C0001 uses T9"))

    def test_a_plan_row_thread_with_no_row(self):
        with NovelFixture() as fx:
            fx.chapter(1)
            fx.state(threads=THREADS.replace("| T3 | Quell knows she went out | — | — | — | planned |\n", ""))
            self.assertTrue(has(findings(fx), "warn", "plan row 2 names T3"))

    def test_a_planned_thread_a_chapter_opened_and_a_stale_last(self):
        with NovelFixture() as fx:
            fx.chapter(1)
            fx.state(thr="~T1 ~T2 ~T3",
                     threads=THREADS.replace("| T1 | the tally's early date | R1 | 1 | 1 |",
                                             "| T1 | the tally's early date | R1 | 1 | 0 |"))
            got = findings(fx)
            self.assertTrue(has(got, "warn", "T3 is `planned`, and ch 1 operated on it"))
            self.assertTrue(has(got, "warn", "T1 says last ch 0"))

    def test_a_paid_thread_whose_row_is_still_open(self):
        with NovelFixture() as fx:
            fx.chapter(1)
            fx.state(thr="~T1 vT2")
            self.assertTrue(has(findings(fx), "warn", "pays T2"))

    def test_a_planned_thread_the_chapter_skipped_warns_and_an_extra_is_a_note(self):
        with NovelFixture() as fx:
            fx.chapter(1)
            fx.state(thr="~T1 ~T3",
                     threads=THREADS.replace("| — | — | planned |", "| 1 | 1 | open |"))
            got = findings(fx)
            self.assertTrue(has(got, "warn", "does not touch T2"))
            self.assertTrue(has(got, "note", "touches T3, which row 1 does not plan"))


class ScenesLedgerTest(unittest.TestCase):
    def test_scene_log_and_timeline_cover_every_block(self):
        with NovelFixture() as fx:
            fx.chapter(1)
            fx.state(scenes="# Scenes\n\n| ch | scene | who | where | tempo | two-hander |\n"
                            "|---|---|---|---|---|---|\n| 2 | 1 | x | y | quiet | maybe |\n",
                     timeline="# Timeline\n")
            got = findings(fx)
            self.assertTrue(has(got, "warn", "ch 1 has a block and no scene rows"))
            self.assertTrue(has(got, "warn", "two-hander is `maybe`"))
            self.assertTrue(has(got, "warn", "ch 1 has a block and no timeline row"))

    def test_ledger_status_forms(self):
        with NovelFixture() as fx:
            fx.chapter(1)
            fx.state()
            ledger = fx.novel().text("plan", "reader-ledger.md")
            fx.write("plan/reader-ledger.md", ledger.replace("| landed ch1 |", "| done |")
                     .replace("| 2 | she walks it | owed |", "| 1 | she walks it | owed |"))
            got = findings(fx)
            self.assertTrue(has(got, "warn", "P1 status `done`"))
            self.assertTrue(has(got, "note", "F2 is still owed; due by ch 1"))

    def test_last_blocks_prints_them_as_written(self):
        with NovelFixture() as fx:
            fx.chapter(1)
            fx.chapter(2)
            fx.state(blocks=(1, 2))
            buf = io.StringIO()
            with contextlib.redirect_stdout(buf):
                state_check.main([fx.root, "--last", "1"])
            self.assertTrue(buf.getvalue().startswith("=C0002= day 2"))
            self.assertNotIn("=C0001=", buf.getvalue())


if __name__ == "__main__":
    unittest.main()
