#!/bin/bash
set -e

echo "Setting up development environment..."

# Create logs directory with proper permissions
mkdir -p logs
chmod 775 logs
mkdir -p backups
chmod 775 backups
touch logs/nath_standalone_flask_template.log
chmod 664 logs/nath_standalone_flask_template.log

# Set ownership to match the container user (UID 1000)
if command -v sudo >/dev/null 2>&1; then
    sudo chown -R 1000:1000 logs/
    sudo chown -R 1000:1000 backups/
else
    echo "Warning: sudo not available, you may need to set permissions manually"
    echo "Run: chown -R 1000:1000 logs/"
    echo "Run: chown -R 1000:1000 backups/"
fi

echo "Development environment setup complete!"
echo "You can now run: docker compose up --build" 