---
type: howto
title: Folding a chapter's facts into the bible
description: How to write the facts an accepted chapter established (the clerk's work/chNNNN/fold.md) into the bible, so the next chapter's writer and continuity editor find them there.
roles: [planner]
---
# The fold

A writer invents as it drafts: a cousin, a distance, a price. Once the chapter is accepted, those
inventions are true, because the reader has read them. The clerk lists them in
`work/chNNNN/fold.md`; you write them into the bible. A fact left only in a chapter is a
contradiction waiting three chapters on, when a writer who never read that chapter gets it wrong.

## For each line

- **`new`**: find where someone looking it up would look. A person's detail goes in their cast file
  (a walk-on's in their `_extras.md` line), a place or distance in `world.md`, a price, law or custom
  in `society.md`, a term or spelling in `lexicon.md`. Write it in that file's own form: a table
  row, a roster stroke, a sentence in the right section. It needs no citation; the chapter is its
  source.
- **`stale`**: correct the bible line to what the chapter set.
- **A `new` fact that contradicts the bible:** the page wins, because the reader has it. Change the
  bible line and add a `changed` line. If the change breaks a plan row or a ledger row, add a `gap`
  line naming the row.
- **A fact you cannot place,** or one that would break the plan: leave it out, and add a `gap` line.
- **A walk-on whose `_extras.md` line now counts a third chapter**, or who made a decision that
  moved the plot: write their profile ([cast-design.md](cast-design.md)) and drop the `_extras.md`
  entry.
- **The chapter's plan row**: set its threads cell to the threads the chapter touched (its block's
  `thr` in `state/continuity.md`), so the plan says what the book did.

A `gap` about a `state/` cell (a thread's chapter, a timeline line) is the clerk's to fix: name the
file and the cell. Fold only what the file lists. What the story editor noted *For the planner* is for the next beat
sheet, not for the bible.

## Example

The world is invented: a harbour town where the sea gives back its drowned once a year.

```
new    Orrin is Ysolde's cousin, not her brother | bible/cast/_extras.md | "your mother's sister's boy"
```

`_extras.md` had `Orrin — Ysolde's brother, boathouse lad — ch 1, 3 — alive`. The line becomes
`Orrin — Ysolde's cousin (her mother's sister's son), boathouse lad — ch 1, 3 — alive`, and the final
message carries:

```
changed  bible/cast/_extras.md: Orrin is Ysolde's cousin, not her brother (ch 3)
gap      plan row 9 has "Ysolde's brother" at the Calder wake; the row needs Orrin's new relation
```

## Your final message for a fold

```
PLANNER DONE fold | <bible files you changed> | gaps <n> | changed <n>
```

`changed` counts the bible lines you altered, not the ones you added. Each gets a `changed` line;
additions need none.
