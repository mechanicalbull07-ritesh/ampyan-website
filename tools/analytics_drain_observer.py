"""Read-only IN-PROCESS observation. A fresh interpreter is not worker evidence."""
import datetime,hashlib,os
from pathlib import Path


def observe(module, expected_pid):
    if expected_pid!=os.getpid():raise RuntimeError('ACTUAL_WORKER_PROCESS_REQUIRED')
    queue=getattr(module,'_queue',None)
    if queue is None:raise RuntimeError('ACTUAL_ANALYTICS_MODULE_REQUIRED')
    with queue.all_tasks_done:
        unfinished=queue.unfinished_tasks
    errors=int(getattr(module,'_last_storage_error',None) is not None)
    return {'worker_pid':os.getpid(),'observed_UTC':datetime.datetime.now(datetime.timezone.utc).isoformat(),
            'module_sha256':hashlib.sha256(Path(module.__file__).read_bytes()).hexdigest(),
            'queue_unfinished':unfinished,'unknown_or_failed':errors,
            'quiescent':unfinished==0 and errors==0,
            'limit':'Current in-process state only; cannot reconstruct historical logged/dropped events or prove ingress isolation.'}


if __name__=='__main__':
    raise SystemExit('NOT_A_WORKER_RECEIPT: call observe on the actual loaded analytics module in each serving worker; do not import it in a fresh shell to claim drain.')
