""" webservices """

import logging
import json
import string

from flask import request, Blueprint, abort, jsonify
from cutlist_optimizer import dao


rest = Blueprint('rest', __name__)
log = logging.getLogger(__name__)


# @rest.route('/test', methods=["GET"])
# def get_test():
#     """ Exemple """

#     gene_id = request.values.get('gene_id')
#     gene = dao.get_gene(gene_id)
#     return jsonify(gene.to_json())
