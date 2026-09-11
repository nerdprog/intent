# StudyCrafter — Multi-Agent Aptitude Tutor & RAG API

StudyCrafter is an AI-powered aptitude preparation tutor designed for college placement exams. It combines multi-agent routing (Understand → Supervisor → Act agents), deterministic assessment grading, SQLite state persistence, and a public HTTPS RAG API for semantic knowledge retrieval from curated topic documents.

---

## 1. RAG Architecture

```
Student / Streamlit
        ↓
    n8n Cloud
        ↓
Intake & Intent Agent → Validate & Route → Tutor Agent
                                              ↓ (HTTPS)
                                       Python RAG API
                                              ↓
                                         Vector Store
                                              ↓
                                Knowledge Base (/data/*.txt)
                                              ↓
                                       Retrieved Context
                                              ↓
                                        Gemini 3 Flash
                                              ↓
                                           Response
```

The RAG API acts as a secure, deployment-ready bridge between your aptitude knowledge base (`/data/*.txt`) and n8n Cloud / LLM agents.

---

## 2. Project Structure

```
Studycrafter/
├── backend/
│   ├── agents/            # Understand, Supervisor, Tutor, Diagnostic, Progress, Replanner agents
│   ├── models/            # Schemas & data structures
│   ├── rag/
│   │   ├── ingestion.py   # Automatic discovery, section chunking & vector store rebuilder
│   │   ├── vector_store.py# Persistent vector store (ChromaDB + TF-IDF fallback)
│   │   └── retrieval.py   # RAG retrieval interface
│   ├── api.py             # Streamlit backend gateway
│   ├── orchestrator.py    # Local multi-agent routing & deterministic evaluation
│   ├── state.py           # SQLite database persistence
│   └── rag_api.py         # FastAPI production web service (GET /health, POST /rag/retrieve)
├── data/
│   ├── aptitude_knowledge/ # Curated .txt knowledge files (averages, percentages, etc.)
│   └── vector_store/       # Persistent vector index storage
├── frontend/              # Streamlit UI & chat interface
├── tests/                 # Comprehensive pytest suite (test_rag.py)
├── app.py                 # Streamlit main entrypoint
├── render.yaml            # Render cloud deployment specification
└── requirements.txt       # Python dependencies
```

---

## 3. Required Dependencies

- **FastAPI** (`fastapi`): Web framework for RAG HTTP API
- **Uvicorn** (`uvicorn`): ASGI server for production deployment
- **Pydantic** (`pydantic`): Request/response schema validation
- **Scikit-Learn & Numpy** (`scikit-learn`, `numpy`): Vector similarity & TF-IDF embeddings
- **Streamlit** (`streamlit`): Frontend user interface
- **Python-Dotenv** (`python-dotenv`): Environment variable management

---

## 4. Installation Commands

```bash
# 1. Clone workspace / navigate to project root
cd Studycrafter

# 2. Create and activate virtual environment (optional)
python -m venv .venv
source .venv/bin/activate        # Linux/macOS
.venv\Scripts\activate           # Windows

# 3. Install dependencies
pip install -r requirements.txt
```

---

## 5. Environment Variables

Create a `.env` file in the project root:

```env
PORT=8000
VECTOR_STORE_PATH=./data/vector_store
GEMINI_API_KEY=your_gemini_api_key_here
GROQ_API_KEY=your_groq_api_key_here
OPENAI_API_KEY=your_openai_api_key_here
```

---

## 6. How to Build / Rebuild the Vector Index

Run the ingestion CLI command to automatically discover all `.txt` files in `/data`, split them into section-tagged chunks, compute embeddings, and save the persistent vector store:

```bash
python -m backend.rag.ingestion
```

---

## 7. How to Start the API Locally

```bash
uvicorn backend.rag_api:app --host 0.0.0.0 --port 8000 --reload
```

---

## 8. How to Test `/health`

```bash
curl http://localhost:8000/health
```

Expected Output:
```json
{
  "status": "ok",
  "vector_store": "available"
}
```

---

## 9. How to Test `/rag/retrieve`

```bash
curl -X POST "http://localhost:8000/rag/retrieve" \
     -H "Content-Type: application/json" \
     -d '{
       "query": "Explain the average formula",
       "topic": "Averages",
       "top_k": 5
     }'
```

---

## 10. Example Request

```json
{
  "query": "What is the formula for probability?",
  "topic": "Probability",
  "top_k": 3
}
```

---

## 11. Example Response

```json
{
  "ok": true,
  "topic": "Probability",
  "results": [
    {
      "content": "Concept: Probability measures the likelihood of an event occurring...\nFormula: P(E) = Number of favorable outcomes / Total number of possible outcomes.",
      "source": "data/aptitude_knowledge/probability.txt",
      "section": "concept",
      "score": 0.9542
    }
  ]
}
```

---

## 12. How to Deploy the API to Render

1. Push your code repository to GitHub (`git push origin main`).
2. Log into [Render Dashboard](https://dashboard.render.com/).
3. Click **New +** → **Web Service**.
4. Connect your GitHub repository `MNivetha1/Studycrafter`.
5. Render will automatically detect `render.yaml`.
   - **Build Command**: `pip install -r requirements.txt && python -m backend.rag.ingestion`
   - **Start Command**: `uvicorn backend.rag_api:app --host 0.0.0.0 --port $PORT`
6. Click **Deploy Web Service**.

---

## 13. How to Obtain the Public HTTPS API URL

Once deployed, Render provides a public HTTPS web service URL, for example:
`https://studycrafter-rag-api.onrender.com`

Verify deployment by opening:
`https://studycrafter-rag-api.onrender.com/health`

---

## 14. What URL Should Be Entered into n8n Cloud

In your n8n Cloud workflow, update the RAG HTTP Request node URL to:
`https://studycrafter-rag-api.onrender.com/rag/retrieve`

---

## 15. How to Rebuild the RAG Index After Changing `/data/*.txt`

Whenever you add or modify `.txt` files in `/data`:
1. Locally: Run `python -m backend.rag.ingestion`
2. On Render: Manually trigger **Clear build cache & deploy** in Render Dashboard, or call `rebuild_vector_index()` via an administrative script.

---

## 16. Persistent-Storage Requirements for the Vector Database

The vector database is saved in `./data/vector_store`. On cloud platforms like Render:
- The build command automatically runs `python -m backend.rag.ingestion` during build time, pre-generating the vector store into `./data/vector_store`.
- If using Render persistent disks, set `VECTOR_STORE_PATH=/var/data/vector_store` to persist vector updates across container restarts.

---

## Running Test Suite

Run pytest to verify all RAG components:

```bash
python -m pytest
```
