"""tools/guard.py - who may read and write what."""
import json
import os
import subprocess
import sys
import tempfile
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "tools"))

import guard  # noqa: E402

PROJECT = "/proj"


def call(tool, agent=None, **tool_input):
    payload = {"tool_name": tool, "tool_input": tool_input, "cwd": PROJECT}
    if agent:
        payload["agent_id"] = "a123"
        payload["agent_type"] = agent
    return payload


def p(rel):
    return os.path.join(PROJECT, rel)


class GuardTest(unittest.TestCase):
    def setUp(self):
        self._env = os.environ.pop("CLAUDE_PROJECT_DIR", None)

    def tearDown(self):
        if self._env is not None:
            os.environ["CLAUDE_PROJECT_DIR"] = self._env

    def allowed(self, payload):
        return guard.verdict(payload) is None

    # --- the cold roles -------------------------------------------------------------------

    def test_beta_reader_reads_only_its_folder(self):
        self.assertTrue(self.allowed(call("Read", "beta-reader", file_path=p("reading/r1abcd/ch01.md"))))
        self.assertTrue(self.allowed(call("Read", "beta-reader", file_path=p("kb/beta-reader/prompt.md"))))
        for rel in ("novels/x/bible/world.md", "novels/x/chapters/0001-a.md", "kb/writer/index.md",
                    "bench/e/blind/X.md", "docs/architecture.md", "CLAUDE.md"):
            self.assertFalse(self.allowed(call("Read", "beta-reader", file_path=p(rel))), rel)

    def test_an_experiments_variant_keeps_its_roles_rules(self):
        self.assertFalse(self.allowed(call("Read", "continuity-editor--medium",
                                           file_path=p("reading/r1abcd/report.md"))))
        self.assertTrue(self.allowed(call("Read", "continuity-editor--medium",
                                          file_path=p("novels/x/bible/world.md"))))
        self.assertFalse(self.allowed(call("Read", "judge--a", file_path=p("novels/x/bible/world.md"))))

    def test_beta_reader_refused_outside_the_project(self):
        self.assertFalse(self.allowed(call("Read", "beta-reader", file_path="/etc/passwd")))

    def test_beta_reader_searches_must_be_scoped(self):
        self.assertFalse(self.allowed(call("Grep", "beta-reader", pattern="Reading")))
        self.assertFalse(self.allowed(call("Glob", "beta-reader", pattern="**/*.md")))
        self.assertTrue(self.allowed(call("Grep", "beta-reader", pattern="x", path=p("reading/r1"))))
        self.assertTrue(self.allowed(call("Glob", "beta-reader", pattern="reading/r1/*.md")))
        self.assertTrue(self.allowed(call("Glob", "beta-reader", pattern="*.md", path=p("reading/r1"))))
        self.assertFalse(self.allowed(call("Glob", "beta-reader", pattern="novels/*/bible/*.md")))
        self.assertFalse(self.allowed(call("Glob", "beta-reader", pattern="../../novels/**",
                                           path=p("reading/r1"))))

    def test_beta_reader_writes_only_its_folder(self):
        self.assertTrue(self.allowed(call("Write", "beta-reader", file_path=p("reading/r1/report.md"))))
        self.assertFalse(self.allowed(call("Write", "beta-reader", file_path=p("novels/x/state/a.md"))))

    def test_judge_reads_only_blind_copies(self):
        self.assertTrue(self.allowed(call("Read", "judge", file_path=p("bench/ch1-abc/blind/Q.md"))))
        self.assertTrue(self.allowed(call("Read", "judge", file_path=p("kb/judge/prompt.md"))))
        self.assertTrue(self.allowed(call("Read", "judge", file_path=p("kb/shared/grading.md"))))
        self.assertFalse(self.allowed(call("Read", "judge", file_path=p("kb/shared/format-spec.md"))))
        for rel in ("bench/ch1-abc/key.md", "bench/ch1-abc/originals/A.md", "reading/r1/ch01.md",
                    "novels/x/bible/premise.md"):
            self.assertFalse(self.allowed(call("Read", "judge", file_path=p(rel))), rel)
        self.assertFalse(self.allowed(call("Write", "judge", file_path=p("bench/ch1-abc/blind/v.md"))))

    # --- the working roles ----------------------------------------------------------------

    def test_writer_is_kept_off_the_reader_and_the_rubrics(self):
        self.assertTrue(self.allowed(call("Read", "writer", file_path=p("novels/x/bible/world.md"))))
        self.assertTrue(self.allowed(call("Read", "writer", file_path=p("kb/writer/index.md"))))
        self.assertTrue(self.allowed(call("Read", "writer", file_path=p("kb/shared/format-spec.md"))))
        for rel in ("reading/r1/report.md", "bench/e/originals/A.md", "docs/lessons.md",
                    "kb/beta-reader/prompt.md", "kb/story-editor/prompt.md", "kb/judge/prompt.md"):
            self.assertFalse(self.allowed(call("Read", "writer", file_path=p(rel))), rel)

    def test_writer_writes_work_and_chapters_only(self):
        self.assertTrue(self.allowed(call("Write", "writer", file_path=p("novels/x/work/ch0001/draft-r0.md"))))
        self.assertTrue(self.allowed(call("Edit", "writer", file_path=p("novels/x/chapters/0001-a.md"))))
        for rel in ("novels/x/bible/world.md", "kb/writer/index.md", "reading/r1/ch01.md"):
            self.assertFalse(self.allowed(call("Write", "writer", file_path=p(rel))), rel)

    def test_planner_reads_reader_notes_but_not_the_judge(self):
        self.assertTrue(self.allowed(call("Read", "planner", file_path=p("reading/r1/notes.md"))))
        self.assertFalse(self.allowed(call("Read", "planner", file_path=p("kb/judge/prompt.md"))))
        self.assertTrue(self.allowed(call("Write", "planner", file_path=p("novels/x/bible/premise.md"))))
        self.assertTrue(self.allowed(call("Write", "planner", file_path=p("novels/x/novel.md"))))
        self.assertFalse(self.allowed(call("Write", "planner", file_path=p("novels/x/chapters/0001-a.md"))))

    def test_story_editor_reads_reports_writes_work(self):
        self.assertTrue(self.allowed(call("Read", "story-editor", file_path=p("reading/L1-r0/report.md"))))
        self.assertTrue(self.allowed(call("Write", "story-editor", file_path=p("novels/x/work/ch0001/notes-r0.md"))))
        self.assertFalse(self.allowed(call("Edit", "story-editor", file_path=p("novels/x/chapters/0001-a.md"))))

    def test_line_editor_edits_chapters_not_reports(self):
        self.assertTrue(self.allowed(call("Edit", "line-editor", file_path=p("novels/x/chapters/0001-a.md"))))
        self.assertFalse(self.allowed(call("Read", "line-editor", file_path=p("reading/r1/report.md"))))
        self.assertFalse(self.allowed(call("Write", "line-editor", file_path=p("bench/e/originals/B1.md"))))

    # --- everyone else --------------------------------------------------------------------

    def test_main_session_is_free(self):
        self.assertTrue(self.allowed(call("Write", None, file_path=p("novels/x/chapters/0001-a.md"))))
        self.assertTrue(self.allowed(call("Read", None, file_path=p("bench/e/key.md"))))

    def test_unknown_agents_fail_open(self):
        self.assertTrue(self.allowed(call("Read", "Explore", file_path=p("bench/e/key.md"))))
        self.assertTrue(self.allowed(call("Write", "general-purpose", file_path=p("kb/x.md"))))

    def test_test_run_marker_stops_the_showrunner_writing_novels(self):
        with tempfile.TemporaryDirectory() as root:
            payload = {"tool_name": "Write", "cwd": root,
                       "tool_input": {"file_path": os.path.join(root, "novels/x/chapters/0001-a.md")}}
            self.assertIsNone(guard.verdict(payload))
            open(os.path.join(root, ".test-run"), "w").close()
            self.assertIsNotNone(guard.verdict(payload))
            payload["tool_input"]["file_path"] = os.path.join(root, "docs/experiments/log.md")
            self.assertIsNone(guard.verdict(payload))

    def test_glob_matching(self):
        self.assertTrue(guard.matches("reading/**", "reading"))
        self.assertTrue(guard.matches("reading/**", "reading/a/b.md"))
        self.assertFalse(guard.matches("reading/**", "readings/a.md"))
        self.assertTrue(guard.matches("bench/*/blind/**", "bench/e1/blind/X.md"))
        self.assertFalse(guard.matches("bench/*/blind/**", "bench/e1/key.md"))
        self.assertTrue(guard.matches("novels/*/novel.md", "novels/x/novel.md"))

    def test_relpath(self):
        self.assertEqual(guard.relpath("/proj/a/b.md", "/proj"), "a/b.md")
        self.assertEqual(guard.relpath("a/../b.md", "/proj"), "b.md")
        self.assertEqual(guard.relpath("/proj", "/proj"), "")
        self.assertIsNone(guard.relpath("/proj/../etc/x", "/proj"))
        self.assertIsNone(guard.relpath("/projector/x", "/proj"))


class GuardProcessTest(unittest.TestCase):
    """The hook as Claude Code runs it: payload on stdin, exit 2 and stderr to refuse."""

    def run_hook(self, payload):
        return subprocess.run([sys.executable, os.path.join(ROOT, "tools", "guard.py")],
                              input=json.dumps(payload), capture_output=True, text=True)

    def test_refusal_exits_2_with_reason(self):
        res = self.run_hook(call("Read", "beta-reader", file_path=p("novels/x/bible/world.md")))
        self.assertEqual(res.returncode, 2)
        self.assertIn("Blocked", res.stderr)
        self.assertIn("reading folder", res.stderr)

    def test_allow_exits_0(self):
        self.assertEqual(self.run_hook(call("Read", "beta-reader", file_path=p("reading/r1/ch01.md"))).returncode, 0)

    def test_garbage_fails_open(self):
        res = subprocess.run([sys.executable, os.path.join(ROOT, "tools", "guard.py")],
                             input="not json", capture_output=True, text=True)
        self.assertEqual(res.returncode, 0)


class ReadLogTest(unittest.TestCase):
    """Every Read the guard allows lands in docs/sessions/<session>.reads.tsv, for the trace."""

    def setUp(self):
        self._env = os.environ.pop("CLAUDE_PROJECT_DIR", None)
        self.tmp = tempfile.TemporaryDirectory()
        self.log = os.path.join(self.tmp.name, "docs", "sessions", "s1.reads.tsv")

    def tearDown(self):
        self.tmp.cleanup()
        if self._env is not None:
            os.environ["CLAUDE_PROJECT_DIR"] = self._env

    def run_hook(self, tool, agent=None, **tool_input):
        payload = {"tool_name": tool, "tool_input": tool_input, "cwd": self.tmp.name,
                   "session_id": "s1"}
        if agent:
            payload.update(agent_id="a9", agent_type=agent)
        return subprocess.run([sys.executable, os.path.join(ROOT, "tools", "guard.py")],
                              input=json.dumps(payload), capture_output=True, text=True)

    def lines(self):
        if not os.path.exists(self.log):
            return []
        with open(self.log, encoding="utf-8") as fh:
            return [l.rstrip("\n").split("\t") for l in fh]

    def test_allowed_reads_are_logged_with_the_role(self):
        doc = os.path.join(self.tmp.name, "kb", "writer", "prompt.md")
        self.assertEqual(self.run_hook("Read", "writer", file_path=doc).returncode, 0)
        self.assertEqual(self.run_hook("Read", file_path=doc).returncode, 0)
        rows = self.lines()
        self.assertEqual([r[1:] for r in rows], [["s1", "a9", "writer", "kb/writer/prompt.md"],
                                                 ["s1", "", "showrunner", "kb/writer/prompt.md"]])

    def test_refused_reads_writes_and_searches_are_not(self):
        self.assertEqual(self.run_hook("Read", "writer", file_path=os.path.join(
            self.tmp.name, "kb", "story-editor", "prompt.md")).returncode, 2)
        self.run_hook("Write", "writer", file_path=os.path.join(self.tmp.name, "novels", "x",
                                                                "work", "a.md"))
        self.run_hook("Grep", "writer", pattern="x", path=self.tmp.name)
        self.assertEqual(self.lines(), [])

    def test_an_unwritable_log_never_blocks(self):
        os.makedirs(os.path.dirname(self.log))
        os.makedirs(self.log)                       # a directory where the file should be
        res = self.run_hook("Read", "writer", file_path=os.path.join(self.tmp.name, "kb", "a.md"))
        self.assertEqual((res.returncode, res.stderr), (0, ""))


if __name__ == "__main__":
    unittest.main()
