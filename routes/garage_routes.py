from flask import Blueprint, render_template, request, redirect
from flask_login import login_required, current_user
from models.models import db, Car, DiagnosticLearning
from ai_engine.garage_intelligence import analyze_vehicle_health

# ===== AI ENGINES =====
from services.car_health_engine import calculate_car_health
from services.maintenance_engine import get_maintenance_suggestions
from services.automotive_knowledge_engine import analyze_vehicle
from services.failure_prediction_engine import predict_component_failure
from services.service_timeline_engine import generate_service_timeline
from services.driving_pattern_engine import analyze_driving_pattern
from services.service_schedule_engine import get_service_schedule
from services.component_health_engine import get_component_health, predict_component_life

garage_bp = Blueprint("garage", __name__)


# ================= GARAGE =================

@garage_bp.route("/garage")
@login_required
def garage():

    cars = Car.query.filter_by(owner_id=current_user.id).all()

    for car in cars:

        car.health = calculate_car_health(car)
        car.analysis = analyze_vehicle(car)
        car.maintenance = get_maintenance_suggestions(car)
        car.failure_prediction = predict_component_failure(car)
        car.timeline = generate_service_timeline(car)
        car.driving_pattern = analyze_driving_pattern(car)
        car.service_schedule = get_service_schedule(car)
        car.components = get_component_health(car)
        car.insights = analyze_vehicle_health(car)

        # AI LIFE PREDICTION
        try:
            car.life_prediction = predict_component_life(car)
        except:
            car.life_prediction = None

    return render_template("garage.html", cars=cars)


# ================= GARAGE DASHBOARD =================

@garage_bp.route("/garage-dashboard")
@login_required
def garage_dashboard():

    cars = Car.query.filter_by(owner_id=current_user.id).all()

    for car in cars:

        car.health = calculate_car_health(car)
        car.analysis = analyze_vehicle(car)
        car.maintenance = get_maintenance_suggestions(car)
        car.failure_prediction = predict_component_failure(car)
        car.timeline = generate_service_timeline(car)
        car.driving_pattern = analyze_driving_pattern(car)
        car.service_schedule = get_service_schedule(car)
        car.components = get_component_health(car)
        car.insights = analyze_vehicle_health(car)

        # FIX FOR TEMPLATE ERROR
        try:
            car.life_prediction = predict_component_life(car)
        except:
            car.life_prediction = None

    diagnostics = DiagnosticLearning.query.filter_by(
        user_id=current_user.id
    ).order_by(DiagnosticLearning.created_at.desc()).limit(5).all()

    return render_template(
        "garage_dashboard.html",
        cars=cars,
        diagnostics=diagnostics
    )


# ================= ADD CAR =================

@garage_bp.route("/add-car", methods=["GET","POST"])
@login_required
def add_car():

    if request.method == "POST":

        brand = request.form.get("brand")
        model = request.form.get("model")
        year = request.form.get("year")
        fuel = request.form.get("fuel")
        mileage = request.form.get("mileage")

        last_service_km = request.form.get("last_service_km")
        daily_km = request.form.get("daily_km")
        current_km = request.form.get("current_km")

        year = int(year) if year else None
        mileage = int(mileage) if mileage else None
        current_km = int(current_km) if current_km else 0
        last_service_km = int(last_service_km) if last_service_km else None
        daily_km = int(daily_km) if daily_km else None

        SERVICE_INTERVAL = 10000
        next_service_km = None

        if last_service_km:
            next_service_km = last_service_km + SERVICE_INTERVAL

        existing_car = Car.query.filter_by(owner_id=current_user.id).first()

        car = Car(

            owner_id=current_user.id,

            brand=brand,
            model=model,
            year=year,

            fuel_type=fuel,
            mileage=mileage,

            current_km=current_km,
            last_service_km=last_service_km,
            next_service_km=next_service_km,
            daily_km=daily_km,

            is_default=True if not existing_car else False
        )

        db.session.add(car)
        db.session.commit()

        return redirect("/garage")

    return render_template("add_car.html")


# ================= SET DEFAULT CAR =================

@garage_bp.route("/set-default-car/<int:car_id>")
@login_required
def set_default_car(car_id):

    cars = Car.query.filter_by(owner_id=current_user.id).all()

    for c in cars:
        c.is_default = False

    car = Car.query.get_or_404(car_id)

    if car.owner_id != current_user.id:
        return "Unauthorized"

    car.is_default = True
    db.session.commit()

    return redirect("/garage")


# ================= DELETE CAR =================

@garage_bp.route("/delete-car/<int:car_id>")
@login_required
def delete_car(car_id):

    car = Car.query.get_or_404(car_id)

    if car.owner_id != current_user.id:
        return "Unauthorized"

    db.session.delete(car)
    db.session.commit()

    return redirect("/garage")


# ================= EDIT CAR =================

@garage_bp.route("/edit-car/<int:car_id>", methods=["GET","POST"])
@login_required
def edit_car(car_id):

    car = Car.query.get_or_404(car_id)

    if car.owner_id != current_user.id:
        return redirect("/garage")

    if request.method == "POST":

        SERVICE_INTERVAL = 10000

        current_km = request.form.get("current_km")
        daily_km = request.form.get("daily_km")
        last_service_km = request.form.get("last_service_km")

        car.brake_replaced_km = request.form.get("brake_replaced_km")
        car.tyre_replaced_km = request.form.get("tyre_replaced_km")
        car.clutch_replaced_km = request.form.get("clutch_replaced_km")
        car.battery_replaced_year = request.form.get("battery_replaced_year")

        car.current_km = int(current_km) if current_km else 0
        car.daily_km = int(daily_km) if daily_km else None
        car.last_service_km = int(last_service_km) if last_service_km else None

        if car.last_service_km:
            car.next_service_km = car.last_service_km + SERVICE_INTERVAL

        db.session.commit()

        return redirect("/garage")

    return render_template("edit_car.html", car=car)