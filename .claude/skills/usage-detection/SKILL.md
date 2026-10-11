---
name: usage-detection
description: Read the live usage of the 5-hour and 7-day limits, the numbers claude.ai and /usage show, instead of guessing them. Use before a long step or a run, when a hook's usage warning looks wrong, or when the user asks how much usage is left.
---

# Usage detection

`python3 .claude/skills/usage-detection/scripts/live.py` prints both windows and when each resets,
fetched now from the account's usage endpoint, the one `/usage` reads. It saves the reading to
`docs/sessions/usage-live.json`.

The handoff hooks (`.claude/skills/handoff/scripts/session_hooks.py`) and `tools/room.py`'s
`PAUSE` read it on their own, in this order:

1. the status line's reading (`usage.json`), where the terminal CLI runs one;
2. this live reading, refetched at most every two minutes.

Nothing else: with neither, no hook warns and `room.py` prints no PAUSE. Run `live.py` to see why
one failed: no credentials file (macOS keeps the login in the Keychain), an
expired login (any Claude Code request refreshes it), or no network.

Act on the live number as on the status line's: 80% of the 5-hour window, finish the step and
start no new chapter; 95% of either window, the handoff skill.
