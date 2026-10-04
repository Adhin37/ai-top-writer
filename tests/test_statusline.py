"""tools/statusline.py - the status line and the usage copy the hooks read."""
import json
import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                                "tools"))
import statusline  # noqa: E402


class StatuslineTest(unittest.TestCase):
    def test_the_line_names_the_model_and_both_windows(self):
        out = statusline.line({"model": {"display_name": "Opus"}, "rate_limits": {
            "five_hour": {"used_percentage": 42.7, "resets_at": "2026-10-04T15:00:00Z"},
            "seven_day": {"used_percentage": 10}}})
        self.assertTrue(out.startswith("Opus · 5h 42% (resets "))
        self.assertTrue(out.endswith(" · 7d 10%"))

    def test_a_bad_payload_still_prints_a_line(self):
        for payload in ({}, {"model": "x", "rate_limits": []},
                        {"rate_limits": {"five_hour": {"used_percentage": "high"}}},
                        {"rate_limits": {"five_hour": {"used_percentage": 5,
                                                       "resets_at": "soon"}}}):
            self.assertTrue(statusline.line(payload).startswith("Claude"))

    def test_reset_time_takes_epoch_or_iso_and_nothing_else(self):
        self.assertRegex(statusline.reset_time(1790000000), r"^\d\d:\d\d$")
        self.assertRegex(statusline.reset_time("2026-10-04T15:00:00+00:00"), r"^\d\d:\d\d$")
        for bad in (True, "", "noon", None, []):
            self.assertIsNone(statusline.reset_time(bad))

    def test_save_writes_the_limits_and_skips_an_empty_payload(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "s", "usage.json")
            statusline.save({"rate_limits": {}}, path)
            self.assertFalse(os.path.exists(path))
            limits = {"five_hour": {"used_percentage": 50}}
            statusline.save({"rate_limits": limits}, path)
            with open(path, encoding="utf-8") as fh:
                data = json.load(fh)
            self.assertEqual(data["rate_limits"], limits)
            self.assertIsInstance(data["updated"], float)
            self.assertEqual(os.listdir(os.path.dirname(path)), ["usage.json"])


if __name__ == "__main__":
    unittest.main()
