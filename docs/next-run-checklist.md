# The next full run: what it checks

Everything plans 06–07 and the post-07 audit built that only a live run can confirm, in one
place. The run itself follows [test-run-protocol.md](test-run-protocol.md); this list is what it
reports on, beside the usual verdicts. Tick each item in the run's write-up, with the figure, and
move the result into the roadmap's *Features* table.

## The showrunner (06, 06b)

From the [optimisation write-up](experiments/2026-10-04-optimisation.md#to-measure-in-the-next-full-run):

- [ ] the trace's *injected context* line: no `mcp`, no `ide_diagnostics`, for any role (the
      pre-run probes);
- [ ] the showrunner's effort reads `medium` per response, **and** the planner and writer still
      read `high`: `settings.json`'s per-model `effortLevel` for Opus must not override an agent's
      own `effort`;
- [ ] showrunner turns per chapter (`trace.py --chapters`), against 15–45 (mean 36; 21 predicted);
- [ ] showrunner mean context and compactions, against mean 344k, peak 596k; no role but the
      showrunner compacted. Whether `autoCompactWindow` reaches subagents at all; if none compacts
      at its peak, lower the window to 150k;
- [ ] the showrunner's share, allotted, against 41%, with `status.py` matching the files and
      `state_check.py` clean after every chapter;
- [ ] each usage-limit pause: its cost, whether it fell at a chapter boundary, and whether the
      `CronCreate` resume ran;
- [ ] `/usage`'s plan breakdown, read once, beside the trace's allotted shares;
- [ ] `docs/sessions/<session>.reads.tsv` fills, and the story and line editors act on
      `history-rK.txt` from chapter 3.

## The roles (06c, 06d)

- [ ] the story editor at `medium`: its cost a spawn against run #7's (06c predicted −26%), and
      its notes still specific (a quote, the evidence, the effect);
- [ ] the writer's revisions at Opus `medium`: not yet tested (06c lever 5, re-aimed by 06d).
      Run them at `high` as now unless a frozen-round pair is run first; log the choice;
- [ ] the planner at `medium` (06c lever 6, "rides on the next full run"): decide before the run,
      log why, and compare its beat sheets' approvals and the ledger's debt against run #7;
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
- [ ] the planner at `medium`: decided by the frozen-round arm, or left at `high` with the reason
      logged.

## Run #8's fixes (2026-10-10)

From the [write-up's fixes](experiments/2026-10-09-run-8.md#fixes-2026-10-10-after-the-run-no-agent-spawned):

- [ ] the pre-run probe **edits** a file under `novels/` with the Edit tool (a Write shows nothing)
      and no diagnostics come back; the trace's injected-context line has no `ide_diagnostics` for
      any role;
- [ ] no git status or git block in any spawn's context, judges included: read one judge's
      disclosure. Start the run in a new session, since `includeGitInstructions` is read at start;
- [ ] the warm story editor: its cost a chapter against run #8's $5.51 for 14 spawns, its notes
      still quote-evidence-effect, and every round-1 and round-2 note file grading the last notes;
      owed grades steady between rounds on similar evidence (F13);
- [ ] `ahead.txt` written at every ACCEPT that offers the beats; no second planner at a fold; a
      `--cold` fold only where the planner was never sent;
- [ ] the line editors act on `gesture` and `tag` lines, the story editors on `recap` lines; the
      judges' tic complaint against run #8's;
- [ ] `lint-rK.txt` printed by every `room.py round` and read by the continuity editor, which runs
      no lint itself;
- [ ] the clerk's and the continuity editor's guard refusals against run #8's 41; the canon
      researcher's `scaffold.py check` runs;
- [ ] the protagonist's move grows chapter to chapter in the plan rows, and the judges' agency
      score against run #8's.

## Plan 08 (2026-10-10)

From [08](roadmap/08-pressure-and-run-9.md):

- [ ] `/plan` first: the planner adds `L1` and `C1` to `novels/ember-terraces`, one step for each
      of ch 1–5 (`status.py --debt` asks for them), and `state_check` raises no `pressure` warn;
- [ ] every beat sheet has a `pressure` line, every notes file grades `L1` and `C1`, and every
      clerk appends one step to each trail; `room.py` put a `Pressure:` flag in a beats dispatch
      only after a step back or two holds, and the next beat sheet answered it;
- [ ] the trail across ch 6–12 against run #8's (backfilled), and the judges' agency complaint
      against run #8's (all three ranked it first or second);
- [ ] the slop note in every `lint-rK.txt`; the index per chapter against run #8's 6.2 mean, and
      whether the line editor touched any of its hits (it is a reference, not a list to cut);
- [ ] the every-10 re-read at chapter 10 (first time), `long-middle.md` opened (`reads.tsv`),
      and click-next through chapters 7–9.

## The bench

- [ ] the blind panel on two models (`bench.py panel`, `judge--fable`): scores per model, with the
      spread.
