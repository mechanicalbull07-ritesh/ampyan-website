import uuid
from flask import g
from flask.testing import FlaskClient
import pytest

@pytest.fixture
def admin_client(monkeypatch):
 import app as website
 from models.models import User,db
 with website.app.app_context():
  db.create_all();u=User(username='manual-admin-'+uuid.uuid4().hex,email=uuid.uuid4().hex+'@example.invalid',password='synthetic',role='admin',is_banned=False);db.session.add(u);db.session.commit()
  monkeypatch.setattr(website,'ADMIN_EMAIL_SET',website.ADMIN_EMAIL_SET | {u.email.lower()})
  client=website.app.test_client()
  with client.session_transaction() as saved:saved['_user_id']=str(u.id);saved['_fresh']=True
  g.pop('_login_user',None)
  yield client

def test_admin_ui_approval_forwards_only_attestation_and_preserves_csrf(admin_client,monkeypatch):
 import app as website
 import services.account_deletion_client as boundary
 rid='a'*32;calls=[]
 def call(path,method='GET',payload=None):
  calls.append((path,method,payload))
  if path.endswith('/review'):return {'request_id':rid,'status':'PENDING','registered_email':'owner@example.invalid'}
  if path.endswith('/tasks'):return {'tasks':[]}
  return {'status':'VERIFIED'}
 monkeypatch.setattr(boundary,'admin_call',call)
 page=admin_client.get('/admin/account-deletion/'+rid)
 assert page.status_code==200 and b'Mark VERIFIED' in page.data and b'owner@example.invalid' in page.data
 assert b'Send/retry verification email' not in page.data
 data={'action':'verify-manual','sender_email':'owner@example.invalid','email_received':'yes','evidence_hash':'b'*64,'user_id':'99'}
 assert FlaskClient(website.app).post('/admin/account-deletion/'+rid,data=data).status_code==400
 assert admin_client.post('/admin/account-deletion/'+rid,data=data).status_code==200
 submitted=next(c for c in calls if c[1]=='POST')
 assert submitted==(f'/api/admin/account-deletion/{rid}/verify-manual','POST',{'sender_email':'owner@example.invalid','email_received':True,'evidence_hash':'b'*64})

@pytest.mark.parametrize('status,expected',[('COMPLETED',200),('PROCESSING',503)])
def test_completion_confirmation_only_for_backend_completed(admin_client,monkeypatch,status,expected):
 import services.account_deletion_client as boundary
 def call(path,method='GET',payload=None):
  return {'status':status} if method=='POST' else {'requests':[]}
 monkeypatch.setattr(boundary,'admin_call',call)
 response=admin_client.post('/admin/account-deletion',data={'request_id':'a'*32,'action':'complete'})
 assert response.status_code==expected
 if status=='COMPLETED':assert b'Manually reply to the original support-email thread' in response.data
 else:assert b'Do not reply confirming completion' in response.data

@pytest.mark.parametrize('action',['send-verification','retry-completion-mail'])
def test_automated_admin_actions_not_exposed(admin_client,monkeypatch,action):
 import services.account_deletion_client as boundary
 def no_call(*args):raise AssertionError('Automatic mail action reached backend')
 monkeypatch.setattr(boundary,'admin_call',no_call)
 assert admin_client.post('/admin/account-deletion',data={'request_id':'a'*32,'action':action}).status_code==400
