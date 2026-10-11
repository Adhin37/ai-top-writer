"""tools/canon_fetch.py - a fan wiki's rendered page as text, and refusals reported, offline.

The wiki is invented: a mage academy on a volcano's flank.
"""
import contextlib
import io
import json
import os
import re
import shutil
import sys
import tempfile
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "tools"))

import canon_fetch  # noqa: E402

PAGE = """<div class="mw-parser-output">
<aside class="portable-infobox pi-theme-character">
<h2 class="pi-item pi-title" data-source="name">Corin Dask</h2>
<figure class="pi-item pi-image"><img src="x.png"/></figure>
<section class="pi-item pi-group"><h2 class="pi-item pi-header">Description</h2>
<div class="pi-item pi-data" data-source="age"><h3 class="pi-data-label">Age</h3>
<div class="pi-data-value">15 (Volume 1)<br/>16 (Volume 2)</div></div>
<div class="pi-item pi-data" data-source="status"><h3 class="pi-data-label">Status</h3>
<div class="pi-data-value">Alive<sup class="reference"><a href="#cite-1">[1]</a></sup></div></div>
</section></aside>
<p><b>Corin Dask</b> is a second-year student at <a href="/wiki/Ashfall">Ashfall Academy</a>.<sup class="reference">[2]</sup></p>
<h2><span class="mw-headline">History</span><span class="mw-editsection">[edit]</span></h2>
<h3>Early life</h3>
<p>He entered the academy &amp; ranked last of his intake.</p>
<ul><li>Roommate: Tam Rook</li><li>Sponsor: Ilse Maro</li></ul>
<table class="wikitable"><tr><th>Year</th><th>Rank</th></tr><tr><td>1</td><td>58th</td></tr></table>
<table class="navbox"><tr><td>Students · Teachers · Places</td></tr></table>
<div class="mw-references-wrap"><ol class="references"><li>Chapter 3</li></ol></div>
</div>"""

CLASSIC = """<table class="infobox"><tr><th colspan="2">Ilse Maro</th></tr>
<tr><th>Title</th><td>Headmistress</td></tr><tr><th>Ward</th><td>the academy</td></tr></table>
<p>The headmistress.</p>"""

TRANSCRIPT = """<div class="mw-parser-output">
<p>The episode opens on the academy's crater rim at dawn.</p>
<table><tr><th>Corin</th><td>[Panting.] Last again.</td></tr>
<tr><th>Tam</th><td>Last is still on the rim.</td></tr></table>
<p>The scene changes to the headmistress's study, lit by lava glow.</p>
<table><tr><th>Ilse</th><td>Send for the Dask boy.</td></tr></table>
<p>Cut to the dormitory. The scene shifts to the night before the trial.</p>
<table><tr><th>Corin</th><td>I won't sleep.</td></tr><tr><th>Tam</th><td>Then I won't either.</td></tr>
<tr><th>Corin</th><td>Fine.</td></tr></table>
<h2>Cast</h2><ul><li>Corin Dask</li></ul>
</div>"""


class TranscriptTest(unittest.TestCase):
    def render(self):
        return canon_fetch.render("Transcript:The Trial", "u", TRANSCRIPT,
                                  ["Ashfall episode transcripts"], "d")[0]

    def test_a_scene_heading_at_each_scene_change(self):
        lines = self.render().split("\n")
        scenes = [l for l in lines if l.startswith("## Scene ")]
        self.assertEqual(scenes, ["## Scene 1 — Corin, Tam", "## Scene 2 — Ilse",
                                  "## Scene 3 — Corin, Tam"])
        self.assertLess(lines.index("categories: Ashfall episode transcripts"),
                        lines.index(scenes[0]))
        self.assertEqual(lines[lines.index(scenes[1]) + 2],
                         "The scene changes to the headmistress's study, lit by lava glow.")
        self.assertIn("## Cast", lines)
        self.assertGreater(lines.index("## Cast"), lines.index(scenes[2]))

    def test_a_long_scene_breaks_at_a_cut(self):
        text = "# Transcript:X\n\nsource: u\n\nA rim.\nCorin | Go.\nCut to the vent.\nTam | Hot.\n"
        self.assertEqual(canon_fetch.add_scenes(text).count("## Scene "), 1)
        saved, canon_fetch.SCENE_CHARS = canon_fetch.SCENE_CHARS, 10
        try:
            self.assertIn("## Scene 2 — Tam\n\nCut to the vent.", canon_fetch.add_scenes(text))
        finally:
            canon_fetch.SCENE_CHARS = saved

    def test_an_article_gets_no_scenes(self):
        text, _box = canon_fetch.render("Corin Dask", "u", PAGE.replace(
            "Early life", "Early life, a transcription error"), ["Characters"], "d")
        self.assertNotIn("## Scene", text)

    def test_restyle_adds_scenes_to_a_saved_page_once(self):
        tmp = tempfile.mkdtemp(prefix="atw-canon-")
        try:
            plain = self.render()
            plain = "\n".join(l for l in plain.split("\n") if not l.startswith("## Scene "))
            with open(os.path.join(tmp, "Transcript_The_Trial.md"), "w", encoding="utf-8") as fh:
                fh.write(plain)
            done = canon_fetch.restyle(tmp)
            self.assertEqual([n for _f, n in done], [3])
            with open(os.path.join(tmp, "Transcript_The_Trial.md"), encoding="utf-8") as fh:
                self.assertEqual(fh.read(), self.render())
            self.assertEqual(canon_fetch.restyle(tmp), [])
        finally:
            shutil.rmtree(tmp, ignore_errors=True)


class ReadingTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp(prefix="atw-canon-")
        self.page = os.path.join(self.tmp, "Corin_Dask.md")
        with open(self.page, "w", encoding="utf-8") as fh:
            fh.write(canon_fetch.render("Corin Dask", "u", PAGE, ["Characters"], "d")[0])
        with open(os.path.join(self.tmp, "Trial.md"), "w", encoding="utf-8") as fh:
            fh.write(canon_fetch.render("Transcript:The Trial", "u", TRANSCRIPT,
                                        ["Ashfall episode transcripts"], "d")[0])

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def test_toc_gives_line_ranges_a_read_can_use(self):
        rows = canon_fetch.toc(self.page)
        with open(self.page, encoding="utf-8") as fh:
            lines = fh.read().split("\n")
        history = next(r for r in rows if r.endswith("## History"))
        first, last = (int(n) for n in history.split()[0].split("-"))
        self.assertEqual(lines[first - 1], "## History")
        self.assertEqual(lines[last - 1], "1 | 58th")
        self.assertTrue(any(r.endswith("### Early life") for r in rows))

    def test_grep_finds_paragraphs_under_their_heading(self):
        rows, extra, _files = canon_fetch.grep(self.tmp, ["intake", "academy"])
        self.assertEqual(extra, 0)
        self.assertIn("   [### Early life]", rows)
        self.assertTrue(any(r.endswith(": He entered the academy & ranked last of his intake.")
                            for r in rows))

    def test_grep_caps_and_counts_the_rest(self):
        rows, extra, files = canon_fetch.grep(self.tmp, ["Corin"], limit=2)
        self.assertEqual(sum(1 for r in rows if r.startswith("   [")), 2)
        self.assertGreater(extra, 0)
        self.assertGreaterEqual(files, 1)

    def test_grep_cuts_a_long_paragraph_around_the_match(self):
        text = "a" * 50 + " Zhao " + "b" * 50
        cut = canon_fetch.clip(text, re.compile("Zhao"), 30)
        self.assertIn("Zhao", cut)
        self.assertTrue(cut.startswith("…") and cut.endswith("…"))
        self.assertEqual(len(cut), 32)


class Response(io.BytesIO):
    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False


def opener(body):
    def fake(req, timeout=None):
        fake.urls.append(req.full_url)
        return Response(body.encode("utf-8"))
    fake.urls = []
    return fake


class RenderTest(unittest.TestCase):
    def test_portable_infobox_and_body(self):
        text, box = canon_fetch.render("Corin Dask", "https://w/wiki/Corin_Dask", PAGE,
                                       ["Characters"], "2026-01-01")
        self.assertEqual(box, 4)
        for line in ("source: https://w/wiki/Corin_Dask", "categories: Characters",
                     "name: Corin Dask", "### Description", "Age: 15 (Volume 1); 16 (Volume 2)",
                     "Status: Alive", "## History", "### Early life",
                     "He entered the academy & ranked last of his intake.",
                     "- Roommate: Tam Rook", "Year | Rank", "1 | 58th"):
            self.assertIn(line, text.split("\n"), line)
        for gone in ("[1]", "[2]", "[edit]", "Students · Teachers", "Chapter 3", "x.png"):
            self.assertNotIn(gone, text, gone)
        self.assertLess(text.index("Status: Alive"), text.index("Corin Dask is a second-year"))

    def test_a_classic_infobox_table(self):
        text, box = canon_fetch.render("Ilse Maro", "u", CLASSIC, [], "d")
        self.assertIn("Title: Headmistress", text)
        self.assertIn("Ward: the academy", text)
        self.assertIn("The headmistress.", text)
        self.assertEqual(box, 3)


class ApiTest(unittest.TestCase):
    def setUp(self):
        self._robots = canon_fetch.robots_allows
        self._pause = canon_fetch.PAUSE
        canon_fetch.robots_allows = lambda api: True
        canon_fetch.PAUSE = 0

    def tearDown(self):
        canon_fetch.robots_allows = self._robots
        canon_fetch.PAUSE = self._pause

    def test_api_urls(self):
        self.assertEqual(canon_fetch.api_url("ashfall.fandom.com"),
                         "https://ashfall.fandom.com/api.php")
        self.assertEqual(canon_fetch.api_url("en.wikipedia.org"),
                         "https://en.wikipedia.org/w/api.php")
        self.assertEqual(canon_fetch.page_url("https://ashfall.fandom.com/api.php", "Corin Dask"),
                         "https://ashfall.fandom.com/wiki/Corin_Dask")

    def test_parse_follows_the_api_and_names_itself(self):
        fake = opener(json.dumps({"parse": {"title": "Corin Dask", "text": PAGE, "categories": [
            {"category": "Characters"}, {"category": "Stubs", "hidden": True}]}}))
        title, html, cats = canon_fetch.parse("https://w/api.php", "Corin", fake)
        self.assertEqual((title, cats), ("Corin Dask", ["Characters"]))
        self.assertIn("action=parse", fake.urls[0])
        self.assertIn("redirects=1", fake.urls[0])

    def test_a_challenge_page_is_a_refusal(self):
        with self.assertRaises(canon_fetch.Refused):
            canon_fetch.get("https://w/api.php", {"action": "query"},
                            opener("<html><title>Just a moment...</title></html>"))

    def test_a_missing_page(self):
        fake = opener(json.dumps({"error": {"code": "missingtitle",
                                            "info": "The page you specified doesn't exist."}}))
        with self.assertRaises(KeyError):
            canon_fetch.parse("https://w/api.php", "Nobody", fake)

    def test_robots_refusal_is_reported_blocked(self):
        canon_fetch.robots_allows = lambda api: False
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            code = canon_fetch.main(["search", "w.example", "Corin"])
        self.assertEqual(code, 3)
        self.assertTrue(out.getvalue().startswith("blocked "))

    def test_a_cached_page_is_not_fetched_again(self):
        tmp = tempfile.mkdtemp(prefix="atw-canon-")
        try:
            with open(os.path.join(tmp, "Corin_Dask.md"), "w", encoding="utf-8") as fh:
                fh.write("# Corin Dask\n")
            canon_fetch.robots_allows = lambda api: self.fail("fetched a cached page")
            out = io.StringIO()
            with contextlib.redirect_stdout(out):
                code = canon_fetch.main(["page", "w.example", "Corin_Dask", "--out", tmp])
            self.assertEqual(code, 0)
            self.assertIn("cached Corin Dask", out.getvalue())
        finally:
            shutil.rmtree(tmp, ignore_errors=True)

    def test_titles_decode_underscores_and_brackets(self):
        self.assertEqual(canon_fetch.arg("Ilse_Maro_%28novel%29"), "Ilse Maro (novel)")
        self.assertEqual(canon_fetch.safe_name("Ilse Maro (novel)"), "Ilse_Maro_novel.md")


if __name__ == "__main__":
    unittest.main()
