# Anthropic's multi-agent study, against the room

2026-10-04. No agent spawned. Sources:
- [Patterns and problems in emerging multiagent systems](https://www.anthropic.com/research/multiagent-systems) (Frontier Red Team, 2026-08-13)
- [How we built our multi-agent research system](https://www.anthropic.com/engineering/multi-agent-research-system) (Anthropic Engineering)

The study gives no checklist for builders. It names failure modes and asks for environments with
the social pressure that keeps human groups working: norms, reputation, recourse. Each mode is set
against this repo below.

| failure mode (study) | what it looks like here | guard | status |
|---|---|---|---|
| **Escalation under conflicting goals** (agents sabotage peers on a shared server) | two roles editing one chapter, each sure the other is wrong | roles run in sequence, never two at once; `tools/guard.py` gives each role a write area; the writer *stets* a note with a reason instead of fighting it | held: nothing to change |
| **Hidden profile** (a group misses what only one member knows) | the cold reader alone knows what the page failed to say; the editors know the bible too well | the story editor grades the reader's retell against the ledger, measuring instead of polling; the reader report and the continuity file reach it side by side | held |
| **Gullibility** (accuracy drops as confident sources lie) | the clerk folds whatever the writer says it established | the clerk checks each `new` fact against the chapter as it stands (`kb/clerk/prompt.md`) | held |
| **Telephone game** (research-system post) | the showrunner paraphrasing one role to another | the wire format passes paths; hand-offs are relayed verbatim | held |
| **Conformity** (agents in similar contexts make the same choice; errors line up) | three judges of one model; a planner's first-draw names | — | **gap: fixed below** |
| **Shared blind spots** (automated evals miss what humans catch) | every reader, in the loop and on the bench, is Claude | — | **open**: noted in plan 07, after the rebuild |

## The conformity evidence, in this repo

- **Names.** `grown-houses` and `varrow-bells` came from different seeds and different sessions,
  and they share five name words: Pell, Aurel, Bram, Orrin and Vane. Sallow and Tallow also rhyme.
  Plan 01's novel had Wren and Voss, which are stock names of the same kind. Each planner was a cold
  spawn, so each drew first.
- **Judges.** Run #7's verdict, "4.5, 4.5, 4.5 from three blind judges", came from three copies
  of `claude-opus-5` given one prompt. Under conformity, the unanimity is weaker evidence than it
  reads.

## Changes

1. **A judge panel on two models.** A new agent, `judge--fable` (`claude-fable-5-1`), was written
   by `bench.py arm` and is committed. `bench.py panel FOLDER` prints two `judge` dispatches and
   one `judge--fable` dispatch. The protocol (§7) asks for each score with its model, and for the
   spread.
   - **Why Fable and not Sonnet 5.5 (the plan's first choice):** Sonnet 5.5 is the beta reader's
     model, and lesson 12 keeps the loop's own critics off the bench. No loop role uses Fable,
     and `trace.py` prices it.
   - Two Opus judges keep the run comparable with run #7.
2. **`scaffold.py check` warns on a shared name word.** It looks at every name word this novel's
   lexicon shares with another novel in `novels/`. Rows starting with *the* are places and are
   skipped. `kb/showrunner/init.md` sends the warning back to the planner unless the user chose
   the name. The planner cannot see other novels, so a tool has to.
3. **A planner example, *A name the world gives*,** in `kb/planner/cast-design.md`. It is built
   like the existing gift-and-cost example: the first-draw version beside the one the world
   produces, and a test (would it fit another book?).
4. **Not done: a line-editor entry for stock names**, which the plan had listed. Names are bible
   facts the planner owns, and the line editor changes no facts. One rule, one owner.

## Checked

- `python3 -m unittest discover tests`: 270 tests pass. New: the panel, the shared-names warning,
  and the wiring tests reading `judge--fable` as the judge.
- `kb_check`: clean.
- `--novel` leak sweeps:
  - `grown-houses`: clean.
  - `varrow-bells`: three `Board` leaks in `kb/writer/orienting-the-reader.md`, present before
    this change and not touched.
- `scaffold.py check novels/varrow-bells` reports the five shared names.

`judge--fable` registers at the next session start. The panel is first used in the next benchmark
run.
