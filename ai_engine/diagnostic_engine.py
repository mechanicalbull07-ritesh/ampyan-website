print("Diagnostic engine loading...")

from failure_database import FAILURE_DATABASE
from ai_engine.reasoning_engine import rank_failures
from ai_engine.component_detector import detect_components
from ai_engine.diagnostic_learning import save_learning, get_learning_boost
from flask_login import current_user
from ai_engine.language_engine import normalize_text, detect_input_language, localize_questions


def filter_failures(problem_text, car=None):

    components = detect_components(problem_text)

    if not components:
        return FAILURE_DATABASE

    filtered = []

    for failure in FAILURE_DATABASE:

        component = failure.get("component", "").lower()
        system = failure.get("system", "").lower()

        for comp in components:
            if comp == system or comp in component:
                filtered.append(failure)
                break

    if not filtered:
        return FAILURE_DATABASE

    return filtered


def diagnose_vehicle(problem_text, answers=None, car=None):

    if answers is None:
        answers = {}

    original_problem_text = problem_text.strip()
    question_language = detect_input_language(original_problem_text)
    problem_text = normalize_text(original_problem_text)

    user = current_user if getattr(current_user, "is_authenticated", False) else None
    user_id = user.id if user else None

    filtered_db = filter_failures(problem_text, car)

    results = rank_failures(problem_text, filtered_db)

    # =============================
    # 🔥 CONTEXT DETECTION
    # =============================

    is_vibration = "vibration" in problem_text
    is_misfire = "misfire" in problem_text
    is_low_power = "low power" in problem_text

    # =============================
    # 🔥 ANSWER IMPACT
    # =============================

    if answers:

        for r in results:

            score = r.get("confidence", 0)
            issue = r.get("issue", "").lower()

            for key, value in answers.items():

                key = str(key).lower()

                if "1" in key:
                    if "spark plug" in issue:
                        score += 12
                    else:
                        score += 2

                elif "2" in key:
                    if "coil" in issue:
                        score += 6
                    elif "spark plug" in issue:
                        score += 9
                    else:
                        score += 3

                if value == "no":
                    score -= 5

            r["confidence"] = max(1, score)

    # =============================
    # 🔥 CONTEXT BALANCE
    # =============================

    for r in results:

        issue = r["issue"].lower()

        if is_vibration:

            if "spark plug" in issue:
                r["confidence"] *= 0.85

            if "coil" in issue:
                r["confidence"] *= 0.8

            if "mount" in issue:
                r["confidence"] *= 1.6

        if is_misfire:

            if "spark plug" in issue:
                r["confidence"] *= 1.2

            if "coil" in issue:
                r["confidence"] *= 1.1

        if is_low_power:

            if "spark plug" in issue:
                r["confidence"] *= 0.5

            if "coil" in issue:
                r["confidence"] *= 0.55

            if "injector" in issue:
                r["confidence"] *= 1.4

            if "fuel" in issue:
                r["confidence"] *= 1.3

            if "turbo" in issue:
                r["confidence"] *= 1.6

            if "filter" in issue:
                r["confidence"] *= 1.3

    # =============================
    # 🔥 FEEDBACK WEIGHT (NEW)
    # =============================

    for r in results:

        for failure in FAILURE_DATABASE:
            if failure["problem"] == r["issue"]:

                feedback = failure.get("feedback", {})
                confirmed = feedback.get("confirmed", 0)
                rejected = feedback.get("rejected", 0)

                total = confirmed + rejected

                if total > 0:

                    success_ratio = confirmed / total

                    if success_ratio > 0.7:
                        r["confidence"] *= 1.2

                    elif success_ratio < 0.3:
                        r["confidence"] *= 0.7

                break

    # =============================
    # SORT
    # =============================

    results = sorted(results, key=lambda x: x["confidence"], reverse=True)

    # =============================
    # 🔥 LEARNING BOOST
    # =============================

    if answers:

        boost_map = get_learning_boost(problem_text, answers, user_id)

        for r in results:

            issue = r["issue"].lower()

            if issue in boost_map:
                boost = min(boost_map[issue], int(r["confidence"] * 0.2))
                r["confidence"] += boost

    # =============================
    # 🔥 NORMALIZATION
    # =============================

    max_score = results[0]["confidence"]

    for r in results:
        r["confidence"] = int((r["confidence"] / max_score) * 100)

    # =============================
    # QUESTIONS
    # =============================

    questions = []

    if results:

        top_issue = results[0]["issue"].lower()

        for failure in FAILURE_DATABASE:
            if failure.get("problem", "").lower() == top_issue:
                questions = failure.get("questions", [])
                break

        if not questions:
            questions = [
                {"id": "q1", "text": "Does the problem appear during acceleration?"},
                {"id": "q2", "text": "Does the issue happen while starting the car?"},
                {"id": "q3", "text": "Do you hear any abnormal sound?"}
            ]

        questions = localize_questions(questions, question_language)

    # =============================
    # 🔥 SAVE LEARNING
    # =============================

    if results:
        save_learning(problem_text, answers, results[0]["issue"], user_id)

    return results, questions
