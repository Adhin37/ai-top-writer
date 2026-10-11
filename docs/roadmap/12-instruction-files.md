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

1. **One hop — dropped 2026-10-11.** Folding each role's `index.md` into its `prompt.md` was built
   and reverted the same day: the index is the knowledge base's structure (OKF), and the user keeps
   it. A role reads its prompt, then its index, then the docs the index names; the extra Read is
   about one turn a spawn.
2. **Doc-to-doc links — done 2026-10-11.** Of the 26 links between kb docs, 24 point at a doc the
   role's own index lists: one level from the index, and the link says when to open it (init's
   round 3 → `cast-design.md`), so they stay. Two were one level too deep: the planner reached the
   canon researcher's `canon-format.md` only through `toggle-fanfic.md` (moved to `kb/shared/`, in
   both indexes), and the showrunner's `init.md` linked the planner's procedure it never runs (now
   a plain path). `kb_check` warns (`depth`) on a doc linking one its bundle's index does not list.
3. **One term per concept — done 2026-10-11, no check.** Counted the variants across `kb/`. One
   real clash: *the lead* is the protagonist in the ledger (`L1` the lead's lever, in the template,
   `scaffold.py` and `status.py`) and the love interest in `toggle-romance.md`; the toggle now says
   *love interest*. The index rows said *final line* where `wire.md` says *status line* (the one line
   that ends the *final message*): now *status line*. *Main session* only defines the showrunner;
   *beat sheet* is the term (*beat-sheet.md* is a file name). No glossary check in `kb_check`: a
   phrase list misfires on literal uses (the clerk's "the block's final line") and would be the
   pile of rules the toolkit avoids; the next count is a grep.
4. **The bible's §Places — done 2026-10-11.** On ember-terraces, `world.md` §Places and distances is
   28.5k of 35.7k: prices, rumours and dated events filed as bullets under one heading. The fold's
   `new` rule (`kb/planner/fold.md`) now places a place's facts under its own `### <place>` heading,
   and keeps dated events out of the bible (the timeline is the clerk's). The bible map lists a
   long section's `###` parts with their ranges (`§Places 38-371 28.5k (The quay 40-90, …)`).
   Existing novels keep their shape until a fold touches them; the next run checks that a fold adds
   headings and that agents Read a part by range.

## P3 — later, if a run shows the need

- Path-scoped `.claude/rules/` for the toolkit-maintenance rules (`paths: kb/**` for invented nouns,
  `paths: tools/**` for the Python rules), if CLAUDE.md grows back.
- The guide's "three evaluations per skill" is the bench's frozen rounds (`tools/bench.py`), and
  "test with each model" is plan 10: no new work.

## Session log

**2026-10-11.** P1 built; no agent spawned. 386 tests; `kb_check` clean on the repo and with
`--novel novels/ember-terraces`.

**2026-10-11, later.** P2.2–P2.4 built; no agent spawned. 388 tests; `kb_check` clean.
