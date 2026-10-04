# ai-top-writer

A writers' room for serialized web fiction (Royal Road / webnovel.com style), run by Claude Code
agents: a planner designs the story, a writer drafts each chapter, a beta reader who has never seen
the bible reads it cold, and editors turn that reader's experience into specific notes the writer
revises against.

It is the rebuild of [skilled-writer](https://github.com/Adhin37/skilled-writer), whose sixth
benchmark run shipped five chapters with zero defects from every instrument and an opening chapter
its user could not follow. Why the rebuild, and what it keeps:
[docs/roadmap/00-diagnosis.md](docs/roadmap/00-diagnosis.md).

## The idea in one picture

You talk to one Claude Code session, the **showrunner**. It writes no prose: it runs a loop of
specialised agents, moves their files with Python tools, and relays what one agent hands back to
the next.

```mermaid
flowchart LR
    U(["you"]) -->|"/new · /write · /plan · /status"| S["showrunner<br/>(the main session)"]
    S -->|"one call per loop step"| T["tools/room.py<br/>and the other tools"]
    T -->|"prints the next dispatch"| S
    S -->|"spawns, relays<br/>hand-offs verbatim"| R["the room (.claude/agents/)<br/>planner · writer · story editor (opus)<br/>beta reader · continuity editor<br/>line editor · clerk (sonnet)"]
    KB[("kb/&lt;role&gt;/<br/>one knowledge base per role")] -.->|"each role reads its own"| R
    R <-->|"read / write"| N[("novels/&lt;slug&gt;/<br/>bible · plan · state · chapters")]
    T -->|"prose-only exports"| RD[("reading/&lt;id&gt;/<br/>the reader's shelf")]
    N --> T
    R <-->|"the beta reader<br/>sees only this"| RD
```

A ninth role, the **judge**, is not in the loop. It reads blind copies in `bench/` for benchmarks,
with a different questionnaire from the beta reader's, so the room cannot tune itself to its judge.

## Status

Rebuild in progress. Plans 01 to 06c have run: chapter 1, the wire format, the full loop across
chapters, the knowledge bases, setting up a new novel, benchmark run #7 (**4.5 / 5 from three blind
judges**, against 3.5 for skilled-writer's run #6), and the cost measurements. What is built, and
whether a run has shown it working: the *Features* table in
[docs/roadmap/README.md](docs/roadmap/README.md), which also says which plan is next.

## Using it

Install and setup: [CONTRIBUTING.md](CONTRIBUTING.md#setup). Then open Claude Code **in this
directory** (agents register when a session starts) and type one of four commands:

| command | what it does |
|---|---|
| `/new [the story in a few sentences]` | the planner interviews you in seven rounds, each question with an answer it recommends, and writes the bible, cast, premise, reader ledger and arc plan |
| `/write [n]` | the next chapter (or the next `n`) through the room |
| `/plan [a direction]` | more chapter rows and ledger rows, and what the ledger owes squared with what the plan delivers |
| `/status` | where the novel stands: chapters, what the page still owes, the reader's last click-next |

Your book lives in `novels/<slug>/`, which git ignores: the book is yours, not the repo's.

## Starting a novel: `/new`

```mermaid
flowchart TD
    S["showrunner<br/>scaffold.py new: copies novels/_template"] --> Q
    Q["planner asks round N, each question with a recommended answer<br/>1 seed and platform · 2 genre, tone, the protagonist · 3 world and society<br/>4 cast, and when the antagonist's face reaches the page<br/>5 style · 6 premise and ledger · 7 title, blurb, arc plan"] --> U{"you answer<br/>(a test run: the answer sheet)"}
    U -->|"answers, verbatim"| F["planner writes what the round decided<br/>into the novel's files"]
    F -->|next round| Q
    F -->|"after round 4: a style beat"| WR["writer drafts the beat three ways;<br/>round 5 asks which is the book's voice"]
    WR --> Q
    F -->|"round 6: your say-back of the premise<br/>misses a fact"| RW["planner rewrites the premise"]
    RW --> U
    F -->|"after round 7"| CK{"scaffold.py check"}
    CK -->|"defects, verbatim"| F
    CK -->|clean| W["/write: chapter 1"]
```

## One chapter through the room: `/write`

```mermaid
flowchart TD
    P["planner<br/>folds the last chapter's new facts,<br/>then writes the beat sheet"] --> A{"showrunner approves:<br/>event kept, ledger rows due,<br/>every fact has a carrier"}
    A -->|sent back| P
    A --> W["writer<br/>draft rK + facts file"]
    W --> R["beta reader, cold<br/>its notes, the last two chapters,<br/>the draft; retell and report"]
    W --> C["continuity editor<br/>the draft against bible and state;<br/>runs lint"]
    R --> E{"story editor<br/>grades the retell,<br/>merges both reports"}
    C --> E
    E -->|"REVISE: at most 5 notes<br/>(2 revision rounds at most)"| W
    E -->|ACCEPT| L["line editor<br/>one polish pass; reads the<br/>last two chapters for habits"]
    L --> CH[("chapters/NNNN-*.md")]
    CH --> K["clerk<br/>state/, ledger status,<br/>the reader's memory, fold.md"]
    K -->|next chapter| P
```

Each round's beta reader is fresh, and only the accepted round's notes become the reader's memory.

### How a hand-off travels

Agents never pass prose through the showrunner's summary. Each role writes a file and ends on one
**status line** ([kb/shared/wire.md](kb/shared/wire.md)); `tools/room.py` parses it, does the
deterministic work (exports, copies, checks), and prints the exact dispatch for the next agent.

```mermaid
sequenceDiagram
    autonumber
    participant S as showrunner
    participant Room as tools/room.py
    participant W as writer
    participant B as beta reader
    participant C as continuity editor
    participant E as story editor

    S->>W: beat sheet path
    W-->>S: DRAFT READY work/chNNNN/draft-rK.md | facts … | new 9
    S->>Room: round novel N K
    Room->>Room: export the draft prose-only into reading/…/chNN-rK/
    Room-->>S: two dispatches, printed
    par in parallel
        S->>B: reading folder only
        B-->>S: report + notes in reading/
    and
        S->>C: draft + bible + state
        C-->>S: CONTINUITY READY … | findings 2
    end
    S->>Room: judge novel N K reader-id
    Room->>Room: file the reader's report, check the continuity file
    Room-->>S: story editor dispatch, and both branches
    S->>E: retell, reports, beat sheet
    E-->>S: NOTES READY … | REVISE | notes 3
    alt REVISE
        S->>W: continue warm: the notes path
    else ACCEPT
        S->>S: spawn the line editor, then room.py clerk
    end
```

## What the reader knows is state

The bible holds the whole truth. The reader holds only what the page has said. The gap between
them is tracked in files, not guessed at.

```mermaid
flowchart LR
    B["bible/<br/>the whole truth"] --> P["bible/premise.md<br/>what a reader must hold<br/>by the end of chapter 1"]
    B --> L["plan/reader-ledger.md<br/>facts, faces and promises<br/>owed, by chapter"]
    L -->|"due this chapter"| BS["beat sheet"]
    BS --> CH["chapter"]
    CH --> RN["the beta reader's notes<br/>what actually landed"]
    RN -->|"clerk marks rows landed"| L
    L -. "owed but not landed<br/>= exposition debt" .-> PL["planner schedules it<br/>(status.py --debt)"]
```

Chapter 1 is **webnovel-clear**: by its end a reader can state the world's central rule, the
protagonist's situation and the stakes in plain words.

## Who may read what

A reader who knows the bible cannot notice what the page never says, and a writer who can read the
reader's questionnaire writes for the questionnaire. `tools/guard.py`, a `PreToolUse` hook, enforces
the walls (the source of truth is `ROLES` in that file). A missing arrow is a wall: the writer
never sees the reader's reports, and no role in the loop opens `bench/`, `docs/` or the judge's
knowledge base.

```mermaid
flowchart LR
    BR["beta reader"]:::sealed -->|only| RD[("reading/")]
    JD["judge"]:::sealed -->|only| BL[("bench/*/blind/")]
    PL["planner"] --> NV[("novels/")]
    PL -->|"the reader's notes"| RD
    SE["story editor · clerk"] --> NV
    SE --> RD
    WR["writer · line editor ·<br/>continuity editor"] --> NV
    classDef sealed fill:#fde2e4,stroke:#c0392b
```

The beta reader and the judge have no `Bash` tool, which is their real wall; the full table is in
[docs/architecture.md](docs/architecture.md#isolation).

## Layout

```
.claude/agents/    thin agent definitions: frontmatter + "read kb/<role>/prompt.md"
.claude/commands/  /new, /write, /plan, /status
.claude/skills/    handoff: resume a session across a usage-limit reset
.claude/settings.json  permissions, the guard hook, session hooks, the status line
kb/                one knowledge base per role (OKF: index.md + prompt.md + typed docs); kb/shared/
tools/             the loop's tools: one call per loop step (room.py), the scaffold and its
                   check, status, exports and the reader's shelf, lint, history, state check,
                   the path guard, hand-backs, the wire-format checker, cost traces, benchmarks,
                   cleanup, session handoffs
tests/             python3 -m unittest discover tests
docs/              for people only (no agent reads it): roadmap, architecture, novel format,
                   lessons, experiments
novels/            the books (gitignored), and _template/, which /new copies
reading/, bench/   the reader's folders, one per novel, and experiment arms (gitignored;
                   tools/clean.py says which novel each belongs to)
```

Requires Python 3.8+ (standard library only) and Claude Code. Contributing:
[CONTRIBUTING.md](CONTRIBUTING.md).

## License

[LICENSE](LICENSE).
