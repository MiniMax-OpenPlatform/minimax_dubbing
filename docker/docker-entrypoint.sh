#!/bin/bash
set -e

echo "============================================"
echo "MiniMax Dubbing - Docker Entrypoint"
echo "============================================"

# Function to wait for a service
wait_for_service() {
    local host=$1
    local port=$2
    local max_attempts=30
    local attempt=1

    echo "Waiting for $host:$port to be ready..."
    while ! nc -z "$host" "$port" 2>/dev/null; do
        if [ $attempt -ge $max_attempts ]; then
            echo "ERROR: $host:$port not ready after $max_attempts attempts"
            return 1
        fi
        echo "Attempt $attempt/$max_attempts: $host:$port not ready yet..."
        sleep 2
        attempt=$((attempt + 1))
    done
    echo "$host:$port is ready!"
}

# Change to app directory
cd /app

echo ""
echo "Step 1: Checking database..."
echo "--------------------------------------------"
# Check if database exists
if [ ! -f "/app/db.sqlite3" ]; then
    echo "Database not found, will be created during migration"
else
    echo "Database found: /app/db.sqlite3"
fi

echo ""
echo "Step 2: Running database migrations..."
echo "--------------------------------------------"
python manage.py migrate --noinput

echo ""
echo "Step 3: Collecting static files..."
echo "--------------------------------------------"
python manage.py collectstatic --noinput --clear || true

echo ""
echo "Step 4: Initializing system..."
echo "--------------------------------------------"
# Initialize admin user and system configuration
python manage.py init_system || true

echo ""
echo "Step 5: Setting up cron jobs..."
echo "--------------------------------------------"
# Install cron jobs for data cleanup
python manage.py crontab add || true
python manage.py crontab show || true

echo ""
echo "Step 6: Creating necessary directories..."
echo "--------------------------------------------"
mkdir -p /app/media /app/staticfiles /app/logs
chmod -R 755 /app/media /app/staticfiles /app/logs

echo ""
echo "Step 7: System information..."
echo "--------------------------------------------"
echo "Python version: $(python --version)"
echo "Django version: $(python -c 'import django; print(django.get_version())')"
echo "FFmpeg version: $(ffmpeg -version | head -n 1)"
echo "Nginx version: $(nginx -v 2>&1)"
echo "Working directory: $(pwd)"
echo "Database location: /app/db.sqlite3"
echo "Media directory: /app/media"
echo "Logs directory: /app/logs"

echo ""
echo "Step 8: Checking AI model cache..."
echo "--------------------------------------------"
if [ -d "/root/.cache/torch/hub/checkpoints" ]; then
    echo "AI models cached:"
    ls -lh /root/.cache/torch/hub/checkpoints/ || echo "Cache directory exists but is empty"
else
    echo "No AI models cached yet (will be downloaded on first use)"
fi

echo ""
echo "============================================"
echo "Starting services..."
echo "============================================"
echo "Backend: http://0.0.0.0:5172"
echo "Frontend: http://0.0.0.0:5173"
echo "Admin: http://0.0.0.0:5172/admin/"
echo "Default admin credentials:"
echo "  Username: admin"
echo "  Password: admin123"
echo "============================================"
echo ""

# Execute the main command (supervisord)
exec "$@"
