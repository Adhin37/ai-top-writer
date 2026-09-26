# ai-top-writer

A writers' room for serialized web fiction, run by Claude Code agents: a planner designs the story,
a writer drafts each chapter, a beta reader who has never seen the bible reads it cold, and editors
turn that reader's experience into specific notes the writer revises against.

It is the rebuild of [skilled-writer](../skilled-writer), whose sixth benchmark run shipped five
chapters with zero defects from every instrument and an opening chapter its user could not follow.
Why the rebuild, and what it keeps: [docs/roadmap/00-diagnosis.md](docs/roadmap/00-diagnosis.md).

## Status

Session 1 (foundation) is done. **Next: [plan 01](docs/roadmap/01-vertical-slice.md)** — chapter 1
through the new loop, against the old toolkit's chapter 1 on the same bible.

To run a plan, open Claude Code **in this directory** (agents register when a session starts) and
say *"execute docs/roadmap/NN"*.

## Layout

```
.claude/agents/   thin agent definitions
kb/               one knowledge base per role (OKF: index.md + typed docs)
tools/            export_prose.py, guard.py
tests/            python3 -m unittest discover tests
docs/             roadmap, architecture, novel format, lessons, experiments
novels/           the books (gitignored)
reading/, bench/  beta-reader exports and experiment arms (gitignored)
```

Requires Python 3.8+ and Claude Code.
