from flask import Blueprint

# Create blueprint with hyphen in URL prefix (without /impact/ since reverse proxy adds it)
calibration_references_bp = Blueprint(
    'calibration_references',
    __name__,
    template_folder='templates',
    url_prefix='/calibration-references'
)