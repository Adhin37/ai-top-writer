# 06b — Session 7b: the showrunner's cost, and noise in agents' contexts

**Goal:** cut the cost that changes no role's judgement. In run #7 the showrunner was $33.88 of
$77.21 (44% as traced; **41%** once the trace's output under-count is allotted, per
[06's baseline](../experiments/2026-10-04-trace-run-7.md)), and almost none of it was thinking. 100M tokens were re-read across 296 responses
over a context of mean 344k ($20.09), plus $10.31 of cache writes, mostly the rebuilds after two
usage-limit pauses. Its own output was $3.48. The cost is context × turns.
Evidence and sources: [2026-10-04 research](../experiments/2026-10-04-cost-levers.md).

**Why no judge:** none of these levers changes what the planner, writer or critics read or how
they reason. Removing injected noise is the one exception, and it only takes away text that no
role asked for. The trace and the routing check them (`tools/status.py`, `tools/state_check.py`,
the wire status lines). The risk is to routing, not to the book.

Depends on 06: the trace's per-chapter split, cache-expiry and injected-context lines are the
before/after instrument (`trace.py <session> --chapters`). Run #7's numbers for each lever are in
[the baseline](../experiments/2026-10-04-trace-run-7.md): 15–45 showrunner turns a chapter (mean
36), $5.73 of showrunner cache rebuilt after two pauses, 166k characters of IDE diagnostics (133k
into the planner), 129k of MCP instructions across 68 spawns.

**Also in this plan's first live chapter** (moved from 06): read `/usage`'s plan breakdown once
in the session and set its per-subagent shares beside the trace's allotted shares. And check that
`docs/sessions/<session>.reads.tsv` fills, and that the story and line editors act on
`history-rK.txt` from chapter 3 (06's changes, live-checked here).

## Levers, cheapest first

1. **Take the noise out.** Both changes are free, and neither needs a run to justify it:
   - **markdownlint.** VS Code's markdownlint extension injects `<ide_diagnostics>` into an agent's
     context after its edits: ~151k characters into run #7's planner, and warnings about its own
     `notes.md` into the cold beta reader. Add a `.markdownlintignore` for `novels/`, `reading/`
     and `bench/`. Running test runs from a terminal instead of the IDE also removes it.
   - **The claude.ai connector.** Its MCP instructions (~2.1k characters) reach every subagent,
     the beta reader and the judge included. Turn the connector off for this project, and check
     in one spawn's transcript that no `mcp_instructions_delta` arrives.
2. **The showrunner's effort.** It runs at `xhigh` (user settings). Set `effortLevel: "medium"` in
   `.claude/settings.json`, which is Claude Code's default for Opus 5.5. Use `ultrathink` for the
   one judgement call it makes, approving a beat sheet. On Opus 5.5 an effort change keeps the
   cache. Expected saving: at most ~$2 a run, but it is free.
3. **Fewer showrunner turns.** Each turn re-reads the whole context; run #7 needed ~59 a chapter.
   - Fold each step's deterministic calls (export, reading view, lint, wire parse, hand-back
     filing) into one `tools/room.py <step>` call. It prints only the paths and status lines the
     next step needs.
   - Spawn the two readers of a round in one turn.
   - Never open a role's file to check that it exists.
   - Target: half the turns per chapter, counted by the trace.
4. **Keep the context small.** Build one candidate and fall back to the other. Pilot each on one
   chapter.
   - **A. A workflow per chapter** (`.claude/workflows/write-chapter.js`, Claude Code's dynamic
     workflows; on Pro, enable in `/config`). The script holds the loop:
     - planner beats → approval → writer → `parallel(beta reader, continuity editor)` → story
       editor → at most two revisions → line editor → clerk → fold;
     - intermediate results stay in script variables, so the showrunner's context grows by one
       launch and one result per chapter;
     - an `agent()` call with a JSON `schema` replaces a status line, so a recap around it cannot
       happen;
     - a run waits out a usage limit and continues on its own (interactive sessions only).

     **Verify first** (read the `/workflow-authoring` skill; probes are user-approved spawns):
     - does `agent()` take a named agent type, so the guard, the model and the effort come from
       `.claude/agents/`?
     - do `PreToolUse` hooks (the guard) fire for workflow agents?
     - can a step continue an agent warm? The writer's revisions are a warm continuation. If they
       cannot, the revision becomes a fresh writer given its draft and the notes. That changes the
       writer's procedure, and [06c](06c-role-levers.md) must judge it, so keep the revision steps
       in the showrunner and script the rest;
     - the script has no shell, so the Python tools run in an agent that has `Bash` (the clerk and
       the continuity editor already do), or in a minimal runner agent on Haiku.
   - **B. One chapter per showrunner context**, the old lever 0. Hand over at each chapter boundary
     with the existing `handoff` skill and `/clear`. Simpler, but it leaves a chapter's turns in
     context. Alternative: set `CLAUDE_CODE_AUTO_COMPACT_WINDOW` to ~150k and put compact
     instructions in `CLAUDE.md`. The hooks already rebuild the handoff every turn, so a
     compaction loses nothing that is on disk.
5. **Pause at chapter boundaries.** The status line already knows the five-hour window's use. Past
   ~80%, finish the current step and start no new chapter. The rebuild after the reset then costs
   a small context, not run #7's ~$2.8 and ~$3.7.

## Measure

Showrunner cost per chapter (run #7: ~$6.8 with judging spread in), turns per chapter, mean
context, and the cost of each usage-limit pause, from the trace. Record the result in
`docs/experiments/<date>-optimisation.md`, including the candidate that lost.

## Exit criteria

- No `ide_diagnostics` or connector instructions in a spawn's transcript.
- The showrunner's share of a run is measured below run #7's 41% (44% as traced), with routing clean:
  `status.py` matches the files, and `state_check.py` is clean after every chapter.
- The chosen context lever is written into `kb/showrunner/loop.md` and the *Features* table.

## Session log

**2026-10-04 — built; no agent spawned.** Following the standing *test by parts* decision, every
lever is built and unit-tested (251 tests pass, `kb_check` clean), and the next full run measures
them. Predictions, the losing candidate and the checklist for that run:
[2026-10-04-optimisation.md](../experiments/2026-10-04-optimisation.md).

- **Lever 1.** `.markdownlintignore` covers `novels/`, `reading/`, `bench/` and `docs/sessions/`.
  `disableClaudeAiConnectors: true` is in `.claude/settings.json`; it takes effect in a new
  session, and it switches the connectors off for every session in this repository, maintenance
  ones included. The test-run protocol now runs from the terminal CLI and checks the probe's
  injected-context line for `mcp` and `ide_diagnostics`.
- **Lever 2.** `effortLevel: "medium"`, and the same under `modelSettings.claude-opus-5-5`,
  because the user's settings set a per-model level there, which outranks a top-level one.
  **`ultrathink` was not used**: it is a keyword in a prompt the user types, and the showrunner
  cannot raise its own effort for the approval mid-run. The approval is a three-point check
  against files, which `medium` (Claude Code's default) can do.
- **Lever 3.** `tools/room.py`: `beats`, `round`, `judge`, `clerk`, `fold`, `adopt`, `where`.
  Each runs a step's tools and checks its files, and prints the next dispatches with the same
  texts `loop.md` held before. `--log` / `--agent` replace the per-agent `handback.py --append`
  calls, and its plan-row and ledger-debt checks replace `/write`'s `status.py` call before each
  chapter. Predicted turns: 8 a chapter plus 5 a round, a mean of 21 on run #7's rounds against 36
  (−42%, short of the half the plan targeted; the rest is one turn per agent sent).
- **Lever 4: B, not A.** A needs workflows switched on in `/config` (a user action on Pro) and
  probe spawns to answer its questions, so it was not built. B: `autoCompactWindow: 250000`,
  `# Compact instructions` in `CLAUDE.md`, and a SessionStart hook that points a compacted
  session at its handoff and `room.py where`. 250k, not 150k, because the docs do not say
  whether the window reaches subagents, and run #7's planner peaked at 194k. The trace now
  counts compactions per role, to settle it.
- **Lever 5.** The status line's reading drives an 80% notice (`session_hooks.py`, once per
  window) and a `PAUSE` line from `room.py beats` and `fold`. `loop.md`'s *Pause at a chapter
  boundary* schedules the resume with a one-shot `CronCreate` at the reset. It works only where
  the status line runs: the terminal CLI.
- **Also in this plan's first live chapter** (above): not done, no chapter ran. It moves to the
  next full run's checklist.
- `docs/lessons.md` 31: the settings traps found on the way.

**Exit criteria:** the first is checked by the next run's probes; the second needs a run; the
third is met (`loop.md`, the *Features* table).
