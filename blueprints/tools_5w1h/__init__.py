# Blueprint factory for tools_5w1h
from flask import Blueprint

tools_5w1h_bp = Blueprint('tools_5w1h', __name__, template_folder='templates', url_prefix='/tools')

from . import routes
