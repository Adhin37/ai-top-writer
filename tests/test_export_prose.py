"""tools/export_prose.py - readers get prose, never a chapter file."""
import hashlib
import os
import sys
import tempfile
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "tools"))

import export_prose  # noqa: E402

CHAPTER = """---
number: 3
title: "The Last Marker"
pov: "Someone"
event: "the intent a reader must never see"
delivers: "the reader understands the thing"
---

<!-- author note: land the premise here -->
The first line of prose.

The second paragraph.
"""


def write(path, text):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as fh:
        fh.write(text)


class ExportTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.dir = self.tmp.name

    def tearDown(self):
        self.tmp.cleanup()

    def read(self, path):
        with open(path, encoding="utf-8") as fh:
            return fh.read()

    def test_strips_frontmatter_and_comments_keeps_title(self):
        src = os.path.join(self.dir, "novels/x/chapters/0003-the-last-marker.md")
        write(src, CHAPTER)
        out = export_prose.export([src], os.path.join(self.dir, "reading/r1"))
        self.assertEqual([os.path.basename(o) for o in out], ["ch03.md"])
        text = self.read(out[0])
        self.assertTrue(text.startswith("# The Last Marker\n\nThe first line of prose."))
        for leak in ("event", "delivers", "intent", "author note", "---", "pov"):
            self.assertNotIn(leak, text)

    def test_a_trailing_comment_is_not_the_title(self):
        for line, want in (('title: "Feed Day"  # working', "Feed Day"), ("title: Feed # Day", "Feed"),
                           ('title: "A # B"', "A # B"), ("title: plain", "plain")):
            fields, _ = export_prose.split_frontmatter("---\n%s\n---\nx" % line)
            self.assertEqual(fields["title"], want, line)

    def test_no_title(self):
        src = os.path.join(self.dir, "a.md")
        write(src, CHAPTER)
        out = export_prose.export([src], os.path.join(self.dir, "r"), keep_title=False)
        self.assertTrue(self.read(out[0]).startswith("The first line of prose."))

    def test_number_from_filename_then_counter(self):
        write(os.path.join(self.dir, "c/0007-x.md"), "Prose seven.\n")
        write(os.path.join(self.dir, "A.md"), "Arm A.\n")
        out = export_prose.export([os.path.join(self.dir, "c/0007-x.md")], os.path.join(self.dir, "r1"))
        self.assertEqual(os.path.basename(out[0]), "ch07.md")
        out = export_prose.export([os.path.join(self.dir, "A.md")], os.path.join(self.dir, "r2"), start=1)
        self.assertEqual(os.path.basename(out[0]), "ch01.md")

    def test_directory_in_order_skipping_underscore(self):
        chapters = os.path.join(self.dir, "chapters")
        write(os.path.join(chapters, "0002-b.md"), "B.\n")
        write(os.path.join(chapters, "0001-a.md"), "A.\n")
        write(os.path.join(chapters, "_chapter-template.md"), "template\n")
        out = export_prose.export([chapters], os.path.join(self.dir, "reading/r"))
        self.assertEqual([os.path.basename(o) for o in out], ["ch01.md", "ch02.md"])

    def test_as_name(self):
        src = os.path.join(self.dir, "C1.md")
        write(src, CHAPTER)
        out = export_prose.export([src], os.path.join(self.dir, "bench/e/blind"), as_name="Q")
        self.assertEqual(os.path.basename(out[0]), "Q.md")
        with self.assertRaises(ValueError):
            export_prose.export([src, src], os.path.join(self.dir, "b"), as_name="Q")

    def test_refuses_to_export_into_a_novel(self):
        src = os.path.join(self.dir, "a.md")
        write(src, CHAPTER)
        with self.assertRaises(ValueError):
            export_prose.export([src], os.path.join(self.dir, "novels/x/reading"))

    def test_print_id_is_neutral_and_stable(self):
        novel = os.path.join(self.dir, "novels/unwritten-surveyor")
        os.makedirs(novel)
        expected = "r" + hashlib.sha1(b"unwritten-surveyor").hexdigest()[:6]
        self.assertEqual(export_prose.novel_id(novel), expected)
        write(os.path.join(novel, "novel.md"), '---\ntitle: "T"\nslug: "other-slug"\n---\n')
        self.assertEqual(export_prose.novel_id(novel),
                         "r" + hashlib.sha1(b"other-slug").hexdigest()[:6])
        self.assertNotIn("surveyor", export_prose.novel_id(novel))

    def test_frontmatter_parser(self):
        fields, body = export_prose.split_frontmatter('---\na: "x: y"\nb: 2\n  nested: no\n---\nBody\n')
        self.assertEqual(fields, {"a": "x: y", "b": "2"})
        self.assertEqual(body, "Body\n")
        self.assertEqual(export_prose.split_frontmatter("No frontmatter\n"), ({}, "No frontmatter\n"))


if __name__ == "__main__":
    unittest.main()
