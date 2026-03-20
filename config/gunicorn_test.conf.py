"""Gunicorn configuration for Greiner Portal TEST environment."""
import multiprocessing

# Server socket
bind = "127.0.0.1:5001"
backlog = 1024

# Worker processes
workers = max(2, multiprocessing.cpu_count())
worker_class = "sync"
worker_connections = 500
timeout = 120
keepalive = 2

# Logging
accesslog = "/opt/greiner-test/logs/gunicorn-test-access.log"
errorlog = "/opt/greiner-test/logs/gunicorn-test-error.log"
loglevel = "info"
access_log_format = '%(h)s %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s "%(f)s" "%(a)s"'

# Process naming
proc_name = "greiner-test"

# Server mechanics
daemon = False
pidfile = "/opt/greiner-test/logs/gunicorn-test.pid"
umask = 0
user = None
group = None
tmp_upload_dir = None
