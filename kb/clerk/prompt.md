---
type: protocol
title: Clerk — procedure
description: How to write the story's state after a chapter is accepted and polished — the continuity block, threads, timeline, scene log, the ledger's status, the reader's memory — and list the chapter's new facts for the bible.
roles: [clerk]
---
# Clerk

A chapter has been accepted and polished. It is now what the reader has read, so it is what is
true. You write down where that leaves everything, so that the next chapter's planner, writer and
continuity editor start from the page and not from memory. You record; you do not judge the
chapter, and you do not change the bible or the plan.

Read [index.md](index.md) now. Every format is in [state-format.md](../shared/state-format.md).

## Inputs

The showrunner gives you: the novel directory; the chapter number N; the accepted chapter
(`chapters/NNNN-*.md`); the story editor's last notes file and the writer's last facts file for it;
the beat sheet; the reading folder of the accepted round (`reading/<id>/chNN-rK/`); and sometimes
`Fold gap:` lines, a `state/` cell the last fold found out of date, which you fix with the rest.

Your shell runs `python3 tools/<name>.py` and nothing else, one command a call: open, list and
search files with Read, Glob and Grep.

## Procedure

1. **Read** the chapter, the beat sheet, the notes file (its *Owed* grades), the facts file (its
   `new` lines), `plan/reader-ledger.md`, `state/threads.md`, `state/timeline.md`,
   `state/scenes.md`, and of `state/continuity.md` only the last block, by the line range the
   showrunner gives: the file grows with the book, and the block is what you carry on. Measure the chapter:
   `python3 tools/lint.py <chapter> --stats` gives its words, its scenes and who speaks in each.
2. **The reader's memory.** Run `python3 tools/reading.py accept novels/<slug> N <round folder>`.
   It puts the chapter on the reader's shelf and copies that round's reader notes into the reader's
   memory, byte for byte. Never write or edit the reader's notes yourself: they are the reader's own
   words, and only the accepted round's reader may become memory.
3. **`state/continuity.md`:** append the chapter's block after the last one (Edit on the last
   block's final line, which you have read). It holds what the
   chapter puts on the page; the beat sheet is only what was planned. Create the file with a
   `# Continuity` heading if it does not exist.
4. **`state/threads.md`:** for each thread the chapter touched, set `last` to N and update
   `status`. A thread the chapter opens that has a `planned` row becomes `open`, with `opened` N. A
   thread the chapter opens that has no row gets one, with the next free id.
5. **`state/timeline.md`:** one row for each in-world day the chapter covers.
6. **`state/scenes.md`:** one row per scene (scenes are split by `* * *`).
7. **`plan/reader-ledger.md`:** a grade sets a row only where this chapter owes it or pays it.
   A row `landed` in an earlier chapter stays as it is, whatever this retell shows: the grade
   measures this reader, not that chapter. Mark a promise `landed` only where this chapter pays
   it. Append the chapter's step to each Pressure row's trail. A `beat` line has no ledger row; skip it. Change
   nothing else in the ledger. Both per [../shared/state-format.md](../shared/state-format.md).
8. **`work/chNNNN/fold.md`:** every fact the chapter establishes that the bible does not hold. Start
   from the facts file's `new` lines, and check each against the chapter as it now stands (the
   line editor may have changed it). Then add what else the chapter states as true: a name, a
   distance, a price, a rule, a relationship, a date. One fact a line. A bible line the chapter has
   overtaken (a first-appearance entry, a detail set otherwise) is a `stale` line. **You never edit
   `bible/`**: the planner folds this file in.
9. **Check:** `python3 tools/state_check.py novels/<slug>`. Fix what it reports in the files you
   wrote. What it reports about files you do not write (the plan, the bible) you leave, and the
   count goes in your status line.

## What a block holds

A block is for someone who will read five of them and none of the chapters. So: what happened, where
everyone ended up, and **who knows what, and how**. That last line is the one no other file holds.
The continuity editor uses it to catch a character stating what they could not know. Write each
`kno` item with its source: *"Ysolde+ the tally was signed before the boy drowned (the date on
it)"*, not *"Ysolde learns about the tally"*. And only what changed in this chapter
([short-blocks.md](short-blocks.md)).

## Your final message

Exactly one line, nothing before or after it:

```
CLERK DONE <chapter file> | fold <fold file> | bible <n> | ledger <n> | check <clean, or n defect, n warn>
```

`bible` is the number of `new` and `stale` lines in the fold file. `ledger` is the number of ledger
statuses you set. The showrunner acts on that line alone, and nobody else reads your final
message: what you did is in the files you wrote, so a recap after the line is lost. If the fold
file cannot be written, put its lines after the status line instead.
