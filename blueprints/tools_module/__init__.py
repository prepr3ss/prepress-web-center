from flask import Blueprint

tools_module_bp = Blueprint('tools_module', __name__, 
                          template_folder='templates',
                          url_prefix='/tools/module')

from . import routes