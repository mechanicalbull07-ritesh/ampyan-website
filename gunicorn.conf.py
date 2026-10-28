import os

bind = f"0.0.0.0:{os.environ.get('PORT', '10000')}"
workers = int(os.environ.get("WEB_CONCURRENCY", "1"))
threads = int(os.environ.get("GUNICORN_THREADS", "2"))
worker_class = "gthread" if threads > 1 else "sync"
timeout = int(os.environ.get("GUNICORN_TIMEOUT", "120"))
graceful_timeout = int(os.environ.get("GUNICORN_GRACEFUL_TIMEOUT", "30"))
keepalive = int(os.environ.get("GUNICORN_KEEPALIVE", "5"))
max_requests = int(os.environ.get("GUNICORN_MAX_REQUESTS", "1000"))
max_requests_jitter = int(os.environ.get("GUNICORN_MAX_REQUESTS_JITTER", "100"))
preload_app = False
accesslog = "-"
errorlog = "-"
loglevel = os.environ.get("GUNICORN_LOG_LEVEL", "info")
capture_output = True
enable_stdio_inheritance = True
proc_name = "ampyan-web"

if os.path.isdir("/dev/shm"):
    worker_tmp_dir = "/dev/shm"
