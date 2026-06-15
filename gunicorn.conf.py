"""Gunicorn nustatymai produkciniam konteineriui."""
import os

port = os.environ.get("PORT", "8000")
bind = os.environ.get("GUNICORN_BIND", f"0.0.0.0:{port}")
workers = int(os.environ.get("GUNICORN_WORKERS", "2"))
worker_class = "sync"
timeout = 30
graceful_timeout = 30
max_requests = 1000
max_requests_jitter = 100
accesslog = "-"
errorlog = "-"
forwarded_allow_ips = "*"
