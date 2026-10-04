"""tools/wire.py - the wire format's status lines, hand-backs, notes and facts files."""
import contextlib
import io
import os
import sys
import tempfile
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "tools"))

import wire  # noqa: E402

NOTES = """# Notes — chapter 3, round 0
verdict REVISE | owed 4/5 | event yes | ending yes | click-next 4

## Owed
P1 partly "some kind of tide festival (guess)" — the rowing-out never reaches the retell
P2 stated "she has to row them out before dawn"
R5 missing

## Notes
N1 Ebb never explained
where "Nessa had four hours until the Long Ebb, and the Harrow boy was still on the tally."
ev    P1 missing · retell "some kind of tide festival (guess)" · guessed: Long Ebb, tally
eff   the reader didn't know the boy was dead, so the last scene read as a family quarrel, not grief
dir   the rule in plain words where the tally is first named

## Keep
"His mother had never once come down to the water to help." — the reader's best moment

## For the planner
the reader thinks the harbourmaster is her father (guess) · place him in ch 4

## Unresolved
"""

FACTS = """# Facts — chapter 3, round 1
learns    P1 "every year the sea gives back its drowned" · P2 "rowed out past the bar"
new       the harbour bar is open two hours either side of low water
couldn't  none
notes     N1 done "the sea gives back what it took, once a year" · N2 stet: the walk sets up the cold
choices   the tally is chalked on the boathouse door
"""


def levels(found):
    return [f[0] for f in found]


class StatusTest(unittest.TestCase):
    def test_each_role_line_parses_clean(self):
        for line in (
                "DRAFT READY w/draft-r0.md | facts w/facts-r0.md | new 12 | stets 0 | couldn't 0",
                "NOTES READY w/notes-r0.md | REVISE | notes 2 | owed 4/5",
                "PLANNER DONE beats | w/beats.md, plan/reader-ledger.md | gaps 0 | changed 1",
                "POLISHED ch/0003.md | changes 14 (\"X, not Y\" 9→3 · 2 thought tags) | left 1",
                "PLANNER ASKS w/init/round-2.md | round 2 | questions 6",
                "SAMPLES READY w/init/style-samples.md | samples 3"):
            with self.subTest(line=line):
                verb, head, fields, found = wire.parse_status(line)
                self.assertTrue(verb)
                self.assertEqual(found, [])
        _, _, fields, _ = wire.parse_status(
            "NOTES READY w/notes-r0.md | ACCEPT | notes 0 | owed 6/6")
        self.assertEqual((fields["verdict"], fields["notes"], fields["owed"]),
                         ("ACCEPT", "0", "6/6"))
        _, _, fields, _ = wire.parse_status(
            "PLANNER DONE beats | w/beats.md | gaps 1 | changed 0")
        self.assertEqual(fields["files"], "w/beats.md")

    def test_the_canon_researchers_hand_back(self):
        text = ("CANON DONE novels/x/bible/canon.md | facts 41 | sources 12 | unsure 2 | blocked 1\n"
                "unsure   Ilse's age: canon never gives it; is 54 right?\n"
                "blocked  https://w.example/wiki/Ilse · her age\n")
        self.assertEqual(wire.check_handback(text), [])
        self.assertIn("defect", levels(wire.parse_status(
            "CANON DONE novels/x/bible/canon.md | facts 41 | sources 12")[3]))

    def test_canon_gaps_are_the_planners_gap_canon_lines(self):
        text = ("PLANNER DONE beats | w/beats.md | gaps 2 | changed 0\n"
                "gap canon does the deck chief have children; names and ages at the start\n"
                "gap the bible gives no distance to the quay\n")
        self.assertEqual(wire.canon_gaps(text), [
            "gap canon does the deck chief have children; names and ages at the start"])
        self.assertEqual(wire.check_handback(text), [])

    def test_a_planner_line_with_no_files_and_init_parse_clean(self):
        _, _, fields, found = wire.parse_status("PLANNER DONE fold | gaps 0 | changed 0")
        self.assertEqual((found, fields.get("files"), fields["gaps"]), ([], None, "0"))
        self.assertEqual(wire.parse_status("PLANNER DONE init")[3], [])
        self.assertIn("defect", levels(wire.parse_status("PLANNER DONE plan")[3]))

    def test_old_and_broken_lines_are_defects(self):
        verb, _, _, found = wire.parse_status("NOTES READY — w/notes-r0.md — REVISE — 2 notes")
        self.assertEqual(verb, "NOTES READY")
        self.assertIn("defect", levels(found))
        verb, _, _, found = wire.parse_status("Chapter 1 is done, see the notes.")
        self.assertIsNone(verb)
        _, _, _, found = wire.parse_status("DRAFT READY w/draft-r0.md | facts w/facts-r0.md")
        self.assertEqual(sum(1 for f in found if f[0] == "defect"), 3)
        _, _, _, found = wire.parse_status("PLANNER ASKS w/init/round-2.md | round 2")
        self.assertIn("defect", levels(found))


class HandbackTest(unittest.TestCase):
    def test_preamble_is_a_defect(self):
        found = wire.check_handback("The verdict is REVISE with two notes.\n\n"
                                    "NOTES READY w/n.md | REVISE | notes 2 | owed 4/5")
        self.assertEqual(levels(found), ["defect"])

    def test_role_lines_may_follow_but_prose_may_not(self):
        self.assertEqual(wire.check_handback(
            "PLANNER DONE beats | w/beats.md | gaps 1 | changed 0\n"
            "gap      the bible never says how far the bar is from the quay"), [])
        found = wire.check_handback("NOTES READY w/n.md | ACCEPT | notes 0 | owed 5/5\n"
                                    "**Why it passes**\n- all five owed facts landed")
        self.assertEqual(levels(found), ["warn"])

    def test_no_status_line(self):
        self.assertEqual(levels(wire.check_handback("done")), ["defect"])


class NotesTest(unittest.TestCase):
    def test_wire_notes_have_no_defect_or_warning(self):
        found = wire.check_notes(NOTES)
        self.assertEqual([f for f in found if f[0] != "note"], [])
        self.assertIn(("note", "words", "Keep: 17"), found)

    def test_a_beat_line_under_owed_is_not_a_ledger_row(self):
        text = NOTES.replace('R5 missing\n', 'R5 missing\nbeat currency stated "a mark is 20 tallies"\n')
        self.assertEqual([f for f in wire.check_notes(text) if f[0] != "note"], [])

    def test_an_accept_with_none_under_notes_is_clean(self):
        # The story editor writes `none` under `## Notes` when it accepts (run #7, F3).
        start, end = NOTES.index("## Notes"), NOTES.index("## Keep")
        text = (NOTES[:start] + "## Notes\nnone\n\n" + NOTES[end:]).replace("REVISE", "ACCEPT")
        self.assertEqual([f for f in wire.check_notes(text) if f[0] != "note"], [])

    def test_a_note_needs_where_ev_and_eff(self):
        found = wire.check_notes(NOTES.replace("eff   the reader didn't", "the reader didn't"))
        self.assertIn(("defect", "note", "N1 has no `eff`"), found)

    def test_too_many_notes(self):
        extra = "".join("N%d x\nwhere \"a\"\nev    b\neff   c\n" % n for n in range(2, 7))
        found = wire.check_notes(NOTES.replace("## Keep", extra + "\n## Keep"))
        self.assertIn(("defect", "notes", "6 notes; at most 5"), found)

    def test_a_long_quote_is_a_note(self):
        long = " ".join(["word"] * 30)
        found = wire.check_notes(NOTES.replace('where "Nessa', 'where "%s Nessa' % long))
        self.assertTrue(any(f[:2] == ("note", "quote") for f in found))

    def test_the_old_prose_form_is_flagged(self):
        old = ("# Notes — chapter 1, round 0\n\nverdict: REVISE\n\n"
               "## What the chapter owed, and what landed\n| id | owed |\n\n## Notes\n"
               "### N1 — x\nwhere: \"a\"\nevidence: b\neffect: c\n\n## Keep\n- \"q\" — why\n")
        self.assertIn("defect", levels(wire.check_notes(old)))


class FactsTest(unittest.TestCase):
    def test_wire_facts_are_clean(self):
        found = wire.check_facts(FACTS)
        self.assertEqual([f for f in found if f[0] != "note"], [])
        self.assertIn("new facts: 1", found[-1][2])

    def test_unknown_keys_and_too_many_choices(self):
        found = wire.check_facts(FACTS + "staging  I moved the fight\n" + "choices x\n" * 3)
        self.assertIn(("warn", "facts", "4 choices; at most 3"), found)
        self.assertTrue(any(f[1] == "facts" and "unknown key" in f[2] for f in found))


CONTINUITY = """# Continuity — chapter 4, round 0
lint  novels/tidewater/work/ch0004/lint-r0.txt · 1 defect · 0 warn
checked  lexicon, world.md §Places; C0001–C0003
F1 know    "Nessa knew Quell had signed the Harrow tally himself" | C0003 kno: "Nessa+ the tally was signed" | nothing on the page tells her who signed it
F2 travel  "By noon she was at the salt pans" | bible/world.md §Places: "a day's walk north" | she left at dawn the same day
"""

FOLD = """# Fold — chapter 3
new    the bar can be crossed on foot for an hour at the lowest ebb | bible/world.md | "the bar was dry for the length of a prayer"
stale  "the Long Ebb — first appears ch 4" | bible/lexicon.md | on the page from ch 1
"""


class NewRolesTest(unittest.TestCase):
    def test_the_new_status_lines_parse(self):
        for line in (
                "CONTINUITY READY w/continuity-r0.md | findings 2 | lint w/lint-r0.txt",
                "CLERK DONE ch/0003-x.md | fold w/fold.md | bible 2 | ledger 3 | check clean",
                "PLANNER DONE fold | bible/world.md, bible/lexicon.md | gaps 0 | changed 1"):
            with self.subTest(line=line):
                self.assertEqual(wire.parse_status(line)[3], [])
        _, _, _, found = wire.parse_status("CLERK DONE ch/0003-x.md | fold w/fold.md | bible 2")
        self.assertEqual(sum(1 for f in found if f[0] == "defect"), 2)

    def test_the_line_editor_may_add_across_lines(self):
        self.assertEqual(wire.check_handback(
            "POLISHED ch/0003.md | changes 4 (x) | left 1\n"
            "left    the ledger scene's triad, Ruck's own cadence\n"
            "across  \"The stone held.\" ch 1, ch 3 — thinned here"), [])

    def test_a_continuity_file(self):
        found = wire.check_continuity(CONTINUITY)
        self.assertEqual([f for f in found if f[0] != "note"], [])
        self.assertIn("findings: 2", found[-1][2])
        self.assertEqual([f for f in wire.check_continuity("# C\nlint x · 0 defect\nnone\n")
                          if f[0] != "note"], [])
        bad = wire.check_continuity(CONTINUITY.replace(' | she left at dawn the same day', '')
                                    .replace("F1 know ", "F1 vibe "))
        self.assertIn("defect", levels(bad))
        self.assertTrue(any("`vibe`" in f[2] for f in bad))

    def test_a_fold_file(self):
        found = wire.check_fold(FOLD)
        self.assertEqual([f for f in found if f[0] != "note"], [])
        self.assertIn("new: 1, stale: 1", found[-1][2])
        bad = wire.check_fold("new  a fact with nothing else\nbible something\n")
        self.assertIn("defect", levels(bad))
        self.assertIn("warn", levels(bad))


class CliTest(unittest.TestCase):
    def test_check_picks_the_kind_by_file_name(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "notes-r0.md")
            with open(path, "w", encoding="utf-8") as fh:
                fh.write(NOTES)
            buf = io.StringIO()
            with contextlib.redirect_stdout(buf):
                self.assertEqual(wire.main(["check", path]), 0)
            self.assertNotIn("defect", buf.getvalue())
            with contextlib.redirect_stderr(io.StringIO()):
                self.assertEqual(wire.main(["check", os.path.join(tmp, "missing.md")]), 1)


if __name__ == "__main__":
    unittest.main()
