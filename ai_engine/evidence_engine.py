# ---------------------------------------
# Evidence Adjustment Engine
# ---------------------------------------

EVIDENCE_RULES = {

    "Brake Pad Wear":{

        "brake_noise":5,
        "brake_vibration":-10
    },

    "Brake Disc Warped":{

        "brake_vibration":15,
        "brake_noise":5
    },

    "Brake Dust Accumulation":{

        "brake_noise":5,
        "brake_vibration":-5
    },

    "Battery Dead":{

        "dashboard_lights_no":15,
        "clicking_sound_yes":10
    },

    "Starter Motor Failure":{

        "clicking_sound_yes":15
    },

    "Alternator Failure":{

        "dashboard_lights_yes":10
    }

}


def adjust_scores(results, answers):

    if not answers:
        return results

    for result in results:

        issue = result["issue"]
        confidence = result["confidence"]

        rules = EVIDENCE_RULES.get(issue)

        if not rules:
            continue

        for key, value in rules.items():

            parts = key.rsplit("_", 1)

            if len(parts) == 2:

                question = parts[0]
                expected = parts[1]

                if answers.get(question) == expected:
                    confidence += value

            else:

                if answers.get(key) == "yes":
                    confidence += value

        confidence = max(5, min(confidence, 95))

        result["confidence"] = confidence

    results.sort(key=lambda x: x["confidence"], reverse=True)

    return results