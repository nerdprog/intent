"""
StudyCrafter — Sidebar dashboard (Aptitude progress only).
"""

import streamlit as st
from backend.api import clear_student_chat, get_student_state


def _status_tag(score: int, assessed: bool) -> str:
    if not assessed:
        return "Not assessed"
    if score < 50:
        return "Weak"
    if score < 80:
        return "Developing"
    return "Strong"


def render_sidebar(student_id: str, on_quick_action=None):
    with st.sidebar:
        st.markdown("### Aptitude Progress")
        state = get_student_state(student_id)
        assessed = bool(state.get("questions_attempted") or state.get("diagnosed"))
        goal = state.get("goal") or "Not set yet"
        days = state.get("days_remaining")
        daily_mins = state.get("daily_study_minutes")
        overall = state.get("overall_mastery", 0)
        status = state.get("status", "Not assessed")
        current_topic = state.get("current_topic") or "—"
        attempted = state.get("questions_attempted") or 0
        accuracy = state.get("accuracy") or 0
        weak = state.get("weak_topics") or []
        plan = state.get("study_plan") or {}

        with st.container(border=True):
            st.markdown(f"**Goal:** {goal}")
            st.markdown(f"**Days remaining:** {days if days is not None else '—'}")
            if daily_mins:
                st.markdown(f"**Daily study time:** `{daily_mins // 60}h {daily_mins % 60}m`")
            else:
                st.markdown("**Daily study time:** —")
            st.markdown(f"**Active topic:** `{current_topic}`")

        st.divider()
        st.markdown("### Overall")
        st.progress(min(max(overall, 0), 100) / 100)
        st.markdown(f"**Score:** `{overall}%` · **Status:** {status}")
        st.markdown(f"**Questions:** {state.get('questions_correct', 0)}/{attempted} · **Accuracy:** {accuracy}%")

        st.divider()
        st.markdown("### Topics")
        masteries = state.get("mastery") or {}
        icons = {
            "Percentages": "📊",
            "Ratio and Proportion": "⚖️",
            "Averages": "📈",
            "Time and Work": "⏱️",
            "Time Speed and Distance": "🚀",
            "Profit and Loss": "💰",
            "Probability": "🎲",
        }
        for topic, score in masteries.items():
            tag = _status_tag(score, assessed)
            tag_class = "tag-weak" if score < 50 else ("tag-dev" if score < 80 else "tag-strong")
            if not assessed:
                tag_class = "tag-dev"
            col_t1, col_t2 = st.columns([3, 1])
            with col_t1:
                st.caption(f"{icons.get(topic, '📚')} **{topic}** · {tag}")
            with col_t2:
                st.markdown(
                    f"<div style='text-align: right;'><span class='{tag_class}'>{score}%</span></div>",
                    unsafe_allow_html=True,
                )
            st.progress(min(max(int(score), 0), 100) / 100)

        if weak and assessed:
            st.caption("Weak topics: " + ", ".join(weak))

        if plan.get("now") or plan.get("priority_topics"):
            st.divider()
            st.markdown("### Live study plan")
            now = plan.get("now") or {}
            nxt = plan.get("next") or {}
            if now.get("topic"):
                st.markdown(
                    f"**Now:** `{now['topic']}` · {now.get('mastery', 0)}% · {now.get('activity', '')}"
                )
            if nxt.get("topic") and nxt.get("topic") != now.get("topic"):
                st.markdown(f"**Next:** `{nxt['topic']}` · {nxt.get('mastery', 0)}%")
            later = plan.get("later") or []
            if later:
                st.caption("Later: " + ", ".join(later))
            st.caption("Updates after each scored answer (weakest topics first).")
            for row in (plan.get("schedule") or [])[:5]:
                st.caption(
                    f"Day {row.get('day')}: {row.get('focus')} "
                    f"({row.get('mastery', 0)}%) — {row.get('activity')}"
                )

        st.divider()
        st.markdown("### Actions")
        if st.button("Short diagnostic", use_container_width=True):
            if on_quick_action:
                on_quick_action("I want to take a diagnostic assessment")
        if st.button("Show my progress", use_container_width=True):
            if on_quick_action:
                on_quick_action("Show my aptitude progress")
        if st.button("Clear conversation", use_container_width=True):
            clear_student_chat(student_id)
            st.rerun()
