# 2026-10-04 — Optimisation: what each lever was built to save, and what a run measured

Plans [06b](../roadmap/06b-showrunner-cost.md) (the showrunner's cost) and
[06c](../roadmap/06c-role-levers.md) (the roles' levers) record their levers here, the ones that
lost included. Baseline: [run #7 through the trace](2026-10-04-trace-run-7.md).

## 06b — the showrunner's cost (built 2026-10-04; no agent spawned)

Nothing here was measured live: following the standing *test by parts* decision, 06b built its levers
and unit-tested them, and the next full run measures them (checklist at the end). Every prediction
below comes from run #7's transcripts.

| lever | built | prediction from run #7 | measured |
|---|---|---|---|
| 1a. markdownlint off agent files | `.markdownlintignore` (`novels/`, `reading/`, `bench/`, `docs/sessions/`); test runs from the terminal CLI | 0 of run #7's ~166k characters of `ide_diagnostics` (133k into the planner) | — |
| 1b. claude.ai connector off | `disableClaudeAiConnectors: true` in `.claude/settings.json` | 0 of 129k characters of MCP instructions across 68 spawns | — |
| 2. showrunner effort `xhigh` → `medium` | `effortLevel` and `modelSettings.claude-opus-5-5.effortLevel` (the user's settings set a per-model level, which outranks a top-level one) | ≤ ~$2 of $3.48 output | — |
| 3. fewer turns | `tools/room.py`: one call per step, printing the next dispatches; both readers in one message; no file opened to check it exists | 8 + 5 a round: ch 1 13, ch 2–5 23 each, mean 21 against 36 (−42%) | — |
| 4. a small context | **B**: `autoCompactWindow: 250000`, compact instructions in `CLAUDE.md`, a SessionStart hook that points a compacted session at its handoff and `room.py where` | cache reads 102M → ~46M tokens ($20.09 → ~$9.1, plus ~$0.7 of compaction writes) | — |
| 5. pause at a chapter boundary | the 80% notice (`session_hooks.py`), `room.py`'s `PAUSE` line, the resume by `CronCreate` (`loop.md`) | the in-flight agents' rebuilds after a pause (run #7: writer $3.37 of expiries, part of it the two pauses); the showrunner's rebuild capped by lever 4 at ≤250k against 303k and 412k | — |

### Lever 3: where run #7's turns went

Chapter 4, three rounds, 35 showrunner turns: per round, the two readers spawned in separate turns;
their two hand-backs filed and logged in two more; a log write of the showrunner's own; the story
editor; its hand-back logged with a `wire.py` check; the `SendMessage` to the writer. About nine a
round. With `room.py`: `round`, both readers in one message, `judge`, the story editor, the writer's
continuation. Five a round. Per chapter on top: read the beat sheet, the writer, the line editor,
`clerk`, the clerk, `fold`, the planner's fold, the beats continuation: eight.

The plan's target was half (18). The prediction is −42%: what is left is one turn per agent sent,
and one tool call where a file must be filed or checked before the next agent. Joining the
planner's fold and its next beats into one message would save one more a chapter, but it changes
how the planner receives its tasks, so it belongs to 06c.

### Lever 4: why B, at 250k, and the candidate that lost

**A, a workflow per chapter, was not built.** On a Pro plan, dynamic workflows stay off until the
user turns them on in `/config`. The session cannot do that itself, and it cannot answer A's
questions without probe spawns: does `agent()` take a named agent type? Do the guard's hooks fire
in workflow agents? Can a step continue the writer warm? Those spawns exist only to test, and the
standing preference is to ask before spending on them. A stays the fallback if B's measured
context is not small enough, with its verification list in 06b.

**B needs neither.** Auto-compaction runs without the user. `/clear` at a chapter boundary would
cut deeper, but only a person can type it.

**The window.** Run #7's showrunner context, replayed with compaction at a window W, falling back to
~45k after each compaction (an assumption: the system prompt and `CLAUDE.md` are ~40k, plus the
summary):

| W | compactions | cache-read tokens | mean context | cache reads $ | compaction writes $ |
|---|---|---|---|---|---|
| none (run #7) | 0 | 101.8M | 344k | 20.09 | 0 |
| 150k | 5 | 28.8M | 97k | 5.77 | 1.80 |
| 200k | 3 | 36.5M | 123k | 7.29 | 1.08 |
| **250k** | 2 | 45.5M | 154k | 9.11 | 0.72 |
| 300k | 2 | 50.0M | 169k | 10.00 | 0.72 |

The docs do not say whether the window also applies to subagents, and run #7's planner peaked at
194k and its writer at 141k. A planner or writer compacted mid-task would judge from a summary,
which is a role lever (06c's to test), not a showrunner one. So the window is 250k, above every
role's peak. The trace now counts compactions per role (`compacted mid-task …`): if the next run
shows that no subagent compacts at its peaks, or the docs settle it, lower it to 150k.

Not counted above: the summarising call itself, which reads the context it summarises. It is not
a response in the transcript; the trace's cross-check against Claude Code's own count includes it.

### To measure in the next full run

Carried into [next-run-checklist.md](../next-run-checklist.md) with 06c–07's items; tick them there.

- [ ] the trace's *injected context* line: no `mcp`, no `ide_diagnostics`, for any role (from the
      pre-run probes);
- [ ] the showrunner's effort reads `medium` per response;
- [ ] showrunner turns per chapter (`--chapters`), against 15–45 (mean 36);
- [ ] showrunner mean context and compactions, against mean 344k, peak 596k; no role but the
      showrunner compacted;
- [ ] the showrunner's share, allotted, against 41% (44% as traced), with `status.py` matching the
      files and `state_check.py` clean after every chapter;
- [ ] the cost of each usage-limit pause, and whether it fell at a chapter boundary;
- [ ] `/usage`'s plan breakdown, read once: its per-subagent shares beside the trace's allotted
      shares (moved from 06);
- [ ] `docs/sessions/<session>.reads.tsv` fills, and the story and line editors act on
      `history-rK.txt` from chapter 3 (06's changes).

## 06c — the roles' levers (2026-10-04)

The comparisons run on run #7's frozen rounds (`novels/grown-houses/work/`, the reader's shelf in
`reading/r7494e3-*`). Built for them: `tools/bench.py`.

- `rounds`: each round's verdict, notes, click-next, continuity findings, and the paragraphs the
  next draft changed. From disk, no spawn.
- `freeze`: a copy of the novel as it stood when round K of chapter N reached a role, with its
  dispatch printed. The copy cuts later chapters, later rounds, state blocks, scene and timeline
  rows, and ledger statuses. It keeps the later folds in the bible, so every arm, the baseline
  replay included, reads the same copy.
- `arm`: writes a `<role>--<arm>` agent file that changes only effort or model. The Agent tool can
  override a model but not an effort. The guard holds the arm to its role's rules.
- `pair`: blind folders in both orders, and the key.
- `agree`: notes matched by their `where` quote, continuity findings by their draft quote, and
  the known catches.

### Lever 1, the loop's cap: **lost, on the in-loop reader's evidence; no judge spent**

`python3 tools/bench.py rounds novels/grown-houses`:

| ch | r0 notes → paragraphs changed | r1 notes → paragraphs changed | r2 | click-next r0/r1/r2 |
|---|---|---|---|---|
| 2 | 5 → 27 of 117 | 3 → 7 of 117 | ACCEPT | 4 / 4 / 4 |
| 3 | 5 → 16 of 142 | 4 → 5 of 142 | ACCEPT | 4 / 4 / 5 |
| 4 | 5 → 18 of 119 | 3 → 7 of 119 | ACCEPT | 4 / 4 / 4 |
| 5 | 5 → 8 of 153 | 1 → 1 of 153 | ACCEPT | 5 / 5 / 5 |

Round 2 rewrites 1–7 paragraphs. The plan's test, a blind pairwise judge on draft-r1 against
draft-r2, would read two texts that differ in a few paragraphs, one chapter alone, without the
chapters before it. Nearly every round-1 note is about what the reader holds from earlier
chapters: a returning character placed, a sum or a coat beat repeated from an earlier page, a day
count. A judge with no earlier chapters cannot see any of them. A tie would be predictable, and it
would not mean round 2 does nothing. So the comparison used the instrument that sees them: the
calibrated in-loop reader. Its round-1 and round-2 reports are on disk, written by fresh readers
who had the same shelf.

| round-1 note | in round 1's report | in round 2's report |
|---|---|---|
| ch 5 N1 Hob comes in as a stranger | "apparently the man whose family's house… (guess)" | "a neighbour who lost his own house to Iven's seal"; "It worked because the Dennet name comes from ch3" |
| ch 4 N1 the sum done twice | skimmed: "the arithmetic was done in the narration and then repeated" | "I followed the sums" |
| ch 4 N2 the shunned coat a fourth time | skimmed: "said the same thing a fourth time" | gone |
| ch 4 N3 the day count where he is believed | confused: "I had lost count of days" | the count is gone; a new half-confusion on the same line |
| ch 3 N1 "Yours." looks like steering | confused: "Why Prent gave him the clearance file… 'Yours'" | gone |
| ch 3 N4 the two answers stated twice | skimmed: "the two-suspect summary repeated" | gone (the paragraph is cut) |
| ch 3 N2 the list never unfolded | (a continuity slip, not in the report) | fixed in the text |
| ch 3 N3 the method spent before the kitchen | skimmed the measuring routine | "I slowed, though it also built the dread": partly |
| ch 2 N2 the charter exchange | skimmed as a repeat | still skimmed; the ledger keeps F19 `partly ch2` |
| ch 2 N1, N3; ch 5 — | not visible in either report | — |

At least 7 of the 13 round-1 notes fixed something the next fresh reader no longer reported. One
persisted. A cap at one round would have shipped those 7. Round 2's story editor also writes the
*For the planner* and *Unresolved* sections that the next beats and the line pass act on (ch 4: 9
and 7 lines). **Decision: keep two revision rounds.** Lever 5 (the writer's revisions on Sonnet)
is therefore live.

**The second question: did the continuity editor find anything after chapter 3?** Yes: 6, 4 and 5
findings in chapter 4's rounds, and 6, 3 and 3 in chapter 5's. Three became the story editor's
notes: ch 4 N2 ("first time he had said it", from r0 F2), ch 4 N3 (the day count, from r1 F1),
and ch 5 N4 (Wren knows what only Tansy said, a `know` finding). **Keep it every round.**

### The wire format across the arc: holds (free)

Hand-backs stayed one line in every loop spawn but one (the trace's table above; line editor
ch 3). Notes files do not grow: 708 words at ch 1, then 850–1,110 a round through ch 5, with no
trend.

### Lever 3, the continuity editor's read-set: measured, ranked last

Its 14 spawns took ~32k tokens of tool results each. Most of it came from `cat` on whole bible
files (world, society, every cast file: 5–7k tokens a call) and whole earlier chapters, although
its prompt says to grep. An extract of the bible lines that the draft's names touch would be
~3.9k of the bible's 10.7k words (chapter 5, r0). The role cost $3.66 in run #7 ($4.9 allotted),
so the lever is worth about $1 a run, about 1%. Not built. If it is, it is a `touches` command and
a step 4 that replaces the current one, tested as an arm (`bench.py arm`) by findings agreement.

### Paid levers: the budget, asked before spending

Per-spawn costs are run #7's, allotted (the Sonnet roles' unrecorded output included):
continuity editor ~$0.35, story editor ~$0.55, clerk ~$0.25, judge (mode 2) ~$0.5.

| lever | what runs | spawns | budget |
|---|---|---|---|
| A/A + 2a continuity editor `medium` | ch 4 r0 and ch 5 r0 (6 findings each): two baseline replays and one `medium` arm each | 6 | ~$2.1 |
| 2b story editor `medium` | ch 3 r1 and ch 4 r1 (4 and 3 notes): two baseline replays and one `medium` arm each | 6 | ~$3.3 |
| 4 clerk on Haiku 4.5 | ch 5, accepted round 2: one Sonnet replay, one Haiku; `state_check` and a block diff, no judge | 2 | ~$0.4 |
| 2c line editor `medium` | only if 2a and 2b hold: ch 4 and ch 5, one arm each, blind pairwise both orders | 2 + 4 judges | ~$2.8 |
| 5 writer's revisions on Sonnet | ch 3 r1 and ch 4 r1 replayed cold from draft-r0 and its notes on each model, blind pairwise both orders | 4 + 4 judges | ~$5 |
| 6 planner `medium` | last: its effect shows a chapter later; rides on the next full run | — | — |

The first wave (2a, 2b, 4) is ~$5.8 plus the showrunner's turns. The user approved it. The
effort arms registered mid-session once `bench.py arm` wrote their files, so no new session was
needed. The clerk's Haiku arm needs no file: the Agent tool's `model` override does it.

### The first wave: what it cost

From `python3 tools/trace.py 779f5f2c-…` (the trace credits each response to the effort it
actually ran at, and every arm ran where it was meant to):

| role | spawns | effort | output | thinking | cost | a spawn |
|---|---|---|---|---|---|---|
| story editor | 4 | high | 59.8k | 71% | $2.74 | $0.69 |
| story editor | 2 | medium | 19.8k | 61% | $1.01 | $0.51 |
| continuity editor | 4 | high | 7.4k (+4.1k unrecorded) | 55% | $1.25 | $0.31 |
| continuity editor | 2 | medium | 0.4k (+2.1k unrecorded) | 0% | $0.36 | $0.18 |
| clerk | 2 | high (Sonnet, Haiku) | 21.7k | 69% | $0.30 | $0.15 |

$5.66 for the spawns, close to the budget.

### Lever 4, the clerk on Haiku 4.5: **lost**

Chapter 5, the accepted round, one Sonnet replay and one Haiku. Both returned `CLERK DONE` and a
clean `state_check`. Read side by side against run #7's own block:

- Haiku re-marked a ledger row that was correctly `landed ch4` as `landed ch5`.
- It put two names that appear only in the beat sheet, never on the page, into the block's `at`.
- Its `ev` shrank to one sentence that drops the chapter's actions, and its `has` is thinner.
- The Sonnet replay matched run #7's block closely.

`state_check` passes all of it: it checks form and references, not whether the block is true or
whole. The next continuity editor would read a wrong `at` and a ledger that misdates a landing.
Saving: ~$0.10 a chapter. **Keep the clerk on Sonnet.**

### Lever 2, the critics at `medium`: **the story editor kept, the continuity editor lost**

Each frozen round got two baseline replays at `high` (aa1, aa2: the A/A) and one `medium` arm.
`python3 tools/bench.py agree`; notes match by their `where` quote, findings by their draft quote.

Story editor (2b), notes matched / union, every verdict REVISE:

| round | aa1·aa2 | aa1·med | aa2·med | run #7·aa1 | run #7·aa2 | run #7·med | owed (aa1, aa2, med, run #7) |
|---|---|---|---|---|---|---|---|
| ch 3 r1 | 3 of 4 | 3 of 3 | 3 of 4 | 3 of 4 | 4 of 4 | 3 of 4 | 3/3 · 3/3 · 3/3 · 3/3 |
| ch 4 r1 | 2 of 6 | 2 of 6 | 3 of 5 | 3 of 4 | 3 of 4 | 3 of 4 | 2/2 · 1/2 · 1/2 · 1/2 |

`medium` agrees with each baseline as well as the baselines agree with each other, and with run
#7 as well as they do. **Kept:** `.claude/agents/story-editor.md` now has `effort: medium`, saving
~$0.18 a spawn, ~26%. In run #7 that is 14 spawns, ~$2.5 a run.

Continuity editor (2a), findings matched / union:

| round | aa1·aa2 | aa1·med | aa2·med | run #7·aa1 | run #7·aa2 | run #7·med | findings (aa1, aa2, med, run #7) |
|---|---|---|---|---|---|---|---|
| ch 4 r0 | 2 of 5 | 1 of 4 | 1 of 3 | 2 of 8 | 1 of 8 | 1 of 6 | 4 · 3 · 1 · 6 |
| ch 5 r0 | 3 of 7 | 4 of 9 | 2 of 9 | 5 of 7 | 3 of 7 | 4 of 9 | 6 · 4 · 7 · 6 |

The A/A itself is loose: two `high` replays share under half their findings, so agreement alone
cannot decide this one. The count and the content do. On ch 4, `medium` found only the four
sacks, which every arm found. It missed the "who could know it" findings that both baselines
raised (Pell's lodging, Iven's "nobody's list"), the kind run #7's story editor turned into notes
(lever 1's section above). On ch 5 it was in range. At `medium` the role recorded no thinking at
all: it ran a check list without weighing it. The saving is ~$0.13 a spawn, ~$1.8 a run, and a
missed `know` finding costs a revision round or reaches the reader. **Lost: the continuity editor
stays at `high`.**

Lever 2c (the line editor at `medium`) needed both to hold, so it was not run. It rides on the
next full run only if someone chooses to try it there; the plan does not schedule it.
