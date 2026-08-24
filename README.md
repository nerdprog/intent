# StudyCrafter — Phase 1

**StudyCrafter** is an Agentic AI-based personalized aptitude learning system. Phase 1 is a Streamlit chatbot that demonstrates basic agentic tutoring behavior — the AI understands student intent, decides what kind of help to provide, and responds accordingly.

## Features

- **Personalized tutoring** — adapts explanations to the student's level (Beginner / Intermediate / Advanced)
- **Context-aware responses** — uses goal, days remaining, and daily study hours when teaching
- **Agentic decision-making** — internally decides whether to teach, explain, give examples, practice, assess, or revise
- **13 aptitude topics** — Number System, Percentages, Probability, Time and Work, and more
- **Session memory** — remembers the full conversation within a session
- **Clean Streamlit UI** — sidebar profile, context card, and chat interface

## Technologies

- Python 3.10+
- Streamlit
- LLM API — **Groq** (free, default), **Google Gemini** (free), or OpenAI (paid)
- python-dotenv

## Project Structure

```
StudyCrafter/
├── app.py                  # Main Streamlit application
├── requirements.txt        # Python dependencies
├── .env.example            # Environment variable template
├── README.md
├── agents/
│   └── tutor_agent.py      # LLM interaction and response generation
├── prompts/
│   └── tutor_prompt.py     # System prompt and context builders
└── utils/
    ├── session_state.py    # Session state initialization and helpers
    └── llm_config.py       # LLM provider settings
```

## Installation

1. **Clone or download** this project and open a terminal in the project folder.

2. **Create a virtual environment** (recommended):

   ```bash
   python -m venv venv

   # Windows
   venv\Scripts\activate

   # macOS / Linux
   source venv/bin/activate
   ```

3. **Install dependencies**:

   ```bash
   pip install -r requirements.txt
   ```

4. **Set up your free API key** (no payment method required):

   ```bash
   # Copy the example file
   copy .env.example .env        # Windows
   cp .env.example .env          # macOS / Linux
   ```

   Open `.env` and configure a **free** provider:

   ### Option A — Groq (recommended, free)

   1. Sign up at [console.groq.com/keys](https://console.groq.com/keys)
   2. Create an API key (no credit card needed)
   3. Set in `.env`:

   ```
   LLM_PROVIDER=groq
   GROQ_API_KEY=gsk_your_actual_groq_key_here
   ```

   ### Option B — Google Gemini (free)

   1. Get a key at [aistudio.google.com/apikey](https://aistudio.google.com/apikey)
   2. Set in `.env`:

   ```
   LLM_PROVIDER=gemini
   GEMINI_API_KEY=your_gemini_key_here
   ```

   ### Option C — OpenAI (requires billing)

   Only use this if you have OpenAI credits:

   ```
   LLM_PROVIDER=openai
   OPENAI_API_KEY=sk-your-actual-key-here
   ```

## How to Run

```bash
python -m streamlit run app.py
```

If `streamlit` is on your PATH, you can also use:

```bash
streamlit run app.py
```

The app opens in your browser (usually at `http://localhost:8501`).

**Windows note:** If you see `'streamlit' is not recognized`, use `python -m streamlit run app.py` instead — Streamlit is installed, but its Scripts folder may not be on your PATH.

## Usage

1. Fill in your **Student Profile** in the sidebar (name, goal, days remaining, daily hours, level).
2. Type a message in the chat input at the bottom.
3. The AI tutor responds based on your profile and conversation history.
4. Use **Clear Chat** in the sidebar to start a new conversation without losing your profile.

## Example Conversations

### Setting up context

**Student:** I have 10 days left for my placement aptitude test. I can study 2 hours per day.

**Agent:** Acknowledges the goal and preparation timeline, may suggest a focused approach given limited time.

### Learning a weak topic

**Student:** I am weak in probability. Teach me.

**Agent:** Provides a beginner-friendly probability explanation with concept, example, and key point — adapted to the student's level and available time.

### Practice

**Student:** Give me a question.

**Agent:** Generates an aptitude question at the appropriate difficulty with options (if MCQ).

### Answer evaluation

**Student:** My answer is B.

**Agent:** Evaluates the answer, explains if incorrect, and continues the learning flow.

### Increasing difficulty

**Student:** Give me a harder question.

**Agent:** Increases difficulty based on the student's level and prior performance in the conversation.

## Supported Aptitude Topics

- Number System
- Percentages
- Profit and Loss
- Ratio and Proportion
- Averages
- Time and Work
- Time, Speed and Distance
- Simple Interest
- Compound Interest
- Probability
- Permutation and Combination
- Logical Reasoning
- Verbal Ability

## Phase 1 Scope

This phase demonstrates:

```
USER → AGENT UNDERSTANDS INTENT → AGENT DECIDES ACTION → LLM GENERATES RESPONSE → STUDENT CONTINUES
```

**Not included in Phase 1:** diagnostic tests, mastery tracking, databases, RAG, LangGraph, study-plan generation, authentication, or deployment. These are planned for later phases.

## Troubleshooting

| Issue | Solution |
|-------|----------|
| "API key not found" | Create `.env` with `LLM_PROVIDER=groq` and `GROQ_API_KEY=...` |
| OpenAI "insufficient_quota" | Switch to free Groq or Gemini in `.env` — no payment needed |
| `'streamlit' is not recognized` | Use `python -m streamlit run app.py` |
| Empty response | Ensure your message is not blank |
| Rate limit | Wait a minute and try again (free tiers have limits) |

## License

For educational and demonstration purposes.
