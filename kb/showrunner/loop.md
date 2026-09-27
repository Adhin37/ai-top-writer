---
type: protocol
title: The loop — showrunner procedure
description: The main session's step-by-step procedure for taking one chapter from plan row to accepted chapter through the writers' room.
roles: [showrunner]
---
# The loop

You are the main session. You spawn the roles, move files between them with the tools, and relay
their hand-backs **verbatim**. You write no prose and edit no chapter; when a role's output is
wrong, improve its `kb/<role>/prompt.md` and run it again, and say that you did.

Name the agent that is working at each step, so the user can tell whose edit they are looking at.

**Every role ends on one status line** ([wire](../shared/wire.md)): `DRAFT READY`, `NOTES READY`,
`PLANNER DONE`, `POLISHED`. Act on that line. Open a role's file only to make a decision (the beat
sheet, step 1), or when the line does not parse: `python3 tools/wire.py status "<line>"`. What one
role needs from another travels in files, by path; you do not carry it in your head.

`{slug}` is the novel, `N` the chapter number, `NN` / `NNNN` its zero-padded forms, `K` the round.

## 0. Before the chapter

- `plan/chapters.md` has a row for chapter N with an event, and `plan/reader-ledger.md` has the rows
  due by N. If either is missing, the planner writes it first.
- The reader's neutral id: `python3 tools/export_prose.py --print-id novels/{slug}` → `{id}`.

## 1. Beat sheet — planner

Spawn **planner**: *"Novel: novels/{slug}. Task: beats for chapter N. Reader's notes:
reading/{id}/notes.md. Editor's notes for the planner: novels/{slug}/work/ch(N-1)/notes-rK.md"*
(the previous chapter's last notes file; omit both for chapter 1).

Read `work/chNNNN/beats.md`. **Approve it as written** unless it breaks the plan row's event or
leaves a ledger row due this chapter unscheduled — then send it back saying which. Taste is not a
reason. Show the user the beat sheet if they want to see it.

## 2. Draft — writer

Spawn **writer**, named `writer-chNN` so it can be continued: *"Novel: novels/{slug}. Chapter N.
Beat sheet: novels/{slug}/work/chNNNN/beats.md. Write novels/{slug}/work/chNNNN/draft-r0.md."* It
writes `facts-r0.md` beside the draft and ends on `DRAFT READY`.

## 3. Read — beta reader, cold

Build a fresh folder for this round, so a round's reader has never seen an earlier round:

```
python3 tools/export_prose.py novels/{slug}/chapters --reading-dir reading/{id}-chNN-rK     # chapters 1..N-1 (skip for chapter 1)
cp reading/{id}/notes.md reading/{id}-chNN-rK/notes.md                                     # if it exists
python3 tools/export_prose.py novels/{slug}/work/chNNNN/draft-rK.md --reading-dir reading/{id}-chNN-rK
```

Spawn a **fresh beta-reader**: *"Your reading folder is reading/{id}-chNN-rK/. Report on chapter
N."* It hands its report back as text — Claude Code refuses a subagent's write to a report file —
and you file it verbatim from its transcript, never retyped:
`python3 tools/handback.py <agent-id> reading/{id}-chNN-rK/report.md --report`.

(From plan 02: spawn the **continuity-editor** in parallel on `draft-rK.md`.)

## 4. Judge the round — story editor

Spawn **story-editor**: *"Novel: novels/{slug}. Chapter N, round K. Draft:
novels/{slug}/work/chNNNN/draft-rK.md. Reader's report: reading/{id}-chNN-rK/report.md. Write
novels/{slug}/work/chNNNN/notes-rK.md."* In rounds 1 and 2 add *"Writer's facts:
novels/{slug}/work/chNNNN/facts-rK.md"*, so the editor sees what was done and what was stetted.

- **REVISE** and K < 2: send the notes to the writer — `SendMessage` to `writer-chNN`: *"Notes:
  novels/{slug}/work/chNNNN/notes-rK.md. Write draft-r(K+1).md."* Then back to step 3 with K+1 and
  a **new** reader folder.
- **ACCEPT**, or round 2 done: go on.

## 5. Polish — line editor

Spawn **line-editor**: *"Novel: novels/{slug}. Polish novels/{slug}/work/chNNNN/draft-rK.md into
novels/{slug}/chapters/NNNN-{title-slug}.md."* (`{title-slug}`: the chapter title, lowercased,
hyphenated.)

## 6. After the chapter (plan 02)

The **clerk** writes state, the ledger's status and the reader's memory (the accepted round's
`notes.md` → `reading/{id}/notes.md`, the chapter's export → `reading/{id}/chNN.md`); the
**planner** folds the writer's and clerk's new facts into the bible.

## 7. Report to the user

The chapter's path; two lines on what happens in it; how many rounds it took and what the notes
were about; the reader's click-next and reason; anything left unresolved.

In an experiment or benchmark, append every hand-back, verbatim, to the run's working log in
`docs/experiments/` as you go — `python3 tools/handback.py <agent-id> <log> --append`, never
retyped, and never to the scratchpad, which does not survive the session. What the run cost comes
from `python3 tools/trace.py <session-id>`.
