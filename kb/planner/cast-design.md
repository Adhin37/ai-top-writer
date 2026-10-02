---
type: howto
title: Designing the cast
description: How to design a protagonist and a cast that generate scenes (a want and a need, edges to their competence, a gift whose cost comes from how it works, voices that differ as minds), and how each one moves.
roles: [planner]
---
# Designing the cast

A character generates scenes through their **edges**: what they want and cannot get, what they are
good at and where it stops, what they misread. The protagonist has a want (concrete, on the page), a
need (what they must learn, usually against the want), two blind spots, and at most three domains of
real competence; everything else they must ask about, guess at or get wrong. A gift's cost comes
from how the gift works, never from a stock list. Each speaker's row in `bible/cast/_voices.md`
makes them a different mind, not a different name.

## Examples

### A gift and its cost

**A stock cost, which would fit any gift:**

> Gift: Tovi can hear a pipe about to fail. Cost: nosebleeds and dizziness after use.

**A cost derived from the gift:**

> Gift: Tovi can hear a pipe about to fail, by listening through her own body pressed to the metal.
> Cost: what she hears, she hears for hours. After a long listen every hum on the Stack sounds like
> a failure, and she cannot tell a real alarm from the echo until she has slept.

Test it: would the same cost fit any other gift? If yes, derive again. The second cost also makes
plot (she is worst at her job right after she was best at it).

### Edges, not a generalist

```
Tovi Brand   domains: pressure systems (expert, to the edge of Deck Nine's processors, which she
             has never touched) · ladder-and-rope rescue (journeyman) · Stack labour law (passable:
             knows her own grade's rules, not the appeals process)
             blind spots: reading a superior's real motive · pricing her own work
```

Everything off the list is `none`. That is what gives her people to ask and things to get wrong.

### Two gifts that are not the same gift

Intelligence (how fast someone reasons) and reading people (how well they read others) are separate
rows. A sharp mind that misreads the powerful is a character; a slow reasoner who reads everyone
is the best ally a protagonist can have.

### A voice row that differs from the protagonist's

| character | intel | eq | artic | wit | heat | turn | hands | cadence |
|---|---|---|---|---|---|---|---|---|
| Tovi | 3 | 2 | 3 | dry | banked | ~15 | grips the nearest rail | builds, then stops short |
| Kell | 3 | 4 | 5 | none | flat | ~35 | folds a rag in thirds | long, even, never hurried |
| Ossie | 2 | 3 | 2 | warm | quick | ~25 | fidgets with the kit strap | talks past his point |

Check: someone above the protagonist on each axis and someone below; no two rows alike on both
intelligence and reading people; at most two with wit; every cadence different.

### A profile

One file per character who carries scenes, `bible/cast/<name-slug>.md`. The frontmatter's `name`
is how the tools find them.

```markdown
---
name: "Tovi Brand"
role: protagonist
first_appears: 1
---
# Tovi Brand

seen      a fitter's coveralls patched at both knees; the Stack reads her as a pair of hands
wants     her grade back, before day thirty-one
needs     to stop proving she is useful before she lets anyone help her
edges     domains: pressure systems · rope rescue · her own grade's rules | blind: a superior's
          motive · pricing her own work
gift      hears a pipe about to fail through her own body pressed to the metal | cost: hears it for
          hours after, and cannot tell a real alarm from the echo until she sleeps | limit: only
          metal she can touch | known by: nobody
voice     _voices.md row
moves     takes help for the first time when the deep crew's first shift goes wrong (arc 1)
```

An antagonist's profile replaces `gift` with `case`: their argument for what they do, as they
would make it.

### A walk-on is one line

```
the stores clerk — Deck Four stores — ch 2
  wants: the chits signed before the bell | tic: never looks up | carries: every clamp on the deck
  passes his counter | voice: answers in four words
```

Promote them to a profile on a third appearance, or when they make a decision that moves the plot.

### How a character moves

A belief moves one rung at a time, and only on a trigger: a cost paid, a contradiction witnessed,
the old method failing, being seen. It can slip back under pressure for a scene, visibly. A
character who changes because chapters passed has not changed.

## When to break it

A character whose purpose is to be a wall (an institution's face, a clerk who says no) can be one
line forever. Give them the line, and let their single stroke be specific.
