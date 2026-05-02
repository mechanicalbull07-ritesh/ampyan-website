SYMPTOM_GRAPH = {

    "misfire": {
        "spark plug": 10,
        "ignition coil": 9,
        "fuel injector": 7
    },

    "shaking": {
        "spark plug": 8,
        "ignition coil": 7,
        "engine mount": 6
    },

    "vibration": {
        "engine mount": 8,
        "wheel balance": 6,
        "brake disc": 5
    },

    "power": {
        "fuel injector": 8,
        "turbocharger": 6,
        "air filter": 5
    },

    "brake": {
        "brake disc": 9,
        "brake pad": 7
    }

}

def graph_reasoning(problem_words):

    component_scores = {}

    for word in problem_words:

        if word in SYMPTOM_GRAPH:

            components = SYMPTOM_GRAPH[word]

            for comp, score in components.items():

                component_scores[comp] = component_scores.get(comp,0) + score

    return component_scores