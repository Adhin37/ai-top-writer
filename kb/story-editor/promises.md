---
type: catalog
title: Promises, reveals and the stakes ceiling
description: Whether what the page promised is played, paid or turned on purpose, whether a reveal re-reads what the reader already had, and whether a consequence outran the reader's ability to price it.
roles: [story-editor]
---
# Promises, reveals and the stakes ceiling

Everything the page sets up is a promise the reader is now holding: a threat, a meeting, a question,
the last line of the last chapter. It is played, paid or turned on purpose. It is never skipped
over a chapter break. A reveal is fair when it re-reads information the reader already had. A
consequence may not escalate past the reader's ability to tell how bad it is.

## Patterns

### The promise skipped over the break

> Chapter 3 ends: "Tomorrow, at the recruitment office." Chapter 4 opens: "Two weeks into the deep
> crew, Tovi had stopped counting the days."

The recruitment scene (the one the reader was promised) happened offstage. Check the last block's
`hook` in `state/continuity.md` and the reader's predictions in its memory against the draft's first
scene.

```
N1 the promised meeting happens offstage
where "Two weeks into the deep crew"
ev    state C0003 hook: "the recruitment office, tomorrow" · reader's memory: "I expect the recruiter scene next"
eff   the reader was waiting for a scene and got its aftermath
dir   play it, or turn it: she goes, and the office is closed
```

### The turn that is a different promise

Turned on purpose is legitimate: she goes to the office and it is closed, and that is worse.
What fails is a turn nobody on the page notices.

### The reveal from nowhere

> "The recruiter was Kell's brother."

If no earlier scene put the two of them in reach of each other, that is an announcement, not a
reveal. A fair one was planted at least once doing another job, and ideally noticed and dismissed by
someone on the page, so the reader remembers having been offered it.

### The reveal that changes nothing

A reveal that only changes the reader's understanding is trivia. It should re-price a relationship,
force a decision, or show an earlier cost was paid for nothing.

### The consequence above the ceiling

> Chapter 2: she mentions the Deck Nine pump. Chapter 3: Security has her name. Chapter 4: she is
> arrested for sabotage.

Each step may be logical, but the reader does not yet know what Security does to people, so the
arrest reads as plot rather than dread. Before a consequence lands, the reader must have seen what
it costs someone. Usually that is a bystander, earlier.

### The mystery without fair play

When `novel.md` has `optional.mystery-clues: on`, the answer must be reachable: every clue the
solution uses was on the page, in plain sight, before the reveal.

## When it does not apply

A promise can be deliberately deferred, if the page says so: the meeting is postponed, and someone
says why. The reader holds a deferred promise patiently. An unexplained skip is what they drop.
