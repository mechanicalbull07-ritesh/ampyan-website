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

    def has_any(*phrases):
        return any(phrase in text for phrase in phrases)

    def calibrated_confidence(raw_score, matched_count, is_generic=False):
        confidence = int(28 + (float(raw_score) / (float(raw_score) + 90.0)) * 67)
        if matched_count >= 2:
            confidence += 6
        elif matched_count == 0:
            confidence -= 12
        if is_generic:
            confidence = min(confidence, 58)
        return max(25, min(95, confidence))

    def matched_symptoms_for(failure):
        matched = []
        for symptom in failure.get("symptoms", []):
            symptom_text = (symptom or "").lower()
            symptom_words = [word for word in symptom_text.split() if len(word) > 2]
            if symptom_text in text or any(word in problem_words for word in symptom_words):
                matched.append(symptom)
        for alias in failure.get("aliases", []):
            alias_text = (alias or "").lower()
            alias_words = [word for word in alias_text.split() if len(word) > 2]
            if alias_text in text or any(word in problem_words for word in alias_words):
                matched.append(alias)
        return matched[:5]

    # ------------------------------------------------
    # PROBABILITY BASED SCORING
    # ------------------------------------------------

    scored_failures = probability_reasoning(problem_words, failure_database, problem_text=text)

    for failure, base_score in scored_failures:

        score = base_score

        component = failure.get("component", "").lower()
        system = failure.get("system", "").lower()
        problem = failure.get("problem", "")

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

        if has_any("brake", "braking") and has_any("vibration", "vibrate", "vibrates", "shaking", "shake"):

            if problem in {"Brake Disc Warped", "Brake Pedal Vibrates", "Car Shakes While Braking"}:
                score += 60
            elif "brake disc" in component:
                score += 28
            elif "pulling" in problem.lower() and not has_any("pull", "left", "right", "one side"):
                score -= 25

        # ------------------------------------
        # CRITICAL BRAKE HYDRAULIC PRIORITY
        # ------------------------------------

        if "brake" in text and ("floor" in text or "sinking" in text or "pedal sinking" in text):
            if problem == "Brake Pedal Goes To Floor":
                score += 55
            elif "brake fluid" in component or "brake system" in component:
                score += 18

        # ------------------------------------
        # COOLING FAN SAFETY PRIORITY
        # ------------------------------------

        if "fan" in text and ("overheat" in text or "overheating" in text or "temperature" in text):
            if problem in {"Fan Not Turning On", "Radiator Fan Failure", "Cooling Fan Relay Failure"}:
                score += 70
            elif "cooling" in system or "fan" in component:
                score += 14
            if "coolant" in component and has_any("fan not", "fan not working", "fan not running"):
                score -= 22

        # ------------------------------------
        # STEERING PULL PRIORITY
        # ------------------------------------

        if has_any("pull", "pulling", "left", "right", "one side") and has_any("steering", "drive", "driving", "road"):
            if problem == "Wheel Alignment Incorrect":
                score += 55
            elif "alignment" in component:
                score += 35
            elif has_any("hard steering", "heavy steering", "tight steering"):
                score += 8
            elif "power steering" in component and not has_any("hard", "heavy", "tight", "noise", "whine"):
                score -= 25

        # ------------------------------------
        # AC COOLING CONTEXT
        # ------------------------------------

        if has_any("ac not cooling", "not cooling", "thandi hawa", "warm air") and has_any("ac", "air conditioning"):
            if problem in {"AC Gas Low", "AC Gas Leak"}:
                score += 35
            elif problem == "AC Compressor Failure":
                score += 20
            elif problem == "AC Condenser Blocked" and not has_any("traffic", "highway", "condenser"):
                score -= 18

        # ------------------------------------
        # EXHAUST SMOKE SAFETY PRIORITY
        # ------------------------------------

        if has_any("white smoke", "white exhaust") or ("smoke" in text and "coolant" in text):
            if problem in {"White Smoke From Exhaust", "Engine Head Gasket Leak", "Coolant Mixed With Oil"}:
                score += 55
            elif system == "ac" and "ac" not in text:
                score -= 35

        if has_any("black smoke", "kala smoke", "kala dhuan") or ("smoke" in text and "black" in text):
            if problem == "Black Smoke From Exhaust":
                score += 90
            elif system == "ac":
                score -= 45

        if has_any("blue smoke", "neela smoke", "neela dhuan", "oil burning smoke") or ("smoke" in text and "blue" in text):
            if problem == "Blue Smoke From Exhaust":
                score += 80
            elif "turbo" in component and has_any("turbo", "boost"):
                score += 20
            elif system == "ac":
                score -= 45

        # ------------------------------------
        # DASHBOARD / LIGHTING PRIORITY
        # ------------------------------------

        if has_any("tail light", "tail lamp", "rear light", "parking light") and has_any("ignition off", "car off", "key off", "band", "stays on", "remain"):
            if problem == "Tail Light Stays On After Ignition Off":
                score += 85
            elif "light" in component or system in {"electrical", "lighting"}:
                score += 12

        if has_any("headlight", "head light", "low beam") and has_any("throw", "dim", "weak", "visibility", "raat"):
            if problem == "Headlight Low Beam Weak":
                score += 80
            elif "headlight" in component:
                score += 20

        if has_any("check engine", "engine light", "mil light", "malfunction indicator"):
            if has_any("flash", "flashing", "blink", "blinking"):
                if problem == "Check Engine Light Flashing":
                    score += 90
                elif problem == "Check Engine Light Solid":
                    score -= 25
            else:
                if problem == "Check Engine Light Solid":
                    score += 95
                elif problem == "Check Engine Light Flashing":
                    score -= 18
                elif problem in {"Ignition Coil Failure", "Spark Plug Worn", "Spark Plug Fouled", "Fuel Injector Clogged"} and not has_any("misfire", "rough", "jerk", "shaking", "power loss"):
                    score -= 40

        if has_any("oil light", "oil pressure", "red oil", "oil lamp"):
            if problem == "Oil Pressure Warning Light On":
                score += 90

        if has_any("temperature light", "temp warning", "red temperature", "coolant temperature"):
            if problem == "Temperature Warning Light On":
                score += 90

        if has_any("brake warning", "red brake light", "parking brake light", "brake fluid light"):
            if problem == "Brake Warning Light On":
                score += 85

        if has_any("tpms", "tyre pressure light", "tire pressure light", "low tyre pressure", "low tire pressure"):
            if problem == "TPMS Warning Light On":
                score += 85

        if has_any("dashboard warning light photo uploaded", "warning light image uploaded", "dashboard symbol photo uploaded"):
            if problem == "Dashboard Warning Light Photo Review Needed":
                score += 70

        if problem == "Dashboard Warning Light Photo Review Needed" and has_any(
            "check engine", "oil pressure", "oil light", "temperature light",
            "brake warning", "tpms", "battery warning", "abs", "airbag"
        ):
            score -= 45

        # ------------------------------------
        # BASIC MAINTENANCE Q&A PRIORITY
        # ------------------------------------

        if system == "maintenance":
            if has_any("warning light", "red light", "oil pressure", "overheating", "brake weak", "brake pedal", "not starting"):
                score -= 20
            if has_any("maintenance", "service", "checklist", "kab change", "when to change", "guidance"):
                score += 25
            if problem == "Basic Maintenance Schedule Guidance" and has_any("basic maintenance", "routine maintenance", "service schedule", "periodic service"):
                score += 55
            if problem == "Engine Oil Change Guidance" and has_any("engine oil", "oil change", "oil service"):
                score += 70
            if problem == "Tyre Pressure And Rotation Guidance" and has_any("tyre pressure", "tire pressure", "tyre rotation", "rotate tyres"):
                score += 70
            if problem == "Battery Maintenance Guidance" and has_any("battery maintenance", "battery health", "replace battery", "battery kab"):
                score += 70
            if problem == "Brake Maintenance Guidance" and has_any("brake maintenance", "brake pad", "brake service", "brake fluid"):
                score += 70
            if problem == "Coolant Maintenance Guidance" and has_any("coolant maintenance", "coolant change", "coolant level", "radiator coolant"):
                score += 70
            if problem == "Filter Maintenance Guidance" and has_any("filter maintenance", "air filter", "cabin filter", "fuel filter"):
                score += 70
            if problem == "Long Trip Maintenance Checklist" and has_any("long trip", "long drive", "road trip", "highway trip", "trip se pehle"):
                score += 75

        # ------------------------------------
        # NOISE CONTEXT PRIORITY
        # ------------------------------------

        if has_any("humming", "ghurrr", "wheel bearing") and has_any("speed", "driving", "badhne", "increase"):
            if problem == "Wheel Bearing Failure":
                score += 80
            elif "timing chain" in problem.lower() and not has_any("engine", "cold start", "startup", "start"):
                score -= 35

        # ------------------------------------
        # BRAKE / CLUTCH / SAFETY CONTEXT
        # ------------------------------------

        if has_any("brake", "braking") and has_any("squeak", "squeaking", "cheekh"):
            if problem == "Brake Pad Wear":
                score += 75
            elif problem == "Brake Fluid Low" and not has_any("soft", "warning light", "fluid", "pedal"):
                score -= 35

        if has_any("brake", "braking") and has_any("pull", "pulls", "pulling", "one side", "left", "right", "khich"):
            if problem == "Brake Caliper Stuck":
                score += 75
            elif problem == "Brake Pad Wear":
                score -= 20

        if has_any("clutch slip", "clutch slipping", "rpm increases speed not increasing", "rpm badh raha", "rpm badhta") and has_any("speed not", "speed nahi", "not increasing", "clutch"):
            if problem == "Clutch Slips Under Load":
                score += 95
            elif system == "engine" and not has_any("misfire", "check engine", "smoke"):
                score -= 35

        if has_any("car shuts off while driving", "engine shuts off while driving", "driving me car band", "chalti gaadi band"):
            if problem == "Car Shuts Off While Driving":
                score += 100

        if has_any("abs light", "abs warning"):
            if problem == "ABS Sensor Fault":
                score += 75
            elif problem == "ABS Module Failure":
                score += 55
            elif problem == "Brake Warning Light On" and "brake warning" not in text:
                score -= 25

        if has_any("airbag light", "airbag warning", "srs light", "srs warning"):
            if problem == "Airbag Warning Light":
                score += 95

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

        matched_symptoms = matched_symptoms_for(failure)

        matches.append({

            "issue": failure.get("problem"),
            "problem": failure.get("problem"),
            "system": failure.get("system"),
            "component": failure.get("component"),
            "raw_score": score,
            "evidence_score": score,
            "probability_score": score,
            "severity": failure.get("severity"),
            "urgency": failure.get("urgency"),
            "repair_cost": failure.get("repair_cost"),
            "questions": failure.get("questions", []),
            "user_checks": failure.get("user_checks"),
            "top_matched_symptoms": matched_symptoms,
            "safety_message": failure.get("safety_message", ""),
            "disclaimer": failure.get("disclaimer", ""),
            "group_id": failure.get("group_id"),
            "aliases": failure.get("aliases", []),
            "is_generic": failure.get("is_generic", False),
            "use_as_router_only": failure.get("use_as_router_only", False),
            "evidence_level": "strong" if score >= 95 and len(matched_symptoms) >= 1 else "medium" if score >= 45 else "low",
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

        relative_confidence = (item["raw_score"] / top_score) * 95
        absolute_confidence = calibrated_confidence(
            item["raw_score"],
            len(item.get("top_matched_symptoms") or []),
            item.get("is_generic", False),
        )
        confidence = min(absolute_confidence, relative_confidence)

        item["confidence"] = round(confidence)
        item["confidence_percent"] = item["confidence"]

        del item["raw_score"]

    # ------------------------------------------------
    # SORT RESULTS
    # ------------------------------------------------

    matches.sort(key=lambda x: x["confidence"], reverse=True)

    # ------------------------------------------------
    # REMOVE DUPLICATES
    # ------------------------------------------------

    unique = []
    seen_groups = set()
    seen = set()

    for item in matches:

        if item["issue"] not in seen:
            group_id = item.get("group_id") or item["issue"]
            if group_id in seen_groups and len(unique) >= 1:
                continue
            unique.append(item)
            seen.add(item["issue"])
            seen_groups.add(group_id)

    if len(unique) < 3:
        for item in matches:
            if item["issue"] not in seen:
                unique.append(item)
                seen.add(item["issue"])
            if len(unique) >= 3:
                break

    return unique[:3]
