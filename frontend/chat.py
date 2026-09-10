"""
StudyCrafter — Interactive Chat & MCQ Question Component
"""

import streamlit as st
from backend.api import (
    get_active_question,
    get_chat_history,
    process_student_message,
    submit_student_answer,
)


def render_prompt_pills(on_pill_click):
    """Render one-click quick prompt pills above or below the chat."""
    st.caption("💡 **Quick Prompts:**")
    pills = [
        "Teach me percentages",
        "Give me a practice question",
        "I am weak in probability",
        "Show my progress",
    ]

    cols = st.columns(len(pills))
    for i, pill in enumerate(pills):
        with cols[i]:
            if st.button(pill, key=f"pill_{i}", use_container_width=True):
                on_pill_click(pill)


def render_chat_messages(student_id: str):
    """Render historical chat conversation."""
    history = get_chat_history(student_id)

    if not history:
        with st.chat_message("assistant", avatar="🎓"):
            st.markdown(
                "Hi! Tell me about your **aptitude preparation**.\n\n"
                "For example: *I have an aptitude test in 7 days. I can study 2 hours daily "
                "and I am weak in percentages and probability.*"
            )
        return

    for msg in history:
        role = msg["role"]
        avatar = "👤" if role == "user" else "🎓"
        with st.chat_message(role, avatar=avatar):
            st.markdown(msg["content"])


def render_active_question_ui(student_id: str):
    """Render interactive MCQ Question card with selectable options and deterministic submission."""
    active_q = get_active_question(student_id)
    if not active_q:
        return

    with st.container(border=True):
        col_q1, col_q2 = st.columns([3, 1])
        with col_q1:
            st.markdown(f"**📚 Topic:** `{active_q.get('topic', 'Aptitude')}`")
        with col_q2:
            diff = active_q.get("difficulty", "Easy")
            st.caption(diff)

        st.markdown(f"### {active_q.get('question')}")

        options = active_q.get("options", {})
        # Format options for radio
        radio_choices = []
        letter_map = {}
        for letter in ["A", "B", "C", "D"]:
            if letter in options:
                opt_str = f"**{letter}.** {options[letter]}"
                radio_choices.append(opt_str)
                letter_map[opt_str] = letter

        if radio_choices:
            selected_choice = st.radio(
                "Select your answer:",
                options=radio_choices,
                key=f"mcq_radio_{active_q.get('id')}",
            )

            col_sub1, col_sub2 = st.columns([1, 4])
            with col_sub1:
                if st.button("Submit Answer", type="primary", key=f"btn_sub_{active_q.get('id')}"):
                    selected_letter = letter_map.get(selected_choice, "A")
                    with st.spinner("Evaluating answer..."):
                        submit_student_answer(
                            student_id=student_id,
                            answer_letter=selected_letter,
                            question_id=active_q.get("id"),
                        )
                    st.rerun()


def handle_user_input(student_id: str, prompt_text: str):
    """Process user prompt and refresh the chat stream."""
    if not prompt_text or not prompt_text.strip():
        return

    with st.spinner("StudyCrafter agents thinking..."):
        process_student_message(student_id=student_id, message=prompt_text.strip())
    st.rerun()
