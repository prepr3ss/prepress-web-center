// ENHANCEMENT: Mounting Data Adjustment - Additional Features
// Add this to the existing mounting_data_adjustment.html file

// 1. Auto-refresh Toggle
function setupAutoRefreshToggle() {
    const autoRefreshHtml = `
        <div class="col-md-4 text-end">
            <div class="d-flex align-items-center justify-content-end gap-3">
                <div class="form-check form-switch">
                    <input class="form-check-input" type="checkbox" id="autoRefresh" checked>
                    <label class="form-check-label small text-muted" for="autoRefresh">
                        <i class="fas fa-sync-alt me-1"></i>Auto Refresh (30s)
                    </label>
                </div>
                <button class="btn btn-outline-clean btn-clean" id="refreshData">
                    <i class="fas fa-refresh me-2"></i>Refresh Data
                </button>
            </div>
        </div>
    `;
    
    // Replace existing refresh button section
    document.querySelector('.filter-section .col-md-4.text-end').innerHTML = autoRefreshHtml;
    
    // Setup auto-refresh functionality
    let autoRefreshInterval;
    const autoRefreshCheckbox = document.getElementById('autoRefresh');
    
    function startAutoRefresh() {
        if (autoRefreshInterval) clearInterval(autoRefreshInterval);
        autoRefreshInterval = setInterval(loadData, 30000); // 30 seconds
    }
    
    function stopAutoRefresh() {
        if (autoRefreshInterval) {
            clearInterval(autoRefreshInterval);
            autoRefreshInterval = null;
        }
    }
    
    autoRefreshCheckbox.addEventListener('change', function() {
        if (this.checked) {
            startAutoRefresh();
        } else {
            stopAutoRefresh();
        }
    });
    
    // Start auto-refresh by default
    startAutoRefresh();
}

// 2. Export to Excel Functionality
function setupExportFunctionality() {
    // Add export button to filter section
    const exportButton = `
        <button class="btn btn-success-clean btn-clean me-2" onclick="exportMountingData()">
            <i class="fas fa-download me-1"></i>Export Excel
        </button>
    `;
    
    document.querySelector('.filter-section .col-md-4.text-end .d-flex').insertAdjacentHTML('afterbegin', exportButton);
}

function exportMountingData() {
    const data = adjustmentData.map(item => ({
        'Mesin Cetak': item.mesin_cetak,
        'WO Number': item.wo_number,
        'MC Number': item.mc_number,
        'Item Name': item.item_name,
        'Jumlah Plate': item.jumlah_plate,
        'Run Length': item.run_length,
        'Status': item.status,
        'Machine Off': formatDateTimeIndonesia(item.machine_off_at),
        'Mulai Adjustment': formatDateTimeIndonesia(item.adjustment_start_at),
        'Selesai Adjustment': formatDateTimeIndonesia(item.adjustment_finish_at),
        'PIC Adjustment': item.adjustment_by || '-',
        'Remarks': item.remarks || '-'
    }));
    
    // Convert to CSV
    const csvContent = convertToCSV(data);
    downloadCSV(csvContent, `mounting_adjustment_${new Date().toISOString().split('T')[0]}.csv`);
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

// 3. Toast Notification System
function showToast(type, message, duration = 5000) {
    // Remove existing toasts
    const existingToasts = document.querySelectorAll('.toast-container');
    existingToasts.forEach(toast => toast.remove());
    
    const toastIcons = {
        success: 'check-circle',
        error: 'exclamation-circle',
        warning: 'exclamation-triangle',
        info: 'info-circle'
    };
    
    const toastColors = {
        success: 'text-success',
        error: 'text-danger',
        warning: 'text-warning',
        info: 'text-primary'
    };
    
    const toastHtml = `
        <div class="toast-container position-fixed top-0 end-0 p-3" style="z-index: 9999;">
            <div class="toast show" role="alert" aria-live="assertive" aria-atomic="true">
                <div class="toast-header">
                    <i class="fas fa-${toastIcons[type]} ${toastColors[type]} me-2"></i>
                    <strong class="me-auto">Mounting Adjustment</strong>
                    <small class="text-muted">Just now</small>
                    <button type="button" class="btn-close" data-bs-dismiss="toast" aria-label="Close"></button>
                </div>
                <div class="toast-body">${message}</div>
            </div>
        </div>
    `;
    
    document.body.insertAdjacentHTML('beforeend', toastHtml);
    
    // Auto remove after duration
    setTimeout(() => {
        const toastElement = document.querySelector('.toast-container');
        if (toastElement) {
            toastElement.remove();
        }
    }, duration);
}

// 4. Enhanced Error Handling with Retry
async function loadDataWithRetry(retries = 3) {
    for (let attempt = 1; attempt <= retries; attempt++) {
        try {
            await loadData();
            return;
        } catch (error) {
            console.error(`Load attempt ${attempt} failed:`, error);
            
            if (attempt === retries) {
                showToast('error', `Gagal memuat data setelah ${retries} percobaan. Silakan refresh halaman.`);
                throw error;
            }
            
            // Show retry notification
            showToast('warning', `Percobaan ${attempt} gagal. Mencoba lagi...`, 2000);
            
            // Wait before retry (exponential backoff)
            await new Promise(resolve => setTimeout(resolve, 1000 * attempt));
        }
    }
}

// 5. Keyboard Shortcuts
function setupKeyboardShortcuts() {
    document.addEventListener('keydown', function(e) {
        // Ctrl + R: Refresh data
        if (e.ctrlKey && e.key === 'r') {
            e.preventDefault();
            loadData();
            showToast('info', 'Data sedang dimuat ulang...');
        }
        
        // Ctrl + E: Export data
        if (e.ctrlKey && e.key === 'e') {
            e.preventDefault();
            exportMountingData();
            showToast('success', 'Data sedang diekspor...');
        }
        
        // Escape: Close modals
        if (e.key === 'Escape') {
            const openModals = document.querySelectorAll('.modal.show');
            openModals.forEach(modal => {
                const modalInstance = bootstrap.Modal.getInstance(modal);
                if (modalInstance) modalInstance.hide();
            });
        }
    });
    
    // Show keyboard shortcuts info
    console.log(`
    ⌨️  Keyboard Shortcuts:
    Ctrl + R: Refresh data
    Ctrl + E: Export data
    Escape: Close modals
    `);
}

// 6. Performance Monitoring
function setupPerformanceMonitoring() {
    const originalLoadData = loadData;
    
    window.loadData = async function() {
        const startTime = performance.now();
        
        try {
            await originalLoadData();
            const loadTime = performance.now() - startTime;
            console.log(`✅ Data loaded in ${Math.round(loadTime)}ms`);
            
            if (loadTime > 2000) {
                showToast('warning', 'Data membutuhkan waktu lama untuk dimuat. Periksa koneksi internet.');
            }
        } catch (error) {
            const loadTime = performance.now() - startTime;
            console.error(`❌ Data load failed after ${Math.round(loadTime)}ms:`, error);
            throw error;
        }
    };
}

// 7. Date Range Filter
function setupDateRangeFilter() {
    const dateFilterHtml = `
        <div class="col-md-3">
            <label class="form-label info-label">Filter Tanggal</label>
            <input type="date" class="form-control form-control-clean" id="dateFilter" 
                   title="Filter berdasarkan tanggal machine off">
        </div>
    `;
    
    // Add to filter section
    document.querySelector('.filter-section .row.g-3').insertAdjacentHTML('beforeend', dateFilterHtml);
    
    // Add date filter functionality
    document.getElementById('dateFilter').addEventListener('change', function() {
        applyFilters();
    });
}

// Enhanced applyFilters function with date filter
function applyFiltersEnhanced() {
    const statusFilter = document.getElementById('statusFilter').value;
    const mesinFilter = document.getElementById('mesinFilter').value;
    const dateFilter = document.getElementById('dateFilter')?.value;
    
    let filteredData = adjustmentData;
    
    if (statusFilter) {
        filteredData = filteredData.filter(item => item.status === statusFilter);
    }
    
    if (mesinFilter) {
        filteredData = filteredData.filter(item => item.mesin_cetak === mesinFilter);
    }
    
    if (dateFilter) {
        filteredData = filteredData.filter(item => {
            if (!item.machine_off_at) return false;
            const itemDate = new Date(item.machine_off_at).toISOString().split('T')[0];
            return itemDate === dateFilter;
        });
    }
    
    displayData(filteredData);
    
    // Show filter result
    const totalFiltered = filteredData.length;
    const totalOriginal = adjustmentData.length;
    
    if (totalFiltered !== totalOriginal) {
        showToast('info', `Menampilkan ${totalFiltered} dari ${totalOriginal} data`, 3000);
    }
}

// 8. Initialize All Enhancements
function initializeEnhancements() {
    // Wait for DOM to be ready
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', initializeEnhancements);
        return;
    }
    
    console.log('🚀 Initializing Mounting Data Adjustment Enhancements...');
    
    setupAutoRefreshToggle();
    setupExportFunctionality();
    setupKeyboardShortcuts();
    setupPerformanceMonitoring();
    setupDateRangeFilter();
    
    // Replace original applyFilters with enhanced version
    window.applyFilters = applyFiltersEnhanced;
    
    // Replace original loadData with retry version
    window.loadData = loadDataWithRetry;
    
    // Enhanced confirmation messages
    window.originalStartAdjustment = startAdjustment;
    window.startAdjustment = function(id) {
        originalStartAdjustment(id);
        showToast('info', 'Menyiapkan proses adjustment...');
    };
    
    window.originalFinishAdjustment = finishAdjustment;
    window.finishAdjustment = function(id) {
        originalFinishAdjustment(id);
        showToast('info', 'Menyelesaikan proses adjustment...');
    };
    
    console.log('✅ All enhancements initialized successfully!');
    showToast('success', 'Mounting Data Adjustment Enhanced Version Ready!', 3000);
}

// Auto-initialize when script loads
initializeEnhancements();
