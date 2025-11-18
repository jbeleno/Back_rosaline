"""
Configuración de Gunicorn optimizada para FastAPI + PostgreSQL remoto.

La mayoría de los valores se pueden sobreescribir con variables de entorno:
 - GUNICORN_WORKERS
 - GUNICORN_BIND
 - GUNICORN_TIMEOUT
 - GUNICORN_GRACEFUL_TIMEOUT
 - GUNICORN_KEEPALIVE
 - GUNICORN_MAX_REQUESTS
 - GUNICORN_MAX_REQUESTS_JITTER
 - GUNICORN_LOG_LEVEL
 - GUNICORN_ACCESSLOG
 - GUNICORN_ERRORLOG
"""

import multiprocessing
import os
from pathlib import Path

APP_DIR = Path(__file__).resolve().parent
DEFAULT_SOCKET = "unix:/run/fastapi-ecommerce.sock"

bind = os.getenv("GUNICORN_BIND", DEFAULT_SOCKET)
workers = int(os.getenv("GUNICORN_WORKERS", (multiprocessing.cpu_count() * 2) + 1))
worker_class = "uvicorn.workers.UvicornWorker"
timeout = int(os.getenv("GUNICORN_TIMEOUT", "120"))
graceful_timeout = int(os.getenv("GUNICORN_GRACEFUL_TIMEOUT", "30"))
keepalive = int(os.getenv("GUNICORN_KEEPALIVE", "5"))

max_requests = int(os.getenv("GUNICORN_MAX_REQUESTS", "1000"))
max_requests_jitter = int(os.getenv("GUNICORN_MAX_REQUESTS_JITTER", "50"))

errorlog = os.getenv("GUNICORN_ERRORLOG", f"/var/log/fastapi-ecommerce/gunicorn-error.log")
accesslog = os.getenv("GUNICORN_ACCESSLOG", f"/var/log/fastapi-ecommerce/gunicorn-access.log")
loglevel = os.getenv("GUNICORN_LOG_LEVEL", "info")

# Ajustes recomendados para conexiones a PostgreSQL
preload_app = True  # reduce la latencia inicial y evita conexiones duplicadas
worker_tmp_dir = "/dev/shm"

def on_starting(server):
    server.log.info("Iniciando Gunicorn con configuración de FastAPI E-commerce")

def when_ready(server):
    server.log.info("Gunicorn listo; notificando a systemd.")

