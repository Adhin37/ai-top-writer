# Knowledge-base mapping: skilled-writer → ai-top-writer

Plan 03 step 1. One row per old skill (`skilled-writer/.claude/skills/`, 44 skills, ~78k words),
naming where its knowledge goes in `kb/`, or that it is dropped and why. Each skill's role cards
(`skilled-writer/roles/<phase>/<skill>.<card>.md`, 119 cards, ~84k words) go with their skill
unless the row says otherwise.

**How a doc is made from a row:** read the skill and its cards, keep the best worked examples (with
invented, genre-neutral nouns), say the idea in three sentences, and drop the rest. What the old
skill said *against* a failure becomes, where possible, an example of the version that works.

**The evidence from plans 01–02** (transcripts of 111 spawns, `docs/experiments/`):
- every role read its `prompt.md` first (111 of 111), and its `index.md` in 37 of 41 working-role
  spawns. The thin agent file that reads its prompt at runtime stays;
- roles open what their index marks "always" and their situational docs about half the time. So
  each index line says plainly *when* to open the doc;
- what the loop actually needed, by role:
  - **writer:** orienting the reader (the lecture fix), scene vs summary, dialogue;
  - **story editor:** grading, briefings, promises across the break, the scene log;
  - **line editor:** the default habits, and recurrence across chapters;
  - **continuity editor:** provenance, time, the bible's figures;
  - **clerk:** a short `kno` line;
  - **planner:** carriers for every fact, the fold.

## Where each skill goes

| old skill | words | → destination | notes |
|---|---|---|---|
| battle-scale | 1,285 | writer `toggle-battle-scale.md` (toggle `battle-scale`) | fronts, attrition and supply, through one viewpoint. The logistics card goes into the same doc |
| bias-guard | 1,641 | planner `bias-structural.md` · line editor `bias-line-level.md` | split by the plan: factions, cast and what the world rewards go to the planner; descriptions, epithets and who gets interiority go to the line editor. Absolute in both, said once in each |
| chapter-plan | 2,697 | planner `arcs-and-chapters.md` | the plan row's columns and replanning. The row format itself stays in `plan/chapters.md` |
| character-development | 1,551 | planner `cast-design.md` (arc ladders) · story editor `cost-and-keep.md` (lasting harm) | a rung is planned; the story editor checks that harm stays paid |
| character-profile | 2,632 | planner `cast-design.md` · continuity editor `people-and-figures.md` (placement at first appearance) | tiers A/B/C, walk-on strokes; non-human and special cases as one example each |
| combat-choreography | 769 | writer `toggle-combat.md` (toggle `combat-choreography`) | duel geography; the audit card's checks become the doc's "flat version" |
| comedy-levity | 832 | writer `toggle-comedy.md` (toggle `comedy-levity`) | |
| competence-map | 2,179 | continuity editor `provenance.md` · planner `cast-design.md` (domains) | who knows what, and how they learned it: the provenance check |
| conflict-engine | 1,776 | planner `stakes.md` (the stake ladder) · story editor `cost-and-keep.md` · writer `scenes.md` (cost on the page) | the ladder is planning; cost and aftermath are the story editor's check |
| continuity-summary | 2,091 | clerk: `kb/shared/state-format.md` (plan 02) + clerk `short-blocks.md` | the 18-line CCS block was replaced by plan 02's 7-key block. The read-set assembly is dropped: each role reads `state/` itself |
| dialogue-voice | 2,684 | writer `dialogue.md` (exists; subtext, same side) · line editor `spoken-register.md` | the corpus anti-patterns become the line editor's flat versions |
| fanfic-canon | 1,353 | planner `toggle-fanfic.md` (toggle `fanfic`) · continuity editor (canon as bible) | the continuity editor treats canon facts as bible lines; no doc of its own |
| grimdark-consequences | 675 | writer `toggle-grimdark.md` (toggle `grimdark-consequences`) | |
| hook-and-pacing | 2,123 | writer `openings-and-endings.md` · planner `arcs-and-chapters.md` (temperatures, arc rhythm, the long middle) · story editor `across-chapters.md` | the eight hook types and the temperatures stay one vocabulary, in the planner's doc |
| lead-interest | 1,028 | planner `toggle-romance.md` (with romance-arc) | the lead is a cast design question, asked only when romance is on |
| litrpg-system | 839 | planner `toggle-litrpg.md` (toggle `litrpg-system`) · writer (status screens are the meta channel, `format-spec.md`) | |
| mc-design | 2,127 | planner `cast-design.md` (the MC, the golden finger and its cost) · continuity editor `people-and-figures.md` (the form ledger) | lessons.md #22: derive a gift's cost from how it works; that becomes the doc's example |
| mc-intel-meter | 908 | writer `intelligence-on-the-page.md` · story editor `never-stupid.md` | writing intelligence, plans and lies for the writer; the idiot-ball check for the editor |
| meta-knowledge | 2,119 | planner `toggle-foreknowledge.md` (toggle on `mc.foreknowledge`) · story editor `never-stupid.md` (win before fail) | |
| mtl-detox | 714 | line editor `ai-default-habits.md` (exists) | its catalogues merge into the stock-phrase list and `tools/lint.py`'s `stock` check |
| mystery-clues | 695 | planner `toggle-mystery.md` (toggle `mystery-clues`) · story editor (fair play, as an example in `promises.md`) | |
| narrator-voice | 2,215 | writer `narration.md` · line editor channel checks in `format-spec.md` (shared, exists) + `tools/lint.py` | distance, interiority, filtering, the four channels |
| no-harem | 663 | planner `toggle-romance.md` (the no-harem setting is a line in it) | its one audit question becomes the romance doc's example |
| novel-init | 2,698 | **plan 04** (planner `init` task, the interview, the template) | register presets and the scaffold are plan 04's; not written now |
| plot-threads | 1,210 | planner `threads.md` (foreshadowing, reveals and reversals) · story editor `promises.md` · clerk (thread board mechanics, `state-format.md`) | |
| pov-switch | 1,466 | planner (a line in `cast-design.md`: who may hold the viewpoint) · writer `toggle-pov-switch.md` (toggle `pov.switch_granularity` other than `never`) | |
| power-scaling | 2,190 | planner `stakes.md` (the gap, curve shapes, failure modes) · story editor `never-stupid.md` (the gap per chapter, one line) | |
| power-system | 1,440 | planner `world-design.md` (costs and limits) · continuity editor (the system's rules are bible lines) | |
| prose-quality | 2,506 | line editor `ai-default-habits.md` (exists) + `rhythm-and-concreteness.md` | the AI-default tells are already in the catalogue |
| revision-pass | 2,694 | **dropped**: replaced by the loop | its passes now belong to roles: delivery → story editor; continuity → continuity editor; prose → line editor. Its owned-pass table is the loop |
| romance-arc | 736 | planner `toggle-romance.md` (toggle `romance-arc`) | |
| scene-craft | 1,510 | writer `scenes.md` (goal, obstacle, turn; group scenes; negotiation) · story editor `delivery-test.md` | |
| slice-of-life-texture | 806 | writer `toggle-slice-of-life.md` (toggle `slice-of-life-texture`) | on for the slice novel |
| social-fabric | 1,803 | planner `world-design.md` (labour, money, law, belief; prices and stakes; gendered experience) | |
| social-perception | 1,509 | planner `cast-design.md` (EQ against intelligence) · writer `intelligence-on-the-page.md` (reading people on the page) | |
| story-bible | 1,941 | planner `world-design.md` (the minimum bible) · continuity editor `time-and-travel.md` (geography and travel) | |
| story-craft | 1,044 | writer `scene-and-summary.md` (exists; why the important beat gets summarised) · planner `arcs-and-chapters.md` (build-up before the spend) | |
| story-opening | 2,685 | writer `orienting-the-reader.md` (exists) · planner `premise.md` + `reader-ledger.md` (exist; promise ledger, contract) + `stakes.md` (the stakes ceiling) | the opening's ledger already replaced it in plan 01 |
| tech-plausibility | 1,130 | planner `world-design.md` (one example: a speculation's second-order effect) | the genre's one idea, kept as an example, not a doc |
| timeline-engine | 1,629 | planner `world-clock.md` (the world's own plot, reaction and governor) · continuity editor `time-and-travel.md` | fanfic mode goes to `toggle-fanfic.md` |
| title-craft | 2,105 | **plan 04** (`/new` and the listing kit) | not used by the loop |
| voice-separation | 2,314 | planner `cast-design.md` (the voice matrix) · writer `distinct-voices.md` (age register, the mirror clause, channels) · line editor `cadence-test.md` | |
| world-texture | 1,645 | writer `world-on-the-page.md` (friction, sensory anchors, narrative space, overbuilding) · writer `orienting-the-reader.md` (exists) | |
| write-chapter | 2,684 | **dropped**: replaced by the loop (`kb/showrunner/loop.md`) | its failure modes are the lessons (`docs/lessons.md`), not a doc; its card index is the roles' `index.md` files |

## The review cards

`roles/review/` (`reader-brief`, `reader-review`, `reader-review-example`) were the old cold read.
They are **dropped**: the beta reader (`kb/beta-reader/`) and the judge (`kb/judge/`) replaced them in
session 1, and both are calibrated instruments that plan 03 does not touch.

## From plan 02's run (no old skill)

| finding | → destination |
|---|---|
| a block's `kno` line grew to 16 items | clerk `short-blocks.md`: a worked long block and its short version |
| "C1 can be marked landed" in *For the planner* reached no rule | story editor's notes template: a row the retell now carries, due or not, is graded under *Owed*, and the clerk sets it |
| beat-sheet items with no ledger id (T7 settles, the currency) | story editor's notes template: `beat <label>` lines under *Owed*; `tools/wire.py` accepts them |
| the continuity editor missed "that afternoon" | continuity editor `time-and-travel.md`: the worked example |
| the line editor's `across` lens | line editor `across-chapters.md`: the recurring move as an example |

## Not carried

- **Every numeric gate and budget** (speech share floors, card budgets, thought budgets, word
  bands as gates). Lessons #8: tools report, judgement decides.
- **The routing machinery** (`metadata.when`, `kb.py`, `sw load`, `readset`, the WATCH row): one
  index per role replaces it.
- **History inside docs** ("benchmark run #N shipped…"): it stays in `docs/lessons.md`.

## The coverage diff (plan 07)

Plan 07 step 1 walked `skilled-writer/docs/coverage-map.md`, all 64 areas in its five tables plus its open items,
against `kb/`, the template and `tools/`. Checking the per-skill mapping above was not enough: a
skill can be mapped while a reference inside it is not. Most rows land where the table above says.
These are the rows that did not, and what was done about each.

**Gaps found and filled**, each as an example in an existing doc (one new doc):

| coverage-map area (old owner) | → destination |
|---|---|
| the long middle, chapters 40–120 (`hook-and-pacing`) | planner `long-middle.md` (new): each arc's own question and permanent change; the four ways a middle goes flat; changing what is threatened instead of escalating; the reader's clock |
| the material curve: money stops deciding as the MC climbs (`social-fabric` §7) | planner `stakes.md`: *When money stops deciding*. The three `means.*` config keys are not carried; the arc is a planning decision, not a field |
| the pace contract: the rate the opening promises (`story-opening`) | planner `arcs-and-chapters.md`: *The rate the opening promises*. `tools/history.py`'s tempo runs report the later chapters |
| non-human minds: beasts, constructs, gods (`character-profile`) | planner `cast-design.md`: *A mind that is not a person* (the three questions). As a narrator it was already in writer `toggle-pov-switch.md` |
| oaths, ritual and taboo (`social-fabric`) | planner `world-design.md`: *An oath the plot can stand on*. Belief as a whole was already its sixth line |
| gendered experience: the stance table (`social-fabric`) | planner `bias-structural.md`: a stance per character, any stance for any gender |
| the acquisition ladder (`competence-map`) | writer `scene-and-summary.md`: *Learning, in the margins* (the practice gets a clause, the stage change gets the scene) · continuity editor `provenance.md`: *The skill with no source* |
| structural clichés: the face-slap loop, the gasping crowd (`mtl-detox` Part 2) | story editor `cost-and-keep.md`: *The free win*, with the five replacements · line editor `ai-default-habits.md`: *the gasping crowd* row |

**Rows that looked like gaps and are covered:**

| coverage-map area | where it is |
|---|---|
| world facts by chapter 1–5 (`chapter-plan`) | the reader ledger's `due by ch` (planner `reader-ledger.md`) |
| the ending contract and its non-negotiables (`timeline-engine`) | `plan/arcs.md` → *The ending*: "who or what must survive it" |
| theme, Pass 9d (`revision-pass`) | its measured failure, the narrated lesson, is line editor `ai-default-habits.md` *the aphoristic close* and *the explained subtext*; the counter-case is the antagonist's `case` (planner `cast-design.md`, `plan/arcs.md`) |
| overbuilding and narrative space (`world-texture`) | writer `world-on-the-page.md`: description as the most expensive mode; *Felt and handled* |
| negotiation and group scenes (`scene-craft`) | writer `scenes.md` |
| lasting harm and aftermath (`conflict-engine`, `character-development`) | story editor `cost-and-keep.md`: *The healed wound*, against the block's `cost` line |
| MTL prose artifacts (`mtl-detox` Part 1) | line editor `ai-default-habits.md` stock phrases, and `tools/lint.py`'s stock check |
| rank recitals, cannon fodder, the treasure escalator (`mtl-detox` Part 2) | writer `orienting-the-reader.md` (*Someone who needs to know asks*) · story editor `never-stupid.md` (opposition made blind to lose) · planner `stakes.md` (the ladder, not the treadmill) |

**Waived, with the reason:**

- **Release cadence** (`hook-and-pacing`): when chapters are posted is the author's, not the room's.
- **The divergence ledger's per-arc rule** (`timeline-engine`, `sw arc`): a check on a table's
  emptiness. The idea survives as planner `world-clock.md` (the world reacts to the protagonist)
  and `toggle-fanfic.md` (one divergence point).
- **The one-sided-rule sweep and the inverse shape** (*Still open*): both are about numeric
  floors (`thought-budget`, speech share) that were not carried (lesson 8).
- **The *deliberately not given an owner* list:** nothing to carry. It records refusals, and this
  repo refuses the same things.

## The `sw` commands (plan 07)

Plan 07 step 2. Every `sw` command and hook in `skilled-writer/scripts/`, and what became of it.

| `sw` command | → here | |
|---|---|---|
| `lint` | **ported**: `tools/lint.py` | channels, stock phrases, numbers, lexicon spellings; no budgets or floors |
| `history` | **ported**: `tools/history.py` | the motif, signature, two-hander and tempo detectors; the rest of its series (dialogue trend, thread ages, pressure) dropped with the numbers they fed |
| `state` | **ported**: `tools/state_check.py` | for the new state format; the step-proof lines (`cand>`, `z4>`, `gav>`) went with the gate |
| `status` | **ported**: `tools/status.py` | plus the ledger's debt (`--debt`) |
| `newnovel` | **ported**: `tools/scaffold.py new` | plus `scaffold.py check`, which init did not have |
| `trace` | **ported**: `tools/trace.py` | per role and chapter, now with effort, cache expiries, injected context and the cross-check; card counts became the docs-opened log (`guard.py`) |
| `readset` | **replaced** by each role reading `state/` and its own `kb/<role>/index.md` | the WATCH row's job is `history.py`'s, read by the editors from ch 3 |
| `audit` | **replaced** by the loop | each check has an owning role; `lint` and `state_check` run every chapter |
| `arc` | **replaced** by `history.py` and the planner's arc rows | its distributional pass was mostly numeric floors |
| `cast` | **dropped** | the voice-matrix audits were numeric (straddle, wit cap, turn-length means). The matrix stays in `_voices.md`; the line editor's `cadence-test.md` reads it; `scaffold.py check` warns on a name another novel uses |
| `curve` | **dropped** | power-curve step sizes and boost debts: numbers a drafter writes toward. The gap is planner `stakes.md` and story editor `never-stupid.md` |
| `stamp` | **dropped** | no word count is a gate (lesson 8); `lint.py --stats` measures when asked |
| `export --okf` | **dropped** | the knowledge bases are OKF; a novel needs no OKF bundle. `export_prose.py` is the export that matters, prose only |
| `load`, `kb`, `contract`, `health` | **dropped**, as expected | the corpus they routed and policed (cards, budgets, owners, contracts rendered from `CLAUDE.md`) does not exist. `kb_check.py` checks the knowledge bases' shape |
| `selftest`, `doctor` | **dropped** | the unit tests (`python3 -m unittest discover tests`) replace both |
| hooks `reader_guard`, `role_scope`, `write_scope` | **replaced** by `tools/guard.py` | one hook, one table of roles and paths |
