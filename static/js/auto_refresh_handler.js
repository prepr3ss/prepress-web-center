/**
 * Auto Refresh Handler - Comprehensive auto-refresh system
 * Provides robust page refreshing with user activity monitoring,
 * loading indicators, and error handling with retry logic
 */
class AutoRefreshHandler {
    constructor(options = {}) {
        // Singleton pattern - prevent multiple instances
        if (AutoRefreshHandler.instance) {
            this.log('AutoRefreshHandler instance already exists, returning existing instance');
            return AutoRefreshHandler.instance;
        }
        
        AutoRefreshHandler.instance = this;

        // Configuration options with defaults
        this.config = {
            refreshInterval: options.refreshInterval || 15000, // 15 seconds default
            inactivityDelay: options.inactivityDelay || 3000,   // 3 seconds of inactivity before pause
            errorRetryInterval: options.errorRetryInterval || 60000, // 1 minute on error
            maxRetries: options.maxRetries || 3,               // Maximum retry attempts
            loadingIndicatorSelector: options.loadingIndicatorSelector || '#updateIndicator',
            errorContainerSelector: options.errorContainerSelector || '#autoRefreshError',
            enableLogging: options.enableLogging || false,
            apiEndpoint: options.apiEndpoint || null,           // Custom API endpoint for data refresh
            dataType: options.dataType || 'bon'                // 'bon' or 'adjustment'
        };

        // State management
        this.state = {
            isActive: false,
            isPaused: false,
            isLoading: false,
            retryCount: 0,
            lastActivityTime: Date.now(),
            refreshTimer: null,
            inactivityTimer: null,
            errorState: false,
            isInitialized: false
        };

        // Event handlers binding
        this.handleVisibilityChange = this.handleVisibilityChange.bind(this);
        
        // Initialize
        this.init();
    }

    /**
     * Get singleton instance
     */
    static getInstance(options = {}) {
        if (!AutoRefreshHandler.instance) {
            AutoRefreshHandler.instance = new AutoRefreshHandler(options);
        }
        return AutoRefreshHandler.instance;
    }

    /**
     * Destroy singleton instance
     */
    static destroyInstance() {
        if (AutoRefreshHandler.instance) {
            AutoRefreshHandler.instance.destroy();
            AutoRefreshHandler.instance = null;
        }
    }

    /**
     * Initialize the auto-refresh system
     */
    init() {
        if (this.state.isInitialized) {
            this.log('Auto Refresh Handler already initialized');
            return;
        }
        
        this.log('Initializing Auto Refresh Handler');
        this.setupEventListeners();
        this.createErrorContainer();
        this.state.isInitialized = true;
        this.start();
    }

    /**
     * Setup event listeners
     */
    setupEventListeners() {
        // No user activity monitoring needed
        // Monitor page visibility
        document.addEventListener('visibilitychange', this.handleVisibilityChange);
    }

    /**
     * Create error container for displaying error messages
     */
    createErrorContainer() {
        let errorContainer = document.querySelector(this.config.errorContainerSelector);
        
        if (!errorContainer) {
            errorContainer = document.createElement('div');
            errorContainer.id = this.config.errorContainerSelector.replace('#', '');
            errorContainer.className = 'auto-refresh-error-container';
            errorContainer.style.cssText = `
                position: fixed;
                top: 20px;
                right: 20px;
                color: white;
                padding: 12px 20px;
                border-radius: 8px;
                box-shadow: 0 4px 15px rgba(0,0,0,0.2);
                z-index: 9999;
                font-size: 14px;
                max-width: 300px;
                display: none;
                animation: slideInRight 0.3s ease-out;
            `;
            
            // Add animation keyframes
            const style = document.createElement('style');
            style.textContent = `
                @keyframes slideInRight {
                    from { transform: translateX(100%); opacity: 0; }
                    to { transform: translateX(0); opacity: 1; }
                }
                @keyframes slideOutRight {
                    from { transform: translateX(0); opacity: 1; }
                    to { transform: translateX(100%); opacity: 0; }
                }
                .auto-refresh-error-container {
                    background: linear-gradient(135deg, #ff6b6b 0%, #ee5a52 100%);
                }
                .auto-refresh-error-container.retry {
                    background: linear-gradient(135deg, #ffa726 0%, #ff9800 100%);
                }
                .auto-refresh-error-container.success {
                    background: linear-gradient(135deg, #66bb6a 0%, #4caf50 100%) !important;
                }
            `;
            document.head.appendChild(style);
            document.body.appendChild(errorContainer);
        }
        
        this.errorContainer = errorContainer;
    }

    /**
     * Start the auto-refresh system
     */
    start() {
        if (this.state.isActive) {
            this.log('Auto refresh already active');
            return;
        }

        this.log('Starting auto refresh');
        this.state.isActive = true;
        this.state.errorState = false;
        this.state.retryCount = 0;
        this.scheduleNextRefresh();
    }

    /**
     * Stop the auto-refresh system
     */
    stop() {
        this.log('Stopping auto refresh');
        this.state.isActive = false;
        this.clearTimers();
        this.hideLoadingIndicator();
    }

    /**
     * Handle page visibility changes
     */
    handleVisibilityChange() {
        // No pause/resume functionality needed
        // Auto-refresh continues regardless of page visibility
    }

    /**
     * Schedule the next refresh
     */
    scheduleNextRefresh() {
        this.clearTimers();
        
        const interval = this.state.errorState ? 
            this.config.errorRetryInterval : 
            this.config.refreshInterval;
            
        this.state.refreshTimer = setTimeout(() => {
            this.performRefresh();
        }, interval);
    }

    /**
     * Perform the actual page refresh
     */
    async performRefresh() {
        if (this.state.isLoading) {
            return;
        }

        this.log('Performing refresh');
        this.state.isLoading = true;
        this.showLoadingIndicator();

        try {
            let response;
            
            // Use API endpoint if available, otherwise fallback to full page refresh
            if (this.config.apiEndpoint) {
                response = await fetch(this.config.apiEndpoint, {
                    method: 'GET',
                    headers: {
                        'X-Requested-With': 'XMLHttpRequest',
                        'Cache-Control': 'no-cache',
                        'Pragma': 'no-cache',
                        'Content-Type': 'application/json'
                    },
                    cache: 'no-store'
                });

                if (!response.ok) {
                    throw new Error(`HTTP ${response.status}: ${response.statusText}`);
                }

                const result = await response.json();
                
                if (!result.success) {
                    throw new Error(result.error || 'API request failed');
                }
                
                // Update page with JSON data
                await this.updatePageFromJSON(result.data);
                
            } else {
                // Fallback to full HTML refresh
                response = await fetch(window.location.href, {
                    method: 'GET',
                    headers: {
                        'X-Requested-With': 'XMLHttpRequest',
                        'Cache-Control': 'no-cache',
                        'Pragma': 'no-cache'
                    },
                    cache: 'no-store'
                });

                if (!response.ok) {
                    throw new Error(`HTTP ${response.status}: ${response.statusText}`);
                }

                const html = await response.text();
                
                // Parse the response and update the page
                await this.updatePageContent(html);
            }
            
            // Reset error state on success
            this.state.errorState = false;
            this.state.retryCount = 0;
            
            this.showSuccessMessage();
            this.log('Refresh completed successfully');

        } catch (error) {
            this.log(`Refresh failed: ${error.message}`);
            this.handleRefreshError(error);
        } finally {
            this.state.isLoading = false;
            this.hideLoadingIndicator();
            
            // Schedule next refresh if still active
            if (this.state.isActive) {
                this.scheduleNextRefresh();
            }
        }
    }

    /**
     * Update page content from JSON data (preserves formatting)
     */
    async updatePageFromJSON(data) {
        this.log('Updating page from JSON data');
        
        // Update status badge
        const statusBadge = document.querySelector('[data-status]');
        if (statusBadge && data.status) {
            statusBadge.setAttribute('data-status', data.status);
            if (window.initializeStatusBadge) {
                window.initializeStatusBadge();
            }
        }
        
        // Update tanggal
        const tanggalElements = document.querySelectorAll('[data-tanggal]');
        tanggalElements.forEach(el => {
            if (data.tanggal) {
                el.textContent = data.tanggal;
                el.setAttribute('data-tanggal', data.tanggal);
            }
        });
        
        // Update datetime elements with proper formatting
        const datetimeFields = [
            'machine_off_at',
            'plate_start_at',
            'plate_finish_at',
            'plate_delivered_at',
            'design_start_at',
            'design_finish_at',
            'pdnd_start_at',
            'pdnd_finish_at',
            'curve_start_at',
            'curve_finish_at',
            'adjustment_start_at',
            'adjustment_finish_at'
        ];
        
        // Define PIC fields mapping for reference
        const picFields = {
            'machine_off_at': 'pic',
            'plate_start_at': 'ctp_by',
            'plate_finish_at': 'ctp_by',
            'plate_delivered_at': 'ctp_by',
            'design_start_at': 'design_by',
            'design_finish_at': 'design_by',
            'pdnd_start_at': 'pdnd_by',
            'pdnd_finish_at': 'pdnd_by',
            'curve_start_at': 'curve_by',
            'curve_finish_at': 'curve_by',
            'adjustment_start_at': 'adjustment_by',
            'adjustment_finish_at': 'adjustment_by'
        };
        
        datetimeFields.forEach(field => {
            if (data[field]) {
                // Find elements by data-step and data-datetime combination
                const stepName = field.replace('_at', '');
                const element = document.querySelector(`[data-step="${stepName}"] [data-datetime]`);
                
                if (element) {
                    // Use the pre-formatted Indonesian datetime from API
                    const formattedDatetime = data[field];
                    const pic = data[picFields[field]] || '';
                    
                    // Update with proper formatting including PIC
                    if (pic) {
                        element.innerHTML = `${formattedDatetime} <span class="text-muted">[${pic}]</span>`;
                    } else {
                        element.textContent = formattedDatetime;
                    }
                    
                    element.setAttribute('data-datetime', formattedDatetime);
                    if (pic) {
                        element.setAttribute('data-pic', pic);
                    }
                }
            }
        });
        
        
        // Update timeline data object
        if (window.updateTimelineData) {
            window.updateTimelineData();
        }
        
        // Update timeline visual state without re-initializing
        if (window.updateTimelineVisualState) {
            window.updateTimelineVisualState(data);
        }
        
        this.log('Page updated from JSON data successfully');
    }

    /**
     * Update page content with fresh data (fallback method)
     */
    async updatePageContent(newHtml) {
        this.log('Updating page from HTML (fallback method)');
        
        // Create a temporary DOM parser
        const parser = new DOMParser();
        const newDoc = parser.parseFromString(newHtml, 'text/html');
        
        // Only update data elements, NOT structure or event listeners
        const elementsToUpdate = [
            '[data-status]',
            '[data-tanggal]',
            '[data-datetime]'
        ];

        for (const selector of elementsToUpdate) {
            const newElements = newDoc.querySelectorAll(selector);
            const currentElements = document.querySelectorAll(selector);
            
            newElements.forEach((newEl, index) => {
                if (currentElements[index]) {
                    const currentEl = currentElements[index];
                    
                    // Update attributes only for data elements
                    Array.from(newEl.attributes).forEach(attr => {
                        if (attr.name.startsWith('data-')) {
                            currentEl.setAttribute(attr.name, attr.value);
                        }
                    });
                    
                    // Update text content for data elements
                    if (newEl.hasAttribute('data-tanggal') || newEl.hasAttribute('data-datetime')) {
                        currentEl.textContent = newEl.textContent;
                        currentEl.innerHTML = newEl.innerHTML;
                    }
                }
            });
        }

        // Update status badges without re-initializing entire timeline
        const statusBadges = document.querySelectorAll('[data-status]');
        const newStatusBadges = newDoc.querySelectorAll('[data-status]');
        
        statusBadges.forEach((badge, index) => {
            if (newStatusBadges[index]) {
                // Only update the badge content and classes, not re-initialize
                badge.className = newStatusBadges[index].className;
                badge.textContent = newStatusBadges[index].textContent;
            }
        });

        // Update timeline data if available
        if (window.updateTimelineData) {
            window.updateTimelineData();
        }

        this.log('Page updated from HTML successfully');
    }

    /**
     * Handle refresh errors with retry logic
     */
    handleRefreshError(error) {
        this.state.errorState = true;
        this.state.retryCount++;
        
        const errorMessage = this.state.retryCount >= this.config.maxRetries ?
            `Gagal memperbarui data setelah ${this.config.maxRetries} percobaan. Silakan refresh halaman secara manual.` :
            `Gagal memperbarui data (${this.state.retryCount}/${this.config.maxRetries}). Mencoba lagi dalam ${this.config.errorRetryInterval/1000} detik...`;
        
        this.showErrorMessage(errorMessage, this.state.retryCount >= this.config.maxRetries);
        
        if (this.state.retryCount >= this.config.maxRetries) {
            this.stop();
        }
    }

    /**
     * Show loading indicator
     */
    showLoadingIndicator() {
        const indicator = document.querySelector(this.config.loadingIndicatorSelector);
        if (indicator) {
            indicator.style.display = 'block';
        }
    }

    /**
     * Hide loading indicator
     */
    hideLoadingIndicator() {
        const indicator = document.querySelector(this.config.loadingIndicatorSelector);
        if (indicator) {
            setTimeout(() => {
                indicator.style.display = 'none';
            }, 1000); // Keep visible for at least 1 second
        }
    }

    /**
     * Show error message
     */
    showErrorMessage(message, isFinal = false) {
        if (!this.errorContainer) return;
        
        this.errorContainer.textContent = message;
        this.errorContainer.className = isFinal ? 
            'auto-refresh-error-container' : 
            'auto-refresh-error-container retry';
        this.errorContainer.style.display = 'block';
        
        // Auto-hide after 5 seconds for retry messages
        if (!isFinal) {
            setTimeout(() => {
                this.hideErrorMessage();
            }, 5000);
        }
    }

    /**
     * Show success message
     */
    showSuccessMessage() {
        if (!this.errorContainer) return;
        
        this.errorContainer.textContent = 'Data berhasil diperbarui';
        this.errorContainer.className = 'auto-refresh-error-container success';
        this.errorContainer.style.display = 'block';
        
        setTimeout(() => {
            this.hideErrorMessage();
        }, 2000);
    }

    /**
     * Hide error message
     */
    hideErrorMessage() {
        if (this.errorContainer) {
            this.errorContainer.style.animation = 'slideOutRight 0.3s ease-out';
            setTimeout(() => {
                this.errorContainer.style.display = 'none';
                this.errorContainer.style.animation = '';
            }, 300);
        }
    }

    /**
     * Clear all timers
     */
    clearTimers() {
        if (this.state.refreshTimer) {
            clearTimeout(this.state.refreshTimer);
            this.state.refreshTimer = null;
        }
    }

    /**
     * Logging function
     */
    log(message) {
        if (this.config.enableLogging) {
            console.log(`[AutoRefresh] ${message}`);
        }
    }

    /**
     * Destroy the auto-refresh handler
     */
    destroy() {
        this.log('Destroying auto refresh handler');
        this.stop();
        
        // Remove event listeners
        document.removeEventListener('visibilitychange', this.handleVisibilityChange);
        
        // Remove error container
        if (this.errorContainer && this.errorContainer.parentNode) {
            this.errorContainer.parentNode.removeChild(this.errorContainer);
        }
    }
}

// Export for global use
window.AutoRefreshHandler = AutoRefreshHandler;
