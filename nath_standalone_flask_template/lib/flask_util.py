import logging

from functools import wraps
from flask import g
from flask_login import login_required as flask_login_required, current_user

from nath_standalone_flask_template import dao
from nath_standalone_flask_template.lib.database import DBSession

log = logging.getLogger(__name__)


# Use Flask-Login's login_required decorator
login_required = flask_login_required


def before_request():
    """ launched before each request """

    g.user = current_user
    if current_user.is_authenticated:
        log.debug(f"User authenticated: {current_user.ide}")
        current_user.reload_permissions()


def after_request():
    """ launched after each request """

    DBSession.remove()


def admin_required(f):
    """Decorator to require admin permissions"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            return login_required(f)(*args, **kwargs)
        
        if not current_user.has_permission('admin'):
            from flask import abort
            abort(403)
        
        return f(*args, **kwargs)
    return decorated_function
