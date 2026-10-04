# 2026-10-04 — Model and effort by role, and Anthropic's skill-authoring guide against `kb/`

For plan [06d](../roadmap/06d-model-effort-and-kb.md). The user's two questions: Sonnet 5.5 looks
dear on public benchmarks against Opus 5.5, so is it the right model for its roles; and does
Anthropic's [skill-authoring best practices](https://platform.claude.com/docs/en/agents-and-tools/agent-skills/best-practices)
page have concepts this project should use. No agent was spawned. Every number comes from run #7's
transcripts (session `9ae41156`) or from the public sources below.

## 1. What the benchmarks say

Artificial Analysis Intelligence Index v4.3.2, score · cost per task in USD, as reported by
[explainx](https://www.explainx.ai/blog/claude-opus-5-5-vs-sonnet-5-5-comparison-2026),
[aivy](https://aivy.com.au/resources/claude-sonnet-5-5-vs-opus-5-5/) and
[kingy](https://kingy.ai/blog/claude-sonnet-5-5-vs-opus-5-5/):

| effort | Sonnet 5.5 | Opus 5.5 |
|---|---|---|
| low | 36 · $0.41 | 42 · $0.55 |
| medium | 41 · $0.59 | **51 · $1.34** |
| high | **47 · $1.08** | 54 · $1.82 |
| xhigh | 52 · $2.74 | 56 · $3.46 |
| max | 56 · $7.60 | 58 · $5.98 |

- **Above `high`, Sonnet costs more than it is worth.** At max it writes about 60% more output
  than Opus and costs more per task, for two points less. Opus at `medium` is within a point of
  Sonnet at xhigh for half the price.
- **Below `high`, Sonnet falls off a cliff:** 6 points at `medium`, where Opus at `low` scores
  better for about the same money. 06c met the same cliff on its own data: the continuity editor
  at `medium` lost its "who could know" catches.
- **Sonnet at `high` is the one point on its curve worth buying.**
- None of these benchmarks measures fiction. They measure reasoning tasks whose cost is mostly
  output, which is why the user's reading ("Sonnet is dear") is right for them.

Prices, $ per million tokens: Opus 5.5 4 in / 20 out; Sonnet 5.5 2 / 10; cache reads 0.20 on both.
A cache write costs 1.25× input (5 minutes) or 2× (1 hour).

## 2. What this room's Sonnet roles cost

The room's Sonnet roles mostly **read**: a bible, state, a draft. Input is where Sonnet is half
price, and cache reads cost the same on both models. In run #7, Claude Code's own count put the
four Sonnet roles at **$11.89 of $82.09 (14%)**: $5.15 cache writes, $1.64 cache reads, $5.09
output (509k tokens, 61% thinking).

The same tokens priced at Opus 5.5 (`tools/trace.py --reprice`, built for this note):

| role | traced $ | on Opus $ | with unrecorded output $ | on Opus $ |
|---|---|---|---|---|
| continuity editor | 3.66 | 6.51 | 4.90 | 8.97 |
| line editor | 2.11 | 4.09 | 2.24 | 4.33 |
| clerk | 1.43 | 2.32 | 2.42 | 4.29 |
| beta reader | 1.73 | 3.31 | 2.34 | 4.54 |
| **total** | 8.93 | 16.23 | **11.90** | **22.13** |

Reproduce: `python3 tools/trace.py 9ae41156 --reprice continuity-editor=claude-opus-5-5 --reprice clerk=claude-opus-5-5 --reprice line-editor=claude-opus-5-5 --reprice beta-reader=claude-opus-5-5`

The reprice keeps token counts, so it is an upper bound for an Opus arm at `medium`, which would
think less. The cache writes would not shrink with effort, though: they are the reading, and they
double ($5.15 → $10.30). An Opus `medium` arm lands near $18, about +$6 a run, and the AA index
puts Opus `medium` only 4 points above Sonnet `high`.

## 3. Decision per role

| role | now | decision | reason |
|---|---|---|---|
| showrunner | Opus `medium` | keep | AA's best-value point (06b) |
| writer | Opus `high` | keep for round 0 | prose is the product |
| writer, revisions | Opus `high` | 06c lever 5, re-aimed: Opus `medium`, still to test | Sonnet `high` scores 4 points under Opus `medium` and saves ~20% on output-heavy work |
| planner | Opus `high` | 06c lever 6, `medium`, still to test | AA: −26% cost for −3 points, the trade the story editor won in 06c |
| story editor | Opus `medium` | keep | kept in 06c on agreement |
| continuity editor | Sonnet `high` | keep | `medium` lost in 06c; Opus adds $3–4 a run, mostly on its reading |
| line editor | Sonnet `high` | keep; 06c lever 2c dropped | `medium` is the cliff |
| clerk | Sonnet `high` | keep | almost all reading; Haiku lost in 06c |
| beta reader | Sonnet `high` | keep | calibrated instrument |
| judge | `claude-opus-5` | keep | calibrated, and 2% of a run |

**The rule, from here on: Sonnet 5.5 runs at `high` only. A role that needs more moves to Opus at
`medium`.** `tools/kb_check.py` now warns on a Sonnet agent at another effort.

## 4. The skill-authoring guide, item by item

| guide item | here |
|---|---|
| one level of references from the entry file | already: `prompt.md` → `index.md` → docs |
| descriptions say what a file is for and when to open it | already: OKF frontmatter, `kb_check` |
| concrete examples | already, with invented nouns, `kb_check`'s leak sweep |
| files under 500 lines | already: the largest `prompt.md` is 134 |
| the template pattern | the wire format |
| evaluations before docs | `tools/bench.py` (06c) |
| observe how agents navigate | `reads.tsv`, `trace --docs` (06) |
| scripts for deterministic operations | `room.py`, `lint.py`, `state_check.py`, `reading.py`. One more measured and dropped, below |
| **validator → fix → repeat** | **new:** the continuity editor runs `wire.py check` on its file before its status line. The clerk already runs `state_check`; the roles without Bash are checked by `room.py` |
| **no time-sensitive text** | **new:** `kb_check` warns on a date, `run #N`, `plan NN`, `session N` or `lesson N` in `kb/`. None today |
| **concise, written for the model that runs it** | **new:** the prompt audit, section 5 |

### Measured and dropped: a bible read-set tool

`touches.py` printed the bible lines a draft's proper nouns touch, for the continuity editor to
read instead of whole files. On run #7's bible (10,715 words) it returned 8,863 words for ch 5 r0
(83%), 9,198 for ch 4 and 8,949 for ch 2. The protagonist's name is in 22% of the bible's 156
blocks, the main setting in 29%, and the protagonist's cast file is always whole. On a small,
dense bible a safe selective read cannot be small, and 06c already ranked the lever at ~$1 a run.
The tool was deleted; the continuity editor's step 4 is unchanged.

### Considered and set aside

- **Inlining the docs every spawn opens.** Agents already batch their `kb/` reads into 2–4
  responses a spawn; inlining saves about one turn.
- **Tables of contents in files over 100 lines.** Agents read whole files with Read.
- **Gerund names.** Agents are named by role, and the guide's naming is for skill discovery.
- **Checklists for the loop.** `room.py` already scripts it.

## 5. Prompt audit

Method: the `claude-api` skill's `shared/prompt-audit.md`, steps 0–6.

- **Scope:** `kb/*/prompt.md`, the `kb/` docs, `.claude/agents/*.md`, `.claude/commands/*.md`.
  `kb/beta-reader/` and `kb/judge/` are out: calibrated instruments.
- **Target:** each file's pinned model, Opus 5.5 or Sonnet 5.5; the showrunner's docs, Opus 5.5.
- **Provenance:** `docs/lessons.md`, `docs/experiments/` and git history.

**Result: the surface is close to clean.**

- **1a pressure language:** zero. No capitalised MUST, NEVER, CRITICAL or IMPORTANT, and no
  hedges on requirements.
- **1b thinking scaffolds:** zero. "Step by step" appears once, in `/new`, about following
  `init.md`'s ordered steps.
- **1e prohibition clusters:** every run of prohibitions carries its reason (the line editor's
  "must not change", the bias rules).
- **Group 2:** every tool, subcommand and flag the prompts name exists. No two instruction files
  disagree.
- **Group 3** is not applicable: there are no tool definitions; agent descriptions are routing
  text.
- **Group 4:** the effort rule above, now checked by `kb_check`.

| location | evidence | pattern | action |
|---|---|---|---|
| `kb/continuity-editor/prompt.md`, final message | "nobody else reads your final message: anything after the line is lost" | 1d fossil: a fix for Sonnet 5's recaps. The run #7 trace showed the recap ended with the move to Sonnet 5.5 on a byte-identical template (18 clean spawns since); the fixes only shrank it on Sonnet 5 | **removed** (medium). The next run checks the final message stays one line |
| `kb/clerk/prompt.md`, final message | "a recap after the line is lost" | the same fix | **kept, flagged:** the clerk's evidence is confounded (its recap and its fix were both on Sonnet 5, its clean runs on another `prompt.md`) |
| every role's final message | "Exactly one line, nothing before or after it" | 1d suppressor, on grep | kept: a format pin that `wire.py` parses (keep list 7) |
| wire lines in four prompts | `≤12 words`, `≤15 words`, `≤8 words` | 1f numeric caps, on grep | kept: quote lengths inside a parsed line, not output ceilings |
| `kb/writer/prompt.md` and `kb/clerk/prompt.md` | "If the facts / fold file cannot be written, put its lines after the status line" | escape hatch beside "nothing after it" | kept, flagged low: a named fallback; it has never fired |
| `kb/line-editor/prompt.md` step 1; `kb/continuity-editor/prompt.md` step 2 | "Read the whole draft once before touching it" | 1c method, low | kept: one line each, and the order matters to both |
| `kb/planner/prompt.md`, plan task | "name to yourself the planned row whose event carries it" | 1b thinking steering, low | kept: it is a check with an output (the `moved to` lines), not a depth instruction |
| `CLAUDE.md` principle 7 | "Cost comes later (plan 06)" | Group 2, stale: plan 06 is built | **rewritten** to the model rule above |

What the next full run checks: the continuity editor's final message (one line in every spawn),
its `wire.py check` calls (in its transcript), and its findings count and cost a spawn against run
#7's (3–6 findings, ~$0.35).
