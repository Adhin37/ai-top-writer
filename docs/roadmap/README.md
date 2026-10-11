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
| 08 | [Session 9: the lead's pressure, an outside slop figure, and run #9](08-pressure-and-run-9.md) | **steps 1–2 built** 2026-10-10: Pressure rows in the ledger (`L1` the lead's lever, `C1` the clock), flagged by `status.py` and handed to the planner; EQ-Bench's slop index in `lint.py` (it does not separate run #7 from run #8). **Step 3 done** 2026-10-10 ($10.13): Pressure rows alone left the ch 5 event passive, so the planner now checks the lever when it writes plan rows; the planner stays at `high`. **Step 4 done** 2026-10-11, run #9 on ch 6–12 ([write-up](../experiments/2026-10-10-run-9.md)): 4.5 / 4.5 / 4 from the blind panel, 14/18 premise facts stated; the agency complaint is gone; $1.95 per 1,000 words | run #8 |
| 09 | [Session 10: the canon researcher reads sections, not pages](09-canon-reading.md) | **built** 2026-10-11: `canon_fetch.py` `toc`, `grep`, `restyle` and scene headings for transcripts; the canon researcher finds, then reads the part (one rule replacing one); the live check rides on the next fan-fiction init or lookup. Haiku 5.5 test closed ([write-up](../experiments/2026-10-11-haiku-5-5.md)): clerk and canon researcher both lost; `trace.py` prices Haiku 5.5's 5× tier. No agent spawned | 08 |
| 10 | [Session 11: prompts a smaller model can follow, then Haiku 5.5 again](10-prompts-for-smaller-models.md) | **done** 2026-10-11: each Haiku miss traced to a `kb/` line it followed (the clerk's "from its grade", a one-clause `ev`, "the work itself" without transcripts, ages without ranks); those lines replaced, one `ev` example, and `state_check` warns on a ledger row the clerk moved after an earlier chapter set it. Retest ([write-up](../experiments/2026-10-11-haiku-5-5-retest.md)): every targeted miss fixed, but both roles **stay on Sonnet** (the clerk thinner on `kno` and the fold; the canon researcher half the sources) | 09 |
| 11 | [Session 12: bounded reads, no context that grows with the book](11-bounded-reads.md) | **built** 2026-10-11: `continuity.md` read by line range (clerk, planner, story editor); `room.py approve` (the showrunner reads the beat sheet's header, not the sheet); `room.py`'s lists capped; `history.py` lists only what the newest chapter uses; the fresh re-read budgeted at ~100k tokens; `canon_fetch` `toc`/`grep`/`category` capped; the handoff keeps 2 + 8 user messages. The reader's report stays a hand-back (Claude Code refuses a report file). No agent spawned | 10 |
| 12 | [The instruction files against Anthropic's guidance](12-instruction-files.md) | **P1 built** 2026-10-11: Contents in the 12 long kb docs, the bible section map in dispatches, CLAUDE.md −28%; **P2 built** the same day: `kb_check` warns on a doc two hops deep, one term per concept, the fold files a place under its own heading; P3 waits for a run that needs it | 11 |

After 08, run #9's routed fixes are built (2026-10-11, [the write-up's fixes](../experiments/2026-10-10-run-9.md#fixes-2026-10-11-after-the-run-no-agent-spawned)):
recap examples for the story editor and the writer, the pressure grade's warn, the motif union, the clock
and the antagonist as planner examples. A run confirms them ([checklist](../next-run-checklist.md#run-9s-fixes-2026-10-11)).
What remains is that run and the first human read of a chapter 1, once the
user lifts the standing decision that they read nothing ([07 § After the rebuild](07-retire-skilled-writer.md#after-the-rebuild)).

Next: no plan is written past 12; 12's P3 waits for a run that needs it. What remains is the next full run, which checks the open items in the [checklist](../next-run-checklist.md) (plans 08–10 among them).

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
| serial memory: one reading folder, capped notes, re-read every 10 chapters | 02 | yes | yes (02, 05): the shelf held five chapters, its notes byte-identical to each accepted round's; compression worked in 02 and was not needed in 05; the every-10 re-read ran at ch 10 in run #9: the fresh reader gave 4, as the warm one did, and named the same gap |
| cross-chapter lens: scene log, line editor reads the last two chapters, promises carried | 02 | yes | partly (02, 05): 33 `across` lines thinned habits in 05, but the two-chapter window kept one refrain four times and all three judges named it. Fixed after 05: it searches every earlier chapter before keeping a callback |
| rewritten knowledge bases and `tools/kb_check.py` | 03 | yes | yes (03): ch 4 on the new bases matched ch 2–3 (2 rounds, click-next 4, notes on reader and continuity evidence); one doc caused a line-editor error, fixed in the doc |
| novel setup: template, planner init interview, writer style samples; `/new`, `/plan`, `/write`, `/status` | 04 | yes | yes (04, 05): `/new` clean on the first check twice; `/write` took a new novel's chapter 1 to ACCEPT with the central rule `stated`; `/status` matched the files after every chapter but one line (fixed); `/plan` moved an overdue fact (the tool then misread it; fixed). The round-6 re-ask and the round-5 mix have not arisen |
| benchmark run #7 against run #6 | 05 | yes | yes (05): 4.5 / 5 from three blind judges, unanimous (run #6: 3.5 from one reader); 18/18 premise facts in their retells; ch 1's central rule `stated` in the loop; $3.18 per 1,000 words (run #6: $4.76). Novel, models and pipeline all differ |
| test run #8, fan fiction (*Avatar* OC), five chapters | — | yes | yes ([write-up](../experiments/2026-10-09-run-8.md)): 4 / 5 from a blind panel on two models, unanimous; 12/18 premise facts stated, 6 partly, 0 wrong (run #7: 4.5, 18/18); $2.43 per 1,000 words (run #7: $3.18). The judges' shared cost is the protagonist's lack of a lever |
| test run #9, the same novel, ch 6–12, with the pressure ledger | 08 | yes | yes ([write-up](../experiments/2026-10-10-run-9.md)): 4.5 / 4.5 / 4 from a blind panel on two models; 14/18 premise facts stated, 4 partly, 0 wrong; $1.95 per 1,000 words. The lever complaint is gone. The judges' shared costs: recap paragraphs (one written for a revision note), tics, and a clock still ~80 days out at ch 12 |
| test-run protocol (`docs/test-run-protocol.md`) and pre-run probes | 05 | yes | yes (05): no showrunner write under `novels/`, the toolkit frozen, every role on its pinned model; two gaps found and fixed (the judges' git status, a zsh trap) |
| per-role and per-chapter measurement: model and tool time, effort, cache expiries, injected context, opened docs, final messages, the cross-check (`tools/trace.py`) | 06 | yes | yes, on run #7's transcripts (06): the chapter split matches the run's hand-cut windows within $0.1; the cross-check matched the input side to the token and found the output under-count (lesson 30). Live (run #8): yes, every figure in its write-up came from it; the injected-context line caught F14 |
| docs-opened log from the guard (`docs/sessions/<session>.reads.tsv`) | 06 | yes | yes (run #8): 856+ rows; it showed all ten 07 examples opened and one planner slip (an earlier beat sheet) |
| cross-chapter detectors: motif, signature, two-hander, tempo (`tools/history.py`), read by the story and line editors from ch 3 | 06 | yes | on run #7's chapters, offline (06): both refrains the judges named, at their counts; the two-hander warning a chapter before the reader's complaint. In the loop (run #8): yes for phrases, from ch 3 the line editors cut repeats citing its counts; it does not count per-character gestures or tag questions, which all three judges named. Fixed after run #8: `gesture`, `tag` and `recap` detectors (on run #8's chapters: the glove in 14 sentences, one captain's 6 tag questions, ch 5's re-told rule); in the loop (run #9): gestures at half run #8's rate and tag questions stopped after ch 8, but `recap` matches near-verbatim sentences and missed the two paraphrased recap paragraphs all three judges named; the motif detector chains a place name into a refrain (a false positive in ch 11). Fixed after run #9: motifs join on two shared places, not one (ch 11 now reports the place name alone); a paraphrase `recap` by paragraph overlap was benched and not shipped (the judges' two recaps ranked near the bottom) |
| context hygiene: no IDE diagnostics or connector instructions in agents' contexts (`.markdownlintignore`, `disableClaudeAiConnectors`, runs from the terminal CLI) | 06b | yes | **no** (run #8): markdownlint in VS Code ignores `.markdownlintignore`, so 425 warnings on `novels/` and `reading/` files reached agents after their edits (planner 174k chars), about 1 s an edit. The probes missed it because they edit nothing. No connector instructions. Fixed after run #8: a `{"default": false}` `.markdownlint.json` per folder (probed by an edit: 9 warnings in `docs/`, 0 in `novels/`), and `includeGitInstructions: false` takes git status out of every context (F20). Live (run #9): **yes**, the edit probe drew nothing, no `ide_diagnostics` in the trace, no judge saw git. New: the harness's `userEmail` line reaches every subagent |
| showrunner levers: `medium` effort; `tools/room.py`, one call per loop step printing the next dispatches; auto-compaction at 250k with compact instructions and a pointer back after it (the chosen context lever, B); a pause at chapter boundaries past 80% of the 5-hour window, resumed by `CronCreate` | 06b | yes | yes (run #8): mean 37 turns a chapter; context mean 136k, peak 217k (run #7: 344k, 596k); 2 compactions; share 22% through ch 5 (run #7: 44%). The `CronCreate` resume never ran: both stops were resumed by the user. Run #9: 33 turns a chapter, mean 134k, peak 216k, share 20%; two usage-limit stops mid-chapter with no PAUSE line (VS Code panel), resumed by the user |
| role cost levers (effort, read-set, model, loop cap), blind-tested | 06c | yes | partly: story editor `medium` kept on agreement with an A/A baseline (−26% a spawn); loop cap, continuity `medium` and clerk on Haiku lost; read-set measured, not built; the writer's revisions at Opus `medium` (re-aimed by 06d) untested; the planner at `medium` lost on a frozen round (2026-10-10: +6% cost, same sheet), it stays at `high`; the line editor at `medium` not scheduled. Haiku 5.5 (2026-10-11, [write-up](../experiments/2026-10-11-haiku-5-5.md)): the clerk lost again (a past ledger row re-marked from a notes line), the canon researcher lost (no transcript read, a rank stated past its date), at a fifth to a quarter of Sonnet's cost; plan 10 traced most misses to the md files and fixed them; the retest ([write-up](../experiments/2026-10-11-haiku-5-5-retest.md)) matched Sonnet on the ledger but not on depth, so both roles stay on Sonnet. Run #8 confirmed the story editor: −27% a spawn, notes still specific. Run #9: the warm story editor cost $0.69 a chapter, $4.84 for 14 rounds (run #8 $5.51 for 14 cold spawns), and its owed grades held steady between rounds |
| model and effort by role: *Sonnet only at `high`* (warned by `kb_check`), `trace.py --reprice` | 06d | yes | on run #7's transcripts (06d): the four Sonnet roles cost $11.90, $22.13 at Opus rates. Live: nothing changed to test |
| continuity editor checks its own file (`wire.py check`) before its status line | 06d | yes | yes (run #8): `wire.py check` in every continuity spawn; 13/13 final messages one line |
| prompt audit against Opus 5.5 / Sonnet 5.5; `kb_check` warns on dated text in `kb/` | 06d | yes | partly: one fossil removed from the continuity editor (its final message must stay one line in the next run); `kb/` has no dated text |
| conformity guards from Anthropic's multi-agent study: a judge panel on two models (`bench.py panel`, `judge--fable`); `scaffold.py check` warns on a name another novel uses; a planner example for names the world gives | — | yes | partly: the names check found the five shared names in the two existing novels. The panel ran in run #8: 4/4/4 on Opus 5 and Fable, spread 0. All three readers said the blind leaks through the session's cwd name, folder path and git status (F20). Run #9: 4.5 / 4.5 on Opus 5, 4 on Fable; spread 0 within a model, 0.5 across |
| skilled-writer retired: coverage and tools diff, history, archive notice, memory | 07 | yes | yes (07): `kb_check` clean; the old repo's `sw health` 0/0/0 and its tests pass with the notice. The 8 filled gaps are new knowledge-base examples, first read in the next full run |
| genre study (`docs/genre-study.md`, `tools/study.py`), run on fan fiction: 6 published books read cold, 20 proposals, 11 applied (a writer `toggle-fanfic.md`; planner, story-editor and comedy examples); the beta reader marks source-work knowledge as a guess; the continuity editor reads `plan/timeline.md`; `kb_check --nouns` ignores ordinary words split from a name | — | yes | partly: the study ran end to end (readers, synthesis, review, apply, leak sweep 0 defects). Read in run #8's loop (the beta reader marked canon knowledge as guesses), not isolated. Two judges still found the canon used as furniture |
| post-07 audit: the guard refuses a working role's unscoped search, the grading rubric and any shell but `python3 tools/…`; reading folders are never rebuilt over a reader's work, and a lost memory is rebuilt by a fresh re-read (`beats`, `adopt`, `where`); `--` refused in slugs and bench names; `wire.py` parses `PLANNER DONE fold|init`; one owner per rule and one tempo threshold; the knowledge base's nouns renamed and `kb_check` warns on near names; one checklist for the next run ([next-run-checklist.md](../next-run-checklist.md)) | — | yes | partly: 291 tests, `kb_check` clean on the repo and both novels, the guard probed by hand. Live (run #8): yes. 41 guard refusals, none needed; no reading folder rebuilt; no false `PLANNER DONE` defect. `kb_check --novel` still flags number words (F4), fixed after the run (29 defects → 0). Run #9: 21 refusals (clerk 10, continuity 11, all shell compounds), none needed |
| canon research for fan fiction: a `canon-researcher` role (Sonnet, high) writes a sourced `bible/canon.md` after init's round 1 (ages and status at the story's start, timeline, terms, conflicts, what fans expect, what it could not source); `tools/canon_fetch.py` reads fan wikis through their MediaWiki API (honest user agent, a pause between requests, robots.txt honoured, a refusal reported `blocked`); the planner's `gap canon` lookups (`room.py canon`); `scaffold.py check` requires the dossier in fan fiction; the continuity editor checks against it | — | yes | partly: the fetch tool live on two Fandom wikis (infoboxes 29 and 18 fields; Wikipedia refused by its robots.txt, as designed). Live (run #8): yes. 36 facts, 23 sources, 10 unsure, 0 blocked, and no canon finding in 14 continuity rounds; two small gaps (init has no slot for `gap canon`, guard refuses its `scaffold.py check`), both fixed after the run |
| post-07 speed audit (offline, no spawn): the writer revises a copy in place; the planner reads only the previous chapter's end; the continuity editor continued warm in rounds 1–2; the next chapter's beats start at ACCEPT beside the line editor; a `planner--medium` arm and `bench.py freeze --role planner`; the 1-hour subagent cache priced and not set (lesson 38) ([audit](../experiments/2026-10-04-optimisation.md#post-07-audit-cheaper-and-faster-chapters-2026-10-06)) | — | yes | not yet: 328 tests, `kb_check` clean. Predicted ~10% of a run's cost and ~25% of its wall time; the warm continuity editor and the planner at `medium` wait for a frozen-round bench (~$2, ~$5), Live (run #8): yes, with one bug. Writer output −27%; warm continuity rounds 0.3–0.5 min; beats at ACCEPT saved the wait, but when they outran the clerk `room.py fold` spawned a second planner (F11). Fixed: an `ahead.txt` mark and `fold --cold`. Added after run #8: the story editor continued warm in rounds 1–2, and `room.py round` runs the lint for the continuity editor. Live (run #9): yes, both. `ahead.txt` at every ACCEPT that offered the beats, no second planner; the lint read in 14 of 14 rounds |
| Pressure in the reader ledger: `L1` the lead's lever and `C1` the clock, one step a chapter (`grew/held/shrank`, `nearer/held/later`), planned in the beat sheet, graded by the story editor, written by the clerk; `status.py` flags a step back or two holds and `room.py` hands the flag to the next beats dispatch | 08 | yes | partly, on a frozen round ([bench](../experiments/2026-10-10-agency-bench.md)): every planner wrote the rows and a `pressure` line unasked, but kept a passive event and one graded a declined move `grew`. Moved upstream: the planner's plan task and init check the rows ahead against `L1`/`C1`. Live (run #9): **yes**. Every beat sheet carried a `pressure` line, the clerk wrote a step a chapter (L1 grew 6 of 7), and the one flag (ch 5's shrank) was answered. No judge named agency, which all three ranked first or second in run #8, and Kesa's want went from partly ×3 to stated ×3. Gaps: the story editor skipped the grade at ch 8–9 and grades uptake rather than direction. Fixed after run #9: `room.py judge` and `clerk` warn on a `pressure` id the notes leave ungraded, and the warm story editor is asked to grade it; the direction stays the clerk's |
| EQ-Bench's slop index in `lint.py` (their lists, vendored, and their formula, unchanged) | 08 | yes | offline only: run #8 mean 6.2, run #7 6.4, so it does not separate the judges' scores; run #8 rose from 3.9 (ch 1) to 8.3 (ch 4). Live (run #9): in every lint file; drafts 5.7, accepted chapters 5.2; a reference the line editor touched twice |
| canon researcher reads sections, not pages: `canon_fetch.py` `toc` (headings with line ranges and sizes), `grep` (matching paragraphs under their heading, capped), scene headings for transcripts (`render()`, and `restyle` for a saved cache); `sources.md` *find, then read the part*; `trace.py` prices Haiku 5.5's 5× tier above 100k input | 09 | yes | not yet: 369 tests, `kb_check` clean; ember-terraces' 31 transcripts split into 497 scenes (median 1.6k characters, against 20–55k a page). Baseline: a Sonnet init spawn $3.45, 0.69M cache writes, 3 compactions. The live check rides on the next fan-fiction init or `gap canon` lookup |
| bounded reads: `continuity.md` by line range in every dispatch that needs a block; `room.py approve` (the beat sheet's header, the due rows); `room.py`'s lists capped at 8; `history.py` counts warn motifs the newest chapter lacks; the fresh re-read's budget (`reading.FRESH_BUDGET`); `canon_fetch` `toc` one line a file, `grep`/`category` ceilings; the handoff's user messages capped | 11 | yes | **yes** (run #10, ch 13–14, [write-up](../experiments/2026-10-11-run-10.md#write-up)): approval from the header, 7 of 7 `continuity.md` reads by range, blocks appended in place, no showrunner compaction, hand-backs 9% of its cache reads (59%); the clerk, planner and story editor cost no less a spawn; the fresh budget waits for ch 20. Offline: offline on ember-terraces ch 12: the last block 5.5 of 46 KB, the history report 7.5 → 5.5 KB, the approval read 2.7–5.9 of 10–17 KB, `toc` of the cache 68 → 6.1 KB. Baseline (run #9): showrunner 3 compactions, hand-backs 59% of its cache reads |
| prompts a smaller model can follow: the clerk's ledger rule (a grade sets a row only where this chapter owes or pays it), a whole `ev`, `at` from the page only, a Pressure step that keeps its day and cost; "the work itself" for a show is its transcripts; ranks worked out at the start; `room.py clerk` saves `ledger-before.md` and `state_check` warns on a moved row | 10 | yes | partly: on Haiku 5.5 every targeted miss gone in the retest, and the warn silent on all four clerk arms; on Sonnet, the next full run checks them |
| best-practice pass: a `## Contents` list in each kb doc over 100 lines (12 docs; `kb_check` warns when one lacks it or misses a section); `room.py` maps each long bible file's sections with line ranges in the planner, writer, continuity and clerk dispatches (`mdio.headings`, fence-aware, shared with `canon_fetch toc`); CLAUDE.md −28% (the tools' list moved to `docs/architecture.md`), its pointers say when to read, no `@` imports. Reverses 06d's set-aside of contents lists for the kb docs, on the user's request; 06d's reason still holds there (they are read whole, so the gain is orientation, ~10 lines a doc); the bible map is the part with evidence (world.md 35.7k on ember-terraces, opened whole 30 times in run #9) | 12 | yes | not yet: 386 tests, `kb_check` clean; the [checklist](../next-run-checklist.md#best-practice-pass-2026-10-11) rides on the next run |

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
