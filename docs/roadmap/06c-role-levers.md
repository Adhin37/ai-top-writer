# 06c — Session 7c: the roles' levers, tested blind and cheaply

**Goal:** reduce what the roles cost without losing run #7's quality. **Keep a change only if a
blind comparison cannot tell it from the baseline.** The user reads nothing during the rebuild, a
standing decision. Test one lever at a time. On a Pro plan the comparisons are the expensive part,
so this plan spends most of its design on making them cheap.
Evidence and sources: [2026-10-04 research](../experiments/2026-10-04-cost-levers.md).

Depends on 06 (the trace's per-chapter and effort lines) and on 06b (a cheaper showrunner makes
every test run cheaper).

## How to compare cheaply

- **Replay one role on frozen inputs.** Run #7 left every round's inputs on disk: beat sheets,
  drafts, reader reports, notes, facts files. Copy them into `bench/<lever>/` and re-run one role
  with one lever changed. This costs a fraction of a chapter. Run a full loop only where the lever
  is the loop itself.
- **Compare critics by agreement first.** A critic's output can be compared without a judge:
  - same verdict (ACCEPT / REVISE);
  - the same notes, matched by quote;
  - the same continuity findings, against the baseline's and against 02's two real catches.

  A judge reads only the disagreements.
- **Blind pairwise, both orders.** Each pair is judged twice with the order swapped, so position
  bias cancels. Keep the judge pinned to `claude-opus-5`, as calibrated. When the arms differ in
  model (Sonnet against Opus prose), say in the write-up that an Opus judge may prefer Opus-like
  prose.
- **A/A once.** Before the first lever, judge two baseline replays of the same input. If the panel
  "tells them apart", it cannot decide a lever at that size: add pairs, or stop.
- **Ask before spending.** Every spawn here exists only to test, so the plan states each lever's
  budget, and the session asks the user before running it (standing preference). Stop a lever as
  soon as its first comparison clearly loses.

## Levers, by expected saving against test cost

1. **Loop pruning: cap at one revision round.** This test needs no new loop run.
   - Run #7: four of five chapters went to round 2, whose ACCEPT is forced.
   - Their round-1 notes numbered 3, 4, 3 and 1; the round-2 readers gave 4, 5, 4 and 5.
   - Test: judge each chapter's round-1 against its round-2 draft blind, both orders, from what is
     on disk. If the judges cannot tell them apart, cap at one round. A round costs a writer
     continuation, two readers and a story editor.
   - The same data answers the second question: did the continuity editor find anything after
     chapter 3? If not, run it every other chapter.
2. **Effort `high` → `medium` on the critics.** `medium` is Claude Code's own default for these
   models; every role was raised to `high`. Thinking was 71% of the continuity editor's output,
   69% of the story editor's and 59% of the line editor's. Test by agreement on frozen rounds,
   continuity editor first, then story editor and line editor. `low` only if `medium` holds.
3. **The continuity editor's read-set.** It reads ~65k tokens a spawn, and its cache writes ($2.29)
   are four times its output ($0.55). Give it the lint and `state_check` output and the bible
   entries the draft's names touch, not the whole bible. Test by findings agreement.
   - **Free in the same pass:** drop `kb/` docs that no role opened (06's guard log).
4. **The clerk on Haiku 4.5.** Mechanical work, and Haiku's older tokenizer adds a second saving.
   `state_check.py` and the next continuity pass check it, with no judge.
   - The beta reader on Haiku stays deferred: a calibrated instrument changes only with its
     calibration (plan 01's).
   - That calibration run can also take 01b's deferred change, the report's lists in wire form,
     as its own arm.
5. **The writer's revisions on Sonnet**, round 0 staying on Opus. Blind pairwise on each revised
   draft. Do it only if lever 1 keeps revision rounds alive.
6. **Planner effort `high` → `medium`** (thinking 56%, $5.69 of output). Test beat sheets through
   the story editor's reading of the resulting chapter. Last, because a beat sheet's effect shows
   only a chapter later.
7. **The warm writer across chapters** (the old lever 1). The cache gives nothing here: run #7's
   writer already lost it between rounds 5.5 minutes apart. Keep it only for time or quality (run
   #6: drafter time halved).

Re-check the wire format across an arc from the trace (hand-backs stay one line, notes files do not
grow). It is free.

Set aside, with reasons in the research note: Fable (usage credits on Pro), the Batch API (real
money), an advisor model, and a 1-hour cache for the writer (break-even).

## Exit criteria

- Every kept lever has its comparison in `docs/experiments/<date>-optimisation.md`, and so does
  every lever that lost.
- The next full run's cost per 1,000 words is measured against run #7's $3.18, with its click-next
  and judges' scores beside it.

## Session log

*(filled in when this plan runs)*
