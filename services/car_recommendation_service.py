from services.india_car_catalog import recommendation_catalog

CAR_CATALOG = recommendation_catalog()


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
    return ranked[:9]


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
