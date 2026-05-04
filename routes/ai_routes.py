from flask import Blueprint, request, jsonify
from flask_login import login_required, current_user
from datetime import datetime
from models.models import db
from ai_engine.diagnostic_engine import diagnose_vehicle

# ================= BLUEPRINT =================

ai_bp = Blueprint("ai", __name__)


# ================= AI ROUTE =================

@ai_bp.route("/ask-ai", methods=["POST"])
def ask_ai():

    data = request.get_json()

    if not data:
        return jsonify({"reply": "Invalid request."})

    user_message = data.get("message")

    if not user_message:
        return jsonify({"reply": "Please explain your issue clearly."})

    if current_user.is_authenticated:
        today = datetime.utcnow().date()

        if not current_user.ai_last_reset or current_user.ai_last_reset.date() != today:
            current_user.ai_uses_today = 0
            current_user.ai_last_reset = datetime.utcnow()
            db.session.commit()

        if current_user.role != "premium" and current_user.ai_uses_today >= 5:
            return jsonify({"reply": "Free AI limit reached (5 per day)."})

    try:
        results, questions = diagnose_vehicle(user_message)
        top_results = results[:3]
    except Exception:
        top_results = []
        questions = []

    if current_user.is_authenticated:
        current_user.ai_uses_today = (current_user.ai_uses_today or 0) + 1
        db.session.commit()

    if not top_results:
        return jsonify({
            "reply": "AMPYAN local AI needs a little more detail. Please mention the symptom, when it happens, and any warning light or sound."
        })

    lines = ["AMPYAN local AI diagnosis:"]
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
