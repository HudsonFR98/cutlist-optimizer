# Database Migrations in a Containerized Environment

This document explains how to manage database migrations for the Nath Standalone Flask Template application when running in Docker containers.

## Understanding Alembic Migrations

The application uses Alembic for database migrations. Alembic tracks changes to your SQLAlchemy models and generates migration scripts to update the database schema accordingly.

## Generating New Migrations

When you make changes to your models (add/modify/remove tables, columns, etc.), you need to generate a new migration script. Here's how to do it in a containerized environment:

1. Connect to the running application container:
   ```bash
   docker exec -it nsft_app_dev bash
   ```

2. Navigate to the application directory:
   ```bash
   cd /opt/nath-standalone-flask-template
   ```

3. Generate a new migration script:
   ```bash
   NATH_STANDALONE_FLASK_TEMPLATE_CONTEXT=dev DB_IP=nsft_db_dev alembic revision --autogenerate -m "Description of your changes"
   ```

   This command will:
   - Set the necessary environment variables
   - Generate a new migration script in the `alembic/versions` directory
   - The script will include SQL commands to make the necessary changes to the database

4. Review the generated migration script to ensure it correctly captures your changes.

## Applying Migrations

Migrations are automatically applied when the application container starts, thanks to the `docker-entrypoint.sh` script. However, if you need to apply migrations manually:

1. Connect to the running application container:
   ```bash
   docker exec -it nsft_app_dev bash
   ```

2. Navigate to the application directory:
   ```bash
   cd /opt/nath-standalone-flask-template
   ```

3. Apply all pending migrations:
   ```bash
   NATH_STANDALONE_FLASK_TEMPLATE_CONTEXT=dev DB_IP=nsft_db_dev alembic upgrade head
   ```

## Initial Database Setup

When the application is first built and the database is newly created, the following happens:

1. The database container initializes with an empty database
2. The application container starts and runs the migrations
3. If no users exist in the database, an admin user is automatically created with:
   - Username: `admin`
   - Password: `admin`
   - Roles: `admin` (with all permissions)

You should change the admin password after the first login for security reasons.

## Troubleshooting

If you encounter issues with migrations:

1. Check the application logs:
   ```bash
   docker logs nsft_app_dev
   ```

2. Ensure the database container is running and accessible:
   ```bash
   docker ps
   ```

3. Verify the database connection settings in your configuration files.

4. If migrations fail, you can try to run them manually with more verbose output:
   ```bash
   docker exec -it nsft_app_dev bash
   cd /opt/nath-standalone-flask-template
   NATH_STANDALONE_FLASK_TEMPLATE_CONTEXT=dev DB_IP=nsft_db_dev alembic upgrade head --verbose
   ```

## Best Practices

1. Always back up your database before applying migrations in production
2. Test migrations in a development or staging environment first
3. Include migration scripts in your version control system
4. Document significant schema changes in the migration script descriptions
5. Consider the impact of migrations on existing data