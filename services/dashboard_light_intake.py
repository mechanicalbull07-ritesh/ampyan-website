from werkzeug.utils import secure_filename


DASHBOARD_LIGHT_HINTS = {
    "check_engine": "check engine light on",
    "check_engine_flashing": "check engine light flashing",
    "battery": "battery warning light on",
    "oil": "oil pressure warning light on",
    "temperature": "temperature warning light on",
    "brake": "brake warning light on",
    "abs": "ABS warning light on",
    "airbag": "airbag warning light on",
    "tpms": "TPMS warning light on",
    "multiple": "multiple dashboard warning lights on",
    "unknown": "dashboard warning light photo uploaded unknown dashboard warning light",
}


def dashboard_light_context(files=None, form=None, data=None):
    form = form or {}
    data = data or {}
    hint = (form.get("dashboard_light_hint") or data.get("dashboard_light_hint") or "").strip().lower()
    context = DASHBOARD_LIGHT_HINTS.get(hint, "")

    image_file = files.get("dashboard_image") if files else None
    filename = secure_filename(getattr(image_file, "filename", "") or "")
    if filename:
        lower_filename = filename.lower()
        for key, phrase in DASHBOARD_LIGHT_HINTS.items():
            if key != "unknown" and key.replace("_", "-") in lower_filename:
                context = f"{context} {phrase}".strip()
        if not context:
            context = DASHBOARD_LIGHT_HINTS["unknown"]

    return context
