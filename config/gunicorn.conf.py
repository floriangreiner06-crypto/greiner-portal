"""Gunicorn configuration for Greiner Portal"""
import multiprocessing

# Server socket
bind = "127.0.0.1:8000"
backlog = 2048

# Worker processes
workers = multiprocessing.cpu_count() * 2 + 1
worker_class = "sync"
worker_connections = 1000
timeout = 30
keepalive = 2

# Logging
accesslog = "/opt/greiner-portal/logs/gunicorn-access.log"
errorlog = "/opt/greiner-portal/logs/gunicorn-error.log"
loglevel = "info"
access_log_format = '%(h)s %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s "%(f)s" "%(a)s"'

# Process naming
proc_name = "greiner-portal"

# Server mechanics
daemon = False
pidfile = "/opt/greiner-portal/logs/gunicorn.pid"
umask = 0
user = None
group = None
tmp_upload_dir = None

# SSL (falls später benötigt)
# keyfile = None
# certfile = None
