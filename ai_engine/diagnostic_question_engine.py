# ai_engine/diagnostic_question_engine.py


QUESTION_RULES = {

    "brake":[

        {
            "question":"Does the noise happen only when braking?",
            "key":"brake_noise"
        },

        {
            "question":"Does the car vibrate when braking?",
            "key":"brake_vibration"
        }

    ],

    "battery":[

        {
            "question":"Do dashboard lights turn on when starting?",
            "key":"dashboard_lights"
        },

        {
            "question":"Do you hear a clicking sound while starting?",
            "key":"clicking_sound"
        }

    ],

    "starter":[

        {
            "question":"Do dashboard lights turn on when starting?",
            "key":"dashboard_lights"
        },

        {
            "question":"Do you hear a clicking sound while starting?",
            "key":"clicking_sound"
        }

    ],

    "cooling":[

        {
            "question":"Does temperature rise in traffic?",
            "key":"traffic_overheat"
        },

        {
            "question":"Do you see coolant leakage?",
            "key":"coolant_leak"
        }

    ]

}


def generate_questions(top_issue):

    issue = top_issue.lower()

    questions = []

    for key, qlist in QUESTION_RULES.items():

        if key in issue:

            questions.extend(qlist)

    # limit questions
    return questions[:3]