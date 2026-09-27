# Architecture

A writers' room for serialized web fiction. A planner designs the story, a writer drafts each
chapter, a reader who knows nothing but the page reads it, and editors turn the reader's experience
into notes the writer revises against. The main Claude Code session is the **showrunner**: it runs
the loop and writes no prose.

Why the design is this shape, with evidence: [roadmap/00-diagnosis.md](roadmap/00-diagnosis.md).
What carries over from skilled-writer: [lessons.md](lessons.md).

## Principles

1. **Writers get intent and examples; critics get rules.** The writer holds a beat sheet, voice
   sheets, a short format spec (facts, not prohibitions) and a few worked examples. Every rule a
   chapter can break lives with exactly one critic, who checks it.
2. **A reader reads every chapter.** The beta reader has no bible, no plan and no author intent. It
   reads a prose-only export in a neutral folder and remembers earlier chapters through its own
   notes. Everyone else knows the world too well to notice what the page never says.
3. **What the reader knows is state.** The bible is the truth. `premise.md` is the part of the truth
   a reader must hold in chapter 1. The **reader ledger** schedules the facts, faces and promises the
   page owes, by chapter. The reader's **notes** record what actually landed. The gap between the
   ledger and the notes is the exposition debt, and the planner schedules it.
4. **The loop is bounded, and its notes are specific.** At most two revision rounds. At most five
   notes a round, each with a quote, the evidence behind it, and the effect on the reader. A note
   that would apply unchanged to another chapter is cut.
5. **Comprehension is measured, not asked.** The beta reader retells the chapter; the story editor
   grades the retell against what the ledger says this chapter owed. "Were you confused?" gets a
   polite no from a model; a retell that leaves out the central rule does not.
6. **Findings become examples, ledger entries, or replacement rules.** Never an appended rule. A
   role's knowledge base should get *better* after a run, not longer. Lessons and history go to
   `docs/`, which no subagent reads.
7. **Nothing gates on a number.** Word count, dialogue share and speech targets were each tried as
   ship gates and each was gamed within a few chapters. Tools report; judgement decides.
8. **Quality first.** Opus where the judgement or the prose is the product, Sonnet elsewhere. Cost
   is optimised later, only where a blind comparison cannot tell the difference.

## Roles

| role | agent | model | reads | writes | job |
|---|---|---|---|---|---|
| **showrunner** | main session | (session) | everything | `bench/`, `reading/` via tools; nothing in `novels/` beyond setup copies | runs the loop, approves beat sheets, relays hand-offs verbatim |
| **planner** | `planner` | opus | novel, `reading/*/notes.md` | `novel.md`, `bible/`, `plan/`, `state/` seeds, `work/` | world, cast, arcs; `premise.md`; reader ledger; each chapter's beat sheet; folds new facts into the bible |
| **writer** | `writer` | opus | novel (not `reading/`, not `bench/`) | `work/`, `chapters/` | prose from the beat sheet; revises warm against the editor's notes; may *stet* a note with a reason |
| **beta reader** | `beta-reader` | sonnet | its reading folder only | its reading folder | retell, world-as-understood, who's who, terms guessed, confusion and skim quotes, best moment, predictions, click-next; keeps its notes |
| **story editor** | `story-editor` | opus | novel, reading reports | `work/` | grades the retell against the ledger; merges reader (and continuity) reports against the beat sheet's intent; ACCEPT or ≤5 notes |
| **line editor** | `line-editor` | sonnet | novel (not `reading/`) | `work/`, `chapters/` | one polish pass after ACCEPT: AI-default tells, tics, format, numerals, lexicon, voice cadence |
| **continuity editor** | `continuity-editor` (plan 02) | sonnet | novel | `work/` | contradictions with bible and state, timeline, travel, provenance |
| **clerk** | `clerk` (plan 02) | sonnet | novel, reading folder | `state/`, ledger status, reader notes | the state write after acceptance; lists new facts for the planner's fold |
| **judge** | `judge` | opus (`claude-opus-5`, pinned) | `bench/*/blind/` only | nothing | not in the loop: the blind benchmark reader, with a different questionnaire from the beta reader's so the loop cannot tune itself to its judge |

## The loop, per chapter

```
planner ──> beats.md ──(showrunner approves)──> writer ──> draft-r0
                                                            │
                         ┌──────────────────────────────────┤ export prose-only
                         v                                  v
                    beta reader                    continuity editor (plan 02)
                         └──────────────┬───────────────────┘
                                        v
                                  story editor ── ACCEPT ──> line editor ──> chapters/NNNN-*.md
                                        │                                         │
                                     REVISE (≤5 notes)                           v
                                        v                                  clerk: state, ledger,
                                   writer (warm) ──> draft-r1 ──> fresh       reader notes; new facts
                                                                 beta reader     ──> planner fold
                                        (at most 2 revision rounds)
```

The showrunner's step-by-step version is [kb/showrunner/loop.md](../kb/showrunner/loop.md).

**Roles hand each other files, and end on one status line.** What one role writes for another
follows the wire format ([kb/shared/wire.md](../kb/shared/wire.md)):
- ids and paths instead of restating;
- quotes clipped to what locates a passage;
- one item per line.

The notes file carries the story editor's lines for the planner. The writer's facts file carries
its stets to the next story editor and its new facts to the planner's fold. The showrunner acts on
the status lines (`tools/wire.py` parses them) and never carries content between roles.

Not wire: the prose, the beta reader's report and memory (the measurement), the judge's answers,
and anything for the user. [roadmap/01b](roadmap/01b-wire-format.md) says why.

**Why a fresh beta reader each round:** a reader who has read round 0 knows what round 1 is trying
to say. The *notes* that become the reader's memory come only from the reader of the accepted
round.

**Why the line editor runs once, after ACCEPT:** polishing a draft that is about to be rewritten is
wasted work, and a committee that polishes every round sands the voice off.

## Knowledge bases

Each role has an OKF bundle in `kb/<role>/`: an `index.md` the role reads first, a `prompt.md` with
its procedure, and typed documents it opens when they apply. One level of disclosure: index, then
doc. Shared documents (the format spec, retell grading) sit in `kb/shared/` and are linked from
each index that uses them. The agent files in `.claude/agents/` are thin — frontmatter plus "read
your prompt" — so a prompt can be improved mid-session without restarting it (agents register at
session start).

What goes in a doc and how it is written: [roadmap/03-knowledge-bases.md](roadmap/03-knowledge-bases.md).
Session 1 seeded only what the chapter-1 experiment needs.

## Isolation

`tools/guard.py` is a `PreToolUse` hook on `Read|Grep|Glob|Write|Edit`, registered once in
`.claude/settings.json`. It identifies the caller from the payload: no `agent_id` means the main
session; otherwise `agent_type` names the role. The source of truth for the table below is `ROLES`
in `tools/guard.py`.

| role | reads | writes |
|---|---|---|
| beta reader | `reading/**`, `kb/beta-reader/**` — **nothing else** | `reading/**` |
| judge | `bench/*/blind/**`, `kb/judge/**`, `kb/shared/grading.md` — **nothing else** | (no write tool) |
| writer | everything except `reading/`, `bench/`, `docs/`, and the critics' and judge's `kb/` folders | `novels/*/work/**`, `novels/*/chapters/**` |
| line editor | everything except `reading/`, `bench/`, `docs/`, `kb/beta-reader/`, `kb/judge/` | `novels/*/work/**`, `novels/*/chapters/**` |
| planner | everything except `bench/`, `docs/`, `kb/beta-reader/`, `kb/judge/` | `novels/*/{novel.md,bible,plan,state,work}/**` |
| story editor | everything except `bench/`, `docs/`, `kb/judge/` | `novels/*/work/**` |
| continuity editor | everything except `reading/`, `bench/`, `docs/`, `kb/beta-reader/`, `kb/judge/` | `novels/*/work/**` |
| clerk | everything except `bench/`, `docs/`, `kb/judge/` | `novels/*/{state,plan,work}/**`, `reading/**` |
| main session | everything | everything — except `novels/**` while a `.test-run` file exists |
| any other agent | not judged (fails open) | not judged |

Searches (`Grep`, `Glob`) by the beta reader and the judge must name a path inside their area; an
unscoped search is refused, because it would search the whole repository.

**Why the working roles are kept out of each other's `kb/`:** the writer writing toward the beta
reader's questionnaire, or the planner designing toward the judge's, is the loop learning its
instrument instead of the craft.

**What this does not cover:** `Bash`. The beta reader and the judge are given no `Bash` tool, which
is the real wall for them. Other roles are routed, not sandboxed.

**Why not agent teams:** they are experimental, teammates load `CLAUDE.md` and every skill (fatal for
a cold reader), and they do not spawn in non-interactive runs. Named subagents plus `SendMessage`
give warm continuation without any of that.

## Files outside the novel

| path | what | git |
|---|---|---|
| `reading/<id>/` | a novel's prose-only exports, the beta reader's reports and notes. `<id>` is neutral: `r` + first 6 hex of sha1(slug), from `tools/export_prose.py --print-id` | ignored |
| `bench/<experiment>/` | experiment arms: `originals/`, `blind/` (what the judge sees), `key.md` (never judged) | ignored |
| `docs/experiments/` | write-ups of experiments and benchmark runs | committed |
