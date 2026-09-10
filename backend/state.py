"""
StudyCrafter — Persistent Student State & Database Management (SQLite)
Manages student profiles, topic masteries, active questions, and chat history.
"""

import json
import sqlite3
import uuid
from pathlib import Path
from typing import Any, Dict, List, Optional

DB_PATH = Path(__file__).resolve().parent.parent / "studycrafter.db"

CORE_TOPICS = [
    "Percentages",
    "Ratio and Proportion",
    "Averages",
    "Time and Work",
    "Time Speed and Distance",
    "Profit and Loss",
    "Probability",
]

# Unmeasured until the student is diagnosed or answers questions.
DEFAULT_MASTERIES = {topic: 0 for topic in CORE_TOPICS}


def get_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(str(DB_PATH), timeout=15)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    """Initialize database tables if they do not exist."""
    with get_connection() as conn:
        cursor = conn.cursor()

        # Students Table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS students (
                student_id TEXT PRIMARY KEY,
                goal TEXT,
                days_remaining INTEGER,
                daily_study_minutes INTEGER,
                current_topic TEXT DEFAULT 'Probability',
                questions_attempted INTEGER DEFAULT 0,
                questions_correct INTEGER DEFAULT 0,
                last_action TEXT DEFAULT 'NEW',
                phase TEXT DEFAULT 'NEW',
                last_intent TEXT,
                diagnosed INTEGER DEFAULT 0,
                understand_json TEXT,
                study_plan_json TEXT,
                diagnostic_queue_json TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Topic Mastery Table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS topic_mastery (
                student_id TEXT,
                topic TEXT,
                mastery INTEGER DEFAULT 40,
                PRIMARY KEY (student_id, topic)
            )
        """)

        # Active Questions Table (Stores question + correct answer internally)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS active_questions (
                student_id TEXT PRIMARY KEY,
                question_id TEXT,
                question_text TEXT,
                options_json TEXT,
                correct_answer TEXT,
                topic TEXT,
                difficulty TEXT,
                is_answered INTEGER DEFAULT 0,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Chat History Table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS chat_messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                student_id TEXT,
                role TEXT,
                content TEXT,
                action TEXT,
                topic TEXT,
                question_id TEXT,
                is_graded INTEGER DEFAULT 0,
                is_correct INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS mistakes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                student_id TEXT,
                topic TEXT,
                question_text TEXT,
                student_answer TEXT,
                correct_answer TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        conn.commit()
        _migrate_student_columns(cursor)
        conn.commit()


def _migrate_student_columns(cursor) -> None:
    cursor.execute("PRAGMA table_info(students)")
    existing = {row[1] for row in cursor.fetchall()}
    extras = {
        "phase": "TEXT DEFAULT 'NEW'",
        "last_intent": "TEXT",
        "diagnosed": "INTEGER DEFAULT 0",
        "understand_json": "TEXT",
        "study_plan_json": "TEXT",
        "diagnostic_queue_json": "TEXT",
    }
    for name, ddl in extras.items():
        if name not in existing:
            cursor.execute(f"ALTER TABLE students ADD COLUMN {name} {ddl}")


# Initialize database on module import
init_db()


class StateManager:
    """High-level interface for querying and persisting student state."""

    @staticmethod
    def get_or_create_student(student_id: Optional[str] = None) -> Dict[str, Any]:
        """Fetch an existing student or create a new one with default masteries."""
        if not student_id:
            student_id = f"student_{uuid.uuid4().hex[:8]}"

        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM students WHERE student_id = ?", (student_id,))
            row = cursor.fetchone()

            if not row:
                cursor.execute("""
                    INSERT INTO students (student_id, current_topic, questions_attempted, questions_correct, last_action, phase)
                    VALUES (?, NULL, 0, 0, 'NEW', 'NEW')
                """, (student_id,))

                # Initialize default masteries
                for topic, default_val in DEFAULT_MASTERIES.items():
                    cursor.execute("""
                        INSERT OR IGNORE INTO topic_mastery (student_id, topic, mastery)
                        VALUES (?, ?, ?)
                    """, (student_id, topic, default_val))
                conn.commit()

                return StateManager.get_student_summary(student_id)

            return StateManager.get_student_summary(student_id)

    @staticmethod
    def update_profile(
        student_id: str,
        goal: Optional[str] = None,
        days_remaining: Optional[int] = None,
        daily_study_minutes: Optional[int] = None,
        current_topic: Optional[str] = None,
        last_action: Optional[str] = None,
        phase: Optional[str] = None,
        last_intent: Optional[str] = None,
        diagnosed: Optional[int] = None,
        understand_json: Optional[str] = None,
        study_plan_json: Optional[str] = None,
        diagnostic_queue_json: Optional[str] = None,
    ):
        """Update student profile fields."""
        with get_connection() as conn:
            cursor = conn.cursor()
            updates = []
            params = []

            if goal is not None:
                updates.append("goal = ?")
                params.append(goal)
            if days_remaining is not None:
                updates.append("days_remaining = ?")
                params.append(days_remaining)
            if daily_study_minutes is not None:
                updates.append("daily_study_minutes = ?")
                params.append(daily_study_minutes)
            if current_topic is not None:
                updates.append("current_topic = ?")
                params.append(current_topic)
            if last_action is not None:
                updates.append("last_action = ?")
                params.append(last_action)
            if phase is not None:
                updates.append("phase = ?")
                params.append(phase)
            if last_intent is not None:
                updates.append("last_intent = ?")
                params.append(last_intent)
            if diagnosed is not None:
                updates.append("diagnosed = ?")
                params.append(int(diagnosed))
            if understand_json is not None:
                updates.append("understand_json = ?")
                params.append(understand_json)
            if study_plan_json is not None:
                updates.append("study_plan_json = ?")
                params.append(study_plan_json)
            if diagnostic_queue_json is not None:
                updates.append("diagnostic_queue_json = ?")
                params.append(diagnostic_queue_json)

            if updates:
                updates.append("updated_at = CURRENT_TIMESTAMP")
                params.append(student_id)
                query = f"UPDATE students SET {', '.join(updates)} WHERE student_id = ?"
                cursor.execute(query, params)
                conn.commit()

    @staticmethod
    def get_topic_masteries(student_id: str) -> Dict[str, int]:
        """Get dictionary of all topic masteries for a student."""
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT topic, mastery FROM topic_mastery WHERE student_id = ?", (student_id,))
            rows = cursor.fetchall()
            masteries = {r["topic"]: r["mastery"] for r in rows}

            # Ensure all core topics are present
            for topic in CORE_TOPICS:
                if topic not in masteries:
                    masteries[topic] = DEFAULT_MASTERIES.get(topic, 40)
            return masteries

    @staticmethod
    def get_mastery(student_id: str, topic: Optional[str] = None) -> int:
        """Get mastery for a specific topic (defaults to current topic or 40)."""
        if not topic:
            student = StateManager.get_student_summary(student_id)
            topic = student.get("current_topic") or "Probability"

        masteries = StateManager.get_topic_masteries(student_id)
        # Fuzzy search
        for k, v in masteries.items():
            if k.lower() == topic.lower() or topic.lower() in k.lower():
                return v
        return 0

    @staticmethod
    def update_mastery(student_id: str, topic: str, new_mastery: int):
        """Update mastery percentage for a specific topic (clamped 0-100)."""
        clamped = max(0, min(100, int(new_mastery)))
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO topic_mastery (student_id, topic, mastery)
                VALUES (?, ?, ?)
                ON CONFLICT(student_id, topic) DO UPDATE SET mastery = ?
            """, (student_id, topic, clamped, clamped))
            conn.commit()

    @staticmethod
    def apply_mastery_delta(student_id: str, topic: str, delta: int) -> int:
        """Apply a positive or negative score delta to topic mastery."""
        current = StateManager.get_mastery(student_id, topic)
        new_val = max(0, min(100, current + delta))
        StateManager.update_mastery(student_id, topic, new_val)
        return new_val

    @staticmethod
    def set_active_question(student_id: str, question_obj: Dict[str, Any]):
        """Store the active MCQ question with its correct answer internally."""
        q_id = question_obj.get("id") or f"q_{uuid.uuid4().hex[:6]}"
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO active_questions (
                    student_id, question_id, question_text, options_json, correct_answer, topic, difficulty, is_answered
                ) VALUES (?, ?, ?, ?, ?, ?, ?, 0)
                ON CONFLICT(student_id) DO UPDATE SET
                    question_id = ?,
                    question_text = ?,
                    options_json = ?,
                    correct_answer = ?,
                    topic = ?,
                    difficulty = ?,
                    is_answered = 0,
                    updated_at = CURRENT_TIMESTAMP
            """, (
                student_id,
                q_id,
                question_obj.get("question") or question_obj.get("text", ""),
                json.dumps(question_obj.get("options", {})),
                (question_obj.get("correct_answer") or "B").strip().upper(),
                question_obj.get("topic") or "Probability",
                question_obj.get("difficulty") or "Medium",
                q_id,
                question_obj.get("question") or question_obj.get("text", ""),
                json.dumps(question_obj.get("options", {})),
                (question_obj.get("correct_answer") or "B").strip().upper(),
                question_obj.get("topic") or "Probability",
                question_obj.get("difficulty") or "Medium",
            ))
            conn.commit()

    @staticmethod
    def get_active_question(student_id: str) -> Optional[Dict[str, Any]]:
        """Get the active pending question for this student."""
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT * FROM active_questions 
                WHERE student_id = ? AND is_answered = 0
            """, (student_id,))
            row = cursor.fetchone()
            if not row:
                return None

            options = {}
            try:
                options = json.loads(row["options_json"])
            except Exception:
                pass

            return {
                "id": row["question_id"],
                "question": row["question_text"],
                "options": options,
                "correct_answer": row["correct_answer"],
                "topic": row["topic"],
                "difficulty": row["difficulty"],
            }

    @staticmethod
    def mark_question_answered(student_id: str, is_correct: bool):
        """Mark active question as answered and update student stats."""
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("UPDATE active_questions SET is_answered = 1 WHERE student_id = ?", (student_id,))
            if is_correct:
                cursor.execute("""
                    UPDATE students 
                    SET questions_attempted = questions_attempted + 1,
                        questions_correct = questions_correct + 1
                    WHERE student_id = ?
                """, (student_id,))
            else:
                cursor.execute("""
                    UPDATE students 
                    SET questions_attempted = questions_attempted + 1
                    WHERE student_id = ?
                """, (student_id,))
            conn.commit()

    @staticmethod
    def clear_active_question(student_id: str):
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM active_questions WHERE student_id = ?", (student_id,))
            conn.commit()

    @staticmethod
    def add_chat_message(
        student_id: str,
        role: str,
        content: str,
        action: Optional[str] = None,
        topic: Optional[str] = None,
        question_id: Optional[str] = None,
        is_graded: int = 0,
        is_correct: Optional[int] = None,
    ):
        """Add a chat message to persistent history."""
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO chat_messages (
                    student_id, role, content, action, topic, question_id, is_graded, is_correct
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (student_id, role, content, action, topic, question_id, is_graded, is_correct))
            conn.commit()

    @staticmethod
    def get_chat_history(student_id: str) -> List[Dict[str, Any]]:
        """Retrieve full chat history for a student."""
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT * FROM chat_messages 
                WHERE student_id = ? 
                ORDER BY id ASC
            """, (student_id,))
            rows = cursor.fetchall()
            return [dict(r) for r in rows]

    @staticmethod
    def clear_chat_history(student_id: str):
        """Clear chat messages for a student."""
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM chat_messages WHERE student_id = ?", (student_id,))
            cursor.execute("DELETE FROM active_questions WHERE student_id = ?", (student_id,))
            conn.commit()

    @staticmethod
    def get_served_question_ids(student_id: str) -> List[str]:
        """Retrieve list of distinct question_ids already served to this student."""
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT DISTINCT question_id FROM chat_messages WHERE student_id = ? AND question_id IS NOT NULL",
                (student_id,),
            )
            rows = cursor.fetchall()
            return [r["question_id"] for r in rows if r["question_id"]]

    @staticmethod
    def get_student_summary(student_id: str) -> Dict[str, Any]:
        """Get full summary of student profile, masteries, and overall readiness."""
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM students WHERE student_id = ?", (student_id,))
            row = cursor.fetchone()

            if not row:
                cursor.execute("""
                    INSERT OR IGNORE INTO students (student_id, current_topic, questions_attempted, questions_correct, last_action, phase)
                    VALUES (?, NULL, 0, 0, 'NEW', 'NEW')
                """, (student_id,))
                for topic, default_val in DEFAULT_MASTERIES.items():
                    cursor.execute("""
                        INSERT OR IGNORE INTO topic_mastery (student_id, topic, mastery)
                        VALUES (?, ?, ?)
                    """, (student_id, topic, default_val))
                conn.commit()

                cursor.execute("SELECT * FROM students WHERE student_id = ?", (student_id,))
                row = cursor.fetchone()

            student_data = dict(row) if row else {}
            masteries = StateManager.get_topic_masteries(student_id)
            student_data["mastery"] = masteries
            student_data["domain"] = "aptitude"

            values = list(masteries.values())
            overall = round(sum(values) / len(values)) if values else 0
            student_data["overall_mastery"] = overall

            attempted = student_data.get("questions_attempted") or 0
            correct = student_data.get("questions_correct") or 0
            student_data["accuracy"] = round((correct / attempted) * 100) if attempted else 0

            assessed = attempted > 0 or bool(student_data.get("diagnosed"))
            if not assessed:
                student_data["status"] = "Not assessed"
            elif overall < 50:
                student_data["status"] = "Weak"
            elif overall < 80:
                student_data["status"] = "Developing"
            else:
                student_data["status"] = "Strong"

            weak, developing, strong = [], [], []
            for topic, score in masteries.items():
                if score < 50:
                    weak.append(topic)
                elif score < 80:
                    developing.append(topic)
                else:
                    strong.append(topic)
            student_data["weak_topics"] = weak
            student_data["strong_topics"] = strong
            student_data["completed_topics"] = strong
            student_data["developing_topics"] = developing

            for key in ("understand_json", "study_plan_json", "diagnostic_queue_json"):
                raw = student_data.get(key)
                parsed_key = key.replace("_json", "")
                try:
                    student_data[parsed_key] = json.loads(raw) if raw else None
                except Exception:
                    student_data[parsed_key] = None

            student_data["recent_mistakes"] = StateManager.get_recent_mistakes(student_id, limit=5)
            return student_data

    @staticmethod
    def add_mistake(
        student_id: str,
        topic: str,
        question_text: str,
        student_answer: str,
        correct_answer: str,
    ) -> None:
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO mistakes (student_id, topic, question_text, student_answer, correct_answer)
                VALUES (?, ?, ?, ?, ?)
                """,
                (student_id, topic, question_text, student_answer, correct_answer),
            )
            conn.commit()

    @staticmethod
    def get_recent_mistakes(student_id: str, topic: Optional[str] = None, limit: int = 5) -> List[Dict[str, Any]]:
        with get_connection() as conn:
            cursor = conn.cursor()
            if topic:
                cursor.execute(
                    """
                    SELECT topic, question_text, student_answer, correct_answer, created_at
                    FROM mistakes WHERE student_id = ? AND topic = ?
                    ORDER BY id DESC LIMIT ?
                    """,
                    (student_id, topic, limit),
                )
            else:
                cursor.execute(
                    """
                    SELECT topic, question_text, student_answer, correct_answer, created_at
                    FROM mistakes WHERE student_id = ?
                    ORDER BY id DESC LIMIT ?
                    """,
                    (student_id, limit),
                )
            return [dict(r) for r in cursor.fetchall()]

    @staticmethod
    def set_diagnostic_queue(student_id: str, questions: List[Dict[str, Any]]) -> None:
        StateManager.update_profile(
            student_id,
            diagnostic_queue_json=json.dumps(questions),
            diagnosed=0,
        )

    @staticmethod
    def pop_diagnostic_question(student_id: str) -> Optional[Dict[str, Any]]:
        summary = StateManager.get_student_summary(student_id)
        queue = summary.get("diagnostic_queue") or []
        if not queue:
            return None
        nxt = queue.pop(0)
        StateManager.update_profile(
            student_id,
            diagnostic_queue_json=json.dumps(queue),
            diagnosed=1 if not queue else 0,
        )
        return nxt
