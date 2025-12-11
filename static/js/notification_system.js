/**
 * Notification System for Impact 360
 * Handles real-time notifications for CTP machine problems
 */

class NotificationSystem {
    constructor() {
        this.notifications = [];
        this.unreadCount = 0;
        this.pollingInterval = null;
        this.isDropdownOpen = false;
        this.isLoading = false;
        
        this.init();
    }

    init() {
        this.setupEventListeners();
        this.startPolling();
        this.loadNotifications();
    }

    setupEventListeners() {
        const notificationDropdown = document.getElementById('notificationDropdown');
        const notificationDropdownMenu = document.getElementById('notificationDropdownMenu');
        const markAllReadBtn = document.getElementById('markAllReadBtn');

        if (notificationDropdown && notificationDropdownMenu) {
            console.log('Setting up notification dropdown event listeners');
            
            // Wait a bit for Bootstrap to be fully available
            setTimeout(() => {
                try {
                    // Initialize Bootstrap dropdown
                    const dropdown = new bootstrap.Dropdown(notificationDropdown, {
                        autoClose: true,
                        reference: 'toggle'
                    });

                    // Store dropdown instance
                    notificationDropdown.dropdownInstance = dropdown;
                    console.log('Bootstrap dropdown initialized successfully');

                    // Handle dropdown visibility changes
                    notificationDropdownMenu.addEventListener('show.bs.dropdown', () => {
                        console.log('Dropdown shown');
                        this.isDropdownOpen = true;
                        this.markNotificationsAsViewed();
                    });

                    notificationDropdownMenu.addEventListener('hide.bs.dropdown', () => {
                        console.log('Dropdown hidden');
                        this.isDropdownOpen = false;
                    });

                    // Keyboard navigation
                    notificationDropdown.addEventListener('keydown', (e) => {
                        if (e.key === 'Enter' || e.key === ' ') {
                            e.preventDefault();
                            dropdown.toggle();
                        }
                    });
                } catch (error) {
                    console.error('Error initializing Bootstrap dropdown:', error);
                    // Fallback: manually handle click events
                    notificationDropdown.addEventListener('click', (e) => {
                        e.preventDefault();
                        e.stopPropagation();
                        this.toggleManualDropdown();
                    });
                }
            }, 100);
        } else {
            console.error('Notification dropdown elements not found:', {
                notificationDropdown: !!notificationDropdown,
                notificationDropdownMenu: !!notificationDropdownMenu
            });
        }

        // Mark all as read button
        if (markAllReadBtn) {
            markAllReadBtn.addEventListener('click', (e) => {
                e.preventDefault();
                e.stopPropagation();
                this.markAllAsRead();
            });
        }

        // Close dropdown when clicking outside
        document.addEventListener('click', (e) => {
            if (this.isDropdownOpen &&
                !e.target.closest('#notificationDropdown') &&
                !e.target.closest('#notificationDropdownMenu')) {
                this.closeDropdown();
            }
        });

        // Keyboard navigation for dropdown items
        document.addEventListener('keydown', (e) => {
            if (this.isDropdownOpen && e.key === 'Escape') {
                this.closeDropdown();
                document.getElementById('notificationDropdown').focus();
            }
        });
    }

    toggleDropdown() {
        const notificationDropdown = document.getElementById('notificationDropdown');
        if (notificationDropdown && notificationDropdown.dropdownInstance) {
            notificationDropdown.dropdownInstance.toggle();
        }
    }

    closeDropdown() {
        const notificationDropdown = document.getElementById('notificationDropdown');
        if (notificationDropdown && notificationDropdown.dropdownInstance) {
            notificationDropdown.dropdownInstance.hide();
        } else {
            this.hideManualDropdown();
        }
    }

    toggleManualDropdown() {
        const notificationDropdown = document.getElementById('notificationDropdown');
        const notificationDropdownMenu = document.getElementById('notificationDropdownMenu');
        
        if (!notificationDropdown || !notificationDropdownMenu) return;
        
        if (this.isDropdownOpen) {
            this.hideManualDropdown();
        } else {
            this.showManualDropdown();
        }
    }

    showManualDropdown() {
        const notificationDropdownMenu = document.getElementById('notificationDropdownMenu');
        if (notificationDropdownMenu) {
            notificationDropdownMenu.style.display = 'block';
            notificationDropdownMenu.style.opacity = '1';
            notificationDropdownMenu.style.visibility = 'visible';
            notificationDropdownMenu.classList.add('show');
            this.isDropdownOpen = true;
            
            // Add click outside listener
            setTimeout(() => {
                document.addEventListener('click', this.handleOutsideClick);
            }, 100);
        }
    }

    hideManualDropdown() {
        const notificationDropdownMenu = document.getElementById('notificationDropdownMenu');
        if (notificationDropdownMenu) {
            notificationDropdownMenu.style.display = 'none';
            notificationDropdownMenu.style.opacity = '0';
            notificationDropdownMenu.style.visibility = 'hidden';
            notificationDropdownMenu.classList.remove('show');
            this.isDropdownOpen = false;
            
            // Remove click outside listener
            document.removeEventListener('click', this.handleOutsideClick);
        }
    }

    handleOutsideClick = (e) => {
        const notificationDropdown = document.getElementById('notificationDropdown');
        const notificationDropdownMenu = document.getElementById('notificationDropdownMenu');
        
        if (this.isDropdownOpen &&
            !e.target.closest('#notificationDropdown') &&
            !e.target.closest('#notificationDropdownMenu')) {
            this.hideManualDropdown();
        }
    }

    async loadNotifications() {
        if (this.isLoading) return;
        
        this.isLoading = true;
        this.showLoadingState();

        try {
            const response = await fetch('/impact/api/ctp-notifications', {
                method: 'GET',
                headers: {
                    'Content-Type': 'application/json',
                    'X-Requested-With': 'XMLHttpRequest'
                }
            });

            const data = await response.json();

            if (data.success) {
                this.notifications = data.data || [];
                this.updateNotificationUI();
                this.updateBadge();
            } else {
                console.error('Failed to load notifications:', data.error);
                this.showErrorState();
            }
        } catch (error) {
            console.error('Error loading notifications:', error);
            this.showErrorState();
        } finally {
            this.isLoading = false;
        }
    }

    async markAsRead(notificationId) {
        try {
            const response = await fetch(`/impact/api/ctp-notifications/${notificationId}/read`, {
                method: 'PUT',
                headers: {
                    'Content-Type': 'application/json',
                    'X-Requested-With': 'XMLHttpRequest'
                }
            });

            const data = await response.json();

            if (data.success) {
                // Update local notification state
                const notification = this.notifications.find(n => n.id === notificationId);
                if (notification) {
                    notification.is_read = true;
                    notification.read_at = new Date().toISOString();
                }

                this.updateNotificationUI();
                this.updateBadge();
            } else {
                console.error('Failed to mark notification as read:', data.error);
            }
        } catch (error) {
            console.error('Error marking notification as read:', error);
            this.showToast('Error marking notification as read', 'danger');
        }
    }

    async markAllAsRead() {
        const unreadNotifications = this.notifications.filter(n => !n.is_read);
        
        if (unreadNotifications.length === 0) {
            return;
        }

        try {
            const promises = unreadNotifications.map(notification => 
                this.markAsRead(notification.id)
            );

            await Promise.all(promises);
            
            // Refresh notifications after marking all as read
            await this.loadNotifications();
            
        } catch (error) {
            console.error('Error marking all notifications as read:', error);
        }
    }

    markNotificationsAsViewed() {
        // This is for analytics/tracking purposes
        // Notifications are marked as read when user clicks on them
    }

    updateNotificationUI() {
        const notificationList = document.getElementById('notificationList');
        
        if (!notificationList) return;

        // Only show unread notifications in dropdown
        const unreadNotifications = this.notifications.filter(n => !n.is_read);

        if (unreadNotifications.length === 0) {
            notificationList.innerHTML = this.getEmptyStateHTML();
            return;
        }

        const notificationsHTML = unreadNotifications.map(notification =>
            this.getNotificationItemHTML(notification)
        ).join('');

        notificationList.innerHTML = notificationsHTML;

        // Add click handlers to notification items
        this.attachNotificationItemHandlers();
    }

    getNotificationItemHTML(notification) {
        const isUnread = !notification.is_read;
        const timeAgo = this.formatTimeAgo(notification.created_at);
        const typeClass = this.getNotificationTypeClass(notification.notification_type);
        const typeLabel = this.getNotificationTypeLabel(notification.notification_type);

        return `
            <li class="notification-item ${isUnread ? 'unread' : ''}"
                data-notification-id="${notification.id}"
                tabindex="0"
                role="button"
                aria-label="Notification: ${notification.message}">
                <div class="notification-header">
                    <div class="notification-machine">${this.escapeHtml(notification.machine_name)}</div>
                    <div class="notification-time">${timeAgo}</div>
                </div>
                <div class="notification-message">${this.escapeHtml(notification.message)}</div>
                <span class="notification-type ${typeClass}">${typeLabel}</span>
            </li>
        `;
    }

    getNotificationTypeClass(type) {
        const typeMap = {
            'new_problem': 'new_problem',
            'problem_resolved': 'problem_resolved',
            'warning': 'warning',
            'error': 'error',
            'info': 'info'
        };
        return typeMap[type] || 'info';
    }

    getNotificationTypeLabel(type) {
        const typeMap = {
            'new_problem': 'Problem Baru',
            'problem_resolved': 'Problem Selesai',
            'warning': 'Peringatan',
            'error': 'Error',
            'info': 'Info'
        };
        return typeMap[type] || 'Info';
    }

    getEmptyStateHTML() {
        return `
            <div class="notification-empty">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
                    <path d="M18 8A6 6 0 0 0 6 8c0 7-3 9-3 9h18s-3-2-3-9"></path>
                    <path d="M13.73 21a2 2 0 0 1-3.46 0"></path>
                </svg>
                <h6>No Notifications</h6>
                <p>You're all caught up! No new notifications to show.</p>
            </div>
        `;
    }

    showLoadingState() {
        const notificationList = document.getElementById('notificationList');
        if (notificationList) {
            notificationList.innerHTML = `
                <div class="notification-loading">
                    <div class="spinner-border spinner-border-sm text-primary me-2" role="status">
                        <span class="visually-hidden">Loading...</span>
                    </div>
                    Loading notifications...
                </div>
            `;
        }
    }

    showErrorState() {
        const notificationList = document.getElementById('notificationList');
        if (notificationList) {
            notificationList.innerHTML = `
                <div class="notification-empty">
                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
                        <circle cx="12" cy="12" r="10"></circle>
                        <line x1="12" y1="8" x2="12" y2="12"></line>
                        <line x1="12" y1="16" x2="12.01" y2="16"></line>
                    </svg>
                    <h6>Error Loading Notifications</h6>
                    <p>Unable to load notifications. Please try again.</p>
                    <button class="btn btn-sm btn-primary mt-2" onclick="notificationSystem.loadNotifications()">
                        Retry
                    </button>
                </div>
            `;
        }
    }

    attachNotificationItemHandlers() {
        const notificationItems = document.querySelectorAll('.notification-item');
        
        notificationItems.forEach(item => {
            item.addEventListener('click', (e) => {
                e.preventDefault();
                e.stopPropagation();
                const notificationId = parseInt(item.dataset.notificationId);
                this.handleNotificationClick(notificationId);
            });

            item.addEventListener('keydown', (e) => {
                if (e.key === 'Enter' || e.key === ' ') {
                    e.preventDefault();
                    e.stopPropagation();
                    const notificationId = parseInt(item.dataset.notificationId);
                    this.handleNotificationClick(notificationId);
                }
            });
        });
    }

    async handleNotificationClick(notificationId) {
        const notification = this.notifications.find(n => n.id === notificationId);
        
        if (notification && !notification.is_read) {
            await this.markAsRead(notificationId);
        }

        // Navigate to relevant page based on notification type
        this.navigateToNotificationTarget(notification);
    }

    navigateToNotificationTarget(notification) {
        // Navigate to specific CTP machine page based on machine name
        let targetUrl = '/impact/log-ctp'; // Default fallback
        
        if (notification.machine_name) {
            const machineName = notification.machine_name.toLowerCase();
            if (machineName.includes('ctp 1') || machineName.includes('suprasetter')) {
                targetUrl = '/impact/log-ctp/suprasetter';
            } else if (machineName.includes('ctp 2') || machineName.includes('platesetter')) {
                targetUrl = '/impact/log-ctp/platesetter';
            } else if (machineName.includes('ctp 3') || machineName.includes('trendsetter')) {
                targetUrl = '/impact/log-ctp/trendsetter';
            }
        }
        
        window.location.href = targetUrl;
    }

    updateBadge() {
        const badge = document.getElementById('notificationBadge');
        if (!badge) return;

        this.unreadCount = this.notifications.filter(n => !n.is_read).length;
        
        if (this.unreadCount === 0) {
            badge.textContent = '0';
            badge.classList.add('zero');
        } else if (this.unreadCount === 1) {
            badge.textContent = '1';
            badge.classList.remove('zero');
            badge.classList.add('single');
        } else {
            badge.textContent = this.unreadCount > 99 ? '99+' : this.unreadCount.toString();
            badge.classList.remove('zero', 'single');
        }
    }

    startPolling() {
        // Poll for new notifications every 30 seconds
        this.pollingInterval = setInterval(() => {
            if (!this.isDropdownOpen) {
                this.loadNotifications();
            }
        }, 30000);
    }

    stopPolling() {
        if (this.pollingInterval) {
            clearInterval(this.pollingInterval);
            this.pollingInterval = null;
        }
    }

    formatTimeAgo(dateString) {
        const date = new Date(dateString);
        const now = new Date();
        const diffMs = now - date;
        const diffMins = Math.floor(diffMs / 60000);
        const diffHours = Math.floor(diffMins / 60);
        const diffDays = Math.floor(diffHours / 24);

        if (diffMins < 1) {
            return 'Baru saja';
        } else if (diffMins < 60) {
            return `${diffMins} menit yang lalu`;
        } else if (diffHours < 24) {
            return `${diffHours} jam yang lalu`;
        } else if (diffDays < 7) {
            return `${diffDays} hari yang lalu`;
        } else {
            return date.toLocaleDateString('id-ID');
        }
    }

    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }


    // Public method to manually refresh notifications
    refresh() {
        this.loadNotifications();
    }

    // Public method to add a new notification (for real-time updates)
    addNotification(notification) {
        this.notifications.unshift(notification);
        this.updateNotificationUI();
        this.updateBadge();
        
        // New notification will appear in dropdown automatically
    }

    // Cleanup method
    destroy() {
        this.stopPolling();
        // Remove event listeners and clean up DOM elements
        document.removeEventListener('click', this.closeDropdown);
        document.removeEventListener('keydown', this.handleKeyboardNavigation);
        document.removeEventListener('click', this.handleOutsideClick);
    }
}

// Initialize the notification system when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    window.notificationSystem = new NotificationSystem();
});

// Clean up when page is unloaded
window.addEventListener('beforeunload', () => {
    if (window.notificationSystem) {
        window.notificationSystem.destroy();
    }
});