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

15. **Agents register at session start.** An agent file created or edited mid-session may not take
    effect, and the two cases look identical. Thin agent files that read their prompt at runtime
    avoid the problem; a new repo's agents need a session opened in that repo.
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
