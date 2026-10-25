"""Proposed minimized Community reads; no bulk export or admin credential fallback."""
import json
import os
import re
from urllib import request, error, parse
from flask import current_app
from services.canonical_garage_client import _token, GarageError


class _NoRedirect(request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


def call(path, *, owner=False, timeout=3):
    target = parse.urlsplit(path)
    if target.scheme or target.netloc or target.fragment:
        return None
    public = target.path in ("/community/posts", "/community/public-reference") or re.fullmatch(r"/community/posts/[0-9]+", target.path)
    if (owner and target.path != "/community/owner/posts") or (not owner and not public):
        return None
    base = (current_app.config.get("AMPYAN_API_BASE_URL") or os.environ.get("AMPYAN_API_BASE_URL")
            or "https://ampyan-api.onrender.com").rstrip("/")
    origin = parse.urlsplit(base)
    if (origin.scheme not in ("http", "https") or not origin.netloc or origin.username
            or origin.password or origin.query or origin.fragment):
        return None
    if origin.scheme != "https" and origin.hostname not in ("localhost", "127.0.0.1", "::1"):
        return None
    headers = {"Accept": "application/json", "X-AMPYAN-Community-Contract": "opaque-v1"}
    if owner:
        try:
            headers["Authorization"] = "Bearer " + _token()
        except GarageError:
            return None
    try:
        req = request.Request(base + path, headers=headers, method="GET")
        with request.build_opener(_NoRedirect()).open(req, timeout=timeout) as response:
            if response.status != 200:
                return None
            data = json.loads(response.read().decode("utf-8"))
        return data if isinstance(data, dict) and data.get("success") is True else None
    except (error.URLError, error.HTTPError, OSError, ValueError):
        return None
