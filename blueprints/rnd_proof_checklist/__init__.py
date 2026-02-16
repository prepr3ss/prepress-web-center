from flask import Blueprint

# Create Blueprint for R&D Proof Checklist
rnd_proof_checklist_bp = Blueprint('rnd_proof_checklist', __name__, 
                               url_prefix='/rnd-proof-checklist',
                               template_folder='templates')

# Import routes to register them
from . import routes