"""tools/room.py - one call per deterministic step, and the exact dispatch for the next."""
import contextlib
import io
import json
import os
import sys
import time
import unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from novel_fixture import NovelFixture  # noqa: E402
import export_prose  # noqa: E402
import room  # noqa: E402

room.READINGS = ()     # the session's own usage files never reach a test

REPORT = """Some preamble the reader wrote.

# Report — chapter 2

## Retell
Nessa rows the boy out.

## Would I click next?
4 — the bar."""

DRAFT = "---\nnumber: 2\ntitle: \"The Bar\"\npov: \"Nessa Vane\"\n---\n\nShe rowed.\n"


def read(path):
    with open(path, encoding="utf-8") as fh:
        return fh.read()


class RoomTest(unittest.TestCase):
    def setUp(self):
        self.fx = NovelFixture().__enter__()
        self.root = self.fx.tmp
        self.novel = "novels/long-ebb"
        self.id = export_prose.novel_id(self.fx.root)
        self.fx.write("state/threads.md", "# Threads\n")
        self.shelf = os.path.join(self.root, "reading", self.id, "shelf")
        os.makedirs(self.shelf)
        with open(os.path.join(self.shelf, "notes.md"), "w", encoding="utf-8") as fh:
            fh.write("The reader's memory after chapter 1.\n")
        self.transcripts = os.path.join(self.root, "transcripts")
        self.readings, room.READINGS = room.READINGS, ()      # never this machine's live usage
        self.cwd = os.getcwd()
        os.chdir(self.root)

    def tearDown(self):
        room.READINGS = self.readings
        os.chdir(self.cwd)
        self.fx.__exit__(None, None, None)

    def run_room(self, *args):
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            code = room.main(list(args) + ["--root", self.root, "--transcripts",
                                           self.transcripts])
        return code, out.getvalue()

    def agent(self, agent_id, message, label=""):
        path = os.path.join(self.transcripts, "s", "subagents", "agent-%s.jsonl" % agent_id)
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w", encoding="utf-8") as fh:
            fh.write(json.dumps({"message": {"role": "assistant", "content": [
                {"type": "tool_use", "name": "SubagentHandback",
                 "input": {"message": message}}]}}) + "\n")
        with open(path[:-len(".jsonl")] + ".meta.json", "w", encoding="utf-8") as fh:
            json.dump({"description": label}, fh)

    # ------------------------------------------------------------ beats

    def test_beats_spawns_a_fresh_planner_and_holds_the_writer_for_approval(self):
        code, out = self.run_room("beats", self.novel, "1")
        self.assertEqual(code, 0, out)
        self.assertIn('@ spawn planner as "planner-ch01"\nNovel: novels/long-ebb. Task: beats '
                      'for chapter 1.', out)
        self.assertIn("then, on PLANNER DONE beats: python3 tools/room.py approve "
                      "novels/long-ebb 1 (it prints the writer)", out)
        self.assertNotIn("@ spawn writer", out)          # approve prints it
        self.fx.write("work/ch0001/beats.md", "# Ch 1\nevent    x\n")
        code, out = self.run_room("approve", self.novel, "1")
        self.assertIn('Approved, send the writer:\n\n@ spawn writer as "writer-ch01"\nNovel: '
                      'novels/long-ebb. Chapter 1. Beat sheet: novels/long-ebb/work/ch0001/'
                      'beats.md. Write novels/long-ebb/work/ch0001/draft-r0.md.', out)

    def test_a_long_bible_file_is_mapped_by_section_in_the_writer_dispatch(self):
        self.fx.write("work/ch0001/beats.md", "# Ch 1\nevent    x\n")
        code, out = self.run_room("approve", self.novel, "1")
        self.assertNotIn("Long bible files", out)
        places = "".join("| quay %d | a day's walk |\n" % i for i in range(room.MAP_OVER // 20))
        self.fx.write("bible/world.md", "# World\n\n## The central rule\nThe sea gives back.\n\n"
                      "## Places\n" + places + "\n```\n## not a section\n```\n")
        code, out = self.run_room("approve", self.novel, "1")
        self.assertIn("Long bible files, by section", out)
        row = next(l for l in out.splitlines() if l.startswith("bible/world.md "))
        self.assertIn("§The central rule 3-4 · §Places 6-", row)
        self.assertNotIn("not a section", row)

    def test_a_long_section_lists_its_places(self):
        self.fx.write("work/ch0001/beats.md", "# Ch 1\nevent    x\n")
        quay = "".join("The quay's lamp %d hangs low.\n" % i for i in range(room.MAP_OVER // 25))
        self.fx.write("bible/world.md", "# World\n\n## The central rule\nThe sea gives back.\n\n"
                      "## Places\n### The quay\n" + quay + "### The chapel\nOn the cliff.\n")
        code, out = self.run_room("approve", self.novel, "1")
        row = next(l for l in out.splitlines() if l.startswith("bible/world.md "))
        self.assertRegex(row, r"§Places 6-\d+ [\d.]+k \(The quay 7-\d+, The chapel \d+-\d+\)")
        self.assertNotIn("(The sea", row)

    def test_beats_stops_without_a_plan_row_or_threads(self):
        code, out = self.run_room("beats", self.novel, "3")
        self.assertEqual(code, 2)
        self.assertIn("STOP: chapter 3 has no plan row", out)
        os.remove(self.fx.path("state", "threads.md"))
        code, out = self.run_room("beats", self.novel, "2")
        self.assertIn("STOP: state/threads.md is missing", out)

    def test_beats_rebuilds_a_lost_memory_before_the_planner(self):
        os.remove(os.path.join(self.shelf, "notes.md"))
        with open(os.path.join(self.shelf, "ch01.md"), "w", encoding="utf-8") as fh:
            fh.write("Text 1.\n")
        code, out = self.run_room("beats", self.novel, "2")
        self.assertEqual(code, 0, out)
        self.assertIn("warn: the reader has no memory before chapter 2", out)
        self.assertIn('@ spawn beta-reader as "beta-reader fresh ch01"', out)
        self.assertIn("room.py adopt novels/long-ebb 1 <agent id>", out)
        self.assertNotIn("@ spawn planner", out)

    def test_approve_prints_the_header_range_and_a_due_row_the_header_misses(self):
        sheet = ('# Ch 2 — "The Bar"\nevent    Nessa rows the boy out\nlearns   %s\n'
                 'pressure L1 grew: she takes the oars\n\n## Scene 1 — the quay\nprose plan\n')
        self.fx.write("work/ch0002/beats.md", sheet % "R1 the tally's date: sc 1, Tam says it")
        self.fx.write("work/ch0001/" + room.AHEAD, "planner-ch02 offered\n")    # judge, at ACCEPT
        code, out = self.run_room("approve", self.novel, "2")
        self.assertEqual(code, 0, out)
        self.assertIn("plan event: Nessa rows the boy out past the bar", out)
        self.assertIn("read novels/long-ebb/work/ch0002/beats.md lines 1-5 only", out)
        self.assertIn("ledger due ch 2: F2 - not in the header: F2", out)
        self.assertIn("(a sheet started at chapter 1's ACCEPT: after room.py fold "
                      "novels/long-ebb 1):\n\n@ spawn writer as \"writer-ch02\"", out)
        self.fx.write("work/ch0002/beats.md", sheet % "F2 the bar is dry: sc 1, she walks it")
        code, out = self.run_room("approve", self.novel, "2")
        self.assertIn("ledger due ch 2: F2\n", out)

    def test_approve_stops_without_a_beat_sheet(self):
        code, out = self.run_room("approve", self.novel, "2")
        self.assertEqual(code, 2)
        self.assertIn("STOP: no beat sheet", out)

    def test_dispatches_name_the_last_continuity_block_by_its_lines(self):
        self.fx.chapter(1, title="The Tally")
        self.fx.state(blocks=(1,))
        rng = "novels/long-ebb/state/continuity.md lines 3-8"
        c = room.Chapter(self.novel, 2, self.root)
        self.assertIn("Last continuity block: %s." % rng, room.planner_beats(c)[1])
        self.assertIn("Last continuity block: %s." % rng, room.story_editor(c, 0)[1])
        one = room.Chapter(self.novel, 1, self.root)
        self.assertIn("Last continuity block: %s." % rng, room.clerk(one, 0)[1])
        self.assertIn("Its block: %s." % rng, room.planner_fold(one)[1])
        self.assertNotIn("continuity block", room.planner_beats(one)[1])   # chapter 1: no state

    def test_long_finding_lists_stop_with_a_count(self):
        self.assertEqual(room.shown(["x"] * 3, "f"), ["x"] * 3)
        out = room.shown(["x%d" % i for i in range(12)], "python3 tools/status.py n --debt", "  ")
        self.assertEqual(len(out), room.SHOWN + 1)
        self.assertEqual(out[-1], "  +4 more: python3 tools/status.py n --debt")

    # ------------------------------------------------------------ round

    def test_round_will_not_rebuild_a_folder_the_reader_worked_in(self):
        self.fx.write("work/ch0002/draft-r0.md", DRAFT)
        self.assertEqual(self.run_room("round", self.novel, "2", "0")[0], 0)
        folder = os.path.join(self.root, "reading", self.id, "ch02-r0")
        with open(os.path.join(folder, "report.md"), "w", encoding="utf-8") as fh:
            fh.write("filed")
        code, out = self.run_room("round", self.novel, "2", "0")
        self.assertEqual(code, 2, out)
        self.assertIn("holds the reader's work", out)
        self.assertEqual(self.run_room("round", self.novel, "2", "0", "--force")[0], 0)
        self.assertFalse(os.path.exists(os.path.join(folder, "report.md")))

    def test_round_builds_the_view_and_dispatches_both_readers(self):
        self.fx.write("work/ch0002/draft-r0.md", DRAFT)
        code, out = self.run_room("round", self.novel, "2", "0")
        self.assertEqual(code, 0, out)
        folder = "reading/%s/ch02-r0" % self.id
        self.assertTrue(os.path.isfile(os.path.join(self.root, folder, "pending", "ch02.md")))
        self.assertIn('@ spawn beta-reader as "beta-reader ch02 r0"\nYour reading folder is '
                      '%s/. Report on chapter 2, pending/ch02.md.' % folder, out)
        self.assertIn('@ spawn continuity-editor as "continuity-ch02"\nNovel: '
                      'novels/long-ebb. Chapter 2, round 0. Draft: '
                      'novels/long-ebb/work/ch0002/draft-r0.md. Lint: '
                      'novels/long-ebb/work/ch0002/lint-r0.txt. Write '
                      'novels/long-ebb/work/ch0002/continuity-r0.md.', out)
        self.assertTrue(os.path.isfile(self.fx.path("work", "ch0002", "lint-r0.txt")))
        self.assertNotIn("history", out)            # before chapter 3
        self.assertIn("room.py judge novels/long-ebb 2 0 <beta-reader agent id>", out)

    def test_round_stops_without_its_draft(self):
        code, out = self.run_room("round", self.novel, "2", "1")
        self.assertEqual(code, 2)
        self.assertIn("STOP: no draft", out)

    def test_round_logs_the_hand_backs_and_the_dispatch_that_led_here(self):
        self.fx.write("work/ch0002/draft-r1.md", DRAFT)
        self.fx.write("work/ch0002/facts-r1.md", "# Facts\n")
        self.agent("w1", "DRAFT READY novels/long-ebb/work/ch0002/draft-r1.md | facts f | new 0 "
                   "| stets 0 | couldn't 0", "writer-ch02")
        log = "docs/experiments/run.md"
        code, out = self.run_room("round", self.novel, "2", "1", "--log", log, "--agent", "w1")
        self.assertEqual(code, 0, out)
        text = read(os.path.join(self.root, log))
        self.assertIn("**writer-ch02** (`w1`), hand-back verbatim", text)
        self.assertIn("continue writer-ch02, verbatim:\n\n```\nNotes: "
                      "novels/long-ebb/work/ch0002/notes-r0.md. Revise draft-r1.md in place: it "
                      "is a copy of draft-r0.md.\n```", text)
        self.assertIn('spawn beta-reader as "beta-reader ch02 r1"', text)
        self.assertLess(text.index("w1"), text.index("continue writer-ch02"))

    # ------------------------------------------------------------ judge

    def judge_ready(self, k):
        self.fx.write("work/ch0002/draft-r%d.md" % k, DRAFT)
        if k:
            self.fx.write("work/ch0002/facts-r%d.md" % k, "# Facts\n")
        self.run_room("round", self.novel, "2", str(k))
        self.fx.write("work/ch0002/continuity-r%d.md" % k,
                      "# Continuity — chapter 2, round %d\nlint     x\nchecked  y\nnone\n" % k)
        self.agent("b%d" % k, REPORT, "beta-reader ch02 r%d" % k)

    def test_judge_files_the_report_and_dispatches_the_story_editor(self):
        self.judge_ready(0)
        code, out = self.run_room("judge", self.novel, "2", "0", "b0")
        self.assertEqual(code, 0, out)
        report = os.path.join(self.root, "reading", "%s/ch02-r0" % self.id, "report.md")
        self.assertTrue(read(report).startswith("# Report — chapter 2"))
        self.assertIn('@ spawn story-editor as "story-editor-ch02"', out)
        self.assertIn("Reader's memory before this chapter: reading/%s/shelf/notes.md." % self.id, out)
        self.assertIn("Writer's facts: novels/long-ebb/work/ch0002/facts-r0.md.", out)
        self.assertIn("(draft-r1.md beside it is the unrevised copy", out)
        self.assertIn("REVISE  -> @ continue writer-ch02", out)
        self.assertIn("ACCEPT -> @ spawn line-editor as \"line-editor ch02\"", out)
        self.assertIn("into novels/long-ebb/chapters/0002-the-bar.md", out)

    def test_judge_logs_the_readers_whole_hand_back(self):
        self.judge_ready(0)
        self.agent("c0", "CONTINUITY READY x | findings 0 | lint clean", "continuity ch02 r0")
        log = "docs/experiments/run.md"
        code, out = self.run_room("judge", self.novel, "2", "0", "b0", "--log", log,
                                  "--agent", "c0")
        self.assertEqual(code, 0, out)
        text = read(os.path.join(self.root, log))
        self.assertIn("Some preamble the reader wrote.", text)       # whole, not the report only
        self.assertLess(text.index("`c0`"), text.index("`b0`"))
        self.assertIn('spawn story-editor as "story-editor-ch02"', text)
        self.assertNotIn("continue writer-ch02", text)               # a branch, not yet sent

    def test_judge_at_the_last_round_only_polishes(self):
        self.judge_ready(2)
        code, out = self.run_room("judge", self.novel, "2", "2", "b2")
        self.assertEqual(code, 0, out)
        self.assertIn("Writer's facts: novels/long-ebb/work/ch0002/facts-r2.md.", out)
        self.assertNotIn("REVISE", out)
        self.assertIn("either -> @ spawn line-editor", out)

    def test_judge_continues_the_story_editor_warm_after_round_0(self):
        self.judge_ready(1)
        code, out = self.run_room("judge", self.novel, "2", "1", "b1")
        self.assertEqual(code, 0, out)
        self.assertIn("@ continue story-editor-ch02\nChapter 2, round 1. Draft: "
                      "novels/long-ebb/work/ch0002/draft-r1.md. Writer's facts: "
                      "novels/long-ebb/work/ch0002/facts-r1.md.", out)
        self.assertIn("Your last notes: novels/long-ebb/work/ch0002/notes-r0.md.", out)
        self.assertNotIn("Reader's memory before", out)          # it read that at round 0
        d = room.story_editor(room.Chapter(self.novel, 2, self.root), 1, warm=False)
        self.assertEqual(d[0], '@ spawn story-editor as "story-editor-ch02"')

    def test_judge_asks_the_warm_story_editor_for_an_ungraded_pressure_id(self):
        self.fx.write("work/ch0002/beats.md", "# Beats\npressure L1 grew — she rows out alone\n"
                      "         past the bar · C1 nearer — the tide turns\n")
        self.fx.write("work/ch0002/notes-r0.md", "verdict REVISE\n\n## Owed\nL1 stated \"rows "
                      "out\"\nbeat bar stated \"the bar\"\n\n## Notes\n\n## Keep\n")
        self.judge_ready(1)
        code, out = self.run_room("judge", self.novel, "2", "1", "b1")
        self.assertEqual(code, 0, out)
        self.assertIn("warn: notes-r0.md grades no C1 from the beat sheet's pressure line", out)
        self.assertIn("Your last notes graded no C1: grade each pressure id in Owed.", out)

    def test_judge_asks_the_warm_story_editor_for_an_unanswered_fact_finding(self):
        self.fx.write("work/ch0002/continuity-r0.md", '# Continuity\nlint x\nchecked y\n'
                      'F1 bible   "two doors" | world.md: "one door" | the boathouse\n'
                      'F2 lexicon "harbor" | lexicon.md: "harbour" | spelling\n'
                      'F3 know    "she knew" | C0001 kno: "no one" | nobody told her\n')
        self.fx.write("work/ch0002/notes-r0.md", "verdict REVISE\n\n## Owed\n\n## Notes\n\n"
                      "## Continuity\nF1 N2\n\n## Keep\n")
        self.judge_ready(1)
        code, out = self.run_room("judge", self.novel, "2", "1", "b1")
        self.assertEqual(code, 0, out)
        self.assertIn("warn: notes-r0.md answers no continuity F3\n", out)
        self.assertIn("Your last notes answered no continuity F3: answer each fact finding in "
                      "Continuity.", out)

    def test_judge_stops_when_the_reader_handed_back_nothing(self):
        self.fx.write("work/ch0002/draft-r0.md", DRAFT)
        self.run_room("round", self.novel, "2", "0")
        code, out = self.run_room("judge", self.novel, "2", "0", "nobody")
        self.assertEqual(code, 2)
        self.assertIn("STOP: ", out)

    # ------------------------------------------------------------ clerk

    def clerk_ready(self, notes_words):
        self.fx.chapter(2, title="The Bar", slug="the-bar")
        folder = os.path.join(self.root, "reading", "%s/ch02-r1" % self.id)
        os.makedirs(folder, exist_ok=True)
        with open(os.path.join(folder, "notes.md"), "w", encoding="utf-8") as fh:
            fh.write("word " * notes_words)

    def test_clerk_dispatches_the_clerk_under_the_cap(self):
        self.clerk_ready(700)
        code, out = self.run_room("clerk", self.novel, "2", "1")
        self.assertEqual(code, 0, out)
        self.assertIn('@ spawn clerk as "clerk ch02"\nNovel: novels/long-ebb. Chapter 2: '
                      'novels/long-ebb/chapters/0002-the-bar.md. Notes: '
                      'novels/long-ebb/work/ch0002/notes-r1.md.', out)
        self.assertIn("Accepted round: reading/%s/ch02-r1/." % self.id, out)

    def test_clerk_saves_the_ledger_once_before_the_clerk(self):
        self.clerk_ready(700)
        saved = os.path.join(self.fx.root, "work", "ch0002", "ledger-before.md")
        ledger = self.fx.novel().text("plan", "reader-ledger.md")
        code, out = self.run_room("clerk", self.novel, "2", "1")
        self.assertIn("saved novels/long-ebb/work/ch0002/ledger-before.md", out)
        with open(saved, encoding="utf-8") as fh:
            self.assertEqual(fh.read(), ledger)
        self.fx.write("plan/reader-ledger.md", ledger.replace("owed", "landed ch2"))
        code, out = self.run_room("clerk", self.novel, "2", "1")
        self.assertNotIn("saved", out)
        with open(saved, encoding="utf-8") as fh:
            self.assertEqual(fh.read(), ledger)

    def test_clerk_warns_when_the_accepted_notes_grade_no_pressure_id(self):
        self.clerk_ready(700)
        self.fx.write("work/ch0002/beats.md", "# Beats\npressure L1 held — she waits\n")
        self.fx.write("work/ch0002/notes-r1.md", "verdict ACCEPT\n\n## Owed\n\n## Notes\n")
        code, out = self.run_room("clerk", self.novel, "2", "1")
        self.assertEqual(code, 0, out)
        self.assertIn("warn: notes-r1.md grades no L1", out)
        self.fx.write("work/ch0002/notes-r1.md", "verdict ACCEPT\n\n## Owed\nL1 held \"x\"\n")
        code, out = self.run_room("clerk", self.novel, "2", "1")
        self.assertNotIn("grades no", out)

    def test_clerk_warns_when_the_accepted_notes_answer_no_fact_finding(self):
        self.clerk_ready(700)
        self.fx.write("work/ch0002/continuity-r1.md", '# Continuity\nlint x\nchecked y\n'
                      'F1 state   "her left palm" | C0001 has: "both palms" | bound\n')
        self.fx.write("work/ch0002/notes-r1.md", "verdict ACCEPT\n\n## Owed\n\n## Notes\n")
        code, out = self.run_room("clerk", self.novel, "2", "1")
        self.assertIn("warn: notes-r1.md answers no continuity F1", out)
        self.fx.write("work/ch0002/notes-r1.md", "verdict ACCEPT\n\n## Continuity\nF1 dismissed "
                      "— the left rag came off at the quay\n")
        code, out = self.run_room("clerk", self.novel, "2", "1")
        self.assertNotIn("answers no continuity", out)

    def test_clerk_asks_the_reader_to_compress_first_over_the_cap(self):
        self.clerk_ready(812)
        code, out = self.run_room("clerk", self.novel, "2", "1")
        self.assertEqual(code, 0, out)
        self.assertIn("@ continue beta-reader ch02 r1\nYour notes.md measures 812 words by count",
                      out)
        self.assertNotIn("spawn clerk", out)

    def test_clerk_stops_without_the_polished_chapter(self):
        code, out = self.run_room("clerk", self.novel, "2", "1")
        self.assertEqual(code, 2)
        self.assertIn("STOP: no polished chapter: novels/long-ebb/chapters/0002-the-bar.md", out)

    # ------------------------------------------------------------ fold

    def test_fold_continues_the_planner_warm_into_the_next_beats(self):
        self.fx.write("work/ch0001/notes-r0.md", "# Notes\nverdict ACCEPT | owed 1/1\n")
        self.fx.write("work/ch0001/fold.md", '# Fold — chapter 1\nnew    the boathouse has two '
                      'doors | bible/world.md | "two doors"\n')
        code, out = self.run_room("fold", self.novel, "1")
        self.assertEqual(code, 0, out)
        self.assertIn("fold novels/long-ebb/work/ch0001/fold.md: 1 line(s) for the bible", out)
        self.assertIn('@ spawn planner as "planner-ch02"\nNovel: novels/long-ebb. Task: fold '
                      'chapter 1.', out)
        self.assertIn("@ continue planner-ch02\n  Task: beats for chapter 2. Reader's notes: "
                      "reading/%s/shelf/notes.md. Editor's notes for "
                      "the planner: novels/long-ebb/work/ch0001/notes-r0.md." % self.id, out)
        self.assertTrue(out.splitlines()[1].startswith("state_check "))
        self.assertIn("and on PLANNER DONE beats: python3 tools/room.py approve novels/long-ebb 2 "
                      "(it prints the writer)", out)

    def test_a_ledger_row_past_due_sends_the_run_to_plan_first(self):
        self.fx.chapter(2, title="The Bar", slug="the-bar")      # F2, due by ch 2, still owed
        self.fx.write("work/ch0002/fold.md", "none\n")
        code, out = self.run_room("fold", self.novel, "2")
        self.assertEqual(code, 0, out)
        self.assertIn("rows past due: kb/showrunner/plan.md first", out)
        self.assertIn("overdue  F2 due ch 2", out)
        code, out = self.run_room("beats", self.novel, "3")
        self.assertEqual(code, 2)

    def test_fold_with_nothing_for_the_bible_spawns_no_planner(self):
        self.fx.write("work/ch0001/fold.md", "# Fold — chapter 1\nnone\n")
        code, out = self.run_room("fold", self.novel, "1")
        self.assertEqual(code, 0, out)
        self.assertNotIn("@ spawn planner", out)
        self.assertIn("room.py beats novels/long-ebb 2", out)

    def test_fold_at_ten_builds_the_fresh_re_read(self):
        shelf = self.shelf
        for n in range(1, 11):
            with open(os.path.join(shelf, "ch%02d.md" % n), "w", encoding="utf-8") as fh:
                fh.write("Text %d.\n" % n)
        self.fx.write("work/ch0010/fold.md", "none\n")
        code, out = self.run_room("fold", self.novel, "10")
        self.assertEqual(code, 0, out)
        self.assertIn('@ spawn beta-reader as "beta-reader fresh ch10"\nYour reading folder is '
                      'reading/%s/fresh-ch10/. There are no notes' % self.id, out)
        self.assertIn("room.py adopt novels/long-ebb 10", out)
        self.assertIn("no plan row for chapter 11", out)

    def test_round_continues_the_continuity_editor_warm_after_round_0(self):
        self.fx.write("work/ch0002/draft-r1.md", DRAFT + "Revised.\n")
        self.fx.write("work/ch0002/facts-r1.md", "# Facts\n")
        code, out = self.run_room("round", self.novel, "2", "1")
        self.assertEqual(code, 0, out)
        self.assertIn("@ continue continuity-ch02\nChapter 2, round 1. Draft: "
                      "novels/long-ebb/work/ch0002/draft-r1.md. Lint: "
                      "novels/long-ebb/work/ch0002/lint-r1.txt. Write "
                      "novels/long-ebb/work/ch0002/continuity-r1.md. Your last file: "
                      "novels/long-ebb/work/ch0002/continuity-r0.md.", out)
        self.assertIn('@ spawn beta-reader as "beta-reader ch02 r1"', out)    # the reader stays cold
        room.WARM_CONTINUITY = False
        try:
            code, out = self.run_room("round", self.novel, "2", "1", "--force")
        finally:
            room.WARM_CONTINUITY = True
        self.assertIn('@ spawn continuity-editor as "continuity-ch02"', out)

    def test_judge_copies_the_draft_for_a_revision_in_place(self):
        self.judge_ready(0)
        code, out = self.run_room("judge", self.novel, "2", "0", "b0")
        self.assertEqual(code, 0, out)
        r0, r1 = self.fx.path("work", "ch0002", "draft-r0.md"), self.fx.path("work", "ch0002",
                                                                             "draft-r1.md")
        self.assertEqual(read(r1), read(r0))
        self.assertIn("copied novels/long-ebb/work/ch0002/draft-r0.md -> "
                      "novels/long-ebb/work/ch0002/draft-r1.md", out)
        self.assertIn("Revise draft-r1.md in place: it is a copy of draft-r0.md.", out)
        # the copy is not a draft yet: where waits for the writer, round refuses it
        self.fx.write("work/ch0002/notes-r0.md", "verdict REVISE | owed 0/1\n")
        self.fx.write("work/ch0002/beats.md", "# Ch 2\n")
        self.fx.chapter(1, title="The Tally", slug="the-tally")
        self.fx.write("work/ch0001/fold.md", "none\n")
        self.assertIn("continue writer-ch02 for draft-r1", room.where(self.fx.root, self.root)[1])
        code, out = self.run_room("round", self.novel, "2", "1")
        self.assertEqual(code, 2)
        self.assertIn("has no facts-r1.md: the writer has not finished the revision (the draft is "
                      "still the unrevised copy)", out)
        # a revised draft is never overwritten by a second judge call
        self.fx.write("work/ch0002/draft-r1.md", DRAFT + "Revised.\n")
        self.run_room("judge", self.novel, "2", "0", "b0")
        self.assertIn("Revised.", read(r1))

    def test_clerk_removes_an_unrevised_copy_after_accept(self):
        self.clerk_ready(700)
        self.fx.write("work/ch0002/draft-r1.md", DRAFT)
        self.fx.write("work/ch0002/facts-r1.md", "# Facts\n")
        self.fx.write("work/ch0002/draft-r2.md", DRAFT)            # judge's copy, ACCEPT came
        code, out = self.run_room("clerk", self.novel, "2", "1")
        self.assertEqual(code, 0, out)
        self.assertIn("removed draft-r2.md, the unrevised copy", out)
        self.assertFalse(os.path.exists(self.fx.path("work", "ch0002", "draft-r2.md")))

    def test_judge_starts_the_next_beats_beside_the_line_editor(self):
        self.fx.write("work/ch0001/draft-r0.md", DRAFT.replace("number: 2", "number: 1"))
        self.run_room("round", self.novel, "1", "0")
        self.fx.write("work/ch0001/continuity-r0.md",
                      "# Continuity — chapter 1, round 0\nlint     x\nchecked  y\nnone\n")
        self.agent("b1", REPORT.replace("chapter 2", "chapter 1"), "beta-reader ch01 r0")
        code, out = self.run_room("judge", self.novel, "1", "0", "b1")
        self.assertEqual(code, 0, out)
        accept = out.split("ACCEPT -> ")[1]
        self.assertIn('in the same message, if chapter 2 is in this run: @ spawn planner as '
                      '"planner-ch02"\n  Novel: novels/long-ebb. Task: beats for chapter 2. '
                      'Chapter 1 is accepted and not yet in state/: its text is '
                      'novels/long-ebb/work/ch0001/draft-r0.md. Reader\'s notes: '
                      'reading/%s/ch01-r0/notes.md. Editor\'s notes for the planner: '
                      'novels/long-ebb/work/ch0001/notes-r0.md.' % self.id, accept)
        self.assertIn("on PLANNER DONE beats: python3 tools/room.py approve novels/long-ebb 2 "
                      "(loop.md step 1)", accept)
        self.assertIn("room.py clerk novels/long-ebb 1 0", accept)

    def test_judge_holds_the_next_beats_without_a_plan_row(self):
        self.judge_ready(0)
        code, out = self.run_room("judge", self.novel, "2", "0", "b0")
        self.assertEqual(code, 0, out)
        self.assertNotIn("@ spawn planner", out)
        self.assertIn("chapter 3's beats wait for room.py fold: no plan row for chapter 3", out)

    def test_fold_after_beats_ahead_continues_that_planner_then_the_writer(self):
        self.fx.write("work/ch0001/notes-r0.md", "# Notes\nverdict ACCEPT | owed 1/1\n")
        self.fx.write("work/ch0001/fold.md", '# Fold — chapter 1\nnew    the boathouse has two '
                      'doors | bible/world.md | "two doors"\n')
        self.fx.write("work/ch0002/beats.md", "# Ch 2\n")
        log = "docs/experiments/run.md"
        code, out = self.run_room("fold", self.novel, "1", "--log", log)
        self.assertEqual(code, 0, out)
        self.assertNotIn("@ spawn planner", out)
        self.assertIn("@ continue planner-ch02\nTask: fold chapter 1. Fold file: "
                      "novels/long-ebb/work/ch0001/fold.md. Then check your beat sheet for "
                      "chapter 2 against what you folded.", out)
        then = out.split("on PLANNER DONE fold, with the beat sheet approved, send the writer:")[1]
        self.assertIn('@ spawn writer as "writer-ch02"', then)
        self.assertIn('spawn planner as "planner-ch02"', read(os.path.join(self.root, log)))
        os.remove(self.fx.path("work", "ch0001", "fold.md"))
        self.fx.write("work/ch0001/fold.md", "none\n")
        code, out = self.run_room("fold", self.novel, "1")
        self.assertNotIn("@ continue planner", out)
        self.assertIn("with the beat sheet approved, send the writer:", out)

    def test_fold_waits_for_a_planner_still_on_the_next_beats(self):
        self.fx.write("work/ch0001/notes-r0.md", "# Notes\nverdict ACCEPT | owed 1/1\n")
        self.fx.write("work/ch0001/fold.md", '# Fold — chapter 1\nnew    the boathouse has two '
                      'doors | bible/world.md | "two doors"\n')
        self.fx.write("work/ch0001/" + room.AHEAD, "planner-ch02 offered\n")    # judge, at ACCEPT
        code, out = self.run_room("fold", self.novel, "1")
        self.assertEqual(code, 0, out)
        self.assertNotIn("@ spawn planner", out)
        self.assertIn("@ continue planner-ch02\nTask: fold chapter 1.", out)
        self.assertIn("send the fold on its PLANNER DONE beats", out)
        self.assertIn("room.py fold novels/long-ebb 1 --cold", out)
        code, out = self.run_room("fold", self.novel, "1", "--cold")
        self.assertIn('@ spawn planner as "planner-ch02"\nNovel: novels/long-ebb. Task: fold '
                      'chapter 1.', out)

    def test_after_a_cold_fold_the_beats_continue_that_planner(self):
        self.fx.write("work/ch0001/notes-r0.md", "# Notes\nverdict ACCEPT | owed 1/1\n")
        self.fx.write("work/ch0001/fold.md", '# Fold — chapter 1\nnew    the boathouse has two '
                      'doors | bible/world.md | "two doors"\n')
        self.fx.write("work/ch0001/" + room.AHEAD, "planner-ch02 offered\n")    # never sent
        code, out = self.run_room("fold", self.novel, "1", "--cold")
        self.assertIn('@ spawn planner as "planner-ch02"', out)
        self.assertFalse(os.path.isfile(self.fx.path("work", "ch0001", room.AHEAD)))
        code, out = self.run_room("beats", self.novel, "2")
        self.assertEqual(code, 0, out)
        self.assertIn("@ continue planner-ch02\nTask: beats for chapter 2.", out)
        self.assertNotIn("@ spawn planner", out)
        code, out = self.run_room("beats", self.novel, "2", "--cold")
        self.assertIn('@ spawn planner as "planner-ch02"', out)
        self.fx.write("work/ch0002/beats.md", "# Ch 2\nevent    x\n")
        code, out = self.run_room("approve", self.novel, "2")
        self.assertNotIn("ACCEPT", out)                    # this sheet came after the fold
        self.assertIn("Approved, send the writer:", out)

    def test_judge_past_the_pause_starts_no_next_beats(self):
        self.fx.write("work/ch0001/draft-r0.md", DRAFT.replace("number: 2", "number: 1"))
        self.run_room("round", self.novel, "1", "0")
        self.fx.write("work/ch0001/continuity-r0.md",
                      "# Continuity — chapter 1, round 0\nlint     x\nchecked  y\nnone\n")
        self.agent("b1", REPORT.replace("chapter 2", "chapter 1"), "beta-reader ch01 r0")
        usage = os.path.join(self.root, "usage.json")
        with open(usage, "w", encoding="utf-8") as fh:
            json.dump({"updated": time.time(), "rate_limits": {"five_hour": {
                "used_percentage": 85}}}, fh)
        room.READINGS = (usage,)
        code, out = self.run_room("judge", self.novel, "1", "0", "b1")
        self.assertEqual(code, 0, out)
        self.assertNotIn("@ spawn planner", out)
        self.assertIn("chapter 2's beats wait for room.py fold: the usage window", out)
        self.assertFalse(os.path.isfile(self.fx.path("work", "ch0001", room.AHEAD)))

    def test_agent_ids_may_be_comma_separated(self):
        self.agent("w1", "DRAFT READY x")
        self.agent("s1", "NOTES READY y")
        self.fx.write("work/ch0001/beats.md", "# Ch 1\nevent    x\n")
        log = "docs/experiments/run.md"
        code, out = self.run_room("approve", self.novel, "1", "--log", log, "--agent", "w1,s1")
        self.assertNotIn("warn log", out)
        self.assertEqual(out.count("log w1") + out.count("log s1"), 2, out)

    def test_judge_marks_the_next_beats_as_offered(self):
        self.fx.write("work/ch0001/draft-r0.md", DRAFT.replace("number: 2", "number: 1"))
        self.run_room("round", self.novel, "1", "0")
        self.fx.write("work/ch0001/continuity-r0.md",
                      "# Continuity — chapter 1, round 0\nlint     x\nchecked  y\nnone\n")
        self.agent("b1", REPORT.replace("chapter 2", "chapter 1"), "beta-reader ch01 r0")
        self.run_room("judge", self.novel, "1", "0", "b1")
        self.assertIn("planner-ch02", read(self.fx.path("work", "ch0001", room.AHEAD)))

    # ------------------------------------------------------------ where

    def test_where_follows_the_files(self):
        w = lambda: room.where(self.fx.root, self.root)[1]  # noqa: E731
        self.assertTrue(w().startswith("step 1: no beat sheet"))
        self.fx.write("work/ch0001/beats.md", "# Ch 1\n")
        self.assertTrue(w().startswith("step 2"))
        self.fx.write("work/ch0001/draft-r0.md", DRAFT)
        self.assertTrue(w().startswith("step 3"))
        os.makedirs(os.path.join(self.root, "reading", "%s/ch01-r0" % self.id))
        self.fx.write("../../reading/%s/ch01-r0/report.md" % self.id, "# Report\n")
        self.assertTrue(w().startswith("step 4: round 0 is read"))
        self.fx.write("work/ch0001/notes-r0.md", "verdict REVISE | owed 0/1\n")
        self.assertIn("continue writer-ch01 for draft-r1", w())
        self.fx.write("work/ch0001/draft-r1.md", DRAFT)
        self.fx.write("work/ch0001/facts-r1.md", "# Facts\n")
        self.fx.write("work/ch0001/notes-r1.md", "verdict ACCEPT | owed 1/1\n")
        self.assertIn("step 5: ACCEPT at round 1 -> the line editor into "
                      "novels/long-ebb/chapters/0001-the-tally.md", w())
        self.fx.chapter(1, title="The Tally", slug="the-tally")
        self.assertIn("room.py clerk novels/long-ebb 1 1", w())
        self.fx.write("work/ch0001/fold.md", "none\n")
        self.assertEqual(room.where(self.fx.root, self.root)[0], 2)

    def test_where_holds_the_next_chapter_until_the_re_read_is_adopted(self):
        self.fx.chapter(1, title="The Tally", slug="the-tally")
        self.fx.write("work/ch0001/fold.md", "none\n")
        fresh = os.path.join(self.root, "reading", self.id, "fresh-ch01")
        os.makedirs(fresh)
        n, line = room.where(self.fx.root, self.root)
        self.assertEqual(n, 1)
        self.assertIn("room.py adopt novels/long-ebb 1 <beta-reader agent id>", line)
        with open(os.path.join(fresh, "ch01.md"), "w", encoding="utf-8") as fh:
            fh.write("Text 1.\n")
        with open(os.path.join(fresh, "notes.md"), "w", encoding="utf-8") as fh:
            fh.write("Fresh notes.\n")
        self.agent("f1", "# Report\nfresh read")
        code, out = self.run_room("adopt", self.novel, "1", "f1")
        self.assertEqual(code, 0, out)
        self.assertIn("adopted", out)
        self.assertEqual(read(os.path.join(self.shelf, "notes.md")), "Fresh notes.\n")
        self.assertTrue(os.path.isfile(os.path.join(fresh, "report.md")))
        self.assertTrue(os.path.isfile(os.path.join(self.shelf, "ch01.md")))
        self.assertEqual(room.where(self.fx.root, self.root)[0], 2)

    def test_adopt_stops_when_the_reader_handed_back_nothing(self):
        os.makedirs(os.path.join(self.root, "reading", self.id, "fresh-ch01"))
        code, out = self.run_room("adopt", self.novel, "1", "nobody")
        self.assertNotEqual(code, 0)
        self.assertIn("STOP", out)

    # ------------------------------------------------------------ usage

    def test_canon_sends_the_planners_gaps_verbatim_then_continues_it(self):
        self.agent("p1", "PLANNER DONE beats | w/beats.md | gaps 2 | changed 0\n"
                   "gap canon is the harbourmaster's son alive at the start; his age\n"
                   "gap the bible gives no distance to the quay", "planner-ch04")
        code, out = self.run_room("canon", self.novel, "p1")
        self.assertEqual(code, 0, out)
        self.assertIn('@ spawn canon-researcher as "canon lookup"\nNovel: novels/long-ebb. Task: '
                      'lookup.\ngap canon is the harbourmaster\'s son alive at the start; his age',
                      out)
        self.assertNotIn("distance to the quay", out)
        before, after = out.split("then, on CANON DONE:")
        self.assertNotIn("@ continue", before)
        self.assertIn("@ continue planner-ch04\nCanon looked up: novels/long-ebb/bible/canon.md. "
                      "Finish the task.", after)

    def test_canon_stops_without_a_gap_canon_line(self):
        self.agent("p2", "PLANNER DONE beats | w/beats.md | gaps 0 | changed 0", "planner-ch04")
        code, out = self.run_room("canon", self.novel, "p2")
        self.assertEqual(code, 2)
        self.assertIn("STOP: agent p2 handed back no `gap canon` line", out)

    def test_the_pause_reads_a_fresh_five_hour_reading(self):
        exact, guess = (os.path.join(self.root, f) for f in ("usage.json", "usage-live.json"))
        paths = (exact, guess)

        def reading(pct, age=0, path=exact):
            with open(path, "w", encoding="utf-8") as fh:
                json.dump({"updated": time.time() - age, "rate_limits": {
                    "five_hour": {"used_percentage": pct, "resets_at": time.time() + 3600}}}, fh)

        self.assertIsNone(room.usage_pause(paths))
        reading(79)
        self.assertIsNone(room.usage_pause(paths))
        reading(81)
        self.assertIn("PAUSE: the 5-hour window is at 81% (resets ", room.usage_pause(paths))
        reading(90, age=600 + 1)
        self.assertIsNone(room.usage_pause(paths))
        reading(85, path=guess)                              # no status line: the live reading
        self.assertIn("at 85%", room.usage_pause(paths))
        reading(70)                                          # a fresh status line wins
        self.assertIsNone(room.usage_pause(paths))
        for path in paths:
            with open(path, "w", encoding="utf-8") as fh:
                json.dump({"updated": "now", "rate_limits": []}, fh)
        self.assertIsNone(room.usage_pause(paths))           # a bad reading, not a crash


if __name__ == "__main__":
    unittest.main()
