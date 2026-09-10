"""
StudyCrafter — Multi-Agent Personalized Aptitude Tutor
Main Streamlit Application
Run with: streamlit run app.py
"""

import streamlit as st
from backend.api import get_or_create_student_session
from frontend.chat import (
    handle_user_input,
    render_active_question_ui,
    render_chat_messages,
    render_prompt_pills,
)
from frontend.dashboard import render_sidebar
from frontend.ui import apply_custom_styles, render_header

# ---------------------------------------------------------------------------
# 1. Page Configuration
# ---------------------------------------------------------------------------
st.set_page_config(
    page_title="StudyCrafter — AI Aptitude Tutor",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ---------------------------------------------------------------------------
# 2. Session Initialization
# ---------------------------------------------------------------------------
if "student_id" not in st.session_state:
    # Auto-generate / restore persistent anonymous student session
    student_record = get_or_create_student_session()
    st.session_state.student_id = student_record.get("student_id")

student_id = st.session_state.student_id

# ---------------------------------------------------------------------------
# 3. Apply Styles & Header
# ---------------------------------------------------------------------------
apply_custom_styles()
render_header()

# ---------------------------------------------------------------------------
# 4. Sidebar Dashboard
# ---------------------------------------------------------------------------
def on_quick_action(action_text: str):
    handle_user_input(student_id, action_text)

render_sidebar(student_id=student_id, on_quick_action=on_quick_action)

# ---------------------------------------------------------------------------
# 5. Suggested Prompt Pills
# ---------------------------------------------------------------------------
render_prompt_pills(on_pill_click=on_quick_action)

st.divider()

# ---------------------------------------------------------------------------
# 6. Chat History & Interactive Question UI
# ---------------------------------------------------------------------------
render_chat_messages(student_id=student_id)

render_active_question_ui(student_id=student_id)

# ---------------------------------------------------------------------------
# 7. Natural Language Chat Input
# ---------------------------------------------------------------------------
user_prompt = st.chat_input(
    placeholder="Ask me anything about your aptitude preparation..."
)

if user_prompt:
    handle_user_input(student_id=student_id, prompt_text=user_prompt)
