from models.models import DiagnosticLearning, db
from collections import defaultdict


# =============================
# SAVE LEARNING
# =============================

def save_learning(problem, answers, final_issue, user_id=None):

    try:
        entry = DiagnosticLearning(
            user_id=user_id,
            problem=problem,
            answers=str(answers),
            final_issue=final_issue
        )

        db.session.add(entry)
        db.session.commit()

        print("🧠 Learning Saved:", {
            "problem": problem,
            "answers": answers,
            "final_issue": final_issue,
            "user_id": user_id
        })

    except Exception as e:
        print("❌ Learning Save Error:", e)


# =============================
# GET LEARNING BOOST
# =============================

def get_learning_boost(problem, answers, user_id=None):

    boost_map = defaultdict(int)

    try:
        records = (
            DiagnosticLearning.query
            .filter(DiagnosticLearning.problem.contains(problem[:120]))
            .order_by(DiagnosticLearning.id.desc())
            .limit(50)
            .all()
        )

        for r in records:

            issue = (r.final_issue or "").lower()

            # 🔥 GLOBAL LEARNING BOOST
            boost_map[issue] += 2

            # 🔥 USER PERSONAL BOOST (HIGH IMPACT)
            if user_id and r.user_id == user_id:
                boost_map[issue] += 5

        print("🧠 BOOST MAP:", dict(boost_map))

    except Exception as e:
        print("❌ Learning Fetch Error:", e)

    return boost_map
