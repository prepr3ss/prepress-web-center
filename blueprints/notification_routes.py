"""
Notification Routes - API endpoints untuk notification system
"""

import logging
from flask import Blueprint, jsonify, request
from flask_login import login_required, current_user
from models import db, UniversalNotification, NotificationRecipient
from services.notification_service import NotificationService

logger = logging.getLogger(__name__)

# Create Blueprint
notification_bp = Blueprint('notifications', __name__, url_prefix='/api/notifications')

# Health check endpoint (must be BEFORE generic /<id> route)
@notification_bp.route('/health', methods=['GET'])
def health_check():
    """
    GET /impact/api/notifications/health
    Health check untuk notification system
    """
    return jsonify({
        'success': True,
        'message': 'Notification service is running'
    })


@notification_bp.route('/unread-count', methods=['GET'])
@login_required
def get_unread_count():
    """
    GET /impact/api/notifications/unread-count
    Get jumlah unread notifications
    """
    try:
        unread_count = NotificationService.get_unread_count(current_user.id)
        
        return jsonify({
            'success': True,
            'unread_count': unread_count
        })
        
    except Exception as e:
        logger.error(f"Error getting unread count: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@notification_bp.route('/mark-all-read', methods=['PUT'])
@login_required
def mark_all_read():
    """
    PUT /impact/api/notifications/mark-all-read
    Mark semua unread notifications sebagai read untuk current user
    """
    try:
        result = NotificationService.mark_all_as_read(current_user.id)
        
        return jsonify({
            'success': True,
            'marked_count': result
        })
        
    except Exception as e:
        logger.error(f"Error marking all as read: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@notification_bp.route('', methods=['GET'])
@login_required
def get_notifications():
    """
    GET /impact/api/notifications
    Get notifikasi untuk current user
    
    Query params:
    - limit: int (default: 50)
    - offset: int (default: 0)
    - include_read: bool (default: true)
    """
    try:
        limit = request.args.get('limit', 50, type=int)
        offset = request.args.get('offset', 0, type=int)
        include_read = request.args.get('include_read', 'true').lower() == 'true'
        
        notifications = NotificationService.get_user_notifications(
            user_id=current_user.id,
            limit=limit,
            offset=offset,
            include_read=include_read
        )
        
        unread_count = NotificationService.get_unread_count(current_user.id)
        
        return jsonify({
            'success': True,
            'data': notifications,
            'unread_count': unread_count,
            'count': len(notifications)
        })
        
    except Exception as e:
        logger.error(f"Error getting notifications: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500



@notification_bp.route('/<int:notification_id>/read', methods=['PUT'])
@login_required
def mark_as_read(notification_id):
    """
    PUT /api/notifications/<id>/read
    Mark notifikasi sebagai sudah dibaca
    """
    try:
        success = NotificationService.mark_as_read(notification_id, current_user.id)
        
        if success:
            return jsonify({
                'success': True,
                'message': 'Notification marked as read'
            })
        else:
            return jsonify({
                'success': False,
                'error': 'Notification not found for this user'
            }), 404
            
    except Exception as e:
        logger.error(f"Error marking notification as read: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@notification_bp.route('/<int:notification_id>', methods=['GET'])
@login_required
def get_notification_detail(notification_id):
    """
    GET /impact/api/notifications/<id>
    Get detail notifikasi tertentu
    """
    try:
        # Check if user is recipient
        recipient = NotificationRecipient.query.filter_by(
            notification_id=notification_id,
            user_id=current_user.id
        ).first()
        
        if not recipient:
            return jsonify({
                'success': False,
                'error': 'Notification not found'
            }), 404
        
        notification = UniversalNotification.query.get(notification_id)
        
        if not notification:
            return jsonify({
                'success': False,
                'error': 'Notification not found'
            }), 404
        
        data = notification.to_dict(include_recipient_status=current_user.id)
        
        return jsonify({
            'success': True,
            'data': data
        })
        
    except Exception as e:
        logger.error(f"Error getting notification detail: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500
