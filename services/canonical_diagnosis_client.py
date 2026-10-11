"""Server-side client for the canonical AMPYAN diagnosis API."""

import json
import os
import urllib.error
import urllib.request


DEFAULT_API_BASE_URL = "https://ampyan-api.onrender.com"
MAX_RESPONSE_BYTES = 1024 * 1024
ALLOWED_PATHS = {"/diagnose", "/get_questions", "/process_answers"}


class CanonicalDiagnosisUnavailable(RuntimeError):
    """Safe public failure used when the canonical service is unavailable."""


def _timeout_seconds():
    try:
        value = float(os.environ.get("AMPYAN_DIAGNOSIS_TIMEOUT_SECONDS", "10"))
    except (TypeError, ValueError):
        value = 10.0
    return min(max(value, 2.0), 20.0)


def _base_url():
    return (os.environ.get("AMPYAN_API_BASE_URL") or DEFAULT_API_BASE_URL).rstrip("/")


def _post(path, payload):
    if path not in ALLOWED_PATHS:
        raise CanonicalDiagnosisUnavailable("Diagnosis service is temporarily unavailable.")
    body = json.dumps(payload if isinstance(payload, dict) else {}).encode("utf-8")
    request = urllib.request.Request(
        f"{_base_url()}{path}",
        data=body,
        method="POST",
        headers={"Content-Type": "application/json", "Accept": "application/json"},
    )
    try:
        with urllib.request.urlopen(request, timeout=_timeout_seconds()) as response:
            raw = response.read(MAX_RESPONSE_BYTES + 1)
            if len(raw) > MAX_RESPONSE_BYTES:
                raise CanonicalDiagnosisUnavailable("Diagnosis service response was too large.")
            data = json.loads(raw.decode("utf-8"))
    except (urllib.error.URLError, TimeoutError, ValueError, json.JSONDecodeError) as exc:
        raise CanonicalDiagnosisUnavailable(
            "Diagnosis is temporarily unavailable. Please try again."
        ) from exc
    if not isinstance(data, dict):
        raise CanonicalDiagnosisUnavailable("Diagnosis service returned an invalid response.")
    return data


def diagnose(problem):
    return _post("/diagnose", {"problem": str(problem or "").strip(), "user_id": 0})


def get_questions(problem):
    return _post("/get_questions", {"problem": str(problem or "").strip()})


def process_answers(problems, answers, problem_text):
    return _post("/process_answers", {
        "problems": list(problems) if isinstance(problems, (list, tuple)) else [],
        "answers": answers if isinstance(answers, dict) else {},
        "problem_text": str(problem_text or "").strip(),
        "user_id": 0,
    })


def response_view(payload):
    """Defensively expose canonical values without re-ranking or recalculating."""
    data = payload if isinstance(payload, dict) else {}
    raw_matches = data.get("top_matches")
    matches = [dict(item) for item in raw_matches if isinstance(item, dict)] if isinstance(raw_matches, list) else []
    response_type = data.get("response_type")
    if response_type not in {"ranking", "safety_guidance", "clarification", "error"}:
        response_type = "ranking" if matches else (
            "safety_guidance" if data.get("summary") and isinstance(data.get("recommended_actions") or data.get("steps"), list)
            else "clarification"
        )
    actions = data.get("recommended_actions")
    if not isinstance(actions, list):
        actions = data.get("steps") if isinstance(data.get("steps"), list) else []
    questions = data.get("followup_questions")
    if not isinstance(questions, list):
        questions = data.get("questions") if isinstance(data.get("questions"), list) else []
    return {
        "response_version": data.get("response_version"),
        "response_type": response_type,
        "success": data.get("success") is not False,
        "summary": data.get("summary") if isinstance(data.get("summary"), str) else None,
        "risk_level": data.get("risk_level") if isinstance(data.get("risk_level"), str) else None,
        "severity": data.get("severity") if isinstance(data.get("severity"), str) else None,
        "can_drive": data.get("can_drive") if isinstance(data.get("can_drive"), bool) else None,
        "recommended_actions": actions,
        "followup_questions": questions,
        "language": data.get("language") if data.get("language") in {"en", "hi", "hinglish"} else "en",
        "top_matches": matches,
        "message": data.get("message") if isinstance(data.get("message"), str) else None,
    }
