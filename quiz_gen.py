import argparse
import json
import random
import time
from dataclasses import dataclass
from datetime import datetime, date
from os import stat_result
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

RESULTS_DIR = Path("results")
PROGRESS_FILE = RESULTS_DIR / "progress.json"

def ensure_results_dir():
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)

def load_json(path: str) -> Any:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def save_json(path: Path, data: Any):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def safe_lower(s: str) -> str:
    return s.strip().lower()

def normalize_short(s: str) -> str:
    return " ".join(s.strip().lower().split())

def now_ts() -> str:
    return datetime.now().strftime("%Y%m%d_%H%M%S")

def parse_iso_date(s: str) -> date:
    y, m, d = s.split("-")
    return date(int(y), int(m), int(d))

def format_seconds(total: float) -> str:
    total = int(round(total))
    mm = total // 60
    ss = total % 60
    if mm > 0:
        return f"{mm} min {ss:02d} sec"
    return f"{ss} sec"

def grade_from_percent(p: float) -> int:
    g = int(round(p / 10))
    if g < 1:
        g = 1
    if g > 10:
        g = 10
    return g

def progress_bar(percent: float, width: int = 20) -> str:
    filled = int(round((percent / 100) * width))
    filled = max(0, min(width, filled))
    return "█" * filled + "░" * (width - filled)

def load_progress() -> dict:
    ensure_results_dir()
    if PROGRESS_FILE.exists():
        try:
            return load_json(str(PROGRESS_FILE))
        except:
            return {"recent_ids": []}
    return {"recent_ids": []}

def save_progress(progress: dict):
    ensure_results_dir()
    save_json(PROGRESS_FILE, progress)

@dataclass
class Question:
    id: str
    category: str
    type: str
    question: str
    options: Optional[List[str]]
    answer: str
    explanation: str

def load_questions(file_path: str) -> List[Question]:
    raw = load_json(file_path)
    questions: List[Question] = []
    for q in raw:
        questions.append(
            Question(
                id=str(q.get("id", "")),
                category=str(q.get("category", "")).lower(),
                type=str(q.get("type", "")).lower(),
                question=str(q.get("question", "")),
                options=q.get("options"),
                answer=str(q.get("answer", "")),
                explication=str(q.get("explanation", "")),
            )
        )
    return questions

def timed_input(prompt: str) -> Tuple[str, float]:
    start = time.time()
    ans = input(prompt)
    elapsed = time.time() - start
    return ans, elapsed

def shuffle_multiple_options(q: Question) -> Tuple[Question, Dict[str, str]]:
    if q.type != "multiple" or not q.options:
        return q, {}

    letters = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
    old_opts = q.options[:]
    old_letters = [letters[i] for i  in range(len(old_opts))]

    old_map = dict(zip(old_letters, old_opts))

    new_opts = old_opts[:]
    random.shuffle(new_opts)

    mapping_new_to_old = {}
    for i, opt_text in enumerate(new_opts):
        new_letter = letters[i]
        old_letter = None
        for k, v in old_map.items():
            if v == opt_text:
                old_letter = k
                break
        mapping_new_to_old[new_letter] = old_letter or "?"

    qq = Question(
        id=q.id,
        category=q.category,
        type=q.type,
        question=q.question,
        options=new_opts,
        answer=q.answer,
        explanation=q.explanation,
    )
    return qq, mapping_new_to_old


@dataclass
class AnswerRecord:
    qid: str
    category: str
    qtype: str
    questions: str
    your_answer: str
    correct_answer: str
    is_correct: bool
    timed_out: bool
    time_sec: float
    explanation: str


@dataclass
class SessionResult:
    user: str
    mode: str
    feedback: str
    category_filter: str
    type_filter: str
    timed_seconds: int
    points_correct: int
    penalty_wrong: int
    num_questions: int
    correct: int
    wrong: int
    score: int
    max_score: int
    percent: float
    total_time_sec: float
    avg_time_sec: float
    date_iso: str
    answers: List[AnswerRecord]

def ask_question(q: Question, timed_seconds: int, mode: str, feedback: str, points_correct: int, penalty_wrong: int):
    print("-" * 55)

    mapping_new_to_old = {}
    qq = q
    if q.type == "multiple":
        qq, mapping_new_to_old = shuffle_multiple_options(q)

    print(qq.question)

    correct_display = ""

    if qq.type == "multiple":
        letters = "ABCDEFGHIJKLMNOPQRSTUVWXYYZ"
        for i, opt in enumerate(qq.options or []):
            print(f" {letters[i]}) {opt}")
        correct_display = q.answer.upper()

        ans_raw, elapsed = timed_input("Raspunsul tau (A/B/C/D): ")
        ans = ans_raw.strip().upper()

        timed_out = timed_seconds > 0 and elapsed > timed_seconds

        original_letter = mapping_new_to_old.get(ans, ans)
        is_correct = (not timed_out) and (original_letter == q.answer.upper())

        your_display = ans

    elif qq.type == "true_false":
        correct_display = q.answer.lower()
        ans_raw, elapsed = timed_input("Raspunsul tau (true/false): ")
        ans = ans_raw.strip().lower()
        timed_out =timed_seconds > 0 and elapsed > timed_seconds
        is_correct = (not timed_out) and (safe_lower(ans) == safe_lower(q.answer))
        your_display = ans

    else:
        correct_display = q.answer
        ans_raw, elapsed = timed_input("Raspunsul tau: ")
        ans = ans_raw.strip()
        timed_out = timed_seconds > 0 and elapsed > timed_seconds
        is_correct = (not timed_out) and (normalize_short(ans) == normalize_short(q.answer))
        your_display = ans

    score_delta = 0
    if mode == "exam":
        score_delta += points_correct if is_correct else -penalty_wrong

    if feedback == "immediate":
        if timed_out:
            print(f"[TIMP EXPIRAT](ai raspuns in {elapsed:.1f}s, limita {timed_seconds}s)")
        if is_correct:
            print(f"[CORECT] (+{points_correct} puncte) [Raspuns in {elapsed:.1f} secunde]" if mode == "exam"
                else f"[CORECT] [Raspuns in {elapsed:.1f} secunde]")
        else:
            print(f"[INCORECT] (-{penalty_wrong} puncte) [Raspuns in {elapsed:.1f} secunde]" if mode == "exam"
                else f"[INCORECT] [Raspuns in {elapsed:.1f} secunde]")
            print(f"Raspuns corect: {correct_display}")
            if q.explanation:
                print(f"Explicatie: {q.explanation}")

    rec = AnswerRecord(
        qid=q.id,
        category=q.category,
        qtype=q.type,
        question=q.question,
        your_answer=your_display,
        correct_answer=correct_display,
        is_correct=is_correct,
        timed_out=timed_out,
        time_sec=round(elapsed, 2),
        explanation=q.explanation,
    )
    return rec, score_delta, (1 if is_correct else 0)