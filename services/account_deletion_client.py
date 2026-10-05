"""Narrow deletion API proxy. Never forward a claimed Website owner ID."""
from flask import current_app
import requests
from .canonical_garage_client import call,GarageError

def public_call(path,payload):
    if path not in ('/api/account-deletion/public','/api/account-deletion/verify'):raise GarageError(403)
    base=current_app.config.get('AMPYAN_API_BASE_URL','').rstrip('/')
    from urllib.parse import urlsplit
    url=urlsplit(base)
    if not url.netloc or url.username or url.password or url.query or url.fragment:raise GarageError(503)
    if url.scheme!='https' and not (url.scheme=='http' and url.hostname in ('localhost','127.0.0.1','::1')):raise GarageError(503)
    try:
        response=requests.post(base+path,json=payload,timeout=15,allow_redirects=False)
        data=response.json()
        if response.status_code not in (200,202) or not isinstance(data,dict):raise GarageError(response.status_code)
        return data
    except (ValueError,requests.RequestException):raise GarageError(503) from None

def admin_call(path,method='GET',payload=None):
    if not path.startswith('/api/admin/account-deletion'):raise GarageError(403)
    return call(path,method,payload)
