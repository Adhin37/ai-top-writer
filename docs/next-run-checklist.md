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

## The bench

- [ ] the blind panel on two models (`bench.py panel`, `judge--fable`): scores per model, with the
      spread.
