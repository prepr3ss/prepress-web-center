/**
 * Notification System - Real-time Polling
 * Handles fetching, displaying, and marking notifications as read
 */

class NotificationManager {
    constructor() {
        this.pollInterval = 10000; // Poll every 10 seconds
        this.pollTimer = null;
        this.isLoading = false;
        this.maxNotificationsDisplay = 999; // Show max 999 notifications in dropdown
        
        this.init();
    }

    init() {
        // Bind elements
        this.badgeElement = document.getElementById('notificationBadge');
        this.dropdownMenuElement = document.getElementById('notificationDropdownMenu');
        this.notificationListElement = document.getElementById('notificationList');
        this.markAllReadBtnElement = document.getElementById('markAllReadBtn');
        
        // Verify elements exist
        if (!this.badgeElement || !this.notificationListElement) {
            console.warn('NotificationManager: Required elements not found');
            return;
        }
        
        // Start polling
        this.startPolling();
        
        // Load notifications immediately
        this.loadNotifications();
        
        // Mark all read button
        if (this.markAllReadBtnElement) {
            this.markAllReadBtnElement.addEventListener('click', () => this.markAllAsRead());
        }
        
        console.log('✓ NotificationManager initialized');
    }

    startPolling() {
        // Clear existing timer
        if (this.pollTimer) {
            clearInterval(this.pollTimer);
        }
        
        // Poll immediately and then at intervals
        this.pollTimer = setInterval(() => {
            this.loadNotifications();
        }, this.pollInterval);
    }

    stopPolling() {
        if (this.pollTimer) {
            clearInterval(this.pollTimer);
            this.pollTimer = null;
        }
    }

    async loadNotifications() {
        if (this.isLoading) return;
        
        this.isLoading = true;
        
        try {
            // Fetch unread count
            const countResponse = await fetch('/impact/api/notifications/unread-count', {
                method: 'GET',
                headers: {
                    'Content-Type': 'application/json'
                }
            });
            
            if (!countResponse.ok) throw new Error(`HTTP ${countResponse.status}`);
            
            const countData = await countResponse.json();
            const unreadCount = countData.unread_count || 0;
            
            // Update badge
            this.updateBadge(unreadCount);
            
            // Fetch notifications - INCLUDE BOTH READ AND UNREAD
            const notifResponse = await fetch(`/impact/api/notifications?limit=${this.maxNotificationsDisplay}&include_read=true`, {
                method: 'GET',
                headers: {
                    'Content-Type': 'application/json'
                }
            });
            
            if (!notifResponse.ok) throw new Error(`HTTP ${notifResponse.status}`);
            
            const notifData = await notifResponse.json();
            const notifications = notifData.data || [];  // API returns 'data' not 'notifications'
            
            // Render notifications
            this.renderNotifications(notifications);
            
        } catch (error) {
            console.error('Error loading notifications:', error);
            this.showError();
        } finally {
            this.isLoading = false;
        }
    }

    updateBadge(count) {
        if (!this.badgeElement) return;
        
        this.badgeElement.textContent = count > 99 ? '99+' : count;
        
        // Show/hide badge based on count
        if (count > 0) {
            this.badgeElement.classList.add('show');
        } else {
            this.badgeElement.classList.remove('show');
        }
    }

    renderNotifications(notifications) {
        if (!this.notificationListElement) return;
        
        if (notifications.length === 0) {
            this.notificationListElement.innerHTML = `
                <div class="text-center text-muted p-3">
                    <p class="mb-0">No new notifications</p>
                </div>
            `;
            return;
        }
        
        const html = notifications.map(notif => this.createNotificationItem(notif)).join('');
        this.notificationListElement.innerHTML = html;
        
        // Add event listeners to notification items
        document.querySelectorAll('.notification-item').forEach(item => {
            item.addEventListener('click', (e) => {
                e.preventDefault();
                const notifId = item.dataset.notificationId;
                const navigationUrl = item.dataset.navigationUrl;
                
                // Mark as read
                if (notifId) {
                    this.markAsRead(notifId, item);
                }
                
                // Navigate to related page
                if (navigationUrl && navigationUrl !== '#') {
                    setTimeout(() => {
                        window.location.href = navigationUrl;
                    }, 300); // Small delay to show read status change
                }
            });
        });
    }

    createNotificationItem(notif) {
        const isRead = notif.is_read ? 'read' : 'unread';
        const readStatusClass = notif.is_read ? 'opacity-50' : '';
        
        // Extract icon from metadata if available
        let icon = '';
        let navigationUrl = '#';
        try {
            if (notif.metadata) {
                const meta = typeof notif.metadata === 'string' ? JSON.parse(notif.metadata) : notif.metadata;
                // Icons dari title notifikasi sudah ada (🚀 ✅ 🚨 etc)
                // Jadi tidak perlu default icon
                
                // Build navigation URL based on notification type
                navigationUrl = this.getNavigationUrl(notif, meta);
            }
        } catch (e) {
            console.error('Error parsing notification metadata:', e);
            // Fallback to empty
        }
        
        // Format timestamp
        const createdAt = new Date(notif.created_at);
        const timeAgo = this.getTimeAgo(createdAt);
        
        return `
            <li class="notification-item ${isRead} ${readStatusClass}" data-notification-id="${notif.id}" data-navigation-url="${navigationUrl}" style="cursor: pointer;">
                <div class="notification-content">
                    <div class="notification-title">
                        <strong>${this.escapeHtml(notif.title)}</strong>
                        ${!notif.is_read ? '<span class="notification-unread-indicator"></span>' : ''}
                    </div>
                    <p class="notification-message">${this.escapeHtml(notif.message)}</p>
                    <small class="notification-time text-muted">${timeAgo}</small>
                </div>
            </li>
        `;
    }

    getNavigationUrl(notif, metadata) {
        /**
         * Build navigation URL based on notification type and metadata
         */
        switch (notif.notification_type) {
            case 'ctp_problem_new':
            case 'ctp_problem_resolved':
                // Navigate to CTP machine log page
                if (metadata.machine_nickname) {
                    return `/impact/log-ctp/${metadata.machine_nickname}`;
                }
                return '/impact/log-ctp';
            
            case 'rnd_job_created':
            case 'rnd_job_completed':
            case 'rnd_step_completed':
            case 'rnd_team_note_new':
                // Navigate to RND job detail page
                if (metadata.job_db_id) {
                    return `/impact/rnd-cloudsphere/job/${metadata.job_db_id}`;
                }
                return '/impact/rnd-cloudsphere';
            
            case '5w1h_entry_created':
            case '5w1h_entry_status_changed':
                // Navigate to 5W1H entry detail page
                if (metadata.entry_id) {
                    return `/impact/tools/5w1h/${metadata.entry_id}`;
                }
                return '/impact/tools/5w1h';
            
            default:
                return '/impact';
        }
    }

    getTimeAgo(date) {
        const now = new Date();
        const seconds = Math.floor((now - date) / 1000);
        
        if (seconds < 60) return 'just now';
        if (seconds < 3600) return `${Math.floor(seconds / 60)}m ago`;
        if (seconds < 86400) return `${Math.floor(seconds / 3600)}h ago`;
        return `${Math.floor(seconds / 86400)}d ago`;
    }

    escapeHtml(text) {
        const map = {
            '&': '&amp;',
            '<': '&lt;',
            '>': '&gt;',
            '"': '&quot;',
            "'": '&#039;'
        };
        return text.replace(/[&<>"']/g, m => map[m]);
    }

    async markAsRead(notificationId, element) {
        try {
            const response = await fetch(`/impact/api/notifications/${notificationId}/read`, {
                method: 'PUT',
                headers: {
                    'Content-Type': 'application/json'
                }
            });
            
            if (!response.ok) throw new Error(`HTTP ${response.status}`);
            
            // Update UI
            if (element) {
                element.classList.add('read', 'opacity-50');
                element.classList.remove('unread');
            }
            
            // Reload to update unread count
            this.loadNotifications();
            
        } catch (error) {
            console.error('Error marking notification as read:', error);
        }
    }

    async markAllAsRead() {
        try {
            const response = await fetch('/impact/api/notifications/mark-all-read', {
                method: 'PUT',
                headers: {
                    'Content-Type': 'application/json'
                }
            });
            
            if (!response.ok) throw new Error(`HTTP ${response.status}`);
            
            // Reload notifications
            this.loadNotifications();
            
        } catch (error) {
            console.error('Error marking all as read:', error);
        }
    }

    showError() {
        if (!this.notificationListElement) return;
        
        this.notificationListElement.innerHTML = `
            <div class="text-center text-danger p-3">
                <p class="mb-0">Failed to load notifications</p>
                <small>Try refreshing the page</small>
            </div>
        `;
    }

    destroy() {
        this.stopPolling();
    }
}

// Initialize when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    window.notificationManager = new NotificationManager();
});

// Cleanup on page unload
window.addEventListener('beforeunload', () => {
    if (window.notificationManager) {
        window.notificationManager.destroy();
    }
});
