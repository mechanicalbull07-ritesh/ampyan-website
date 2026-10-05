"""Display-only Google avatar, bound to the authenticated Website user."""
from urllib.parse import urlsplit
from flask import session

SESSION_KEY = 'google_profile_picture'

def remember_google_picture(user_id, user_info):
    session.pop(SESSION_KEY, None)
    picture = user_info.get('picture')
    if not isinstance(picture, str) or len(picture) > 2048:
        return
    try:
        parsed = urlsplit(picture)
        if parsed.scheme != 'https' or not parsed.hostname or parsed.username or parsed.password:
            return
    except ValueError:
        return
    session[SESSION_KEY] = {'website_user': str(user_id), 'url': picture}

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
