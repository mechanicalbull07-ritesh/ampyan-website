from models.models import MechanicReview


def calculate_trust_profile_score(data):
    score = 30

    if data.get("address"):
        score += 10
    if data.get("pincode"):
        score += 8
    if data.get("specialties"):
        score += 10
    if data.get("service_types"):
        score += 10
    if data.get("about"):
        score += 10
    if data.get("accepts_emergency"):
        score += 5
    if data.get("pickup_drop_available"):
        score += 5

    experience_years = int(data.get("experience_years") or 0)
    score += min(12, experience_years)

    return min(score, 100)


def trust_level_from_score(score):
    if score >= 90:
        return "Elite Garage"
    if score >= 78:
        return "Trusted Garage"
    if score >= 62:
        return "Verified Local Garage"
    return "Starter Garage"


def refresh_mechanic_reputation(mechanic):
    base_score = calculate_trust_profile_score({
        "address": mechanic.address,
        "pincode": mechanic.pincode,
        "specialties": mechanic.specialties,
        "service_types": mechanic.service_types,
        "about": mechanic.about,
        "accepts_emergency": mechanic.accepts_emergency,
        "pickup_drop_available": mechanic.pickup_drop_available,
        "experience_years": mechanic.experience_years
    })

    review_count = len(mechanic.reviews)
    avg_rating = (
        sum(review.rating for review in mechanic.reviews) / review_count
        if review_count else 0
    )

    score = base_score

    if mechanic.is_verified:
        score += 15
    if mechanic.is_featured:
        score += 5

    score += min(10, review_count * 2)
    score += int(avg_rating * 4)

    mechanic.trust_score = min(score, 100)
    mechanic.trust_level = trust_level_from_score(mechanic.trust_score)

    return {
        "review_count": review_count,
        "average_rating": round(avg_rating, 1) if review_count else 0,
        "trust_score": mechanic.trust_score,
        "trust_level": mechanic.trust_level
    }
