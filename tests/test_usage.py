"""usage.py - the usage windows estimated from the transcripts, where no status line runs."""
import datetime as dt
import json
import os
import sys
import tempfile
import time
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, ".claude", "skills", "handoff", "scripts"))

import session_hooks  # noqa: E402
import usage  # noqa: E402

H = 3600
# an hour mark, two days back: the past window and today's both sit inside KEEP_S
BASE = (int(time.time()) // H - 48) * H
OUTPUT_ONLY = 1e6 / 25          # output tokens that cost $1 on opus


def call(t, dollars, mid, model="claude-opus-5-5"):
    return {"type": "assistant", "timestamp": dt.datetime.fromtimestamp(t).astimezone().isoformat(),
            "requestId": "r" + mid,
            "message": {"id": mid, "model": model,
                        "usage": {"input_tokens": 0, "output_tokens": dollars * OUTPUT_ONLY}}}


def rejection(t, resets, kind="five_hour"):
    return {"type": "assistant", "timestamp": dt.datetime.fromtimestamp(t).astimezone().isoformat(),
            "error": "rate_limit", "isApiErrorMessage": True,
            "quotaLimits": {"status": "rejected", "rateLimitType": kind, "resetsAt": resets}}


class UsageTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = os.path.join(self.tmp.name, "repo")
        self.projects = os.path.join(self.tmp.name, "projects")
        os.makedirs(os.path.join(self.projects, "p", "s1", "subagents"))
        self.main = os.path.join(self.projects, "p", "s1.jsonl")
        self.agent = os.path.join(self.projects, "p", "s1", "subagents", "agent-a.jsonl")

    def tearDown(self):
        self.tmp.cleanup()

    def write(self, path, rows, mode="a"):
        with open(path, mode, encoding="utf-8") as fh:
            for row in rows:
                fh.write(json.dumps(row) + "\n")

    def history(self):
        """A past window spent at $40 across the main session and an agent, then rejected."""
        self.write(self.main, [call(BASE + 60, 10, "m1"), call(BASE + 2 * H, 10, "m2"),
                               rejection(BASE + 3 * H, BASE + 5 * H)])
        self.write(self.agent, [call(BASE + H, 20, "a1")])

    def test_cost_at_list_price(self):
        u = {"input_tokens": 1e6, "output_tokens": 1e6, "cache_read_input_tokens": 1e6,
             "cache_creation_input_tokens": 2e6,
             "cache_creation": {"ephemeral_1h_input_tokens": 1e6}}
        self.assertAlmostEqual(usage.cost("claude-opus-5-5", u), 5 + 25 + 0.5 + 6.25 + 10)
        self.assertAlmostEqual(usage.cost("claude-sonnet-5-5", {"output_tokens": 1e6}), 15)
        self.assertEqual(usage.cost("<synthetic>", u), 0)

    def test_a_rejection_sets_the_cap_and_the_current_window_is_measured_against_it(self):
        self.history()
        now = BASE + 30 * H
        self.write(self.main, [call(BASE + 28 * H + 5 * 60, 30, "m3"),
                               call(BASE + 29 * H, 8, "m4")])
        result = usage.estimate(self.root, self.projects, now=now)
        five = result["rate_limits"]["five_hour"]
        self.assertEqual(result["detail"]["five_hour"]["cap"], 40)
        self.assertEqual(five["used_percentage"], 95)
        self.assertEqual(five["resets_at"], BASE + 33 * H)          # 28h, on its 10-minute mark
        self.assertEqual(result["source"], "estimate")

    def test_a_streamed_message_counts_once(self):
        self.history()
        self.write(self.main, [call(BASE + 28 * H, 5, "m3"), call(BASE + 28 * H, 10, "m3")])
        result = usage.estimate(self.root, self.projects, now=BASE + 29 * H)
        self.assertEqual(result["detail"]["five_hour"]["spent"], 10)

    def test_no_rejection_on_file_no_estimate(self):
        self.write(self.main, [call(BASE, 10, "m1")])
        self.assertEqual(usage.estimate(self.root, self.projects, now=BASE + H)["rate_limits"], {})

    def test_no_open_window_is_zero(self):
        self.history()
        result = usage.estimate(self.root, self.projects, now=BASE + 20 * H)
        self.assertEqual(result["rate_limits"]["five_hour"]["used_percentage"], 0)

    def test_the_scan_is_incremental_and_keeps_its_caps(self):
        self.history()
        usage.estimate(self.root, self.projects, now=BASE + 28 * H, max_age=0)
        self.write(self.main, [call(BASE + 28 * H, 20, "m3")])
        with open(self.main, "a") as fh:
            fh.write('{"type": "assistant", "half a li')        # still being written
        result = usage.estimate(self.root, self.projects, now=BASE + 29 * H, max_age=0)
        self.assertEqual(result["rate_limits"]["five_hour"]["used_percentage"], 50)
        with open(os.path.join(self.root, "docs", "sessions", usage.CACHE)) as fh:
            self.assertEqual(json.load(fh)["caps"]["five_hour"], {str(BASE + 5 * H): 40})

    def test_a_recent_estimate_is_reused(self):
        self.history()
        first = usage.estimate(self.root, self.projects, now=BASE + 28 * H)
        self.write(self.main, [call(BASE + 28 * H, 20, "m3")])
        self.assertEqual(usage.estimate(self.root, self.projects, now=BASE + 28 * H + 30), first)

    def test_the_cap_is_the_lowest_recent_one_outliers_aside(self):
        self.assertEqual(usage.cap({"1": 50, "2": 44, "3": 48, "4": 10, "5": 55}), 44)
        self.assertIsNone(usage.cap({}))

    def test_the_weekly_window_rolls_on_from_its_last_reset(self):
        week = usage.SPAN_S["seven_day"]
        start, end = usage.window("seven_day", [], [BASE], BASE + 2 * week + H)
        self.assertEqual((start, end), (BASE + 2 * week, BASE + 3 * week))

    def test_the_hook_warns_from_the_estimate(self):
        self.history()
        self.write(self.main, [call(time.time() - 60, 39, "m3")])
        text = session_hooks.handle({"hook_event_name": "PostToolUse", "session_id": "s1",
                                     "transcript_path": self.main}, self.root)
        self.assertIn("5-hour limit is at 97% (estimated from the transcripts)", text)
        self.assertIn("handoff skill", text)


if __name__ == "__main__":
    unittest.main()
