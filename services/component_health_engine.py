# ==========================================
# AMPYAN Component Health Engine (Improved)
# ==========================================

from datetime import datetime

def get_component_health(car):

    result = {}

    current_km = car.current_km or 0
    year = car.year or datetime.now().year
    age = datetime.now().year - year
    daily_km = car.daily_km or 30

    # =====================
    # USAGE MULTIPLIER
    # =====================

    usage_factor = 1

    if daily_km > 80:
        usage_factor = 1.25

    elif daily_km > 40:
        usage_factor = 1.1

    elif daily_km < 10:
        usage_factor = 0.9


    # =================================================
    # BRAKE HEALTH
    # =================================================

    brake_life = 40000

    brake_base_km = (
        car.brake_replaced_km
        or car.last_service_km
        or 0
    )

    brake_used = max(0, current_km - brake_base_km)

    brake_wear = (brake_used / brake_life) * usage_factor

    brake_health = max(0, 100 - int(brake_wear * 100))

    result["brake"] = brake_health


    # =================================================
    # CLUTCH HEALTH
    # =================================================

    clutch_life = 90000

    clutch_base_km = (
        car.clutch_replaced_km
        or car.last_service_km
        or 0
    )

    clutch_used = max(0, current_km - clutch_base_km)

    clutch_wear = (clutch_used / clutch_life) * usage_factor

    clutch_health = max(0, 100 - int(clutch_wear * 100))

    result["clutch"] = clutch_health


    # =================================================
    # TYRE HEALTH
    # =================================================

    tyre_life = 50000

    tyre_base_km = (
        car.tyre_replaced_km
        or car.last_service_km
        or 0
    )

    tyre_used = max(0, current_km - tyre_base_km)

    tyre_wear = (tyre_used / tyre_life) * usage_factor

    tyre_health = max(0, 100 - int(tyre_wear * 100))

    result["tyre"] = tyre_health


    # =================================================
    # BATTERY HEALTH
    # =================================================

    battery_life = 5

    if car.battery_replaced_year:

        battery_age = datetime.now().year - car.battery_replaced_year

    else:

        battery_age = age

    battery_wear = battery_age / battery_life

    battery_health = max(0, 100 - int(battery_wear * 100))

    result["battery"] = battery_health


    return result
def predict_component_life(car):

    current_km = car.current_km or 0

    brake_life = 50000
    tyre_life = 60000
    clutch_life = 90000

    brake_replaced = car.brake_replaced_km or 0
    tyre_replaced = car.tyre_replaced_km or 0
    clutch_replaced = car.clutch_replaced_km or 0

    brake_remaining = brake_life - (current_km - brake_replaced)
    tyre_remaining = tyre_life - (current_km - tyre_replaced)
    clutch_remaining = clutch_life - (current_km - clutch_replaced)

    return {
        "brake": max(brake_remaining,0),
        "tyre": max(tyre_remaining,0),
        "clutch": max(clutch_remaining,0)
    }