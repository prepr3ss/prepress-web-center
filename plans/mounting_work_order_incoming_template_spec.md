# Spesifikasi Template HTML untuk Work Order Incoming

## 1. Struktur File: templates/mounting_work_order_incoming.html

### 1.1. Header Section
```html
<!-- Page Header dengan Mounting theme -->
<div class="page-header">
    <div class="container-fluid">
        <div class="d-flex justify-content-between align-items-center">
            <div>
                <h2 class="mb-1 text-white">Work Order Incoming</h2>
                <p class="mb-0 opacity-75">Input work order dari divisi PPIC</p>
            </div>
        </div>
    </div>
</div>
```

### 1.2. Main Content Structure
```html
<div class="container-fluid pt-3">
    <!-- Input Section -->
    <div class="card data-card mb-4">
        <div class="card-header card-header-clean">
            <h5 class="mb-0">
                <i class="fas fa-plus-circle me-2 text-primary"></i>
                Input Work Order
            </h5>
        </div>
        <div class="card-body">
            <!-- Excel-like Input Table -->
            <div class="table-responsive">
                <table class="table table-bordered" id="workOrderTable">
                    <thead class="table-light">
                        <tr>
                            <th style="width: 50px;">No</th>
                            <th>WO Number *</th>
                            <th>MC Number *</th>
                            <th>Customer Name *</th>
                            <th>Item Name *</th>
                            <th>Print Block *</th>
                            <th>Print Machine *</th>
                            <th>Run Length</th>
                            <th>Sheet Size</th>
                            <th>Paper Type</th>
                            <th style="width: 80px;">Action</th>
                        </tr>
                    </thead>
                    <tbody id="workOrderTableBody">
                        <!-- Dynamic rows will be inserted here -->
                    </tbody>
                </table>
            </div>
            
            <!-- Action Buttons -->
            <div class="d-flex justify-content-between align-items-center mt-3">
                <div>
                    <button type="button" class="btn btn-outline-clean btn-clean" id="addRowBtn">
                        <i class="fas fa-plus me-1"></i>Tambah Baris
                    </button>
                    <button type="button" class="btn btn-outline-clean btn-clean" id="clearAllBtn">
                        <i class="fas fa-eraser me-1"></i>Hapus Semua
                    </button>
                </div>
                <div>
                    <span class="text-muted me-3" id="rowCountInfo">0 baris</span>
                    <button type="button" class="btn btn-primary-clean btn-clean" id="submitBtn" disabled>
                        <i class="fas fa-save me-1"></i>Submit All
                    </button>
                </div>
            </div>
        </div>
    </div>

    <!-- Data Table Section -->
    <div class="card data-card">
        <div class="card-header card-header-clean">
            <div class="d-flex justify-content-between align-items-center">
                <h5 class="mb-0">
                    <i class="fas fa-list me-2 text-info"></i>
                    Data Work Order Incoming
                </h5>
                <div>
                    <button type="button" class="btn btn-sm btn-outline-clean btn-clean" id="refreshBtn">
                        <i class="fas fa-sync-alt me-1"></i>Refresh
                    </button>
                </div>
            </div>
        </div>
        <div class="card-body">
            <!-- Filter Section -->
            <div class="row mb-3">
                <div class="col-md-3">
                    <label class="form-label info-label">Filter Tanggal</label>
                    <input type="date" class="form-control form-control-clean" id="filterDate">
                </div>
                <div class="col-md-3">
                    <label class="form-label info-label">Filter Status</label>
                    <select class="form-control form-control-clean" id="filterStatus">
                        <option value="">Semua Status</option>
                        <option value="incoming">Incoming</option>
                        <option value="processed">Processed</option>
                        <option value="cancelled">Cancelled</option>
                    </select>
                </div>
                <div class="col-md-3">
                    <label class="form-label info-label">Filter Customer</label>
                    <input type="text" class="form-control form-control-clean" id="filterCustomer" placeholder="Nama customer...">
                </div>
                <div class="col-md-3">
                    <label class="form-label info-label">Pencarian</label>
                    <input type="text" class="form-control form-control-clean" id="searchInput" placeholder="Cari WO, MC, Item...">
                </div>
            </div>
            
            <!-- Data Table -->
            <div class="table-responsive">
                <table class="table table-hover" id="dataTable">
                    <thead class="table-light">
                        <tr>
                            <th>Tanggal & Waktu</th>
                            <th>WO Number</th>
                            <th>MC Number</th>
                            <th>Customer Name</th>
                            <th>Item Name</th>
                            <th>Print Block</th>
                            <th>Print Machine</th>
                            <th>Run Length</th>
                            <th>Sheet Size</th>
                            <th>Paper Type</th>
                            <th>Status</th>
                            <th>Actions</th>
                        </tr>
                    </thead>
                    <tbody id="dataTableBody">
                        <!-- Data will be loaded here -->
                    </tbody>
                </table>
            </div>
            
            <!-- Pagination -->
            <nav class="mt-3">
                <ul class="pagination pagination-sm justify-content-center" id="pagination">
                    <!-- Pagination will be generated here -->
                </ul>
            </nav>
        </div>
    </div>
</div>
```

### 1.3. Modal Konfirmasi
```html
<!-- Confirmation Modal -->
<div class="modal fade" id="confirmModal" tabindex="-1">
    <div class="modal-dialog modal-dialog-centered">
        <div class="modal-content" style="border: none; border-radius: 15px; overflow: hidden;">
            <div class="modal-header" style="background: linear-gradient(135deg, #2193b0 0%, #6dd5ed 100%); color: white; border: none;">
                <h5 class="modal-title"><i class="fas fa-exclamation-triangle me-2"></i>Konfirmasi Submit</h5>
                <button type="button" class="btn-close btn-close-white" data-bs-dismiss="modal"></button>
            </div>
            <div class="modal-body p-4">
                <div class="alert" style="background: linear-gradient(135deg, #e3f2fd 0%, #f3e5f5 100%); border: none; border-radius: 10px;">
                    <div class="d-flex align-items-center">
                        <i class="fas fa-info-circle me-2 text-primary"></i>
                        <div>
                            <strong>Verifikasi Data</strong>
                            <div class="small text-muted" id="confirmMessage">Terdapat 0 work order yang akan disubmit. Lanjutkan?</div>
                        </div>
                    </div>
                </div>
            </div>
            <div class="modal-footer border-0 p-4">
                <button type="button" class="btn btn-outline-clean btn-clean" data-bs-dismiss="modal">
                    <i class="fas fa-times me-1"></i>Batal
                </button>
                <button type="button" class="btn btn-primary-clean btn-clean" id="confirmSubmitBtn">
                    <i class="fas fa-check me-1"></i>Ya, Submit
                </button>
            </div>
        </div>
    </div>
</div>
```

## 2. Styling CSS

### 2.1. Custom Styles
```css
/* Table Styles */
#workOrderTable {
    font-size: 0.9rem;
}

#workOrderTable th {
    background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%);
    font-weight: 600;
    font-size: 0.85rem;
    text-transform: uppercase;
    letter-spacing: 0.5px;
    border: 1px solid #dee2e6;
}

#workOrderTable td {
    vertical-align: middle;
    padding: 0.5rem;
}

#workOrderTable input, #workOrderTable select {
    border: 1px solid #ced4da;
    border-radius: 5px;
    padding: 0.25rem 0.5rem;
    font-size: 0.85rem;
    transition: all 0.2s ease;
}

#workOrderTable input:focus, #workOrderTable select:focus {
    border-color: #2193b0;
    box-shadow: 0 0 0 0.2rem rgba(33, 147, 176, 0.25);
    outline: none;
}

#workOrderTable input.is-invalid {
    border-color: #dc3545;
    background-color: #f8d7da;
}

/* Button Styles */
.btn-action {
    padding: 0.25rem 0.5rem;
    font-size: 0.8rem;
    border-radius: 5px;
}

/* Row Count Info */
#rowCountInfo {
    font-weight: 600;
    color: #6c757d;
    background: #f8f9fa;
    padding: 0.25rem 0.75rem;
    border-radius: 15px;
    font-size: 0.85rem;
}

/* Data Table Styles */
#dataTable th {
    background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%);
    font-weight: 600;
    font-size: 0.85rem;
    text-transform: uppercase;
    letter-spacing: 0.5px;
    border: 1px solid #dee2e6;
    position: sticky;
    top: 0;
    z-index: 10;
}

.status-badge {
    padding: 0.25rem 0.75rem;
    border-radius: 15px;
    font-size: 0.75rem;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.5px;
}

.status-incoming {
    background: linear-gradient(135deg, #ff9a56 0%, #ff6b35 100%);
    color: white;
}

.status-processed {
    background: linear-gradient(135deg, #56ab2f 0%, #a8e6cf 100%);
    color: white;
}

.status-cancelled {
    background: linear-gradient(135deg, #dc3545 0%, #ff4b2b 100%);
    color: white;
}
```

## 3. JavaScript Functionality

### 3.1. Core Functions
```javascript
// Global variables
let workOrderData = [];
let currentEditingRow = null;

// Initialize table with empty rows
function initializeTable() {
    // Add 5 empty rows by default
    for (let i = 0; i < 5; i++) {
        addNewRow();
    }
    updateRowCount();
}

// Add new row
function addNewRow() {
    const rowCount = workOrderData.length;
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
    
    workOrderData.push(newRow);
    renderRow(newRow, rowCount + 1);
    updateRowCount();
}

// Render single row
function renderRow(data, rowNumber) {
    const tbody = document.getElementById('workOrderTableBody');
    const row = document.createElement('tr');
    row.innerHTML = `
        <td>${rowNumber}</td>
        <td><input type="text" class="form-control form-control-sm" data-field="wo_number" data-id="${data.id}" value="${data.wo_number}" required></td>
        <td><input type="text" class="form-control form-control-sm" data-field="mc_number" data-id="${data.id}" value="${data.mc_number}" required></td>
        <td><input type="text" class="form-control form-control-sm" data-field="customer_name" data-id="${data.id}" value="${data.customer_name}" required></td>
        <td><input type="text" class="form-control form-control-sm" data-field="item_name" data-id="${data.id}" value="${data.item_name}" required></td>
        <td><input type="text" class="form-control form-control-sm" data-field="print_block" data-id="${data.id}" value="${data.print_block}" required></td>
        <td><input type="text" class="form-control form-control-sm" data-field="print_machine" data-id="${data.id}" value="${data.print_machine}" required></td>
        <td><input type="number" class="form-control form-control-sm" data-field="run_length_sheet" data-id="${data.id}" value="${data.run_length_sheet}"></td>
        <td><input type="text" class="form-control form-control-sm" data-field="sheet_size" data-id="${data.id}" value="${data.sheet_size}"></td>
        <td><input type="text" class="form-control form-control-sm" data-field="paper_type" data-id="${data.id}" value="${data.paper_type}"></td>
        <td>
            <button type="button" class="btn btn-sm btn-danger btn-action" onclick="removeRow('${data.id}')">
                <i class="fas fa-trash"></i>
            </button>
        </td>
    `;
    tbody.appendChild(row);
}

// Remove row
function removeRow(id) {
    workOrderData = workOrderData.filter(item => item.id !== id);
    renderAllRows();
    updateRowCount();
}

// Update row count
function updateRowCount() {
    const count = workOrderData.length;
    document.getElementById('rowCountInfo').textContent = `${count} baris`;
    document.getElementById('submitBtn').disabled = count === 0;
}

// Validate all rows
function validateData() {
    let isValid = true;
    const errors = [];
    
    workOrderData.forEach((item, index) => {
        const requiredFields = ['wo_number', 'mc_number', 'customer_name', 'item_name', 'print_block', 'print_machine'];
        
        requiredFields.forEach(field => {
            if (!item[field] || item[field].trim() === '') {
                isValid = false;
                errors.push(`Baris ${index + 1}: ${field} tidak boleh kosong`);
            }
        });
    });
    
    return { isValid, errors };
}

// Show confirmation modal
function showConfirmationModal() {
    const validation = validateData();
    
    if (!validation.isValid) {
        showToast('Error validasi: ' + validation.errors.join(', '), 'error');
        return;
    }
    
    const count = workOrderData.length;
    document.getElementById('confirmMessage').textContent = `Terdapat ${count} work order yang akan disubmit. Lanjutkan?`;
    
    const modal = new bootstrap.Modal(document.getElementById('confirmModal'));
    modal.show();
}

// Submit data
async function submitData() {
    try {
        const response = await fetch('/impact/api/mounting-work-order-incoming/batch', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                work_orders: workOrderData,
                created_by: window.currentUserName
            })
        });
        
        if (response.ok) {
            showToast('Data berhasil disubmit!', 'success');
            clearAllRows();
            loadData();
        } else {
            const error = await response.json();
            showToast('Gagal submit: ' + error.message, 'error');
        }
    } catch (error) {
        showToast('Terjadi kesalahan: ' + error.message, 'error');
    }
}

// Clear all rows
function clearAllRows() {
    workOrderData = [];
    renderAllRows();
    updateRowCount();
}

// Render all rows
function renderAllRows() {
    const tbody = document.getElementById('workOrderTableBody');
    tbody.innerHTML = '';
    
    workOrderData.forEach((item, index) => {
        renderRow(item, index + 1);
    });
}

// Load data from server
async function loadData() {
    try {
        const response = await fetch('/impact/api/mounting-work-order-incoming');
        const data = await response.json();
        
        renderDataTable(data.data);
        updatePagination(data.pagination);
    } catch (error) {
        showToast('Gagal load data: ' + error.message, 'error');
    }
}

// Render data table
function renderDataTable(data) {
    const tbody = document.getElementById('dataTableBody');
    tbody.innerHTML = '';
    
    data.forEach(item => {
        const row = document.createElement('tr');
        row.innerHTML = `
            <td>${formatDateTimeIndonesia(item.incoming_datetime)}</td>
            <td>${item.wo_number}</td>
            <td>${item.mc_number}</td>
            <td>${item.customer_name}</td>
            <td>${item.item_name}</td>
            <td>${item.print_block}</td>
            <td>${item.print_machine}</td>
            <td>${item.run_length_sheet || '-'}</td>
            <td>${item.sheet_size || '-'}</td>
            <td>${item.paper_type || '-'}</td>
            <td><span class="status-badge status-${item.status}">${item.status}</span></td>
            <td>
                <button type="button" class="btn btn-sm btn-primary btn-action" onclick="editItem(${item.id})">
                    <i class="fas fa-edit"></i>
                </button>
                <button type="button" class="btn btn-sm btn-danger btn-action" onclick="deleteItem(${item.id})">
                    <i class="fas fa-trash"></i>
                </button>
            </td>
        `;
        tbody.appendChild(row);
    });
}

// Event listeners
document.addEventListener('DOMContentLoaded', function() {
    initializeTable();
    loadData();
    
    // Add event listeners
    document.getElementById('addRowBtn').addEventListener('click', addNewRow);
    document.getElementById('clearAllBtn').addEventListener('click', clearAllRows);
    document.getElementById('submitBtn').addEventListener('click', showConfirmationModal);
    document.getElementById('confirmSubmitBtn').addEventListener('click', submitData);
    document.getElementById('refreshBtn').addEventListener('click', loadData);
    
    // Input change handlers
    document.getElementById('workOrderTableBody').addEventListener('input', function(e) {
        if (e.target.matches('input[data-field]')) {
            const id = parseFloat(e.target.dataset.id);
            const field = e.target.dataset.field;
            const value = e.target.value;
            
            const item = workOrderData.find(item => item.id === id);
            if (item) {
                item[field] = value;
            }
        }
    });
    
    // Filter handlers
    document.getElementById('filterDate').addEventListener('change', loadData);
    document.getElementById('filterStatus').addEventListener('change', loadData);
    document.getElementById('filterCustomer').addEventListener('input', debounce(loadData, 500));
    document.getElementById('searchInput').addEventListener('input', debounce(loadData, 500));
});
```

## 4. Responsive Design

### 4.1. Mobile Adaptations
```css
@media (max-width: 768px) {
    #workOrderTable {
        font-size: 0.8rem;
    }
    
    #workOrderTable th, #workOrderTable td {
        padding: 0.25rem;
    }
    
    .btn-action {
        padding: 0.2rem 0.3rem;
        font-size: 0.7rem;
    }
    
    #dataTable {
        font-size: 0.8rem;
    }
    
    .status-badge {
        font-size: 0.65rem;
        padding: 0.2rem 0.5rem;
    }
}
```

## 5. Accessibility Features

### 5.1. ARIA Labels
```html
<input type="text" class="form-control form-control-sm" 
       data-field="wo_number" 
       data-id="${data.id}" 
       value="${data.wo_number}" 
       required 
       aria-label="WO Number"
       aria-describedby="woNumberHelp">
<small id="woNumberHelp" class="form-text text-muted">Nomor Work Order wajib diisi</small>
```

### 5.2. Keyboard Navigation
- Tab order yang logical
- Shortcut keys:
  - Ctrl+N: Tambah baris baru
  - Ctrl+S: Submit data
  - Ctrl+R: Refresh data
  - Escape: Tutup modal

## 6. Error Handling

### 6.1. Validation Messages
```javascript
const validationMessages = {
    wo_number: 'WO Number tidak boleh kosong',
    mc_number: 'MC Number tidak boleh kosong',
    customer_name: 'Customer Name tidak boleh kosong',
    item_name: 'Item Name tidak boleh kosong',
    print_block: 'Print Block tidak boleh kosong',
    print_machine: 'Print Machine tidak boleh kosong'
};
```

### 6.2. Error Display
```javascript
function showFieldError(fieldId, message) {
    const field = document.querySelector(`[data-field="${fieldId}"]`);
    if (field) {
        field.classList.add('is-invalid');
        
        // Create or update error message
        let errorDiv = field.parentNode.querySelector('.invalid-feedback');
        if (!errorDiv) {
            errorDiv = document.createElement('div');
            errorDiv.className = 'invalid-feedback';
            field.parentNode.appendChild(errorDiv);
        }
        errorDiv.textContent = message;
    }
}

function clearFieldError(fieldId) {
    const field = document.querySelector(`[data-field="${fieldId}"]`);
    if (field) {
        field.classList.remove('is-invalid');
        const errorDiv = field.parentNode.querySelector('.invalid-feedback');
        if (errorDiv) {
            errorDiv.remove();
        }
    }
}
```

## 7. Performance Optimizations

### 7.1. Debouncing
```javascript
function debounce(func, wait) {
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
```

### 7.2. Virtual Scrolling (untuk data besar)
- Implementasi virtual scrolling jika data > 1000 baris
- Lazy loading untuk pagination