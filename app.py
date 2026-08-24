"""
StudyCrafter — Phase 1: AI Aptitude Tutor Chatbot

Run with: streamlit run app.py
"""

import streamlit as st

from agents.tutor_agent import TutorAgent
from utils.session_state import clear_chat, get_student_context, init_session_state


@st.cache_resource
def get_tutor_agent() -> TutorAgent:
    """Create one tutor agent instance per app session for faster responses."""
    return TutorAgent()


# ---------------------------------------------------------------------------
# Page configuration — must be the first Streamlit command
# ---------------------------------------------------------------------------
st.set_page_config(
    page_title="StudyCrafter",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ---------------------------------------------------------------------------
# Initialize session state
# ---------------------------------------------------------------------------
init_session_state()

# ---------------------------------------------------------------------------
# Sidebar — student profile inputs
# Use `key=` so Streamlit manages widget state (+/- buttons work correctly).
# ---------------------------------------------------------------------------
with st.sidebar:
    st.markdown("## 🎓 StudyCrafter")
    st.caption("AI Aptitude Learning Agent")
    st.divider()

    st.subheader("Student Profile")

    st.text_input(
        "Your Name",
        key="student_name",
        placeholder="Enter your name",
    )

    st.text_area(
        "Your Goal",
        key="goal",
        placeholder="e.g. Crack placement aptitude test",
        height=80,
    )

    st.number_input(
        "Days Remaining",
        min_value=0,
        max_value=365,
        step=1,
        key="days_remaining",
    )

    st.number_input(
        "Daily Study Hours",
        min_value=0,
        max_value=24,
        step=1,
        key="daily_hours",
    )

    st.selectbox(
        "Current Level",
        options=["Beginner", "Intermediate", "Advanced"],
        key="current_level",
    )

    st.divider()

    if st.button("🗑️ Clear Chat", use_container_width=True):
        clear_chat()
        st.rerun()

    st.divider()
    st.caption(f"AI Provider: {TutorAgent.get_provider_label()}")
    st.caption("Phase 1 — Agentic AI Demo")

# ---------------------------------------------------------------------------
# Main page — header and student context card
# ---------------------------------------------------------------------------
st.title("🎓 StudyCrafter")
st.subheader("Your AI Aptitude Learning Agent")

ctx = get_student_context()

# Native Streamlit card — avoids raw HTML showing as plain text
with st.container(border=True):
    st.markdown("**Your Study Profile**")
    col1, col2 = st.columns(2)
    with col1:
        st.markdown(f"**Student:** {ctx['student_name']}")
        st.markdown(f"**Goal:** {ctx['goal']}")
        st.markdown(f"**Current Level:** {ctx['current_level']}")
    with col2:
        st.markdown(f"**Days Remaining:** {ctx['days_remaining']}")
        st.markdown(f"**Daily Study Time:** {ctx['daily_hours']} hours")

st.divider()

# ---------------------------------------------------------------------------
# Chat history display
# ---------------------------------------------------------------------------
for message in st.session_state.chat_history:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# ---------------------------------------------------------------------------
# Chat input and agent response
# ---------------------------------------------------------------------------
user_input = st.chat_input("Ask your aptitude tutor anything...")

if user_input:
    with st.chat_message("user"):
        st.markdown(user_input)

    st.session_state.chat_history.append(
        {"role": "user", "content": user_input}
    )

    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            try:
                agent = get_tutor_agent()
                prior_history = st.session_state.chat_history[:-1]
                response = agent.generate_response(
                    student_context=get_student_context(),
                    chat_history=prior_history,
                    user_message=user_input,
                )
                st.markdown(response)

                st.session_state.chat_history.append(
                    {"role": "assistant", "content": response}
                )

            except Exception as exc:
                error_msg = TutorAgent.format_error(exc)
                st.markdown(error_msg)
                st.session_state.chat_history.pop()
