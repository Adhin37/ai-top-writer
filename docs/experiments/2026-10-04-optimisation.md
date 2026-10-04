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
