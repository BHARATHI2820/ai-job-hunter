-- Phase 11 — only the two tables actually needed right now.
-- candidate_profile, job_status_history, job_sources deferred
-- until a real feature needs them (per section 20's own guidance).

CREATE TABLE IF NOT EXISTS jobs (
    id SERIAL PRIMARY KEY,
    source TEXT NOT NULL,
    source_job_id TEXT NOT NULL,
    title TEXT NOT NULL,
    company TEXT,
    location TEXT,
    description TEXT,
    salary_min NUMERIC,
    salary_max NUMERIC,
    currency TEXT DEFAULT 'INR',
    job_url TEXT,
    posted_date TIMESTAMPTZ,
    fetched_at TIMESTAMPTZ NOT NULL,
    active_status TEXT DEFAULT 'unknown',
    active_status_reason TEXT,
    matched_skills TEXT[],
    skill_match_score NUMERIC,
    semantic_match_score NUMERIC,
    experience_min NUMERIC,
    experience_max NUMERIC,
    UNIQUE (source, source_job_id)
);

CREATE TABLE IF NOT EXISTS search_history (
    id SERIAL PRIMARY KEY,
    role TEXT NOT NULL,
    location TEXT NOT NULL,
    result_count INTEGER NOT NULL,
    searched_at TIMESTAMPTZ NOT NULL DEFAULT now()
);