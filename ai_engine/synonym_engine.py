# ai_engine/synonym_engine.py

def expand_words(problem_text):

    text = problem_text.lower()

    synonyms = {

        # Noise related
        "noise": [
            "sound",
            "squeak",
            "squeaking",
            "grinding",
            "rattling",
            "knocking",
            "humming"
        ],

        # Brake related
        "brake": [
            "braking",
            "brakes",
            "pedal",
            "disc",
            "rotor",
            "stop"
        ],

        # Starting issues
        "start": [
            "starting",
            "crank",
            "cranking",
            "not starting",
            "hard start"
        ],

        # Engine related
        "engine": [
            "motor",
            "power",
            "rpm",
            "engine shaking"
        ],

        # Overheating
        "overheat": [
            "overheating",
            "temperature",
            "hot",
            "high temperature"
        ],

        # Vibration
        "vibration": [
            "shake",
            "shaking",
            "vibrate",
            "car shaking"
        ],

        # Power issues
        "power": [
            "power loss",
            "low power",
            "weak acceleration"
        ],

        # Steering
        "steering": [
            "turning",
            "hard steering",
            "steering tight"
        ],

        # Gear / transmission
        "gear": [
            "gearbox",
            "shifting",
            "gear shifting",
            "gear change"
        ],

        # Cooling system
        "coolant": [
            "cooling",
            "radiator",
            "engine temperature"
        ],

        # AC system
        "ac": [
            "air conditioning",
            "cooling",
            "ac cooling"
        ]

    }

    expanded_words = text.split()

    for word in text.split():

        if word in synonyms:
            expanded_words.extend(synonyms[word])

    # remove duplicates
    expanded_words = list(set(expanded_words))

    return expanded_words