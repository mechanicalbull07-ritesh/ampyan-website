"""Release-relative public CA bundle and explicit, attributable TLS connections."""
import hashlib
import os
from pathlib import Path
import re
import ssl
from sqlalchemy.engine import make_url

CA_SHA256 = 'fc9165a12403263e7ebfbdad7be7a3eac0fa5d325d3c70465f28d3690072ca28'


def ca_path():
    path = Path(__file__).resolve().parents[1]/'certs/postgres-roots.pem'
    if not path.is_file() or hashlib.sha256(path.read_bytes()).hexdigest() != CA_SHA256:
        raise RuntimeError('POSTGRES_CA_BUNDLE_MISSING_OR_DRIFTED')
    ssl.create_default_context(cafile=str(path))
    return str(path)


def database_url(value, service):
    url = make_url(value)
    if url.drivername == 'postgres':
        url = url.set(drivername='postgresql')
    if not url.drivername.startswith('postgresql'):
        raise RuntimeError('POSTGRES_TRANSPORT_REQUIRES_POSTGRES')
    instance = os.environ.get('RENDER_INSTANCE_ID', '')
    instance = instance if re.fullmatch(r'[a-zA-Z0-9_-]{1,40}', instance) else 'instance-unset'
    if service not in ('api', 'website', 'controller', 'readonly-verifier'):
        raise RuntimeError('UNKNOWN_POSTGRES_SERVICE_TAG')
    query = {'application_name': 'ampyan/'+service+'/'+instance}
    root = os.environ.get('COMMUNITY_PG_SYNTHETIC_ROOT')
    if root:
        p = Path(root)
        host = url.query.get('host') or url.host or ''
        if (os.environ.get('ENV', '').lower() == 'production' or os.environ.get('RENDER', '').lower() == 'true'
                or not root.startswith('/private/tmp/ampyan-primary-pg-') or p.resolve() != p
                or p.stat().st_uid != os.getuid() or p.stat().st_mode & 0o077
                or host != str(p/'socket') or not (url.database or '').startswith('qa_primary_')):
            raise RuntimeError('NON_OWNED_SYNTHETIC_TARGET')
    else:
        if url.query.get('sslmode') not in (None, 'verify-full'):
            raise RuntimeError('CONTRADICTORY_POSTGRES_TLS_MODE')
        query.update(sslmode='verify-full', sslrootcert=ca_path())
    return url.update_query_dict(query).render_as_string(hide_password=False)
