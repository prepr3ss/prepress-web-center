"""
external_delay_routes.py
API Routes for External Lead Time Tracking in R&D Cloudsphere

This blueprint handles all external delay management:
- Creating external delay records
- Retrieving external delays for a job
- Auto-completing delays when tasks are done
- Calculating lead time breakdowns
- Deleting delay records

Blueprint URL Prefix: /rnd-cloudsphere/api/external-delay

Usage in app.py:
    from blueprints.external_delay_routes import external_delay_bp
    app.register_blueprint(external_delay_bp)
"""

import logging
from datetime import datetime
import pytz
from flask import Blueprint, jsonify, request, current_app
from flask_login import login_required, current_user
from functools import wraps

from models import db, User
from models_rnd import RNDJob, RNDJobProgressAssignment, RNDJobTaskAssignment
from models_rnd_external import RNDExternalTime

# Setup logging
logger = logging.getLogger(__name__)

# Jakarta timezone
jakarta_tz = pytz.timezone('Asia/Jakarta')

# Create Blueprint
external_delay_bp = Blueprint('external_delay', __name__, url_prefix='/rnd-cloudsphere/api/external-delay')


# Access control decorator
def require_admin(f):
    """Decorator to require admin access"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_admin():
            return jsonify({'success': False, 'message': 'Admin access required'}), 403
        return f(*args, **kwargs)
    return decorated_function


def require_rnd_access(f):
    """Decorator to require RND Cloudsphere access"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Use the same RND access check as rnd_cloudsphere blueprint
        if not hasattr(current_user, 'can_access_rnd') or not current_user.can_access_rnd():
            return jsonify({'success': False, 'message': 'RND Cloudsphere access required'}), 403
        return f(*args, **kwargs)
    return decorated_function


# ==================== CREATE EXTERNAL DELAY ====================

@external_delay_bp.route('', methods=['POST'])
@login_required
@require_admin
def create_external_delay():
    """
    Create a new external delay record
    
    POST /rnd-cloudsphere/api/external-delay
    
    Request Body:
    {
        "job_id": 123,
        "last_progress_assignment_id": 456,
        "next_progress_assignment_id": 789,
        "delay_category": "PPIC",
        "delay_reason": "Tunggu Planning PPIC",
        "delay_notes": "Planning batch perlu approval"
    }
    
    Response:
    {
        "success": true,
        "message": "External delay recorded successfully",
        "data": { ... RNDExternalTime.to_dict() ... }
    }
    """
    try:
        data = request.get_json()
        
        # Validation: Check required fields
        required_fields = ['job_id', 'last_progress_assignment_id', 'delay_category', 'delay_reason']
        for field in required_fields:
            if field not in data or not data[field]:
                return jsonify({
                    'success': False,
                    'message': f'Missing required field: {field}'
                }), 400
        
        # Validation: Check job exists
        job = RNDJob.query.get(data['job_id'])
        if not job:
            return jsonify({
                'success': False,
                'message': 'Job not found'
            }), 404
        
        # Validation: Check last_progress_assignment exists and is completed
        last_progress = RNDJobProgressAssignment.query.get(
            data['last_progress_assignment_id']
        )
        if not last_progress:
            return jsonify({
                'success': False,
                'message': 'Last progress assignment not found'
            }), 404
        
        if last_progress.status != 'completed':
            return jsonify({
                'success': False,
                'message': 'Last progress must be completed status'
            }), 400
        
        if not last_progress.finished_at:
            return jsonify({
                'success': False,
                'message': 'Last progress has no finished_at timestamp'
            }), 400
        
        # Validation: Check next_progress_assignment if provided
        next_progress = None
        if data.get('next_progress_assignment_id'):
            next_progress = RNDJobProgressAssignment.query.get(
                data['next_progress_assignment_id']
            )
            if not next_progress:
                return jsonify({
                    'success': False,
                    'message': 'Next progress assignment not found'
                }), 404
            
            # Check if delay already exists for this pair
            existing_delay = RNDExternalTime.query.filter(
                RNDExternalTime.last_progress_assignment_id == data['last_progress_assignment_id'],
                RNDExternalTime.next_progress_assignment_id == data['next_progress_assignment_id']
            ).first()
            
            if existing_delay:
                return jsonify({
                    'success': False,
                    'message': 'External delay already exists for this progress pair'
                }), 409
        
        # Validation: Check delay_category is valid
        valid_categories = ['PPIC', 'CSR', 'Other']
        if data['delay_category'] not in valid_categories:
            return jsonify({
                'success': False,
                'message': f'Invalid delay_category. Must be one of: {", ".join(valid_categories)}'
            }), 400
        
        # Create external delay record
        external_delay = RNDExternalTime(
            job_id=data['job_id'],
            last_progress_assignment_id=data['last_progress_assignment_id'],
            next_progress_assignment_id=data.get('next_progress_assignment_id'),
            delay_category=data['delay_category'],
            delay_reason=data['delay_reason'],
            delay_notes=data.get('delay_notes'),
            sample_type=job.sample_type,
            external_wait_start=last_progress.finished_at,
            created_by_user_id=current_user.id
        )
        
        db.session.add(external_delay)
        db.session.commit()
        
        logger.info(
            f'External delay created: ID={external_delay.id}, Job={job.job_id}, '
            f'Category={data["delay_category"]}, Reason={data["delay_reason"]}'
        )
        
        return jsonify({
            'success': True,
            'message': 'External delay recorded successfully',
            'data': external_delay.to_dict()
        }), 201
    
    except Exception as e:
        db.session.rollback()
        logger.error(f'Error creating external delay: {str(e)}')
        return jsonify({
            'success': False,
            'message': f'Error creating external delay: {str(e)}'
        }), 500


# ==================== GET EXTERNAL DELAYS FOR JOB ====================

@external_delay_bp.route('/job/<int:job_id>', methods=['GET'])
@login_required
@require_rnd_access
def get_external_delays_for_job(job_id):
    """
    Get all external delays for a specific job
    
    GET /rnd-cloudsphere/api/external-delay/job/123
    
    Response:
    {
        "success": true,
        "data": [
            {
                "id": 1,
                "job_id": 123,
                "delay_category": "PPIC",
                "delay_reason": "Tunggu Planning",
                "external_wait_start": "2026-01-12T12:05:00+07:00",
                "external_wait_end": null,
                "external_wait_hours": null,
                "is_active": true,
                "is_completed": false,
                ...
            }
        ]
    }
    """
    try:
        job = RNDJob.query.get(job_id)
        if not job:
            return jsonify({
                'success': False,
                'message': 'Job not found'
            }), 404
        
        # Get all external delays for this job
        external_delays = RNDExternalTime.query.filter(
            RNDExternalTime.job_id == job_id
        ).order_by(RNDExternalTime.created_at.desc()).all()
        
        return jsonify({
            'success': True,
            'data': [delay.to_dict() for delay in external_delays]
        })
    
    except Exception as e:
        logger.error(f'Error getting external delays: {str(e)}')
        return jsonify({
            'success': False,
            'message': f'Error getting external delays: {str(e)}'
        }), 500


# ==================== COMPLETE EXTERNAL DELAY ====================

@external_delay_bp.route('/<int:delay_id>/complete', methods=['PUT'])
@login_required
def complete_external_delay(delay_id):
    """
    Complete an external delay (auto-triggered when first task in next_progress is checked)
    
    PUT /rnd-cloudsphere/api/external-delay/1/complete
    
    Response:
    {
        "success": true,
        "message": "External delay completed",
        "data": { ... updated RNDExternalTime.to_dict() ... }
    }
    """
    try:
        external_delay = RNDExternalTime.query.get(delay_id)
        if not external_delay:
            return jsonify({
                'success': False,
                'message': 'External delay not found'
            }), 404
        
        if external_delay.is_completed:
            return jsonify({
                'success': False,
                'message': 'External delay is already completed'
            }), 400
        
        # Mark as completed
        external_delay.external_wait_end = datetime.now(jakarta_tz)
        external_delay.is_active = False
        external_delay.calculate_external_wait_hours()
        
        db.session.add(external_delay)
        db.session.commit()
        
        logger.info(
            f'External delay completed: ID={delay_id}, '
            f'Wait time: {external_delay.external_wait_hours} hours'
        )
        
        return jsonify({
            'success': True,
            'message': 'External delay completed',
            'data': external_delay.to_dict()
        })
    
    except Exception as e:
        db.session.rollback()
        logger.error(f'Error completing external delay: {str(e)}')
        return jsonify({
            'success': False,
            'message': f'Error completing external delay: {str(e)}'
        }), 500


# ==================== GET LEAD TIME BREAKDOWN ====================

@external_delay_bp.route('/job/<int:job_id>/lead-time-breakdown', methods=['GET'])
@login_required
@require_rnd_access
def get_lead_time_breakdown(job_id):
    """
    Get detailed lead time breakdown for a job
    (total, internal work, external wait, and all delays)
    
    GET /rnd-cloudsphere/api/external-delay/job/123/lead-time-breakdown
    
    Response:
    {
        "success": true,
        "data": {
            "job_id": 123,
            "job_started_at": "2025-12-29T15:49:00+07:00",
            "job_finished_at": "2026-01-20T14:30:00+07:00",
            "total_lead_time_hours": 432,
            "total_lead_time_days": 18.0,
            "total_lead_time_formatted": "18 days 0 hours",
            "external_wait_time_hours": 72,
            "external_wait_time_days": 3.0,
            "external_wait_time_formatted": "3 days 0 hours",
            "actual_internal_work_hours": 360,
            "actual_internal_work_days": 15.0,
            "actual_internal_work_formatted": "15 days 0 hours",
            "efficiency_percentage": 83.33,
            "external_delays": [
                {
                    "id": 1,
                    "delay_category": "PPIC",
                    "delay_reason": "Tunggu Planning PPIC",
                    "external_wait_hours": 72
                }
            ]
        }
    }
    """
    try:
        job = RNDJob.query.get(job_id)
        if not job:
            return jsonify({
                'success': False,
                'message': 'Job not found'
            }), 404
        
        # Calculate total lead time
        total_lead_time_hours = 0
        total_lead_time_days = 0
        total_lead_time_formatted = "N/A"
        
        if job.started_at and job.finished_at:
            delta = job.finished_at - job.started_at
            total_lead_time_hours = delta.total_seconds() / 3600.0
            total_lead_time_days = total_lead_time_hours / 24.0
            total_lead_time_formatted = format_duration(total_lead_time_hours)
        
        # Calculate external wait time
        external_delays = RNDExternalTime.query.filter(
            RNDExternalTime.job_id == job_id
        ).all()
        
        external_wait_time_hours = 0
        for delay in external_delays:
            if delay.external_wait_hours:
                external_wait_time_hours += delay.external_wait_hours
        
        external_wait_time_days = external_wait_time_hours / 24.0
        external_wait_time_formatted = format_duration(external_wait_time_hours)
        
        # Calculate actual internal work time
        actual_internal_work_hours = total_lead_time_hours - external_wait_time_hours
        actual_internal_work_days = actual_internal_work_hours / 24.0
        actual_internal_work_formatted = format_duration(actual_internal_work_hours)
        
        # Calculate efficiency
        efficiency_percentage = 0
        if total_lead_time_hours > 0:
            efficiency_percentage = round((actual_internal_work_hours / total_lead_time_hours) * 100, 2)
        
        return jsonify({
            'success': True,
            'data': {
                'job_id': job.id,
                'job_job_id': job.job_id,
                'job_started_at': job.started_at.isoformat() if job.started_at else None,
                'job_finished_at': job.finished_at.isoformat() if job.finished_at else None,
                'total_lead_time_hours': round(total_lead_time_hours, 2),
                'total_lead_time_days': round(total_lead_time_days, 2),
                'total_lead_time_formatted': total_lead_time_formatted,
                'external_wait_time_hours': round(external_wait_time_hours, 2),
                'external_wait_time_days': round(external_wait_time_days, 2),
                'external_wait_time_formatted': external_wait_time_formatted,
                'actual_internal_work_hours': round(actual_internal_work_hours, 2),
                'actual_internal_work_days': round(actual_internal_work_days, 2),
                'actual_internal_work_formatted': actual_internal_work_formatted,
                'efficiency_percentage': efficiency_percentage,
                'external_delays': [
                    {
                        'id': delay.id,
                        'last_progress_step_name': delay.last_progress_step_name,
                        'next_progress_step_name': delay.next_progress_step_name,
                        'delay_category': delay.delay_category,
                        'delay_reason': delay.delay_reason,
                        'external_wait_hours': round(delay.external_wait_hours, 2) if delay.external_wait_hours else 0,
                        'is_completed': delay.is_completed
                    }
                    for delay in sorted(external_delays, key=lambda x: x.created_at)
                ]
            }
        })
    
    except Exception as e:
        logger.error(f'Error getting lead time breakdown: {str(e)}')
        return jsonify({
            'success': False,
            'message': f'Error getting lead time breakdown: {str(e)}'
        }), 500


# ==================== DELETE EXTERNAL DELAY ====================

@external_delay_bp.route('/<int:delay_id>', methods=['DELETE'])
@login_required
@require_admin
def delete_external_delay(delay_id):
    """
    Delete an external delay record
    Can only delete if delay is not yet completed
    
    DELETE /rnd-cloudsphere/api/external-delay/1
    
    Response:
    {
        "success": true,
        "message": "External delay deleted successfully"
    }
    """
    try:
        external_delay = RNDExternalTime.query.get(delay_id)
        if not external_delay:
            return jsonify({
                'success': False,
                'message': 'External delay not found'
            }), 404
        
        # Only allow deletion if delay is not completed
        if external_delay.is_completed:
            return jsonify({
                'success': False,
                'message': 'Cannot delete completed external delay'
            }), 400
        
        db.session.delete(external_delay)
        db.session.commit()
        
        logger.info(f'External delay deleted: ID={delay_id}')
        
        return jsonify({
            'success': True,
            'message': 'External delay deleted successfully'
        })
    
    except Exception as e:
        db.session.rollback()
        logger.error(f'Error deleting external delay: {str(e)}')
        return jsonify({
            'success': False,
            'message': f'Error deleting external delay: {str(e)}'
        }), 500


# ==================== HELPER FUNCTIONS ====================

def format_duration(hours):
    """
    Format hours into human-readable duration string
    
    Args:
        hours (float): Duration in hours
    
    Returns:
        str: Formatted string like "3 days 6 hours" or "12 hours"
    """
    if not hours:
        return "0 hours"
    
    days = int(hours // 24)
    remaining_hours = int(hours % 24)
    minutes = int((hours % 1) * 60)
    
    parts = []
    if days > 0:
        parts.append(f"{days} day{'s' if days > 1 else ''}")
    if remaining_hours > 0:
        parts.append(f"{remaining_hours} hour{'s' if remaining_hours > 1 else ''}")
    if minutes > 0 and days == 0:  # Only show minutes if less than 1 day
        parts.append(f"{minutes} minute{'s' if minutes > 1 else ''}")
    
    return " ".join(parts) if parts else "0 hours"


def auto_complete_external_delay_for_task(task_assignment):
    """
    Automatically complete external delay when first task in next_progress is checked
    This function is called from rnd_cloudsphere.py when a task is completed
    
    Args:
        task_assignment (RNDJobTaskAssignment): The task that was completed
    
    Returns:
        RNDExternalTime: The completed external delay, or None if not found
    """
    try:
        progress_assignment = task_assignment.progress_assignment
        
        # Find active external delay for this progress
        external_delay = RNDExternalTime.query.filter(
            RNDExternalTime.next_progress_assignment_id == progress_assignment.id,
            RNDExternalTime.is_active == True
        ).first()
        
        if external_delay:
            # Mark as completed
            external_delay.external_wait_end = datetime.now(jakarta_tz)
            external_delay.is_active = False
            external_delay.calculate_external_wait_hours()
            
            db.session.add(external_delay)
            db.session.commit()
            
            logger.info(
                f'External delay auto-completed: ID={external_delay.id}, '
                f'Wait time: {external_delay.external_wait_hours} hours'
            )
            
            return external_delay
    
    except Exception as e:
        logger.error(f'Error auto-completing external delay: {str(e)}')
        return None


def get_active_external_delay_for_progress(progress_assignment_id):
    """
    Get active external delay for a specific progress assignment (as next_progress)
    
    Args:
        progress_assignment_id (int): Progress assignment ID
    
    Returns:
        RNDExternalTime: Active external delay, or None if not found
    """
    return RNDExternalTime.query.filter(
        RNDExternalTime.next_progress_assignment_id == progress_assignment_id,
        RNDExternalTime.is_active == True
    ).first()
