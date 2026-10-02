"""tools/lib/mdio.py - frontmatter, the small YAML reader, pipe tables, sections.

Everything downstream reads config through here, so a silent parse failure does not look like a
parse failure. It looks like a novel with no protagonist. Adapted from skilled-writer's
tests/test_mdio.py.
"""
import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from novel_fixture import NOVEL_MD, NovelFixture  # noqa: E402
from lib import mdio  # noqa: E402


class ReadTextTest(unittest.TestCase):
    def test_a_bom_does_not_hide_the_frontmatter(self):
        with NovelFixture() as fx:
            path = fx.write("chapters/0001-x.md", "---\nnumber: 1\n---\n\nCold.\n", bom=True)
            fm, body = mdio.frontmatter(mdio.read_text(path))
            self.assertEqual(fm.get("number"), 1)
            self.assertEqual(body.strip(), "Cold.")

    def test_crlf_is_normalised(self):
        with NovelFixture() as fx:
            path = fx.write("chapters/0001-x.md", "---\nnumber: 1\n---\n\nCold.\n", newline="\r\n")
            text = mdio.read_text(path)
            self.assertNotIn("\r", text)
            self.assertEqual(mdio.frontmatter(text)[0]["number"], 1)

    def test_a_missing_file_reads_empty(self):
        self.assertEqual(mdio.read_text(os.path.join("no", "such", "file.md")), "")


class YamlTest(unittest.TestCase):
    def test_tabs_keep_their_nesting(self):
        cfg = mdio.parse_yaml("mc:\n\tname: Nessa\n\tintel: 4\n")
        self.assertEqual(mdio.dig(cfg, "mc.name"), "Nessa")
        self.assertEqual(mdio.dig(cfg, "mc.intel"), 4)

    def test_an_unclosed_quote_does_not_eat_the_next_key(self):
        cfg = mdio.parse_yaml('voice: "never closes\nnumber: 7\nstatus: drafted\n')
        self.assertEqual(cfg.get("number"), 7)
        self.assertEqual(cfg.get("status"), "drafted")

    def test_a_quoted_scalar_over_several_lines_joins(self):
        cfg = mdio.parse_yaml('note: "short bursts,\n  clipped and factual"\n')
        self.assertIn("clipped and factual", cfg["note"])

    def test_a_hash_after_whitespace_is_a_comment(self):
        self.assertEqual(mdio.parse_yaml("title: Book #2\n")["title"], "Book")
        self.assertEqual(mdio.parse_yaml('title: "Book #2"\n')["title"], "Book #2")

    def test_scalars_and_lists(self):
        cfg = mdio.parse_yaml("a: true\nb: null\nc: 1.5\nd: [x, \"y, z\"]\ne:\n  - one\n  - two\n"
                              "f: on\n")
        self.assertEqual((cfg["a"], cfg["b"], cfg["c"]), (True, None, 1.5))
        self.assertEqual(cfg["d"], ["x", "y, z"])
        self.assertEqual(cfg["e"], ["one", "two"])
        self.assertEqual(cfg["f"], "on")

    def test_a_map_inside_a_list_item_neither_raises_nor_leaks(self):
        fm = ("name: reader\nhooks:\n  PreToolUse:\n    - matcher: \"Read\"\n      hooks:\n"
              "        - type: command\nomitClaudeMd: true\n")
        cfg = mdio.parse_yaml(fm)
        self.assertIs(cfg.get("omitClaudeMd"), True)
        for leaked in ("matcher", "type"):
            self.assertNotIn(leaked, cfg)

    def test_the_fixture_novel_and_the_real_channels_parse(self):
        cfg = mdio.frontmatter(NOVEL_MD)[0]
        self.assertEqual(mdio.dig(cfg, "mc.name"), "Nessa Vane")
        self.assertEqual(mdio.dig(cfg, "channels.thought"), "'…'")
        self.assertEqual(mdio.dig(cfg, "channels.speech"), '"…"')


class TablesTest(unittest.TestCase):
    TEXT = ("# Top\n\n## Facts\n| id | fact | due by ch |\n|---|---|---|\n| P1 | a \\| b | 1 |\n"
            "| P2 | c | 2 |\n\n## Other\n| x | y |\n|:--|--:|\n| 1 | 2 |\n")

    def test_tables_rows_and_headings(self):
        tables = mdio.parse_tables(self.TEXT)
        self.assertEqual(len(tables), 2)
        self.assertEqual(tables[0].heading, "Facts")
        self.assertEqual(tables[0].rows[0].get("Due by ch"), "1")
        self.assertEqual(tables[0].rows[0].get("fact"), "a \\| b")
        self.assertEqual(tables[0].rows[1].line_no, 7)

    def test_a_table_is_found_by_its_columns(self):
        self.assertEqual(mdio.table_with(self.TEXT, "x", "y").rows[0].first(), "1")
        self.assertIsNone(mdio.table_with(self.TEXT, "id", "nope"))

    def test_section(self):
        self.assertTrue(mdio.section(self.TEXT, "facts").startswith("## Facts"))
        self.assertNotIn("Other", mdio.section(self.TEXT, "facts"))
        self.assertEqual(mdio.section(self.TEXT, "missing"), "")


if __name__ == "__main__":
    unittest.main()
