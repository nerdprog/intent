"""
StudyCrafter — Custom CSS & UI Layout Enhancements
"""

import streamlit as st


def apply_custom_styles():
    """Inject modern glassmorphism CSS styles for an educational product look."""
    st.markdown("""
        <style>
        /* Base typography & colors */
        @import url('https://fonts.googleapis.com/css2?family=Outfit:wght@400;500;600;700&family=Inter:wght@400;500;600&family=JetBrains+Mono:wght@400;600&display=swap');

        html, body, [class*="css"] {
            font-family: 'Inter', sans-serif;
        }

        h1, h2, h3, h4, h5, h6 {
            font-family: 'Outfit', sans-serif;
            letter-spacing: -0.01em;
        }

        /* Sidebar — match the light main screen so labels stay readable */
        [data-testid="stSidebar"] {
            background-color: #f8fafc;
            border-right: 1px solid #e2e8f0;
        }

        [data-testid="stSidebar"] > div:first-child {
            background-color: #f8fafc;
        }

        [data-testid="stSidebar"] h1,
        [data-testid="stSidebar"] h2,
        [data-testid="stSidebar"] h3,
        [data-testid="stSidebar"] p,
        [data-testid="stSidebar"] label,
        [data-testid="stSidebar"] span,
        [data-testid="stSidebar"] .stMarkdown,
        [data-testid="stSidebar"] [data-testid="stCaption"] {
            color: #0f172a !important;
        }

        [data-testid="stSidebar"] [data-testid="stCaption"] {
            color: #475569 !important;
        }

        [data-testid="stSidebar"] [data-testid="stVerticalBlockBorderWrapper"] {
            background-color: #ffffff;
            border: 1px solid #e2e8f0 !important;
            border-radius: 12px;
        }

        /* Custom Header Badge */
        .brand-header-box {
            background: linear-gradient(135deg, rgba(99, 102, 241, 0.12) 0%, rgba(168, 85, 247, 0.08) 100%);
            border: 1px solid rgba(99, 102, 241, 0.3);
            border-radius: 12px;
            padding: 14px 18px;
            margin-bottom: 20px;
            display: flex;
            align-items: center;
            justify-content: space-between;
        }

        .brand-title {
            font-size: 22px;
            font-weight: 700;
            color: #ffffff;
            margin: 0;
            display: flex;
            align-items: center;
            gap: 10px;
        }

        .brand-subtitle {
            font-size: 13px;
            color: #94a3b8;
            margin: 2px 0 0 0;
        }

        .hud-badge {
            background: rgba(99, 102, 241, 0.2);
            border: 1px solid rgba(99, 102, 241, 0.4);
            color: #818cf8;
            font-size: 11px;
            font-weight: 600;
            padding: 4px 10px;
            border-radius: 9999px;
            text-transform: uppercase;
            letter-spacing: 0.04em;
        }

        /* Topic Mastery Progress Cards */
        .mastery-card {
            background: #ffffff;
            border: 1px solid #e2e8f0;
            border-radius: 8px;
            padding: 10px 12px;
            margin-bottom: 8px;
        }

        .mastery-header {
            display: flex;
            justify-content: space-between;
            font-size: 13px;
            font-weight: 600;
            color: #0f172a;
            margin-bottom: 4px;
        }

        .tag-weak { color: #e11d48 !important; font-weight: 700; }
        .tag-dev { color: #d97706 !important; font-weight: 700; }
        .tag-strong { color: #059669 !important; font-weight: 700; }

        /* MCQ Card Styling */
        .question-card-box {
            background: linear-gradient(135deg, rgba(26, 33, 56, 0.95) 0%, rgba(16, 21, 38, 0.98) 100%);
            border: 1px solid rgba(99, 102, 241, 0.4);
            border-radius: 14px;
            padding: 20px;
            margin: 15px 0;
            box-shadow: 0 8px 30px rgba(0, 0, 0, 0.4);
        }

        .question-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 12px;
        }

        .question-badge {
            background: rgba(99, 102, 241, 0.25);
            border: 1px solid rgba(99, 102, 241, 0.5);
            color: #c7d2fe;
            padding: 3px 10px;
            border-radius: 9999px;
            font-size: 11px;
            font-weight: 700;
        }

        .difficulty-badge {
            font-size: 11px;
            font-weight: 600;
            padding: 2px 8px;
            border-radius: 9999px;
            background: rgba(245, 158, 11, 0.2);
            color: #fbbf24;
        }

        .question-text {
            font-size: 16px;
            font-weight: 500;
            color: #ffffff;
            line-height: 1.5;
            margin-bottom: 16px;
        }

        /* Buttons Styling */
        div.stButton > button {
            border-radius: 8px;
            font-weight: 600;
            transition: all 0.2s ease;
        }

        /* Chat input floating effect */
        [data-testid="stChatInput"] {
            border-radius: 12px;
        }
        </style>
    """, unsafe_allow_html=True)


def render_header():
    """Render the application header with status badges."""
    st.markdown("""
        <div class="brand-header-box">
            <div>
                <h1 class="brand-title">🎓 StudyCrafter</h1>
                <p class="brand-subtitle">Your AI Aptitude Tutor</p>
            </div>
            <div>
                <span class="hud-badge">⚡ Autonomous Agents</span>
            </div>
        </div>
    """, unsafe_allow_html=True)
