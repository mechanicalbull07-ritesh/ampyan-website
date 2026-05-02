CAR_CATALOG = [
    {
        "name": "Maruti Suzuki WagonR",
        "body_style": "Tall hatchback",
        "price_band": "Budget",
        "fuel": ["petrol", "cng"],
        "transmission": ["manual", "automatic"],
        "city_score": 9,
        "highway_score": 6,
        "family_score": 8,
        "solo_score": 7,
        "running_cost_score": 10,
        "comfort_score": 7,
        "tags": ["city", "family", "budget", "daily", "practical"],
        "reason": "Very easy to drive in city traffic, affordable to maintain and spacious for daily family use."
    },
    {
        "name": "Tata Punch",
        "body_style": "Micro SUV",
        "price_band": "Budget",
        "fuel": ["petrol", "cng"],
        "transmission": ["manual", "automatic"],
        "city_score": 8,
        "highway_score": 7,
        "family_score": 8,
        "solo_score": 7,
        "running_cost_score": 8,
        "comfort_score": 7,
        "tags": ["city", "family", "weekend", "high-ground-clearance"],
        "reason": "Good for mixed city use, broken roads and buyers who want a compact SUV-like feel."
    },
    {
        "name": "Hyundai Exter",
        "body_style": "Compact SUV",
        "price_band": "Budget",
        "fuel": ["petrol", "cng"],
        "transmission": ["manual", "automatic"],
        "city_score": 8,
        "highway_score": 7,
        "family_score": 7,
        "solo_score": 8,
        "running_cost_score": 8,
        "comfort_score": 7,
        "tags": ["city", "solo", "family", "feature-rich"],
        "reason": "Feature-rich option for urban buyers who want easy driving and decent road-trip ability."
    },
    {
        "name": "Maruti Suzuki Baleno",
        "body_style": "Premium hatchback",
        "price_band": "Mid",
        "fuel": ["petrol", "cng"],
        "transmission": ["manual", "automatic"],
        "city_score": 8,
        "highway_score": 8,
        "family_score": 8,
        "solo_score": 8,
        "running_cost_score": 9,
        "comfort_score": 8,
        "tags": ["city", "highway", "family", "refined"],
        "reason": "Balanced all-rounder with good efficiency, cabin space and everyday comfort."
    },
    {
        "name": "Honda Amaze",
        "body_style": "Compact sedan",
        "price_band": "Mid",
        "fuel": ["petrol"],
        "transmission": ["manual", "automatic"],
        "city_score": 7,
        "highway_score": 8,
        "family_score": 8,
        "solo_score": 7,
        "running_cost_score": 8,
        "comfort_score": 8,
        "tags": ["family", "boot-space", "highway", "comfort"],
        "reason": "Strong choice for users who want comfort, boot space and a relaxed family-friendly drive."
    },
    {
        "name": "Hyundai Creta",
        "body_style": "Mid-size SUV",
        "price_band": "Premium",
        "fuel": ["petrol", "diesel"],
        "transmission": ["manual", "automatic"],
        "city_score": 7,
        "highway_score": 9,
        "family_score": 9,
        "solo_score": 7,
        "running_cost_score": 6,
        "comfort_score": 9,
        "tags": ["family", "highway", "premium", "road-trip"],
        "reason": "Great for family highway users who want comfort, road presence and long-distance ease."
    },
    {
        "name": "Kia Carens",
        "body_style": "MPV",
        "price_band": "Premium",
        "fuel": ["petrol", "diesel"],
        "transmission": ["manual", "automatic"],
        "city_score": 6,
        "highway_score": 9,
        "family_score": 10,
        "solo_score": 5,
        "running_cost_score": 6,
        "comfort_score": 9,
        "tags": ["large-family", "highway", "comfort", "touring"],
        "reason": "Excellent for bigger families, frequent outstation travel and maximum passenger comfort."
    },
    {
        "name": "Mahindra XUV 3XO",
        "body_style": "Compact SUV",
        "price_band": "Mid",
        "fuel": ["petrol", "diesel"],
        "transmission": ["manual", "automatic"],
        "city_score": 7,
        "highway_score": 8,
        "family_score": 8,
        "solo_score": 8,
        "running_cost_score": 7,
        "comfort_score": 8,
        "tags": ["highway", "family", "performance", "feature-rich"],
        "reason": "A strong match for users who want a safer, more powerful compact SUV for mixed usage."
    },
]


def _preference_bonus(car, preferences):
    score = 0

    usage_mix = preferences.get("usage_mix", "city")
    family_use = preferences.get("family_use", "family")
    budget = preferences.get("budget", "mid")
    fuel = preferences.get("fuel_preference", "any")
    transmission = preferences.get("transmission", "any")
    priority = preferences.get("priority", "balanced")
    daily_run = int(preferences.get("daily_run") or 0)
    occasional_need = preferences.get("occasional_need", "weekend")

    if usage_mix == "city":
        score += car["city_score"] * 2
    elif usage_mix == "highway":
        score += car["highway_score"] * 2
    else:
        score += car["city_score"] + car["highway_score"]

    if family_use == "family":
        score += car["family_score"] * 2
    elif family_use == "solo":
        score += car["solo_score"] * 2
    else:
        score += car["family_score"] + 2

    if budget == car["price_band"].lower():
        score += 10
    elif budget == "premium" and car["price_band"] == "Mid":
        score += 5
    elif budget == "mid" and car["price_band"] == "Budget":
        score += 4

    if fuel != "any" and fuel in car["fuel"]:
        score += 8

    if transmission != "any" and transmission in car["transmission"]:
        score += 6

    if priority == "low_running_cost":
        score += car["running_cost_score"] * 2
    elif priority == "comfort":
        score += car["comfort_score"] * 2
    elif priority == "space":
        score += car["family_score"] * 2
    else:
        score += car["comfort_score"] + car["running_cost_score"]

    if daily_run >= 50:
        score += car["running_cost_score"] * 2
        if "cng" in car["fuel"] or "diesel" in car["fuel"]:
            score += 6
    elif daily_run <= 20:
        score += car["city_score"]

    if occasional_need == "road_trips":
        score += car["highway_score"] * 2
    elif occasional_need == "rough_roads" and "high-ground-clearance" in car["tags"]:
        score += 8
    elif occasional_need == "airport_luggage" and "boot-space" in car["tags"]:
        score += 8

    return score


def recommend_cars(preferences):
    ranked = []

    for car in CAR_CATALOG:
        total_score = _preference_bonus(car, preferences)
        ranked.append({
            **car,
            "match_score": min(98, max(58, total_score)),
            "fit_summary": _build_fit_summary(car, preferences)
        })

    ranked.sort(key=lambda item: item["match_score"], reverse=True)
    return ranked[:3]


def _build_fit_summary(car, preferences):
    usage_mix = preferences.get("usage_mix", "city")
    family_use = preferences.get("family_use", "family")
    daily_run = int(preferences.get("daily_run") or 0)

    points = []

    if usage_mix == "city":
        points.append("easy for city traffic")
    elif usage_mix == "highway":
        points.append("better for highway stability")
    else:
        points.append("balanced for mixed usage")

    if family_use == "family":
        points.append("works well for family comfort")
    elif family_use == "solo":
        points.append("practical for solo driving")

    if daily_run >= 50:
        points.append("supports higher daily running")
    elif daily_run > 0:
        points.append("comfortable for daily commuting")

    return ", ".join(points[:3]).capitalize() + "."


def build_user_profile_summary(preferences):
    return {
        "usage_mix": preferences.get("usage_mix", "city").replace("_", " ").title(),
        "daily_run": f"{preferences.get('daily_run', 0)} km/day",
        "family_use": preferences.get("family_use", "family").replace("_", " ").title(),
        "priority": preferences.get("priority", "balanced").replace("_", " ").title(),
        "occasional_need": preferences.get("occasional_need", "weekend").replace("_", " ").title(),
    }
