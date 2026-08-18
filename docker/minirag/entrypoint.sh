#!/bin/bash
set -e

cd /app/models/db_schemes/minirag/
alembic upgrade head
cd /app

exec "$@"