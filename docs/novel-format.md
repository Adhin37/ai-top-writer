# Novel format

A novel is a directory, `novels/<slug>/`. `novels/` is gitignored: the book belongs to whoever ran
the tool, and the toolkit deliberately manages no version control or backups for it.

This is the **target** format. Session 2 runs on skilled-writer run #6's bible as it stands, plus
the two files marked **new**; plan 04 builds the template.

```
novels/<slug>/
  novel.md                config (YAML frontmatter) + premise paragraph + blurb
  bible/
    premise.md            NEW — what a reader must hold, in plain words (below)
    world.md              setting, places, distances, factions, the rules of the world
    society.md            labour, money, law, belief — the central rule reaching ordinary life
    lexicon.md            spellings, terms, forms of address, number style
    cast/_voices.md       one row per speaker: intel, eq, articulacy, wit, heat, cadence
    cast/<name>.md        profiles for major characters
    cast/_extras.md       one line per walk-on
  plan/
    arcs.md               arc-level design, including when the antagonist reaches the page
    chapters.md           one row per chapter: title, pov, temp, hook, goal, obstacle, turn, event, cost
    reader-ledger.md      NEW — facts, faces and promises owed to the reader, by chapter (below)
  state/
    continuity.md         one short block per chapter (plan 02 defines it)
    threads.md            open promises and foreshadowing, with ages
    timeline.md           the in-world calendar
    scenes.md             one row per scene: chapter, who, where, tempo (plan 02)
  work/chNNNN/            the loop's hand-off files for the chapter in progress — beat sheet,
                          drafts per round, editor notes. Overwritten per chapter; not a backup
  chapters/NNNN-<slug>.md the accepted chapters
```

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

## Chapter files

Minimal frontmatter: `number`, `title`, `pov`, `words` (measured, never a target). **No intent
fields** — `event`, `delivers` and the like live in the beat sheet, because anything in a chapter
file can reach a reader, and in skilled-writer run #6 it did.
