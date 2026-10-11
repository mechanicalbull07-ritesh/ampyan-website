"""Website news admission spans local commit and API sync; no browser secrets."""
import os,hashlib,hmac,math
from functools import wraps
from sqlalchemy import select
from flask import g,request,jsonify,current_app
from flask_login import current_user
from models.models import db
from services import news_admission as gate
from services import capability_security as caps

def required_capability():
 path=request.path
 if '/delete/' in path:return 'news.delete'
 if '/edit/' in path:return 'news.edit'
 if path=='/admin/sync-app-content':return 'news.edit'
 return 'news.create'

def admin_actor():
 if os.environ.get('RENDER','').lower()=='true' or os.environ.get('ENV','').lower()=='production':
  configured=os.environ.get('SECRET_KEY','');effective=current_app.secret_key or ''
  if len(configured)<32 or len(effective)<32:raise gate.NewsGateError('NEWS_SESSION_CONFIGURATION_REQUIRED')
 if not current_user.is_authenticated:raise gate.NewsGateError('NEWS_AUTH_REQUIRED',401)
 if not caps.active(current_user):raise gate.NewsGateError('NEWS_ADMIN_REQUIRED',403)
 caps.check(db.engine,current_user,required_capability())
 return current_user

def service_headers():
 u=admin_actor();token=os.environ.get('NEWS_WEBSITE_SERVICE_TOKEN','')
 if len(token)<32:raise gate.NewsGateError('NEWS_SERVICE_NOT_CONFIGURED')
 try:
  with db.engine.connect() as c:
   row=c.execute(select(gate.CREDENTIAL).where(gate.CREDENTIAL.c.id=='website-news')).mappings().first();t=gate.now(c)
  if not row or not row['active'] or not math.isfinite(row['expires_at']) or row['expires_at']<=t or not hmac.compare_digest(hashlib.sha256(token.encode()).hexdigest(),row['secret_sha256']):raise ValueError()
 except Exception:raise gate.NewsGateError('NEWS_SERVICE_UNAVAILABLE') from None
 headers={'X-AMPYAN-NEWS-SERVICE-TOKEN':token,'X-AMPYAN-NEWS-USER-ID':str(u.id),'X-AMPYAN-NEWS-CREDENTIAL-VERSION':hashlib.sha256(str(u.password or '').encode()).hexdigest()}
 if getattr(g,'news_admission',None):headers['X-AMPYAN-NEWS-ADMISSION']=g.news_admission
 return headers

def register(app):
 def enter():
  if current_user.is_authenticated and request.path.startswith(('/garage','/my-garage','/car-health','/service-history','/profile')):
   try:
    restricted,permissions=caps.profile(db.engine,current_user)
    if restricted and 'platform.admin' not in permissions:raise caps.PermissionDenied('RESTRICTED_IDENTITY_PRIVATE_DATA_DENIED')
   except caps.PermissionDenied as e:return jsonify(success=False,error={'code':e.code}),e.status
  targeted=request.method in {'POST','PUT','PATCH','DELETE'} and (request.path.startswith('/admin/news/') or request.path=='/admin/sync-app-content')
  if request.path=='/admin' or request.path.startswith('/admin/'):
   if not (request.path.startswith('/admin/news/') or request.path=='/admin/sync-app-content'):
    try:
     if not current_user.is_authenticated:
      if request.method in {'GET','HEAD'}:return current_app.login_manager.unauthorized()
      raise caps.PermissionDenied('AUTHENTICATION_REQUIRED',401)
     caps.check(db.engine,current_user,'platform.admin')
    except caps.PermissionDenied as e:return jsonify(success=False,error={'code':e.code}),e.status
    return
   try:admin_actor()
   except (gate.NewsGateError,caps.PermissionDenied) as e:
    if e.status==401 and request.method in {'GET','HEAD'}:return current_app.login_manager.unauthorized()
    return jsonify(success=False,error={'code':e.code}),e.status
  if not targeted:return
  try:
   u=admin_actor();service_headers();g.news_admission=gate.admission(db.engine,u.id,'WEBSITE',authorize=lambda c:caps.require(c,u,required_capability(),'website.news.admit'),prepare=lambda c:caps.lock_accounts(c,[u.id]))
  except (gate.NewsGateError,caps.PermissionDenied) as e:return jsonify(success=False,error={'code':e.code,'message':'News administration is temporarily unavailable. Keep your draft and retry after operator review.'}),e.status
 def leave(error=None):
  ident=getattr(g,'news_admission',None)
  if ident:
   db.session.rollback()
   gate.finish(db.engine,ident);g.news_admission=None
 app.before_request(enter)
 # Fence administration before unrelated middleware or local news commits.
 app.before_request_funcs[None].remove(enter)
 funcs=app.before_request_funcs[None];position=next((i+1 for i,f in enumerate(funcs) if f.__name__=='csrf_protect'),0)
 funcs.insert(position,enter)
 app.teardown_request(leave)


def with_news_admission(fn):
 @wraps(fn)
 def wrapped(*args,**kwargs):
  ident=None
  try:
   u=admin_actor();service_headers()
   if not getattr(g,'news_admission',None):
    ident=gate.admission(db.engine,u.id,'WEBSITE',authorize=lambda c:caps.require(c,u,required_capability(),'website.news.admit'),prepare=lambda c:caps.lock_accounts(c,[u.id]));g.news_admission=ident
   return fn(*args,**kwargs)
  except (gate.NewsGateError,caps.PermissionDenied):return False
  finally:
   if ident:
    db.session.rollback();gate.finish(db.engine,ident);g.news_admission=None
 return wrapped
