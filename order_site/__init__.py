# order_site/__init__.py
from flask import Blueprint

order_bp = Blueprint('orders', __name__, template_folder='templates')

from . import routes