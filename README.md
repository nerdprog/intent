# StudyCrafter

StudyCrafter is a Streamlit-based aptitude tutor that helps students prepare for placement and competitive exams through a local Python backend, agent routing, RAG knowledge retrieval, diagnostic assessment, practice questions, adaptive planning, and SQLite persistence.

## Streamlit workflow

```text
Student
  -> Streamlit UI
  -> Python backend / orchestrator
  -> Understand Agent
  -> Supervisor Agent
  -> Tutor / Assessment / Diagnostic Agents
  -> Knowledge base, question bank, evaluation, progression logic
  -> SQLite student state
  -> Streamlit UI
```

The app runs from the project root with:

```bash
streamlit run app.py
```

## Key capabilities

- Natural-language aptitude chat
- Understand and supervisor routing
- Tutor responses grounded in the local aptitude knowledge base
- Practice question generation and MCQ submission
- Deterministic grading and mastery updates
- Diagnostic assessment flow
- Adaptive study plan and replanning
- Per-student SQLite state and chat history

## Optional n8n integration

n8n is optional and not required for the default Streamlit workflow.

- `USE_N8N=false` by default
- The local orchestrator in `backend/orchestrator.py` handles the full learning flow without n8n
- `backend/n8n_client.py` sends to n8n only when `USE_N8N=true`, and falls back to the local Python workflow if the webhook is unavailable

If you want to enable the n8n webhook, import the workflow from `n8n/studycrafter_aptitude_workflow.json`, set:

```ini
USE_N8N=true
N8N_WEBHOOK_URL=http://localhost:5678/webhook/studycrafter
```

and restart Streamlit.

## Project structure

```text
studycrafter/
├── app.py
├── frontend/                 # Streamlit UI components
├── backend/
│   ├── agents/               # Understand, Supervisor, Tutor, Assessment, Diagnostic, Progress, Replanner
│   ├── rag/                  # Knowledge retrieval against aptitude files
│   ├── skills/               # Reusable aptitude lesson and plan playbooks
│   ├── tools/                # Knowledge, assessment, evaluation, state helpers
│   ├── models/               # Shared schemas
│   ├── api.py                # Streamlit-facing backend API
│   ├── orchestrator.py       # Local agent orchestration
│   ├── n8n_client.py        # Optional n8n bridge with local fallback
│   └── state.py             # SQLite persistence and student state management
├── data/aptitude_knowledge/  # Local aptitude knowledge base
├── prompts/                  # Tutor prompt and context templates
├── utils/                    # LLM config helpers
├── agents/                   # LLM provider wrapper used by the tutor backend
├── n8n/                      # Optional workflow export
├── .env.example              # Environment variable template
├── requirements.txt          # Python dependencies for the Streamlit app
├── studycrafter.db          # SQLite student data store
└── README.md
```

## Quick start

```bash
pip install -r requirements.txt
copy .env.example .env
streamlit run app.py
```

Open the local Streamlit app at `http://localhost:8501`.

## Notes

- The application is intentionally Streamlit-only.
- The modern browser frontend and dedicated web server were removed because the active app runs through Streamlit and the local Python backend.
- The local aptitude knowledge files remain in `data/aptitude_knowledge` and are used by the tutor and assessment system.
- The SQLite database is the persistent student state store used by the app.
