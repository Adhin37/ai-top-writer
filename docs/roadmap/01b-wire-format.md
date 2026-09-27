# 01b — Session 2b: the wire format, terse hand-offs between agents

**Goal:** make what agents write *for each other* short, keyed and parseable, without touching what
a reader of the book sees, and prove that no one can tell the difference in the chapter. The user
brought this forward of "tokens later" (2026-09-27) because it only touches channels no human reads.
Prose-side levers stay in [06](06-measure-and-optimise.md).

**Hypothesis:** the room's hand-offs can shrink by about half, with no loss in what the writer does
with the notes, if they follow one discipline:
- keyed lines;
- ids and paths instead of restating;
- quotes clipped to what locates a passage;
- a one-line status as each role's final message;
- information for a role goes in a file that role reads.

The discipline pays in the showrunner's re-reads, in wall time, and in outputs a tool can check.

## Why: what plan 01's transcripts show

Session `6f833c83`, read from `~/.claude/projects/-home-adhin-projects-ai-top-writer/`. Costs are
from `bench/ch1-abc/cost.txt`; the other numbers were computed from the transcripts.

| role | cost | output tokens | thinking share of output | cache writes (reading) vs output (writing) |
|---|---|---|---|---|
| showrunner | $19.96 | 127k | — | $12.86 is cache *reads*: context averaged ~315k tokens and peaked ~610k over 204 responses |
| writer | $4.50 | 96.8k | 53% | $2.13 vs $1.94 |
| story editor | $2.62 | 58.0k | 61% | $1.22 vs $1.16 |
| planner | $2.16 | 47.5k | 69% | $1.08 vs $0.95 |
| line editor | $1.49 | 84.1k | 73% | $0.45 vs $0.84 |
| beta reader | $1.30 | 61.9k | 42% | $0.53 vs $0.62 |

- **The files agents write for each other run long:**
  - notes files are 1,370–2,060 words for 0–2 notes. The owed table restates every fact in full,
    each *Keep* line carries a paragraph of justification, and a summary paragraph repeats the
    verdict;
  - reader reports are 1,170–1,570 words;
  - the ledger is 2,408 words, and restates `premise.md`;
  - the beat sheet is 1,667 words, against a ~450-word example.
- **The one-line contracts are not kept.**
  - The story editor's prompt says *"End your turn with one line"*, and it wrote ~700 words of
    summary before `NOTES READY`.
  - Writer L2 put ~250 words of staging notes before its block, and listed ~25 new facts (~600
    words).
  - The harness's subagent default, which is to return findings as text, pulls toward a summary.
    A prompt has to name the final message's exact form to win.
- **Every hand-back lands in the showrunner's context and is re-read on every later turn.**
  - Hand-backs were 116k tokens and 9.8M re-read tokens, second only to the showrunner's own file
    reads (11M re-read tokens).
  - The largest chunk is the showrunner's own writing: the experiment log and scripts.
  - 95k of the 116k were judges'.
- **Information goes to the wrong place.**
  - The L2 story editor's four "for planning, not for revision" observations reached only the
    showrunner.
  - The writer's stet reasons never reach the story editor who judges the next round.
- **Sizing, honestly.** The text agents write for each other is about 10–15% of the room's output
  tokens, and output is under half of each role's cost. Halving that text saves roughly 3–6% of the
  room's cost directly, counting the next role reading it. It saves more on the showrunner's
  re-reads, on wall time and on reliability. The large levers are:
  - thinking, 53–69% of the Opus roles' output;
  - the showrunner's context;
  - what agents read.

  They are plan 06's.

## What already exists (researched 2026-09-27)

- **No usable agent language.** Latent or KV-cache communication (LatentMAS, [Interlat](https://pith.science/paper/2511.09149),
  [Q-KVComm](https://arxiv.org/pdf/2512.17914)) needs model internals, which Claude Code does not
  expose.
- **Invented compressed protocols can cost more.** Parse failures that force extra calls raised total
  tokens 8–11% ([arXiv 2609.06129](https://arxiv.org/abs/2609.06129)).
- **[Caveman](https://github.com/juliusbrussee/caveman)**, a Claude Code skill, claims 65–75% savings;
  a [paired A/B test on 86 tasks](https://blog.jetbrains.com/ai/2026/07/speak-to-ai-agents-like-cavemen-tosave-tokens/)
  measured 8.5%, with quality unchanged. It is written for chat narration, and it drops the
  articles and conjunctions a writer needs to act on a note.
- **[Chain of Draft](https://arxiv.org/abs/2502.18600)** targets terse *thinking*, as little as 7.6%
  of the tokens. In Claude Code a subagent's thinking is reachable only through the `effort`
  frontmatter ([docs](https://code.claude.com/docs/en/sub-agents)). That is plan 06's lever.
- **[Let Me Speak Freely?](https://arxiv.org/abs/2408.02442)** Strict formats such as JSON degrade
  reasoning. Constrain the artifact, never the thinking; use keyed text, not JSON.
- **[TOON](https://github.com/toon-format/toon)** saves ~40% over JSON on uniform tables and does
  worse on mixed data. Our tables are small markdown, so it adds nothing here.
- **Anthropic's [multi-agent research system](https://www.anthropic.com/engineering/multi-agent-research-system)**:
  subagents write artifacts to files and pass lightweight references, so the coordinator's context
  stays lean. This repo already passes paths and P/R/F ids; the wire format finishes the job.

## Prerequisites

- Plan 01's ITERATE re-run of step 5 is done. Call it **L3**; its prompts are the verbose baseline.
  The user's cold read (01 step 6.4) is recorded.
- `python3 -m unittest discover tests` passes.

## Rules for this session

- **One lever at a time.** Nothing in 01b changes what a role *decides*, only how it writes it
  down. A change to a note's content, the accept rule, or the writer's examples belongs to another
  plan.
- **Replace, never append.** Each role's output template is swapped for its wire form. No "be
  concise" line is added on top of an old template.
- **Unchanged, on purpose:**
  - the prose;
  - the beta reader's **retell** and *what the main character wants*, which are the measurement;
  - the reader's `notes.md`, its memory in its own words, whose drift plan 02 tests;
  - `premise.md`, the grading key, in words a reader could repeat;
  - the beat sheet's story lines, which are intent for the writer (principle 1);
  - every judge answer, which is benchmark-only and read by the user;
  - everything addressed to the user.
- `touch .test-run` before any replay. Delete it when the run is written up.

## Steps

### 1. `tools/trace.py`, pulled forward from plan 06 Part A §1

Port skilled-writer's `scripts/swlib/transcripts.py` and `cmd_trace.py` as 06 describes: usage,
timestamps and tool names only, never prompt text or prose. Scope it by session id. Add:
- thinking tokens (`usage.output_tokens_details.thinking_tokens`) apart from visible output;
- cache writes and cache reads, in tokens and dollars (rates as in plan 01's write-up);
- the showrunner's context per response and its peak;
- the size of each hand-back entering the showrunner. Hand-backs arrive two ways: as `Agent` /
  `SendMessage` tool results, and as `[Subagent hand-back]` agent messages;
- usage counted once per message id.

Also add `tests/test_trace.py`, with a small fixture JSONL. **Baseline:** run it on `6f833c83` and on
L3's session. It must reproduce `bench/ch1-abc/cost.txt` per role, within rounding.

### 2. `kb/shared/wire.md`

Type `reference`, linked from `kb/shared/index.md` and from each working role's `index.md` (planner,
writer, story editor, line editor). The beta reader cannot open `kb/shared/` (guard) and gets no
link. Its template change lives inside its own prompt. The judge is unchanged. The doc states, as
facts:

1. **The final message is one status line:** `VERB <path> | key value | …`. The showrunner reads
   nothing else; anything before or after it is discarded.
2. **Refer, don't restate:** ids (P1, R5, F15, N2) and paths. The reader of the file already holds
   the premise, the ledger and the beat sheet.
3. **Quote to locate:** the fewest words that find the passage (about twelve).
4. **One item per line**, with `key value` fields. Fragments are fine. There is no preamble and no
   recap, and the only headings are the template's.
5. **Judgement stays a plain clause.** The *effect* on the reader and a *stet* reason are what the
   writer acts on. They get shorter, never ambiguous.
6. **Information for a role goes in the file that role reads**, never in the hand-back.

Its one worked pair is `note-protocol.md`'s invented Long Ebb note, today's form beside this one:

```
N1 Ebb never explained
where "Nessa had four hours until the Long Ebb, and the Harrow boy was still on the tally."
ev    P1 missing · retell "some kind of tide festival (guess)" · guessed: Long Ebb, tally
eff   the reader didn't know the boy was dead, so the last scene read as a family quarrel, not grief
dir   the rule in plain words where the tally is first named
```

### 3. Replace the output templates

| role | file(s) | new form |
|---|---|---|
| story editor | `kb/story-editor/prompt.md`, `note-protocol.md` (examples become wire) | header `verdict REVISE \| owed 5/6 stated \| event yes \| ending yes \| click-next 4`; `## Owed` one line per id: `P2 partly "<≤12 words of retell>" — <what is missing>`; `## Notes` as in the example; `## Keep` `"<quote>" — <≤8 words>`; **new** `## For the planner`, one line each; `## Unresolved` (round 2). Final message: `NOTES READY <path> \| REVISE \| notes 2 \| owed 5/6` |
| writer | `kb/writer/prompt.md` | the hand-back block moves to `work/chNNNN/facts-rK.md`: `learns P1 "<≤12 words>" · …`; `new <one fact, ≤15 words>` per line; `couldn't`; `notes N1 done "<new words>" · N2 stet: <reason>`; at most 3 `choices` lines. Final message: `DRAFT READY <draft> \| facts <facts> \| new 12 \| stets 0 \| couldn't 0` |
| planner | `kb/planner/prompt.md`, `reader-ledger.md` | `PLANNER DONE <task> \| <files> \| gaps n \| changed n`, then one `gap` / `changed` line each. Ledger: premise rows point at `premise.md` instead of restating it; other facts ≤20 words; *how it lands* names a moment in ≤25 words |
| line editor | `kb/line-editor/prompt.md` | `POLISHED <path> \| changes 14 (<the top 3>) \| left n`, then one `left` line each |
| beta reader | `kb/beta-reader/prompt.md`: list sections only (**step 7**) | world rules, who's who, terms, confused, skimmed, best moment, expect next: one line each, a quote of ≤15 words and a reason of ≤12. Retell and *what the MC wants* untouched |
| showrunner | `kb/showrunner/loop.md` | act on status lines; open a role's file only to decide (the beat sheet) or when a status line does not parse; give the story editor `facts-rK.md` in rounds 1–2, and the planner the last notes file's *For the planner* lines; in experiments, file hand-backs with `handback.py --append` instead of retyping them |

### 4. Tools and tests

- **`tools/wire.py`** plus `tests/test_wire.py`.
  - It parses each role's status line and the notes and facts templates.
  - It prints findings as `level check: detail` (plan 02's convention): a note without
    where/ev/eff, more than five notes, text before a status line, words per section.
  - It reports; it never gates.
- **`tools/handback.py --append LOG`** appends a hand-back verbatim to an experiment log. Add a test
  in `tests/test_handback.py`.
- **`tests/test_wiring.py`:** every working role's `index.md` links `kb/shared/wire.md`, and the
  cold roles' do not.

### 5. Probe (T1)

Spawn the writer (a revision round on L1's `draft-r0.md` with L1's `notes-r0.md`), the story editor
and the line editor on plan 01's files. Check:
- **each final message is exactly one line** that `tools/wire.py` parses;
- **the writer's `facts-rK.md` write is not refused** by Claude Code's "report file" rule (plan 01
  found that rule for `report.md`). If it is refused, fall back: the terse block becomes the final
  message, filed with `handback.py`. Log which.

### 6. Replay the notes channel (T2)

Inputs held fixed: L1's `draft-r0.md` and `reading/L1-r0/report.md`.

1. Two story editors run on the old template (from git) and two on the wire template.
2. Compare the verdict, the note count, and which draft passages the notes target.
3. Each note set goes to a **fresh** writer: the same cold condition for both arms, which is not the
   loop's warm one. Each revision goes to a fresh beta reader.
4. Pairwise-judge the revisions, old against wire: 3 judges per pair, labels and order swapped.

About $12–15.

### 7. Replay the reader's list sections (T3; optional, last)

Re-run plan 01's calibration (three readers on A, three on the control, each graded) with the new
list sections. Then run two readers on L1 `draft-r0` and have the story editor grade both reports.
About $2–3. Skip it if the session runs long; it is the smallest saving and the only one that
touches an instrument.

### 8. End to end (T4)

One full loop of chapter 1 (**L4**) from the same beat sheet, with every kept change. `tools/trace.py`
compares L4 with L1, L2 and L3 on:
- words per artifact;
- the room's output, thinking and cache;
- the showrunner's peak context and hand-back tokens;
- model seconds and cost.

The user reads L4's chapter.

### 9. Close

Update the docs that describe the new state. They wait until now because the files did not exist
before:
- `CLAUDE.md`: *act on status lines; open a role's file only to decide*, and `tools/wire.py` and
  `tools/trace.py` under *Where things live*;
- `docs/architecture.md`, *The loop*: agents hand each other files, and each final message is a
  status line (`kb/shared/wire.md`);
- plan 06's Part A §1, trimmed to what is left.

## Keep criteria, per channel (fixed before step 5)

| channel | kept when |
|---|---|
| status lines and hand-backs (T1) | every probe line parses; tests pass |
| notes (T2) | the wire notes target the same passages and verdict as the old ones (1 of 4 editors may differ, as the old ones differ among themselves), **and** the wire-note revisions tie or win at least 3 of 6 pairwise picks |
| facts file | the probe's write is accepted, or the fallback works |
| reader list sections (T3) | calibration passes as in plan 01 (A's central rule missing/wrong ≥2/3; the control's stated ≥2/3), and the story editor's grades of L1 r0 do not move |
| the whole (T4) | the user cannot tell L4's chapter is worse than L3's; trace shows the saving |

A channel that fails is reverted, and the write-up records it as a lever that lost.

## Known confounds, to write down, not fix

- **n is small:** two editors per arm, three judges per pair. A difference of one pick is noise.
- **The T2 revisions are cold**, while the loop's are warm. Both arms share the condition, so the
  comparison is fair, but the absolute quality is not the loop's.
- **L3 and L4 differ by loop variance too** (L1 took three rounds, L2 one). T4 reads the trend, not a
  verdict.

## Files produced

- `tools/trace.py`, `tools/wire.py`; `tools/handback.py --append`; their tests.
- `kb/shared/wire.md`, and the replaced templates in `kb/`.
- `docs/experiments/<date>-wire-format.md`, which is committed. It holds:
  - the trace baseline;
  - the probe;
  - the T2–T4 tables;
  - the channels kept and reverted;
  - cost and time;
  - confounds.
- `docs/lessons.md`: what the format taught, if anything.

## Verification

- `python3 -m unittest discover tests` passes, with the new trace, wire and handback tests.
- Every role's final message in T4 is one line that `tools/wire.py` parses.
- `tools/trace.py` on `6f833c83` reproduces `bench/ch1-abc/cost.txt` per role.
- No kept channel is without its T-row in the write-up.

## Out of scope

- `effort` per role, and model per role (plan 06).
- The showrunner's context per chapter (plan 06, lever 0).
- The beat sheet's length. It is intent for the writer, and changing it changes the story.
- The reader's `notes.md`.
- The judge.

## Session log

*(filled in when this plan runs)*
