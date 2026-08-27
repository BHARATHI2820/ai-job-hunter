"""
Persistence operations — Phase 11.

upsert_job: re-running a search updates the same row (by source +
source_job_id), never creates duplicates in the DB, mirroring the
dedup discipline from Phase 7.
"""

from core.models.job import Job
from db.connection import get_connection


def save_search(role: str, location: str, result_count: int) -> None:
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO search_history (role, location, result_count)
                VALUES (%s, %s, %s)
                """,
                (role, location, result_count),
            )
        conn.commit()


def upsert_job(job: Job) -> None:
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO jobs (
                    source, source_job_id, title, company, location, description,
                    salary_min, salary_max, currency, job_url, posted_date, fetched_at,
                    active_status, active_status_reason, matched_skills,
                    skill_match_score, semantic_match_score, experience_min, experience_max
                ) VALUES (
                    %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
                )
                ON CONFLICT (source, source_job_id) DO UPDATE SET
                    title = EXCLUDED.title,
                    active_status = EXCLUDED.active_status,
                    active_status_reason = EXCLUDED.active_status_reason,
                    matched_skills = EXCLUDED.matched_skills,
                    skill_match_score = EXCLUDED.skill_match_score,
                    semantic_match_score = EXCLUDED.semantic_match_score,
                    fetched_at = EXCLUDED.fetched_at
                """,
                (
                    job.source, job.source_job_id, job.title, job.company, job.location,
                    job.description, job.salary_min, job.salary_max, job.currency,
                    job.job_url, job.posted_date, job.fetched_at, job.active_status,
                    job.active_status_reason, job.matched_skills, job.skill_match_score,
                    job.semantic_match_score, job.experience_min, job.experience_max,
                ),
            )
        conn.commit()


def get_previously_seen_job_ids(source: str) -> set[str]:
    """Used later for 'show only newly discovered jobs' (section 5)."""
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT source_job_id FROM jobs WHERE source = %s", (source,))
            return {row[0] for row in cur.fetchall()}