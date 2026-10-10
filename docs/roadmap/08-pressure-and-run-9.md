# 08 — Session 9: the lead's pressure, an outside slop figure, and run #9

**Goal:** close the gap run #8's judges ranked first (a lead whose moves shrink, a clock pushed back
in dialogue), give the room an outside measure of model prose, then test both live past chapter 5,
where no run has gone.

**Why:** run #8 scored 4/5 at $2.43 per 1,000 words; cost is no longer the bottleneck. In co-writing
studies, models elaborate what is on the page and rarely introduce pressure that lasts (Fundal and
Bizzoni, arXiv 2604.23676 and 2609.07920). That is the mechanism behind both of the judges' top
costs. On Royal Road, readers drop off around chapters 7–9, and in one author's measured
experiment the fix was a heroine who chooses rather than drifts. Five-chapter runs never reach that
window.

## Steps

1. **Pressure as ledger state** (offline, no spawn). Two standing ledger rows, `L1` the lead's lever
   and `C1` the clock, each with a trail of one step per chapter (`grew/held/shrank`,
   `nearer/held/later`). The beat sheet's `pressure` line plans the step, the story editor grades
   it as an owed row, and the clerk writes it. `status.py` flags a step that shrank or went later,
   and a row that held two chapters running; `room.py` hands those flags to the next beats
   dispatch, and `--debt` asks for the rows when a ledger has none. This replaces nothing: the
   planner's *lead's move* example now points at the trail.
2. **EQ-Bench's slop index in `lint.py`** (offline). Their three lists, vendored (MIT), and their
   formula, unchanged, so the figure sits beside their leaderboard. A note line, never a gate.
3. **Two frozen-round benches** (~$10). Agency: `bench.py freeze --role planner` at run #8's ch 4
   and ch 5, after a planner `/plan` adds the Pressure rows to a copy; arm A without them, arm B
   with them, blind pair, one question: whose lead acts? Then the planner at `medium`
   (`planner--medium`), pending since 06c.
4. **Run #9:** `novels/ember-terraces`, chapters 6–12, the full loop under `.test-run`, starting
   with `/plan` (the Pressure rows, backfilled for ch 1–5 by the planner). It reaches the every-10
   re-read and `long-middle.md`, and crosses the chapter 7–9 window. About $80; it may be split at a
   chapter boundary. Report on [next-run-checklist.md](../next-run-checklist.md).

## Session log

**2026-10-10, steps 1–2.** No agent spawned; nothing committed.

- Step 1 built: `Novel.pressure()` (`tools/lib/novel.py`), `status.pressure()` and
  `pressure_flags()`, `state_check.check_pressure()` (vocabulary, steps past the last chapter, a
  chapter with no step), `room.pressure_note()` in both beats dispatches, `bench._cut_ledger` drops
  steps from the cut on, `scaffold.py check` warns when either row is missing. Docs:
  `kb/planner/reader-ledger.md` (the kind, the example, a check), `beat-sheet.md` (the `pressure`
  line, a check), `prompt.md` (beats and ledger tasks), `init.md` (before you finish),
  `arcs-and-chapters.md` (the example points at the trail), `kb/shared/state-format.md` (how the
  clerk writes a step), `kb/clerk/prompt.md` step 7, `kb/story-editor/prompt.md` step 1, the
  template ledger and `docs/novel-format.md`.
- Step 2 built: `tools/lib/slop.py`, `tools/data/eqbench/` (three lists and a NOTICE), a `slop` note
  in `lint.py`. **Back-test:** run #8's chapters 3.9, 4.2, 6.4, 8.3, 7.1 (mean 6.2); run #7's 7.1,
  6.6, 4.8, 1.9, 10.5 (mean 6.4). Run #7 scored 4.5 and run #8 4, so the index does not separate
  the runs the judges separated: it stays a reference figure. Run #8's rise from chapter 1 to 4 does
  match the judges' "tics turn into mannerism".
- Found on the way: `history.gestures()` broke ties between companions in set order, which changes
  from one process to the next, and its test failed about two runs in three. Ties now go to the
  first companion in alphabetical order (lesson 40).
- Verified: 347 tests, three full runs green; `kb_check` clean on the repo and on
  `novels/ember-terraces`; `status.py --debt` on that novel asks for the Pressure rows.
- Not done here: steps 3 and 4 spend agents and wait for the weekly limit.

**2026-10-10, step 3** ([write-up](../experiments/2026-10-10-agency-bench.md)). Four planner spawns,
$10.13 in all; nothing committed.

- The agency bench froze run #8 before ch 5's beats. Every arm wrote the Pressure rows unasked (the
  beat-sheet doc asks for the `pressure` line), so the "without" arm became run #8's own ch 5.
- All three beat sheets kept the row's event, in which the garrison acts and Kesa watches; arm B
  wrote it `L1 shrank`, arm A wrote the same declined move `grew`. A blind pair would have measured
  the writer, so drafts and judges were skipped.
- **Decided:** the lever is checked where events are chosen. The planner's plan task walks the rows
  ahead against `L1`/`C1` and rewrites a row that holds or shrinks the lever past one cool chapter
  an arc, or moves the clock later without a reason; init's last check asks the same.
- **Decided:** the planner stays at `high`; `medium` cost 6% more for the same sheet (06c lever 6
  closed).
- Seen: the room grades its own trail leniently. Run #9 shows whether the story editor's grade is
  stricter.
- Step 4 (run #9) waits for the weekly limit. Its first `/plan` must rewrite the passive rows ahead.
