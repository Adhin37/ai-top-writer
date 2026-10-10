# 2026-10-10 — plan 08, step 3: the agency bench and the planner at `medium`

Working log first, write-up at the end. Plan: [08](../roadmap/08-pressure-and-run-9.md).
The user's request (2026-10-10, verbatim): *"continue"* (after step 1–2 were reported).

## Configuration

| parameter | value | why |
|---|---|---|
| frozen point | `novels/ember-terraces`, before chapter 5's beats (`bench.py freeze … 5 0 agency <arm> --role planner`) | ch 5 is run #8's clearest no-lever chapter: the lead plans a rescue and declines it, and all three judges named it |
| arm A | `planner` (Opus 5.5, high), ledger as run #8 left it | the current room on a novel without Pressure rows |
| arm B | `planner`, after a `planner` ledger task backfilled `L1`/`C1` for ch 1–4 (the debt line verbatim); its beats dispatch carries `room.pressure_note` | the change under test |
| arm C | `planner--medium` (Opus 5.5, medium), as A | the effort lever pending since 06c |
| drafts | one `writer` round 0 per arm A and B, from that arm's beat sheet | the judge compares prose, not plans |
| judging | `bench.py pair agency a-vs-b`: two blind folders, X/Y swapped, one `judge` each (mode 2) | position bias cancels across the pair |
| C's verdict | the beat sheet against A's, on `kb/planner/beat-sheet.md`'s checks, its trail step, and cost and time from `trace.py` | a cheap first look; no prose |
| `.test-run` | on from the freeze | the showrunner writes nothing under `novels/` |

One sample per arm: a direction, not a measurement.

## Log

- **Freeze** (bench.py): three copies, no defect. `--agent` parses only before the positionals
  (`freeze --role planner --agent planner--medium NOVEL 5 0 agency c`).
- **Arm B backfill** (planner, ledger task, 70k tokens, 2.0 min): `PLANNER DONE ledger | … | gaps 0 |
  changed 2`. L1 `set · grew · shrank · grew`, C1 `set · nearer · nearer · nearer`; `state_check`
  clean. It also moved P4 (Kesa's want) from `landed ch1` to `moved to ch5`: the reader's notes hold
  no line of it, which matches run #8's graders (P4 `partly` in all three retells).
  - **The flag did not fire for ch 5**: the trail ends on `grew`, so `room.pressure_note` is empty
    and arm B differs from A by the trail in the ledger only (plus P4 moved).
  - **The room grades its own trail leniently.** It marks ch 3's clock `nearer` (the fort's three
    days put to Ishen), where two judges ranked ch 3's "Three months off" the second cost: the
    clock unwound. And ch 4 `grew` for a message carried through Yan that Gao refuses. A reader
    outside the room would likely have written `later` and `held`.
- Arm B beats: spawned fresh, the dispatch as A's (no `Pressure:` clause).
- **Arm A beats** (planner): `PLANNER DONE beats | … | gaps 1 | changed 3`. **It backfilled the
  Pressure rows itself** (L1 ends `grew`, C1 `nearer`), because `beat-sheet.md` now asks for a
  `pressure` line. So the new knowledge base alone brings the rows in, and A is not a "without"
  arm. Its gap is the freeze's known limit: the bible and `threads.md` keep chapter 5's fold.
  - **Design changed:** the baseline is what the old room wrote, run #8's own ch 5 (`beats.md`,
    `draft-r0.md` in `novels/ember-terraces/work/ch0005/`), from the same point. The blind pair is
    run #8's r0 against arm B's r0; A's beat sheet is a second sample of the new room's plan.
- **Arm C beats** (planner--medium): `PLANNER DONE beats | … | gaps 2 | changed 2`. It also
  backfilled L1/C1 unasked, and used them: "L1 needed a deed bigger than ch 4's, so at dusk she
  lights all forty on the breath to cut the boy's time in irons, and the town reads it as
  eagerness". The plan row's cost ("she could do nothing") is kept at noon only. Same freeze gap
  as A.
- **Arm B beats** (planner): `PLANNER DONE beats | … | gaps 1 | changed 2`. `pressure L1 shrank`:
  the noon route to free the boy is laid and declined ("the noon sun would take three roofs"), the
  dusk lighting is done "to keep her mother's stall out of it". The step is honest, and the chapter
  is still the one the judges faulted: the plan row's event leaves her no move.
- **Arm A's step is lenient:** the same declined route and the same lighting, written `L1 grew`.
  Two planners, one event, opposite words: the trail is only as honest as whoever grades it.
- **Drafts and judges skipped.** All three beat sheets keep the row's event (the garrison sends
  the boy downriver while Kesa lights the lamps above him); A and B differ in wording, not in
  structure, so a blind pair would measure the writer's variance. The fix has to reach the row.

## Costs (`trace.py --agents`)

| spawn | arm | responses | wall | output | cost |
|---|---|---|---|---|---|
| ledger backfill | B, planner high | 16 | 2.0 min | 9.1k | $0.62 |
| ch 5 beats | A, planner high | 14 | 5.3 min | 29.4k | $1.34 |
| ch 5 beats | B, planner high | 15 | 4.9 min | 27.0k | $1.26 |
| ch 5 beats | C, planner medium | 18 | 5.7 min | 31.4k | $1.42 |

Agents $4.64; the showrunner $5.50 (it also built step 1's tail and the write-up); total $10.13.

## Write-up

**Question 1: do Pressure rows make the lead act?** Not on their own, at the beat sheet. Every arm
wrote the rows (the new beat-sheet doc brings them in unasked), and the one arm that graded itself
honestly (B, `shrank`) still planned the declined rescue, because the plan row's event is the
garrison's act and Kesa is its witness. Only C's planner reached past the row and gave her a deed
(lighting all forty faster to cut the boy's hour in irons), and that is one sample.

**Decision:** the lever is checked where the event is chosen, not after. The planner's plan task
now walks the rows ahead against the `L1` and `C1` trails and rewrites a row that would hold or
shrink the lever beyond the arc's one cool chapter (a want she acts on, an event of which she is
the subject) or move the clock later without a reason the reader is given; init's last check asks
the same of every later row. `kb_check` clean. Live test: run #9's first `/plan`, which must
rewrite `ember-terraces`' passive rows ahead (row 8 "get away from Dao", row 11 "let her father
speak for her" read as holds).

**Side finding:** the room grades its own trail leniently (B's backfill wrote ch 3's clock `nearer`
where two judges called it unwound; A wrote `grew` for a declined move). The status flags can only
fire on what the grader writes. No rule added: the story editor already grades the `pressure` line
as an owed row against the retell, and run #9 will show whether its grade is stricter than the
planner's own; if not, that is the next lever.

**Question 2: the planner at `medium`?** No. Arm C cost 6% more than A ($1.42 against $1.34), took
longer and wrote more, at no visible loss or gain in the sheet. The planner stays at `high`; 06c
lever 6 is closed. `planner--medium` stays as a bench arm.

**Clean-up:** the three beat sheets and ledgers kept in `bench/agency/`; the frozen copies and their reading folders removed with `tools/clean.py`;
`.test-run` removed.
