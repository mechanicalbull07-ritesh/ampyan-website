import json
import os
import sys


PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from failure_database import FAILURE_DATABASE, validate_failure_database


def main():
    report = validate_failure_database(FAILURE_DATABASE)
    print(json.dumps(report, indent=2, sort_keys=True))

    blocking_keys = [
        "missing_required_fields",
        "missing_question_impact",
        "invalid_urgency",
        "invalid_severity",
        "invalid_repair_cost",
        "empty_symptoms",
        "empty_questions",
    ]
    has_blockers = any(report.get(key) for key in blocking_keys)
    return 1 if has_blockers else 0


if __name__ == "__main__":
    raise SystemExit(main())
