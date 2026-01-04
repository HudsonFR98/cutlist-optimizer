from flask import Blueprint, request, redirect, url_for, session
from flask_babel import get_locale

i18n = Blueprint('i18n', __name__)


@i18n.route('/language/<language>')
def set_language(language):
    """Set the language for the current session"""
    session['language'] = language
    return redirect(request.referrer or url_for('dashboard.home'))


@i18n.route('/language')
def get_current_language():
    """Get the current language"""
    return str(get_locale()) 