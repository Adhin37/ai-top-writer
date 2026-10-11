# 2026-10-11: Haiku 5.5 again, after the prompt fixes

Plan [10](../roadmap/10-prompts-for-smaller-models.md), step 3. Run in session `5ea71f12` on
2026-10-11, after step 2's md fixes and backstop. The user chose to spend the retest (*"Run it
now"*). It follows the [first test](2026-10-11-haiku-5-5.md).

## Configuration

| parameter | value |
|---|---|
| clerk | ember-terraces ch 12 (round 1) and grown-houses ch 5 (round 2), each its novel's last accepted chapter; `bench.py freeze` copies `--h55r-{et12,gh5}-{son,hku}`, each with `work/chNNNN/ledger-before.md` saved by hand, since `room.py clerk` was not run on a copy |
| canon researcher | ember-terraces' init canon task on `--h55r-canonhku`, built as the first test built its copies (bible/canon.md and the fetch cache removed, `work/init/` cut back to round 1) |
| models | Sonnet 5.5 `high` from the agent file; Haiku 5.5 `high` by the Agent tool's `model: haiku`. `trace.py` reports both models on the clerk and `claude-haiku-5-5` on the canon researcher |
| verdict | the clerks' blocks and ledger lines against each other and against the run's own; the dossier against `bench/h55-canon/canonson.md` (the first test's Sonnet arm) |

One sample per arm.

**A flaw of the copies.** `bench.py freeze` copies `reading/<id>/` without the accepted round's
folder, so every clerk arm (Sonnet included) found no round notes to copy into the reader's memory.
Both Sonnet arms reported it, and so did the Haiku arm on grown-houses. It touches no file the
verdict reads. The frozen bible also holds the folds of the chapter being replayed (the caveat in
`bench.py`'s docstring), so the fold files cannot be compared fairly; see below.

## Cost and time (`trace.py --agents`)

| arm | responses | time | cost |
|---|---|---|---|
| clerk et ch 12, Sonnet / Haiku | 18 / 19 | 168 / 239 s | $0.66 / $0.23 |
| clerk gh ch 5, Sonnet / Haiku | 20 / 22 | 144 / 248 s | $0.56 / $0.13 |
| canon researcher, Haiku | 35 | 366 s | $0.24 (12 responses over 100k, $0.21 of it at the 5× tier) |

The Haiku canon spawn cost a third of the first test's ($0.77), with 0.17M cache writes against
0.59M and no compaction against two. That is plan 09's section reading at work: 7 `toc`, 15 `grep`,
22 Reads with an offset and 3 whole.

## The clerk: closer, still behind

| line | first test (Haiku) | retest (Haiku) | Sonnet replay |
|---|---|---|---|
| ledger statuses | F11 re-marked from a notes line | et: F13 R3 R8 R9 `landed ch12`, F11 untouched; gh: F12 F13 `landed ch5`. Same as Sonnet and the run | same |
| C1 step | "about eighty days", no day | "sixteen markets, about day 96 … the first gold, day 26" | "about day 96-101 … day 26" |
| L1 step | the cost dropped | "buys her mother off with her yes, ten days off" (the cost is there, but not "for Bai") | "it costs her a public yes …" |
| `ev` | (06c, Haiku 4.5: one sentence) | whole, action by action, in both rounds | whole |
| `at` | (06c: beat-sheet names) | only who is on the page; it noticed that the beat sheet's "Bet" and "Pip" are not in the text and left them out | Sonnet's gh `ev` names "Bet", from the beat sheet |
| `kno` | — | et 19 items, against Sonnet's 27 and the run's 28; one item marks Kesa's ignorance with `-` on a thing she was told she would not learn | fuller |
| `thr` | — | gh: no `^T17`, which the run has (the notes said the page does not advance it; Sonnet and the run disagree) | `^T17` |
| fold | — | et: `none` ("every new fact I checked is already in the bible"); gh: 3 lines | et 7, gh 9 lines |
| status line | notes under it | gh: a paragraph under it again | et clean; gh a warning appended to the line |

The fold count is unfair to both arms: the frozen bible already holds the run's ch 12 and ch 5
folds, so Haiku was right that the facts file's lines were in it. Sonnet's extra lines are the
second half of step 8 (*"Then add what else the chapter states as true"*), which Haiku skipped in
both rounds.

The new `state_check` warn (`check_ledger_moves`) found nothing on any arm: no arm changed a row
landed before its chapter.

**Verdict: the clerk stays on Sonnet.** The bar was every block and ledger line in both rounds. The
ledger now matches, and every miss the fixes aimed at is gone. What remains is thinner `kno`, a
missed thread, a fold that never looks past the facts file, and text under the status line. These
are depth and obedience, not an ambiguous rule. A Haiku clerk would save about $0.40 a chapter.

## The canon researcher: fixed where it failed, thinner everywhere else

| check | canonson (Sonnet, first test) | first test (Haiku) | retest (Haiku) |
|---|---|---|---|
| Zuko / Iroh / Ozai at the start | 15 or 16 / about 54 / about 44 | the same | the same |
| Zhao at the start | Unsure (still "Captain" in ep 3) | **"newly commander at the start"** | post and rank before the winter find "not sourced"; asked under Unsure |
| transcripts cited | 13 | 0 | 3 (The Boy in the Iceberg, The Southern Air Temple, The Deserter), found with `grep`, none Read whole |
| facts / sources / unsure | 43 / 37 / 11 | 47 / 27 / 13 | 36 / 20 / 8 |
| the full-moon rule | — | under Unsure | gone: "weaker at night, powerless in an eclipse", cited to the Firebending page and "The Boy in the Iceberg" |
| `## Fans expect` | two searches, nothing found, said so; one fanon line | — | built from the wiki only; "Fanon: not searched in this pass", and it asks the user whether to search |
| non-show material | — | — | named and left out (Yu Dao, the Harmony Restoration Movement), per the scope |

**Verdict: the canon researcher stays on Sonnet.** Both of the first test's misses are fixed:
`sources.md` now names transcripts, and `canon-format.md` works out ranks at the start. But the bar
was ages, statuses *and sources*. Haiku cites about half Sonnet's sources and a quarter of its
transcripts, and it skipped the fan-discussion search its prompt asks for. The role runs once per
fan-fiction novel. Saving $1–3 once is not worth a thinner foundation for every chapter.

## What changed for every model

The step 2 fixes stay. They replace lines Sonnet had been reading past (the "from its grade" rule,
the one-clause `ev`, "the work itself" without transcripts, ages without ranks), so the next full
run on Sonnet checks them (`docs/next-run-checklist.md`, plan 10).

`canonson.md` is kept: it is still the baseline for plan 09's live check, which has not run.
