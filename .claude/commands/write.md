---
description: Write the next chapter, or the next n, through the writers' room loop
argument-hint: "[n] [novel slug]"
---

Write chapters through the room. `$ARGUMENTS` may hold a count `n` (default 1) and a novel's slug;
`kb/showrunner/index.md` says which novel when none is named.

For each of the next `n` chapters, starting after the last accepted one:

1. `python3 tools/status.py novels/{slug}`: if its `next` line says the chapter has no plan row,
   or its `ledger` line counts rows past due and not landed, run `kb/showrunner/plan.md` first.
   Promises paid in a later arc are not debt.
2. Run `kb/showrunner/loop.md`, steps 0 to 7, for that chapter.

Stop after `n` chapters, or earlier if the user says so. A queued chapter is not an instruction.
