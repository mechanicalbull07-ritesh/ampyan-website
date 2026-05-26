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

    if not results:
        return [], []

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

    has_specific_results = any(not r.get("use_as_router_only") for r in results)
    if has_specific_results:
        for r in results:
            if r.get("use_as_router_only"):
                r["confidence"] *= 0.35

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
    # 🔥 TRUST CALIBRATION
    # =============================

    results = sorted(results, key=lambda x: x["confidence"], reverse=True)
    top_confidence = int(results[0].get("confidence", 0) or 0)
    second_confidence = int(results[1].get("confidence", 0) or 0) if len(results) > 1 else 0
    needs_more_info = bool(second_confidence and top_confidence - second_confidence <= 8)

    for index, r in enumerate(results):
        confidence = int(max(1, min(95, r.get("confidence", 0))))
        if index > 0:
            confidence = min(confidence, max(1, top_confidence - 3))
        r["confidence"] = confidence
        r["confidence_percent"] = confidence
        r["needs_more_info"] = needs_more_info if index == 0 else False
        if confidence < 55:
            r["evidence_level"] = "low"
        elif confidence < 78:
            r["evidence_level"] = "medium"
        else:
            r["evidence_level"] = r.get("evidence_level") or "strong"

    if results and results[0]["confidence"] < 40:
        results = [
            {
                "issue": "General Vehicle Inspection Needed",
                "problem": "General Vehicle Inspection Needed",
                "system": "general",
                "component": "multiple",
                "severity": "medium",
                "urgency": "service_soon",
                "confidence": 40,
                "confidence_percent": 40,
                "probability_score": 40,
                "top_matched_symptoms": [],
                "questions": [
                    {"id": "q1", "text": "When did the problem start?", "impact": {"yes": 1.5, "no": 0.6}},
                    {"id": "q2", "text": "Are any warning lights visible?", "impact": {"yes": 1.5, "no": 0.6}},
                    {"id": "q3", "text": "Did anything change after the last service?", "impact": {"yes": 1.5, "no": 0.6}},
                ],
                "user_checks": ["Describe the symptom, warning light, sound, smell, speed and driving condition in more detail."],
                "repair_cost": {"min": 0, "max": 5000},
                "safety_message": "",
                "disclaimer": "AMPYAN provides informational guidance only. Confirm the issue with a qualified mechanic before making repair or safety decisions.",
                "reason": "The symptom is too broad for a reliable fault match.",
                "advice": "Please add details such as when it happens, warning lights, noise type, smell, speed, recent service and whether the car is safe to drive.",
                "evidence_level": "low",
                "needs_more_info": True,
                "is_generic": True,
                "use_as_router_only": False,
            }
        ]

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
                {"id": "q1", "text": "Does the problem appear during acceleration?", "impact": {"yes": 1.5, "no": 0.6}},
                {"id": "q2", "text": "Does the issue happen while starting the car?", "impact": {"yes": 1.5, "no": 0.6}},
                {"id": "q3", "text": "Do you hear any abnormal sound?", "impact": {"yes": 1.5, "no": 0.6}}
            ]

        questions = localize_questions(questions, question_language)

    # =============================
    # 🔥 SAVE LEARNING
    # =============================

    if results:
        save_learning(problem_text, answers, results[0]["issue"], user_id)

    return results, questions
