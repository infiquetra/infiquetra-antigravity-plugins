#!/usr/bin/env python3
"""Score saved review output against a small canary fixture."""

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, cast

PRIORITY_RE = re.compile(r"\bP[0-3]\b")
CITATION_RE = re.compile(r"[\w./-]+:\d+")


@dataclass
class Score:
    passed: bool
    missed: list[str]
    false_positives: list[str]
    invalid_uncited: list[str]
    matched: list[str]


def load_expected(review_path: Path, expected_path: Path | None) -> dict[str, Any]:
    if expected_path is None:
        expected_path = review_path.with_name("expected_findings.json")
    return cast(dict[str, Any], json.loads(expected_path.read_text()))


def finding_lines(text: str) -> list[str]:
    return [line.strip() for line in text.splitlines() if PRIORITY_RE.search(line)]


def has_terms(line: str, terms: list[str]) -> bool:
    lowered = line.lower()
    return all(term.lower() in lowered for term in terms)


def score_review(review_path: Path, expected_path: Path | None = None) -> Score:
    expected = load_expected(review_path, expected_path)
    lines = finding_lines(review_path.read_text())
    required = expected.get("required", [])
    allowed_extra_terms = expected.get("allowed_extra_terms", [])

    matched: list[str] = []
    missed: list[str] = []
    invalid_uncited = [line for line in lines if not CITATION_RE.search(line)]

    for item in required:
        item_id = item["id"]
        terms = item["terms"]
        if any(has_terms(line, terms) for line in lines):
            matched.append(item_id)
        else:
            missed.append(item_id)

    false_positives: list[str] = []
    for line in lines:
        if any(has_terms(line, item["terms"]) for item in required):
            continue
        if any(term.lower() in line.lower() for term in allowed_extra_terms):
            continue
        false_positives.append(line)

    return Score(
        passed=not missed and not invalid_uncited and not false_positives,
        missed=missed,
        false_positives=false_positives,
        invalid_uncited=invalid_uncited,
        matched=matched,
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Score a review canary")
    parser.add_argument("review_path", type=Path)
    parser.add_argument("--expected", type=Path, default=None)
    args = parser.parse_args(argv)

    score = score_review(args.review_path, args.expected)
    print(json.dumps(asdict(score), indent=2, sort_keys=True))
    return 0 if score.passed else 1


if __name__ == "__main__":
    sys.exit(main())
