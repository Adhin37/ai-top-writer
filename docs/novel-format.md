# Novel format

A novel is a directory, `novels/<slug>/`. `novels/` is gitignored: the book belongs to whoever ran
the tool, and the toolkit deliberately manages no version control or backups for it.

`novels/_template/` is this format with every value a `{{…}}` placeholder. `/new` copies it
(`python3 tools/scaffold.py new <slug>`), the planner's init interview fills it
([kb/planner/init.md](../kb/planner/init.md)), and `python3 tools/scaffold.py check
novels/<slug>` reports what is left. The slice novel of plans 01–03 predates the template: its
`novel.md` is skilled-writer run #6's, and its plan's `hook` column holds the last line, not its
kind.

```
novels/<slug>/
  novel.md                config (YAML frontmatter) + blurb + style anchor (below)
  bible/
    premise.md            what a reader must hold, in plain words (below)
    world.md              setting, places, distances, factions, the rules of the world
    society.md            labour, money, law, belief — the central rule reaching ordinary life
    lexicon.md            spellings, terms, forms of address, number style
    canon.md              fan fiction only: the canon researcher's sourced dossier of the source
                          work (kb/canon-researcher/canon-format.md)
    cast/_voices.md       one row per speaker: intel, eq, articulacy, wit, heat, cadence
    cast/<name>.md        profiles for major characters
    cast/_extras.md       one line per walk-on
  plan/
    arcs.md               arc-level design, including when the antagonist reaches the page
    chapters.md           one row per chapter: title, pov, temp, hook, goal, obstacle, turn, event,
                          cost, keeps, threads
    reader-ledger.md      facts, faces and promises owed to the reader, by chapter (below)
    timeline.md           the world's clock: what the opposition and the world do on their own
  state/                  written by the clerk after each accepted chapter (below)
    continuity.md         one short block per chapter: event, where everyone is, who knows what
    threads.md            the thread board: the plan's thread ids, opened / last touched / status
    timeline.md           the in-world calendar
    scenes.md             one row per scene: chapter, who, where, tempo, two-hander
  work/init/              the init interview: round-N.md (questions, then the answers verbatim),
                          style-beat.md, style-samples.md
  work/canon/             fan fiction: src/<wiki>/ (pages tools/canon_fetch.py cached, the
                          dossier's evidence) and inbox/ (pages or notes the user saved)
  work/chNNNN/            the loop's hand-off files for the chapter in progress — beat sheet,
                          drafts per round, the writer's facts file per round, the continuity
                          editor's file and lint report per round, the history report per
                          round from ch 3 (tools/history.py), editor notes, the clerk's
                          fold file. Written in the wire format (kb/shared/wire.md). Overwritten
                          per chapter; not a backup
  chapters/NNNN-<slug>.md the accepted chapters
```

## `novel.md`

The frontmatter keeps a key only if a role or a tool reads it: `title` and `slug`; `platform` and
`exposition` (`clear`: every premise fact lands by chapter 1, the default on Royal Road and
webnovel.com); `genre`; `narration` and `pov` (the writer, the format spec, lint); `tone` (the
writer, the story editor); `channels` (lint and the text tools); `mc.name` and `mc.foreknowledge`;
`opening.promise` and `opening.contract_by_ch` (the antagonist's face is on the page by then);
`content` (rating, romance, hard limits); `optional` (the modules each role's index switches on);
in fan fiction, `canon` (the source work, the scope, where the story starts on canon's timeline,
who must appear: round 1's answers, which the canon researcher reads).

The body has two sections: `# Blurb` (the platform listing, 60–120 words) and `# Style anchor`,
the sample the user chose in init's round 5, verbatim. The style anchor is the voice every chapter
is written in; it replaces naming authors to imitate.

## `bible/premise.md`

The part of the bible a reader must hold by the end of chapter 1, in words a reader could repeat.
Written by the planner, **restating** the bible — every fact cites its source line, and a fact with
no source is an invented fact.

```markdown
---
type: reference
title: Premise
---
# Premise

## In one breath
<Two or three sentences a reader could say to a friend: what is different about this world and how
it works, who the protagonist is and what they want, and what stands in the way.>

## Load-bearing facts
| id | fact, in plain words | source |
|---|---|---|
| P1 | <the world's central rule — how it works, not just its name> | bible/world.md §Premise |
| P2 | <who holds power because of it> | bible/world.md §Factions |
| P3 | <the protagonist's place in it and what they want> | novel.md mc |
| P4 | <what they stand to lose> | ... |
```

Three to seven facts. Coined terms appear only glossed ("the Reading — the rite that says where the
roads will lie after the thaw").

## `plan/reader-ledger.md`

What the page owes the reader, and when. The planner schedules it; the story editor grades the beta
reader's retell against the rows due this chapter; the clerk marks what landed.

```markdown
# Reader ledger

## Facts
| id | fact, in plain words | due by ch | how it lands | status |
|---|---|---|---|---|
| P1 | ... | 1 | the rule costs someone on the page, stated in one plain sentence | owed |

## Faces
| id | who | why the reader needs them | on the page by ch | status |
|---|---|---|---|---|
| A1 | the antagonist | the opposition needs a person, not a letterhead | 3 | owed |

## Promises
| id | what the page promises | made in ch | paid by ch | status |
|---|---|---|---|---|
```

**Status** is `owed`, `landed chN`, `partly chN` (with what is missing), or `moved to chN` (with the
reason). Every premise fact is due by chapter 1 on webnovel platforms (the standing decision).

## The beat sheet — `work/chNNNN/beats.md`

```markdown
# Ch N — "<title>"
event    <one clause a reader could retell: concrete verb, a target>
temp     <fast|tense|loud|warm|funny|bleak|procedural|quiet>    hook <reveal|arrival|decision|question|threat|reversal|cliff|quiet>
learns   P1, P2 (+ how each lands, one line each)
faces    <who is introduced, and the one stroke that places them>
promises made: <…>   paid: <…>
cost     <what the protagonist loses or spends>
keeps    <one thing in this chapter worth the price — small, unearned counts>
voices   <speaker → bible/cast/…>

## Scene 1 — <place>; <who>
goal / obstacle / turn
- <beats in story language, in order: what happens>
- reader learns: <ledger ids, and the moment each lands>
- feel: <what the reader should feel by the end of the scene>

## Scene 2 — …

## Ending
<the last beat and the question it leaves>
```

## `state/`

What is true *now*, after the last accepted chapter, and who knows it. The clerk writes it; the
continuity editor checks each draft against it; the planner and the story editor read what the last
page promised. The full format, with examples, is agent-facing:
[kb/shared/state-format.md](../kb/shared/state-format.md). `tools/state_check.py` checks that the
files agree with the chapters, the plan and each other.

A continuity block is a header and seven keyed lines at most. It replaces skilled-writer's CCS
block (up to 18 lines, with lines that existed to prove a gate had run):

```
=C0003= day 12, dusk to night | words 2410
ev    Nessa rows the Harrow boy out past the bar alone, against the harbourmaster's order
at    Nessa: the boathouse · Quell: the harbour office · Tam: the quay steps
kno   Nessa+ the tally was signed before the boy drowned (the date on it) · Quell? suspects she has seen it
has   Nessa: the Harrow tally, folded in her boot · Tam: the boathouse key
cost  Nessa: two fingers frostbitten, no grip in her left hand for days
thr   ^T2 ~T4
hook  Quell's lamp is lit in the office window when she comes back in
```

`kno` carries each item's source, so a character can be caught stating what they could not know.
`hook` is what the last page promised; the next chapter plays it, pays it or turns it on purpose.

After the block, the clerk lists the chapter's new facts in `work/chNNNN/fold.md`, and the planner
folds them into the bible. The clerk never edits `bible/`.

## The reader's folder — `reading/<id>/`

The beta reader's serial memory, one folder per novel, outside the novel (`tools/reading.py`).
`<id>` is neutral, so the reader's path does not name the book; `tools/clean.py` lists which novel
each folder belongs to, and removes it with its novel.

```
reading/<id>/
  shelf/                  the accepted chapters, prose only, and the reader's memory
    ch01.md … chNN.md
    notes.md              in the reader's own words, under 800 words; the reader compresses it
  chNN-rK/                one draft round's view: a copy of notes.md, the last two accepted
    notes.md              chapters, and the draft. The round's fresh reader updates notes.md
    chNN-2.md, chNN-1.md  here, and its report is filed here. Only the accepted round's notes
    pending/chNN.md       are copied onto the shelf (by the clerk, byte for byte)
    report.md
  fresh-chNN/             every 10 chapters: ch01 … chNN and no notes; a fresh reader's notes
                          replace the running ones
```

## Chapter files

Minimal frontmatter: `number`, `title`, `pov`, `words` (measured, never a target). **No intent
fields** — `event`, `delivers` and the like live in the beat sheet, because anything in a chapter
file can reach a reader, and in skilled-writer run #6 it did.
