"""The ledger's Pressure rows (the lead's lever, the clock): read by lib/novel.py, flagged by
status.py, checked by state_check.py, cut by bench.py, warned on by scaffold.py."""
import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from novel_fixture import LEDGER, NovelFixture  # noqa: E402
import bench  # noqa: E402
import room  # noqa: E402
import state_check  # noqa: E402
import status  # noqa: E402

PRESSURE = """
## Pressure
| id | what the reader tracks | by chapter |
|---|---|---|
| L1 | Nessa's lever: what she can do about the Harrow boy | %s |
| C1 | the clock: the bar dries at the lowest ebb | %s |
"""


def ledger(lever, clock):
    return LEDGER + PRESSURE % (lever, clock)


def flags(fx):
    return status.pressure_flags(fx.novel())


class PressureTest(unittest.TestCase):
    def test_the_trail_is_read_step_by_step(self):
        with NovelFixture() as fx:
            fx.write("plan/reader-ledger.md", ledger(
                "ch1 set — she reads the tally · ch2 grew — she rows him out", "ch1 set — dawn"))
            rows = fx.novel().pressure()
            self.assertEqual([r[0] for r in rows], ["L1", "C1"])
            self.assertEqual(rows[0][2], [(1, "set", "she reads the tally"),
                                          (2, "grew", "she rows him out")])

    def test_a_ledger_without_pressure_says_so(self):
        with NovelFixture() as fx:
            self.assertEqual(fx.novel().pressure(), [])
            self.assertTrue(status.pressure(fx.novel())[0].startswith("none"))
            self.assertEqual(flags(fx), [])
            self.assertTrue(any(l.startswith("pressure no L1") for l in status.debt(fx.novel())))

    def test_growing_and_nearer_raise_no_flag(self):
        with NovelFixture() as fx:
            fx.chapter(1)
            fx.chapter(2)
            fx.write("plan/reader-ledger.md", ledger(
                "ch1 set — a · ch2 grew — b", "ch1 set — c · ch2 nearer — d"))
            self.assertEqual(flags(fx), [])

    def test_shrank_later_and_held_twice_are_flagged(self):
        with NovelFixture() as fx:
            fx.chapter(1)
            fx.chapter(2)
            fx.chapter(3)
            fx.write("plan/reader-ledger.md", ledger(
                "ch1 set — a · ch2 held — b · ch3 held — c", "ch1 set — d · ch2 nearer · ch3 later"))
            out = flags(fx)
            self.assertIn("held two chapters running", out[0])
            self.assertIn("later at ch 3", out[1])
            fx.write("plan/reader-ledger.md", ledger("ch1 set · ch2 grew · ch3 shrank",
                                                     "ch1 set · ch2 held · ch3 nearer"))
            self.assertEqual(len(flags(fx)), 1)
            self.assertIn("shrank at ch 3", flags(fx)[0])

    def test_a_missing_step_for_the_last_chapter_is_flagged_and_checked(self):
        with NovelFixture() as fx:
            fx.chapter(1)
            fx.chapter(2)
            fx.state(blocks=(1, 2))
            fx.write("plan/reader-ledger.md", ledger("ch1 set — a", "ch1 set · ch2 nearer · ch3 nearer"))
            self.assertIn("no step for ch 2", flags(fx)[0])
            found = state_check.run(fx.novel()).lines()
            self.assertTrue(any("L1 has no step for ch 2" in l for l in found), found)
            self.assertTrue(any("C1 has a step for ch 3, past" in l for l in found), found)

    def test_a_word_from_the_other_row_is_checked(self):
        with NovelFixture() as fx:
            fx.chapter(1)
            fx.state()
            fx.write("plan/reader-ledger.md", ledger("ch1 nearer", "ch1 grew"))
            found = state_check.run(fx.novel()).lines()
            self.assertTrue(any("L1 ch1 `nearer`" in l for l in found), found)
            self.assertTrue(any("C1 ch1 `grew`" in l for l in found), found)

    def test_the_planner_dispatch_carries_the_flags(self):
        with NovelFixture() as fx:
            fx.chapter(1)
            fx.chapter(2)
            fx.write("plan/reader-ledger.md", ledger("ch1 set · ch2 shrank", "ch1 set · ch2 nearer"))
            note = room.pressure_note(fx.novel())
            self.assertTrue(note.startswith(" Pressure: L1"), note)
            self.assertNotIn("C1", note)

    def test_a_frozen_ledger_drops_steps_from_the_cut_on(self):
        text = ledger("ch1 set — a · ch2 grew — b · ch3 held — c", "ch1 set — d · ch2 nearer — e")
        cut = bench._cut_ledger(text, 2)
        self.assertIn("| ch1 set — a |", cut)
        self.assertIn("| ch1 set — d |", cut)
        self.assertNotIn("ch2", cut)
        self.assertIn("| landed ch1 |", cut)


if __name__ == "__main__":
    unittest.main()
