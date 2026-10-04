# 2026-10-04 — Where run #7's tokens went, and what Claude Code offers against it

Research for plans [06](../roadmap/06-measure-and-optimise.md), [06b](../roadmap/06b-showrunner-cost.md)
and [06c](../roadmap/06c-role-levers.md). No agent was spawned: the numbers come from run #7's
transcripts (session `9ae41156`), the agent files, the user's settings and Anthropic's docs as of
this date. The user is on **Claude Pro**: the binding constraint is the five-hour and weekly usage
limit, not dollars. Dollars below are list-price equivalents, which is how Claude Code itself
estimates usage ("re-reads that history at the cached token rate").

## Run #7 per role (`python3 tools/trace.py 9ae41156…`)

| role | spawns | responses | output | thinking | cache write $ | cache read $ | output $ | cost $ |
|---|---|---|---|---|---|---|---|---|
| showrunner | 1 | 296 | 174k | 31% | 10.31 | 20.09 | 3.48 | **33.88** |
| writer | 7 | 128 | 266k | 42% | 6.40 | 1.51 | 5.32 | 13.23 |
| planner | 8 | 178 | 285k | 56% | 4.06 | 2.01 | 5.69 | 11.76 |
| story editor | 14 | 127 | 164k | 69% | 3.55 | 0.73 | 3.28 | 7.56 |
| continuity editor | 14 | 138 | 55k | 71% | 2.29 | 0.82 | 0.55 | 3.66 |
| line editor | 6 | 35 | 112k | 59% | 0.85 | 0.14 | 1.12 | 2.11 |
| judge | 6 | 37 | 5k | 1% | 1.40 | 0.32 | 0.12 | 1.84 |
| beta reader | 14 | 61 | 39k | 32% | 1.19 | 0.14 | 0.39 | 1.73 |
| clerk | 6 | 78 | 7k | 6% | 0.82 | 0.54 | 0.07 | 1.43 |
| **total** | | | | | | | | **77.21** |

(The session also holds work after the run, hence $77.21 against the $70.73 the run reported.)

What the table says:
- **The showrunner is 44%, and it is context × turns, not thinking.** 296 responses over a context
  of mean 344k and peak 596k: 100M tokens re-read ($20.09). Its own output is $3.48. Its cache
  writes ($10.31) are 1-hour writes at $8/MTok, and most of them are the two rebuilds after
  usage-limit pauses.
- **Reading costs as much as writing in every role but the prose ones.** Continuity editor: $2.29
  of cache writes against $0.55 of output (≈65k tokens read per spawn). Story editor and planner
  are about even.
- **Thinking is 56–71% of the critics' and planner's output**, at `effort: high`.

## Facts found in the transcripts and settings

1. **Every role runs at `effort: high`** (`.claude/agents/*.md`), above Claude Code's default for
   these models: Opus 5.5 and Sonnet 5.5 default to `medium`. The showrunner runs at **`xhigh`**
   (`effortLevel` in `~/.claude/settings.json`). On Opus 5.5 / Sonnet 5.5 a mid-session effort
   change keeps the prompt cache.
2. **Subagents cache for 5 minutes; the main session for 1 hour** (Claude Code's defaults on a
   subscription). Every subagent write in run #7 is `ephemeral_5m`.
3. **The warm writer loses its cache between rounds.** 6 of its continuations came 5.5–6.5 min
   after its last request (or after a usage-limit pause) and re-wrote 85–126k tokens each: ~675k
   tokens, ~$3.4 of its $13.23. Setting `experimental.cacheTtl: 1h` on the writer roughly breaks
   even, because every write then costs $8 instead of $5/MTok and the two pause gaps (3.5 h) miss
   anyway. **Rejected on the numbers**; revisit only if round gaps grow.
4. **VS Code's markdownlint warnings are injected into agents' contexts.** After their edits, the
   IDE extension adds `<ide_diagnostics>` (MD060 table style, MD022, MD032…): 32 injections, ~151k
   characters, into the planner; 12 into the beta reader (on its own `notes.md`). Noise for a cold
   reader, tokens re-read on every later turn, and a prompt to "fix" lint.
5. **The claude.ai connector's MCP instructions reach every subagent** (~2.1k characters each,
   75 spawns), the beta reader and the blind judge included.
6. `omitClaudeMd: true` is already on every agent: no subagent loads CLAUDE.md. Verified (the
   beta reader's first request is ~4.4k tokens: its 170-character body, boilerplate, ~2.5k of tool
   schemas).
7. The judge is pinned to `claude-opus-5` ($5/$25, cache read $0.50), dearer than Opus 5.5
   ($4/$20, $0.20). It is a calibrated instrument; noted, not a lever.

## What Anthropic offers (docs read 2026-10-03/04)

| feature | what it does for this room | source |
|---|---|---|
| Opus 5.5 / Sonnet 5.5 prices | $4/$20 and $2/$10 per MTok; **cache read $0.20 on both**; no long-context premium up to 1M | [pricing](https://platform.claude.com/docs/en/about-claude/pricing) |
| Haiku 4.5 | $1/$5, and the older tokenizer: Claude 4.7+ models produce ~30% more tokens for the same text | same |
| Fable 5.1 | $10/$50; on Pro it **bills to usage credits** (real money) | [model config](https://code.claude.com/docs/en/model-config) |
| effort | `low`…`max`; adaptive thinking is always on, effort is the only control; per-agent `effort:` | same, [subagents](https://code.claude.com/docs/en/subagents) |
| cache TTL controls | `promptCacheTtl`, `subagentPromptCacheTtl`, per-agent `experimental.cacheTtl` | [prompt caching](https://code.claude.com/docs/en/prompt-caching) |
| auto-compact window | `CLAUDE_CODE_AUTO_COMPACT_WINDOW` (default ~967k on these models) | [model config](https://code.claude.com/docs/en/model-config) |
| **dynamic workflows** | a saved JavaScript script (`.claude/workflows/`) runs the loop: `agent()`, `parallel()`, `pipeline()`, JSON `schema` outputs; results stay in script variables, **not in the main context**; resumable; waits out a usage limit and continues (v2.1.271+, interactive). On Pro, enable in `/config` | [workflows](https://code.claude.com/docs/en/workflows) |
| advisor tool | a cheaper main model consults a stronger one at decision points; the advisor re-reads the whole conversation **uncached** each call | [advisor](https://code.claude.com/docs/en/advisor) |
| `/usage` plan breakdown | usage attributed to subagents, flags for long context and cache misses; `Prompt cache (main)` line | [costs](https://code.claude.com/docs/en/costs) |
| Batch API | −50%, but billed to an API key: real money on top of Pro. Out of scope | [pricing](https://platform.claude.com/docs/en/about-claude/pricing) |

Claude Code here is v2.1.287 (VS Code extension), so every feature above is available.

## Considered and set aside

- **Sonnet as the showrunner.** Its cost is cache reads, priced the same on Sonnet and Opus 5.5.
  Shrinking the context wins; changing the model barely moves it.
- **Advisor on the showrunner.** Each call re-reads a ~344k context uncached. Worse, not better.
- **Fable anywhere.** Usage credits on Pro.
- **Batch API for the judges.** Real money; the judges are 2% of the run.
- **1-hour cache on the warm writer.** Break-even on run #7's numbers (fact 3).
