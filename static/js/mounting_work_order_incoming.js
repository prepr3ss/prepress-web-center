// Work Order Incoming JavaScript
// File: static/js/mounting_work_order_incoming.js

class WorkOrderIncoming {
    constructor() {
        console.log('WorkOrderIncoming constructor called');
        this.workOrderData = [];
        this.currentPage = 1;
        this.perPage = 20;
        this.totalPages = 1;
        this.currentFilters = {};
        
        console.log('About to initialize event listeners...');
        this.initializeEventListeners();
        console.log('About to initialize table...');
        this.initializeTable();
        console.log('About to load data...');
        this.loadData();
        console.log('WorkOrderIncoming constructor completed');
    }
    
    initializeEventListeners() {
        console.log('Initializing event listeners...');
        
        // Debug: Check if elements exist
        const addRowBtn = document.getElementById('addRowBtn');
        const clearAllBtn = document.getElementById('clearAllBtn');
        const submitBtn = document.getElementById('submitBtn');
        const confirmSubmitBtn = document.getElementById('confirmSubmitBtn');
        const confirmClearAllBtn = document.getElementById('confirmClearAllBtn');
        const refreshBtn = document.getElementById('refreshBtn');
        const filterDate = document.getElementById('filterDate');
        const filterStatus = document.getElementById('filterStatus');
        const filterCustomer = document.getElementById('filterCustomer');
        const searchInput = document.getElementById('searchInput');
        const workOrderTableBody = document.getElementById('workOrderTableBody');
        
        console.log('Elements found:', {
            addRowBtn: !!addRowBtn,
            clearAllBtn: !!clearAllBtn,
            submitBtn: !!submitBtn,
            confirmSubmitBtn: !!confirmSubmitBtn,
            confirmClearAllBtn: !!confirmClearAllBtn,
            refreshBtn: !!refreshBtn,
            filterDate: !!filterDate,
            filterStatus: !!filterStatus,
            filterCustomer: !!filterCustomer,
            searchInput: !!searchInput,
            workOrderTableBody: !!workOrderTableBody
        });
        
        // Input table buttons
        if (addRowBtn) {
            console.log('Adding click listener to addRowBtn');
            addRowBtn.addEventListener('click', (e) => {
                console.log('addRowBtn clicked!', e);
                this.addNewRow();
            });
        } else {
            console.error('addRowBtn not found!');
        }
        
        if (clearAllBtn) {
            clearAllBtn.addEventListener('click', () => this.showClearAllConfirmationModal());
        } else {
            console.error('clearAllBtn not found!');
        }
        
        if (submitBtn) {
            submitBtn.addEventListener('click', () => this.showConfirmationModal());
        } else {
            console.error('submitBtn not found!');
        }
        
        if (confirmSubmitBtn) {
            confirmSubmitBtn.addEventListener('click', () => this.submitData());
        } else {
            console.error('confirmSubmitBtn not found!');
        }
        
        if (confirmClearAllBtn) {
            confirmClearAllBtn.addEventListener('click', () => this.clearAllRowsConfirmed());
        } else {
            console.error('confirmClearAllBtn not found!');
        }
        
        // Data table buttons
        if (refreshBtn) {
            refreshBtn.addEventListener('click', () => this.loadData());
        } else {
            console.error('refreshBtn not found!');
        }
        
        // Filter events
        if (filterDate) {
            filterDate.addEventListener('change', () => this.applyFilters());
        }
        
        if (filterStatus) {
            filterStatus.addEventListener('change', () => this.applyFilters());
        }
        
        if (filterCustomer) {
            filterCustomer.addEventListener('input', () => this.debounce(() => this.applyFilters(), 500));
        }
        
        if (searchInput) {
            searchInput.addEventListener('input', () => this.debounce(() => this.applyFilters(), 500));
        }
        
        // Input table change events
        if (workOrderTableBody) {
            workOrderTableBody.addEventListener('input', (e) => {
                if (e.target.matches('input[data-field]')) {
                    this.updateRowData(e);
                }
            });
            
            // Add change event for select elements
            workOrderTableBody.addEventListener('change', (e) => {
                if (e.target.matches('select[data-field]')) {
                    this.updateRowData(e);
                }
            });
        } else {
            console.error('workOrderTableBody not found!');
        }
    }
    
    initializeTable() {
        console.log('Initializing table with 1 empty rows...');
        // Add 5 empty rows by default
        for (let i = 0; i < 1; i++) {
            console.log(`Adding row ${i + 1}`);
            this.addNewRow();
        }
        this.updateRowCount();
        console.log('Table initialized with', this.workOrderData.length, 'rows');
    }
    
    addNewRow() {
        console.log('addNewRow() called');
        const rowCount = this.workOrderData.length;
        console.log('Current row count:', rowCount);
        
        const newRow = {
            id: Date.now() + Math.random(), // Unique ID
            wo_number: '',
            mc_number: '',
            customer_name: '',
            item_name: '',
            print_block: '',
            print_machine: '',
            run_length_sheet: '',
            sheet_size: '',
            paper_type: ''
        };
        
        console.log('New row data:', newRow);
        
        this.workOrderData.push(newRow);
        console.log('Work order data after push:', this.workOrderData);
        
        this.renderRow(newRow, rowCount + 1);
        this.updateRowCount();
        
        console.log('Row added successfully');
    }
    
    renderRow(data, rowNumber) {
        console.log('renderRow() called with:', { data, rowNumber });
        const tbody = document.getElementById('workOrderTableBody');
        
        if (!tbody) {
            console.error('workOrderTableBody not found in renderRow!');
            return;
        }
        
        const row = document.createElement('tr');
        row.innerHTML = `
            <td class="text-center">${rowNumber}</td>
            <td>
                <input type="text" class="form-control form-control-sm"
                       data-field="wo_number" data-id="${data.id}"
                       value="${data.wo_number}" required
                       placeholder="25XXXXXXX">
            </td>
            <td>
                <input type="text" class="form-control form-control-sm"
                       data-field="mc_number" data-id="${data.id}"
                       value="${data.mc_number}" required
                       placeholder="OFSXXXXXXXX">
            </td>
            <td>
                <input type="text" class="form-control form-control-sm"
                       data-field="customer_name" data-id="${data.id}"
                       value="${data.customer_name}" required
                       placeholder="PT. XXXXXX">
            </td>
            <td>
                <input type="text" class="form-control form-control-sm"
                       data-field="item_name" data-id="${data.id}"
                       value="${data.item_name}" required
                       placeholder="">
            </td>
            <td>
                <input type="text" class="form-control form-control-sm"
                       data-field="print_block" data-id="${data.id}"
                       value="${data.print_block}" required
                       placeholder="OFSXXXXXXXX-ALL-XXX">
            </td>
            <td>
                <select class="form-control form-control-sm"
                       data-field="print_machine" data-id="${data.id}"
                       required>
                    <option value="">Pilih Mesin</option>
                    <option value="SM2" ${data.print_machine === 'SM2' ? 'selected' : ''}>SM2</option>
                    <option value="SM3" ${data.print_machine === 'SM3' ? 'selected' : ''}>SM3</option>
                    <option value="SM4" ${data.print_machine === 'SM4' ? 'selected' : ''}>SM4</option>
                    <option value="SM5" ${data.print_machine === 'SM5' ? 'selected' : ''}>SM5</option>
                    <option value="SM6" ${data.print_machine === 'SM6' ? 'selected' : ''}>SM6</option>
                    <option value="VLF" ${data.print_machine === 'VLF' ? 'selected' : ''}>VLF</option>
                </select>
            </td>
            <td>
                <input type="number" class="form-control form-control-sm"
                       data-field="run_length_sheet" data-id="${data.id}"
                       value="${data.run_length_sheet}" required
                       placeholder="">
            </td>
            <td>
                <input type="text" class="form-control form-control-sm"
                       data-field="sheet_size" data-id="${data.id}"
                       value="${data.sheet_size}"
                       placeholder="500X500">
            </td>
            <td>
                <input type="text" class="form-control form-control-sm"
                       data-field="paper_type" data-id="${data.id}"
                       value="${data.paper_type}"
                       placeholder="FAJAR, CMI">
            </td>
            <td class="text-center">
                <button type="button" class="btn btn-sm btn-danger" onclick="workOrderIncoming.removeRow(${data.id})">
                    <i class="fas fa-trash"></i>
                </button>
            </td>
        `;
        tbody.appendChild(row);
        console.log('Row rendered successfully');
    }
    
    removeRow(id) {
        console.log('removeRow() called with id:', id, 'type:', typeof id);
        console.log('Current workOrderData before removal:', this.workOrderData);
        
        // Find the item to remove for debugging
        const itemToRemove = this.workOrderData.find(item => item.id == id);
        console.log('Item to remove:', itemToRemove);
        
        const originalLength = this.workOrderData.length;
        // Use == for comparison to handle string/number conversion
        this.workOrderData = this.workOrderData.filter(item => item.id != id);
        console.log('Work order data after removal:', this.workOrderData);
        console.log('Items removed:', originalLength - this.workOrderData.length);
        
        this.renderAllRows();
        this.updateRowCount();
        console.log('Row removal completed');
    }
    
    renderAllRows() {
        const tbody = document.getElementById('workOrderTableBody');
        tbody.innerHTML = '';
        
        this.workOrderData.forEach((item, index) => {
            this.renderRow(item, index + 1);
        });
    }
    
    updateRowData(e) {
        const id = e.target.dataset.id;
        const field = e.target.dataset.field;
        const value = e.target.value;
        
        console.log('updateRowData called:', { id, field, value, elementType: e.target.tagName });
        
        // Use == for comparison to handle string/number conversion
        const item = this.workOrderData.find(item => item.id == id);
        if (item) {
            item[field] = value;
            console.log('Data updated:', item);
        } else {
            console.error('Item not found with id:', id);
            console.error('Available IDs:', this.workOrderData.map(item => item.id));
        }
    }
    
    updateRowCount() {
        const count = this.workOrderData.length;
        console.log('updateRowCount() called, count:', count);
        
        const rowCountInfo = document.getElementById('rowCountInfo');
        const submitBtn = document.getElementById('submitBtn');
        
        if (rowCountInfo) {
            rowCountInfo.textContent = `${count} baris`;
            console.log('Row count updated:', count);
        } else {
            console.error('rowCountInfo element not found!');
        }
        
        if (submitBtn) {
            submitBtn.disabled = count === 0;
            console.log('Submit button disabled state:', submitBtn.disabled);
        } else {
            console.error('submitBtn element not found!');
        }
    }
    
    clearAllRows() {
        // This method is now deprecated, use showClearAllConfirmationModal instead
        this.showClearAllConfirmationModal();
    }
    
    // New method to clear rows without confirmation
    clearAllRowsWithoutConfirmation() {
        this.workOrderData = [];
        this.renderAllRows();
        this.updateRowCount();
    }
    
    // Show confirmation modal for clearing all rows
    showClearAllConfirmationModal() {
        if (this.workOrderData.length > 0) {
            const count = this.workOrderData.length;
            document.getElementById('clearAllMessage').textContent =
                `Apakah Anda yakin ingin menghapus ${count} baris? Tindakan ini tidak dapat dibatalkan.`;
            
            const modal = new bootstrap.Modal(document.getElementById('clearAllModal'));
            modal.show();
        }
    }
    
    // Execute the clear all operation after confirmation
    clearAllRowsConfirmed() {
        this.workOrderData = [];
        this.renderAllRows();
        this.updateRowCount();
        this.showToast('Semua baris berhasil dihapus', 'success');
        
        // Close modal
        const modal = bootstrap.Modal.getInstance(document.getElementById('clearAllModal'));
        modal.hide();
    }
    
    validateData() {
        let isValid = true;
        const errors = [];
        
        this.workOrderData.forEach((item, index) => {
            const requiredFields = ['wo_number', 'mc_number', 'customer_name', 'item_name', 'print_block', 'print_machine'];
            
            requiredFields.forEach(field => {
                if (!item[field] || item[field].trim() === '') {
                    isValid = false;
                    errors.push(`Baris ${index + 1}: ${this.getFieldLabel(field)} tidak boleh kosong`);
                }
            });
        });
        
        return { isValid, errors };
    }
    
    getFieldLabel(field) {
        const labels = {
            'wo_number': 'WO Number',
            'mc_number': 'MC Number',
            'customer_name': 'Customer Name',
            'item_name': 'Item Name',
            'print_block': 'Print Block',
            'print_machine': 'Print Machine'
        };
        return labels[field] || field;
    }
    
    async showConfirmationModal() {
        // First validate data using API
        try {
            const response = await fetch('/impact/api/mounting-work-order-incoming/validate', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    work_orders: this.workOrderData
                })
            });
            
            if (!response.ok) {
                const error = await response.json();
                this.showToast('Error validasi: ' + error.message, 'error');
                return;
            }
            
            const result = await response.json();
            
            if (result.valid_rows === 0) {
                this.showToast('Tidak ada data work order yang valid untuk disubmit', 'error');
                return;
            }
            
            // Show confirmation with validation results
            const count = result.valid_rows;
            const totalRows = result.total_rows;
            let message = `Terdapat ${count} work order valid dari ${totalRows} baris yang akan disubmit.`;
            
            document.getElementById('confirmMessage').textContent = message;
            
            const modal = new bootstrap.Modal(document.getElementById('confirmModal'));
            modal.show();
            
        } catch (error) {
            console.error('Error validating data:', error);
            this.showToast('Terjadi kesalahan saat validasi data: ' + error.message, 'error');
        }
    }
    
    async submitData() {
        try {
            const response = await fetch('/impact/api/mounting-work-order-incoming', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    work_orders: this.workOrderData
                })
            });
            
            if (response.ok) {
                const result = await response.json();
                this.showToast(result.message, 'success');
                
                // Close modal first
                const modal = bootstrap.Modal.getInstance(document.getElementById('confirmModal'));
                modal.hide();
                
                // Clear input table without confirmation
                this.clearAllRowsWithoutConfirmation();
                
                // Refresh data table with a small delay to ensure modal is closed
                setTimeout(() => {
                    this.loadData();
                }, 300);
            } else {
                const error = await response.json();
                this.showToast('Gagal submit: ' + error.message, 'error');
            }
        } catch (error) {
            console.error('Error submitting data:', error);
            this.showToast('Terjadi kesalahan: ' + error.message, 'error');
        }
    }
    
    async loadData() {
        try {
            this.showLoading(true);
            
            const params = new URLSearchParams({
                page: this.currentPage,
                per_page: this.perPage,
                ...this.currentFilters
            });
            
            const response = await fetch(`/impact/api/mounting-work-order-incoming?${params}`);
            if (!response.ok) throw new Error('Failed to fetch data');
            
            const result = await response.json();
            this.renderDataTable(result.data);
            this.updatePagination(result.pagination);
            
        } catch (error) {
            console.error('Error loading data:', error);
            this.showToast('Gagal load data: ' + error.message, 'error');
        } finally {
            this.showLoading(false);
        }
    }
    
    renderDataTable(data) {
        const tbody = document.getElementById('dataTableBody');
        
        if (!data || data.length === 0) {
            tbody.innerHTML = `
                <tr>
                    <td colspan="12" class="text-center py-4">
                        <i class="fas fa-inbox text-muted" style="font-size: 2rem;"></i>
                        <p class="mt-2 text-muted">Tidak ada data work order</p>
                    </td>
                </tr>
            `;
            return;
        }
        
        const html = data.map(item => {
            const statusBadge = this.getStatusBadge(item.status);
            const formattedDate = this.formatDateTimeIndonesia(item.incoming_datetime);
            
            return `
                <tr>
                    <td>${formattedDate}</td>
                    <td><strong>${item.wo_number}</strong></td>
                    <td>${item.mc_number}</td>
                    <td>${item.customer_name}</td>
                    <td>${item.item_name}</td>
                    <td>${item.print_block}</td>
                    <td>${item.print_machine}</td>
                    <td class="text-end">${item.run_length_sheet || '-'}</td>
                    <td>${item.sheet_size || '-'}</td>
                    <td>${item.paper_type || '-'}</td>
                    <td>${statusBadge}</td>
                    <td>
                        <div class="d-flex gap-1">
                            <button class="btn btn-sm btn-primary" onclick="workOrderIncoming.editItem(${item.id})">
                                <i class="fas fa-edit"></i>
                            </button>
                            <button class="btn btn-sm btn-danger" onclick="workOrderIncoming.deleteItem(${item.id})">
                                <i class="fas fa-trash"></i>
                            </button>
                        </div>
                    </td>
                </tr>
            `;
        }).join('');
        
        tbody.innerHTML = html;
    }
    
    getStatusBadge(status) {
        const badges = {
            'pending': '<span class="badge bg-warning">Pending</span>',
            'in_progress': '<span class="badge bg-info">In Progress</span>',
            'completed': '<span class="badge bg-success">Completed</span>',
            'cancelled': '<span class="badge bg-danger">Cancelled</span>'
        };
        return badges[status] || `<span class="badge bg-secondary">${status}</span>`;
    }
    
    formatDateTimeIndonesia(datetimeString) {
        if (!datetimeString || datetimeString === '-') return '-';
        
        try {
            const date = new Date(datetimeString);
            if (isNaN(date.getTime())) return datetimeString;
            
            const bulanIndonesia = [
                'Januari', 'Februari', 'Maret', 'April', 'Mei', 'Juni',
                'Juli', 'Agustus', 'September', 'Oktober', 'November', 'Desember'
            ];
            
            const day = date.getDate();
            const month = bulanIndonesia[date.getMonth()];
            const year = date.getFullYear();
            const hour = date.getHours().toString().padStart(2, '0');
            const minute = date.getMinutes().toString().padStart(2, '0');
            
            return `${day} ${month} ${year} ${hour}:${minute}`;
        } catch (error) {
            return datetimeString;
        }
    }
    
    updatePagination(pagination) {
        const paginationContainer = document.getElementById('pagination');
        
        if (!pagination || pagination.total_pages <= 1) {
            paginationContainer.innerHTML = '';
            return;
        }
        
        let html = '';
        const { current_page, total_pages } = pagination;
        
        // Previous button
        html += `
            <li class="page-item ${current_page === 1 ? 'disabled' : ''}">
                <a class="page-link" href="#" onclick="workOrderIncoming.changePage(${current_page - 1})">
                    <i class="fas fa-chevron-left"></i>
                </a>
            </li>
        `;
        
        // Page numbers
        for (let i = 1; i <= total_pages; i++) {
            if (i === 1 || i === total_pages || (i >= current_page - 2 && i <= current_page + 2)) {
                html += `
                    <li class="page-item ${i === current_page ? 'active' : ''}">
                        <a class="page-link" href="#" onclick="workOrderIncoming.changePage(${i})">${i}</a>
                    </li>
                `;
            } else if (i === current_page - 3 || i === current_page + 3) {
                html += `<li class="page-item disabled"><span class="page-link">...</span></li>`;
            }
        }
        
        // Next button
        html += `
            <li class="page-item ${current_page === total_pages ? 'disabled' : ''}">
                <a class="page-link" href="#" onclick="workOrderIncoming.changePage(${current_page + 1})">
                    <i class="fas fa-chevron-right"></i>
                </a>
            </li>
        `;
        
        paginationContainer.innerHTML = html;
    }
    
    changePage(page) {
        if (page < 1 || page > this.totalPages) return;
        this.currentPage = page;
        this.loadData();
    }
    
    applyFilters() {
        this.currentFilters = {};
        
        const dateFilter = document.getElementById('filterDate').value;
        const statusFilter = document.getElementById('filterStatus').value;
        const customerFilter = document.getElementById('filterCustomer').value.trim();
        const searchFilter = document.getElementById('searchInput').value.trim();
        
        if (dateFilter) this.currentFilters.date = dateFilter;
        if (statusFilter) this.currentFilters.status = statusFilter;
        if (customerFilter) this.currentFilters.customer = customerFilter;
        if (searchFilter) this.currentFilters.search = searchFilter;
        
        this.currentPage = 1;
        this.loadData();
    }
    
    editItem(id) {
        // TODO: Implement edit functionality
        this.showToast('Edit functionality coming soon', 'info');
    }
    
    async deleteItem(id) {
        if (!confirm('Apakah Anda yakin ingin menghapus work order ini?')) {
            return;
        }
        
        try {
            const response = await fetch(`/impact/api/mounting-work-order-incoming/${id}`, {
                method: 'DELETE'
            });
            
            if (response.ok) {
                this.showToast('Work order berhasil dihapus', 'success');
                this.loadData();
            } else {
                const error = await response.json();
                this.showToast('Gagal menghapus: ' + error.error.message, 'error');
            }
        } catch (error) {
            console.error('Error deleting item:', error);
            this.showToast('Terjadi kesalahan saat menghapus', 'error');
        }
    }
    
    showLoading(show) {
        // You can implement a loading indicator here if needed
        if (show) {
            // Show loading
        } else {
            // Hide loading
        }
    }
    
    showToast(message, type = 'info', duration = 5000) {
        const toastContainer = document.getElementById('toastContainer');
        const toastId = 'toast-' + Date.now();
        
        const icons = {
            'success': 'fa-check-circle',
            'error': 'fa-exclamation-circle',
            'info': 'fa-info-circle',
            'warning': 'fa-exclamation-triangle'
        };
        
        const toastHTML = `
            <div class="toast toast-${type}" id="${toastId}" role="alert" aria-live="assertive" aria-atomic="true">
                <div class="toast-body d-flex align-items-center">
                    <i class="fas ${icons[type] || icons['info']} me-2"></i>
                    <span class="flex-grow-1">${message}</span>
                    <button type="button" class="btn-close btn-close-white ms-2" data-bs-dismiss="toast"></button>
                </div>
            </div>
        `;
        
        toastContainer.insertAdjacentHTML('beforeend', toastHTML);
        
        const toastElement = document.getElementById(toastId);
        const toast = new bootstrap.Toast(toastElement, { delay: duration });
        toast.show();
        
        // Auto remove after duration
        setTimeout(() => {
            if (toastElement && toastElement.parentNode) {
                toastElement.parentNode.removeChild(toastElement);
            }
        }, duration + 1000);
    }
    
    debounce(func, wait) {
        let timeout;
        return function executedFunction(...args) {
            const later = () => {
                clearTimeout(timeout);
                func(...args);
            };
            clearTimeout(timeout);
            timeout = setTimeout(later, wait);
        };
    }
}

// Initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    // Check if we are on mounting work order incoming page
    const pageElement = document.querySelector('.work-order-incoming-page');
    if (pageElement) {
        console.log('Work Order Incoming page detected, initializing module...');
        window.workOrderIncoming = new WorkOrderIncoming();
        console.log('Work Order Incoming module loaded');
    } else {
        console.log('Not on Work Order Incoming page, skipping initialization');
    }
});