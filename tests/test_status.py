"""tools/status.py - where a novel stands, read from its files."""
import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from novel_fixture import NovelFixture  # noqa: E402
import export_prose  # noqa: E402
import status  # noqa: E402

PLAN = """# Chapters

| # | title | pov | temp | hook | event | threads |
|---|---|---|---|---|---|---|
| 1 | The Tally | Nessa Vane | quiet | question | Nessa finds the Harrow boy's name on the tally | ~T1 ~T2 |
| 2 | The Bar | Nessa Vane | tense | threat | Nessa rows the boy out past the bar | ^T2 ~T3 |
"""

REPORT = """# Report

## Would I click next?
4 — I want to know who chalked the name.
"""


def lines(fx, reading=None):
    return status.report(fx.novel(), reading or os.path.join(fx.tmp, "reading"))


def line(out, prefix):
    return next((l for l in out if l.startswith(prefix)), "")


class ReportTest(unittest.TestCase):
    def test_a_novel_with_one_chapter(self):
        with NovelFixture() as fx:
            fx.write("plan/chapters.md", PLAN)
            fx.chapter(1, title="The Tally")
            fx.state()
            out = lines(fx)
            self.assertIn('1 accepted · last ch 1 "The Tally"', line(out, "chapters"))
            self.assertIn('ch 2 "The Bar": Nessa rows the boy out', line(out, "next"))
            self.assertIn("1 row(s) ahead", line(out, "plan"))
            # A1 is only partly landed and was due by ch 1; F2 is due next.
            self.assertIn("1 past due and not landed · due ch 2: F2", line(out, "ledger"))
            self.assertTrue(any(l.strip().startswith("A1 due ch 1, partly ch1") for l in out))
            self.assertIn("1 open · 0 past their chapter", line(out, "promises"))
            self.assertIn("2 open · 1 planned", line(out, "threads"))
            self.assertTrue(line(out, "state").endswith("clean"), out)

    def test_no_chapters_yet(self):
        with NovelFixture() as fx:
            fx.write("plan/chapters.md", PLAN)
            out = lines(fx)
            self.assertIn("none accepted yet", line(out, "chapters"))
            self.assertIn('ch 1 "The Tally"', line(out, "next"))
            self.assertEqual(line(out, "reader"), "")

    def test_the_plan_has_run_out(self):
        with NovelFixture() as fx:
            fx.chapter(1)
            fx.chapter(2)
            fx.state(blocks=(1, 2))
            self.assertIn("ch 3 has no plan row", line(lines(fx), "next"))


class ClickNextTest(unittest.TestCase):
    def test_from_the_last_rounds_report(self):
        with NovelFixture() as fx:
            fx.chapter(1)
            fx.state()
            fx.write("work/ch0001/notes-r0.md", "# Notes\nverdict REVISE | owed 1/2 | click-next 3\n")
            fx.write("work/ch0001/notes-r1.md", "# Notes\nverdict ACCEPT | owed 2/2 | click-next 4\n")
            reading = os.path.join(fx.tmp, "reading")
            rid = export_prose.novel_id(fx.root)
            os.makedirs(os.path.join(reading, "%s-ch01-r1" % rid))
            with open(os.path.join(reading, "%s-ch01-r1" % rid, "report.md"), "w") as fh:
                fh.write(REPORT)
            self.assertEqual(line(lines(fx, reading), "reader"),
                             "reader    ch 1 r1: 4 — I want to know who chalked the name.")

    def test_from_the_notes_when_no_report_was_filed(self):
        with NovelFixture() as fx:
            fx.chapter(1)
            fx.state()
            fx.write("work/ch0001/notes-r0.md", "# Notes\nverdict ACCEPT | owed 2/2 | click-next 5\n")
            self.assertIn("ch 1 r0: 5 (from the notes", line(lines(fx), "reader"))


class DebtTest(unittest.TestCase):
    def test_overdue_and_beyond_the_plan(self):
        with NovelFixture() as fx:
            fx.write("plan/chapters.md", PLAN)
            fx.chapter(1)
            fx.state()
            out = status.debt(fx.novel())
            self.assertTrue(any(l.startswith("overdue  A1 due ch 1") for l in out), out)
            self.assertTrue(any(l.startswith("beyond   R1 due ch 6") for l in out), out)
            self.assertFalse(any("F2" in l for l in out), out)

    def test_a_payoff_in_a_later_arc_is_no_chapter(self):
        with NovelFixture() as fx:
            fx.write("plan/chapters.md", PLAN)
            fx.write("plan/reader-ledger.md", "# Reader ledger\n\n## Promises\n"
                     "| id | what the page promises | made in ch | paid by ch | status |\n"
                     "|---|---|---|---|---|\n"
                     "| R4 | the melt | 1 | arc 2 (planned with arc 2) | owed |\n"
                     "| R5 | a voice back | 1 | late in the book | owed |\n")
            fx.chapter(1)
            fx.chapter(2)
            fx.state(blocks=(1, 2))
            out = lines(fx)
            self.assertIn("2 open · 0 past their chapter", line(out, "promises"))
            self.assertTrue(any("R4 made ch 1, paid by arc 2" in l for l in out), out)
            debt = status.debt(fx.novel())
            self.assertTrue(any(l.startswith('beyond   R4 due "arc 2') for l in debt), debt)
            self.assertTrue(any(l.startswith('beyond   R5 due "late in the book"') for l in debt))

    def test_a_moved_row_is_due_at_its_new_chapter(self):
        # A row the planner moved (`moved to chN`, with the reason) is due at N, not at its old
        # chapter: /write and /plan must not send it back as overdue (run #7, F2).
        with NovelFixture() as fx:
            fx.write("plan/chapters.md", PLAN)
            fx.write("plan/reader-ledger.md", "# Reader ledger\n\n## Facts\n"
                     "| id | fact, in plain words | due by ch | how it lands | status |\n"
                     "|---|---|---|---|---|\n"
                     "| P3 | the guild sells the plot | 1 | the chalked gatepost | "
                     "moved to ch2 — the sale did not register |\n")
            fx.chapter(1)
            fx.state()
            self.assertTrue(status.debt(fx.novel())[0].startswith("clean"), status.debt(fx.novel()))
            self.assertIn("0 past due and not landed · due ch 2: P3", line(lines(fx), "ledger"))

    def test_clean(self):
        with NovelFixture() as fx:
            fx.write("plan/chapters.md", PLAN)
            fx.write("plan/reader-ledger.md", "# Reader ledger\n\n## Facts\n"
                     "| id | fact, in plain words | due by ch | how it lands | status |\n"
                     "|---|---|---|---|---|\n| F2 | the bar is dry | 2 | she walks it | owed |\n")
            self.assertTrue(status.debt(fx.novel())[0].startswith("clean"))


if __name__ == "__main__":
    unittest.main()
