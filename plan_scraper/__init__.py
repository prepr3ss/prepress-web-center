# Plan Scraper Blueprint
from flask import Blueprint

# Create blueprint
plan_scraper_bp = Blueprint('plan_scraper', __name__, 
                          template_folder='templates',
                          static_folder='static')

# Import routes to avoid circular imports
from . import routes