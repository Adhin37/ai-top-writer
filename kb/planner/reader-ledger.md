---
type: howto
title: The reader ledger
description: How to write plan/reader-ledger.md — the facts, faces and promises the page owes the reader, scheduled by chapter.
roles: [planner]
---
# The reader ledger

The bible tracks what is true and the plan tracks what happens; the ledger tracks **what the reader
has been told**. Every row is a debt the page owes, with a due chapter and a plan for how it lands.
The story editor grades the beta reader's retell against the rows due each chapter, and the clerk
marks what landed — so a fact the page never delivered stays visibly owed instead of silently
assumed.

Three kinds of row:

- **Facts** — how the world works, in plain words. The premise facts are due in chapter 1.
- **Faces** — people the reader must meet in person: above all the antagonist, who must be a person
  on the page, not a letterhead, by the opening contract chapter.
- **Promises** — what the page has promised the reader will happen or be answered, and by when.

The ledger is read by the planner, the story editor and the clerk, never by a reader of the book,
so it is [wire](../shared/wire.md): one row per debt, the fact in one clause (about twenty words),
and *how it lands* as a moment in about twenty-five. Premise facts are already written out in
`bible/premise.md`; their rows say `premise` and the moment, not the fact again.

## Example

The world is invented.

```markdown
# Reader ledger

## Facts
| id | fact, in plain words | due by ch | how it lands | status |
|---|---|---|---|---|
| P1 | premise | 1 | Tovi's first line of work is a leaking air main; she says it to the new hire | owed |
| P2 | premise | 1 | her meter ticks over at shift change the moment her grade is struck | owed |
| P3 | premise | 1 | the clerk tells her, reading it off the form; her brother asks what day thirty-one means | owed |
| F4 | The deep crews are paid in air, not credits | 2 | the crew boss's offer | owed |
| F5 | Down-well is a mining colony, and no one has ever bought their way back up | 4 | a letter from someone who went | owed |

## Faces
| id | who | why the reader needs them | on the page by ch | status |
|---|---|---|---|---|
| A1 | Supervisor Kell, who struck Tovi's grade | the opposition needs a face and a reason | 1 | owed |
| A2 | the deep-crew boss | the offer she cannot refuse needs a person making it | 2 | owed |

## Promises
| id | what the page promises | made in ch | paid by ch | status |
|---|---|---|---|---|
| R1 | why Kell struck her grade | 1 | 6 | owed |
| R2 | what happened to the last deep crew | 2 | 8 | owed |
```

**Status** is `owed`, `landed chN`, `partly chN — <what is missing>`, or `moved to chN — <why>`.

## Checks

- **"How it lands" names a moment**, not a method: which character, which action, which line. "As
  consequence" is not a plan; "her meter ticks over when her grade is struck" is.
- **Chapter 1 carries the premise and not much else.** If chapter 1's column holds ten facts, most
  of them belong later.
- **The antagonist has a face early.** An opposition that only ever acts through documents,
  orders and rumours reads as weather, not a threat.
- **Promises get paid or deliberately moved** — never silently dropped. A scene the previous chapter
  promised is played, paid, or rescheduled with a reason.
