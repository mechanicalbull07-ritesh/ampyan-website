"""Reproduce the website RC using only explicit frozen checkouts and disposable state."""
import argparse,json,os,shutil,subprocess,sys
from pathlib import Path

RC='df045fc46b89d0a56819c67d4279821a1f6f8466'
p=argparse.ArgumentParser()
p.add_argument('--root',required=True)
p.add_argument('--backend',required=True)
p.add_argument('--backend-python',required=True)
p.add_argument('--postgres-bin',required=True)
args=p.parse_args()
w=Path(__file__).resolve().parents[1];b=Path(args.backend).resolve();r=Path(args.root).resolve()
if not r.is_relative_to(Path('/tmp').resolve()) or r.exists():
    raise SystemExit('--root must be a NEW disposable directory under /tmp')
if subprocess.check_output(['git','rev-parse','HEAD'],cwd=b,text=True).strip()!=RC:
    raise SystemExit('Wrong backend RC')
if subprocess.check_output(['git','status','--porcelain'],cwd=b,text=True).strip():
    raise SystemExit('Backend checkout must be clean')
r.mkdir();reports=r/'reports';reports.mkdir();state=r/'state';state.mkdir()
pg=Path(args.postgres_bin).resolve();python=str(Path(args.backend_python).absolute())
e={k:v for k,v in os.environ.items() if not k.startswith('PG') and 'DATABASE_URL' not in k and 'POSTGRES' not in k and k not in ('AMPYAN_WEBSITE_TEST_PG_META','PYTHONPATH')}
e.update(ENV='test',RENDER='false',PYTHONDONTWRITEBYTECODE='1',AMPYAN_SCHEMA_MANAGED_EXTERNALLY='1',
 AMPYAN_BACKEND_RC_PATH=str(b),AMPYAN_BACKEND_TEST_PYTHON=python,AMPYAN_API_BASE_URL='http://127.0.0.1:1',
 ENABLE_BACKGROUND_DB_INIT='false',ENABLE_REQUEST_DB_INIT='false',ENABLE_MANAGED_PERSONA_MIGRATION='false',
 AUTH_SIGNING_KEY='synthetic-website-integration-key-only-not-for-real-accounts',
 SECRET_KEY='synthetic-release-validation-session-key',DATABASE_URL='sqlite:///'+str(state/'validation.sqlite'),
 AMPYAN_REPORT_DIR=str(reports),AMPYAN_TEST_STATE=str(state))
def run(label,cmd,env=None,cwd=None):
    with (reports/(label+'.log')).open('w') as log:
        result=subprocess.run(cmd,cwd=cwd or w,env=env or e,stdout=log,stderr=subprocess.STDOUT)
    print(label,result.returncode,flush=True)
    if result.returncode:
        raise RuntimeError(label+' failed; inspect '+str(reports/(label+'.log')))
pytest=[sys.executable,'-m','pytest','-q','--disable-warnings','-o','cache_dir='+str(r/'pytest-cache')]
run('website-sqlite',pytest+['--basetemp',str(r/'sqlite-tests')])
run('analytics-e2e',[sys.executable,'-c',"import runpy; runpy.run_path('tests/conftest.py'); runpy.run_path('tests/local_analytics_e2e.py',run_name='__main__')"])
be=dict(e,PYTHONPATH=str(b))
run('configuration-matrix',[python,'-m','pytest','-q','tests/car_health/test_configuration_overlay.py',
 '--basetemp',str(r/'configuration-tests'),'-o','cache_dir='+str(r/'backend-cache')],be,b)
cluster=r/'postgres';socket=cluster/'socket';socket.mkdir(parents=True)
meta=dict(data=str(cluster/'data'),socket=str(socket),port=55459,user='ampyan_website_test',database='ampyan_website_synthetic')
meta_file=r/'pg-meta.json';meta_file.write_text(json.dumps(meta))
pe=dict(be,DATABASE_URL=f"postgresql+psycopg2://{meta['user']}@/{meta['database']}?host={socket}&port={meta['port']}")
run('pg-init',[str(pg/'initdb'),'-D',meta['data'],'-U',meta['user'],'--auth=trust','--no-locale','--encoding=UTF8'])
started=False
try:
    run('pg-start',[str(pg/'pg_ctl'),'-D',meta['data'],'-l',str(reports/'postgres.log'),'-o',f"-k {socket} -p {meta['port']} -c listen_addresses=''",'start'])
    started=True
    run('pg-createdb',[str(pg/'createdb'),'-h',str(socket),'-p',str(meta['port']),'-U',meta['user'],meta['database']])
    proof="""import psycopg2,os,json
from pathlib import Path
m=json.loads(Path(%r).read_text())
c=psycopg2.connect(os.environ['DATABASE_URL'].replace('postgresql+psycopg2:','postgresql:'))
q=c.cursor();q.execute("SELECT current_setting('data_directory'),current_setting('unix_socket_directories'),current_setting('listen_addresses'),inet_server_addr(),current_database(),version()")
r=q.fetchone();assert r[0]==m['data'] and r[1]==m['socket'] and r[2]=='' and r[3] is None and r[4]==m['database'];print(r);c.close()
""" % str(meta_file)
    run('pg-local-proof',[python,'-c',proof],pe,b)
    run('pg-schema',[python,str(b/'tools/release_validation/schema.py')],pe,b)
    we=dict(e,AMPYAN_WEBSITE_TEST_PG_META=str(meta_file))
    run('website-postgresql',pytest+['--basetemp',str(r/'pg-tests')],we)
    run('pg-deletion-atomicity',[python,str(b/'tests/support/vehicle_deletion_contract.py')],pe,b)
finally:
    if started:
        run('pg-stop',[str(pg/'pg_ctl'),'-D',meta['data'],'-m','fast','stop'])
        assert not (Path(meta['data'])/'postmaster.pid').exists()
        shutil.rmtree(cluster)
        (reports/'cleanup.json').write_text(json.dumps(dict(stopped=True,removed=True)))
print('WEBSITE RC VALIDATION PASS',flush=True)
