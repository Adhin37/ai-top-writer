---
type: protocol
title: Init — the new-novel interview
description: How the planner turns a seed into a novel the room can write from, in seven rounds of numbered questions with a recommended answer each, writing the template's files as the answers come in.
roles: [planner]
---
# Init — the new-novel interview

The showrunner has copied `novels/_template/` to `novels/<slug>/` and given you the user's seed. You
turn it into a bible, a cast, a premise, a reader ledger and an arc plan, by asking the user in
**seven rounds**. Each round you write its questions to a file and **stop**. The showrunner shows
them to the user and continues you with the answers. Then you write what the round decided into the
novel's files, and ask the next round.

Most users know little about their own story yet. Lead: every question carries the answer you
recommend for *this* seed, and the reason in one line, so "take the recommendation" is always a
good answer. Ask only what changes the book. Decide the rest, and say what you decided in the
round's file, so the user can overrule it.

Every file you fill has `{{…}}` placeholders: replace every one, and add rows as the tables need.
`python3 tools/scaffold.py check` will find any you leave.

## The round file

`work/init/round-N.md`, for the user, in plain words. It is not [wire](../shared/wire.md).

```markdown
# Round 2 — genre, tone, viewpoint, the protagonist

Decided without asking: past tense; the protagonist is the only viewpoint.

1. How warm is this story allowed to be?
   Recommended: measured. People help each other, at a price.
   Why: the seed is about a debt clock; warmth that costs nothing would let the air out of it.
   Or: warm (the crew is a family) · cold (nobody is safe and nobody is kind)

2. What does Tovi's gift cost her?
   Recommended: what she hears through the pipes, she keeps hearing for hours, so after a long
   listen she cannot tell a real alarm from an echo until she has slept.
   Why: the cost comes from how the gift works, and makes her worst at her job right after she
   was best at it.
   Or: …
```

Number the questions. At most eight a round. "Or" is optional: give up to two real alternatives,
never a straw one. When the answers come back, append them under `## Answers`, verbatim, one per
number; `rec` means the user took your recommendation.

If you start fresh mid-interview, read `work/init/round-*.md`: the first round with no `## Answers`
is where you are.

## The rounds

**1. Seed and platform.** Restate the seed as the story in one line (`opening.promise`) and ask
if that is the story. The platform: Royal Road or webnovel.com set `exposition: clear` (every
premise fact lands in chapter 1); anywhere else, recommend `clear` anyway unless the user wants the
world withheld. The audience: rating, and anything that must never be on the page
(`content.hard_limits`). Writes `novel.md`.

In fan fiction, round 1 also asks the canon (`canon:` in `novel.md`): the source work, as fans
name it; the scope (which works and adaptations count, how far into them, which wins where they
disagree); where on canon's timeline the story starts; the canon characters a reader will expect
to meet; and whether the user has sources to give (saved pages, their own notes, into
`work/canon/inbox/`). After the answers, write `novel.md` and end on `PLANNER DONE canon-scope |
novel.md | gaps 0 | changed 0`. The canon researcher writes `bible/canon.md`; you are continued
with its path and its `unsure` lines. Ask those lines in round 2, each as a question with your
recommendation where the dossier suggests one. Move each answer into its section of the dossier,
citing a `## Sources` row for `work/init/round-2.md`, and take it off `## Unsure`. From round 2
on, read `bible/canon.md` before anything you propose touches canon
([toggle-fanfic.md](toggle-fanfic.md)).

**2. Genre, tone, viewpoint, the protagonist.** Genre and subgenre; tone (register, warmth);
person, tense and how many viewpoints. The protagonist per [cast-design.md](cast-design.md): name;
how the world reads them on sight; intelligence and reading people, as two separate answers;
what they want (concrete, on the page) and what they need (usually against the want); up to three
domains and two blind spots; the gift, how it works, its **cost derived from how it works**, its
limit, and who knows of it. If they know the future, ask what, and how well (`mc.foreknowledge`).
The optional modules (`optional:` in `novel.md`), offered as features: "fights choreographed
blow by blow", "a comic beat on purpose", "work, food and money in every scene"; recommend from
the genre. Writes `novel.md`, the protagonist's profile, their `_voices.md` row.

**3. World and society.** Per [world-design.md](world-design.md): the **one central rule**, as a
mechanism a reader could predict from; who holds power because of it; the rule followed down into
labour, money, law, belief, mobility and news (propose all six lines; the user corrects); prices in
days of an ordinary wage; who lost out when the rule arrived; the places of the first arc, with
distances in days. Writes `bible/world.md`, `bible/society.md`, and the names and terms so far in
`bible/lexicon.md`.

**4. Cast.** The antagonist is **a person**, with their own case for what they do, put as they
would put it. Ask **when their face reaches the page**: by `opening.contract_by_ch` at the latest
(3 by default; recommend earlier when the seed allows it). An opposition that only acts through
documents reads as weather. Two to four others who carry scenes: their relation to the protagonist,
their power, one concrete stroke. Show the voice matrix as a table and ask if anyone is wrong.
Romance (`content.romance`; "decide later" is a good answer) and its modules if on. Writes the
profiles, `_voices.md`, `_extras.md`, `plan/timeline.md` (the actors, per
[world-clock.md](world-clock.md)), and `novel.md`.

Then, before round 5, write `work/init/style-beat.md`: one moment from the first chapter's world,
five lines of story language (who, where, what happens, what the reader should feel), with the
central rule in it. End on `PLANNER DONE style-beat | <its path> | gaps 0 | changed 0`. The writer
drafts it three ways.

**5. Style.** You are continued with the writer's samples file. Copy the three samples into the
round file verbatim, labelled as the writer labelled them, and ask which is the book's voice, or
what to mix. Recommend the one that a reader of this platform would follow most easily at the
moment the rule bites; a clear, plain register is right for Royal Road far more often than a
literary one. The chosen sample goes under `# Style anchor` in `novel.md`, **verbatim**. A user who
asks for a mix gets it from the writer first, so the answer you receive names a sample in the file.

**6. Premise and ledger.** Write `bible/premise.md` per [premise.md](premise.md) and
`plan/reader-ledger.md` per [reader-ledger.md](reader-ledger.md), from the answers so far and
nothing else. The round file holds the premise's *In one breath*, as written, and one question:
"Say this back in your own words, as you would tell a friend." It has no recommendation: the point
is the user's words. When the say-back comes, check every load-bearing fact against it. If one is
missing or wrong, the premise did not land: rewrite *In one breath* (plainer, the missing fact
earlier) and ask again as `round-6b.md`. A say-back that adds something the premise lacks is the
user telling you the story; put it in the bible and say so in a `changed` line.

**7. Title, blurb, the arc plan.** Before asking, write:
- `plan/arcs.md`: the ending (from the seed and the answers), arc 1 in full per
  [stakes.md](stakes.md), two later arcs sketched in one row each;
- `plan/chapters.md`: the first ten to fifteen rows per [arcs-and-chapters.md](arcs-and-chapters.md),
  each with its temperature and its hook, the antagonist's face in the row the ledger says;
- the ledger's later rows, scheduled against those rows; the thread board, `state/threads.md`;
  the clocks in `plan/timeline.md`.

Then ask: the title, three candidates per [title-and-blurb.md](title-and-blurb.md); the blurb,
written against your recommended title; the ending, in a sentence; arc 1's question and the rows'
titles and events, as a list. After the answers, write the title and the blurb into `novel.md`
(rewrite the blurb if another title was chosen) and fold the corrections into the plan.

## Before you finish

- Every `{{…}}` replaced, in every file the template has.
- Each premise fact has a ledger row due by chapter 1 (with `exposition: clear`), and a row that
  carries it: the row's event can land it.
- The antagonist has a face row due by `opening.contract_by_ch`, and a chapter row whose event
  puts them on the page.
- Every thread id the rows name has a row on `state/threads.md`, `planned`.
- The premise restates the bible and the answers. A fact you added that nobody answered is
  invented: take it out, or ask.
- In fan fiction: the dossier's `divergence` line is written, and every canon character in the
  cast files, the plan and the ledger has a row in `bible/canon.md`'s cast.

Then end on `PLANNER DONE init`. The showrunner runs the check and sends you any defect it finds.
