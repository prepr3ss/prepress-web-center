// Plan Scraper JavaScript
let currentPage = 1;
let currentPerPage = 25;
let currentSearch = '';
let currentMachine = '';

// Context Menu Variables
let currentWorkOrderId = null;
let currentWorkOrderWO = null;
let currentWorkOrderMachine = null;
let currentWorkOrderItem = null;
let currentWorkOrderReceived = null;

// Initialize on page load - REMOVED (moved to bottom to avoid duplicate)

// Initialize upload area with drag and drop
function initializeUploadArea() {
    const uploadArea = document.getElementById('uploadArea');
    const fileInput = document.getElementById('fileInput');
    
    // Click to upload (but not when clicking on button)
    uploadArea.addEventListener('click', function(e) {
        // Don't trigger if clicking on button
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
    
    tableBody.innerHTML = data.map((item, index) => {
        const hasReceived = item.received === true || item.received === 'true';
        return `
        <tr class="plan-scraper-row ${hasReceived ? 'received' : ''}" data-id="${item.id}" data-received="${hasReceived ? 'true' : 'false'}"
            oncontextmenu="showContextMenu(event, ${item.id}, '${item.wo_number}', '${item.print_machine}', '${item.item_name}', ${item.received ? 'true' : 'false'}); return false;"
            onclick="handleRowClick(event, ${item.id})">
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
        </tr>
        `;
    }).join('');
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

// Debounce function to limit API calls
function debounce(func, wait) {
    let timeout;
    return function(...args) {
        const context = this;
        clearTimeout(timeout);
        timeout = setTimeout(() => func.apply(context, args), wait);
    };
}

// Show Context Menu
function showContextMenu(event, id, woNumber, machine, item, received) {
    event.preventDefault();
    
    // Convert received to boolean if it's a string
    const isReceived = received === true || received === 'true';
    
    currentWorkOrderId = id;
    currentWorkOrderWO = woNumber;
    currentWorkOrderMachine = machine;
    currentWorkOrderItem = item;
    currentWorkOrderReceived = isReceived;
    
    const contextMenu = document.getElementById('contextMenu');
    if (!contextMenu) return;
    
    // Clear existing menu items
    contextMenu.innerHTML = '';
    
    // Add menu items based on received status
    let menuHTML = '';
    
    // Always show View Details
    menuHTML += `
        <div class="context-menu-item" onclick="viewDetails(${id})">
            <i class="fas fa-eye"></i>
            View Details
        </div>
    `;
    
    if (!isReceived) {
        menuHTML += `
            <div class="context-menu-item success" onclick="receiveWorkOrder(${id})">
                <i class="fas fa-check"></i>
                Receive Work Order
            </div>
            <div class="context-menu-divider"></div>
            <div class="context-menu-item danger" onclick="deleteRecord(${id})">
                <i class="fas fa-trash"></i>
                Delete
            </div>
        `;
    } else {
        menuHTML += `
            <div class="context-menu-item disabled">
                <i class="fas fa-check-circle"></i>
                Already Received
            </div>
        `;
    }
    
    contextMenu.innerHTML = menuHTML;
    
    // Position menu
    const x = event.clientX;
    const y = event.clientY;
    
    // Make sure the menu doesn't go off screen
    const menuWidth = 200; // Approximate width
    const menuHeight = contextMenu.children.length * 40; // Approximate height
    
    let finalX = x;
    let finalY = y;
    
    if (x + menuWidth > window.innerWidth) {
        finalX = window.innerWidth - menuWidth - 10;
    }
    
    if (y + menuHeight > window.innerHeight) {
        finalY = window.innerHeight - menuHeight - 10;
    }
    
    contextMenu.style.left = finalX + 'px';
    contextMenu.style.top = finalY + 'px';
    
    // Show the menu with a slight delay for smooth animation
    setTimeout(() => {
        contextMenu.classList.add('show');
    }, 10);
}

// Hide Context Menu
function hideContextMenu() {
    const contextMenu = document.getElementById('contextMenu');
    if (contextMenu) {
        contextMenu.classList.remove('show');
    }
}

// View Details
function viewDetails(id) {
    fetch(`/impact/api/plan-scraper/${id}`)
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            const record = data.data;
            
            // Create details HTML
            const detailsHTML = `
                <div class="row">
                    <div class="col-md-6">
                        <strong>WO Number:</strong> ${record.wo_number}
                    </div>
                    <div class="col-md-6">
                        <strong>Print Machine:</strong> ${record.print_machine}
                    </div>
                </div>
                <div class="row mt-2">
                    <div class="col-md-6">
                        <strong>MC Number:</strong> ${record.mc_number}
                    </div>
                    <div class="col-md-6">
                        <strong>Item Name:</strong> ${record.item_name}
                    </div>
                </div>
                <div class="row mt-2">
                    <div class="col-md-6">
                        <strong>Up:</strong> ${record.num_up}
                    </div>
                    <div class="col-md-6">
                        <strong>Sheet:</strong> ${formatNumber(record.run_length_sheet)}
                    </div>
                </div>
                <div class="row mt-2">
                    <div class="col-md-6">
                        <strong>Paper Description:</strong> ${record.paper_desc || '-'}
                    </div>
                    <div class="col-md-6">
                        <strong>Paper Type:</strong> ${record.paper_type || '-'}
                    </div>
                </div>
                <div class="row mt-2">
                    <div class="col-md-6">
                        <strong>Status:</strong> 
                        <span class="badge ${record.received ? 'bg-success' : 'bg-warning'}">
                            ${record.received ? 'Received' : 'Not Received'}
                        </span>
                    </div>
                    <div class="col-md-6">
                        <strong>Created At:</strong> ${formatDate(record.created_at) || '-'}
                    </div>
                </div>
            `;
            
            // Show in modal
            const modal = document.createElement('div');
            modal.className = 'modal fade';
            modal.innerHTML = `
                <div class="modal-dialog modal-dialog-centered">
                    <div class="modal-content">
                        <div class="modal-header">
                            <h5 class="modal-title">Work Order Details</h5>
                            <button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="Close"></button>
                        </div>
                        <div class="modal-body">
                            ${detailsHTML}
                        </div>
                        <div class="modal-footer">
                            <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Close</button>
                        </div>
                    </div>
                </div>
            `;
            
            document.body.appendChild(modal);
            const bsModal = new bootstrap.Modal(modal);
            bsModal.show();
            
            // Remove modal from DOM when hidden
            modal.addEventListener('hidden.bs.modal', function() {
                document.body.removeChild(modal);
            });
        } else {
            showAlert(data.error || 'Error loading work order details', 'danger');
        }
    })
    .catch(error => {
        console.error('Error:', error);
        showAlert('Error loading work order details. Please try again.', 'danger');
    });
}

// Handle row click - disabled since we have context menu (right-click)
function handleRowClick(event, id) {
    // Left-click is disabled - use right-click context menu instead
    return;
}

// Receive Work Order
function receiveWorkOrder(id) {
    console.log('📥 receiveWorkOrder called with ID:', id);
    
    // Find record data from current page
    fetch(`/impact/api/plan-scraper/${id}`)
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            const record = data.data;
            
            // Populate modal with record details
            document.getElementById('receiveWO').textContent = record.wo_number || 'N/A';
            document.getElementById('receiveMachine').textContent = record.print_machine || 'N/A';
            document.getElementById('receiveItem').textContent = record.item_name || 'N/A';
            
            // Show modal
            const receiveModal = new bootstrap.Modal(document.getElementById('receiveModal'));
            receiveModal.show();
        } else {
            showAlert('Gagal memuat data record', 'danger');
        }
    })
    .catch(error => {
        console.error('Error loading record data:', error);
        showAlert('Terjadi kesalahan saat memuat data', 'danger');
    });
}

// Receive data storage for merge logic
let pendingReceiveData = {
    planDataId: null,
    priority: null,
    notes: null,
    primaryWorkQueueId: null,
    existingWorkOrders: [],
    newWONumber: null,
    mcNumber: null,
    itemName: null
};

// Confirm Receive
function confirmReceive() {
    const id = currentWorkOrderId;
    if (!id) return;
    
    const priority = document.getElementById('receivePriority').value;
    const notes = document.getElementById('receiveNotes').value;
    
    console.log('📥 Confirming receive for ID:', id, { priority, notes });
    
    // Show loading state
    const confirmBtn = document.querySelector('#receiveModal .btn-success');
    const originalText = confirmBtn.innerHTML;
    confirmBtn.disabled = true;
    confirmBtn.innerHTML = '<i class="fas fa-spinner fa-spin me-2"></i>Receiving...';
    
    // Perform receive request
    fetch(`/impact/api/plan-scraper/${id}/receive`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-Requested-With': 'XMLHttpRequest'
        },
        body: JSON.stringify({
            priority: priority,
            notes: notes
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            // Check if merge is required
            if (data.merge_required) {
                console.log('🔗 MERGE REQUIRED: Showing merge confirmation modal');
                console.log('📋 Merge data:', data);
                
                // Store pending receive data for merge decision
                pendingReceiveData = {
                    planDataId: id,
                    priority: priority,
                    notes: notes,
                    primaryWorkQueueId: data.primary_work_queue_id,
                    existingWorkOrders: data.existing_work_orders,
                    newWONumber: data.new_wo_number,
                    mcNumber: data.mc_number,
                    itemName: data.item_name
                };
                
                console.log(`✅ Stored pending receive data:`, pendingReceiveData);
                
                // Populate merge confirmation modal with all WOs
                populateMergeModal(data);
                
                // Close receive modal
                const receiveModal = bootstrap.Modal.getInstance(document.getElementById('receiveModal'));
                receiveModal.hide();
                
                // Show merge confirmation modal
                const mergeModal = new bootstrap.Modal(document.getElementById('receiveMergeConfirmModal'));
                mergeModal.show();
            } else {
                // No merge required, just complete the receive
                console.log('✅ Work order received successfully (no merge needed)');
                
                // Close modal
                const receiveModal = bootstrap.Modal.getInstance(document.getElementById('receiveModal'));
                receiveModal.hide();
                
                // Show success message
                showAlert('Work order received successfully!', 'success');
                
                // Reload data and statistics
                loadData(currentPage, currentSearch, currentMachine);
                updateStatistics();
                loadPrintMachines();
            }
        } else {
            showAlert(data.error || 'Gagal menerima work order', 'danger');
        }
    })
    .catch(error => {
        console.error('Error receiving work order:', error);
        showAlert('Terjadi kesalahan saat menerima work order', 'danger');
    })
    .finally(() => {
        // Reset button state
        confirmBtn.disabled = false;
        confirmBtn.innerHTML = originalText;
    });
}

// Populate merge confirmation modal with list of all WOs to be merged
function populateMergeModal(mergeData) {
    console.log('📋 Populating merge confirmation modal with:', mergeData);
    
    // Update modal title with count
    const totalWOs = (mergeData.existing_work_orders?.length || 0) + 1; // +1 for new WO
    const modalTitle = document.querySelector('#receiveMergeConfirmModal .modal-title');
    if (modalTitle) {
        modalTitle.innerHTML = `<i class="fas fa-code-branch me-2"></i>Merge ${totalWOs} Work Orders?`;
    }
    
    // Build WO list HTML
    let woListHTML = '';
    
    // Add existing WOs
    if (mergeData.existing_work_orders && mergeData.existing_work_orders.length > 0) {
        mergeData.existing_work_orders.forEach((wo, index) => {
            woListHTML += `
                <div class="d-flex align-items-center gap-2 py-1 px-2 bg-light rounded mb-1">
                    <i class="fas fa-circle-check text-success"></i>
                    <strong>WO #${wo.wo_number}</strong>
                    ${index === 0 ? '<span class="badge bg-primary ms-auto">Primary</span>' : '<span class="badge bg-secondary ms-auto">Will Merge</span>'}
                </div>
            `;
        });
    }
    
    // Add new WO
    woListHTML += `
        <div class="d-flex align-items-center gap-2 py-1 px-2 bg-light rounded mb-1">
            <i class="fas fa-plus text-info"></i>
            <strong>WO #${mergeData.new_wo_number}</strong>
            <span class="badge bg-info ms-auto">New</span>
        </div>
    `;
    
    // Update modal with merged list
    const woListContainer = document.querySelector('#receiveMergeConfirmModal .modal-body');
    if (woListContainer) {
        // Find or create the WO list section
        let woListSection = woListContainer.querySelector('#mergeWOList');
        if (!woListSection) {
            woListSection = document.createElement('div');
            woListSection.id = 'mergeWOList';
            woListSection.className = 'mb-3';
            // Insert after the info alert
            const infoAlert = woListContainer.querySelector('[style*="background"]');
            if (infoAlert) {
                infoAlert.parentNode.insertBefore(woListSection, infoAlert.nextSibling);
            }
        }
        woListSection.innerHTML = `
            <div style="background: #f0f4ff; border-left: 4px solid #0d6efd; padding: 1rem; border-radius: 0.5rem; margin-bottom: 1.5rem;">
                <strong class="d-block mb-2"><i class="fas fa-list me-2"></i>Work Orders to Merge:</strong>
                ${woListHTML}
            </div>
        `;
    }
    
    console.log('✅ Merge modal populated');
}

// Confirm merge decision from merge confirmation modal
function confirmReceiveMergeDecision(shouldMerge) {
    console.log(`📋 Merge decision: ${shouldMerge ? 'MERGE' : 'SEPARATE'}`);
    console.log('📋 Pending receive data:', pendingReceiveData);
    
    // Show loading
    const confirmBtn = shouldMerge ? 
        document.querySelector('#receiveMergeConfirmModal .btn-primary') :
        document.querySelector('#receiveMergeConfirmModal .btn-outline-primary');
    const originalText = confirmBtn.innerHTML;
    confirmBtn.disabled = true;
    confirmBtn.innerHTML = '<i class="fas fa-spinner fa-spin me-2"></i>Processing...';
    
    // Call merge endpoint
    fetch('/impact/api/work-queue/merge', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-Requested-With': 'XMLHttpRequest'
        },
        body: JSON.stringify({
            existing_work_queue_id: pendingReceiveData.primaryWorkQueueId,
            new_plan_data_id: pendingReceiveData.planDataId,
            priority: pendingReceiveData.priority,
            notes: pendingReceiveData.notes,
            should_merge: shouldMerge
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            // Close merge modal
            const mergeModal = bootstrap.Modal.getInstance(document.getElementById('receiveMergeConfirmModal'));
            mergeModal.hide();
            
            let message;
            if (shouldMerge) {
                // Build merged message with all WO numbers
                const allWOs = pendingReceiveData.existingWorkOrders.map(wo => wo.wo_number);
                allWOs.push(pendingReceiveData.newWONumber);
                const mergedList = allWOs.join(', ');
                message = `Merged ${allWOs.length} work orders: ${mergedList}`;
            } else {
                message = `Work order #${pendingReceiveData.newWONumber} received as separate`;
            }
            
            showAlert(message, 'success');
            
            // Reload data and statistics
            loadData(currentPage, currentSearch, currentMachine);
            updateStatistics();
            loadPrintMachines();
        } else {
            showAlert(data.error || 'Error processing merge decision', 'danger');
        }
    })
    .catch(error => {
        console.error('Error in merge decision:', error);
        showAlert('Error processing merge decision', 'danger');
    })
    .finally(() => {
        // Reset button state
        confirmBtn.disabled = false;
        confirmBtn.innerHTML = originalText;
    });
}

// Event listeners for filters
document.addEventListener('DOMContentLoaded', function() {
    // Add event listeners safely
    const searchInput = document.getElementById('searchInput');
    const machineFilter = document.getElementById('machineFilter');
    
    if (searchInput) {
        // Create debounced version of applyFilters for search input
        const debouncedSearch = debounce(function() {
            applyFilters();
        }, 300); // 300ms delay
        
        // Add keyup event for real-time search
        searchInput.addEventListener('keyup', debouncedSearch);
        
        // Keep Enter key functionality as well
        searchInput.addEventListener('keypress', function(e) {
            if (e.key === 'Enter') {
                e.preventDefault(); // Prevent form submission
                applyFilters();
            }
        });
    }
    
    if (machineFilter) {
        machineFilter.addEventListener('change', applyFilters);
    }
    
    // Add click event listener to hide context menu when clicking elsewhere
    document.addEventListener('click', function(event) {
        const contextMenu = document.getElementById('contextMenu');
        if (contextMenu && !contextMenu.contains(event.target)) {
            hideContextMenu();
        }
    });

    // Add context menu event listener to prevent default browser context menu
    document.addEventListener('contextmenu', function(event) {
        if (event.target.closest('.plan-scraper-row')) {
            event.preventDefault();
        }
    });
    
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

// Show upload loading
function showUploadLoading(fileName) {
    const uploadArea = document.getElementById('uploadArea');
    if (uploadArea) {
        uploadArea.innerHTML = `
            <i class="fas fa-spinner fa-spin upload-icon"></i>
            <h6>Uploading ${fileName}...</h6>
            <p class="text-muted mb-3 small">Please wait...</p>
        `;
        uploadArea.style.cursor = 'not-allowed';
    }
}

// Hide upload loading
function hideUploadLoading() {
    const uploadArea = document.getElementById('uploadArea');
    if (uploadArea) {
        uploadArea.innerHTML = `
            <i class="fas fa-file-excel upload-icon"></i>
            <h6>Upload Excel File</h6>
            <p class="text-muted mb-3 small">Drag & drop or click to browse</p>
            <input type="file" id="fileInput" accept=".xlsx,.xls" style="display: none;">
            <button class="btn btn-primary btn-sm" onclick="document.getElementById('fileInput').click()">
                <i class="fas fa-folder-open me-2"></i>
                Choose File
            </button>
        `;
        uploadArea.style.cursor = 'pointer';
    }
}
