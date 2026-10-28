from models.models import DiagnosticLearning, db
from collections import defaultdict
from flask import current_app


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

        current_app.logger.info("diagnosis_learning_saved issue=%s user_id=%s", final_issue, user_id)

    except Exception as e:
        try:
            current_app.logger.warning("diagnosis_learning_save_skipped error=%s", e.__class__.__name__)
        except Exception:
            pass


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

        current_app.logger.info("diagnosis_learning_boost_loaded count=%s", len(boost_map))

    except Exception as e:
        try:
            current_app.logger.warning("diagnosis_learning_boost_skipped error=%s", e.__class__.__name__)
        except Exception:
            pass

    return boost_map
