def get_service_interval(brand, fuel):

    brand = brand.lower() if brand else ""
    fuel = fuel.lower() if fuel else ""

    # default
    interval = 10000

    # EV vehicles
    if fuel == "electric":
        return 15000

    # brand specific rules
    if brand in ["maruti", "suzuki"]:
        interval = 10000

    elif brand == "hyundai":
        interval = 10000

    elif brand == "tata":
        interval = 15000

    elif brand == "mahindra":
        interval = 10000

    else:
        interval = 10000

    return interval