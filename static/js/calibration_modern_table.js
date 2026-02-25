// Calibration References Modern Table JavaScript
class CalibrationModernTable {
    constructor(standard = 'G7') {
        // Jika standard kosong atau null, default ke G7
        this.standard = (standard && standard.trim() !== "") ? standard.toUpperCase() : 'G7';
        
        console.log('CalibrationModernTable initialized with standard:', this.standard);
        
        this.data = [];
        this.filteredData = [];
        this.currentPage = 1;
        this.itemsPerPage = 10;
        this.filters = {
            search: '',
            machine: '',
            paper: '',
            ink: '',
            sortBy: 'updated_at',
            standard: this.standard
        };
        
        this.init();
    }

    init() {
        this.loadData();
        this.loadFilterOptions();
        this.setupEventListeners();
    }

    setupEventListeners() {
        // Search input debounce
        let searchTimeout;
        const searchInput = document.getElementById('searchInput');
        if (searchInput) {
            searchInput.addEventListener('input', (e) => {
                clearTimeout(searchTimeout);
                searchTimeout = setTimeout(() => {
                    this.filters.search = e.target.value;
                    this.applyFilters();
                }, 500);
            });
        }

        // Machine filter
        const machineFilter = document.getElementById('machineFilter');
        if (machineFilter) {
            machineFilter.addEventListener('change', (e) => {
                this.filters.machine = e.target.value;
                this.applyFilters();
            });
        }

        // Paper filter
        const paperFilter = document.getElementById('paperFilter');
        if (paperFilter) {
            paperFilter.addEventListener('change', (e) => {
                this.filters.paper = e.target.value;
                this.applyFilters();
            });
        }

        // Ink filter
        const inkFilter = document.getElementById('inkFilter');
        if (inkFilter) {
            inkFilter.addEventListener('change', (e) => {
                this.filters.ink = e.target.value;
                this.applyFilters();
            });
        }

        // Sort filter
        const sortBy = document.getElementById('sortBy');
        if (sortBy) {
            sortBy.addEventListener('change', (e) => {
                this.filters.sortBy = e.target.value;
                this.applyFilters();
            });
        }

        // Clear search button
        const clearSearch = document.getElementById('clearSearch');
        if (clearSearch) {
            clearSearch.addEventListener('click', () => {
                const searchInput = document.getElementById('searchInput');
                if (searchInput) searchInput.value = '';
                this.filters.search = '';
                this.applyFilters();
            });
        }
    }

    async loadData() {
        try {
            this.showLoading(true);
            const apiUrl = `/impact/calibration-references/api/data?all=true&standard=${this.standard}`;
            const response = await fetch(apiUrl);
            if (!response.ok) throw new Error('Network response was not ok');
            const result = await response.json();
            
            if (result.data) {
                this.data = result.data;
                this.applyFilters();
            } else {
                this.showEmptyState();
            }
        } catch (error) {
            console.error('Error loading data:', error);
            this.showEmptyState();
        } finally {
            this.showLoading(false);
        }
    }

    async loadFilterOptions() {
        try {
            const response = await fetch('/impact/calibration-references/api/filter-options');
            const result = await response.json();
            if (result) {
                this.populatePaperFilter(result.paper_types);
                this.populateInkFilter(result.ink_types);
            }
        } catch (error) {
            console.error('Error loading filter options:', error);
        }
    }

    populatePaperFilter(paperTypes) {
        const paperFilter = document.getElementById('paperFilter');
        if (!paperFilter) return;
        paperFilter.innerHTML = '<option value="">All Paper Types</option>';
        if (paperTypes && paperTypes.length > 0) {
            paperTypes.sort().forEach(paper => {
                paperFilter.innerHTML += `<option value="${paper}">${paper}</option>`;
            });
        }
    }

    populateInkFilter(inkTypes) {
        const inkFilter = document.getElementById('inkFilter');
        if (!inkFilter) return;
        inkFilter.innerHTML = '<option value="">All Ink Types</option>';
        if (inkTypes && inkTypes.length > 0) {
            inkTypes.sort().forEach(ink => {
                inkFilter.innerHTML += `<option value="${ink}">${ink}</option>`;
            });
        }
    }

    applyFilters() {
        this.currentPage = 1;
        this.filteredData = [...this.data];
        
        if (this.filters.search) {
            const searchTerm = this.filters.search.toLowerCase();
            this.filteredData = this.filteredData.filter(item =>
                item.calib_code.toLowerCase().includes(searchTerm) ||
                item.calib_name.toLowerCase().includes(searchTerm) ||
                item.calib_group.toLowerCase().includes(searchTerm) ||
                item.print_machine.toLowerCase().includes(searchTerm) ||
                (item.paper_type && item.paper_type.toLowerCase().includes(searchTerm)) ||
                (item.ink_type && item.ink_type.toLowerCase().includes(searchTerm))
            );
        }
        
        if (this.filters.machine) {
            this.filteredData = this.filteredData.filter(item => item.print_machine === this.filters.machine);
        }
        if (this.filters.paper) {
            this.filteredData = this.filteredData.filter(item => item.paper_type === this.filters.paper);
        }
        if (this.filters.ink) {
            this.filteredData = this.filteredData.filter(item => item.ink_type === this.filters.ink);
        }
        
        this.filteredData.sort((a, b) => {
            switch (this.filters.sortBy) {
                case 'calib_code': return a.calib_code.localeCompare(b.calib_code);
                case 'calib_name': return a.calib_name.localeCompare(b.calib_name);
                case 'updated_at':
                default: return new Date(b.updated_at) - new Date(a.updated_at);
            }
        });
        
        this.renderTable();
        this.renderPagination();
    }

    renderTable() {
        const tableBody = document.getElementById('tableBody');
        if (!tableBody) return;

        if (this.filteredData.length === 0) {
            this.showEmptyState();
            return;
        }
        
        const startIndex = (this.currentPage - 1) * this.itemsPerPage;
        const pageData = this.filteredData.slice(startIndex, startIndex + this.itemsPerPage);
        
        tableBody.innerHTML = pageData.map((item, index) => this.createTableRow(item, index)).join('');
    }

    createTableRow(item, index) {
        const date = item.updated_at ? new Date(item.updated_at).toLocaleDateString('en-US', {
            year: 'numeric', month: 'short', day: 'numeric'
        }) : 'No date';
        
        const machineClass = item.print_machine.toLowerCase();
        const isActive = this.isRecentlyUpdated(item.updated_at);
        const standardBadge = this.getStandardBadge(item.calib_standard);
        
        return `
            <tr style="animation: fadeInUp 0.3s ease ${index * 0.05}s both">
                <td>
                    <span class="status-indicator ${isActive ? 'active' : 'inactive'}"></span>
                    <span class="machine-badge ${machineClass}">${item.print_machine}</span>
                </td>
                <td><span class="code-badge">${item.calib_code}</span></td>
                <td><strong>${item.calib_name}</strong></td>
                <td><span class="group-tag">${item.calib_group}</span></td>
                <td>${standardBadge}</td>
                <td><small class="text-muted">${date}</small></td>
                <td>
                    <div class="action-buttons">
                        <a href="/impact/calibration-references/${this.standard.toLowerCase()}/edit/${item.id}"
                           class="btn-action btn-action-edit" title="Edit">
                            <i class="fas fa-edit"></i>
                        </a>
                        <button type="button" class="btn-action btn-action-delete"
                                onclick="confirmDelete(${item.id}, '${item.calib_code}')" title="Delete">
                            <i class="fas fa-trash"></i>
                        </button>
                    </div>
                </td>
            </tr>
        `;
    }

    isRecentlyUpdated(updatedAt) {
        if (!updatedAt) return false;
        const updateDate = new Date(updatedAt);
        const sevenDaysAgo = new Date();
        sevenDaysAgo.setDate(sevenDaysAgo.getDate() - 7);
        return updateDate >= sevenDaysAgo;
    }

    getStandardBadge(standard) {
        if (!standard) return '<span class="standard-badge standard-default">-</span>';
        const std = standard.toLowerCase();
        const labels = { 'g7': 'standard-g7', 'iso': 'standard-iso', 'existing': 'standard-existing' };
        const cssClass = labels[std] || 'standard-default';
        return `<span class="standard-badge ${cssClass}">${standard.toUpperCase()}</span>`;
    }

    renderPagination() {
        const totalPages = Math.ceil(this.filteredData.length / this.itemsPerPage);
        const container = document.getElementById('paginationContainer');
        if (!container || totalPages <= 1) {
            if (container) container.innerHTML = '';
            return;
        }
        
        let html = `<li class="page-item ${this.currentPage === 1 ? 'disabled' : ''}">
            <a class="page-link" href="#" onclick="changePage(${this.currentPage - 1}); return false;"><i class="fas fa-chevron-left"></i></a>
        </li>`;

        for (let i = 1; i <= totalPages; i++) {
            if (totalPages > 5 && Math.abs(i - this.currentPage) > 2) continue;
            html += `<li class="page-item ${i === this.currentPage ? 'active' : ''}">
                <a class="page-link" href="#" onclick="changePage(${i}); return false;">${i}</a>
            </li>`;
        }

        html += `<li class="page-item ${this.currentPage === totalPages ? 'disabled' : ''}">
            <a class="page-link" href="#" onclick="changePage(${this.currentPage + 1}); return false;"><i class="fas fa-chevron-right"></i></a>
        </li>`;
        
        container.innerHTML = html;
    }

    changePage(page) {
        this.currentPage = page;
        this.renderTable();
        this.renderPagination();
        document.querySelector('.table-modern').scrollIntoView({ behavior: 'smooth', block: 'start' });
    }

    showLoading(show) {
        const overlay = document.getElementById('loadingOverlay');
        const body = document.getElementById('tableBody');
        if (overlay) overlay.classList.toggle('d-none', !show);
        if (body) body.style.opacity = show ? '0.5' : '1';
    }

    // --- EMPTY STATE VERSI LAMA (DENGAN IKON & BUTTON) ---
    showEmptyState() {
        const tableBody = document.getElementById('tableBody');
        if (tableBody) {
            tableBody.innerHTML = `
                <tr>
                    <td colspan="7" class="text-center py-5">
                        <div class="empty-state">
                            <i class="fas fa-inbox"></i>
                            <h5 class="mt-3">No Calibration References Found</h5>
                            <p>There are no calibration references matching your current filters for ${this.standard}.</p>
                            <button class="btn btn-outline-primary" onclick="clearFilters()">
                                Clear Filters
                            </button>
                        </div>
                    </td>
                </tr>
            `;
        }
        const paginationContainer = document.getElementById('paginationContainer');
        if (paginationContainer) paginationContainer.innerHTML = '';
    }

    showMessage(type, message) {
        const messageContainer = document.getElementById('dataMessage');
        if (!messageContainer) return;
        messageContainer.className = `alert alert-${type}`;
        messageContainer.textContent = message;
        messageContainer.classList.remove('d-none');
        setTimeout(() => messageContainer.classList.add('d-none'), 5000);
    }
}

// Global functions
function changePage(page) {
    if (window.calibrationModernTableInstance) window.calibrationModernTableInstance.changePage(page);
}

function clearFilters() {
    if (window.calibrationModernTableInstance) {
        const searchInput = document.getElementById('searchInput');
        const machineFilter = document.getElementById('machineFilter');
        const paperFilter = document.getElementById('paperFilter');
        const inkFilter = document.getElementById('inkFilter');

        if (searchInput) searchInput.value = '';
        if (machineFilter) machineFilter.value = '';
        if (paperFilter) paperFilter.value = '';
        if (inkFilter) inkFilter.value = '';
        
        window.calibrationModernTableInstance.filters = {
            search: '',
            machine: '',
            paper: '',
            ink: '',
            sortBy: 'updated_at',
            standard: window.calibrationModernTableInstance.standard
        };
        
        window.calibrationModernTableInstance.applyFilters();
    }
}

// Initialize when DOM is ready
document.addEventListener('DOMContentLoaded', function() {
    const wrapper = document.querySelector('[data-standard]');
    const standard = wrapper ? wrapper.dataset.standard : 'G7';

    if (!window.calibrationModernTableInstance) {
        window.calibrationModernTableInstance = new CalibrationModernTable(standard);
    }
});