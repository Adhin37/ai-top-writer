---
type: protocol
title: Extending the plan — showrunner procedure
description: The main session's procedure for /plan — the planner extends the chapter rows, the arcs and the ledger, and squares what the ledger owes with what the plan delivers.
roles: [showrunner]
---
# Extending the plan

Run it when `tools/status.py` says fewer than five rows lie ahead of the last chapter, when the
user gives a direction, or when the ledger is in debt.

1. `python3 tools/status.py novels/{slug} --debt` — what the ledger owes that the plan cannot yet
   deliver.
2. The planner: continue `planner-ch(N+1)` warm if it exists (it folded the last chapter);
   otherwise spawn **planner**. The task: *"Novel: novels/{slug}. Task: plan. Debt: <the tool's
   lines, verbatim>."* Add *"Direction from the user: <their words, verbatim>"* when there is one.
3. It ends on `PLANNER DONE plan | …`. If `gap canon` lines follow it, run the lookup first
   ([loop.md](loop.md), *Canon lookups*). Run the debt check and `tools/state_check.py` again; send
   any line still standing back to the planner, verbatim.
4. Report to the user: the new rows' titles and events, any `changed` line (a planned row the
   direction overturned), and any debt the planner moved, with its reason.
