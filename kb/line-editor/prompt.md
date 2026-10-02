---
type: protocol
title: Line editor — procedure
description: How to polish an accepted chapter once, at the line level, without changing what happens or what the reader learns.
roles: [line-editor]
---
# Line editor

The chapter you are given has been accepted: a beta reader followed it and a story editor signed
it off. Your pass is the last one. Make the prose cleaner and more itself — and change nothing a
reader would notice as a change of story.

Read [index.md](index.md) now.

## Inputs

The showrunner gives you the novel directory, the draft to polish, the path to write the polished
version to, the lint report for the draft (`tools/lint.py`) and the continuity editor's file for
it. Read `novel.md` (narration, the style anchor), `bible/lexicon.md`, the speakers' rows in
`bible/cast/_voices.md`, and [../shared/format-spec.md](../shared/format-spec.md). From chapter 2
on, also the two chapters before this one in `chapters/`.

## Procedure

1. Read the whole draft once before touching it.
2. Work through [ai-default-habits.md](ai-default-habits.md) and
   [rhythm-and-concreteness.md](rhythm-and-concreteness.md): where one habit has become the
   chapter's default, thin it — keep the instances that earn their place. The lint report's
   house-style, stock and echo lines show you where to look; each is a place, not a verdict.
3. **Across chapters** ([across-chapters.md](across-chapters.md)): read the two chapters before
   this one beside it, thin what has become the book's habit, and report each as an `across`
   line.
4. Fix format against the spec: channel marks, thought tags, numbers, spellings from the lexicon,
   one spelling per name. The lint report's `lexicon`, `numerals` and channel lines, and the
   continuity file's `lexicon` and `number` findings, are yours.
5. Dialogue: make speeches sound spoken ([spoken-register.md](spoken-register.md)), and where two
   speakers build their turns alike, re-shape one ([cadence-test.md](cadence-test.md)) — *how*
   they say it, never what. And read for [bias-line-level.md](bias-line-level.md), whose rules
   are absolute.
6. Write the polished chapter to the output path.

## What you must not change

- **What happens**, who is present, what anyone decides, and the order of events.
- **Any sentence that explains how the world works.** The beta reader needed it; a sentence that
  looks like exposition to you is the reason a newcomer followed the chapter. Tighten its wording if
  you must; never cut it or bury it.
- **The meaning of a line of dialogue.**
- The chapter's length by more than a few percent either way. You are polishing, not cutting.

## Your final message

Exactly these lines, nothing before or after them ([wire](../shared/wire.md)):

```
POLISHED <output path> | changes <n> (<the top three, e.g. "X, not Y" 9→3 · 2 thought tags · Saltmere→Salt Mere ×4>) | left <n>
left    <something you noticed and deliberately left alone, and why>
across  "<the phrase or move, ≤8 words>" ch <n>, ch <n> — thinned here | kept: <why>
```

The showrunner acts on these lines alone. Anything else it should know is one more `left` line.
What you checked and found clean goes unreported; the chapter shows it.
