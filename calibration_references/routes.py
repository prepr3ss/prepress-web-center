from flask import (
    render_template, redirect, url_for, request, jsonify, 
    flash, current_app, abort
)
from werkzeug.utils import secure_filename
import os
from flask_login import login_required, current_user
from . import calibration_references_bp
from .forms import CalibrationReferenceForm
from models import db, CalibrationReference
from functools import wraps

def admin_required(f):
    """Decorator to require admin role"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_admin():
            flash('You do not have permission to access this page.', 'danger')
            return redirect(url_for('index'))
        return f(*args, **kwargs)
    return decorated_function

def validate_standard(standard):
    """Validate calibration standard parameter"""
    valid_standards = ['g7', 'iso', 'existing', 'nestle', 'gmi']
    if standard.lower() not in valid_standards:
        abort(404, description="Invalid calibration standard")
    return standard.upper()

@calibration_references_bp.route('/<standard>/')
@login_required
@admin_required
def standard_list(standard):
    """Standard-specific listing page for calibration references"""
    current_app.logger.info(f"standard_list called with parameter: '{standard}'")
    validated_standard = validate_standard(standard)
    current_app.logger.info(f"validated_standard: '{validated_standard}'")
    return render_template('calibration_references/calibration_modern_table.html',
                         standard=validated_standard)

@calibration_references_bp.route('/')
@login_required
@admin_required
def index():
    """Main listing page for calibration references - redirect to G7"""
    return redirect(url_for('calibration_references.standard_list', standard='g7'))

@calibration_references_bp.route('/<standard>/create', methods=['GET', 'POST'])
@login_required
@admin_required
def standard_create(standard):
    """Create calibration reference for specific standard"""
    validated_standard = validate_standard(standard)
    form = CalibrationReferenceForm()
    
    # Pre-select the calibration standard
    form.calib_standard.data = validated_standard
    
    if form.validate_on_submit():
        try:
            # Create new calibration reference
            calibration_ref = CalibrationReference(
                print_machine=form.print_machine.data,
                calib_group=form.calib_group.data,
                calib_code=form.calib_code.data,
                calib_name=form.calib_name.data,
                paper_type=form.paper_type.data,
                ink_type=form.ink_type.data,
                calib_standard=form.calib_standard.data,
                c20=form.c20.data,
                c25=form.c25.data,
                c40=form.c40.data,
                c50=form.c50.data,
                c75=form.c75.data,
                c80=form.c80.data,
                m20=form.m20.data,
                m25=form.m25.data,
                m40=form.m40.data,
                m50=form.m50.data,
                m75=form.m75.data,
                m80=form.m80.data,
                y20=form.y20.data,
                y25=form.y25.data,
                y40=form.y40.data,
                y50=form.y50.data,
                y75=form.y75.data,
                y80=form.y80.data,
                k20=form.k20.data,
                k25=form.k25.data,
                k40=form.k40.data,
                k50=form.k50.data,
                k75=form.k75.data,
                k80=form.k80.data
            )
            
            db.session.add(calibration_ref)
            db.session.commit()
            
            flash('Calibration reference created successfully!', 'success')
            return redirect(url_for('calibration_references.standard_list', standard=standard.lower()))
            
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Error creating calibration reference: {str(e)}")
            flash('An error occurred while creating calibration reference.', 'danger')
    
    return render_template('calibration_references/calibration_references_create.html',
                         form=form, action='Create', standard=validated_standard)

@calibration_references_bp.route('/<standard>/edit/<int:id>', methods=['GET', 'POST'])
@login_required
@admin_required
def standard_edit(standard, id):
    """Edit calibration reference for specific standard"""
    validated_standard = validate_standard(standard)
    calibration_ref = CalibrationReference.query.get_or_404(id)
    
    # Validate that the calibration reference belongs to the specified standard
    if calibration_ref.calib_standard != validated_standard:
        abort(404, description="Calibration reference not found in this standard")
    
    form = CalibrationReferenceForm(obj=calibration_ref)
    
    if form.validate_on_submit():
        try:
            # Update calibration reference
            form.populate_obj(calibration_ref)
            db.session.commit()
            
            flash('Calibration reference updated successfully!', 'success')
            return redirect(url_for('calibration_references.standard_list', standard=standard.lower()))
            
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Error updating calibration reference: {str(e)}")
            flash('An error occurred while updating calibration reference.', 'danger')
    
    return render_template('calibration_references/calibration_references_create.html',
                         form=form, action='Edit', calibration_ref=calibration_ref, standard=validated_standard)



@calibration_references_bp.route('/api/data')
@login_required
@admin_required
def get_data():
    """API endpoint for DataTable and other views"""
    try:
        # Get parameters
        draw = request.args.get('draw', type=int)
        start = request.args.get('start', type=int, default=0)
        length = request.args.get('length', type=int, default=10)
        search = request.args.get('search[value]', '', type=str)
        all_data = request.args.get('all', 'false', type=str).lower() == 'true'
        standard = request.args.get('standard', '', type=str)
        
        # Build query
        query = CalibrationReference.query
        
        # Apply standard filter if provided
        if standard:
            query = query.filter_by(calib_standard=standard.upper())
            current_app.logger.info(f"Filtering by standard: {standard.upper()}")
        else:
            current_app.logger.info("No standard filter applied")
        
        # Apply search filter
        if search:
            query = query.filter(
                db.or_(
                    CalibrationReference.calib_code.ilike(f'%{search}%'),
                    CalibrationReference.calib_name.ilike(f'%{search}%'),
                    CalibrationReference.calib_group.ilike(f'%{search}%'),
                    CalibrationReference.print_machine.ilike(f'%{search}%'),
                    CalibrationReference.calib_standard.ilike(f'%{search}%')
                )
            )
        
        # Get total records
        total_records = query.count()
        current_app.logger.info(f"Total records after filtering: {total_records}")
        
        # Apply pagination and ordering (only for DataTable, not for other views)
        if all_data:
            # Get all records for Kanban, Timeline, Masonry, Dashboard views
            records = query.all()
            current_app.logger.info(f"Retrieved {len(records)} records (all_data=true)")
        else:
            # Apply pagination for DataTable
            records = query.offset(start).limit(length).all()
            current_app.logger.info(f"Retrieved {len(records)} records (paginated)")
        
        # Format data for DataTable
        data = []
        for record in records:
            data.append({
                'id': record.id,
                'print_machine': record.print_machine,
                'calib_group': record.calib_group,
                'calib_code': record.calib_code,
                'calib_name': record.calib_name,
                'paper_type': record.paper_type,
                'ink_type': record.ink_type,
                'calib_standard': record.calib_standard,
                'updated_at': record.updated_at.isoformat() if record.updated_at else None,
                'actions': f'''
                    <div class="btn-group" role="group">
                        <a href="{url_for('calibration_references.standard_edit', standard=record.calib_standard.lower(), id=record.id)}"
                           class="btn btn-sm btn-outline-primary" title="Edit">
                            <i class="fas fa-edit"></i>
                        </a>
                        <button type="button"
                                class="btn btn-sm btn-outline-danger"
                                onclick="confirmDelete({record.id}, '{record.calib_code}')"
                                title="Delete">
                            <i class="fas fa-trash"></i>
                        </button>
                    </div>
                '''
            })
        
        return jsonify({
            'draw': draw,
            'recordsTotal': total_records,
            'recordsFiltered': total_records,
            'data': data
        })
        
    except Exception as e:
        current_app.logger.error(f"Error in get_data: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

@calibration_references_bp.route('/api/filter-options')
@login_required
@admin_required
def get_filter_options():
    """API endpoint for filter dropdown options"""
    try:
        # Get unique paper types
        paper_types = db.session.query(CalibrationReference.paper_type)\
            .filter(CalibrationReference.paper_type.isnot(None))\
            .distinct()\
            .all()
        
        # Get unique ink types
        ink_types = db.session.query(CalibrationReference.ink_type)\
            .filter(CalibrationReference.ink_type.isnot(None))\
            .distinct()\
            .all()
        
        # Get unique groups
        groups = db.session.query(CalibrationReference.calib_group)\
            .distinct()\
            .all()
        
        return jsonify({
            'paper_types': [pt[0] for pt in paper_types if pt[0]],
            'ink_types': [it[0] for it in ink_types if it[0]],
            'groups': [g[0] for g in groups if g[0]],
            'calib_standards': ['G7', 'ISO', 'EXISTING']
        })
        
    except Exception as e:
        current_app.logger.error(f"Error in get_filter_options: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

@calibration_references_bp.route('/create', methods=['GET', 'POST'])
@login_required
@admin_required
def create():
    """Create new calibration reference"""
    form = CalibrationReferenceForm()
    
    if form.validate_on_submit():
        try:
            # Create new calibration reference
            calibration_ref = CalibrationReference(
                print_machine=form.print_machine.data,
                calib_group=form.calib_group.data,
                calib_code=form.calib_code.data,
                calib_name=form.calib_name.data,
                paper_type=form.paper_type.data,
                ink_type=form.ink_type.data,
                calib_standard=form.calib_standard.data,
                c20=form.c20.data,
                c25=form.c25.data,
                c40=form.c40.data,
                c50=form.c50.data,
                c75=form.c75.data,
                c80=form.c80.data,
                m20=form.m20.data,
                m25=form.m25.data,
                m40=form.m40.data,
                m50=form.m50.data,
                m75=form.m75.data,
                m80=form.m80.data,
                y20=form.y20.data,
                y25=form.y25.data,
                y40=form.y40.data,
                y50=form.y50.data,
                y75=form.y75.data,
                y80=form.y80.data,
                k20=form.k20.data,
                k25=form.k25.data,
                k40=form.k40.data,
                k50=form.k50.data,
                k75=form.k75.data,
                k80=form.k80.data
            )
            
            db.session.add(calibration_ref)
            db.session.commit()
            
            flash('Calibration reference created successfully!', 'success')
            return redirect(url_for('calibration_references.index'))
            
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Error creating calibration reference: {str(e)}")
            flash('An error occurred while creating calibration reference.', 'danger')
    
    return render_template('calibration_references/calibration_references_create.html', 
                         form=form, action='Create')

@calibration_references_bp.route('/edit/<int:id>', methods=['GET', 'POST'])
@login_required
@admin_required
def edit(id):
    """Edit existing calibration reference"""
    calibration_ref = CalibrationReference.query.get_or_404(id)
    form = CalibrationReferenceForm(obj=calibration_ref)
    
    if form.validate_on_submit():
        try:
            # Update calibration reference
            form.populate_obj(calibration_ref)
            db.session.commit()
            
            flash('Calibration reference updated successfully!', 'success')
            return redirect(url_for('calibration_references.index'))
            
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Error updating calibration reference: {str(e)}")
            flash('An error occurred while updating calibration reference.', 'danger')
    
    return render_template('calibration_references/calibration_references_create.html', 
                         form=form, action='Edit', calibration_ref=calibration_ref)

@calibration_references_bp.route('/delete/<int:id>', methods=['POST'])
@login_required
@admin_required
def delete(id):
    """Delete calibration reference"""
    try:
        calibration_ref = CalibrationReference.query.get_or_404(id)
        standard = calibration_ref.calib_standard.lower() if calibration_ref.calib_standard else 'g7'
        db.session.delete(calibration_ref)
        db.session.commit()
        
        flash('Calibration reference deleted successfully!', 'success')
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error deleting calibration reference: {str(e)}")
        flash('An error occurred while deleting calibration reference.', 'danger')
    
    return redirect(url_for('calibration_references.standard_list', standard=standard))

@calibration_references_bp.route('/import-parse', methods=['POST'])
@login_required
@admin_required
def import_parse():
    """Parse Prinect Manager file for import (future enhancement)"""
    try:
        if 'file' not in request.files:
            return jsonify({'error': 'No file provided'}), 400
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400
        
        if not file.filename.lower().endswith('.txt'):
            return jsonify({'error': 'Invalid file format. Please select a .txt file.'}), 400
        
        # Read file content
        content = file.read().decode('utf-8')
        
        # Parse calibration data (same logic as frontend)
        calibration_data = parse_prinect_content(content)
        
        if not calibration_data:
            return jsonify({'error': 'Invalid file format. Please ensure this is a valid Prinect Manager export file.'}), 400
        
        return jsonify({
            'success': True,
            'data': calibration_data,
            'filename': file.filename
        })
        
    except Exception as e:
        current_app.logger.error(f"Error parsing import file: {str(e)}")
        return jsonify({'error': f'Failed to parse file: {str(e)}'}), 500

def parse_prinect_content(content):
    """Parse Prinect Manager file content and extract calibration data"""
    lines = content.split('\n')
    calibration_data = {
        'cyan': {},
        'magenta': {},
        'yellow': {},
        'black': {}
    }
    
    def parse_calibration_line(line, color_data, prefix):
        parts = line.split(r'\s+')
        
        if len(parts) >= 6:
            patch_percentage = None
            dot_value = None
            
            # Find the patch percentage and corresponding DOT value
            for i in range(1, 5):
                value = float(parts[i]) if parts[i].replace('.', '').isdigit() else 0
                if value > 0:
                    patch_percentage = value
                    dot_value = float(parts[i + 4])
                    break
            
            if patch_percentage is not None and dot_value is not None:
                tint_key = str(int(patch_percentage))
                color_data[tint_key] = dot_value
    
    # Parse each line looking for calibration data
    for line in lines:
        trimmed_line = line.strip()
        
        if trimmed_line.startswith('"Calibration_C"'):
            parse_calibration_line(trimmed_line, calibration_data['cyan'], 'c')
        elif trimmed_line.startswith('"Calibration_M"'):
            parse_calibration_line(trimmed_line, calibration_data['magenta'], 'm')
        elif trimmed_line.startswith('"Calibration_Y"'):
            parse_calibration_line(trimmed_line, calibration_data['yellow'], 'y')
        elif trimmed_line.startswith('"Calibration_K"'):
            parse_calibration_line(trimmed_line, calibration_data['black'], 'k')
    
    # Validate that we have required data
    required_tints = ['20', '25', '40', '50', '75', '80']
    has_valid_data = False
    
    for color in ['cyan', 'magenta', 'yellow', 'black']:
        for tint in required_tints:
            if tint in calibration_data[color]:
                has_valid_data = True
                break
        if has_valid_data:
            break
    
    if has_valid_data:
        return calibration_data
    else:
        return None