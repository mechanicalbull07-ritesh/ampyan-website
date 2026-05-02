# -----------------------------------------
# EXPLANATION ENGINE
# -----------------------------------------

def generate_explanation(problem_text, failure, answers):

    explanation = []

    text = problem_text.lower()

    # ---------------------------------
    # symptom explanation
    # ---------------------------------

    for symptom in failure["symptoms"]:

        if symptom.lower() in text:

            explanation.append(
                f"Symptom match: {symptom}"
            )

    # ---------------------------------
    # component explanation
    # ---------------------------------

    component = failure.get("component", "")

    if component:

        explanation.append(
            f"Component match: {component}"
        )

    # ---------------------------------
    # system explanation
    # ---------------------------------

    system = failure.get("system", "")

    if system:

        explanation.append(
            f"System detected: {system}"
        )

    # ---------------------------------
    # answer explanation
    # ---------------------------------

    if answers:

        for key, value in answers.items():

            if value == "yes":

                explanation.append(
                    f"User confirmed: {key}"
                )

    return explanation