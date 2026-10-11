import uuid
import pytest
from flask.testing import FlaskClient
from flask import session
from flask_wtf.csrf import generate_csrf
from models.models import db,User,News
import app as website
from services import capability_security as caps,news_admission as gate

@pytest.fixture
def roles():
 app=website.app
 with app.app_context():
  db.create_all()
  with db.engine.begin() as c:
   caps.migrate(c)
   for t in gate.TABLES:t.create(c,checkfirst=True)
  users=[]
  for kind in ['publisher','operator','platform','manager']:
   u=User(id=1000000+int(uuid.uuid4().hex[:7],16),username=uuid.uuid4().hex,email=uuid.uuid4().hex+'@example.invalid',password='synthetic',role='user');db.session.add(u);db.session.flush();users.append(u)
  db.session.commit()
  with db.engine.begin() as c:
   for u,permissions in zip(users,[['news.create','news.edit'],['maintenance.news_gate'],['platform.admin'],['news.create','news.edit','news.delete','news.manage_publishers']]):caps.bootstrap_verified(c,u,permissions,caps.now(c)+3600,'synthetic-role-verification',True,True)
  ids=[u.id for u in users]
 return app,ids

def logged(app,uid):
 c=FlaskClient(app,app.response_class)
 with c.session_transaction() as s:s['_user_id']=str(uid);s['_fresh']=True
 return c

def test_restricted_roles_cannot_view_platform_dashboard(roles):
 app,ids=roles
 for uid in [ids[0],ids[1],ids[3]]:assert logged(app,uid).get('/admin').status_code==403

def test_publisher_not_legacy_admin_can_open_create(roles):
 app,ids=roles;assert logged(app,ids[0]).get('/admin/news/create').status_code==200
 assert logged(app,ids[1]).get('/admin/news/create').status_code==403

def test_old_cookie_revoked_grant_denied(roles):
 app,ids=roles;c=logged(app,ids[0]);assert c.get('/admin/news/create').status_code==200
 with app.app_context():
  with db.engine.begin() as conn:conn.execute(caps.GRANT.update().where(caps.GRANT.c.user_id==ids[0]).values(active=False))
 assert c.get('/admin/news/create').status_code==403

def test_publisher_does_not_get_delete_controls(roles):
 app,ids=roles
 with app.app_context():n=News(title='Synthetic',content='Synthetic',category='auto-news');db.session.add(n);db.session.commit();id=n.id
 assert logged(app,ids[0]).get('/admin/news/delete/'+str(id)).status_code in (403,405)
 page=logged(app,ids[0]).get('/news').text
 assert '/admin/news/create' in page
 assert '/admin/news/delete/'+str(id) not in page
