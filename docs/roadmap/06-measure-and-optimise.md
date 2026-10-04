# 06 — Session 7: measurement

**Goal:** see what the book does across chapters and what each role costs, per chapter, before
any lever is pulled. Nothing in this plan spawns an agent: the trace reads transcripts and the
detectors read chapters. The levers are in [06b](06b-showrunner-cost.md) and
[06c](06c-role-levers.md). The user's instruction was quality first and tokens later. This is later,
and on a Pro plan the usage limit is what binds.

## Part A — measurement

### 1. Extend the trace

[01b](01b-wire-format.md) built `tools/trace.py`: per role, the thinking and visible output, cache
reads and writes, cost, the showrunner's context, and hand-back sizes, scoped by session id. Add:

- **Per role:** model seconds against tool seconds (from timestamps), and which `kb/` docs were
  opened.
- **Per chapter:** the same, plus loop rounds.
- **An unpriced model is flagged** (done in plan 02): it used to count as $0 without a word.
- **The Sonnet roles' final messages.** In plan 02 the continuity editor wrapped its status line in
  a recap three times, through two template fixes, then was clean twice, but only after the
  `sonnet` alias moved to Sonnet 5.5. Find out which of the two did it before tuning the
  templates further.
- **The known under-count is flagged** (done after 01's ITERATE re-run). Every agent's final
  response, the one that calls `SubagentHandback`, is written to its transcript before its usage
  lands. `trace.py` reports it on its own line: tokens estimated from the hand-back's length, a
  lower bound, kept out of the recorded totals.
  - Plan 01: at least $3.08, mostly judges.
  - The ITERATE re-run: at least $0.70.
  - The thinking behind that response cannot be recovered.
- **Cache expiries.** Per role, the requests that follow a gap longer than the agent's cache TTL,
  and the tokens they re-wrote. Run #7's warm writer re-wrote ~675k tokens this way (~$3.4 of
  $13.23). The same line for the showrunner, per usage-limit pause.
- **Injected context.** Per role, the size of what Claude Code adds to an agent's context that no
  role asked for: `ide_diagnostics`, MCP instructions, other attachments. Run #7's planner got
  ~151k characters of markdownlint warnings.
- **Effort per spawn.** Read it from the agent file at spawn time, so a result is never credited to
  the wrong level. Every role ran at `high` in run #7, the showrunner at `xhigh`.
- **Opened docs from the guard.** `tools/guard.py` already sees every `Read` with the caller's role.
  Have it append `role, path` to a log under `docs/sessions/`, so "which `kb/` docs were opened" is
  exact, not parsed out of transcripts.
- **A cross-check.** Compare one session's per-role shares with `/usage`'s plan breakdown, which
  attributes usage to subagents. If they disagree by more than a few points, find out why before
  trusting either.

### 2. Port the cross-chapter detectors

From `cmd_history.py`, as `tools/history.py`. The line editor and the story editor run it from
chapter 3 onwards, and at every arc boundary. All four were tuned on runs #5 and #6, and both
readers named the patterns.

- **Signature phrases.** Three-to-five-word phrases, with no proper nouns and no lexicon words, that
  recur across chapters or across mouths.
- **Two-hander runs.** The share of recent conversations with two named speakers or fewer.
- **Tempo and temperature runs** from `state/scenes.md`.
- **Motif echo** across chapters. The old repo's `echo` check only looked within one chapter, and a
  phrase travelled from a roster line into four chapters.

They produce findings for a critic to weigh. They do not gate.

Run #7's evidence for the motif check: "Old ones hold their shape" four times and "broad as a
barrel-head" four times across five chapters, which all three judges named. The line editor's
two-chapter window kept the refrain as a callback each time it met it; its doc now asks it to search
every earlier chapter first (lesson 28). A tool that lists the repeats would give it the count.

## Part B moved: 06b and 06c

The optimisation levers are split by what it costs to check them on a Pro plan
([research, 2026-10-04](../experiments/2026-10-04-cost-levers.md)):

- [06b](06b-showrunner-cost.md): **levers that change no role's judgement**: the showrunner's
  context and turns, its effort, and noise injected into agents' contexts. Checked by the trace
  and by routing, with no judge.
- [06c](06c-role-levers.md): **levers that can change the book**: effort, model and read-set per
  role, loop pruning. Each needs a blind comparison, run on frozen inputs to keep it cheap.

## Exit criteria

- Cost and time per role are known, per chapter, with cache expiries, injected context and effort
  on their own lines.
- The cross-chapter detectors run in the loop.
- The trace report on run #7 is in `docs/experiments/`, as 06b's and 06c's baseline.

## Session log

*(filled in when this plan runs)*
