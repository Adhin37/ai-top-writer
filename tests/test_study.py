"""tools/study.py - a genre study's intake, and the step its files say is next."""
import os
import shutil
import sys
import tempfile
import unittest
import zipfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "tools"))

import study  # noqa: E402

WORDS = " ".join(["The ferry ran late again and nobody on the quay said a word."] * 30)

RR_PAGE = """<html><head><title>Chapter 1 - The Quay | Royal Road</title>
<style>.cjk9Xa{display: none; speak: never;}</style></head><body>
<nav>Home Fictions</nav>
<h1>Chapter 1 - The Quay</h1>
<div class="portlet author-note-portlet"><div class="author-note"><p>Thanks for reading!</p></div></div>
<div class="chapter-inner chapter-content">
<p>%s</p>
<p class="cjk9Xa">A planted line the page hides.</p>
<p>Orlan waited.</p>
<table><tr><td>Strength</td><td>4</td></tr></table>
</div>
<div class="comments">Great chapter</div>
</body></html>""" % WORDS

WN_PAGE = """<html><body><h1 class="cha-tit">Chapter 2: Salt</h1>
<div class="cha-content"><div class="cha-words">
<p class="cha-paragraph"><span>%s</span><i class="para-comment">12</i></p>
<p class="cha-paragraph"><span>Vey nodded.</span></p>
</div></div></body></html>""" % WORDS

XHTML = """<?xml version="1.0" encoding="utf-8"?><html xmlns="http://www.w3.org/1999/xhtml">
<head><title>%s</title></head><body><h1>%s</h1><p>%s</p></body></html>"""


def epub(path, items):
    with zipfile.ZipFile(path, "w") as z:
        z.writestr("mimetype", "application/epub+zip")
        z.writestr("META-INF/container.xml",
                   '<?xml version="1.0"?><container xmlns="urn:oasis:names:tc:opendocument:xmlns:'
                   'container"><rootfiles><rootfile full-path="OEBPS/content.opf"/></rootfiles>'
                   '</container>')
        manifest = "".join('<item id="i%d" href="Text/%d.xhtml"/>' % (i, i)
                           for i in range(len(items)))
        spine = "".join('<itemref idref="i%d"/>' % i for i in range(len(items)))
        z.writestr("OEBPS/content.opf",
                   '<?xml version="1.0"?><package xmlns="http://www.idpf.org/2007/opf">'
                   '<manifest>%s</manifest><spine>%s</spine></package>' % (manifest, spine))
        for i, (title, body) in enumerate(items):
            z.writestr("OEBPS/Text/%d.xhtml" % i, XHTML % (title, title, body))


class StudyTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.study = os.path.join(self.tmp, "research", "tide")
        study.init(self.study, "tide", "2030-01-01")
        self.usage = os.path.join(self.tmp, "usage.json")   # absent: no pause

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def write(self, rel, text):
        path = os.path.join(self.study, rel)
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w", encoding="utf-8") as fh:
            fh.write(text)
        return path

    def books(self, rows, chapters=2):
        text = study.BOOKS_TEMPLATE.format(genre="tide", date="2030-01-01")
        text = text.replace("chapters: 10", "chapters: %d" % chapters)
        text = text.replace("doc: docs/", "doc: %s/docs/" % self.tmp)
        self.write("books.md", text + "".join(
            "| %s | rr | %d | Book %s |  | Sea |  | %s |  |\n" % (slug, i, slug, src)
            for i, (slug, src) in enumerate(rows, 1)))

    def step(self):
        return study.step(self.study, root="/", usage=self.usage)

    def test_a_royal_road_page_keeps_prose_and_notes_and_drops_the_planted_line(self):
        title, paras = study.html_prose(RR_PAGE)
        self.assertEqual(title, "Chapter 1 - The Quay")
        self.assertEqual(paras[0], "> [A/N] Thanks for reading!")
        self.assertIn("Orlan waited.", paras)
        self.assertIn("Strength | 4 |", paras)
        joined = "\n".join(paras)
        for gone in ("planted", "Home Fictions", "Great chapter"):
            self.assertNotIn(gone, joined)

    def test_a_webnovel_page_drops_the_paragraph_comment_counts(self):
        title, paras = study.html_prose(WN_PAGE)
        self.assertEqual(title, "Chapter 2: Salt")
        self.assertEqual(paras, [WORDS, "Vey nodded."])

    def test_intake_from_an_epub_skips_front_matter(self):
        epub(os.path.join(self.study, "inbox", "a.epub"),
             [("Information", "Source: somewhere. " * 5), ("Chapter 1", WORDS),
              ("Chapter 2", WORDS), ("Chapter 3", "Short.")])
        self.books([("a", "inbox/a.epub")])
        lines = study.intake(self.study)
        self.assertIn("a: front matter skipped: Information", lines)
        with open(os.path.join(self.study, "source", "a", "ch01.md"), encoding="utf-8") as fh:
            self.assertEqual(fh.read(), "# Chapter 1\n\n%s\n" % WORDS)
        self.assertTrue(os.path.isfile(os.path.join(self.study, "source", "a", "ch02.md")))
        self.assertFalse(os.path.exists(os.path.join(self.study, "source", "a", "ch03.md")))

    def test_intake_from_a_folder_of_pages_flags_a_stub_and_a_gap(self):
        self.write("inbox/b/chapter-10.html", WN_PAGE)
        self.write("inbox/b/chapter-9.html", RR_PAGE.replace(WORDS, "Locked."))
        self.books([("b", "inbox/b")], chapters=3)
        lines = study.intake(self.study)
        self.assertTrue(lines[0].startswith("b ch01") and "STUB?" in lines[0], lines)
        self.assertTrue(lines[1].startswith("b ch02") and "Chapter 2: Salt" in lines[1], lines)
        self.assertEqual(lines[2], "b: only 2 of 3 chapters in inbox/b")

    def test_intake_from_one_text_file(self):
        self.write("inbox/c.txt", "Chapter 1: Ebb\n\n%s\n\nChapter 2: Flood\n\nShe ran.\n" % WORDS)
        self.books([("c", "inbox/c.txt")])
        lines = study.intake(self.study)
        self.assertIn("Chapter 1: Ebb", lines[0])
        self.assertIn("Chapter 2: Flood", lines[1])

    def test_the_steps_in_order(self):
        with self.assertRaises(study.Stop) as cm:
            self.step()
        self.assertIn("S1", str(cm.exception))
        self.books([("a", "inbox/a"), ("b", "inbox/b")])
        with self.assertRaises(study.Stop) as cm:
            self.step()
        self.assertIn("S2", str(cm.exception))
        for i in (1, 2):
            self.write("source/a/ch%02d.md" % i, "# x\n")
        lines, sends, _then = self.step()            # a book without source waits; a is read
        self.assertEqual([h for h, _t in sends], ['@ spawn general-purpose · sonnet as "read a"'])
        self.assertIn("Waiting on source", lines[1])
        for slug in ("a", "b"):
            for i in (1, 2):
                self.write("source/%s/ch%02d.md" % (slug, i), "# x\n")
        self.write("notes/a/ch01.md", "notes")
        lines, sends, _then = self.step()
        self.assertIn("2 of 2 books", lines[0])
        self.assertEqual([h for h, _t in sends],
                         ['@ spawn general-purpose · sonnet as "read a ch02-02"',
                          '@ spawn general-purpose · sonnet as "read b"'])
        self.assertIn("notes for chapters 1-1 exist", sends[0][1])
        self.assertIn("Read all 2 chapters.", sends[1][1])
        for slug in ("a", "b"):
            for name in ("ch01.md", "ch02.md", "summary.md"):
                self.write("notes/%s/%s" % (slug, name), "notes")
        lines, sends, _then = self.step()
        self.assertIn("summary.md and names.txt", sends[0][1])
        for slug in ("a", "b"):
            self.write("notes/%s/names.txt" % slug, "Orlan Vey\n# a comment\n")
        lines, sends, _then = self.step()
        self.assertTrue(lines[0].startswith("S4"), lines)
        self.assertIn("general-purpose · opus", sends[0][0])
        doc = os.path.join(self.tmp, "docs", "experiments", "2030-01-01-tide-study.md")
        os.makedirs(os.path.dirname(doc))
        table = "| id | finding | scope | verdict |\n|---|---|---|---|\n| F1 | x | fanfic | %s |\n"
        with open(doc, "w", encoding="utf-8") as fh:
            fh.write("# Study\n\n## Proposals\n\n" + table % "")
        lines, sends, _then = self.step()
        self.assertTrue(lines[0].startswith("S5") and "F1" in lines[0], lines)
        self.assertEqual(sends, [])
        with open(doc, "w", encoding="utf-8") as fh:
            fh.write("# Study\n\n## Proposals\n\n" + table % "accept")
        lines, sends, _then = self.step()
        self.assertTrue(lines[0].startswith("S6"), lines)
        with open(doc, "a", encoding="utf-8") as fh:
            fh.write("\n## Applied\n\nF1: kb/planner/x.md\n")
        lines, sends, _then = self.step()
        self.assertTrue(lines[0].startswith("DONE"), lines)
        path, count = study.names(self.study)
        with open(path, encoding="utf-8") as fh:
            self.assertEqual(fh.read(), "# a\nOrlan Vey\n# b\n# titles\nBook a\nBook b\n")
        self.assertEqual(count, 3)

    def test_a_long_book_is_read_in_ranges(self):
        self.books([("a", "inbox/a")], chapters=4)
        for i, n in enumerate((40000, 15000, 30000, 5000), 1):
            self.write("source/a/ch%02d.md" % i, "word " * n)
        self.assertEqual(study.reading_range(self.study, "a", 1, 4), 2)
        self.assertEqual(study.reading_range(self.study, "a", 3, 4), 4)
        self.assertEqual(study.reading_range(self.study, "a", 1, 4, budget=1000), 1)
        _lines, sends, _then = self.step()
        self.assertEqual(sends[0][0], '@ spawn general-purpose · sonnet as "read a ch01-02"')
        self.assertIn("Stop after chapter 2's notes", sends[0][1])
        self.assertIn("`READ a ch01-02`", sends[0][1])
        for i in (1, 2):
            self.write("notes/a/ch%02d.md" % i, "notes")
        _lines, sends, _then = self.step()
        self.assertIn("chapters 3 to 4", sends[0][1])
        self.assertNotIn("Stop after", sends[0][1])

    def test_status(self):
        self.books([("a", "inbox/a")])
        self.write("source/a/ch01.md", "# x\n")
        self.assertEqual(study.status(self.study)[1].split()[:3], ["a", "rr", "1/2"])


if __name__ == "__main__":
    unittest.main()
