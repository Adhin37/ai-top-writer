# Lessons carried forward

What six benchmark runs of [skilled-writer](../../skilled-writer) (2026-09-06 → 09-26) taught, kept
because the evidence still applies to this design. Everything else from the old repo was left
behind on purpose — the user's standing instruction is to carry a rule over only when its evidence
still holds. This file is for maintainers; no agent reads `docs/`.

When a run teaches something new, it goes here with its evidence — not into a role's knowledge base
as a rule.

## About the story

1. **"Something happens" must be stated as an event, not a difference.** Asked only what a chapter
   *delivers*, a model writes "proximity that isn't refused" and ships eleven hundred words in which
   nothing occurs (run #2, five chapters). The beat sheet's `event` line is one clause a reader
   could retell, with a concrete verb and a target.
2. **Models summarise the turns that matter.** Machine fiction glosses over important events rather
   than padding trivia (CONCOCT, arXiv 2311.04459). A turn reported in a past-perfect clause is a
   skipped scene. The event gets the longest scene.
3. **One register for a whole book reads as machine-made**, and no phrase list catches it. Run #2
   had zero cliché hits and a reader flagged it as AI on page one: every sentence loaded, every scene
   closed on a small ironic withholding. Plain sentences, on purpose, and a change of temperature
   between chapters.
4. **Banning a thing leaves a vacuum the model fills with its own default.** Thirty bans produced a
   narrower fingerprint than the clichés they removed (run #2). Examples of what to do beat lists of
   what not to.
5. **The opposition needs a face early.** Runs #5 and #6 both built a hostile institution that
   acted only through documents; both readers named it the biggest cost. Schedule the antagonist's
   first appearance in the plan.
6. **A book that only takes is not tense.** Every chapter should name one thing worth the price,
   or the reader is paying instalments on something never shown (run #5, zero defects, 3 / 5).
7. **Cross-chapter habits are invisible to a per-chapter check.** Run #6's top reader costs — the
   same aphorism in three mouths, eight of eleven scenes as two-person talks, one tempo, a promised
   scene skipped — were all across chapters. Something must read more than one chapter.

## About the machinery

8. **Never gate on a number.** Word count (run #1: chapter 5 landed on the minimum to the word),
   dialogue share (run #2) and a speech target (run #5) were each gamed within a few chapters.
   Tools report; judgement decides.
9. **Whoever knows the world cannot see what the page leaves out.** Run #6: every loop agent held
   the bible, the only cold reader ran after five chapters, and the premise never reached the page.
   The fix is structural — a reader without the bible, in the loop — not another rule.
10. **Anything in a chapter file can reach a reader.** Run #6's chapter frontmatter said what the
    reader was supposed to understand; the "blind" reader read it, and the directory slug too.
    Readers get prose-only exports in neutral folders.
11. **A finding turned into a rule makes the next run worse.** Each run's findings were appended to
    cards until the drafter held ~30 constraints (13 cards, 7,650 words and 208 negations in one
    phase) and wrote defensively. A finding becomes an example, a ledger entry, or a rule that
    replaces one.
12. **LLM judges agree with human preference on creative writing only ~73% of the time** and are
    biased by position, length and formatting. A judge may locate and describe; it may not gate.
    The judge that benchmarks the loop must not be the loop's own critic, or the loop learns its
    judge.
13. **Warm continuation is the biggest time lever measured.** Run #6: a writer continued with
    `SendMessage` took 755 model-seconds against 1,531 cold, with no visible quality cost (n = 1).
    Wall time was extended thinking, not tools (~4% of drafter time was tools).
14. **A killed agent's partial edit is invisible to its successor.** Run #6 shipped a tic a killed
    gate introduced. Every hand-off leaves a file; every phase marks the chapter's status first.

## About Claude Code

15. **Agents register at session start — and new ones can register later.** An agent file edited
    mid-session may not take effect, and the two cases look identical. Thin agent files that read
    their prompt at runtime avoid the problem; a new repo's agents need a session opened in that
    repo. Plan 02: two agent files *created* mid-session were listed as spawnable about 25 minutes
    later, by a system notice. Wait for the notice; do not assume either way.
16. **`omitClaudeMd: true` also drops the auto-memory index** — measured both ways. Use it on the
    beta reader and the judge; it is part of what keeps them cold.
17. **Hooks see `agent_id` and `agent_type`.** No `agent_id` means the main session. Project hooks
    need the folder to be trusted. Permissions are inherited: a subagent cannot be granted what the
    parent lacks, and deny rules are global.
18. **Path guards do not cover `Bash`.** A `cat` is not judged by a `Read` hook. The only real wall
    is not giving the tool.
19. **The scratchpad is turn-scoped.** It was emptied mid-session once, taking measurement files
    with it. Anything a run needs goes in `docs/experiments/` or `bench/`.
20. **`novels/` has no undo.** It is gitignored by design and the user does not want snapshot
    features. Before overwriting a novel file in a session, copy it somewhere durable and read it
    back.

## About examples

21. **The last run's novel leaks into the examples written right after it.** Runs #1–#4's fanfic
    vocabulary and run #5's names both settled into the corpus via fixes written while that novel was
    nearest to hand. Knowledge-base examples use invented nouns and portable officialdom, and every
    run ends with a sweep.
22. **Two original-fantasy runs gave the golden finger the same cost** (nosebleed and
    disorientation) with no source in the corpus: a model default. Derive costs from how the gift
    works, and test whether the same cost would fit any other gift.

## About running the room

23. **A model alias can move under a running experiment.** Plan 02 paused for four days at a usage
    limit; after it, `sonnet` meant `claude-sonnet-5-5`, not `claude-sonnet-5`. Eight agents ran
    on the new model, which confounds what changed in the Sonnet roles, and the cost trace counted
    them as $0 until it was made to warn. Pin full model ids for a benchmark; a tool that prices
    by model must say when it meets one it does not know. Plan 06 found the model was the cause:
    the continuity editor recapped on Sonnet 5 and was one clean line on Sonnet 5.5, reading a
    byte-identical template. Two template fixes had only shrunk the recap. Before tuning a prompt
    for a behaviour, check whether the model changed under it.
24. **A model cannot count its own words.** Two beta readers told to keep their notes under 800
    words wrote 915 and 976. One asked to compress reported success at 868. Given the measured
    count and a target, it reached 749 (plan 02). Give a cap's number from a tool, every time.
25. **What only a reader with memory sees.** A reader carrying notes across chapters caught a
    contradiction between chapters 2 and 3 that a fresh reader of both missed, and it also kept a
    wrong belief (a man missing, held as dead) that the page never corrected. Memory is both the
    instrument and the drift; the every-10 fresh re-read is the check (plan 02).
26. **Model-default names turn up on both sides.** In plan 04's init run, the new novel's names
    collided with the knowledge bases' invented ones. The showrunner's seed named the protagonist
    "Ness" (the examples have "Nessa"). The planner chose "Pell" (a writer example) and "Vane
    House" (the test fixture's "Nessa Vane"). Neither side copied the other: these are names a model
    reaches for. So the leak sweep (`kb_check --novel`) runs after init too, not only after a run,
    and a hit renames the example. Run #7, a third init from a seed that named nobody, gave Pell,
    Aurel, Vane, Wren, Bram and Orrin: every one a name from an earlier novel or fixture. The sweep
    catches the knowledge bases' side; a name shared only with another novel is invisible to it,
    and no reader of a single novel can see it.
27. **Every agent sees the working tree's git status, judges included.** `omitClaudeMd` keeps out
    `CLAUDE.md` and the memory index, not the harness's git-status block. In run #7 it showed the
    leak sweep's two renamed `kb/writer/` docs as modified, and all three blind judges inferred "an
    AI writing system… against craft guidance in `kb/writer/`" before reading a word. Untracked
    files can be hidden with `.git/info/exclude`; modified tracked files cannot. Judge from a
    committed tree.
28. **A per-chapter window cannot see a refrain's fourth use.** The line editor reads two chapters
    back and was right each time it kept "Old ones hold their shape" as a callback (ch 3, ch 5);
    the judges counted four uses across five chapters and all three named it. A habit check has to
    search every earlier chapter before it keeps a line, not only the two beside it (run #7).
    `tools/history.py` now counts every use across the book for it (plan 06).
29. **The in-loop reader tracked the blind judges.** Fourteen beta-reader rounds gave click-next 4–5;
    three blind judges gave 4.5. The showrunner's own impression, written first, guessed 3.5–4 and
    over-weighted length, which no judge named. On a verdict, trust the cold reader over the
    showrunner who has read every report (run #7).
30. **A transcript under-counts output, and Sonnet's most.** Claude Code writes a response's usage
    as its rows stream, and some rows land before the last tokens do. On Opus 5.5 only an agent's
    final response lost its count. On Sonnet 5.5, 147 ordinary tool-call responses recorded 2–3
    output tokens and no thinking. Run #7's trace was $4.88 (5.9%) under Claude Code's own count:
    a third short for the Sonnet roles, nearly half for the judges. The input side matched to the
    token. The session's `cost-state` row holds the true per-model count; check any per-role cost
    against it before using it to choose a lever (plan 06).
31. **Settings have traps a cost lever falls into.** A per-model `effortLevel` in user settings
    (`modelSettings`) outranks a top-level one in the project's, so the project sets both.
    `ultrathink` is a keyword in a prompt the user types: the main session cannot raise its own
    effort for one decision mid-run. Dynamic workflows are off on Pro until the user turns them on
    in `/config`, so a session cannot build and probe one alone. The docs do not say whether
    `autoCompactWindow` also reaches subagents, so the window stays above every role's peak context
    (run #7: planner 194k, writer 141k) until a trace shows it does not (plan 06b).
32. **Pick the instrument that can see the effect.** A blind judge reading one chapter alone
    cannot see a revision that fixes what the reader carries from earlier chapters, and run #7's
    round-2 notes were nearly all of that kind. The in-loop reader's reports before and after could
    see it (plan 06c, lever 1). Likewise, `state_check` passes a clerk block that is well formed but
    wrong or thin: a cheaper clerk is checked by reading its block against the baseline's.
33. **A critic's A/A is loose; read what the arm missed.** Two `high` continuity replays of one
    draft shared under half their findings, so a count of matches cannot separate an arm from noise.
    What decided it was the kind of finding lost: at `medium` the continuity editor did no thinking
    and dropped the "who could know it" checks, while the story editor at `medium` stayed within its
    A/A (plan 06c, lever 2).
