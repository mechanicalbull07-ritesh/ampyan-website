# ==========================================
# AMPYAN Manufacturer Service Schedule Engine
# ==========================================

def get_service_schedule(car):

    schedule = []

    brand = (car.brand or "").lower()
    fuel = (car.fuel_type or "").lower()
    current_km = car.current_km or 0

    # base intervals
    steps = [10000, 20000, 30000, 40000, 60000, 80000, 100000]

    for step in steps:

        tasks = []

        # basic service
        if step % 10000 == 0:
            tasks.append("Engine oil replacement")
            tasks.append("General inspection")

        # filters
        if step % 20000 == 0:
            tasks.append("Air filter inspection")

        # brake service
        if step >= 30000:
            tasks.append("Brake inspection")

        # spark plugs (petrol)
        if fuel == "petrol" and step >= 60000:
            tasks.append("Spark plug replacement")

        # fuel filter (diesel)
        if fuel == "diesel" and step >= 30000:
            tasks.append("Fuel filter inspection")

        # coolant
        if step >= 80000:
            tasks.append("Coolant replacement")

        # suspension
        if step >= 60000:
            tasks.append("Suspension inspection")

        schedule.append({
            "km": step,
            "tasks": tasks
        })

    # show only future services
    future_schedule = []

    for item in schedule:
        if item["km"] > current_km:
            future_schedule.append(item)

    return future_schedule[:3]