# ai_engine/system_detector.py

def detect_system(problem_text):

    text = problem_text.lower()

    systems = {

        "engine":[
            "engine","misfire","stall","power loss","loss of power",
            "smoke","knocking","rpm","engine shaking","engine vibration"
        ],

        "brake":[
            "brake","braking","pedal","disc","rotor","caliper","pad",
            "abs","stopping","brake noise"
        ],

        "electrical":[
            "battery","starter","alternator","fuse","relay","sensor",
            "not starting","no start","clicking sound"
        ],

        "cooling":[
            "overheat","overheating","coolant","radiator","temperature",
            "fan","water pump"
        ],

        "transmission":[
            "gear","gearbox","shifting","gear slipping","clutch"
        ],

        "steering":[
            "steering","alignment","pulling","hard steering"
        ],

        "suspension":[
            "suspension","shock","bump","clunk","wheel bearing"
        ],

        "fuel":[
            "fuel","injector","fuel pump","fuel smell","fuel pressure"
        ],

        "ac":[
            " ac ","air conditioning","compressor","blower","weak cooling"
        ],

        "exhaust":[
            "exhaust","smoke","catalytic","dpf"
        ],

        "body":[
            "door","window","sunroof","lock","horn","wiper"
        ]

    }

    scores = {}

    # -----------------------------
    # count keyword matches
    # -----------------------------

    for system, words in systems.items():

        score = 0

        for word in words:

            if word in text:
                score += 1

        if score > 0:
            scores[system] = score

    # -----------------------------
    # no match
    # -----------------------------

    if not scores:
        return None

    # -----------------------------
    # return highest match system
    # -----------------------------

    detected_system = max(scores, key=scores.get)

    return detected_system