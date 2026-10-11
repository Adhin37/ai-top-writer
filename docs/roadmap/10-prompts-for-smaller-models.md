# 10 — Session 11: prompts a smaller model can follow, then Haiku 5.5 again

**Goal:** find out whether Haiku 5.5 lost on 2026-10-11 because the roles' `kb/` files lean on
Sonnet's judgement, fix those files, and test it again fairly. At about a twentieth of Sonnet's price,
a role Haiku can do as well is worth a short pass on its md files.

Depends on 09. Its section reading keeps a Haiku canon researcher under the 100k-input tier, where
the price goes up 5×, and away from the compactions that test its long-context weak spot. Its aside
writes up the first Haiku test (`docs/experiments/2026-10-11-haiku-5-5.md`), which this plan starts
from. 09 spawns nothing; this plan spends a small replay budget.

**One prompt per role, for every model.** No per-model files. A fix aimed at Haiku has to leave
Sonnet as good: it replaces a rule or adds an example, never piles on a new rule.

## Evidence: was it the prompts, or the chapters already written?

- **The prompts, at least once.** Ch 12's notes file graded `F11 partly "Kesa's fire is at its worst
  at noon" — … not owed here`. `kb/clerk/prompt.md` step 7 says *"set the status of each fact and
  face row the notes file grades, from its grade"*. Haiku did exactly that and lowered a row that
  had landed in ch 6. Sonnet read past the letter and kept it. The rule is ambiguous, and Sonnet's
  judgement hid that. In the same way, the Haiku canon researcher read wiki summaries, not
  transcripts. `kb/canon-researcher/sources.md` ranks "the work itself" first but never says what
  that is for a TV series.
- **The chapters already written, partly.** `bench.py freeze` cuts rows opened from chapter N on.
  It does not cut a thread's `last` raised by a later chapter, or the bible's later folds. Haiku's
  ch 9 hand-back flagged exactly that. Both arms read the same copy, but a smaller model may be
  thrown more by it. Ch 12 is the novel's last chapter, so its miss owes nothing to this.

## Step 1 — diagnose each miss (no spawn)

For every Haiku miss on record, name the line of `kb/` it followed, or the gap it fell into:

- 06c's Haiku 4.5 clerk ([write-up](../experiments/2026-10-04-optimisation.md)): a ledger row
  misdated from `landed ch4` to `landed ch5`; names that appear only in the beat sheet put into
  `at`; a one-sentence `ev`;
- 2026-10-11's Haiku 5.5 clerk: F11 lowered; the C1 step without its day; the L1 step dropping
  "pays for Bai"; extra text under the status line;
- 2026-10-11's Haiku 5.5 canon researcher: wiki summaries read instead of transcripts; the rule
  "firebending is weak at night and at the full moon", which has no source.

Put the table in the session log. A miss with no `kb/` cause is the model's own; record it, and
fix nothing for it.

## Step 2 — fix the md files, and a backstop that needs no model

- `kb/clerk/prompt.md` step 7, replacing its first sentence: a grade moves a row only where this
  chapter owes it or pays it. A row `landed` in an earlier chapter stays landed, whatever a later
  retell shows. `at` names only who is on the page. A Pressure step keeps its day or count as the
  page states it.
- `kb/clerk/short-blocks.md`: one example, with invented nouns, of a full `ev`: the chapter's
  actions, not a summary of them.
- `kb/canon-researcher/sources.md` § What outranks what: "the work itself" names its forms (the
  text; for a show, its transcripts; a summary that cites its chapter or episode). A rule found only
  on a wiki is written as "wiki".
- **Backstop:** `tools/room.py`'s clerk step saves `work/chNNNN/ledger-before.md`, and
  `tools/state_check.py` warns on any row whose earlier-chapter status changed. It reports and
  never gates. This catches the F11 kind of miss whatever model the clerk runs on. Tests go in
  `tests/`.
- `tools/bench.py freeze`: document that model arms prefer rounds with no later chapter.
- Run `python3 tools/kb_check.py` and `python3 -m unittest discover tests`.

## Step 3 — the retest (paid, small)

A model change cannot ride on a normal run without risking the book, so this plan has the one
replay budget, as 06c did. It uses rounds with nothing written after them: ember-terraces ch 12 and
grown-houses ch 5 (06c's Haiku 4.5 round). `touch .test-run` first.

| arm | rounds | spawns | budget |
|---|---|---|---|
| clerk, Sonnet `high`, new prompt (the regression guard) | et ch 12, gh ch 5 | 2 | ~$0.8 |
| clerk, Haiku 5.5 `high` (`model` override), new prompt | et ch 12, gh ch 5 | 2 | ~$0.1 |
| canon researcher, Haiku 5.5 `high`, 09's procedure | ember-terraces init | 1 | ~$0.3 |

- Compare the clerks line by line with the run's own block and ledger, and read the new warn.
- Compare the canon dossier with 09's live-check Sonnet dossier and with
  `bench/h55-canon/canonson.md`: ages and statuses at the start, sources
  that exist, transcripts read, no rule without a source.
- Confirm from the transcripts that each arm ran on `claude-haiku-5-5`, and take the cost from
  `tools/trace.py`.

## Step 4 — decide and record

A role moves to Haiku only if it matches Sonnet on every block and ledger line in both rounds (the
clerk) or on ages, statuses and sources (the canon researcher).

- **If it does:** change its agent file's `model`; add a Haiku line to the standing decision in
  `README.md` and to principle 7 in `CLAUDE.md`; teach `kb_check` Haiku's effort levels. The next
  full run checks the change.
- **If not:** the write-up names what still fails. The prompt fixes stay, since they help Sonnet too.

Write `docs/experiments/<date>-haiku-5-5-retest.md` and update the *Features* table. Then delete
the copies, `canonson` included, and `.test-run`.

## Session log

### 2026-10-11 — steps 1 and 2 (no spawn)

**Step 1, each miss against the line it followed:**

| miss | model | the `kb/` line, or the gap | cause | fix |
|---|---|---|---|---|
| F11 `landed ch6` → `partly ch6` | Haiku 5.5 | clerk step 7, *"set the status … from its grade"*, and state-format's grade table (partly → `partly chN`), with no word on a row already landed | kb | step 7's first sentence replaced: a grade sets a row only where this chapter owes or pays it; an earlier `landed` stays |
| `landed ch4` → `landed ch5` | Haiku 4.5 | the same: ch 5's notes graded the row *stated* again, and the table says stated → `landed chN` | kb | the same |
| beat-sheet names in `at` | Haiku 4.5 | step 1 has the clerk read the beat sheet and never says it is the plan, not the page; `at` said "each person on the page" | kb, weak | step 3: the block holds the page, the beat sheet only the plan; the `at` row: nobody only in the beat sheet |
| one-sentence `ev` | Haiku 4.5 | state-format's `ev`: *"the event as it played on the page, one clause"*, with a one-clause example; short-blocks.md says *short* throughout. Sonnet ignored the letter | kb | `ev` row replaced ("action by action, a clause each") and its example made whole; short-blocks.md gets *Short is for `kno`, not for `ev`* |
| C1 step without its day | Haiku 5.5 | the trail format, *"<what the page did, one clause>"*, says nothing of numbers | kb, gap | the trail sentence: the clause keeps the day, count or price, and a lever's cost, with an example |
| L1 step dropped "pays for Bai" | Haiku 5.5 | the same gap | kb, gap | the same |
| notes under the status line | Haiku 5.5 | the prompt says *"Exactly one line, nothing before or after it"* | model's own | none |
| no transcript read | Haiku 5.5 | sources.md ranks "the work itself" first as *"a chapter the user saved … or a chapter summary"*: nothing for a show | kb | rank 1 names the forms: a book's text, a show's transcripts (`Transcript:<episode>`), a summary that cites its episode; an uncited summary is the wiki's |
| Zhao "newly commander at the start" | Haiku 5.5 | canon-format works out **ages** at `start` from the timeline, not ranks; the wiki's infobox gives the latest rank | kb, gap | the rule now covers ages and ranks, with a rank example |
| the full-moon rule | Haiku 5.5 | — | not a miss | Haiku put it under `## Unsure`, which is right for a wiki-only rule; the plan's "write it as wiki" is dropped, since nothing failed |

**Step 2, built:**

- `kb/clerk/prompt.md` steps 3 and 7; `kb/shared/state-format.md` (`ev`, `at`, the Pressure
  clause); `kb/clerk/short-blocks.md` (a whole `ev`, invented nouns); `kb/canon-researcher/
  sources.md` rank 1; `kb/canon-researcher/canon-format.md` ages and ranks. Every change replaces
  a line or adds an example; no rule added to a pile.
- Backstop: `room.py clerk` saves `work/chNNNN/ledger-before.md` once, before the clerk;
  `state_check.py` warns when a row `landed` before the chapter changed, or a Pressure step for an
  earlier chapter changed (`check_ledger_moves`). `Novel.ledger` and `Novel.pressure` take a saved
  text. Tests: `test_clerk_saves_the_ledger_once_before_the_clerk`,
  `test_a_row_landed_earlier_stays_as_the_clerk_found_it`.
- `bench.py`'s docstring: a model arm prefers a round with no later chapter.
- `kb_check` clean; 371 tests pass.

### 2026-10-11 — steps 3 and 4

The user chose to run the retest ("Run it now"). Five spawns, $1.82 by `trace.py`: Sonnet clerks
$0.66 + $0.56, Haiku clerks $0.23 + $0.13, the Haiku canon researcher $0.24. Every arm's model was
confirmed in its transcript. Write-up: [2026-10-11-haiku-5-5-retest](../experiments/2026-10-11-haiku-5-5-retest.md).

- **Clerk: stays on Sonnet.** The ledger matched in both rounds, with F11 untouched and C1 keeping
  its day. `ev` and `at` were fixed. Still behind: `kno` (19 items against 27), a missed `^T17`, a
  fold that never looks past the facts file, and text under the status line.
- **Canon researcher: stays on Sonnet.** It now cites transcripts (3) and leaves Zhao's rank at the
  start unsure, not wrong, but it has about half of Sonnet's sources and skipped the fan search.
- No agent file, `README.md` decision, `CLAUDE.md` principle or `kb_check` level changed.
- The fixes stay, for every model. The next run checks them on Sonnet (`docs/next-run-checklist.md`,
  plan 10).
- Found on the way: `bench.py freeze` leaves out the accepted round's reading folder, so a frozen
  clerk cannot update the reader's memory. That is harmless to a verdict on state; noted in the
  write-up, not fixed.
- Deleted: the five `--h55r-` copies, their reading folders, `bench/h55r/` and `.test-run`.
  `bench/h55-canon/canonson.md` is kept until plan 09's live check runs.
- Found while cleaning up: a copy made with `cp -r` keeps its source's `slug`, so `clean.py` gave it
  the source's reading folder, and `--delete` on such a copy would have removed the real novel's
  reading. `owned()` now skips a copy's id when it equals its source's
  (`test_a_copy_that_kept_its_sources_slug_never_owns_the_sources_reading`); 372 tests pass.
