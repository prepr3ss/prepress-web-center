/**
 * Proof Checklist API Handler
 * Handles all CRUD operations via REST API
 */

class ProofChecklistAPI {
    constructor(baseUrl = '/impact/rnd-proof-checklist') {
        this.baseUrl = baseUrl;
        this.masterDataCache = null;
    }

    /**
     * Create new proof checklist
     * @param {Object} data - Checklist data
     * @returns {Promise} Response from API
     */
    async createChecklist(data) {
        try {
            const response = await fetch(`${this.baseUrl}/api/checklist`, {
                method: 'POST',
                credentials: 'include',
                headers: {
                    'Content-Type': 'application/json',
                    'X-Requested-With': 'XMLHttpRequest'
                },
                body: JSON.stringify(data)
            });

            const result = await response.json();

            if (!response.ok) {
                throw new Error(result.message || 'Error creating checklist');
            }

            return {
                success: true,
                data: result.data
            };
        } catch (error) {
            return {
                success: false,
                message: error.message
            };
        }
    }

    /**
     * Get single checklist
     * @param {number} id - Checklist ID
     * @returns {Promise} Checklist data
     */
    async getChecklist(id) {
        try {
            const response = await fetch(`${this.baseUrl}/api/checklist/${id}`, {
                method: 'GET',
                credentials: 'include',
                headers: {
                    'X-Requested-With': 'XMLHttpRequest'
                }
            });

            const result = await response.json();

            if (!response.ok) {
                throw new Error(result.message || 'Error fetching checklist');
            }

            return {
                success: true,
                data: result.data
            };
        } catch (error) {
            return {
                success: false,
                message: error.message
            };
        }
    }

    /**
     * Update proof checklist
     * @param {number} id - Checklist ID
     * @param {Object} data - Updated data
     * @returns {Promise} Response from API
     */
    async updateChecklist(id, data) {
        try {
            const response = await fetch(`${this.baseUrl}/api/checklist/${id}`, {
                method: 'PUT',
                credentials: 'include',
                headers: {
                    'Content-Type': 'application/json',
                    'X-Requested-With': 'XMLHttpRequest'
                },
                body: JSON.stringify(data)
            });

            const result = await response.json();

            if (!response.ok) {
                throw new Error(result.message || 'Error updating checklist');
            }

            return {
                success: true,
                data: result.data
            };
        } catch (error) {
            return {
                success: false,
                message: error.message
            };
        }
    }

    /**
     * Delete proof checklist
     * @param {number} id - Checklist ID
     * @returns {Promise} Response from API
     */
    async deleteChecklist(id) {
        try {
            const response = await fetch(`${this.baseUrl}/api/checklist/${id}`, {
                method: 'DELETE',
                credentials: 'include',
                headers: {
                    'X-Requested-With': 'XMLHttpRequest'
                }
            });

            const result = await response.json();

            if (!response.ok) {
                throw new Error(result.message || 'Error deleting checklist');
            }

            return {
                success: true,
                data: result
            };
        } catch (error) {
            return {
                success: false,
                message: error.message
            };
        }
    }

    /**
     * Update checklist status
     * @param {number} id - Checklist ID
     * @param {string} status - New status
     * @returns {Promise} Response from API
     */
    async updateStatus(id, status) {
        try {
            const response = await fetch(`${this.baseUrl}/api/checklist/${id}/status`, {
                method: 'PUT',
                credentials: 'include',
                headers: {
                    'Content-Type': 'application/json',
                    'X-Requested-With': 'XMLHttpRequest'
                },
                body: JSON.stringify({ status })
            });

            const result = await response.json();

            if (!response.ok) {
                throw new Error(result.message || 'Error updating status');
            }

            return {
                success: true,
                data: result.data
            };
        } catch (error) {
            return {
                success: false,
                message: error.message
            };
        }
    }

    /**
     * Get all checklists with filters
     * @param {Object} options - Filter options
     * @returns {Promise} Paginated checklist list
     */
    async getChecklists(options = {}) {
        try {
            console.log('🔍 [DEBUG] getChecklists called with options:', options);
            const params = new URLSearchParams();
            
            if (options.page) params.append('page', options.page);
            if (options.search) params.append('search', options.search);
            if (options.status) params.append('status', options.status);
            if (options.date_filter) params.append('date_filter', options.date_filter);

            const url = `${this.baseUrl}/api/checklists?${params}`;
            console.log('🌐 [DEBUG] Fetch URL:', url);
            console.log('🌐 [DEBUG] baseUrl:', this.baseUrl);

            const response = await fetch(url, {
                method: 'GET',
                credentials: 'include',
                headers: {
                    'X-Requested-With': 'XMLHttpRequest'
                }
            });

            console.log('📡 [DEBUG] Response status:', response.status);
            console.log('📡 [DEBUG] Response ok:', response.ok);

            const result = await response.json();
            console.log('✅ [DEBUG] Response data:', result);
            console.log('✅ [DEBUG] Response data (JSON):', JSON.stringify(result, null, 2));
            console.log('✅ [DEBUG] result.data.checklists length:', result.data?.checklists?.length);
            console.log('✅ [DEBUG] result.data keys:', Object.keys(result.data || {}));

            if (!response.ok) {
                throw new Error(result.message || 'Error fetching checklists');
            }

            return {
                success: true,
                data: result.data
            };
        } catch (error) {
            console.error('❌ [ERROR] getChecklists error:', error);
            return {
                success: false,
                message: error.message
            };
        }
    }

    /**
     * Get master data (print machines, separations, inks, postpress machines)
     * @returns {Promise} Master data
     */
    async getMasterData() {
        try {
            const response = await fetch(`${this.baseUrl}/api/master-data`, {
                method: 'GET',
                credentials: 'include',
                headers: {
                    'X-Requested-With': 'XMLHttpRequest'
                }
            });

            const result = await response.json();

            if (!response.ok) {
                throw new Error(result.message || 'Error fetching master data');
            }

            this.masterDataCache = result.data;
            return {
                success: true,
                data: result.data
            };
        } catch (error) {
            return {
                success: false,
                message: error.message
            };
        }
    }

    /**
     * Prepare form data for API submission
     * @param {HTMLFormElement} form - Form element
     * @returns {Object} Form data as object
     */
    prepareFormData(form) {
        const data = {};
        const formData = new FormData(form);

        // Get all form fields
        for (let [key, value] of formData.entries()) {
            // Handle multiple values (arrays)
            if (key.endsWith('[]') || key.includes('[') && key.includes(']')) {
                const cleanKey = key.replace('[]', '').replace(/\[.*\]/, '');
                if (!data[cleanKey]) {
                    data[cleanKey] = [];
                }
                if (value) {
                    data[cleanKey].push(value);
                }
            } else {
                // Handle single values
                if (value) {
                    data[key] = value;
                }
            }
        }

        // Handle checkboxes for array fields
        const checkboxGroups = {
            'print_machines': 'print_machines',
            'print_separations': 'print_separations',
            'print_inks': 'print_inks',
            'postpress_machines': 'postpress_machines'
        };

        for (let [groupName, fieldName] of Object.entries(checkboxGroups)) {
            const checkboxes = form.querySelectorAll(`input[name="${fieldName}"]:checked`);
            data[fieldName] = Array.from(checkboxes).map(cb => cb.value);
        }

        return data;
    }

    /**
     * Show alert message
     * @param {string} message - Alert message
     * @param {string} type - Alert type (success, danger, warning, info)
     * @param {HTMLElement} container - Container element
     */
    static showAlert(message, type = 'info', container = null) {
        if (!container) {
            container = document.getElementById('alertContainer');
        }

        if (!container) {
            console.warn('Alert container not found');
            return;
        }

        const alertElement = container.querySelector('.alert');
        const alertMessage = container.querySelector('#alertMessage');

        if (alertElement && alertMessage) {
            alertElement.className = `alert alert-${type} alert-dismissible fade show`;
            alertElement.innerHTML = `
                ${message}
                <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
            `;
            container.style.display = 'block';

            // Auto-hide alert after 5 seconds
            setTimeout(() => {
                const bootstrapAlert = new bootstrap.Alert(alertElement);
                bootstrapAlert.close();
            }, 5000);
        }
    }

    /**
     * Validate form data
     * @param {Object} data - Form data
     * @returns {Object} Validation result
     */
    static validateFormData(data) {
        const errors = [];

        if (!data.proof_date) errors.push('Proof date is required');
        if (!data.customer_name) errors.push('Customer name is required');
        if (!data.item_name) errors.push('Item name is required');

        return {
            valid: errors.length === 0,
            errors
        };
    }
}

/**
 * Form Handler for Proof Checklist
 */
class ProofChecklistFormHandler {
    constructor(formSelector = '#proofChecklistForm', baseUrl = '/impact/rnd-proof-checklist') {
        this.form = document.querySelector(formSelector);
        this.api = new ProofChecklistAPI(baseUrl);
        this.isEditMode = false;
        this.checklistId = null;

        if (this.form) {
            this.init();
        }
    }

    /**
     * Initialize form handler
     */
    async init() {
        // Check if we're in edit mode
        const urlPath = window.location.pathname;
        const editMatch = urlPath.match(/\/(\d+)\/edit/);
        
        if (editMatch) {
            this.isEditMode = true;
            this.checklistId = parseInt(editMatch[1]);
        }

        // Load master data
        await this.loadMasterData();

        // Attach form submission handler
        this.form.addEventListener('submit', (e) => this.handleSubmit(e));

        // Initialize datepicker if available
        this.initDatepicker();
    }

    /**
     * Load master data
     */
    async loadMasterData() {
        const result = await this.api.getMasterData();

        if (result.success) {
            this.populateMasterDataSelects(result.data);
        } else {
            console.error('Error loading master data:', result.message);
        }
    }

    /**
     * Populate select elements with master data
     */
    populateMasterDataSelects(masterData) {
        // This can be overridden in specific page implementations
        // For now, this is handled by the template rendering
        console.log('Master data loaded');
    }

    /**
     * Handle form submission
     */
    async handleSubmit(e) {
        e.preventDefault();

        // Prepare form data
        const formData = this.api.prepareFormData(this.form);

        // Validate
        const validation = ProofChecklistAPI.validateFormData(formData);
        if (!validation.valid) {
            ProofChecklistAPI.showAlert(
                validation.errors.join('<br>'),
                'danger'
            );
            return;
        }

        // Show loading indicator
        const submitBtn = this.form.querySelector('button[type="submit"]');
        const originalText = submitBtn.textContent;
        submitBtn.disabled = true;
        submitBtn.textContent = 'Processing...';

        let result;
        if (this.isEditMode) {
            result = await this.api.updateChecklist(this.checklistId, formData);
        } else {
            result = await this.api.createChecklist(formData);
        }

        // Restore button
        submitBtn.disabled = false;
        submitBtn.textContent = originalText;

        if (result.success) {
            const action = this.isEditMode ? 'updated' : 'created';
            ProofChecklistAPI.showAlert(
                `Proof Checklist ${action} successfully!`,
                'success'
            );

            // Redirect after 2 seconds
            setTimeout(() => {
                const id = result.data.id || this.checklistId;
                window.location.href = `/impact/rnd-proof-checklist/${id}`;
            }, 2000);
        } else {
            ProofChecklistAPI.showAlert(result.message, 'danger');
        }
    }

    /**
     * Initialize datepicker
     */
    initDatepicker() {
        const dateInputs = this.form.querySelectorAll('input[type="text"][name*="date"]');
        
        dateInputs.forEach(input => {
            if (typeof $.fn.datepicker !== 'undefined') {
                $(input).datepicker({
                    format: 'yyyy-mm-dd',
                    autoclose: true,
                    startDate: new Date(2000, 0, 1)
                });
            }
        });
    }
}

/**
 * Dashboard Handler for Proof Checklist List
 */
class ProofChecklistDashboardHandler {
    constructor(options = {}) {
        console.log('🚀 [DEBUG] ProofChecklistDashboardHandler constructor called');
        this.api = new ProofChecklistAPI(options.baseUrl || '/impact/rnd-proof-checklist');
        console.log('🔧 [DEBUG] API initialized with baseUrl:', this.api.baseUrl);
        
        this.currentPage = 1;
        this.filters = {
            search: '',
            status: '',
            date_filter: ''
        };

        this.searchInput = document.getElementById('searchInput');
        console.log('📋 [DEBUG] searchInput element:', this.searchInput);
        this.statusFilter = document.getElementById('statusFilter');
        this.dateFilter = document.getElementById('dateFilter');
        this.tableBody = document.getElementById('checklistsTableBody');
        this.paginationContainer = document.getElementById('paginationContainer');
        console.log('📍 [DEBUG] paginationContainer element:', this.paginationContainer);
        this.loadingSpinner = document.getElementById('loadingSpinner');
        this.emptyState = document.getElementById('emptyState');

        if (this.searchInput) {
            this.init();
        }
    }

    /**
     * Initialize dashboard
     */
    init() {
        console.log('⚙️  [DEBUG] ProofChecklistDashboardHandler.init() called');
        console.log('📍 [DEBUG] baseUrl:', this.api.baseUrl);
        
        // Attach event listeners
        if (this.searchInput) {
            this.searchInput.addEventListener('input', () => this.handleSearch());
        }

        if (this.statusFilter) {
            this.statusFilter.addEventListener('change', () => this.handleFilterChange());
        }

        if (this.dateFilter) {
            this.dateFilter.addEventListener('change', () => this.handleFilterChange());
        }

        // Load initial data
        console.log('📥 [DEBUG] Calling loadChecklists()...');
        this.loadChecklists();
    }

    /**
     * Handle search input
     */
    handleSearch() {
        this.filters.search = this.searchInput.value;
        this.currentPage = 1;
        this.loadChecklists();
    }

    /**
     * Handle filter change
     */
    handleFilterChange() {
        this.filters.status = this.statusFilter?.value || '';
        this.filters.date_filter = this.dateFilter?.value || '';
        this.currentPage = 1;
        this.loadChecklists();
    }

    /**
     * Load checklists
     */
    async loadChecklists() {
        console.log('🔄 [DEBUG] loadChecklists() called');
        console.log('🔄 [DEBUG] currentPage:', this.currentPage);
        console.log('🔄 [DEBUG] filters:', this.filters);
        console.log('📊 [DEBUG] Showing loading spinner...');
        
        // Show loading spinner row, hide empty state
        if (this.loadingSpinner) this.loadingSpinner.style.display = 'table-row';
        if (this.emptyState) this.emptyState.style.display = 'none';
        
        const result = await this.api.getChecklists({
            page: this.currentPage,
            ...this.filters
        });

        console.log('📊 [DEBUG] loadChecklists result:', result);
        console.log('📊 [DEBUG] result.data:', result.data);
        console.log('📊 [DEBUG] result.data.checklists:', result.data?.checklists);

        if (result.success) {
            console.log('✅ [DEBUG] Success! Rendering table with data');
            const checklists = result.data?.checklists || [];
            console.log('✅ [DEBUG] Final checklists array:', checklists);
            
            // Hide loading spinner
            if (this.loadingSpinner) this.loadingSpinner.style.display = 'none';
            
            this.renderTable(checklists);
            this.renderPagination(result.data);
        } else {
            console.error('❌ [DEBUG] Failed! Error:', result.message);
            if (this.loadingSpinner) this.loadingSpinner.style.display = 'none';
            if (this.emptyState) this.emptyState.style.display = 'table-row';
            ProofChecklistAPI.showAlert(result.message, 'danger');
        }
    }

    /**
     * Format date to "DD MMMM YYYY" format (e.g., "16 February 2026")
     */
    formatDateLong(dateString) {
        if (!dateString) return '-';
        
        try {
            const date = new Date(dateString);
            const options = { 
                day: 'numeric', 
                month: 'long', 
                year: 'numeric' 
            };
            return date.toLocaleDateString('en-GB', options);
        } catch (error) {
            console.error('Error formatting date:', error);
            return dateString;
        }
    }

    /**
     * Render table rows
     */
    renderTable(checklists) {
        console.log('📊 [DEBUG] renderTable called with data:', checklists);
        console.log('📊 [DEBUG] checklists length:', checklists?.length);
        console.log('📊 [DEBUG] tableBody element:', this.tableBody);
        
        if (!this.tableBody) {
            console.error('❌ [ERROR] tableBody not found!');
            return;
        }

        if (!checklists || checklists.length === 0) {
            console.log('⚠️  [DEBUG] No checklists found, showing empty state');
            // Clear table and show empty state
            this.tableBody.innerHTML = '';
            if (this.loadingSpinner) this.loadingSpinner.style.display = 'none';
            if (this.emptyState) {
                this.emptyState.style.display = 'table-row';
                // Re-add empty state to tbody if it was removed
                if (!this.tableBody.contains(this.emptyState)) {
                    this.tableBody.appendChild(this.emptyState);
                }
            }
            return;
        }

        console.log('✅ [DEBUG] Rendering', checklists.length, 'checklists');
        if (checklists.length > 0) {
            console.log('📋 [DEBUG] First checklist data:', checklists[0]);
        }
        try {
            // Clear existing content
            this.tableBody.innerHTML = '';
            
            // Create rows from checklists
            const rowsHTML = checklists.map(checklist => `
            <tr>
                <td>${this.formatDateLong(checklist.proof_date)}</td>
                <td>${checklist.customer_name || '-'}</td>
                <td>${checklist.item_name || '-'}</td>
                <td>
                    <span class="status-badge status-${checklist.status.toLowerCase()}">
                        ${checklist.status}
                    </span>
                </td>
                <td>${this.formatDateLong(checklist.created_at)}</td>
                <td>
                    <a href="/impact/rnd-proof-checklist/${checklist.id}" class="btn btn-action btn-action-view">
                        <i class="fas fa-eye"></i> View
                    </a>
                </td>
            </tr>
        `).join('');
            
            this.tableBody.innerHTML = rowsHTML;
            console.log('✅ [DEBUG] Table HTML rendered successfully');
            
            // Hide empty state and loading spinner
            if (this.emptyState) this.emptyState.style.display = 'none';
            if (this.loadingSpinner) this.loadingSpinner.style.display = 'none';
        } catch (error) {
            console.error('❌ [ERROR] Error rendering table:', error);
            this.tableBody.innerHTML = `
                <tr>
                    <td colspan="6" class="text-center text-danger py-4">
                        Error rendering table: ${error.message}
                    </td>
                </tr>
            `;
        }
    }

    /**
     * Get badge color based on status
     */
    getStatusBadgeColor(status) {
        const colors = {
            'DRAFT': 'secondary',
            'ACTIVE': 'success',
            'COMPLETED': 'info',
            'CANCELLED': 'danger'
        };
        return colors[status] || 'secondary';
    }

    /**
     * Render pagination
     */
    renderPagination(data) {
        if (!this.paginationContainer) return;

        const { current_page, total_pages } = data;
        let html = '';

        // Previous button
        if (current_page > 1) {
            html += `<li class="page-item"><a class="page-link" href="#" data-page="${current_page - 1}">Previous</a></li>`;
        }

        // Page numbers
        for (let i = Math.max(1, current_page - 2); i <= Math.min(total_pages, current_page + 2); i++) {
            html += `<li class="page-item ${i === current_page ? 'active' : ''}">
                <a class="page-link" href="#" data-page="${i}">${i}</a>
            </li>`;
        }

        // Next button
        if (current_page < total_pages) {
            html += `<li class="page-item"><a class="page-link" href="#" data-page="${current_page + 1}">Next</a></li>`;
        }

        this.paginationContainer.innerHTML = html;

        // Attach pagination handlers
        this.paginationContainer.querySelectorAll('.page-link').forEach(link => {
            link.addEventListener('click', (e) => {
                e.preventDefault();
                this.currentPage = parseInt(link.dataset.page);
                this.loadChecklists();
                window.scrollTo(0, 0);
            });
        });
    }
}

// Initialize on document ready
document.addEventListener('DOMContentLoaded', () => {
    // Auto-initialize form handler if form exists
    if (document.querySelector('#proofChecklistForm')) {
        new ProofChecklistFormHandler();
    }

    // Auto-initialize dashboard handler if in dashboard
    if (document.body.classList.contains('proof-checklist-dashboard')) {
        new ProofChecklistDashboardHandler();
    }
});
