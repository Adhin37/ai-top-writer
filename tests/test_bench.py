"""tools/bench.py - frozen rounds, blind pairs, agreement."""
import contextlib
import io
import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from novel_fixture import NovelFixture  # noqa: E402
import bench  # noqa: E402
import export_prose  # noqa: E402

DRAFT = "---\nnumber: %d\ntitle: \"The Bar\"\n---\n\n%s\n"
NOTES = """# Notes — chapter 2, round %d
verdict %s | owed 1/1 | event yes | ending yes | click-next 4

## Owed
F1 stated "the bar"

## Notes
%s
## Keep
"She rowed."
"""
NOTE_A = """N1 the boy appears from nowhere
where "Tam shrugged at the door and said nothing"
ev    retell "who is Tam?"
eff   the reader stops
N2 the tide is wrong
where "the tide was out by noon"
ev    timeline day 2
eff   a careful reader trips
"""
NOTE_B = """N1 Tam is a stranger to the reader
where "Tam shrugged at the door and said nothing at all"
ev    retell "a boy"
eff   the reader stops
"""
CONT = """# Continuity — chapter 2, round 0
lint     x · 0 defect · 0 warn
checked  lexicon
%s"""


def read(path):
    with open(path, encoding="utf-8") as fh:
        return fh.read()


class BenchTest(unittest.TestCase):
    def setUp(self):
        self.fx = NovelFixture().__enter__()
        self.root = self.fx.tmp
        self.cwd = os.getcwd()
        os.chdir(self.root)
        fx = self.fx
        fx.chapter(1)
        fx.chapter(2)
        fx.state(blocks=(1, 2))
        fx.write("plan/reader-ledger.md", "# Ledger\n\n| id | what | due | carrier | status |\n"
                 "|---|---|---|---|---|\n| F1 | the bar | 1 | x | landed ch1 |\n"
                 "| F2 | the boy | 2 | y | landed ch2 |\n| F3 | the sale | 2 | z | partly ch2 — "
                 "skimmed |\n")
        w = "work/ch0002/"
        fx.write(w + "beats.md", "# Beats — chapter 2, \"The Bar\"\n")
        fx.write(w + "draft-r0.md", DRAFT % (2, "She rowed.\n\nTam shrugged.\n\nThe tide."))
        fx.write(w + "draft-r1.md", DRAFT % (2, "She rowed.\n\nTam, her cousin, shrugged.\n\n"
                                                "The tide."))
        for k, verdict, notes in ((0, "REVISE", NOTE_A), (1, "ACCEPT", "none\n")):
            fx.write(w + "notes-r%d.md" % k, NOTES % (k, verdict, notes))
            fx.write(w + "continuity-r%d.md" % k, CONT % ('F1 time "the tide was out by noon" | '
                                                         'timeline: "day 2" | early\n'))
            fx.write(w + "lint-r%d.txt" % k, "")
            fx.write(w + "facts-r%d.md" % k, "learns x\n")
        fx.write(w + "fold.md", "# Fold\n")
        self.id = export_prose.novel_id(fx.root)
        for k in (0, 1):
            fx.write("../../reading/%s/ch02-r%d/report.md" % (self.id, k), "report %d" % k)
            fx.write("../../reading/%s/ch02-r%d/notes.md" % (self.id, k), "memory %d" % k)
        fx.write("work/ch0001/notes-r0.md", NOTES % (0, "ACCEPT", "none\n"))
        fx.write("../../reading/%s/ch01-r0/notes.md" % self.id, "memory after ch1")

    def tearDown(self):
        os.chdir(self.cwd)
        self.fx.__exit__(None, None, None)

    def run_bench(self, *args):
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            code = bench.main(["--root", self.root] + list(args))
        return code, out.getvalue()

    def p(self, *parts):
        return os.path.join(self.root, *parts)

    # ------------------------------------------------------------ rounds

    def test_rounds_reports_each_round_and_what_the_next_draft_changed(self):
        out = bench.rounds(self.fx.root)
        row0 = next(l for l in out.splitlines() if l.startswith("2   0"))
        self.assertIn("REVISE", row0)
        self.assertIn("1/3", row0)        # one paragraph of three rewritten in draft-r1
        self.assertRegex(row0, r"REVISE\s+2\s+4")
        row1 = next(l for l in out.splitlines() if l.startswith("2   1"))
        self.assertIn("ACCEPT", row1)

    # ------------------------------------------------------------ freeze

    def test_freeze_for_the_continuity_editor_removes_its_outputs_and_the_future(self):
        code, out = self.run_bench("freeze", "novels/long-ebb", "2", "0", "eff", "med",
                                   "--role", "continuity-editor", "--agent",
                                   "continuity-editor--medium")
        self.assertEqual(code, 0, out)
        copy = self.p("novels", "long-ebb--eff-med")
        self.assertIn('@ spawn continuity-editor--medium as "continuity-ch02"\nNovel: '
                      'novels/long-ebb--eff-med. Chapter 2, round 0. Draft: '
                      'novels/long-ebb--eff-med/work/ch0002/draft-r0.md.', out)
        work = sorted(os.listdir(os.path.join(copy, "work", "ch0002")))
        self.assertEqual(work, ["beats.md", "draft-r0.md", "facts-r0.md"])
        self.assertEqual([n for n in os.listdir(os.path.join(copy, "chapters"))],
                         ["0001-chapter-1.md"])
        self.assertNotIn("=C0002=", read(os.path.join(copy, "state", "continuity.md")))
        self.assertIn("=C0001=", read(os.path.join(copy, "state", "continuity.md")))
        ledger = read(os.path.join(copy, "plan", "reader-ledger.md"))
        self.assertIn("| landed ch1 |", ledger)
        self.assertNotIn("ch2", ledger)
        self.assertEqual(ledger.count("| owed |"), 2)
        self.assertIn('slug: "long-ebb--eff-med"', read(os.path.join(copy, "novel.md")))
        cid = export_prose.novel_id(copy)
        self.assertEqual(read(self.p("reading", cid, "shelf", "notes.md")), "memory after ch1")
        # the source is untouched
        self.assertTrue(os.path.isfile(self.fx.path("work", "ch0002", "continuity-r0.md")))

    def test_freeze_for_the_story_editor_keeps_the_round_and_its_report(self):
        code, out = self.run_bench("freeze", "novels/long-ebb", "2", "1", "eff", "base",
                                   "--role", "story-editor")
        self.assertEqual(code, 0, out)
        copy = self.p("novels", "long-ebb--eff-base")
        work = set(os.listdir(os.path.join(copy, "work", "ch0002")))
        self.assertIn("continuity-r1.md", work)
        self.assertIn("notes-r0.md", work)
        self.assertNotIn("notes-r1.md", work)
        self.assertNotIn("fold.md", work)
        cid = export_prose.novel_id(copy)
        self.assertEqual(read(self.p("reading", "%s/ch02-r1" % cid, "report.md")), "report 1")
        self.assertIn("@ spawn story-editor as", out)

    def test_freeze_refuses_an_existing_copy(self):
        self.run_bench("freeze", "novels/long-ebb", "2", "0", "e", "a", "--role", "clerk")
        code, _ = self.run_bench("freeze", "novels/long-ebb", "2", "0", "e", "a", "--role", "clerk")
        self.assertEqual(code, 1)

    def test_freeze_refuses_a_bad_name(self):
        for exp, arm in (("e", "../x"), ("e--f", "a"), ("E", "a")):
            with self.assertRaises(ValueError):
                bench.freeze("novels/long-ebb", 2, 0, exp, arm, "clerk", self.root)

    def test_cut_rows_reads_each_table_by_its_own_header(self):
        text = ("| ch | what |\n|---|---|\n| 1 | a |\n| 3 | b |\n\n"
                "| what | ch |\n|---|---|\n| c | 1 |\n| d | 3 |\n")
        cut = bench._cut_rows(text, "ch", 2)
        self.assertIn("| 1 | a |", cut)
        self.assertIn("| c | 1 |", cut)
        self.assertNotIn("| 3 | b |", cut)
        self.assertNotIn("| d | 3 |", cut)

    def test_freeze_for_the_planner_stands_before_the_beats(self):
        code, out = self.run_bench("freeze", "novels/long-ebb", "2", "0", "plan", "med",
                                   "--role", "planner", "--agent", "planner--medium")
        self.assertEqual(code, 0, out)
        copy = self.p("novels", "long-ebb--plan-med")
        self.assertEqual(os.listdir(os.path.join(copy, "work", "ch0002")), [])
        self.assertEqual(os.listdir(os.path.join(copy, "chapters")), ["0001-chapter-1.md"])
        self.assertNotIn("=C0002=", read(os.path.join(copy, "state", "continuity.md")))
        self.assertIn('@ spawn planner--medium as "planner-ch02"\nNovel: novels/long-ebb--plan-med. '
                      'Task: beats for chapter 2.', out)

    def test_freeze_continuity_after_round_0_replays_a_fresh_spawn(self):
        code, out = self.run_bench("freeze", "novels/long-ebb", "2", "1", "w", "a",
                                   "--role", "continuity-editor")
        self.assertEqual(code, 0, out)
        self.assertIn('@ spawn continuity-editor as "continuity-ch02"', out)
        self.assertNotIn("@ continue", out)

    def test_freeze_for_the_clerk_keeps_the_accepted_chapter(self):
        self.run_bench("freeze", "novels/long-ebb", "2", "1", "e", "c", "--role", "clerk")
        copy = self.p("novels", "long-ebb--e-c")
        self.assertEqual(len(os.listdir(os.path.join(copy, "chapters"))), 2)
        self.assertNotIn("fold.md", os.listdir(os.path.join(copy, "work", "ch0002")))
        self.assertNotIn("=C0002=", read(os.path.join(copy, "state", "continuity.md")))

    # ------------------------------------------------------------ arm

    def test_arm_changes_only_effort_and_names_itself(self):
        self.fx.write("../../.claude/agents/story-editor.md",
                      "---\nname: story-editor\ndescription: Judges a draft.\nmodel: opus\n"
                      "effort: high\nomitClaudeMd: true\n---\n\nRead kb/story-editor/prompt.md.\n")
        code, out = self.run_bench("arm", "story-editor", "medium", "--effort", "medium")
        self.assertEqual(code, 0, out)
        text = read(self.p(".claude", "agents", "story-editor--medium.md"))
        self.assertIn("name: story-editor--medium\n", text)
        self.assertIn("description: Experiment arm only, never in the loop", text)
        self.assertIn("effort: medium\n", text)
        self.assertNotIn("effort: high", text)
        self.assertIn("model: opus\nomitClaudeMd: true", text)
        self.assertTrue(text.endswith("---\n\nRead kb/story-editor/prompt.md.\n"))
        self.run_bench("arm", "story-editor", "medium", "--remove")
        self.assertFalse(os.path.exists(self.p(".claude", "agents", "story-editor--medium.md")))
        code, _ = self.run_bench("arm", "story-editor", "x")
        self.assertEqual(code, 1)
        for name in ("../../x", "A B", "fable"):        # a path; not a name; the panel's own
            role = "judge" if name == "fable" else "story-editor"
            code, _ = self.run_bench("arm", role, name, "--remove")
            self.assertEqual(code, 1, name)

    # ------------------------------------------------------------ pair

    def test_pair_writes_both_orders_and_a_key_the_judge_cannot_see(self):
        a = self.fx.path("work", "ch0002", "draft-r0.md")
        b = self.fx.path("work", "ch0002", "draft-r1.md")
        code, out = self.run_bench("pair", "cap", "ch02", "r0=" + a, "r1=" + b)
        self.assertEqual(code, 0, out)
        key = read(self.p("bench", "cap", "key.md"))
        rows = [l for l in key.splitlines() if l.startswith("| ch02 ")]
        self.assertEqual([r.split(" | ")[2:4] for r in rows], [["r0", "r1"], ["r1", "r0"]])
        folder = rows[0].split(" | ")[1]
        x = read(self.p(folder, "X.md"))
        self.assertNotIn("number:", x)
        self.assertIn("Tam shrugged.", x)
        self.assertIn("Tam, her cousin", read(self.p(folder, "Y.md")))
        self.assertEqual(out.count("@ spawn judge as"), 2)
        self.assertIn("Mode 2 — compare. Your folder is %s/. Read X first, then Y." % folder, out)

    # ------------------------------------------------------------ panel

    def test_panel_mixes_models_and_needs_their_agent_files(self):
        os.makedirs(self.p("bench", "vt", "blind", "abcd"))
        code, out = self.run_bench("panel", "bench/vt/blind/abcd")
        self.assertEqual(code, 1)
        for name in ("judge", "judge--fable"):
            self.fx.write("../../.claude/agents/%s.md" % name, "---\nname: %s\n---\n" % name)
        code, out = self.run_bench("panel", "bench/vt/blind/abcd/")
        self.assertEqual(code, 0, out)
        self.assertEqual(out.count("@ spawn judge as"), 2)
        self.assertEqual(out.count("@ spawn judge--fable as"), 1)
        self.assertEqual(out.count("Mode 1 — read. Your folder is bench/vt/blind/abcd/."), 3)
        code, _ = self.run_bench("panel", "bench/vt/abcd")
        self.assertEqual(code, 1)

    # ------------------------------------------------------------ agree

    def test_same_passage_needs_a_run_of_words(self):
        self.assertTrue(bench.same_passage("Tam shrugged at the door and said nothing",
                                           "and Tam shrugged at the door, and said"))
        self.assertTrue(bench.same_passage("Yours.", "“Yours.”"))
        self.assertFalse(bench.same_passage("the tide was out by noon", "the tide was in"))

    def test_agree_notes_matches_by_quote_and_compares_verdicts(self):
        w = self.fx.path("work", "ch0002")
        b = self.fx.write("work/ch0002/notes-b.md", NOTES % (0, "REVISE", NOTE_B))
        out = bench.agree_notes(os.path.join(w, "notes-r0.md"), b)
        self.assertIn("verdict  REVISE · REVISE · same", out)
        self.assertIn("matched  1 of 2 (A 2, B 1)", out)
        self.assertIn("A only   N2 the tide is wrong", out)
        out = bench.agree_notes(os.path.join(w, "notes-r0.md"), os.path.join(w, "notes-r1.md"))
        self.assertIn("DIFFERENT", out)

    def test_agree_continuity_reports_the_known_catches(self):
        a = self.fx.path("work", "ch0002", "continuity-r0.md")
        b = self.fx.write("work/ch0002/cont-b.md", CONT % (
            'F1 know "Tam knew the price already" | C0001 kno: "Tam- price" | no source\n'))
        out = bench.agree_continuity(a, b, ["the tide was out by noon"])
        self.assertIn("matched  0 of 2", out)
        self.assertIn('catch    "the tide was out by noon" · A F1 · B -', out)


if __name__ == "__main__":
    unittest.main()
