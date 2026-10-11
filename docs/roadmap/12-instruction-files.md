# 12 — The instruction files against Anthropic's guidance

**Goal:** apply what Anthropic's published guidance says about instruction files to the files the
room's agents read: `CLAUDE.md`, `kb/`, the novel's bible. Each change is measured on the next run,
or dropped.

Depends on 11 (bounded reads: the pattern of line ranges in dispatches).

## Sources (read 2026-10-11)

- [Skill authoring best practices](https://platform.claude.com/docs/en/agents-and-tools/agent-skills/best-practices):
  the entry file is a table of contents under 500 lines; references one level deep (a nested one is
  often only partly read); a reference file over 100 lines opens with a contents list; one term per
  concept; no time-sensitive text; watch how agents actually navigate.
- [CLAUDE.md](https://code.claude.com/docs/en/memory): under 200 lines; `@path` imports load at
  launch, so they organise but do not save context; a procedure or a rule for one part of the tree
  belongs in a skill or a path-scoped `.claude/rules/` file.
- [Best practices](https://code.claude.com/docs/en/best-practices): for each line, "would removing
  this cause mistakes?"; no file-by-file description of the codebase.
- [Subagents](https://code.claude.com/docs/en/sub-agents): a subagent loads the CLAUDE.md hierarchy
  unless `omitClaudeMd: true` (every room agent sets it).

06d read the same guide on 2026-10-04 and set aside contents lists, because agents read whole files
with Read. That holds for the kb docs; it does not hold for a bible that grows with the book.

## P1 — built 2026-10-11 (the next run checks it)

- A `## Contents` list under the title of each kb doc over 100 lines (12 docs), each section with
  when to read it. `kb_check` warns on a long doc without one, or one that misses a `##` section.
- `mdio.headings`: headings with line ranges, skipping fenced blocks; `canon_fetch toc` uses it.
- `room.py`: the planner, writer, continuity editor and clerk dispatches carry a section map of each
  bible file over 8,000 characters with two or more `##` sections, and say to read a section or
  Grep a name, the whole file only when the task needs all of it.
- `CLAUDE.md` 9.6k → 7.0k characters: the tools' list moved to `docs/architecture.md`; each pointer
  says when to read its file; no `@` imports.

Checklist: [next-run-checklist.md](../next-run-checklist.md#best-practice-pass-2026-10-11).

## P2 — in the refactor (measure with the guard's `*.reads.tsv` before and after)

1. **One hop.** Fold each role's `index.md` table into its `prompt.md`, so the prompt is the table
   of contents and every doc sits one level below it. In run #9's log, `index.md` opened 13 times
   for 17 `prompt.md` opens. Expected gain: about one turn a spawn, the size 06d judged not worth
   inlining the always-read docs for, so do it when the refactor touches the prompts anyway.
   Touches `kb_check` (`RESERVED`, `check_indexes`), `tests/test_wiring.py`, `docs/architecture.md`.
2. **Flatten doc-to-doc links.** 12 docs link to other docs; `kb/planner/init.md` links 11. Route
   each through the role's table, or inline the one line needed. Links into `kb/shared/` stay.
3. **One term per concept.** A short glossary check in `kb_check` (e.g. *beat sheet* / *beats*,
   *hand-back* / *report*).
4. **The bible's §Places.** On ember-terraces, `world.md` §Places and distances is 28.5k of 35.7k:
   the folds file every new fact there. A rule in `kb/planner/fold.md` that places facts by kind
   (or a section per region), so the map has sections worth reading by.

## P3 — later, if a run shows the need

- Path-scoped `.claude/rules/` for the toolkit-maintenance rules (`paths: kb/**` for invented nouns,
  `paths: tools/**` for the Python rules), if CLAUDE.md grows back.
- The guide's "three evaluations per skill" is the bench's frozen rounds (`tools/bench.py`), and
  "test with each model" is plan 10: no new work.

## Session log

**2026-10-11.** P1 built; no agent spawned. 386 tests; `kb_check` clean on the repo and with
`--novel novels/ember-terraces`.
