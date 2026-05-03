from datetime import date, datetime

from services.automotive_knowledge_engine import analyze_vehicle
from services.car_health_engine import calculate_car_health
from services.component_health_engine import get_component_health, predict_component_life
from services.driving_pattern_engine import analyze_driving_pattern
from services.failure_prediction_engine import predict_component_failure
from ai_engine.garage_intelligence import analyze_vehicle_health
from services.maintenance_engine import get_maintenance_suggestions
from services.service_schedule_engine import get_service_schedule
from services.service_timeline_engine import generate_service_timeline


SERVICE_INTERVAL_KM = 10000


def _safe_int(value, fallback=0):
    try:
        if value in [None, ""]:
            return fallback
        return int(value)
    except (TypeError, ValueError):
        return fallback


def _date_status(value):
    if not value:
        return {"date": None, "days_left": None, "status": "Not Added", "tone": "muted"}

    today = date.today()
    expiry_date = value.date() if isinstance(value, datetime) else value
    days_left = (expiry_date - today).days

    if days_left < 0:
        status = "Expired"
        tone = "red"
    elif days_left <= 30:
        status = "Expiring Soon"
        tone = "yellow"
    else:
        status = "Valid"
        tone = "green"

    return {
        "date": expiry_date.isoformat(),
        "days_left": days_left,
        "status": status,
        "tone": tone,
    }


def _service_progress(car):
    current_km = _safe_int(car.current_km)
    last_service_km = _safe_int(car.last_service_km)
    next_service_km = _safe_int(car.next_service_km)

    if not next_service_km and last_service_km:
        next_service_km = last_service_km + SERVICE_INTERVAL_KM

    remaining_km = next_service_km - current_km if next_service_km else None
    driven_since_service = max(current_km - last_service_km, 0) if last_service_km else 0
    progress_percent = min(round((driven_since_service / SERVICE_INTERVAL_KM) * 100), 100) if last_service_km else 0

    if remaining_km is None:
        status = "Add service data"
        tone = "muted"
    elif remaining_km <= 0:
        status = "Overdue"
        tone = "red"
    elif remaining_km <= 1000:
        status = "Due Soon"
        tone = "yellow"
    else:
        status = "Healthy"
        tone = "green"

    daily_km = _safe_int(car.daily_km)
    days_left = round(remaining_km / daily_km) if remaining_km is not None and daily_km else None

    return {
        "last_service_km": last_service_km or None,
        "next_service_km": next_service_km or None,
        "remaining_km": remaining_km,
        "days_left": days_left,
        "progress_percent": progress_percent,
        "status": status,
        "tone": tone,
    }


def _fuel_cost(car, fuel_price=105):
    daily_km = _safe_int(car.daily_km)
    mileage = _safe_int(car.mileage)

    if not daily_km or not mileage:
        return {
            "daily_cost": None,
            "monthly_cost": None,
            "fuel_price": fuel_price,
            "summary": "Add daily running and mileage",
        }

    daily_cost = round((daily_km / mileage) * fuel_price, 2)
    return {
        "daily_cost": daily_cost,
        "monthly_cost": round(daily_cost * 30, 2),
        "fuel_price": fuel_price,
        "summary": f"Approx ₹{daily_cost}/day at ₹{fuel_price}/L",
    }


def _usage_insight(car):
    daily_km = _safe_int(car.daily_km)
    mileage = _safe_int(car.mileage)
    monthly_km = daily_km * 30 if daily_km else None

    if daily_km > 80:
        status = "Heavy Usage"
        tone = "yellow"
    elif daily_km >= 25:
        status = "Regular Usage"
        tone = "blue"
    elif daily_km:
        status = "Light Usage"
        tone = "green"
    else:
        status = "Usage Missing"
        tone = "muted"

    return {
        "daily_km": daily_km or None,
        "monthly_km": monthly_km,
        "mileage": mileage or None,
        "status": status,
        "tone": tone,
    }


def _maintenance_cost_estimate(car):
    age = max(datetime.now().year - _safe_int(car.year, datetime.now().year), 0)
    current_km = _safe_int(car.current_km)
    base = 4500

    if current_km > 100000:
        base += 5000
    elif current_km > 60000:
        base += 3000
    elif current_km > 30000:
        base += 1500

    if age >= 8:
        base += 4000
    elif age >= 5:
        base += 2000

    if car.fuel_type == "Diesel":
        base += 1500
    elif car.fuel_type == "Electric":
        base = max(base - 2000, 2500)

    return {
        "estimated_min": round(base * 0.8),
        "estimated_max": round(base * 1.35),
        "label": "Routine annual estimate",
        "disclaimer": "Estimated for planning only. Actual workshop cost may vary.",
    }


def enrich_car_for_garage(car):
    car.health = calculate_car_health(car)
    car.analysis = analyze_vehicle(car)
    car.maintenance = get_maintenance_suggestions(car)
    car.failure_prediction = predict_component_failure(car)
    car.timeline = generate_service_timeline(car)
    car.driving_pattern = analyze_driving_pattern(car)
    car.service_schedule = get_service_schedule(car)
    car.components = get_component_health(car)
    car.insights = analyze_vehicle_health(car)
    try:
        car.life_prediction = predict_component_life(car)
    except Exception:
        car.life_prediction = None

    car.garage_summary = build_garage_summary(car)
    return car


def build_garage_summary(car):
    health = getattr(car, "health", None) or calculate_car_health(car)
    return {
        "vehicle": {
            "id": car.id,
            "brand": car.brand,
            "model": car.model,
            "year": car.year,
            "fuel_type": car.fuel_type,
            "is_default": car.is_default,
        },
        "usage": _usage_insight(car),
        "service": _service_progress(car),
        "health": health,
        "fuel_cost": _fuel_cost(car),
        "expiry": {
            "insurance": _date_status(getattr(car, "insurance_expiry", None)),
            "pollution": _date_status(getattr(car, "pollution_expiry", None)),
        },
        "cost_insights": _maintenance_cost_estimate(car),
        "component_health": getattr(car, "components", None) or get_component_health(car),
        "maintenance": getattr(car, "maintenance", None) or get_maintenance_suggestions(car),
    }


def serialize_garage_car(car):
    summary = getattr(car, "garage_summary", None) or build_garage_summary(car)
    service = summary["service"]
    expiry = summary["expiry"]
    return {
        "id": car.id,
        "brand": car.brand,
        "model": car.model,
        "year": car.year,
        "fuel_type": car.fuel_type,
        "mileage": car.mileage,
        "current_km": car.current_km,
        "last_service_km": car.last_service_km,
        "next_service_km": car.next_service_km,
        "daily_km": car.daily_km,
        "insurance_expiry": expiry["insurance"]["date"],
        "pollution_expiry": expiry["pollution"]["date"],
        "is_default": car.is_default,
        "created_at": car.created_at.isoformat() if car.created_at else None,
        "health_score": summary["health"]["score"],
        "health_status": summary["health"]["status"],
        "service_reminder": service,
        "fuel_cost": summary["fuel_cost"],
        "usage_insight": summary["usage"],
        "expiry_status": expiry,
        "cost_insights": summary["cost_insights"],
        "component_health": summary["component_health"],
        "maintenance": summary["maintenance"],
    }
