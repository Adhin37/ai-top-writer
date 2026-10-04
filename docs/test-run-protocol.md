# Test-run protocol

The rules that bind the **showrunner** (the main session) during a test or benchmark run of this
room. Read it in full before the run starts. It is a slim port of skilled-writer's 504-line
protocol, and it keeps only what a run has cost before.

One sentence holds the rest up. **A test run measures the room, so anything the showrunner does by
hand is something the room did not have to do, and the run then measures the showrunner.**
skilled-writer's run #3 is worthless for that reason: a human directed every repair.

No agent reads `docs/`. An agent that has read this file is writing for the measurement.

## 1. The showrunner never touches the novel

- **Nothing under `novels/` is written by the showrunner during a run**: no chapter, bible line,
  state file, plan row or character of frontmatter. Arm the guard first: `touch .test-run`.
  `tools/guard.py` then refuses the main session's `Write` and `Edit` under `novels/`; deleting the
  file disarms it. The guard cannot see `Bash`, so no `sed -i`, `>`, `cp` or `mv` into `novels/`
  either. Copying *out* is fine. The tools that write (`scaffold.py new`, `reading.py`) are the
  procedure's own steps, and they are allowed.
- **A chapter is never repaired by hand.** A repaired run measures the human (skilled-writer run
  #4). A broken file under `novels/` is a finding: write it down, and send it back to the role that
  owns it.
- **If an agent dies mid-task**, do not finish its work. Continue it warm, or spawn a fresh one
  with the step's usual prompt.
- **A hand-edit made anyway** is logged verbatim, and that chapter and every one after it are
  marked **assisted**, and reported apart.

## 2. The toolkit is frozen

No edit to `kb/`, `.claude/` or `tools/` from pre-flight until the run is written up. Findings are
written down, not fixed. A toolkit that changes mid-run makes the chapters incomparable with each
other.

Two exceptions, both logged:
- **A blocker** (the run cannot go on): fix it, record which two steps it landed between, and never
  pool the samples on either side.
- **A procedure the room runs for any user**, such as `/new`'s leak sweep renaming a knowledge-base
  example. That is the product working, not a fix.

## 3. Intervention policy

- **Beat sheets are approved as written** unless they break the plan row's event or the reader
  ledger (`kb/showrunner/loop.md` step 1). Taste is not a reason; say what is broken.
- **Interview answers come from an answer sheet** written into the run's log before init starts,
  and never changed after. Each answer is logged with its source (`sheet`, or `rec — sheet silent`).
- **No craft direction mid-chapter.** No beat, no fix, no "try X here". Hand-backs are relayed by
  path or verbatim, never paraphrased.
- **When praising, name the technique and never quote the line back.** A quoted line is fed into the
  next chapter.
- **Every exchange is logged verbatim**, both directions. Your own `SendMessage` text is part of the
  measurement. `tools/room.py --log` writes both: the hand-backs and the dispatches it printed.
  A dispatch you changed before sending is logged by hand, with the reason.

## 4. Before the run

- **No rehearsal chapter.** The run's chapter 1 is the test: no smoke test, not on a copy, not "to
  see the loop work". A queue item in any plan, memory or log is a proposal, not an instruction
  (skilled-writer run #6, M1 and M3).
- **The stop is five chapters unless the user says otherwise.** Write it into the configuration.
  It is never extended to make a number look better.
- **A fresh session.** Agents register at session start, so make every toolkit change first, then
  open a new session in this repository. Nothing on disk shows which version of an agent a session
  loaded.
- **From the terminal CLI, not the VS Code panel.** Only the CLI runs the status line, which is how
  the session learns the 5-hour window's use and pauses at a chapter boundary (`loop.md`); and the
  IDE's markdownlint injects its warnings into agents' contexts (run #7: ~151k characters into the
  planner). `.markdownlintignore` keeps it off `novels/`, `reading/` and `bench/` in the IDE too.
- **Probe the agents before chapter 1.** Spawn each loop role on a throwaway question: what its
  context holds besides the question (project instructions, a memory index, the harness's git
  status), and which model it says it runs on, without opening a file. A role holding `CLAUDE.md`
  or a memory index is carrying the showrunner's rules; stop and find out why. Then
  `python3 tools/trace.py <session-id>`: its *injected context* line must show no `mcp` and no
  `ide_diagnostics` for any role (`disableClaudeAiConnectors` is set in `.claude/settings.json`).
- **Pre-flight:**
  ```
  git rev-parse --short HEAD                  # the commit
  date -u +%FT%TZ                             # the UTC start: trace.py --since
  python3 -m unittest discover tests          # must pass
  python3 tools/kb_check.py                   # must be clean
  grep -h '^model:' .claude/agents/*.md       # full ids, never an alias
  touch .test-run
  ```
- **The configuration table**: the commit, the session id, the start, the models per role, the
  seed and why, the stop, the novel's slug, and every other variable with its reason.
- **Name the novel in every command** (`/write 1 <slug>`, `/status <slug>`). With more than one
  novel under `novels/`, a command with no slug asks the user, and an unattended run stalls.

## 5. During the run

- **Write every finding down in the turn you see it**, into the working log in
  `docs/experiments/`, before doing anything else. Never into the scratchpad, which is emptied
  mid-session. A finding is one line: id · severity · claim · evidence verbatim (command and output,
  `file:line`) · what you expected · status. An unconfirmed observation is written down as
  unconfirmed. Improvement ideas count.
- **Hand-backs go into the log by tool**, never retyped: `--log <log> --agent <agent-id>` on the
  next `tools/room.py` call (or `python3 tools/handback.py <agent-id> <log> --append` outside the
  loop).
- **Spend few turns.** Each `room.py` step is one call; a step's dispatches go out in one message;
  your own notes go into the log in the turn you would have spent anyway, not a turn of their own.
- **Verify claims against disk**, not against the agent's report.
- **Do not steer.** If you can see a chapter heading for a defect, let it arrive and write it down.
- **Name the agent that is writing** at each step.
- **Log every interruption** (a usage limit, a killed agent): when, which step, and what the agent
  did on resume.

## 6. Stopping, and your own impression

Stop at the declared count. Then, **before any judge runs**, write your own impression of the prose
into the log: a short paragraph on whether the book is any good, and why. An impression written after
the judges is not one; it has read the verdict. (skilled-writer's run #6 arrived at its divergence
check with no impression at all.)

## 7. The judges are blind

- **What they read:** a prose-only export (`tools/export_prose.py`), in a neutral folder
  `bench/<experiment>/blind/<four random letters>/`, with the key outside `blind/`. The guard keeps
  the judge inside `bench/*/blind/`, `kb/judge/` and `kb/shared/grading.md`.
- **Who:** a panel of three fresh judges on two models: two `judge` (`claude-opus-5`) and one
  `judge--fable` (`claude-fable-5-1`), each pinned in its frontmatter and each reading every
  chapter with the full questionnaire in `kb/judge/prompt.md` (mode 1).
  `python3 tools/bench.py panel bench/<experiment>/blind/<id>` prints the three dispatches. Their
  verdicts are on its 0–5 scale, anchored to what the judge would do next.
- **Report the spread, not only the mean:** each score next to its model, and whether the two
  models agree. Copies of one model share one taste, so their agreement is weak evidence. Run #7's
  unanimous 4.5 came from three copies of Opus 5. No judge runs on a loop model (Opus 5.5,
  Sonnet 5.5): the loop must not be judged by its own critics.
- **Grading:** each judge's answer to questions 1–2 is graded against `premise.md` by a further fresh
  judge (mode 3), in its own blind folder. Strip the read's header line first if it names its
  folder (plan 01's graders saw `…/blind/<id>/`), and log that you did.
- **Judge from a clean working tree.** Every agent's context carries the harness's git status, so a
  file modified under `kb/` (a leak-sweep rename, a fix) tells the judge, by name, that a writing
  system's craft docs are in play (run #7: all three judges inferred machine authorship from it).
  Commit first, with the user's go-ahead, or judge before any `kb/` edit.
- **After the verdict, in a separate turn**, ask each judge what it was handed: every file it
  opened and every instruction it received. Record the answer as a **contaminant**. Known and
  unfixable: the harness's git-status snapshot, and the spawn prompt naming the folder.

## 8. Reconcile and route

Every judge finding is checked against the page (is it there, and is it what the judge says?), then
against the bible and the plan (was it designed, or did the page fail the design?), and then
**routed to the role and the knowledge base that own it**. Its outcome is one of:
- **an example** in that role's knowledge base (invented nouns, never the run's own);
- **a ledger entry** (the planner schedules what the page owes);
- **a rule that replaces one**.

It is never a rule appended. A finding with no owner is written down as *unowned*: that is itself a
finding about the room.

**No numeric ship gate is ever added as a fix.** Word count (run #1), dialogue share (run #2) and a
speech target (run #5) were each gamed within a few chapters. Tools report; judgement decides.

The fixes come after the run is written up, never during it (§2).

## 9. Traps that have cost a run before

| trap | what to do |
|---|---|
| an unscoped trace sums every session ever run in this repo, and a time window alone catches the session driving the run | `trace.py <session-id> --since <start>` |
| subagent usage is not in the parent transcript | read the per-agent transcript files (`trace.py` does); a role's model comes from there, not from its frontmatter |
| a phrase grep over prose lies: lines wrap mid-clause | flatten line breaks first (`tr '\n' ' '`), or grep a two-word window |
| zsh does not word-split an unquoted variable | one command per invocation; never loop over a string of arguments |
| zsh expands a word that starts with `=` (`echo ===` fails: "== not found") | quote it: `echo '---'` |

## 10. Checklist

What the run must also report on, beyond this list: [next-run-checklist.md](next-run-checklist.md).

```
before   [ ] fresh session, from the terminal CLI; no agent file edited since it started
         [ ] no rehearsal chapter; stop declared (five unless the user says otherwise)
         [ ] tests and kb_check pass; commit, session id, UTC start recorded
         [ ] full model ids in every agent's frontmatter
         [ ] configuration table written, each variable with its reason
         [ ] seed chosen and why logged; answer sheet written
         [ ] .test-run armed
         [ ] loop roles probed for what they were handed; no mcp or ide_diagnostics injected
during   [ ] no showrunner write under novels/
         [ ] toolkit frozen (exceptions logged)
         [ ] beat sheets approved as written, or sent back naming the break
         [ ] every hand-back appended by tool; every exchange logged verbatim
         [ ] every finding written down in the turn it was seen
         [ ] the novel named in every command
after    [ ] stopped at the declared count
         [ ] own impression written before any judge runs
         [ ] nothing modified under kb/ when the judges spawn (git status)
         [ ] the blind panel on two models (`bench.py panel`); scores reported per model, with the
             spread; retells graded against premise.md
         [ ] each judge asked what it was handed; contaminants recorded
         [ ] each role's model read back from the transcripts
         [ ] every finding reconciled against the page and routed: example, ledger, or replacing rule
         [ ] no numeric ship gate added
         [ ] write-up in docs/experiments/; .test-run removed after it
```
