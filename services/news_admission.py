"""Durable news-only admissions. No timers, polling, Redis or automatic reopening.
Used by both server applications against the same PostgreSQL database.
"""
import secrets,os,socket
WORKER_BOOT=secrets.token_hex(8)
from contextlib import contextmanager
from sqlalchemy import MetaData,Table,Column,Integer,String,Float,Boolean,ForeignKey,CheckConstraint,select,func,text,delete
META=MetaData();Table('user',META,Column('id',Integer,primary_key=True))
GATE=Table('news_write_gate',META,Column('id',Integer,primary_key=True,autoincrement=False),Column('state',String(16),nullable=False),Column('generation',String(64),nullable=False),Column('owner_id',Integer,nullable=True),Column('owner_binding',String(64),nullable=True),Column('deadline',Float,nullable=True),CheckConstraint('id=1'),CheckConstraint("state IN ('OPEN','PAUSING','PAUSED')"))
LEASE=Table('news_write_admission',META,Column('id',String(64),primary_key=True),Column('actor_id',Integer,ForeignKey('user.id'),nullable=False),Column('kind',String(16),nullable=False),Column('worker_ref',String(200),nullable=False),Column('parent_id',String(64),ForeignKey('news_write_admission.id',ondelete='SET NULL'),nullable=True),Column('started_at',Float,nullable=False),Column('expires_at',Float,nullable=False),CheckConstraint("kind IN ('API','WEBSITE','CONTINUATION','SEED')"))
CREDENTIAL=Table('news_service_credential',META,Column('id',String(32),primary_key=True),Column('secret_sha256',String(64),nullable=False),Column('active',Boolean,nullable=False),Column('expires_at',Float,nullable=False))
PERMISSION=Table('news_admin_permission',META,Column('user_id',Integer,ForeignKey('user.id',ondelete='CASCADE'),primary_key=True,autoincrement=False),Column('credential_binding',String(64),nullable=False),Column('active',Boolean,nullable=False))
TABLES=(GATE,LEASE,CREDENTIAL,PERMISSION)
class NewsGateError(Exception):
 def __init__(self,code,status=503):super().__init__(code);self.code=code;self.status=status

def now(c):
 return float(c.execute(text("SELECT EXTRACT(EPOCH FROM clock_timestamp())" if c.dialect.name=='postgresql' else "SELECT (julianday('now')-2440587.5)*86400.0")).scalar_one())
@contextmanager
def locked(engine,prepare=None):
 try:
  with engine.begin() as c:
   if c.dialect.name=='sqlite':
    c.execute(text('PRAGMA foreign_keys=ON'))
    if not c.connection.driver_connection.in_transaction:c.execute(text('BEGIN IMMEDIATE'))
   if prepare is not None:prepare(c)
   row=c.execute(select(GATE).where(GATE.c.id==1).with_for_update()).mappings().first()
   if row is None:raise NewsGateError('NEWS_GATE_NOT_INITIALIZED')
   yield c,row
 except NewsGateError:raise
 except Exception:raise NewsGateError('NEWS_GATE_UNAVAILABLE') from None

def _leases(c):return list(c.execute(select(LEASE)).mappings())
def _incident(row,leases,t):return (row['state']!='OPEN' and (row['deadline'] is None or t>=row['deadline'])) or any(t>=x['expires_at'] for x in leases)
def admission(engine,actor_id,kind,parent_id=None,authorize=None,prepare=None):
 with locked(engine,prepare) as (c,row):
  t=now(c);leases=_leases(c)
  if authorize is not None:authorize(c)
  if _incident(row,leases,t):raise NewsGateError('NEWS_OPERATOR_REVIEW_REQUIRED')
  if len(leases)>=1000:raise NewsGateError('NEWS_ADMISSION_CAPACITY')
  if parent_id is not None:
   parent=next((x for x in leases if x['id']==parent_id),None)
   if not parent or parent['kind']!='WEBSITE' or parent['actor_id']!=actor_id:raise NewsGateError('NEWS_CONTINUATION_INVALID',403)
   kind='CONTINUATION'
  elif row['state']!='OPEN':raise NewsGateError('NEWS_WRITES_PAUSED')
  ident=secrets.token_hex(32);c.execute(LEASE.insert().values(id=ident,actor_id=actor_id,kind=kind,worker_ref=(socket.gethostname()+':'+str(os.getpid())+':'+WORKER_BOOT)[:200],parent_id=parent_id,started_at=t,expires_at=t+120))
  return ident

def finish(engine,ident):
 with locked(engine) as (c,row):c.execute(delete(LEASE).where(LEASE.c.id==ident))
def status(engine):
 with locked(engine) as (c,row):
  t=now(c);leases=_leases(c);incident=_incident(row,leases,t)
  return {'state':'INCIDENT' if incident else row['state'],'generation':row['generation'],'deadline':row['deadline'],'active_admissions':len(leases),'expired_admissions':[x['id'] for x in leases if t>=x['expires_at']],'admission_details':[{'id':x['id'],'kind':x['kind'],'worker_ref':x['worker_ref'],'started_at':x['started_at'],'expires_at':x['expires_at']} for x in leases],'participating_writers_drained':row['state']=='PAUSED' and not leases and not incident,'external_sql_writers_verified':False,'full_quiescence':False}
def pause(engine,actor_id,generation=None,duration=60,owner_binding=None):
 if type(duration) is not int or not 1<=duration<=60:raise NewsGateError('NEWS_PAUSE_DURATION_INVALID',400)
 with locked(engine) as (c,row):
  t=now(c);leases=_leases(c)
  if row['state']=='OPEN':
   if generation is not None:raise NewsGateError('NEWS_GATE_GENERATION_CONFLICT',409)
   generation=secrets.token_hex(32);state='PAUSING' if leases else 'PAUSED';c.execute(GATE.update().where(GATE.c.id==1).values(state=state,generation=generation,owner_id=actor_id,owner_binding=owner_binding,deadline=t+duration))
  else:
   if generation!=row['generation'] or row['owner_id']!=actor_id or row['owner_binding']!=owner_binding:raise NewsGateError('NEWS_GATE_GENERATION_CONFLICT',409)
   if _incident(row,leases,t):raise NewsGateError('NEWS_OPERATOR_REVIEW_REQUIRED',409)
   if not leases:c.execute(GATE.update().where(GATE.c.id==1).values(state='PAUSED'))
 return status(engine)
def resume(engine,actor_id,generation,incident_ack=False,owner_binding=None):
 with locked(engine) as (c,row):
  leases=_leases(c);t=now(c)
  if generation!=row['generation'] or row['owner_id']!=actor_id or row['owner_binding']!=owner_binding:raise NewsGateError('NEWS_GATE_GENERATION_CONFLICT',409)
  if leases:raise NewsGateError('NEWS_WRITERS_NOT_DRAINED',409)
  if _incident(row,leases,t) and incident_ack is not True:raise NewsGateError('NEWS_INCIDENT_ACK_REQUIRED',409)
  c.execute(GATE.update().where(GATE.c.id==1).values(state='OPEN',generation=secrets.token_hex(32),owner_id=None,owner_binding=None,deadline=None))
 return status(engine)
def reconcile(engine,actor_id,generation,ids,terminated_confirmed,owner_binding=None):
 if terminated_confirmed is not True or not isinstance(ids,list) or not ids:raise NewsGateError('NEWS_TERMINATION_EVIDENCE_REQUIRED',400)
 with locked(engine) as (c,row):
  if row['owner_id']!=actor_id or row['generation']!=generation or row['owner_binding']!=owner_binding:raise NewsGateError('NEWS_GATE_GENERATION_CONFLICT',409)
  t=now(c);leases={x['id']:x for x in _leases(c)}
  if any(i not in leases or leases[i]['expires_at']>t for i in ids):raise NewsGateError('NEWS_LEASE_REVIEW_INVALID',409)
  c.execute(delete(LEASE).where(LEASE.c.id.in_(ids)))
 return status(engine)

def takeover(engine,actor_id,generation,confirmed,owner_unavailable,owner_binding):
 if confirmed is not True:raise NewsGateError('NEWS_TAKEOVER_ACK_REQUIRED',400)
 with locked(engine) as (c,row):
  if row['state']=='OPEN' or row['generation']!=generation:raise NewsGateError('NEWS_GATE_GENERATION_CONFLICT',409)
  if not _incident(row,_leases(c),now(c)) and not owner_unavailable:raise NewsGateError('NEWS_CURRENT_OPERATOR_ACTIVE',409)
  c.execute(GATE.update().values(owner_id=actor_id,owner_binding=owner_binding,generation=secrets.token_hex(32)))
 return status(engine)

def renew(engine,actor_id,generation,confirmed,duration,owner_binding):
 if confirmed is not True or type(duration) is not int or not 1<=duration<=60:raise NewsGateError('NEWS_RENEW_ACK_REQUIRED',400)
 with locked(engine) as (c,row):
  if row['state']=='OPEN' or row['generation']!=generation:raise NewsGateError('NEWS_GATE_GENERATION_CONFLICT',409)
  if row['owner_id'] is not None and (row['owner_id']!=actor_id or row['owner_binding']!=owner_binding):raise NewsGateError('NEWS_GATE_GENERATION_CONFLICT',409)
  if _leases(c):raise NewsGateError('NEWS_WRITERS_NOT_DRAINED',409)
  c.execute(GATE.update().values(state='PAUSED',owner_id=actor_id,owner_binding=owner_binding,generation=secrets.token_hex(32),deadline=now(c)+duration))
 return status(engine)
