# Header Notification System Implementation Guide

## File Structure
```
static/
├── css/
│   └── header_notification.css
├── js/
│   └── header_notification.js
└── img/
    └── notification-icons.svg
templates/
└── _top_header.html (modified)
```

## Step 1: CSS Implementation

Create `static/css/header_notification.css` with the complete styling from the design document.

## Step 2: JavaScript Implementation

Create `static/js/header_notification.js`:

```javascript
/**
 * Header Notification System
 * Manages notification display, interactions, and state
 */
class HeaderNotificationSystem {
    constructor() {
        this.notifications = [];
        this.unreadCount = 0;
        this.isDropdownOpen = false;
        this.isLoading = false;
        this.apiEndpoint = '/impact/api/notifications';
        this.markReadEndpoint = '/impact/api/notifications/{id}/read';
        this.deleteEndpoint = '/impact/api/notifications/{id}';
        this.markAllReadEndpoint = '/impact/api/notifications/read-all';
        
        this.init();
    }

    init() {
        this.cacheElements();
        this.bindEvents();
        this.loadNotifications();
        this.startPolling();
    }

    cacheElements() {
        this.elements = {
            toggleButton: document.getElementById('notificationDropdown'),
            badge: document.getElementById('notificationBadge'),
            dropdown: document.querySelector('.notification-dropdown-menu'),
            notificationList: document.getElementById('notificationList'),
            markAllReadBtn: document.getElementById('markAllReadBtn'),
            noNotifications: document.getElementById('noNotifications')
        };
    }

    bindEvents() {
        // Toggle dropdown
        if (this.elements.toggleButton) {
            this.elements.toggleButton.addEventListener('click', (e) => {
                e.preventDefault();
                this.toggleDropdown();
            });
        }

        // Close dropdown when clicking outside
        document.addEventListener('click', (e) => {
            if (this.isDropdownOpen && !this.containsNotificationElements(e.target)) {
                this.closeDropdown();
            }
        });

        // Mark all as read
        if (this.elements.markAllReadBtn) {
            this.elements.markAllReadBtn.addEventListener('click', () => {
                this.markAllAsRead();
            });
        }

        // Keyboard navigation
        document.addEventListener('keydown', (e) => {
            if (e.key === 'Escape' && this.isDropdownOpen) {
                this.closeDropdown();
            }
        });
    }

    containsNotificationElements(target) {
        return this.elements.toggleButton?.contains(target) || 
               this.elements.dropdown?.contains(target);
    }

    async loadNotifications() {
        if (this.isLoading) return;
        
        this.isLoading = true;
        this.showLoadingState();

        try {
            const response = await fetch(this.apiEndpoint);
            if (!response.ok) throw new Error('Failed to load notifications');
            
            const data = await response.json();
            this.notifications = data.notifications || [];
            this.unreadCount = data.unread_count || 0;
            
            this.renderNotifications();
            this.updateBadge();
            
        } catch (error) {
            console.error('Error loading notifications:', error);
            this.showErrorState();
        } finally {
            this.isLoading = false;
            this.hideLoadingState();
        }
    }

    renderNotifications() {
        if (!this.elements.notificationList) return;

        if (this.notifications.length === 0) {
            this.showEmptyState();
            return;
        }

        const groupedNotifications = this.groupNotificationsByCategory();
        let html = '';

        Object.entries(groupedNotifications).forEach(([category, items]) => {
            html += this.renderCategory(category, items);
        });

        this.elements.notificationList.innerHTML = html;
        this.bindNotificationItemEvents();
    }

    groupNotificationsByCategory() {
        const groups = {
            system: [],
            messages: [],
            reminders: []
        };

        this.notifications.forEach(notification => {
            const category = notification.category || 'system';
            if (groups[category]) {
                groups[category].push(notification);
            }
        });

        return groups;
    }

    renderCategory(category, items) {
        const categoryConfig = {
            system: { icon: '⚙️', title: 'System', color: 'primary' },
            messages: { icon: '💬', title: 'Messages', color: 'success' },
            reminders: { icon: '⏰', title: 'Reminders', color: 'warning' }
        };

        const config = categoryConfig[category] || categoryConfig.system;
        const unreadCount = items.filter(item => !item.is_read).length;

        let html = `
            <div class="notification-category">
                <div class="category-header">
                    <span class="category-title">
                        <span class="category-icon">${config.icon}</span>
                        ${config.title}
                    </span>
                    ${unreadCount > 0 ? `<span class="category-count">${unreadCount}</span>` : ''}
                </div>
                <div class="notification-items">
        `;

        items.forEach(notification => {
            html += this.renderNotificationItem(notification, config.color);
        });

        html += `
                </div>
            </div>
        `;

        return html;
    }

    renderNotificationItem(notification, colorClass) {
        const timeAgo = this.formatTimeAgo(notification.created_at);
        const unreadClass = !notification.is_read ? 'unread' : '';
        
        return `
            <div class="notification-item ${unreadClass}" 
                 data-notification-id="${notification.id}"
                 data-read="${notification.is_read}">
                <div class="notification-content">
                    <div class="notification-icon ${colorClass}">
                        ${this.getCategoryIcon(notification.category)}
                    </div>
                    <div class="notification-details">
                        <div class="notification-title">${notification.title}</div>
                        <div class="notification-message">${notification.message}</div>
                        <div class="notification-time">${timeAgo}</div>
                    </div>
                </div>
                <div class="notification-actions">
                    ${!notification.is_read ? `
                        <button class="mark-read-btn" 
                                data-notification-id="${notification.id}"
                                title="Mark as read">
                            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                                <polyline points="20 6 9 17 4 12"></polyline>
                            </svg>
                        </button>
                    ` : ''}
                    <button class="delete-btn" 
                            data-notification-id="${notification.id}"
                            title="Delete">
                        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                            <polyline points="3 6 5 6 21 6"></polyline>
                            <path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"></path>
                        </svg>
                    </button>
                </div>
            </div>
        `;
    }

    getCategoryIcon(category) {
        const icons = {
            system: `<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <circle cx="12" cy="12" r="3"></circle>
                <path d="M12 1v6m0 6v6m4.22-13.22l4.24 4.24M1.54 1.54l4.24 4.24M20.46 20.46l-4.24-4.24M1.54 20.46l4.24-4.24"></path>
            </svg>`,
            messages: `<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"></path>
            </svg>`,
            reminders: `<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <circle cx="12" cy="12" r="10"></circle>
                <polyline points="12 6 12 12 16 14"></polyline>
            </svg>`
        };
        return icons[category] || icons.system;
    }

    formatTimeAgo(timestamp) {
        const now = new Date();
        const time = new Date(timestamp);
        const diffInSeconds = Math.floor((now - time) / 1000);

        if (diffInSeconds < 60) return 'Just now';
        if (diffInSeconds < 3600) return `${Math.floor(diffInSeconds / 60)} minutes ago`;
        if (diffInSeconds < 86400) return `${Math.floor(diffInSeconds / 3600)} hours ago`;
        if (diffInSeconds < 604800) return `${Math.floor(diffInSeconds / 86400)} days ago`;
        
        return time.toLocaleDateString();
    }

    bindNotificationItemEvents() {
        // Mark as read buttons
        document.querySelectorAll('.mark-read-btn').forEach(btn => {
            btn.addEventListener('click', (e) => {
                e.stopPropagation();
                const notificationId = btn.dataset.notificationId;
                this.markAsRead(notificationId);
            });
        });

        // Delete buttons
        document.querySelectorAll('.delete-btn').forEach(btn => {
            btn.addEventListener('click', (e) => {
                e.stopPropagation();
                const notificationId = btn.dataset.notificationId;
                this.deleteNotification(notificationId);
            });
        });

        // Notification item clicks
        document.querySelectorAll('.notification-item').forEach(item => {
            item.addEventListener('click', (e) => {
                if (!e.target.closest('.notification-actions')) {
                    const notificationId = item.dataset.notificationId;
                    const isRead = item.dataset.read === 'true';
                    
                    if (!isRead) {
                        this.markAsRead(notificationId);
                    }
                    
                    // Optional: Navigate to notification target
                    const notification = this.notifications.find(n => n.id == notificationId);
                    if (notification && notification.action_url) {
                        window.location.href = notification.action_url;
                    }
                }
            });
        });
    }

    async markAsRead(notificationId) {
        try {
            const response = await fetch(this.markReadEndpoint.replace('{id}', notificationId), {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': this.getCSRFToken()
                }
            });

            if (!response.ok) throw new Error('Failed to mark as read');

            // Update local state
            const notification = this.notifications.find(n => n.id == notificationId);
            if (notification) {
                notification.is_read = true;
                this.unreadCount = Math.max(0, this.unreadCount - 1);
            }

            // Update UI
            this.updateNotificationItem(notificationId, true);
            this.updateBadge();

        } catch (error) {
            console.error('Error marking notification as read:', error);
            this.showErrorMessage('Failed to mark notification as read');
        }
    }

    async deleteNotification(notificationId) {
        if (!confirm('Are you sure you want to delete this notification?')) {
            return;
        }

        try {
            const response = await fetch(this.deleteEndpoint.replace('{id}', notificationId), {
                method: 'DELETE',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': this.getCSRFToken()
                }
            });

            if (!response.ok) throw new Error('Failed to delete notification');

            // Update local state
            const notificationIndex = this.notifications.findIndex(n => n.id == notificationId);
            if (notificationIndex !== -1) {
                const notification = this.notifications[notificationIndex];
                if (!notification.is_read) {
                    this.unreadCount = Math.max(0, this.unreadCount - 1);
                }
                this.notifications.splice(notificationIndex, 1);
            }

            // Update UI
            this.removeNotificationItem(notificationId);
            this.updateBadge();

        } catch (error) {
            console.error('Error deleting notification:', error);
            this.showErrorMessage('Failed to delete notification');
        }
    }

    async markAllAsRead() {
        if (this.unreadCount === 0) return;

        try {
            const response = await fetch(this.markAllReadEndpoint, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': this.getCSRFToken()
                }
            });

            if (!response.ok) throw new Error('Failed to mark all as read');

            // Update local state
            this.notifications.forEach(notification => {
                notification.is_read = true;
            });
            this.unreadCount = 0;

            // Update UI
            this.renderNotifications();
            this.updateBadge();

        } catch (error) {
            console.error('Error marking all notifications as read:', error);
            this.showErrorMessage('Failed to mark all notifications as read');
        }
    }

    updateNotificationItem(notificationId, isRead) {
        const item = document.querySelector(`[data-notification-id="${notificationId}"]`);
        if (item) {
            item.dataset.read = isRead;
            if (isRead) {
                item.classList.remove('unread');
                const markReadBtn = item.querySelector('.mark-read-btn');
                if (markReadBtn) {
                    markReadBtn.remove();
                }
            }
        }
    }

    removeNotificationItem(notificationId) {
        const item = document.querySelector(`[data-notification-id="${notificationId}"]`);
        if (item) {
            item.style.animation = 'slideOut 0.3s ease-out';
            setTimeout(() => {
                item.remove();
                if (this.notifications.length === 0) {
                    this.showEmptyState();
                }
            }, 300);
        }
    }

    updateBadge() {
        if (!this.elements.badge) return;

        const hasNotifications = this.unreadCount > 0;
        const badgeText = this.unreadCount > 99 ? '99+' : this.unreadCount.toString();

        this.elements.badge.textContent = badgeText;
        this.elements.badge.style.display = hasNotifications ? 'flex' : 'none';

        if (this.elements.toggleButton) {
            this.elements.toggleButton.classList.toggle('has-notifications', hasNotifications);
            this.elements.toggleButton.classList.toggle('no-notifications', !hasNotifications);
        }

        // Add pulse animation for new notifications
        if (hasNotifications) {
            this.elements.badge.classList.add('pulse');
        } else {
            this.elements.badge.classList.remove('pulse');
        }
    }

    toggleDropdown() {
        if (this.isDropdownOpen) {
            this.closeDropdown();
        } else {
            this.openDropdown();
        }
    }

    openDropdown() {
        if (!this.elements.dropdown) return;

        this.elements.dropdown.classList.add('show');
        this.isDropdownOpen = true;
        
        // Mark notifications as seen (not read) when dropdown opens
        this.markNotificationsAsSeen();
    }

    closeDropdown() {
        if (!this.elements.dropdown) return;

        this.elements.dropdown.classList.remove('show');
        this.isDropdownOpen = false;
    }

    async markNotificationsAsSeen() {
        // Optional: Call API to mark notifications as seen
        // This is different from marking as read
    }

    showLoadingState() {
        if (this.elements.notificationList) {
            this.elements.notificationList.innerHTML = `
                <div class="notification-loading">
                    <div class="spinner-border spinner-border-sm" role="status">
                        <span class="visually-hidden">Loading...</span>
                    </div>
                    Loading notifications...
                </div>
            `;
        }
    }

    hideLoadingState() {
        // Loading state is replaced when notifications are rendered
    }

    showEmptyState() {
        if (this.elements.notificationList) {
            this.elements.notificationList.innerHTML = `
                <div class="notification-empty">
                    <div class="empty-icon">🔔</div>
                    <div class="empty-title">No notifications</div>
                    <div class="empty-message">You're all caught up!</div>
                </div>
            `;
        }
    }

    showErrorState() {
        if (this.elements.notificationList) {
            this.elements.notificationList.innerHTML = `
                <div class="notification-error">
                    <div class="error-icon">⚠️</div>
                    <div class="error-title">Error loading notifications</div>
                    <button class="btn btn-sm btn-primary retry-btn" onclick="headerNotificationSystem.loadNotifications()">
                        Retry
                    </button>
                </div>
            `;
        }
    }

    showErrorMessage(message) {
        // Simple toast or alert for now
        // In production, use a proper toast system
        console.error(message);
    }

    getCSRFToken() {
        const meta = document.querySelector('meta[name="csrf-token"]');
        return meta ? meta.getAttribute('content') : '';
    }

    startPolling() {
        // Check for new notifications every 30 seconds
        setInterval(() => {
            if (!this.isDropdownOpen) {
                this.loadNotifications();
            }
        }, 30000);
    }

    // Public method to add new notifications (for real-time updates)
    addNotification(notification) {
        this.notifications.unshift(notification);
        if (!notification.is_read) {
            this.unreadCount++;
        }
        this.renderNotifications();
        this.updateBadge();
        
        // Show brief animation for new notification
        this.showNewNotificationAnimation();
    }

    showNewNotificationAnimation() {
        if (this.elements.toggleButton) {
            this.elements.toggleButton.classList.add('new-notification');
            setTimeout(() => {
                this.elements.toggleButton.classList.remove('new-notification');
            }, 1000);
        }
    }
}

// Initialize the notification system when DOM is ready
let headerNotificationSystem;

document.addEventListener('DOMContentLoaded', () => {
    headerNotificationSystem = new HeaderNotificationSystem();
});

// Make it globally accessible for debugging
window.headerNotificationSystem = headerNotificationSystem;
```

## Step 3: Template Integration

Update `templates/_top_header.html`:

```html
<header class="impact-top-header">
    <div class="impact-top-header-left d-flex align-items-center">
        <img src="{{ url_for('static', filename='img/impact360.png') }}" class="impact-top-logo" alt="Impact 360">
        <span class="impact-top-title">Impact 360</span>
    </div>
    {% if current_user.is_authenticated %}
    <div class="impact-top-header-right">
        <!-- Notification Dropdown (NEW) -->
        <div class="dropdown me-2">
            <button class="btn notification-toggle-button" type="button" id="notificationDropdown" data-bs-toggle="dropdown" aria-expanded="false">
                <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round" class="notification-bell-icon">
                    <path d="M18 8A6 6 0 0 0 6 8c0 7-3 9-3 9h18s-3-2-3-9"/>
                    <path d="M13.73 21a2 2 0 0 1-3.46 0"/>
                    <circle cx="12" cy="8" r="2"/>
                </svg>
                <span class="notification-badge" id="notificationBadge">0</span>
            </button>
            <div class="dropdown-menu dropdown-menu-end notification-dropdown-menu" aria-labelledby="notificationDropdown">
                <div class="notification-header">
                    <h6>Notifications</h6>
                    <button class="btn btn-sm btn-outline-primary mark-all-read-btn" id="markAllReadBtn">
                        Mark all as read
                    </button>
                </div>
                <div class="notification-list" id="notificationList">
                    <!-- Notifications will be dynamically inserted here -->
                </div>
                <div class="notification-footer">
                    <a href="/impact/notifications" class="view-all-link">View all notifications</a>
                </div>
            </div>
        </div>
        
        <!-- User Dropdown (EXISTING) -->
        <div class="dropdown">
            <button class="btn impact-user-toggle d-flex align-items-center" type="button" id="userDropdown" data-bs-toggle="dropdown" aria-expanded="false">
                <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round" class="me-2" aria-hidden="true">
                    <circle cx="12" cy="8" r="3.2" />
                    <path d="M5 20.5c.7-2.8 3.1-4.5 7-4.5s6.3 1.7 7 4.5" />
                </svg>
                <span class="impact-user-name me-1">{{ current_user.name or current_user.username }}</span>
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round" class="impact-user-chevron" aria-hidden="true">
                    <polyline points="6 9 12 15 18 9" />
                </svg>
            </button>
            <ul class="dropdown-menu dropdown-menu-end" aria-labelledby="userDropdown">
                <li>
                    <a class="dropdown-item" href="/impact/settings/change-password">
                        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round" class="me-2" aria-hidden="true">
                            <circle cx="7" cy="17" r="2.2" />
                            <path d="M3 17a4 4 0 1 1 7.3-2.2L21 4l1 1-3 3 2 2-1.5 1.5-2-2-2.5 2.5" />
                        </svg>
                        Ganti Password
                    </a>
                </li>
                <li><hr class="dropdown-divider"></li>
                <li>
                    <a class="dropdown-item text-danger" href="{{ url_for('logout') }}">
                        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round" class="me-2" aria-hidden="true">
                            <path d="M10 5H6a2 2 0 0 0-2 2v10a2 2 0 0 0 2 2h4" />
                            <polyline points="15 17 20 12 15 7" />
                            <line x1="9" y1="12" x2="20" y2="12" />
                        </svg>
                        Logout
                    </a>
                </li>
            </ul>
        </div>
    </div>
    {% endif %}
</header>

<!-- Include notification system assets -->
<link rel="stylesheet" href="{{ url_for('static', filename='css/header_notification.css') }}">
<script src="{{ url_for('static', filename='js/header_notification.js') }}"></script>
```

## Step 4: Additional CSS for Loading and Empty States

Add these additional styles to `header_notification.css`:

```css
/* Loading State */
.notification-loading {
    display: flex;
    align-items: center;
    justify-content: center;
    padding: 2rem;
    color: var(--medium-text);
}

.notification-loading .spinner-border {
    margin-right: 0.5rem;
}

/* Empty State */
.notification-empty {
    text-align: center;
    padding: 2rem;
    color: var(--medium-text);
}

.empty-icon {
    font-size: 2rem;
    margin-bottom: 0.5rem;
    opacity: 0.5;
}

.empty-title {
    font-weight: 600;
    margin-bottom: 0.25rem;
}

.empty-message {
    font-size: 0.875rem;
}

/* Error State */
.notification-error {
    text-align: center;
    padding: 2rem;
    color: var(--danger-color);
}

.error-icon {
    font-size: 2rem;
    margin-bottom: 0.5rem;
}

.error-title {
    font-weight: 600;
    margin-bottom: 1rem;
}

/* New Notification Animation */
.notification-toggle-button.new-notification {
    animation: newNotificationPulse 1s ease-out;
}

@keyframes newNotificationPulse {
    0% {
        transform: scale(1);
    }
    50% {
        transform: scale(1.2);
    }
    100% {
        transform: scale(1);
    }
}

/* Slide Out Animation */
@keyframes slideOut {
    to {
        opacity: 0;
        transform: translateX(100%);
    }
}

/* Category Icon */
.category-icon {
    margin-right: 0.5rem;
    font-size: 0.875rem;
}

/* Footer */
.notification-footer {
    padding: 0.75rem 1rem;
    border-top: 1px solid var(--light-border);
    text-align: center;
}

.view-all-link {
    color: var(--primary-color);
    text-decoration: none;
    font-size: 0.875rem;
    font-weight: 500;
    transition: color 0.2s ease;
}

.view-all-link:hover {
    color: var(--primary-darker);
    text-decoration: underline;
}
```

## Step 5: Backend API Requirements

The frontend expects these API endpoints:

### GET /impact/api/notifications
```json
{
    "notifications": [
        {
            "id": 1,
            "title": "System Update",
            "message": "System will be updated tonight at 10 PM",
            "category": "system",
            "is_read": false,
            "created_at": "2023-12-01T10:30:00Z",
            "action_url": "/impact/system/updates"
        }
    ],
    "unread_count": 3
}
```

### POST /impact/api/notifications/{id}/read
Marks a specific notification as read.

### DELETE /impact/api/notifications/{id}
Deletes a specific notification.

### POST /impact/api/notifications/read-all
Marks all notifications as read.

## Testing Checklist

1. **Visual Tests**
   - [ ] Bell icon appears correctly
   - [ ] Badge shows correct count
   - [ ] Badge color changes based on state
   - [ ] Dropdown opens/closes properly
   - [ ] Categories are displayed correctly
   - [ ] Responsive design works on mobile

2. **Interaction Tests**
   - [ ] Clicking bell toggles dropdown
   - [ ] Clicking outside closes dropdown
   - [ ] Mark as read functionality works
   - [ ] Delete functionality works
   - [ ] Mark all as read works
   - [ ] Keyboard navigation (ESC to close)

3. **State Tests**
   - [ ] Badge updates when notifications are read/deleted
   - [ ] Unread items are visually distinguished
   - [ ] Loading state shows correctly
   - [ ] Empty state shows correctly
   - [ ] Error state handles gracefully

4. **Performance Tests**
   - [ ] Notifications load quickly
   - [ ] Animations are smooth
   - [ ] Polling doesn't impact performance
   - [ ] Memory usage is reasonable

## Browser Compatibility

- Chrome 60+
- Firefox 55+
- Safari 12+
- Edge 79+

Features used:
- CSS Grid and Flexbox
- CSS Custom Properties
- ES6+ JavaScript
- Fetch API
- CSS Animations and Transitions