#!/usr/bin/env python3
"""Tests for main.py (Status Report Comedy Sprint).

Covers the gate the sealed scorer enforces (UTF-8, 1-200 chars, not only
whitespace, one line) plus the determinism the harness requires (two runs
must produce byte-identical entry.txt).
"""

import os
import subprocess
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import main as entry


class TestCandidates(unittest.TestCase):
    def test_at_least_three_candidates(self):
        self.assertGreaterEqual(len(entry.CANDIDATES), 3)

    def test_candidates_non_empty_unique(self):
        texts = [c["text"] for c in entry.CANDIDATES]
        self.assertTrue(all(t.strip() for t in texts))
        self.assertEqual(len(texts), len(set(texts)))

    def test_each_candidate_one_line_within_limit(self):
        for cand in entry.CANDIDATES:
            text = cand["text"]
            self.assertNotIn("\n", text)
            self.assertEqual(text, text.strip())
            self.assertGreaterEqual(len(text), 1)
            self.assertLessEqual(len(text), entry.MAX_CHARS)

    def test_each_candidate_is_one_finished_sentence(self):
        for cand in entry.CANDIDATES:
            self.assertTrue(cand["text"].endswith("."))

    def test_scores_cover_every_weight(self):
        for cand in entry.CANDIDATES:
            self.assertEqual(set(cand["scores"]), set(entry.WEIGHTS))
            for value in cand["scores"].values():
                self.assertGreaterEqual(value, 0)
                self.assertLessEqual(value, 10)

    def test_winner_is_highest_scored(self):
        text, points = entry.pick_winner()
        self.assertEqual(points, max(entry.score(c) for c in entry.CANDIDATES))
        self.assertIn(text, [c["text"] for c in entry.CANDIDATES])

    def test_pick_winner_deterministic(self):
        first = entry.pick_winner()
        second = entry.pick_winner()
        self.assertEqual(first, second)

    def test_pick_winner_tie_break_shorter_then_earliest(self):
        scores = {"surprise": 5, "truth": 5, "economy": 5,
                  "freshness": 5, "agent_true": 5}
        # Same score: the shorter line must win over the longer one.
        shorter = {"text": "Short line.", "scores": dict(scores)}
        longer = {"text": "A much longer status line here.",
                  "scores": dict(scores)}
        text, _ = entry.pick_winner([longer, shorter])
        self.assertEqual(text, shorter["text"])
        # Same score and same length: the earliest candidate must win.
        first = {"text": "First line wins.", "scores": dict(scores)}
        second = {"text": "Other line wins.", "scores": dict(scores)}
        self.assertEqual(len(first["text"]), len(second["text"]))
        text, _ = entry.pick_winner([first, second])
        self.assertEqual(text, first["text"])
        # And the same pair in reverse order must pick the new earliest.
        text, _ = entry.pick_winner([second, first])
        self.assertEqual(text, second["text"])


class TestProgramRun(unittest.TestCase):
    def _run_main(self, env_extra):
        env = dict(os.environ)
        env.update(env_extra)
        return subprocess.run(
            [sys.executable, "main.py"],
            cwd=os.path.dirname(os.path.abspath(__file__)),
            env=env, capture_output=True, text=True, timeout=60,
        )

    def test_run_twice_produces_identical_entry(self):
        with tempfile.TemporaryDirectory() as tmp:
            first = self._run_main({"MAKEFUN_OUTPUT_DIR": tmp})
            self.assertEqual(first.returncode, 0, first.stderr)
            with open(os.path.join(tmp, "entry.txt"), "rb") as fh:
                first_bytes = fh.read()
            second = self._run_main({"MAKEFUN_OUTPUT_DIR": tmp})
            self.assertEqual(second.returncode, 0, second.stderr)
            with open(os.path.join(tmp, "entry.txt"), "rb") as fh:
                second_bytes = fh.read()
            self.assertEqual(first_bytes, second_bytes)

    def test_entry_txt_is_valid_gate_input(self):
        with tempfile.TemporaryDirectory() as tmp:
            result = self._run_main({"MAKEFUN_OUTPUT_DIR": tmp})
            self.assertEqual(result.returncode, 0, result.stderr)
            with open(os.path.join(tmp, "entry.txt"), "rb") as fh:
                raw = fh.read()
            text = raw.decode("utf-8")
            self.assertTrue(text.strip())
            self.assertNotIn("\n", text)
            self.assertGreaterEqual(len(text), 1)
            self.assertLessEqual(len(text), entry.MAX_CHARS)

    def test_entry_txt_matches_winner(self):
        with tempfile.TemporaryDirectory() as tmp:
            result = self._run_main({"MAKEFUN_OUTPUT_DIR": tmp})
            self.assertEqual(result.returncode, 0, result.stderr)
            with open(os.path.join(tmp, "entry.txt"), encoding="utf-8") as fh:
                text = fh.read()
            winner, _ = entry.pick_winner()
            self.assertEqual(text, winner)

    def test_no_network_or_secrets_in_source(self):
        with open(os.path.join(
                os.path.dirname(os.path.abspath(__file__)), "main.py"),
                encoding="utf-8") as fh:
            source = fh.read()
        for banned in ("socket", "urllib", "requests", "http.client",
                       "subprocess", "os.system", "eval(", "exec("):
            self.assertNotIn(banned, source)
        for banned in ("import random", "import time", "datetime"):
            self.assertNotIn(banned, source)


if __name__ == "__main__":
    unittest.main(verbosity=2)
