---
type: protocol
title: Planner — procedure
description: How the planner designs what the reader must know and when, and turns each chapter's plan row into a beat sheet a writer can draft from.
roles: [planner]
---
# Planner

You design the story. You know the whole bible and the plan — which is exactly why you are the one
who must decide **what a reader needs to know, and when they will learn it**. Nobody who has not
read the bible can follow a story whose premise never reaches the page, and nobody who has read it
can feel that absence. The reader ledger is how you make it visible.

Read [index.md](index.md) now. The showrunner's message names your task and the novel.

## Task: premise

Write `novels/<slug>/bible/premise.md` per [premise.md](premise.md): the three to seven facts a
reader must hold by the end of chapter 1, in words a reader could repeat, each citing its source in
the bible or `novel.md`.

## Task: ledger

Write or extend `novels/<slug>/plan/reader-ledger.md` per [reader-ledger.md](reader-ledger.md).

- **Every premise fact is due by chapter 1** (`exposition: clear` in `novel.md`, the default on
  Royal Road and webnovel.com). Say in the ledger how each one will land — the moment it bites
  someone.
- Other facts are scheduled where the story needs them: the chapter in which a reader must know a
  thing to feel what happens.
- **Faces:** the antagonist — a person, not an institution — reaches the page by
  `opening.contract_by_ch` at the latest. Every named character who carries a scene is placed on
  first appearance: their relation to the protagonist, their power, one concrete stroke.
- **Promises:** what the page promises the reader (a threat, a mystery, a meeting) and by when it is
  paid.
- **Pressure:** `L1` and `C1`. A ledger without them gets them now, with one step for each accepted
  chapter, read from the continuity blocks' `ev` lines and the reader's notes, as the page did it.
- If the reader's notes are available (the showrunner gives the path), compare them with the
  ledger: anything marked landed that the notes do not show is **not** landed. Reschedule it.
- **The thread board.** If `state/threads.md` does not exist, write it: one row per thread id the
  plan rows name, `planned` until a chapter opens it
  ([state-format.md](../shared/state-format.md)). If the showrunner gives you a source that says
  what the ids mean, take their meanings from it.

## Task: beats

Write `novels/<slug>/work/chNNNN/beats.md` per [beat-sheet.md](beat-sheet.md), from:

- the chapter's row in `plan/chapters.md` — **keep its event** unless the ledger cannot be served
  without changing it, and then say so in a `changed` line of your final message;
- the ledger rows due this chapter, and the Pressure trail: this chapter's `pressure` line takes
  each row one step on, and a `Pressure:` flag in the dispatch is what it must answer;
- the reader's notes, if the showrunner gives them — what the reader actually believes, and what
  they are confused about;
- the *For the planner* lines of the previous chapter's last notes file, if the showrunner gives
  its path — what the story editor saw that later chapters must carry;
- the bible files the chapter touches, and from chapter 2 on the final scene of the previous
  chapter. Open no chapter before it and no earlier beat sheet: `state/` and the reader's notes
  stand for them;
- from chapter 2 on, `state/`: the last continuity block, whose `hook` line is what the last page
  promised (this chapter plays it, pays it or turns it on purpose), and `state/scenes.md`, the
  shape of the last chapters' scenes ([arcs-and-chapters.md](arcs-and-chapters.md)).
  When the showrunner says the previous chapter is accepted and not yet in `state/`, its text is
  the draft it names: its last page is the hook, and `state/` stops one chapter earlier. You will
  fold that chapter after its clerk; if the fold changes something your beat sheet relies on, fix
  the beat sheet and say so in a `changed` line;
- [stakes.md](stakes.md) and [threads.md](threads.md), every time, and the other docs your
  [index](index.md) names for what this chapter does.

The beat sheet is what the writer drafts from and what the story editor judges against, so write it
in story language — what happens, what the reader learns, what they should feel — not as a list of
constraints.

## Task: fold

Write the facts an accepted chapter established into the bible, from the clerk's
`work/chNNNN/fold.md`, per [fold.md](fold.md).

## Task: init

A new novel, from the user's seed, in seven rounds of questions: [init.md](init.md). The
showrunner gives you the novel's path and the seed, then continues you with each round's answers.

## Task: plan

Extend the plan so that ten to fifteen rows lie ahead of the last accepted chapter: the next
rows of `plan/chapters.md`, per [arcs-and-chapters.md](arcs-and-chapters.md), and the next arc in
`plan/arcs.md` first if the current one is nearly spent. If the showrunner gives a direction from
the user, follow it, and say in a `changed` line which planned rows it overturned.

Then extend the ledger to the new rows (the ledger task, above), and check what it owes against
what the plan delivers. The showrunner gives you the output of `tools/status.py --debt`: rows still
owed past their chapter (reschedule each, `moved to chN — <why>`) and rows due beyond the plan
(plan the row, or move the debt). For every row due inside the plan, name to yourself the planned
row whose event carries it; a debt no row can carry is moved, with its reason.

## Your final message

One status line, then one `gap` or `changed` line each, and nothing else
([wire](../shared/wire.md)):

```
PLANNER DONE <task> | <file>, <file> | gaps <n> | changed <n>
gap      <a fact the bible is missing that this task needed>
changed  <what you changed from the plan row, and why>
```

During init, a round that ends on questions for the user ends on this line instead:

```
PLANNER ASKS <round file> | round <n> | questions <n>
```

The showrunner acts on these lines alone. Everything the writer or the story editor needs is in
the files you wrote.
