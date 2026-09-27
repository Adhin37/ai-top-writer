---
name: handoff
description: Hand a session over across a usage-limit reset, or pick one up. Use when a hook says usage is near the limit, when a hook points at a handoff in docs/sessions/, after a session was stopped by a usage limit (HTTP 429, "You've hit your session limit"), or when the user asks to hand off, pause, resume or continue where the last session left off.
---

# Handoff

Hooks keep `docs/sessions/<session-id>.md` current without you: they rebuild it from the transcripts
at the end of every turn and at the moment a usage limit stops the session (`tools/checkpoint.py`).
It holds the user's messages, your last messages, the agents in flight with what each wrote since
its last instruction, the files written, and each in-flight agent's spawn prompt, verbatim.

Two things only you can add: the **note**, and **closing** the handoff once its work is resumed.

## Near the limit

When a hook says usage has reached the threshold:

1. **Spawn no new agent.** One started now dies half-way. Agents already running carry on.
2. **Write the note** in your own handoff, between `<!-- note -->` and `<!-- /note -->`. Keep it to
   ten lines at most: the plan and step you are on, the exact next action, and anything decided in
   this conversation that is on no file yet. Rebuilds keep the note.
3. Run `python3 tools/checkpoint.py` and tell the user, in one line, where the handoff is and when
   the limit resets.

## Resuming

When a hook points you at a handoff, or the user asks you to continue after a limit:

1. Tell the user what stopped and when, in one line. Then read the handoff: the note first, then
   *Agents in flight*.
2. For each agent in flight, compare what its instruction asked for with what is on disk. A file it
   wrote may be complete; open it to be sure.
   - **This is the stopped session itself**, i.e. its id is this session's (resumed, or continued
     after the reset): `SendMessage` to the agent's id — *"You were cut off by a usage limit after
     writing <file>. Finish per your procedure, then hand back."* Its memory is intact.
   - **This is a fresh session**: the old agents cannot be reached. Spawn the same agent type with
     its spawn prompt from the handoff, verbatim, plus its latest instruction if it has one, then
     one line: *"An earlier run was cut off by a usage limit; <files> exist from it."* A warm agent,
     for example a writer continued round after round, loses its memory this way. Tell the user,
     and in a test run log it as a deviation in the run's working log.
   - A hand-back that reached no file is filed from the agent's transcript with
     `tools/handback.py`, never retyped.
3. Carry on from the note's next action, or from where the last messages leave off.
4. Close it: `python3 tools/checkpoint.py --close <session-id>`, so the hooks stop pointing at it.
5. Tell the user in three lines or fewer what you resumed, what you re-spawned and what comes next.

If the user would rather do something else first, do that and leave the handoff open.

## Which session to resume in

The user chooses. Reopening the stopped session keeps warm agents' memory, but it re-reads the
whole context uncached (the handoff's `context_tokens` says how much). A fresh session starts from
the handoff alone. If asked, recommend the fresh session unless a warm agent's memory matters.
