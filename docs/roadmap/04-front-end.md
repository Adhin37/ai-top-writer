# 04 — Session 5: novel setup and planning from scratch

**Goal:** a user can start a brand-new novel in this repo, answer an interview, and get a bible,
cast, premise, reader ledger and arc plan that the writers' room can write from. Plans 01–03 all ran
on skilled-writer's run #6 bible, and this is the session that stops depending on it.

## Steps

### 1. The novel template

Create `novels/_template/`, following [novel-format.md](../novel-format.md):
- `novel.md`: a slimmer config than the old one. Keep a key only if a role reads it.
- `bible/`: `premise.md`, `world.md`, `society.md`, `lexicon.md`, `cast/`.
- `plan/`: `arcs.md`, `chapters.md`, `reader-ledger.md`.
- `state/`: empty seeds.
- `chapters/`.

`.gitignore` already lets `_template/` through.

### 2. The planner's init mode

This is an interview in rounds. The planner asks and the showrunner relays the user's answers. It
stops at each round with numbered questions and a recommended answer for each. That is the product
feature. **In rebuild test runs the user answers nothing:** the showrunner writes an answer sheet
before init starts, answers every round from it, and logs each pick.

1. **Seed and platform.** The premise in one line, the platform, the audience. The platform sets the
   defaults: Royal Road and webnovel.com mean **exposition: clear**, per the user's standing decision.
2. **Genre, tone, POV, MC.** The old `mc-design` material: the MC's appearance, intelligence and EQ,
   what they want and need, the golden finger with a cost derived from how it works, and its limit.
3. **World and society.** One central rule, propagated into labour, money, law and belief.
4. **Cast.** Voice matrix, competence, the antagonist and **when their face reaches the page**. That
   is by the opening contract chapter at the latest (run #6's top finding).
5. **Style.** The user picks a register:
   - the **writer drafts the same short beat three ways** (about 150 words each, in different
     registers), and the user picks one or mixes them;
   - the chosen sample goes into `novel.md` as the style anchor;
   - this replaces naming authors to imitate, which in run #6 led the architect to pick literary
     withholding for a Royal Road book.
6. **Premise and reader ledger.** The planner writes `premise.md` and the ledger, and the user reads
   the premise. **If the user cannot say it back in their own words, it is rewritten.**
7. **Title, blurb and the arc plan**, with a temperature and a hook type per chapter row, and the
   first 10–15 rows.

### 3. The showrunner's commands

In `.claude/commands/`:
- `/new`: runs init.
- `/plan`: extends the arc plan and the ledger, and checks what the ledger owes against what the
  plan delivers.
- `/write [n]`: the loop, per `kb/showrunner/loop.md`.
- `/status`: where the novel stands: chapters, open promises, ledger debt, the reader's latest
  click-next.

Each command is a short procedure that points at `kb/showrunner/` and does not restate it.

### 4. Try it

The showrunner picks a seed and writes the answer sheet, then starts a small throwaway novel. It
runs init end to end, answering from the sheet, then writes chapter 1 with `/write`. It checks:
- every interview round asked and stopped, and the recommended answers were usable;
- the premise restates the answer sheet and adds nothing;
- the chapter-1 check below.

Keep the throwaway novel until 05 has run; it is gitignored.

## Verification

- Init produces every file the template has, with no placeholders left.
- The chapter-1 check: a fresh beta reader's retell of chapter 1, graded against `premise.md`, states
  the central rule.
- `/status` output is correct against the files.

## Exit criteria

Init and `/write` take a seed to an accepted chapter 1 in one session, with no file touched by
hand. The *Features* table in the roadmap README is updated.

## Session log

**2026-10-02/03, session `6cf7e805`.** Run log:
[docs/experiments/2026-10-02-init.md](../experiments/2026-10-02-init.md).

- **Step 1, the template:** `novels/_template/`. `novel.md` keeps only keys a role or tool reads
  (listed in [novel-format.md](../novel-format.md)). The run #6 blocks are dropped: scaling, means,
  theme, chapter length, `style.read_like`. The body is the blurb and the **style anchor**. The
  bible is premise, world, society, lexicon and `cast/` (`_voices`, `_extras`); the plan is arcs,
  chapters, the ledger and `timeline.md` (the world's clock, which `world-clock.md` already named);
  `state/` has empty seeds. Every value to fill is a `{{…}}` placeholder.
- **Two tools.** `tools/scaffold.py`: `new` copies the template, `check` reports whether init
  finished (files, placeholders, keys, premise, ledger against premise and antagonist,
  rows, cast, the thread board, the rounds). `tools/status.py`: where a novel stands, and `--debt`
  for `/plan`.
- **Step 2, the planner's init mode:** `kb/planner/init.md`, the seven rounds, with a round file
  per round: questions for the user, then the answers verbatim, so a fresh planner can resume.
  `title-and-blurb.md` is distilled from `title-craft`. A profile example went into
  `cast-design.md`. `Task: init` and `Task: plan` are in the prompt.
- **New status lines:** `PLANNER ASKS` (a round that stops for the user) and `SAMPLES READY` (the
  writer's style samples, `kb/writer/registers.md`).
- **Step 3, the commands:** `/new`, `/write`, `/plan`, `/status` in `.claude/commands/`, each
  pointing at a showrunner doc (`init.md`, `loop.md`, `plan.md`, `status.md`). They registered
  mid-session, and init ran through `/new` itself.
- **Step 4, init only** (the user's choice, against the plan's "init and chapter 1"). The seed was
  a bell-oath city (why this one: in the log), answered from an answer sheet written first. Seven
  rounds, all stopped and answered. The check was clean on the first pass, nothing went back to the
  planner, and no file was touched by hand. 24 of 34 answers took the recommendation; the other 10
  were folded in. The premise restates the answers and adds nothing. **$8.16.**
- **Fixed during the run:** `status.py` and `state_check.py` read "arc 2" in a ledger due cell as
  chapter 2 (`due_chapter`). The leak sweep now ends `/new`, after it found model-default names
  shared between the novel and the examples (lesson 26). Tests 182 → 207.
- **Not exercised, carried to 05:** the chapter-1 check; `/write`, `/plan` and `/status` as
  commands; the round-6 re-ask and the round-5 mix (neither arose); the `AskUserQuestion` relay,
  which no test run uses.

**Exit criteria:** init's half is met (a seed to a checked novel in one session, no file touched by
hand). `/write` to an accepted chapter 1 moves to plan 05's first chapter. The *Features* table is
updated. `.test-run` was removed after the write-up. `novels/varrow-bells/` is kept until 05 has
run. Nothing committed by this session.
