---
type: catalog
title: Time and travel
description: How to check that the days, hours and journeys on the page follow the timeline and the bible's distances, including the small time words that quietly put an earlier day into today.
roles: [continuity-editor]
---
# Time and travel

`state/timeline.md` says which day each chapter covers; each block's header says the day and time;
the bible's distance table says how long a journey takes and what slows it. Everyone has
travelled, so a reader prices a three-day journey done overnight more exactly than almost
anything else. Check the arithmetic, and read the small time words ("that afternoon", "yesterday",
"three days ago"), which carry it without looking like they do.

## Patterns

### The time word that moved a day

> Draft (day 4, evening): "She said it to the man who had carried the Harrow boy up from the water
> that afternoon."
> C0002 header: "day 3" · C0002 ev: "Doran carries the Harrow boy up from the quay"

"That afternoon", in a chapter set on day 4, says the boy was carried up today; the block says
yesterday. A reader stops, counts, and loses the line's weight. This is the slip easiest to miss,
because the sentence reads fine on its own. Read every time word against the header of the block it
points back to.

```
F1 time  "carried the Harrow boy up from the water that afternoon" | C0002 header: "day 3" | that was yesterday; this chapter is day 4
```

### The journey too fast

> Draft: "She left the quay at dawn. By noon she was at the salt pans."
> bible/world.md §Distances: "quay → salt pans: one day on foot"

```
F2 travel  "By noon she was at the salt pans" | bible/world.md §Distances: "quay to salt pans, one day on foot" | half a day, and nothing to make it faster
```

Speed is an institution: anyone faster than the table is using something someone owns (a boat, a
relay, a permit). If the draft names it, check that the bible has it.

### The count that does not add

> "Three days since the signing" in a chapter whose block says day 6, when the signing was day 1.

Recompute every "N days ago" from the block headers.

### News faster than a messenger

A character in one place knows what happened in another place that day. Check how news travels in
the bible, and whether anyone could have carried it.

## When it does not apply

A character's own sense of time may be wrong on purpose (feverish, imprisoned, grieving), and then
the narration says so or shows it. If the draft marks the confusion as the character's, there is
no finding.
