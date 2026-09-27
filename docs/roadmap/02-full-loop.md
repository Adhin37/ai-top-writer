# 02 — Session 3: the full loop and serial memory

**Goal:** run the writers' room across chapters. Chapters 2 and 3 of the slice novel go through the
complete loop, with the beta reader's memory carried forward, state written after each chapter,
and continuity checked against the bible. After this session, the loop can write a book rather than
an opening.

**Prerequisite:** plan 01 ended **GO**, or **ITERATE** with the iteration done, and plan
[01b](01b-wire-format.md) has run. Read their session logs and experiment write-ups first. Where they
changed the loop, they override this plan.

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
approves. The user reads both chapters.

## Verification

- `python3 -m unittest discover tests` passes, including the ported modules.
- After chapter 3:
  - `state/` holds three continuity blocks in order;
  - `tools/state_check.py` is clean;
  - `reading/<id>/` holds ch01–ch03 and a `notes.md` under 800 words.
- **The notes check.** A fresh beta reader given ch01–03 cold writes its own notes. Diff them against
  the running notes; anything the running notes believe that the fresh reader does not is drift.
  Record it.
- The user's verdict on chapters 2–3 is recorded in the session log.

## Exit criteria

- Three chapters were written by the loop without the showrunner touching a chapter.
- The state is consistent, and the reader's notes agree with a fresh read.
- The user would keep reading.

**If the user would not keep reading:** record why, in their words, and adjust plan 03 to target it
before the knowledge bases are written.

## Session log

*(filled in when this plan runs)*
