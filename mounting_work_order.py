# Mounting Work Order Incoming Routes
from datetime import datetime
from flask import Blueprint, jsonify, request, render_template
from flask_login import login_required, current_user
from sqlalchemy import or_, extract, cast, String
import pytz

# Create blueprint
mounting_work_order_bp = Blueprint('mounting_work_order', __name__)

# Import functions to avoid circular imports
def get_db():
    from app import db
    return db

def get_require_mounting_access():
    from app import require_mounting_access
    return require_mounting_access

def get_mounting_work_order_model():
    from models_mounting import MountingWorkOrderIncoming
    return MountingWorkOrderIncoming

# Timezone untuk Jakarta
jakarta_tz = pytz.timezone('Asia/Jakarta')

@mounting_work_order_bp.route('/mounting-work-order-incoming')
@login_required
def mounting_work_order_incoming_page():
    """Render halaman Work Order Incoming"""
    require_mounting_access = get_require_mounting_access()
    return require_mounting_access(lambda: render_template('mounting_work_order_incoming.html'))()

# API Endpoints untuk Work Order Incoming CRUD Operations

@mounting_work_order_bp.route('/api/mounting-work-order-incoming', methods=['GET'])
@login_required
def get_mounting_work_orders():
    """Get list of work orders with pagination and filtering"""
    require_mounting_access = get_require_mounting_access()
    return require_mounting_access(_get_mounting_work_orders_impl)()

def _get_mounting_work_orders_impl():
    try:
        # Get dependencies
        db = get_db()
        MountingWorkOrderIncoming = get_mounting_work_order_model()
        
        # Get query parameters
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 10, type=int)
        search = request.args.get('search', '')
        status_filter = request.args.get('status', '')
        date_filter = request.args.get('date', '')
        
        # Base query
        query = MountingWorkOrderIncoming.query
        
        # Apply search filter
        if search:
            search_term = f"%{search}%"
            query = query.filter(
                or_(
                    MountingWorkOrderIncoming.wo_number.ilike(search_term),
                    MountingWorkOrderIncoming.mc_number.ilike(search_term),
                    MountingWorkOrderIncoming.customer_name.ilike(search_term),
                    MountingWorkOrderIncoming.item_name.ilike(search_term),
                    MountingWorkOrderIncoming.print_block.ilike(search_term),
                    MountingWorkOrderIncoming.print_machine.ilike(search_term),
                    MountingWorkOrderIncoming.paper_type.ilike(search_term),
                    cast(MountingWorkOrderIncoming.id, String).ilike(search_term),
                    cast(MountingWorkOrderIncoming.run_length_sheet, String).ilike(search_term),
                    cast(MountingWorkOrderIncoming.sheet_size, String).ilike(search_term)
                )
            )
        
        # Apply status filter
        if status_filter:
            query = query.filter_by(status=status_filter)
            
        # Apply date filter
        if date_filter:
            try:
                filter_date = datetime.strptime(date_filter, '%Y-%m-%d').date()
                query = query.filter(
                    extract('year', MountingWorkOrderIncoming.incoming_datetime) == filter_date.year,
                    extract('month', MountingWorkOrderIncoming.incoming_datetime) == filter_date.month,
                    extract('day', MountingWorkOrderIncoming.incoming_datetime) == filter_date.day
                )
            except ValueError:
                return jsonify({'error': 'Invalid date format'}), 400
        
        # Order by latest first
        query = query.order_by(MountingWorkOrderIncoming.incoming_datetime.desc())
        
        # Paginate
        pagination = query.paginate(page=page, per_page=per_page)
        
        return jsonify({
            'success': True,
            'data': [wo.to_dict() for wo in pagination.items],
            'total': pagination.total,
            'pages': pagination.pages,
            'current_page': page
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Error fetching work orders: {str(e)}'
        }), 500

@mounting_work_order_bp.route('/api/mounting-work-order-incoming', methods=['POST'])
@login_required
def create_mounting_work_orders():
    """Create multiple work orders (batch operation)"""
    require_mounting_access = get_require_mounting_access()
    return require_mounting_access(_create_mounting_work_orders_impl)()

def _create_mounting_work_orders_impl():
    try:
        # Get dependencies
        db = get_db()
        MountingWorkOrderIncoming = get_mounting_work_order_model()
        
        data = request.get_json()
        
        # Validate required data
        if not data or 'work_orders' not in data:
            return jsonify({
                'success': False,
                'message': 'No work orders data provided'
            }), 400
        
        work_orders_data = data['work_orders']
        if not isinstance(work_orders_data, list) or len(work_orders_data) == 0:
            return jsonify({
                'success': False,
                'message': 'Work orders must be a non-empty array'
            }), 400
        
        created_work_orders = []
        errors = []
        
        # Process each work order
        for index, wo_data in enumerate(work_orders_data):
            try:
                # Validate required fields for each work order
                required_fields = ['wo_number', 'mc_number', 'customer_name', 'item_name',
                                 'print_block', 'print_machine', 'run_length_sheet',
                                 'sheet_size', 'paper_type']
                
                missing_fields = [field for field in required_fields if not wo_data.get(field)]
                if missing_fields:
                    errors.append(f"Row {index + 1}: Missing required fields: {', '.join(missing_fields)}")
                    continue
                
                # Parse incoming_datetime if provided, otherwise use current time
                incoming_datetime = datetime.now(jakarta_tz)  # Get current time when processing each request
                if wo_data.get('incoming_datetime'):
                    try:
                        incoming_datetime = datetime.strptime(wo_data['incoming_datetime'], '%Y-%m-%d %H:%M:%S')
                        incoming_datetime = jakarta_tz.localize(incoming_datetime)
                    except ValueError:
                        errors.append(f"Row {index + 1}: Invalid datetime format, using current time")
                
                # Create new work order
                new_work_order = MountingWorkOrderIncoming(
                    incoming_datetime=incoming_datetime,
                    wo_number=wo_data['wo_number'],
                    mc_number=wo_data['mc_number'],
                    customer_name=wo_data['customer_name'],
                    item_name=wo_data['item_name'],
                    print_block=wo_data['print_block'],
                    print_machine=wo_data['print_machine'],
                    run_length_sheet=wo_data['run_length_sheet'],
                    sheet_size=wo_data['sheet_size'],
                    paper_type=wo_data['paper_type'],
                    status='pending',  # Default status
                    created_by=current_user.username if current_user else 'system'
                )
                
                db.session.add(new_work_order)
                created_work_orders.append(new_work_order)
                
            except Exception as e:
                errors.append(f"Row {index + 1}: {str(e)}")
        
        # If there are any errors, rollback and return them
        if errors:
            db.session.rollback()
            return jsonify({
                'success': False,
                'message': 'Some work orders could not be created',
                'errors': errors
            }), 400
        
        # Commit all work orders
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': f'Successfully created {len(created_work_orders)} work orders',
            'data': [wo.to_dict() for wo in created_work_orders]
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': f'Error creating work orders: {str(e)}'
        }), 500

@mounting_work_order_bp.route('/api/mounting-work-order-incoming/<int:wo_id>', methods=['GET'])
@login_required
def get_mounting_work_order(wo_id):
    """Get single work order by ID"""
    require_mounting_access = get_require_mounting_access()
    return require_mounting_access(_get_mounting_work_order_impl)(wo_id)

def _get_mounting_work_order_impl(wo_id):
    try:
        # Get dependencies
        db = get_db()
        MountingWorkOrderIncoming = get_mounting_work_order_model()
        
        work_order = db.session.get(MountingWorkOrderIncoming, wo_id)
        if not work_order:
            return jsonify({
                'success': False,
                'message': 'Work order not found'
            }), 404
        
        return jsonify({
            'success': True,
            'data': work_order.to_dict()
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Error fetching work order: {str(e)}'
        }), 500

@mounting_work_order_bp.route('/api/mounting-work-order-incoming/<int:wo_id>', methods=['PUT'])
@login_required
def update_mounting_work_order(wo_id):
    """Update work order by ID"""
    require_mounting_access = get_require_mounting_access()
    return require_mounting_access(_update_mounting_work_order_impl)(wo_id)

def _update_mounting_work_order_impl(wo_id):
    try:
        # Get dependencies
        db = get_db()
        MountingWorkOrderIncoming = get_mounting_work_order_model()
        
        work_order = db.session.get(MountingWorkOrderIncoming, wo_id)
        if not work_order:
            return jsonify({
                'success': False,
                'message': 'Work order not found'
            }), 404
        
        data = request.get_json()
        if not data:
            return jsonify({
                'success': False,
                'message': 'No data provided'
            }), 400
        
        # Update fields if provided
        if 'incoming_datetime' in data:
            try:
                work_order.incoming_datetime = datetime.strptime(data['incoming_datetime'], '%Y-%m-%d %H:%M:%S')
            except ValueError:
                return jsonify({
                    'success': False,
                    'message': 'Invalid datetime format'
                }), 400
        
        # Update other fields
        updatable_fields = ['wo_number', 'mc_number', 'customer_name', 'item_name',
                          'print_block', 'print_machine', 'run_length_sheet',
                          'sheet_size', 'paper_type', 'status']
        
        for field in updatable_fields:
            if field in data:
                setattr(work_order, field, data[field])
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Work order updated successfully',
            'data': work_order.to_dict()
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': f'Error updating work order: {str(e)}'
        }), 500

@mounting_work_order_bp.route('/api/mounting-work-order-incoming/<int:wo_id>', methods=['DELETE'])
@login_required
def delete_mounting_work_order(wo_id):
    """Delete work order by ID"""
    require_mounting_access = get_require_mounting_access()
    return require_mounting_access(_delete_mounting_work_order_impl)(wo_id)

def _delete_mounting_work_order_impl(wo_id):
    try:
        # Get dependencies
        db = get_db()
        MountingWorkOrderIncoming = get_mounting_work_order_model()
        
        work_order = db.session.get(MountingWorkOrderIncoming, wo_id)
        if not work_order:
            return jsonify({
                'success': False,
                'message': 'Work order not found'
            }), 404
        
        db.session.delete(work_order)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Work order deleted successfully'
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': f'Error deleting work order: {str(e)}'
        }), 500

@mounting_work_order_bp.route('/api/mounting-work-order-incoming/<int:wo_id>/status', methods=['PUT'])
@login_required
def update_mounting_work_order_status(wo_id):
    """Update work order status"""
    require_mounting_access = get_require_mounting_access()
    return require_mounting_access(_update_mounting_work_order_status_impl)(wo_id)

def _update_mounting_work_order_status_impl(wo_id):
    try:
        # Get dependencies
        db = get_db()
        MountingWorkOrderIncoming = get_mounting_work_order_model()
        
        work_order = db.session.get(MountingWorkOrderIncoming, wo_id)
        if not work_order:
            return jsonify({
                'success': False,
                'message': 'Work order not found'
            }), 404
        
        data = request.get_json()
        if not data or 'status' not in data:
            return jsonify({
                'success': False,
                'message': 'Status is required'
            }), 400
        
        # Validate status
        valid_statuses = ['pending', 'in_progress', 'completed', 'cancelled']
        if data['status'] not in valid_statuses:
            return jsonify({
                'success': False,
                'message': f'Invalid status. Must be one of: {", ".join(valid_statuses)}'
            }), 400
        
        work_order.status = data['status']
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Work order status updated successfully',
            'data': work_order.to_dict()
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': f'Error updating work order status: {str(e)}'
        }), 500

@mounting_work_order_bp.route('/api/mounting-work-order-incoming/validate', methods=['POST'])
@login_required
def validate_work_orders():
    """Validate work orders data before submission"""
    require_mounting_access = get_require_mounting_access()
    return require_mounting_access(_validate_work_orders_impl)()

def _validate_work_orders_impl():
    try:
        data = request.get_json()
        
        if not data or 'work_orders' not in data:
            return jsonify({
                'success': False,
                'message': 'No work orders data provided'
            }), 400
        
        work_orders_data = data['work_orders']
        if not isinstance(work_orders_data, list):
            return jsonify({
                'success': False,
                'message': 'Work orders must be an array'
            }), 400
        
        # Count valid rows
        valid_rows = 0
        errors = []
        
        required_fields = ['wo_number', 'mc_number', 'customer_name', 'item_name',
                         'print_block', 'print_machine', 'run_length_sheet',
                         'sheet_size', 'paper_type']
        
        for index, wo_data in enumerate(work_orders_data):
            # Check if row has any data
            if not any(wo_data.values()):
                continue  # Skip empty rows
            
            # Check required fields
            missing_fields = [field for field in required_fields if not wo_data.get(field)]
            if missing_fields:
                errors.append(f"Row {index + 1}: Missing required fields: {', '.join(missing_fields)}")
            else:
                valid_rows += 1
        
        return jsonify({
            'success': True,
            'total_rows': len(work_orders_data),
            'valid_rows': valid_rows,
            'errors': errors,
            'message': f'Found {valid_rows} valid work orders out of {len(work_orders_data)} rows'
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Error validating work orders: {str(e)}'
        }), 500