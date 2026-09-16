"""
AI Job Hunter — Streamlit Chatbot UI (Phase 17.4)

Candidate-facing job search interface with:
- Chat-based job search
- Conversation context via previous_interaction_id
- Candidate-friendly job cards
- Prominent match score
- Active/inactive status
- Matched skills
- Experience and freshness information
- Direct job posting links
"""

import sys
from pathlib import Path
import traceback

# streamlit run launches this script directly, so the project root
# is not automatically available on sys.path.
_PROJECT_ROOT = Path(__file__).resolve().parent.parent

if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))

import asyncio

import streamlit as st

from agent_host.host import run_query


# ---------------------------------------------------------------------------
# Page configuration
# ---------------------------------------------------------------------------

st.set_page_config(
    page_title="AI Job Hunter",
    page_icon="🧭",
    layout="wide",
)


# ---------------------------------------------------------------------------
# Custom styling
# ---------------------------------------------------------------------------

st.markdown(
    """
    <style>

    /* ---------------------------------------------------------------
       Job card
       --------------------------------------------------------------- */

    .job-card {
        padding: 1.25rem 1.35rem;
        border: 1px solid rgba(128, 128, 128, 0.22);
        border-radius: 16px;
        margin-bottom: 1rem;
        background: rgba(128, 128, 128, 0.035);
    }


    /* ---------------------------------------------------------------
       Job title
       --------------------------------------------------------------- */

    .job-title {
        font-size: 1.18rem;
        font-weight: 700;
        line-height: 1.35;
        margin-bottom: 0.35rem;
    }


    /* ---------------------------------------------------------------
       Company
       --------------------------------------------------------------- */

    .job-company {
        font-size: 0.96rem;
        font-weight: 600;
        margin-bottom: 0.2rem;
    }


    /* ---------------------------------------------------------------
       Location
       --------------------------------------------------------------- */

    .job-location {
        font-size: 0.88rem;
        opacity: 0.72;
        margin-bottom: 0.85rem;
    }


    /* ---------------------------------------------------------------
       Match score
       --------------------------------------------------------------- */

    .job-match-box {
        text-align: center;
        padding: 0.55rem 0.7rem;
        border-radius: 12px;
        background: rgba(46, 160, 67, 0.10);
        border: 1px solid rgba(46, 160, 67, 0.22);
        margin-bottom: 0.55rem;
    }

    .job-match-label {
        font-size: 0.72rem;
        opacity: 0.72;
        text-transform: uppercase;
        letter-spacing: 0.04em;
    }

    .job-match-score {
        font-size: 1.45rem;
        font-weight: 800;
        line-height: 1.2;
    }


    /* ---------------------------------------------------------------
       Status
       --------------------------------------------------------------- */

    .job-status {
        font-size: 0.82rem;
        font-weight: 600;
        margin-bottom: 0.6rem;
    }


    /* ---------------------------------------------------------------
       Skills
       --------------------------------------------------------------- */

    .job-skills {
        margin-top: 0.35rem;
        margin-bottom: 0.2rem;
    }

    .job-skill {
        display: inline-block;
        padding: 0.22rem 0.5rem;
        margin: 0.15rem 0.25rem 0.15rem 0;
        border-radius: 7px;
        font-size: 0.76rem;
        background: rgba(128, 128, 128, 0.10);
        border: 1px solid rgba(128, 128, 128, 0.16);
    }


    /* ---------------------------------------------------------------
       Job metadata
       --------------------------------------------------------------- */

    .job-meta {
        font-size: 0.82rem;
        opacity: 0.78;
        margin: 0.22rem 0;
    }


    /* ---------------------------------------------------------------
       Small helper text
       --------------------------------------------------------------- */

    .job-helper {
        font-size: 0.78rem;
        opacity: 0.65;
        margin-top: 0.2rem;
    }

    </style>
    """,
    unsafe_allow_html=True,
)


# ---------------------------------------------------------------------------
# Header
# ---------------------------------------------------------------------------

st.title("🧭 AI Job Hunter")

st.caption(
    "Ask for jobs by role and location. Follow-up questions such as "
    '"only show active ones" or "broaden to remote" can continue the search.'
)


# ---------------------------------------------------------------------------
# Session state
# ---------------------------------------------------------------------------

if "messages" not in st.session_state:
    st.session_state.messages = []

if "last_interaction_id" not in st.session_state:
    st.session_state.last_interaction_id = None


# ---------------------------------------------------------------------------
# Helper functions
# ---------------------------------------------------------------------------

def _status_badge(status: str) -> str:
    """
    Convert backend job status into a candidate-friendly label.
    """

    return {
        "active": "🟢 Active",
        "inactive": "🔴 Inactive",
        "unknown": "⚪ Status unknown",
    }.get(
        status,
        "⚪ Status unknown",
    )


def _format_experience(job: dict) -> str:
    """
    Convert experience_min / experience_max into human-readable text.
    """

    minimum = job.get("experience_min")
    maximum = job.get("experience_max")

    if minimum is None:
        return "Not specified"

    minimum = float(minimum)

    if maximum is not None:
        maximum = float(maximum)

        if minimum.is_integer() and maximum.is_integer():
            return f"{minimum:.0f}–{maximum:.0f} years"

        return f"{minimum:g}–{maximum:g} years"

    if minimum.is_integer():
        return f"{minimum:.0f}+ years"

    return f"{minimum:g}+ years"


def _format_freshness(score) -> str:
    """
    Convert freshness score into candidate-friendly language.
    """

    if score is None:
        return "Not available"

    score = float(score)

    if score >= 90:
        return "Very recent"

    if score >= 75:
        return "Recent"

    if score >= 50:
        return "Moderate"

    return "Older"


def _render_job_cards(jobs: list[dict]) -> None:
    """
    Render ranked jobs as candidate-facing cards.

    Backend ranking scores are retained in the job objects but
    internal scoring details such as keyword/semantic percentages
    are intentionally not exposed in the UI.
    """

    if not jobs:
        return

    st.subheader(f"Top {len(jobs)} matching job(s)")

    for index, job in enumerate(jobs, start=1):

        with st.container(border=True):

            col1, col2 = st.columns(
                [3.2, 1],
                gap="large",
            )

            # -------------------------------------------------------
            # Left column
            # -------------------------------------------------------

            with col1:

                title = job.get("title") or "Untitled"

                st.markdown(
                    f"<div class='job-title'>"
                    f"{index}. {title}"
                    f"</div>",
                    unsafe_allow_html=True,
                )

                company = job.get("company") or "Unknown company"

                st.markdown(
                    f"<div class='job-company'>"
                    f"{company}"
                    f"</div>",
                    unsafe_allow_html=True,
                )

                location = job.get("location") or "Unknown location"

                st.markdown(
                    f"<div class='job-location'>"
                    f"📍 {location}"
                    f"</div>",
                    unsafe_allow_html=True,
                )

                # ---------------------------------------------------
                # Matched skills
                # ---------------------------------------------------

                matched_skills = job.get("matched_skills") or []

                if matched_skills:

                    st.markdown("**Matched skills**")

                    skills_html = "".join(
                        f"<span class='job-skill'>{skill}</span>"
                        for skill in matched_skills
                    )

                    st.markdown(
                        f"<div class='job-skills'>"
                        f"{skills_html}"
                        f"</div>",
                        unsafe_allow_html=True,
                    )

                else:

                    st.caption(
                        "No specific skill matches available."
                    )

            # -------------------------------------------------------
            # Right column
            # -------------------------------------------------------

            with col2:

                # ---------------------------------------------------
                # Match score
                # ---------------------------------------------------

                relevance_score = job.get("relevance_score")

                if relevance_score is not None:

                    st.markdown(
                        f"""
                        <div class="job-match-box">
                            <span class="job-match-label">MATCH SCORE</span><br>
                            <span class="job-match-score">
                                {float(relevance_score):.0f}%
                            </span>
                        </div>
                        """,
                        unsafe_allow_html=True,
                    )

                # ---------------------------------------------------
                # Active status
                # ---------------------------------------------------

                status = job.get(
                    "active_status",
                    "unknown",
                )

                st.markdown(
                    f"<div class='job-status'>"
                    f"{_status_badge(status)}"
                    f"</div>",
                    unsafe_allow_html=True,
                )

                # ---------------------------------------------------
                # Experience
                # ---------------------------------------------------

                experience = _format_experience(job)

                st.markdown(
                    f"<div class='job-meta'>"
                    f"💼 Experience: {experience}"
                    f"</div>",
                    unsafe_allow_html=True,
                )

                # ---------------------------------------------------
                # Freshness
                # ---------------------------------------------------

                freshness = _format_freshness(
                    job.get("freshness_score")
                )

                st.markdown(
                    f"<div class='job-meta'>"
                    f"🕒 Posted: {freshness}"
                    f"</div>",
                    unsafe_allow_html=True,
                )

                # ---------------------------------------------------
                # Job posting
                # ---------------------------------------------------

                job_url = job.get("job_url")

                if job_url:

                    st.link_button(
                        "View Job Posting →",
                        job_url,
                        use_container_width=True,
                    )


# ---------------------------------------------------------------------------
# Render previous conversation
# ---------------------------------------------------------------------------

for msg in st.session_state.messages:

    with st.chat_message(msg["role"]):

        if msg.get("jobs"):

            st.markdown(
                "Here are the best matching jobs I found."
            )

            _render_job_cards(msg["jobs"])

        else:

            st.markdown(
                msg["content"]
            )


# ---------------------------------------------------------------------------
# Chat input
# ---------------------------------------------------------------------------

user_input = st.chat_input(
    "Find GenAI Engineer jobs in Chennai..."
)


# ---------------------------------------------------------------------------
# Handle new user query
# ---------------------------------------------------------------------------

if user_input:

    # ---------------------------------------------------------------
    # Store user message
    # ---------------------------------------------------------------

    st.session_state.messages.append(
        {
            "role": "user",
            "content": user_input,
        }
    )

    with st.chat_message("user"):

        st.markdown(user_input)

    # ---------------------------------------------------------------
    # Run agent
    # ---------------------------------------------------------------

    with st.chat_message("assistant"):

        with st.spinner("Searching for matching jobs..."):

            try:

                result = asyncio.run(
                    run_query(
                        user_input,
                        previous_interaction_id=(
                            st.session_state.last_interaction_id
                        ),
                    )
                )

            except BaseExceptionGroup as eg:

                st.error(
                    "The agent encountered multiple errors. "
                    "Please check the terminal logs."
                )

                for i, sub_exc in enumerate(
                    eg.exceptions
                ):

                    print(
                        f"\n[DEBUG] Sub-exception {i}: "
                        f"{type(sub_exc).__name__}: {sub_exc}"
                    )

                    traceback.print_exception(
                        type(sub_exc),
                        sub_exc,
                        sub_exc.__traceback__,
                    )

                raise

            except Exception as exc:

                st.error(
                    f"Something went wrong while searching: {exc}"
                )

                traceback.print_exc()

                raise

        # -----------------------------------------------------------
        # Final assistant response
        # -----------------------------------------------------------

        final_answer = result.get(
            "final_answer",
            "I couldn't generate a response.",
        )

        jobs = result.get(
            "last_search_results"
        )

        # -----------------------------------------------------------
        # Avoid duplicate job listing from LLM
        # -----------------------------------------------------------

        if jobs:

            st.markdown(
                "Here are the best matching jobs I found."
            )

            _render_job_cards(jobs)

        else:

            st.markdown(final_answer)

        # -----------------------------------------------------------
        # Persist interaction
        # -----------------------------------------------------------

        interaction = result.get("interaction")

        if interaction is not None:

            st.session_state.last_interaction_id = (
                interaction.id
            )

        # -----------------------------------------------------------
        # Store assistant message
        # -----------------------------------------------------------

        st.session_state.messages.append(
            {
                "role": "assistant",
                "content": final_answer,
                "jobs": jobs,
            }
        )