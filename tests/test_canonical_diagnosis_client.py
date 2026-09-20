import json
from pathlib import Path

import pytest

from services import canonical_diagnosis_client as client


SHARED_FIXTURE = (
    Path(__file__).resolve().parents[2]
    / "motronix_api"
    / "tests"
    / "fixtures"
    / "diagnosis_parity_cases.json"
)
CASES = json.loads(SHARED_FIXTURE.read_text(encoding="utf-8"))


@pytest.mark.parametrize("case", CASES, ids=[case["id"] for case in CASES])
def test_shared_53_case_presenter_preserves_canonical_values(monkeypatch, case):
    ranking = [{
        "problem": f"canonical-{case['id']}",
        "confidence": 68,
        "severity": "moderate",
        "repair_cost": {
            "currency": "INR", "min": 1500, "max": 4500, "label": "₹1,500–₹4,500",
        },
    }]
    payload = {
        "response_version": "diagnosis-v1",
        "response_type": case["expected_response_type"],
        "success": True,
        "language": "en",
        "summary": f"summary-{case['id']}",
        "risk_level": "moderate",
        "severity": "moderate",
        "can_drive": None,
        "recommended_actions": ["canonical action"],
        "followup_questions": [{"id": "q1", "text": "canonical question"}],
        "top_matches": ranking if case["expected_response_type"] == "ranking" else [],
    }
    monkeypatch.setattr(client, "_post", lambda path, body: payload)

    response = client.diagnose(case["input"])
    view = client.response_view(response)

    assert view["response_type"] == payload["response_type"]
    assert view["summary"] == payload["summary"]
    assert view["risk_level"] == payload["risk_level"]
    assert view["severity"] == payload["severity"]
    assert view["can_drive"] == payload["can_drive"]
    assert view["recommended_actions"] == payload["recommended_actions"]
    assert view["followup_questions"] == payload["followup_questions"]
    assert view["language"] == payload["language"]
    assert view["top_matches"] == payload["top_matches"]


def test_presenter_does_not_rerank_or_recalculate():
    matches = [
        {"problem": "First", "confidence": 41, "repair_cost": {"min": 1, "max": 2}},
        {"problem": "Second", "confidence": 99, "repair_cost": {"min": 3, "max": 4}},
    ]
    view = client.response_view({
        "response_type": "ranking",
        "top_matches": matches,
        "recommended_actions": ["Keep this exact action"],
        "followup_questions": ["Keep this exact question"],
    })

    assert view["top_matches"] == matches
    assert [item["problem"] for item in view["top_matches"]] == ["First", "Second"]
    assert [item["confidence"] for item in view["top_matches"]] == [41, 99]


def test_invalid_upstream_response_is_controlled(monkeypatch):
    class InvalidResponse:
        def __enter__(self):
            return self

        def __exit__(self, *args):
            return False

        def read(self, _limit):
            return b"not-json"

    monkeypatch.setattr(client.urllib.request, "urlopen", lambda *args, **kwargs: InvalidResponse())
    with pytest.raises(client.CanonicalDiagnosisUnavailable) as error:
        client.diagnose("battery weak")
    assert "temporarily unavailable" in str(error.value).lower()
    assert "not-json" not in str(error.value)


@pytest.mark.parametrize(
    "payload",
    [
        {"response_type": "ranking", "top_matches": "bad", "repair_cost": None},
        {"response_type": "ranking", "top_matches": [None, "bad", {"problem": "Valid"}]},
        {"response_type": "safety_guidance", "top_matches": [], "followup_questions": None},
        {"response_type": "clarification", "future_field": {"anything": True}},
        {"response_type": "error", "message": None},
    ],
)
def test_optional_malformed_null_and_future_fields_are_safe(payload):
    view = client.response_view(payload)
    assert view["response_type"] in {"ranking", "safety_guidance", "clarification", "error"}
    assert isinstance(view["top_matches"], list)
    assert isinstance(view["recommended_actions"], list)
    assert isinstance(view["followup_questions"], list)
