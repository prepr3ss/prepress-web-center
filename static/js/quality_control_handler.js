/**
 * Quality Control Handler JavaScript
 * Menggunakan Clean Framework
 * 
 * File ini adalah contoh implementasi JavaScript handler
 * untuk module Quality Control menggunakan Clean Framework
 */

// =================
// CONFIGURATION
// =================
const QCConfig = {
    apiEndpoints: {
        inspections: '/api/quality-control-data',
        newInspection: '/api/quality-control/new-inspection',
        inspectionDetail: '/api/quality-control/inspection',
        updateInspection: '/api/quality-control/update-inspection',
        deleteInspection: '/api/quality-control/delete-inspection'
    },
    refreshInterval: 30000, // 30 seconds
    maxRetries: 3
};

// =================
// GLOBAL VARIABLES
// =================
let currentInspections = [];
let filteredInspections = [];
let selectedInspectionId = null;

// =================
// INITIALIZATION
// =================
document.addEventListener('DOMContentLoaded', function() {
    console.log('Quality Control module initialized');
    
    // Initialize module
    initializeQCModule();
    
    // Set up event listeners
    setupEventListeners();
    
    // Load initial data
    loadInspections();
    
    // Set up auto-refresh
    if (QCConfig.refreshInterval > 0) {
        setInterval(loadInspections, QCConfig.refreshInterval);
    }
});

// =================
// MODULE INITIALIZATION
// =================
function initializeQCModule() {
    console.log('Initializing Quality Control module...');
    
    // Set up form validation
    setupFormValidation();
    
    // Initialize date pickers
    initializeDatePickers();
    
    // Set up tooltips
    const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });
}

// =================
// EVENT LISTENERS
// =================
function setupEventListeners() {
    // Filter event listeners
    const statusFilter = document.getElementById('statusFilter');
    const startDate = document.getElementById('startDate');
    const endDate = document.getElementById('endDate');
    const searchInput = document.getElementById('searchInput');
    
    if (statusFilter) {
        statusFilter.addEventListener('change', applyInspectionFilters);
    }
    
    if (startDate) {
        startDate.addEventListener('change', applyInspectionFilters);
    }
    
    if (endDate) {
        endDate.addEventListener('change', applyInspectionFilters);
    }
    
    if (searchInput) {
        let searchTimeout;
        searchInput.addEventListener('input', function() {
            clearTimeout(searchTimeout);
            searchTimeout = setTimeout(applyInspectionFilters, 300);
        });
    }
    
    // Modal event listeners
    const newInspectionModal = document.getElementById('newInspectionModal');
    if (newInspectionModal) {
        newInspectionModal.addEventListener('hidden.bs.modal', function() {
            resetNewInspectionForm();
        });
    }
}

// =================
// DATA LOADING
// =================
async function loadInspections() {
    try {
        showLoadingState();
        
        const response = await fetch(QCConfig.apiEndpoints.inspections);
        const data = await response.json();
        
        if (data.success && data.data) {
            currentInspections = data.data;
            applyInspectionFilters();
            updateSummaryCards();
        } else {
            showNoDataState();
            console.error('Failed to load inspections:', data.message);
        }
    } catch (error) {
        console.error('Error loading inspections:', error);
        showErrorState('Failed to load inspection data');
    }
}

// =================
// FILTERING
// =================
function applyInspectionFilters() {
    let filtered = [...currentInspections];
    
    // Status filter
    const statusFilter = document.getElementById('statusFilter');
    if (statusFilter && statusFilter.value) {
        filtered = filtered.filter(item => 
            item.inspection_status === statusFilter.value
        );
    }
    
    // Date range filter
    const startDate = document.getElementById('startDate');
    const endDate = document.getElementById('endDate');
    
    if (startDate && startDate.value) {
        filtered = filtered.filter(item => 
            new Date(item.inspection_date) >= new Date(startDate.value)
        );
    }
    
    if (endDate && endDate.value) {
        filtered = filtered.filter(item => 
            new Date(item.inspection_date) <= new Date(endDate.value)
        );
    }
    
    // Search filter
    const searchInput = document.getElementById('searchInput');
    if (searchInput && searchInput.value.trim()) {
        const searchTerm = searchInput.value.toLowerCase();
        filtered = filtered.filter(item => 
            item.inspection_id.toLowerCase().includes(searchTerm) ||
            item.product_name.toLowerCase().includes(searchTerm) ||
            item.inspector_name.toLowerCase().includes(searchTerm) ||
            item.batch_number.toLowerCase().includes(searchTerm)
        );
    }
    
    filteredInspections = filtered;
    displayInspections();
}

function resetInspectionFilters() {
    // Reset all filter inputs
    const statusFilter = document.getElementById('statusFilter');
    const startDate = document.getElementById('startDate');
    const endDate = document.getElementById('endDate');
    const searchInput = document.getElementById('searchInput');
    
    if (statusFilter) statusFilter.value = '';
    if (startDate) startDate.value = '';
    if (endDate) endDate.value = '';
    if (searchInput) searchInput.value = '';
    
    filteredInspections = [...currentInspections];
    displayInspections();
}

// =================
// DISPLAY FUNCTIONS
// =================
function displayInspections() {
    if (filteredInspections.length === 0) {
        showNoDataState();
        return;
    }
    
    const tableBody = document.getElementById('dataTableBody');
    const dataCount = document.getElementById('dataCount');
    
    // Update count
    dataCount.textContent = `${filteredInspections.length} inspections found`;
    
    // Generate table rows
    tableBody.innerHTML = filteredInspections.map((inspection, index) => {
        return generateInspectionTableRow(inspection, index);
    }).join('');
    
    showDataTableState();
}

function generateInspectionTableRow(inspection, index) {
    const statusConfig = {
        'pending': { class: 'clean-badge-accent', icon: 'fas fa-clock' },
        'passed': { class: 'clean-badge-success', icon: 'fas fa-check' },
        'failed': { class: 'clean-badge-secondary', icon: 'fas fa-times' },
        'rework': { class: 'clean-badge-info', icon: 'fas fa-redo' }
    };
    
    const status = statusConfig[inspection.inspection_status] || { class: 'clean-badge-secondary', icon: 'fas fa-question' };
    
    return `
        <tr>
            <td>${index + 1}</td>
            <td>
                <strong>${inspection.inspection_id}</strong><br>
                <small class="text-muted">Batch: ${inspection.batch_number}</small>
            </td>
            <td>
                <div class="clean-info-section">
                    <div class="clean-info-label">Product</div>
                    <div class="clean-info-value">${inspection.product_name}</div>
                </div>
            </td>
            <td>
                <i class="fas fa-user"></i> ${inspection.inspector_name}<br>
                <small class="text-muted">${inspection.inspector_id}</small>
            </td>
            <td>
                <i class="fas fa-calendar"></i> ${formatInspectionDate(inspection.inspection_date)}<br>
                <small class="text-muted">${inspection.inspection_time}</small>
            </td>
            <td>
                <span class="clean-status-badge ${status.class}">
                    <i class="${status.icon}"></i>
                    ${inspection.inspection_status.toUpperCase()}
                </span>
            </td>
            <td>
                <div class="d-flex align-items-center">
                    <div class="progress me-2" style="width: 60px; height: 6px;">
                        <div class="progress-bar ${getScoreProgressClass(inspection.quality_score)}" 
                             style="width: ${inspection.quality_score}%"></div>
                    </div>
                    <strong>${inspection.quality_score}%</strong>
                </div>
            </td>
            <td class="text-center">
                <div class="btn-group" role="group">
                    <button class="btn clean-btn clean-btn-accent btn-sm" 
                            onclick="viewInspectionDetail('${inspection.inspection_id}')" 
                            data-bs-toggle="modal" data-bs-target="#inspectionDetailModal"
                            data-bs-toggle="tooltip" title="View Details">
                        <i class="fas fa-eye"></i>
                    </button>
                    <button class="btn clean-btn clean-btn-secondary btn-sm" 
                            onclick="editInspection('${inspection.inspection_id}')"
                            data-bs-toggle="tooltip" title="Edit Inspection">
                        <i class="fas fa-edit"></i>
                    </button>
                    <button class="btn clean-btn clean-btn-outline btn-sm" 
                            onclick="printInspectionReport('${inspection.inspection_id}')"
                            data-bs-toggle="tooltip" title="Print Report">
                        <i class="fas fa-print"></i>
                    </button>
                </div>
            </td>
        </tr>
    `;
}

// =================
// UTILITY FUNCTIONS
// =================
function formatInspectionDate(dateStr) {
    const date = new Date(dateStr);
    return date.toLocaleDateString('id-ID', {
        year: 'numeric',
        month: 'short',
        day: 'numeric'
    });
}

function getScoreProgressClass(score) {
    if (score >= 90) return 'bg-success';
    if (score >= 70) return 'bg-warning';
    return 'bg-danger';
}

function updateSummaryCards() {
    if (currentInspections.length === 0) return;
    
    const stats = {
        total: currentInspections.length,
        pending: currentInspections.filter(i => i.inspection_status === 'pending').length,
        passed: currentInspections.filter(i => i.inspection_status === 'passed').length,
        failed: currentInspections.filter(i => i.inspection_status === 'failed').length
    };
    
    // Update summary cards (this would need specific elements in HTML)
    console.log('Inspection Statistics:', stats);
}

// =================
// STATE MANAGEMENT
// =================
function showLoadingState() {
    document.getElementById('loadingState').classList.remove('d-none');
    document.getElementById('noDataState').classList.add('d-none');
    document.getElementById('dataTable').classList.add('d-none');
}

function showNoDataState() {
    document.getElementById('loadingState').classList.add('d-none');
    document.getElementById('noDataState').classList.remove('d-none');
    document.getElementById('dataTable').classList.add('d-none');
    document.getElementById('dataCount').textContent = '0 inspections found';
}

function showDataTableState() {
    document.getElementById('loadingState').classList.add('d-none');
    document.getElementById('noDataState').classList.add('d-none');
    document.getElementById('dataTable').classList.remove('d-none');
}

function showErrorState(message) {
    const container = document.getElementById('dataContainer');
    container.innerHTML = `
        <div class="clean-no-data">
            <i class="fas fa-exclamation-triangle fa-3x text-danger mb-3"></i>
            <h5 class="text-danger">Error</h5>
            <p class="text-muted mb-0">${message}</p>
            <button class="btn clean-btn clean-btn-primary mt-3" onclick="loadInspections()">
                <i class="fas fa-refresh"></i> Retry
            </button>
        </div>
    `;
}

// =================
// INSPECTION ACTIONS
// =================
async function viewInspectionDetail(inspectionId) {
    console.log('View inspection detail:', inspectionId);
    selectedInspectionId = inspectionId;
    
    try {
        const response = await fetch(`${QCConfig.apiEndpoints.inspectionDetail}/${inspectionId}`);
        const data = await response.json();
        
        if (data.success && data.inspection) {
            displayInspectionDetail(data.inspection);
        } else {
            showAlert('error', 'Failed to load inspection details');
        }
    } catch (error) {
        console.error('Error loading inspection detail:', error);
        showAlert('error', 'Error loading inspection details');
    }
}

function displayInspectionDetail(inspection) {
    const content = document.getElementById('inspectionDetailContent');
    content.innerHTML = `
        <div class="row">
            <div class="col-md-6 mb-3">
                <div class="clean-info-section">
                    <div class="clean-info-label">Inspection ID</div>
                    <div class="clean-info-value">${inspection.inspection_id}</div>
                </div>
            </div>
            <div class="col-md-6 mb-3">
                <div class="clean-info-section">
                    <div class="clean-info-label">Product</div>
                    <div class="clean-info-value">${inspection.product_name}</div>
                </div>
            </div>
            <div class="col-md-6 mb-3">
                <div class="clean-info-section">
                    <div class="clean-info-label">Inspector</div>
                    <div class="clean-info-value">${inspection.inspector_name}</div>
                </div>
            </div>
            <div class="col-md-6 mb-3">
                <div class="clean-info-section">
                    <div class="clean-info-label">Quality Score</div>
                    <div class="clean-info-value">
                        <div class="d-flex align-items-center">
                            <div class="progress me-2" style="width: 100px; height: 8px;">
                                <div class="progress-bar ${getScoreProgressClass(inspection.quality_score)}" 
                                     style="width: ${inspection.quality_score}%"></div>
                            </div>
                            <strong>${inspection.quality_score}%</strong>
                        </div>
                    </div>
                </div>
            </div>
            <div class="col-md-6 mb-3">
                <div class="clean-info-section">
                    <div class="clean-info-label">Status</div>
                    <div class="clean-info-value">
                        <span class="clean-status-badge clean-badge-primary">
                            ${inspection.inspection_status.toUpperCase()}
                        </span>
                    </div>
                </div>
            </div>
            <div class="col-md-6 mb-3">
                <div class="clean-info-section">
                    <div class="clean-info-label">Date</div>
                    <div class="clean-info-value">${formatInspectionDate(inspection.inspection_date || new Date())}</div>
                </div>
            </div>
            <div class="col-md-12 mb-3">
                <div class="clean-info-section">
                    <div class="clean-info-label">Notes</div>
                    <div class="clean-info-value">${inspection.notes || 'No notes available'}</div>
                </div>
            </div>
        </div>
    `;
}

function editInspection(inspectionId) {
    console.log('Edit inspection:', inspectionId);
    // Implement edit functionality
    showAlert('info', 'Edit functionality will be implemented here');
}

function printInspectionReport(inspectionId) {
    console.log('Print inspection report:', inspectionId);
    window.open(`/print-inspection-report/${inspectionId}`, '_blank');
}

// =================
// FORM HANDLING
// =================
function setupFormValidation() {
    const form = document.getElementById('newInspectionForm');
    if (form) {
        form.addEventListener('submit', function(e) {
            e.preventDefault();
            saveNewInspection();
        });
    }
}

async function saveNewInspection() {
    const form = document.getElementById('newInspectionForm');
    if (!form) return;
    
    // Validate form
    if (!form.checkValidity()) {
        form.classList.add('was-validated');
        return;
    }
    
    const formData = new FormData(form);
    const data = Object.fromEntries(formData.entries());
    
    try {
        // Show loading
        const saveButton = document.querySelector('#newInspectionModal .modal-footer .clean-btn-primary');
        const originalText = saveButton.innerHTML;
        saveButton.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Saving...';
        saveButton.disabled = true;
        
        const response = await fetch(QCConfig.apiEndpoints.newInspection, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(data)
        });
        
        const result = await response.json();
        
        if (result.success) {
            // Close modal and refresh data
            const modal = bootstrap.Modal.getInstance(document.getElementById('newInspectionModal'));
            modal.hide();
            
            await loadInspections();
            showAlert('success', `New inspection ${result.inspection_id} created successfully!`);
        } else {
            showAlert('error', result.message || 'Failed to create inspection');
        }
        
        // Restore button
        saveButton.innerHTML = originalText;
        saveButton.disabled = false;
        
    } catch (error) {
        console.error('Error creating inspection:', error);
        showAlert('error', 'An error occurred while creating inspection');
        
        // Restore button
        const saveButton = document.querySelector('#newInspectionModal .modal-footer .clean-btn-primary');
        saveButton.innerHTML = '<i class="fas fa-save"></i> Save';
        saveButton.disabled = false;
    }
}

function resetNewInspectionForm() {
    const form = document.getElementById('newInspectionForm');
    if (form) {
        form.reset();
        form.classList.remove('was-validated');
    }
}

// =================
// ADDITIONAL FEATURES
// =================
function generateQCReport() {
    console.log('Generate QC Report');
    showAlert('info', 'Generating quality control report...');
    
    // Simulate report generation
    setTimeout(() => {
        window.open('/generate-qc-report', '_blank');
    }, 1000);
}

function exportQCData() {
    console.log('Export QC Data');
    showAlert('info', 'Preparing data export...');
    
    // Simulate export preparation
    setTimeout(() => {
        const csvData = convertToCSV(filteredInspections);
        downloadCSV(csvData, 'quality_control_data.csv');
    }, 1000);
}

function convertToCSV(data) {
    if (data.length === 0) return '';
    
    const headers = Object.keys(data[0]);
    const csvContent = [
        headers.join(','),
        ...data.map(row => headers.map(header => `"${row[header]}"`).join(','))
    ].join('\n');
    
    return csvContent;
}

function downloadCSV(csvContent, filename) {
    const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
    const link = document.createElement('a');
    
    if (link.download !== undefined) {
        const url = URL.createObjectURL(blob);
        link.setAttribute('href', url);
        link.setAttribute('download', filename);
        link.style.visibility = 'hidden';
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
    }
}

// =================
// DATE PICKER INITIALIZATION
// =================
function initializeDatePickers() {
    // Set default date range (last 30 days)
    const endDate = new Date();
    const startDate = new Date();
    startDate.setDate(startDate.getDate() - 30);
    
    const startDateInput = document.getElementById('startDate');
    const endDateInput = document.getElementById('endDate');
    
    if (startDateInput) {
        startDateInput.value = startDate.toISOString().split('T')[0];
    }
    
    if (endDateInput) {
        endDateInput.value = endDate.toISOString().split('T')[0];
    }
}

// =================
// ALERT SYSTEM
// =================
function showAlert(type, message, duration = 5000) {
    const alertClass = {
        'success': 'alert-success',
        'error': 'alert-danger',
        'warning': 'alert-warning',
        'info': 'alert-info'
    };
    
    const alertIcon = {
        'success': 'fas fa-check-circle',
        'error': 'fas fa-exclamation-circle',
        'warning': 'fas fa-exclamation-triangle',
        'info': 'fas fa-info-circle'
    };
    
    const alertHTML = `
        <div class="alert ${alertClass[type] || 'alert-info'} alert-dismissible fade show position-fixed" 
             style="top: 20px; right: 20px; z-index: 9999; min-width: 300px;" role="alert">
            <i class="${alertIcon[type] || 'fas fa-info-circle'} me-2"></i>
            ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        </div>
    `;
    
    document.body.insertAdjacentHTML('beforeend', alertHTML);
    
    // Auto remove after specified duration
    setTimeout(() => {
        const alerts = document.querySelectorAll('.alert');
        if (alerts.length > 0) {
            const lastAlert = alerts[alerts.length - 1];
            const bsAlert = new bootstrap.Alert(lastAlert);
            bsAlert.close();
        }
    }, duration);
}

// =================
// EXPORT FUNCTIONS
// =================
window.QualityControlModule = {
    loadInspections,
    applyInspectionFilters,
    resetInspectionFilters,
    viewInspectionDetail,
    editInspection,
    printInspectionReport,
    saveNewInspection,
    generateQCReport,
    exportQCData,
    showAlert
};
