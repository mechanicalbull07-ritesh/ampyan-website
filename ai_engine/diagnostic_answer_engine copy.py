# -----------------------------------------
# MOTRONIX AI V9 - ANSWER BASED REASONING
# -----------------------------------------

def refine_results(results, answers):

    if not results:
        return results

    top_issue = results[0]["issue"]

    # Brake logic
    if top_issue == "Brake Pad Wear":

        if answers.get("brake_vibration") == "yes":
            results[0]["issue"] = "Brake Disc Warped"
            results[0]["confidence"] = 92

    if top_issue == "Brake Disc Warped":

        if answers.get("brake_vibration") == "no":
            results[0]["issue"] = "Brake Pad Wear"
            results[0]["confidence"] = 88

    # Example engine logic
    if top_issue == "Engine Misfire":

        if answers.get("engine_vibration") == "yes":
            results[0]["issue"] = "Ignition Coil Failure"
            results[0]["confidence"] = 90

    return results