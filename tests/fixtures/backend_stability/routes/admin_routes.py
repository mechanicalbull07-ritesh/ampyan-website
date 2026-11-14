"""Exact function from deployed SHA d37fe3a6c39e91cf9ff65c4b3225f86ddd828d0c."""
def _build_admin_analytics_context(section="overview"):
    now = datetime.utcnow()
    today_start = _ist_day_start_utc()
    yesterday_start = _ist_day_start_utc(1)
    last_24h = now - timedelta(hours=24)
    last_7d = now - timedelta(days=7)
    last_30d = now - timedelta(days=30)
    last_365d = now - timedelta(days=365)
    admin_user_ids = [user.id for user in User.query.filter_by(role="admin").all()]

    tracked_visits = WebsiteVisit.query.filter_by(is_page_view=True)
    public_visits_query = tracked_visits.filter(
        WebsiteVisit.is_bot.isnot(True),
        WebsiteVisit.is_internal.isnot(True),
        WebsiteVisit.is_admin.isnot(True),
        (WebsiteVisit.user_id.is_(None)) | (~WebsiteVisit.user_id.in_(admin_user_ids))
    )
    admin_visits_query = tracked_visits.filter(WebsiteVisit.user_id.in_(admin_user_ids)) if admin_user_ids else tracked_visits.filter(False)
    visit_count = public_visits_query.count()
    today_page_views = public_visits_query.filter(WebsiteVisit.visit_time >= today_start).count()
    yesterday_page_views = public_visits_query.filter(
        WebsiteVisit.visit_time >= yesterday_start,
        WebsiteVisit.visit_time < today_start
    ).count()
    total_unique_visitors = db.session.query(db.func.count(db.func.distinct(WebsiteVisit.visitor_id))).filter(
        WebsiteVisit.is_page_view.is_(True),
        WebsiteVisit.visitor_id.isnot(None),
        (WebsiteVisit.user_id.is_(None)) | (~WebsiteVisit.user_id.in_(admin_user_ids))
    ).scalar() or 0
    today_unique_visitors = db.session.query(db.func.count(db.func.distinct(WebsiteVisit.visitor_id))).filter(
        WebsiteVisit.is_page_view.is_(True),
        WebsiteVisit.visitor_id.isnot(None),
        WebsiteVisit.visit_time >= today_start,
        (WebsiteVisit.user_id.is_(None)) | (~WebsiteVisit.user_id.in_(admin_user_ids))
    ).scalar() or 0

    device_breakdown = db.session.query(
        WebsiteVisit.device_type,
        db.func.count(WebsiteVisit.id).label("views")
    ).filter(
        WebsiteVisit.is_page_view.is_(True),
        WebsiteVisit.device_type.isnot(None),
        WebsiteVisit.is_bot.isnot(True),
        WebsiteVisit.is_internal.isnot(True),
        WebsiteVisit.is_admin.isnot(True),
        (WebsiteVisit.user_id.is_(None)) | (~WebsiteVisit.user_id.in_(admin_user_ids))
    ).group_by(WebsiteVisit.device_type).order_by(db.func.count(WebsiteVisit.id).desc()).all()

    recent_visit_rows = public_visits_query.filter(WebsiteVisit.visit_time >= last_365d).order_by(
        WebsiteVisit.visit_time.desc()
    ).limit(5000).all()
    all_public_visit_rows = (
        public_visits_query
        .order_by(WebsiteVisit.visit_time.desc())
        .limit(5000)
        .all()
    )
    total_unique_visitors = len({_visitor_key(visit) for visit in all_public_visit_rows})
    today_unique_visitors = len({
        _visitor_key(visit)
        for visit in all_public_visit_rows
        if visit.visit_time and visit.visit_time >= today_start
    })
    admin_visit_rows = admin_visits_query.filter(WebsiteVisit.visit_time >= last_30d).order_by(
        WebsiteVisit.visit_time.desc()
    ).limit(2000).all()
    visits_24h = [visit for visit in recent_visit_rows if visit.visit_time and visit.visit_time >= last_24h]
    visits_30d = [visit for visit in recent_visit_rows if visit.visit_time and visit.visit_time >= last_30d]
    hourly_traffic = _count_by_hour(visits_24h)
    daily_traffic = _count_by_day(visits_30d)
    monthly_traffic = _count_by_month(recent_visit_rows)

    public_click_query = WebsiteEvent.query.filter_by(event_type="click").filter(
        WebsiteEvent.event_time >= last_30d,
        (WebsiteEvent.user_id.is_(None)) | (~WebsiteEvent.user_id.in_(admin_user_ids))
    )
    admin_click_query = WebsiteEvent.query.filter_by(event_type="click").filter(
        WebsiteEvent.event_time >= last_30d,
        WebsiteEvent.user_id.in_(admin_user_ids)
    ) if admin_user_ids else WebsiteEvent.query.filter(False)
    click_events = public_click_query.order_by(WebsiteEvent.event_time.desc()).limit(5000).all()
    admin_click_events = admin_click_query.order_by(WebsiteEvent.event_time.desc()).limit(2000).all()
    security_events = WebsiteEvent.query.filter_by(event_type="security").filter(
        WebsiteEvent.event_time >= last_30d
    ).order_by(WebsiteEvent.event_time.desc()).limit(2000).all()
    security_events_24h = [
        event for event in security_events
        if event.event_time and event.event_time >= last_24h
    ]

    click_counter = Counter((event.label or event.target_url or "Click") for event in click_events)
    top_clicks = click_counter.most_common(20)
    click_page_counter = Counter((event.path or "Unknown") for event in click_events)
    top_click_pages = click_page_counter.most_common(20)
    referrer_counter = Counter(_referrer_source(visit.referrer) for visit in visits_30d)
    top_referrers = referrer_counter.most_common(20)

    page_metrics = []
    page_visit_groups = defaultdict(list)
    for visit in all_public_visit_rows:
        page_visit_groups[_analytics_path(visit.path)].append(visit)
    page_click_groups = Counter(_analytics_path(event.path) for event in click_events)
    for path, page_visits in sorted(page_visit_groups.items(), key=lambda item: len(item[1]), reverse=True)[:20]:
        page_visits_30d = [visit for visit in page_visits if visit.visit_time and visit.visit_time >= last_30d]
        page_metrics.append({
            "path": path,
            "views": len(page_visits),
            "views_30d": len(page_visits_30d),
            "unique": len({_visitor_key(visit) for visit in page_visits}),
            "logged_in": sum(1 for visit in page_visits if visit.is_authenticated),
            "guest": sum(1 for visit in page_visits if not visit.is_authenticated),
            "clicks": page_click_groups[path],
            "last_visit": _to_ist(max((visit.visit_time for visit in page_visits if visit.visit_time), default=None)),
        })

    suspicious_ip_counter = Counter(event.ip_address or "Unknown" for event in security_events_24h)
    suspicious_ips = suspicious_ip_counter.most_common(10)
    safety_alerts = []
    if security_events_24h:
        safety_alerts.append({
            "severity": "High",
            "title": "Sensitive or abusive requests blocked",
            "detail": f"{len(security_events_24h)} blocked security event(s) in the last 24 hours.",
        })
    if suspicious_ips and suspicious_ips[0][1] >= 5:
        safety_alerts.append({
            "severity": "Medium",
            "title": "Repeated requests from one source",
            "detail": f"{suspicious_ips[0][0]} triggered {suspicious_ips[0][1]} security event(s).",
        })
    if yesterday_page_views and today_page_views > yesterday_page_views * 2:
        safety_alerts.append({
            "severity": "Info",
            "title": "Traffic spike",
            "detail": f"Today has {today_page_views} views vs {yesterday_page_views} yesterday.",
        })
    if not safety_alerts:
        safety_alerts.append({
            "severity": "Good",
            "title": "No major safety alerts",
            "detail": "No unusual security pattern detected from tracked events.",
        })

    cars = Car.query.order_by(Car.created_at.desc()).limit(1000).all()
    today = now.date()
    service_due_cars = [
        car for car in cars
        if car.next_service_km and car.current_km and car.current_km >= car.next_service_km
    ]
    service_soon_cars = [
        car for car in cars
        if car.next_service_km and car.current_km and 0 <= (car.next_service_km - car.current_km) <= 500
    ]
    insurance_expired_cars = [
        car for car in cars
        if car.insurance_expiry and car.insurance_expiry < today
    ]
    pollution_expired_cars = [
        car for car in cars
        if car.pollution_expiry and car.pollution_expiry < today
    ]

    frequency_filter = request.args.get("frequency", "30d")
    frequency_start, frequency_label = _frequency_start(frequency_filter)
    user_rows = []
    for user in User.query.order_by(User.id.desc()).limit(500).all():
        user_visits_query = WebsiteVisit.query.filter(
            WebsiteVisit.user_id == user.id,
            WebsiteVisit.is_page_view.is_(True)
        )
        if frequency_start:
            user_visits_query = user_visits_query.filter(WebsiteVisit.visit_time >= frequency_start)
        user_visits = user_visits_query.order_by(WebsiteVisit.visit_time.desc()).limit(1000).all()
        latest_visit = user_visits[0] if user_visits else (
            WebsiteVisit.query.filter_by(user_id=user.id, is_page_view=True)
            .order_by(WebsiteVisit.visit_time.desc())
            .first()
        )
        user_cars = sorted(user.cars, key=lambda car: car.created_at or datetime.min, reverse=True)
        primary_car = next((car for car in user_cars if car.is_default), user_cars[0] if user_cars else None)
        user_events_query = WebsiteEvent.query.filter(WebsiteEvent.user_id == user.id)
        if frequency_start:
            user_events_query = user_events_query.filter(WebsiteEvent.event_time >= frequency_start)
        user_rows.append({
            "user": user,
            "cars": user_cars,
            "primary_car": primary_car,
            "visit_count": len(user_visits),
            "event_count": user_events_query.count(),
            "last_seen": _format_ist(latest_visit.visit_time) if latest_visit else "No visit tracked",
            "last_path": latest_visit.path if latest_visit else "N/A",
        })
    user_rows.sort(key=lambda row: (row["visit_count"], row["event_count"], row["user"].id), reverse=True)
    active_user_rows = [row for row in user_rows if row["visit_count"] > 0]
    user_frequency_summary = {
        "hour": _period_user_stats(all_public_visit_rows, now - timedelta(hours=1)),
        "day": _period_user_stats(all_public_visit_rows, today_start),
        "week": _period_user_stats(all_public_visit_rows, last_7d),
        "month": _period_user_stats(all_public_visit_rows, last_30d),
    }
    admin_activity = {
        "views_30d": len(admin_visit_rows),
        "views_24h": sum(1 for visit in admin_visit_rows if visit.visit_time and visit.visit_time >= last_24h),
        "clicks_30d": len(admin_click_events),
        "clicks_24h": sum(1 for event in admin_click_events if event.event_time and event.event_time >= last_24h),
        "unique_admins_30d": len({visit.user_id for visit in admin_visit_rows if visit.user_id}),
    }

    return {
        "traffic_quality": traffic_quality_summary(),
        "live_analytics": safe_live_summary(),
        "section": section,
        "frequency_filter": frequency_filter,
        "frequency_label": frequency_label,
        "frequency_options": _frequency_options(),
        "user_rows": user_rows,
        "active_user_rows": active_user_rows,
        "inactive_user_count": max(0, len(user_rows) - len(active_user_rows)),
        "user_frequency_summary": user_frequency_summary,
        "admin_activity": admin_activity,
        "visit_count": visit_count,
        "today_page_views": today_page_views,
        "yesterday_page_views": yesterday_page_views,
        "traffic_delta_today": today_page_views - yesterday_page_views,
        "total_unique_visitors": total_unique_visitors,
        "today_unique_visitors": today_unique_visitors,
        "logged_in_views": public_visits_query.filter_by(is_authenticated=True).count(),
        "guest_views": public_visits_query.filter_by(is_authenticated=False).count(),
        "page_metrics": page_metrics,
        "device_breakdown": device_breakdown,
        "hourly_traffic": hourly_traffic,
        "daily_traffic": daily_traffic,
        "monthly_traffic": monthly_traffic,
        "top_clicks": top_clicks,
        "top_click_pages": top_click_pages,
        "top_referrers": top_referrers,
        "security_events": security_events[:50],
        "security_events_24h": security_events_24h,
        "suspicious_ips": suspicious_ips,
        "safety_alerts": safety_alerts,
        "click_events_count": len(click_events),
        "total_cars": len(cars),
        "car_owner_count": db.session.query(db.func.count(db.func.distinct(Car.owner_id))).scalar() or 0,
        "service_due_cars": service_due_cars,
        "service_soon_cars": service_soon_cars,
        "insurance_expired_cars": insurance_expired_cars,
        "pollution_expired_cars": pollution_expired_cars,
        "recent_cars": cars[:30],
    }
