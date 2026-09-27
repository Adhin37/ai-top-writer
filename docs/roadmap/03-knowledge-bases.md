# 03 — Session 4: the knowledge bases

**Goal:** give each role a small, example-first knowledge base in OKF format, distilled from what
skilled-writer knew. This replaces the 44 skills, the 119 cards, and the machinery that routed them.

**Why now, and not first:** plans 01–02 will have shown what each role actually needed and what it
ignored. That comes from the session logs, the agents' notes, and the showrunner's prompt edits.
Writing the knowledge bases before any loop ran would repeat the old mistake of rules written for a
pipeline nobody had run.

## The shape of a knowledge base

```
kb/<role>/
  index.md      the role's map. Preloaded (the prompt tells the agent to read it first). One line per
                doc: link, what it is for, and when to open it. No frontmatter (OKF reserved file)
  prompt.md     the role's procedure: inputs, outputs, steps. The agent file points here
  <doc>.md      one topic each, OKF frontmatter, opened on demand
kb/shared/      docs more than one role opens (the format spec, the glossary). A role's index links
                the shared docs it uses
```

- **One level of disclosure.** A role goes index → doc and never index → sub-index → doc. A second
  level "never helps and sometimes breaks accuracy" (arXiv 2607.17598).
- **OKF frontmatter.** `type` is required; `title` and `description` are recommended. The types used
  here are:
  - `howto`: how to do one thing;
  - `example`: worked examples;
  - `reference`: facts and formats;
  - `protocol`: a procedure with inputs and outputs;
  - `catalog`: a list of patterns, for critics.

  Two custom keys are allowed: `roles:` (who opens it) and `toggle:` (the `novel.md` key that
  switches it on, for optional modules). OKF says consumers keep unknown keys.

**Every craft doc follows this template:**

```markdown
---
type: howto
title: <topic>
description: <one sentence: what a reader of the doc can do afterwards>
---
# <topic>

<The idea in three sentences or fewer.>

## Examples
<Two or three worked examples: the version that works, and a flat version beside it with one
line on the difference. Invented, genre-neutral nouns.>

## When to break it
<The case where the chapter is better without this.>
```

**How to write a doc:**
- **Prefer examples to rules.** A doc that grows by adding "don't" lines is getting worse, whatever
  its length. `tools/kb_check.py` prints each doc's negation count so the trend is visible. It is a
  number to watch, never a limit.
- **Keep history out.** "Run #4 shipped…" belongs in `docs/lessons.md`, never in a knowledge base. An
  agent reading why a rule exists is spending attention on the past.
- **Output templates are wire; teaching stays prose.** A `prompt.md` that defines what a role hands
  back links `kb/shared/wire.md` (from 01b) instead of restating its rules. Craft docs keep writing
  in full sentences and examples.
- **Keep examples genre-neutral.** Use invented proper nouns and portable officialdom (an inspector, a
  toll-keeper). The last run's novel always leaks into the examples written right after it, so sweep
  for it at the end of every run.

## Steps

### 1. Map old to new

Write `docs/kb-mapping.md` first: one row per old skill, naming where its knowledge goes, or that it
is dropped and why. Starting proposal, to be revised against plans 01–02's evidence:

| role | draws from (old skills) |
|---|---|
| **planner** | novel-init, title-craft, mc-design, lead-interest, character-profile, voice-separation (the matrix), competence-map, social-perception (EQ design), story-bible, social-fabric, story-opening (the reader ledger, promise, stakes ceiling), chapter-plan, plot-threads, power-scaling, timeline-engine, conflict-engine (the stake ladder), hook-and-pacing (temperatures, arc rhythm), story-craft (build-up), character-development (arc ladders), meta-knowledge, bias-guard (structural half); genre and optional: power-system, tech-plausibility, fanfic-canon, romance-arc, mystery-clues, battle-scale, litrpg-system |
| **writer** | narrator-voice (distance, interiority, channels), dialogue-voice, scene-craft, story-craft (scene vs summary), world-texture and story-opening (orienting the reader), hook-and-pacing (openings, endings), mc-intel-meter (writing intelligence on the page); toggle-gated: combat-choreography, comedy-levity, slice-of-life-texture, grimdark-consequences, pov-switch |
| **story editor** | scene-craft (the delivery test), conflict-engine (cost and what is worth the price), story-craft (the event gets the scene), mc-intel-meter (the MC is never stupid), meta-knowledge (win before fail), plot-threads (promises), story-opening (the stakes ceiling), theme dramatized, power-scaling (the gap per chapter) |
| **continuity editor** | story-bible (facts), timeline-engine (clock, travel), competence-map (provenance), character-profile (placement at first appearance), mc-design (form ledger), the lexicon |
| **line editor** | prose-quality, mtl-detox, dialogue-voice (the spoken-register audit), voice-separation (the cadence test), narrator-voice (channel check), bias-guard (line-level half) |
| **clerk** | continuity-summary (a smaller block format), plot-threads (ledger mechanics) |
| **beta reader** | **nothing**, deliberately |
| **judge** | the questionnaire only |

`write-chapter` and `revision-pass` are replaced by the loop itself, run by the showrunner, and
have no knowledge base.

### 2. Write the bundles

- **Order:** writer → story editor → line editor → continuity editor → planner → clerk. The writer and
  story editor come first because the chapter's quality moves through them.
- **For each doc:** read the old sources, keep the best worked examples (made genre-neutral),
  rewrite the idea in three sentences, and drop the rest.
- **Expected size:** about 8–15 docs per role, most under 600 words. This is a sense of scale, not a
  limit.
- **Optional modules** (`toggle:`) sit in the role that uses them. A role's prompt says to open a
  toggled doc only when `novel.md` switches it on.
- **Bias.** The structural half (factions, cast, what the world rewards) goes to the planner. The
  line-level half (descriptions, epithets, who gets interiority) goes to the line editor. It is the
  one area whose rules stay absolute. Say so in both docs, once.

### 3. `tools/kb_check.py`, with tests

It checks:
- every non-reserved `.md` under `kb/` has parseable frontmatter with a non-empty `type` (OKF §9);
- every doc is linked from its role's `index.md`, and every index link resolves;
- every `.claude/agents/*.md` points at a `kb/<role>/prompt.md` that exists.

It also prints words and negations per doc, as information only.

### 4. Loading

Decide from plans 01–02's transcripts whether every agent actually read its `prompt.md` and
`index.md` first. If any did not, move the prompt into the agent body, rendered by a small script,
or preload it through the agent's `skills:` field. Record the decision in `docs/architecture.md`.

### 5. Prove it

Re-run chapter 4 of the slice novel through the loop with the new knowledge bases, and compare it
with chapters 2–3:
- the beta reader's click-next;
- how many REVISE rounds the story editor needed;
- whether the notes got more specific.

## Verification

- `python3 tools/kb_check.py` is clean, and tests pass.
- Every row of `docs/kb-mapping.md` names a destination or a reason for the drop.
- **A leak sweep.** `grep` the whole `kb/` for the slice novel's proper nouns (Wren, Ruck, Calder,
  Charter, Aldstead, Threnn) and for run #5's. There must be zero hits.

## Exit criteria

Chapter 4 is at least as good as chapters 2–3 by the reader's click-next, the story editor's rounds
and how specific its notes are. The knowledge bases are in place, and no role's prompt carries rules
its knowledge base now owns.

## Session log

*(filled in when this plan runs)*
