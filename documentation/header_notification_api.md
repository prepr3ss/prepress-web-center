# Header Notification System API Documentation

## Overview
This document describes the API endpoints required for the header notification system. The API handles CRUD operations for notifications and provides real-time updates to the frontend.

## Database Schema

### Notifications Table
```sql
CREATE TABLE notifications (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    title VARCHAR(255) NOT NULL,
    message TEXT NOT NULL,
    category VARCHAR(50) DEFAULT 'system',
    is_read BOOLEAN DEFAULT FALSE,
    action_url VARCHAR(500),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users (id)
);
```

## API Endpoints

### 1. Get User Notifications
**GET** `/impact/api/notifications`

Retrieves all notifications for the authenticated user, with unread count.

#### Response Format
```json
{
    "success": true,
    "data": {
        "notifications": [
            {
                "id": 1,
                "title": "System Maintenance",
                "message": "System will undergo maintenance tonight at 10 PM",
                "category": "system",
                "is_read": false,
                "action_url": "/impact/maintenance",
                "created_at": "2023-12-01T10:30:00Z",
                "updated_at": "2023-12-01T10:30:00Z"
            },
            {
                "id": 2,
                "title": "New Message from Admin",
                "message": "Please check the updated CTP production schedule",
                "category": "messages",
                "is_read": false,
                "action_url": "/impact/messages/123",
                "created_at": "2023-12-01T09:15:00Z",
                "updated_at": "2023-12-01T09:15:00Z"
            },
            {
                "id": 3,
                "title": "Production Reminder",
                "message": "Daily production report is due today",
                "category": "reminders",
                "is_read": true,
                "action_url": "/impact/reports/production",
                "created_at": "2023-11-30T16:00:00Z",
                "updated_at": "2023-12-01T08:00:00Z"
            }
        ],
        "unread_count": 2,
        "total_count": 3
    }
}
```

#### Query Parameters
- `limit` (optional, default: 50): Maximum number of notifications to return
- `offset` (optional, default: 0): Number of notifications to skip
- `category` (optional): Filter by category (system, messages, reminders)
- `is_read` (optional): Filter by read status (true/false)

#### Example Requests
```bash
# Get all notifications
GET /impact/api/notifications

# Get only unread notifications
GET /impact/api/notifications?is_read=false

# Get only system notifications
GET /impact/api/notifications?category=system

# Get last 10 unread notifications
GET /impact/api/notifications?is_read=false&limit=10
```

### 2. Mark Notification as Read
**POST** `/impact/api/notifications/{id}/read`

Marks a specific notification as read for the authenticated user.

#### Path Parameters
- `id`: Notification ID

#### Request Body
```json
{
    "notification_id": 1
}
```

#### Response Format
```json
{
    "success": true,
    "message": "Notification marked as read",
    "data": {
        "id": 1,
        "is_read": true,
        "updated_at": "2023-12-01T11:00:00Z"
    }
}
```

#### Error Responses
```json
{
    "success": false,
    "error": "Notification not found",
    "code": "NOT_FOUND"
}
```

```json
{
    "success": false,
    "error": "Access denied",
    "code": "ACCESS_DENIED"
}
```

### 3. Delete Notification
**DELETE** `/impact/api/notifications/{id}`

Deletes a specific notification for the authenticated user.

#### Path Parameters
- `id`: Notification ID

#### Response Format
```json
{
    "success": true,
    "message": "Notification deleted successfully",
    "data": {
        "id": 1,
        "deleted": true
    }
}
```

#### Error Responses
```json
{
    "success": false,
    "error": "Notification not found",
    "code": "NOT_FOUND"
}
```

### 4. Mark All Notifications as Read
**POST** `/impact/api/notifications/read-all`

Marks all unread notifications as read for the authenticated user.

#### Request Body
```json
{
    "user_id": 123
}
```

#### Response Format
```json
{
    "success": true,
    "message": "All notifications marked as read",
    "data": {
        "updated_count": 5,
        "unread_count": 0
    }
}
```

### 5. Create Notification (Admin/System)
**POST** `/impact/api/notifications`

Creates a new notification (for admin use or system-generated notifications).

#### Request Body
```json
{
    "user_id": 123,
    "title": "New System Update",
    "message": "System has been updated with new features",
    "category": "system",
    "action_url": "/impact/updates/latest"
}
```

#### Response Format
```json
{
    "success": true,
    "message": "Notification created successfully",
    "data": {
        "id": 45,
        "user_id": 123,
        "title": "New System Update",
        "message": "System has been updated with new features",
        "category": "system",
        "is_read": false,
        "action_url": "/impact/updates/latest",
        "created_at": "2023-12-01T12:00:00Z",
        "updated_at": "2023-12-01T12:00:00Z"
    }
}
```

### 6. Bulk Create Notifications (Admin/System)
**POST** `/impact/api/notifications/bulk`

Creates multiple notifications for multiple users (for admin broadcasts).

#### Request Body
```json
{
    "notifications": [
        {
            "user_ids": [1, 2, 3, 4, 5],
            "title": "System Maintenance",
            "message": "System will be down for maintenance",
            "category": "system",
            "action_url": "/impact/maintenance"
        },
        {
            "user_ids": [2, 3],
            "title": "Production Alert",
            "message": "CTP production needs attention",
            "category": "reminders",
            "action_url": "/impact/ctp/alerts"
        }
    ]
}
```

#### Response Format
```json
{
    "success": true,
    "message": "Bulk notifications created successfully",
    "data": {
        "created_count": 7,
        "notifications": [
            {
                "id": 46,
                "user_id": 1,
                "title": "System Maintenance",
                "message": "System will be down for maintenance",
                "category": "system",
                "is_read": false,
                "action_url": "/impact/maintenance",
                "created_at": "2023-12-01T12:00:00Z"
            }
            // ... more notification objects
        ]
    }
}
```

## Notification Categories

### System Notifications
- System maintenance alerts
- Software updates
- Security alerts
- Configuration changes
- Error reports

### Messages
- Direct messages from other users
- Admin announcements
- Team communications
- Project updates

### Reminders
- Task deadlines
- Report due dates
- Production schedules
- Maintenance reminders

## Error Codes

| Code | Description |
|------|-------------|
| SUCCESS | Operation completed successfully |
| NOT_FOUND | Notification not found |
| ACCESS_DENIED | User doesn't have permission |
| INVALID_INPUT | Invalid request parameters |
| SERVER_ERROR | Internal server error |
| VALIDATION_ERROR | Request validation failed |

## Rate Limiting

- **GET /notifications**: 60 requests per minute per user
- **POST /notifications/{id}/read**: 30 requests per minute per user
- **DELETE /notifications/{id}**: 30 requests per minute per user
- **POST /notifications/read-all**: 10 requests per minute per user
- **POST /notifications**: 20 requests per minute (admin only)

## Security Considerations

1. **Authentication**: All endpoints require user authentication
2. **Authorization**: Users can only access their own notifications
3. **CSRF Protection**: All POST/DELETE requests require CSRF token
4. **Input Validation**: All inputs are validated and sanitized
5. **Rate Limiting**: Prevents abuse and ensures fair usage

## Real-time Updates (Optional Enhancement)

For real-time notification updates, consider implementing:

### WebSocket Endpoint
```
WS /impact/ws/notifications
```

### Server-Sent Events
```
GET /impact/sse/notifications
```

### Push Notifications
```
POST /impact/api/push/subscribe
```

## Mock Data for Development

### Sample Notifications
```json
[
    {
        "id": 1,
        "title": "Welcome to Impact 360",
        "message": "Get started by exploring the dashboard and setting up your profile.",
        "category": "system",
        "is_read": false,
        "action_url": "/impact/dashboard",
        "created_at": "2023-12-01T08:00:00Z",
        "updated_at": "2023-12-01T08:00:00Z"
    },
    {
        "id": 2,
        "title": "CTP Production Alert",
        "message": "Production line 2 needs attention - quality threshold exceeded",
        "category": "reminders",
        "is_read": false,
        "action_url": "/impact/ctp/alerts/2",
        "created_at": "2023-12-01T09:30:00Z",
        "updated_at": "2023-12-01T09:30:00Z"
    },
    {
        "id": 3,
        "title": "New Message from Supervisor",
        "message": "Please review the updated production schedule for next week",
        "category": "messages",
        "is_read": true,
        "action_url": "/impact/messages/456",
        "created_at": "2023-11-30T16:45:00Z",
        "updated_at": "2023-12-01T08:15:00Z"
    },
    {
        "id": 4,
        "title": "System Update Available",
        "message": "Version 2.1.0 is now available with new features and improvements",
        "category": "system",
        "is_read": false,
        "action_url": "/impact/updates/v2.1.0",
        "created_at": "2023-12-01T07:00:00Z",
        "updated_at": "2023-12-01T07:00:00Z"
    },
    {
        "id": 5,
        "title": "Daily Report Reminder",
        "message": "Don't forget to submit your daily production report by 5 PM",
        "category": "reminders",
        "is_read": true,
        "action_url": "/impact/reports/daily",
        "created_at": "2023-11-30T14:00:00Z",
        "updated_at": "2023-11-30T14:00:00Z"
    }
]
```

## Implementation Notes

### Flask Route Examples
```python
from flask import Blueprint, request, jsonify, current_app
from flask_login import login_required, current_user

notifications_bp = Blueprint('notifications', __name__)

@notifications_bp.route('/api/notifications', methods=['GET'])
@login_required
def get_notifications():
    try:
        limit = request.args.get('limit', 50, type=int)
        offset = request.args.get('offset', 0, type=int)
        category = request.args.get('category')
        is_read = request.args.get('is_read', type=bool)
        
        # Query database based on parameters
        notifications = Notification.query.filter_by(user_id=current_user.id)
        
        if category:
            notifications = notifications.filter_by(category=category)
        
        if is_read is not None:
            notifications = notifications.filter_by(is_read=is_read)
        
        notifications = notifications.order_by(Notification.created_at.desc())
        notifications = notifications.offset(offset).limit(limit).all()
        
        unread_count = Notification.query.filter_by(
            user_id=current_user.id, 
            is_read=False
        ).count()
        
        return jsonify({
            'success': True,
            'data': {
                'notifications': [n.to_dict() for n in notifications],
                'unread_count': unread_count,
                'total_count': len(notifications)
            }
        })
        
    except Exception as e:
        current_app.logger.error(f"Error getting notifications: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Failed to load notifications'
        }), 500
```

### Database Model Example
```python
class Notification(db.Model):
    __tablename__ = 'notifications'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    title = db.Column(db.String(255), nullable=False)
    message = db.Column(db.Text, nullable=False)
    category = db.Column(db.String(50), default='system')
    is_read = db.Column(db.Boolean, default=False)
    action_url = db.Column(db.String(500))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'title': self.title,
            'message': self.message,
            'category': self.category,
            'is_read': self.is_read,
            'action_url': self.action_url,
            'created_at': self.created_at.isoformat() + 'Z',
            'updated_at': self.updated_at.isoformat() + 'Z'
        }
```

## Testing

### Unit Tests
```python
def test_get_notifications(client, auth_headers):
    response = client.get('/impact/api/notifications', headers=auth_headers)
    assert response.status_code == 200
    data = json.loads(response.data)
    assert data['success'] == True
    assert 'notifications' in data['data']
    assert 'unread_count' in data['data']

def test_mark_notification_as_read(client, auth_headers):
    response = client.post('/impact/api/notifications/1/read', 
                         headers=auth_headers,
                         json={'notification_id': 1})
    assert response.status_code == 200
    data = json.loads(response.data)
    assert data['success'] == True
```

### Integration Tests
```python
def test_notification_workflow(client, auth_headers):
    # 1. Get initial notifications
    response = client.get('/impact/api/notifications', headers=auth_headers)
    initial_data = json.loads(response.data)['data']
    
    # 2. Mark notification as read
    notification_id = initial_data['notifications'][0]['id']
    response = client.post(f'/impact/api/notifications/{notification_id}/read',
                         headers=auth_headers)
    
    # 3. Verify unread count decreased
    response = client.get('/impact/api/notifications', headers=auth_headers)
    updated_data = json.loads(response.data)['data']
    assert updated_data['unread_count'] == initial_data['unread_count'] - 1
```

This API documentation provides a complete foundation for implementing the backend functionality required by the header notification system.