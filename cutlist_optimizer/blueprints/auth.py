import logging

from flask import redirect, url_for, request, Blueprint, render_template
from flask import make_response, g, flash
from flask_login import login_user, logout_user, login_required, current_user

from cutlist_optimizer.lib import config
from cutlist_optimizer.models import User

auth = Blueprint('auth', __name__)
log = logging.getLogger(__name__)


@auth.route('/', methods=['GET', 'POST'])
@auth.route('/login', methods=['GET', 'POST'])
def login():
    """Handle user login"""
    # Redirect if user is already logged in
    if current_user.is_authenticated:
        return redirect(url_for('dashboard.home'))

    if request.method == 'POST':
        try:
            user = User.authenticate(request.form['USR'], request.form['PWD'])
            if user and user.is_active():
                login_user(user, remember=True)
                log.debug(f"User logged in successfully: {user.ide}")
                response = make_response(redirect(url_for("dashboard.home")))
                response.set_cookie('nath_signature', value='signed !!')
                return response
            else:
                flash('User account is inactive', 'error')
        except Exception as e:
            log.warning(f"Authentication failed: {e}")
            if config.CONTEXT == 'dev':
                flash(str(e), 'error')
            else:
                flash('Invalid username or password', 'error')

    return render_template('login.html')


@auth.route('/logout')
@login_required
def logout():
    """Handle user logout"""
    logout_user()
    flash('Please sign in again')
    response = make_response(redirect(url_for('.login')))
    response.delete_cookie('nath_signature')
    return response


@auth.route('/test-session')
@login_required
def test_session():
    """Test route to verify session functionality"""
    log.debug(f"Test session route - Current user: {current_user.ide if current_user else 'None'}")
    
    if current_user.is_authenticated:
        return f"Session working! User: {current_user.ide}, User ID: {current_user.id}"
    else:
        return "No user in session"
