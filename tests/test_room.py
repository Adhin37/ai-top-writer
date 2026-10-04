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
        self.transcripts = os.path.join(self.root, "transcripts")
        self.cwd = os.getcwd()
        os.chdir(self.root)

    def tearDown(self):
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
        before, after = out.split("then: read novels/long-ebb/work/ch0001/beats.md")
        self.assertNotIn("writer", before)
        self.assertIn('@ spawn writer as "writer-ch01"\nNovel: novels/long-ebb. Chapter 1. Beat '
                      'sheet: novels/long-ebb/work/ch0001/beats.md. Write '
                      'novels/long-ebb/work/ch0001/draft-r0.md.', after)

    def test_beats_stops_without_a_plan_row_or_threads(self):
        code, out = self.run_room("beats", self.novel, "3")
        self.assertEqual(code, 2)
        self.assertIn("STOP: chapter 3 has no plan row", out)
        os.remove(self.fx.path("state", "threads.md"))
        code, out = self.run_room("beats", self.novel, "2")
        self.assertIn("STOP: state/threads.md is missing", out)

    # ------------------------------------------------------------ round

    def test_round_builds_the_view_and_dispatches_both_readers(self):
        self.fx.write("work/ch0002/draft-r0.md", DRAFT)
        code, out = self.run_room("round", self.novel, "2", "0")
        self.assertEqual(code, 0, out)
        folder = "reading/%s/ch02-r0" % self.id
        self.assertTrue(os.path.isfile(os.path.join(self.root, folder, "pending", "ch02.md")))
        self.assertIn('@ spawn beta-reader as "beta-reader ch02 r0"\nYour reading folder is '
                      '%s/. Report on chapter 2, pending/ch02.md.' % folder, out)
        self.assertIn('@ spawn continuity-editor as "continuity ch02 r0"\nNovel: '
                      'novels/long-ebb. Chapter 2, round 0. Draft: '
                      'novels/long-ebb/work/ch0002/draft-r0.md. Write '
                      'novels/long-ebb/work/ch0002/continuity-r0.md.', out)
        self.assertNotIn("history", out)            # before chapter 3
        self.assertIn("room.py judge novels/long-ebb 2 0 <beta-reader agent id>", out)

    def test_round_stops_without_its_draft(self):
        code, out = self.run_room("round", self.novel, "2", "1")
        self.assertEqual(code, 2)
        self.assertIn("STOP: no draft", out)

    def test_round_logs_the_hand_backs_and_the_dispatch_that_led_here(self):
        self.fx.write("work/ch0002/draft-r1.md", DRAFT)
        self.agent("w1", "DRAFT READY novels/long-ebb/work/ch0002/draft-r1.md | facts f | new 0 "
                   "| stets 0 | couldn't 0", "writer-ch02")
        log = "docs/experiments/run.md"
        code, out = self.run_room("round", self.novel, "2", "1", "--log", log, "--agent", "w1")
        self.assertEqual(code, 0, out)
        text = read(os.path.join(self.root, log))
        self.assertIn("**writer-ch02** (`w1`), hand-back verbatim", text)
        self.assertIn("continue writer-ch02, verbatim:\n\n```\nNotes: "
                      "novels/long-ebb/work/ch0002/notes-r0.md. Write draft-r1.md.\n```", text)
        self.assertIn('spawn beta-reader as "beta-reader ch02 r1"', text)
        self.assertLess(text.index("w1"), text.index("continue writer-ch02"))

    # ------------------------------------------------------------ judge

    def judge_ready(self, k):
        self.fx.write("work/ch0002/draft-r%d.md" % k, DRAFT)
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
        self.assertIn('@ spawn story-editor as "story-editor ch02 r0"', out)
        self.assertIn("Reader's memory before this chapter: reading/%s/shelf/notes.md." % self.id, out)
        self.assertNotIn("Writer's facts", out)       # round 0
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
        self.assertIn('spawn story-editor as "story-editor ch02 r0"', text)
        self.assertNotIn("continue writer-ch02", text)               # a branch, not yet sent

    def test_judge_at_the_last_round_only_polishes(self):
        self.judge_ready(2)
        code, out = self.run_room("judge", self.novel, "2", "2", "b2")
        self.assertEqual(code, 0, out)
        self.assertIn("Writer's facts: novels/long-ebb/work/ch0002/facts-r2.md.", out)
        self.assertNotIn("REVISE", out)
        self.assertIn("either -> @ spawn line-editor", out)

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
        self.assertIn("@ continue planner-ch02\n  Task: beats for chapter 2. Editor's notes for "
                      "the planner: novels/long-ebb/work/ch0001/notes-r0.md.", out)
        self.assertTrue(out.splitlines()[1].startswith("state_check "))

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
        shelf = os.path.join(self.root, "reading", self.id, "shelf")
        os.makedirs(shelf)
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
        self.fx.write("work/ch0001/notes-r1.md", "verdict ACCEPT | owed 1/1\n")
        self.assertIn("step 5: ACCEPT at round 1 -> the line editor into "
                      "novels/long-ebb/chapters/0001-the-tally.md", w())
        self.fx.chapter(1, title="The Tally", slug="the-tally")
        self.assertIn("room.py clerk novels/long-ebb 1 1", w())
        self.fx.write("work/ch0001/fold.md", "none\n")
        self.assertEqual(room.where(self.fx.root, self.root)[0], 2)

    # ------------------------------------------------------------ usage

    def test_the_pause_reads_a_fresh_five_hour_reading(self):
        path = os.path.join(self.root, "usage.json")

        def reading(pct, age=0):
            with open(path, "w", encoding="utf-8") as fh:
                json.dump({"updated": time.time() - age, "rate_limits": {
                    "five_hour": {"used_percentage": pct, "resets_at": time.time() + 3600}}}, fh)

        self.assertIsNone(room.usage_pause(path))
        reading(79)
        self.assertIsNone(room.usage_pause(path))
        reading(81)
        self.assertIn("PAUSE: the 5-hour window is at 81% (resets ", room.usage_pause(path))
        reading(90, age=room.FRESH_S + 1)
        self.assertIsNone(room.usage_pause(path))


if __name__ == "__main__":
    unittest.main()
