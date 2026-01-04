import logging

from flask import Blueprint, render_template
from cutlist_optimizer.lib.flask_util import login_required

doc = Blueprint('doc', __name__)
log = logging.getLogger(__name__)


@doc.route('')
@login_required
def index():
    """Documentation home page - provides information about the application"""
    return render_template('doc/index.html')
