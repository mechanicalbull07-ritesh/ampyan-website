"""Read-only, bounded admin aggregates. No tracking, classification or cache writes."""
from datetime import datetime, timedelta
from sqlalchemy import case, func, or_
from models.models import db, User, WebsiteVisit, AnalyticsEvent, TrafficMetric
from services.analytics_contract import CANONICAL_EVENTS, ALLOWED_EVENT_TYPES

SECTIONS = {'overview': 'Overview', 'traffic': 'Traffic & Bots',
            'engagement': 'Engagement', 'acquisition': 'Acquisition', 'conversions': 'Conversions'}
PERIODS = {'today': 'Today', '7d': '7 days', '30d': '30 days'}
MEANINGFUL_EVENTS = CANONICAL_EVENTS - {'sign_up', 'login'}
LABELS = {'sign_up': 'Signup recorded', 'login': 'Login', 'page_view': 'Page viewed',
          'diagnosis_started': 'Diagnosis started', 'diagnosis_completed': 'Diagnosis completed',
          'vehicle_added': 'Vehicle added', 'vehicle_updated': 'Vehicle updated',
          'car_health_viewed': 'Car Health viewed', 'fuel_calculator_used': 'Fuel calculator used',
          'emi_calculator_used': 'EMI calculator used', 'depreciation_calculator_used': 'Depreciation calculator used',
          'repair_estimate_used': 'Repair estimate used', 'garage_viewed': 'Garage viewed',
          'garage_contact_clicked': 'Garage contact clicked', 'blog_viewed': 'Blog viewed',
          'blog_created': 'Blog created', 'comment_added': 'Comment added',
          'marketplace_viewed': 'Marketplace viewed', 'video_clicked': 'Video clicked', 'share_clicked': 'Share clicked'}
# Only controlled source categories leave the database; raw UTM/referrer values never do.
SOURCE_LABELS = {'direct': 'Recorded as direct', 'google': 'Google', 'bing': 'Bing',
                 'facebook': 'Facebook', 'instagram': 'Instagram', 'youtube': 'YouTube',
                 'newsletter': 'Newsletter', 'referral': 'Referral', 'linkedin': 'LinkedIn'}
IST = timedelta(hours=5, minutes=30)


def window(period, now=None):
    now = now or datetime.utcnow()
    if period not in PERIODS:
        raise ValueError('Unsupported analytics period')
    start = ((now + IST).replace(hour=0, minute=0, second=0, microsecond=0) - IST
             if period == 'today' else now - timedelta(days=int(period[:-1])))
    return start, now


def build_summary(period='7d', section='overview', now=None):
    """Six aggregate queries for overview; no ORM hydration or per-account queries."""
    from routes.auth_routes import ADMIN_EMAIL_SET
    if section not in SECTIONS:
        raise ValueError('Unsupported analytics section')
    start, end = window(period, now)
    eligible = (func.coalesce(User.role, 'user') != 'admin',
                func.lower(User.email).notin_(ADMIN_EMAIL_SET), User.is_managed_persona.isnot(True))
    excluded = db.select(User.id).where(or_(func.coalesce(User.role, 'user') == 'admin',
                       func.lower(User.email).in_(ADMIN_EMAIL_SET), User.is_managed_persona.is_(True)))
    human = (AnalyticsEvent.created_at >= start, AnalyticsEvent.created_at < end,
             AnalyticsEvent.is_bot.is_(False), AnalyticsEvent.is_internal.is_(False),
             AnalyticsEvent.is_admin.is_(False),
             or_(AnalyticsEvent.user_id.is_(None), AnalyticsEvent.user_id.notin_(excluded)))
    # Hourly anonymous counts cannot resolve IST midnight's half-hour boundary.
    traffic_start = start.replace(minute=0, second=0, microsecond=0)
    if traffic_start < start:
        traffic_start += timedelta(hours=1)
    traffic_filter = (TrafficMetric.hour_start_utc >= traffic_start, TrafficMetric.hour_start_utc < end)
    traffic = {key: 0 for key in ('human_like', 'likely_bot', 'unknown')}
    for quality, count in db.session.query(TrafficMetric.quality, func.sum(TrafficMetric.count)).filter(*traffic_filter).group_by(TrafficMetric.quality):
        traffic[quality] = int(count or 0)
    registered = db.session.query(func.count(User.id)).filter(*eligible).scalar() or 0
    active = (db.session.query(func.count(func.distinct(AnalyticsEvent.user_id)))
              .join(User, User.id == AnalyticsEvent.user_id)
              .filter(*human, *eligible, AnalyticsEvent.event_type.in_(MEANINGFUL_EVENTS)).scalar() or 0)
    event_key = case((AnalyticsEvent.event_type.in_(ALLOWED_EVENT_TYPES), AnalyticsEvent.event_type), else_='other')
    platform = case((AnalyticsEvent.traffic_type.in_(['web', 'app']), AnalyticsEvent.traffic_type), else_='other')
    counts = {}
    for key, channel, total in db.session.query(event_key, platform, func.count()).filter(*human).group_by(event_key, platform):
        counts.setdefault(key, {'web': 0, 'app': 0, 'other': 0})[channel] = int(total)
    visits = (WebsiteVisit.is_page_view.is_(True), WebsiteVisit.visit_time >= start, WebsiteVisit.visit_time < end,
              WebsiteVisit.is_bot.isnot(True), WebsiteVisit.is_internal.isnot(True), WebsiteVisit.is_admin.isnot(True),
              or_(WebsiteVisit.user_id.is_(None), WebsiteVisit.user_id.notin_(excluded)))
    website_views = db.session.query(func.count(WebsiteVisit.id)).filter(*visits).scalar() or 0
    trend = []
    if section in {'overview', 'traffic'}:
        day = func.date(TrafficMetric.hour_start_utc)
        rows = db.session.query(day, TrafficMetric.quality, func.sum(TrafficMetric.count)).filter(*traffic_filter).group_by(day, TrafficMetric.quality).all()
        grouped = {}
        for date, quality, total in rows:
            grouped.setdefault(str(date), {}).update({quality: int(total)})
        date = traffic_start.date()
        while date <= end.date():
            values = grouped.get(str(date), {})
            trend.append({'day': str(date), **{key: values.get(key, 0) for key in traffic}})
            date += timedelta(days=1)
    sources = []
    if section == 'acquisition':
        raw = func.lower(func.trim(func.coalesce(AnalyticsEvent.source, '')))
        source = case((raw == '', 'missing'), (raw.in_(SOURCE_LABELS), raw), else_='other')
        for key, total in (db.session.query(source, func.count()).filter(*human, AnalyticsEvent.traffic_type == 'web')
                           .group_by(source).order_by(func.count().desc(), source).limit(12)):
            label = SOURCE_LABELS.get(key, 'Not recorded' if key == 'missing' else 'Other recorded labels')
            sources.append({'label': label, 'count': int(total)})
    conversions = [{'key': key, 'label': LABELS[key], **counts.get(key, {'web': 0, 'app': 0, 'other': 0})}
                   for key in ['sign_up', 'vehicle_added', 'diagnosis_completed']]
    engagement = [{'label': LABELS[key], **counts[key]} for key in sorted(counts) if key in MEANINGFUL_EVENTS]
    return {'traffic': traffic, 'traffic_total': sum(traffic.values()), 'registered': registered,
            'active': int(active), 'website_views': website_views, 'event_records': sum(sum(v.values()) for v in counts.values()),
            'counts': counts, 'conversions': conversions, 'engagement': engagement, 'trend': trend,
            'trend_max': max([sum(row[key] for key in traffic) for row in trend] or [1]) or 1,
            'sources': sources, 'start': start, 'end': end, 'traffic_start': traffic_start,
            'traffic_start_ist': (traffic_start + IST).strftime('%d %b, %H:%M IST'),
            'window_start_ist': (start + IST).strftime('%d %b, %H:%M IST'),
            'as_of_ist': (end + IST).strftime('%d %b %Y, %H:%M IST')}
