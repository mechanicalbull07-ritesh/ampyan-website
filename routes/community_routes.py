from datetime import datetime, timedelta
import json
import os
from types import SimpleNamespace
from urllib import error, parse, request as urllib_request

from flask import Blueprint, current_app, flash, jsonify, redirect, render_template, request, url_for
from flask_login import current_user, login_required
from models.models import CarCommunity, Comment, Post, User, Vote, db
from sqlalchemy import or_
from sqlalchemy.orm import selectinload
from werkzeug.utils import secure_filename

community_bp = Blueprint("community", __name__)
REMOTE_POST_CACHE = {"expires_at": None, "posts": []}
REMOTE_CACHE_TTL_SECONDS = int(os.environ.get("REMOTE_COMMUNITY_CACHE_SECONDS", "60"))


class RemoteSyncError(Exception):
    pass


def _ampyan_api_base_url():
    return (os.environ.get("AMPYAN_API_BASE_URL") or "https://ampyan-api.onrender.com").rstrip("/")


def _ampyan_api_request(path, method="GET", payload=None, timeout=3):
    url = f"{_ampyan_api_base_url()}{path}"
    data = None
    headers = {}
    if payload is not None:
        data = json.dumps(payload).encode("utf-8")
        headers["Content-Type"] = "application/json"

    req = urllib_request.Request(url, data=data, headers=headers, method=method)
    try:
        with urllib_request.urlopen(req, timeout=timeout) as response:
            raw = response.read().decode("utf-8")
            return json.loads(raw) if raw else {}
    except error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="ignore")
        raise RemoteSyncError(f"{exc.code} {body}".strip())
    except Exception as exc:
        raise RemoteSyncError(str(exc))


def _safe_remote_call(path, method="GET", payload=None, timeout=3):
    try:
        return _ampyan_api_request(path, method=method, payload=payload, timeout=timeout)
    except RemoteSyncError as exc:
        current_app.logger.warning("AMPYAN API sync failed for %s: %s", path, exc)
        return None


def _sync_user_profile(user):
    payload = {
        "name": user.username,
        "email": user.email,
        "phone": user.mobile or "",
        "user_email": user.email,
    }
    return _safe_remote_call("/profile/sync", method="POST", payload=payload)


def _author_avatar_url(profile_photo):
    if not profile_photo:
        return None
    if profile_photo.startswith("http://") or profile_photo.startswith("https://"):
        return profile_photo
    return url_for("static", filename=f"profile_images/{profile_photo}")


def _slugify(text):
    slug = "".join(char.lower() if char.isalnum() else "-" for char in (text or ""))
    return "-".join(part for part in slug.split("-") if part)


def _get_or_create_car_community(name, description="", user=None):
    name = (name or "").strip()
    if not name:
        return None

    slug = _slugify(name)
    if not slug:
        return None

    community = CarCommunity.query.filter_by(slug=slug).first()
    if community:
        return community

    community = CarCommunity(
        name=name[:120],
        slug=slug[:140],
        description=(description or f"{name} owners and enthusiasts community.")[:255],
        created_by=user.id if user and user.is_authenticated else None,
    )
    db.session.add(community)
    db.session.flush()
    return community


def _decorate_local_comment(comment):
    comment.author_name = comment.user.username
    comment.author_badge = getattr(comment.user, "badge", "Member")
    comment.author_avatar_url = _author_avatar_url(getattr(comment.user, "profile_photo", None))
    comment.author_avatar_letter = (comment.user.username[:1] or "U").upper()
    comment.can_edit = bool(
        current_user.is_authenticated
        and (current_user.id == comment.user_id or current_user.role == "admin")
    )
    comment.edit_url = url_for("community.edit_comment", comment_id=comment.id)
    comment.delete_url = url_for("community.delete_comment", comment_id=comment.id)
    return comment


def _decorate_local_post(post):
    post.is_remote = False
    post.remote_id = None
    post.detail_url = url_for("community.post_detail", post_id=post.id)
    post.share_url = url_for("community.post_detail", post_id=post.id, _external=True)
    post.reply_url = url_for("community.add_comment", post_id=post.id)
    post.vote_url = url_for("community.upvote", post_id=post.id)
    post.delete_url = url_for("community.delete_post", post_id=post.id)
    post.edit_url = url_for("community.edit_post", post_id=post.id)
    post.vote_count = len(post.votes)
    post.reply_count = len(post.comments)
    post.image_url = url_for("static", filename=f"post_images/{post.image}") if post.image else None
    post.community_name = post.car_community.name if post.car_community else "General Community"
    post.community_slug = post.car_community.slug if post.car_community else None
    post.community_url = (
        url_for("community.community", car_community=post.community_slug)
        if post.community_slug
        else url_for("community.community")
    )
    post.author_display_name = post.author.username
    post.author_badge = getattr(post.author, "badge", "Member")
    post.author_reputation = getattr(post.author, "reputation", 0)
    post.author_city = getattr(post.author, "city", None)
    post.author_avatar_url = _author_avatar_url(getattr(post.author, "profile_photo", None))
    post.author_avatar_letter = (post.author.username[:1] or "U").upper()
    post.preview_text = post.content[:180] + ("..." if len(post.content) > 180 else "")
    sorted_comments = sorted(
        [comment for comment in post.comments if comment.parent_id is None],
        key=lambda item: item.id,
        reverse=True,
    )
    post.top_comments = [_decorate_local_comment(comment) for comment in sorted_comments[:4]]
    post.can_edit = bool(
        current_user.is_authenticated
        and (current_user.id == post.user_id or current_user.role == "admin")
    )
    post.can_vote = True
    post.comments = [_decorate_local_comment(comment) for comment in post.comments]
    post.reply_threads = [comment for comment in post.comments if comment.parent_id is None]
    return post


def _remote_title(text):
    base_text = (text or "Untitled").strip().splitlines()[0]
    return (base_text[:80] + "...") if len(base_text) > 80 else base_text


def _social_preview_text(text, fallback="AMPYAN community discussion"):
    cleaned = " ".join((text or "").split())
    if not cleaned:
        cleaned = fallback
    return cleaned[:157] + "..." if len(cleaned) > 160 else cleaned


def _absolute_image_url(image_url):
    if not image_url:
        return url_for("static", filename="images/logo.png", _external=True)
    if str(image_url).startswith(("http://", "https://")):
        return image_url
    return parse.urljoin(request.url_root, str(image_url).lstrip("/"))


def _post_social_context(post):
    return {
        "meta_title": post.title,
        "meta_description": _social_preview_text(
            post.content,
            f"{post.community_name} discussion on AMPYAN.",
        ),
        "meta_url": post.share_url,
        "meta_image": _absolute_image_url(post.image_url),
        "meta_type": "article",
    }


def _build_remote_comment(reply):
    user = reply.get("user") or {}
    author_name = user.get("name") or user.get("email") or reply.get("userId") or "Community Member"
    return SimpleNamespace(
        id=f"remote-reply-{reply.get('id')}",
        user_id=user.get("id"),
        content=reply.get("text") or "",
        created_at=reply.get("created_at"),
        author_name=author_name,
        author_badge=user.get("role", "user").title(),
        author_avatar_url=_author_avatar_url(user.get("profile_photo")),
        author_avatar_letter=(author_name[:1] or "U").upper(),
        can_edit=False,
        edit_url=None,
        delete_url=None,
        replies=[],
        user=SimpleNamespace(username=author_name),
    )


def _build_remote_post(post):
    user = post.get("user") or {}
    author_name = user.get("name") or user.get("email") or post.get("userId") or "Community Member"
    replies = [_build_remote_comment(reply) for reply in (post.get("replies") or [])]
    image_url = post.get("imagePath")
    if image_url and not str(image_url).startswith(("http://", "https://", "/")):
        image_url = None
    return SimpleNamespace(
        id=f"remote-post-{post.get('id')}",
        remote_id=post.get("id"),
        is_remote=True,
        title=_remote_title(post.get("text") or "Untitled"),
        content=post.get("text") or "",
        image=None,
        image_url=image_url,
        created_at=post.get("created_at"),
        detail_url=url_for("community.remote_post_detail", remote_post_id=post.get("id")),
        share_url=url_for("community.remote_post_detail", remote_post_id=post.get("id"), _external=True),
        reply_url=url_for("community.remote_add_comment", remote_post_id=post.get("id")),
        vote_url=None,
        delete_url=None,
        edit_url=None,
        vote_count=0,
        community_name="Phone/App Feed",
        community_slug=None,
        community_url=url_for("community.community"),
        reply_count=len(replies),
        comments=replies,
        reply_threads=replies,
        top_comments=replies[:2],
        can_edit=False,
        can_vote=False,
        source=post.get("source") or "ampyan",
        author_display_name=author_name,
        author_badge=user.get("role", "user").title(),
        author_reputation=user.get("reputation", 0),
        author_city=post.get("location") or user.get("city"),
        author_avatar_url=_author_avatar_url(user.get("profile_photo")),
        author_avatar_letter=(author_name[:1] or "U").upper(),
        author=SimpleNamespace(
            username=author_name,
            badge=user.get("role", "user").title(),
            reputation=user.get("reputation", 0),
            city=post.get("location") or user.get("city"),
            profile_photo=user.get("profile_photo"),
            email=user.get("email"),
        ),
        preview_text=(post.get("text") or "")[:180] + ("..." if len(post.get("text") or "") > 180 else ""),
    )


def _load_remote_posts():
    now = datetime.utcnow()
    if REMOTE_POST_CACHE["expires_at"] and REMOTE_POST_CACHE["expires_at"] > now:
        return REMOTE_POST_CACHE["posts"]

    payload = _safe_remote_call("/community/export?include_replies=true")
    if not payload:
        return REMOTE_POST_CACHE["posts"] if REMOTE_POST_CACHE["posts"] else []

    remote_posts = []
    for post in payload.get("posts") or []:
        if (post.get("source") or "").lower() == "website":
            continue
        remote_posts.append(_build_remote_post(post))
    remote_posts = remote_posts[:40]
    REMOTE_POST_CACHE["posts"] = remote_posts
    REMOTE_POST_CACHE["expires_at"] = now + timedelta(seconds=REMOTE_CACHE_TTL_SECONDS)
    return remote_posts


def _load_remote_post(remote_post_id):
    for post in _load_remote_posts():
        if str(post.remote_id) == str(remote_post_id):
            return post
    return None


def _find_remote_post_id_for_website_post(local_post_id):
    payload = _safe_remote_call("/community/export?include_replies=true")
    if not payload:
        return None

    external_id = f"web-post-{local_post_id}"
    for post in payload.get("posts") or []:
        if (post.get("source") or "").lower() != "website":
            continue
        if str(post.get("external_id") or "") == external_id:
            return post.get("id")
    return None


def refresh_author_stats(user):
    posts_count = Post.query.filter_by(user_id=user.id).count()
    comments_count = Comment.query.filter_by(user_id=user.id).count()
    vote_count = (
        db.session.query(Vote)
        .join(Post, Vote.post_id == Post.id)
        .filter(Post.user_id == user.id)
        .count()
    )

    user.posts_count = posts_count
    user.reputation = max(0, (posts_count * 5) + (comments_count * 2) + (vote_count * 3))


def _create_local_post(title, content, community_id=None, new_community_name="", image_filename=None, external_image_url=None):
    car_community = None
    if new_community_name:
        car_community = _get_or_create_car_community(new_community_name, user=current_user)
    elif community_id:
        car_community = CarCommunity.query.get(community_id)

    post = Post(
        title=title,
        content=content,
        image=image_filename,
        user_id=current_user.id,
        community_id=car_community.id if car_community else None,
    )
    db.session.add(post)
    db.session.flush()

    current_user.posts_count = (current_user.posts_count or 0) + 1
    current_user.reputation = (current_user.reputation or 0) + 5
    _sync_user_profile(current_user)
    _safe_remote_call(
        "/community/posts",
        method="POST",
        payload={
            "source": "website",
            "external_id": f"web-post-{post.id}",
            "email": current_user.email,
            "fullName": current_user.username,
            "mobile": current_user.mobile or "",
            "location": current_user.city or "Website",
            "text": f"{title}\n\n{content}",
            "imageUrl": external_image_url,
            "community": car_community.name if car_community else "General Community",
        },
    )
    db.session.commit()
    return post


def _create_local_comment(post_id, content, parent_id=None):
    if parent_id and not Comment.query.filter_by(id=parent_id, post_id=post_id).first():
        parent_id = None

    new_comment = Comment(content=content, user_id=current_user.id, post_id=post_id, parent_id=parent_id)
    db.session.add(new_comment)
    db.session.flush()
    _sync_user_profile(current_user)

    remote_post_id = _find_remote_post_id_for_website_post(post_id)
    if remote_post_id:
        _safe_remote_call(
            f"/community/posts/{remote_post_id}/replies",
            method="POST",
            payload={
                "source": "website",
                "external_id": f"web-reply-{new_comment.id}",
                "email": current_user.email,
                "fullName": current_user.username,
                "mobile": current_user.mobile or "",
                "location": current_user.city or "Website",
                "text": content,
            },
        )

    db.session.commit()
    return new_comment


def _isoformat(value):
    return value.isoformat() if hasattr(value, "isoformat") else value


def _serialize_comment(comment):
    author_name = getattr(comment, "author_name", None)
    user = getattr(comment, "user", None)
    if not author_name and user:
        author_name = getattr(user, "username", None)

    return {
        "id": str(getattr(comment, "id", "")),
        "content": getattr(comment, "content", "") or "",
        "created_at": _isoformat(getattr(comment, "created_at", None)),
        "author": {
            "id": getattr(comment, "user_id", None),
            "name": author_name or "Community Member",
            "badge": getattr(comment, "author_badge", None) or getattr(user, "badge", "Member"),
            "profile_photo": getattr(comment, "author_avatar_url", None),
        },
        "replies": [_serialize_comment(reply) for reply in getattr(comment, "replies", [])],
    }


def _serialize_post(post):
    return {
        "id": str(getattr(post, "id", "")),
        "remote_id": getattr(post, "remote_id", None),
        "is_remote": bool(getattr(post, "is_remote", False)),
        "title": getattr(post, "title", "") or "",
        "content": getattr(post, "content", "") or "",
        "created_at": _isoformat(getattr(post, "created_at", None)),
        "image_url": getattr(post, "image_url", None),
        "detail_url": getattr(post, "detail_url", None),
        "share_url": getattr(post, "share_url", None),
        "vote_count": getattr(post, "vote_count", 0) or 0,
        "reply_count": getattr(post, "reply_count", 0) or 0,
        "community": {
            "name": getattr(post, "community_name", "General Community"),
            "slug": getattr(post, "community_slug", None),
        },
        "author": {
            "name": getattr(post, "author_display_name", "Community Member"),
            "badge": getattr(post, "author_badge", "Member"),
            "reputation": getattr(post, "author_reputation", 0) or 0,
            "city": getattr(post, "author_city", None),
            "profile_photo": getattr(post, "author_avatar_url", None),
        },
        "comments": [_serialize_comment(comment) for comment in getattr(post, "reply_threads", [])],
    }


def _community_feed(limit=50, include_remote=False):
    local_query = (
        Post.query
        .options(
            selectinload(Post.author),
            selectinload(Post.car_community),
            selectinload(Post.votes),
            selectinload(Post.comments).selectinload(Comment.user),
        )
        .order_by(Post.id.desc())
        .limit(limit)
    )
    local_posts = [_decorate_local_post(post) for post in local_query.all()]
    remote_posts = _load_remote_posts() if include_remote else []
    posts = sorted(
        local_posts + remote_posts,
        key=lambda post: str(getattr(post, "created_at", "") or ""),
        reverse=True,
    )
    return posts[:limit]


@community_bp.route("/api/community/posts")
def api_community_posts():
    limit = min(max(request.args.get("limit", default=50, type=int) or 50, 1), 100)
    include_remote = request.args.get("include_remote", "").strip().lower() == "true"
    posts = _community_feed(limit=limit, include_remote=include_remote)
    return jsonify({
        "status": "success",
        "source": "website",
        "include_remote": include_remote,
        "posts": [_serialize_post(post) for post in posts],
    })


@community_bp.route("/api/community/posts", methods=["POST"])
def api_create_community_post():
    if not current_user.is_authenticated:
        return jsonify({"status": "error", "message": "authentication required"}), 401

    payload = request.get_json(silent=True) or request.form
    title = (payload.get("title") or "").strip()
    content = (payload.get("content") or payload.get("text") or "").strip()
    community_id = payload.get("community_id")
    new_community_name = (payload.get("new_community_name") or payload.get("community") or "").strip()

    if not title or not content:
        return jsonify({"status": "error", "message": "title and content are required"}), 400

    try:
        post = _create_local_post(
            title=title,
            content=content,
            community_id=community_id,
            new_community_name=new_community_name,
        )
    except Exception as exc:
        db.session.rollback()
        current_app.logger.warning("API community post create failed: %s", exc.__class__.__name__)
        return jsonify({"status": "error", "message": "post could not be created"}), 500

    return jsonify({"status": "success", "post": _serialize_post(_decorate_local_post(post))}), 201


@community_bp.route("/api/community/posts/<int:post_id>")
def api_community_post_detail(post_id):
    post = (
        Post.query
        .options(
            selectinload(Post.author),
            selectinload(Post.car_community),
            selectinload(Post.votes),
            selectinload(Post.comments).selectinload(Comment.user),
        )
        .get_or_404(post_id)
    )
    return jsonify({"status": "success", "post": _serialize_post(_decorate_local_post(post))})


@community_bp.route("/api/community/posts/<int:post_id>/replies", methods=["POST"])
def api_create_community_reply(post_id):
    if not current_user.is_authenticated:
        return jsonify({"status": "error", "message": "authentication required"}), 401

    payload = request.get_json(silent=True) or request.form
    content = (payload.get("content") or payload.get("text") or "").strip()
    parent_id = payload.get("parent_id")

    if not content:
        return jsonify({"status": "error", "message": "content is required"}), 400
    if not Post.query.get(post_id):
        return jsonify({"status": "error", "message": "post not found"}), 404

    try:
        comment = _create_local_comment(post_id, content, parent_id=parent_id)
    except Exception as exc:
        db.session.rollback()
        current_app.logger.warning("API community reply create failed: %s", exc.__class__.__name__)
        return jsonify({"status": "error", "message": "reply could not be created"}), 500

    return jsonify({"status": "success", "reply": _serialize_comment(_decorate_local_comment(comment))}), 201


@community_bp.route("/api/community/remote/<int:remote_post_id>")
def api_remote_community_post_detail(remote_post_id):
    post = _load_remote_post(remote_post_id)
    if not post:
        return jsonify({"status": "error", "message": "post not found"}), 404
    return jsonify({"status": "success", "post": _serialize_post(post)})


@community_bp.route("/community")
def community():
    query = (request.args.get("q") or "").strip().lower()
    sort = (request.args.get("sort") or "new").strip()
    active_car_community = (request.args.get("car_community") or "").strip()
    database_ready = current_app.config.get("DATABASE_READY", False)

    try:
        if database_ready:
            local_query = (
                Post.query
                .options(
                    selectinload(Post.author),
                    selectinload(Post.car_community),
                    selectinload(Post.votes),
                    selectinload(Post.comments).selectinload(Comment.user),
                )
                .order_by(Post.id.desc())
            )
            if active_car_community:
                local_query = local_query.join(CarCommunity).filter(CarCommunity.slug == active_car_community)
            if query:
                local_query = local_query.filter(
                    or_(
                        Post.title.ilike(f"%{query}%"),
                        Post.content.ilike(f"%{query}%"),
                    )
                )
            local_posts = [_decorate_local_post(post) for post in local_query.limit(80).all()]
        else:
            local_posts = []
    except Exception as exc:
        db.session.rollback()
        current_app.logger.warning("community_section_error=local_posts error=%s detail=%s", exc.__class__.__name__, str(exc)[:300])
        local_posts = []

    try:
        remote_posts = _load_remote_posts()
    except Exception as exc:
        current_app.logger.warning("community_section_error=remote_posts error=%s detail=%s", exc.__class__.__name__, str(exc)[:300])
        remote_posts = []

    combined_posts = local_posts + remote_posts

    try:
        if database_ready:
            car_communities = (
                CarCommunity.query
                .order_by(CarCommunity.name.asc())
                .all()
            )
        else:
            car_communities = []
    except Exception as exc:
        db.session.rollback()
        current_app.logger.warning("community_section_error=car_communities error=%s detail=%s", exc.__class__.__name__, str(exc)[:300])
        car_communities = []

    if active_car_community:
        combined_posts = [
            post for post in combined_posts
            if getattr(post, "community_slug", None) == active_car_community
        ]

    if query:
        filtered = []
        for post in combined_posts:
            haystack = f"{post.title} {post.content} {post.author_display_name}".lower()
            haystack = f"{haystack} {getattr(post, 'community_name', '')}".lower()
            if query in haystack:
                filtered.append(post)
                continue
            if any(query in (comment.content or "").lower() for comment in post.comments):
                filtered.append(post)
        combined_posts = filtered

    if sort == "popular":
        posts = sorted(
            combined_posts,
            key=lambda post: (post.vote_count, post.reply_count, str(post.id)),
            reverse=True,
        )
    else:
        posts = sorted(
            combined_posts,
            key=lambda post: str(post.created_at or ""),
            reverse=True,
        )

    try:
        if database_ready:
            top_contributors = (
                User.query
                .filter(User.posts_count > 0)
                .order_by(User.reputation.desc(), User.helpful_answers.desc(), User.posts_count.desc(), User.id.asc())
                .limit(5)
                .all()
            )
        else:
            top_contributors = []
    except Exception as exc:
        db.session.rollback()
        current_app.logger.warning("community_section_error=top_contributors error=%s detail=%s", exc.__class__.__name__, str(exc)[:300])
        top_contributors = []

    topic_counts = {
        "Engine": 0,
        "Mileage": 0,
        "Service": 0,
        "Tyres": 0,
        "Battery": 0,
        "Buying": 0,
    }

    for post in posts:
        haystack = f"{post.title} {post.content}".lower()
        if "engine" in haystack or "start" in haystack:
            topic_counts["Engine"] += 1
        if "mileage" in haystack or "fuel" in haystack:
            topic_counts["Mileage"] += 1
        if "service" in haystack or "maintenance" in haystack:
            topic_counts["Service"] += 1
        if "tyre" in haystack or "tire" in haystack:
            topic_counts["Tyres"] += 1
        if "battery" in haystack:
            topic_counts["Battery"] += 1
        if "buy" in haystack or "purchase" in haystack or "suggest" in haystack:
            topic_counts["Buying"] += 1

    active_topics = [(name, count) for name, count in topic_counts.items() if count > 0]
    active_topics.sort(key=lambda item: item[1], reverse=True)
    active_topics = active_topics[:6]

    total_votes = sum(post.vote_count for post in posts)
    total_comments = sum(post.reply_count for post in posts)
    unanswered_posts = [post for post in posts if post.reply_count == 0][:5]
    most_active_posts = sorted(
        posts,
        key=lambda post: (post.reply_count + post.vote_count, str(post.created_at or "")),
        reverse=True,
    )[:4]
    quick_topics = [
        ("Engine problem", "engine"),
        ("Mileage drop", "mileage"),
        ("Service advice", "service"),
        ("Battery issue", "battery"),
        ("Buying help", "buying"),
    ]

    return render_template(
        "community.html",
        posts=posts,
        search_query=request.args.get("q") or "",
        current_sort=sort,
        top_contributors=top_contributors,
        active_topics=active_topics,
        unanswered_posts=unanswered_posts,
        most_active_posts=most_active_posts,
        quick_topics=quick_topics,
        car_communities=car_communities,
        active_car_community=active_car_community,
        community_stats={
            "posts": len(posts),
            "comments": total_comments,
            "votes": total_votes,
            "contributors": len(top_contributors),
        },
    )


@community_bp.route("/create-post", methods=["GET", "POST"])
@login_required
def create_post():
    if request.method == "POST":
        title = (request.form.get("title") or "").strip()
        content = (request.form.get("content") or "").strip()
        community_id = request.form.get("community_id")
        new_community_name = (request.form.get("new_community_name") or "").strip()

        if not title or not content:
            flash("Title and content required")
            return redirect("/create-post")

        image = request.files.get("image")
        filename = None
        external_image_url = None

        if image and image.filename != "":
            filename = secure_filename(image.filename)
            upload_path = os.path.join("static/post_images", filename)
            image.save(upload_path)
            external_image_url = url_for("static", filename=f"post_images/{filename}", _external=True)

        post = _create_local_post(
            title=title,
            content=content,
            community_id=community_id,
            new_community_name=new_community_name,
            image_filename=filename,
            external_image_url=external_image_url,
        )
        flash("Post created successfully")
        return redirect("/community")

    car_communities = CarCommunity.query.order_by(CarCommunity.name.asc()).all()
    selected_community = request.args.get("car_community") or ""
    return render_template(
        "create_post.html",
        car_communities=car_communities,
        selected_community=selected_community,
    )


@community_bp.route("/community/cars/create", methods=["POST"])
@login_required
def create_car_community():
    name = (request.form.get("name") or "").strip()
    description = (request.form.get("description") or "").strip()
    if not name:
        flash("Car community name is required.")
        return redirect(url_for("community.community"))

    car_community = _get_or_create_car_community(name, description=description, user=current_user)
    db.session.commit()
    flash(f"{car_community.name} community is ready.")
    return redirect(url_for("community.community", car_community=car_community.slug))


@community_bp.route("/post/<int:post_id>")
def post_detail(post_id):
    post = _decorate_local_post(Post.query.get_or_404(post_id))
    return render_template("post_detail.html", post=post, **_post_social_context(post))


@community_bp.route("/community/remote/<int:remote_post_id>")
def remote_post_detail(remote_post_id):
    post = _load_remote_post(remote_post_id)
    if not post:
        flash("Post not found in shared community feed.")
        return redirect(url_for("community.community"))
    return render_template("post_detail.html", post=post, **_post_social_context(post))


@community_bp.route("/post/<int:post_id>/edit", methods=["GET", "POST"])
@login_required
def edit_post(post_id):
    post = Post.query.get_or_404(post_id)
    if post.user_id != current_user.id and current_user.role != "admin":
        return "Unauthorized"

    if request.method == "POST":
        post.title = request.form["title"]
        post.content = request.form["content"]
        new_community_name = (request.form.get("new_community_name") or "").strip()
        community_id = request.form.get("community_id")
        if new_community_name:
            post.car_community = _get_or_create_car_community(new_community_name, user=current_user)
        elif community_id:
            post.car_community = CarCommunity.query.get(community_id)
        else:
            post.car_community = None
        remote_post_id = _find_remote_post_id_for_website_post(post.id)
        if remote_post_id:
            _safe_remote_call(
                f"/community/posts/{remote_post_id}",
                method="PUT",
            payload={
                "email": current_user.email,
                "text": f"{post.title}\n\n{post.content}",
                "location": current_user.city or "Website",
            },
            )
        db.session.commit()
        return redirect(url_for("community.post_detail", post_id=post.id))

    return render_template(
        "edit_post.html",
        post=post,
        car_communities=CarCommunity.query.order_by(CarCommunity.name.asc()).all(),
    )


@community_bp.route("/post/<int:post_id>/delete", methods=["POST"])
@login_required
def delete_post(post_id):
    post = Post.query.get_or_404(post_id)
    if post.user_id != current_user.id and current_user.role != "admin":
        return "Unauthorized"

    author = post.author
    remote_post_id = _find_remote_post_id_for_website_post(post.id)
    if remote_post_id:
        _safe_remote_call(
            f"/community/posts/{remote_post_id}",
            method="DELETE",
            payload={"email": current_user.email},
        )
    db.session.delete(post)
    db.session.flush()
    refresh_author_stats(author)
    db.session.commit()
    return redirect("/community")


@community_bp.route("/add_comment/<int:post_id>", methods=["POST"])
@login_required
def add_comment(post_id):
    content = (request.form.get("content") or "").strip()
    parent_id = request.form.get("parent_id") or None
    if content:
        _create_local_comment(post_id, content, parent_id=parent_id)
    return redirect(url_for("community.post_detail", post_id=post_id))


@community_bp.route("/community/remote/<int:remote_post_id>/reply", methods=["POST"])
@login_required
def remote_add_comment(remote_post_id):
    content = (request.form.get("content") or "").strip()
    if not content:
        flash("Reply text is required.")
        return redirect(url_for("community.remote_post_detail", remote_post_id=remote_post_id))

    _sync_user_profile(current_user)
    result = _safe_remote_call(
        f"/community/posts/{remote_post_id}/replies",
        method="POST",
        payload={
            "source": "website",
            "email": current_user.email,
            "fullName": current_user.username,
            "mobile": current_user.mobile or "",
            "location": current_user.city or "Website",
            "text": content,
        },
    )
    if result is None:
        flash("Reply could not be synced right now. Please try again.")
    else:
        flash("Reply added to shared community.")
    return redirect(url_for("community.remote_post_detail", remote_post_id=remote_post_id))


@community_bp.route("/upvote/<int:post_id>")
@login_required
def upvote(post_id):
    existing_vote = Vote.query.filter_by(user_id=current_user.id, post_id=post_id).first()
    post = Post.query.get(post_id)

    if existing_vote:
        db.session.delete(existing_vote)
        post.author.reputation = max(0, post.author.reputation - 3)
    else:
        db.session.add(Vote(user_id=current_user.id, post_id=post_id))
        post.author.reputation += 3

    db.session.commit()
    return redirect("/community")


@community_bp.route("/comment/<int:comment_id>/edit", methods=["GET", "POST"])
@login_required
def edit_comment(comment_id):
    comment = Comment.query.get_or_404(comment_id)
    if comment.user_id != current_user.id and current_user.role != "admin":
        return "Unauthorized"

    if request.method == "POST":
        comment.content = request.form["content"]
        db.session.commit()
        return redirect(url_for("community.post_detail", post_id=comment.post_id))

    return render_template("edit_comment.html", comment=comment)


@community_bp.route("/comment/<int:comment_id>/delete", methods=["POST"])
@login_required
def delete_comment(comment_id):
    comment = Comment.query.get_or_404(comment_id)
    if comment.user_id != current_user.id and current_user.role != "admin":
        return "Unauthorized"

    post_id = comment.post_id
    db.session.delete(comment)
    db.session.commit()
    return redirect(url_for("community.post_detail", post_id=post_id))
