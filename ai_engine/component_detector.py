# ai_engine/component_detector.py

def detect_components(problem_text):

    text = problem_text.lower()

    # remove generic words
    if "car " in text:
        text = text.replace("car ", "")

    COMPONENT_KEYWORDS = {

        "brake":[
            "brake","braking","pedal","disc","rotor","caliper",
            "pad","abs","stopping","brake failure","brake weak",
            "squeaking while braking","pulling to one side while braking"
        ],

        "engine":[
            "engine","misfire","power loss","stall","knocking",
            "rpm","engine shaking","engine vibration","rough running",
            "not starting","stalling","overheating","check engine light",
            "engine warning light","oil pressure light","oil pressure warning light",
            "oil warning light","oil light","black smoke","blue smoke",
            "white smoke","car shuts off while driving"
        ],

        "electrical":[
            "battery","starter","alternator","fuse",
            "not starting","no start","relay","sensor",
            "dashboard light","warning light","tail light","headlight",
            "parking light","check engine light","oil light","tpms"
        ],

        "cooling":[
            "overheat","overheating","coolant","radiator",
            "temperature","fan","water pump","coolant loss","hot",
            "temperature warning light","temperature light","temp warning"
        ],

        "steering":[
            "steering",
            "alignment",
            "pulling",
            "car pulling",
            "pulling to one side",
            "vehicle pulling",
            "steering vibration",
            "hard steering",
            "steering heavy",
            "steering loose"
        ],

        "ac":[
            "ac","cooling","compressor",
            "air conditioning","blower","weak cooling","ac not cooling","ac weak"
        ],

        "fuel":[
            "fuel","injector","fuel pump",
            "fuel smell","fuel pressure"
        ],

        "tyre":[
            "tpms","tyre pressure","tire pressure","low tyre pressure",
            "low tire pressure"
        ],

        "transmission":[
            "gear",
            "gearbox",
            "shifting",
            "gear slipping",
            "clutch",
            "clutch slip",
            "rpm increases speed not increasing"
        ],

        "suspension":[
            "shock",
            "suspension",
            "bump",
            "clunk",
            "wheel bearing",
            "cv joint",
            "car shaking",
            "shaking while driving",
            "vibration while driving",
            "vehicle vibration",
            "wheel vibration"
        ],

        "ev":[
            "ev","battery pack","charging",
            "range drop","electric motor"
        ],

        "hybrid":[
            "hybrid","regen braking","hybrid battery"
        ],

        "adas":[
            "lane assist","adaptive cruise",
            "collision warning","parking assist"
        ],

        "body":[
            "door","window","sunroof",
            "wiper","mirror","body noise"
        ],

        "maintenance":[
            "maintenance","service schedule","periodic service","checklist",
            "engine oil change","tyre rotation","tire rotation",
            "battery maintenance","brake maintenance","coolant maintenance",
            "filter maintenance","long trip checklist","road trip maintenance"
        ],

        "lighting":[
            "tail light","tail lamp","parking light","brake light",
            "headlight","low beam","high beam","light throw"
        ],

        "dashboard":[
            "dashboard","dash light","warning light","check engine light",
            "oil pressure light","temperature light","tpms light",
            "battery warning light","airbag light","abs light"
        ],

        "safety":[
            "airbag light","airbag warning","srs light","srs warning"
        ]
    }

    detected = set()

    for component, keywords in COMPONENT_KEYWORDS.items():

        for word in keywords:

            if word in text:
                detected.add(component)
                break

    return list(detected)
