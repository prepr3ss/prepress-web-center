// R&D Proof Checklist Dashboard JavaScript
class ProofChecklist {
    constructor() {
        this.filters = {
            status: '',
            date_filter: '',
            search: ''
        };
        this.checklists = [];
        this.currentPage = 1;
        this.totalPages = 1;
        this.init();
    }

    init() {
        this.loadChecklists();
        this.setupEventListeners();
    }

    setupEventListeners() {
        // Filter change events
        document.getElementById('statusFilter').addEventListener('change', (e) => {
            this.filters.status = e.target.value;
            this.currentPage = 1;
            this.loadChecklists();
        });

        document.getElementById('dateFilter').addEventListener('change', (e) => {
            this.filters.date_filter = e.target.value;
            this.currentPage = 1;
            this.loadChecklists();
        });

        document.getElementById('searchInput').addEventListener('input', (e) => {
            this.filters.search = e.target.value;
            this.currentPage = 1;
            this.debounceSearch();
        });
    }

    debounceSearch() {
        clearTimeout(this.searchTimeout);
        this.searchTimeout = setTimeout(() => {
            this.loadChecklists();
        }, 500);
    }

    async loadChecklists() {
        try {
            this.showLoading(true);
            
            const params = new URLSearchParams(this.filters);
            params.append('page', this.currentPage);

            const response = await fetch(`/impact/rnd-proof-checklist/api/checklists?${params}`);
            const data = await response.json();
            
            if (data.success) {
                this.checklists = data.data.checklists;
                this.totalPages = data.data.total_pages;
                this.renderChecklists(data.data.checklists);
                this.renderPagination(data.data.total_pages, data.data.current_page);

            } else {
                this.showMessage('error', data.message || 'Failed to load checklists');
            }
        } catch (error) {
            console.error('Error loading checklists:', error);
            this.showMessage('error', 'Error loading checklists');
        } finally {
            this.showLoading(false);
        }
    }

    renderChecklists(checklists) {
        const container = document.getElementById('checklistsContainer');
        const emptyState = document.getElementById('emptyState');
        
        if (!container) return;

        if (checklists.length === 0) {
            container.innerHTML = '';
            emptyState.style.display = 'block';
            return;
        }

        emptyState.style.display = 'none';

        const checklistsHTML = checklists.map(checklist => this.createChecklistCard(checklist)).join('');
        container.innerHTML = `<div class="row">${checklistsHTML}</div>`;
    }

    createChecklistCard(checklist) {
        const statusClass = checklist.status.toLowerCase().replace('_', '-');
        
        return `
            <div class="col-lg-4 col-md-6 mb-4">
                <div class="proof-checklist-card h-100">
                    <div class="d-flex justify-content-between align-items-center mb-3">
                        <h6 class="card-title mb-0">${checklist.customer_name}</h6>
                        <span class="status-badge status-${statusClass}">
                            ${checklist.status}
                        </span>
                    </div>
                    <div>
                        <div class="proof-info-item">
                            <span class="proof-info-label">Item:</span>
                            <span class="proof-info-value">${checklist.item_name}</span>
                        </div>
                        <div class="proof-info-item">
                            <span class="proof-info-label">Category:</span>
                            <span class="proof-info-value">${checklist.product_category}</span>
                        </div>
                        <div class="proof-info-item">
                            <span class="proof-info-label">Proof Date:</span>
                            <span class="proof-info-value">${this.formatDate(checklist.proof_date)}</span>
                        </div>
                        <div class="proof-info-item">
                            <span class="proof-info-label">Paper:</span>
                            <span class="proof-info-value">${checklist.paper_grammage || '-'}</span>
                        </div>
                        ${checklist.print_machines && checklist.print_machines.length > 0 ? `
                        <div class="proof-info-item">
                            <span class="proof-info-label">Machines:</span>
                            <span class="proof-info-value">
                                ${checklist.print_machines.map(machine => machine.print_machine.machine_name).join(', ')}
                            </span>
                        </div>
                        ` : ''}
                        <div class="proof-info-item">
                            <span class="proof-info-label">Created:</span>
                            <span class="proof-info-value">${this.formatDateTime(checklist.created_at)}</span>
                        </div>
                    </div>
                    <div class="mt-3 pt-3 border-top d-flex gap-2">
                        <div class="btn-group w-100" role="group">
                            <a href="/impact/rnd-proof-checklist/${checklist.id}" 
                               class="btn btn-outline-primary btn-sm">
                                <i class="fas fa-eye me-1"></i>View
                            </a>
                            <a href="/impact/rnd-proof-checklist/${checklist.id}/edit" 
                               class="btn btn-outline-secondary btn-sm">
                                <i class="fas fa-edit me-1"></i>Edit
                            </a>
                            ${checklist.status !== 'COMPLETED' && checklist.status !== 'CANCELLED' ? `
                            <form method="POST" action="/impact/rnd-proof-checklist/${checklist.id}/update-status" 
                                  class="d-inline" onsubmit="return confirm('Mark this checklist as completed?')">
                                <input type="hidden" name="status" value="COMPLETED">
                                <button type="submit" class="btn btn-outline-success btn-sm">
                                    <i class="fas fa-check me-1"></i>Complete
                                </button>
                            </form>
                            ` : ''}
                        </div>
                    </div>
                </div>
            </div>
        `;
    }

    formatDate(dateString) {
        if (!dateString) return '-';
        const date = new Date(dateString);
        const months = ['Januari', 'Februari', 'Maret', 'April', 'Mei', 'Juni', 
                       'Juli', 'Agustus', 'September', 'Oktober', 'November', 'Desember'];
        return `${date.getDate()} ${months[date.getMonth()]} ${date.getFullYear()}`;
    }

    formatDateTime(dateString) {
        if (!dateString) return '-';
        const date = new Date(dateString);
        const months = ['Jan', 'Feb', 'Mar', 'Apr', 'Mei', 'Jun', 
                       'Jul', 'Agu', 'Sep', 'Okt', 'Nov', 'Des'];
        const hours = date.getHours().toString().padStart(2, '0');
        const minutes = date.getMinutes().toString().padStart(2, '0');
        return `${date.getDate()} ${months[date.getMonth()]} ${date.getFullYear()}, ${hours}:${minutes}`;
    }

    renderPagination(totalPages, currentPage) {
        const paginationContainer = document.querySelector('.pagination-container');
        if (!paginationContainer) return;

        if (totalPages <= 1) {
            paginationContainer.innerHTML = '';
            return;
        }

        let paginationHTML = '<nav aria-label="Proof Checklists pagination"><ul class="pagination">';
        
        // Previous button
        if (currentPage > 1) {
            paginationHTML += `
                <li class="page-item">
                    <a class="page-link" href="#" onclick="window.proofChecklistInstance.goToPage(${currentPage - 1})">
                        <i class="fas fa-chevron-left"></i>
                    </a>
                </li>
            `;
        }
        
        // Page numbers
        for (let i = 1; i <= totalPages; i++) {
            if (i === currentPage) {
                paginationHTML += `
                    <li class="page-item active">
                        <span class="page-link">${i}</span>
                    </li>
                `;
            } else {
                paginationHTML += `
                    <li class="page-item">
                        <a class="page-link" href="#" onclick="window.proofChecklistInstance.goToPage(${i})">${i}</a>
                    </li>
                `;
            }
        }
        
        // Next button
        if (currentPage < totalPages) {
            paginationHTML += `
                <li class="page-item">
                    <a class="page-link" href="#" onclick="window.proofChecklistInstance.goToPage(${currentPage + 1})">
                        <i class="fas fa-chevron-right"></i>
                    </a>
                </li>
            `;
        }
        
        paginationHTML += '</ul></nav>';
        
        // Create pagination container if it doesn't exist
        if (!document.querySelector('.pagination-container')) {
            const container = document.getElementById('checklistsContainer');
            const paginationDiv = document.createElement('div');
            paginationDiv.className = 'pagination-container d-flex justify-content-center mt-4';
            container.parentNode.insertBefore(paginationDiv, container.nextSibling);
        }
        
        document.querySelector('.pagination-container').innerHTML = paginationHTML;
    }

    goToPage(page) {
        this.currentPage = page;
        this.loadChecklists();
    }

    showLoading(show) {
        const loadingSpinner = document.getElementById('loadingSpinner');
        const checklistsContainer = document.getElementById('checklistsContainer');
        
        if (show) {
            loadingSpinner.style.display = 'block';
            checklistsContainer.style.display = 'none';
        } else {
            loadingSpinner.style.display = 'none';
            checklistsContainer.style.display = 'block';
        }
    }

    showMessage(type, message) {
        const messageContainer = document.getElementById('dataMessage');
        if (!messageContainer) return;
        
        messageContainer.className = `alert alert-${type}`;
        messageContainer.textContent = message;
        messageContainer.classList.remove('d-none');
        
        // Auto-hide after 5 seconds
        setTimeout(() => {
            messageContainer.classList.add('d-none');
        }, 5000);
    }

    clearFilters() {
        this.filters = {
            status: '',
            date_filter: '',
            search: ''
        };
        this.currentPage = 1;
        
        // Reset form elements
        document.getElementById('statusFilter').value = '';
        document.getElementById('dateFilter').value = '';
        document.getElementById('searchInput').value = '';
        
        this.loadChecklists();
    }
}

// Make instance globally accessible
window.proofChecklistInstance = null;

// Initialize when DOM is ready (only if not already initialized)
document.addEventListener('DOMContentLoaded', function() {
    if (!window.proofChecklistInstance) {
        window.proofChecklistInstance = new ProofChecklist();
    }
});