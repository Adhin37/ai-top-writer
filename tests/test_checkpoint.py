"""tools/checkpoint.py - a session's handoff, built from its transcripts."""
import contextlib
import datetime as dt
import io
import json
import os
import sys
import tempfile
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "tools"))

import checkpoint  # noqa: E402

SID = "sess-1"
RESETS = 1790461200                                  # 2026-09-26T22:20Z


def ts(minute):
    return "2026-09-26T19:%02d:00.000Z" % minute


def human(minute, text):
    return {"type": "user", "timestamp": ts(minute), "origin": {"kind": "human"},
            "message": {"role": "user", "content": [
                {"type": "text", "text": "<ide_opened_file>x</ide_opened_file>"},
                {"type": "text", "text": text}]}}


def said(minute, text, *uses, tokens=1000):
    content = ([{"type": "text", "text": text}] if text else []) + [
        {"type": "tool_use", "id": i, "name": n, "input": inp} for i, n, inp in uses]
    return {"type": "assistant", "timestamp": ts(minute), "message": {
        "role": "assistant", "content": content,
        "usage": {"input_tokens": 1, "cache_read_input_tokens": tokens - 1}}}


def result(minute, tool_id, text="ok", error=False):
    return {"type": "user", "timestamp": ts(minute), "message": {"role": "user", "content": [
        {"type": "tool_result", "tool_use_id": tool_id, "is_error": error,
         "content": [{"type": "text", "text": text}]}]}}


def notified(minute, agent, status, summary=""):
    return {"type": "user", "timestamp": ts(minute), "origin": {"kind": "task-notification"},
            "message": {"role": "user", "content": (
                "<task-notification>\n<task-id>%s</task-id>\n<status>%s</status>\n"
                "<summary>%s</summary>\n</task-notification>" % (agent, status, summary))}}


def handed_back(minute, agent):
    return {"type": "user", "timestamp": ts(minute), "isMeta": True,
            "origin": {"kind": "peer", "from": agent},
            "message": {"role": "user", "content": "<agent-message>[Subagent hand-back] done"}}


def limit(minute):
    return {"type": "assistant", "timestamp": ts(minute), "error": "rate_limit",
            "isApiErrorMessage": True,
            "quotaLimits": {"status": "rejected", "resetsAt": RESETS, "rateLimitType": "five_hour"},
            "message": {"role": "assistant", "content": [
                {"type": "text", "text": "You've hit your session limit"}]}}


def launched(minute, tool_id, agent):
    return result(minute, tool_id, "Async agent launched successfully.\nagentId: %s (internal)"
                  % agent)


def spawn(tool_id, kind, prompt, name=None):
    inp = {"subagent_type": kind, "description": "%s task" % kind, "prompt": prompt,
           "run_in_background": True}
    if name:
        inp["name"] = name
    return (tool_id, "Agent", inp)


def write_jsonl(path, rows):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as fh:
        for row in rows:
            fh.write(json.dumps(row) + "\n")
        fh.write("not json\n")


class CheckpointTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.base = os.path.join(self.tmp.name, "transcripts")
        self.root = os.path.join(self.tmp.name, "repo")
        os.makedirs(self.root)
        self.now = dt.datetime(2026, 9, 26, 22, 0, tzinfo=dt.timezone.utc).astimezone()

    def tearDown(self):
        self.tmp.cleanup()

    def session(self, rows):
        write_jsonl(os.path.join(self.base, SID + ".jsonl"), rows)

    def agent(self, agent_id, tool_id, kind, rows):
        sub = os.path.join(self.base, SID, "subagents")
        write_jsonl(os.path.join(sub, "agent-%s.jsonl" % agent_id), rows)
        with open(os.path.join(sub, "agent-%s.meta.json" % agent_id), "w") as fh:
            json.dump({"agentType": kind, "description": "%s task" % kind, "toolUseId": tool_id,
                       "requestShape": "background"}, fh)

    def build(self, **kw):
        path = checkpoint.build(SID, self.base, self.root, now=self.now, **kw)
        with open(path, encoding="utf-8") as fh:
            return fh.read()

    def writer_rows(self, *extra):
        return [{"type": "user", "timestamp": ts(1), "message": {"role": "user",
                                                                 "content": "Write draft-r0.md"}},
                said(2, "", ("w1", "Write", {"file_path": os.path.join(self.root, "d-r0.md")})),
                result(2, "w1")] + list(extra)

    def test_an_agent_cut_off_by_the_limit_is_in_flight(self):
        self.session([human(0, "start roadmap 01"),
                      said(1, "Spawning the writer.", spawn("t1", "writer", "Write draft-r0.md")),
                      launched(1, "t1", "aw1"),
                      said(2, "writer-1 is drafting."),
                      notified(3, "aw1", "failed", "API error (error type rate_limit, HTTP 429)"),
                      limit(3)])
        self.agent("aw1", "t1", "writer", self.writer_rows(limit(3)))
        text = self.build()
        front, _ = checkpoint.read_frontmatter(checkpoint.handoff_path(self.root, SID))
        self.assertEqual(front["status"], "stopped")
        self.assertEqual(front["reason"], "usage limit, five_hour window")
        self.assertEqual(front["in_flight"], "1")
        self.assertEqual(checkpoint.when(front["resets_at"]),
                         dt.datetime.fromtimestamp(RESETS).astimezone().replace(second=0))
        self.assertIn("| aw1 | writer |", text)
        self.assertIn("failed - rate_limit", text)
        self.assertIn("`d-r0.md`", text)
        self.assertIn("> start roadmap 01", text)
        self.assertNotIn("ide_opened_file", text)
        self.assertIn("```\nWrite draft-r0.md\n```", text)           # the spawn prompt, verbatim

    def test_a_finished_agent_is_not_in_flight(self):
        self.session([human(0, "go"), said(1, "", spawn("t1", "judge", "grade")),
                      launched(1, "t1", "aj1"), handed_back(2, "aj1"), said(3, "Judge done.")])
        self.agent("aj1", "t1", "judge", [said(2, "", ("h", "SubagentHandback", {"message": "x"}))])
        text = self.build()
        self.assertIn("## Agents in flight\n\nNone.", text)
        self.assertIn("1 other agent(s) finished earlier", text)
        self.assertIn("status: working", text)

    def test_a_message_after_a_failure_makes_the_agent_run_again(self):
        self.session([said(1, "", spawn("t1", "writer", "Write draft-r0.md", name="writer-1")),
                      launched(1, "t1", "aw1"),
                      notified(2, "aw1", "failed", "error type rate_limit"),
                      said(9, "Resuming writer-1.", ("s1", "SendMessage",
                                                     {"to": "writer-1", "message": "Finish r1."})),
                      result(9, "s1")])
        self.agent("aw1", "t1", "writer", self.writer_rows())
        text = self.build()
        self.assertIn("| aw1 | writer | writer-1 | background | running |", text)
        self.assertIn("Its latest instruction, by SendMessage:\n\n```\nFinish r1.\n```", text)

    def test_a_failure_the_session_already_answered_is_not_in_flight(self):
        self.session([said(1, "", spawn("t1", "writer", "p")), launched(1, "t1", "aw1"),
                      notified(2, "aw1", "failed", "error type overloaded"),
                      said(3, "The writer failed; I re-spawned it as aw2.")])
        self.agent("aw1", "t1", "writer", self.writer_rows())
        self.assertIn("## Agents in flight\n\nNone.", self.build())

    def test_an_agent_that_died_without_notice_is_failed(self):
        self.session([said(1, "", spawn("t1", "writer", "p")), launched(1, "t1", "aw1"), limit(3)])
        self.agent("aw1", "t1", "writer", self.writer_rows(limit(3)))
        self.assertIn("| aw1 | writer | writer task | background | failed - rate_limit |",
                      self.build())

    def test_a_foreground_result_counts_as_completed(self):
        self.session([said(1, "", spawn("t1", "planner", "beats")),
                      result(2, "t1", "report delivered\nagentId: ap1 (use SendMessage)"),
                      said(3, "Beats are in.")])
        self.agent("ap1", "t1", "planner", [said(2, "done")])
        self.assertIn("## Agents in flight\n\nNone.", self.build())

    def test_only_writes_since_the_last_instruction_and_never_refused_ones(self):
        rows = self.writer_rows(
            {"type": "user", "timestamp": ts(5), "isMeta": True, "origin": {"kind": "coordinator"},
             "message": {"role": "user", "content": "Notes: notes-r0.md. Write draft-r1.md."}},
            said(6, "", ("w2", "Write", {"file_path": "report.md"}),
                 ("w3", "Write", {"file_path": os.path.join(self.root, "d-r1.md")})),
            result(6, "w2", "Subagents should return findings as text", error=True),
            result(6, "w3"))
        self.session([said(1, "", spawn("t1", "writer", "p")), launched(1, "t1", "aw1")])
        self.agent("aw1", "t1", "writer", rows)
        text = self.build()
        row = [l for l in text.splitlines() if l.startswith("| aw1 ")][0]
        self.assertIn("`d-r1.md`", row)
        self.assertNotIn("d-r0.md", row)
        self.assertNotIn("report.md", text)
        self.assertIn("| `d-r0.md` | writer aw1 |", text)            # still in the session's files

    def test_notifications_are_not_the_users_messages(self):
        self.session([human(0, "hello"), notified(1, "x", "completed", "monitor fired"),
                      said(2, "Hi.")])
        text = self.build()
        self.assertIn("> hello", text)
        self.assertNotIn("monitor fired", text)

    def test_note_and_closed_at_survive_a_rebuild(self):
        self.session([human(0, "go"), limit(1)])
        path = checkpoint.handoff_path(self.root, SID)
        self.build()
        with open(path, encoding="utf-8") as fh:
            text = fh.read()
        with open(path, "w", encoding="utf-8") as fh:
            fh.write(text.replace("<!-- note -->\n", "<!-- note -->\nNext: send notes-r0 to writer-1.\n"))
        checkpoint.close(SID, self.root, now=self.now)
        text = self.build()
        self.assertIn("<!-- note -->\nNext: send notes-r0 to writer-1.\n<!-- /note -->", text)
        front, note = checkpoint.read_frontmatter(path)
        self.assertEqual(front["closed_at"], checkpoint.iso(self.now))
        self.assertEqual(note, "Next: send notes-r0 to writer-1.\n")

    def test_session_end_and_stop_failure(self):
        self.session([human(0, "go"), said(1, "Working.")])
        self.assertIn("status: ended", self.build(event="SessionEnd"))
        text = self.build(event="StopFailure", failure="rate_limit")
        self.assertIn("status: stopped", text)
        self.assertIn("reason: usage limit", text)

    def test_needs_resume(self):
        stopped = {"status": "stopped", "stopped_at": "2026-09-26T21:50+02:00", "closed_at": ""}
        self.assertTrue(checkpoint.needs_resume(stopped))
        self.assertFalse(checkpoint.needs_resume(dict(stopped, closed_at="2026-09-27T09:30+02:00")))
        self.assertTrue(checkpoint.needs_resume(dict(stopped, closed_at="2026-09-26T20:00+02:00")))
        self.assertFalse(checkpoint.needs_resume({"status": "working", "in_flight": "2"}))
        self.assertFalse(checkpoint.needs_resume({"status": "ended", "in_flight": "0"}))
        self.assertTrue(checkpoint.needs_resume({"status": "ended", "in_flight": "1",
                                                 "stopped_at": "2026-09-26T21:50+02:00"}))

    def test_cli_defaults_to_the_newest_session(self):
        self.session([human(0, "go")])
        out = os.path.join(self.tmp.name, "h.md")
        with contextlib.redirect_stdout(io.StringIO()):
            rc = checkpoint.main(["--transcripts", self.base, "--out", out])
        self.assertEqual(rc, 0)
        self.assertTrue(os.path.isfile(out))


if __name__ == "__main__":
    unittest.main()
