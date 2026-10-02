# 02 — Session 3: the full loop and serial memory

**Goal:** run the writers' room across chapters. Chapters 2 and 3 of the slice novel go through the
complete loop, with the beta reader's memory carried forward, state written after each chapter,
and continuity checked against the bible. After this session, the loop can write a book rather than
an opening.

**Prerequisite:** plan 01 ended **GO**, or **ITERATE** with the iteration done, and plan
[01b](01b-wire-format.md) has run. Read their session logs and experiment write-ups first. Where they
changed the loop, they override this plan.

**From 01's ITERATE re-run** ([write-up](../experiments/2026-09-27-ch1-iterate.md)):
- It ended not GO. Comprehension holds, but one paragraph of rules was still skimmed by all three
  judges.
- The beat sheet had staged that paragraph *"in free indirect"*, so its fix moved to the planner:
  `kb/planner/beat-sheet.md` now asks every `learns` item to name who carries it. Chapters 2–3
  are that fix's first run.
- **Chapter 1 is C3**, L3's final, already in `chapters/0001-the-last-marker.md` (the showrunner's
  pick; see 01's session log).

## Steps

### 1. Port the mechanical core, with its tests

Port these from `skilled-writer/scripts/swlib/`, **by reading, not by copying wholesale**. Keep what
the new roles actually call.

| old module | port as | used by |
|---|---|---|
| `mdio.py` (frontmatter, tables, sections) | `tools/lib/mdio.py` | everything |
| `novelio.py` (novel paths, config, chapter list, roster) | `tools/lib/novel.py`, trimmed to the new format | clerk, continuity editor, export |
| `textstats.py` (words, sections, speech share, sentences) | `tools/lib/textstats.py` | line editor, clerk |
| `cmd_lint.py`: channels, thought-tag, house-style patterns, echo, numerals, lexicon spellings | `tools/lint.py`, **per-chapter checks only** | line editor, continuity editor |
| `cmd_state.py`: block ordering, thread ids against the plan | `tools/state_check.py` | clerk |

Rules for the port:
- **Output is a report the critic reads.** Nothing gates on it.
- Findings print as `level check: detail`, where level is `defect`, `warn` or `note`. There are no
  budgets and no ship thresholds.
- Genre-neutral strings only, because a critic reads them.
- Tests come with each module (`tests/test_<module>.py`). Adapt the old tests' fixtures instead of
  rewriting them.
- A third-party package is allowed when it earns its place (PyYAML for frontmatter, for instance). If
  one is added, record it in `requirements.txt` and in README.

### 2. The two remaining roles

- **Continuity editor** (sonnet), `.claude/agents/continuity-editor.md` + `kb/continuity-editor/`.
  - **Reads:** the draft, `bible/`, `state/`, and the last 5 continuity blocks. It runs `tools/lint.py`.
  - **Returns:** contradictions with the bible, timeline and travel errors, lexicon and numeral drift,
    and knowledge provenance (a character stating something they could not know). Each finding comes
    with a quote and the bible line.
  - **Where it runs:** in parallel with the beta reader on every round. The story editor merges both.
- **Clerk** (sonnet), `.claude/agents/clerk.md` + `kb/clerk/`.
  - **Runs** after ACCEPT and the line pass.
  - **Writes:** the continuity block (a new, smaller format; see [novel-format.md](../novel-format.md)),
    thread updates, timeline, and the reader-ledger status. It **copies** the accepted round's reader
    notes into the reader's memory, so a draft-round reader's beliefs never become memory.
  - **Lists** every new fact the chapter established under `Bible:` in its report. It never edits
    `bible/`.
- **Planner, fold mode:** takes the clerk's `Bible:` list and writes the facts into `bible/`.
- **Both new roles are born in the wire format** (`kb/shared/wire.md`, from 01b).
  - Each final message is one status line.
  - The continuity editor's findings are one line each: a quote, the bible line, the defect.
  - The clerk's `Bible:` list has one fact a line.
  - Claude Code refuses a subagent's report file, so a text report is filed verbatim with
    `tools/handback.py`.
  - The `mdio.py` port may absorb `tools/wire.py`'s parsing.

### 3. Serial memory for the beta reader

- **One reading folder per novel.** It is `reading/<id>/`, where `id = r + sha1(slug)[:6]`
  (`tools/export_prose.py --print-id novels/<slug>`). It holds the accepted chapters, prose only, as
  `ch01.md` … `chNN.md`, and the reader's `notes.md`.
- **A draft under review** is exported to `reading/<id>/pending/chNN.md`. The reader reads its notes,
  the last two accepted chapters in full, and the pending chapter.
- **Notes are capped.** `notes.md` is the reader's memory in its own words: who's who, what the world
  is, open questions, predictions, and what it is unsure of. **It stays under 800 words**, and when it
  would grow past that, the reader compresses it.
- **A fresh reader re-reads everything every 10 chapters** from `ch01.md`, and its notes replace the
  running ones. This catches drift.

### 4. The cross-chapter lens, minimal version

The biggest costs in run #6 were cross-chapter: the same aphorism in every mouth, 8 of 11 scenes as
two-person talks, one tempo, a promised scene skipped. For now:

- **The clerk logs scene shape.** It appends one row per scene to `state/scenes.md`: chapter, who,
  where, tempo, and whether it is a two-person talk.
- **The line editor reads the last two chapters** beside the new one, and reports phrases, moves and
  motifs that recur across them.
- **Promises carry forward.** The story editor reads `state/scenes.md` and the beta reader's
  predictions. A beat the previous chapter promised on the page is played, paid or deliberately
  subverted, never skipped over the break (run #6's one unowned finding).
- **Plan 06 ports the proper detectors:** signature phrases, two-hander runs, motif echo.

### 5. Write chapters 2 and 3

Through the full loop. The beat sheets come from the planner, from run #6's plan rows 2–3, and the
event is kept unless the reader ledger needs it changed: the planner says so and the showrunner
approves.

## Verification

- `python3 -m unittest discover tests` passes, including the ported modules.
- After chapter 3:
  - `state/` holds three continuity blocks in order;
  - `tools/state_check.py` is clean;
  - `reading/<id>/` holds ch01–ch03 and a `notes.md` under 800 words.
- **The notes check.** A fresh beta reader given ch01–03 cold writes its own notes. Diff them against
  the running notes; anything the running notes believe that the fresh reader does not is drift.
  Record it.
- Per chapter, the session log records the reader's click-next and reason, and the story editor's
  rounds and verdicts.
- **01b's live checks for this plan** (01b §5–8):
  - the planner's status and `gap` / `changed` lines parse (`tools/wire.py handback`);
  - a ledger written in the new form, with premise rows saying `premise`;
  - *For the planner* lines reaching the next beats task;
  - the facts files' `new` lines feeding the fold;
  - carried from L3: the line editor's final message (status and `left` lines only); the story
    editor's `owed <n>/<n>`; a stet not re-raised unless the reader's evidence answers it.

  Where one fails, fix the template or revert it, and log which.
- **01's ITERATE fix, checked:**
  - every `learns` item in the chapter 2–3 beat sheets names who carries it;
  - where a reader skims, or the story editor finds a briefing, the log says whether the beat sheet
    staged it.

## Exit criteria

- Three chapters were written by the loop without the showrunner touching a chapter.
- The state is consistent, and the reader's notes agree with a fresh read.
- The in-loop reader would keep reading, by its own report on chapters 2 and 3.
- The *Features* table in the roadmap README is updated.

**If the reader would not keep reading:** record why, in its words, and adjust plan 03 to target it
before the knowledge bases are written.

## Session log

**2026-09-27 → 10-02, session `a21d2d62`, paused twice at usage limits (five-hour, then weekly) and
resumed in the same session both times.** Working log and write-up:
[docs/experiments/2026-09-27-full-loop.md](../experiments/2026-09-27-full-loop.md).

- **Built (§1–4):**
  - `tools/lib/` (`mdio`, `novel`, `textstats`), `tools/lint.py`, `tools/state_check.py`,
    `tools/reading.py`;
  - the continuity editor and the clerk (agents + `kb/`), `kb/shared/state-format.md`, the
    planner's fold;
  - the story editor's and line editor's cross-chapter inputs, and `loop.md` rewritten.

  Tests 95 → 174, all passing. No dependency added.
- **Run (§5):**
  - ch 2 in 2 rounds (REVISE 3, ACCEPT) and ch 3 in 3 (REVISE 5, REVISE 4, ACCEPT at round 2);
  - click-next 4 on every round;
  - 12 notes, all acted on, 0 stets.
- **Verification:**
  - tests pass; `state_check` clean with 3 blocks in order;
  - the shelf holds `ch01–03.md` and `notes.md` (712 words);
  - the notes check agrees with a fresh read, with one drift (the running notes hold Voss dead;
    the page only has him missing);
  - 01b's live checks and 01's ITERATE check are all yes, except stets (untestable, 0).
- **Exit: met.** Plan 02 is done.
- **Cost:** $54.89, of which the showrunner $32.80 and the room $22.09 (ch 2 $8.68, ch 3 $10.53).

Changed during the run, each logged with its reason:
- **Where the reader reads.** Each round reads a fresh view of the shelf
  (`reading/<id>-chNN-rK/`: notes, the last two chapters, `pending/chNN.md`), not the shelf
  itself. A draft-round reader writing into the shelf would make its beliefs memory, and a report
  filed there would show the next round's fresh reader the earlier round. The reader's calibrated
  prompt was left unchanged.
- **Memory cap.** The cap only holds because the accepted round's reader is continued warm with
  its measured word count and compresses its own notes; on its own it ran to 915–976 words.
- **The continuity editor's file** gained a `checked` line, and its judgement of a finding goes on
  the finding's line: its first hand-backs carried both in prose nobody else reads.
- **The clerk marks a promise `landed` only when it is paid.** The editor grades promises *made*.
- **`trace.py` prices Sonnet 5.5 and warns on any unpriced model.** The `sonnet` alias moved to
  `claude-sonnet-5-5` across the weekly pause and was counted as $0. 8 Sonnet-role agents ran on
  the new model, which confounds the improvement in the Sonnet roles' final messages.
- **New agent files registered mid-session**, about 25 minutes after they were written
  (lessons.md #15 updated).

`.test-run` was removed after the write-up. Nothing committed.
