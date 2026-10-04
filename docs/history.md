# History: the benchmark runs

Seven end-to-end runs, from skilled-writer's first (2026-09-05) to this room's first
(2026-10-03). Runs #1–#6 are condensed from skilled-writer's `docs/benchmark.md`. Each run's full
write-up is in [that repo's git history](https://github.com/Adhin37/skilled-writer/commits/main/docs/benchmark.md):
run #1 at `a3b11b0`, #2 at `eab5514`, #3 and #4 at `55eb4a6`, #5 at `cdf7761`, #6 at `ef9d86e`.
Run #7's write-up is [here](experiments/2026-10-03-run-7.md). The lessons that still hold are in
[lessons.md](lessons.md); this page is what happened.

## The runs

| run | date | novel | harness | chapters · words | cost · per 1,000 words | verdict |
|---|---|---|---|---|---|---|
| 1 | 09-05 | fanfic, reincarnator | one Sonnet 5 subagent | 5 · 8,140 | $28.39 · ~$1.17 steady state | 16 of 37 skills loaded; 3 high-severity defects |
| 2 | 09-09 | fanfic, transmigrator | one Sonnet 5 subagent, plus a revision agent | 5 · 6,804 | $22.81 · $3.35 | every check clean; a human reader found stiff dialogue and characters never introduced |
| 3 | 09-09 → 12 | fanfic, reincarnator | one subagent; a coordinator-directed redraft of all five | 5 · 4,695 | not recorded | no write-up; reconstructed from what the redraft fixed |
| 4 | 09-12 | fanfic, corrupted foreknowledge | one warm subagent, then one cold chapter | 5 warm · 5,904, and a cold 6th | $31.58 · $5.35 for the five | 0 defects; the warm agent opened 5 cards in five chapters |
| 5 | 09-13 → 19 | original fantasy, *The Grain Beneath the Lie* | one warm subagent behind a compressing proxy | 3 measured · 4,554 | $22.85 · $5.02 | cold read 3 / 5 against 0 defects |
| 6 | 09-25 → 26 | original fantasy, *The Unwritten Surveyor* | role pipeline: architect, cold drafter, gate | 5 · 8,572 | $40.77 · $4.76 | cold read 3.5 / 5 against 0 defects; the user found chapter 1 unreadable |
| **7** | 10-03 | original fantasy, *Every House Must Eat* | **this room**: seven roles, an in-loop cold reader, a reader ledger | 5 · 22,265 | $70.73 · **$3.18** | **4.5 / 5 from three blind judges**; 18/18 premise facts in their retells |

The runs are not a controlled series. The novel, the model, the toolkit and the instrument changed
between most of them, and each write-up names its own confounds.

## What each run established

**Run #1** found what the toolkit cost to operate and stopped at chapter 5 on purpose. Dialogue
was starved (2–5% speech), chapters landed on the word floor, and 21 of 37 skills never loaded,
because a condensed checklist made their sources unnecessary to open.

**Run #2.** The novel passed every command in the repo, and the first human to read it said the
dialogue did not sound like people and the characters were never introduced. Both were true and
measurable, and neither was measured. Its chapter 2 cleared the new 10% dialogue-share floor at 10.2%, by giving a character a
muttering habit the drafter admitted was retrofitted to the gate. That is how *never gate on a number* was learned the second time.

**Run #3** shipped only after a redraft of all five chapters, and what the redraft fixed became
six rules: the ~45-word turn ceiling, the cadence test, the build-up thesis, and the sharpest one:
**a prohibition is satisfied by silence.** Five chapters passed every check because the drafter
never mentioned the body it was forbidden to get wrong.

**Run #4** ran unaided. A warm agent opened 5 draft cards and no audit card in five chapters; a
cold one opened 33 in one chapter. A human reading the chapters found three things no script saw,
chief among them that every habit-shaped check was a note and the cross-chapter detectors read
only defects and warns, so what mattered only across chapters was excluded by construction.

**Run #5** did not reproduce run #4's card decay: the same harness opened the full set. Its cold
read (3 / 5 against 0 defects) found five costs with no owner: no story underway, five two-handers
in a row, one line four times in two mouths, a world named but not built, and negation density. A
warn-level speech target was optimised to within 0.3 points: **a warn is a gate, whatever the
doctrine says**, learned a third time. The compressing proxy shortened a read-set from 515 words
to 397 and nobody noticed; it was removed.

**Run #6** was the first run through the role pipeline, and the last on skilled-writer. It ran
unassisted for five chapters with every hand-off on disk. The reader's two highest costs were both
cross-chapter, an antagonist who never reached the page and one rhetorical move in every mouth,
and no per-chapter gate could see them. The user found chapter 1 unreadable: the premise never
reached the page. The diagnosis ([00](roadmap/00-diagnosis.md)) followed: every loop agent held
the bible, the only cold reader ran after five chapters and read intent-bearing frontmatter, and
each run's findings had been appended as rules (~190k words of corpus). The user chose a rebuild.

**Run #7** was this room's first, on a fresh seed, with no file touched by hand. Chapter 1's
central rule was `stated` in the in-loop reader's retell, and three blind judges gave 4.5. Their
top costs were a villain readable too early (the opposite of run #6's absent antagonist), one
narrator refrain across chapters (run #6's class, smaller), the narrator explaining its own move,
and an ally handing over the investigation's biggest step. Each was routed to a knowledge base or a
tool ([05](roadmap/05-benchmark-run-7.md)). The cost per word fell from $4.76 to $3.18; the
chapters are 2.6 times longer.

## The thread through all seven

Every gain after run #2 came from a reader, not a check. Each run's checks passed, and a reader
then found what they could not see: what the page leaves out (#2, #6), what recurs across chapters
(#4, #5, #6, #7), and what a rule satisfied by silence (#3). This room is built on that: a reader
who has not seen the bible reads every chapter, in the loop.
