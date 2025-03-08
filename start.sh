#!/bin/bash
# Ensure script exits on any error
set -e

# Use Gunicorn with Uvicorn workers
exec gunicorn -k uvicorn.workers.UvicornWorker -c gunicorn_conf.py app:app