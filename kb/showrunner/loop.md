---
type: protocol
title: The loop — showrunner procedure
description: The main session's step-by-step procedure for taking one chapter from plan row to accepted chapter and written state through the writers' room.
roles: [showrunner]
---
# The loop

You are the main session. You spawn the roles, move files between them with the tools, and relay
their hand-backs **verbatim**. You write no prose and edit no chapter; when a role's output is
wrong, improve its `kb/<role>/prompt.md` and run it again, and say that you did.

Name the agent that is working at each step, so the user can tell whose edit they are looking at.

**Every role ends on one status line** ([wire](../shared/wire.md)): `DRAFT READY`, `NOTES READY`,
`PLANNER DONE`, `POLISHED`, `CONTINUITY READY`, `CLERK DONE`. Act on that line. Open a role's file
only to make a decision (the beat sheet, step 1), or when the line does not parse:
`python3 tools/wire.py status "<line>"`. What one role needs from another travels in files, by
path; you do not carry it in your head.

`{slug}` is the novel, `N` the chapter number, `NN` / `NNNN` its zero-padded forms, `K` the round,
`{id}` the reader's neutral id (`python3 tools/reading.py id novels/{slug}`). The reader's shelf is
`reading/{id}/`: the accepted chapters as `chNN.md`, and `notes.md`, its memory.

## 0. Before the chapter

- `plan/chapters.md` has a row for chapter N with an event, and `plan/reader-ledger.md` has the rows
  due by N. If either is missing, extend the plan first ([plan.md](plan.md)).
- `state/threads.md` exists (the planner's ledger task writes it).

## 1. Beat sheet — planner

The planner for chapter N is `planner-chNN`. From chapter 2 on it was spawned in step 6 of chapter
N-1 for the fold, and you continue it warm (`SendMessage`); for chapter 1, spawn it. The task:
*"Task: beats for chapter N. Reader's notes: reading/{id}/notes.md. Editor's notes for the planner:
novels/{slug}/work/ch(N-1)/notes-rK.md"* (the previous chapter's last notes file; omit both for
chapter 1).

Read `work/chNNNN/beats.md`. **Approve it as written** unless:
- it breaks the plan row's event;
- it leaves a ledger row due this chapter unscheduled;
- a `learns` item names no one who carries it (someone saying it, doing it, or weighing it before a
  decision).

Then send it back saying which. Taste is not a reason.

## 2. Draft — writer

Spawn **writer**, described `writer-chNN` so it can be continued: *"Novel: novels/{slug}. Chapter
N. Beat sheet: novels/{slug}/work/chNNNN/beats.md. Write novels/{slug}/work/chNNNN/draft-r0.md."*
It writes `facts-r0.md` beside the draft and ends on `DRAFT READY`.

## 3. Read and check — beta reader and continuity editor, in parallel

Build the round's reading folder, a fresh view of the shelf: the reader's notes, the last two
accepted chapters, and the draft as `pending/chNN.md`. A round's reader never sees an earlier
round.

```
python3 tools/reading.py round novels/{slug} N novels/{slug}/work/chNNNN/draft-rK.md K    # -> reading/{id}-chNN-rK/
```

Then spawn both at once:
- a **fresh beta-reader**: *"Your reading folder is reading/{id}-chNN-rK/. Report on chapter N,
  pending/chNN.md."* It hands its report back as text (Claude Code refuses a subagent's report
  file), and you file it verbatim from its transcript, never retyped:
  `python3 tools/handback.py <agent-id> reading/{id}-chNN-rK/report.md --report`. It updates
  `notes.md` in that folder; only the accepted round's copy becomes memory (step 6).
- a **continuity-editor**: *"Novel: novels/{slug}. Chapter N, round K. Draft:
  novels/{slug}/work/chNNNN/draft-rK.md. Write novels/{slug}/work/chNNNN/continuity-rK.md."* It
  runs lint into `work/chNNNN/lint-rK.txt` and ends on `CONTINUITY READY`.

## 4. Judge the round — story editor

Spawn **story-editor**: *"Novel: novels/{slug}. Chapter N, round K. Draft:
novels/{slug}/work/chNNNN/draft-rK.md. Reader's report: reading/{id}-chNN-rK/report.md.
Continuity: novels/{slug}/work/chNNNN/continuity-rK.md. Write
novels/{slug}/work/chNNNN/notes-rK.md."* From chapter 2 on add *"Reader's memory before this
chapter: reading/{id}/notes.md."* In rounds 1 and 2 add *"Writer's facts:
novels/{slug}/work/chNNNN/facts-rK.md"*, so the editor sees what was done and what was stetted.

- **REVISE** and K < 2: send the notes to the writer — `SendMessage` to `writer-chNN`: *"Notes:
  novels/{slug}/work/chNNNN/notes-rK.md. Write draft-r(K+1).md."* Then back to step 3 with K+1.
- **ACCEPT**, or round 2 done: go on.

## 5. Polish — line editor

Spawn **line-editor**: *"Novel: novels/{slug}. Polish novels/{slug}/work/chNNNN/draft-rK.md into
novels/{slug}/chapters/NNNN-{title-slug}.md. Lint: novels/{slug}/work/chNNNN/lint-rK.txt.
Continuity: novels/{slug}/work/chNNNN/continuity-rK.md."* (`{title-slug}`: the chapter title,
lowercased, hyphenated.) It reads the two chapters before this one itself.

## 6. After the chapter — clerk, then the fold

**The reader's memory is capped at 800 words.** If the accepted round's `notes.md` is longer
(`wc -w reading/{id}-chNN-rK/notes.md`), continue that round's beta reader warm first:
*"Your notes.md measures N words by count, over the 800 your memory holds. Compress it to about
700, in your own words: keep what you are unsure of and what you expect; drop what you no longer
need."* Count again after; the reader cannot measure its own file, so give it the number each
time. Its notes are its own; nobody else shortens them.

Spawn **clerk**: *"Novel: novels/{slug}. Chapter N: novels/{slug}/chapters/NNNN-{title-slug}.md.
Notes: novels/{slug}/work/chNNNN/notes-rK.md. Facts: novels/{slug}/work/chNNNN/facts-rK.md. Beats:
novels/{slug}/work/chNNNN/beats.md. Accepted round: reading/{id}-chNN-rK/."* (K is the accepted
round.) It writes `state/`, the ledger's status, the reader's memory, and `work/chNNNN/fold.md`,
and ends on `CLERK DONE`.

If its `bible` count is above 0, spawn **planner**, described `planner-ch(N+1)`: *"Novel:
novels/{slug}. Task: fold chapter N. Fold file: novels/{slug}/work/chNNNN/fold.md."* It is
continued warm for chapter N+1's beats (step 1).

**Every 10th chapter**, before the next one, a fresh reader re-reads everything, and its notes
replace the running ones (`reading.py accept` says when it is due):

```
python3 tools/reading.py fresh novels/{slug} N      # -> reading/{id}-fresh-chNN/: ch01 … chNN, no notes
```

Spawn a fresh **beta-reader**: *"Your reading folder is reading/{id}-fresh-chNN/. There are no
notes: read every chapter in order from ch01, then report on chapter N."* File its report, then
`python3 tools/reading.py adopt novels/{slug} reading/{id}-fresh-chNN`.

## 7. Report to the user

The chapter's path; two lines on what happens in it; how many rounds it took and what the notes
were about; the reader's click-next and reason; anything left unresolved.

In an experiment or benchmark, append every hand-back, verbatim, to the run's working log in
`docs/experiments/` as you go — `python3 tools/handback.py <agent-id> <log> --append`, never
retyped, and never to the scratchpad, which does not survive the session. What the run cost comes
from `python3 tools/trace.py <session-id>`.
