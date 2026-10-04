---
type: reference
title: State format
description: The files the clerk writes after each accepted chapter — continuity blocks, threads, timeline, scene log, ledger status, the fold file — and what each line means to the roles that read them.
roles: [clerk, continuity-editor, story-editor, planner]
---
# State format

`state/` is what is true *now*, chapter by chapter, and who knows it. The bible says what the world
is; state says where everyone stands after the last accepted chapter. The clerk writes it; the
continuity editor checks drafts against it; the story editor and the planner read what the last
page promised. All of it is [wire](wire.md): keyed lines, ids, short quotes.
`python3 tools/state_check.py novels/<slug>` checks that the files agree.

The examples are from an invented world: a harbour town where the sea gives back its drowned once a
year, on the Long Ebb, and they must be rowed out past the bar before dawn.

## `state/continuity.md` — one block per chapter

Appended, in chapter order, never rewritten. A header, then one line per key.

```
=C0003= day 12, dusk to night | words 2410
ev    Ysolde rows the Calder boy out past the bar alone, against the harbourmaster's order
at    Ysolde: the boathouse · Quell: the harbour office · Orrin: the quay steps
kno   Ysolde+ the tally was signed before the boy drowned (the date on it) · Quell? suspects she has seen it · Orrin- does not know she went out
has   Ysolde: the Calder tally, folded in her boot · Orrin: the boathouse key
cost  Ysolde: two fingers frostbitten, no grip in her left hand for days
thr   ^T2 ~T4
hook  Quell's lamp is lit in the office window when she comes back in
```

| key | what it holds | who reads it for what |
|---|---|---|
| header | `day` (the in-world day and time the chapter covers) · `words` (the chapter's measured length) | the continuity editor: time between chapters |
| `ev` | the event as it played on the page, one clause | everyone: what happened |
| `at` | where each person on the page is at the end | travel and presence in the next chapter |
| `kno` | who learned what, and how: `Name+` knows · `Name?` suspects · `Name-` does not know. The *how* matters: it is what lets a character say it later | knowledge provenance: a character may state only what they have a source for |
| `has` | who holds the objects that matter | an object in two hands at once |
| `cost` | what was spent, hurt or lost, and for how long | an injury healed too fast |
| `thr` | the threads this chapter moved: `~` opened, `^` advanced, `v` paid, `x` dropped | threads and the plan rows |
| `hook` | what the last page promises the reader next, in plain words | the next chapter plays it, pays it or turns it on purpose; it is never skipped over the break |

`ev`, `at`, `kno`, `thr` and `hook` are always there (`none` if a line is empty). `has` and
`cost` only when something changed.

## `state/threads.md` — the thread board

| id | thread | ledger | opened | last | status |
|---|---|---|---|---|---|
| T2 | who signed the Calder tally, and when | R3 | 1 | 3 | open |
| T4 | Quell knows she went out | — | 3 | 3 | open |
| T5 | the drowned who were never rowed out | R6 | — | — | planned |

- `id` is the id the plan rows use (`~T2` in `plan/chapters.md`). `ledger` is the promise row in
  `plan/reader-ledger.md` it serves, or `—`.
- `opened` and `last`: the chapter that opened it and the last one that touched it.
- `status`: `planned` (named in the plan, not yet on the page) · `open` · `paid` · `subverted` ·
  `dropped` (with the reason in the thread cell).

## `state/timeline.md` — the in-world calendar

| day | ch | where | what happens |
|---|---|---|---|
| 11 | 2 | the quay | the Long Ebb begins at dusk |
| 12 | 3 | the bar; the boathouse | Ysolde rows the boy out; back before dawn |

One row per in-world day a chapter covers. Distances and travel times are in the bible; this says
when.

## `state/scenes.md` — the scene log

| ch | scene | who | where | tempo | two-hander |
|---|---|---|---|---|---|
| 3 | 1 | Ysolde, Orrin | the quay steps | quiet | yes |
| 3 | 2 | Ysolde, the Calder boy (dead) | the bar at night | tense | no |
| 3 | 3 | Ysolde, Quell | the harbour office | tense | yes |

- `who`: everyone present, speaking or not.
- `tempo`: one of fast, tense, loud, warm, funny, bleak, procedural, quiet.
- `two-hander`: `yes` when the scene is two people talking and nothing else happens.

The log is for shape across chapters: a run of two-handers, or one tempo for three chapters, reads
as sameness to a reader long before anyone can name it.

## The reader ledger's status

The clerk sets the `status` cell of `plan/reader-ledger.md`, and nothing else in it:

| the story editor's grade | status |
|---|---|
| stated | `landed ch3` |
| partly | `partly ch3 — <what is missing, one clause>` |
| missing, wrong | unchanged (`owed`): the planner reschedules it |

That is for facts and faces. A **promise** is `landed chN` only in the chapter that pays it; the
grade of a promise the chapter makes says the reader holds it, and its row stays `owed` until the
payoff. `moved to chN — <why>` is the planner's.

## `work/chNNNN/fold.md` — new facts for the bible

What the chapter established that the bible does not yet hold, one fact a line. The planner folds
it into the bible; the clerk never edits `bible/`.

```
# Fold — chapter 3
new    the bar can be crossed on foot for an hour at the Long Ebb's lowest | bible/world.md | "the bar was dry for the length of a prayer"
new    Orrin is Ysolde's cousin, not her brother | bible/cast/_extras.md | "your mother's sister's boy"
stale  "the Long Ebb — first appears ch 4" | bible/lexicon.md | on the page from ch 1
```

- `new <fact, about twenty words> | <the bible file it belongs in> | "<the chapter's words>"`
- `stale <the bible line, clipped> | <its file> | <what the chapter set instead>`
