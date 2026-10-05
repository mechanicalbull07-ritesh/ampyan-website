"""Authenticated backend boundary; no local health calculations or owner headers."""
import os
from urllib.parse import urlsplit, parse_qs
import requests
from flask import current_app, session
from flask_login import current_user

MESSAGES = {
    405: 'Manage vehicle details in the AMPYAN App. This Website dashboard is read-only.',
    401: 'Sign in to Garage again. Your Garage session is missing or expired.',
    403: 'You do not have permission to perform this action.',
    404: 'This vehicle or record is unavailable to your account.',
    409: 'Conflicting records prevented this change. Refresh and review before retrying.',
    400: 'Check the submitted values. Odometer changes may require acknowledgement or a correction.',
    422: 'Check the submitted values and try again.',
    429: 'Too many requests. Please wait before retrying.',
    503: 'Garage is temporarily unavailable. No local health estimate has been substituted.',
}

class GarageError(Exception):
    def __init__(self, status):
        self.status = status if status in MESSAGES else 503
        self.message = MESSAGES[self.status]
        super().__init__(self.message)

def clear_credentials():
    session.pop('garage_credentials', None)
    session.pop('garage_selected', None)

def _token():
    saved = session.get('garage_credentials') or {}
    if not current_user.is_authenticated or saved.get('website_user') != str(current_user.get_id()):
        raise GarageError(401)
    if not saved.get('token'):
        raise GarageError(401)
    return saved['token']

def call(path, method='GET', payload=None, *, public=False):
    target = urlsplit(path)
    if target.path == '/api/garage/cars' or target.path.startswith('/api/garage/cars/'):
        parts = target.path.removeprefix('/api/garage/cars').strip('/').split('/')
        allowed = target.path == '/api/garage/cars' or (
            parts[0].isdigit() and (len(parts) == 1 or
            (len(parts) == 2 and parts[1] in {'health', 'mileage', 'configuration', 'service-records'})))
        if method.upper() not in {'GET', 'HEAD'} or not allowed:
            raise GarageError(405)
        if parts[-1] == 'health' and parse_qs(target.query).get('read_only') != ['1']:
            raise GarageError(405)
    base = current_app.config.get('AMPYAN_API_BASE_URL') or os.environ.get('AMPYAN_API_BASE_URL', '')
    url = urlsplit(base)
    if url.scheme not in ('http', 'https') or not url.netloc or url.username or url.password or url.query or url.fragment:
        raise GarageError(503)
    if url.scheme != 'https' and url.hostname not in ('localhost', '127.0.0.1', '::1'):
        raise GarageError(503)
    headers = {'Accept': 'application/json'}
    if not public:
        headers['Authorization'] = 'Bearer ' + _token()
    try:
        response = requests.request(method, base.rstrip('/') + path, json=payload, headers=headers,
                                    timeout=(3, 15), allow_redirects=False)
        if response.status_code >= 300:
            if response.status_code == 401 and not public:
                clear_credentials()
            raise GarageError(response.status_code)
        result = response.json()
        if not isinstance(result, dict) or result.get('success') is False:
            raise GarageError(503)
        return result
    except (requests.RequestException, ValueError):
        raise GarageError(503) from None

def connect(password=None, id_token=None):
    clear_credentials()
    if not current_user.is_authenticated:
        raise GarageError(401)
    result = call('/google-login' if id_token else '/login', 'POST',
        {'id_token': id_token} if id_token else {'email': current_user.email, 'password': password}, public=True)
    email = result.get('email') or (result.get('user') or {}).get('email')
    if str(email or '').lower() != str(current_user.email).lower() or not result.get('access_token'):
        raise GarageError(401)
    session['garage_credentials'] = {'website_user': str(current_user.get_id()), 'token': result['access_token']}

def sync_profile(name, phone=''):
    return call('/profile/sync', 'POST', {'name': name, 'phone': phone})

def create_garage_account(password):
    """Explicit opt-in registration; never claim an existing account by email."""
    if not current_user.is_authenticated:
        raise GarageError(401)
    clear_credentials()
    call('/register','POST',{'name':current_user.username,'email':current_user.email,
        'phone':current_user.mobile or '', 'password':password},public=True)
    connect(password=password)
