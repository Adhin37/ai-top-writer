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
stops at each round with numbered questions and a recommended answer for each.

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

Start a small throwaway novel from a seed the user picks. Run init end to end, then write chapter 1
with `/write`. The user judges:
- whether the interview was worth their time;
- whether the premise was right;
- whether the chapter oriented them.

Delete the throwaway novel afterwards only if the user says so.

## Verification

- Init produces every file the template has, with no placeholders left.
- The chapter-1 check: a fresh beta reader's retell of chapter 1, graded against `premise.md`, states
  the central rule.
- `/status` output is correct against the files.

## Exit criteria

The user can go from an idea to an approved chapter 1 in one sitting, without touching a file
themselves.

## Session log

*(filled in when this plan runs)*
