from copy import deepcopy

from failure_database import FAILURE_DATABASE


LANGUAGE_LABELS = {
    "en": {
        "page_title": "Final AI Diagnosis",
        "detected_language": "Detected language",
        "car": "Car",
        "final_issue": "Final Detected Issue",
        "confidence": "Confidence",
        "severity": "Severity",
        "urgency": "Urgency",
        "repair_cost": "Estimated Repair",
        "driveability": "Can You Drive It?",
        "why": "Why This Diagnosis?",
        "checks": "Quick Checks You Can Do",
        "next_steps": "What Should You Do Next?",
        "other_issues": "Other Possible Issues",
        "feedback": "Was this diagnosis accurate?",
        "yes": "Yes, this looks right",
        "no": "No, this seems wrong",
        "save": "Save your diagnosis",
        "login_cta": "Login to unlock features",
        "retry": "Check Another Problem",
        "no_result": "No Diagnosis Found",
        "no_result_desc": "AMPYAN AI could not identify the issue clearly. Please describe the problem in more detail."
    },
    "hi": {
        "page_title": "AI Diagnosis Result",
        "detected_language": "Detected language",
        "car": "Car",
        "final_issue": "Final detected issue",
        "confidence": "Confidence",
        "severity": "Severity",
        "urgency": "Urgency",
        "repair_cost": "Estimated repair",
        "driveability": "Can you drive it?",
        "why": "Why this diagnosis?",
        "checks": "Quick checks you can do",
        "next_steps": "What should you do next?",
        "other_issues": "Other possible issues",
        "feedback": "Was this diagnosis accurate?",
        "yes": "Yes, seems right",
        "no": "No, seems wrong",
        "save": "Save your diagnosis",
        "login_cta": "Login to unlock features",
        "retry": "Check another problem",
        "no_result": "No diagnosis found",
        "no_result_desc": "AMPYAN AI could not identify the issue clearly. Please describe the problem in more detail."
    }
}


SEVERITY_DETAILS = {
    "low": {
        "label": "Low",
        "summary": "The issue is usually manageable for now, but it should not be ignored for too long.",
        "driveability": "Generally safe for short drives if no new warning signs appear."
    },
    "medium": {
        "label": "Medium",
        "summary": "The issue can worsen if ignored and may affect reliability, fuel efficiency or drivability.",
        "driveability": "Drive carefully for a limited time and arrange inspection soon."
    },
    "high": {
        "label": "High",
        "summary": "The issue may affect safety or lead to faster damage if the vehicle keeps running in the same condition.",
        "driveability": "Avoid long trips and get the vehicle checked urgently."
    },
    "critical": {
        "label": "Critical",
        "summary": "The issue may create immediate safety risk or major mechanical damage.",
        "driveability": "Do not continue driving unless absolutely necessary for safety."
    },
    "unknown": {
        "label": "Unknown",
        "summary": "The system could not confidently assign a severity level yet.",
        "driveability": "Drive conservatively until the root cause is confirmed."
    }
}


URGENCY_DETAILS = {
    "normal": {
        "label": "Normal",
        "summary": "Monitor the symptom and schedule a check in your usual service window.",
        "next_step": "Inspect during your next routine visit."
    },
    "service_soon": {
        "label": "Service Soon",
        "summary": "The problem should be inspected soon before it grows into a bigger repair.",
        "next_step": "Book service in the next few days."
    },
    "urgent": {
        "label": "Urgent",
        "summary": "The issue needs fast attention to reduce safety risk or prevent further damage.",
        "next_step": "Get the vehicle checked as early as possible."
    },
    "immediate": {
        "label": "Immediate Attention",
        "summary": "The issue may need immediate action before the car is driven again.",
        "next_step": "Stop using the vehicle and contact a mechanic immediately."
    },
    "unknown": {
        "label": "Unknown",
        "summary": "The system could not confidently assign an urgency level yet.",
        "next_step": "Inspect the vehicle manually if symptoms persist."
    }
}


DEFAULT_NEXT_STEPS = [
    "Inspect the affected system carefully.",
    "Avoid aggressive driving until the symptom is confirmed.",
    "If the symptom repeats, visit a trusted mechanic."
]


ROMAN_HINDI_HINTS = ["nahi", "gaadi", "awaaz", "garam", "start", "band", "jerk", "pickup"]

LANGUAGE_NAMES = {
    "en": "English",
    "hi": "Hindi / Hinglish",
    "ta": "Tamil",
    "te": "Telugu",
    "bn": "Bengali",
    "ml": "Malayalam",
    "kn": "Kannada"
}


def detect_response_language(text):
    sample = (text or "").strip()
    if not sample:
        return "en"

    if any("\u0b80" <= ch <= "\u0bff" for ch in sample):
        return "ta"
    if any("\u0c00" <= ch <= "\u0c7f" for ch in sample):
        return "te"
    if any("\u0980" <= ch <= "\u09ff" for ch in sample):
        return "bn"
    if any("\u0d00" <= ch <= "\u0d7f" for ch in sample):
        return "ml"
    if any("\u0c80" <= ch <= "\u0cff" for ch in sample):
        return "kn"
    if any("\u0900" <= ch <= "\u097f" for ch in sample):
        return "hi"

    lowered = sample.lower()
    if any(token in lowered for token in ROMAN_HINDI_HINTS):
        return "hi"

    return "en"


def get_ui_strings(language_code):
    return LANGUAGE_LABELS.get(language_code, LANGUAGE_LABELS["en"])


def _find_failure(issue_name):
    for failure in FAILURE_DATABASE:
        if failure.get("problem") == issue_name:
            return failure
    return None


def _localized_step(result):
    advice = result.get("advice")
    if advice:
        return [advice]
    return deepcopy(DEFAULT_NEXT_STEPS)


def enrich_diagnosis_results(results, problem_text):
    language_code = detect_response_language(problem_text)
    ui_text = get_ui_strings(language_code)

    enriched = []

    for result in results or []:
        item = deepcopy(result)
        failure = _find_failure(item.get("issue"))

        if failure:
            item["severity"] = (item.get("severity") or failure.get("severity") or "unknown").lower()
            item["urgency"] = (failure.get("urgency") or "unknown").lower()
            item["repair_cost"] = item.get("repair_cost") or failure.get("repair_cost")
            item["user_checks"] = item.get("user_checks") or failure.get("user_checks", [])
            item["advice"] = item.get("advice") or failure.get("advice")
        else:
            item["severity"] = (item.get("severity") or "unknown").lower()
            item["urgency"] = "unknown"

        severity_details = SEVERITY_DETAILS.get(item["severity"], SEVERITY_DETAILS["unknown"])
        urgency_details = URGENCY_DETAILS.get(item["urgency"], URGENCY_DETAILS["unknown"])

        item["severity_label"] = severity_details["label"]
        item["severity_summary"] = severity_details["summary"]
        item["urgency_label"] = urgency_details["label"]
        item["urgency_summary"] = urgency_details["summary"]
        item["driveability"] = severity_details["driveability"]
        item["recommended_steps"] = _localized_step(item)
        item["urgency_next_step"] = urgency_details["next_step"]

        enriched.append(item)

    return {
        "results": enriched,
        "language_code": language_code,
        "language_name": LANGUAGE_NAMES.get(language_code, "English"),
        "ui_text": ui_text
    }
