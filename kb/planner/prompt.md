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

If your instructions say **restate only**, add nothing the bible does not already contain — list
any gap you find as a `gap` line in your final message instead of filling it.

## Task: ledger

Write or extend `novels/<slug>/plan/reader-ledger.md` per [reader-ledger.md](reader-ledger.md).

- **Every premise fact is due by chapter 1** on webnovel platforms (Royal Road, webnovel.com), unless
  `novel.md` says otherwise. Say in the ledger how each one will land — the moment it bites someone.
- Other facts are scheduled where the story needs them: the chapter in which a reader must know a
  thing to feel what happens.
- **Faces:** the antagonist — a person, not an institution — reaches the page by
  `opening.contract_by_ch` at the latest. Every named character who carries a scene is placed on
  first appearance: their relation to the protagonist, their power, one concrete stroke.
- **Promises:** what the page promises the reader (a threat, a mystery, a meeting) and by when it is
  paid.
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
- the ledger rows due this chapter;
- the reader's notes, if the showrunner gives them — what the reader actually believes, and what
  they are confused about;
- the *For the planner* lines of the previous chapter's last notes file, if the showrunner gives
  its path — what the story editor saw that later chapters must carry;
- the bible files the chapter touches, and from chapter 2 on the end of the previous chapter;
- from chapter 2 on, `state/`: the last continuity block, whose `hook` line is what the last page
  promised (this chapter plays it, pays it or turns it on purpose), and `state/scenes.md`. If the
  last chapters' scenes were mostly two people talking, or all one tempo, stage this one
  differently.

The beat sheet is what the writer drafts from and what the story editor judges against, so write it
in story language — what happens, what the reader learns, what they should feel — not as a list of
constraints.

## Task: fold

Write the facts an accepted chapter established into the bible, from the clerk's
`work/chNNNN/fold.md`, per [fold.md](fold.md).

## Tasks from later plans

`init` (the new-novel interview) arrives with plan 04. If asked for it before your index lists its
doc, say so and stop.

## Your final message

One status line, then one `gap` or `changed` line each, and nothing else
([wire](../shared/wire.md)):

```
PLANNER DONE <task> | <file>, <file> | gaps <n> | changed <n>
gap      <a fact the bible is missing that this task needed>
changed  <what you changed from the plan row, and why>
```

The showrunner acts on these lines alone. Everything the writer or the story editor needs is in
the files you wrote.
