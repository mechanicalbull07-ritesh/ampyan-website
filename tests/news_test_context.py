"""Authenticated synthetic admin context for payload-only News regressions."""
import uuid,os,hashlib
from contextlib import contextmanager
from unittest.mock import patch
from flask_login import login_user
from models.models import db,User
from services import news_admission as gate
from services import capability_security as caps
@contextmanager
def news_context(app,path='/',**kwargs):
 with app.test_request_context(path,**kwargs):
  db.create_all()
  with db.engine.begin() as c:
   caps.migrate(c)
   for table in gate.TABLES:table.create(c,checkfirst=True)
   c.execute(gate.LEASE.delete());c.execute(gate.GATE.delete())
   if not c.execute(gate.GATE.select()).first():c.execute(gate.GATE.insert().values(id=1,state='OPEN',generation=uuid.uuid4().hex))
  u=User(username=uuid.uuid4().hex,email=uuid.uuid4().hex+'@example.invalid',password='synthetic-test-password',role='admin');db.session.add(u);db.session.commit();login_user(u)
  with db.engine.begin() as c:c.execute(gate.PERMISSION.insert().values(user_id=u.id,credential_binding=hashlib.sha256(u.password.encode()).hexdigest(),active=True))
  with db.engine.begin() as c:caps.bootstrap_verified(c,u,list(caps.SCOPES),caps.now(c)+3600,'synthetic-news-context',True,True)
  secret='synthetic-news-service-token-32chars'
  with db.engine.begin() as c:
   c.execute(gate.CREDENTIAL.delete());c.execute(gate.CREDENTIAL.insert().values(id='website-news',secret_sha256=hashlib.sha256(secret.encode()).hexdigest(),active=True,expires_at=gate.now(c)+3600))
  import app as website
  from routes import auth_routes
  allowed=set(auth_routes.ADMIN_EMAIL_SET)|{u.email}
  with patch.dict(os.environ,NEWS_WEBSITE_SERVICE_TOKEN=secret),patch.object(website,'ADMIN_EMAIL_SET',allowed),patch.object(auth_routes,'ADMIN_EMAIL_SET',allowed):yield
  db.session.rollback()
