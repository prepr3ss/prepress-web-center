/**
 * Reusable Export Service for CTP Log Data
 * Provides PDF and Excel export functionality with robust error handling
 */
class ExportService {
    constructor() {
        this.isExporting = false;
        this.maxRetries = 3;
        this.retryDelay = 1000;
    }

    /**
     * Show export modal with current filter options
     * @param {string} machineNickname - Current machine nickname
     * @param {Object} currentFilters - Current filter values
     */
    showExportModal(machineNickname, currentFilters = {}) {
        // Create modal if it doesn't exist
        if (!document.getElementById('exportModal')) {
            this.createExportModal();
        }

        // Set current filter values
        this.populateCurrentFilters(currentFilters);
        
        // Set machine name
        document.getElementById('exportMachineName').textContent = machineNickname;
        
        // Show modal
        const modal = new bootstrap.Modal(document.getElementById('exportModal'));
        modal.show();
    }

    /**
     * Create export modal HTML
     */
    createExportModal() {
        const modalHtml = `
            <div class="modal fade" id="exportModal" tabindex="-1">
                <div class="modal-dialog modal-dialog-centered">
                    <div class="modal-content">
                        <div class="modal-header">
                            <h5 class="modal-title">
                                <i class="fas fa-download me-2"></i>
                                Export Data Log CTP
                            </h5>
                            <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
                        </div>
                        <div class="modal-body">
                            <div class="mb-3">
                                <div class="alert alert-info">
                                    <i class="fas fa-info-circle me-2"></i>
                                    <strong>Mesin:</strong> <span id="exportMachineName"></span><br>
                                    Export akan menggunakan filter yang sedang aktif pada halaman ini.
                                </div>
                            </div>
                            
                            <div class="mb-3">
                                <label class="form-label">Format Export</label>
                                <div class="btn-group w-100" role="group">
                                    <input type="radio" class="btn-check" name="exportFormat" id="exportExcel" value="excel" checked>
                                    <label class="btn btn-outline-success" for="exportExcel">
                                        <i class="fas fa-file-excel me-2"></i>Excel
                                    </label>
                                    
                                    <input type="radio" class="btn-check" name="exportFormat" id="exportPDF" value="pdf">
                                    <label class="btn btn-outline-danger" for="exportPDF">
                                        <i class="fas fa-file-pdf me-2"></i>PDF
                                    </label>
                                </div>
                            </div>

                            <div class="row">
                                <div class="col-md-6">
                                    <label class="form-label">Filter Tahun</label>
                                    <select class="form-select" id="exportYearFilter">
                                        <option value="">Semua Tahun</option>
                                    </select>
                                </div>
                                <div class="col-md-6">
                                    <label class="form-label">Filter Bulan</label>
                                    <select class="form-select" id="exportMonthFilter">
                                        <option value="">Semua Bulan</option>
                                    </select>
                                </div>
                            </div>

                            <div class="row mt-3">
                                <div class="col-md-6">
                                    <label class="form-label">Filter Vendor</label>
                                    <select class="form-select" id="exportVendorFilter">
                                        <option value="">Semua Vendor</option>
                                        <option value="lokal">Lokal</option>
                                        <option value="vendor">Vendor</option>
                                        <option value="none">Tidak memanggil teknisi</option>
                                    </select>
                                </div>
                                <div class="col-md-6">
                                    <label class="form-label">Filter Status</label>
                                    <select class="form-select" id="exportStatusFilter">
                                        <option value="">Semua Status</option>
                                        <option value="ongoing">Sedang Berjalan</option>
                                        <option value="completed">Selesai</option>
                                    </select>
                                </div>
                            </div>

                            <div class="mt-3">
                                <label class="form-label">Pencarian</label>
                                <input type="text" class="form-control" id="exportSearchFilter" placeholder="Cari problem, teknisi, atau solusi...">
                            </div>
                        </div>
                        <div class="modal-footer">
                            <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">
                                <i class="fas fa-times me-1"></i>Batal
                            </button>
                            <button type="button" class="btn btn-primary" id="confirmExportBtn">
                                <i class="fas fa-download me-1"></i>Export
                            </button>
                        </div>
                    </div>
                </div>
            </div>
        `;
        
        document.body.insertAdjacentHTML('beforeend', modalHtml);
        
        // Add event listener for export button
        document.getElementById('confirmExportBtn').addEventListener('click', () => {
            // Get machine nickname from the modal that was set when modal was shown
            const machineNameElement = document.getElementById('exportMachineName');
            const machineNickname = machineNameElement ? machineNameElement.textContent : '';
            this.handleExport(machineNickname);
        });
    }

    /**
     * Populate current filter values
     * @param {Object} currentFilters - Current filter values
     */
    populateCurrentFilters(currentFilters) {
        if (currentFilters.year) {
            document.getElementById('exportYearFilter').value = currentFilters.year;
        }
        if (currentFilters.month) {
            document.getElementById('exportMonthFilter').value = currentFilters.month;
        }
        if (currentFilters.vendor) {
            document.getElementById('exportVendorFilter').value = currentFilters.vendor;
        }
        if (currentFilters.status) {
            document.getElementById('exportStatusFilter').value = currentFilters.status;
        }
        if (currentFilters.search) {
            document.getElementById('exportSearchFilter').value = currentFilters.search;
        }
        
        // Populate year and month options from current page filters
        this.populateYearOptions();
        this.populateMonthOptions();
    }

    /**
     * Populate year options from main filter
     */
    populateYearOptions() {
        const mainYearFilter = document.getElementById('filterYear');
        const exportYearFilter = document.getElementById('exportYearFilter');
        
        if (mainYearFilter && exportYearFilter) {
            // Copy options from main filter
            exportYearFilter.innerHTML = mainYearFilter.innerHTML;
            // Set same selected value
            exportYearFilter.value = mainYearFilter.value;
        }
    }

    /**
     * Populate month options from main filter
     */
    populateMonthOptions() {
        const mainMonthFilter = document.getElementById('filterMonth');
        const exportMonthFilter = document.getElementById('exportMonthFilter');
        
        if (mainMonthFilter && exportMonthFilter) {
            // Copy options from main filter
            exportMonthFilter.innerHTML = mainMonthFilter.innerHTML;
            // Set same selected value
            exportMonthFilter.value = mainMonthFilter.value;
        }
    }

    /**
     * Handle export process
     * @param {string} machineNickname - Machine nickname
     */
    async handleExport(machineNickname) {
        if (this.isExporting) {
            this.showToast('Export sedang berlangsung, harap tunggu...', 'warning');
            return;
        }

        const format = document.querySelector('input[name="exportFormat"]:checked').value;
        const filters = {
            machine_nickname: machineNickname,
            year: document.getElementById('exportYearFilter').value,
            month: document.getElementById('exportMonthFilter').value,
            technician_type: document.getElementById('exportVendorFilter').value,
            status: document.getElementById('exportStatusFilter').value,
            search: document.getElementById('exportSearchFilter').value.trim()
        };

        try {
            this.isExporting = true;
            this.showExportLoading(true);
            
            // Close modal
            bootstrap.Modal.getInstance(document.getElementById('exportModal')).hide();
            
            await this.performExport(format, filters);
            
        } catch (error) {
            console.error('Export error:', error);
            this.handleExportError(error);
        } finally {
            this.isExporting = false;
            this.showExportLoading(false);
        }
    }

    /**
     * Perform export with retry logic
     * @param {string} format - Export format (excel/pdf)
     * @param {Object} filters - Filter parameters
     */
    async performExport(format, filters) {
        let lastError;
        
        for (let attempt = 1; attempt <= this.maxRetries; attempt++) {
            try {
                const response = await this.exportRequest(format, filters);
                
                if (!response.ok) {
                    throw new Error(`HTTP ${response.status}: ${response.statusText}`);
                }
                
                // Handle successful response
                await this.handleExportResponse(response, format);
                return; // Success, exit retry loop
                
            } catch (error) {
                lastError = error;
                console.warn(`Export attempt ${attempt} failed:`, error);
                
                if (attempt < this.maxRetries) {
                    await this.delay(this.retryDelay * attempt);
                    this.showToast(`Export gagal, mencoba lagi... (${attempt}/${this.maxRetries})`, 'warning');
                }
            }
        }
        
        // All retries failed
        throw lastError;
    }

    /**
     * Make export request
     * @param {string} format - Export format
     * @param {Object} filters - Filter parameters
     */
    async exportRequest(format, filters) {
        const params = new URLSearchParams();
        
        Object.entries(filters).forEach(([key, value]) => {
            if (value) params.append(key, value);
        });
        params.append('format', format);
        
        return fetch(`/impact/export-ctp-logs?${params.toString()}`, {
            method: 'GET',
            headers: {
                'X-Requested-With': 'XMLHttpRequest'
            }
        });
    }

    /**
     * Handle successful export response
     * @param {Response} response - Fetch response
     * @param {string} format - Export format
     */
    async handleExportResponse(response, format) {
        const contentType = response.headers.get('Content-Type');
        const contentDisposition = response.headers.get('Content-Disposition');
        
        // Extract filename from Content-Disposition header
        let filename = `ctp_log_export_${new Date().toISOString().split('T')[0]}`;
        if (contentDisposition) {
            const filenameMatch = contentDisposition.match(/filename[^;=\n]*=((['"]).*?\2|[^;\n]*)/);
            if (filenameMatch && filenameMatch[1]) {
                filename = filenameMatch[1].replace(/['"]/g, '');
            }
        }
        
        // Add appropriate extension
        if (!filename.includes('.')) {
            filename += format === 'excel' ? '.xlsx' : '.pdf';
        }
        
        // Convert response to blob
        const blob = await response.blob();
        
        // Create download link
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = filename;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        window.URL.revokeObjectURL(url);
        
        this.showToast(`Export ${format.toUpperCase()} berhasil! File "${filename}" telah diunduh.`, 'success');
    }

    /**
     * Handle export errors
     * @param {Error} error - Error object
     */
    handleExportError(error) {
        let message = 'Export gagal. ';
        
        if (error.message.includes('HTTP 401')) {
            message += 'Sesi Anda telah berakhir. Silakan login kembali.';
        } else if (error.message.includes('HTTP 403')) {
            message += 'Anda tidak memiliki izin untuk export data ini.';
        } else if (error.message.includes('HTTP 404')) {
            message += 'Data tidak ditemukan.';
        } else if (error.message.includes('HTTP 500')) {
            message += 'Terjadi kesalahan pada server. Silakan coba lagi nanti.';
        } else if (error.message.includes('timeout')) {
            message += 'Request timeout. Data terlalu besar atau koneksi lambat.';
        } else if (error.message.includes('Failed to fetch')) {
            message += 'Tidak dapat terhubung ke server. Periksa koneksi internet.';
        } else {
            message += `Kesalahan: ${error.message}`;
        }
        
        this.showToast(message, 'danger');
    }

    /**
     * Show/hide export loading indicator
     * @param {boolean} show - Show or hide loading
     */
    showExportLoading(show) {
        let loadingOverlay = document.getElementById('exportLoadingOverlay');
        
        if (show) {
            if (!loadingOverlay) {
                loadingOverlay = document.createElement('div');
                loadingOverlay.id = 'exportLoadingOverlay';
                loadingOverlay.className = 'export-loading-overlay';
                loadingOverlay.innerHTML = `
                    <div class="export-loading-content">
                        <div class="spinner-border text-primary" role="status">
                            <span class="visually-hidden">Loading...</span>
                        </div>
                        <div class="mt-2">Sedang menyiapkan data export...</div>
                    </div>
                `;
                document.body.appendChild(loadingOverlay);
            }
        } else {
            if (loadingOverlay) {
                loadingOverlay.remove();
            }
        }
    }

    /**
     * Show toast notification
     * @param {string} message - Toast message
     * @param {string} type - Toast type (success, warning, danger, info)
     */
    showToast(message, type = 'info') {
        const toastContainer = document.querySelector('.toast-container') || this.createToastContainer();
        const toast = document.createElement('div');
        toast.className = `toast align-items-center text-white bg-${type === 'error' ? 'danger' : type} border-0`;
        toast.setAttribute('role', 'alert');
        toast.setAttribute('aria-live', 'assertive');
        toast.setAttribute('aria-atomic', 'true');

        toast.innerHTML = `
            <div class="d-flex">
                <div class="toast-body">
                    ${message}
                </div>
                <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast" aria-label="Close"></button>
            </div>
        `;

        toastContainer.appendChild(toast);
        const bsToast = new bootstrap.Toast(toast);
        bsToast.show();

        // Remove toast after it's hidden
        toast.addEventListener('hidden.bs.toast', () => {
            toast.remove();
        });
    }

    /**
     * Create toast container if it doesn't exist
     */
    createToastContainer() {
        const container = document.createElement('div');
        container.className = 'toast-container position-fixed bottom-0 end-0 p-3';
        document.body.appendChild(container);
        return container;
    }

    /**
     * Utility function for delay
     * @param {number} ms - Milliseconds to delay
     */
    delay(ms) {
        return new Promise(resolve => setTimeout(resolve, ms));
    }
}

// Create global export service instance
window.exportService = new ExportService();