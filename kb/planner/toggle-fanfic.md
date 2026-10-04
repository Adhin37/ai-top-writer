---
type: howto
title: A story in someone else's world
description: How to plan fan fiction (from the researched canon dossier, with lookups for what it lacks; one divergence point; a budget for characters acting out of their canon selves) as an original story.
roles: [planner]
toggle: genre (fanfic)
---
# A story in someone else's world

Fan fiction readers know the source better than you do: they forgive an invented city, never a
character who would not say that, or who is two years too old. Canon comes to you researched: the
canon researcher's `bible/canon.md` ([its format](../canon-researcher/canon-format.md)) holds the
scope, the cast with their ages and status at the story's start, the timeline, the terms and what
fans expect, each fact sourced. Design from it, not from memory. A canon fact you need that it
lacks is a lookup: end your message with `gap canon <the question>`, and the showrunner sends it
to the researcher. Never state a canon fact the dossier does not hold, and never quote the source
work. Plan one divergence point, where your story leaves canon, write it on the dossier's
`divergence` line, and let everything after it follow from that one change.

## Examples

### A canon fact the dossier lacks

**From memory (never):**

```
beats  sc 2: the deck chief's daughter, nine, runs the message to Deck Six
```

Nothing in `bible/canon.md` says he has a daughter, or how old she is. A fan who knows she is
twelve, or that she does not exist, stops trusting every page after.

**As a lookup:**

```
PLANNER DONE beats | work/ch0006/beats.md | gaps 1 | changed 0
gap canon does the deck chief have children before season 1; names and ages at the story's start
```

The beat waits for the answer, or the scene uses someone the dossier holds.

### One divergence

```
divergence  ch 1: the inspector who in canon dies in the Deck Six fire is not on Deck Six, because
            the protagonist moved her shift
after it    the council's audit (canon: never happens) runs, because she is alive to request it
            the deck chief (canon: promoted) is investigated instead
```

Each change downstream follows from the one before it. A second, unrelated change is a second
story.

### The departure is a premise fact

How the story leaves canon (who the protagonist is to the canon cast, how they got there, any
power or system they brought) is a premise fact, due in chapter 1 in plain words. A fan infers it
from the first page; a reader new to the source cannot.

```
premise   P1 | Mara Quill, a fitter from our world, woke in the body of the deck chief's
          youngest cadet, eight months before the canon's first season | novel.md mc · bible/canon.md §scope
ledger    P1 | premise | 1 | first scene: she knows the deck chief's name before anyone says it, and
          says to herself, plainly, whose body this is and when
```

**Signalled in asides (never):** chapters 1–4 drop hints (a word from another world, a joke about
knowing how this goes), and the plain statement waits for chapter 5. The fan enjoyed it; the new
reader spent four chapters guessing what kind of book this is.

### Characters out of character

Characters change when your story changes their circumstances, and the page shows why. A character
behaving against their canon self with no cause on the page is spending the reader's trust. Plan a
budget: a few such changes an arc, each with its cause in a scene.

### The world track as canon

What canon says happens next goes in `plan/timeline.md`, from the dossier's `## Timeline`, as your
own one-line summaries. It is the clock the protagonist's changes interrupt; the continuity editor
checks a chapter against it as against the bible.

A canon event is a stage: plan the protagonist's own errand to move inside it, so the beat pays
twice.

**A replay:**

```
ch 6   the Deck Six fire, as in canon; Mara watches the deck chief seal the bulkhead
```

**A stage:**

```
ch 6   the Deck Six fire, as in canon; Mara uses the evacuation to reach the audit office while it
       stands empty, and finds her own name in the file she came for
```

The replay is a rerun to the fan and a list of strangers to everyone else. A chapter with no
host-world event and no protagonist in it (a canon character's day, a retold story from elsewhere)
fails the skim test the same way.

## When to break it

An alternate universe that declares itself (the same characters in a different world) has no
divergence point; its canon is the characterisation alone. Say so in the scope line.
