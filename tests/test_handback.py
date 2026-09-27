"""tools/handback.py - a subagent's hand-back, filed verbatim, never retyped."""
import contextlib
import io
import json
import os
import sys
import tempfile
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "tools"))

import handback  # noqa: E402

REPORT = """# Report — chapter 1

## Retell
Somebody rowed somebody out.

## Would I click next?
4 — the ending."""


def use(name, inp):
    return {"message": {"role": "assistant", "content": [
        {"type": "tool_use", "name": name, "input": inp}]}}


def transcript(path, rows):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as fh:
        for row in rows:
            fh.write(json.dumps(row) + "\n")
        fh.write("not json\n")


class HandbackTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.base = self.tmp.name
        self.path = os.path.join(self.base, "sess", "subagents", "agent-abc.jsonl")

    def tearDown(self):
        self.tmp.cleanup()

    def test_whole_message_is_the_last_handback(self):
        transcript(self.path, [use("SubagentHandback", {"message": "first"}),
                               use("SubagentHandback", {"message": "second, after notes"})])
        self.assertEqual(handback.extract(self.path), "second, after notes")

    def test_report_block_drops_preamble_and_trailer(self):
        msg = "I read the folder.\n\n---\n\n" + REPORT + "\n\n---\n\nFiles: ch01.md"
        transcript(self.path, [use("SubagentHandback", {"message": msg})])
        self.assertEqual(handback.extract(self.path, report=True), REPORT + "\n")

    def test_report_falls_back_to_a_refused_write(self):
        transcript(self.path, [use("Write", {"file_path": "reading/x/report.md", "content": REPORT}),
                               use("SubagentHandback", {"message": "the write was refused"})])
        self.assertEqual(handback.extract(self.path, report=True), REPORT)

    def test_finds_the_transcript_by_agent_id(self):
        transcript(self.path, [use("SubagentHandback", {"message": "hi"})])
        self.assertEqual(handback.find_transcript("abc", self.base), self.path)
        with self.assertRaises(FileNotFoundError):
            handback.find_transcript("zzz", self.base)

    def test_cli_writes_the_file(self):
        transcript(self.path, [use("SubagentHandback", {"message": REPORT})])
        out = os.path.join(self.base, "reading", "r1", "report.md")
        with contextlib.redirect_stdout(io.StringIO()):
            rc = handback.main(["abc", out, "--report", "--transcripts", self.base])
        self.assertEqual(rc, 0)
        with open(out, encoding="utf-8") as fh:
            self.assertEqual(fh.read(), REPORT + "\n")


if __name__ == "__main__":
    unittest.main()
