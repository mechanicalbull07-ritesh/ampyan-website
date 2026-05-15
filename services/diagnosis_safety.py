import time

from flask import current_app

from ai_engine.diagnostic_engine import diagnose_vehicle


FALLBACK_RESULTS = [
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
        "questions": [],
        "user_checks": [
            "Check warning lights, fluid levels, battery voltage and tyre pressure."
        ],
        "repair_cost": {"min": 0, "max": 5000},
        "safety_message": "",
        "disclaimer": "AMPYAN provides informational guidance only. Confirm the issue with a qualified mechanic before making repair or safety decisions.",
        "reason": "AMPYAN could not complete the full diagnosis quickly. Please check basic safety items first: warning lights, fluids, battery voltage, tyre pressure and recent service history.",
        "advice": "If the issue affects braking, steering, overheating or engine misfire, avoid driving and consult a trusted mechanic.",
    }
]

FALLBACK_QUESTIONS = [
    {"id": "q1", "text": "When did the problem start?", "impact": {"yes": 1.5, "no": 0.6}},
    {"id": "q2", "text": "Are any warning lights visible?", "impact": {"yes": 1.5, "no": 0.6}},
    {"id": "q3", "text": "Did anything change after the last service?", "impact": {"yes": 1.5, "no": 0.6}},
]


def safe_diagnose_vehicle(problem, answers=None, car=None, route_name="diagnosis"):
    start = time.perf_counter()
    try:
        results, questions = diagnose_vehicle(problem or "", answers=answers, car=car)
        elapsed = time.perf_counter() - start
        if elapsed >= float(current_app.config.get("DIAGNOSIS_SLOW_SECONDS", 2.0)):
            current_app.logger.warning(
                "slow_diagnosis route=%s duration=%.3fs results=%s",
                route_name,
                elapsed,
                len(results or []),
            )
        return results or FALLBACK_RESULTS, questions or []
    except Exception as exc:
        elapsed = time.perf_counter() - start
        current_app.logger.exception(
            "diagnosis_fallback route=%s duration=%.3fs error=%s",
            route_name,
            elapsed,
            exc.__class__.__name__,
        )
        return FALLBACK_RESULTS, FALLBACK_QUESTIONS
