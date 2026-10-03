# 05 — Session 6: benchmark run #7

**Goal:** the first comparable measurement of the rebuild, and the roadmap's **one complete test
run**. The plans before it checked their changes by parts, each in the next real run, so this is
where everything is exercised together, end to end. A fresh novel, set up with plan 04's init
and written through the full loop, for five chapters. It is judged blind and by the user, and
compared with skilled-writer's run #6 (3.5 / 5 from the reader; confusing to the user from chapter 1
on).

## Step 1 — write the protocol first

Write `docs/test-run-protocol.md`. It is a slim port of skilled-writer's 504-line protocol, and it
keeps only what a run has cost before:

- **The showrunner never touches the novel.**
  - It writes nothing under `novels/` during a run. Arm it: `touch .test-run`. `tools/guard.py`
    then refuses the main session's writes under `novels/`, and deleting the file disarms it.
  - It never repairs a chapter by hand. A repaired run measures the human (skilled-writer run #4).
- **Toolkit frozen.** No edit to `kb/`, `.claude/`, `tools/` during the run. Findings are written
  down, not fixed.
- **Intervention policy.**
  - Beat sheets are approved as written unless they break the event or the ledger.
  - Interview answers come from an answer sheet written before the run.
  - No craft direction mid-chapter.
  - When praising, name the technique and never quote the line back: quoting it feeds it into the
    next chapter.
  - Every exchange is logged verbatim.
- **No rehearsal chapter.** The stop is **five chapters unless the user says otherwise**. A queue
  item in any plan is a proposal, not an instruction (skilled-writer run #6, M1 and M3).
- **A fresh session**, with the agents probed for what they were handed before chapter 1.
- **Write findings down in the turn they are seen**, into the working log in `docs/experiments/`.
  Never into the scratchpad, which is emptied mid-session.
- **The showrunner's own impression of the prose is written before the judge runs.**
- **The judge is blind:** a prose-only export, a neutral path, three fresh judges, `claude-opus-5`,
  the questionnaire in `kb/judge/`. Afterwards, ask each judge what it was handed, and record its
  answer as a contaminant.
- **Reconcile and route.** Every judge finding is checked against the page and then routed to the
  role and knowledge base that owns it. Its outcome is **an example, a ledger entry, or a rule that
  replaces one**. It is never a rule appended.
- **No numeric ship gate is ever added as a fix.** This was learned three times.

Carry over the old *traps* table only where it still applies:
- scope any trace by session id;
- read subagent usage from per-agent transcript files;
- grep prose with line breaks flattened;
- zsh does not word-split variables.

## Step 2 — the run

1. **Pre-flight.**
   - Tests and `kb_check` pass. Record the commit SHA, the UTC start time and the configuration table.
   - **Full model ids are pinned** in every agent's frontmatter (`claude-opus-5-5`,
     `claude-sonnet-5-5`; the judge `claude-opus-5`), done at the close of plan 04 so the run's
     fresh session registers them. Check them, and read each role's model back from the
     transcripts after the run. In plan 02 the `sonnet` alias moved across a usage-limit pause, and
     eight agents ran on a different model.
   - **Name the novel in every command** (`/write 1 <slug>`, `/status <slug>`). `novels/` holds
     more than one novel (the slice novel and plan 04's throwaway), and a command with no slug
     asks the user which, which stalls an unattended run.
   - The showrunner picks the seed and logs why.
   - Write the answer sheet.
2. **Init**, via `/new`: the interview, with the user's answers from the sheet.
   - Plan 04 ran init once, from another seed: clean on the first check, $8.16. Choose a seed and
     names away from the model's defaults (lesson 26).
   - `/new` ends with the leak sweep. A hit renames the knowledge-base example before chapter 1.
     That is `/new`'s own procedure for any user, so it is not a fix under the freeze; log it.
3. **Five chapters** via `/write`.
   - Plan 04 left these unexercised, and this run checks them:
     - `/write` itself, and chapter 1 of a novel init made;
     - `/status` after each chapter, checked against the files;
     - `/plan`, if the rows run short;
     - the round-6 re-ask and the round-5 mix, only if they arise.
   - The chapter-1 check: the beta reader's retell, graded against `premise.md`, must state the
     central rule. If it does not, the loop revises. This is the loop working, not an intervention.
   - Log per chapter: rounds, notes, stets, the reader's click-next, words, and model time and cost
     per role. Time and cost come from `tools/trace.py` (built in 01b), scoped by session id.
4. **Stop at five.** Write the showrunner's impression.

## Step 3 — judging

- **Three fresh judges** read all five chapters blind, with the full questionnaire. Their retells are
  graded against `premise.md`, and their verdicts are on a 0–5 scale anchored to behaviour.
- **The judges' verdict is the run's verdict.** The user reads nothing (standing decision).
- **The comparison table** against run #6 covers:
  - verdict;
  - chapter 1 comprehension;
  - the top-ranked findings;
  - cost per 1,000 words (run #6: $4.76);
  - model time per chapter.

## Step 4 — the write-up

`docs/experiments/<date>-run-7.md` holds:
- configuration;
- per-chapter table;
- judges;
- **the feature table**: every feature 01–04 built, whether this run exercised it, and whether it
  worked;
- reconciliation and routing;
- limitations;
- what run #8 must do.

Then fix what the run found, after the run, each fix following the routing rule above, and update
`docs/lessons.md` with anything newly learned.

## Exit criteria

- The feature table is complete. Every feature built in 01–04 ran, and each worked or its failure
  is routed. The roadmap README's *Features* table is updated from it.
- Every finding is routed.
- The comparison with run #6 is written, and its confounds are named. The novels, the models and the
  pipeline all differ.

## Session log

**2026-10-03, session `9ae41156`.** Run log and write-up:
[docs/experiments/2026-10-03-run-7.md](../experiments/2026-10-03-run-7.md). Protocol:
[docs/test-run-protocol.md](../test-run-protocol.md).

- **Step 1, the protocol:** written first, a slim port of skilled-writer's (~170 lines from 504),
  keeping only what a run has cost before.
- **Step 2, the run:**
  - **Pre-flight:** 207 tests, `kb_check` clean, every agent on a full model id. Seven probes:
    none carried `CLAUDE.md` or a memory index.
  - **The probes found one contaminant (C0):** the git status named this run's log and protocol.
    Both were hidden with `.git/info/exclude` for the run.
  - **The seed** was grown houses that starve, chosen away from the room's earlier worlds and naming
    nobody. The answer sheet was written first.
  - **Init:** `/new` in 7 rounds, check clean first pass, $6.70. The leak sweep renamed two writer
    examples (Pell, Sallow): `/new`'s own step, the only `kb/` edits during the run.
  - **Five chapters** through `/write` and the loop, no file touched by hand: 13 rounds, 31 notes,
    no stets, click-next 4, 4, 5, 4, 5. Chapter 1 was accepted at round 0, with the central rule
    `stated` in the reader's retell. Every other chapter went to round 2.
  - **`/status`** ran after each chapter and matched the files but for one line (F2). **`/plan`**
    ran once.
  - **Two usage limits**, both resumed warm in the same session; one `/handoff` by the user.
- **Step 3, judging:**
  - The showrunner's impression was written before any judge.
  - **Three fresh blind judges gave 4.5, 4.5, 4.5.** Their retells, graded by three more, state
    **18 of 18** premise facts.
  - **Contaminants:** each judge, asked after its verdict, named the git status (C1). The
    leak-sweep renames showed as modified `kb/writer/` files.
- **Step 4, the write-up:**
  - the feature table (every 01–04 feature ran but four paths that did not arise), the comparison
    with run #6 and its confounds, and every finding routed;
  - **fixed after the write-up, by the routing rule:**
    - five knowledge-base changes: three examples (`toggle-mystery`, `stakes`, `world-clock`) and
      two rules that replace one (`ai-default-habits`, `across-chapters`);
    - two tools, each with a test that fails on the old code: `status.py` reads `moved to chN`;
      `wire.py` accepts `none`;
    - the protocol's judging step and traps; lessons 26–29;
  - tests 207 → 209.

**Exit criteria:** met.
- The feature table is complete, and the README's *Features* table is updated from it.
- Every finding is routed.
- The comparison with run #6 is written, its confounds named.

`.test-run` and the `.git/info/exclude` lines were removed after the write-up. `novels/grown-houses/`
and `novels/varrow-bells/` are kept (gitignored). Nothing committed.
