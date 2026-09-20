"""Version 1 of the shared AMPYAN analytics event contract."""

SCHEMA_VERSION = 1
CANONICAL_EVENTS = frozenset({
    "sign_up", "login", "diagnosis_started", "diagnosis_completed",
    "vehicle_added", "vehicle_updated", "car_health_viewed",
    "fuel_calculator_used", "emi_calculator_used", "depreciation_calculator_used",
    "repair_estimate_used", "garage_viewed", "garage_contact_clicked",
    "blog_viewed", "blog_created", "comment_added", "marketplace_viewed",
    "video_clicked", "share_clicked",
})
LEGACY_EVENTS = frozenset({
    "api_error", "app_open", "click", "community_opened", "garage_added",
    "login_failure", "login_success", "news_opened", "page_view",
    "screen_view", "scroll_depth", "odometer_updated", "service_record_added",
    "dashcam_loop_delete_oldest",
})
ALLOWED_EVENT_TYPES = CANONICAL_EVENTS | LEGACY_EVENTS

EVENT_PARAMETERS = {
    "sign_up": {"method"}, "login": {"method"},
    "diagnosis_started": {"feature"}, "diagnosis_completed": {"feature"},
    "vehicle_added": {"feature"}, "vehicle_updated": {"feature"},
    "car_health_viewed": {"feature"}, "fuel_calculator_used": {"feature"},
    "emi_calculator_used": {"feature"}, "depreciation_calculator_used": {"feature"},
    "repair_estimate_used": {"feature"}, "garage_viewed": {"feature"},
    "garage_contact_clicked": {"feature"}, "blog_viewed": {"content_type"},
    "blog_created": {"content_type"}, "comment_added": {"content_type"},
    "marketplace_viewed": {"feature"}, "video_clicked": {"content_type"},
    "share_clicked": {"content_type"},
}
FEATURE_VALUES = frozenset({
    "diagnosis", "vehicle", "car_health", "fuel_calculator", "emi_calculator",
    "depreciation_calculator", "repair_estimate", "garage", "marketplace",
})
CONTENT_VALUES = frozenset({"blog", "community", "news", "video", "vehicle"})
METHOD_VALUES = frozenset({"email", "google", "password"})
SCREEN_VALUES = frozenset({"home", "ai", "community", "garage", "tools", "history"})
CANONICAL_FEATURE = {
    "diagnosis_started": "diagnosis", "diagnosis_completed": "diagnosis",
    "vehicle_added": "vehicle", "vehicle_updated": "vehicle",
    "car_health_viewed": "car_health", "fuel_calculator_used": "fuel_calculator",
    "emi_calculator_used": "emi_calculator",
    "depreciation_calculator_used": "depreciation_calculator",
    "repair_estimate_used": "repair_estimate", "garage_viewed": "garage",
    "garage_contact_clicked": "garage", "marketplace_viewed": "marketplace",
}
CANONICAL_CONTENT = {
    "blog_viewed": {"blog"}, "blog_created": {"blog"},
    "comment_added": {"blog", "community"}, "video_clicked": {"video"},
    "share_clicked": {"blog", "news", "video", "vehicle"},
}
