# 06 — Session 7: measurement, then optimisation

**Goal:** first see what the book does across chapters and what each role costs. Then, and only
then, reduce cost without losing the quality run #7 established. The user's instruction was
quality first and tokens later. This is later.

## Part A — measurement

### 1. Extend the trace

[01b](01b-wire-format.md) built `tools/trace.py`: per role, the thinking and visible output, cache
reads and writes, cost, the showrunner's context, and hand-back sizes, scoped by session id. Add:

- **Per role:** model seconds against tool seconds (from timestamps), and which `kb/` docs were
  opened.
- **Per chapter:** the same, plus loop rounds.
- **Flag the known under-count.** A response whose thinking block dwarfs its recorded output tokens
  counts as a lower bound, which run #6 saw 60 times. Plan 01's judges recorded 28k output tokens
  against ~100k tokens of hand-back text.

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

## Part B — optimisation

**Keep any change only if a blind judge panel plus the user cannot tell it from the baseline.** Test
one lever at a time, on the same beat sheets.

0. **The showrunner's context.** In plan 01 the main session cost $19.96 of $38.03. $12.86 of that
   was cache reads: its context averaged ~315k tokens and peaked ~610k over 204 responses. Hand-backs
   were 9.8M of those re-reads and its own file reads 11M; its own writing was most of the rest. The
   lever: **one chapter per showrunner context**, handed over with the existing `handoff` skill,
   plus 01b's status-line reads. The showrunner writes no prose, so the risk is to routing, not to
   the book. Measure the showrunner's cost per chapter before and after.
1. **Warm writer across chapters.** Continue the same writer via `SendMessage` for an arc, instead of
   a fresh one per chapter. Run #6 measured this once: drafter time halved (755 s against 1,531 s).
2. **Effort per role: the largest subagent lever.** In plan 01, thinking was 53–69% of the Opus
   roles' output tokens (writer 53%, story editor 61%, planner 69%), and 73% of the line editor's
   on Sonnet.
   `effort` in an agent's frontmatter is the only per-subagent control over thinking; Claude Code
   has no thinking cap. Try `effort: medium` on the Sonnet critics first, then on the story editor.
   The prose roles come last, if at all. Terse-thinking results such as [Chain of Draft](https://arxiv.org/abs/2502.18600)
   come from reasoning benchmarks, not fiction.
3. **Model per role.** Can the writer's revision rounds run on Sonnet while round 0 stays on Opus?
   Can the beta reader drop to Haiku? Run the beta-reader calibration from plan 01 again before
   trusting it. The same calibration run can take 01b's deferred change: the report's list
   sections in wire form, with the retell untouched. Test it as its own arm, not mixed with the
   model change.
4. **Loop pruning.** From the round statistics: if the second revision round almost never changes
   the verdict, cap at one. If the continuity editor rarely finds anything after chapter 3, run it
   every other chapter.
5. **Read-set trimming.** From the trace's opened-docs list, drop knowledge-base docs no role opens.
   Reading costs as much as writing: each Opus role's cache writes roughly equalled its output in
   plan 01 (writer $2.13 against $1.94).
6. **Re-check the wire format over many chapters.** 01b tested it on one chapter. Across an arc,
   check with the trace that hand-backs stay one line and that notes files have not grown back.

Record every result in `docs/experiments/<date>-optimisation.md`, including the levers that lost.

## Exit criteria

- Cost and time per role are known, per chapter.
- The cross-chapter detectors run in the loop.
- Every kept optimisation has a blind comparison behind it.

## Session log

*(filled in when this plan runs)*
