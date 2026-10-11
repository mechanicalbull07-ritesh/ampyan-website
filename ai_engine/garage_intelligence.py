# ================= GARAGE INTELLIGENCE ENGINE =================

def analyze_vehicle_health(car):

    insights = []

    # -------- BRAKES --------
    if hasattr(car, "components") and car.components.get("brake"):

        brake_health = car.components["brake"]

        if brake_health < 40:
            insights.append({
                "component": "Brake Pads",
                "risk": "High",
                "message": "Brake pads likely worn out. Replace soon.",
                "cost": "₹1500 – ₹3500"
            })

        elif brake_health < 70:
            insights.append({
                "component": "Brake Pads",
                "risk": "Medium",
                "message": "Brake pads showing wear. Monitor condition.",
                "cost": "₹1500 – ₹3500"
            })


    # -------- TYRES --------
    if hasattr(car, "components") and car.components.get("tyre"):

        tyre_health = car.components["tyre"]

        if tyre_health < 50:
            insights.append({
                "component": "Tyres",
                "risk": "Medium",
                "message": "Tyres showing wear. Check tread depth.",
                "cost": "₹4000 – ₹12000"
            })


    # -------- BATTERY --------
    if hasattr(car, "components") and car.components.get("battery"):

        battery_health = car.components["battery"]

        if battery_health < 40:
            insights.append({
                "component": "Battery",
                "risk": "High",
                "message": "Battery weak. Replacement may be required.",
                "cost": "₹4000 – ₹8000"
            })


    return insights