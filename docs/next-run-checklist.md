# The next full run: what it checks

Everything plans 06–07 and the post-07 audit built that only a live run can confirm, in one
place. The run itself follows [test-run-protocol.md](test-run-protocol.md); this list is what it
reports on, beside the usual verdicts. Tick each item in the run's write-up, with the figure, and
move the result into the roadmap's *Features* table.

## The showrunner (06, 06b)

From the [optimisation write-up](experiments/2026-10-04-optimisation.md#to-measure-in-the-next-full-run):

- [x] the trace's *injected context* line: no `mcp`, no `ide_diagnostics`, for any role (the
      pre-run probes); run #9: harness and one hook only, for every role;
- [x] the showrunner's effort reads `medium` per response, **and** the planner and writer still
      read `high` (run #9: showrunner medium 252, planner high 233, writer high 168): `settings.json`'s per-model `effortLevel` for Opus must not override an agent's
      own `effort`;
- [x] showrunner turns per chapter (`trace.py --chapters`), against 15–45 (mean 36; 21 predicted);
      run #9: 30–41, mean 33 (ch 6–12);
- [x] showrunner mean context and compactions, against mean 344k, peak 596k (run #9: mean 134k,
      peak 216k, 2 compactions; no subagent compacted, so the window stays); no role but the
      showrunner compacted. Whether `autoCompactWindow` reaches subagents at all; if none compacts
      at its peak, lower the window to 150k;
- [x] the showrunner's share, allotted, against 41% (run #9: 20%, $13.66 of $68.08), with `status.py` matching the files and
      `state_check.py` clean after every chapter;
- [x] each usage-limit pause (run #9: two, both mid-chapter, $2.72 of showrunner cache rewrites;
      no PAUSE line in the VS Code panel; no `CronCreate`, the user resumed by hand): its cost, whether it fell at a chapter boundary, and whether the
      `CronCreate` resume ran;
- [ ] `/usage`'s plan breakdown, read once, beside the trace's allotted shares; run #9: not read: `/usage` is
      the user's command, and the run asked for no user step. Still open;
- [x] `docs/sessions/<session>.reads.tsv` fills, and the story and line editors act on
      `history-rK.txt` from chapter 3 (run #9: 1,333 reads; story editor 13 and line editor 7 reads
      of `history-rK.txt`, cited in notes and hand-backs).

## The roles (06c, 06d)

- [ ] the story editor at `medium`: its cost a spawn against run #7's (06c predicted −26%), and
      its notes still specific (a quote, the evidence, the effect);
- [ ] the writer's revisions at Opus `medium`: not yet tested (06c lever 5, re-aimed by 06d).
      Run them at `high` as now unless a frozen-round pair is run first; log the choice;
- [x] the planner at `medium` (06c lever 6): decided 2026-10-10 on a frozen round, it stays at
      `high` (+6% cost, same sheet; [bench](experiments/2026-10-10-agency-bench.md));
- [ ] the continuity editor: its final message is one line in every spawn, `wire.py check` is in
      its transcript, and its findings and cost a spawn sit beside run #7's;
- [ ] the clerk's kept anti-recap sentence and the four low-confidence prompt lines 06d flagged:
      did any of them show in a block or a hand-back;
- [ ] cost per 1,000 words against run #7's $3.18, beside click-next and the judges' scores.

## The knowledge bases (07)

- [ ] the eight examples 07 added (planner `long-middle.md`, and the examples in `stakes.md`,
      `arcs-and-chapters.md`, `cast-design.md`, `world-design.md`, `bias-structural.md`, writer
      `scene-and-summary.md`, continuity `provenance.md`, story editor `cost-and-keep.md`, line
      editor `ai-default-habits.md`) are opened (`reads.tsv`), and nothing from them is copied into
      the new novel: `kb_check.py --novel` clean, near-name warns included.

## The audit's changes (post-07)

- [ ] the guard refuses no call a role needed: every refusal in the transcripts was a search over
      the root or `kb/`, a rubric, or a shell command other than `python3 tools/...`;
- [ ] no reading folder rebuilt over a reader's work; if a novel's memory was missing, `room.py
      beats` printed the fresh re-read and `adopt` restored the shelf;
- [ ] `wire.py` raised no false `PLANNER DONE` defect.

## The post-07 audit's speed levers (2026-10-06)

From the [audit](experiments/2026-10-04-optimisation.md#post-07-audit-cheaper-and-faster-chapters-2026-10-06):

- [ ] the writer's revisions are edits: output per revision against run #7's 7–11k; `bench.py
      rounds` still shows each note acted on (paragraphs changed, `notes` lines in `facts-rK.md`);
      no `round` STOP on an unrevised copy;
- [ ] the planner opens no chapter before the previous one and no earlier beat sheet
      (`reads.tsv`); its peak context against run #7's 143k;
- [ ] the continuity editor continued warm in rounds 1–2: round time against 5.5–6.4 min, the
      writer's cache expiries against 6 ($3.37), and its findings a round beside run #7's (run the
      ~$2 agreement bench first, if the budget allows);
- [ ] beats started at ACCEPT: wall time from ACCEPT to the next writer's spawn against ch 4's
      ~16 min; no beat sheet sent back for something the fold changed;
- [x] the planner at `medium`: left at `high` (2026-10-10, see above).

## Run #8's fixes (2026-10-10)

From the [write-up's fixes](experiments/2026-10-09-run-8.md#fixes-2026-10-10-after-the-run-no-agent-spawned):

- [x] (run #9: no diagnostics after the clerk's Edit, none in the trace) the pre-run probe **edits** a file under `novels/` with the Edit tool (a Write shows nothing)
      and no diagnostics come back; the trace's injected-context line has no `ide_diagnostics` for
      any role;
- [x] (run #9: none, all three judges' disclosures; new contaminant, the harness's `userEmail` line) no git status or git block in any spawn's context, judges included: read one judge's
      disclosure. Start the run in a new session, since `includeGitInstructions` is read at start;
- [x] (run #9: $4.84 for 14 rounds, $0.69 a chapter; every r1 grades its last notes; owed steady) the warm story editor: its cost a chapter against run #8's $5.51 for 14 spawns, its notes
      still quote-evidence-effect, and every round-1 and round-2 note file grading the last notes;
      owed grades steady between rounds on similar evidence (F13);
- [x] (run #9: ch 6–9, 11, 12; ch 10 blocked by the re-read; `--cold` only at ch 12) `ahead.txt` written at every ACCEPT that offers the beats; no second planner at a fold; a
      `--cold` fold only where the planner was never sent;
- [x] (run #9: gestures at half run #8's rate, tag questions none after ch 8; `recap` missed two paraphrased paragraphs, F13) the line editors act on `gesture` and `tag` lines, the story editors on `recap` lines; the
      judges' tic complaint against run #8's;
- [x] (run #9: 14 of 14 rounds, read by the continuity editor 14 times, no lint run by it) `lint-rK.txt` printed by every `room.py round` and read by the continuity editor, which runs
      no lint itself;
- [x] (run #9: 21, clerk 10, continuity 11, all shell compounds; canon researcher not spawned) the clerk's and the continuity editor's guard refusals against run #8's 41; the canon
      researcher's `scaffold.py check` runs;
- [x] (run #9: L1 grew 6 of 7; no judge names agency; P4 stated ×3) the protagonist's move grows chapter to chapter in the plan rows, and the judges' agency
      score against run #8's.

## Plan 08 (2026-10-10)

From [08](roadmap/08-pressure-and-run-9.md):

- [x] (run #9: done, no `pressure` warn) `/plan` first: the planner adds `L1` and `C1` to `novels/ember-terraces`, one step for each
      of ch 1–5 (`status.py --debt` asks for them), and `state_check` raises no `pressure` warn;
- [x] (run #9: rows 8 and 11 rewritten as acts) the same `/plan` rewrites the passive rows ahead in `changed` lines (a want she acts on, an
      event of which she is the subject): rows 8 ("get away from Dao") and 11 ("let her father
      speak for her") read as holds; a ch 5 bench kept a passive event without this;
- [x] (run #9: it grades the reader's uptake, not the direction, F2; the clerk's step was stricter than the planner's twice; the direction stays the clerk's, see *Run #9's fixes*) the story editor's grade of each `pressure` line against the planner's: stricter, or as
      lenient as the bench's (a declined move graded `grew`);
- [x] (run #9: every beat sheet and clerk yes; notes 10 of 14, ch 8–9 skipped it, F12; one flag, at ch 6, answered) every beat sheet has a `pressure` line, every notes file grades `L1` and `C1`, and every
      clerk appends one step to each trail; `room.py` put a `Pressure:` flag in a beats dispatch
      only after a step back or two holds, and the next beat sheet answered it;
- [x] (run #9: L1 grew, grew, held, grew, grew, grew, grew; agency gone from the judges' lists) the trail across ch 6–12 against run #8's (backfilled), and the judges' agency complaint
      against run #8's (all three ranked it first or second);
- [x] (run #9: in all 14; drafts 5.7, accepted 5.2, against 6.2; touched twice) the slop note in every `lint-rK.txt`; the index per chapter against run #8's 6.2 mean, and
      whether the line editor touched any of its hits (it is a reference, not a list to cut);
- [x] (run #9: re-read done, fresh 4 = warm 4; `long-middle.md` not opened, correctly: its index line says arc 3; click-next 4 through ch 7–9) the every-10 re-read at chapter 10 (first time), `long-middle.md` opened (`reads.tsv`),
      and click-next through chapters 7–9.

## Run #9's fixes (2026-10-11)

From the [write-up's fixes](experiments/2026-10-10-run-9.md#fixes-2026-10-11-after-the-run-no-agent-spawned):

- [ ] every notes file grades each `pressure` id; where one does not, `room.py judge` printed the
      warn and the next round's notes graded it (F12);
- [ ] where the clerk's step (the direction) and the story editor's grade (the reader's uptake)
      disagree, which the trail kept, and whether the next beat sheet answered it (F2: the clerk
      was stricter twice in run #9);
- [ ] no paragraph written for a revision note re-tells an earlier chapter: each confusion note's
      `dir` asks for a clause (`note-protocol.md` N4), and no judge names a recap the loop wrote;
      the judges' recap complaint against run #9's (all three);
- [ ] `history.py`'s motif warns name no phrase a place name chained into a refrain; the line
      editors' cuts still cite real refrains;
- [ ] no line editor hand-back asks the showrunner anything (`left` lines final; run #9: four);
- [ ] no fold `gap` the clerk had already closed (F4);
- [ ] the judges' labelled-tell, clock and never-wrong-antagonist complaints, against run #9's, once
      a `/plan` has re-planned rows 13 and 15 with the new `stakes.md` and `cast-design.md` examples;
- [ ] each judge's disclosure: whether `userEmail` reached it and whether it named the author;
- [ ] the run started from the terminal CLI: a PAUSE line at the threshold, and whether the
      `CronCreate` resume ran.

## Plan 09 (2026-10-11)

From [09](roadmap/09-canon-reading.md), at the next fan-fiction init or `gap canon` lookup (no
replay was paid for it):

- [ ] `trace.py` for `canon-researcher`: cache writes and compactions a spawn, against the Sonnet
      baseline (init: 0.69M cache writes, 3 compactions, $3.45; 31 of 39 pages opened more than
      once); no `long_tier` warn if the role runs on Haiku;
- [ ] its transcript uses `toc` or `grep` before a Read, and Reads with an offset; a page read whole
      only where `toc` shows no heading that fits;
- [ ] the dossier against `bench/h55-canon/canonson.md`: the same ages and statuses at the start
      (Zuko 15–16, Iroh about 54, Zhao Captain or Commander, not "newly commander"), transcripts
      still cited, and every path under `## Sources` exists. Facts missing: loosen what counts as a
      whole-page read; do not revert the tool.

Partial evidence, on Haiku (plan 10's retest, 2026-10-11): 7 `toc`, 15 `grep`, 22 Reads with an
offset and 3 whole, no compaction, 0.17M cache writes; three transcripts cited, all through `grep`.
The Sonnet run is still owed.

## Plan 10 (2026-10-11)

From [10](roadmap/10-prompts-for-smaller-models.md), on the next run's clerk (Sonnet), each chapter:

- [ ] no `state_check` warn that a row "was landed … before ch N's clerk", or that a step "changed
      in ch N's clerk pass", and `work/chNNNN/ledger-before.md` is there for every chapter;
- [ ] each block's `ev` keeps the chapter's actions in order, and `at` names nobody who is only in
      the beat sheet;
- [ ] each Pressure step carries the day, count or price the page gives, and a lever step its cost;
- [ ] at a fan-fiction init: the dossier cites transcripts for a show, and states each rank at the
      start, with how it was worked out.

## Plan 11 (2026-10-11)

From [11](roadmap/11-bounded-reads.md), on the next full run (baseline: run #9's trace). Run #10 (ch 13–14, [write-up](experiments/2026-10-11-run-10.md#write-up)) ticked four; the budget waits for ch 20:

- [x] the showrunner runs `room.py approve` and Reads `beats.md` with a limit (the header), not
      whole; its compactions (run #9: 3 at 217k) and its context mean (129k);
- [x] clerk, planner and story editor Read `state/continuity.md` with an offset, never whole (the
      guard's `*.reads.tsv` and the transcripts); their cache writes a spawn against run #9;
- [x] the clerk's block still appended in place, after the last one (`state_check` clean), and no
      continuity or story-editor finding traced to a fact only an earlier block held;
- [x] the line editor still acts on the history report's motifs in its chapter;
- [ ] at ch 15+ or a lost memory past the budget: the fresh reader's notes say what it skipped.

## Run #10's fixes (2026-10-11)

From [run #10](experiments/2026-10-11-run-10.md) F2 and F3:

- [ ] the writer's dispatch comes from `room.py approve` (and, for a sheet started at ACCEPT, from
      `fold`); none sent by hand;
- [ ] every notes file's *Continuity* answers each `bible`/`state`/`time`/`travel`/`know` finding,
      and no accepted chapter reaches the clerk with one unanswered (`clerk`'s warn); the round
      count against run #10's (2 a chapter): more notes per round, not more rounds.

## Best-practice pass (2026-10-11)

From Anthropic's skill-authoring and CLAUDE.md guidance (a Contents list in each reference doc over
100 lines; pointers that say when to read, never `@` imports; CLAUDE.md lean). Baseline: run #9's
`*.reads.tsv`, where `bible/world.md` was opened whole by the planner (9), writer (7), continuity
editor (7) and clerk (7):

- [ ] planner, writer, continuity editor and clerk Read the long bible files (`world.md`,
      `canon.md`) by the section the dispatch's map names, or Grep them, and not whole (the
      transcripts' Read offsets; the guard log only counts opens); their cache writes a spawn
      against run #9's;
- [ ] no finding traced to a bible fact outside the section a role read (a continuity miss, a
      writer contradiction the continuity editor catches);
- [ ] the showrunner's injected context at session start (`trace.py`) against run #9's: CLAUDE.md
      went from 9.6k to 7.0k characters.
- [ ] a fold that adds a place files it under a `### <place>` heading in `world.md` §Places, and
      keeps dated events out of the bible (plan 12 P2.4); the map then lists the parts.

## The bench

- [x] the blind panel on two models (`bench.py panel`, `judge--fable`): scores per model, with the
      spread (run #9: Opus 4.5, 4.5; Fable 4; spread 0.5 across models, 0 within).
