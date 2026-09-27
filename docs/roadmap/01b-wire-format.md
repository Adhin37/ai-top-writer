# 01b — Session 2b: the wire format, terse hand-offs between agents

**Goal:** make what agents write *for each other* short, keyed and parseable, without touching what
a reader of the book sees. The next plans' runs check that no one can tell the difference in the
chapter. The user brought this forward of "tokens later" (2026-09-27) because it only touches
channels no human reads. Prose-side levers stay in [06](06-measure-and-optimise.md).

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

- **The user's cold read (01 step 6.4) is recorded, and 01's verdict is final.** On NO-GO, stop:
  the room is being redesigned, and its hand-off format is moot.
- **01's ITERATE re-run has *not* run yet.** It runs after 01b, on the wire templates, so the note
  protocol is written once. The baseline here is plan 01's **L1 and L2**, which ran on today's
  prompts, so 01b's comparison measures the format alone.
- `python3 -m unittest discover tests` passes.

## Rules for this session

- **One lever at a time.** Nothing in 01b changes what a role *decides*, only how it writes it
  down. A change to a note's content, the accept rule, or the writer's examples belongs to 01's
  ITERATE re-run, which follows this plan.
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

Also add `tests/test_trace.py`, with a small fixture JSONL. **Baseline:** run it on `6f833c83`, plan 01's
session, which holds L1 and L2. It must reproduce `bench/ch1-abc/cost.txt` per role, within rounding.

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
| beta reader | `kb/beta-reader/prompt.md`: list sections only, **deferred** (see 5–8) | proposed: world rules, who's who, terms, confused, skimmed, best moment, expect next, one line each, a quote of ≤15 words and a reason of ≤12. Retell and *what the MC wants* untouched |
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

### 5–8. Live checks, in the next plans' runs (no replays here)

**The user's decision (2026-09-27):** no paid replays per plan, because each one costs a share of
the session limit. Each change is checked in the next plan's real run that uses it, and the whole
roadmap gets one complete test run at the end (plan 05). The probe, T2 (the notes replay) and T4
(an L4 loop) became the checklist below. T3 became a non-change: the beta reader's report is a
calibrated instrument, and it is not touched without the calibration run it needs.

**In 01's ITERATE re-run (L3)**, the first loop on the wire templates:
1. Every final message is one line: `python3 tools/wire.py handback <filed hand-back>` finds no
   defect.
2. The writer's `facts-rK.md` is written. If Claude Code refuses it as a report file, the status
   line is followed by the facts lines (the prompt's fallback), and the showrunner files them with
   `handback.py`. Log which happened.
3. `python3 tools/wire.py check` on each notes and facts file finds no defect. Compare its words
   per section with L1's notes-r0: owed table 766, notes 502, keep 318.
4. In rounds 1–2 the story editor was given the facts file. It does not re-raise a stetted note
   unless the reader's evidence answers the writer's reason.
5. `python3 tools/trace.py <session>` against L1 and L2 (`--match` on the spawn labels) gives words
   per artifact, hand-back tokens into the showrunner, its context peak, and cost per round.
6. The user's read of L3's chapter. Are the notes still acted on where the reader stumbled?

L3 carries ITERATE's content changes as well as the format, so a quality change cannot be pinned
on either. Only a clear regression in how the notes are acted on would point at the format.

**In plan 02:**
- the planner's status and `gap` / `changed` lines;
- the ledger written in the new form, with premise rows saying `premise`;
- *For the planner* lines reaching the next beats task;
- the facts files' `new` lines feeding the fold.

**In plan 05 (the complete test run):** the format across five chapters, with `tools/trace.py`
per chapter.

**Deferred:** the beta reader's list sections, with plan 06's calibration re-run (lever 3 re-runs
it anyway, for Haiku).

### 9. Close

Update the docs that describe the new state. They wait until now because the files did not exist
before:
- `CLAUDE.md`: *act on status lines; open a role's file only to decide*, and `tools/wire.py` and
  `tools/trace.py` under *Where things live*;
- `docs/architecture.md`, *The loop*: agents hand each other files, and each final message is a
  status line (`kb/shared/wire.md`);
- plan 06's Part A §1, trimmed to what is left.

Then plan 01's ITERATE re-run is next, and it edits the wire templates. The writer's examples and
the story editor's note protocol are its levers, and it runs the checks above.

## When a live check fails

The plan whose run found it revises the template, or reverts the channel to its prose form, and
logs which in its session log. `tools/wire.py` reports and never gates; nothing about the chapter
waits on it.

## Files produced

- `tools/trace.py`, `tools/wire.py`, `tools/handback.py --append`, and their tests.
- `kb/shared/wire.md`, and the replaced templates in `kb/`.
- Updated `CLAUDE.md`, `docs/architecture.md` and `docs/novel-format.md`.

## Verification

- `python3 -m unittest discover tests` passes, with the new trace, wire and handback tests.
- `tests/test_wiring.py`: every working role's index links `wire.md` and no cold role's does, and
  every status-line template in a prompt parses in `tools/wire.py`.
- `tools/trace.py 6f833c83 --until 2026-09-27T07:58:16` reproduces `bench/ch1-abc/cost.txt` per
  role.

## Out of scope

- `effort` per role, and model per role (plan 06).
- The showrunner's context per chapter (plan 06, lever 0).
- The beat sheet's length. It is intent for the writer, and changing it changes the story.
- The reader's `notes.md`.
- The judge.

## Session log

**2026-09-27. Steps 1–4 and 9 built; steps 5–8 became live checks for the next runs, by the
user's decision.** No agent was spawned, and nothing under `novels/` was written.

- **Deviation: run before 01 step 6.4.** The user asked for 01b before their cold read of C1, so
  01's verdict is still a provisional ITERATE.
- **`tools/trace.py`** matches `bench/ch1-abc/cost.txt` exactly on 6f833c83 with
  `--until 2026-09-27T07:58:16` (when `cost.txt` was written; the session ran on after it): cost
  per role and in total ($38.03), responses, and output tokens.
  - Model seconds are the trace's own measure: from the row a response answers to that response's
    last row. They agree with `cost.txt` within 5 s for five roles. The writer shows 968 against
    926, and the showrunner 1,094 against 643; `cost.txt` counted those differently.
  - Showrunner baseline for that window: context mean 307k, peak 581k tokens over 189 responses.
    110 hand-backs came in, ~115k tokens and ~8.2M re-read tokens, 14% of its cache reads.
- **`kb/shared/wire.md`**, linked from the shared index and from the planner's, writer's, story
  editor's, line editor's and showrunner's indexes.
- **Templates replaced:**
  - story editor: `prompt.md`, and `note-protocol.md`, whose examples are now wire;
  - writer: `prompt.md`, with the `facts-rK.md` file;
  - planner: `prompt.md`, the `premise.md` check line, and `reader-ledger.md`;
  - line editor: `prompt.md`;
  - showrunner: `loop.md`.
- **Unchanged:** the beta reader (deferred to plan 06's calibration) and the judge.
- **Tools:** `tools/wire.py`, `tools/handback.py --append`, `tools/trace.py`. Tests went from 72
  to 94, all passing. `tests/test_wiring.py` now checks that every prompt's status-line template
  parses.
- **Baseline for live check 3:** `wire.py check` on L1's `notes-r0.md` flags it as the old form.
  Its words per section: owed table 766, notes 502, keep 318.
- **Docs:** `CLAUDE.md` (act on status lines; the new tools), `docs/architecture.md` (hand-offs as
  files plus a status line), `docs/novel-format.md` (`work/` holds the facts files).

**Live checks, L3 (2026-09-27, in 01's ITERATE re-run).** Results in
[docs/experiments/2026-09-27-ch1-iterate.md](../experiments/2026-09-27-ch1-iterate.md), *01b live
checks*.

- **Status lines:**
  - writer clean 3/3;
  - story editor 2/3: one `owed 9/10 stated`, copied from the notes header, whose template now
    reads `owed 5/6`;
  - line editor 0/2: a prose recap after its `left` lines. Its template now says *"Exactly these
    lines"*, and anything else goes in one more `left` line.
- **Facts files:** written 3/3, no refusal.
- **Notes files:** 707–945 words (L1: 1,609–2,056); `wire.py check` found no defect.
- **Stets:** none, so check 4 could not be tested.
- **Notes acted on:** 5 of 5, and each problem the reader stumbled on was gone in the next draft. No
  sign the format cost the notes anything.
- **Cost:** not measurably changed. L3's room cost $6.04, the same as L1 over the same three rounds.
- **The user's read of L3 (check 6):** outstanding.

**Baseline correction.** `trace.py` missed hand-backs that reach the showrunner mid-turn, as
`queued_command` attachment rows. It counts them now, with a test.
- Plan 01's showrunner baseline (above) is really **140 hand-back entries, ~170k tokens, ~12.4M
  re-read tokens, 22% of its cache reads**, not 110 / ~115k / ~8.2M / 14%.
- Cost per role is unchanged.
- Separately, every agent's final response, the `SubagentHandback` call, is logged before its usage
  lands. So transcripts under-count output by at least $3.09 on plan 01, mostly judges'. Plan 06 §1
  says so.
