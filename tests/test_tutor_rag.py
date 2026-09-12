from backend import context_builder
from backend.agents import tutor_agent
from prompts.tutor_prompt import build_context_message


def test_build_context_preserves_retrieved_rag_chunks(monkeypatch):
    monkeypatch.setattr(
        context_builder.StateManager,
        "get_student_summary",
        staticmethod(lambda student_id: {"current_topic": "Averages", "weak_topics": []}),
    )
    monkeypatch.setattr(
        context_builder.StateManager,
        "get_mastery",
        staticmethod(lambda student_id, topic: 40),
    )
    monkeypatch.setattr(
        context_builder.StateManager,
        "get_recent_mistakes",
        staticmethod(lambda student_id, topic, limit: []),
    )
    monkeypatch.setattr(
        context_builder,
        "retrieve_aptitude_knowledge_tool",
        lambda topic, query, k: [
            {
                "text": "Weighted Average = total weighted value / total weight.",
                "metadata": {"source": "averages.txt", "topic": "averages"},
            }
        ],
    )

    result = context_builder.build_context("student-1", topic="Averages", query="weighted average")

    assert result["rag_chunks"] == [
        {
            "text": "Weighted Average = total weighted value / total weight.",
            "source": "averages.txt",
            "topic": "averages",
        }
    ]


def test_run_tutor_passes_rag_chunks_to_tutor(monkeypatch):
    captured = {}

    monkeypatch.setattr(
        tutor_agent,
        "build_context",
        lambda student_id, topic, query: {
            "mastery": 40,
            "goal": "Aptitude preparation",
            "days_remaining": 7,
            "daily_study_minutes": 60,
            "previous_mistakes": [],
            "rag_chunks": [
                {
                    "text": "Average = Sum / Count.",
                    "source": "averages.txt",
                    "topic": "averages",
                }
            ],
        },
    )
    monkeypatch.setattr(tutor_agent.StateManager, "get_chat_history", staticmethod(lambda student_id: []))
    monkeypatch.setattr(tutor_agent.StateManager, "update_profile", staticmethod(lambda *args, **kwargs: None))

    class FakeTutor:
        def generate_response(self, student_context, chat_history, user_message):
            captured["student_context"] = student_context
            return "grounded answer"

    monkeypatch.setattr(tutor_agent, "_get_tutor", lambda: FakeTutor())

    result = tutor_agent.run_tutor("student-1", "Averages", "Explain the average formula")

    assert result["response"] == "grounded answer"
    assert captured["student_context"]["rag_chunks"][0]["text"] == "Average = Sum / Count."


def test_prompt_contains_retrieved_knowledge_when_available():
    prompt = build_context_message(
        {
            "current_topic": "Averages",
            "current_level": "Beginner",
            "rag_chunks": [
                {
                    "text": "Weighted Average = (w1*x1 + w2*x2) / (w1 + w2).",
                    "source": "averages.txt",
                    "section": "concept",
                }
            ],
        }
    )

    assert "RETRIEVED STUDYCRAFTER KNOWLEDGE" in prompt
    assert "Weighted Average" in prompt
    assert "Prefer its formulas, concepts, and examples" in prompt
    assert "Never mention internal retrieval" not in prompt


def test_prompt_remains_valid_without_rag_chunks():
    prompt = build_context_message({"current_topic": "Averages", "rag_chunks": []})

    assert "CURRENT STUDENT PROFILE" in prompt
    assert "Averages" in prompt
    assert "RETRIEVED STUDYCRAFTER KNOWLEDGE" not in prompt
