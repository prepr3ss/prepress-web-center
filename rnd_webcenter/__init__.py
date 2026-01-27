from flask import Blueprint

# Create Blueprint for RND WebCenter
rnd_webcenter_bp = Blueprint('rnd_webcenter', __name__, 
                          url_prefix='/rnd-webcenter',
                          template_folder='templates',
                          static_folder='static')

# Import routes to register them with blueprint
from . import routes
