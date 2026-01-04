CUTLIST_OPTIMIZER
============================


# Technical documentation for the Cutlist Optimizer Application

The application's CI/CD pipeline is organized through GitLab CI/CD, with distinct stages for different environments. Here's a step-by-step breakdown of how it works:

## Development Setup

### Prerequisites
- Docker and Docker Compose installed
- Git

### Renaming the Application (For New Projects)

If you're starting a new project based on this template, you'll want to rename the application to reflect your project's name. Use the provided rename script:

```bash
./rename_app.sh
```

The script will prompt you for:
- **Old names**: The current template names (e.g., `cutopt`, `cutlist-optimizer`)
- **New names**: Your desired project names (e.g., `myapp`, `my-awesome-application`)

The script automatically handles all name variations:
- Short name: `cutopt` → `myapp`
- Full name with hyphens: `cutlist-optimizer` → `my-awesome-application`
- Full name with underscores: `cutlist_optimizer` → `my_awesome_application`
- Full name in uppercase: `CUTLIST_OPTIMIZER` → `MY_AWESOME_APPLICATION`
- Full name in title case: `Cutlist Optimizer` → `My Awesome Application`

**Important:** Run this script before making any other changes to the project, as it will rename the entire application structure.

### Quick Start
1. Clone the repository
2. Run the setup script:
   ```bash
   ./setup_dev.sh
   ```
3. Start by building the development environment:
   ```bash
   docker compose up --build
   ```
   If the app is already built, you can simply use:
   ```bash
      docker compose up
   ```
4. Access the application at http://localhost:8080


### Development Environment Details
- **Database**: PostgreSQL 15 on port 5437 (container: `cutopt_db_dev`)
- **Application**: Flask app on port 8080 (container: `cutopt_app_dev`)
- **Redis**: Redis on port 6382 (container: `cutopt_redis_dev`)
- **Network**: `cutopt_network_dev`
- **Logs**: Stored in `./logs/` directory
- **User**: Container runs as UID 1000 for proper file permissions


**Environment variables**:
   - Set in docker-compose.yml for local development
   - Can be overridden with a .env file

**Compatibility Notes**:
   - The docker-compose.yml file uses version 3.8 for compatibility with Docker Compose 2.35.1 and Docker 28.1.1
   - The CI/CD pipeline uses Docker 28.1.1 for building and testing
   - The PostgreSQL container uses the Alpine-based image for better compatibility
   - Both containers have healthchecks configured to ensure proper initialization
   - Volume configurations have been simplified for better compatibility
   - The Ansible deployment scripts install the full set of Docker packages needed for Docker 28.1.1

**Run test in development**
   ```
   docker exec -it cutopt_app_dev bash -c "CUTLIST_OPTIMIZER_CONTEXT=dev DB_IP=cutopt_db_dev /opt/env3/cutlist_optimizer/bin/python cutlist_optimizer/tests/run_tests.py"
   ```

### Resetting Development Database or Changing Database Password
If you need to reset all development data (for example, after changing the database password or to start with a clean database):

1. **Stop and remove all containers and volumes:**
   ```bash
   docker compose down -v --remove-orphans
   ```
   This will delete all data in your development database. **Make sure to back up any important data first!**

2. **Rebuild and start the containers:**
   ```bash
   docker compose up --build
   ```
   This will recreate the database with the new password and initialize it with the default data.

**Note:**
- The database password is set in `docker-compose.yml` under the `POSTGRES_PASSWORD` environment variable for the `db` service.
- The application and all configuration files must use the same password as set in the database container.
- If you change the password, update it everywhere (see `docker-compose.yml`, `.gitlab-ci.yml`, `cutlist_optimizer/lib/_config.py`, and deployment scripts).

### Restoring Database from Backup
If you need to restore your development database from a backup file in the `backups` directory:

1. **Stop your application container to prevent data corruption:**
   ```bash
   docker compose stop app
   ```

2. **Stop and remove the database container:**
   ```bash
   docker compose stop db
   docker compose rm -f db
   ```

3. **Remove the database volume to ensure a clean restore:**
   ```bash
   docker volume rm cutlist-optimizer_postgres_data
   ```

4. **Start the database container fresh:**
   ```bash
   docker compose up -d db
   ```

5. **Wait for the database to be ready (check health status):**
   ```bash
   docker compose ps db
   ```

6. **Restore from your chosen backup file. For example, to restore from the most recent backup:**
   ```bash
   docker exec -i cutopt_db_dev psql -U web -d cutopt < backups/cutopt_backup_YYYYMMDD_HHMMSS.sql
   ```

   Or if you want to restore to the `postgres` database (which is the default):
   ```bash
   docker exec -i cutopt_db_dev psql -U web -d postgres < backups/cutopt_backup_YYYYMMDD_HHMMSS.sql
   ```

7. **Start your application container:**
   ```bash
   docker compose up -d app
   ```


## Testing

The application uses a consolidated testing approach with organized, easily editable test data.

Test data is organized in the `cutlist_optimizer/tests/fixtures/` directory

### Test Runner

The consolidated test runner (`run_tests.py`) handles:
- Permission issues by using temporary directories
- Environment variable setup
- Coverage reporting
- Cleanup after execution

## 1. GitLab CI/CD Pipeline Structure

The pipeline is defined in `.gitlab-ci.yml` and consists of six stages:

1. **Install**: Sets up the test environment
2. **Test**: Runs tests and code quality checks
3. **Build**: Creates a distributable package
4. **Docker**: Builds and pushes Docker images
5. **Demo**: Deploys to the demo/staging environment (manual trigger)
6. **Prod**: Deploys to the production environment (manual trigger)

## 2. Environment Configuration

The application uses environment variables to determine which configuration to use:

- `CUTLIST_OPTIMIZER_CONTEXT`: Specifies the environment (dev, test, demo, prod)
- `DB_IP`: Required for dev and test environments to specify the database IP

These configurations are defined in `cutlist_optimizer/lib/_config.py` with specific classes for each environment:

### DEV Environment
- **Purpose**: Local development
- **Configuration**: `DevConfig` class
- **Database**: Uses a local database specified by `DB_IP` environment variable (defaults to `cutopt_db_dev`)
- **Run Command**: `docker compose up --build`
- **Deployment**: Docker containers with volume mounts for development

### PROD Environment
- **Purpose**: Production deployment
- **Configuration**: `ProdConfig` class
- **Database**: Uses a prod database (`cutopt`) on the `cutopt_db_prod` container
- **Deployment**:
  - Triggered manually in GitLab CI
  - Uses Ansible to deploy Docker containers to `nath-server.local` server
  - Accessible at `http://nath-server.local`
  - Uses Docker for process management

## 3. Deployment Process

The deployment process is handled by several scripts:

1. **GitLab CI** triggers the deployment through the `.gitlab-ci.yml` file
2. **Ansible** (`deploy/ansible/*.yml`) is used to:
   - Install Docker on the target server
   - Pull the Docker image from the GitLab Container Registry
   - Run the Docker container with appropriate environment variables and volume mounts

3. **Docker** containers handle:
   - Application execution
   - Database migrations
   - Nginx configuration
   - Process management

## 4. Environment-Specific Configurations

Each environment has specific configurations for:

- **Docker**: Different environment variables and volume mounts
- **Database Connections**: Different database URIs in the config classes
- **Installation Process**: Different installation methods based on environment

## 5. Update Process

Updates to existing installations are handled by:
- The Ansible playbooks with conditional logic based on action type
- Dedicated GitLab CI jobs (`update_demo` and `update_prod`)
- Preserves existing database containers and data during updates

This comprehensive CI/CD setup ensures that code is properly tested before being deployed to staging and production environments, with appropriate controls and environment-specific configurations at each stage.


## Nginx Setup (Test, Demo and Production)

The test, demo, and production environments now use a modern Nginx reverse proxy:

### Architecture
- **Nginx Container**: Handles HTTP traffic on port 80 (e.g., `cutopt_nginx_test`)
- **Application Container**: Runs Gunicorn on internal port 8084 (not exposed externally) (e.g., `cutopt_app_test`)
- **Database Container**: PostgreSQL 15 on internal port 5437 (e.g., `cutopt_db_test`)
- **Redis Container**: Redis cache on internal port 6379 (e.g., `cutopt_redis_test`)
- **Network**: Isolated Docker network per environment (e.g., `cutopt_network_test`)

### Features
- **Modern Security Headers**: X-Frame-Options, X-Content-Type-Options, X-XSS-Protection
- **Static File Serving**: Flask application serves static files (CSS, JS, images)
- **Health Checks**: Built-in health check endpoints
- **Clean Proxy Configuration**: Proper forwarding of headers and protocols

### Access URLs
- **Production**: http://nath-server.local

### Configuration Files
- **Test**: `deploy/nginx_test.conf`
- **Demo**: `deploy/nginx_demo.conf`
- **Production**: `deploy/nginx_prod.conf`

### Session Security
Test, demo, and production environments use standard HTTP session cookies:
- `SESSION_COOKIE_SECURE = False` (HTTP compatible)
- `SESSION_COOKIE_HTTPONLY = True` (No JavaScript access)
- `SESSION_COOKIE_SAMESITE = 'Lax'` (CSRF protection)

**Note**: HTTPS and SSL certificates can be added later by re-enabling the certbot steps in the Ansible deployment and updating the Nginx configurations.

## Internationalization (i18n) Support

The application now supports internationalization with English and French translations. Users can switch between languages using the language selector in the navigation bar.

### Translation Management

The application uses Flask-Babel for internationalization. Translation files are located in `cutlist_optimizer/translations/`.

#### Adding New Translations

When you add new translatable strings to the application:

1. **Mark strings for translation** in your Python code:
   ```python
   from flask_babel import gettext as _
   
   message = _('Your translatable string')
   ```

2. **Mark strings for translation** in your Jinja2 templates:
   ```html
   <h1>{{ _('Welcome to the Dashboard') }}</h1>
   ```

3. **Extract translatable strings**:
   ```bash
   python manage_translations.py extract
   ```

4. **Update existing translation files**:
   ```bash
   python manage_translations.py update
   ```

5. **Edit the translation files**:
   - English: `cutlist_optimizer/translations/en/LC_MESSAGES/messages.po`
   - French: `cutlist_optimizer/translations/fr/LC_MESSAGES/messages.po`

6. **Compile the translations**:
   ```bash
   python manage_translations.py compile
   ```

#### Adding a New Language

To add support for a new language (e.g., Spanish):

1. **Initialize the new language**:
   ```bash
   python manage_translations.py init es
   ```

2. **Add the language to the configuration** in `cutlist_optimizer/lib/_config.py`:
   ```python
   LANGUAGES = {
       'en': 'English',
       'fr': 'Français',
       'es': 'Español'
   }
   ```

3. **Add the language to the navbar** in `cutlist_optimizer/templates/base.html`:
   ```html
   <a class="dropdown-item" href="{{ url_for('i18n.set_language', language='es') }}">Español</a>
   ```

4. **Translate the strings** in `cutlist_optimizer/translations/es/LC_MESSAGES/messages.po`

5. **Compile the translations**:
   ```bash
   python manage_translations.py compile
   ```

#### Translation Management Script

The `manage_translations.py` script provides convenient commands for translation management:

- `python manage_translations.py extract` - Extract translatable strings
- `python manage_translations.py update` - Update existing translation files
- `python manage_translations.py compile` - Compile all translation files
- `python manage_translations.py init <lang>` - Initialize new language
- `python manage_translations.py all` - Run extract, update, and compile

#### Translation Workflow

1. **Development**: Add translatable strings using `_()` function
2. **Extraction**: Run `python manage_translations.py extract` to create/update `messages.pot`
3. **Update**: Run `python manage_translations.py update` to update existing `.po` files
4. **Translation**: Edit the `.po` files with translations
5. **Compilation**: Run `python manage_translations.py compile` to create `.mo` files
6. **Testing**: Test the translations in the application

### Current Supported Languages

- **English (en)**: Default language
- **French (fr)**: Full translation available
