from flask import Blueprint, current_app, render_template, request, jsonify, session
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


def _safe_float(value, default=None):
    try:
        if value in [None, ""]:
            return default
        return float(value)
    except (TypeError, ValueError):
        return default


@tools_bp.route("/tools/fuel-cost", methods=["GET", "POST"])
def fuel_cost():
    result = None
    error = None
    form_data = {
        "distance": request.form.get("distance", ""),
        "daily_km": request.form.get("daily_km", ""),
        "mileage": request.form.get("mileage", ""),
        "fuel_price": request.form.get("fuel_price", ""),
    }

    if request.method == "POST":
        distance = _safe_float(form_data["distance"])
        daily_km = _safe_float(form_data["daily_km"])
        mileage = _safe_float(form_data["mileage"])
        fuel_price = _safe_float(form_data["fuel_price"])

        estimate_distance = distance if distance is not None else daily_km

        if estimate_distance is None or estimate_distance <= 0:
            error = "Enter trip distance or daily running."
        elif mileage is None or mileage <= 0:
            error = "Mileage must be greater than zero."
        elif fuel_price is None or fuel_price <= 0:
            error = "Fuel price must be greater than zero."
        else:
            trip_cost = (estimate_distance / mileage) * fuel_price
            daily_cost = ((daily_km / mileage) * fuel_price) if daily_km and daily_km > 0 else trip_cost
            result = {
                "fuel_used": round(estimate_distance / mileage, 2),
                "trip_cost": round(trip_cost, 2),
                "daily_cost": round(daily_cost, 2),
                "monthly_cost": round(daily_cost * 30, 2),
                "yearly_cost": round(daily_cost * 365, 2),
            }

    return render_template("fuel_cost.html", result=result, error=error, form_data=form_data)


@tools_bp.route("/tools/emi-calculator", methods=["GET", "POST"])
def emi_calculator():
    result = None
    error = None
    form_data = {
        "loan_amount": request.form.get("loan_amount", ""),
        "interest_rate": request.form.get("interest_rate", ""),
        "tenure": request.form.get("tenure", ""),
        "tenure_type": request.form.get("tenure_type", "months"),
        "down_payment": request.form.get("down_payment", ""),
    }

    if request.method == "POST":
        loan_amount = _safe_float(form_data["loan_amount"])
        interest_rate = _safe_float(form_data["interest_rate"])
        tenure = _safe_float(form_data["tenure"])
        down_payment = _safe_float(form_data["down_payment"], 0) or 0

        if loan_amount is None or loan_amount <= 0:
            error = "Loan amount must be greater than zero."
        elif interest_rate is None or interest_rate < 0:
            error = "Interest rate cannot be negative."
        elif tenure is None or tenure <= 0:
            error = "Tenure must be greater than zero."
        elif down_payment >= loan_amount:
            error = "Down payment must be less than loan amount."
        else:
            principal = loan_amount - down_payment
            months = int(tenure * 12) if form_data["tenure_type"] == "years" else int(tenure)
            monthly_rate = (interest_rate / 12) / 100

            if monthly_rate == 0:
                emi = principal / months
            else:
                factor = (1 + monthly_rate) ** months
                emi = principal * monthly_rate * factor / (factor - 1)

            total_payable = emi * months
            result = {
                "principal": round(principal, 2),
                "months": months,
                "monthly_emi": round(emi, 2),
                "total_interest": round(total_payable - principal, 2),
                "total_payable": round(total_payable, 2),
            }

    return render_template("emi_calculator.html", result=result, error=error, form_data=form_data)


@tools_bp.route("/tools/depreciation-calculator", methods=["GET", "POST"])
def depreciation_calculator():
    result = None
    error = None
    form_data = {
        "purchase_price": request.form.get("purchase_price", ""),
        "vehicle_age": request.form.get("vehicle_age", ""),
        "odometer": request.form.get("odometer", ""),
        "fuel_type": request.form.get("fuel_type", "Petrol"),
        "condition": request.form.get("condition", "good"),
    }

    if request.method == "POST":
        purchase_price = _safe_float(form_data["purchase_price"])
        vehicle_age = _safe_float(form_data["vehicle_age"])
        odometer = _safe_float(form_data["odometer"], 0) or 0

        if purchase_price is None or purchase_price <= 0:
            error = "Purchase price must be greater than zero."
        elif vehicle_age is None or vehicle_age < 0:
            error = "Vehicle age cannot be negative."
        elif odometer < 0:
            error = "Odometer cannot be negative."
        else:
            depreciation_rate = min(0.12 + (vehicle_age * 0.075), 0.82)
            if odometer > 100000:
                depreciation_rate += 0.08
            elif odometer > 60000:
                depreciation_rate += 0.04

            if form_data["fuel_type"] == "Diesel":
                depreciation_rate += 0.03
            elif form_data["fuel_type"] == "Electric":
                depreciation_rate += 0.05

            condition_adjustment = {
                "excellent": -0.05,
                "good": 0,
                "average": 0.05,
                "poor": 0.12,
            }.get(form_data["condition"], 0)

            depreciation_rate = min(max(depreciation_rate + condition_adjustment, 0.08), 0.9)
            depreciation_amount = purchase_price * depreciation_rate
            current_value = purchase_price - depreciation_amount
            result = {
                "current_value": round(current_value, 2),
                "depreciation_amount": round(depreciation_amount, 2),
                "depreciation_percentage": round(depreciation_rate * 100, 1),
            }

    return render_template("depreciation_calculator.html", result=result, error=error, form_data=form_data)


@tools_bp.route("/tools/maintenance-cost", methods=["GET", "POST"])
def maintenance_cost():
    result = None
    error = None
    form_data = {
        "vehicle_age": request.form.get("vehicle_age", ""),
        "current_km": request.form.get("current_km", ""),
        "fuel_type": request.form.get("fuel_type", "Petrol"),
        "service_type": request.form.get("service_type", "routine"),
    }

    if request.method == "POST":
        vehicle_age = _safe_float(form_data["vehicle_age"])
        current_km = _safe_float(form_data["current_km"])
        if vehicle_age is None or vehicle_age < 0:
            error = "Vehicle age cannot be negative."
        elif current_km is None or current_km < 0:
            error = "Current odometer cannot be negative."
        else:
            base = 4500
            if form_data["service_type"] == "major":
                base = 11000
            elif form_data["service_type"] == "repair":
                base = 16000
            if current_km > 80000:
                base += 4500
            elif current_km > 40000:
                base += 2500
            if vehicle_age > 7:
                base += 3500
            if form_data["fuel_type"] == "Diesel":
                base += 1800
            elif form_data["fuel_type"] == "Electric":
                base = max(base - 2200, 2500)
            result = {
                "estimated_min": round(base * 0.85, 2),
                "estimated_max": round(base * 1.35, 2),
                "note": "Estimated maintenance planning range. Actual workshop cost may vary.",
            }

    return render_template("maintenance_cost.html", result=result, error=error, form_data=form_data)


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

            current_app.logger.info("AI diagnosis completed with %s result(s)", len(results or []))

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

    results, questions = diagnose_vehicle(problem, answers)

    current_app.logger.info("AI diagnosis follow-up completed with %s result(s)", len(results or []))

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

    # 🔥 SAVE TO DATABASE (PERMANENT)
    new_feedback = AIFeedback(issue=issue, feedback=feedback)
    db.session.add(new_feedback)
    db.session.commit()

    current_app.logger.info("AI feedback saved")

    # 🔥 MEMORY UPDATE (IN-RUNTIME)
    for item in FAILURE_DATABASE:
        if item["problem"] == issue:

            if feedback == "yes":
                item["feedback"]["confirmed"] += 1

            elif feedback == "no":
                item["feedback"]["rejected"] += 1

            break

    return jsonify({"status": "success"})
