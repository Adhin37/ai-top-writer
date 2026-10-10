"""tools/lint.py - the per-chapter report a critic reads.

Nothing here gates: the tests check what is found and at what level, and that the report stays a
report. Scene-break, markup and thought-tag cases are adapted from skilled-writer's
tests/test_channels.py.
"""
import contextlib
import io
import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from novel_fixture import NovelFixture  # noqa: E402
import lint  # noqa: E402


def found(body, **fields):
    with NovelFixture() as fx:
        path = fx.chapter(1, body, **fields)
        return [(lv, check, detail) for lv, check, _line, detail in lint.lint(path).found]


def checks(body, **fields):
    return {(lv, check) for lv, check, _d in found(body, **fields)}


class FormatTest(unittest.TestCase):
    def test_a_lone_star_or_other_shape_is_not_a_scene_break(self):
        for shape in ("*", "***", "---", "~~~", "* * * *"):
            self.assertIn(("warn", "scene-break"),
                          checks("She stopped.\n\n%s\n\nIt was empty.\n" % shape), shape)

    def test_a_well_formed_break_is_clean(self):
        got = checks("She stopped.\n\n* * *\n\nIt was empty.\n")
        self.assertFalse({c for _l, c in got} & {"scene-break", "markup"})

    def test_italics_and_bold_are_markup_but_arithmetic_and_snake_case_are_not(self):
        self.assertIn(("defect", "markup"), checks("She ran.\n\n*She would not make it.*\n"))
        self.assertIn(("defect", "markup"), checks("She ran.\n\n**She would not.**\n"))
        self.assertIn(("defect", "markup"), checks("She ran.\n\n_She would not._\n"))
        for body in ("The answer was 3 * 4 * 5.\n", "He read some_file_name aloud.\n"):
            self.assertNotIn(("defect", "markup"), checks(body), body)

    def test_intent_fields_in_a_chapter_file_are_flagged(self):
        got = found("Cold.\n", event="she finds the tally")
        self.assertTrue(any(c == "frontmatter" and "`event`" in d for _l, c, d in got))

    def test_a_meta_block_opening_the_chapter(self):
        self.assertIn(("warn", "meta"), checks("[ Notice — the bar is closed ]\n\nShe read it.\n"))


class ThoughtTest(unittest.TestCase):
    def test_a_tagged_thought_is_a_warning(self):
        self.assertIn(("warn", "thought-tag"), checks("'Not again,' she thought.\n"))

    def test_an_unclosed_thought_mark_is_a_defect(self):
        self.assertIn(("defect", "channel-collision"),
                      checks("'Start with what you are sure of and work outwards\n"))

    def test_narration_in_thought_marks_is_a_note(self):
        self.assertIn(("note", "thought-person"), checks("'The boat had been late again.'\n"))

    def test_the_count_is_a_note_never_a_budget(self):
        body = "\n\n".join("'Go now.'" for _ in range(6)) + "\n"
        levels = {lv for lv, c, _d in found(body) if c == "thoughts"}
        self.assertEqual(levels, {"note"})


class HouseStyleTest(unittest.TestCase):
    def test_house_style_shapes_are_notes_in_narration_only(self):
        body = ("It was weather, not prophecy. Not relief. Something smaller.\n\n"
                "\"It was weather, not prophecy,\" she said.\n")
        got = found(body)
        hits = [d for lv, c, d in got if c == "house-style" and "per 1,000" not in d]
        self.assertEqual(len(hits), 2, hits)
        self.assertEqual({lv for lv, c, _d in got if c == "house-style"}, {"note"})

    def test_stock_phrases_warn(self):
        self.assertIn(("warn", "stock"), checks("It was a testament to her patience.\n"))

    def test_echo(self):
        body = ("Close enough to sign. He said it. Close enough to sign, again. "
                "And once more: close enough to sign.\n")
        self.assertTrue(any(c == "echo" and "close enough to sign" in d
                            for _l, c, d in found(body)))


class NumbersAndLexiconTest(unittest.TestCase):
    def test_one_unit_counted_both_ways_in_the_same_range(self):
        got = found("It was 11 links off. Eleven links toward the gully.\n")
        self.assertTrue(any(lv == "warn" and c == "numerals" and "link" in d for lv, c, d in got))

    def test_words_under_twenty_and_digits_over_it_are_not_drift(self):
        got = found("Reading Day was two days off. The kit cost 45 days' wages.\n")
        self.assertFalse(any(lv == "warn" and c == "numerals" for lv, c, _d in got))

    def test_a_never_write_as_spelling_is_a_defect(self):
        got = found("Harbormaster Quell looked up. Nesa waited. Nessa Vane's hands were cold.\n")
        lex = [d for lv, c, d in got if c == "lexicon" and lv == "defect"]
        self.assertEqual(len(lex), 2, lex)

    def test_a_banned_word_warns(self):
        self.assertIn(("warn", "lexicon"), checks("It was her destiny to row.\n"))


class ReportTest(unittest.TestCase):
    def test_the_report_is_level_check_detail_and_never_gates(self):
        with NovelFixture() as fx:
            path = fx.chapter(1, "She ran.\n\n*She would not make it.*\n")
            out = os.path.join(fx.tmp, "lint.txt")
            buf = io.StringIO()
            with contextlib.redirect_stdout(buf):
                self.assertEqual(lint.main([path, "--out", out]), 0)
            lines = buf.getvalue().strip().splitlines()
            for line in lines[:-1]:
                self.assertRegex(line, r"^(defect|warn|note) [a-z-]+: ")
            self.assertRegex(lines[-1], r"^\d+ defect · \d+ warn · \d+ note$")
            with open(out, encoding="utf-8") as fh:
                self.assertEqual(fh.read(), buf.getvalue())

    def test_stats_name_who_speaks_in_each_scene(self):
        with NovelFixture() as fx:
            path = fx.chapter(1)
            buf = io.StringIO()
            with contextlib.redirect_stdout(buf):
                lint.main([path, "--stats"])
            self.assertIn("1) Nessa Vane, Tam Orrin", buf.getvalue())


if __name__ == "__main__":
    unittest.main()


class SlopTest(unittest.TestCase):
    """lib/slop.py: EQ-Bench's formula, (words + 2 bigrams + 8 trigrams) per 1,000 tokens."""

    def test_the_formula_weights_each_list(self):
        from lib import slop
        index, tokens, hits = slop.score("She took deep breath. He nodded. Absently.")
        # 7 tokens; nodded, absently (1 each); "took deep", "deep breath" (2 each); "took deep
        # breath" (8)
        self.assertEqual(tokens, 7)
        self.assertEqual(hits["took deep breath"], 1)
        self.assertAlmostEqual(index, (1 + 1 + 2 + 2 + 8) * 1000.0 / 7)

    def test_the_lists_are_vendored_whole(self):
        from lib import slop
        self.assertEqual([len(s) for s in slop.lists()], [1000, 200, 200])

    def test_the_report_carries_one_note(self):
        lines = [d for lv, check, d in found("He nodded. She nodded again, absently.\n")
                 if check == "slop"]
        self.assertEqual(len(lines), 1)
        self.assertIn("nodded 2", lines[0])
