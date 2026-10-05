"""Display-only Google avatar, bound to the authenticated Website user."""
from urllib.parse import urlsplit
from flask import current_app, session

SESSION_KEY = 'google_profile_picture'

def remember_google_picture(user_id, user_info, *, userinfo_fallback_attempted=False):
    session.pop(SESSION_KEY, None)
    picture = user_info.get('picture')
    accepted = False
    stored = False
    try:
        if not isinstance(picture, str) or len(picture) > 2048:
            return
        try:
            parsed = urlsplit(picture)
            if parsed.scheme != 'https' or not parsed.hostname or parsed.username or parsed.password:
                return
        except ValueError:
            return
        accepted = True
        session[SESSION_KEY] = {'website_user': str(user_id), 'url': picture}
        stored = True
    finally:
        # Temporary diagnostics: fixed labels and booleans only; never log inputs.
        current_app.logger.info(
            'avatar_diagnostic stage=google_callback picture_claim_present=%s '
            'picture_value_nonempty=%s picture_url_accepted=%s avatar_helper_called=%s '
            'avatar_stored=%s google_userinfo_fallback_attempted=%s',
            'picture' in user_info, bool(isinstance(picture, str) and picture),
            accepted, True, stored, bool(userinfo_fallback_attempted),
        )

def clear_google_picture():
    session.pop(SESSION_KEY, None)

def current_user_picture(user, resolve_uploaded):
    if not user.is_authenticated:
        return None
    if user.profile_photo:
        return resolve_uploaded(user.profile_photo)
    saved = session.get(SESSION_KEY) or {}
    if saved.get('website_user') == str(user.id):
        return saved.get('url')
    return None


def log_authenticated_avatar_state(user):
    """Observe the existing display selection; do not mutate session or identity."""
    if not user.is_authenticated:
        return
    saved = session.get(SESSION_KEY) or {}
    user_id = getattr(user, 'id', None)
    binding_valid = bool(saved and user_id is not None and saved.get('website_user') == str(user_id))
    uploaded_present = bool(getattr(user, 'profile_photo', None))
    google_available = bool(binding_valid and saved.get('url'))
    source = 'uploaded' if uploaded_present else ('google' if google_available else 'fallback')
    current_app.logger.info(
        'avatar_diagnostic stage=authenticated_request avatar_session_present=%s '
        'avatar_user_binding_valid=%s uploaded_profile_photo_present=%s '
        'google_avatar_available=%s navbar_source=%s',
        SESSION_KEY in session, binding_valid, uploaded_present, google_available, source,
    )
