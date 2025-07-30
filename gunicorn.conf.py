# Gunicorn configuration file for Saudi Arabian CTAS Triage System
# Railway deployment settings

import os
import multiprocessing

# Server socket - Railway provides PORT environment variable
bind = f"0.0.0.0:{os.environ.get('PORT', 8000)}"
backlog = 2048

# Worker processes - adjust for Railway's container limits
workers = int(os.environ.get('WORKERS', min(multiprocessing.cpu_count() * 2 + 1, 4)))
worker_class = 'sync'
worker_connections = 1000
timeout = int(os.environ.get('TIMEOUT', 300))
keepalive = 2

# Restart workers after this many requests, to prevent memory leaks
max_requests = int(os.environ.get('MAX_REQUESTS', 1000))
max_requests_jitter = int(os.environ.get('MAX_REQUESTS_JITTER', 50))

# Application
wsgi_app = "app:app"

# Logging - Railway handles log aggregation
accesslog = "-"  # Log to stdout for Railway
errorlog = "-"   # Log to stderr for Railway
loglevel = os.environ.get('LOG_LEVEL', 'info').lower()
access_log_format = os.environ.get('ACCESS_LOG_FORMAT', '%(h)s %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s "%(f)s" "%(a)s" %(D)s')

# Process naming
proc_name = "saudi-ctas-triage"

# Server mechanics - Railway specific
daemon = False
pidfile = None  # Railway doesn't need pidfiles
user = None
group = None
tmp_upload_dir = None

# SSL (uncomment and configure for HTTPS)
# keyfile = "/path/to/private.key"
# certfile = "/path/to/certificate.crt"

# Worker temp directory
worker_tmp_dir = "/dev/shm"

# Preload application for better performance
preload_app = True

# Security
limit_request_line = 4094
limit_request_fields = 100
limit_request_field_size = 8190

# Healthcare-specific settings for reliability
graceful_timeout = int(os.environ.get('GRACEFUL_TIMEOUT', 30))

def when_ready(server):
    print("🩺 Saudi Arabian CTAS Triage System is ready!")
    print("🇸🇦 CTAS-based medical triage system")
    print(f"👥 Workers: {workers}")
    print(f"🌐 Listening on: {bind}")
    print(f"📊 Environment: {os.environ.get('FLASK_ENV', 'production')}")

def worker_int(worker):
    print(f"👷 Worker {worker.pid} received INT signal")

def pre_fork(server, worker):
    print(f"👷 Worker {worker.pid} starting...")

def post_fork(server, worker):
    print(f"✅ Worker {worker.pid} started successfully")

def worker_abort(worker):
    print(f"❌ Worker {worker.pid} aborted")

def on_exit(server):
    print("🛑 Saudi Arabian CTAS Triage System shutting down...")
    print("👋 Healthcare system offline!") 