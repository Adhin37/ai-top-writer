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

**2026-10-04.** No agent was spawned. Baseline report:
[docs/experiments/2026-10-04-trace-run-7.md](../experiments/2026-10-04-trace-run-7.md).

**Part A.1, the trace** (`tools/trace.py`; 16 tests, 9 new). Each item, built or decided:

- **Per role, model seconds against tool seconds:** built. A tool's seconds belong to the
  response that called it.
- **Per chapter, the same plus rounds:** built (`--chapters`). Every dispatch names its chapter
  (`chapter N`, `work/chNNNN/`), and each agent response follows the dispatch that started it, so
  a warm planner is split between the fold and the next beats. Run #7's split agrees with its
  hand-cut windows within $0.1 a chapter.
- **The kb docs each role opened:** built. Per role from the transcripts, or from the guard's log
  when it has one (`--docs` lists the docs never opened). It is not split per chapter, since
  nothing needed it.
- **Effort:** built, but from the transcripts, not the agent file. Claude Code writes `effort` on
  every assistant row, so the level is the one each response ran at. Better than the plan's
  reading at spawn time, and no hook was needed.
- **The Sonnet roles' final messages:** built. Every status-line role's final messages are parsed
  (`wire.py`). **Answered: the model did it.** Ch 3 r0 on Sonnet 5 recapped, and ch 3 r1–r2 on
  Sonnet 5.5 were clean, reading byte-identical templates. No more template tuning; lesson 23
  extended.
- **The under-count:** generalised. Sonnet loses its usage on ordinary tool-call responses too
  (147 in run #7), not only the final one. The lower bound now covers every stale response
  (lesson 30).
- **Cache expiries:** built: a gap past the TTL, *and* more written than read. The second
  condition removed one false positive, a writer continuation 5.0 minutes after that still hit.
  The showrunner gets one line per pause.
- **Injected context:** built. IDE diagnostics, MCP instructions, other hooks and the harness, in
  characters, per role.
- **Opened docs from the guard:** built. `tools/guard.py` appends every allowed Read to
  `docs/sessions/<session>.reads.tsv`, and never blocks on it (3 tests).
- **Cross-check:** `/usage` is interactive and per-window, so it cannot be read for a past
  session. Claude Code's own `cost-state` row in the same transcript can.
  - The input side matches to the token.
  - Output is short by $4.88 (5.9%), all of it the under-count above.
  - The trace now allots each model's gap to its roles. The showrunner's share is 41.3% allotted
    (43.9% as traced). The Sonnet roles and the judge rise.
  - Reading `/usage` once in a live session is moved to 06b's first chapter.

**Part A.2, the detectors** (`tools/history.py`; 7 tests):

- **What it does:** `motif` and `signature` lines for the line editor, `two-hander` and
  `tempo`/`temp` lines for the story editor, as `level check: detail` under each owner. Nothing
  gates.
- **Motif** is new, not a port. It counts a phrase that comes back whole, at every use, across
  the whole book, and names the bible line it came from. It merges a refrain broken by a clause,
  and extends a use along its shared, all-common-word tail.
- **Signature** is skilled-writer's rule unchanged, minus what a motif already covers.
- **On run #7:**
  - It found both refrains all three judges named, at the judges' counts (x4, x4), and traced
    "broad as a barrel-head" to `bible/world.md:15`.
  - It found the judge's "hand flat on" gesture (x5).
  - Its two-hander warning fires from ch 3, one chapter before the in-loop reader's "another
    conversation in which nobody will say anything useful would lose me".
- **In the loop:** the showrunner runs it from chapter 3 on, every round, with the draft in it
  (`work/chNNNN/history-rK.txt`, `kb/showrunner/loop.md` step 3). The story editor and the line
  editor get the path. Their `across-chapters.md` docs say which lines are theirs. The line
  editor's "search every earlier chapter" became "count its earlier uses: the report does it".
- **"At every arc boundary"** adds nothing to "from chapter 3 on", because no planned arc ends
  before chapter 3, so there is no separate arc-boundary run.

**Not live-checked** (test by parts): the guard's log, and the two editors reading the report,
are first exercised by the next run that writes a chapter (06b's pilot).

Tests 209 → 228 (all OK); `kb_check` clean.
