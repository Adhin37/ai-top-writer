# 09 — Session 10: the canon researcher reads sections, not pages

**Goal:** cut what a canon researcher spawn costs without losing what the dossier holds. The lever
is how it reads, not which model it runs on, so it holds for Sonnet today and for any model the role
moves to later.

Depends on 08 (run #9's novel, ember-terraces, and its saved canon pages).

## Evidence

A replay of ember-terraces' canon init on 2026-10-11, part of the Haiku 5.5 test (aside below).
From `python3 tools/trace.py b4e04d3f-1c4d-41d9-9e44-a4544b7a038e`:

| role | spawns | cache writes | compactions | cost a spawn |
|---|---|---|---|---|
| canon researcher (Sonnet `high`) | 1 | ~1.28M across both arms | 5 | ~$1.7 |
| clerk (Sonnet `high`), for scale | 2 | ~0.57M across four | 0 | ~$0.4 |

The cause: the role saves wiki pages with `canon_fetch.py page … --out work/canon/src/<wiki>/` and
then reads each one **whole**. A character or history page is about 80k characters, roughly 20k
tokens. Ember-terraces' `src/` holds 1.8 MB. The dossier needs a few lines from most of them.
Every whole page stays in context until the context compacts, and each compaction rewrites the
cache. So the cost is in the cache-write column, not the output.

## Step 1 — the tool: find before reading

`tools/canon_fetch.py`, standard library only:

- `grep <dir> <words…> [--context N]` prints each matching paragraph with its file, line number
  and nearest `##` heading. Output is capped, with a count of the hits past the cap, so a broad
  word cannot flood the context.
- `toc <file>` prints a saved page's headings with their line numbers, so the role can Read one
  section by offset and limit.

Both reuse the heading format `render()` writes. Tests go in `tests/test_canon_fetch.py`, on a
fixture page. `tools/guard.py` already lets the role run `python3 tools/…`: confirm it, change
nothing there.

## Step 2 — the procedure: one rule replacing one

In `kb/canon-researcher/sources.md` § Fetching, the step after `page … --out` becomes: *find with
`grep` or `toc`, then Read only that section (offset, limit). Read a page whole only for a
transcript the dossier quotes line by line.* Point `prompt.md` init step 3 at it. This replaces
the current fetch step; it is not a new rule appended. Then run `python3 tools/kb_check.py`
(clean) and `python3 -m unittest discover tests`.

## Step 3 — checked live, not replayed

Per the standing decision (*test by parts*): no paid replay in this plan. The next fan-fiction
init, or the next `gap canon` lookup, checks the change. Add it to
[next-run-checklist.md](../next-run-checklist.md):

- `trace.py` for `canon-researcher`: cache writes and compactions, against the baseline above;
- the dossier against `novels/ember-terraces--h55-canonson/bible/canon.md` (this test's Sonnet
  replay; keep that copy until the check has run): the same ages and statuses at the start, and
  every path under `## Sources` exists.

The change is kept if the dossier holds and the cost falls. If facts go missing, the rule is
too tight: loosen what counts as a whole-page read. Do not revert the tool.

## Aside — the Haiku 5.5 test, closed in the same session (no spawn)

Haiku 5.5 is `claude-haiku-5-5`, released 2026-10-07: $0.10/$0.50 per million tokens up to 100k
input, and 5× that above. On 2026-10-11 it was replayed against Sonnet on two roles. Close it here:

- **Clerk: lost**, the same failure as Haiku 4.5 in 06c. Ch 9 was at par. In ch 12 it re-marked
  past row F11 from `landed ch6` to `partly ch6`, gave the C1 step no day number and dropped
  "pays for Bai" from L1. `state_check` was clean on both.
- **Canon researcher:** compare `novels/ember-terraces--h55-canonhku/bible/canon.md` with the
  Sonnet replay and with the original. Check the ages and statuses at the start (Zuko 15–16, Iroh
  about 54, Zhao's rank), that every source path exists, whether transcripts were read (by its own
  hand-back, it read only wiki summaries), and any rule stated without a source (it offered
  "firebending is weak at night and at the full moon").
- Add `claude-haiku-5-5` to `RATES` in `tools/trace.py` (0.10 / 0.50 / 0.01), and a warn when a
  response's input passes 100k, where the 5× tier applies.
- Write `docs/experiments/2026-10-11-haiku-5-5.md`. Update the *Features* row for role cost levers.
- Quote the evidence 10 needs into the write-up (the ch 12 ledger diff and its notes line for F11,
  the ch 9 hand-back on later rows, the Haiku dossier's misses) before removing anything.
- Remove the other five `h55` copies and their `reading/` folders (`tools/clean.py`), keep
  `canonson` for step 3, and delete `.test-run`.

## Session log

(empty: fill in when the plan runs)
