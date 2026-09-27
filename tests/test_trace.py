"""tools/trace.py - a session's cost per role, counted once per response, from transcripts."""
import contextlib
import io
import json
import os
import sys
import tempfile
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "tools"))

import trace  # noqa: E402

OPUS = "claude-opus-5-5"


def usage(output, thinking=0, read=0, w5=0, w1=0, inp=0):
    return {"input_tokens": inp, "cache_read_input_tokens": read,
            "cache_creation_input_tokens": w5 + w1, "output_tokens": output,
            "cache_creation": {"ephemeral_5m_input_tokens": w5, "ephemeral_1h_input_tokens": w1},
            "output_tokens_details": {"thinking_tokens": thinking}}


def assistant(ts, mid, u, blocks=None, req="req-" + "x"):
    return {"type": "assistant", "timestamp": ts, "requestId": req + mid,
            "message": {"id": mid, "model": OPUS, "usage": u, "content": blocks or []}}


def user(ts, content):
    return {"type": "user", "timestamp": ts, "message": {"role": "user", "content": content}}


def write(path, rows):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as fh:
        for row in rows:
            fh.write(json.dumps(row) + "\n")
        fh.write("half-written line\n")


class TraceTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.base = self.tmp.name
        sess = "0123abcd-0000"
        spawn = {"type": "tool_use", "id": "tu1", "name": "Agent", "input": {}}
        write(os.path.join(self.base, sess + ".jsonl"), [
            user("2026-01-01T00:00:00.000Z", "go"),
            # one response, streamed as two rows repeating the usage; output is a running counter
            assistant("2026-01-01T00:00:02.000Z", "m1", usage(5, 0, read=1000, w5=100)),
            assistant("2026-01-01T00:00:04.000Z", "m1", usage(50, 30, read=1000, w5=100),
                      [spawn]),
            user("2026-01-01T00:00:10.000Z",
                 [{"type": "tool_result", "tool_use_id": "tu1", "content": "x" * 400}]),
            assistant("2026-01-01T00:00:11.000Z", "m2", usage(10, 0, read=2000)),
            user("2026-01-01T00:00:20.000Z", "[Subagent hand-back] " + "y" * 779),
            # a hand-back that lands mid-turn is queued as an attachment row
            {"type": "attachment", "timestamp": "2026-01-01T00:00:20.500Z",
             "attachment": {"type": "queued_command",
                            "prompt": "[Subagent hand-back] " + "z" * 379}},
            assistant("2026-01-01T00:00:21.000Z", "m3", usage(10, 0, read=3000)),
        ])
        sub = os.path.join(self.base, sess, "subagents", "agent-a1.jsonl")
        write(sub, [user("2026-01-01T00:00:05.000Z", "draft"),
                    assistant("2026-01-01T00:00:08.000Z", "s1", usage(1000, 600, w1=500))])
        with open(sub[:-len(".jsonl")] + ".meta.json", "w", encoding="utf-8") as fh:
            json.dump({"agentType": "writer", "description": "writer L1 round 0"}, fh)
        self.paths = trace.transcripts_for("0123", self.base)

    def tearDown(self):
        self.tmp.cleanup()

    def test_rows_of_one_response_are_counted_once(self):
        t = trace.Transcript(self.paths[0])
        self.assertEqual(len(t.responses), 3)
        first = t.responses[0]
        self.assertEqual((first.output, first.thinking, first.read, first.write_5m),
                         (50, 30, 1000, 100))
        self.assertAlmostEqual(first.model_s, 4.0)

    def test_cost_per_role(self):
        result = trace.summarise(self.paths)
        writer = result["roles"]["writer"]
        # output 1000 x $20 + 1-hour write 500 x $4 x 2, per million
        self.assertAlmostEqual(writer["cost"], (1000 * 20 + 500 * 8) / 1e6)
        self.assertEqual((writer["spawns"], writer["thinking"]), (1, 600))
        show = result["roles"]["showrunner"]
        self.assertEqual((show["responses"], show["output"], show["cache_read"]), (3, 70, 6000))
        self.assertAlmostEqual(result["total"], writer["cost"] + show["cost"])

    def test_handbacks_entering_the_showrunner(self):
        s = trace.summarise(self.paths)["showrunner"]
        self.assertEqual(s["handbacks"], 3)
        self.assertAlmostEqual(s["handback_tokens"], 100 + 200 + 100)
        # the tool result is read again by m2 and m3; the hand-back message and attachment by m3
        self.assertAlmostEqual(s["handback_rereads"], 100 * 2 + 200 * 1 + 100 * 1)
        self.assertEqual(s["context_peak"], 3000)

    def test_window_and_match(self):
        early = trace.summarise(self.paths, until="2026-01-01T00:00:15")
        self.assertEqual(early["roles"]["showrunner"]["responses"], 2)
        only = trace.summarise(self.paths, match="round 0")
        self.assertEqual(set(only["roles"]), {"writer"})
        self.assertEqual(trace.summarise(self.paths, match="round 1")["roles"], {})

    def test_cli(self):
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            rc = trace.main(["0123", "--transcripts", self.base, "--agents"])
        self.assertEqual(rc, 0)
        self.assertIn("writer L1 round 0", buf.getvalue())
        with contextlib.redirect_stderr(io.StringIO()):
            self.assertEqual(trace.main(["ffff", "--transcripts", self.base]), 1)


if __name__ == "__main__":
    unittest.main()
