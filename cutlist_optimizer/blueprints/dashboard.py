import logging

from flask import Blueprint, render_template
from cutlist_optimizer.lib.flask_util import login_required

dashboard = Blueprint('dashboard', __name__)
log = logging.getLogger(__name__)

@dashboard.route('/home')
@login_required
def home():
    """Dashboard home page - the default landing page after login"""
    return render_template('dashboard/home.html')