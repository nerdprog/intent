"""Session state helpers for StudyCrafter Streamlit app."""

import streamlit as st


# Default values used when initializing the session
DEFAULTS = {
    "student_name": "",
    "goal": "",
    "days_remaining": 0,
    "daily_hours": 0,
    "current_level": "Beginner",
    "chat_history": [],
    "initialized": False,
}


def init_session_state() -> None:
    """Initialize all session state variables with defaults if not already set."""
    for key, value in DEFAULTS.items():
        if key not in st.session_state:
            st.session_state[key] = value

    if not st.session_state.initialized:
        st.session_state.initialized = True


def clear_chat() -> None:
    """Clear the conversation history while keeping student profile intact."""
    st.session_state.chat_history = []


def _display(value: str, fallback: str = "Not set yet") -> str:
    """Return a cleaned display value for the UI."""
    cleaned = (value or "").strip()
    return cleaned if cleaned else fallback


def get_student_context() -> dict:
    """Return the current student profile as a dictionary for the agent."""
    name = _display(st.session_state.student_name, "Not set yet")
    goal = _display(st.session_state.goal, "Not set yet")

    return {
        "student_name": name,
        "goal": goal,
        "days_remaining": st.session_state.days_remaining,
        "daily_hours": st.session_state.daily_hours,
        "current_level": st.session_state.current_level,
        # Values used when calling the LLM (friendlier defaults for the agent)
        "agent_name": name if name != "Not set yet" else "Student",
        "agent_goal": goal if goal != "Not set yet" else "Not specified",
    }
