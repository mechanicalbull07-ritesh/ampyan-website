from flask import Blueprint, request, jsonify
from flask_login import login_required, current_user
from datetime import datetime
from models.models import db

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

    return jsonify({
        "reply": "AMPYAN AI chat assistant is currently disabled. Please use AI Diagnosis for automotive issue analysis."
    })
