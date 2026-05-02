# ==========================================
# AMPYAN Service Timeline Engine (Fixed)
# ==========================================

def generate_service_timeline(car):

    timeline = []

    current_km = car.current_km or 0
    last_service = car.last_service_km or 0
    fuel = car.fuel_type

    SERVICE_INTERVAL = 10000

    next_service = last_service + SERVICE_INTERVAL

    # NEXT SERVICE

    tasks = []

    tasks.append("Engine oil replacement")
    tasks.append("Air filter inspection")
    tasks.append("Brake inspection")

    if fuel == "Petrol":
        tasks.append("Spark plug inspection")

    if fuel == "Diesel":
        tasks.append("Fuel filter inspection")

    if fuel == "CNG":
        tasks.append("Valve clearance inspection")

    timeline.append({
        "km": next_service,
        "tasks": tasks
    })

    # NEXT + 10000

    second_service = next_service + SERVICE_INTERVAL

    timeline.append({
        "km": second_service,
        "tasks": [
            "Engine oil replacement",
            "Air filter inspection",
            "Brake inspection"
        ]
    })

    # NEXT + 20000

    third_service = second_service + SERVICE_INTERVAL

    timeline.append({
        "km": third_service,
        "tasks": [
            "Coolant inspection",
            "Brake fluid inspection",
            "Suspension inspection"
        ]
    })

    return timeline