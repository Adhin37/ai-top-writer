"""usage-detection's live.py - the usage windows as /usage shows them, never guessed."""
import io
import json
import os
import sys
import tempfile
import time
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, ".claude", "skills", "usage-detection", "scripts"))

import live  # noqa: E402

ANSWER = {"five_hour": {"utilization": 92.0, "resets_at": "2026-10-11T16:50:00.045620+00:00"},
          "seven_day": {"utilization": 86.0, "resets_at": "2026-10-16T02:00:00+00:00"},
          "seven_day_opus": None}


class Opener(object):
    """Stands in for urlopen: records each request, answers ANSWER or raises."""

    def __init__(self, answer=ANSWER, error=None):
        self.answer, self.error, self.requests = answer, error, []

    def __call__(self, req, timeout=None):
        self.requests.append(req)
        if self.error:
            raise self.error
        return io.BytesIO(json.dumps(self.answer).encode())


class LiveTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = self.tmp.name
        self.creds = os.path.join(self.root, ".credentials.json")
        self.login(time.time() + 3600)

    def tearDown(self):
        self.tmp.cleanup()

    def login(self, expires):
        with open(self.creds, "w") as fh:
            json.dump({"claudeAiOauth": {"accessToken": "tok-1", "expiresAt": expires * 1000}}, fh)

    def read(self, opener, now=None, **kw):
        return live.reading(self.root, now=now or time.time(), creds=self.creds, opener=opener,
                            **kw)

    def test_the_answer_in_the_status_line_shape(self):
        opener = Opener()
        found = self.read(opener)
        self.assertEqual(found["source"], "live")
        self.assertEqual(found["rate_limits"]["five_hour"]["used_percentage"], 92.0)
        self.assertEqual(found["rate_limits"]["seven_day"]["resets_at"], live._epoch(
            "2026-10-16T02:00:00+00:00"))
        req = opener.requests[0]
        self.assertEqual(req.full_url, live.URL)
        self.assertEqual(req.get_header("Authorization"), "Bearer tok-1")

    def test_the_token_is_never_saved(self):
        self.read(Opener())
        with open(os.path.join(self.root, live.SAVED)) as fh:
            self.assertNotIn("tok-1", fh.read())

    def test_a_fresh_reading_is_reused_then_fetched_again(self):
        opener, now = Opener(), time.time()
        self.read(opener, now)
        self.read(opener, now + live.MAX_AGE_S - 1)
        self.assertEqual(len(opener.requests), 1)
        self.read(opener, now + live.MAX_AGE_S + 1)
        self.assertEqual(len(opener.requests), 2)

    def test_an_expired_login_sends_nothing(self):
        self.login(time.time() - 60)
        opener = Opener()
        self.assertIsNone(self.read(opener))
        self.assertEqual(opener.requests, [])

    def test_a_failure_gives_no_reading_and_waits_before_retrying(self):
        opener, now = Opener(error=OSError("no network")), time.time()
        self.assertIsNone(self.read(opener, now))
        self.assertIsNone(self.read(opener, now + 10))
        self.assertEqual(len(opener.requests), 1)
        self.read(opener, now + live.RETRY_S + 1)
        self.assertEqual(len(opener.requests), 2)

    def test_an_answer_without_windows_is_no_reading(self):
        self.assertIsNone(self.read(Opener(answer={"five_hour": None})))


if __name__ == "__main__":
    unittest.main()
