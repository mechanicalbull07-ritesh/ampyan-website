from ai_engine.component_detector import detect_components
from ai_engine.synonym_engine import expand_words
from ai_engine.diagnostic_tree import detect_component
from ai_engine.explanation_engine import generate_explanation
from ai_engine.probability_engine import probability_reasoning
from ai_engine.symptom_graph_engine import graph_reasoning
from ai_engine.system_detector import detect_system
from ai_engine.symptom_weight_engine import symptom_weight_score


# ------------------------------------------------
# MAIN RANKING ENGINE
# ------------------------------------------------

def rank_failures(problem_text, failure_database):

    matches = []

    # expand synonyms
    words = expand_words(problem_text)
    problem_words = [w.lower() for w in words]

    # symptom reasoning
    weight_scores = symptom_weight_score(problem_words)
    graph_scores = graph_reasoning(problem_words)

    # detect system / component
    detected_system = detect_system(problem_text)
    detected_component = detect_component(problem_text)
    components = detect_components(problem_text)

    text = problem_text.lower()

    # ------------------------------------------------
    # PROBABILITY BASED SCORING
    # ------------------------------------------------

    scored_failures = probability_reasoning(problem_words, failure_database)

    for failure, base_score in scored_failures:

        score = base_score

        component = failure.get("component", "").lower()
        system = failure.get("system", "").lower()

        # ------------------------------------
        # VEHICLE TYPE SAFETY FILTER
        # ------------------------------------

        if "ev" in system and "ev" not in text:
            continue

        if "hybrid" in system and "hybrid" not in text:
            continue

        # ------------------------------------
        # STARTING SYSTEM PRIORITY
        # ------------------------------------

        if "not starting" in text or "no start" in text:

            if "battery" in component:
                score += 35

            if "starter motor" in component:
                score += 20

            if "starter relay" in component:
                score += 10

        # ------------------------------------
        # IGNITION SYSTEM PRIORITY
        # ------------------------------------

        if "misfire" in text or "engine shaking" in text or "rough idle" in text:

            if "spark plug" in component:
                score += 12

            if "ignition coil" in component:
                score += 8

        # ------------------------------------
        # BRAKE DISC PRIORITY
        # ------------------------------------

        if "brake" in text and "vibration" in text:

            if "brake disc" in component:
                score += 18

        # ------------------------------------
        # SYMPTOM WEIGHT BOOST
        # ------------------------------------

        if component in weight_scores:
            score += weight_scores[component] * 2

        # ------------------------------------
        # SYMPTOM GRAPH BOOST
        # ------------------------------------

        if component in graph_scores:
            score += graph_scores[component]

        # ------------------------------------
        # SYSTEM BOOST
        # ------------------------------------

        if detected_system:
            if system == detected_system:
                score += 15

        # ------------------------------------
        # COMPONENT BOOST
        # ------------------------------------

        if detected_component and detected_component in component:
            score += 20

        # ------------------------------------
        # EXTRA COMPONENT BOOST
        # ------------------------------------

        for comp in components:

            if comp and comp in component:
                score += 10

        # ignore very low score
        if score <= 5:
            continue

        matches.append({

            "issue": failure.get("problem"),
            "raw_score": score,
            "severity": failure.get("severity"),
            "repair_cost": failure.get("repair_cost"),
            "user_checks": failure.get("user_checks"),
            "explanation": generate_explanation(problem_text, failure, {})

        })

    if not matches:
        return []

    # ------------------------------------------------
    # FIND TOP SCORE
    # ------------------------------------------------

    top_score = max(item["raw_score"] for item in matches)

    # ------------------------------------------------
    # NORMALIZE CONFIDENCE
    # ------------------------------------------------

    for item in matches:

        confidence = (item["raw_score"] / top_score) * 95
        confidence = min(95, confidence)

        item["confidence"] = round(confidence)

        del item["raw_score"]

    # ------------------------------------------------
    # SORT RESULTS
    # ------------------------------------------------

    matches.sort(key=lambda x: x["confidence"], reverse=True)

    # ------------------------------------------------
    # REMOVE DUPLICATES
    # ------------------------------------------------

    unique = []
    seen = set()

    for item in matches:

        if item["issue"] not in seen:
            unique.append(item)
            seen.add(item["issue"])

    return unique[:3]