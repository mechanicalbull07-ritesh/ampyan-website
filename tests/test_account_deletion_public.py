import uuid
import pytest
from flask.testing import FlaskClient

def test_public_deletion_safe_proxy_and_csrf(monkeypatch):
 import app as website
 import services.account_deletion_client as boundary
 from models.models import db,HelpReport
 with website.app.app_context():
  db.create_all();client=website.app.test_client();calls=[]
  monkeypatch.setattr(boundary,'public_call',lambda path,payload:(calls.append((path,payload)) or {'message':'generic'}))
  page=client.get('/account-deletion');assert page.status_code==200
  assert page.headers['Cache-Control']=='no-store' and page.headers['Referrer-Policy']=='no-referrer'
  for label in [b'AMPYAN',b'without installing',b'Privacy Policy',b'Logging out',b'backup integrity']:assert label in page.data
  assert b'type="password"' not in page.data
  before=HelpReport.query.count()
  data={'email':'fixture@example.invalid','confirm':'yes'}
  assert FlaskClient(website.app).post('/account-deletion',data=data).status_code==400
  assert client.post('/account-deletion',data={**data,'confirm':''}).status_code==400
  assert client.post('/account-deletion',data={**data,'email':'bad'}).status_code==400
  for _ in range(2):assert client.post('/account-deletion',data=data,follow_redirects=True).status_code==200
  assert all(path=='/api/account-deletion/public' and payload=={'email':'fixture@example.invalid','confirm':True} for path,payload in calls)
  assert HelpReport.query.count()==before
  assert client.post('/account-deletion',data={'action':'verify','request_id':'a'*32,'code':'synthetic-only'},follow_redirects=True).status_code==200
  assert calls[-1][0]=='/api/account-deletion/verify'

def test_admin_requires_login_and_role(monkeypatch):
 import app as website
 from models.models import User,db
 with website.app.app_context():
  db.create_all();client=website.app.test_client();assert client.get('/admin/account-deletion').status_code==302
  user=User(username='deletion-'+uuid.uuid4().hex,email=uuid.uuid4().hex+'@example.invalid',password='synthetic',role='user',is_banned=False);db.session.add(user);db.session.commit()
  with client.session_transaction() as saved:saved['_user_id']=str(user.id);saved['_fresh']=True
  from flask import g
  g.pop('_login_user', None)
  assert client.get('/admin/account-deletion').status_code==403

def test_service_failure_not_claimed_success(monkeypatch):
 import app as website
 import services.account_deletion_client as boundary
 from services.canonical_garage_client import GarageError
 def fail(*args):raise GarageError(503)
 monkeypatch.setattr(boundary,'public_call',fail)
 response=website.app.test_client().post('/account-deletion',data={'email':'fixture@example.invalid','confirm':'yes'})
 assert response.status_code==503 and b'No deletion completion is confirmed' in response.data


def test_fenced_website_identity_caches_cleared():
 import app as website
 from models.models import User,db
 from flask import g
 with website.app.app_context():
  db.create_all();u=User(username='deleted-'+uuid.uuid4().hex,email=uuid.uuid4().hex+'@example.invalid',password='synthetic',role='user',is_banned=True);db.session.add(u);db.session.commit()
  c=website.app.test_client()
  with c.session_transaction() as saved:
   saved['_user_id']=str(u.id);saved['_fresh']=True;saved['garage_credentials']={'website_user':str(u.id),'token':'synthetic'};saved['google_profile_picture']={'website_user':str(u.id),'url':'https://example.invalid/picture'};saved['garage_selected']=201
  g.pop('_login_user',None)
  assert c.get('/api/session').json['authenticated'] is False
  with c.session_transaction() as saved:
   assert not any(key in saved for key in ('_user_id','garage_credentials','garage_selected','google_profile_picture'))
