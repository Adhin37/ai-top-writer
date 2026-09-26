# 06 — Session 7: measurement, then optimisation

**Goal:** first see what the book does across chapters and what each role costs. Then, and only
then, reduce cost without losing the quality run #7 established. The user's instruction was
quality first and tokens later. This is later.

## Part A — measurement

### 1. Port the trace

Port skilled-writer's `scripts/swlib/transcripts.py` and `cmd_trace.py` into `tools/trace.py`. They
read Claude Code's transcripts for usage, timestamps and tool names, and **never** prompt text, tool
results or prose.

- **Scope** by session id. The showrunner's session takes in every agent it spawned.
- **Per role:**
  - responses and cost;
  - model seconds against tool seconds (from timestamps);
  - which `kb/` docs were opened.
- **Per chapter:** the same, plus loop rounds.
- **Flag the known under-count.** A response whose thinking block dwarfs its recorded output tokens
  counts as a lower bound, which run #6 saw 60 times.

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

1. **Warm writer across chapters.** Continue the same writer via `SendMessage` for an arc, instead of
   a fresh one per chapter. Run #6 measured this once: drafter time halved (755 s against 1,531 s).
2. **Effort per role.** `effort: medium` on the Sonnet critics first, then on the story editor.
3. **Model per role.** Can the writer's revision rounds run on Sonnet while round 0 stays on Opus?
   Can the beta reader drop to Haiku? Run the beta-reader calibration from plan 01 again before
   trusting it.
4. **Loop pruning.** From the round statistics: if the second revision round almost never changes
   the verdict, cap at one. If the continuity editor rarely finds anything after chapter 3, run it
   every other chapter.
5. **Read-set trimming.** From the trace's opened-docs list, drop knowledge-base docs no role opens.

Record every result in `docs/experiments/<date>-optimisation.md`, including the levers that lost.

## Exit criteria

- Cost and time per role are known, per chapter.
- The cross-chapter detectors run in the loop.
- Every kept optimisation has a blind comparison behind it.

## Session log

*(filled in when this plan runs)*
