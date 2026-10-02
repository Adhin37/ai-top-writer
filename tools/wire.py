#!/usr/bin/env python3
"""Parse and check what roles write for each other, in the wire format (`kb/shared/wire.md`).

What can be checked:

  * a **status line**, the one line a role's final message is: `VERB <head> | key value | ...`;
  * a **hand-back**, a whole final message: the status line must come first, and only the lines
    its role may add (`gap`, `changed`, `left`, `across`) may follow it;
  * a **notes file** (`notes-rK.md`, the story editor's);
  * a **facts file** (`facts-rK.md`, the writer's);
  * a **continuity file** (`continuity-rK.md`, the continuity editor's);
  * a **fold file** (`fold.md`, the clerk's list of new facts for the bible).

Findings print as `level check: detail`, where level is `defect`, `warn` or `note`, plus words per
section as notes. It reports and never gates: the exit status is 0 whatever it finds, unless the
input cannot be read.

Usage:
  wire.py status "<line>"
  wire.py handback FILE          (a filed hand-back, e.g. from tools/handback.py)
  wire.py check FILE...          (notes-, facts-, continuity-rK.md or fold.md, by name)
"""
import argparse
import os
import re
import sys

# verb -> (the head's meaning, required keys, lines that may follow the status line)
VERBS = {
    "DRAFT READY": ("draft", ("facts", "new", "stets", "couldn't"),
                    ("learns", "new", "couldn't", "notes", "choices")),
    "NOTES READY": ("notes file", ("notes", "owed"), ()),
    "PLANNER DONE": ("task", ("gaps", "changed"), ("gap", "changed")),
    "PLANNER ASKS": ("round file", ("round", "questions"), ()),
    "SAMPLES READY": ("samples file", ("samples",), ()),
    "POLISHED": ("output path", ("changes", "left"), ("left", "across")),
    "CONTINUITY READY": ("continuity file", ("findings", "lint"), ()),
    "CLERK DONE": ("chapter", ("fold", "bible", "ledger", "check"), ()),
}
STATUS = re.compile(r"^(%s)\s+(.*)$" % "|".join(re.escape(v) for v in VERBS))
VERDICTS = ("ACCEPT", "REVISE")
GRADES = ("stated", "partly", "missing", "wrong")
OWED = re.compile(r"^([A-Z]+\d+[a-z]?)\s+(\S+)(.*)$")
NOTE_HEAD = re.compile(r"^N(\d+)\b")
QUOTE = re.compile(r'"([^"]*)"')
NOTE_FIELDS = ("where", "ev", "eff", "dir")
FACT_KEYS = ("learns", "new", "couldn't", "notes", "choices")
LONG_QUOTE = 25     # words: a quote this long is proving, not locating
MAX_NOTES = 5
MAX_CHOICES = 3
FINDING = re.compile(r"^F(\d+)\s+(\S+)\s+(.*)$")
FINDING_KINDS = ("bible", "state", "time", "travel", "lexicon", "number", "know")
FOLD_KEYS = ("new", "stale")


def finding(level, check, detail):
    return (level, check, detail)


def parse_status(line):
    """(verb, head, fields, findings). `verb` is None when the line is not a status line."""
    m = STATUS.match((line or "").strip())
    if not m:
        return None, "", {}, [finding("defect", "status", "not a status line: %r"
                                      % (line or "").strip()[:80])]
    verb, rest = m.group(1), m.group(2)
    parts = [p.strip() for p in rest.split(" | ")]
    head, fields, found = parts[0], {}, []
    for part in parts[1:]:
        if verb == "NOTES READY" and part in VERDICTS:
            fields["verdict"] = part
            continue
        if verb == "PLANNER DONE" and "files" not in fields and not fields:
            fields["files"] = part
            continue
        key, _, value = part.partition(" ")
        fields[key] = value.strip()
    if not head:
        found.append(finding("defect", "status", "%s names no %s" % (verb, VERBS[verb][0])))
    for key in VERBS[verb][1]:
        if key not in fields:
            found.append(finding("defect", "status", "%s has no `%s`" % (verb, key)))
    if verb == "NOTES READY":
        if fields.get("verdict") not in VERDICTS:
            found.append(finding("defect", "status", "NOTES READY needs ACCEPT or REVISE"))
        if "owed" in fields and not re.match(r"^\d+/\d+$", fields["owed"]):
            found.append(finding("warn", "status", "owed should read <stated>/<due>, got %r"
                                 % fields["owed"]))
    return verb, head, fields, found


def check_handback(text):
    """Findings for a whole final message: status line first, nothing but its own lines after."""
    lines = [l for l in (text or "").splitlines() if l.strip()]
    if not lines:
        return [finding("defect", "handback", "empty")]
    first = next((i for i, l in enumerate(lines) if STATUS.match(l.strip())), None)
    if first is None:
        return [finding("defect", "handback", "no status line")]
    found = []
    if first:
        found.append(finding("defect", "handback", "%d line(s), %d words before the status line"
                             % (first, sum(len(l.split()) for l in lines[:first]))))
    verb, _, _, status_found = parse_status(lines[first])
    found += status_found
    allowed = VERBS[verb][2]
    extra = [l for l in lines[first + 1:] if l.strip().split(" ", 1)[0] not in allowed]
    if extra:
        found.append(finding("warn", "handback", "%d line(s), %d words after the status line "
                             "that %s does not take" % (len(extra),
                                                        sum(len(l.split()) for l in extra), verb)))
    return found


def sections(text):
    """{heading: [lines]} for `## ` sections, with the lines before the first under ''."""
    out, current = {"": []}, ""
    for line in text.splitlines():
        if line.startswith("## "):
            current = line[3:].strip()
            out.setdefault(current, [])
        elif line.strip() and not line.startswith("# "):
            out[current].append(line.rstrip())
    return out


def words(lines):
    return sum(len(l.split()) for l in lines)


def long_quotes(line):
    return [q for q in QUOTE.findall(line) if len(q.split()) > LONG_QUOTE]


def check_notes(text):
    found = []
    secs = sections(text)
    header = " ".join(secs.get("", []))
    m = re.search(r"\bverdict\s+(\w+)", header)
    verdict = m.group(1) if m else None
    if verdict not in VERDICTS:
        found.append(finding("defect", "notes", "no `verdict ACCEPT|REVISE` header line"))
    for key in ("owed", "event", "ending", "click-next"):
        if not re.search(r"\b%s\b" % re.escape(key), header):
            found.append(finding("warn", "notes", "header has no `%s`" % key))
    for name in ("Owed", "Notes", "Keep"):
        if name not in secs:
            found.append(finding("defect", "notes", "no `## %s` section" % name))

    for line in secs.get("Owed", []):
        if line.strip().startswith("beat "):
            continue                    # a beat-sheet item with no ledger id: not counted
        m = OWED.match(line.strip())
        if not m or m.group(2) not in GRADES:
            found.append(finding("warn", "owed", "not `<id> <grade> \"<retell>\"`: %r"
                                 % line.strip()[:60]))
        elif m.group(2) == "stated" and not QUOTE.search(line):
            found.append(finding("warn", "owed", "%s stated without the retell's words"
                                 % m.group(1)))

    notes, current = [], None
    for line in secs.get("Notes", []):
        if NOTE_HEAD.match(line.strip()):
            current = {"id": line.strip().split()[0], "fields": set()}
            notes.append(current)
            continue
        key = line.strip().split(" ", 1)[0]
        if current is not None and key in NOTE_FIELDS:
            current["fields"].add(key)
            for q in long_quotes(line):
                found.append(finding("note", "quote", "%s %s quotes %d words; about twelve "
                                     "locate a passage" % (current["id"], key, len(q.split()))))
        else:
            found.append(finding("warn", "notes", "line outside a note's fields: %r"
                                 % line.strip()[:60]))
    for n in notes:
        for key in ("where", "ev", "eff"):
            if key not in n["fields"]:
                found.append(finding("defect", "note", "%s has no `%s`" % (n["id"], key)))
    if len(notes) > MAX_NOTES:
        found.append(finding("defect", "notes", "%d notes; at most %d" % (len(notes), MAX_NOTES)))
    if verdict == "REVISE" and not notes:
        found.append(finding("warn", "notes", "REVISE with no notes"))
    if not secs.get("Keep"):
        found.append(finding("warn", "keep", "*Keep* is empty"))
    for name, lines in secs.items():
        found.append(finding("note", "words", "%s: %d" % (name or "header", words(lines))))
    return found


def check_facts(text):
    found, counts = [], {}
    for line in text.splitlines():
        if not line.strip() or line.startswith("#"):
            continue
        key = line.strip().split(" ", 1)[0]
        if key not in FACT_KEYS:
            found.append(finding("warn", "facts", "unknown key: %r" % line.strip()[:60]))
            continue
        counts[key] = counts.get(key, 0) + 1
        for q in long_quotes(line):
            found.append(finding("note", "quote", "%s quotes %d words" % (key, len(q.split()))))
    for key in ("learns", "couldn't"):
        if key not in counts:
            found.append(finding("warn", "facts", "no `%s` line" % key))
    if counts.get("choices", 0) > MAX_CHOICES:
        found.append(finding("warn", "facts", "%d choices; at most %d"
                             % (counts["choices"], MAX_CHOICES)))
    found.append(finding("note", "words", "new facts: %d, words: %d"
                         % (counts.get("new", 0), words(text.splitlines()))))
    return found


def check_continuity(text):
    """The continuity editor's file: a `lint` line, a `checked` line, then one `F<n> <kind>
    "<quote>" | <source>: "<line>" | <defect>` line each, or `none`."""
    found, count = [], 0
    has_lint = False
    for line in text.splitlines():
        s = line.strip()
        if not s or s.startswith("#"):
            continue
        if s.startswith("lint "):
            has_lint = True
            continue
        if s.startswith("checked "):
            continue
        if s == "none":
            continue
        m = FINDING.match(s)
        if not m:
            found.append(finding("warn", "continuity", "not a finding line: %r" % s[:60]))
            continue
        count += 1
        tag, kind, rest = "F" + m.group(1), m.group(2), m.group(3)
        if kind not in FINDING_KINDS:
            found.append(finding("warn", "finding", "%s kind `%s` is not one of %s"
                                 % (tag, kind, " ".join(FINDING_KINDS))))
        parts = [p.strip() for p in rest.split(" | ")]
        if len(parts) != 3:
            found.append(finding("defect", "finding", "%s needs three parts, quote | source | "
                                 "defect; has %d" % (tag, len(parts))))
            continue
        if not QUOTE.search(parts[0]):
            found.append(finding("defect", "finding", "%s has no quote from the draft" % tag))
        if ":" not in parts[1]:
            found.append(finding("warn", "finding", "%s source should read `<file or id>: "
                                 "\"<line>\"`" % tag))
        for q in long_quotes(line):
            found.append(finding("note", "quote", "%s quotes %d words" % (tag, len(q.split()))))
    if not has_lint:
        found.append(finding("warn", "continuity", "no `lint` line"))
    found.append(finding("note", "words", "findings: %d, words: %d"
                         % (count, words(text.splitlines()))))
    return found


def check_fold(text):
    """The clerk's fold file: `new <fact> | <bible file> | "<quote>"` and `stale <bible line> |
    <bible file> | <why>` lines, one fact a line."""
    found, counts = [], {}
    for line in text.splitlines():
        s = line.strip()
        if not s or s.startswith("#") or s == "none":
            continue
        key = s.split(" ", 1)[0]
        if key not in FOLD_KEYS:
            found.append(finding("warn", "fold", "unknown key: %r" % s[:60]))
            continue
        counts[key] = counts.get(key, 0) + 1
        parts = [p.strip() for p in s[len(key):].split(" | ")]
        if len(parts) != 3:
            found.append(finding("defect", "fold", "%s line needs three parts: %r"
                                 % (key, s[:60])))
            continue
        if not parts[1].startswith("bible/"):
            found.append(finding("warn", "fold", "%s names no bible file: %r" % (key, parts[1])))
        if key == "new" and not QUOTE.search(parts[2]):
            found.append(finding("warn", "fold", "new fact with no quote from the chapter: %r"
                                 % parts[0][:40]))
    found.append(finding("note", "words", "new: %d, stale: %d"
                         % (counts.get("new", 0), counts.get("stale", 0))))
    return found


def check_file(path):
    with open(path, encoding="utf-8") as fh:
        text = fh.read()
    name = os.path.basename(path)
    for prefix, check in (("notes-", check_notes), ("facts-", check_facts),
                          ("continuity-", check_continuity), ("fold", check_fold)):
        if name.startswith(prefix):
            return check(text)
    return [finding("warn", "file", "%s is not a notes-, facts- or continuity-rK.md, or fold.md"
                    % name)]


def render(found):
    return "\n".join("%s %s: %s" % f for f in found) or "clean"


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    sub = ap.add_subparsers(dest="cmd", required=True)
    s = sub.add_parser("status")
    s.add_argument("line")
    h = sub.add_parser("handback")
    h.add_argument("file")
    c = sub.add_parser("check")
    c.add_argument("files", nargs="+")
    args = ap.parse_args(argv)
    try:
        if args.cmd == "status":
            verb, head, fields, found = parse_status(args.line)
            if verb:
                print("%s %s %s" % (verb, head, " ".join("%s=%s" % kv for kv in fields.items())))
            print(render(found))
        elif args.cmd == "handback":
            with open(args.file, encoding="utf-8") as fh:
                print(render(check_handback(fh.read())))
        else:
            for path in args.files:
                if len(args.files) > 1:
                    print("== %s" % path)
                print(render(check_file(path)))
    except OSError as exc:
        sys.stderr.write("wire: %s\n" % exc)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
