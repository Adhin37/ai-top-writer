---
type: catalog
title: Who could know it
description: How to check that every fact a character states, and every inference the narration makes, has a source the character actually had.
roles: [continuity-editor]
---
# Who could know it

For every fact a character states or acts on, there is a way they know it: they were **taught** it,
they **did** it, someone **told** them, they **read** it, or they are **guessing** openly. If none of
the five fits, they cannot say the line; the author knows it and the character does not. The
blocks' `kno` lines in `state/continuity.md` say who learned what and how; the chapters before say
the rest. Being clever is not a source.

## Patterns

### The fact nobody told them

> Draft: "Ossie said the recruiter had sent nine crews down this year."
> C0003 kno: "Tovi+ nine crews this year (the recruitment ledger, read on Deck Seven)"

Tovi read it alone. Ossie has no source, unless the draft shows her telling him.

```
F1 know  "the recruiter had sent nine crews down this year" | C0003 kno: "Tovi+ nine crews (the recruitment ledger)" | Ossie was not there and nobody tells him on the page
```

### The narration that knows too much

> Kell had already decided to strike her grade before she walked in.

In a limited viewpoint the narration knows what its character can see, hear, remember or infer.
Tovi cannot know when Kell decided. It is a finding when the viewpoint is limited, because the
reader takes it as fact.

### The expert outside their trade

> The fitter glanced at the chit and said the ink was a forger's ink.

A fitter knows pipes. Unless their profile or an earlier chapter gives them a reason to know ink,
this is the author's knowledge in her mouth. The fix is often one word: "looks wrong to me".

### The guess said as fact

> "The pump's going to fail on the third shift."

If the page shows how she'd know (she's heard the pitch change before, she read the maintenance log),
it holds. If not, a guess said flat is a provenance break; said as a guess ("I'd bet the third
shift") it is fine, and a flag the reader will remember if it turns out wrong.

### Knowing the future

When `novel.md` gives the protagonist foreknowledge, that is a sixth source, bounded by what the
bible says they remember and how precisely. An unlisted item is not "probably fine". And remembering
that a skill exists is not being able to do it.

## When it does not apply

A fact everyone in the setting knows (the shift bell, the price of a meal, who runs the deck) needs
no source. If you are unsure whether it is common knowledge, the bible's society file usually says.
