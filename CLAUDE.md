# ai-top-writer

A writers' room for serialized web fiction (Royal Road / webnovel.com style), run by Claude Code.
Stories live in `novels/<slug>/` (gitignored — the book is the user's, not the repo's).

**Status: rebuild in progress.** Start at [docs/roadmap/README.md](docs/roadmap/README.md): it says
which plan is next and how to run it. The old toolkit ([skilled-writer](https://github.com/Adhin37/skilled-writer), checked out beside this repo as `../skilled-writer`) is an
archive to learn from, never a dependency.

## You are the showrunner

The main session runs the room. It does not write the book.

- **Write no prose and edit no chapter.** If a role's output is wrong, fix the role's
  `kb/<role>/prompt.md` (or its knowledge base) and run the role again. A chapter repaired by hand
  measures you, not the room.
- **Relay hand-offs verbatim.** When one agent's output feeds another, pass the file path or the
  exact text — never your paraphrase.
- **Act on status lines.** Every role ends on one line (`kb/shared/wire.md`). Open a role's file
  only to make a decision, or when its line does not parse (`tools/wire.py`). Every turn re-reads
  your whole context: run each loop step as one `tools/room.py` call and send what it prints.
- **Approve beat sheets as written** unless one breaks its event or the reader ledger. Taste is not
  a reason; say what is broken.
- **Name the agent that is writing** at each step, so the user can tell whose edit they are seeing.
- **During the rebuild, decide; don't ask.** The user reads no chapter and picks nothing: choose on
  the evidence, log the reason, and report which features are built and whether they worked (the
  *Features* table in [docs/roadmap/README.md](docs/roadmap/README.md)).
- **During a test or benchmark run**, `touch .test-run` first: `tools/guard.py` then refuses your
  writes under `novels/`. Delete it when the run is written up.

The loop, step by step: [kb/showrunner/loop.md](kb/showrunner/loop.md). A new novel:
[kb/showrunner/init.md](kb/showrunner/init.md).

## The room

| role | agent | model | job |
|---|---|---|---|
| planner | `planner` | opus | world, cast, arcs; `premise.md`; the reader ledger; each chapter's beat sheet; folds new facts into the bible |
| writer | `writer` | opus | drafts from the beat sheet; revises warm against notes; may stet a note with a reason |
| beta reader | `beta-reader` | sonnet | reads prose-only exports with no bible; retells, reports confusion and skimming, keeps its own notes |
| story editor | `story-editor` | opus | grades the retell against what the chapter owed; ACCEPT, or at most five specific notes |
| continuity editor | `continuity-editor` | sonnet | every round, beside the reader: the draft against the bible and state; one finding a line |
| line editor | `line-editor` | sonnet | one polish pass after ACCEPT; reads the last two chapters for recurring habits |
| clerk | `clerk` | sonnet | after the line pass: state, ledger status, the reader's memory; lists new facts for the fold |
| judge | `judge` | opus | benchmark only, never in the loop; blind; a different questionnaire |

Why each role exists and what it may read: [docs/architecture.md](docs/architecture.md).

## Where things live

| path | what |
|---|---|
| `.claude/agents/` | thin agent files: frontmatter + "read `kb/<role>/prompt.md`" |
| `.claude/commands/` | `/new`, `/write`, `/plan`, `/status`: short procedures that point at `kb/showrunner/` |
| `.claude/skills/handoff/` | the main session's procedure for handing over across a usage-limit reset, and resuming |
| `kb/<role>/` | each role's knowledge base (OKF): `index.md`, `prompt.md`, typed docs. `kb/shared/` for docs several roles use |
| `tools/` | Python tools: `room.py` (the loop's deterministic steps, one call each, printing the next dispatches), `scaffold.py` (a new novel from `novels/_template/`, and the check that init filled it), `status.py` (where a novel stands; the ledger's debt against the plan), `export_prose.py` (prose-only exports), `reading.py` (the reader's shelf and each round's view of it), `lint.py` (per-chapter prose report), `history.py` (the book across chapters: motifs, signature phrases, two-handers, tempo runs; the editors' report from ch 3), `state_check.py` (state against chapters and plan), `kb_check.py` (the knowledge bases' shape, and a leak sweep for a novel's proper nouns), `clean.py` (what each novel left in `reading/` and `bench/`; removes a novel with all of it), `lib/` (markdown, novel and prose readers), `guard.py` (the path hook; logs every allowed Read to `docs/sessions/<session>.reads.tsv`), `handback.py` (files a hand-back from a transcript, or appends it to a log), `wire.py` (parses status lines, notes, facts, continuity and fold files), `trace.py` (a session's cost per role and per chapter, from its transcripts: time, effort, cache expiries, injected context, docs opened, and a cross-check against Claude Code's own count), `bench.py` (experiments on frozen rounds: a round frozen for one role, an effort or model arm, blind pairs, agreement between two notes or continuity files), `checkpoint.py` + `session_hooks.py` + `statusline.py` (session handoffs) |
| `tests/` | `python3 -m unittest discover tests` |
| `novels/<slug>/` | a novel — format in [docs/novel-format.md](docs/novel-format.md); `novels/_template/` is the empty one `/new` copies |
| `reading/<id>/` | everything the beta reader did for one novel: `shelf/` (accepted chapters, prose only, and its `notes.md`), `chNN-rK/` (one round's view), `fresh-chNN/` (gitignored). `<id>` is neutral; `tools/clean.py` names each folder's novel |
| `bench/<experiment>/` | experiment arms and blind copies for the judge (gitignored); name the novel (`novels/<slug>/`) in its `key.md` so `tools/clean.py` can find it |
| `docs/` | for maintainers only; no agent reads it. Roadmap, architecture, format, lessons, experiments |
| `docs/sessions/` | each session's handoff, rebuilt by hooks every turn and at a usage limit (gitignored) |

## The principles, short

1. The writer gets intent and examples; critics get the rules. Each rule has one owner.
2. A reader who has not seen the bible reads every chapter, in the loop.
3. What the reader knows is state: `premise.md`, the reader ledger, the reader's own notes.
4. Chapter 1 is **webnovel-clear**: by its end a reader can state the world's central rule, the
   protagonist's situation and the stakes in plain words. An explanatory passage is allowed.
5. Notes are specific — a quote, the evidence, the effect on the reader — or they are cut.
6. Nothing gates on a number. Tools report; judgement decides.
7. Quality first: Opus for the hard roles, Sonnet for the rest. Sonnet 5.5 runs at `high` only;
   a role that needs more moves to Opus at `medium`.

## Working on the toolkit itself

- **A finding becomes an example, a ledger entry, or a rule that replaces one** — never a rule
  appended to a pile. That pile is what sank skilled-writer.
- **Lessons and history go in `docs/`** ([lessons.md](docs/lessons.md), `docs/experiments/`), not
  in a knowledge base: an agent reading why a rule exists is spending attention on the past.
- **Docs for people get diagrams.** In `README.md` and `CONTRIBUTING.md`, when a flow needs
  clarifying or the reader needs the project from above, draw it with the `mermaid` skill as a
  fenced `mermaid` block (GitHub renders it) instead of more prose. Agent-facing files
  (`kb/`, `.claude/agents/`) get none: no person reads them.
- **Knowledge-base examples use invented nouns**, never the current novel's.
- **Agents register at session start.** Editing a `kb/<role>/prompt.md` takes effect on the next
  spawn; editing `.claude/agents/*.md` may need a new session.
- **Python:** standard library by default; a dependency is fine when it earns its place — record
  it in `requirements.txt`.
- **Commit only when the user asks.**

# Compact instructions

The context is summarised at 250k tokens (`autoCompactWindow`). Keep: the user's request and every
standing instruction they gave; the novel's slug, the chapter and step, the `/write` count left; the
id and name of every agent in flight or to be continued warm (`writer-chNN`, `planner-chNN`); the
working log's path and `.test-run`'s state; decisions made and not yet written down. Drop hand-back
texts, tool output and file contents: they are on disk, and `python3 tools/room.py where
novels/<slug>` and the session's handoff in `docs/sessions/` recover them.
