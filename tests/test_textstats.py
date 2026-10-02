"""tools/lib/textstats.py - the four channels, scenes, sentences, echoes.

Every channel case here was a real miscount in skilled-writer's first parser; adapted from its
tests/test_channels.py.
"""
import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from novel_fixture import NovelFixture  # noqa: E402
from lib.textstats import Channels, Chapter, find_speech_spans  # noqa: E402

C = Channels()

MULTI_PARAGRAPH_SPEECH = '''"I was there when the levee went," she said.

"We waited three days for the water to drop. Nobody came up the road, and nobody was going to,
because the road was under eleven feet of it.

"By the fourth day we walked out over the fields."

The rain had not stopped since.
'''


def spans(text, channels=C):
    return [text[s:e] for s, e in find_speech_spans(text, channels)]


def chapter(body, novel_md=None):
    return Chapter("0001-x.md", text="---\nnumber: 1\ntitle: \"X\"\npov: \"N\"\n---\n\n" + body)


class SpeechTest(unittest.TestCase):
    def test_speech_over_several_paragraphs_is_all_speech(self):
        found = spans(MULTI_PARAGRAPH_SPEECH)
        self.assertEqual(len(found), 3)
        self.assertIn("By the fourth day", found[2])
        ch = chapter(MULTI_PARAGRAPH_SPEECH)
        self.assertGreater(ch.speech_share, 60.0)

    def test_an_unclosed_quote_stops_at_its_paragraph(self):
        text = '"Go, she said.\n\nThe room was cold.\n\n"Now."\n'
        for span in spans(text):
            self.assertNotIn("The room was cold", span)

    def test_curly_and_mixed_marks(self):
        for text in ("“Go on,” she said.", '"Go on," she said.', '“Go on," she said.'):
            self.assertEqual(len(spans(text)), 1, text)

    def test_a_stray_closing_mark_opens_nothing(self):
        self.assertEqual(spans("She left.” The door shut."), [])


class ThoughtTest(unittest.TestCase):
    def test_straight_and_curly_thoughts(self):
        self.assertEqual(len(C.thought_re.findall("'Start with what you're sure of.'")), 1)
        self.assertEqual(len(C.thought_re.findall("‘Start with what you’re sure of.’")), 1)

    def test_contractions_and_possessives_are_not_thoughts(self):
        self.assertEqual(C.thought_re.findall("She didn't move. The boys' room was empty."), [])

    def test_a_thought_inside_speech_is_a_nested_quotation(self):
        ch = chapter('"He said \'no\' twice," she told him.\n')
        self.assertEqual(ch.thoughts(), [])
        self.assertEqual(ch.nested_thought_in_speech(), 1)

    def test_elisions_are_words_and_an_open_mark_is_reported(self):
        self.assertEqual(chapter("'twas nothing.\n\nShe grabbed 'em and ran.\n\nIn '99 it was "
                                 "cold.\n").unterminated_thoughts(), [])
        self.assertEqual(len(chapter("'Start with what you are sure of and work outwards\n")
                             .unterminated_thoughts()), 1)

    def test_the_marks_come_from_the_config(self):
        ch = Chapter("0001-x.md", channels=Channels(thought="«…»"),
                     text="«Start with what you are sure of.»\n\n'Not a thought now.'\n")
        self.assertEqual(len(ch.thoughts()), 1)


class StructureTest(unittest.TestCase):
    BODY = ("One. Two three.\n\n\"Four,\" Nessa said.\n\n* * *\n\nFive six seven.\n\n"
            "\"Eight,\" Quell said. \"Nine.\"\n")

    def test_scenes_and_words(self):
        ch = chapter(self.BODY)
        self.assertEqual(ch.scene_breaks(), 1)
        self.assertEqual(ch.section_words(), [6, 7])
        self.assertEqual(ch.words, len(self.BODY.split()))

    def test_line_numbers_count_the_frontmatter(self):
        ch = chapter(self.BODY)
        self.assertEqual(ch.line_of(ch.body.index("Five")), 6 + 7)

    def test_speakers_by_scene(self):
        ch = chapter(self.BODY)
        self.assertEqual(ch.scene_speakers(["Nessa Vane", "Harbourmaster Quell"]),
                         [{"Nessa Vane"}, {"Harbourmaster Quell"}])

    def test_sentences_and_narration(self):
        ch = chapter('She waited. "Go," he said. It rained.\n')
        self.assertEqual([s for _o, s in ch.narration_sentences()], ["She waited.", "It rained."])


class EchoTest(unittest.TestCase):
    def test_an_echoed_phrase_is_found_without_a_list(self):
        body = ("It was its own kind of question. It was its own kind of answer. "
                "It was its own kind of kindness, and its own kind of worry.\n")
        found = dict(chapter(body).echoed_phrases(4, 3))
        self.assertEqual(found.get("its own kind of"), 4)

    def test_overlapping_windows_report_once(self):
        body = ("It was its own kind of question. It was its own kind of answer. "
                "It was its own kind of kindness.\n")
        self.assertEqual(len(chapter(body).echoed_phrases(4, 3)), 1)

    def test_ordinary_prose_echoes_nothing(self):
        body = "She counted the sacks. The quarter closed on Tuesday and nobody came.\n"
        self.assertEqual(chapter(body).echoed_phrases(4, 3), [])


class LoadTest(unittest.TestCase):
    def test_chapters_load_in_order_with_numbers(self):
        with NovelFixture() as fx:
            fx.chapter(2)
            fx.chapter(1)
            nums = [c.number for c in fx.novel().chapters()]
            self.assertEqual(nums, [1, 2])


if __name__ == "__main__":
    unittest.main()
