# 01 — Session 2: vertical slice, chapter 1 A/B/C

**Goal:** find out, before anything else is built, whether the writers' room produces a chapter 1
that a newcomer understands *and* wants to continue. Test it on the same bible that produced
run #6's confusing chapter 1.

**Hypothesis:** four things together fix the opening:
- a writer holding intent, examples and a format spec instead of thirty rules;
- a reader ledger that schedules the premise for chapter 1;
- an in-loop beta reader who has no bible;
- a story editor who turns the reader's evidence into specific notes.

**The loop, for this session:** planner → writer → beta reader → story editor → writer (warm) → fresh
beta reader → … → line editor. The continuity editor and the clerk are not needed for one chapter;
they come in [02](02-full-loop.md).

## Prerequisites

- Session 1 is done: this repo has the six agents, their `kb/<role>/prompt.md`, `tools/guard.py` and
  `tools/export_prose.py`, and tests pass.
- **The session is opened in the repo root**, and the folder is trusted when
  Claude Code asks. Project hooks need workspace trust.
- The old repo exists read-only at `../skilled-writer`.

## Rules for this session

- **The showrunner (main session) writes no prose and edits no chapter.** It copies files, runs
  tools, spawns agents and relays their output verbatim. If a role's output is wrong, fix the role's
  `kb/<role>/prompt.md` and re-run the role. Never repair the output by hand: a repaired chapter
  measures the showrunner. Log every such change.
- **Agent prompts may be edited mid-session.** The agent files are thin and read
  `kb/<role>/prompt.md` at runtime. Every edit is logged in the session log with its reason.
- **Write the go/no-go criteria down before the first draft** (they are below; amend them only
  before step 4).

## Steps

### Step 0 — environment (about 10 minutes)

1. `python3 -m unittest discover tests`: all pass.
2. Spawn each of the six agents with: *"Probe: name your role and quote the first line of your
   prompt file. Open nothing else."* Each must answer correctly.
3. In each subagent transcript (`~/.claude/projects/-home-adhin-projects-ai-top-writer/<session>/subagents/*.jsonl`),
   check the `message.model` of the first response:
   - `opus` for planner, writer, story editor and judge (the judge is pinned to `claude-opus-5`);
   - `sonnet` for beta reader and line editor.
4. Guard check, after step 1 copies the novel: ask a beta reader to open
   `novels/unwritten-surveyor/bible/world.md`. **It must be refused.** If it is not, stop: the
   experiment is invalid without isolation. The likely cause is untrusted hooks.

### Step 1 — set up the novel and the arms

1. Copy from the old repo, **without `chapters/` and without `state/`**:
   `novels/unwritten-surveyor/{novel.md,bible,plan}` → `novels/unwritten-surveyor/`.
   - Chapter 1 needs no prior state.
   - The bible is the post-run version, and it includes facts run #6's folds added (for example,
     that Ruck cannot read a form). **Record this confound.** It slightly favours the new arms, and
     there is no pre-run snapshot to use instead.
2. **Arm A** is run #6's final chapter 1. Copy
   `../skilled-writer/novels/unwritten-surveyor/chapters/0001-the-last-marker.md`
   to `bench/ch1-abc/originals/A.md`.
3. **Calibration control.** Fetch chapter I of H. G. Wells, *The Time Machine* (public domain,
   Project Gutenberg #35) into `bench/calibration/originals/control.md`. It explains an invented
   premise on the page, at a dinner table. The showrunner writes `bench/calibration/control-premise.md`:
   - a man claims time is a fourth dimension that can be travelled like the other three;
   - he demonstrates a small model machine that vanishes;
   - he says a full-size machine is nearly finished.

### Step 2 — the premise sheet (planner)

Spawn the **planner**: *"Novel: novels/unwritten-surveyor. Write bible/premise.md per your procedure.
Restate only; add no fact the bible does not contain."*

The showrunner then checks that every premise fact cites a line in `bible/` and adds nothing. **A
fact with no source line is an invented fact:** send it back.

The premise must contain the resettling range, the Reading as the only foreknowledge of where roads
will lie, and the Guild's job of sealing what the Reading declared. If it is missing any of those,
the planner has misread the bible: send it back.

### Step 3 — calibrate the beta reader (the gate for everything after)

The instrument must fail where the user failed, and pass where a clear text passes.

1. Export each calibration text to **its own neutral folder per reader instance**, so no instance can
   see another's report:
   `python3 tools/export_prose.py bench/ch1-abc/originals/A.md --reading-dir reading/cal-a1`
   (and `cal-a2`, `cal-a3`, `cal-c1`, `cal-c2`, `cal-c3` for the control).
2. Spawn **six fresh beta readers**, one per folder: *"Your reading folder is reading/{dir}/. Follow
   your procedure."*
3. Spawn a fresh **judge in grading mode** for each report, with the report and the matching premise
   copied into `bench/calibration/blind/grade-{n}/`. It marks each premise fact **stated**,
   **partly**, **missing** or **wrong**, quoting the retell.
4. **Pass:**
   - on A, at least 2 of 3 readers score the central-rule fact (the range resettles / the Reading
     says where roads lie) as *missing* or *wrong*;
   - on the control, at least 2 of 3 score it *stated*;
   - both "terms I had to guess" lists are non-empty on A.
5. **If it fails:**
   - revise `kb/beta-reader/prompt.md` (for example: retell only what the page says, and mark every
     inference as a guess) and re-run;
   - at most 3 iterations, each logged;
   - if it still fails, stop the session and write up why: an in-loop reader that cannot see the
     problem cannot fix it.

### Step 4 — plan chapter 1 (planner)

Spawn the **planner**: *"Write plan/reader-ledger.md for arc 1, then the chapter 1 beat sheet at
novels/unwritten-surveyor/work/ch0001/beats.md, per your procedure."*

**Held constant from run #6's plan row 1:**
- the goal: close out the season's last routine boundary survey cleanly;
- the event: *Wren signs the Charter filing on a marker he privately believes is wrong*;
- the turn: Wren alone notices the discrepancy is real, not error;
- the title (*The Last Marker*);
- `novel.md` unchanged, style target included.

The ledger must put every premise fact in chapter 1's column. The showrunner approves the beat sheet
**as written** unless it changes the event, and logs it either way. The user may look at it but does
not edit it, so the experiment measures the loop.

### Step 5 — the loop, run twice

Run the whole loop twice, **L1** and **L2**, from the same beat sheet, each time with a fresh writer.

For each run k:

1. **Writer, round 0.** Spawn the **writer**, named `writer-k` so it can be continued: *"Novel:
   novels/unwritten-surveyor. Chapter 1. Beat sheet: work/ch0001/beats.md. Write
   work/ch0001/L{k}/draft-r0.md per your procedure."*
2. **Beta reader.** Export the draft:
   `python3 tools/export_prose.py novels/unwritten-surveyor/work/ch0001/L{k}/draft-r0.md --reading-dir reading/L{k}-r0`.
   Then spawn a fresh beta reader on that folder.
3. **Story editor.** Spawn the **story editor**: *"Chapter 1, run L{k}, round 0. Draft:
   work/ch0001/L{k}/draft-r0.md. Reader report: reading/L{k}-r0/report.md. Write
   work/ch0001/L{k}/notes-r0.md per your procedure."* The verdict is **ACCEPT** or **REVISE** with at
   most 5 notes.
4. **On REVISE:**
   - send the notes to `writer-k` with `SendMessage` (warm): *"Notes: work/ch0001/L{k}/notes-r0.md.
     Write draft-r1.md."* The writer may **stet** a note with a reason.
   - Export the new draft to `reading/L{k}-r1`, spawn a **fresh** beta reader, then the story editor.
   - **At most 2 revision rounds.** After round 2 the last draft is accepted, and the editor's open
     notes are logged as unresolved.
5. **Line editor.**
   - It polishes the accepted draft once, into `work/ch0001/L{k}/final.md`.
   - It also polishes `draft-r0.md` once, into `work/ch0001/L{k}/r0-polished.md`, so every arm has
     had exactly one line pass.
   - The line editor cannot reach `bench/`. The showrunner copies:
     - `final.md` → `bench/ch1-abc/originals/C{k}.md`;
     - `r0-polished.md` → `bench/ch1-abc/originals/B{k}.md`;
     - L1's `final.md` → `novels/unwritten-surveyor/chapters/0001-the-last-marker.md`. The
       showrunner writes no prose; this is a file copy, and it is logged.

Record per round: words, the reader's retell grade, the verdict, and the number of notes and stets.

### Step 6 — judging, blind

1. Export every arm (A, B1, C1, B2, C2) prose-only into `bench/ch1-abc/blind/`, named with random
   letters. The mapping goes in `bench/ch1-abc/key.md`, which the judge cannot open.
2. **Single reads.** Each text goes to 3 fresh judges, each seeing only that text:
   - the questionnaire (retell, would-continue, 0–5 with reasons, what confused them, where they
     skimmed);
   - retells are graded against `premise.md` by a fresh judge in grading mode.
3. **Pairwise.** A–C1, A–C2, B1–C1 and B2–C2, each by 3 fresh judges, with the order swapped
   between judges.
4. **The user's reads: dropped** (2026-09-27, standing decision: the user reads nothing during the
   rebuild). The judges carry them: criterion 2 (single reads) and criterion 6 (pairwise).

### Step 7 — cost and time

- Run the old toolkit's trace against this session:
  `python3 ../skilled-writer/scripts/sw.py trace --session <this session id>`,
  using `--transcripts` if needed.
- If it cannot read another project's transcripts, sum `usage` from the subagent JSONL files with a
  throwaway script in the scratchpad. Porting the trace properly is [06](06-measure-and-optimise.md).
- Record per role: responses, model seconds, and cost. For comparison, run #6 cost $5–8.50 per
  chapter.

## Go / no-go (fixed before step 4)

**GO** requires all of:
1. Calibration passed (step 3).
2. For **both** C1 and C2, at least 2 of 3 single-read judges state the central rule correctly
   (graded *stated*).
3. *Dropped 2026-09-27; carried by 2.* It was: the user, reading C1 cold, can state the central
   rule, Wren's situation and the stakes.
4. *Dropped 2026-09-27; carried by 6.* It was: the user prefers C1 to A.
5. At most 1 of 3 judges per C arm reports skimming an explanation or lecture.
6. C beats A in at least 4 of the 6 pairwise A–C judgements.

**ITERATE** (fix, then re-run step 5 once) when comprehension passes (2) but the prose reads flat,
lectures or is skimmed (5 fails):
- revise the writer's examples in `kb/writer/orienting-the-reader.md`;
- revise the story editor's note protocol.

**NO-GO** when C fails comprehension like A. Writing the premise into the plan and putting a reader
in the loop did not fix orientation. Stop, write it up in the session log, and revise
[architecture.md](../architecture.md) before any further plan runs.

**B vs C** says whether the loop adds anything beyond the plan fix, and it informs plan 02:
- B ≈ C: the loop is overhead, and the ledger did the work;
- C > B: the loop earns its cost.

## Known confounds, to write down, not fix

- **Model:** run #6 was Sonnet 5 throughout, and the new writer is Opus. Quality is the goal, so
  model and pipeline are not separated.
- **Bible:** the post-run bible contains facts run #6 invented on the page.
- **The user has read A**, so their A judgement is not blind.
- **n is small:** two loop runs and three judges per comparison. Differences under about 2 of 6 are
  noise.

## Files produced

- `novels/unwritten-surveyor/`: `bible/premise.md`, `plan/reader-ledger.md`, `work/ch0001/**`, and
  `chapters/0001-the-last-marker.md`.
- `reading/*`: exports and beta-reader reports (gitignored).
- `bench/ch1-abc/*` and `bench/calibration/*`: arms, blind copies, key, verdicts (gitignored).
- **`docs/experiments/2026-MM-DD-ch1-abc.md`**: the write-up, which is committed. It holds:
  - configuration;
  - calibration results;
  - per-round loop table;
  - judge tables;
  - user verdict;
  - cost and time;
  - confounds;
  - GO / ITERATE / NO-GO;
  - what changes in plan 02.

## Verification

- The experiment write-up exists, and every number in it traces to a file in `bench/` or `reading/`.
- No file under `novels/` was written by the main session except the step 1 copy. Check the session
  transcript's `Write`/`Edit` calls.
- Every mid-session prompt change is logged, with its reason.

## Out of scope

The continuity editor, the clerk, chapters 2+, the full knowledge bases, novel setup, and token
optimisation.

## Session log

**2026-09-26 → 27. Steps 0–7 run; step 6.4 (the user's reading) outstanding.** Full log and write-up:
[docs/experiments/2026-09-26-ch1-abc.md](../experiments/2026-09-26-ch1-abc.md).

- **Calibration passed first time**: A's central rule missing/wrong 3/3; the control stated 3/3 (all
  three control readers recognised Wells — an upper bound).
- **Loop**: L1 took all three rounds (REVISE, REVISE, ACCEPT); L2 was accepted at round 0, so B2 = C2
  and the B2–C2 pairwise was not run.
- **Judging**: central rule stated — A 0/3, B1 2/3, C1 2/3, C2 1/3 (the C2 misses are one corollary
  clause the graders split on); pairwise C over A 6/6, C1 over B1 3/3; mean scores A 3.67, B1 4.00,
  C1 4.17, C2 4.33; skimmed an explanation in 11 of 12 reads.
- **Provisional verdict: ITERATE** (criterion 5 fails on both C arms; 2 fails strictly on C2), final
  after the user's cold read of C1 and B1/C1 pick.
- **Cost**: $38.03 in all; the room $6.04 (L1) and $2.85 (L2) a chapter plus $2.12 planning; the
  showrunner $19.96.

Changed during the session, each logged with its reason: the beta reader hands its report back as
text (Claude Code refuses a subagent's report file); `tools/handback.py` (+5 tests) files hand-backs
verbatim; `kb/showrunner/loop.md` step 3 names it; the control is sections I–II of Gutenberg #35.
`.test-run` is still armed. Nothing committed.

**Follow-up (2026-09-27):** this session's transcripts showed that what the agents wrote for each
other ran long, and that the one-line hand-back contracts were not kept. The story editor wrote ~700
words before `NOTES READY`, and the notes files ran 1,370–2,060 words for 0–2 notes. Every hand-back
was re-read on each later showrunner turn: 116k tokens, 9.8M re-reads. That became
[01b](01b-wire-format.md). **Order:** step 6.4 (the user's cold read) → 01b → this plan's ITERATE
re-run, whose fixes to the writer's examples and the note protocol go into 01b's wire templates.
That re-run is also the wire format's first live run; it works through 01b's checklist (01b §5–8).

**ITERATE re-run (2026-09-27, session `bb94d8f1`).** Log and write-up:
[docs/experiments/2026-09-27-ch1-iterate.md](../experiments/2026-09-27-ch1-iterate.md). Step 6.4 was
still outstanding, and the user asked for the re-run first.

- **Levers:** `kb/writer/orienting-the-reader.md` example 3, the narrator block → *"the rules as
  somebody's problem"*; the story editor's note protocol (N2, a briefing note from its own reading)
  plus its step 3 and ACCEPT rule.
- **Loop L3:** REVISE (4 notes), REVISE (1: *"the ridge argument stops for a briefing"*), ACCEPT.
  The loop raised the lecture as a note for the first time. C3: 2,617 words, the first arm in the
  band.
- **Judging** (the user chose C3 single reads + C1–C3):
  - central rule stated 2/3, the resettling 3/3;
  - mean score 4.00;
  - **skimmed an explanation 3/3, all on the one Reading paragraph** (C1 had two to three skimmed
    places);
  - C1–C3 pairwise C3 2/3, but each judge picked the text it read first;
  - all three called C3's rule clearer.
- **Verdict: still not GO.** Criterion 5 fails, and the one iteration is spent. Comprehension holds.
  The remaining paragraph is staged by the beat sheet (*"In free indirect: …"*), which was held
  constant. **Recommended:** go on to 02 and move the lever to the planner's beat-sheet example,
  The alternatives (accept criterion 5 in spirit, or re-plan
  chapter 1) are in the write-up.
- **Cost:** $13.94 in all. The room $6.04, the same as L1; judges $1.48; the showrunner $6.42,
  against $19.96 in plan 01.
- **Changed during the session, each logged with its reason:**
  - `kb/story-editor/prompt.md`: the notes header now reads `owed 5/6`, like the status line;
  - `kb/line-editor/prompt.md`: *"Exactly these lines"*, with extra flags as `left` lines;
  - `tools/trace.py` counts hand-backs queued mid-turn, with a test.

  `.test-run` was removed after the write-up.

**Closed (2026-09-27), by the showrunner.** The user decided that during the rebuild they read and
pick nothing, so step 6.4 and criteria 3–4 were dropped (the judges' 2 and 6 carry them).
- **Verdict: ITERATE done, going on.** Comprehension passes, and C beat A 6/6. Criterion 5 alone
  fails, on one paragraph the beat sheet staged. The lever moved to the planner
  (`kb/planner/beat-sheet.md`), and plan 02 checks it.
- **Chapter 1 = C3.** L3's final was copied to `chapters/0001-the-last-marker.md`. L1's final stays
  in `work/ch0001/L1/`. C3 is in the length band, all three pairwise judges found its rule clearer,
  it was made by the current prompts, and the C1–C3 pairwise was inside the order effect.
