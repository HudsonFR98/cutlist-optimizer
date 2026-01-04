#!/bin/bash
set -e

# Function to run as web user (only if we're not already web user)
run_as_web() {
    if [ "$(id -u)" = "1000" ]; then
        # We're already running as web user
        eval "$1"
    else
        # Switch to web user
        su - web -c "$1"
    fi
}

# Get database host from environment variable, default to 'db' for backward compatibility
DB_HOST="${DB_IP:-db}"

# Wait for the cutopt database to be ready
echo "Waiting for cutopt database to be ready on ${DB_HOST}..."
max_retries=30
retries=0
while [ $retries -lt $max_retries ]; do
    if PGPASSWORD=cutopt2025_x psql -h "${DB_HOST}" -U web -d cutopt -c "SELECT 1" > /dev/null 2>&1; then
        echo "Database cutopt is ready!"
        break
    fi
    retries=$((retries+1))
    echo "Database cutopt not ready yet, retrying... ($retries/$max_retries)"
    sleep 2
done

if [ $retries -eq $max_retries ]; then
    echo "Error: Maximum retries reached. Database cutopt is not available on ${DB_HOST}."
    echo "Checking database container status..."
    docker ps | grep "${DB_HOST}" || echo "No container found with name ${DB_HOST}"
    echo "Checking database logs..."
    docker logs "${DB_HOST}" 2>/dev/null || echo "Could not get logs for ${DB_HOST}"
    exit 1
fi

# Install requirements and run database migrations
echo "Setting up application..."
run_as_web "cd /opt/cutlist_optimizer && \
    CUTLIST_OPTIMIZER_CONTEXT=$CUTLIST_OPTIMIZER_CONTEXT \
    DB_IP=${DB_HOST} \
    /opt/env3/cutlist_optimizer/bin/pip install -r deploy/requirements.txt && \
    /opt/env3/cutlist_optimizer/bin/alembic upgrade head"


# Determine which server to use based on context
if [ "$CUTLIST_OPTIMIZER_CONTEXT" = "dev" ]; then
    echo "Starting Flask development server with hot reloading..."
    # Use Flask development server for hot reloading in dev mode
    exec /opt/env3/cutlist_optimizer/bin/python cutlist_optimizer_app.py
else
    echo "Starting Gunicorn production server..."
    # Use Gunicorn for production/demo/test modes
    exec /opt/env3/cutlist_optimizer/bin/gunicorn --bind 0.0.0.0:8080 --log-level=debug --capture-output --enable-stdio-inheritance cutlist_optimizer_app:app
fi
