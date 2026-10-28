# ==========================================
# AMPYAN Component Failure Prediction Engine
# ==========================================

def predict_component_failure(car):

    predictions = []

    current_km = car.current_km or 0
    year = int(car.year)
    age = 2026 - year
    daily_km = car.daily_km or 0


    # ==============================
    # BRAKE PAD FAILURE RISK
    # ==============================

    if current_km > 35000:

        risk = "Medium"

        if current_km > 45000:
            risk = "High"

        predictions.append({
            "component": "Brake Pads",
            "risk": risk,
            "advice": "Brake inspection recommended"
        })


    # ==============================
    # BATTERY FAILURE RISK
    # ==============================

    if age >= 3:

        risk = "Medium"

        if age >= 5:
            risk = "High"

        predictions.append({
            "component": "Battery",
            "risk": risk,
            "advice": "Battery health check recommended"
        })


    # ==============================
    # SUSPENSION WEAR
    # ==============================

    if current_km >= 60000:

        predictions.append({
            "component": "Suspension",
            "risk": "Medium",
            "advice": "Suspension inspection recommended"
        })


    # ==============================
    # CLUTCH WEAR
    # ==============================

    if current_km >= 80000:

        predictions.append({
            "component": "Clutch",
            "risk": "Medium",
            "advice": "Clutch inspection recommended"
        })


    # ==============================
    # HIGH USAGE VEHICLE
    # ==============================

    if daily_km > 80:

        predictions.append({
            "component": "General Wear",
            "risk": "Medium",
            "advice": "High usage vehicle – frequent inspection recommended"
        })


    return predictions