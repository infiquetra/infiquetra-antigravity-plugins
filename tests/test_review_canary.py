from __future__ import annotations

from pathlib import Path

from scripts.review_canary import score_review

FIXTURE = Path("tests/fixtures/review_canaries/worker_model_cache_scheduling")
EXPECTED = FIXTURE / "expected_findings.json"


def write_review(tmp_path: Path, text: str) -> Path:
    path = tmp_path / "review.md"
    path.write_text(text)
    return path


def test_good_sample_passes() -> None:
    score = score_review(FIXTURE / "sample_review.md")

    assert score.passed is True
    assert score.missed == []
    assert score.invalid_uncited == []
    assert score.false_positives == []


def test_missing_expected_finding_fails(tmp_path: Path) -> None:
    review = write_review(
        tmp_path,
        "| P0 | `Unit` lacks file-path data for segmentation. | docs/a.md:1 | fix |\n",
    )

    score = score_review(review, EXPECTED)

    assert score.passed is False
    assert "row_cardinality" in score.missed
    assert "segment_dependencies" in score.missed


def test_uncited_finding_fails(tmp_path: Path) -> None:
    review = write_review(tmp_path, "| P1 | Row cardinality emits one row per unit. | missing | fix |\n")

    score = score_review(review, EXPECTED)

    assert score.passed is False
    assert score.invalid_uncited


def test_allowed_advisory_extra_does_not_fail(tmp_path: Path) -> None:
    base = (FIXTURE / "sample_review.md").read_text()
    review = write_review(tmp_path, base + "\n| P3 | advisory note only. | docs/a.md:1 | none |\n")

    score = score_review(review, EXPECTED)

    assert score.passed is True


def test_false_positive_reported(tmp_path: Path) -> None:
    base = (FIXTURE / "sample_review.md").read_text()
    review = write_review(tmp_path, base + "\n| P2 | unrelated issue. | docs/a.md:1 | remove |\n")

    score = score_review(review, EXPECTED)

    assert score.passed is False
    assert score.false_positives
