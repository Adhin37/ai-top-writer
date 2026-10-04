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


def sub(base, sess, agent, role, description, tool_use, rows):
    path = os.path.join(base, sess, "subagents", "agent-%s.jsonl" % agent)
    write(path, rows)
    with open(path[:-len(".jsonl")] + ".meta.json", "w", encoding="utf-8") as fh:
        json.dump({"agentType": role, "description": description, "toolUseId": tool_use}, fh)


def spawn(tid, description, prompt):
    return {"type": "tool_use", "id": tid, "name": "Agent",
            "input": {"description": description, "prompt": prompt}}


def send(tid, to, message):
    return {"type": "tool_use", "id": tid, "name": "SendMessage",
            "input": {"to": to, "summary": "x", "message": message}}


def handback(message):
    return {"type": "tool_use", "id": "hb" + str(len(message)), "name": "SubagentHandback",
            "input": {"message": message}}


def read(tid, path):
    return {"type": "tool_use", "id": tid, "name": "Read", "input": {"file_path": path}}


def result(tid, ts):
    return user(ts, [{"type": "tool_result", "tool_use_id": tid, "content": "ok"}])


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

    def test_an_unpriced_model_is_named_not_silently_free(self):
        sub = os.path.join(self.base, "0123abcd-0000", "subagents", "agent-a2.jsonl")
        row = assistant("2026-01-01T00:00:09.000Z", "s2", usage(500))
        row["message"]["model"] = "claude-newmodel-9"
        write(sub, [user("2026-01-01T00:00:08.500Z", "read"), row])
        result = trace.summarise(trace.transcripts_for("0123", self.base))
        self.assertEqual(result["unpriced"], {"claude-newmodel-9": 1})
        self.assertIn("warn: no rate for claude-newmodel-9", trace.render(result))
        self.assertEqual(trace.summarise(self.paths)["unpriced"], {})

    def test_handbacks_entering_the_showrunner(self):
        s = trace.summarise(self.paths)["showrunner"]
        self.assertEqual(s["handbacks"], 3)
        self.assertAlmostEqual(s["handback_tokens"], 100 + 200 + 100)
        # the tool result is read again by m2 and m3; the hand-back message and attachment by m3
        self.assertAlmostEqual(s["handback_rereads"], 100 * 2 + 200 * 1 + 100 * 1)
        self.assertEqual(s["context_peak"], 3000)

    def test_unrecorded_final_response(self):
        sess = "4567ef-0000"
        write(os.path.join(self.base, sess + ".jsonl"), [user("2026-01-01T00:00:00.000Z", "go")])
        final = {"type": "tool_use", "id": "tu9", "name": "SubagentHandback",
                 "input": {"message": "r" * 785}}             # 800 characters as JSON
        sub = os.path.join(self.base, sess, "subagents", "agent-a2.jsonl")
        write(sub, [user("2026-01-01T00:00:01.000Z", "read"),
                    assistant("2026-01-01T00:00:02.000Z", "j1", usage(400), [
                        {"type": "tool_use", "id": "tu8", "name": "Read", "input": {}}]),
                    # the hand-back response: its usage never got past the first token
                    assistant("2026-01-01T00:00:09.000Z", "j2", usage(3), [final])])
        result = trace.summarise(trace.transcripts_for("4567", self.base))
        role = result["roles"]["subagent"]
        self.assertEqual(role["output"], 403)                 # recorded totals are untouched
        self.assertAlmostEqual(role["unrecorded"], 800 / 4.0 - 3)
        self.assertAlmostEqual(result["unrecorded_usd"], (800 / 4.0 - 3) * 20 / 1e6)
        self.assertIn("unrecorded output", trace.render(result))
        self.assertEqual(trace.summarise(self.paths)["unrecorded_usd"], 0)

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


class RoomTraceTest(unittest.TestCase):
    """A two-chapter session: a planner continued warm from ch 1's fold into ch 2's beats, a writer
    continued after its cache lapsed, injected context, final messages, and Claude Code's count."""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        base, sess = self.tmp.name, "beef-0000"
        t = "2026-01-01T00:%02d:%02d.000Z"
        write(os.path.join(base, sess + ".jsonl"), [
            user(t % (0, 0), "go"),
            assistant(t % (0, 1), "m1", usage(10, read=100),
                      [spawn("sp1", "planner-ch01", "Novel: n. Task: beats for chapter 1.")]),
            result("sp1", t % (1, 0)),
            assistant(t % (1, 1), "m2", usage(10, read=100),
                      [spawn("sp2", "writer-ch01", "Novel: n. Chapter 1. Write work/ch0001/"
                                                   "draft-r0.md.")]),
            result("sp2", t % (2, 0)),
            assistant(t % (2, 1), "m3", usage(10, read=100),
                      [send("se1", "w1", "Notes: n/work/ch0001/notes-r0.md. Write draft-r1.md.")]),
            result("se1", t % (9, 0)),
            assistant(t % (9, 1), "m4", usage(10, read=100),
                      [send("se2", "p1", "Task: fold chapter 1. Fold file: n/work/ch0001/fold.md")]),
            result("se2", t % (10, 0)),
            # between chapters: the showrunner's own turn goes to the next chapter
            assistant(t % (10, 30), "m5", usage(10, read=100)),
            assistant(t % (11, 1), "m6", usage(10, read=100),
                      [send("se3", "p1", "Task: beats for chapter 2.")]),
            result("se3", t % (12, 0)),
            {"type": "attachment", "timestamp": t % (12, 1),
             "attachment": {"type": "mcp_instructions_delta", "addedBlocks": ["m" * 300]}},
            {"type": "cost-state", "modelUsage": {OPUS: {
                "inputTokens": 0, "outputTokens": 99999, "thinkingTokens": 0,
                "cacheReadInputTokens": 0, "cacheCreationInputTokens": 0, "costUSD": 9.0}},
             "totalCostUSD": 9.0},
        ])
        sub(base, sess, "p1", "planner", "planner-ch01", "sp1", [
            user(t % (0, 2), "beats"),
            dict(assistant(t % (0, 5), "p1a", usage(100, 60, w5=1000),
                           [read("r1", "/x/kb/planner/beat-sheet.md")]), effort="high"),
            result("r1", t % (0, 7)),
            dict(assistant(t % (0, 50), "p1b", usage(5, w5=10),
                           [handback("PLANNER DONE beats | n/work/ch0001/beats.md | gaps 0 | "
                                     "changed 0")]), effort="high"),
            user(t % (9, 2), "Task: fold chapter 1."),
            dict(assistant(t % (9, 30), "p1c", usage(50, read=1000, w5=10)), effort="medium"),
            user(t % (12, 2), "Task: beats for chapter 2."),
            dict(assistant(t % (12, 40), "p1d", usage(70, read=1000, w5=10)), effort="medium"),
            {"type": "attachment", "timestamp": t % (12, 41),
             "attachment": {"type": "hook_additional_context", "hookName": "PostToolUse:Edit",
                            "content": ["<ide_diagnostics>" + "d" * 483 + "</ide_diagnostics>"]}},
        ])
        sub(base, sess, "w1", "writer", "writer-ch01", "sp2", [
            user(t % (1, 2), "draft"),
            assistant(t % (1, 50), "w1a", usage(2000, w5=5000)),
            # continued 7 minutes later: past the 5-minute cache, it writes its context again
            user(t % (9, 2), "Notes: notes-r0.md. Write draft-r1.md."),
            assistant(t % (9, 40), "w1b", usage(1500, read=100, w5=6000), [handback(
                "DRAFT READY n/work/ch0001/draft-r1.md | facts f | new 0 | stets 0 | "
                "couldn't 0\nI also re-read the whole bible and here is a recap of it.")]),
        ])
        self.paths = trace.transcripts_for("beef", base)
        self.result = trace.summarise(self.paths, log=None)

    def tearDown(self):
        self.tmp.cleanup()

    def test_a_warm_agent_is_split_between_the_chapters_it_worked_on(self):
        ch = self.result["chapters"]
        self.assertEqual(ch["1"]["planner"]["responses"], 3)        # beats, hand-back, fold
        self.assertEqual(ch["2"]["planner"]["responses"], 1)        # beats for chapter 2
        self.assertEqual(ch["1"]["writer"]["responses"], 2)
        self.assertEqual(ch["1"]["showrunner"]["responses"], 4)
        self.assertEqual(ch["2"]["showrunner"]["responses"], 2)     # m5, between chapters, and m6
        self.assertEqual(self.result["rounds"], {"1": [0, 1]})
        self.assertIn("per chapter", trace.render(self.result, show_chapters=True))

    def test_tool_seconds_belong_to_the_response_that_called_the_tool(self):
        self.assertAlmostEqual(self.result["roles"]["planner"]["tool_s"], 2.0)
        self.assertAlmostEqual(self.result["roles"]["showrunner"]["tool_s"], 59 + 59 + 419 + 59 + 59)

    def test_effort_is_read_per_response(self):
        self.assertEqual(self.result["roles"]["planner"]["effort"], {"high": 2, "medium": 2})
        self.assertIn("planner high 2, medium 2", trace.render(self.result))

    def test_a_request_after_the_cache_lapsed_rewrites_it(self):
        writer = self.result["roles"]["writer"]
        self.assertEqual((writer["expiries"], writer["expiry_tokens"]), (1, 6000))
        self.assertAlmostEqual(writer["expiry_usd"], 6000 * 4 * 1.25 / 1e6)
        # the planner's fold came 8 minutes after its last request but read its context from
        # cache (1000 read, 10 written): a hit, not an expiry
        self.assertEqual(self.result["roles"]["planner"]["expiries"], 0)
        self.assertIn("cache expiries", trace.render(self.result))

    def test_injected_context_by_kind(self):
        planner = self.result["roles"]["planner"]
        self.assertEqual(planner["injected"]["ide_diagnostics"], 483 + 35)
        self.assertEqual(self.result["roles"]["showrunner"]["injected"], {"mcp": 300})
        self.assertIn("ide_diagnostics", trace.render(self.result))

    def test_final_messages_are_checked_as_status_lines(self):
        f = self.result["finals"]
        self.assertEqual((f["planner"]["clean"], f["writer"]["extra"]), (1, 1))
        self.assertIn("writer-ch01 (extra)", trace.render(self.result))

    def test_kb_docs_from_transcripts_or_the_guard_log(self):
        self.assertEqual(self.result["docs"], {"planner": {"kb/planner/beat-sheet.md": 1}})
        self.assertEqual(self.result["docs_source"], "transcripts")
        logged = trace.summarise(self.paths, log=[
            ("2026-01-01T00:00:06Z", "p1", "planner", "kb/planner/prompt.md"),
            ("2026-01-01T00:00:06Z", "w1", "writer", "/x/kb/writer/prompt.md"),
            ("2026-01-01T00:00:06Z", "w1", "writer", "novels/n/bible/world.md")])
        self.assertEqual(logged["docs"], {"planner": {"kb/planner/prompt.md": 1},
                                          "writer": {"kb/writer/prompt.md": 1}})
        self.assertEqual(logged["docs_source"], "guard log")

    def test_cross_check_against_claude_codes_count(self):
        cc = self.result["crosscheck"]
        m = cc["models"][OPUS]
        self.assertEqual(m["cc_output"] - m["trace_output"], 99999 - sum(
            r["output"] for r in self.result["roles"].values()))
        self.assertFalse(m["input_side_equal"])
        # the whole gap is allotted to the roles on that model
        allotted = sum(r["allotted"] for r in cc["roles"].values())
        self.assertAlmostEqual(allotted, (99999 - 3725 - 60) * 20 / 1e6, places=6)
        self.assertIsNone(trace.summarise(self.paths, since="2026-01-01T00:05", log=None)[
            "crosscheck"])

    def test_dispatch_tags(self):
        d = trace.dispatch("2026-01-01T00:00:00Z", spawn("x", "story editor ch02 r1",
                                                          "Novel: n. Chapter 2, round 1."))
        self.assertEqual((d["chapter"], d["round"]), (2, 1))
        d = trace.dispatch("2026-01-01T00:00:00Z", spawn("x", "planner-ch03",
                                                          "Task: fold chapter 2. Fold file: x"))
        self.assertEqual((d["chapter"], d["round"]), (2, None))
        d = trace.dispatch("2026-01-01T00:00:00Z", send("x", "a", "Task: plan. Debt: due ch 1"))
        self.assertIsNone(d["chapter"])


if __name__ == "__main__":
    unittest.main()
