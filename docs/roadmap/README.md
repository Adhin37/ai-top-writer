# Roadmap

The rebuild of [skilled-writer](../../../skilled-writer) as a writers' room. Each plan below is one
working session. They are ordered by what has to be true before the next one is worth doing.

**To run a plan:** open a Claude Code session **in this repository**. Agents register when a
session starts, so a session opened anywhere else cannot spawn them. Then say *"execute
docs/roadmap/NN"*. When the session ends, fill in the plan's *Session log*, update the status
column below, and fix any later plan the session proved wrong. Plans are proposals, not contracts.

| # | plan | status | depends on |
|---|---|---|---|
| 00 | [Diagnosis: why the rebuild](00-diagnosis.md) | reference | — |
| — | Session 1: foundation (this repo, the docs, the roadmap, the spike's agents and tools) | **done** 2026-09-26 | — |
| 01 | [Session 2: vertical slice, chapter 1 A/B/C](01-vertical-slice.md) | next | session 1 |
| 02 | [Session 3: the full loop and serial memory](02-full-loop.md) | planned | 01 = GO |
| 03 | [Session 4: the knowledge bases](03-knowledge-bases.md) | planned | 02 |
| 04 | [Session 5: novel setup and planning from scratch](04-front-end.md) | planned | 03 |
| 05 | [Session 6: benchmark run #7](05-benchmark-run-7.md) | planned | 04 |
| 06 | [Session 7: measurement, then optimisation](06-measure-and-optimise.md) | planned | 05 |
| 07 | [Session 8: retire skilled-writer](07-retire-skilled-writer.md) | planned | 05 |

## Why this order

1. **01 tests the hypothesis before anything is built on it.** The hypothesis is that a lean writer
   plus an in-loop cold reader plus a reader ledger produces a chapter 1 a newcomer understands and
   wants to continue. It is tested on the same bible that produced run #6's confusing chapter 1. If
   the answer is no, nothing after it is worth doing as planned.
2. **02 finishes the loop across chapters.** One chapter cannot test serial memory, the state write
   or continuity.
3. **03 writes the knowledge bases** once the loop has shown what each role needs. Writing them
   first would repeat the old mistake: rules written for a pipeline nobody had run.
4. **04 is the front end.** Setting up a new novel needs the knowledge bases, and the benchmark needs
   a new novel.
5. **05 is the first comparable measurement** against run #6.
6. **06 optimises cost only after quality is established.** The user's instruction: quality first,
   tokens later.
7. **07 retires the old repo** only after the new one has shipped a benchmark.

## Standing decisions (from the user, 2026-09-26)

- **Fresh repo.** Port only what is proven useful. The old repo is an archive, not a dependency.
- **Chapter 1 is webnovel-clear.** By its end a reader can state the world's central rule, the MC's
  situation and the stakes in plain words. An explanatory passage is allowed.
- **Quality first.** **Opus for the hard roles** (planner, writer, story editor, judge),
  **Sonnet for the rest.** No design constraint exists for the sake of a smaller model.
- **Multiple agents in feedback loops**, not a single drafter plus a gate.
- **Per-role knowledge bases in OKF format** replace the old cards, routing and search.
- **Fewer limitations than the old repo.** Carry over a rule only when its evidence still applies.
  [lessons.md](../lessons.md) says which ones do.

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
