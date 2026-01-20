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
                explanation=str(q.get("explanation", "")),
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
    question: str
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
        letters = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
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
        timed_out = timed_seconds > 0 and elapsed > timed_seconds
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

def run_session(questions: List[Question], user: str, mode: str, feedback: str, timed_seconds: int,
                points_correct: int, penalty_wrong: int, category_filter: str, type_filter: str)-> SessionResult:

    score = 0
    correct = 0
    wrong = 0
    answers: List[AnswerRecord] = []
    start_total = time.time()

    print("=" * 55)
    title_cat = category_filter if category_filter else "Toate categoriile"
    print(f"Quiz - {title_cat} ({len(questions)} intrebari)")
    print(f"Mod: {'Examen' if mode == 'exam' else 'Practica'}")
    print(f"Timp per intrebare: {timed_seconds} secunde" if timed_seconds > 0 else "Timp per intrebare: fara timer")
    if mode == "exam":
        print(f"Punctaj: {points_correct} puncte/raspuns corect | Penalizare: {penalty_wrong}")
    print("=" * 55)

    for i, q in enumerate(questions, start=1):
        print(f"\nIntrebare {i}/{len(questions)}" + (f" [Timp: {timed_seconds}s]" if timed_seconds > 0 else ""))
        rec, delta, ok = ask_question(q, timed_seconds, mode, feedback, points_correct, penalty_wrong)
        answers.append(rec)

        score += delta
        if score < 0:
            score = 0

        correct += ok
        if ok == 0:
            wrong += 1

    total_time = time.time() - start_total
    max_score = len(questions) * points_correct if mode == "exam" else 0
    percent = (score / max_score * 100.0) if max_score > 0 else (correct / len(questions) *100.0)

    avg_time = total_time / len(questions) if questions else 0.0

    return SessionResult(
        user=user,
        mode=mode,
        feedback=feedback,
        category_filter=category_filter,
        type_filter=type_filter,
        timed_seconds=timed_seconds,
        points_correct=points_correct,
        penalty_wrong=penalty_wrong,
        num_questions=len(questions),
        correct=correct,
        wrong=wrong,
        score=score,
        max_score=max_score,
        percent=round(percent, 2),
        total_time_sec=round(total_time, 2),
        avg_time_sec=round(avg_time, 2),
        date_iso=datetime.now().date().isoformat(),
        answers=answers,
    )

def save_session(result: SessionResult) -> Path:
    ensure_results_dir()
    path = RESULTS_DIR / f"results_{now_ts()}_{result.user}.json"

    data = {
        "user": result.user,
        "date": result.date_iso,
        "mode": result.mode,
        "feedback": result.feedback,
        "category_filter": result.category_filter,
        "type_filter": result.type_filter,
        "timed_seconds": result.timed_seconds,
        "points_correct": result.points_correct,
        "penalty_wrong": result.penalty_wrong,
        "num_questions": result.num_questions,
        "correct": result.correct,
        "wrong": result.wrong,
        "score": result.score,
        "max_score": result.max_score,
        "percent": result.percent,
        "total_time_sec": result.total_time_sec,
        "avg_time_sec": result.avg_time_sec,
        "answers": [a.__dict__ for a in result.answers],
    }

    save_json(path, data)
    return path

def list_result_files() -> List[Path]:
    ensure_results_dir()
    return sorted(RESULTS_DIR.glob("results_*.json"))

def load_results() -> List[Dict[str, Any]]:
    res = []
    for f in list_result_files():
        try:
            res.append(load_json(str(f)))
        except:
            pass
    return res

def print_results_for_user(user: str, date_filter: Optional[str]):
    all_r = load_results()
    rows = [r for r in all_r if str(r.get("user", "")).lower() == user.lower()]
    if date_filter:
        rows = [r for r in rows if r.get("date") == date_filter]

    if not rows:
        print("Nu exista rezultate pentru filtrele alese.")
        return

    rows = sorted(rows, key=lambda x: x.get("date", ""))
    print(f"Rezultate pentru {user}" + (f" la data{date_filter}" if date_filter else ""))
    print("-" * 55)
    for r in rows:
        print(f"{r.get('date')} | {r.get('mode')} | {r.get('score')}/{r.get('max_score')} ({r.get('percent')}%)")

def stats_user(user: str, all_results: List[Dict[str, Any]]):
    rows = [r for r in all_results if str(r.get("user", "")).lower() == user.lower()]
    if not rows:
        print("Nu exista rezultate pentru acest user.")
        return

    percents = [float(r.get("percent", 0)) for r in rows]
    avg = sum(percents) / len(percents)
    mn = min(percents)
    mx = max(percents)

    by_cat: Dict[str, List[float]] = {}
    for r in rows:
        cat = r.get("category_filter") or "all"
        by_cat.setdefault(cat, []).append(float(r.get("percent", 0)))

    print(f"Statistici Quiz - {user}")
    print(f"Total quiz-uri completate: {len(rows)}")
    print(f"Scor mediu: {avg:.0f}%")
    print(f"Scor minim: {mn:.0f}%")
    print(f"Scor maxim: {mx:.0f}%")
    print(f"Performanta pe categorii:")
    for cat, vals in by_cat.items():
        print(f" {cat}: {sum(vals)/len(vals):.0f}% ({len(vals)} quiz-uri)")

    last5 = sorted(rows, key=lambda x: x.get("date", ""))[-5:]
    print("Evolutie (ultimele 5 quiz-uri):")
    start_index = max(1, len(rows) - 4)
    for i, r in enumerate(last5, start=start_index):
        pct = float(r.get("percent", 0))
        print(f" Quiz #{i}: {pct:.0f}% {progress_bar(pct)}")

    first = float(sorted(rows, key=lambda x: x.get("date", ""))[0].get("percent",0))
    trend = avg - first
    tword = "Imbunatatire" if trend >= 0 else "Scadere"
    print(f"Tendinta: {tword} ({trend:+.0f}% fata de primul quiz)")

def stats_all_users(all_results: List[Dict[str, Any]]):
    users = sorted({str(r.get("user", "")) for r in all_results if r.get("user")})
    if not users:
        print("Nu exista rezultate salvate.")
        return

    print("Statistici - Toti userii")
    print("-" * 55)
    for u in users:
        rows = [r for r in all_results if str(r.get("user", "")).lower() == u.lower()]
        percents = [float(r.get("percent", 0)) for r in rows]
        print(f"{u}: {len(rows)} quiz-uri | medie {sum(percents)/len(percents):.0f}% | "
              f"max {max(percents):.0f}% | min {min(percents):.0f}%")

def add_question_interactive(file_path: str):
    questions_raw = load_json(file_path)

    print("Adaugare intrebare (interactive)")
    qid = input("id (ex: m3): ").strip()
    category = input("category (ex: matematica): ").strip().lower()
    qtype = input("type (multiple/true_false/short): ").strip().lower()
    text = input("question: ").strip()

    newq: Dict[str, Any] = {
        "id": qid,
        "category": category,
        "type": qtype,
        "question": text,
        "explanation": ""
    }

    if qtype == "multiple":
        opts = []
        print("Introdu 4 optiuni:")
        for i in range(4):
            opts.append(input(f" option {i+1}: ").strip())
        newq["options"] = opts
        newq["answer"] = input("answer (A/B/C/D): ").strip().upper()
    elif qtype == "true_false":
        newq["answer"] = input("answer (true/false): ").strip().lower()
    else:
        newq["answer"] = input("answer (short): ").strip()

    newq["explanation"] = input("explanation (optional): ").strip()

    questions_raw.append(newq)
    save_json(Path(file_path), questions_raw)
    print("Intrebarea a fost adaugata in fisier.")

def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="quiz_gen", description="Quiz generator")

    p.add_argument("--file", default="questions.json")
    p.add_argument("--num", type=int, default=5)
    p.add_argument("--category", default="")
    p.add_argument("--type", dest="qtype", default="")
    p.add_argument("--timed", type=int, default=0)
    p.add_argument("--mode", choices=["practice", "exam"], default="exam")
    p.add_argument("--feedback", choices=["immediate", "final"], default="immediate")
    p.add_argument("--user", default="Anonim")

    p.add_argument("--results", action="store_true")
    p.add_argument("--date", default="")

    p.add_argument("--add_question", action="store_true")
    p.add_argument("--interactive", action="store_true")

    p.add_argument("--stats", action="store_true")
    p.add_argument("--all_users", action="store_true")

    return p

def main():
    args = build_parser().parse_args()

    if args.results:
        print_results_for_user(args.user, args.date if args.date else None)
        return

    if args.add_question:
        if args.interactive:
            add_question_interactive(args.file)
        else:
            print("Foloseste: --add_question --interactive")
        return

    if args.stats:
        all_r = load_results()
        if args.all_users:
            stats_all_users(all_r)
        else:
            stats_user(args.user, all_r)
        return

    questions = load_questions(args.file)

    cat = args.category.strip().lower()
    tq = args.qtype.strip().lower()

    if cat:
        questions = [q for q in questions if q.category == cat]
    if tq:
        questions = [q for q in questions if q.type == tq]

    if not questions:
        print("Nu exista intrebari pentru filtrele alese.")
        return

    progress = load_progress()
    recent = set(progress.get("recent_ids", []))

    fresh = [q for q in questions if q.id not in recent]
    if len(fresh) < args.num:
        fresh = questions[:]
        recent = set()

    random.shuffle(fresh)
    picked = fresh[: args.num] if args.num > 0 else fresh

    ids = progress.get("recent_ids", [])
    ids.extend([q.id for q in picked])
    progress["recent_ids"] = ids[-50:]
    save_progress(progress)

    points_correct = 10
    penalty_wrong = 2

    result = run_session(
        picked,
        user=args.user,
        mode=args.mode,
        feedback=args.feedback,
        timed_seconds=args.timed,
        points_correct=points_correct,
        penalty_wrong=penalty_wrong,
        category_filter=cat,
        type_filter=tq,
    )

    print("=" * 55)
    print("REZULTATE FINALE")
    if result.mode == "exam":
        print(f"Scor final: {result.score}/{result.max_score} puncte ({result.percent:.0f}%)")
    else:
        print(f"Mod practica (fara scor) | Precizie: {result.percent:.0f}%")

    print(f"Raspunsuri corecte: {result.correct}/{result.num_questions}")
    print(f"Raspunsuri gresite: {result.wrong}/{result.num_questions}")
    print(f"Timp total: {format_seconds(result.total_time_sec)}")
    print(f"Timp mediu/intrebare: {result.avg_time_sec:.0f} sec")

    grade = grade_from_percent(result.percent)
    status = "PROMOVAT" if grade >= 5 else "RESPINS"
    print(f"Nota: {grade}/10")
    print(f"Status: {status}")

    saved = save_session(result)
    print(f"Salvat in {saved.name}")

    if result.feedback == "immediate":
        see = input("Vrei sa vezi raspunsurile corecte pentru intrebarile gresite? (y/n): ").strip().lower()
        if see == "y":
            for i, a in enumerate(result.answers, start=1):
                if a.is_correct:
                    continue
                print(f"\nIntrebarea {i}:")
                print(f" Intrebare: {a.question}")
                print(f" Raspunsul tau: {a.your_answer}")
                print(f" Raspuns corect: {a.correct_answer}")
                if a.explanation:
                    print(f" Explicatie: {a.explanation}")

if __name__ == "__main__":
    main()