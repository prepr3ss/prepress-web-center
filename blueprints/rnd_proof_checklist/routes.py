from flask import render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from models import db, User
from models_proof_checklist import (
    ProofChecklist, MasterPrintMachine, MasterPrintSeparation,
    MasterPrintInk, MasterPostpressMachine,
    ProofChecklistPrintMachine, ProofChecklistPrintSeparation,
    ProofChecklistPrintInk, ProofChecklistPostpressMachine,
    ProofChecklistStatusHistory
)
from datetime import datetime
import pytz
from . import rnd_proof_checklist_bp
from sqlalchemy import or_

# Get Jakarta timezone
jakarta_tz = pytz.timezone('Asia/Jakarta')

def require_rnd_access(f):
    """Decorator to require R&D access"""
    from functools import wraps
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not hasattr(current_user, 'can_access_rnd') or not current_user.can_access_rnd():
            flash('You do not have permission to access R&D Proof Checklist.', 'danger')
            return redirect(url_for('dashboard'))
        return f(*args, **kwargs)
    return decorated_function

@rnd_proof_checklist_bp.route('/')
@login_required
@require_rnd_access
def dashboard():
    """Dashboard for Proof Checklist"""
    # Check if this is an API request (from JavaScript) or regular request
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest' or request.args.get('api'):
        # Handle API request for JavaScript filtering
        return api_checklists()
    else:
        # Handle regular request for initial page load
        page = request.args.get('page', 1, type=int)
        per_page = 20
        search = request.args.get('search', '', type=str)
        status_filter = request.args.get('status', '', type=str)
        date_filter = request.args.get('date_filter', '', type=str)
        
        # Build query
        query = ProofChecklist.query
        
        # Apply search filter
        if search:
            query = query.filter(
                or_(
                    ProofChecklist.customer_name.ilike(f'%{search}%'),
                    ProofChecklist.item_name.ilike(f'%{search}%'),
                    ProofChecklist.paper_supplier.ilike(f'%{search}%')
                )
            )
        
        # Apply status filter
        if status_filter:
            query = query.filter(ProofChecklist.status == status_filter)
        
        # Apply date filter
        if date_filter:
            now = datetime.now(jakarta_tz)
            if date_filter == 'today':
                start_of_day = now.replace(hour=0, minute=0, second=0, microsecond=0)
                query = query.filter(ProofChecklist.created_at >= start_of_day)
            elif date_filter == 'week':
                from datetime import timedelta
                start_of_week = now - timedelta(days=now.weekday())
                start_of_week = start_of_week.replace(hour=0, minute=0, second=0, microsecond=0)
                query = query.filter(ProofChecklist.created_at >= start_of_week)
            elif date_filter == 'month':
                start_of_month = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
                query = query.filter(ProofChecklist.created_at >= start_of_month)
            elif date_filter == 'quarter':
                current_month = now.month
                quarter_start_month = ((current_month - 1) // 3) * 3 + 1
                start_of_quarter = now.replace(month=quarter_start_month, day=1, hour=0, minute=0, second=0, microsecond=0)
                query = query.filter(ProofChecklist.created_at >= start_of_quarter)
        
        # Order by created date descending
        query = query.order_by(ProofChecklist.created_at.desc())
        
        # Paginate
        proof_checklists = query.paginate(
            page=page, per_page=per_page, error_out=False
        )
        
        return render_template('rnd_proof_checklist/dashboard.html',
                             proof_checklists=proof_checklists,
                             search=search,
                             status_filter=status_filter,
                             date_filter=date_filter)

@rnd_proof_checklist_bp.route('/api/checklists')
@login_required
@require_rnd_access
def api_checklists():
    """API endpoint for fetching checklists with filters"""
    try:
        page = request.args.get('page', 1, type=int)
        per_page = 20
        search = request.args.get('search', '', type=str)
        status_filter = request.args.get('status', '', type=str)
        date_filter = request.args.get('date_filter', '', type=str)
        
        # Build query
        query = ProofChecklist.query
        
        # Apply search filter
        if search:
            query = query.filter(
                or_(
                    ProofChecklist.customer_name.ilike(f'%{search}%'),
                    ProofChecklist.item_name.ilike(f'%{search}%'),
                    ProofChecklist.paper_supplier.ilike(f'%{search}%')
                )
            )
        
        # Apply status filter
        if status_filter:
            query = query.filter(ProofChecklist.status == status_filter)
        
        # Apply date filter
        if date_filter:
            now = datetime.now(jakarta_tz)
            if date_filter == 'today':
                start_of_day = now.replace(hour=0, minute=0, second=0, microsecond=0)
                query = query.filter(ProofChecklist.created_at >= start_of_day)
            elif date_filter == 'week':
                from datetime import timedelta
                start_of_week = now - timedelta(days=now.weekday())
                start_of_week = start_of_week.replace(hour=0, minute=0, second=0, microsecond=0)
                query = query.filter(ProofChecklist.created_at >= start_of_week)
            elif date_filter == 'month':
                start_of_month = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
                query = query.filter(ProofChecklist.created_at >= start_of_month)
            elif date_filter == 'quarter':
                current_month = now.month
                quarter_start_month = ((current_month - 1) // 3) * 3 + 1
                start_of_quarter = now.replace(month=quarter_start_month, day=1, hour=0, minute=0, second=0, microsecond=0)
                query = query.filter(ProofChecklist.created_at >= start_of_quarter)
        
        # Order by created date descending
        query = query.order_by(ProofChecklist.created_at.desc())
        
        # Paginate
        checklists_paginated = query.paginate(
            page=page, per_page=per_page, error_out=False
        )
        
        # Serialize checklists with related data
        checklists_data = []
        for checklist in checklists_paginated.items:
            checklist_dict = checklist.to_dict()
            
            # Add related machine data
            if checklist.print_machines:
                checklist_dict['print_machines'] = [
                    {'print_machine': machine.print_machine.to_dict()}
                    for machine in checklist.print_machines
                ]
            
            checklists_data.append(checklist_dict)
        
        return jsonify({
            'success': True,
            'data': {
                'checklists': checklists_data,
                'total': checklists_paginated.total,
                'current_page': page,
                'total_pages': checklists_paginated.pages,
                'per_page': per_page
            }
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Error loading checklists: {str(e)}'
        }), 500

@rnd_proof_checklist_bp.route('/create', methods=['GET', 'POST'])
@login_required
@require_rnd_access
def create():
    """Create new Proof Checklist"""
    if request.method == 'POST':
        try:
            # Create new proof checklist
            proof_checklist = ProofChecklist(
                proof_date=request.form.get('proof_date'),
                customer_name=request.form.get('customer_name'),
                item_name=request.form.get('item_name'),
                product_category=request.form.get('product_category'),
                paper_supplier=request.form.get('paper_supplier'),
                paper_grammage=request.form.get('paper_grammage'),
                paper_size=request.form.get('paper_size'),
                paper_substance=request.form.get('paper_substance'),
                flute=request.form.get('flute'),
                up_num=request.form.get('up_num', type=int) if request.form.get('up_num') else None,
                print_coating=request.form.get('print_coating'),
                print_laminating=request.form.get('print_laminating'),
                postpress_packing_pallet=request.form.get('postpress_packing_pallet'),
                additional_information=request.form.get('additional_information'),
                created_by=current_user.id,
                status='DRAFT'
            )
            
            db.session.add(proof_checklist)
            db.session.flush()  # Get the ID without committing
            
            # Handle print machines
            print_machine_ids = request.form.getlist('print_machines')
            for machine_id in print_machine_ids:
                if machine_id:
                    pm = ProofChecklistPrintMachine(
                        proof_checklist_id=proof_checklist.id,
                        print_machine_id=int(machine_id)
                    )
                    db.session.add(pm)
            
            # Handle print separations (master data)
            print_separation_ids = request.form.getlist('print_separations')
            for separation_id in print_separation_ids:
                if separation_id:
                    ps = ProofChecklistPrintSeparation(
                        proof_checklist_id=proof_checklist.id,
                        print_separation_id=int(separation_id),
                        custom_separation_name=None
                    )
                    db.session.add(ps)
            
            # Handle custom separations
            custom_separations = request.form.getlist('custom_separations[]')
            for custom_name in custom_separations:
                if custom_name and custom_name.strip():
                    ps = ProofChecklistPrintSeparation(
                        proof_checklist_id=proof_checklist.id,
                        print_separation_id=None,
                        custom_separation_name=custom_name.strip()
                    )
                    db.session.add(ps)
            
            # Handle print inks (master data)
            print_ink_ids = request.form.getlist('print_inks')
            for ink_id in print_ink_ids:
                if ink_id:
                    pi = ProofChecklistPrintInk(
                        proof_checklist_id=proof_checklist.id,
                        print_ink_id=int(ink_id),
                        custom_ink_name=None
                    )
                    db.session.add(pi)
            
            # Handle custom inks
            custom_inks = request.form.getlist('custom_inks[]')
            for custom_name in custom_inks:
                if custom_name and custom_name.strip():
                    pi = ProofChecklistPrintInk(
                        proof_checklist_id=proof_checklist.id,
                        print_ink_id=None,
                        custom_ink_name=custom_name.strip()
                    )
                    db.session.add(pi)
            
            # Handle postpress machines
            postpress_machine_ids = request.form.getlist('postpress_machines')
            for machine_id in postpress_machine_ids:
                if machine_id:
                    ppm = ProofChecklistPostpressMachine(
                        proof_checklist_id=proof_checklist.id,
                        postpress_machine_id=int(machine_id)
                    )
                    db.session.add(ppm)
            
            db.session.commit()
            flash('Proof Checklist created successfully!', 'success')
            return redirect(url_for('rnd_proof_checklist.dashboard'))
            
        except Exception as e:
            db.session.rollback()
            flash(f'Error creating Proof Checklist: {str(e)}', 'danger')
    
    # Get master data for form
    print_machines = MasterPrintMachine.query.filter_by(is_active=True).all()
    print_separations = MasterPrintSeparation.query.filter_by(is_active=True).all()
    print_inks = MasterPrintInk.query.filter_by(is_active=True).all()
    postpress_machines = MasterPostpressMachine.query.filter_by(is_active=True).all()
    
    # Group postpress machines by category
    postpress_by_category = {}
    for machine in postpress_machines:
        if machine.machine_category not in postpress_by_category:
            postpress_by_category[machine.machine_category] = []
        postpress_by_category[machine.machine_category].append(machine)
    
    # Empty lists for create mode (template will check if proof_checklist exists)
    selected_print_machines = []
    selected_print_separations = []
    selected_print_inks = []
    selected_postpress_machines = []
    
    return render_template('rnd_proof_checklist/form.html',
                         proof_checklist=None,
                         print_machines=print_machines,
                         print_separations=print_separations,
                         print_inks=print_inks,
                         postpress_by_category=postpress_by_category,
                         selected_print_machines=selected_print_machines,
                         selected_print_separations=selected_print_separations,
                         selected_print_inks=selected_print_inks,
                         selected_postpress_machines=selected_postpress_machines)

@rnd_proof_checklist_bp.route('/<int:id>')
@login_required
@require_rnd_access
def view(id):
    """View Proof Checklist details"""
    proof_checklist = ProofChecklist.query.get_or_404(id)
    return render_template('rnd_proof_checklist/view.html', 
                         proof_checklist=proof_checklist)

@rnd_proof_checklist_bp.route('/<int:id>/edit', methods=['GET', 'POST'])
@login_required
@require_rnd_access
def edit(id):
    """Edit Proof Checklist"""
    proof_checklist = ProofChecklist.query.get_or_404(id)
    
    if request.method == 'POST':
        try:
            # Update basic fields
            proof_checklist.proof_date = request.form.get('proof_date')
            proof_checklist.customer_name = request.form.get('customer_name')
            proof_checklist.item_name = request.form.get('item_name')
            proof_checklist.product_category = request.form.get('product_category')
            proof_checklist.paper_supplier = request.form.get('paper_supplier')
            proof_checklist.paper_grammage = request.form.get('paper_grammage')
            proof_checklist.paper_size = request.form.get('paper_size')
            proof_checklist.paper_substance = request.form.get('paper_substance')
            proof_checklist.flute = request.form.get('flute')
            proof_checklist.up_num = request.form.get('up_num', type=int) if request.form.get('up_num') else None
            proof_checklist.print_coating = request.form.get('print_coating')
            proof_checklist.print_laminating = request.form.get('print_laminating')
            proof_checklist.postpress_packing_pallet = request.form.get('postpress_packing_pallet')
            proof_checklist.additional_information = request.form.get('additional_information')
            proof_checklist.updated_by = current_user.id
            
            # Clear existing relationships
            ProofChecklistPrintMachine.query.filter_by(proof_checklist_id=id).delete()
            ProofChecklistPrintSeparation.query.filter_by(proof_checklist_id=id).delete()
            ProofChecklistPrintInk.query.filter_by(proof_checklist_id=id).delete()
            ProofChecklistPostpressMachine.query.filter_by(proof_checklist_id=id).delete()
            
            # Add new relationships
            print_machine_ids = request.form.getlist('print_machines')
            for machine_id in print_machine_ids:
                if machine_id:
                    pm = ProofChecklistPrintMachine(
                        proof_checklist_id=id,
                        print_machine_id=int(machine_id)
                    )
                    db.session.add(pm)
            
            print_separation_ids = request.form.getlist('print_separations')
            for separation_id in print_separation_ids:
                if separation_id:
                    ps = ProofChecklistPrintSeparation(
                        proof_checklist_id=id,
                        print_separation_id=int(separation_id)
                    )
                    db.session.add(ps)
            
            print_ink_ids = request.form.getlist('print_inks')
            for ink_id in print_ink_ids:
                if ink_id:
                    pi = ProofChecklistPrintInk(
                        proof_checklist_id=id,
                        print_ink_id=int(ink_id)
                    )
                    db.session.add(pi)
            
            postpress_machine_ids = request.form.getlist('postpress_machines')
            for machine_id in postpress_machine_ids:
                if machine_id:
                    ppm = ProofChecklistPostpressMachine(
                        proof_checklist_id=id,
                        postpress_machine_id=int(machine_id)
                    )
                    db.session.add(ppm)
            
            db.session.commit()
            flash('Proof Checklist updated successfully!', 'success')
            return redirect(url_for('rnd_proof_checklist.view', id=id))
            
        except Exception as e:
            db.session.rollback()
            flash(f'Error updating Proof Checklist: {str(e)}', 'danger')
    
    # Get master data for form
    print_machines = MasterPrintMachine.query.filter_by(is_active=True).all()
    print_separations = MasterPrintSeparation.query.filter_by(is_active=True).all()
    print_inks = MasterPrintInk.query.filter_by(is_active=True).all()
    postpress_machines = MasterPostpressMachine.query.filter_by(is_active=True).all()
    
    # Group postpress machines by category
    postpress_by_category = {}
    for machine in postpress_machines:
        if machine.machine_category not in postpress_by_category:
            postpress_by_category[machine.machine_category] = []
        postpress_by_category[machine.machine_category].append(machine)
    
    # Get selected IDs for pre-filling form
    selected_print_machines = [pm.print_machine_id for pm in proof_checklist.print_machines]
    selected_print_separations = [ps.print_separation_id for ps in proof_checklist.print_separations]
    selected_print_inks = [pi.print_ink_id for pi in proof_checklist.print_inks]
    selected_postpress_machines = [pm.postpress_machine_id for pm in proof_checklist.postpress_machines]
    
    return render_template('rnd_proof_checklist/form.html',
                         proof_checklist=proof_checklist,
                         print_machines=print_machines,
                         print_separations=print_separations,
                         print_inks=print_inks,
                         postpress_by_category=postpress_by_category,
                         selected_print_machines=selected_print_machines,
                         selected_print_separations=selected_print_separations,
                         selected_print_inks=selected_print_inks,
                         selected_postpress_machines=selected_postpress_machines)

@rnd_proof_checklist_bp.route('/<int:id>/delete', methods=['POST'])
@login_required
@require_rnd_access
def delete(id):
    """Delete Proof Checklist"""
    proof_checklist = ProofChecklist.query.get_or_404(id)
    
    try:
        db.session.delete(proof_checklist)
        db.session.commit()
        flash('Proof Checklist deleted successfully!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error deleting Proof Checklist: {str(e)}', 'danger')
    
    return redirect(url_for('rnd_proof_checklist.dashboard'))

@rnd_proof_checklist_bp.route('/<int:id>/status', methods=['POST'])
@login_required
@require_rnd_access
def update_status(id):
    """Update Proof Checklist status"""
    proof_checklist = ProofChecklist.query.get_or_404(id)
    new_status = request.form.get('status')
    
    if new_status in ['DRAFT', 'ACTIVE', 'COMPLETED', 'CANCELLED']:
        old_status = proof_checklist.status
        proof_checklist.status = new_status
        proof_checklist.updated_by = current_user.id
        
        # Save status history
        status_history = ProofChecklistStatusHistory(
            proof_checklist_id=id,
            old_status=old_status,
            new_status=new_status,
            changed_by=current_user.id
        )
        db.session.add(status_history)
        db.session.commit()
        flash(f'Status updated to {new_status}!', 'success')
    else:
        flash('Invalid status!', 'danger')
    
    return redirect(url_for('rnd_proof_checklist.view', id=id))

# API endpoints for master data
@rnd_proof_checklist_bp.route('/api/print-machines')
@login_required
@require_rnd_access
def api_print_machines():
    """API endpoint for print machines"""
    machines = MasterPrintMachine.query.filter_by(is_active=True).all()
    return jsonify([machine.to_dict() for machine in machines])

@rnd_proof_checklist_bp.route('/api/print-separations')
@login_required
@require_rnd_access
def api_print_separations():
    """API endpoint for print separations"""
    separations = MasterPrintSeparation.query.filter_by(is_active=True).all()
    return jsonify([separation.to_dict() for separation in separations])

@rnd_proof_checklist_bp.route('/api/print-inks')
@login_required
@require_rnd_access
def api_print_inks():
    """API endpoint for print inks"""
    inks = MasterPrintInk.query.filter_by(is_active=True).all()
    return jsonify([ink.to_dict() for ink in inks])

@rnd_proof_checklist_bp.route('/api/postpress-machines')
@login_required
@require_rnd_access
def api_postpress_machines():
    """API endpoint for postpress machines"""
    machines = MasterPostpressMachine.query.filter_by(is_active=True).all()
    return jsonify([machine.to_dict() for machine in machines])

# =====================================================================
# CRUD API ENDPOINTS - Full API support for JavaScript/Frontend
# =====================================================================

@rnd_proof_checklist_bp.route('/api/checklist', methods=['POST'])
@login_required
@require_rnd_access
def api_create_checklist():
    """API endpoint for creating proof checklist via JSON"""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({
                'success': False,
                'message': 'No data provided'
            }), 400
        
        # Create new proof checklist
        proof_checklist = ProofChecklist(
            proof_date=data.get('proof_date'),
            customer_name=data.get('customer_name'),
            item_name=data.get('item_name'),
            product_category=data.get('product_category'),
            paper_supplier=data.get('paper_supplier'),
            paper_grammage=data.get('paper_grammage'),
            paper_size=data.get('paper_size'),
            paper_substance=data.get('paper_substance'),
            flute=data.get('flute'),
            up_num=data.get('up_num'),
            print_coating=data.get('print_coating'),
            print_laminating=data.get('print_laminating'),
            postpress_packing_pallet=data.get('postpress_packing_pallet'),
            additional_information=data.get('additional_information'),
            created_by=current_user.id,
            status='DRAFT'
        )
        
        db.session.add(proof_checklist)
        db.session.flush()  # Get the ID
        
        # Handle print machines
        print_machine_ids = data.get('print_machines', [])
        for machine_id in print_machine_ids:
            if machine_id:
                pm = ProofChecklistPrintMachine(
                    proof_checklist_id=proof_checklist.id,
                    print_machine_id=int(machine_id)
                )
                db.session.add(pm)
        
        # Handle print separations (master data)
        print_separation_ids = data.get('print_separations', [])
        for separation_id in print_separation_ids:
            if separation_id:
                ps = ProofChecklistPrintSeparation(
                    proof_checklist_id=proof_checklist.id,
                    print_separation_id=int(separation_id),
                    custom_separation_name=None
                )
                db.session.add(ps)
        
        # Handle custom separations
        custom_separations = data.get('custom_separations', [])
        for custom_name in custom_separations:
            if custom_name and isinstance(custom_name, str) and custom_name.strip():
                ps = ProofChecklistPrintSeparation(
                    proof_checklist_id=proof_checklist.id,
                    print_separation_id=None,
                    custom_separation_name=custom_name.strip()
                )
                db.session.add(ps)
        
        # Handle print inks (master data)
        print_ink_ids = data.get('print_inks', [])
        for ink_id in print_ink_ids:
            if ink_id:
                pi = ProofChecklistPrintInk(
                    proof_checklist_id=proof_checklist.id,
                    print_ink_id=int(ink_id),
                    custom_ink_name=None
                )
                db.session.add(pi)
        
        # Handle custom inks
        custom_inks = data.get('custom_inks', [])
        for custom_name in custom_inks:
            if custom_name and isinstance(custom_name, str) and custom_name.strip():
                pi = ProofChecklistPrintInk(
                    proof_checklist_id=proof_checklist.id,
                    print_ink_id=None,
                    custom_ink_name=custom_name.strip()
                )
                db.session.add(pi)
        
        # Handle postpress machines
        postpress_machine_ids = data.get('postpress_machines', [])
        for machine_id in postpress_machine_ids:
            if machine_id:
                ppm = ProofChecklistPostpressMachine(
                    proof_checklist_id=proof_checklist.id,
                    postpress_machine_id=int(machine_id)
                )
                db.session.add(ppm)
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Proof Checklist created successfully',
            'data': {
                'id': proof_checklist.id,
                'checklist': proof_checklist.to_dict()
            }
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': f'Error creating Proof Checklist: {str(e)}'
        }), 500

@rnd_proof_checklist_bp.route('/api/checklist/<int:id>', methods=['GET'])
@login_required
@require_rnd_access
def api_get_checklist(id):
    """API endpoint for fetching single checklist detail"""
    try:
        proof_checklist = ProofChecklist.query.get(id)
        
        if not proof_checklist:
            return jsonify({
                'success': False,
                'message': 'Proof Checklist not found'
            }), 404
        
        # Build complete checklist data with relations
        checklist_data = proof_checklist.to_dict()
        
        # Add print machines
        checklist_data['print_machines'] = [
            {
                'id': pm.id,
                'print_machine_id': pm.print_machine_id,
                'print_machine': pm.print_machine.to_dict() if pm.print_machine else None
            }
            for pm in proof_checklist.print_machines
        ]
        
        # Add print separations
        checklist_data['print_separations'] = [
            {
                'id': ps.id,
                'print_separation_id': ps.print_separation_id,
                'custom_separation_name': ps.custom_separation_name,
                'print_separation': ps.print_separation.to_dict() if ps.print_separation else None
            }
            for ps in proof_checklist.print_separations
        ]
        
        # Add print inks
        checklist_data['print_inks'] = [
            {
                'id': pi.id,
                'print_ink_id': pi.print_ink_id,
                'custom_ink_name': pi.custom_ink_name,
                'print_ink': pi.print_ink.to_dict() if pi.print_ink else None
            }
            for pi in proof_checklist.print_inks
        ]
        
        # Add postpress machines
        checklist_data['postpress_machines'] = [
            {
                'id': pm.id,
                'postpress_machine_id': pm.postpress_machine_id,
                'postpress_machine': pm.postpress_machine.to_dict() if pm.postpress_machine else None
            }
            for pm in proof_checklist.postpress_machines
        ]
        
        return jsonify({
            'success': True,
            'data': checklist_data
        }), 200
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Error fetching Proof Checklist: {str(e)}'
        }), 500

@rnd_proof_checklist_bp.route('/api/checklist/<int:id>', methods=['PUT'])
@login_required
@require_rnd_access
def api_update_checklist(id):
    """API endpoint for updating proof checklist via JSON"""
    try:
        proof_checklist = ProofChecklist.query.get(id)
        
        if not proof_checklist:
            return jsonify({
                'success': False,
                'message': 'Proof Checklist not found'
            }), 404
        
        data = request.get_json()
        
        if not data:
            return jsonify({
                'success': False,
                'message': 'No data provided'
            }), 400
        
        # Update basic fields
        proof_checklist.proof_date = data.get('proof_date', proof_checklist.proof_date)
        proof_checklist.customer_name = data.get('customer_name', proof_checklist.customer_name)
        proof_checklist.item_name = data.get('item_name', proof_checklist.item_name)
        proof_checklist.product_category = data.get('product_category', proof_checklist.product_category)
        proof_checklist.paper_supplier = data.get('paper_supplier', proof_checklist.paper_supplier)
        proof_checklist.paper_grammage = data.get('paper_grammage', proof_checklist.paper_grammage)
        proof_checklist.paper_size = data.get('paper_size', proof_checklist.paper_size)
        proof_checklist.paper_substance = data.get('paper_substance', proof_checklist.paper_substance)
        proof_checklist.flute = data.get('flute', proof_checklist.flute)
        proof_checklist.up_num = data.get('up_num', proof_checklist.up_num)
        proof_checklist.print_coating = data.get('print_coating', proof_checklist.print_coating)
        proof_checklist.print_laminating = data.get('print_laminating', proof_checklist.print_laminating)
        proof_checklist.postpress_packing_pallet = data.get('postpress_packing_pallet', proof_checklist.postpress_packing_pallet)
        proof_checklist.additional_information = data.get('additional_information', proof_checklist.additional_information)
        proof_checklist.updated_by = current_user.id
        
        # Clear existing relationships
        ProofChecklistPrintMachine.query.filter_by(proof_checklist_id=id).delete()
        ProofChecklistPrintSeparation.query.filter_by(proof_checklist_id=id).delete()
        ProofChecklistPrintInk.query.filter_by(proof_checklist_id=id).delete()
        ProofChecklistPostpressMachine.query.filter_by(proof_checklist_id=id).delete()
        
        # Add new relationships
        print_machine_ids = data.get('print_machines', [])
        for machine_id in print_machine_ids:
            if machine_id:
                pm = ProofChecklistPrintMachine(
                    proof_checklist_id=id,
                    print_machine_id=int(machine_id)
                )
                db.session.add(pm)
        
        # Handle print separations (master data)
        print_separation_ids = data.get('print_separations', [])
        for separation_id in print_separation_ids:
            if separation_id:
                ps = ProofChecklistPrintSeparation(
                    proof_checklist_id=id,
                    print_separation_id=int(separation_id),
                    custom_separation_name=None
                )
                db.session.add(ps)
        
        # Handle custom separations
        custom_separations = data.get('custom_separations', [])
        for custom_name in custom_separations:
            if custom_name and isinstance(custom_name, str) and custom_name.strip():
                ps = ProofChecklistPrintSeparation(
                    proof_checklist_id=id,
                    print_separation_id=None,
                    custom_separation_name=custom_name.strip()
                )
                db.session.add(ps)
        
        # Handle print inks (master data)
        print_ink_ids = data.get('print_inks', [])
        for ink_id in print_ink_ids:
            if ink_id:
                pi = ProofChecklistPrintInk(
                    proof_checklist_id=id,
                    print_ink_id=int(ink_id),
                    custom_ink_name=None
                )
                db.session.add(pi)
        
        # Handle custom inks
        custom_inks = data.get('custom_inks', [])
        for custom_name in custom_inks:
            if custom_name and isinstance(custom_name, str) and custom_name.strip():
                pi = ProofChecklistPrintInk(
                    proof_checklist_id=id,
                    print_ink_id=None,
                    custom_ink_name=custom_name.strip()
                )
                db.session.add(pi)
        
        postpress_machine_ids = data.get('postpress_machines', [])
        for machine_id in postpress_machine_ids:
            if machine_id:
                ppm = ProofChecklistPostpressMachine(
                    proof_checklist_id=id,
                    postpress_machine_id=int(machine_id)
                )
                db.session.add(ppm)
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Proof Checklist updated successfully',
            'data': {
                'id': proof_checklist.id,
                'checklist': proof_checklist.to_dict()
            }
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': f'Error updating Proof Checklist: {str(e)}'
        }), 500

@rnd_proof_checklist_bp.route('/api/checklist/<int:id>', methods=['DELETE'])
@login_required
@require_rnd_access
def api_delete_checklist(id):
    """API endpoint for deleting proof checklist"""
    try:
        proof_checklist = ProofChecklist.query.get(id)
        
        if not proof_checklist:
            return jsonify({
                'success': False,
                'message': 'Proof Checklist not found'
            }), 404
        
        # Delete related records will be handled by cascade delete if configured in models
        db.session.delete(proof_checklist)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Proof Checklist deleted successfully'
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': f'Error deleting Proof Checklist: {str(e)}'
        }), 500

@rnd_proof_checklist_bp.route('/api/checklist/<int:id>/status', methods=['PUT'])
@login_required
@require_rnd_access
def api_update_checklist_status(id):
    """API endpoint for updating checklist status via JSON"""
    try:
        proof_checklist = ProofChecklist.query.get(id)
        
        if not proof_checklist:
            return jsonify({
                'success': False,
                'message': 'Proof Checklist not found'
            }), 404
        
        data = request.get_json()
        new_status = data.get('status')
        
        if not new_status:
            return jsonify({
                'success': False,
                'message': 'Status is required'
            }), 400
        
        if new_status not in ['DRAFT', 'ACTIVE', 'COMPLETED', 'CANCELLED']:
            return jsonify({
                'success': False,
                'message': f'Invalid status: {new_status}'
            }), 400
        
        proof_checklist.status = new_status
        proof_checklist.updated_by = current_user.id
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': f'Status updated to {new_status}',
            'data': {
                'id': proof_checklist.id,
                'status': proof_checklist.status,
                'checklist': proof_checklist.to_dict()
            }
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': f'Error updating status: {str(e)}'
        }), 500

@rnd_proof_checklist_bp.route('/api/master-data', methods=['GET'])
@login_required
@require_rnd_access
def api_get_master_data():
    """API endpoint for fetching all master data at once"""
    try:
        print_machines = MasterPrintMachine.query.filter_by(is_active=True).all()
        print_separations = MasterPrintSeparation.query.filter_by(is_active=True).all()
        print_inks = MasterPrintInk.query.filter_by(is_active=True).all()
        postpress_machines = MasterPostpressMachine.query.filter_by(is_active=True).all()
        
        # Group postpress machines by category
        postpress_by_category = {}
        for machine in postpress_machines:
            if machine.machine_category not in postpress_by_category:
                postpress_by_category[machine.machine_category] = []
            postpress_by_category[machine.machine_category].append(machine.to_dict())
        
        return jsonify({
            'success': True,
            'data': {
                'print_machines': [m.to_dict() for m in print_machines],
                'print_separations': [s.to_dict() for s in print_separations],
                'print_inks': [i.to_dict() for i in print_inks],
                'postpress_machines': [m.to_dict() for m in postpress_machines],
                'postpress_by_category': postpress_by_category
            }
        }), 200
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Error fetching master data: {str(e)}'
        }), 500