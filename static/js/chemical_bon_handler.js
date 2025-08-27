// Global variables
let selectedItems = new Map(); // To store selected items and their quantities

// Initialize when document is ready
document.addEventListener('DOMContentLoaded', function() {
    // Initialize year filter with last 5 years
    const yearSelect = document.getElementById('yearFilter');

    const currentYear = new Date().getFullYear();
    for (let year = currentYear; year >= currentYear - 4; year--) {
        const option = document.createElement('option');
        option.value = year;
        option.textContent = year;
        yearSelect.appendChild(option);
    }
    
    // Load initial table data
    filterTableData();
    
    // Add event listeners for filters
    document.getElementById('yearFilter').addEventListener('change', filterTableData);
    document.getElementById('monthFilter').addEventListener('change', filterTableData);
    document.getElementById('brandFilter').addEventListener('change', filterTableData);
    document.getElementById('searchInput').addEventListener('input', filterTableData);
    document.getElementById('modalBrandFilter').addEventListener('change', handleBrandChange);
    document.getElementById('saveItemsBtn').addEventListener('click', handleSaveItems);
    document.getElementById('createBonAutoBtn').addEventListener('click', handleBonWeb);
    document.getElementById('finalizeBtn').addEventListener('click', handleFinalize);
    document.getElementById('clearSearch').addEventListener('click', function() {
        // Reset all filters to default values
        document.getElementById('searchInput').value = '';
        document.getElementById('yearFilter').value = ''; // Ensure this also resets the year
        document.getElementById('monthFilter').value = '';
        document.getElementById('brandFilter').value = '';
        
        // Refresh table data with cleared filters
        filterTableData();
    });
    
    // Hide finalize button initially
    document.getElementById('finalizeBtn').style.display = 'none';
    
    // Add event listener for request number
    document.getElementById('requestNumber').addEventListener('input', function(e) {
        document.getElementById('finalizeBtn').style.display = e.target.value ? 'block' : 'none';
    });
    
    // Add event listeners for modal reset
    ['hidden.bs.modal'].forEach(event => {
        document.getElementById('newBonModal').addEventListener(event, function() {
            resetModal();
        });
    });
    
    // Add event listener for cancel button
    document.querySelector('[data-bs-dismiss="modal"]').addEventListener('click', function() {
        resetModal();
    });

    // Set initial states
    document.getElementById('bonWebSection').style.display = 'none';
    document.getElementById('requestNumberSection').style.display = 'none';

    // Set current date as default
    const today = new Date().toISOString().split('T')[0];
    document.getElementById('tanggal').value = today;
    
    // Set default period (e.g., "Agustus 2025")
    const months = ['Januari', 'Februari', 'Maret', 'April', 'Mei', 'Juni', 'Juli', 'Agustus', 'September', 'Oktober', 'November', 'Desember'];
    const currentDate = new Date();
    document.getElementById('bonPeriode').value = `${months[currentDate.getMonth()]} ${currentDate.getFullYear()}`;
});

// Handle brand selection change
async function handleBrandChange(event) {
    const brand = event.target.value;
    const tableSection = document.getElementById('itemsTableSection');
    const tableBody = document.getElementById('chemicalItemsTableBody');
    
    // Clear previous items
    tableBody.innerHTML = '';
    
    if (!brand) {
        tableSection.style.display = 'none';
        return;
    }

    try {
        const response = await fetch(`/api/chemical-items/${brand}`);
        const data = await response.json();

        if (data.success && data.data.length > 0) {
            // Show table section
            tableSection.style.display = 'block';
            
            // Populate table
            data.data.forEach(item => {
                const row = document.createElement('tr');
                row.innerHTML = `
                    <td>${item.code}</td>
                    <td>${item.name}</td>
                    <td>
                        <input type="number" class="form-control" 
                               min="0" step="1" 
                               data-item-code="${item.code}"
                               data-item-name="${item.name}"
                               onchange="handleQuantityChange(event)">
                    </td>
                `;
                tableBody.appendChild(row);
            });
        } else {
            tableSection.style.display = 'none';
            showToast('Tidak ada item untuk brand ini', 'warning');
        }
    } catch (error) {
        console.error('Error fetching items:', error);
        showToast('Gagal mengambil data items', 'error');
    }
}

// Handle quantity change
function handleQuantityChange(event) {
    const input = event.target;
    const itemCode = input.dataset.itemCode;
    const itemName = input.dataset.itemName;
    const quantity = parseInt(input.value) || 0;

    if (quantity > 0) {
        selectedItems.set(itemCode, {
            name: itemName,
            quantity: quantity
        });
    } else {
        selectedItems.delete(itemCode);
    }
}

// Handle save items
async function handleSaveItems() {
    const tanggal = document.getElementById('tanggal').value;
    const bonPeriode = document.getElementById('bonPeriode').value;
    const brand = document.getElementById('modalBrandFilter').value;

    if (!tanggal || !bonPeriode || !brand || selectedItems.size === 0) {
        showToast('Mohon lengkapi semua data dan pilih minimal satu item', 'warning');
        return;
    }

    // Show Bon Web section after saving
    document.getElementById('bonWebSection').style.display = 'block';
    document.getElementById('saveItemsBtn').style.display = 'none';

    // Disable inputs after saving
    document.getElementById('tanggal').readOnly = true;
    document.getElementById('bonPeriode').readOnly = true;
    document.getElementById('modalBrandFilter').disabled = true;
    document.querySelectorAll('#chemicalItemsTableBody input').forEach(input => {
        input.readOnly = true;
    });

    showToast('Data berhasil disimpan', 'success');
}

// Handle Bon Web button click
function handleBonWeb() {
    // Open Bon Web in new tab
    window.open('http://172.27.169.1/material_management/create_material_cons_request/add', '_blank');
    
    // Show request number section
    document.getElementById('requestNumberSection').style.display = 'block';
    document.getElementById('createBonAutoBtn').style.display = 'none';
}

// Handle finalize (submit everything)
async function handleFinalize() {
    const requestNumber = document.getElementById('requestNumber').value;
    if (!requestNumber) {
        showToast('Mohon isi Request Number', 'warning');
        return;
    }

    try {
        // Prepare and validate items data
        const items = Array.from(selectedItems.entries()).map(([code, data]) => ({
            item_code: code,
            item_name: data.name,
            jumlah: data.quantity
        }));
        
        const formData = {
            tanggal: document.getElementById('tanggal').value,
            bon_periode: document.getElementById('bonPeriode').value,
            brand: document.getElementById('modalBrandFilter').value,
            request_number: requestNumber,
            items: items
        };
        
        const response = await fetch('/api/chemical-bon-ctp/create', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(formData)
        });

        const result = await response.json();

        if (result.success) {
            // Close modal
            const modal = bootstrap.Modal.getInstance(document.getElementById('newBonModal'));
            modal.hide();
            
            // Reset form dan selectedItems
            selectedItems.clear();
            document.getElementById('newBonForm').reset();
            document.getElementById('itemsTableSection').style.display = 'none';
            document.getElementById('bonWebSection').style.display = 'none';
            document.getElementById('requestNumberSection').style.display = 'none';
            
            // Re-enable inputs
            document.getElementById('tanggal').readOnly = false;
            document.getElementById('bonPeriode').readOnly = false;
            document.getElementById('modalBrandFilter').disabled = false;
            
            // Refresh table data
            filterTableData();
            
            // Show success message
            showToast('Chemical Bon berhasil dibuat', 'success');
        } else {
            showToast(result.message || 'Gagal membuat Chemical Bon', 'error');
        }
    } catch (error) {
        console.error('Error creating bon:', error);
        showToast('Terjadi kesalahan saat membuat bon', 'error');
    }
}

// Function to handle main page brand filter
// Function to reset modal
function resetModal() {
    // Reset form
    document.getElementById('newBonForm').reset();
    
    // Reset displays
    document.getElementById('itemsTableSection').style.display = 'none';
    document.getElementById('bonWebSection').style.display = 'none';
    document.getElementById('requestNumberSection').style.display = 'none';
    document.getElementById('saveItemsBtn').style.display = 'block';
    document.getElementById('finalizeBtn').style.display = 'none';
    
    // Reset inputs state
    document.getElementById('tanggal').readOnly = false;
    document.getElementById('bonPeriode').readOnly = false;
    document.getElementById('modalBrandFilter').disabled = false;
    
    // Clear selected items
    selectedItems.clear();
    
    // Set default date and period
    const today = new Date().toISOString().split('T')[0];
    document.getElementById('tanggal').value = today;
    
    const months = ['Januari', 'Februari', 'Maret', 'April', 'Mei', 'Juni', 'Juli', 'Agustus', 'September', 'Oktober', 'November', 'Desember'];
    const currentDate = new Date();
    document.getElementById('bonPeriode').value = `${months[currentDate.getMonth()]} ${currentDate.getFullYear()}`;
}

async function filterTableData() {
    const year = document.getElementById('yearFilter').value;
    const month = document.getElementById('monthFilter').value;
    const brand = document.getElementById('brandFilter').value;
    const searchInput = document.getElementById('searchInput').value;
    
    try {
        // Mendapatkan nilai page dan per_page dari URL atau set default
        const urlParams = new URLSearchParams(window.location.search);
        const currentPage = parseInt(urlParams.get('page')) || 1;
        // Asumsi per_page default sama dengan di backend (10)
        const itemsPerPage = parseInt(urlParams.get('per_page')) || 10; 

        // Mengirimkan parameter page dan per_page ke backend
        const response = await fetch(`/api/chemical-bon-ctp/list?year=${year}&month=${month}&brand=${brand}&search=${searchInput}&page=${currentPage}&per_page=${itemsPerPage}`);
        const data = await response.json();

        const tableBody = document.getElementById('chemicalBonTableBody');
        tableBody.innerHTML = ''; // Clear existing table data first

        // Add the new check for no data
        if (!data.success || !data.data || data.data.length === 0) {
            tableBody.innerHTML = '<tr><td colspan="10" class="text-center">Tidak ada data</td></tr>';
            const paginationElement = document.getElementById('pagination');
            if (paginationElement) {
                paginationElement.innerHTML = ''; 
            }
            return; // Exit function if no data
        }

        // Ambil nilai total dari respons backend
        const totalItems = data.total || 0; 

        // Jika ada paginationElement, update pagination UI
        const paginationElement = document.getElementById('pagination');
        if (paginationElement) {
            // Perlu menyesuaikan struktur pagination dengan yang dikembalikan backend
            updatePagination({
                page: data.current_page || 1,
                per_page: itemsPerPage, // Gunakan itemsPerPage dari frontend atau default backend
                total: data.total || 0,
                pages: data.pages || 1
            });
        }


        // If data exists, proceed to populate the table
        data.data.forEach((bon, index) => {
            const row = document.createElement('tr');
            const tanggal = new Date(bon.tanggal);
            const options = { 
                day: 'numeric', 
                month: 'long', 
                year: 'numeric'
            };

            // Hitung nomor urut terbalik
            // totalItems (total dari backend) - ( (currentPage - 1) * itemsPerPage ) - index (index di halaman saat ini)
            const reversedIndex = totalItems - ((currentPage - 1) * itemsPerPage) - index;

            row.innerHTML = `
                <td>${reversedIndex}</td>
                <td>${tanggal.toLocaleDateString('id-ID', options)}</td>
                <td>${bon.request_number}</td>
                <td>${bon.bon_periode}</td>
                <td>${bon.brand}</td>
                <td>${bon.item_code}</td>
                <td>${bon.item_name}</td>
                <td>${bon.jumlah}</td>
                <td>${bon.created_by}</td>
                <td>
                    <button class="btn btn-sm btn-primary" onclick="printChemicalBon('${bon.id}')">
                        <i class="fas fa-print"></i>
                    </button>
                </td>
            `;
            tableBody.appendChild(row);
        });
    } catch (error) {
        console.error('Error fetching data:', error);
        showToast('Terjadi kesalahan saat memuat data', 'error');
        // If an error occurs, also show "Tidak ada data"
        const tableBody = document.getElementById('chemicalBonTableBody');
        tableBody.innerHTML = '<tr><td colspan="10" class="text-center">Terjadi kesalahan saat memuat data.</td></tr>';
        const paginationElement = document.getElementById('pagination');
        if (paginationElement) {
            paginationElement.innerHTML = '';
        }
    }
}

// Function to handle chemical bon printing
async function printChemicalBon(bonId) {
    // Ambil data bon dari API
    try {
        const response = await fetch(`/api/chemical-bon-ctp/${bonId}`);
        const result = await response.json();
        
        if (result.success) {
            const bon = result.data;
            const queryParams = new URLSearchParams({
                date: bon.tanggal,
                brand: bon.brand,
                request_number: bon.request_number
            });
            window.open(`/print-chemical-bon?${queryParams.toString()}`, '_blank');
        } else {
            showToast('Gagal mengambil data bon', 'error');
        }
    } catch (error) {
        console.error('Error:', error);
        showToast('Terjadi kesalahan saat mencetak bon', 'error');
    }
}

// Utility function to show toast notifications
function showToast(message, type = 'info') {
    const toastContainer = document.querySelector('.toast-container');
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

// Export
function showExportModal() {
    const today = new Date();
    const firstDayOfMonth = new Date(today.getFullYear(), today.getMonth(), 1);
    document.getElementById('exportDateFrom').value = firstDayOfMonth.toISOString().split('T')[0];
    document.getElementById('exportDateTo').value = today.toISOString().split('T')[0];
    const modal = new bootstrap.Modal(document.getElementById('exportModal'));
    modal.show();
}

document.getElementById('confirmExport').addEventListener('click', function() {
    const dateFrom = document.getElementById('exportDateFrom').value;
    const dateTo = document.getElementById('exportDateTo').value;
    const brand = document.getElementById('exportBrandFilter').value;

    if (!dateFrom || !dateTo) {
        showToast('Harap isi rentang tanggal', 'error');
        return;
    }

    let queryParams = [];
    queryParams.push(`date_from=${encodeURIComponent(dateFrom)}`);
    queryParams.push(`date_to=${encodeURIComponent(dateTo)}`);
    if (brand) queryParams.push(`brand=${encodeURIComponent(brand)}`);
    const queryString = queryParams.length > 0 ? '?' + queryParams.join('&') : '';

    window.open(`/export-chemical-bon${queryString}`, '_blank');
    bootstrap.Modal.getInstance(document.getElementById('exportModal')).hide();
    showToast('Export berhasil dimulai, file akan segera didownload', 'success');
});