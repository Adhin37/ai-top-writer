# 07 — Session 8: retire skilled-writer

**Goal:** close the old repo cleanly once this one has shipped a benchmark (plan 05). Nothing it knew
should be lost by accident; anything dropped is dropped on purpose.

## Steps

1. **Coverage diff.** Walk `skilled-writer/docs/coverage-map.md` area by area. Every area should
   have a destination in this repo (a KB doc, a tool, a role's procedure, a ledger) or a written
   reason in `docs/kb-mapping.md` for being dropped. List the gaps and fill or waive each one.
2. **Tools diff.** For every `sw` command, record: ported (where), replaced (by what), or dropped
   (why). `health`, `contract`, `load`, `kb` routing and the card budgets are expected drops — the
   corpus they policed no longer exists.
3. **History.** Copy the durable parts of `skilled-writer/docs/benchmark.md` (the per-run headline
   table, the *what run #N established* sections) into `docs/history.md` here, condensed; link the
   old repo's git history for the rest.
4. **Archive notice.** Replace the one-line banner in the old repo's `README.md` and `CLAUDE.md`
   with a short archive notice pointing here; the old agents stay as they are (nobody should run
   them, but deleting them destroys the record).
5. **Memory.** Update the Claude Code memory files for both projects: mark the skilled-writer
   memories as historical, and make sure every lesson still in force lives in this repo's
   `docs/lessons.md` rather than only in memory.
6. Commit in both repos **only if the user asks**.

## After the rebuild

Every reader in the loop and on the bench is Claude, so they share blind spots that no panel can
reveal (Anthropic's multi-agent study, and its research-system post: automated evals miss what
human testers catch). When the rebuild closes and the standing decision that the user reads
nothing lapses, the first human read is the check: one person reads chapter 1 blind and answers
the judge's questions 1–3. It is not part of this plan.

## Exit criteria

The coverage diff has no unexplained gap, and a new session in either repo is told where the live
work is.

## Session log

2026-10-04, one session in this repo. No agent spawned; nothing committed in either repo.

- **Step 1, the coverage diff** ([kb-mapping.md § The coverage diff](../kb-mapping.md#the-coverage-diff-plan-07)).
  - I walked all 64 areas of `coverage-map.md` plus its open items against `kb/`, the template and
    `tools/`, reading the destination doc wherever a grep was not proof. The per-skill mapping
    from plan 03 had missed eight areas, each a reference inside a skill that was mapped.
  - **Filled** (one new doc, the rest as examples with the knowledge bases' invented nouns):
    planner `long-middle.md` (new, indexed), and examples in `stakes.md` (money stops deciding),
    `arcs-and-chapters.md` (the rate the opening promises), `cast-design.md` (a mind that is not a
    person), `world-design.md` (an oath), `bias-structural.md` (the stance), writer
    `scene-and-summary.md` and continuity `provenance.md` (learning a skill), story editor
    `cost-and-keep.md` (the free win, the face-slap loop), line editor `ai-default-habits.md`
    (the gasping crowd).
  - **Covered** under other names: eight areas. **Waived**, each with its reason: four.
  - Fixed on the way: the mapping named `people-on-the-page.md`, which plan 03 shipped as
    `people-and-figures.md`.
- **Step 2, the tools diff** ([kb-mapping.md § The `sw` commands](../kb-mapping.md#the-sw-commands-plan-07)).
  Six commands ported, three replaced, ten dropped, three hooks replaced by `guard.py`. The
  expected drops (`health`, `contract`, `load`, `kb`, the budgets) were dropped, and so were `cast`,
  `curve` and `stamp`: each was a number a drafter writes toward (lesson 8).
- **Step 3, history**: [history.md](../history.md). It has a table of runs #1–#7, what each
  established, and the commit holding each old write-up. Runs #1–#2's figures came from the old
  repo's git history, because its current `benchmark.md` keeps only #3 onward in detail.
- **Step 4, the archive notice**: `README.md`, `CLAUDE.md` and `AGENTS.md` in the old repo
  (`AGENTS.md` too, since other harnesses read it first). Its agents, skills and novels are
  untouched. Its `sw health` is 0/0/0 and its tests pass with the notice. The untracked
  `plan the following :.md` there is the user's, and I left it alone.
- **Step 5, memory.**
  - skilled-writer's 14 memories: each is marked historical in its body, and the index opens on a
    line saying so. `ai-top-writer-rebuild` had said "next is plan 01"; it now points here.
  - Lessons that lived only in memory are now in [lessons.md](../lessons.md): 16 (memory hooks are
    a prompt), 17 (hook paths, failing open), 35 (a custom base URL costs the 1M window), 36 (a
    test that stops looking).
  - This repo's two memories still hold, so they are unchanged.
- **Checks**: `kb_check.py` 0 defect · 0 warn; tests 270 OK.
- **Found, not fixed**: `kb_check.py --novel novels/varrow-bells` reports three leak defects for
  "Board" in writer `orienting-the-reader.md`. That predates this plan. The word is generic, the
  novel is plan 04's throwaway, and the example is the lecture fix's calibrated one, so I left it.
  Rename it if varrow-bells is ever used again.

**Exit criteria: met.** The coverage diff has no unexplained gap. A new session in the old repo
reads the archive notice in `CLAUDE.md`, and its memory index opens on a line pointing here. A
session here reads `CLAUDE.md` and the roadmap.
