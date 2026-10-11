def calculate_service_status(car):

    if not car.next_service_km or not car.current_km:
        return None

    remaining_km = car.next_service_km - car.current_km

    status = "healthy"

    if remaining_km <= 0:
        status = "overdue"

    elif remaining_km <= 1000:
        status = "due"

    elif remaining_km <= 3000:
        status = "soon"

    return {
        "remaining_km": remaining_km,
        "status": status
    }