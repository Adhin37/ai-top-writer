---
type: reference
title: The canon dossier
description: The sections of bible/canon.md and what goes in each, with an example from an invented source work; the planner designs from it and the continuity editor checks chapters against it.
roles: [canon-researcher, planner, continuity-editor]
---
# The canon dossier — `bible/canon.md`

One file, in this order. Tables where `tools/scaffold.py check` reads them: the column names are
load-bearing, the headings may be edited. Every row and fact line ends on its source ids.

| section | what goes in it |
|---|---|
| `## Scope` | `works`, `versions` (which wins), `start` (where on canon's timeline), `divergence` (left to the planner) |
| `## Cast` | a table: name · age at start · status at start · looks · power and limits · ties · manner · first appears · source |
| `## World` | one fact a line: the rules, the factions, the places, distances and travel times when canon gives them |
| `## Timeline` | a table: when · event · ages then · source. Around the start, and what canon does after it |
| `## Terms` | a table: canonical · what it is · never write as · source. Spellings, ranks, honorifics, the translation's choices |
| `## Conflicts` | where sources disagree: who says what, which wins, why |
| `## Fans expect` | who fans will look for, the dynamics they love or hate, canon pairings, fanon (labelled), what fics in this fandom get attacked for |
| `## Unsure` | each fact you could not source, as a question the user can answer |
| `## Sources` | a table: id · where · what. A URL, or a path under `work/canon/` |

**Ages are at the story's start.** Canon gives an age at some moment; work out the age at `start`
from the timeline and say how (`16 at entry, start is one year later`). An age you cannot work out
goes under `## Unsure`.

**Manner is characterisation in your words:** how they talk, what they never do, how they treat
the people around them. It is what a fan checks first in a scene, and the planner's only guide to
writing them in character.

## Example

The source work is invented: *Ashfall Academy*, a web novel (and its anime) about a mage academy
on a volcano's flank.

```markdown
# Canon — Ashfall Academy

## Scope
works      the web novel, chapters 1–212 (volumes 1–4); the anime only where it adds nothing new
versions   the web novel wins; the anime's changes are listed under Conflicts
start      the first week of Corin's second year, one month before the Ember Trials (ch 58)
divergence (the planner's)

## Cast
| name | age at start | status at start | looks | power and limits | ties | manner | first appears | source |
|---|---|---|---|---|---|---|---|---|
| Corin Dask | 16 (15 at entry, ch 1; start is a year later) | alive; second-year, ranked 31st | short, ash-grey hair from his first burn | heat-sense; can't cast while touching metal | Tam Rook (roommate); Ilse Maro (sponsor) | deflects with jokes; never asks for help; keeps score of debts | ch 1 | S1, S2 |
| Ilse Maro | 54? (the wiki's estimate; Unsure) | alive; headmistress | — | ward-weaving; the wards answer to her alone | sponsors Corin; owes the Council | speaks in rules; kind only in private | ch 3 | S3 |
| Tam Rook | 17 | alive; dies in the Trials (ch 71) | tall, burn-scarred left hand | none of note; brews remedies | Corin's roommate | loud, loyal, the first to volunteer | ch 2 | S1, S4 |

## World
- casting draws heat from the caster's blood; three casts in a row bring fever · S2
- the academy to the capital: four days by mule road, one by the Council's lift · S5

## Timeline
| when | event | ages then | source |
|---|---|---|---|
| year 1, autumn | Corin enters, last of his intake | Corin 15 | S1 |
| year 2, winter (ch 58–74) | the Ember Trials; Tam dies in the third round | Corin 16, Tam 17 | S4 |

## Terms
| canonical | what it is | never write as | source |
|---|---|---|---|
| the Ember Trials | the second-year ranking tournament | Ember Trial, the Trials of Ember | S4 |
| Headmistress | Ilse's title; students never use her name to her face | Principal | S3 |

## Conflicts
- Tam's death: the novel kills him in the third round (S4); the anime spares him (S6). Novel wins.

## Fans expect
- Corin and Tam's friendship is the fandom's favourite thing; fics that sideline Tam are criticised.
- fanon: Ilse is Corin's grandmother. Never stated in canon (S3 notes the theory and the author's
  "no comment"). Do not state it as fact.

## Unsure
- Ilse's age: canon never gives it; 54 is the wiki's estimate from her graduation year. Is it right?

## Sources
| id | where | what |
|---|---|---|
| S1 | https://ashfall.fandom.com/wiki/Corin_Dask | the wiki's character page, cites chapters |
| S2 | https://ashfall.fandom.com/wiki/Casting | the magic system |
| S3 | https://ashfall.fandom.com/wiki/Ilse_Maro | the headmistress |
| S4 | https://ashfall.fandom.com/wiki/Ember_Trials | the arc, by chapter |
| S5 | work/canon/inbox/ch-040.md | the chapter the user saved |
| S6 | https://ashfall.fandom.com/wiki/Anime_differences | the anime's changes |
```

The age column shows its working; a planner reading `16` alone could not tell whether it was
checked. The wiki's estimate for Ilse is marked and asked, not passed off as canon.
