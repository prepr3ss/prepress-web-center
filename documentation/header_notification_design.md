# Header Notification System Design

## Overview
Comprehensive notification system for the web application featuring a Lucida-style SVG icon positioned to the right of the user information in the '_top_header.html' template. The system displays unread notification counts with a red circular badge and provides a dropdown menu with categorized notifications.

## Architecture

### 1. Component Structure
```
impact-top-header-right
├── notification-dropdown (NEW)
│   ├── notification-toggle-button
│   │   ├── bell-icon (Lucida-style SVG)
│   │   └── notification-badge
│   └── notification-dropdown-menu
│       ├── notification-header
│       ├── notification-categories
│       │   ├── system-notifications
│       │   ├── messages-notifications
│       │   └── reminders-notifications
│       └── notification-footer
└── user-dropdown (EXISTING)
    └── [current user menu]
```

### 2. Icon Design (Lucida-style SVG)
```html
<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round" class="notification-bell-icon">
    <path d="M18 8A6 6 0 0 0 6 8c0 7-3 9-3 9h18s-3-2-3-9"/>
    <path d="M13.73 21a2 2 0 0 1-3.46 0"/>
    <circle cx="12" cy="8" r="2"/>
</svg>
```

## Features

### 1. Visual States
- **Default State**: Gray bell icon
- **New Notifications**: Blue bell icon with red badge showing count
- **All Read**: Gray bell icon, no badge
- **Hover Effects**: Smooth transitions and color changes

### 2. Badge System
- **Red circular badge** positioned at top-right corner of bell icon
- **Dynamic count** display (1-99+, shows "99+" for 100+)
- **Animated appearance** when new notifications arrive
- **Pulse animation** for new notifications

### 3. Dropdown Menu Structure
```html
<div class="notification-dropdown-menu">
    <!-- Header -->
    <div class="notification-header">
        <h6>Notifications</h6>
        <button class="mark-all-read-btn">Mark all as read</button>
    </div>
    
    <!-- Categories -->
    <div class="notification-categories">
        <!-- System Category -->
        <div class="notification-category">
            <div class="category-header">
                <span class="category-title">System</span>
                <span class="category-count">3</span>
            </div>
            <div class="notification-items">
                <!-- Individual notification items -->
            </div>
        </div>
        
        <!-- Messages Category -->
        <div class="notification-category">
            <div class="category-header">
                <span class="category-title">Messages</span>
                <span class="category-count">2</span>
            </div>
            <div class="notification-items">
                <!-- Individual notification items -->
            </div>
        </div>
        
        <!-- Reminders Category -->
        <div class="notification-category">
            <div class="category-header">
                <span class="category-title">Reminders</span>
                <span class="category-count">1</span>
            </div>
            <div class="notification-items">
                <!-- Individual notification items -->
            </div>
        </div>
    </div>
    
    <!-- Footer -->
    <div class="notification-footer">
        <a href="/impact/notifications" class="view-all-link">View all notifications</a>
    </div>
</div>
```

### 4. Notification Item Structure
```html
<div class="notification-item" data-notification-id="123" data-read="false">
    <div class="notification-content">
        <div class="notification-icon">
            <!-- Category-specific icon -->
        </div>
        <div class="notification-details">
            <div class="notification-title">Notification Title</div>
            <div class="notification-message">Notification message content</div>
            <div class="notification-time">2 minutes ago</div>
        </div>
    </div>
    <div class="notification-actions">
        <button class="mark-read-btn" title="Mark as read">
            <svg>...</svg>
        </button>
        <button class="delete-btn" title="Delete">
            <svg>...</svg>
        </button>
    </div>
</div>
```

## CSS Design Specifications

### 1. Notification Button
```css
.notification-toggle-button {
    position: relative;
    background: transparent;
    border: none;
    padding: 0.5rem;
    margin-right: 0.5rem;
    border-radius: 0.375rem;
    transition: all 0.2s ease-in-out;
    cursor: pointer;
}

.notification-toggle-button:hover {
    background-color: rgba(13, 110, 253, 0.05);
}

.notification-toggle-button.has-notifications .notification-bell-icon {
    color: var(--primary-color); /* Blue for new notifications */
}

.notification-toggle-button.no-notifications .notification-bell-icon {
    color: var(--medium-text); /* Gray when no notifications */
}
```

### 2. Notification Badge
```css
.notification-badge {
    position: absolute;
    top: -2px;
    right: -2px;
    background-color: var(--danger-color); /* Red */
    color: white;
    border-radius: 50%;
    min-width: 18px;
    height: 18px;
    font-size: 0.65rem;
    font-weight: 600;
    display: flex;
    align-items: center;
    justify-content: center;
    border: 2px solid white;
    animation: badgeAppear 0.3s ease-out;
}

.notification-badge.pulse {
    animation: badgePulse 2s infinite;
}

@keyframes badgeAppear {
    from {
        transform: scale(0);
        opacity: 0;
    }
    to {
        transform: scale(1);
        opacity: 1;
    }
}

@keyframes badgePulse {
    0% {
        box-shadow: 0 0 0 0 rgba(220, 53, 69, 0.7);
    }
    70% {
        box-shadow: 0 0 0 10px rgba(220, 53, 69, 0);
    }
    100% {
        box-shadow: 0 0 0 0 rgba(220, 53, 69, 0);
    }
}
```

### 3. Dropdown Menu
```css
.notification-dropdown-menu {
    position: absolute;
    top: 100%;
    right: 0;
    width: 380px;
    max-height: 480px;
    background: white;
    border: 1px solid var(--light-border);
    border-radius: 0.5rem;
    box-shadow: 0 0.5rem 1rem rgba(0, 0, 0, 0.15);
    z-index: 1050;
    overflow: hidden;
    display: none;
}

.notification-dropdown-menu.show {
    display: block;
    animation: dropdownSlide 0.2s ease-out;
}

@keyframes dropdownSlide {
    from {
        opacity: 0;
        transform: translateY(-10px);
    }
    to {
        opacity: 1;
        transform: translateY(0);
    }
}
```

### 4. Notification Categories
```css
.notification-category {
    border-bottom: 1px solid var(--light-border);
}

.category-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 0.75rem 1rem;
    background-color: var(--lighter-bg);
    font-weight: 600;
    font-size: 0.875rem;
}

.category-title {
    color: var(--dark-text);
}

.category-count {
    background-color: var(--primary-color);
    color: white;
    border-radius: 12px;
    padding: 0.125rem 0.5rem;
    font-size: 0.75rem;
    font-weight: 600;
}
```

### 5. Notification Items
```css
.notification-item {
    display: flex;
    justify-content: space-between;
    align-items: flex-start;
    padding: 0.75rem 1rem;
    border-bottom: 1px solid var(--light-border);
    transition: background-color 0.2s ease;
    position: relative;
}

.notification-item:hover {
    background-color: var(--lighter-bg);
}

.notification-item.unread {
    background-color: rgba(13, 110, 253, 0.02);
    border-left: 3px solid var(--primary-color);
}

.notification-item.unread::before {
    content: '';
    position: absolute;
    left: 0.5rem;
    top: 1rem;
    width: 8px;
    height: 8px;
    background-color: var(--primary-color);
    border-radius: 50%;
}

.notification-content {
    display: flex;
    align-items: flex-start;
    flex: 1;
    min-width: 0;
}

.notification-icon {
    margin-right: 0.75rem;
    width: 32px;
    height: 32px;
    border-radius: 50%;
    display: flex;
    align-items: center;
    justify-content: center;
    flex-shrink: 0;
}

.notification-icon.system {
    background-color: rgba(13, 110, 253, 0.1);
    color: var(--primary-color);
}

.notification-icon.message {
    background-color: rgba(25, 135, 84, 0.1);
    color: var(--success-color);
}

.notification-icon.reminder {
    background-color: rgba(255, 193, 7, 0.1);
    color: var(--warning-color);
}

.notification-details {
    flex: 1;
    min-width: 0;
}

.notification-title {
    font-weight: 600;
    font-size: 0.875rem;
    color: var(--dark-text);
    margin-bottom: 0.25rem;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
}

.notification-message {
    font-size: 0.8rem;
    color: var(--medium-text);
    margin-bottom: 0.25rem;
    display: -webkit-box;
    -webkit-line-clamp: 2;
    -webkit-box-orient: vertical;
    overflow: hidden;
}

.notification-time {
    font-size: 0.75rem;
    color: var(--medium-text);
}

.notification-actions {
    display: flex;
    gap: 0.25rem;
    opacity: 0;
    transition: opacity 0.2s ease;
}

.notification-item:hover .notification-actions {
    opacity: 1;
}

.notification-actions button {
    background: transparent;
    border: none;
    padding: 0.25rem;
    border-radius: 0.25rem;
    cursor: pointer;
    transition: background-color 0.2s ease;
}

.notification-actions button:hover {
    background-color: rgba(0, 0, 0, 0.05);
}
```

### 6. Responsive Design
```css
@media (max-width: 768px) {
    .notification-dropdown-menu {
        width: 320px;
        right: -1rem;
    }
    
    .notification-item {
        padding: 0.5rem 0.75rem;
    }
    
    .notification-title {
        font-size: 0.8rem;
    }
    
    .notification-message {
        font-size: 0.75rem;
    }
}

@media (max-width: 480px) {
    .notification-dropdown-menu {
        width: calc(100vw - 2rem);
        left: 1rem;
        right: 1rem;
    }
}
```

## JavaScript Functionality

### 1. Core Functions
- `loadNotifications()` - Fetch notifications from API
- `updateNotificationBadge()` - Update badge count and color
- `renderNotifications()` - Render notifications in dropdown
- `markAsRead(notificationId)` - Mark individual notification as read
- `deleteNotification(notificationId)` - Delete notification
- `markAllAsRead()` - Mark all notifications as read

### 2. Event Handlers
- Click on notification bell - Toggle dropdown
- Click outside dropdown - Close dropdown
- Click on notification item - Mark as read and optionally navigate
- Click on action buttons - Mark as read/delete
- Keyboard navigation support

### 3. State Management
- Track unread count
- Track dropdown open/close state
- Cache notifications for performance
- Handle real-time updates

## Integration Points

### 1. Template Integration
Add notification component to `_top_header.html` before user dropdown:

```html
<!-- Notification Dropdown -->
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
        <!-- Notification content will be dynamically inserted here -->
    </div>
</div>
```

### 2. CSS Integration
Include CSS file in main layout or specific templates:
```html
<link rel="stylesheet" href="{{ url_for('static', filename='css/header_notification.css') }}">
```

### 3. JavaScript Integration
Include JavaScript file:
```html
<script src="{{ url_for('static', filename='js/header_notification.js') }}"></script>
```

## Browser Compatibility
- Modern browsers (Chrome 60+, Firefox 55+, Safari 12+, Edge 79+)
- Uses CSS Grid and Flexbox for layout
- CSS custom properties for theming
- ES6+ JavaScript features
- Graceful degradation for older browsers

## Performance Considerations
- Lazy loading of notification content
- Efficient DOM manipulation
- Debounced API calls
- Minimal reflows and repaints
- Optimized animations using CSS transforms

## Accessibility
- Semantic HTML structure
- ARIA labels and roles
- Keyboard navigation support
- Screen reader compatibility
- High contrast mode support
- Focus management