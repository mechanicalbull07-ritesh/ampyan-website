import json
import os
import secrets
import re
from urllib.parse import parse_qs, urlparse

from flask import (
    Blueprint, abort, current_app, flash, redirect, render_template,
    request, session, url_for,
)
from flask_login import current_user, login_required

from services.blog_api_client import BlogApiClient, BlogApiError


blog_bp = Blueprint("website_blogs", __name__, url_prefix="/blogs")
TRUE_VALUES = {"true", "1", "yes", "on"}
REPORT_REASONS = {
    "spam", "abusive", "misinformation", "copyright",
    "unsafe_advice", "duplicate", "other",
}
BLOG_IMAGE_MAX_BYTES = 8 * 1024 * 1024


def blog_enabled():
    value = current_app.config.get(
        "COMMUNITY_BLOG_ENABLED",
        os.environ.get("COMMUNITY_BLOG_ENABLED", "false"),
    )
    return str(value or "").strip().lower() in TRUE_VALUES


@blog_bp.before_request
def require_blog_feature():
    if not blog_enabled():
        abort(404)


def client():
    return BlogApiClient(
        base_url=current_app.config.get("AMPYAN_API_BASE_URL"),
        service_token=current_app.config.get("BLOG_WEBSITE_SERVICE_TOKEN"),
    )


def actor_id():
    return int(current_user.id) if current_user.is_authenticated else None


def safe_public_url(value):
    parsed = urlparse(str(value or "").strip())
    return (
        parsed.geturl()
        if parsed.scheme == "https" and bool(parsed.netloc)
        else ""
    )


YOUTUBE_ID_RE = re.compile(r"^[A-Za-z0-9_-]{11}$")
INSTAGRAM_CODE_RE = re.compile(r"^[A-Za-z0-9_-]+$")


def youtube_embed_url(value):
    """Return a no-cookie player URL for a supported YouTube URL."""
    parsed = urlparse(str(value or "").strip())
    if parsed.scheme != "https" or parsed.username or parsed.password:
        return ""
    host = (parsed.hostname or "").lower().rstrip(".")
    parts = [part for part in parsed.path.split("/") if part]
    video_id = ""
    if host == "youtu.be" and parts:
        video_id = parts[0]
    elif host in {"youtube.com", "www.youtube.com", "m.youtube.com"}:
        if parsed.path == "/watch":
            video_id = parse_qs(parsed.query).get("v", [""])[0]
        elif len(parts) == 2 and parts[0] in {"shorts", "embed"}:
            video_id = parts[1]
    if not YOUTUBE_ID_RE.fullmatch(video_id):
        return ""
    return f"https://www.youtube-nocookie.com/embed/{video_id}"


def instagram_embed(value):
    """Return validated canonical and embed URLs for a post or Reel."""
    parsed = urlparse(str(value or "").strip())
    if parsed.scheme != "https" or parsed.username or parsed.password:
        return None
    host = (parsed.hostname or "").lower().rstrip(".")
    parts = [part for part in parsed.path.split("/") if part]
    if (
        host not in {"instagram.com", "www.instagram.com"}
        or len(parts) != 2
        or parts[0] not in {"p", "reel"}
        or not INSTAGRAM_CODE_RE.fullmatch(parts[1])
    ):
        return None
    canonical = f"https://www.instagram.com/{parts[0]}/{parts[1]}/"
    return {"url": canonical, "embed_url": f"{canonical}embed/"}


def safe_back_url(default_endpoint="website_blogs.index"):
    target = request.referrer
    if target:
        parsed = urlparse(target)
        expected = urlparse(request.url_root)
        if (
            parsed.scheme in {"http", "https"}
            and parsed.scheme == expected.scheme
            and parsed.netloc == expected.netloc
        ):
            return target
    return url_for(default_endpoint)


def _items(data):
    return data.get("items", []) if isinstance(data, dict) else []


def _comment_tree(items):
    roots, by_id = [], {}
    for raw in items:
        if not isinstance(raw, dict):
            continue
        comment = dict(raw)
        comment["replies"] = []
        by_id[comment.get("id")] = comment
    for comment in by_id.values():
        parent = by_id.get(comment.get("parent_comment_id"))
        if parent and parent.get("parent_comment_id") is None:
            parent["replies"].append(comment)
        else:
            roots.append(comment)
    return roots


def _handle_error(exc, *, private=False):
    if exc.status == 404:
        abort(404)
    if exc.status in {401, 403}:
        if private:
            flash(exc.message, "error")
            return redirect(url_for("website_blogs.index"))
        abort(404)
    return render_template(
        "blogs/unavailable.html",
        message=exc.message,
        noindex=True,
    ), exc.status if exc.status in {409, 429, 503} else 503


def _editor_payload():
    try:
        blocks = json.loads(request.form.get("content_blocks") or "[]")
    except (TypeError, ValueError):
        raise BlogApiError(
            "BLOG_VALIDATION_FAILED",
            "Content blocks must be valid JSON.",
            400,
        )
    if not isinstance(blocks, list):
        raise BlogApiError(
            "BLOG_VALIDATION_FAILED",
            "Content blocks must be a list.",
            400,
        )
    return {
        "title": (request.form.get("title") or "").strip(),
        "subtitle": (request.form.get("subtitle") or "").strip(),
        "cover_image_url": (request.form.get("cover_image_url") or "").strip(),
        "category": (request.form.get("category") or "").strip() or None,
        "tags": [
            item.strip()
            for item in (request.form.get("tags") or "").split(",")
            if item.strip()
        ],
        "content_blocks": blocks,
    }


def _taxonomy(api):
    categories, tags = [], []
    try:
        categories = _items(api.list_categories())
        tags = _items(api.list_tags())
    except BlogApiError:
        pass
    return categories, tags


@blog_bp.get("")
def index():
    params = {
        key: value
        for key in ("query", "category", "tag", "author", "sort", "cursor")
        if (value := (request.args.get(key) or "").strip())
    }
    if params.get("sort") not in {None, "latest", "popular", "trending", "most_discussed"}:
        params["sort"] = "latest"
    api = client()
    try:
        data, meta = api.list_blogs(params, actor_id())
        categories, tags = _taxonomy(api)
    except BlogApiError as exc:
        return _handle_error(exc)
    return render_template(
        "blogs/index.html",
        blogs=_items(data),
        meta=meta,
        categories=categories,
        tags=tags,
        filters=params,
        safe_public_url=safe_public_url,
        meta_title="Community Blog",
        meta_description="Automotive stories and practical advice from the AMPYAN community.",
    )


@blog_bp.get("/me")
@login_required
def my_blogs():
    try:
        blogs = _items(client().list_my_blogs(actor_id()))
    except BlogApiError as exc:
        return _handle_error(exc, private=True)
    return render_template("blogs/my_blogs.html", blogs=blogs, noindex=True)


@blog_bp.get("/me/analytics")
@login_required
def analytics():
    try:
        analytics_data = client().get_my_analytics(actor_id())
    except BlogApiError as exc:
        return _handle_error(exc, private=True)
    return render_template(
        "blogs/analytics.html", analytics=analytics_data, noindex=True
    )


@blog_bp.route("/write", methods=["GET", "POST"])
@login_required
def write():
    api = client()
    categories, tags = _taxonomy(api)
    key = session.get("blog_draft_idempotency_key")
    if not key:
        key = secrets.token_urlsafe(32)
        session["blog_draft_idempotency_key"] = key
    if request.method == "POST":
        try:
            created = api.create_draft(_editor_payload(), actor_id(), key)
            session.pop("blog_draft_idempotency_key", None)
            flash("Draft created safely.", "success")
            return redirect(url_for("website_blogs.edit", blog_id=created["id"]))
        except BlogApiError as exc:
            return render_template(
                "blogs/editor.html", blog=None, categories=categories, tags=tags,
                error=exc.message, preserved=request.form, noindex=True,
            ), exc.status
    return render_template(
        "blogs/editor.html", blog=None, categories=categories, tags=tags, noindex=True
    )


def _owned_blog(api, blog_id):
    return next(
        (item for item in _items(api.list_my_blogs(actor_id())) if item.get("id") == blog_id),
        None,
    )


@blog_bp.route("/<int:blog_id>/edit", methods=["GET", "POST"])
@login_required
def edit(blog_id):
    api = client()
    try:
        blog = _owned_blog(api, blog_id)
        if blog is None:
            abort(404)
        categories, tags = _taxonomy(api)
        if request.method == "POST":
            try:
                updated = api.update_draft(
                    blog_id, _editor_payload(), actor_id(),
                    request.form.get("version"),
                )
                flash("Draft saved.", "success")
                return redirect(url_for("website_blogs.edit", blog_id=blog_id))
            except BlogApiError as exc:
                return render_template(
                    "blogs/editor.html", blog=blog, categories=categories, tags=tags,
                    error=exc.message, conflict=exc.code == "BLOG_EDIT_CONFLICT",
                    preserved=request.form, noindex=True,
                ), exc.status
        return render_template(
            "blogs/editor.html", blog=blog, categories=categories, tags=tags,
            noindex=True,
        )
    except BlogApiError as exc:
        return _handle_error(exc, private=True)


def _action(method_name, blog_id, success):
    try:
        getattr(client(), method_name)(blog_id, actor_id())
        flash(success, "success")
    except BlogApiError as exc:
        flash(exc.message, "error")
    return redirect(safe_back_url("website_blogs.my_blogs"))


@blog_bp.post("/<int:blog_id>/delete")
@login_required
def delete(blog_id):
    return _action("delete_draft", blog_id, "Draft deleted.")


@blog_bp.post("/<int:blog_id>/submit")
@login_required
def submit(blog_id):
    return _action("submit_blog", blog_id, "Blog submitted for review.")


@blog_bp.post("/<int:blog_id>/withdraw")
@login_required
def withdraw(blog_id):
    return _action("withdraw_blog", blog_id, "Blog returned to drafts.")


def _engage(blog_id, kind, enabled):
    try:
        client().set_engagement(blog_id, kind, enabled, actor_id())
        flash(f"{kind.title()} updated.", "success")
    except BlogApiError as exc:
        flash(exc.message, "error")
    return redirect(safe_back_url())


@blog_bp.post("/<int:blog_id>/like")
@login_required
def like(blog_id):
    return _engage(blog_id, "like", True)


@blog_bp.post("/<int:blog_id>/unlike")
@login_required
def unlike(blog_id):
    return _engage(blog_id, "like", False)


@blog_bp.post("/<int:blog_id>/bookmark")
@login_required
def bookmark(blog_id):
    return _engage(blog_id, "bookmark", True)


@blog_bp.post("/<int:blog_id>/unbookmark")
@login_required
def unbookmark(blog_id):
    return _engage(blog_id, "bookmark", False)


@blog_bp.post("/authors/<int:author_id>/follow")
@login_required
def follow(author_id):
    return _follow(author_id, True)


@blog_bp.post("/authors/<int:author_id>/unfollow")
@login_required
def unfollow(author_id):
    return _follow(author_id, False)


def _follow(author_id, enabled):
    try:
        client().set_follow(author_id, enabled, actor_id())
        flash("Author follow preference updated.", "success")
    except BlogApiError as exc:
        flash(exc.message, "error")
    return redirect(safe_back_url())


@blog_bp.post("/<int:blog_id>/comments")
@login_required
def add_comment(blog_id):
    body = (request.form.get("body") or "").strip()
    if not body or len(body) > 2000:
        flash("Comments must contain 1–2,000 characters.", "error")
    else:
        try:
            client().create_comment(
                blog_id,
                {"body": body, "parent_comment_id": request.form.get("parent_comment_id") or None},
                actor_id(),
            )
            flash("Comment added.", "success")
        except BlogApiError as exc:
            flash(exc.message, "error")
    return redirect(safe_back_url())


@blog_bp.post("/comments/<int:comment_id>/edit")
@login_required
def edit_comment(comment_id):
    try:
        client().edit_comment(comment_id, (request.form.get("body") or "").strip(), actor_id())
        flash("Comment updated.", "success")
    except BlogApiError as exc:
        flash(exc.message, "error")
    return redirect(safe_back_url())


@blog_bp.post("/comments/<int:comment_id>/delete")
@login_required
def delete_comment(comment_id):
    try:
        client().delete_comment(comment_id, actor_id())
        flash("Comment removed.", "success")
    except BlogApiError as exc:
        flash(exc.message, "error")
    return redirect(safe_back_url())


@blog_bp.post("/<int:blog_id>/report")
@login_required
def report(blog_id):
    reason = (request.form.get("reason") or "").strip()
    if reason not in REPORT_REASONS:
        flash("Choose a valid report reason.", "error")
    else:
        try:
            client().report_blog(
                blog_id,
                {"reason": reason, "details": request.form.get("details") or ""},
                actor_id(),
            )
            flash("Report received for review. It does not automatically remove the Blog.", "success")
        except BlogApiError as exc:
            flash(exc.message, "error")
    return redirect(safe_back_url())


@blog_bp.post("/media")
@login_required
def media():
    uploaded = request.files.get("image")
    if not uploaded or uploaded.mimetype not in {"image/png", "image/jpeg", "image/webp"}:
        return {"success": False, "message": "Choose a PNG, JPEG or WebP image."}, 400
    uploaded.stream.seek(0, os.SEEK_END)
    size = uploaded.stream.tell()
    uploaded.stream.seek(0)
    if size > BLOG_IMAGE_MAX_BYTES:
        return {"success": False, "message": "Image must be 8 MB or smaller."}, 413
    try:
        return {"success": True, "media": client().upload_media(uploaded, actor_id())}
    except BlogApiError as exc:
        return {"success": False, "message": exc.message, "code": exc.code}, exc.status


@blog_bp.get("/moderation")
@login_required
def moderation():
    try:
        blogs = _items(client().list_moderation_queue(actor_id(), request.args.get("status")))
    except BlogApiError as exc:
        return _handle_error(exc, private=True)
    return render_template("blogs/moderation.html", blogs=blogs, noindex=True)


@blog_bp.post("/<int:blog_id>/moderate")
@login_required
def moderate(blog_id):
    action = (request.form.get("action") or "").strip()
    reason = (request.form.get("reason") or "").strip()
    if action in {"reject", "archive"} and not reason:
        flash("A reason is required for this moderation action.", "error")
    else:
        try:
            client().moderate_blog(
                blog_id, {"action": action, "reason": reason},
                actor_id(), request.form.get("version"),
            )
            flash("Moderation action recorded.", "success")
        except BlogApiError as exc:
            flash(exc.message, "error")
    return redirect(url_for("website_blogs.moderation"))


@blog_bp.get("/<string:slug>")
def detail(slug):
    api = client()
    try:
        blog = api.get_blog(slug, actor_id())
        comments, comment_meta = api.list_comments(blog["id"])
    except BlogApiError as exc:
        return _handle_error(exc)
    view_session = session.get("blog_view_session")
    if not view_session:
        view_session = secrets.token_urlsafe(24)
        session["blog_view_session"] = view_session
    try:
        api.record_view(blog["id"], view_session)
    except BlogApiError:
        pass
    try:
        related = _items(api.list_related_blogs(blog["id"], actor_id()))
    except BlogApiError:
        related = []
    return render_template(
        "blogs/detail.html",
        blog=blog,
        comments=_comment_tree(_items(comments)),
        related_blogs=related,
        comment_meta=comment_meta,
        safe_public_url=safe_public_url,
        youtube_embed_url=youtube_embed_url,
        instagram_embed=instagram_embed,
        meta_title=blog.get("title"),
        meta_description=blog.get("excerpt"),
        meta_image=safe_public_url(blog.get("cover_image_url")) or None,
        meta_type="article",
        meta_url=request.base_url,
    )
