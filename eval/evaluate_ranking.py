"""
Evaluation script — Precision@5 for job ranking.

Phase 17.5.5.

Runs the actual matching + ranking pipeline (normalize -> dedup ->
hard filter -> keyword/experience/freshness scoring -> semantic
scoring -> ranking) against frozen, manually-labelled job fixtures.

This is deliberately OFFLINE (no live API calls) so results are
reproducible and can run in CI.
"""

import json
from pathlib import Path

from core.dedup.deduplicate import dedup_jobs
from core.filtering.hard_filter import HardFilterConfig, apply_hard_filters
from core.matching.experience_fit import calculate_experience_fit
from core.matching.freshness import calculate_freshness_score
from core.matching.keyword_match import score_job_against_profile
from core.matching.ranking import rank_jobs
from core.matching.semantic_match import semantic_score_jobs
from core.models.normalize import normalize_job
from core.profile.load_profile import load_profile

FIXTURES_DIR = Path(__file__).parent / "fixtures"
LABELS_DIR = Path(__file__).parent / "labels"
RESULTS_PATH = Path(__file__).parent / "results.json"

TOP_K = 5


def _job_key(title: str | None, company: str | None) -> str:
    return f"{(title or '').strip().lower()}|{(company or '').strip().lower()}"


def _run_pipeline(raw_jobs: list[dict], location: str, profile) -> list:
    normalized = [normalize_job(job) for job in raw_jobs]
    deduped = dedup_jobs(normalized)

    config = HardFilterConfig(
        candidate_experience_years=profile.experience_years,
        experience_buffer_years=2.0,
        requested_location=location,
        allow_remote=True,
    )
    kept, _rejected = apply_hard_filters(deduped, config)

    for job in kept:
        matched, score = score_job_against_profile(job, profile)
        job.matched_skills = matched
        job.skill_match_score = score
        job.experience_fit_score = calculate_experience_fit(
            job, profile.experience_years
        )
        job.freshness_score = calculate_freshness_score(job)

    semantic_score_jobs(kept, profile)

    return rank_jobs(kept)


def evaluate_fixture(fixture_path: Path, profile) -> dict:
    with open(fixture_path, "r", encoding="utf-8") as f:
        fixture = json.load(f)

    label_path = LABELS_DIR / fixture_path.name
    if not label_path.exists():
        raise FileNotFoundError(
            f"No label file for {fixture_path.name} — expected {label_path}"
        )
    with open(label_path, "r", encoding="utf-8") as f:
        relevant_keys = {key.strip().lower() for key in json.load(f)}

    role = fixture["role"]
    location = fixture["location"]
    raw_jobs = fixture["jobs"]

    ranked = _run_pipeline(raw_jobs, location, profile)
    top_k = ranked[:TOP_K]

    relevant_in_top_k = sum(
        1 for job in top_k if _job_key(job.title, job.company) in relevant_keys
    )
    precision = relevant_in_top_k / min(TOP_K, len(top_k)) if top_k else 0.0

    return {
        "query": f"{role} @ {location}",
        "fixture": fixture_path.name,
        "top_k": len(top_k),
        "relevant_in_top_k": relevant_in_top_k,
        "precision_at_5": round(precision, 2),
        "ranked_titles": [f"{job.title} — {job.company}" for job in top_k],
    }


def main() -> None:
    profile = load_profile()
    fixture_paths = sorted(FIXTURES_DIR.glob("*.json"))

    if not fixture_paths:
        print(f"No fixtures found in {FIXTURES_DIR}.")
        return

    results = [evaluate_fixture(path, profile) for path in fixture_paths]

    print(f"{'Query':<35} {'Precision@5':<15} {'Relevant/Top-K'}")
    print("-" * 70)
    for r in results:
        print(
            f"{r['query']:<35} {r['precision_at_5']:<15} "
            f"{r['relevant_in_top_k']}/{r['top_k']}"
        )

    avg_precision = round(sum(r["precision_at_5"] for r in results) / len(results), 2)
    print("-" * 70)
    print(f"{'Average Precision@5':<35} {avg_precision}")

    with open(RESULTS_PATH, "w", encoding="utf-8") as f:
        json.dump(
            {"results": results, "average_precision_at_5": avg_precision},
            f,
            indent=2,
        )
    print(f"\nSaved detailed results to {RESULTS_PATH}")


if __name__ == "__main__":
    main()