import hashlib,uuid,os
import pytest
import app as website
from models.models import db,User,News
from services import news_admission as gate
from services import capability_security as caps

@pytest.fixture
def scoped(monkeypatch):
 app=website.app
 with app.app_context():
  db.create_all()
  with db.engine.begin() as c:
   caps.migrate(c)
   for t in gate.TABLES:t.create(c,checkfirst=True)
   c.execute(gate.LEASE.delete());c.execute(gate.CREDENTIAL.delete());c.execute(gate.GATE.delete());c.execute(gate.GATE.insert().values(id=1,state='OPEN',generation=uuid.uuid4().hex))
  users=[]
  for role in ['admin','user']:
   u=User(username=uuid.uuid4().hex,email=uuid.uuid4().hex+'@example.invalid',password='synthetic',role=role);db.session.add(u);db.session.flush();users.append(u)
  db.session.commit();ids=[u.id for u in users]
  from routes import auth_routes
  allowed=set(auth_routes.ADMIN_EMAIL_SET)|{users[0].email}
  monkeypatch.setattr(website,'ADMIN_EMAIL_SET',allowed);monkeypatch.setattr(auth_routes,'ADMIN_EMAIL_SET',allowed)
  with db.engine.begin() as c:c.execute(gate.PERMISSION.insert().values(user_id=users[0].id,credential_binding=hashlib.sha256(users[0].password.encode()).hexdigest(),active=True))
  with db.engine.begin() as c:caps.bootstrap_verified(c,users[0],list(caps.SCOPES),caps.now(c)+3600,'synthetic-website-fixture',True,True)
  secret='synthetic-website-news-token-32chars';monkeypatch.setenv('NEWS_WEBSITE_SERVICE_TOKEN',secret)
  with db.engine.begin() as c:c.execute(gate.CREDENTIAL.insert().values(id='website-news',secret_sha256=hashlib.sha256(secret.encode()).hexdigest(),active=True,expires_at=gate.now(c)+3600))
 yield app,ids

def logged(app,uid=None):
 c=app.test_client()
 if uid:
  with c.session_transaction() as s:s['_user_id']=str(uid);s['_fresh']=True
 return c

def test_unauthorized_bulk_and_role_headers(scoped):
 app,ids=scoped
 assert logged(app).post('/admin/sync-app-content',headers={'X-AMPYAN-ROLE':'admin'}).status_code==401
 assert logged(app,ids[1]).post('/admin/sync-app-content').status_code==403

def test_pause_blocks_before_local_commit_and_preserves_essentials(scoped):
 app,ids=scoped
 with app.app_context():before=News.query.count();g=gate.pause(db.engine,ids[0]);assert g['state']=='PAUSED'
 c=logged(app,ids[0])
 for path in ['/admin/news/create','/admin/news/edit/1','/admin/news/delete/1','/admin/sync-app-content']:
  assert c.post(path,data={'title':'Blocked','content':'Blocked'}).status_code==503
 with app.app_context():assert News.query.count()==before;assert gate.status(db.engine)['active_admissions']==0
 assert c.get('/health').status_code==200
 assert c.get('/login').status_code==200

def test_expired_service_prevents_local_news_commit(scoped):
 app,ids=scoped
 with app.app_context():
  before=News.query.count()
  with db.engine.begin() as c:c.execute(gate.CREDENTIAL.update().values(active=False))
 assert logged(app,ids[0]).post('/admin/news/create',data={'title':'Blocked','content':'Blocked'}).status_code==503
 with app.app_context():assert News.query.count()==before

def test_public_news_not_gated(scoped):
 app,ids=scoped
 with app.app_context():gate.pause(db.engine,ids[0])
 assert logged(app).get('/news').status_code==200


def test_news_credentials_never_follow_redirects_or_plaintext_remote(scoped,monkeypatch):
 from services import app_api_sync
 from unittest.mock import patch
 from types import SimpleNamespace
 monkeypatch.setattr(app_api_sync,'APP_API_BASE_URL','http://example.invalid')
 with patch.object(app_api_sync.requests,'request') as send:
  assert app_api_sync._request('PUT','/news/articles/1',headers={'X-AMPYAN-NEWS-SERVICE-TOKEN':'synthetic'}) is False
  send.assert_not_called()
 monkeypatch.setattr(app_api_sync,'APP_API_BASE_URL','https://example.invalid')
 with patch.object(app_api_sync.requests,'request',return_value=SimpleNamespace(status_code=302,raise_for_status=lambda:None)) as send:
  assert app_api_sync._request('PUT','/news/articles/1',headers={'X-AMPYAN-NEWS-SERVICE-TOKEN':'synthetic'}) is False
  assert send.call_args.kwargs['allow_redirects'] is False


def test_production_news_fails_closed_with_short_session_key(scoped,monkeypatch):
 app,ids=scoped;monkeypatch.setenv('ENV','production');monkeypatch.setenv('SECRET_KEY','short')
 assert logged(app,ids[0]).post('/admin/news/create',data={'title':'Blocked','content':'Blocked'}).status_code==503
 assert logged(app).get('/health').status_code==200
