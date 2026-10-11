def generate_questions(problem, initial_results):

    questions = []

    problem = problem.lower()

    # FIX: more flexible condition
    if "vibration" in problem and "brake" in problem:

        questions = [
            {
                "id": "steering_vibration",
                "text": "Kya steering bhi vibrate karta hai?",
                "type": "yes_no"
            },
            {
                "id": "high_speed",
                "text": "High speed par vibration zyada hota hai?",
                "type": "yes_no"
            },
            {
                "id": "noise",
                "text": "Brake lagate waqt awaz bhi aati hai?",
                "type": "yes_no"
            }
        ]

    elif "vibration" in problem:

        questions = [
            {
                "id": "idle_vibration",
                "text": "Kya car idle pe bhi vibrate karti hai?",
                "type": "yes_no"
            }
        ]

    return questions