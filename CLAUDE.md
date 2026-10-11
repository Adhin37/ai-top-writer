# ai-top-writer

A writers' room for serialized web fiction (Royal Road / webnovel.com style), run by Claude Code.
Stories live in `novels/<slug>/` (gitignored — the book is the user's, not the repo's).

**Status: rebuild in progress.** Before choosing what to work on, read
[docs/roadmap/README.md](docs/roadmap/README.md): it says which plan is next and how to run it. The
old toolkit ([skilled-writer](https://github.com/Adhin37/skilled-writer), checked out as
`../skilled-writer`) is an archive to learn from, never a dependency.

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
  *Features* table in the roadmap).
- **During a test or benchmark run**, `touch .test-run` first: `tools/guard.py` then refuses your
  writes under `novels/`. Delete it when the run is written up.

Before writing a chapter (`/write`), read [kb/showrunner/loop.md](kb/showrunner/loop.md). Before
starting a novel (`/new`), read [kb/showrunner/init.md](kb/showrunner/init.md).

## The room

| role | agent | model, effort | in short |
|---|---|---|---|
| planner | `planner` | opus, high | world, cast, arcs, premise, reader ledger, beat sheets, the fold |
| writer | `writer` | opus, high | drafts from the beat sheet; revises warm against notes |
| beta reader | `beta-reader` | sonnet, high | reads prose only, no bible; retells, reports confusion and skimming |
| story editor | `story-editor` | opus, medium | grades the retell against what was owed; ACCEPT or ≤5 notes |
| continuity editor | `continuity-editor` | sonnet, high | every round: the draft against the bible and state |
| line editor | `line-editor` | sonnet, high | one polish pass after ACCEPT |
| clerk | `clerk` | sonnet, high | state, ledger status, the reader's memory; facts for the fold |
| canon researcher | `canon-researcher` | sonnet, high | fan fiction: the sourced canon dossier; `gap canon` lookups |
| judge | `judge`, `judge--fable` | opus 5, fable; high | benchmark only, never in the loop; blind |

Before changing what a role reads or writes, read [docs/architecture.md](docs/architecture.md)
(roles, isolation, and every tool in `tools/`).

## Where things live

| path | what |
|---|---|
| `.claude/agents/` | thin agent files: frontmatter + "read `kb/<role>/prompt.md`" |
| `.claude/commands/` | `/new`, `/write`, `/plan`, `/status`, pointing at `kb/showrunner/` |
| `kb/<role>/` | each role's knowledge base: `index.md`, `prompt.md`, typed docs; `kb/shared/` for several roles |
| `tools/` | Python, one tool a job; `tools/room.py` runs the loop's steps |
| `tests/` | `python3 -m unittest discover tests` |
| `novels/<slug>/` | a novel; `novels/_template/` is the empty one `/new` copies. Before changing a novel's files, read [docs/novel-format.md](docs/novel-format.md) |
| `reading/<id>/` | the beta reader's shelf and rounds for one novel; `<id>` is neutral (`tools/clean.py` names it) |
| `research/<genre>/` | a genre study (gitignored). Before running one, read [docs/genre-study.md](docs/genre-study.md) |
| `bench/<experiment>/` | experiment arms and blind copies (gitignored); name the novel in its `key.md` |
| `docs/` | for maintainers; no room agent reads it. Roadmap, architecture, lessons, experiments, sessions |

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
- **Agent-facing files point, they don't import.** A pointer says when to read: "Before X, read
  `path`", or an index row's *open it when*. Never `@path`: it loads the file at every launch. A kb
  doc over 100 lines opens with a `## Contents` list (`tools/kb_check.py` warns).
- **Docs for people get diagrams.** In `README.md` and `CONTRIBUTING.md`, draw a flow with the
  `mermaid` skill as a fenced `mermaid` block instead of more prose. Agent-facing files get none.
- **Knowledge-base examples use invented nouns**, never the current novel's.
- **Agents register at session start.** Editing a `kb/<role>/prompt.md` takes effect on the next
  spawn; editing `.claude/agents/*.md` may need a new session.
- **Python:** standard library by default; a dependency is fine when it earns its place — record
  it in `requirements.txt`.
- **Commit only when the user asks.**

# Compact instructions

The context is summarised at 250k tokens (`autoCompactWindow`). Keep: the user's request and every
standing instruction they gave; the novel's slug, the chapter and step, the `/write` count left; the
id and name of every agent in flight or to be continued warm (`writer-chNN`, `planner-chNN`,
`continuity-chNN`); the working log's path and `.test-run`'s state; decisions made and not yet
written down. Drop hand-back texts, tool output and file contents: they are on disk, and
`python3 tools/room.py where novels/<slug>` and the session's handoff in `docs/sessions/` recover
them.
