from datetime import datetime


# ================= SAFE INT =================

def safe_int(value):

    try:
        if value is None or value == "":
            return None
        return int(value)
    except:
        return None


# ================= MAIN HEALTH ENGINE =================

def calculate_car_health(car):

    score = 0
    reasons = []

    current_km = safe_int(car.current_km) or 0

    # ======================
    # 1. SERVICE STATUS (35)
    # ======================

    service_score = 35

    next_service_km = safe_int(car.next_service_km)

    if next_service_km and current_km:

        remaining = next_service_km - current_km

        if remaining > 5000:
            service_score = 35

        elif remaining > 1000:
            service_score = 25
            reasons.append("Service due soon")

        elif remaining > 0:
            service_score = 15
            reasons.append("Service due")

        else:
            service_score = 5
            reasons.append("Service overdue")

    score += service_score


    # ======================
    # 2. AGE VS KM (30)
    # ======================

    age_score = 30

    if car.year and current_km:

        current_year = datetime.now().year
        age = current_year - car.year

        expected_km = age * 12000

        if expected_km > 0:

            ratio = current_km / expected_km

            if 0.5 <= ratio <= 1.2:
                age_score = 30

            elif 0.3 <= ratio < 0.5:
                age_score = 26
                reasons.append("Car used less than average")

            elif 1.2 < ratio <= 1.6:
                age_score = 22
                reasons.append("Car used heavily")

            else:
                age_score = 15
                reasons.append("Very heavy usage")

    score += age_score


    # ======================
    # 3. TOTAL KM WEAR (20)
    # ======================

    km_score = 20

    if current_km:

        if current_km < 30000:
            km_score = 20

        elif current_km < 60000:
            km_score = 17

        elif current_km < 100000:
            km_score = 14

        elif current_km < 150000:
            km_score = 10
            reasons.append("High mileage")

        else:
            km_score = 6
            reasons.append("Very high mileage")

    score += km_score


    # ======================
    # 4. DRIVING PATTERN (10)
    # ======================

    driving_score = 10

    daily_km = safe_int(car.daily_km)

    if daily_km:

        if 10 <= daily_km <= 40:
            driving_score = 10

        elif 5 <= daily_km < 10:
            driving_score = 8
            reasons.append("Mostly short trips")

        elif 40 < daily_km <= 80:
            driving_score = 7

        else:
            driving_score = 5
            reasons.append("Very heavy daily usage")

    score += driving_score


    # ======================
    # 5. MILEAGE ANOMALY (5)
    # ======================

    mileage_score = 5

    mileage = safe_int(car.mileage)

    if mileage:

        if mileage < 10:
            mileage_score = 2
            reasons.append("Low fuel efficiency")

        elif mileage < 14:
            mileage_score = 3

        else:
            mileage_score = 5

    score += mileage_score


    # ======================
    # 6. COMPONENT WEAR CHECK
    # ======================

    brake_km = safe_int(car.brake_replaced_km)

    if brake_km is not None:

        used = current_km - brake_km

        if used > 35000:
            score -= 5
            reasons.append("Brake wear high")


    tyre_km = safe_int(car.tyre_replaced_km)

    if tyre_km is not None:

        used = current_km - tyre_km

        if used > 45000:
            score -= 5
            reasons.append("Tyre wear high")


    clutch_km = safe_int(car.clutch_replaced_km)

    if clutch_km is not None:

        used = current_km - clutch_km

        if used > 80000:
            score -= 5
            reasons.append("Clutch wear high")


    battery_year = safe_int(car.battery_replaced_year)

    if battery_year is not None:

        battery_age = datetime.now().year - battery_year

        if battery_age > 4:
            score -= 5
            reasons.append("Battery aging")


    # ======================
    # FINAL STATUS
    # ======================

    if score >= 90:
        status = "Excellent"

    elif score >= 75:
        status = "Good"

    elif score >= 60:
        status = "Attention Needed"

    else:
        status = "Critical"


    return {
        "score": score,
        "status": status,
        "reasons": reasons
    }