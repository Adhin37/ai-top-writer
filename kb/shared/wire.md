---
type: reference
title: Wire format
description: How roles write for each other — the one status line that ends a turn, and the keyed lines of a notes, facts or ledger file.
roles: [planner, writer, story-editor, line-editor, continuity-editor, clerk, showrunner]
---
# Wire format

What one role writes for another is read by a model that already has the premise, the ledger and
the beat sheet open, and by a tool that parses it. No person reads it. So it carries only what its
reader does not already hold, one item per line.

Not wire: prose, and anything addressed to the user. Those are written in full.

## The rules

1. **Your final message is one status line**, `VERB <path> | key value | …`, in the form your
   prompt gives. The showrunner acts on that line alone, so a summary around it reaches nobody who
   can use it. Anything another role needs goes in a file.
2. **Refer, don't restate.** A fact is its id (P1, F15, R5), a note its number (N2), a file its
   path. Your reader has them open.
3. **Quote to locate.** The fewest words that find the passage, about twelve. One quote per point.
4. **One item per line, `key value`.** Fragments are fine. No preamble, no recap, no bold, and no
   headings beyond your template's.
5. **Judgement stays a plain clause.** The effect on the reader, a stet's reason, why a passage
   should be kept: the next role acts on these. Shorten them, but never into something that could
   mean two things.
6. **Information goes to the role that uses it**, in the file that role reads. An observation for
   the planner goes in the notes file's *For the planner* section, not in your final message.

## Example

The world is invented: a harbour town where the sea returns its drowned once a year.

The same note in prose, about 120 words:

> **N1 — the Ebb is never explained**
> where: "Ysolde had four hours until the Long Ebb, and the Calder boy was still on the tally."
> evidence: the reader's retell says "some kind of tide festival (guess)"; *Long Ebb* and *tally*
> are both on their guessed-terms list; owed item P1 (the sea returns the drowned, who must be
> rowed out by dawn) graded **missing**.
> effect: the reader did not know the boy on the tally was dead, so the chapter's last scene — his
> mother refusing to come down to the water — read as a family quarrel, not a grief.
> direction: the rule, in plain words, the first time the tally is named.

As wire, about 70 words:

```
N1 Ebb never explained
where "Ysolde had four hours until the Long Ebb, and the Calder boy was still on the tally."
ev    P1 missing · retell "some kind of tide festival (guess)" · guessed: Long Ebb, tally
eff   the reader didn't know the boy was dead, so the last scene read as a family quarrel, not grief
dir   the rule in plain words where the tally is first named
```

What went:
- P1, restated in full; the writer has `premise.md`;
- the mother's scene, described back to the writer who wrote it;
- the emphasis.

What stayed: the quote that finds the passage, the evidence, and the effect as a whole clause.

A final message, the same both ways:

```
NOTES READY novels/tidewater/work/ch0003/notes-r0.md | REVISE | notes 2 | owed 4/5
```

The prose version opened *"Chapter 3, round 0: the verdict is **REVISE**, with two notes. The
chapter is close…"* and ran three hundred words before reaching that line.

## Status lines

| role | final message |
|---|---|
| planner | `PLANNER DONE <task> \| <file>, <file> \| gaps <n> \| changed <n>`, then one `gap <…>` or `changed <…>` line each |
| planner, an init round that asks the user | `PLANNER ASKS <round file> \| round <n> \| questions <n>` |
| writer | `DRAFT READY <draft> \| facts <facts file> \| new <n> \| stets <n> \| couldn't <n>` |
| writer, style samples for a new novel | `SAMPLES READY <samples file> \| samples <n>` |
| story editor | `NOTES READY <notes file> \| ACCEPT or REVISE \| notes <n> \| owed <stated>/<due>` |
| line editor | `POLISHED <path> \| changes <n> (<the top three>) \| left <n>`, then one `left <…>` or `across <…>` line each |
| continuity editor | `CONTINUITY READY <continuity file> \| findings <n> \| lint <lint file>` |
| clerk | `CLERK DONE <chapter> \| fold <fold file> \| bible <n> \| ledger <n> \| check <result>` |
