import json
from pathlib import Path

import pytest

import routes.tools_routes as tools_routes
import app as app_module


app = app_module.app


@pytest.fixture(autouse=True)
def _clear_rate_limit():
    app_module.rate_limit_hits.clear()


SNAPSHOTS = json.loads((
    Path(__file__).resolve().parents[2]
    / "ampyan_clean"
    / "test"
    / "fixtures"
    / "diagnosis_53_contract_responses.json"
).read_text(encoding="utf-8"))


def test_effective_website_route_renders_canonical_ranking(monkeypatch):
    payload = {
        "response_version": "diagnosis-v1",
        "response_type": "ranking",
        "success": True,
        "language": "en",
        "summary": "Battery Weak",
        "risk_level": "moderate",
        "severity": "moderate",
        "can_drive": None,
        "recommended_actions": ["Check battery voltage."],
        "followup_questions": [{"id": "q1", "text": "Are the lights dim?"}],
        "top_matches": [{
            "problem": "Battery Weak",
            "confidence": 68,
            "severity": "moderate",
            "repair_cost": {
                "currency": "INR", "min": 1500, "max": 4500, "label": "₹1,500–₹4,500",
            },
        }],
    }
    monkeypatch.setattr(tools_routes, "canonical_diagnose", lambda problem: payload)

    response = app.test_client().post(
        "/tools/ai-diagnosis", data={"problem": "battery weak"}
    )
    html = response.get_data(as_text=True)

    assert response.status_code == 200
    assert "Battery Weak" in html
    assert "68%" in html
    assert "₹1,500–₹4,500" in html
    assert "Check battery voltage." in html
    assert "Are the lights dim?" in html


def test_effective_website_route_renders_safety_guidance(monkeypatch):
    payload = {
        "response_version": "diagnosis-v1",
        "response_type": "safety_guidance",
        "success": True,
        "language": "en",
        "summary": "Stop safely and switch the engine off.",
        "risk_level": "critical",
        "severity": "critical",
        "can_drive": False,
        "recommended_actions": ["Arrange a tow."],
        "followup_questions": ["Is there steam or smoke?"],
        "top_matches": [],
    }
    monkeypatch.setattr(tools_routes, "canonical_diagnose", lambda problem: payload)

    response = app.test_client().post(
        "/tools/ai-diagnosis", data={"problem": "car overheating"}
    )
    html = response.get_data(as_text=True)

    assert response.status_code == 200
    assert "Safety Warning" in html
    assert "Stop safely and switch the engine off." in html
    assert "Arrange a tow." in html
    assert "Is there steam or smoke?" in html
    assert "No Diagnosis Found" not in html


def test_ranking_semantic_order_and_cause_order(monkeypatch):
    payload = {
        "response_type": "ranking",
        "language": "en",
        "summary": "Canonical summary",
        "risk_level": "high",
        "can_drive": False,
        "recommended_actions": ["Canonical next action"],
        "followup_questions": [{"id": "q1", "text": "Canonical question"}],
        "top_matches": [
            {"problem": "First cause", "confidence": 71, "repair_cost": {"label": "₹1–₹2"}},
            {"problem": "Second cause", "confidence": 64, "repair_cost": {}},
            {"problem": "Third cause", "confidence": 51, "repair_cost": {}},
        ],
    }
    monkeypatch.setattr(tools_routes, "canonical_diagnose", lambda problem: payload)
    html = app.test_client().post("/tools/ai-diagnosis", data={"problem": "x"}).get_data(as_text=True)

    headings = [
        "Risk and Driveability", "Diagnosis Summary", "Top Possible Causes",
        "Recommended Next Action", "Continue Diagnosis", "Estimated Repair Cost",
        "Additional Details",
    ]
    positions = [html.index(value) for value in headings]
    assert positions == sorted(positions)
    assert html.index("First cause") < html.index("Second cause") < html.index("Third cause")
    assert "71%" in html and "64%" in html and "51%" in html


@pytest.mark.parametrize("snapshot", SNAPSHOTS, ids=[item["id"] for item in SNAPSHOTS])
def test_all_53_snapshots_render_without_semantic_loss(monkeypatch, snapshot):
    payload = snapshot["payload"]
    monkeypatch.setattr(tools_routes, "canonical_diagnose", lambda problem: payload)
    response = app.test_client().post("/tools/ai-diagnosis", data={"problem": snapshot["id"]})
    html = response.get_data(as_text=True)

    assert response.status_code == 200
    assert "No diagnosis match" not in html
    for value in (payload.get("summary"), payload.get("message")):
        if value:
            assert value in html
    for match in payload.get("top_matches") or []:
        assert match["problem"] in html
        assert f'{match["confidence"]}%' in html
        label = (match.get("repair_cost") or {}).get("label")
        if label and match is payload["top_matches"][0]:
            assert label in html
    for action in payload.get("recommended_actions") or []:
        assert action in html
    for question in payload.get("followup_questions") or []:
        text = question.get("text") if isinstance(question, dict) else question
        assert text in html


def test_clarification_is_valid_and_actionable(monkeypatch):
    payload = {
        "response_type": "clarification", "language": "hinglish",
        "summary": "Thodi aur information chahiye.",
        "message": "Fuel mode confirm karein.",
        "followup_questions": [{"id": "fuel", "text": "Petrol, CNG ya diesel?"}],
        "top_matches": [], "recommended_actions": [],
    }
    monkeypatch.setattr(tools_routes, "canonical_diagnose", lambda problem: payload)
    html = app.test_client().post("/tools/ai-diagnosis", data={"problem": "pickup nahi"}).get_data(as_text=True)
    assert "More Information Needed" in html
    assert "Petrol, CNG ya diesel?" in html
    assert "Continue Diagnosis" in html
    assert "Diagnosis temporarily unavailable" not in html


def test_controlled_error_has_both_recovery_actions(monkeypatch):
    def unavailable(_problem):
        raise tools_routes.CanonicalDiagnosisUnavailable("Please try again.")

    monkeypatch.setattr(tools_routes, "canonical_diagnose", unavailable)
    html = app.test_client().post("/tools/ai-diagnosis", data={"problem": "battery"}).get_data(as_text=True)
    assert "Diagnosis is temporarily unavailable" in html
    assert "Retry" in html
    assert "Start New Diagnosis" in html
    assert "Traceback" not in html
