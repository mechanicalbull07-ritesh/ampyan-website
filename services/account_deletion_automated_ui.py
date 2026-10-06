"""Preserved P16D handlers. Not imported/registered in manual 1.0.5.
Future integration requires explicit security/release review.
"""
@app.route("/account-deletion", methods=["GET", "POST"])
def account_deletion_request():
    from services.account_deletion_client import public_call
    from services.canonical_garage_client import GarageError
    if request.method == "POST":
        email = request.form.get("email", "").strip()
        action = request.form.get("action", "request")
        if action == "verify":
            payload = {"request_id": request.form.get("request_id", "")[:32], "code": request.form.get("code", "")[:128]}
            endpoint = "/api/account-deletion/verify"
        else:
            if (len(email) > 150 or not re.fullmatch(r"[^@\s]+@[^@\s]+\.[^@\s]+", email) or request.form.get("confirm") != "yes"):
                flash("Provide an account email and deliberate confirmation. Never send passwords.")
                return render_template("account_deletion.html"), 400
            payload = {"email": email, "confirm": True}
            endpoint = "/api/account-deletion/public"
        try:
            public_call(endpoint, payload)
            flash("Verification accepted. AMPYAN administrator will review the request; deletion has not yet completed." if action == "verify" else "If eligible, verification instructions are queued for the stored account email. This response does not confirm account existence or email delivery. No account has been deleted.")
        except GarageError:
            flash("Unable to continue now. Retry later. No deletion completion is confirmed.")
            return render_template("account_deletion.html"), 503
        return redirect("/account-deletion")
    return render_template("account_deletion.html")


@app.route("/admin/account-deletion", methods=["GET", "POST"])
@login_required
def deletion_admin_queue():
    from services.account_deletion_client import admin_call
    from services.canonical_garage_client import GarageError
    if current_user.role != "admin" or current_user.is_banned:
        abort(403)
    try:
        if request.method == "POST":
            rid = request.form.get("request_id", "")
            if not re.fullmatch(r"[0-9a-f]{32}", rid):abort(400)
            action = request.form.get("action", "")
            if action not in ("process", "complete", "reject", "send-verification", "retry-completion-mail"):abort(400)
            admin_call("/api/admin/account-deletion/" + rid + "/" + action, "POST", {"confirm": True})
        rows = admin_call("/api/admin/account-deletion").get("requests", [])
    except GarageError:
        return "Connect an authorized administrator Garage session; deletion service may be unavailable.", 503
    return render_template("account_deletion_admin.html", requests=rows)


@app.route("/admin/account-deletion/<rid>", methods=["GET", "POST"])
@login_required
def deletion_admin_tasks(rid):
    from services.account_deletion_client import admin_call
    from services.canonical_garage_client import GarageError
    if current_user.role != "admin" or current_user.is_banned:abort(403)
    if not re.fullmatch(r"[0-9a-f]{32}", rid):abort(400)
    try:
        if request.method == "POST":
            tid = request.form.get("task_id", "")
            if not re.fullmatch(r"[0-9a-f]{32}", tid) or request.form.get("confirm") != "yes":abort(400)
            admin_call("/api/admin/account-deletion/" + rid + "/tasks/" + tid + "/review", "POST", {"confirm": True, "evidence_hash": request.form.get("evidence_hash", "")})
        rows = admin_call("/api/admin/account-deletion/" + rid + "/tasks").get("tasks", [])
        for row in rows:
            if row["kind"] not in ("COMPLETION_EMAIL", "VERIFICATION_EMAIL"):
                row["review"] = admin_call("/api/admin/account-deletion/" + rid + "/tasks/" + row["id"]).get("review", {})
    except GarageError:return "Operator cleanup remains pending. No completion confirmed.", 503
    return render_template("account_deletion_tasks.html", tasks=rows)