import uuid
from urllib.parse import urlsplit,parse_qs
from flask.testing import FlaskClient


def test_public_manual_deletion_page_no_login_no_credentials_no_automation(monkeypatch):
 import app as website
 import services.account_deletion_client as boundary
 from models.models import db,HelpReport
 def no_call(*args):raise AssertionError('Public manual page attempted automated API intake')
 monkeypatch.setattr(boundary,'public_call',no_call)
 with website.app.app_context():
  db.create_all();client=website.app.test_client();before=HelpReport.query.count()
  page=client.get('/account-deletion');assert page.status_code==200
  assert page.headers['Cache-Control']=='no-store' and page.headers['Referrer-Policy']=='no-referrer'
  for label in [b'AMPYAN',b'without installing',b'Privacy Policy',b'Logging out',b'Historical backups',b'Email Account Deletion Request',b'hiampyan@gmail.com',b'/account-deletion/request',b'No automatic verification']:
   assert label in page.data
  assert b'type="password"' not in page.data and b'Deletion verification code' not in page.data
  assert client.post('/account-deletion',data={'email':'fixture@example.invalid','confirm':'yes'}).status_code==405
  assert FlaskClient(website.app).post('/account-deletion',data={'email':'fixture@example.invalid'}).status_code==400
  assert HelpReport.query.count()==before


def test_support_mailto_generic_and_invalid_configuration_fails_closed(monkeypatch):
 import app as website
 from services.manual_deletion import context
 with website.app.test_request_context():
  uri=urlsplit(context()['deletion_mailto']);query=parse_qs(uri.query)
  assert uri.scheme=='mailto' and uri.path=='hiampyan@gmail.com'
  assert set(query)=={'subject','body'}
  assert all(term not in query['body'][0] for term in ['password','OTP','bearer','user_id','receipt'])
 monkeypatch.setitem(website.app.config,'AMPYAN_SUPPORT_EMAIL','bad\r\nBcc: other@example.invalid')
 response=website.app.test_client().get('/account-deletion');assert response.status_code==503 and b'mailto:' not in response.data


def test_admin_requires_login_and_role(monkeypatch):
 import app as website
 from models.models import User,db
 with website.app.app_context():
  db.create_all();client=website.app.test_client();assert client.get('/admin/account-deletion').status_code==302
  user=User(username='deletion-'+uuid.uuid4().hex,email=uuid.uuid4().hex+'@example.invalid',password='synthetic',role='user',is_banned=False);db.session.add(user);db.session.commit()
  with client.session_transaction() as saved:saved['_user_id']=str(user.id);saved['_fresh']=True
  from flask import g
  g.pop('_login_user',None)
  assert client.get('/admin/account-deletion').status_code==403


def test_browser_authenticated_request_without_app_and_no_claimed_owner(monkeypatch):
 import app as website
 import services.canonical_garage_client as boundary
 from models.models import User,db
 from flask import g
 client=website.app.test_client()
 assert client.get('/account-deletion/request').status_code==302
 with website.app.app_context():
  db.create_all();user=User(username='manual-'+uuid.uuid4().hex,email=uuid.uuid4().hex+'@example.invalid',password='synthetic',role='user',is_banned=False);db.session.add(user);db.session.commit()
  with client.session_transaction() as saved:saved['_user_id']=str(user.id);saved['_fresh']=True
  g.pop('_login_user',None);calls=[]
  monkeypatch.setattr(boundary,'call',lambda *args:(calls.append(args) or {'workflow':'MANUAL_1_0_5','status':'PENDING'}))
  response=client.post('/account-deletion/request',data={'confirm':'yes','user_id':'99999','email':'other@example.invalid'})
  assert response.status_code==200 and b'owner-bound request is recorded' in response.data
  assert calls==[('/api/account-deletion/requests','POST',{'confirm':True})]
  assert response.headers['Cache-Control']=='no-store'
  assert FlaskClient(website.app).post('/account-deletion/request',data={'confirm':'yes'}).status_code==400


def test_browser_connect_error_does_not_claim_completion(monkeypatch):
 import app as website
 import services.canonical_garage_client as boundary
 from models.models import User,db
 from flask import g
 with website.app.app_context():
  db.create_all();user=User(username='manual-'+uuid.uuid4().hex,email=uuid.uuid4().hex+'@example.invalid',password='synthetic',role='user',is_banned=False);db.session.add(user);db.session.commit();client=website.app.test_client()
  with client.session_transaction() as saved:saved['_user_id']=str(user.id);saved['_fresh']=True
  g.pop('_login_user',None)
  def fail(*args):raise boundary.GarageError(401)
  monkeypatch.setattr(boundary,'call',fail)
  response=client.post('/account-deletion/request',data={'confirm':'yes'})
  assert response.status_code==503 and b'Garage sign-in' in response.data
  assert b'owner-bound request is recorded' not in response.data


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
  with c.session_transaction() as saved:assert not any(key in saved for key in ('_user_id','garage_credentials','garage_selected','google_profile_picture'))
