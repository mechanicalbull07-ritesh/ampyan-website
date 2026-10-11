from flask import Blueprint, current_app, render_template, request, jsonify, session
from flask_login import current_user
from models.models import Car, AIFeedback, db
from services.car_recommendation_service import recommend_cars, build_user_profile_summary
from services.dashboard_light_intake import dashboard_light_context
from services.analytics_service import safe_track_event, action_event_id
from service_estimator import estimate_service

from services.canonical_diagnosis_client import (
    CanonicalDiagnosisUnavailable,
    diagnose as canonical_diagnose,
    process_answers as canonical_process_answers,
    response_view as canonical_response_view,
)

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
        "car_make": request.form.get("car_make", ""),
        "car_model": request.form.get("car_model", ""),
        "fuel_type": request.form.get("fuel_type", "petrol"),
        "transmission": request.form.get("transmission", "manual"),
        "vehicle_age_years": request.form.get("vehicle_age_years", request.form.get("vehicle_age", "")),
        "odometer_km": request.form.get("odometer_km", request.form.get("current_km", "")),
        "average_daily_km": request.form.get("average_daily_km", ""),
        "usage_type": request.form.get("usage_type", "city"),
        "driving_style": request.form.get("driving_style", "normal"),
        "last_service_km": request.form.get("last_service_km", ""),
        "last_service_months_ago": request.form.get("last_service_months_ago", ""),
        "last_service_date": request.form.get("last_service_date", ""),
        "query": request.form.get("query", ""),
    }

    if request.method == "POST":
        vehicle_age = _safe_float(form_data["vehicle_age_years"])
        current_km = _safe_float(form_data["odometer_km"])
        if vehicle_age is None or vehicle_age < 0:
            error = "Vehicle age cannot be negative."
        elif current_km is None or current_km < 0:
            error = "Current odometer cannot be negative."
        else:
            result = estimate_service(form_data)

    return render_template("maintenance_cost.html", result=result, error=error, form_data=form_data)


@tools_bp.route("/api/service-estimator", methods=["POST"])
def api_service_estimator():
    data = request.get_json(silent=True) or {}
    result = estimate_service(data)
    return jsonify(result)


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
        problem = (request.form.get("problem") or "").strip()
        diagnosis_payload = {"feature": "diagnosis"}
        event_id = action_event_id(request.form.get("analytics_request_token"))
        if event_id:
            diagnosis_payload["event_id"] = event_id
        extra_context = dashboard_light_context(request.files, request.form)
        if extra_context:
            problem = f"{problem or ''} {extra_context}".strip()
        selected_car = Car.query.get(request.form.get("car_id")) if request.form.get("car_id") else default_car
        if not problem:
            return render_template(
                "canonical_diagnosis_result.html",
                diagnosis=None,
                diagnosis_error="Please describe the vehicle problem.",
                problem=problem,
                car=selected_car,
            )
        safe_track_event("diagnosis_started", diagnosis_payload)
        try:
            diagnosis = canonical_response_view(canonical_diagnose(problem))
            matches = diagnosis["top_matches"]
            if diagnosis["success"] and diagnosis["response_type"] in {"ranking", "safety_guidance"} and (matches or diagnosis["summary"]):
                safe_track_event("diagnosis_completed", diagnosis_payload)
            current_app.logger.info(
                "Canonical AI diagnosis completed response_type=%s results=%s",
                diagnosis["response_type"],
                len(matches),
            )
            if matches:
                session["last_result"] = matches[0].get("problem") or matches[0].get("issue")
            session["diagnosis_candidates"] = [
                item.get("problem") or item.get("issue")
                for item in matches
                if item.get("problem") or item.get("issue")
            ]
            return render_template(
                "canonical_diagnosis_result.html",
                diagnosis=diagnosis,
                diagnosis_error=None,
                problem=problem,
                car=selected_car,
            )
        except CanonicalDiagnosisUnavailable as exc:
            current_app.logger.warning(
                "Canonical diagnosis unavailable error=%s", exc.__class__.__name__
            )
            return render_template(
                "canonical_diagnosis_result.html",
                diagnosis=None,
                diagnosis_error=str(exc),
                problem=problem,
                car=selected_car,
            )

    return render_template(
        "ai_diagnosis.html",
        cars=cars,
        default_car=default_car,
    )


# ================= 🔥 FOLLOW-UP ANSWER ROUTE =================

@tools_bp.route("/tools/ai-diagnosis-followup", methods=["POST"])
def ai_diagnosis_followup():
    problem = (request.form.get("problem") or "").strip()
    diagnosis_payload = {"feature": "diagnosis"}
    event_id = action_event_id(request.form.get("analytics_request_token"))
    if event_id:
        diagnosis_payload["event_id"] = event_id
    answers = {
        key: request.form.get(key)
        for key in request.form
        if key.startswith("q")
    }
    problems = [value for value in request.form.getlist("problems") if value]
    if not problems:
        problems = list(session.get("diagnosis_candidates") or [])
    if problems or problem or answers:
        safe_track_event("diagnosis_started", diagnosis_payload)
    car = Car.query.get(request.form.get("car_id")) if request.form.get("car_id") else None
    try:
        diagnosis = canonical_response_view(
            canonical_process_answers(problems, answers, problem)
        )
        matches = diagnosis["top_matches"]
        if diagnosis["success"] and diagnosis["response_type"] in {"ranking", "safety_guidance"} and (matches or diagnosis["summary"]):
            safe_track_event("diagnosis_completed", diagnosis_payload)
        if matches:
            session["last_result"] = matches[0].get("problem") or matches[0].get("issue")
        return render_template(
            "canonical_diagnosis_result.html",
            diagnosis=diagnosis,
            diagnosis_error=None,
            problem=problem,
            car=car,
        )
    except CanonicalDiagnosisUnavailable as exc:
        current_app.logger.warning(
            "Canonical diagnosis follow-up unavailable error=%s", exc.__class__.__name__
        )
        return render_template(
            "canonical_diagnosis_result.html",
            diagnosis=None,
            diagnosis_error=str(exc),
            problem=problem,
            car=car,
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
