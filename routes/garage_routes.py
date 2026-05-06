from datetime import datetime

from flask import Blueprint, render_template, request, redirect
from flask_login import login_required, current_user
from models.models import db, Car, DiagnosticLearning
from services.garage_summary import enrich_car_for_garage
from services.india_car_catalog import catalog_brands, garage_catalog_payload

garage_bp = Blueprint("garage", __name__)


def _safe_int(value, default=None):
    try:
        if value in [None, ""]:
            return default
        return int(value)
    except (TypeError, ValueError):
        return default


def _safe_date(value):
    try:
        if not value:
            return None
        return datetime.strptime(value, "%Y-%m-%d").date()
    except (TypeError, ValueError):
        return None


# ================= GARAGE =================

@garage_bp.route("/garage")
@login_required
def garage():

    cars = Car.query.filter_by(owner_id=current_user.id).all()

    for car in cars:

        enrich_car_for_garage(car)

    return render_template("garage.html", cars=cars)


# ================= GARAGE DASHBOARD =================

@garage_bp.route("/garage-dashboard")
@login_required
def garage_dashboard():

    cars = Car.query.filter_by(owner_id=current_user.id).all()

    for car in cars:

        enrich_car_for_garage(car)

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
        insurance_expiry = request.form.get("insurance_expiry")
        pollution_expiry = request.form.get("pollution_expiry")

        year = _safe_int(year)
        mileage = _safe_int(mileage)
        current_km = _safe_int(current_km, 0)
        last_service_km = _safe_int(last_service_km)
        daily_km = _safe_int(daily_km)

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
            insurance_expiry=_safe_date(insurance_expiry),
            pollution_expiry=_safe_date(pollution_expiry),

            is_default=True if not existing_car else False
        )

        db.session.add(car)
        db.session.commit()

        return redirect("/garage")

    return render_template(
        "add_car.html",
        car_brands=catalog_brands(),
        car_catalog=garage_catalog_payload(),
    )


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
        year = request.form.get("year")
        mileage = request.form.get("mileage")

        car.brand = request.form.get("brand")
        car.model = request.form.get("model")
        car.year = _safe_int(year)
        car.fuel_type = request.form.get("fuel")
        car.mileage = _safe_int(mileage)

        car.brake_replaced_km = _safe_int(request.form.get("brake_replaced_km"))
        car.tyre_replaced_km = _safe_int(request.form.get("tyre_replaced_km"))
        car.clutch_replaced_km = _safe_int(request.form.get("clutch_replaced_km"))
        car.battery_replaced_year = _safe_int(request.form.get("battery_replaced_year"))

        car.current_km = _safe_int(current_km, 0)
        car.daily_km = _safe_int(daily_km)
        car.last_service_km = _safe_int(last_service_km)
        car.insurance_expiry = _safe_date(request.form.get("insurance_expiry"))
        car.pollution_expiry = _safe_date(request.form.get("pollution_expiry"))

        if car.last_service_km:
            car.next_service_km = car.last_service_km + SERVICE_INTERVAL

        db.session.commit()

        return redirect("/garage")

    return render_template("edit_car.html", car=car)
