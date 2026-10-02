---
okf_version: "0.2"
---
# Knowledge bases

One bundle per role. Each role reads its own `index.md` first, then its `prompt.md`, then the
documents its index points to when they apply. One level of disclosure: index, then document.

| bundle | who reads it |
|---|---|
| [showrunner/](showrunner/index.md) | the main session |
| [planner/](planner/index.md) | the planner |
| [writer/](writer/index.md) | the writer |
| [beta-reader/](beta-reader/index.md) | the beta reader — and nobody else |
| [story-editor/](story-editor/index.md) | the story editor |
| [line-editor/](line-editor/index.md) | the line editor |
| [continuity-editor/](continuity-editor/index.md) | the continuity editor |
| [clerk/](clerk/index.md) | the clerk |
| [judge/](judge/index.md) | the judge — and nobody else |
| [shared/](shared/index.md) | documents several roles open; linked from each role's index |

Every document except an `index.md` carries OKF frontmatter with a non-empty `type` (`protocol`,
`howto`, `example`, `reference`, `catalog`). How to write one: `docs/roadmap/03-knowledge-bases.md`.
