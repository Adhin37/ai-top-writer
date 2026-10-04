"""tools/session_hooks.py and tools/statusline.py - keeping the handoff current, and coming back."""
import contextlib
import io
import json
import os
import sys
import tempfile
import time
import unittest
from unittest import mock

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "tools"))

import checkpoint  # noqa: E402
import session_hooks  # noqa: E402
import statusline  # noqa: E402

FUTURE = int(time.time()) + 3600


def handoff(root, sid, **front):
    fields = {"session": sid, "title": "Plan 02", "status": "stopped", "reason": "usage limit",
              "stopped_at": "2026-09-26T21:50+02:00", "resets_at": "2026-09-27T00:20+02:00",
              "in_flight": "2", "closed_at": ""}
    fields.update(front)
    path = checkpoint.handoff_path(root, sid)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as fh:
        fh.write("---\n%s\n---\n# Handoff\n" % "\n".join("%s: %s" % kv for kv in fields.items()))


class PointerTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = self.tmp.name

    def tearDown(self):
        self.tmp.cleanup()

    def start(self, sid="new", **extra):
        return session_hooks.handle(dict({"hook_event_name": "SessionStart", "session_id": sid,
                                          "source": "startup"}, **extra), self.root)

    def test_points_at_a_stopped_session(self):
        handoff(self.root, "old")
        text = self.start()
        self.assertIn("docs/sessions/old.md", text)
        self.assertIn("usage limit", text)
        self.assertIn("2 agent(s) in flight", text)
        self.assertIn("handoff skill", text)

    def test_not_for_an_ended_closed_or_working_session(self):
        handoff(self.root, "a", status="ended", in_flight="0")
        handoff(self.root, "b", closed_at="2026-09-27T09:30+02:00")
        handoff(self.root, "c", status="working")
        self.assertIsNone(self.start())

    def test_an_ended_session_with_agents_running_counts(self):
        handoff(self.root, "a", status="ended", reason="session closed", in_flight="1")
        self.assertIn("docs/sessions/a.md", self.start())

    def test_newest_stop_first(self):
        handoff(self.root, "older", stopped_at="2026-09-25T10:00+02:00")
        handoff(self.root, "newer")
        text = self.start()
        self.assertIn("docs/sessions/newer.md", text)
        self.assertIn("1 older handoffs", text)

    def test_resuming_the_stopped_session_itself(self):
        handoff(self.root, "old")
        self.assertIn("This session stopped", self.start("old", source="resume"))

    def test_a_429_the_hooks_missed_is_found_at_the_next_start(self):
        transcripts = os.path.join(self.root, "t")
        os.makedirs(transcripts)
        old = os.path.join(transcripts, "old.jsonl")
        with open(old, "w") as fh:
            fh.write(json.dumps({"type": "ai-title", "aiTitle": "Plan 02"}) + "\n")
        checkpoint.build("old", transcripts, self.root)                  # the last Stop: working
        self.assertIsNone(self.start(transcript_path=os.path.join(transcripts, "new.jsonl")))
        with open(old, "a") as fh:                                        # then the 429 lands
            fh.write(json.dumps({"type": "assistant", "error": "rate_limit",
                                 "isApiErrorMessage": True, "message": {"content": []}}) + "\n")
        past = time.time() - 60
        os.utime(checkpoint.handoff_path(self.root, "old"), (past, past))
        text = self.start(transcript_path=os.path.join(transcripts, "new.jsonl"))
        self.assertIn("docs/sessions/old.md", text)

    def test_after_a_compaction_points_at_its_own_handoff(self):
        handoff(self.root, "other")             # an unresumed stop elsewhere is not the point
        text = session_hooks.handle({"hook_event_name": "SessionStart", "session_id": "s1",
                                     "source": "compact"}, self.root)
        self.assertIn("just compacted", text)
        self.assertIn(os.path.join("docs", "sessions", "s1.md"), text)
        self.assertIn("tools/room.py where", text)

    def test_subagents_get_nothing(self):
        handoff(self.root, "old")
        self.assertIsNone(self.start(agent_id="a1", agent_type="writer"))

    def test_a_prompt_in_a_stopped_session_is_pointed_back(self):
        handoff(self.root, "s1")
        payload = {"hook_event_name": "UserPromptSubmit", "session_id": "s1", "prompt": "continue"}
        self.assertIn("resume procedure", session_hooks.handle(payload, self.root))
        checkpoint.close("s1", self.root)
        self.assertIsNone(session_hooks.handle(payload, self.root))


class UsageTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = self.tmp.name
        self.usage = os.path.join(self.root, "docs", "sessions", "usage.json")

    def tearDown(self):
        self.tmp.cleanup()

    def reading(self, pct, resets=FUTURE, age=0, window="five_hour"):
        statusline.save({"rate_limits": {window: {"used_percentage": pct, "resets_at": resets}}},
                        self.usage)
        if age:
            with open(self.usage) as fh:
                data = json.load(fh)
            data["updated"] -= age
            with open(self.usage, "w") as fh:
                json.dump(data, fh)

    def tool(self):
        return session_hooks.handle({"hook_event_name": "PostToolUse", "session_id": "s",
                                     "tool_name": "Agent"}, self.root)

    def test_warns_once_per_window_at_the_threshold(self):
        self.reading(79)
        self.assertIsNone(self.tool())
        self.reading(94)
        self.assertIn("start no new chapter", self.tool())
        self.assertIsNone(self.tool())
        self.reading(95)
        text = self.tool()
        self.assertIn("5-hour limit is at 95%", text)
        self.assertIn("spawn no new agent", text)
        self.reading(97)
        self.assertIsNone(self.tool())
        self.reading(96, resets=FUTURE + 5 * 3600)
        self.assertIn("5-hour", self.tool())

    def test_the_pause_comes_once_per_window_and_not_after_the_hand_off(self):
        self.reading(82)
        text = self.tool()
        self.assertIn("5-hour window is at 82%", text)
        self.assertIn("Pause at a chapter boundary", text)
        self.assertNotIn("handoff skill", text)
        self.assertIsNone(self.tool())
        self.reading(83, resets=FUTURE + 5 * 3600)
        self.assertIn("start no new chapter", self.tool())

    def test_a_jump_past_the_threshold_skips_the_pause(self):
        self.reading(97)
        self.assertIn("handoff skill", self.tool())
        self.assertIsNone(self.tool())

    def test_the_weekly_window_has_no_pause(self):
        self.reading(85, window="seven_day")
        self.assertIsNone(self.tool())

    def test_the_weekly_window_too(self):
        self.reading(96, window="seven_day")
        self.assertIn("7-day limit", self.tool())

    def test_a_stale_reading_is_ignored(self):
        self.reading(99, age=session_hooks.FRESH_S + 1)
        self.assertIsNone(self.tool())

    def test_a_window_with_no_reset_time_warns_again_in_its_next_span(self):
        self.reading(96, resets=None)
        self.assertIn("5-hour limit", self.tool())
        self.assertIsNone(self.tool())
        later = time.time() + 5 * 3600 + 1
        with open(self.usage) as fh:
            data = json.load(fh)
        data["updated"] = later
        with open(self.usage, "w") as fh:
            json.dump(data, fh)
        self.assertIn("5-hour limit", session_hooks.usage_warning(self.root, now=later))

    def test_a_reading_with_a_bad_timestamp_is_ignored(self):
        self.reading(99)
        with open(self.usage) as fh:
            data = json.load(fh)
        data["updated"] = "yesterday"
        with open(self.usage, "w") as fh:
            json.dump(data, fh)
        self.assertIsNone(self.tool())

    def test_no_reading_no_warning(self):
        self.assertIsNone(self.tool())

    def test_subagents_are_not_warned(self):
        self.reading(99)
        self.assertIsNone(session_hooks.handle({"hook_event_name": "PostToolUse",
                                                "agent_id": "a1"}, self.root))

    def test_statusline_prints_the_windows(self):
        payload = {"model": {"display_name": "Opus 5.5"},
                   "rate_limits": {"five_hour": {"used_percentage": 63.4, "resets_at": FUTURE},
                                   "seven_day": {"used_percentage": 44}}}
        text = statusline.line(payload)
        self.assertTrue(text.startswith("Opus 5.5 · 5h 63% (resets "), text)
        self.assertTrue(text.endswith(" · 7d 44%"), text)
        self.assertEqual(statusline.line({}), "Claude")


class FailOpenTest(unittest.TestCase):
    def run_main(self, stdin):
        out = io.StringIO()
        with mock.patch("sys.stdin", io.StringIO(stdin)), contextlib.redirect_stdout(out), \
                contextlib.redirect_stderr(io.StringIO()):
            rc = session_hooks.main()
        return rc, out.getvalue()

    def test_malformed_payloads_exit_zero_and_say_nothing(self):
        for stdin in ("", "not json", "[]", "null", '{"hook_event_name": "Stop"}',
                      '{"hook_event_name": "Stop", "session_id": "x", "transcript_path": "/nope"}',
                      '{"hook_event_name": "Mystery", "session_id": 5}'):
            self.assertEqual(self.run_main(stdin), (0, ""), stdin)

    def test_a_crash_inside_exits_zero(self):
        with mock.patch.object(session_hooks, "handle", side_effect=RuntimeError("boom")):
            self.assertEqual(self.run_main('{"hook_event_name": "Stop"}'), (0, ""))

    def test_context_is_printed_as_hook_json(self):
        with mock.patch.object(session_hooks, "handle", return_value="hello"):
            rc, out = self.run_main('{"hook_event_name": "SessionStart"}')
        self.assertEqual(json.loads(out), {"hookSpecificOutput": {
            "hookEventName": "SessionStart", "additionalContext": "hello"}})

    def test_stop_rebuilds_the_handoff(self):
        with tempfile.TemporaryDirectory() as tmp:
            transcript = os.path.join(tmp, "t", "s9.jsonl")
            os.makedirs(os.path.dirname(transcript))
            with open(transcript, "w") as fh:
                fh.write(json.dumps({"type": "ai-title", "aiTitle": "Plan 02"}) + "\n")
            session_hooks.handle({"hook_event_name": "Stop", "session_id": "s9",
                                  "transcript_path": transcript}, tmp)
            front, _ = checkpoint.read_frontmatter(checkpoint.handoff_path(tmp, "s9"))
        self.assertEqual(front["title"], "Plan 02")
        self.assertEqual(front["status"], "working")


if __name__ == "__main__":
    unittest.main()
