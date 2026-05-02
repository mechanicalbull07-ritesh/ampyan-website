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
        "ac compressor": ["compressor"]

    }

    for component, words in components.items():

        for word in words:

            if word in text:
                return component

    return None