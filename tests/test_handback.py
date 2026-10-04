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
        for bad in ("*", "../abc", "a/b", ""):
            with self.assertRaises(FileNotFoundError):
                handback.find_transcript(bad, self.base)

    def test_append_adds_a_fenced_entry_named_by_the_spawn_label(self):
        transcript(self.path, [use("SubagentHandback", {"message": "NOTES READY w/n.md | ACCEPT"})])
        with open(self.path[:-len(".jsonl")] + ".meta.json", "w", encoding="utf-8") as fh:
            json.dump({"agentType": "story-editor", "description": "Story editor on L4 r0"}, fh)
        log = os.path.join(self.base, "log.md")
        with open(log, "w", encoding="utf-8") as fh:
            fh.write("# Log\n")
        for _ in range(2):
            with contextlib.redirect_stdout(io.StringIO()):
                rc = handback.main(["abc", log, "--append", "--transcripts", self.base])
            self.assertEqual(rc, 0)
        with open(log, encoding="utf-8") as fh:
            text = fh.read()
        entry = ("\n**Story editor on L4 r0** (`abc`), hand-back verbatim:\n\n"
                 "```\nNOTES READY w/n.md | ACCEPT\n```\n")
        self.assertEqual(text, "# Log\n" + entry + entry)

    def test_append_fences_around_a_fence(self):
        entry = handback.log_entry("abc", "", "text\n```\ncode\n```\n")
        self.assertTrue(entry.startswith("\n`abc`, hand-back verbatim:\n\n````\n"))
        self.assertTrue(entry.endswith("\n````\n"))

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
