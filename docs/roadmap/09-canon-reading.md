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
| canon researcher (Sonnet `high`) | 1 | 0.69M | 3 | $3.45 |
| clerk (Sonnet `high`), for scale | 2 | 0.13–0.14M each | 0 | $0.72–0.91 |

(Corrected at the write-up: the first figures averaged both arms with Haiku priced at $0.)

The cause: the role saves wiki pages with `canon_fetch.py page … --out work/canon/src/<wiki>/` and
then reads each one **whole**. A character or history page is about 80k characters, roughly 20k
tokens. Ember-terraces' `src/` holds 1.8 MB. The dossier needs a few lines from most of them.
Every whole page stays in context until the context compacts, and each compaction rewrites the
cache. So the cost is in the cache-write column, not the output.

## Step 1 — the tool: find before reading

**What a saved page already is.** `canon_fetch.py page` pulls the rendered page through the wiki's
API. Its `Page` parser drops scripts, styles, navboxes, references, galleries and edit links, and
keeps every heading as `##`/`###`. Pages are clean markdown: stripping more HTML saves nothing.
Measured on ember-terraces' 50 saved pages (1.84 MB):

- **Transcripts are 56% of the bytes, and have no headings** (`Transcript_The_Storm.md`: 33k
  characters, one heading). Today they can only be read whole.
- **Articles have headings** (`Zuko.md`: 46, from `## History` → `### Winter 99 AG` to `## Trivia`),
  so they can already be navigated. Nothing in the procedure says to.
- **Sections that never carry canon are 7%** (Trivia, Production notes, Appearances, Quick Answers,
  Cast). Too little to strip; `toc` lets the role skip them.

So the saving comes from navigation, not stripping. In `tools/canon_fetch.py`, standard library
only:

- **Scene headings for transcripts.** When `render()` writes a page in a transcript category, it
  starts a `## Scene N — <speakers>` heading at each scene change ("Cut to…", "The scene cuts/
  changes/shifts…"; 21 in *The Storm*). The speakers are the `Name |` lines in that scene. A
  transcript then reads like an article: the role can open the scenes where its cast speaks.
- **`toc <file>`** prints each heading with its line range and its size in characters, so the role
  can Read one section by offset and limit, and see a large out-of-scope section (a later era, a
  sequel series) before opening it.
- **`grep <dir> <words…> [--context N]`** prints each matching paragraph with its file, line number
  and nearest heading. Output is capped, with a count of the hits past the cap, so a broad word
  cannot flood the context.
- **`restyle <dir>`** adds the scene headings to transcripts already saved, by the same function
  working on the markdown, so ember-terraces' cache needs no re-fetch.

Tests go in `tests/test_canon_fetch.py`: a fixture article, and a fixture transcript with two scene
cuts. `tools/guard.py` already lets the role run `python3 tools/…`: confirm it, change nothing
there.

## Step 2 — the procedure: one rule replacing one

In `kb/canon-researcher/sources.md` § Fetching, the step after `page … --out` becomes: *find with
`grep` or `toc`, then Read only that section or scene (offset, limit). Read a page whole only when
`toc` shows no heading that fits.* Point `prompt.md` init step 3 at it. This replaces
the current fetch step; it is not a new rule appended. Then run `python3 tools/kb_check.py`
(clean) and `python3 -m unittest discover tests`.

## Step 3 — checked live, not replayed

Per the standing decision (*test by parts*): no paid replay in this plan. The next fan-fiction
init, or the next `gap canon` lookup, checks the change. Add it to
[next-run-checklist.md](../next-run-checklist.md):

- `trace.py` for `canon-researcher`: cache writes and compactions, against the baseline above;
- the dossier against `bench/h55-canon/canonson.md` (this test's Sonnet replay, rebuilt from its
  transcript; keep it until the check has run): the same ages and statuses at the start, and
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

2026-10-11, one session, no spawn.

- **Found at the start:** the six `h55` copies were already deleted (10:08, before this plan was
  written), with both dossiers. Rebuilt both from the canon arms' Write and Edit calls (every Edit
  applied) into `bench/h55-canon/`, with a `key.md`; quoted the clerks' ledger edits from their
  transcripts. The four `reading/` folders left without a novel were the clerk copies' (their
  `novel_id`s match exactly): removed. The canon copies had none.
- **Step 1, built.** `canon_fetch.py`: `toc`, `grep`, `restyle`, and scene headings in `render()`.
  On the 31 saved transcripts the wording varies by writer (*The Beach* never says "scene"), so a
  scene starts at an explicit mark (scene changes/cuts/shifts…, fades, a flashback) and, once a
  scene has run 3,000 characters, at the next "Cut to". 497 scenes: median 1.6k characters, 90%
  under 4.1k, the largest 10k (no cut to break at). A transcript is a page whose title starts
  `Transcript:` or whose category ends in "transcripts" (Zuko's article says "transcription").
  `grep` is AND over the words, cut to 400 characters around the match, 40 hits by default.
  Guard: confirmed, unchanged (the role's Bash takes any arguments to `canon_fetch.py` that hold no
  quotes or shell syntax). 8 tests added.
- **Step 2, built.** `sources.md` § Fetching: the "read it there" bullet replaced by *find, then read
  the part*; `toc` and `grep` in its command block; `prompt.md` init step 3 points at it.
  `kb_check` clean; 369 tests pass.
- **Step 3:** the checklist entry is in [next-run-checklist.md](../next-run-checklist.md) § Plan 09.
  ember-terraces' cache restyled (31 transcripts), so its next `gap canon` lookup reads scenes.
- **Aside, closed.** [Write-up](../experiments/2026-10-11-haiku-5-5.md): clerk lost, canon researcher
  lost (no transcript read, Zhao "newly commander at the start"). `trace.py` prices
  `claude-haiku-5-5` with its 5× tier above 100k input and warns per role (the session now traces
  at $9.39 against Claude Code's $9.40). `.test-run` deleted.
