import re


STOPWORDS = {
    "a", "an", "and", "are", "at", "but", "car", "from", "hai", "he", "is",
    "ka", "ki", "me", "mein", "my", "of", "on", "or", "the", "to", "while",
    "with",
}


def _tokens(text):
    return [
        token
        for token in re.findall(r"[a-z0-9]+", (text or "").lower())
        if len(token) > 2 and token not in STOPWORDS
    ]


def _phrase_score(text, problem_words, phrase):
    phrase_text = (phrase or "").lower().strip()
    if not phrase_text:
        return 0

    phrase_tokens = _tokens(phrase_text)
    if not phrase_tokens:
        return 0

    if phrase_text in text:
        return 45 + min(20, len(phrase_tokens) * 3)

    matched = sum(1 for token in phrase_tokens if token in problem_words)
    coverage = matched / len(phrase_tokens)

    if coverage >= 0.8 and matched >= 2:
        return 30
    if coverage >= 0.6 and matched >= 2:
        return 18
    if matched == 1 and len(phrase_tokens) == 1:
        return 6

    return 0


def probability_reasoning(problem_words, failures, problem_text=""):

    scores = []
    problem_words = set(problem_words)
    text = (problem_text or " ".join(problem_words)).lower()

    for failure in failures:

        score = 0

        symptoms = failure.get("symptoms", [])
        aliases = failure.get("aliases", [])
        causes = failure.get("possible_causes", [])

        # -------------------------
        # SYMPTOM MATCH
        # -------------------------

        for symptom in symptoms:
            score += _phrase_score(text, problem_words, symptom)

        for alias in aliases:
            score += min(35, _phrase_score(text, problem_words, alias))

        # -------------------------
        # CAUSE MATCH
        # -------------------------

        for cause in causes:
            score += min(12, _phrase_score(text, problem_words, cause) // 4)

        # -------------------------
        # PROBABILITY WEIGHT
        # -------------------------

        score += failure.get("probability", 3)

        scores.append((failure, score))

    return scores
