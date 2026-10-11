# =====================================
# AMPYAN Predictive Maintenance Engine
# =====================================

def get_maintenance_suggestions(car):

    suggestions = []

    km = car.current_km or 0
    age = 2026 - int(car.year)

    # ENGINE OIL
    if km >= 10000:
        suggestions.append("Engine oil replacement recommended")

    # AIR FILTER
    if km >= 15000:
        suggestions.append("Air filter inspection recommended")

    # SPARK PLUGS (Petrol / CNG)
    if car.fuel_type in ["Petrol", "CNG"]:
        if km >= 30000:
            suggestions.append("Spark plug inspection recommended")

    # BRAKE PADS
    if km >= 40000:
        suggestions.append("Brake pads inspection recommended")

    # COOLANT
    if km >= 50000:
        suggestions.append("Coolant replacement recommended")

    # BATTERY AGE
    if age >= 3:
        suggestions.append("Battery health check recommended")

    # HIGH DAILY USAGE
    if car.daily_km:
        if car.daily_km > 80:
            suggestions.append("High usage vehicle – frequent inspection recommended")

    return suggestions