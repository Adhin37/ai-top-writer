---
type: protocol
title: Where the novel stands — showrunner procedure
description: The main session's procedure for /status — read the novel's standing from its files with tools/status.py and report it to the user in plain words.
roles: [showrunner]
---
# Where the novel stands

Read-only: nothing is spawned and nothing is written.

```
python3 tools/status.py novels/{slug}
```

It reads the files: the chapters, the next plan row, the reader's click-next for the last accepted
chapter (from its last round's report), the ledger rows past due and not landed, the open
promises, the threads, and `state_check`'s verdict. Report it to the user in plain words, under
two hundred:

- how many chapters, and what the last one did;
- what the reader said of it, with the click-next as the reader gave it;
- what the page still owes the reader (past-due rows, overdue promises), each in a few words;
- what comes next, and how many rows are planned ahead.

End with the one thing that most needs attention, if anything does: a debt past its chapter, a
cold thread, a plan about to run out (`/plan`), or a state check that is not clean.
