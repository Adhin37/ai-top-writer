# 11 — Session 12: bounded reads, no context that grows with the book

**Goal:** after 09 fixed the canon researcher's whole-page reads, find every other place where a
role, or the showrunner, loads something whose size grows with the book, and bound it the same way:
a line range instead of a file, a capped list with a count of the rest, a summary line per file.
Each fix is a tool cap, or a rule that replaces the read it bounds.

Depends on 09 (the pattern), 10 (done).

## Evidence

The usual advice on long contexts agrees with 09:

- quality falls as the context fills, before the limit (Chroma's *context rot*);
- every kept token is re-read on each later turn, and a compaction rewrites the cache;
- so load by path and range when it is needed, cap tool output with a count past the cap, and keep
  large files on disk.

Run #9's trace (`trace.py f5286e1a-99b7-4ef6-a834-8004a2e0c0d9 --since 2026-10-10T13:48:36Z
--agents`, ember-terraces ch 6–12):

- **No subagent compacted.** The showrunner did, 3 times at 217k (mean context 129k, peak 216k).
  Its 209 hand-backs, ~128k tokens, were 59% of its cache reads; it was the dearest role at $19.60.
- Reads that grow with the book, measured on ember-terraces at ch 12:

| what | who | size at ch 12 | growth |
|---|---|---|---|
| `state/continuity.md`, read whole for its last block | clerk, planner, story editor (59 opens in the guard logs) | 46 KB | ~5 KB a chapter |
| `history-rK.txt` | story editor, line editor, every round | 8.2 KB (1.9 KB at ch 3) | linear: 46 warn motifs listed, every chapter named per line |
| the every-10th fresh re-read | beta reader | 271 KB at ch 10 | ~135 KB more every 10 chapters |
| `beats.md`, read to approve | showrunner, every chapter | 10–17 KB | per chapter, kept in its context |
| `canon_fetch.py toc src/*.md` | canon researcher | 68 KB | with the cache |
| the handoff's user messages | a resumed session | uncapped count | with the session |

## Step 1 — the showrunner

1. **The reader's report stays a hand-back.** The first idea was for the beta reader to write
   `report.md` itself and end on a status line. Claude Code refuses a subagent's write to a report
   file, and 01 decided not to rename the file to get past that (`tools/handback.py`'s docstring).
   So reports still land in the showrunner's context (~2.5k tokens a round).
2. **`room.py approve NOVEL N`**, after PLANNER DONE beats. It prints:
   - the plan row's event;
   - the ledger rows due this chapter, and any the sheet's header does not name;
   - L1/C1 rows the `pressure` line does not step;
   - the header's line range, which the showrunner reads in place of the whole sheet.

   `loop.md` step 1 now says to do this. The `beats`, `judge` and `where` texts point at it.
3. **`room.py`'s own lists stop at 8 lines** (`shown()`), with `+n more: <command>`:
   - state_check findings;
   - continuity defects;
   - overdue ledger rows.

   History failures are cut to 300 characters, as lint's already were. The `gap canon` lines stay
   whole: they are a dispatch, sent verbatim.
4. `autoCompactWindow` stays at 250k. The next trace says whether 1.2–1.3 moved it.

## Step 2 — `state/continuity.md` by range

`room.py block_lines()` names a block as `<novel>/state/continuity.md lines A-B`. It uses
`Block.last_line`, added to `lib/novel.py`. Each dispatch that needs the block carries it:

- the planner's beats (fresh, warm and ahead);
- the fresh story editor;
- the clerk;
- the planner's fold, which gets the folded chapter's own block.

Five lines in the planner, fold, story-editor and clerk prompts now name that range in place of the
file. The clerk's "every file in `state/`" became the files it names, and only the last block of
`continuity.md`.

## Step 3 — `history.py`

- A warn motif that the newest chapter does not use is counted, not listed: `+n more at the warn
  level, none in ch N`. The editors of chapter N can cut only from chapter N.
- `where()` keeps the first 2 and the last 3 chapters past 6.
- `--out` writes the report to the file only and prints one line.
- The line editor's prompt says that a refrain counted that way is not its to cut.

## Step 4 — the fresh re-read's budget

`reading.FRESH_BUDGET` is 400,000 bytes, about 100k tokens. Past it, `fresh_keep` keeps chapters 1–3
and as many of the latest as fit, always including the last. The dispatch names the skipped stretch
(`reading.skipped`), and the reader marks it as skipped in its notes. A skipped chapter the shelf
lacks is exported to the shelf, so a rebuilt shelf stays whole. Ch 1–10 (271 KB) are under the
budget, so nothing changes before about ch 15.

## Step 5 — `canon_fetch.py`

- `toc` with several files prints one line a file (size, heading count); `--full` gives every file's
  headings.
- `grep` holds at `--context 3` and `--max 100`.
- `category` defaults to 100 pages, and says when it stopped at the limit.
- The canon researcher goes through its inbox files the same way as fetched pages (*find, then read
  the part*).

## Step 6 — the handoff

`checkpoint.py` keeps the first 2 and the last 8 user messages, and counts the ones it leaves out.
The spawn prompts of agents in flight stay verbatim, because a fresh session re-spawns from them.
`status.py --debt` stays uncapped, because the planner must see every overdue row.

## Watch list

Revisit any of these when it doubles, with the same pattern (range or find-then-read):

| file | size at ch 12 |
|---|---|
| `state/threads.md` | 14.6 KB |
| `state/scenes.md` | 7.5 KB |
| `bible/world.md` | 30 KB |
| a cast file | 16 KB |
| `state_check --last 5` output, read by the continuity editor | 22 KB |
| `plan/chapters.md` | 11 KB |

The planner's ledger task reads every block's `ev` lines, but only once, to add `L1`/`C1` to a
ledger that has none. It is not bounded.

## Checked live, not replayed

Per the standing decision (*test by parts*), no paid replay: the next run's `trace.py` checks it
([next-run-checklist.md](../next-run-checklist.md) § Plan 11).

## Session log

2026-10-11, one session, no spawn.

- Web search (context rot, Claude Code context tax, Anthropic's context engineering), then two
  read-only audits, then run #9's trace. Plan written, then built.
- **Step 1:**
  - 1.1 dropped, for the reason above.
  - 1.2 built. On ember-terraces ch 12, `approve` prints 575 bytes, and the header it points at is
    2.7–5.9 KB on ch 6–12, against 10–17 KB for the whole sheet.
  - 1.3 built.
- **Step 2, built.** Ch 12's block is lines 104–111 of 111 (5.5 KB of 46 KB). Checked in the
  scratchpad: Edit accepts a file Read only by offset and limit, so the clerk appends after the
  last block's final line without reading the file whole. If that line is not unique in the file,
  the Edit fails and the clerk has to give it more context.
- **Step 3, built.** The ch 12 report on the same input: 7.5 KB → 5.5 KB, with 41 → 19 warn motifs
  listed and 22 counted.
- **Step 4, built.**
- **Step 5, built.** `toc` over the 50 cached pages: 68 KB → 6.1 KB.
- **Step 6, built.**
- 372 → 383 tests, all pass; `kb_check` clean.

2026-10-11, the live check: run #10 on ember-terraces ch 13–14 ([write-up](../experiments/2026-10-11-run-10.md#write-up)).

- Every planned read bounded: the showrunner approved from the header (limit 19 and 45); 7 of 7
  reads of `continuity.md` by range; the clerk's blocks appended in place, `state_check` clean.
- No showrunner compaction in two chapters; hand-backs 9% of its cache reads (59% in run #9).
- The history report fell to 5.3 KB at ch 14, and the line editor still cut from it.
- Per-spawn cost of the clerk, planner and story editor did not fall: what else they read grew
  more than the range saved. $1.75 per 1,000 words (run #9 $1.86 without judges).
- The fresh read's budget is unchecked until ch 20.

