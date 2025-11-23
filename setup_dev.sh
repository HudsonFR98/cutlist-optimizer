#!/bin/bash
set -e

echo "Setting up development environment..."

# Set ownership to match the container user (UID 1000)
if command -v sudo >/dev/null 2>&1; then
    sudo mkdir -p /var/log/nath_standalone_flask_template
    sudo chmod 775 /var/log/nath_standalone_flask_template
    sudo chown -R 1000:1000 /var/log/nath_standalone_flask_template
    
    # Backups directory
    sudo mkdir -p /var/backups/nath_standalone_flask_template
    sudo chmod 775 /var/backups/nath_standalone_flask_template
    sudo chown -R 1000:1000 /var/backups/nath_standalone_flask_template
    
    # Database data directory (PostgreSQL 15)
    sudo mkdir -p /opt/nath_standalone_flask_template_data/postgresql/15/main
    sudo chmod 775 /opt/nath_standalone_flask_template_data/postgresql/15/main
    sudo chown -R 1000:1000 /opt/nath_standalone_flask_template_data/postgresql/15/main  # PostgreSQL uses UID 999
    
    # Create log file
    sudo touch /var/log/nath_standalone_flask_template/nath_standalone_flask_template.log
    sudo chmod 664 /var/log/nath_standalone_flask_template/nath_standalone_flask_template.log
    sudo chown 1000:1000 /var/log/nath_standalone_flask_template/nath_standalone_flask_template.log

else
    echo "Warning: sudo not available, you may need to create directories manually"
    echo "Run the following commands with appropriate permissions:"
    echo "  mkdir -p /var/log/nath_standalone_flask_template"
    echo "  mkdir -p /var/backups/nath_standalone_flask_template"
    echo "  mkdir -p /opt/nath_standalone_flask_template_data/postgresql/15/main"
    echo "  chown -R 1000:1000 /var/log/nath_standalone_flask_template"
    echo "  chown -R 1000:1000 /var/backups/nath_standalone_flask_template"
    echo "  chown -R 999:999 /opt/nath_standalone_flask_template_data/postgresql/15/main"
fi

echo "Development environment setup complete!"
echo "You can now run: docker compose up --build" 