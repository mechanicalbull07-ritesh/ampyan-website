# ==========================================
# AMPYAN Driving Pattern Analyzer
# ==========================================

def analyze_driving_pattern(car):

    result = {
        "pattern": "Normal Usage",
        "wear_level": "Normal",
        "maintenance_risk": "Low"
    }

    daily_km = car.daily_km or 0
    current_km = car.current_km or 0

    # ==============================
    # DRIVING INTENSITY
    # ==============================

    if daily_km > 80:

        result["pattern"] = "Heavy Usage"
        result["wear_level"] = "High"
        result["maintenance_risk"] = "High"

    elif daily_km > 40:

        result["pattern"] = "Moderate Usage"
        result["wear_level"] = "Moderate"
        result["maintenance_risk"] = "Medium"

    elif daily_km < 10:

        result["pattern"] = "Low Usage"
        result["wear_level"] = "Low"
        result["maintenance_risk"] = "Battery Drain Risk"

    # ==============================
    # VERY HIGH MILEAGE VEHICLE
    # ==============================

    if current_km > 100000:

        result["wear_level"] = "High"
        result["maintenance_risk"] = "High"

    return result