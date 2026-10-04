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

**Every turn re-reads your whole context, so spend few.** Each step below is one call to
`tools/room.py`: it runs the step's tools, checks the files the step needs, and prints the next
dispatches, filled in:

```
@ spawn <agent type> as "<description>"      -> Agent, with that description
@ continue <name>                            -> SendMessage to that agent's id
<the text to send, unchanged>
```

- Send each dispatch's text exactly as printed. Spawn all of one step's dispatches in one message.
- Never open a file to check that a role wrote it: the next `room.py` call checks, and prints
  `STOP: <why>` when something is missing. Act on the STOP.
- `python3 tools/room.py where novels/{slug}` says which chapter and step the files are at: after a
  compaction, a resume, or whenever you are unsure.

`{slug}` is the novel, `N` the chapter number, `K` the round.

## 1. Beat sheet — planner

From chapter 2 on, the previous chapter's `room.py fold` printed this step: continue the planner
warm. For chapter 1, the first chapter of a session, or when no fold ran:
`python3 tools/room.py beats novels/{slug} N`. It stops if the chapter has no plan row or the
ledger has rows past due ([plan.md](plan.md) first; `fold` says the same for the next chapter), and
it prints a `PAUSE` line when the usage window is nearly spent (below).

Read `work/chNNNN/beats.md` (`room.py` printed its path). Approve it **as written** unless:
- it breaks the plan row's event;
- it leaves a ledger row due this chapter unscheduled;
- a `learns` item names no one who carries it (someone saying it, doing it, or weighing it before a
  decision).

Then send it back saying which. Taste is not a reason.

## 2. Draft — writer

Send the writer dispatch `room.py beats` or `fold` printed. The writer writes `facts-r0.md` beside
the draft and ends on `DRAFT READY`.

## 3. Read and check — beta reader and continuity editor

On `DRAFT READY`: `python3 tools/room.py round novels/{slug} N K`. It builds the round's reading
folder (the reader's notes, the last two accepted chapters, the draft as `pending/chNN.md`; a
round's reader never sees an earlier round) and, from chapter 3 on, the history report for the
story editor and the line editor. Spawn the two dispatches it prints, a fresh **beta-reader** and a
**continuity-editor**, in one message, and wait for both.

## 4. Judge the round — story editor

With both back: `python3 tools/room.py judge novels/{slug} N K <beta-reader agent id>`. It files
the reader's report verbatim from its transcript (Claude Code refuses a subagent's report file)
and checks the continuity file. Spawn the **story-editor** it prints. On its `NOTES READY` line,
send the branch `room.py judge` printed for that verdict:

- **REVISE** and K < 2: continue `writer-chNN` with the notes, then step 3 with K+1.
- **ACCEPT**, or round 2 done: spawn the **line-editor**, step 5.

## 5. Polish — line editor

The line editor reads the two chapters before this one itself, and ends on `POLISHED`.

## 6. After the chapter — clerk, then the fold

On `POLISHED`: `python3 tools/room.py clerk novels/{slug} N K` (K, the accepted round). **The
reader's memory is capped at 800 words**: if the accepted round's `notes.md` is over, it prints a
continuation of that round's beta reader to compress its own notes, and you run `room.py clerk`
again after, which counts afresh (the reader cannot measure its own file). Its notes are its own;
nobody else shortens them. Under the cap, it prints the **clerk**. The clerk writes `state/`, the
ledger's status, the reader's memory and `work/chNNNN/fold.md`, and ends on `CLERK DONE`.

On `CLERK DONE`: `python3 tools/room.py fold novels/{slug} N`. It runs the state check and counts
the fold file. If the fold has lines for the bible it prints a **planner**, described
`planner-ch(N+1)`, to fold them; that planner is continued warm for chapter N+1's beats, which it
also prints. Send the fold now; the beats when chapter N+1 starts.

**Every 10th chapter** `room.py fold` also builds a fresh reading folder (ch01 … chNN, no notes) and
prints a fresh **beta-reader** for it. With its report back, `python3 tools/room.py adopt
novels/{slug} N <agent id>` files the report, and its notes replace the running ones before the
next chapter.

## Pause at a chapter boundary

When `room.py` prints a `PAUSE` line, or a hook says the 5-hour window is past 80%, finish the step
in hand and the chapter's fold, and start no new chapter. Then schedule the resume and stop:

- load `CronCreate` (`ToolSearch`, `select:CronCreate`) and create a one-shot (`recurring: false`)
  at a minute or two past the reset time printed, with the prompt *"The usage window has reset.
  Resume the run: chapter N+1 of {slug}, then the rest of the /write count, from
  kb/showrunner/loop.md; `python3 tools/room.py where novels/{slug}` says the step."*;
- tell the user, in one line, when it resumes.

The job lives only in this session; if the session closes, its handoff (`docs/sessions/`) resumes
it. If the limit is hit mid-step anyway, Claude Code waits for the reset and continues.

## 7. Report to the user

The chapter's path; two lines on what happens in it; how many rounds it took and what the notes
were about; the reader's click-next and reason; anything left unresolved.

In an experiment or benchmark, add `--log docs/experiments/<log>.md` to every `room.py` call, and
`--agent <id>` for each agent that has handed back since the last call (the writer, the continuity
editor, the story editor, the line editor, the clerk, the planner). It appends their hand-backs
verbatim, and every dispatch sent, to the run's working log; never to the scratchpad, which does
not survive the session. What the run cost comes from `python3 tools/trace.py <session-id>
--chapters`.
