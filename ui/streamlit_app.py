"""
AI Job Hunter — Streamlit Chatbot UI (Phase 13)

Wraps the LangGraph agent in a chat interface. Conversation context
persists across turns via previous_interaction_id, so follow-ups like
"only show active ones" reference the prior search, per section 5.
"""

import sys
from pathlib import Path
import traceback

# streamlit run launches this script directly (like `python ui/streamlit_app.py`),
# so the project root is NOT automatically on sys.path the way `python -m`
# entry points are. Insert it explicitly, robust to being run from any
# working directory.
_PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))

import asyncio

import streamlit as st

from agent_host.host import run_query

st.set_page_config(page_title="AI Job Hunter", page_icon="🧭", layout="wide")
st.title("🧭 AI Job Hunter")
st.caption(
    "Ask for jobs by role and location. Follow-up questions "
    "(\"only show active ones\", \"broaden to remote\") continue the same search."
)

if "messages" not in st.session_state:
    st.session_state.messages = []
if "last_interaction_id" not in st.session_state:
    st.session_state.last_interaction_id = None


def _status_badge(status: str) -> str:
    return {"active": "🟢 Active", "inactive": "🔴 Inactive", "unknown": "⚪ Unknown"}.get(
        status, "⚪ Unknown"
    )


def _render_job_cards(jobs: list[dict]) -> None:
    if not jobs:
        return
    st.subheader(f"Found {len(jobs)} job(s)")
    for job in jobs:
        with st.container(border=True):
            col1, col2 = st.columns([3, 1])
            with col1:
                st.markdown(f"**{job.get('title', 'Untitled')}**")
                st.write(f"{job.get('company') or 'Unknown company'} — {job.get('location') or 'Unknown location'}")
                if job.get("matched_skills"):
                    st.caption("Matched skills: " + ", ".join(job["matched_skills"]))
            with col2:
                st.write(_status_badge(job.get("active_status", "unknown")))
                if job.get("skill_match_score") is not None:
                    st.write(f"Keyword match: {job['skill_match_score']}%")
                if job.get("semantic_match_score") is not None:
                    st.write(f"Semantic match: {job['semantic_match_score']}%")
                if job.get("job_url"):
                    st.link_button("View posting", job["job_url"])


for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])
        if msg.get("jobs"):
            _render_job_cards(msg["jobs"])

user_input = st.chat_input("Find GenAI Engineer jobs in Chennai...")

if user_input:
    st.session_state.messages.append({"role": "user", "content": user_input})
    with st.chat_message("user"):
        st.markdown(user_input)

    with st.chat_message("assistant"):
        with st.spinner("Searching..."):
            try:
                result = asyncio.run(
                    run_query(user_input, previous_interaction_id=st.session_state.last_interaction_id)
                )
            except BaseExceptionGroup as eg:
                st.error("Caught an ExceptionGroup — printing all sub-exceptions to terminal.")
                for i, sub_exc in enumerate(eg.exceptions):
                    print(f"\n[DEBUG] Sub-exception {i}: {type(sub_exc).__name__}: {sub_exc}")
                    traceback.print_exception(type(sub_exc), sub_exc, sub_exc.__traceback__)
                raise
        

        final_answer = result.get("final_answer", "I couldn't generate a response.")
        st.markdown(final_answer)

        jobs = result.get("last_search_results")
        if jobs:
            _render_job_cards(jobs)

        st.session_state.last_interaction_id = result["interaction"].id
        st.session_state.messages.append(
            {"role": "assistant", "content": final_answer, "jobs": jobs}
        )