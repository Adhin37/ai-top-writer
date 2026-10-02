# ai-top-writer

A writers' room for serialized web fiction, run by Claude Code agents: a planner designs the story,
a writer drafts each chapter, a beta reader who has never seen the bible reads it cold, and editors
turn that reader's experience into specific notes the writer revises against.

It is the rebuild of [skilled-writer](../skilled-writer), whose sixth benchmark run shipped five
chapters with zero defects from every instrument and an opening chapter its user could not follow.
Why the rebuild, and what it keeps: [docs/roadmap/00-diagnosis.md](docs/roadmap/00-diagnosis.md).

## Status

Plans 01 (chapter 1), 01b (the wire format), 02 (the full loop across chapters) and 03 (the
knowledge bases) have run. What is built, and whether a run has shown it working: the *Features*
table in [docs/roadmap/README.md](docs/roadmap/README.md), which also says which plan is next.

To run a plan, open Claude Code **in this directory** (agents register when a session starts) and
say *"execute docs/roadmap/NN"*.

## Using it

Four commands, typed in a Claude Code session opened in this directory:

| command | what it does |
|---|---|
| `/new [the story in a few sentences]` | the planner interviews you in seven rounds, each question with an answer it recommends, and writes the bible, cast, premise, reader ledger and arc plan |
| `/write [n]` | the next chapter (or the next `n`) through the room |
| `/plan [a direction]` | more chapter rows and ledger rows, and what the ledger owes squared with what the plan delivers |
| `/status` | where the novel stands: chapters, what the page still owes, the reader's last click-next |

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

## One chapter through the room

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
Every role ends on one status line; what one role needs from another travels in files.

## Layout

```
.claude/agents/   thin agent definitions
.claude/commands/ /new, /write, /plan, /status
kb/               one knowledge base per role (OKF: index.md + typed docs)
tools/            the loop's tools: the scaffold and its check, status, exports and the reader's
                  shelf, lint, state check, the path guard, hand-backs, the wire-format checker,
                  cost traces, session handoffs
tests/            python3 -m unittest discover tests
docs/             roadmap, architecture, novel format, lessons, experiments
novels/           the books (gitignored), and _template/, which /new copies
reading/, bench/  the reader's shelf and experiment arms (gitignored)
```

Requires Python 3.8+ and Claude Code. Standard library only.
