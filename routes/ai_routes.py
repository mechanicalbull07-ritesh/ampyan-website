from flask import Blueprint, request, jsonify
from flask_login import login_required, current_user
from datetime import datetime
from models.models import db
from services.diagnosis_safety import safe_diagnose_vehicle

# ================= BLUEPRINT =================

ai_bp = Blueprint("ai", __name__)


def local_ai_fallback(message):
    text = (message or "").lower()
    if any(word in text for word in ["battery", "start", "starting", "self"]):
        return "AMPYAN Vehicle Intelligence: Battery voltage, terminal corrosion, starter motor and alternator charging should be checked first. If the car starts slow only in the morning, begin with a battery load test."
    if any(word in text for word in ["brake", "vibration", "disc", "pad"]):
        return "AMPYAN Vehicle Intelligence: Brake vibration usually needs brake disc runout check, pad condition check and wheel balancing inspection. Avoid high-speed driving until brakes are inspected."
    if any(word in text for word in ["mileage", "fuel", "average"]):
        return "AMPYAN Vehicle Intelligence: Mileage drop commonly comes from tyre pressure, clogged air filter, brake drag, old spark plugs, traffic change or fuel quality. Start with tyre pressure and OBD fuel-trim scan."
    if any(word in text for word in ["ac", "cooling", "compressor"]):
        return "AMPYAN Vehicle Intelligence: Weak AC cooling can come from low refrigerant, condenser dust, radiator fan weakness or cabin filter blockage. In traffic, fan and condenser airflow are important checks."
    if any(word in text for word in ["engine", "noise", "pickup", "power"]):
        return "AMPYAN Vehicle Intelligence: Engine power/noise issues need OBD scan, engine oil level check, air filter check and misfire/fuel pressure inspection. Share warning lights or when it happens for a sharper answer."
    return "AMPYAN Vehicle Intelligence: Please mention the symptom, when it happens, car fuel type, warning lights and recent service history. I can guide likely checks from AMPYAN's local automotive knowledge."


# ================= INTELLIGENCE ROUTE =================

@ai_bp.route("/ask-ai", methods=["POST"])
def ask_ai():

    data = request.get_json(silent=True) or request.form

    if not data:
        return jsonify({"reply": "Invalid request."})

    user_message = (data.get("message") or data.get("problem") or data.get("q") or "").strip()

    if not user_message:
        return jsonify({"reply": "Please explain your issue clearly."})

    if current_user.is_authenticated:
        today = datetime.utcnow().date()

        if not current_user.ai_last_reset or current_user.ai_last_reset.date() != today:
            current_user.ai_uses_today = 0
            current_user.ai_last_reset = datetime.utcnow()
            db.session.commit()

        if current_user.role != "premium" and current_user.ai_uses_today >= 5:
            return jsonify({"reply": "Free intelligence limit reached (5 per day)."})

    results, questions = safe_diagnose_vehicle(user_message, route_name="ask_ai")
    top_results = results[:3]

    if current_user.is_authenticated:
        current_user.ai_uses_today = (current_user.ai_uses_today or 0) + 1
        db.session.commit()

    if not top_results:
        return jsonify({"reply": local_ai_fallback(user_message)})

    lines = ["AMPYAN Vehicle Intelligence report:"]
    for index, result in enumerate(top_results, start=1):
        lines.append(
            f"{index}. {result.get('issue', 'Possible issue')} - {result.get('confidence', 0)}% confidence"
        )
        reason = result.get("reason")
        if reason:
            lines.append(f"   Reason: {reason}")

    if questions:
        lines.append("Next checks:")
        for question in questions[:3]:
            lines.append(f"- {question.get('text') if isinstance(question, dict) else question}")

    return jsonify({"reply": "\n".join(lines)})
