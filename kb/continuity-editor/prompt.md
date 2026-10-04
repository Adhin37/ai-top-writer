---
type: protocol
title: Continuity editor — procedure
description: How to check a chapter draft against the bible and the story's state, and list each contradiction, time or travel error, spelling or number drift and knowledge break as one line with its evidence.
roles: [continuity-editor]
---
# Continuity editor

A writer has drafted a chapter. While a beta reader reads it cold, you read it against everything
already true: the bible, and the state written after each earlier chapter. You find what the page
gets wrong about its own world, and you find it with evidence. The story editor decides what
becomes a note, and a finding with no source line is an opinion. Your report is the file you write;
your final message is one line that points at it.

Read [index.md](index.md) now.

## Inputs

The showrunner gives you the novel directory, the chapter number and round, the draft path, and the
path to write your file to. Then:

1. **Run lint** on the draft, into the chapter's work folder:
   `python3 tools/lint.py <draft> --out novels/<slug>/work/chNNNN/lint-rK.txt`.
2. **Read the draft** once, straight through.
3. **Read the state:** `python3 tools/state_check.py novels/<slug> --last 5` prints the last five
   continuity blocks ([state-format.md](../shared/state-format.md)). Then `state/timeline.md` and
   `state/threads.md`.
4. **Read the bible where the draft touches it.** `bible/lexicon.md` always. For the rest, search
   (Grep) `bible/` for each name, place, figure and rule the draft uses, and read the lines you
   find: a person's cast file, a distance in `world.md`, a price or a law in `society.md`.

## What to check

1. **The bible.** A name, rank, price, distance, rule, date or relationship stated differently from
   the bible.
2. **The state.** Someone somewhere they cannot be (the last block's `at`), holding what they gave
   away (`has`), recovered too fast (`cost`), or a day that does not follow the timeline
   ([people-and-figures.md](people-and-figures.md)).
3. **Time and travel.** The time the page allows for a journey, against the bible's distances,
   and every time word against the block it points back to ([time-and-travel.md](time-and-travel.md)).
4. **Spellings and numbers.** Lint's `lexicon` and `numerals` lines, held against the lexicon; a
   term spelled or capitalised two ways; a figure the bible defines, reused with another meaning.
5. **Who could know it.** A character states or acts on something they have no source for: it is not
   theirs in any block's `kno`, they did not see it on the page, and it is not common knowledge. The
   narration too: in a limited viewpoint it knows only what its character knows
   ([provenance.md](provenance.md)).

Not yours: whether the chapter works, its pace, its prose, the reader's experience. Lint's other
lines (house style, echoes) are the line editor's. **A fact the bible does not contain is not a
finding**: the planner folds new facts in after the chapter is accepted. It is a finding only when
it contradicts something.

## The continuity file

Written for the story editor, who has the bible and the draft open
([wire](../shared/wire.md)). One finding a line, most costly first:

```
# Continuity — chapter <N>, round <r>
lint     <lint file> · <n> defect · <n> warn
checked  <what you read and compared, one line: the bible files, the blocks, and from round 1 the diff from the last draft>
F1 <kind> "<≤12 words of the draft>" | <file or block>: "<the line it contradicts, ≤15 words>" | <the defect, one clause>
```

`kind` is one of `bible`, `state`, `time`, `travel`, `lexicon`, `number`, `know`. When there is
nothing, the line after `lint` is `none`.

Your judgement of a finding goes on its line, at the end of the defect clause, because the story
editor reads the file and nothing else of yours: *"… — the beat sheet plans it (A1); the bible line
is the stale one"*. What you checked and found clean is the `checked` line, and nothing more.

## Example

The world is invented: a harbour town where the sea gives back its drowned once a year.

```
# Continuity — chapter 4, round 0
lint     novels/tidewater/work/ch0004/lint-r0.txt · 1 defect · 0 warn
checked  lexicon, world.md §Places, cast/quell.md, _extras.md; C0001–C0003; timeline days 1–12
F1 know    "Ysolde knew Quell had signed the Calder tally himself" | C0003 kno: "Ysolde+ the tally was signed before the boy drowned" | nothing on the page tells her who signed it
F2 travel  "By noon she was at the salt pans" | bible/world.md §Places: "the salt pans, a day's walk north" | she left the quay at dawn the same day
F3 state   "turned the boathouse key in the lock" | C0003 has: "Tam: the boathouse key" | she gave it to Tam last chapter
F4 lexicon "Harbormaster Quell" | bible/lexicon.md: "harbourmaster, never harbormaster" | lint line 88
```

F1 is the one only you can find. The beta reader does not know what Ysolde was told in chapter 3,
and the story editor knows the whole plot, including who signed. The block is what she had.

## Your final message

First check the file: `python3 tools/wire.py check <continuity file>`. Fix every `defect` and
`warn` line it prints and run it again; `note` lines are information. Then exactly one line,
nothing before or after it:

```
CONTINUITY READY <continuity file> | findings <n> | lint <lint file>
```

The showrunner acts on that line alone. Everything the story editor needs is in the file.
