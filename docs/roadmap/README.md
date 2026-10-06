# Roadmap

The rebuild of [skilled-writer](https://github.com/Adhin37/skilled-writer) as a writers' room. Each plan below is one
working session. They are ordered by what has to be true before the next one is worth doing.

**To run a plan:** open a Claude Code session **in this repository**. Agents register when a
session starts, so a session opened anywhere else cannot spawn them. Then say *"execute
docs/roadmap/NN"*. When the session ends, fill in the plan's *Session log*, update the status
column below, and fix any later plan the session proved wrong. Plans are proposals, not contracts.

A session stopped by the usage limit is picked up by the next one on its own: hooks keep its handoff
in `docs/sessions/`, and the `handoff` skill resumes it (the same session, or a fresh one).

| # | plan | status | depends on |
|---|---|---|---|
| 00 | [Diagnosis: why the rebuild](00-diagnosis.md) | reference | — |
| — | Session 1: foundation (this repo, the docs, the roadmap, the spike's agents and tools) | **done** 2026-09-26 | — |
| 01 | [Session 2: vertical slice, chapter 1 A/B/C](01-vertical-slice.md) | **closed** 2026-09-27: ITERATE done. Comprehension holds; not GO on one lecture paragraph, whose lever moved to the planner. Chapter 1 = C3 | session 1 |
| 01b | [Session 2b: the wire format, terse hand-offs between agents](01b-wire-format.md) | **built** 2026-09-27; L3's live checks done (two templates fixed, the trace fixed); the rest in 02 and 05 | 01 |
| 02 | [Session 3: the full loop and serial memory](02-full-loop.md) | **done** 2026-10-02: ch 2–3 through the full loop, click-next 4 every round; state clean; memory agrees with a fresh read (one drift) | 01 (closed), 01b |
| 03 | [Session 4: the knowledge bases](03-knowledge-bases.md) | **done** 2026-10-02: 51 docs from 44 skills; `kb_check` clean, zero leaks; ch 4 at least as good as ch 2–3 (2 rounds, click-next 4) | 02 |
| 04 | [Session 5: novel setup and planning from scratch](04-front-end.md) | **done** 2026-10-03: template, init interview, `/new` `/write` `/plan` `/status`; init ran end to end from a seed (7 rounds, check clean first pass, $8.16); chapter 1 moved to 05 | 03 |
| 05 | [Session 6: benchmark run #7](05-benchmark-run-7.md) | **done** 2026-10-03: five chapters from a fresh seed, no file touched by hand; **4.5 / 5 from three blind judges** (run #6: 3.5); 18/18 premise facts in their retells; $70.73 ($3.18 per 1,000 words); findings routed, two tools and five docs fixed | 04 |
| 06 | [Session 7: measurement](06-measure-and-optimise.md) | **done** 2026-10-04: the trace per role and per chapter (time, effort, cache expiries, injected context, docs opened, a cross-check against Claude Code's own count); `tools/history.py` in the loop from ch 3. [Run #7's baseline](../experiments/2026-10-04-trace-run-7.md): the trace was 5.9% under on output (Sonnet's usage lands late); the showrunner is 41% allotted. No agent spawned | 05 |
| 06b | [Session 7b: the showrunner's cost, and noise in agents' contexts](06b-showrunner-cost.md) | **built** 2026-10-04: markdownlint and the connector out of agents' contexts; the showrunner at `medium`; `tools/room.py` (one call per step, the dispatches printed: −42% turns predicted); auto-compaction at 250k (candidate B; A needs workflows switched on); a pause at chapter boundaries. No agent spawned: the [checklist](../experiments/2026-10-04-optimisation.md) rides on the next full run | 06 |
| 06c | [Session 7c: the roles' levers, tested blind and cheaply](06c-role-levers.md) | **done** 2026-10-04: `tools/bench.py` (frozen rounds, arms, blind pairs, agreement); story editor at `medium` kept (−26% a spawn, agreement at the A/A level); loop cap, continuity editor at `medium` and clerk on Haiku lost; the writer's revisions (re-aimed by 06d to Opus `medium`) still to test | 06, 06b |
| 06d | [Session 7d: model and effort by role; the skill-authoring guide against `kb/`](06d-model-effort-and-kb.md) | **built** 2026-10-04: no role changes model (the Sonnet roles mostly read; on Opus +$6–10 a run); the rule *Sonnet only at `high`*, warned by `kb_check`; `trace.py --reprice`; the continuity editor checks its own file; a prompt audit (one fossil removed); `kb_check` warns on dated text; a bible read-set tool measured and dropped. No agent spawned | 06c |
| 07 | [Session 8: retire skilled-writer](07-retire-skilled-writer.md) | **done** 2026-10-04: the coverage diff (64 areas; 8 gaps filled, one as a new planner doc and seven as examples; the rest covered, or waived with a reason) and the `sw` tools diff in [kb-mapping.md](../kb-mapping.md); [history.md](../history.md); an archive notice in the old repo; both projects' memory updated, lessons 35–36. No agent spawned | 05 |

**After 07, no plan is written.** What remains is the next full run, which works through
[the next-run checklist](../next-run-checklist.md) (the 06–07 items and the post-07 audit's), and
the first human read of a chapter 1, once the
user lifts the standing decision that they read nothing ([07 § After the rebuild](07-retire-skilled-writer.md#after-the-rebuild)).

## Why this order

1. **01 tests the hypothesis before anything is built on it.** The hypothesis is that a lean writer
   plus an in-loop cold reader plus a reader ledger produces a chapter 1 a newcomer understands and
   wants to continue. It is tested on the same bible that produced run #6's confusing chapter 1. If
   the answer is no, nothing after it is worth doing as planned.
2. **01b makes what agents write for each other terse.**
   - It ran before 01's ITERATE re-run, whose note-protocol fix is then written once, in the new
     format.
   - It runs before 02, which adds two roles whose whole output is for other agents, so they are
     born in the wire format. It touches no channel a reader of the
   book sees, which is why the user brought it forward of "tokens later" (2026-09-27). Prose-side
   levers (effort, model, the showrunner's context) stay in 06b and 06c.
3. **02 finishes the loop across chapters.** One chapter cannot test serial memory, the state write
   or continuity.
4. **03 writes the knowledge bases** once the loop has shown what each role needs. Writing them
   first would repeat the old mistake: rules written for a pipeline nobody had run.
5. **04 is the front end.** Setting up a new novel needs the knowledge bases, and the benchmark needs
   a new novel.
6. **05 is the first comparable measurement** against run #6.
7. **06 optimises cost only after quality is established.** The user's instruction: quality first,
   tokens later. 06 measures and spawns nothing; 06b cuts what changes no role's judgement
   (no judge needed); 06c tests the levers that can change the book, on frozen inputs.
8. **07 retires the old repo** only after the new one has shipped a benchmark.

## Features

What the rebuild has built, and whether a real run has shown it working. Each session updates this
table: it is what the user reads.

| feature | plan | built | worked in a run |
|---|---|---|---|
| the room's roles (six at first, seven from 02): thin agent files and per-role knowledge bases | 1 | yes | yes (01) |
| isolation guard (`tools/guard.py`) and prose-only exports (`tools/export_prose.py`) | 1 | yes | yes (01) |
| premise sheet and reader ledger (planner) | 1 | yes | yes (01) |
| in-loop cold beta reader, calibrated | 1, 01 | yes | yes (01) |
| story editor notes and ACCEPT; warm writer revisions; one line pass | 1 | yes | yes (01) |
| blind judge: read, compare, grade | 1 | yes | yes (01) |
| hand-backs filed verbatim (`tools/handback.py`) | 01 | yes | yes (01) |
| session handoff across usage limits (hooks, `checkpoint.py`, status line, `handoff` skill) | — | yes | yes (02, 05): resumed four times in all, the agents in flight continued warm, nothing re-spawned; in 05 a user-asked `/handoff` note survived the rebuilds |
| wire format: one status line per role, notes and facts files (`kb/shared/wire.md`, `tools/wire.py`) | 01b | yes | yes for writer, story editor, line editor, planner (02). Continuity editor and clerk: the file always parses; their final message needed two fixes and is confounded with a model change (02) |
| cost and context trace (`tools/trace.py`), with the unrecorded-output flag | 01b | yes | yes (L3, 02); now warns on an unpriced model |
| lecture fixes: writer example, briefing notes, beat-sheet `learns` carriers | 01 | yes | yes: the planner check held 11 of 11 in ch 2–3, and no editor found a briefing (02); every `learns` item carried in 05's five beat sheets. The judges found three narrator lines that explain or argue, a habit now in the line editor's catalogue (05) |
| ported core: `mdio`, novel paths, text stats, lint, state check | 02 | yes | yes (02): lint every round, `state_check` clean after each chapter |
| continuity editor and clerk; planner fold mode | 02 | yes | yes (02): two real catches nobody else made; 4 clean state writes; 3 folds |
| serial memory: one reading folder, capped notes, re-read every 10 chapters | 02 | yes | yes (02, 05): the shelf held five chapters, its notes byte-identical to each accepted round's; compression worked in 02 and was not needed in 05; the every-10 re-read is still unexercised (first due at ch 10) |
| cross-chapter lens: scene log, line editor reads the last two chapters, promises carried | 02 | yes | partly (02, 05): 33 `across` lines thinned habits in 05, but the two-chapter window kept one refrain four times and all three judges named it. Fixed after 05: it searches every earlier chapter before keeping a callback |
| rewritten knowledge bases and `tools/kb_check.py` | 03 | yes | yes (03): ch 4 on the new bases matched ch 2–3 (2 rounds, click-next 4, notes on reader and continuity evidence); one doc caused a line-editor error, fixed in the doc |
| novel setup: template, planner init interview, writer style samples; `/new`, `/plan`, `/write`, `/status` | 04 | yes | yes (04, 05): `/new` clean on the first check twice; `/write` took a new novel's chapter 1 to ACCEPT with the central rule `stated`; `/status` matched the files after every chapter but one line (fixed); `/plan` moved an overdue fact (the tool then misread it; fixed). The round-6 re-ask and the round-5 mix have not arisen |
| benchmark run #7 against run #6 | 05 | yes | yes (05): 4.5 / 5 from three blind judges, unanimous (run #6: 3.5 from one reader); 18/18 premise facts in their retells; ch 1's central rule `stated` in the loop; $3.18 per 1,000 words (run #6: $4.76). Novel, models and pipeline all differ |
| test-run protocol (`docs/test-run-protocol.md`) and pre-run probes | 05 | yes | yes (05): no showrunner write under `novels/`, the toolkit frozen, every role on its pinned model; two gaps found and fixed (the judges' git status, a zsh trap) |
| per-role and per-chapter measurement: model and tool time, effort, cache expiries, injected context, opened docs, final messages, the cross-check (`tools/trace.py`) | 06 | yes | yes, on run #7's transcripts (06): the chapter split matches the run's hand-cut windows within $0.1; the cross-check matched the input side to the token and found the output under-count (lesson 30). Live, in a new run: not yet |
| docs-opened log from the guard (`docs/sessions/<session>.reads.tsv`) | 06 | yes | not yet: first written by the next run (06b) |
| cross-chapter detectors: motif, signature, two-hander, tempo (`tools/history.py`), read by the story and line editors from ch 3 | 06 | yes | on run #7's chapters, offline (06): both refrains the judges named, at their counts; the two-hander warning a chapter before the reader's complaint. In the loop: not yet (06b) |
| context hygiene: no IDE diagnostics or connector instructions in agents' contexts (`.markdownlintignore`, `disableClaudeAiConnectors`, runs from the terminal CLI) | 06b | yes | not yet: the next run's probes |
| showrunner levers: `medium` effort; `tools/room.py`, one call per loop step printing the next dispatches; auto-compaction at 250k with compact instructions and a pointer back after it (the chosen context lever, B); a pause at chapter boundaries past 80% of the 5-hour window, resumed by `CronCreate` | 06b | yes | not yet: the next full run measures turns, context, compactions and the showrunner's share against run #7's 36 turns, 344k and 41% |
| role cost levers (effort, read-set, model, loop cap), blind-tested | 06c | yes | partly: story editor `medium` kept on agreement with an A/A baseline (−26% a spawn); loop cap, continuity `medium` and clerk on Haiku lost; read-set measured, not built; the writer's revisions at Opus `medium` (re-aimed by 06d) and the planner's effort untested; the line editor at `medium` not scheduled. Savings unconfirmed until the next full run |
| model and effort by role: *Sonnet only at `high`* (warned by `kb_check`), `trace.py --reprice` | 06d | yes | on run #7's transcripts (06d): the four Sonnet roles cost $11.90, $22.13 at Opus rates. Live: nothing changed to test |
| continuity editor checks its own file (`wire.py check`) before its status line | 06d | yes | not yet: the next run |
| prompt audit against Opus 5.5 / Sonnet 5.5; `kb_check` warns on dated text in `kb/` | 06d | yes | partly: one fossil removed from the continuity editor (its final message must stay one line in the next run); `kb/` has no dated text |
| conformity guards from Anthropic's multi-agent study: a judge panel on two models (`bench.py panel`, `judge--fable`); `scaffold.py check` warns on a name another novel uses; a planner example for names the world gives | — | yes | partly: the names check found the five shared names in the two existing novels. The panel waits for the next benchmark |
| skilled-writer retired: coverage and tools diff, history, archive notice, memory | 07 | yes | yes (07): `kb_check` clean; the old repo's `sw health` 0/0/0 and its tests pass with the notice. The 8 filled gaps are new knowledge-base examples, first read in the next full run |
| genre study (`docs/genre-study.md`, `tools/study.py`), run on fan fiction: 6 published books read cold, 20 proposals, 11 applied (a writer `toggle-fanfic.md`; planner, story-editor and comedy examples); the beta reader marks source-work knowledge as a guess; the continuity editor reads `plan/timeline.md`; `kb_check --nouns` ignores ordinary words split from a name | — | yes | partly: the study ran end to end (readers, synthesis, review, apply, leak sweep 0 defects). The edits are first read in the next fan-fiction run; none is tested in the loop |
| post-07 audit: the guard refuses a working role's unscoped search, the grading rubric and any shell but `python3 tools/…`; reading folders are never rebuilt over a reader's work, and a lost memory is rebuilt by a fresh re-read (`beats`, `adopt`, `where`); `--` refused in slugs and bench names; `wire.py` parses `PLANNER DONE fold|init`; one owner per rule and one tempo threshold; the knowledge base's nouns renamed and `kb_check` warns on near names; one checklist for the next run ([next-run-checklist.md](../next-run-checklist.md)) | — | yes | partly: 291 tests, `kb_check` clean on the repo and both novels, the guard probed by hand. Live behaviour: the next run (checklist, *the audit's changes*) |
| canon research for fan fiction: a `canon-researcher` role (Sonnet, high) writes a sourced `bible/canon.md` after init's round 1 (ages and status at the story's start, timeline, terms, conflicts, what fans expect, what it could not source); `tools/canon_fetch.py` reads fan wikis through their MediaWiki API (honest user agent, a pause between requests, robots.txt honoured, a refusal reported `blocked`); the planner's `gap canon` lookups (`room.py canon`); `scaffold.py check` requires the dossier in fan fiction; the continuity editor checks against it | — | yes | partly: the fetch tool live on two Fandom wikis (infoboxes 29 and 18 fields; Wikipedia refused by its robots.txt, as designed). The role itself not yet spawned: the next fan-fiction `/new` |
| post-07 speed audit (offline, no spawn): the writer revises a copy in place; the planner reads only the previous chapter's end; the continuity editor continued warm in rounds 1–2; the next chapter's beats start at ACCEPT beside the line editor; a `planner--medium` arm and `bench.py freeze --role planner`; the 1-hour subagent cache priced and not set (lesson 38) ([audit](../experiments/2026-10-04-optimisation.md#post-07-audit-cheaper-and-faster-chapters-2026-10-06)) | — | yes | not yet: 328 tests, `kb_check` clean. Predicted ~10% of a run's cost and ~25% of its wall time; the warm continuity editor and the planner at `medium` wait for a frozen-round bench (~$2, ~$5), the rest for the next run's checklist |

## Standing decisions (from the user, 2026-09-26)

- **Fresh repo.** Port only what is proven useful. The old repo is an archive, not a dependency.
- **Chapter 1 is webnovel-clear.** By its end a reader can state the world's central rule, the MC's
  situation and the stakes in plain words. An explanatory passage is allowed.
- **Quality first.** **Opus for the hard roles** (planner, writer, story editor, judge),
  **Sonnet for the rest.** No design constraint exists for the sake of a smaller model.
  **Sonnet 5.5 runs at `high` only** (2026-10-04, [06d](06d-model-effort-and-kb.md)): below it the
  public index drops sharply, above it Opus at `medium` is cheaper for more. A role that needs more
  moves to Opus at `medium`. `kb_check` warns on a Sonnet agent at another effort.
- **Multiple agents in feedback loops**, not a single drafter plus a gate.
- **Per-role knowledge bases in OKF format** replace the old cards, routing and search.
- **Fewer limitations than the old repo.** Carry over a rule only when its evidence still applies.
  [lessons.md](../lessons.md) says which ones do.
- **Test by parts, then once end to end** (2026-09-27). A plan builds its change and unit-tests
  it; it spends no agent runs re-testing itself. Each change is checked live by the next plan whose
  run uses it, and the whole roadmap gets one complete test run at the end (05). A calibrated
  instrument (the beta reader, the judge) is not changed without the calibration it needs.
- **The user reads nothing and picks nothing during the rebuild** (2026-09-27). Every call a plan
  once left to the user, such as which arm, which seed or which register, the showrunner makes on
  the evidence and logs with its reason. Quality verdicts come from the blind judges and the in-loop
  reader. A product feature that asks its user something (the init interview) is still built, and
  in test runs the showrunner answers it from an answer sheet. Each session reports to the user
  which features are built and whether they worked: the *Features* table above.
- **What agents write for each other is terse** (2026-09-27): keyed lines, ids and paths instead of
  restating, and one status line as each role's final message. No human reads those channels. The
  prose, the reader's retell and everything addressed to the user stay full. See [01b](01b-wire-format.md).

## Session 1 log (2026-09-26, run from the skilled-writer session)

Built: this README, 00–07, `docs/architecture.md`, `docs/novel-format.md`, `docs/lessons.md`,
`CLAUDE.md`, six thin agents, seed knowledge bases (`kb/`: showrunner, planner, writer, beta reader,
story editor, line editor, judge, shared), `tools/guard.py`, `tools/export_prose.py`, 36 tests. The
old repo got a one-line archive banner in `README.md` and `CLAUDE.md` (its health check and 776
tests still pass). Nothing committed in either repo.

Decided during the session, beyond the approved plan:

- **Fewer limitations** (the user, mid-session): a Python dependency is allowed when it earns its
  place, and the guard enforces isolation only where it is load-bearing.
- **The working roles are kept out of each other's `kb/`** (the writer cannot open the beta reader's
  questionnaire or the critics' rubrics; nobody in the loop can open the judge's), so the loop
  cannot learn its instruments.
- **`grading.md` lives in `kb/shared/`** because the judge grades retells too, and the judge can
  read nothing outside its own folder except that one file.
- **The line editor cannot reach `bench/`**, so in plan 01 it writes to `work/` and the showrunner
  copies arms into `bench/`.
- **Real-data check:** `export_prose.py` on run #6's chapter 1 strips every intent field
  (`event`, `delivers`, `threads`, `in_world_day`); its neutral id is `rff04f9`.

Claude Code memory for this work lives in skilled-writer's project memory, which a session opened
here will not load. Everything a session here needs is in this repo: `CLAUDE.md` and this roadmap.
