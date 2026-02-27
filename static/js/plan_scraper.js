// Plan Scraper JavaScript
let currentPage = 1;
let currentPerPage = 25;
let currentSearch = '';
let currentMachine = '';

// Initialize on page load - REMOVED (moved to bottom to avoid duplicate)

// Initialize upload area with drag and drop
function initializeUploadArea() {
    const uploadArea = document.getElementById('uploadArea');
    const fileInput = document.getElementById('fileInput');
    
    // Click to upload (but not when clicking the button)
    uploadArea.addEventListener('click', function(e) {
        // Don't trigger if clicking on the button
        if (e.target.tagName !== 'BUTTON' && !e.target.closest('button')) {
            fileInput.click();
        }
    });
    
    // File input change
    fileInput.addEventListener('change', function(e) {
        const file = e.target.files[0];
        if (file) {
            uploadFile(file);
        }
    });
    
    // Drag and drop
    uploadArea.addEventListener('dragover', function(e) {
        e.preventDefault();
        uploadArea.classList.add('dragover');
    });
    
    uploadArea.addEventListener('dragleave', function(e) {
        e.preventDefault();
        uploadArea.classList.remove('dragover');
    });
    
    uploadArea.addEventListener('drop', function(e) {
        e.preventDefault();
        uploadArea.classList.remove('dragover');
        
        const files = e.dataTransfer.files;
        if (files.length > 0) {
            uploadFile(files[0]);
        }
    });
}

// Upload file to server
function uploadFile(file) {
    // Validate file type
    const validTypes = ['application/vnd.openxmlformats-officedocument.spreadsheetml.sheet', 'application/vnd.ms-excel'];
    if (!validTypes.includes(file.type) && !file.name.match(/\.(xlsx|xls)$/i)) {
        showAlert('Invalid file type. Please upload an Excel file (.xlsx or .xls)', 'danger');
        return;
    }
    
    // Show loading state on upload area
    showUploadLoading(file.name);
    
    // Create form data
    const formData = new FormData();
    formData.append('file', file);
    
    // Upload file
    fetch('/impact/plan-scraper/upload', {
        method: 'POST',
        body: formData,
        headers: {
            'X-Requested-With': 'XMLHttpRequest'
        }
    })
    .then(response => response.json())
    .then(data => {
        hideUploadLoading();
        
        if (data.success) {
            showAlert(data.message, 'success');
            // Reset file input
            document.getElementById('fileInput').value = '';
            // Reload data and machines
            loadData();
            updateStatistics();
            loadPrintMachines(); // Reload machine dropdown after successful upload
        } else {
            showAlert(data.error || 'Error uploading file', 'danger');
        }
    })
    .catch(error => {
        hideUploadLoading();
        console.error('Error:', error);
        showAlert('Error uploading file. Please try again.', 'danger');
    });
}

// Load data from server
function loadData(page = 1, search = '', machine = '') {
    currentPage = page;
    currentSearch = search;
    currentMachine = machine;
    
    // DEBUG: Log parameters
    console.log('🔍 loadData called with:', {
        page: page,
        search: search,
        machine: machine,
        per_page: currentPerPage
    });
    
    const params = new URLSearchParams({
        page: page,
        per_page: currentPerPage,
        search: search,
        print_machine: machine
    });
    
    const url = `/impact/api/plan-scraper?${params}`;
    console.log('🌐 Fetching URL:', url);
    
    fetch(url)
    .then(response => response.json())
    .then(data => {
        console.log('📊 Response received:', data);
        if (data.success) {
            console.log('✅ Data loaded successfully:', {
                dataCount: data.data.length,
                pagination: data.pagination
            });
            renderDataTable(data.data);
            renderPagination(data.pagination);
        } else {
            console.error('❌ Server error:', data.error);
            showAlert(data.error || 'Error loading data', 'danger');
        }
    })
    .catch(error => {
        console.error('🚨 Network error:', error);
        showAlert('Error loading data. Please try again.', 'danger');
    });
}

// Render data table
function renderDataTable(data) {
    console.log('📋 renderDataTable called with:', data.length, 'items');
    const tableBody = document.getElementById('dataTableBody');
    
    if (data.length === 0) {
        console.log('🚫 No data to display');
        tableBody.innerHTML = `
            <tr>
                <td colspan="9" class="text-center py-4">
                    <i class="fas fa-inbox me-2"></i>
                    No data found
                </td>
            </tr>
        `;
        return;
    }
    
    console.log('✅ Rendering', data.length, 'rows of data');
    
    // Add page indicator for better UX
    const pageInfo = document.getElementById('pageInfo');
    if (pageInfo) {
        pageInfo.textContent = `Showing ${data.length} records`;
    }
    
    tableBody.innerHTML = data.map((item, index) => `
        <tr>
            <td>
                <span class="machine-badge machine-${item.print_machine.toLowerCase()}">
                    ${item.print_machine}
                </span>
            </td>
            <td><strong>${item.wo_number}</strong></td>
            <td>${item.mc_number}</td>
            <td>${item.item_name}</td>
            <td>${item.num_up}</td>
            <td>${formatNumber(item.run_length_sheet)}</td>
            <td>${item.paper_desc || '-'}</td>
            <td>${item.paper_type || '-'}</td>
            <td>
                <button class="btn btn-sm btn-outline-danger" onclick="deleteRecord(${item.id})" title="Delete">
                    <i class="fas fa-trash"></i>
                </button>
            </td>
        </tr>
    `).join('');
}

// Render pagination
function renderPagination(pagination) {
    console.log('📄 renderPagination called with:', pagination);
    const paginationElement = document.getElementById('pagination');
    
    if (pagination.pages <= 1) {
        console.log('🚫 No pagination needed (pages <= 1)');
        paginationElement.innerHTML = '';
        return;
    }
    
    let paginationHTML = '';
    
    // Previous button
    if (pagination.has_prev) {
        paginationHTML += `
            <li class="page-item">
                <a class="page-link" href="#" onclick="event.preventDefault(); loadData(${pagination.page - 1}, '${currentSearch}', '${currentMachine}')">
                    <i class="fas fa-chevron-left"></i>
                </a>
            </li>
        `;
    }
    
    // Page numbers
    const startPage = Math.max(1, pagination.page - 2);
    const endPage = Math.min(pagination.pages, pagination.page + 2);
    
    console.log('🔢 Pagination range:', { startPage, endPage, totalPages: pagination.pages });
    
    if (startPage > 1) {
        paginationHTML += `
            <li class="page-item">
                <a class="page-link" href="#" onclick="event.preventDefault(); loadData(1, '${currentSearch}', '${currentMachine}')">1</a>
            </li>
        `;
        if (startPage > 2) {
            paginationHTML += `<li class="page-item disabled"><span class="page-link">...</span></li>`;
        }
    }
    
    for (let i = startPage; i <= endPage; i++) {
        paginationHTML += `
            <li class="page-item ${i === pagination.page ? 'active' : ''}">
                <a class="page-link" href="#" onclick="event.preventDefault(); loadData(${i}, '${currentSearch}', '${currentMachine}')">${i}</a>
            </li>
        `;
    }
    
    if (endPage < pagination.pages) {
        if (endPage < pagination.pages - 1) {
            paginationHTML += `<li class="page-item disabled"><span class="page-link">...</span></li>`;
        }
        paginationHTML += `
            <li class="page-item">
                <a class="page-link" href="#" onclick="event.preventDefault(); loadData(${pagination.pages}, '${currentSearch}', '${currentMachine}')">${pagination.pages}</a>
            </li>
        `;
    }
    
    // Next button
    if (pagination.has_next) {
        paginationHTML += `
            <li class="page-item">
                <a class="page-link" href="#" onclick="event.preventDefault(); loadData(${pagination.page + 1}, '${currentSearch}', '${currentMachine}')">
                    <i class="fas fa-chevron-right"></i>
                </a>
            </li>
        `;
    }
    
    console.log('🎯 Pagination HTML generated:', paginationHTML);
    paginationElement.innerHTML = paginationHTML;
    
    // Update page info
    const pageInfo = document.getElementById('pageInfo');
    if (pageInfo) {
        const startRecord = ((pagination.page - 1) * pagination.per_page) + 1;
        const endRecord = Math.min(pagination.page * pagination.per_page, pagination.total);
        pageInfo.textContent = `Showing ${startRecord}-${endRecord} of ${pagination.total} records (Page ${pagination.page} of ${pagination.pages})`;
    }
}

// Load print machines for filter
function loadPrintMachines() {
    fetch('/impact/api/plan-scraper/machines')
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            const machineFilter = document.getElementById('machineFilter');
            const currentValue = machineFilter.value;
            
            machineFilter.innerHTML = '<option value="">All Machines</option>';
            data.data.forEach(machine => {
                machineFilter.innerHTML += `<option value="${machine}">${machine}</option>`;
            });
            
            // Restore previous selection
            machineFilter.value = currentValue;
        }
    })
    .catch(error => {
        console.error('Error loading machines:', error);
    });
}

// Apply filters
function applyFilters() {
    const search = document.getElementById('searchInput').value;
    const machine = document.getElementById('machineFilter').value;
    
    console.log('🔍 applyFilters called:', { search, machine });
    loadData(1, search, machine);
}

// Update statistics
function updateStatistics() {
    fetch('/impact/api/plan-scraper?page=1&per_page=1000')
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            const records = data.data;
            
            // Total records
            document.getElementById('totalRecords').textContent = data.pagination.total.toLocaleString();
            
            // Total machines
            const machines = [...new Set(records.map(r => r.print_machine))];
            document.getElementById('totalMachines').textContent = machines.length;
            
            // Total sheets
            const totalSheets = records.reduce((sum, r) => sum + parseFloat(r.run_length_sheet || 0), 0);
            document.getElementById('totalSheets').textContent = formatNumber(totalSheets);
            
            // Last update
            if (records.length > 0) {
                const lastUpdate = new Date(records[0].created_at);
                document.getElementById('lastUpdate').textContent = formatDate(lastUpdate);
            }
        }
    })
    .catch(error => {
        console.error('Error updating statistics:', error);
    });
}

// Delete record
function deleteRecord(id) {
    if (!confirm('Are you sure you want to delete this record?')) {
        return;
    }
    
    fetch(`/impact/api/plan-scraper/${id}`, {
        method: 'DELETE',
        headers: {
            'X-Requested-With': 'XMLHttpRequest'
        }
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            showAlert(data.message, 'success');
            loadData(currentPage, currentPerPage, currentSearch, currentMachine);
            updateStatistics();
        } else {
            showAlert(data.error || 'Error deleting record', 'danger');
        }
    })
    .catch(error => {
        console.error('Error:', error);
        showAlert('Error deleting record. Please try again.', 'danger');
    });
}

// Refresh data
function refreshData() {
    loadData(currentPage, currentPerPage, currentSearch, currentMachine);
    updateStatistics();
    loadPrintMachines();
}

// Show loading overlay
function showLoading() {
    document.getElementById('loadingOverlay').style.display = 'flex';
}

// Hide loading overlay
function hideLoading() {
    document.getElementById('loadingOverlay').style.display = 'none';
}

// Show alert message as toast notification
function showAlert(message, type) {
    // Create toast container if it doesn't exist
    let toastContainer = document.getElementById('toast-container');
    if (!toastContainer) {
        toastContainer = document.createElement('div');
        toastContainer.id = 'toast-container';
        toastContainer.style.cssText = `
            position: fixed;
            top: 20px;
            right: 20px;
            z-index: 9999;
            max-width: 350px;
        `;
        document.body.appendChild(toastContainer);
    }
    
    // Create unique toast ID
    const toastId = 'toast-' + Date.now();
    
    // Create toast HTML
    const toastHTML = `
        <div id="${toastId}" class="toast align-items-center text-white bg-${type === 'success' ? 'success' : 'danger'} border-0" role="alert" aria-live="assertive" aria-atomic="true">
            <div class="d-flex">
                <div class="toast-body">
                    <i class="fas fa-${type === 'success' ? 'check-circle' : 'exclamation-triangle'} me-2"></i>
                    ${message}
                </div>
                <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast" aria-label="Close"></button>
            </div>
        </div>
    `;
    
    // Add toast to container
    toastContainer.insertAdjacentHTML('beforeend', toastHTML);
    
    // Initialize and show toast using Bootstrap
    const toastElement = document.getElementById(toastId);
    const toast = new bootstrap.Toast(toastElement, {
        autohide: true,
        delay: 5000
    });
    
    toast.show();
    
    // Remove toast element after it's hidden
    toastElement.addEventListener('hidden.bs.toast', function () {
        toastElement.remove();
    });
}

// Format number with thousand separator
function formatNumber(num) {
    return parseFloat(num).toLocaleString('id-ID');
}

// Event listeners for filters
document.addEventListener('DOMContentLoaded', function() {
    // Add event listeners safely
    const searchInput = document.getElementById('searchInput');
    const machineFilter = document.getElementById('machineFilter');
    
    if (searchInput) {
        searchInput.addEventListener('keypress', function(e) {
            if (e.key === 'Enter') {
                applyFilters();
            }
        });
    }
    
    if (machineFilter) {
        machineFilter.addEventListener('change', applyFilters);
    }
    
    // Initialize page
    initializeUploadArea();
    loadPrintMachines();
    loadData();
    updateStatistics();
});

// Format date
function formatDate(dateString) {
    if (!dateString) return '-';
    
    const date = new Date(dateString);
    return date.toLocaleDateString('id-ID', {
        day: '2-digit',
        month: 'short',
        year: 'numeric',
        hour: '2-digit',
        minute: '2-digit'
    });
}

// Show upload loading state
function showUploadLoading(fileName) {
    const uploadArea = document.getElementById('uploadArea');
    const originalContent = uploadArea.innerHTML;
    
    // Store original content
    uploadArea.dataset.originalContent = originalContent;
    
    // Show loading state
    uploadArea.innerHTML = `
        <div class="upload-loading-state">
            <div class="spinner-border text-primary mb-3" role="status">
                <span class="visually-hidden">Loading...</span>
            </div>
            <h6 class="text-primary mb-2">Processing File...</h6>
            <p class="text-muted small mb-0">${fileName}</p>
            <div class="progress mt-3" style="height: 4px;">
                <div class="progress-bar progress-bar-striped progress-bar-animated bg-primary" role="progressbar" style="width: 100%"></div>
            </div>
        </div>
    `;
    
    uploadArea.classList.add('upload-processing');
    uploadArea.style.pointerEvents = 'none';
}

// Hide upload loading state
function hideUploadLoading() {
    const uploadArea = document.getElementById('uploadArea');
    
    // Restore original content
    if (uploadArea.dataset.originalContent) {
        uploadArea.innerHTML = uploadArea.dataset.originalContent;
        delete uploadArea.dataset.originalContent;
    }
    
    uploadArea.classList.remove('upload-processing');
    uploadArea.style.pointerEvents = 'auto';
}

// Event listeners for filters
document.getElementById('searchInput').addEventListener('keypress', function(e) {
    if (e.key === 'Enter') {
        applyFilters();
    }
});

document.getElementById('machineFilter').addEventListener('change', applyFilters);