"""tools/clean.py - what each novel left outside novels/."""
import contextlib
import io
import os
import shutil
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                                "tools"))

import clean  # noqa: E402
import export_prose  # noqa: E402


class CleanTest(unittest.TestCase):
    def setUp(self):
        self.root = tempfile.mkdtemp()
        for name in ("tide", "tide--vt-a", "ash", "_template"):
            self.mk("novels", name)
        self.tide = export_prose.novel_id(self.p("novels", "tide"))
        self.copy = export_prose.novel_id(self.p("novels", "tide--vt-a"))
        for rid in (self.tide, self.copy, "r000000"):
            self.mk("reading", rid, "shelf")
        self.write("bench/vt/key.md", "| a | bench/vt/blind/x | A | B | A=novels/tide--vt-a/c.md |")
        self.write("bench/both/notes.txt", "novels/tide/chapters and novels/ash/chapters")
        self.write("bench/cal/key.md", "no novel here")
        self.write("bench/dot/key.md", "Arms of novels/tide, compared with novels/ash.")
        self.write("bench/csv/key.md", "novels/tide/chapters")
        self.write("bench/csv/rows.csv", "arm,novel\nb,novels/ash/bible\n")

    def tearDown(self):
        shutil.rmtree(self.root)

    def p(self, *parts):
        return os.path.join(self.root, *parts)

    def mk(self, *parts):
        os.makedirs(self.p(*parts))

    def write(self, rel, text):
        os.makedirs(os.path.dirname(self.p(rel)), exist_ok=True)
        with open(self.p(rel), "w", encoding="utf-8") as fh:
            fh.write(text)

    def test_the_survey_names_each_folders_novel_or_none(self):
        got = dict(clean.survey(self.root))
        self.assertEqual(got["reading/%s" % self.tide], ["tide"])
        self.assertEqual(got["reading/%s" % self.copy], ["tide--vt-a"])
        self.assertEqual(got["reading/r000000"], [])
        self.assertEqual(got["bench/vt"], ["tide"])
        self.assertEqual(got["bench/both"], ["ash", "tide"])
        self.assertEqual(got["bench/cal"], [])
        self.assertEqual(got["bench/dot"], ["ash", "tide"])     # a slug before a full stop
        self.assertEqual(got["bench/csv"], ["ash", "tide"])     # any text file, not just .md

    def test_a_novel_owns_its_copies_their_reading_and_its_own_bench(self):
        paths, shared = clean.owned("tide", self.root)
        self.assertEqual(sorted(paths), sorted([
            "novels/tide", "novels/tide--vt-a", "reading/%s" % self.tide,
            "reading/%s" % self.copy, "bench/vt"]))
        self.assertEqual(sorted(shared), ["bench/both", "bench/csv", "bench/dot"])

    def test_delete_removes_only_what_the_novel_owns(self):
        with contextlib.redirect_stdout(io.StringIO()):
            clean.main(["tide", "--delete", "--root", self.root])
        self.assertFalse(os.path.exists(self.p("novels", "tide--vt-a")))
        self.assertFalse(os.path.exists(self.p("reading", self.tide)))
        self.assertFalse(os.path.exists(self.p("bench", "vt")))
        for kept in (("novels", "ash"), ("bench", "both"), ("reading", "r000000")):
            self.assertTrue(os.path.exists(self.p(*kept)), kept)


if __name__ == "__main__":
    unittest.main()
