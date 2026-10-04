---
type: protocol
title: New novel — showrunner procedure
description: The main session's procedure for /new — scaffold a novel from the template, relay the planner's seven interview rounds, the canon researcher's dossier in fan fiction and the writer's style samples, and check the result.
roles: [showrunner]
---
# New novel

The planner runs the interview ([its procedure](../planner/init.md)); you carry it. Each round it
writes its questions to a file and stops on `PLANNER ASKS`. You show the user the questions, and
continue the planner with the answers, **verbatim**. You never answer for the user, and you never
fill a file yourself.

## In a test run: the answer sheet first

The user answers nothing during the rebuild. Before step 1, write the answer sheet into the run's
log in `docs/experiments/`: the seed, the platform, and what the author wants on each round's
topics (the protagonist, the world's rule, the antagonist, the voice, the ending), as an author
would say it. In fan fiction, add the source work, the scope, where the story starts, and who
must appear; the sheet gives no sources, so `blocked` lines are logged and not waited on. Then `touch .test-run`.

Answer every question from the sheet, and log each answer with its source: `sheet`, or `rec —
sheet silent` when you took the recommendation because the sheet says nothing. Never change the
sheet once init has started. In round 6, read the premise's paragraph once, then write the
say-back from memory in your own words.

## 1. Scaffold

Choose a slug from the seed: two or three words, permanent (the title can change; the slug
cannot).

```
python3 tools/scaffold.py new <slug>        # -> novels/<slug>/, from novels/_template/
```

## 2. The rounds — planner

Spawn **planner**, described `planner-init`: *"Novel: novels/{slug}. Task: init. Seed: <the user's
seed, verbatim>."*

Each round ends on `PLANNER ASKS novels/{slug}/work/init/round-N.md | round N | questions n`.
Show the user the round file's questions as written. Use `AskUserQuestion` when they fit (at most
four a call, the recommendation first, labelled as recommended); otherwise show the file and take
the answers in chat. Then continue `planner-init`:

*"Answers to round N:
1. rec
2. <the user's words>"*

`rec` means the user took the recommendation.

## 2b. The canon — canon researcher (fan fiction only)

In fan fiction, after round 1's answers the planner ends on `PLANNER DONE canon-scope | …`. Spawn
**canon-researcher**, described `canon-init`: *"Novel: novels/{slug}. Task: init."* It ends on
`CANON DONE novels/{slug}/bible/canon.md | …`, then its `unsure` and `blocked` lines. Continue
`planner-init` with the lines, verbatim: *"Canon: novels/{slug}/bible/canon.md. Ask round 2.
<the unsure lines>"*. The `blocked` lines go to the user with round 2's questions, as an offer, not
a wait: a page they save into `novels/{slug}/work/canon/inbox/` is read by the next lookup.

Later, when any planner's hand-back carries `gap canon` lines, run
`python3 tools/room.py canon novels/{slug} <planner agent id>` and send what it prints: the
researcher's lookup, then the planner continued.

## 3. The style — writer

After round 4's answers the planner ends on `PLANNER DONE style-beat | <beat path> | …`. Spawn
**writer**, described `writer-style`: *"Novel: novels/{slug}. Style samples. Beat:
novels/{slug}/work/init/style-beat.md. Write novels/{slug}/work/init/style-samples.md."* It ends on
`SAMPLES READY`. Continue `planner-init`: *"Samples: novels/{slug}/work/init/style-samples.md. Ask
round 5."*

If the user's round-5 answer is a mix, continue `writer-style` first: *"Mix: <the user's words>.
Add it as sample D."* Then answer the planner: *"Answers to round 5: 1. D"*.

## 4. Finish and check

After round 7's answers the planner ends on `PLANNER DONE init | …`. Run:

```
python3 tools/scaffold.py check novels/{slug}
python3 tools/state_check.py novels/{slug}
python3 tools/kb_check.py --novel novels/{slug}
```

A defect from the first two goes back to `planner-init` with the check's lines, verbatim:
*"Check: <lines>. Fix them."* Run the check again after. A warn is yours to decide: send it back or
log why it stands.

A `names` warn from `scaffold.py check` is a name word another novel beside this one already
uses. Every planner is a fresh spawn of one model, and its first draw is the same each time. Send
it back to `planner-init` unless the user chose the name.

A `leak` from `kb_check` is a name this novel shares with a knowledge-base example, and a role can
blend the two. Before chapter 1, rename the example: invented nouns are cheap, and a name in the
novel may be one the user chose.

## 5. Report to the user

The title and the two titles not chosen; the blurb; the premise's *In one breath*; the
protagonist and the antagonist in a line each, and the chapter where the antagonist's face reaches
the page; the first rows' titles; the modules switched on; then: *"`/write` starts chapter 1."*
