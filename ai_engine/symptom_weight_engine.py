# ai_engine/symptom_weight_engine.py

SYMPTOM_WEIGHTS = {

    "misfire": {
        "spark plug": 22,
        "ignition coil": 20,
        "fuel injector": 16
    },

    "engine shaking": {
        "spark plug": 20,
        "ignition coil": 18,
        "fuel injector": 15,
        "engine mount": 5
    },

    "power loss": {
        "fuel injector": 15,
        "fuel pump": 12,
        "air filter": 8,
        "turbocharger": 10
    },

    "vibration while braking": {
        "brake disc": 30,
        "brake pad": 5,
        "brake caliper": 8
    },

    "brake vibration": {
        "brake disc": 30,
        "brake pad": 5,
        "brake caliper": 8
    },

    "squeaking brake": {
        "brake pad": 18
    },

    "hard steering": {
        "power steering": 20
    },

    "steering vibration": {
        "tie rod": 18,
        "steering rack": 16,
        "wheel rim": 12,
        "wheel": 10
    },

    "car shaking": {
        "wheel": 15,
        "wheel rim": 12,
        "tie rod": 10
    },
 
"car shaking while driving": {
    "wheel": 18,
    "wheel rim": 15,
    "tie rod": 12,
    "cv joint": 14,
    "suspension": 10
},
"vibration while driving": {
    "wheel": 18,
    "wheel rim": 15,
    "tie rod": 12,
    "cv joint": 14
},

    "car not starting": {
        "battery": 20,
        "starter motor": 18,
        "alternator": 12
    },

    "ac not cooling": {
        "ac refrigerant": 20,
        "ac compressor": 15,
        "ac condenser": 12

},
"overheating": {
    "coolant system": 25,
    "radiator": 20,
    "thermostat": 18,
    "water pump": 18
},

}


def symptom_weight_score(problem_words):

    print("DEBUG WORDS:", problem_words)

    scores = {}

    text = " ".join(problem_words).lower()

    print("DEBUG TEXT:", text)

    for symptom, components in SYMPTOM_WEIGHTS.items():

        if symptom in text:

            print("MATCHED SYMPTOM:", symptom)

            for comp, weight in components.items():

                scores[comp] = scores.get(comp, 0) + weight

    return scores