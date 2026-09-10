"""generate_aptitude_question — Enhanced, anti-repetitive aptitude question engine."""

import random
import uuid
from typing import Any, Dict, List, Optional

from backend.state import StateManager

QUESTION_BANK: Dict[str, List[Dict[str, Any]]] = {
    "Percentages": [
        {
            "id": "pct_e1",
            "question": "What is 15% of 240?",
            "options": {"A": "32", "B": "36", "C": "40", "D": "48"},
            "correct_answer": "B",
            "difficulty": "Easy",
        },
        {
            "id": "pct_e2",
            "question": "A shirt priced at $80 is discounted by 25%. What is the final sale price?",
            "options": {"A": "$55", "B": "$60", "C": "$65", "D": "$70"},
            "correct_answer": "B",
            "difficulty": "Easy",
        },
        {
            "id": "pct_e3",
            "question": "In a class of 50 students, 60% are girls. How many boys are in the class?",
            "options": {"A": "15", "B": "20", "C": "25", "D": "30"},
            "correct_answer": "B",
            "difficulty": "Easy",
        },
        {
            "id": "pct_m1",
            "question": "If 40% of a number is equal to 120, what is 15% of that same number?",
            "options": {"A": "35", "B": "45", "C": "50", "D": "60"},
            "correct_answer": "B",
            "difficulty": "Medium",
        },
        {
            "id": "pct_m2",
            "question": "A student scored 72 marks out of 90 in Math and 80 out of 100 in Science. What is their combined percentage?",
            "options": {"A": "76%", "B": "80%", "C": "82%", "D": "84%"},
            "correct_answer": "B",
            "difficulty": "Medium",
        },
        {
            "id": "pct_m3",
            "question": "If the price of sugar increases by 25%, by what percentage must consumption be reduced so expenditure remains constant?",
            "options": {"A": "15%", "B": "20%", "C": "25%", "D": "30%"},
            "correct_answer": "B",
            "difficulty": "Medium",
        },
        {
            "id": "pct_h1",
            "question": "A price increases by 20% and then falls by 10%. What is the net percentage change?",
            "options": {"A": "+10%", "B": "+8%", "C": "+12%", "D": "+6%"},
            "correct_answer": "B",
            "difficulty": "Hard",
        },
        {
            "id": "pct_h2",
            "question": "In an election between two candidates, the winner received 56% of total valid votes and won by a majority of 1,440 votes. What was the total number of valid votes?",
            "options": {"A": "10,000", "B": "12,000", "C": "14,400", "D": "15,000"},
            "correct_answer": "B",
            "difficulty": "Hard",
        },
    ],
    "Ratio and Proportion": [
        {
            "id": "rat_e1",
            "question": "Divide $5,000 between A and B in the ratio 2:3. How much does A receive?",
            "options": {"A": "$1,500", "B": "$2,000", "C": "$2,500", "D": "$3,000"},
            "correct_answer": "B",
            "difficulty": "Easy",
        },
        {
            "id": "rat_e2",
            "question": "The ratio of boys to girls in a club is 5:4. If there are 36 girls, how many boys are there?",
            "options": {"A": "40", "B": "45", "C": "50", "D": "54"},
            "correct_answer": "B",
            "difficulty": "Easy",
        },
        {
            "id": "rat_m1",
            "question": "If A:B = 3:4 and B:C = 8:9, find the ratio A:C.",
            "options": {"A": "2:3", "B": "3:2", "C": "1:2", "D": "3:4"},
            "correct_answer": "A",
            "difficulty": "Medium",
        },
        {
            "id": "rat_m2",
            "question": "Two numbers are in the ratio 3:5. If 6 is added to each number, the ratio becomes 2:3. What is the smaller number?",
            "options": {"A": "15", "B": "18", "C": "21", "D": "24"},
            "correct_answer": "B",
            "difficulty": "Medium",
        },
        {
            "id": "rat_h1",
            "question": "A mixture of 60 liters contains milk and water in the ratio 2:1. How much water must be added so the ratio becomes 1:2?",
            "options": {"A": "40 liters", "B": "60 liters", "C": "80 liters", "D": "50 liters"},
            "correct_answer": "B",
            "difficulty": "Hard",
        },
    ],
    "Averages": [
        {
            "id": "avg_e1",
            "question": "The average of 5 numbers is 18. Four numbers sum to 70. What is the fifth number?",
            "options": {"A": "18", "B": "20", "C": "22", "D": "25"},
            "correct_answer": "B",
            "difficulty": "Easy",
        },
        {
            "id": "avg_e2",
            "question": "Find the average of 10, 20, 30, 40, and 50.",
            "options": {"A": "25", "B": "30", "C": "35", "D": "40"},
            "correct_answer": "B",
            "difficulty": "Easy",
        },
        {
            "id": "avg_m1",
            "question": "The average age of 24 students and their teacher is 15 years. If the teacher's age is excluded, the average decreases by 1 year. What is the teacher's age?",
            "options": {"A": "35 years", "B": "39 years", "C": "40 years", "D": "42 years"},
            "correct_answer": "B",
            "difficulty": "Medium",
        },
        {
            "id": "avg_h1",
            "question": "A cricketer has an average of 42 runs in 19 innings. How many runs must he score in the 20th innings to raise his average to 45 runs?",
            "options": {"A": "98", "B": "102", "C": "105", "D": "110"},
            "correct_answer": "B",
            "difficulty": "Hard",
        },
    ],
    "Time and Work": [
        {
            "id": "tw_e1",
            "question": "A completes a task in 10 days and B in 15 days. Working together, how many days will they take?",
            "options": {"A": "5 days", "B": "6 days", "C": "7.5 days", "D": "8 days"},
            "correct_answer": "B",
            "difficulty": "Easy",
        },
        {
            "id": "tw_e2",
            "question": "If 6 workers build a wall in 12 days, how many days will 9 workers take to build the same wall?",
            "options": {"A": "6 days", "B": "8 days", "C": "9 days", "D": "10 days"},
            "correct_answer": "B",
            "difficulty": "Easy",
        },
        {
            "id": "tw_m1",
            "question": "Pipe A fills a tank in 8 hours and Pipe B empties it in 12 hours. If both are opened together, in how many hours will the tank be full?",
            "options": {"A": "16 hours", "B": "20 hours", "C": "24 hours", "D": "30 hours"},
            "correct_answer": "C",
            "difficulty": "Medium",
        },
        {
            "id": "tw_m2",
            "question": "A is twice as efficient as B. Working together, they finish a work in 14 days. In how many days can A alone finish the work?",
            "options": {"A": "18 days", "B": "21 days", "C": "24 days", "D": "28 days"},
            "correct_answer": "B",
            "difficulty": "Medium",
        },
        {
            "id": "tw_h1",
            "question": "A and B can do a job in 12 days, B and C in 15 days, and C and A in 20 days. How many days will A, B, and C take working together?",
            "options": {"A": "8 days", "B": "10 days", "C": "12 days", "D": "14 days"},
            "correct_answer": "B",
            "difficulty": "Hard",
        },
    ],
    "Time Speed and Distance": [
        {
            "id": "tsd_e1",
            "question": "A car travels 150 km in 3 hours. What is its average speed in km/h?",
            "options": {"A": "45 km/h", "B": "50 km/h", "C": "55 km/h", "D": "60 km/h"},
            "correct_answer": "B",
            "difficulty": "Easy",
        },
        {
            "id": "tsd_e2",
            "question": "Convert a speed of 72 km/h into meters per second (m/s).",
            "options": {"A": "15 m/s", "B": "20 m/s", "C": "25 m/s", "D": "30 m/s"},
            "correct_answer": "B",
            "difficulty": "Easy",
        },
        {
            "id": "tsd_m1",
            "question": "A train 180 meters long is traveling at 54 km/h. How many seconds will it take to pass an electric pole?",
            "options": {"A": "10 seconds", "B": "12 seconds", "C": "15 seconds", "D": "18 seconds"},
            "correct_answer": "B",
            "difficulty": "Medium",
        },
        {
            "id": "tsd_h1",
            "question": "A person travels from city A to B at 40 km/h and returns at 60 km/h. What is the average speed for the entire round trip?",
            "options": {"A": "48 km/h", "B": "50 km/h", "C": "52 km/h", "D": "54 km/h"},
            "correct_answer": "A",
            "difficulty": "Hard",
        },
    ],
    "Profit and Loss": [
        {
            "id": "pl_e1",
            "question": "An item bought for $500 is sold for $600. What is the profit percentage?",
            "options": {"A": "15%", "B": "20%", "C": "25%", "D": "30%"},
            "correct_answer": "B",
            "difficulty": "Easy",
        },
        {
            "id": "pl_e2",
            "question": "Cost Price = $800, Profit = 10%. What is the Selling Price?",
            "options": {"A": "$850", "B": "$880", "C": "$900", "D": "$920"},
            "correct_answer": "B",
            "difficulty": "Easy",
        },
        {
            "id": "pl_m1",
            "question": "By selling an article for $450, a shopkeeper loses 10%. At what price should he sell it to gain 20%?",
            "options": {"A": "$550", "B": "$600", "C": "$650", "D": "$700"},
            "correct_answer": "B",
            "difficulty": "Medium",
        },
        {
            "id": "pl_h1",
            "question": "A dishonest dealer professes to sell his goods at cost price, but uses a weight of 900 grams for a 1 kg weight. What is his real gain percentage?",
            "options": {"A": "10%", "B": "11.11%", "C": "12.5%", "D": "15%"},
            "correct_answer": "B",
            "difficulty": "Hard",
        },
    ],
    "Probability": [
        {
            "id": "prob_e1",
            "question": "A bag contains 3 red balls and 2 blue balls. What is the probability of drawing a red ball?",
            "options": {"A": "2/5", "B": "3/5", "C": "1/2", "D": "3/2"},
            "correct_answer": "B",
            "difficulty": "Easy",
        },
        {
            "id": "prob_e2",
            "question": "A fair six-sided die is rolled once. What is the probability of getting an even number?",
            "options": {"A": "1/3", "B": "1/2", "C": "2/3", "D": "1/6"},
            "correct_answer": "B",
            "difficulty": "Easy",
        },
        {
            "id": "prob_m1",
            "question": "A fair six-sided die is rolled once. What is the probability of getting a number strictly greater than 4?",
            "options": {"A": "1/6", "B": "1/3", "C": "1/2", "D": "2/3"},
            "correct_answer": "B",
            "difficulty": "Medium",
        },
        {
            "id": "prob_m2",
            "question": "Two coins are tossed simultaneously. What is the probability of getting at least one Head?",
            "options": {"A": "1/4", "B": "1/2", "C": "3/4", "D": "2/3"},
            "correct_answer": "C",
            "difficulty": "Medium",
        },
        {
            "id": "prob_h1",
            "question": "Two fair dice are rolled. What is the probability that the sum of the numbers equals 8?",
            "options": {"A": "5/36", "B": "1/6", "C": "7/36", "D": "1/9"},
            "correct_answer": "A",
            "difficulty": "Hard",
        },
        {
            "id": "prob_h2",
            "question": "From a well-shuffled deck of 52 cards, two cards are drawn at random without replacement. What is the probability that both are Kings?",
            "options": {"A": "1/221", "B": "1/169", "C": "1/52", "D": "4/663"},
            "correct_answer": "A",
            "difficulty": "Hard",
        },
    ],
}


def _shuffle_options(options_dict: Dict[str, str], correct_letter: str) -> tuple[Dict[str, str], str]:
    """Randomly distribute options across A, B, C, D so correct answer is balanced."""
    correct_text = options_dict.get(correct_letter, "")
    items = list(options_dict.values())
    random.shuffle(items)
    
    letters = ["A", "B", "C", "D"][:len(items)]
    new_options = {}
    new_correct = "A"
    
    for ltr, text in zip(letters, items):
        new_options[ltr] = text
        if text == correct_text:
            new_correct = ltr
            
    return new_options, new_correct


def generate_aptitude_question(
    topic: str,
    difficulty: str = "Easy",
    student_id: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Select or generate an aptitude practice question.
    Filters out already served questions for the student to prevent repetitive questions.
    """
    # Normalize topic lookup
    matched_topic = "Probability"
    for k in QUESTION_BANK:
        if k.lower() == topic.lower() or topic.lower() in k.lower():
            matched_topic = k
            break

    bank = QUESTION_BANK.get(matched_topic, QUESTION_BANK["Probability"])

    # Find already served question IDs for this student
    served_ids = set()
    if student_id:
        served_ids = set(StateManager.get_served_question_ids(student_id))

    # Try to find an unserved question matching requested difficulty
    candidates = [q for q in bank if q.get("difficulty", "").lower() == difficulty.lower() and q.get("id") not in served_ids]
    
    # If all questions of this difficulty were served, pick any unserved question in this topic
    if not candidates:
        candidates = [q for q in bank if q.get("id") not in served_ids]

    # If all questions in the entire topic were served, fallback to all candidates of that difficulty
    if not candidates:
        candidates = [q for q in bank if q.get("difficulty", "").lower() == difficulty.lower()] or bank

    selected = random.choice(candidates)
    
    # Shuffle options so the correct answer is not always "B"
    raw_options = dict(selected["options"])
    raw_correct = selected["correct_answer"]
    shuffled_options, shuffled_correct = _shuffle_options(raw_options, raw_correct)

    return {
        "id": selected.get("id") or f"q_{uuid.uuid4().hex[:6]}",
        "question": selected["question"],
        "options": shuffled_options,
        "correct_answer": shuffled_correct,
        "topic": matched_topic,
        "difficulty": selected.get("difficulty") or difficulty,
    }


def generate_diagnostic_set(topics: List[str], limit: int = 5) -> List[Dict[str, Any]]:
    """Generate diagnostic set across core topics."""
    chosen = topics[:limit] if topics else list(QUESTION_BANK.keys())[:limit]
    questions = []
    for t in chosen:
        questions.append(generate_aptitude_question(t, "Easy"))
    return questions

