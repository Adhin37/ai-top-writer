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

(empty: fill in when the plan runs)
