#!/bin/bash
set -e

exec gunicorn -k uvicorn.workers.UvicornWorker -c gunicorn_conf.py app:app