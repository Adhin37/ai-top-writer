"""tools/history.py - the book across chapters, as findings for the line and story editors.

Nothing here gates: the tests check what is found, at what level, under which owner, and that
fewer than three chapters report nothing.
"""
import contextlib
import io
import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from novel_fixture import NovelFixture  # noqa: E402
import history  # noqa: E402

REFRAIN = "Old ropes keep their knots, the ferryman told the gulls. Then they part all at once."

WORDS = (("tally", "door", "chalk"), ("ledger", "window", "ink"), ("chit", "rope", "seal"),
         ("slate", "lamp", "thumb"), ("roll", "stove", "pencil"))
TALK = """"The %s is wrong," Nessa said.

Tam looked at the %s. "Quell did it, with his %s."

"Then Quell can explain the %s," Nessa said.

"That's not an answer," %s said."""
LEXICON = """# Lexicon

## Names
| canonical | who/what | never write as |
|---|---|---|
| Nessa Vane | the rower | Nesa |
| Harbourmaster Quell | the harbour office | Quel |
| Tam Orrin | the boathouse lad | Tom |
"""


def talk(n):
    a, b, c = WORDS[n]
    return TALK % (a, b, c, a, "Tam" if n % 2 else "she")


def body(*parts):
    return "\n\n* * *\n\n".join(parts)


SCENES = """# Scenes

| ch | scene | who | where | tempo | two-hander |
|---|---|---|---|---|---|
| 1 | 1 | Nessa, Tam | the quay | tense | yes |
| 1 | 2 | Nessa, Tam | the boathouse | tense | yes |
| 2 | 1 | Nessa, Tam | the quay | tense | yes |
| 2 | 2 | Nessa, Tam | the bar | tense | yes |
| 3 | 1 | Nessa, Tam | the quay | tense | yes |
"""

PLAN = """# Chapters

| # | title | pov | temp | event | threads |
|---|---|---|---|---|---|
| 1 | One | Nessa Vane | tense | e | ~T1 |
| 2 | Two | Nessa Vane | quiet | e | ^T1 |
| 3 | Three | Nessa Vane | quiet | e | ^T1 |
| 4 | Four | Nessa Vane | quiet | e | ^T1 |
"""


def findings(fx, **kw):
    rep, data = history.history(fx.novel(), **kw)
    return rep.items, data


class HistoryTest(unittest.TestCase):
    def book(self, fx, chapters=3):
        fx.write("bible/world.md", "# World\n\n- The ferry. Old ropes keep their knots, as the "
                                   "ferrymen say.\n")
        fx.write("plan/chapters.md", PLAN)
        fx.write("bible/lexicon.md", LEXICON)
        fx.chapter(1, body(REFRAIN + " She rowed.\n\n" + talk(0), talk(1) + "\n\n" + REFRAIN))
        fx.chapter(2, body(talk(2), "She rowed out.\n\n" + REFRAIN + "\n\n" + talk(3)))
        if chapters >= 3:
            fx.chapter(3, body(REFRAIN + "\n\n" + talk(4)))
        fx.state(blocks=(), scenes=SCENES)

    def test_a_refrain_is_counted_across_chapters_with_its_bible_line(self):
        with NovelFixture() as fx:
            self.book(fx)
            items, data = findings(fx)
        motif = [d for lv, c, d in items if c == "motif" and lv == "warn"]
        self.assertEqual(len(motif), 1, items)
        self.assertIn("Old ropes keep their knots", motif[0])
        self.assertIn("x4 in ch 1 (2), 2, 3", motif[0])
        self.assertIn("also in bible/world.md:3", motif[0])
        self.assertEqual(data["motifs"][0]["chapters"], [1, 1, 2, 3])

    def test_a_line_in_several_mouths_is_a_signature_and_a_refrain_is_not(self):
        with NovelFixture() as fx:
            self.book(fx)
            items, _data = findings(fx)
        sigs = [d for _lv, c, d in items if c == "signature"]
        self.assertTrue(any("that's not an answer" in d and "(spoken only)" in d for d in sigs),
                        sigs)
        # the refrain's own words, and its tail, are the motif's
        self.assertFalse(any("knots" in d or "all at once" in d for d in sigs), sigs)
        # a phrase with a name in it is the setting's, never a signature
        self.assertFalse(any("quell" in d for d in sigs), sigs)

    def test_two_handers_and_their_run(self):
        with NovelFixture() as fx:
            self.book(fx)
            items, data = findings(fx)
        talk = [(lv, d) for lv, c, d in items if c == "two-hander"]
        self.assertEqual(len(data["conversations"]), 5)
        self.assertTrue(all(len(c["speakers"]) <= 2 for c in data["conversations"]))
        self.assertIn(("warn", "5 two-handers in a row, c1 s1 to c3 s1"), talk)
        # five conversations is under the six a share needs before it is a shape
        self.assertTrue(any(lv == "note" and d.startswith("5 of 5") for lv, d in talk), talk)

    def test_tempo_runs_from_the_scene_log_and_the_plan(self):
        with NovelFixture() as fx:
            self.book(fx)
            items, _data = findings(fx)
        tempo = [(lv, c, d) for lv, c, d in items if c in ("tempo", "temp")]
        self.assertIn(("warn", "tempo", "5 scenes in a row at tense, ch 1 to ch 3"), tempo)
        self.assertIn(("warn", "tempo", "3 chapters in a row open tense: ch 1-3"), tempo)
        self.assertIn(("note", "temp", "ch 2 was planned quiet and played tense, tense"), tempo)
        self.assertFalse(any(c == "temp" and lv == "warn" for lv, c, _d in tempo), tempo)

    def test_a_draft_stands_in_for_the_next_chapter(self):
        with NovelFixture() as fx:
            self.book(fx, chapters=2)
            draft = fx.write("work/ch0003/draft-r0.md", "---\nnumber: 3\n---\n\n" + REFRAIN)
            items, data = findings(fx)
            self.assertEqual((items, data["chapters"]), ([], [1, 2]))
            items, data = findings(fx, draft=draft)
            self.assertEqual((data["chapters"], data["draft"]), ([1, 2, 3], 3))
            self.assertTrue(any(c == "motif" for _lv, c, _d in items))
            # --upto drops later chapters, and the draft follows the last one kept
            _items, data = findings(fx, draft=draft, upto=1)
            self.assertEqual(data["chapters"], [1, 2])

    def test_the_report_names_each_owner_and_never_gates(self):
        with NovelFixture() as fx:
            self.book(fx)
            out = os.path.join(fx.tmp, "history.txt")
            buf = io.StringIO()
            with contextlib.redirect_stdout(buf):
                rc = history.main([fx.root, "--out", out])
            self.assertEqual(rc, 0)
            text = buf.getvalue()
            self.assertIn("## for the line editor", text)
            self.assertIn("## for the story editor", text)
            self.assertIn("findings to weigh, not gates", text)
            with open(out, encoding="utf-8") as fh:
                self.assertEqual(fh.read(), text)
        with contextlib.redirect_stderr(io.StringIO()):
            self.assertEqual(history.main(["/no/such/novel"]), 1)

    def test_fewer_than_three_chapters_say_so(self):
        with NovelFixture() as fx:
            self.book(fx, chapters=2)
            buf = io.StringIO()
            with contextlib.redirect_stdout(buf):
                history.main([fx.root])
        self.assertIn("nothing across chapters to report before ch 3", buf.getvalue())


if __name__ == "__main__":
    unittest.main()
