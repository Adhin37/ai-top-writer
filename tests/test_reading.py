"""tools/reading.py - the reader's shelf, the per-round view, and memory from the accepted round only."""
import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from novel_fixture import NovelFixture  # noqa: E402
import export_prose  # noqa: E402
import reading  # noqa: E402


def read(path):
    with open(path, encoding="utf-8") as fh:
        return fh.read()


class ShelfTest(unittest.TestCase):
    def setUp(self):
        self.fx = NovelFixture().__enter__()
        self.shelf = reading.shelf(self.fx.root, self.fx.tmp)
        os.makedirs(self.shelf)
        for n in (1, 2, 3):
            with open(os.path.join(self.shelf, "ch%02d.md" % n), "w", encoding="utf-8") as fh:
                fh.write("# Chapter %d\n\nText.\n" % n)
        with open(os.path.join(self.shelf, "notes.md"), "w", encoding="utf-8") as fh:
            fh.write("The running notes.\n")

    def tearDown(self):
        self.fx.__exit__(None, None, None)

    def test_the_novels_folder_is_named_by_the_neutral_id_and_holds_the_shelf(self):
        self.assertEqual(os.path.basename(reading.folder(self.fx.root, self.fx.tmp)),
                         export_prose.novel_id(self.fx.root))
        self.assertEqual(os.path.dirname(self.shelf), reading.folder(self.fx.root, self.fx.tmp))

    def test_a_round_holds_the_notes_the_last_two_chapters_and_the_draft(self):
        draft = self.fx.write("work/ch0004/draft-r0.md",
                              "---\nnumber: 4\ntitle: \"Four\"\npov: \"N\"\n---\n\nDraft.\n")
        folder = reading.build_round(self.fx.root, 4, draft, 0, self.fx.tmp)
        self.assertEqual(folder, os.path.join(reading.folder(self.fx.root, self.fx.tmp), "ch04-r0"))
        files = sorted(os.path.relpath(os.path.join(d, f), folder)
                       for d, _s, fs in os.walk(folder) for f in fs)
        self.assertEqual(files, ["ch02.md", "ch03.md", "notes.md", os.path.join("pending",
                                                                               "ch04.md")])
        self.assertNotIn("number:", read(os.path.join(folder, "pending", "ch04.md")))

    def test_a_rebuilt_round_forgets_what_an_earlier_build_left(self):
        draft = self.fx.write("work/ch0004/draft-r1.md", "Draft.\n")
        folder = reading.build_round(self.fx.root, 4, draft, 1, self.fx.tmp)
        with open(os.path.join(folder, "report.md"), "w", encoding="utf-8") as fh:
            fh.write("an old report")
        reading.build_round(self.fx.root, 4, draft, 1, self.fx.tmp)
        self.assertFalse(os.path.exists(os.path.join(folder, "report.md")))

    def test_accept_copies_the_rounds_notes_byte_for_byte_and_shelves_the_chapter(self):
        self.fx.chapter(4, "The accepted text.\n", title="Four")
        rnd = os.path.join(self.fx.tmp, "reading", "round")
        os.makedirs(rnd)
        with open(os.path.join(rnd, "notes.md"), "w", encoding="utf-8") as fh:
            fh.write("The accepted round's notes, with “curly” marks.\n")
        out = reading.accept(self.fx.root, 4, rnd, self.fx.tmp)
        self.assertEqual(read(os.path.join(self.shelf, "notes.md")),
                         "The accepted round's notes, with “curly” marks.\n")
        self.assertEqual(read(os.path.join(self.shelf, "ch04.md")),
                         "# Four\n\nThe accepted text.\n")
        self.assertTrue(any("7 words" in line for line in out), out)

    def test_accept_names_notes_over_the_cap_and_the_tenth_chapter(self):
        self.fx.chapter(10, "Ten.\n")
        rnd = os.path.join(self.fx.tmp, "reading", "round")
        os.makedirs(rnd)
        with open(os.path.join(rnd, "notes.md"), "w", encoding="utf-8") as fh:
            fh.write("word " * 801)
        out = reading.accept(self.fx.root, 10, rnd, self.fx.tmp)
        self.assertTrue(any("over 800" in line for line in out), out)
        self.assertTrue(any("fresh reader re-reads ch01–ch10" in line for line in out), out)

    def test_fresh_has_every_chapter_and_no_notes_and_adopt_replaces_the_notes(self):
        folder = reading.build_fresh(self.fx.root, 3, self.fx.tmp)
        self.assertEqual(sorted(os.listdir(folder)), ["ch01.md", "ch02.md", "ch03.md"])
        with open(os.path.join(folder, "notes.md"), "w", encoding="utf-8") as fh:
            fh.write("Fresh notes.\n")
        reading.adopt(self.fx.root, folder, self.fx.tmp)
        self.assertEqual(read(os.path.join(self.shelf, "notes.md")), "Fresh notes.\n")


if __name__ == "__main__":
    unittest.main()
