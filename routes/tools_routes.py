from flask import Blueprint, render_template, request, jsonify, session
from flask_login import current_user
from models.models import Car, AIFeedback, db
from services.car_recommendation_service import recommend_cars, build_user_profile_summary

# AI ENGINE
from ai_engine.diagnostic_engine import diagnose_vehicle
from ai_engine.response_formatter import enrich_diagnosis_results

# FAILURE DATABASE
from failure_database import FAILURE_DATABASE

tools_bp = Blueprint("tools", __name__)


@tools_bp.route("/tools")
def tools():
    return render_template("tools.html")


@tools_bp.route("/tools/car-suggestion", methods=["GET", "POST"])
def car_suggestion():
    form_data = {
        "usage_mix": "city",
        "daily_run": 30,
        "family_use": "family",
        "budget": "mid",
        "fuel_preference": "any",
        "transmission": "any",
        "priority": "balanced",
        "occasional_need": "weekend",
    }
    recommendations = []
    profile_summary = None

    if request.method == "POST":
        for key in form_data:
            value = request.form.get(key)
            if value not in [None, ""]:
                form_data[key] = value

        recommendations = recommend_cars(form_data)
        profile_summary = build_user_profile_summary(form_data)

    return render_template(
        "car_recommendation.html",
        form_data=form_data,
        recommendations=recommendations,
        profile_summary=profile_summary
    )


@tools_bp.route("/tools/ai-diagnosis", methods=["GET", "POST"])
def ai_diagnosis_page():

    diagnosis_result = None
    questions = []

    if current_user.is_authenticated:

        cars = Car.query.filter_by(owner_id=current_user.id).all()

        default_car = Car.query.filter_by(
            owner_id=current_user.id,
            is_default=True
        ).first()

    else:
        cars = []
        default_car = None


    if request.method == "POST":

        problem = request.form.get("problem")

        if problem:

            results, questions = diagnose_vehicle(problem)

            print("RESULTS:", results)
            print("QUESTIONS:", questions)

            # 🔥 SAVE TOP RESULT FOR FEEDBACK
            if results:
                session["last_result"] = results[0]["issue"]

            causes = []

            for r in results[:3]:
                causes.append({
                    "name": r["issue"],
                    "probability": int(r["confidence"])
                })

            top_issue = results[0]["issue"] if results else None

            failure_data = None

            for failure in FAILURE_DATABASE:
                if failure.get("problem") == top_issue:
                    failure_data = failure
                    break

            cost_list = []

            if failure_data:

                cost_data = failure_data.get("repair_cost")

                if isinstance(cost_data, dict):

                    min_cost = cost_data.get("min")
                    max_cost = cost_data.get("max")

                    if min_cost and max_cost:
                        cost_list = [f"Estimated repair cost: ₹{min_cost} – ₹{max_cost}"]

                elif isinstance(cost_data, list):
                    cost_list = cost_data


            diagnosis_result = {
                "causes": causes,
                "severity": failure_data.get("severity", "Unknown").capitalize() if failure_data else "Unknown",
                "user_checks": failure_data.get("user_checks", []) if failure_data else [],
                "estimated_cost": cost_list,
                "advice": failure_data.get("advice", "Consult a mechanic.") if failure_data else "Consult a mechanic."
            }

    return render_template(
        "ai_diagnosis.html",
        cars=cars,
        default_car=default_car,
        diagnosis_result=diagnosis_result,
        questions=questions
    )


# ================= 🔥 FOLLOW-UP ANSWER ROUTE =================

@tools_bp.route("/tools/ai-diagnosis-followup", methods=["POST"])
def ai_diagnosis_followup():

    problem = request.form.get("problem")

    answers = {}

    for key in request.form:
        if key.startswith("q"):
            answers[key] = request.form.get(key)

    print("USER ANSWERS:", answers)

    results, questions = diagnose_vehicle(problem, answers)

    print("UPDATED RESULTS:", results)

    final_issue = results[0]["issue"] if results else "Unknown"

    # 🔥 SAVE RESULT FOR FEEDBACK
    if results:
        session["last_result"] = results[0]["issue"]

    # 🔥 ADD ADVICE TO RESULTS (IMPORTANT FIX)
    for r in results:
        for failure in FAILURE_DATABASE:
            if failure.get("problem") == r["issue"]:
                r["advice"] = failure.get("advice", "Consult a mechanic")
                break

    diagnosis_view = enrich_diagnosis_results(results, problem)

    return render_template(
        "diagnosis_result.html",
        results=diagnosis_view["results"],
        ui_text=diagnosis_view["ui_text"],
        response_language=diagnosis_view["language_code"],
        response_language_name=diagnosis_view["language_name"],
        final_issue=final_issue,
        questions=questions,
        problem=problem,
        car={"id": 0, "brand": "Your Car", "model": "", "year": ""}
    )


# ================= 🔥 FEEDBACK ROUTE =================

@tools_bp.route('/submit_feedback', methods=['POST'])
def submit_feedback():

    data = request.get_json()
    feedback = data.get("feedback")

    issue = session.get("last_result")

    print("USER FEEDBACK:", feedback)
    print("ISSUE:", issue)

    # 🔥 SAVE TO DATABASE (PERMANENT)
    new_feedback = AIFeedback(issue=issue, feedback=feedback)
    db.session.add(new_feedback)
    db.session.commit()

    print("SAVED TO DB")

    # 🔥 MEMORY UPDATE (IN-RUNTIME)
    for item in FAILURE_DATABASE:
        if item["problem"] == issue:

            if feedback == "yes":
                item["feedback"]["confirmed"] += 1

            elif feedback == "no":
                item["feedback"]["rejected"] += 1

            print("UPDATED FEEDBACK:", item["feedback"])
            break

    return jsonify({"status": "success"})
