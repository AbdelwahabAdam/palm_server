#!/bin/bash
set -e

echo "Waiting for PostgreSQL..."
until pg_isready -h "${POSTGRES_HOST:-postgres}" -p "${POSTGRES_PORT:-5432}" -U "${POSTGRES_USER:-palmuser}"; do
  sleep 2
done

echo "Running database migrations..."
cd /app
alembic upgrade head

echo "Tip: run 'python seed_data.py' to create the admin user if needed."

echo "Starting application..."
exec pserve production.ini \
  "DATABASE_URL=${DATABASE_URL}" \
  "SECRET_KEY=${SECRET_KEY}" \
  "S3_BUCKET=${S3_BUCKET}" \
  "AWS_ACCESS_KEY_ID=${AWS_ACCESS_KEY_ID}" \
  "AWS_SECRET_ACCESS_KEY=${AWS_SECRET_ACCESS_KEY}" \
  "AWS_REGION=${AWS_REGION:-us-east-1}" \
  "SMTP_HOST=${SMTP_HOST}" \
  "SMTP_PORT=${SMTP_PORT:-587}" \
  "SMTP_USER=${SMTP_USER}" \
  "SMTP_PASSWORD=${SMTP_PASSWORD}" \
  "SMTP_FROM=${SMTP_FROM:-${SMTP_USER}}" \
  "SMTP_USE_TLS=${SMTP_USE_TLS:-true}" \
  "FRONTEND_URL=${FRONTEND_URL:-http://localhost}"
