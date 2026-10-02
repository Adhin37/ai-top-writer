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
   - **Pin full model ids** in every agent's frontmatter for the run (`claude-opus-5-5`, not `opus`).
     In plan 02 the `sonnet` alias moved across a usage-limit pause, and eight agents ran on a
     different model.
   - The showrunner picks the seed and logs why.
   - Write the answer sheet.
2. **Init**, via `/new`: the interview, with the user's answers from the sheet.
3. **Five chapters** via `/write`.
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

*(filled in when this plan runs)*
