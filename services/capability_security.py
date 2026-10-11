"""Account-bound application capabilities, distinct from legacy roles and SQL roles."""
import hashlib,math,secrets
from contextlib import contextmanager
from sqlalchemy import MetaData,Table,Column,Integer,String,Float,Boolean,ForeignKey,CheckConstraint,select,text
META=MetaData();USER=Table('user',META,Column('id',Integer,primary_key=True),Column('password',String),Column('is_blocked',Boolean),Column('is_banned',Boolean))
STATE=Table('app_permission_revision',META,Column('user_id',Integer,ForeignKey('user.id',ondelete='CASCADE'),primary_key=True,autoincrement=False),Column('revision',Integer,nullable=False),Column('news_staff_verified',Boolean,nullable=False),Column('restricted_identity',Boolean,nullable=False,server_default=text('false')),CheckConstraint('revision>=0'))
GRANT=Table('app_capability_grant',META,Column('user_id',Integer,ForeignKey('app_permission_revision.user_id',ondelete='CASCADE'),primary_key=True,autoincrement=False),Column('capability',String(64),primary_key=True),Column('scope',String(64),nullable=False),Column('credential_binding',String(64),nullable=False),Column('active',Boolean,nullable=False),Column('expires_at',Float,nullable=False),CheckConstraint('expires_at>0 AND expires_at<1000000000000'))
AUDIT=Table('app_authorization_audit',META,Column('id',String(64),primary_key=True),Column('actor_user_id',Integer,ForeignKey('user.id',ondelete='SET NULL')),Column('subject_user_id',Integer,ForeignKey('user.id',ondelete='SET NULL')),Column('action',String(64),nullable=False),Column('target',String(64),nullable=False),Column('outcome',String(32),nullable=False),Column('permission_revision',Integer),Column('approval_reference',String(64)),Column('recorded_at',Float,nullable=False))
APPROVAL=Table('app_maintenance_approval',META,Column('id',String(64),primary_key=True),Column('user_id',Integer,ForeignKey('app_permission_revision.user_id',ondelete='CASCADE'),nullable=False),Column('issued_by',Integer,ForeignKey('user.id',ondelete='SET NULL')),Column('action',String(32),nullable=False),Column('target',String(64),nullable=False),Column('credential_binding',String(64),nullable=False),Column('permission_revision',Integer,nullable=False),Column('active',Boolean,nullable=False),Column('expires_at',Float,nullable=False),Column('remaining_uses',Integer,nullable=False),CheckConstraint('expires_at>0 AND expires_at<1000000000000'),CheckConstraint('remaining_uses>=0 AND remaining_uses<=10'))
TABLES=(STATE,GRANT,AUDIT,APPROVAL)
SCOPES={**{x:'news' for x in ['news.read','news.create','news.edit','news.delete','news.manage_publishers']},'news.seed':'news_seed','maintenance.news_gate':'news_write_gate','maintenance.news_sequence_review':'public.news_article_id_seq','platform.admin':'platform'}
NEWS_STAFF={'news.read','news.create','news.edit','news.delete'}
GATE_ACTIONS={'status','pause','resume','renew','takeover','reconcile'}
class PermissionDenied(Exception):
 def __init__(self,code='CAPABILITY_REQUIRED',status=403):self.code=code;self.status=status;super().__init__(code)
def binding(user):return hashlib.sha256(str(user.password or '').encode()).hexdigest()
def now(c):return float(c.execute(text("SELECT EXTRACT(EPOCH FROM clock_timestamp())" if c.dialect.name=='postgresql' else "SELECT (julianday('now')-2440587.5)*86400.0")).scalar_one())
def active(user):return bool(user and not user.is_blocked and not user.is_banned)
def audit(c,uid,action,target,outcome,revision=None,subject=None,reference=None):
 c.execute(AUDIT.insert().values(id=secrets.token_hex(32),actor_user_id=uid,subject_user_id=subject,action=action,target=target,outcome=outcome,permission_revision=revision,approval_reference=reference,recorded_at=now(c)))
def lock_accounts(c,uids):
 if c.dialect.name=='sqlite' and not c.connection.driver_connection.in_transaction:
  c.exec_driver_sql('PRAGMA foreign_keys=ON');c.exec_driver_sql('BEGIN IMMEDIATE')
 c.execute(select(USER.c.id).where(USER.c.id.in_(sorted(set(uids)))).order_by(USER.c.id).with_for_update(read=True)).all()
def state(c,uid,lock=False):
 if lock and c.dialect.name=='sqlite' and not c.connection.driver_connection.in_transaction:c.exec_driver_sql('BEGIN IMMEDIATE')
 stmt=select(STATE).where(STATE.c.user_id==uid)
 if lock:stmt=stmt.with_for_update()
 return c.execute(stmt).mappings().first()
def allowed(c,user,cap):
 if cap not in SCOPES or not active(user):return False
 # Current account and credential version are authoritative, not a cached role/session.
 live=c.execute(select(USER).where(USER.c.id==user.id)).mappings().first()
 if not live or live['is_blocked'] or live['is_banned'] or hashlib.sha256(str(live['password'] or '').encode()).hexdigest()!=binding(user):return False
 row=c.execute(select(GRANT).where(GRANT.c.user_id==user.id,GRANT.c.capability==cap)).mappings().first()
 return bool(row and row['active'] and row['scope']==SCOPES[cap] and math.isfinite(row['expires_at']) and row['expires_at']>now(c) and row['credential_binding']==binding(user))
def profile(engine,user):
 try:
  with engine.connect() as c:
   s=state(c,user.id);live=c.execute(select(USER).where(USER.c.id==user.id)).mappings().first()
   if not live or live['is_blocked'] or live['is_banned'] or hashlib.sha256(str(live['password'] or '').encode()).hexdigest()!=binding(user):raise PermissionDenied('ACCOUNT_UNAVAILABLE',401)
   rows=c.execute(select(GRANT).where(GRANT.c.user_id==user.id)).mappings().all();t=now(c)
   capabilities=frozenset(x['capability'] for x in rows if x['capability'] in SCOPES and x['scope']==SCOPES[x['capability']] and x['active'] and math.isfinite(x['expires_at']) and x['expires_at']>t and x['credential_binding']==binding(user))
   return bool(s and s['restricted_identity']),capabilities
 except PermissionDenied:raise
 except Exception:raise PermissionDenied('AUTHORIZATION_UNAVAILABLE',503) from None

def has(engine,user,cap):
 try:
  with engine.connect() as c:return allowed(c,user,cap)
 except Exception:return False
def require(c,user,cap,action='authorize'):
 if user:lock_accounts(c,[user.id])
 revision=state(c,user.id,True) if user else None
 valid=allowed(c,user,cap);audit(c,user.id if active(user) else None,action,SCOPES.get(cap,'unknown'),'ALLOW' if valid else 'DENY',revision['revision'] if revision else None)
 if not valid:raise PermissionDenied()
def check(engine,user,cap):
 # Persist denials as well as successful decisions before raising.
 error=None
 try:
  with engine.begin() as c:
   try:require(c,user,cap)
   except PermissionDenied as e:error=e
 except PermissionDenied:raise
 except Exception:raise PermissionDenied('AUTHORIZATION_UNAVAILABLE',503) from None
 if error:raise error

def bootstrap_verified(c,user,caps,expires_at,reference,verified=False,news_staff=False):
 """Offline/operator provisioning helper; no HTTP bootstrap. Never inferred from role/email."""
 if verified is not True or not reference or len(reference)>64 or not active(user):raise PermissionDenied('VERIFIED_IDENTITY_REQUIRED')
 if not math.isfinite(expires_at) or not now(c)<expires_at<=now(c)+30*86400:raise PermissionDenied('INVALID_GRANT_EXPIRY',400)
 if not caps or any(x not in SCOPES for x in caps):raise PermissionDenied('UNKNOWN_CAPABILITY',400)
 lock_accounts(c,[user.id])
 current=state(c,user.id,True)
 if not current:c.execute(STATE.insert().values(user_id=user.id,revision=0,news_staff_verified=news_staff,restricted_identity=any(x!='news.read' for x in caps)));current=state(c,user.id,True)
 revision=current['revision']+1
 for cap in caps:
  values=dict(user_id=user.id,capability=cap,scope=SCOPES[cap],credential_binding=binding(user),active=True,expires_at=expires_at)
  row=c.execute(select(GRANT.c.user_id).where(GRANT.c.user_id==user.id,GRANT.c.capability==cap)).first()
  if row:c.execute(GRANT.update().where(GRANT.c.user_id==user.id,GRANT.c.capability==cap).values(**values))
  else:c.execute(GRANT.insert().values(**values))
 c.execute(STATE.update().where(STATE.c.user_id==user.id).values(revision=revision,news_staff_verified=bool(news_staff or current['news_staff_verified']),restricted_identity=bool(current['restricted_identity'] or any(x!='news.read' for x in caps))))
 audit(c,None,'verified.bootstrap','account_capabilities','ALLOW',revision,user.id,reference);return revision

def change(c,actor,subject,cap,expires_at,enabled,expected_revision):
 if cap not in SCOPES or type(expected_revision) is not int or type(enabled) is not bool:raise PermissionDenied('INVALID_PERMISSION_CHANGE',400)
 # Serialize actor/subject locks in deterministic order; concurrent stale updates409.
 lock_accounts(c,[actor.id,subject.id])
 for uid in sorted({actor.id,subject.id}):state(c,uid,True)
 platform=allowed(c,actor,'platform.admin');manager=allowed(c,actor,'news.manage_publishers')
 target=state(c,subject.id,True)
 if not platform and not (manager and cap in NEWS_STAFF and target and target['news_staff_verified']):raise PermissionDenied('GRANT_SCOPE_DENIED')
 if not target:raise PermissionDenied('PRIVATE_IDENTITY_VERIFICATION_REQUIRED')
 if target['revision']!=expected_revision:raise PermissionDenied('STALE_PERMISSION_REVISION',409)
 if not math.isfinite(expires_at) or not now(c)<expires_at<=now(c)+30*86400:raise PermissionDenied('INVALID_GRANT_EXPIRY',400)
 issuer_cap='platform.admin' if platform else 'news.manage_publishers'
 issuer=c.execute(select(GRANT.c.expires_at).where(GRANT.c.user_id==actor.id,GRANT.c.capability==issuer_cap)).scalar_one()
 if expires_at>issuer:raise PermissionDenied('DELEGATION_EXPIRY_EXCEEDS_AUTHORITY',400)
 values=dict(scope=SCOPES[cap],credential_binding=binding(subject),active=enabled,expires_at=expires_at)
 existing=c.execute(select(GRANT.c.user_id).where(GRANT.c.user_id==subject.id,GRANT.c.capability==cap)).first()
 if existing:c.execute(GRANT.update().where(GRANT.c.user_id==subject.id,GRANT.c.capability==cap).values(**values))
 else:c.execute(GRANT.insert().values(user_id=subject.id,capability=cap,**values))
 revision=expected_revision+1;c.execute(STATE.update().where(STATE.c.user_id==subject.id).values(revision=revision,restricted_identity=bool(target['restricted_identity'] or enabled and cap!='news.read')));audit(c,actor.id,'grant.change',cap,'ALLOW',revision,subject.id);return revision

def issue_approval(c,actor,subject,action,target,expires_at,uses=1):
 lock_accounts(c,[actor.id,subject.id])
 for uid in sorted({actor.id,subject.id}):state(c,uid,True)
 require(c,actor,'platform.admin','approval.issue')
 permitted=(action in GATE_ACTIONS and target=='news_write_gate') or (action=='sequence_review' and target=='public.news_article_id_seq') or (action=='seed' and target=='news_seed')
 cap='news.seed' if action=='seed' else 'maintenance.news_sequence_review' if action=='sequence_review' else 'maintenance.news_gate'
 s=state(c,subject.id,True)
 if not permitted or not s or not allowed(c,subject,cap):raise PermissionDenied('APPROVAL_TARGET_DENIED')
 if not math.isfinite(expires_at) or not now(c)<expires_at<=now(c)+300 or type(uses) is not int or not 1<=uses<=10:raise PermissionDenied('INVALID_APPROVAL_WINDOW',400)
 issuer_expiry=c.execute(select(GRANT.c.expires_at).where(GRANT.c.user_id==actor.id,GRANT.c.capability=='platform.admin')).scalar_one()
 if expires_at>issuer_expiry:raise PermissionDenied('APPROVAL_EXPIRY_EXCEEDS_AUTHORITY',400)
 ident=secrets.token_hex(32);c.execute(APPROVAL.insert().values(id=ident,user_id=subject.id,issued_by=actor.id,action=action,target=target,credential_binding=binding(subject),permission_revision=s['revision'],active=True,expires_at=expires_at,remaining_uses=uses));audit(c,actor.id,'approval.issue',target,'ALLOW',s['revision'],subject.id,ident);return ident

def consume(c,user,ident,action,target):
 cap='news.seed' if action=='seed' else 'maintenance.news_sequence_review' if action=='sequence_review' else 'maintenance.news_gate'
 require(c,user,cap,'maintenance.'+action);s=state(c,user.id,True);row=c.execute(select(APPROVAL).where(APPROVAL.c.id==ident).with_for_update()).mappings().first()
 if not row or row['user_id']!=user.id or row['action']!=action or row['target']!=target or not row['active'] or not math.isfinite(row['expires_at']) or row['expires_at']<=now(c) or row['remaining_uses']<=0 or row['credential_binding']!=binding(user) or row['permission_revision']!=s['revision']:raise PermissionDenied('EXACT_OPERATION_APPROVAL_REQUIRED')
 issuer=c.execute(select(USER).where(USER.c.id==row['issued_by'])).mappings().first()
 if not issuer or issuer['is_blocked'] or issuer['is_banned']:raise PermissionDenied('APPROVAL_ISSUER_UNAVAILABLE')
 from types import SimpleNamespace
 issuer_user=SimpleNamespace(**dict(issuer))
 if not allowed(c,issuer_user,'platform.admin'):raise PermissionDenied('APPROVAL_ISSUER_REVOKED')
 c.execute(APPROVAL.update().where(APPROVAL.c.id==ident).values(remaining_uses=row['remaining_uses']-1));audit(c,user.id,'maintenance.'+action,target,'ALLOW',s['revision'],reference=ident)

def migrate(c):
 from sqlalchemy import inspect
 if 'user' not in inspect(c).get_table_names():raise RuntimeError('Existing user schema required')
 created=[]
 for t in TABLES:
  if t.name not in inspect(c).get_table_names():t.create(c);created.append(t.name)
  else:
   i=inspect(c)
   columns={x['name']:x for x in i.get_columns(t.name)}
   if set(columns)!=set(t.c.keys()) or set(i.get_pk_constraint(t.name)['constrained_columns'])!={x.name for x in t.primary_key}:raise RuntimeError('Capability schema drift')
   for col in t.c:
    actual=columns[col.name]
    if actual['type']._type_affinity!=col.type._type_affinity or getattr(actual['type'],'length',None)!=getattr(col.type,'length',None) or actual['nullable']!=col.nullable:raise RuntimeError('Capability column drift')
   expected={(tuple(x.parent.name for x in fk.elements),tuple(x.column.table.name+'.'+x.column.name for x in fk.elements),fk.ondelete) for fk in t.foreign_key_constraints}
   actual={(tuple(x['constrained_columns']),tuple(x['referred_table']+'.'+col for col in x['referred_columns']),x.get('options',{}).get('ondelete')) for x in i.get_foreign_keys(t.name)}
   if expected!=actual:raise RuntimeError('Capability foreign key drift')
   import re
   def normalize(value):return re.sub(r'[()\s]', '',re.sub(r"'([0-9]+)'",r'\1',re.sub(r'::(?:double precision|integer|bigint|numeric)','',str(value).lower())))
   expected={normalize(x.sqltext) for x in t.constraints if isinstance(x,CheckConstraint)}
   actual={normalize(x['sqltext']) for x in i.get_check_constraints(t.name)}
   if expected!=actual:raise RuntimeError('Capability check drift: '+t.name+': '+repr(expected)+' != '+repr(actual))
 return {'created_tables':created}
def rollback_unused(c,journal):
 if any(c.execute(select(t).limit(1)).first() for t in TABLES):raise RuntimeError('Adopted permissions/audit must be retained')
 for t in reversed(TABLES):
  if t.name in journal['created_tables']:t.drop(c)
