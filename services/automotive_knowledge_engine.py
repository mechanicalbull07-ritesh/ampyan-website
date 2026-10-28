# ==========================================
# AMPYAN Automotive Knowledge Engine v2
# ==========================================

def analyze_vehicle(car):

    result = {
        "health_score": 100,
        "status": "Excellent",
        "warnings": [],
        "maintenance": [],
        "next_service_km": None,
        "service_plan": []
    }

    current_km = car.current_km or 0
    year = int(car.year)
    age = 2026 - year
    daily_km = car.daily_km or 0

    # ==================================
    # AGE FACTOR
    # ==================================

    if age > 10:
        result["health_score"] -= 20
        result["warnings"].append("Old vehicle age")

    elif age > 5:
        result["health_score"] -= 10


    # ==================================
    # MILEAGE FACTOR
    # ==================================

    if current_km > 100000:
        result["health_score"] -= 20
        result["warnings"].append("High mileage vehicle")

    elif current_km > 60000:
        result["health_score"] -= 10


    # ==================================
    # DAILY USAGE FACTOR
    # ==================================

    if daily_km > 80:
        result["health_score"] -= 15
        result["warnings"].append("Very high daily usage")

    elif daily_km > 40:
        result["health_score"] -= 5


    # ==================================
    # SERVICE STATUS
    # ==================================

    if car.next_service_km and current_km:

        remaining = car.next_service_km - current_km
        result["next_service_km"] = remaining

        if remaining <= 0:
            result["health_score"] -= 20
            result["warnings"].append("Service overdue")

        elif remaining <= 2000:
            result["health_score"] -= 10
            result["warnings"].append("Service due soon")


    # ==================================
    # COMPONENT WEAR LOGIC
    # ==================================

    if current_km >= 35000:
        result["maintenance"].append("Brake pads inspection recommended")

    if current_km >= 60000:
        result["maintenance"].append("Suspension inspection recommended")

    if current_km >= 80000:
        result["maintenance"].append("Clutch wear inspection recommended")

    if age >= 3:
        result["maintenance"].append("Battery health check recommended")


    # ==================================
    # FUEL TYPE LOGIC
    # ==================================

    if car.fuel_type == "Petrol":

        if current_km >= 30000:
            result["maintenance"].append("Spark plug inspection recommended")

    if car.fuel_type == "Diesel":

        if current_km >= 20000:
            result["maintenance"].append("Fuel filter inspection recommended")

    if car.fuel_type == "CNG":

        result["maintenance"].append("Valve clearance inspection recommended")


    # ==================================
    # NEXT 10,000 KM SERVICE PLAN
    # ==================================

    if current_km >= 10000:
        result["service_plan"].append("Engine oil change")

    if current_km >= 15000:
        result["service_plan"].append("Air filter inspection")

    if current_km >= 20000:
        result["service_plan"].append("Brake inspection")

    if current_km >= 30000:
        result["service_plan"].append("Cabin filter replacement")

    if current_km >= 40000:
        result["service_plan"].append("Tyre inspection")


    # ==================================
    # HEALTH LIMIT
    # ==================================

    if result["health_score"] < 0:
        result["health_score"] = 0


    # ==================================
    # STATUS
    # ==================================

    if result["health_score"] >= 85:
        result["status"] = "Excellent"

    elif result["health_score"] >= 70:
        result["status"] = "Good"

    elif result["health_score"] >= 50:
        result["status"] = "Average"

    else:
        result["status"] = "Poor"


    return result