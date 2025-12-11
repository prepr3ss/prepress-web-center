// Global variables
let selectedItems = new Map(); // To store selected items and their quantities

// Initialize when document is ready
document.addEventListener('DOMContentLoaded', function() {
    // Hide loading spinner on initial load
    hideLoadingSpinner();
    
    // Add event listeners
    document.getElementById('brandFilter').addEventListener('change', handleBrandChange);
    document.getElementById('saveItemsBtn').addEventListener('click', handleSaveItems);
    document.getElementById('createBonAutoBtn').addEventListener('click', handleBonWeb);
    document.getElementById('finalizeBtn').addEventListener('click', handleFinalize);

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
        showLoadingSpinner();
        const response = await fetch(`/impact/api/chemical-items/${brand}`);
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
    } finally {
        hideLoadingSpinner();
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
    const brand = document.getElementById('brandFilter').value;

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
    document.getElementById('brandFilter').disabled = true;
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
        showLoadingSpinner();
        const formData = {
            tanggal: document.getElementById('tanggal').value,
            bon_periode: document.getElementById('bonPeriode').value,
            brand: document.getElementById('brandFilter').value,
            request_number: requestNumber,
            items: Array.from(selectedItems.entries()).map(([code, data]) => ({
                item_code: code,
                item_name: data.name,
                jumlah: data.quantity
            }))
        };

        const response = await fetch('/impact/api/chemical-bon-ctp/create', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(formData)
        });

        const result = await response.json();

        if (result.success) {
            showToast('Chemical Bon berhasil dibuat', 'success');
            // Close modal and refresh table
            const modal = bootstrap.Modal.getInstance(document.getElementById('newBonModal'));
            modal.hide();
            location.reload();
        } else {
            showToast(result.message || 'Gagal membuat Chemical Bon', 'error');
        }
    } catch (error) {
        console.error('Error creating bon:', error);
        showToast('Terjadi kesalahan saat membuat bon', 'error');
    } finally {
        hideLoadingSpinner();
    }
}

// Loading spinner functions
function showLoadingSpinner() {
    const spinner = document.querySelector('.spinner-overlay');
    if (spinner) spinner.style.display = 'flex';
}

function hideLoadingSpinner() {
    const spinner = document.querySelector('.spinner-overlay');
    if (spinner) spinner.style.display = 'none';
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
