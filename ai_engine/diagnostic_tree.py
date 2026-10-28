# ai_engine/diagnostic_tree.py

def detect_system(problem_text):

    text = problem_text.lower()

    brake_words = [
        "brake", "braking", "pedal", "disc", "rotor", "caliper"
    ]

    engine_words = [
        "engine", "misfire", "power", "stall", "smoke"
    ]

    starting_words = [
        "not starting", "no start", "starting issue", "crank"
    ]

    cooling_words = [
        "overheat", "temperature", "coolant", "radiator"
    ]

    steering_words = [
        "steering", "alignment", "pulling", "vibration"
    ]

    ac_words = [
        "ac", "cooling", "air conditioning"
    ]

    lighting_words = [
        "tail light", "tail lamp", "headlight", "low beam",
        "high beam", "parking light", "light throw"
    ]

    dashboard_words = [
        "dashboard", "warning light", "check engine light", "oil light",
        "temperature light", "tpms", "battery warning light"
    ]

    for word in brake_words:
        if word in text:
            return "brake"

    for word in engine_words:
        if word in text:
            return "engine"

    for word in starting_words:
        if word in text:
            return "electrical"

    for word in cooling_words:
        if word in text:
            return "cooling"

    for word in steering_words:
        if word in text:
            return "steering"

    for word in ac_words:
        if word in text:
            return "ac"

    for word in lighting_words:
        if word in text:
            return "lighting"

    for word in dashboard_words:
        if word in text:
            return "electrical"

    return None


def detect_component(problem_text):

    text = problem_text.lower()

    components = {

        "brake pad": ["pad", "pads"],
        "brake disc": ["disc", "rotor"],
        "caliper": ["caliper"],
        "battery": ["battery"],
        "starter motor": ["starter"],
        "alternator": ["alternator"],
        "radiator": ["radiator"],
        "fan": ["fan"],
        "spark plug": ["spark"],
        "ignition coil": ["coil"],
        "fuel pump": ["fuel pump"],
        "ac compressor": ["compressor"],
        "tail light circuit": ["tail light", "tail lamp", "rear light"],
        "headlight low beam": ["headlight", "low beam", "light throw"],
        "dashboard warning light": ["dashboard", "warning light"],
        "oil pressure system": ["oil light", "oil pressure"],
        "cooling system": ["temperature light", "temp warning"],
        "brake warning system": ["brake warning", "parking brake light"],
        "tpms": ["tpms", "tyre pressure", "tire pressure"]

    }

    for component, words in components.items():

        for word in words:

            if word in text:
                return component

    return None
