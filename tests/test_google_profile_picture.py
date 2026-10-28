"""Synthetic Google/API responses; no remote authentication or image fetch."""
from types import SimpleNamespace
from uuid import uuid4
import pytest
from flask.testing import FlaskClient
from flask_wtf.csrf import generate_csrf
import app as website
from models.models import db,User
from services import canonical_garage_client as api
from services.google_profile_picture import SESSION_KEY
PICTURE='https://lh3.googleusercontent.com/synthetic-avatar'
@pytest.fixture
def setup(monkeypatch):
    monkeypatch.setattr(website,'database_ready_for_queries',lambda:True)
    monkeypatch.setattr(website,'safe_track_page_visit',lambda:False)
    monkeypatch.setenv('ANALYTICS_ENABLED','false');website.rate_limit_hits.clear()
    email=uuid4().hex+'@example.invalid'
    with website.app.app_context():
        db.create_all();user=User(username='R'+uuid4().hex,email=email,password='synthetic',role='user',is_banned=False,email_verified=True)
        db.session.add(user);db.session.commit();uid=user.id
    claims={'email':email,'picture':PICTURE}
    monkeypatch.setattr(website.google,'authorize_access_token',lambda:{'userinfo':claims,'id_token':'synthetic-id-only'})
    def request(method,url,**kwargs):
        data={'email':email,'access_token':'synthetic-bearer-only'} if url.endswith(('/login','/google-login')) else {'cars':[]}
        return SimpleNamespace(status_code=200,json=lambda:data)
    monkeypatch.setattr(api.requests,'request',request)
    monkeypatch.setitem(website.app.config,'AMPYAN_API_BASE_URL','http://127.0.0.1:1')
    return FlaskClient(website.app,website.app.response_class),claims,uid

def csrf(client):
    with client.session_transaction() as saved:
        with website.app.test_request_context():
            from flask import session
            session.update(saved);value=generate_csrf();saved['csrf_token']=session['csrf_token']
    return {'X-CSRFToken':value}
def login(c):assert c.get('/google/callback').status_code==302

def test_picture_connect_refresh_logout_login(setup):
    c,claims,uid=setup;login(c)
    with c.session_transaction() as s:
        assert s[SESSION_KEY]=={'website_user':str(uid),'url':PICTURE}
        assert s['garage_credentials']['website_user']==s['_user_id']==str(uid)
    for route in ('/garage','/profile','/garage'):
        response=c.get(route);assert response.status_code==200 and PICTURE in response.get_data(as_text=True)
    assert c.post('/garage/connect',data={'password':'synthetic'},headers=csrf(c)).status_code==302
    with c.session_transaction() as s:assert s['_user_id']==str(uid) and s[SESSION_KEY]['url']==PICTURE
    assert c.post('/logout',headers=csrf(c)).status_code==302
    with c.session_transaction() as s:assert SESSION_KEY not in s and 'garage_credentials' not in s
    login(c);assert PICTURE in c.get('/garage').get_data(as_text=True)
    with website.app.app_context():assert db.session.get(User,uid).profile_photo is None

@pytest.mark.parametrize('picture',[None,'','javascript:alert(1)','http://example.invalid/avatar','https://user:password@example.invalid/avatar'])
def test_no_picture_fallback(setup,picture):
    c,claims,uid=setup;claims['picture']=picture
    with c.session_transaction() as s:s[SESSION_KEY]={'website_user':str(uid),'url':PICTURE}
    login(c)
    with c.session_transaction() as s:assert SESSION_KEY not in s
    html=c.get('/profile').get_data(as_text=True)
    assert PICTURE not in html and 'author-avatar-letter profile-avatar' in html

def test_expired_garage_preserves_identity_picture(setup,monkeypatch):
    c,claims,uid=setup;login(c)
    monkeypatch.setattr(api.requests,'request',lambda *a,**k:SimpleNamespace(status_code=401))
    response=c.get('/garage');assert response.status_code==401 and PICTURE in response.get_data(as_text=True)
    with c.session_transaction() as s:
        assert s['_user_id']==str(uid) and s[SESSION_KEY]['url']==PICTURE and 'garage_credentials' not in s
    assert PICTURE in c.get('/profile').get_data(as_text=True)

def test_upload_priority_and_cross_user_isolation(setup):
    c,claims,uid=setup;login(c)
    with website.app.app_context():db.session.get(User,uid).profile_photo='https://example.invalid/uploaded';db.session.commit()
    html=c.get('/profile').get_data(as_text=True);assert 'https://example.invalid/uploaded' in html and PICTURE not in html
    with website.app.app_context():db.session.get(User,uid).profile_photo=None;db.session.commit()
    with c.session_transaction() as s:s[SESSION_KEY]={'website_user':'different-user','url':PICTURE}
    assert PICTURE not in c.get('/profile').get_data(as_text=True)

def test_csrf_and_api_logout(setup):
    c,claims,uid=setup;login(c)
    assert c.post('/garage/connect',data={'password':'synthetic'}).status_code==400
    assert c.post('/api/logout',headers=csrf(c)).status_code==200
    with c.session_transaction() as s:assert SESSION_KEY not in s and '_user_id' not in s
