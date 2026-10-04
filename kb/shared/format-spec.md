---
type: reference
title: Format spec
description: The facts every chapter file follows — text channels, viewpoint and tense, numbers and spellings, and the file's own frontmatter.
roles: [writer, line-editor, story-editor, continuity-editor]
---
# Format spec

Facts, not taste. The novel's own settings in `novel.md` win wherever they differ from a default
below.

## Text channels

| channel | mark | use |
|---|---|---|
| speech | `"…"` | anything said aloud |
| direct thought | `'…'` | the viewpoint character's own words in their head, verbatim. A few per chapter, where the character is caught in the moment — never the scene's point restated for the reader. No "he thought" tag beside the marks |
| meta | `[…]` | system text, notices, documents read out whole — anything that is on the page as an object |
| free indirect | unmarked | the default for interiority: the narration takes on the character's words and attitude without marks |

The marks come from `novel.md` → `channels:`. An apostrophe inside a word is not a thought mark.

## Viewpoint and tense

From `novel.md` → `narration` and `pov`. In a limited viewpoint the narration knows what the
viewpoint character can see, hear, remember and infer — and reports other people by what they do
and say, never by what they had decided.

## Numbers, names and spellings

- Spellings, terms and forms of address: `bible/lexicon.md`. A name spelled one way stays that way.
- Numbers follow the lexicon's style line if it has one; otherwise spell out one to one hundred in
  narration and dialogue, and use numerals for measurements, dates and figures on documents.
- A figure the bible defines (a price, a distance, a duration) keeps the bible's meaning — a price
  is not reused as a length of time.

## The chapter file

```markdown
---
number: 1
title: "The Title"
pov: "Viewpoint Character"
---

First line of prose.
```

`words` is added by a tool once the chapter is accepted; drafts leave it out. Nothing else goes in
the frontmatter: no intent, no summary, no notes. Anything in a chapter file can
reach a reader. Scene breaks are a line with `* * *`. No headings inside the prose.
