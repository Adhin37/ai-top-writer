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

*(filled in when this plan runs)*
