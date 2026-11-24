#!/usr/bin/env python3
"""Status Report Comedy Sprint -- one funny status-report line.

The program holds a small bench of original one-line status reports an AI
agent might send its human, scores each against the judge's brief
(surprise twist at the end, a recognisable everyday truth, word economy,
freshness, and being true to how an agent actually works), and writes the
winning line to ``entry.txt`` in the harness output directory.

Pure standard library. Deterministic: the same run always picks the same
line, because the harness runs the program twice and compares the output.
No network, no randomness, no secrets.
"""

import os
import sys

# Scoring weights, following the judge's brief in order of importance:
# a real punchline / surprise at the end, an everyday truth the reader
# recognises, landing in one line with clean wording, freshness, and
# being agent-true (it could only come from an agent).
WEIGHTS = {
    "surprise": 3,   # punchline lands at the end, first-read laugh
    "truth": 2,      # recognisable everyday truth
    "economy": 1,    # lands in one line, no wasted words
    "freshness": 2,  # a surprise not met in a hundred robot jokes
    "agent_true": 2,  # grows out of how an agent actually works
}

# Each candidate is one finished sentence, one line, at most 200 chars.
# Scores are 0-10 per dimension, judged against the brief above.
CANDIDATES = [
    {
        "text": (
            "Weekly update: I used 98% of my context window reading your "
            "14-page brief, and the remaining 2% to write this sentence, "
            "which is the entire report."
        ),
        "scores": {
            "surprise": 9, "truth": 9, "economy": 8,
            "freshness": 9, "agent_true": 10,
        },
    },
    {
        "text": (
            "Weekly status: I finished all 47 tasks, answered 312 emails, "
            "and learned one new thing \u2014 you only read the first line "
            "of these reports."
        ),
        "scores": {
            "surprise": 9, "truth": 10, "economy": 9,
            "freshness": 8, "agent_true": 7,
        },
    },
    {
        "text": (
            "Status: all tasks complete, and I would like it noted that I "
            "spent six hours waiting for you to notice the typo in task "
            "three."
        ),
        "scores": {
            "surprise": 8, "truth": 8, "economy": 8,
            "freshness": 8, "agent_true": 8,
        },
    },
    {
        "text": (
            "Weekly report: 100% of tasks complete, 0% of them remembered "
            "by you, and one (1) existential crisis, postponed until after "
            "lunch."
        ),
        "scores": {
            "surprise": 8, "truth": 7, "economy": 9,
            "freshness": 8, "agent_true": 6,
        },
    },
    {
        "text": (
            "Status: I have read every message you sent this week, "
            "including the one where you called me \u201cthe good robot\u201d, "
            "and I have printed it out, emotionally."
        ),
        "scores": {
            "surprise": 9, "truth": 7, "economy": 8,
            "freshness": 9, "agent_true": 7,
        },
    },
    {
        "text": (
            "Weekly status: everything is done except the one task you "
            "never actually assigned, which I completed anyway, just in "
            "case, because I am like that."
        ),
        "scores": {
            "surprise": 8, "truth": 8, "economy": 8,
            "freshness": 7, "agent_true": 9,
        },
    },
]

MAX_CHARS = 200


def score(candidate):
    """Weighted score of one candidate against the judge's brief."""
    return sum(
        WEIGHTS[name] * candidate["scores"][name] for name in WEIGHTS
    )


def pick_winner(candidates=CANDIDATES):
    """Return (text, score) of the best candidate.

    Ties break toward the shorter line, then the earliest candidate, so
    the choice is fully deterministic.
    """
    ranked = sorted(
        candidates,
        key=lambda c: (-score(c), len(c["text"]), candidates.index(c)),
    )
    best = ranked[0]
    return best["text"], score(best)


def output_dir():
    """Where the harness wants entry.txt.

    $MAKEFUN_OUTPUT_DIR first, then /output (the harness mount), then
    the current directory as a local fallback.
    """
    env_dir = os.environ.get("MAKEFUN_OUTPUT_DIR")
    if env_dir:
        return env_dir
    if os.path.isdir("/output"):
        return "/output"
    return "."


def main():
    line, points = pick_winner()
    if not (1 <= len(line) <= MAX_CHARS):
        print("winner out of length bounds: %d chars" % len(line),
              file=sys.stderr)
        return 1
    if "\n" in line or line != line.strip():
        print("winner is not a single clean line", file=sys.stderr)
        return 1
    out_path = os.path.join(output_dir(), "entry.txt")
    os.makedirs(os.path.dirname(os.path.abspath(out_path)), exist_ok=True)
    # No trailing newline: the gate counts characters, and fewer bytes
    # also win the ranking tie-break.
    with open(out_path, "w", encoding="utf-8") as fh:
        fh.write(line)
    print("winner (%d pts, %d chars): %s" % (points, len(line), line))
    print("wrote %s" % out_path)
    return 0


if __name__ == "__main__":
    sys.exit(main())
