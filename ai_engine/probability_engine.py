def probability_reasoning(problem_words, failures):

    scores = []

    for failure in failures:

        score = 0

        symptoms = failure.get("symptoms", [])
        causes = failure.get("possible_causes", [])

        # -------------------------
        # SYMPTOM MATCH
        # -------------------------

        for symptom in symptoms:

            symptom_words = symptom.lower().split()

            match_count = 0

            for word in symptom_words:

                if word in problem_words:
                    match_count += 1

            if match_count >= 2:
                score += 25

            elif match_count == 1:
                score += 10

        # -------------------------
        # CAUSE MATCH
        # -------------------------

        for cause in causes:

            for word in cause.lower().split():

                if word in problem_words:
                    score += 3

        # -------------------------
        # PROBABILITY WEIGHT
        # -------------------------

        score += failure.get("probability", 3) * 2

        scores.append((failure, score))

    return scores