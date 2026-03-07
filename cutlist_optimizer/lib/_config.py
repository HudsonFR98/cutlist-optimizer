import os
import logging
import tempfile

from logging.config import dictConfig

"""
Configuration module for cutlist_optimizer application.

Deployment Architecture:
- DEV: Uses external database specified by DB_IP environment variable
- TEST/DEMO/PROD: Use Docker containers with local PostgreSQL databases
  - Database container name: 'cutopt_db_{context}' (e.g., 'cutopt_db_test', 'cutopt_db_demo', 'cutopt_db_prod')
  - Database name: 'cutopt'
  - All environments accessible on port 8080
  - Deploy vs Update operations supported (data preservation during updates)

Environment Variables:
- CUTLIST_OPTIMIZER_CONTEXT: Required for all environments (dev, test, demo, prod)
- DB_IP: Required in all contexts

Session Security:
- All environments currently configured for HTTP (SESSION_COOKIE_SECURE = False)
- When HTTPS is enabled, update SESSION_COOKIE_SECURE to True in respective configs
- SESSION_COOKIE_SAMESITE set to 'Lax' for HTTP compatibility
"""


def setup_logging():
    """Set up logging configuration with proper error handling."""
    log_dir = '/var/log/cutlist_optimizer'
    log_file = os.path.join(log_dir, 'cutlist_optimizer.log')

    # Ensure log directory exists and is writable
    try:
        os.makedirs(log_dir, exist_ok=True)
        test_file = os.path.join(log_dir, '.test_write')
        with open(test_file, 'w') as f:
            f.write('test')
        os.remove(test_file)
        use_file_handler = True
    except (OSError, PermissionError):
        use_file_handler = False
        log_file = os.path.join(tempfile.gettempdir(), 'cutlist_optimizer.log')

    config = {
        'version': 1,
        'formatters': {'default': {
            'format': '[%(asctime)s] %(levelname)s in %(module)s: %(message)s',
        }},
        'handlers': {
            'console': {
                'level': 'DEBUG',
                'formatter': 'default',
                'class': 'logging.StreamHandler',
            },
        },
        'loggers': {
            'cutlist_optimizer': {
                'handlers': ['console'],
                'level': 'DEBUG',
                'propagate': False
            },
            'sqlalchemy.engine': {
                'handlers': ['console'],
                'level': 'WARNING',
                'propagate': False
            },
        }
    }

    if use_file_handler:
        config['handlers']['file'] = {
            'level': 'DEBUG',
            'formatter': 'default',
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': log_file,
            'mode': 'a',
            'maxBytes': 5000000,
            'backupCount': 10,
        }
        config['loggers']['cutlist_optimizer']['handlers'].append('file')
        config['loggers']['sqlalchemy.engine']['handlers'].append('file')

    try:
        dictConfig(config)
    except Exception as e:
        logging.basicConfig(
            level=logging.DEBUG,
            format='[%(asctime)s] %(levelname)s in %(module)s: %(message)s'
        )
        logging.warning(f"Failed to configure logging: {e}")


setup_logging()


def require_env(name: str) -> str:
    """Return a required environment variable or raise a clear error."""
    value = os.environ.get(name)
    if value is None or str(value).strip() == "":
        raise RuntimeError(f"La variable d'environnement {name} n'est pas renseignee")
    return value


def build_db_uri() -> str:
    """Build SQLAlchemy DB URI from required env vars."""
    host = require_env("DB_IP")
    user = require_env("POSTGRES_USER")
    password = require_env("POSTGRES_PASSWORD")
    db_name = require_env("CUTOPT_DB_NAME")
    return f"postgresql://{user}:{password}@{host}/{db_name}"


class Config(object):
    """Base configuration class."""

    EMAIL_DEV = 'natha.debanne@gmail.com'
    SETTINGS = None
    STATIC_URI = '/static'
    SECRET_KEY = require_env("SECRET_KEY")

    TELEGRAM_BOT_TOKEN = require_env("TELEGRAM_BOT_TOKEN")
    TELEGRAM_CHAT_ID = require_env("TELEGRAM_CHAT_ID")

    ADMIN_USER_USERNAME = require_env("ADMIN_USER_USERNAME")
    ADMIN_USER_PASSWORD = require_env("ADMIN_USER_PASSWORD")
    ADMIN_USER_FIRST_NAME = require_env("ADMIN_USER_FIRST_NAME")
    ADMIN_USER_LAST_NAME = require_env("ADMIN_USER_LAST_NAME")
    ADMIN_USER_EMAIL = require_env("ADMIN_USER_EMAIL")

    DB_URI = build_db_uri()
    SQLALCHEMY_DATABASE_URI = DB_URI
    APP_NAME = 'Cutlist Optimizer'

    ERROR_EMAIL_FROM = ''
    ERROR_EMAIL_TO = EMAIL_DEV
    ERROR_EMAIL_SMTP_SERVER = ''
    ERROR_EMAIL_SMTP_USER = ''
    ERROR_EMAIL_SMTP_PASSWORD = ''
    ERROR_EMAIL_SMTP_PORT = 587

    SESSION_COOKIE_SECURE = False
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    REMEMBER_COOKIE_SECURE = False
    REMEMBER_COOKIE_HTTPONLY = True
    REMEMBER_COOKIE_SAMESITE = 'Lax'
    WTF_CSRF_ENABLED = True
    WTF_CSRF_TIME_LIMIT = 3600

    BABEL_DEFAULT_LOCALE = 'en'
    BABEL_DEFAULT_TIMEZONE = 'UTC'
    BABEL_TRANSLATION_DIRECTORIES = 'translations'
    LANGUAGES = {
        'en': 'English',
        'fr': 'Français'
    }

    DOC_DIR = '/opt/cutlist_optimizer_docs'
    BASE_URL = 'http://localhost:8080'


class ProdConfig(Config):
    CONTEXT = 'prod'
    LOG_LEVEL = logging.ERROR
    SESSION_COOKIE_SECURE = True
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    REMEMBER_COOKIE_SECURE = True
    REMEMBER_COOKIE_HTTPONLY = True
    REMEMBER_COOKIE_SAMESITE = 'Lax'
    PREFERRED_URL_SCHEME = 'https'


class DevConfig(Config):
    CONTEXT = 'dev'
    DEBUG = True
    TESTING = False
    LOG_LEVEL = logging.DEBUG
    PRESERVE_CONTEXT_ON_EXCEPTION = False
    DEBUG_TB_ENABLED = True
    DEBUG_TB_INTERCEPT_REDIRECTS = False
    SESSION_COOKIE_SECURE = False
    SESSION_COOKIE_HTTPONLY = False
    SESSION_COOKIE_SAMESITE = 'Lax'


class DemoConfig(Config):
    CONTEXT = 'demo'
    LOG_LEVEL = logging.ERROR
    SESSION_COOKIE_SECURE = False
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'


class TestConfig(Config):
    CONTEXT = 'test'
    TESTING = True
    LOG_LEVEL = logging.ERROR
    SERVER_NAME = 'localhost'
    SESSION_COOKIE_SECURE = False
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'


require_env("CUTLIST_OPTIMIZER_CONTEXT")
require_env("DB_IP")


_envs = dict(
    test=TestConfig,
    dev=DevConfig,
    demo=DemoConfig,
    prod=ProdConfig
)
config = _envs[os.environ['CUTLIST_OPTIMIZER_CONTEXT']]
