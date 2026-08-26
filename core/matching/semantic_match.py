"""
Semantic matching — Phase 10.

Embeds the candidate profile and job descriptions using Sentence
Transformers, compares via ChromaDB cosine similarity. Same pattern as
production schema-RAG work — applied here to job descriptions instead
of table schemas.
"""

import chromadb
import uuid
from sentence_transformers import SentenceTransformer

from core.models.job import Job
from core.profile.candidate_profile import CandidateProfile

_MODEL_NAME = "all-MiniLM-L6-v2"
_model: SentenceTransformer | None = None


def _get_model() -> SentenceTransformer:
    global _model
    if _model is None:
        _model = SentenceTransformer(_MODEL_NAME)
    return _model


def build_profile_text(profile: CandidateProfile) -> str:
    """Turns the structured skill profile into one descriptive paragraph
    suitable for embedding — similar to a resume summary line."""
    skills = ", ".join(profile.all_skills())
    return (
        f"Experienced software engineer with hands-on skills in: {skills}. "
        f"Focused on GenAI, LLM-powered applications, retrieval augmented "
        f"generation, and backend engineering."
    )


def _distance_to_score(distance: float) -> float:
    """ChromaDB's default distance is cosine distance (0 = identical,
    2 = opposite). Convert to an intuitive 0-100 similarity score."""
    similarity = max(0.0, 1.0 - (distance / 2.0))
    return round(similarity * 100, 1)


def semantic_score_jobs(jobs: list[Job], profile: CandidateProfile) -> None:
    """Mutates each job in-place, setting semantic_match_score.
    Uses an ephemeral (in-memory) ChromaDB client — no persistence yet,
    that's Phase 11's job."""
    if not jobs:
        return

    model = _get_model()
    profile_text = build_profile_text(profile)
    profile_embedding = model.encode(profile_text).tolist()

    client = chromadb.EphemeralClient()
    collection = client.create_collection(name=f"job_matching_{uuid.uuid4().hex}")

    documents = [f"{job.title or ''} {job.description or ''}" for job in jobs]
    embeddings = model.encode(documents).tolist()
    ids = [f"job-{i}" for i in range(len(jobs))]

    collection.add(ids=ids, embeddings=embeddings, documents=documents)

    results = collection.query(
        query_embeddings=[profile_embedding], n_results=len(jobs)
    )

    id_to_distance = dict(zip(results["ids"][0], results["distances"][0]))

    for i, job in enumerate(jobs):
        distance = id_to_distance.get(f"job-{i}")
        job.semantic_match_score = _distance_to_score(distance) if distance is not None else None