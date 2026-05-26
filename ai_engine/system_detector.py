# ai_engine/system_detector.py

def detect_system(problem_text):

    text = problem_text.lower()

    systems = {

        "engine":[
            "engine","misfire","stall","power loss","loss of power",
            "smoke","knocking","rpm","engine shaking","engine vibration",
            "check engine light","engine warning light","oil pressure light",
            "oil pressure warning light","oil warning light","oil light",
            "black smoke","blue smoke","white smoke","car shuts off while driving"
        ],

        "brake":[
            "brake","braking","pedal","disc","rotor","caliper","pad",
            "abs","stopping","brake noise","brake warning light",
            "red brake light","parking brake light"
        ],

        "electrical":[
            "battery","starter","alternator","fuse","relay","sensor",
            "not starting","no start","clicking sound","dashboard light",
            "warning light","tail light","headlight","parking light",
            "check engine light","oil light","tpms"
        ],

        "cooling":[
            "overheat","overheating","coolant","radiator","temperature",
            "fan","water pump","temperature warning light","temperature light",
            "temp warning"
        ],

        "transmission":[
            "gear","gearbox","shifting","gear slipping","clutch",
            "clutch slip","rpm increases speed not increasing"
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

        "tyre":[
            "tpms","tyre pressure","tire pressure","low tyre pressure",
            "low tire pressure"
        ],

        "ac":[
            " ac ","air conditioning","compressor","blower","weak cooling"
        ],

        "exhaust":[
            "exhaust","smoke","catalytic","dpf"
        ],

        "body":[
            "door","window","sunroof","lock","horn","wiper"
        ],

        "safety":[
            "airbag light","airbag warning","srs light","srs warning"
        ],

        "maintenance":[
            "maintenance","service schedule","periodic service","checklist",
            "engine oil change","tyre rotation","tire rotation",
            "battery maintenance","brake maintenance","coolant maintenance",
            "filter maintenance","long trip checklist","road trip maintenance"
        ],

        "lighting":[
            "tail light","tail lamp","headlight","low beam","high beam",
            "parking light","brake light","light throw"
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
