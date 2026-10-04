# 00 — Diagnosis: why the rebuild

Written 2026-09-26, after skilled-writer's benchmark run #6. It records why the old toolkit was
retired rather than patched, and it is the evidence behind every decision in
[architecture.md](../architecture.md). Old-repo paths are relative to
`../skilled-writer/`.

## What happened

Run #6 wrote five chapters of *The Unwritten Surveyor* through a role pipeline:

1. an architect built the bible and plan;
2. a cold drafter wrote a 13-line brief, then the prose;
3. a gate ran 19 audit cards and made line edits;
4. the drafter wrote the state files.

Every instrument reported **0 defects**. A blind reader (Opus) scored it **3.5 / 5**.

The user opened chapter 1 and was lost. They had seen the same failure in earlier runs. Its second
paragraph introduces *the Charter*, *the Guild of Chain and Stone*, *House Calder's Reading*, chains
and links, *the orphan stone* and *marker nine*, and none of them is explained. The chapter goes on
to add *Calderhold*, *the Fallow*, *Reading Day*, *Threnn* and the *spring assizes*. By its last line
a reader cannot say why eleven links matters.

The premise is the first paragraph of the novel's own bible (`novels/unwritten-surveyor/bible/world.md`):

> Threnn is a mountain marcher country where no road survives a winter unchanged: the range
> resettles itself every winter, and only House Calder — through a rite called the Reading,
> performed once at midwinter by the sitting head of the House — can say in advance where the paths
> will lie. That reading is law.

**No sentence of that reaches chapters 1–5.** The reader ranked "the Reading is never shown" sixth of
eight findings. The same complaint was run #1's finding #1/10. It was marked fixed, with rules, and
it came back.

## Why no step flagged it

**1. Every agent in the loop already knew the world.** The architect, drafter and gate all load the
bible. A reviewer who knows what the Reading is cannot notice that the page never says. The only
agent without the bible was the benchmark reader, which ran once, after five chapters, outside the
loop. Its findings became rule patches for the *next* run, never a fix to *this* chapter.

**2. The one cold reader was contaminated.**
- Chapter frontmatter carries the author's intent, and the reader read chapter files whole.
- Chapter 1's frontmatter says `delivers: "the reader sees the Charter/Guild/Reading system work
  exactly as designed…"`.
- The reader also saw the directory name ("I had 'surveyor' and 'unwritten' in mind before reading a
  word"), and the do-not-open table told it scores existed.
- A reader handed the author's intent cannot measure whether the page delivers it.

**3. The corpus argued against orientation.** About ten rules pushed against exposition. Among them:
- "enter scenes in motion";
- "no establishing paragraphs";
- "the world is delivered, not described";
- a description budget;
- `roles/draft/story-opening.draft-card.md`: "**Spend one, not four**" world facts per chapter;
- `roles/draft/story-opening.chapter-one.md`: first 20% of chapter 1 is "Disruption … never
  weather".

One soft test pushed the other way ("a reader can say what kind of world this is"). The drafter
obeyed the majority. The architect also chose Le Guin and *The Tainted Cup* as the style target,
both literary withholding, for a book aimed at Royal Road.

**4. Nothing modelled what the reader knows.** The toolkit tracked what *characters* know
(`competence-map`, `meta-knowledge`), never the reader. The plan's `world entry` column for rows
1–5 scheduled derived facts:
- a sealed number outranks the ground;
- a failed road renewal;
- the licensing ladder;
- a watch flag;
- what stone-reckoning costs.

**No row scheduled the premise itself.** The drafter delivered its row, and the gate checked the
chapter against the row.

**5. The gate edited at line level.**
- Its 14 edits on chapter 1 (`run6-artifacts/ch1-pregate.md` against `ch1-postgate.md`) were all
  verbal tics: thought tags, a shrug, the "its own kind of" closer.
- Pass 9b, the anchor test, passed, because the gate knew the world.

**6. Every fix added rules.**
- Each run's findings became more card text. Post-run #6, finding 6 got one more sentence in an
  audit card, the same fix that had failed before.
- For chapter 6, `sw load` counts Phase A alone at **13 cards, 7,650 words and 208 negations**.
- On top of that sit a 7,000-word agent contract and a 30–40k-character read-set. The corpus totals
  about 73k words of skill bodies, 84k of cards and 32k of contracts.
- A drafter holding about thirty simultaneous constraints spends its time reconciling them. Phase A
  once spent 386 s in a single 30k-token thinking turn. The user's session effort was high
  throughout, so effort was not the cause. The load was.

## What the research says

- **Examples beat rule lists; use the smallest set of high-signal tokens.** Anthropic, [Effective
  context engineering for AI agents](https://www.anthropic.com/engineering/effective-context-engineering-for-ai-agents):
  "examples are the 'pictures' worth a thousand words"; attention is a budget. Anthropic's model
  guidance adds that prompts written for older models are often too prescriptive and reduce output
  quality.
- **Planning agents and writing agents, with an orchestrator.** [Agents' Room (arXiv 2410.02603)](https://arxiv.org/abs/2410.02603)
  splits planners (character, conflict, setting) from writers and shares a scratchpad between them.
  [StoryWriter (arXiv 2506.16445)](https://arxiv.org/abs/2506.16445) chains outline, then
  per-chapter planning, then writing.
- **Critics are generic by default.** [Constructive feedback on stories (arXiv 2609.04824)](https://arxiv.org/abs/2609.04824):
  LLM story feedback tends to be generic, not actionable, and unprioritised. Actionability is the
  main driver of useful feedback.
- **One level of disclosure.** [Progressive disclosure for long-context agents (arXiv 2607.17598)](https://arxiv.org/pdf/2607.17598):
  an index leading to documents helps once a corpus is too large to read. A second routing level
  "never helps and sometimes breaks accuracy outright".
- **LLM judges agree with human preference on creative writing only about 73% of the time**, and are
  biased by position, length and formatting (skilled-writer `docs/design-notes.md`). A judge may
  locate and describe. It may not gate.
- **Agent teams in Claude Code** are experimental. Teammates load CLAUDE.md and every skill, and do
  not spawn in non-interactive mode ([docs](https://code.claude.com/docs/en/agent-teams)). Named
  subagents with `SendMessage` need none of that ([docs](https://code.claude.com/docs/en/sub-agents)).

## OKF, revisited

The old repo argued that [Open Knowledge Format](http://okf.md/spec/) was an export target, not a
working format. Half of that still holds, and half does not.

| | verdict |
|---|---|
| **Novel state** (`bible/`, `plan/`, `state/`) | **Still not OKF.** A role gets a *slice* (the last five ledger blocks, this chapter's plan row, these speakers' voice rows), and OKF hands over whole files |
| **Craft knowledge** | **OKF, per role.** Each role gets a small bundle: `index.md` preloaded, typed documents opened on demand, one level of disclosure |

The honest caveat: the old repo had already half-adopted OKF-style typed frontmatter in its role
trees, and quality did not move. **The format was never the problem; the content was.** It was about
190k words of rules and prohibitions, each carrying the history of the run that produced it. So the
knowledge bases are rewritten example-first ([plan 03](03-knowledge-bases.md)), not migrated.

## What the rebuild changes, and what it keeps

| old | new | why |
|---|---|---|
| one drafter holds the rules and polices itself | the **writer** gets intent, examples and a format spec; **critics** hold the rules | a writer juggling thirty constraints writes defensively and slowly |
| gate at line level, knows the world | **beta reader** with no bible, every chapter, in the loop; **story editor** turns its evidence into notes | the curse of knowledge (finding 1) |
| benchmark reader sees frontmatter and slug | **prose-only export** to a neutral path | contamination (finding 2) |
| characters' knowledge tracked, the reader's not | **premise** and **reader ledger** (facts, faces, promises), plus the reader's own **notes** | finding 4 |
| findings become rules | findings become an **example**, a **ledger entry**, or a rule that **replaces** one | finding 6 |
| Sonnet everywhere, "tuned for low effort" | **Opus** for planner, writer, story editor, judge; **Sonnet** for the rest | quality first (the user) |
| 44 skills, 119 cards, routing, budgets, health checks | about 8 roles, one OKF bundle each | finding 6 |

**Kept:**
- the novel directory idea (config, bible, plan, state);
- the countable checks that caught real defects (lint, state ordering, cross-chapter repetition),
  ported as tools the critics run;
- the benchmark discipline (blind reader, coordinator writes nothing, reconcile findings against the
  page).

The lessons that still apply, with their evidence, are in [lessons.md](../lessons.md).
