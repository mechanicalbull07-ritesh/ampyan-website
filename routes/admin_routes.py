from datetime import datetime, time

from flask import Blueprint, render_template, redirect, flash
from flask_login import login_required, current_user
from models.models import db, User, Post, Comment, News, WebsiteVisit, MechanicProfile, MechanicReview
from services.garage_network_service import refresh_mechanic_reputation

admin_bp = Blueprint("admin", __name__)


# ================= ADMIN DASHBOARD =================

@admin_bp.route("/admin")
@login_required
def admin_dashboard():
    if current_user.role != "admin":
        return "Access Denied", 403

    users = User.query.order_by(User.id.desc()).all()
    posts = Post.query.order_by(Post.id.desc()).all()
    comments = Comment.query.order_by(Comment.id.desc()).all()
    news = News.query.order_by(News.id.desc()).all()
    mechanics = MechanicProfile.query.order_by(
        MechanicProfile.is_verified.asc(),
        MechanicProfile.is_featured.desc(),
        MechanicProfile.id.desc()
    ).all()
    reviews = MechanicReview.query.order_by(MechanicReview.id.desc()).limit(10).all()

    total_ai_usage = db.session.query(db.func.sum(User.ai_uses_today)).scalar() or 0
    today_start = datetime.combine(datetime.utcnow().date(), time.min)
    tracked_visits = WebsiteVisit.query.filter_by(is_page_view=True)
    visit_count = tracked_visits.count()
    today_page_views = tracked_visits.filter(WebsiteVisit.visit_time >= today_start).count()
    total_unique_visitors = db.session.query(db.func.count(db.func.distinct(WebsiteVisit.visitor_id))).filter(
        WebsiteVisit.is_page_view.is_(True),
        WebsiteVisit.visitor_id.isnot(None)
    ).scalar() or 0
    today_unique_visitors = db.session.query(db.func.count(db.func.distinct(WebsiteVisit.visitor_id))).filter(
        WebsiteVisit.is_page_view.is_(True),
        WebsiteVisit.visitor_id.isnot(None),
        WebsiteVisit.visit_time >= today_start
    ).scalar() or 0
    logged_in_views = tracked_visits.filter_by(is_authenticated=True).count()
    guest_views = tracked_visits.filter_by(is_authenticated=False).count()
    top_pages = db.session.query(
        WebsiteVisit.path,
        db.func.count(WebsiteVisit.id).label("views")
    ).filter(
        WebsiteVisit.is_page_view.is_(True),
        WebsiteVisit.path.isnot(None)
    ).group_by(WebsiteVisit.path).order_by(db.func.count(WebsiteVisit.id).desc()).limit(8).all()
    device_breakdown = db.session.query(
        WebsiteVisit.device_type,
        db.func.count(WebsiteVisit.id).label("views")
    ).filter(
        WebsiteVisit.is_page_view.is_(True),
        WebsiteVisit.device_type.isnot(None)
    ).group_by(WebsiteVisit.device_type).order_by(db.func.count(WebsiteVisit.id).desc()).all()
    total_users = User.query.count()
    banned_users_count = User.query.filter_by(is_banned=True).count()
    admin_users_count = User.query.filter_by(role="admin").count()
    pending_garages_count = MechanicProfile.query.filter_by(is_verified=False).count()
    approved_garages_count = MechanicProfile.query.filter_by(is_verified=True).count()
    featured_garages_count = MechanicProfile.query.filter_by(is_featured=True).count()

    for mechanic in mechanics:
        refresh_mechanic_reputation(mechanic)

    pending_mechanics = [mechanic for mechanic in mechanics if not mechanic.is_verified]
    approved_mechanics = [mechanic for mechanic in mechanics if mechanic.is_verified][:8]
    recent_users = users[:10]
    recent_posts = posts[:8]
    banned_users = [user for user in users if user.is_banned][:8]

    return render_template(
        "admin.html",
        users=users,
        posts=posts,
        comments=comments,
        news=news,
        mechanics=mechanics,
        reviews=reviews,
        total_users=total_users,
        total_ai_usage=total_ai_usage,
        visit_count=visit_count,
        today_page_views=today_page_views,
        total_unique_visitors=total_unique_visitors,
        today_unique_visitors=today_unique_visitors,
        logged_in_views=logged_in_views,
        guest_views=guest_views,
        top_pages=top_pages,
        device_breakdown=device_breakdown,
        banned_users_count=banned_users_count,
        admin_users_count=admin_users_count,
        pending_garages_count=pending_garages_count,
        approved_garages_count=approved_garages_count,
        featured_garages_count=featured_garages_count,
        pending_mechanics=pending_mechanics,
        approved_mechanics=approved_mechanics,
        recent_users=recent_users,
        recent_posts=recent_posts,
        banned_users=banned_users
    )


# ================= DELETE USER =================

@admin_bp.route("/admin/delete-user/<int:user_id>")
@login_required
def delete_user(user_id):

    if current_user.role != "admin":
        return "Access Denied"

    user = User.query.get_or_404(user_id)

    # admin खुद को delete नहीं कर सकता
    if user.id == current_user.id:
        flash("You cannot delete yourself")
        return redirect("/admin")

    # पहले user के posts delete
    Post.query.filter_by(user_id=user.id).delete()

    # user के comments delete
    Comment.query.filter_by(user_id=user.id).delete()

    # अब user delete
    db.session.delete(user)
    db.session.commit()

    flash("User deleted successfully")

    return redirect("/admin")


# ================= BAN USER =================

@admin_bp.route("/admin/ban-user/<int:user_id>")
@login_required
def ban_user(user_id):

    if current_user.role != "admin":
        return "Access Denied"

    user = User.query.get_or_404(user_id)

    user.is_banned = True
    db.session.commit()

    return redirect("/admin")


# ================= UNBAN USER =================

@admin_bp.route("/admin/unban-user/<int:user_id>")
@login_required
def unban_user(user_id):

    if current_user.role != "admin":
        return "Access Denied"

    user = User.query.get_or_404(user_id)

    user.is_banned = False
    db.session.commit()

    return redirect("/admin")


# ================= REMOVE ADMIN =================

@admin_bp.route("/admin/remove-admin/<int:user_id>")
@login_required
def remove_admin(user_id):

    if current_user.role != "admin":
        return "Access Denied"

    user = User.query.get_or_404(user_id)

    user.role = "user"
    db.session.commit()

    return redirect("/admin")


@admin_bp.route("/admin/approve-garage/<int:mechanic_id>")
@login_required
def approve_garage(mechanic_id):

    if current_user.role != "admin":
        return "Access Denied"

    mechanic = MechanicProfile.query.get_or_404(mechanic_id)
    mechanic.is_verified = True
    refresh_mechanic_reputation(mechanic)
    db.session.commit()

    flash("Garage approved successfully.")
    return redirect("/admin")


@admin_bp.route("/admin/reject-garage/<int:mechanic_id>")
@login_required
def reject_garage(mechanic_id):

    if current_user.role != "admin":
        return "Access Denied"

    mechanic = MechanicProfile.query.get_or_404(mechanic_id)
    mechanic.is_verified = False
    mechanic.is_featured = False
    refresh_mechanic_reputation(mechanic)
    db.session.commit()

    flash("Garage moved back to pending state.")
    return redirect("/admin")


@admin_bp.route("/admin/feature-garage/<int:mechanic_id>")
@login_required
def feature_garage(mechanic_id):

    if current_user.role != "admin":
        return "Access Denied"

    mechanic = MechanicProfile.query.get_or_404(mechanic_id)
    mechanic.is_featured = True
    refresh_mechanic_reputation(mechanic)
    db.session.commit()

    flash("Garage featured on the network.")
    return redirect("/admin")


@admin_bp.route("/admin/unfeature-garage/<int:mechanic_id>")
@login_required
def unfeature_garage(mechanic_id):

    if current_user.role != "admin":
        return "Access Denied"

    mechanic = MechanicProfile.query.get_or_404(mechanic_id)
    mechanic.is_featured = False
    refresh_mechanic_reputation(mechanic)
    db.session.commit()

    flash("Garage removed from featured list.")
    return redirect("/admin")
