from datetime import datetime


DISCLAIMER = "This is an estimate. Follow your vehicle owner's manual and qualified mechanic advice."

STATUS_OK = "OK"
STATUS_MONITOR = "Monitor"
STATUS_SERVICE_SOON = "Service Soon"
STATUS_REPLACE_NOW = "Replace Now"
STATUS_NOT_REQUIRED = "Avoid / Not Required"


SERVICE_ITEMS = [
    {
        "item": "Engine Oil",
        "aliases": ["engine oil", "oil change", "engine oil change"],
        "km": 10000,
        "months": 12,
        "cost": {"min": 2500, "max": 6000},
        "fuel_exclude": ["ev"],
        "reason": "Engine oil protects internal engine parts and degrades with heat, time and traffic use.",
    },
    {
        "item": "Oil Filter",
        "aliases": ["oil filter"],
        "km": 10000,
        "months": 12,
        "cost": {"min": 400, "max": 1500},
        "fuel_exclude": ["ev"],
        "reason": "Oil filter should usually be replaced with every engine oil change.",
    },
    {
        "item": "Air Filter",
        "aliases": ["air filter", "engine air filter"],
        "km": 15000,
        "months": 12,
        "cost": {"min": 500, "max": 1800},
        "fuel_exclude": [],
        "reason": "A clogged air filter can reduce pickup and fuel economy, especially in dusty city use.",
    },
    {
        "item": "Cabin AC Filter",
        "aliases": ["cabin filter", "ac filter", "cabin ac filter"],
        "km": 12000,
        "months": 12,
        "cost": {"min": 500, "max": 2000},
        "fuel_exclude": [],
        "reason": "Cabin filter affects AC airflow, smell and dust inside the cabin.",
    },
    {
        "item": "Fuel Filter",
        "aliases": ["fuel filter"],
        "km_by_fuel": {"petrol": 35000, "cng": 35000, "diesel": 25000, "hybrid": 35000},
        "months": None,
        "cost": {"min": 1200, "max": 4500},
        "fuel_exclude": ["ev"],
        "reason": "Fuel filters clog faster in diesel and poor fuel conditions, causing hesitation or low power.",
    },
    {
        "item": "Spark Plug",
        "aliases": ["spark plug", "spark plugs"],
        "km": 35000,
        "months": None,
        "cost": {"min": 1000, "max": 5000},
        "fuel_include": ["petrol", "cng", "hybrid"],
        "reason": "Spark plugs wear with use and can cause misfire, rough idle or poor mileage.",
    },
    {
        "item": "Brake Fluid",
        "aliases": ["brake fluid"],
        "km": None,
        "months": 24,
        "cost": {"min": 800, "max": 2500},
        "fuel_exclude": [],
        "reason": "Brake fluid absorbs moisture over time and affects braking performance.",
        "safety": True,
    },
    {
        "item": "Coolant",
        "aliases": ["coolant", "coolant change", "radiator coolant"],
        "km": 40000,
        "months": 30,
        "cost": {"min": 1200, "max": 4500},
        "fuel_exclude": [],
        "reason": "Coolant protects against overheating, corrosion and water pump/radiator damage.",
        "safety": True,
    },
    {
        "item": "Brake Pads",
        "aliases": ["brake pad", "brake pads", "brake pad replace"],
        "km": 32000,
        "months": None,
        "cost": {"min": 2500, "max": 9000},
        "fuel_exclude": [],
        "reason": "Brake pads wear faster in stop-go traffic and aggressive driving.",
        "safety": True,
    },
    {
        "item": "Drive Belt / Serpentine Belt",
        "aliases": ["drive belt", "serpentine belt", "belt replace"],
        "km": 70000,
        "months": None,
        "cost": {"min": 1500, "max": 6000},
        "fuel_exclude": ["ev"],
        "reason": "A worn drive belt can cause squealing, charging issues or accessory failure.",
    },
    {
        "item": "Timing Belt",
        "aliases": ["timing belt"],
        "km": 90000,
        "months": None,
        "cost": {"min": 6000, "max": 25000},
        "fuel_exclude": ["ev"],
        "reason": "If your engine uses a timing belt, delayed replacement can cause severe engine damage.",
        "safety": True,
    },
    {
        "item": "Transmission Oil",
        "aliases": ["transmission oil", "gear oil", "gearbox oil", "transmission fluid"],
        "km_by_transmission": {
            "manual": 70000,
            "automatic": 50000,
            "amt": 60000,
            "cvt": 50000,
            "dct": 50000,
        },
        "months": None,
        "cost": {"min": 2500, "max": 12000},
        "fuel_exclude": [],
        "reason": "Transmission fluid/oil protects gears, clutch packs and shift quality.",
    },
    {
        "item": "AC Service",
        "aliases": ["ac service", "air conditioning service", "weak cooling", "ac smell"],
        "km": None,
        "months": 12,
        "cost": {"min": 1500, "max": 6000},
        "fuel_exclude": [],
        "reason": "Yearly AC checks help catch weak cooling, smell, blocked filters or gas leaks early.",
    },
]


def _safe_float(value, default=0):
    try:
        if value in [None, ""]:
            return default
        return max(float(value), 0)
    except (TypeError, ValueError):
        return default


def _clean_choice(value):
    return (value or "").strip().lower().replace(" ", "_")


def _months_since(date_value):
    if not date_value:
        return 0
    if isinstance(date_value, (int, float)):
        return _safe_float(date_value)
    try:
        parsed = datetime.strptime(str(date_value)[:10], "%Y-%m-%d")
    except ValueError:
        return 0
    today = datetime.utcnow()
    return max((today.year - parsed.year) * 12 + today.month - parsed.month, 0)


def calculate_stress_factor(data):
    usage_type = _clean_choice(data.get("usage_type"))
    driving_style = _clean_choice(data.get("driving_style"))
    query = (data.get("query") or "").lower()

    if usage_type == "highway":
        stress = 0.90
    elif usage_type == "mixed":
        stress = 1.10
    else:
        stress = 1.25

    if driving_style == "aggressive":
        stress += 0.15
    if driving_style == "stop_go" and usage_type != "city":
        stress += 0.10
    if usage_type == "city" and any(token in query for token in ["dust", "pollution", "traffic"]):
        stress += 0.10
    if any(token in query for token in ["ac heavy", "ac use", "weak cooling", "ac smell"]):
        stress += 0.10

    return round(stress, 2)


def _item_interval(item, fuel_type, transmission):
    km = item.get("km")
    if "km_by_fuel" in item:
        km = item["km_by_fuel"].get(fuel_type, item["km_by_fuel"].get("petrol"))
    if "km_by_transmission" in item:
        km = item["km_by_transmission"].get(transmission, item["km_by_transmission"].get("manual"))
    return km, item.get("months")


def _matches_query(item, query):
    if not query:
        return True
    return any(alias in query for alias in item.get("aliases", []))


def _priority(status, safety=False):
    if status == STATUS_REPLACE_NOW:
        return "high" if safety else "medium"
    if status == STATUS_SERVICE_SOON:
        return "medium"
    if status == STATUS_MONITOR:
        return "low"
    return "low"


def _status_from_due(km_since_service, months_since_service, km_interval, month_interval):
    ratios = []
    if km_interval:
        ratios.append(km_since_service / km_interval)
    if month_interval:
        ratios.append(months_since_service / month_interval)
    due_ratio = max(ratios) if ratios else 0

    if due_ratio >= 1:
        return STATUS_REPLACE_NOW
    if due_ratio >= 0.85:
        return STATUS_SERVICE_SOON
    if due_ratio >= 0.65:
        return STATUS_MONITOR
    return STATUS_OK


def _engine_flush_recommendation(data, km_since_service, months_since_service):
    query = (data.get("query") or "").lower()
    odometer = _safe_float(data.get("odometer_km"))
    age = _safe_float(data.get("vehicle_age_years"))
    sludge_signals = ["sludge", "dirty oil", "black oil", "rough idle", "delayed oil change", "oil pressure"]
    poor_history = km_since_service > 15000 or months_since_service > 18
    should_flush = (odometer > 60000 and poor_history) or any(token in query for token in sludge_signals) or (age > 7 and "rough" in query)

    if should_flush:
        status = STATUS_SERVICE_SOON
        reason = "Engine flush may be considered because sludge/poor oil history is suspected. Use only after mechanic inspection."
        priority = "medium"
    else:
        status = STATUS_NOT_REQUIRED
        reason = "Engine flush is not mandatory in every service. Normal oil + filter replacement is safer unless sludge is suspected."
        priority = "low"

    return {
        "item": "Engine Flush",
        "status": status,
        "reason": reason,
        "approx_cost": {"min": 800, "max": 2500},
        "priority": priority,
    }


def estimate_service(data):
    fuel_type = _clean_choice(data.get("fuel_type")) or "petrol"
    transmission = _clean_choice(data.get("transmission")) or "manual"
    odometer = _safe_float(data.get("odometer_km") or data.get("current_km"))
    last_service_km = _safe_float(data.get("last_service_km"))
    vehicle_age_years = _safe_float(data.get("vehicle_age_years") or data.get("vehicle_age"))
    last_service_months = _safe_float(data.get("last_service_months_ago"))
    if not last_service_months:
        last_service_months = _months_since(data.get("last_service_date"))
    query = (data.get("query") or "").strip().lower()

    stress_factor = calculate_stress_factor(data)
    effective_km = round(odometer * stress_factor)
    km_since_service = max(effective_km - last_service_km, 0) if last_service_km else effective_km

    recommended = []
    not_required = []

    for item in SERVICE_ITEMS:
        if fuel_type in item.get("fuel_exclude", []):
            continue
        if item.get("fuel_include") and fuel_type not in item["fuel_include"]:
            continue
        if query and not _matches_query(item, query):
            continue

        km_interval, month_interval = _item_interval(item, fuel_type, transmission)
        status = _status_from_due(km_since_service, last_service_months, km_interval, month_interval)
        service = {
            "item": item["item"],
            "status": status,
            "reason": item["reason"],
            "approx_cost": item["cost"],
            "priority": _priority(status, item.get("safety", False)),
        }
        if status == STATUS_OK:
            service["reason"] += " Based on the provided km/months, it does not look due yet."
        if status == STATUS_OK and query:
            not_required.append(service)
        else:
            recommended.append(service)

    if "flush" in query or "engine flush" in query:
        flush = _engine_flush_recommendation(data, km_since_service, last_service_months)
        if flush["status"] == STATUS_NOT_REQUIRED:
            not_required.append(flush)
        else:
            recommended.append(flush)

    if not recommended and not not_required:
        recommended = [
            {
                "item": "General Service Inspection",
                "status": STATUS_MONITOR,
                "reason": "No exact service item matched the query. Inspect fluids, filters, brakes, tyres and warning lights.",
                "approx_cost": {"min": 500, "max": 2000},
                "priority": "low",
            }
        ]

    safety_terms = ["brake", "steering", "overheat", "overheating", "fuel smell", "coolant boiling"]
    safety_note = ""
    if any(term in query for term in safety_terms) or any(item.get("priority") == "high" for item in recommended):
        safety_note = "If the issue affects brakes, steering, overheating or fuel smell, avoid driving and get it inspected urgently."

    due_count = sum(1 for item in recommended if item["status"] in {STATUS_REPLACE_NOW, STATUS_SERVICE_SOON})
    summary = (
        f"{due_count} service item(s) need attention based on km, age, usage and query."
        if due_count
        else "No urgent service item is due from the provided details. Monitor symptoms and follow the owner's manual."
    )

    return {
        "stress_factor": stress_factor,
        "effective_km": effective_km,
        "summary": summary,
        "recommended_services": recommended,
        "not_required": not_required,
        "safety_note": safety_note,
        "disclaimer": DISCLAIMER,
        "inputs": {
            "car_make": data.get("car_make", ""),
            "car_model": data.get("car_model", ""),
            "fuel_type": fuel_type,
            "transmission": transmission,
            "vehicle_age_years": vehicle_age_years,
            "odometer_km": odometer,
            "last_service_km": last_service_km,
            "last_service_months_ago": last_service_months,
        },
    }
