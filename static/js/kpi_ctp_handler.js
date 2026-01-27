// static/js/kpi_ctp_handler.js

// --- Fungsi Debounce (ditempatkan di awal file, di luar DOMContentLoaded) ---
function debounce(func, delay) {
    let timeout;
    return function(...args) {
        const context = this;
        clearTimeout(timeout);
        timeout = setTimeout(() => func.apply(context, args), delay);
    };
}

// --- Variabel Global untuk Sorting ---
let currentSortColumn = 'id'; // Default sort column
let currentSortOrder = 'desc';      // Default sort order (descending)

let currentPage = 1;
const perPage = 30;
let totalPages = 1;

// --- Variabel Global untuk Menu Kontekstual ---
let contextMenu = null; // Menyimpan referensi menu kontekstual agar bisa dihapus

// --- NEW: Variabel Global untuk modal konfirmasi delete dan ID yang akan dihapus ---
let deleteModal = null; // Akan menyimpan instance Bootstrap Modal
let currentDeleteId = null; // Untuk menyimpan ID yang akan dihapus

// --- NEW: Fungsi untuk menampilkan Bootstrap Toast ---
function showBootstrapToast(message, header = 'Info', type = 'success') {
    const toastEl = document.getElementById('liveToast');
    if (!toastEl) {
        console.error("Toast element with ID 'liveToast' not found. Make sure you have the toast HTML structure in your page.");
        return;
    }
    const toastHeader = toastEl.querySelector('.toast-header strong');
    const toastBody = toastEl.querySelector('.toast-body');

    // Pastikan untuk menghapus semua kelas warna yang mungkin ada sebelumnya
    toastEl.classList.remove('text-bg-success', 'text-bg-danger', 'text-bg-info');

    if (toastHeader) {
        if (type === 'success') {
            toastHeader.textContent = 'Berhasil!';
            toastEl.classList.add('text-bg-success');
        } else if (type === 'danger') {
            toastHeader.textContent = 'Error!';
            toastEl.classList.add('text-bg-danger');
        } else { // type === 'info' atau lainnya
            toastHeader.textContent = header; // Gunakan header yang diberikan
            toastEl.classList.add('text-bg-info');
        }
    } else {
        console.warn("Toast header strong element not found.");
    }
    
    if (toastBody) {
        toastBody.textContent = message;
    } else {
        console.warn("Toast body element not found.");
    }

    const toast = new bootstrap.Toast(toastEl);
    toast.show();
}


// --- Fungsi loadKpiData (di luar DOMContentLoaded untuk akses global) ---
async function loadKpiData() {
    const kpiTableBody = document.getElementById('kpiTableBody');
    const searchInput = document.getElementById('searchInput');
    const filterMonth = document.getElementById('filterMonth');
    const filterGroup = document.getElementById('filterGroup');
    const filterYear = document.getElementById('filterYear');
    const dataMessage = document.getElementById('dataMessage'); // Untuk menampilkan pesan "Tidak ada data"

    // Only proceed if elements relevant to the table view exist
    if (!kpiTableBody || !searchInput || !filterMonth || !filterGroup || !filterYear || !dataMessage) {
        // This function will simply do nothing if called on pages without the table
        return;
    }

    kpiTableBody.innerHTML = '';
    dataMessage.classList.add('d-none'); // Hide previous messages

    // --- REMOVED: showBootstrapToast('Memuat data...', 'Informasi', 'info'); di sini
    // Karena ini bisa menimpa toast lain

    const searchValue = searchInput.value.trim();
    const monthValue = filterMonth.value;
    const groupValue = filterGroup.value;
    const yearValue = filterYear.value;

    let url = `/impact/get-kpi-data?search=${encodeURIComponent(searchValue)}&month=${encodeURIComponent(monthValue)}&group=${encodeURIComponent(groupValue)}&year=${encodeURIComponent(yearValue)}&sort_by=${encodeURIComponent(currentSortColumn)}&sort_order=${encodeURIComponent(currentSortOrder)}&page=${currentPage}&per_page=${perPage}`;

    try {
        const response = await fetch(url);
        const result = await response.json();
        const data = result.data || [];
        totalPages = result.pages || 1;

        if (response.ok) {
            // --- REMOVED: Kode untuk menyembunyikan toast 'Memuat data...' di sini
            // Karena tidak ada lagi toast 'Memuat data...' yang dipanggil di awal fungsi ini

            if (data.length > 0) {
                data.forEach((item, index) => {
                    const row = kpiTableBody.insertRow();
                    row.setAttribute('data-id', item.id);

                    // Calculate reversed index for No. column
                    const totalItems = result.total || (totalPages * perPage);
                    const itemsPerPage = perPage;
                    const reversedIndex = totalItems - ((currentPage - 1) * itemsPerPage) - index;
                    // First cell: No.
                    let cellNo = row.insertCell();
                    cellNo.textContent = reversedIndex;

                    const columns = [
                        'log_date',
                        'ctp_group', 'ctp_shift', 'ctp_pic', 'ctp_machine',
                        'wo_number', 'mc_number',
                        'print_machine', 'remarks_job', 'item_name', 'plate_type_material',
                        'num_plate_good', 'num_plate_not_good', 'paper_type', 'raster',
                        'created_at'  // Tambahkan created_at agar tersedia di DOM
                    ];

                    columns.forEach(col => {
                        let cell = row.insertCell();
                        let value = item[col];

                        if (col === 'log_date') {
                            value = value ? new Date(value).toLocaleDateString('id-ID', {
                                year: 'numeric',
                                month: 'long',
                                day: 'numeric'
                            }) : '';
                        } else if (col === 'created_at') {
                            // Untuk created_at, simpan nilai asli dalam atribut data untuk context menu
                            // tapi jangan tampilkan di layar karena kolomnya hidden
                            if (value) {
                                cell.setAttribute('data-created-at', value);
                                cell.textContent = ''; // Kosongkan karena kolom tersembunyi
                            } else {
                                cell.textContent = '';
                            }
                        } else if (col === 'updated_at') {
                            value = value ? new Date(value).toLocaleString('id-ID', {
                                year: 'numeric',
                                month: 'long',
                                day: 'numeric',
                                hour: '2-digit',
                                minute: '2-digit'
                            }) : '';
                        } else if (col === 'start_time' || col === 'finish_time') {
                            if (value) {
                                const timeParts = value.split(':');
                                if (timeParts.length >= 2) {
                                    const hour = timeParts[0].padStart(2, '0');
                                    const minute = timeParts[1].padStart(2, '0');
                                    value = `${hour}:${minute}`;
                                } else {
                                    value = value;
                                }
                            } else {
                                value = '';
                            }
                        }

                        if (col === 'num_plate_good') {
                            if (value !== null && parseInt(value) > 0) {
                                cell.classList.add('text-success');
                            }
                        } else if (col === 'num_plate_not_good') {
                            if (value !== null && parseInt(value) > 0) {
                                cell.classList.add('text-danger');
                            }
                        }

                        // Special handling for wo_number to make it clickable
                        if (col === 'wo_number') {
                            if (value && value.trim() !== '') {
                                cell.innerHTML = `<a href="#" class="wo-number-link text-primary text-decoration-none" data-id="${item.id}" onclick="showKpiDetail(${item.id}); return false;">${value}</a>`;
                            } else {
                                cell.textContent = value !== null && value !== undefined ? value : '';
                            }
                        } else {
                            cell.textContent = value !== null && value !== undefined ? value : '';
                        }
                    });
                });
                // Setelah render, baru assign ke global
                if (Array.isArray(data)) {
                    window.kpiTableData = data;
                }
            } else {
                dataMessage.textContent = 'Tidak ada data yang ditemukan dengan kriteria tersebut.';
                dataMessage.classList.remove('d-none');
                dataMessage.classList.add('alert-info');
                window.kpiTableData = [];
            }
        } else {
            const errorData = await response.json();
            showBootstrapToast(errorData.error || 'Gagal mengambil data.', 'Error!', 'danger');
            dataMessage.textContent = errorData.error || 'Gagal mengambil data.';
            dataMessage.classList.remove('d-none');
            dataMessage.classList.add('alert-danger');
        }
    } catch (error) {
        showBootstrapToast('Kesalahan jaringan: ' + error.message, 'Error!', 'danger');
        dataMessage.textContent = 'Kesalahan jaringan: ' + error.message;
        dataMessage.classList.remove('d-none');
        dataMessage.classList.add('alert-danger');
    }

    renderPagination();
}

// -- Paginasi
function renderPagination() {
    const paginationNav = document.getElementById('paginationNav');
    if (!paginationNav) return;
    paginationNav.innerHTML = '';
    if (totalPages <= 1) return;

    // Tombol Previous
    const prevLi = document.createElement('li');
    prevLi.className = 'page-item' + (currentPage === 1 ? ' disabled' : '');
    const prevA = document.createElement('a');
    prevA.className = 'page-link';
    prevA.href = '#';
    prevA.textContent = '«';
    prevA.addEventListener('click', function(e) {
        e.preventDefault();
        if (currentPage > 1) {
            currentPage--;
            loadKpiData();
        }
    });
    prevLi.appendChild(prevA);
    paginationNav.appendChild(prevLi);

    // Sliding window: maksimal 5 page number
    let startPage = Math.max(1, currentPage - 2);
    let endPage = Math.min(totalPages, currentPage + 2);
    if (currentPage <= 3) {
        endPage = Math.min(5, totalPages);
    }
    if (currentPage >= totalPages - 2) {
        startPage = Math.max(1, totalPages - 4);
    }
    for (let i = startPage; i <= endPage; i++) {
        const li = document.createElement('li');
        li.className = 'page-item' + (i === currentPage ? ' active' : '');
        const a = document.createElement('a');
        a.className = 'page-link';
        a.href = '#';
        a.textContent = i;
        a.addEventListener('click', function(e) {
            e.preventDefault();
            if (currentPage !== i) {
                currentPage = i;
                loadKpiData();
            }
        });
        li.appendChild(a);
        paginationNav.appendChild(li);
    }

    // Tombol Next
    const nextLi = document.createElement('li');
    nextLi.className = 'page-item' + (currentPage === totalPages ? ' disabled' : '');
    const nextA = document.createElement('a');
    nextA.className = 'page-link';
    nextA.href = '#';
    nextA.textContent = '»';
    nextA.addEventListener('click', function(e) {
        e.preventDefault();
        if (currentPage < totalPages) {
            currentPage++;
            loadKpiData();
        }
    });
    nextLi.appendChild(nextA);
    paginationNav.appendChild(nextLi);
}

// --- Fungsi untuk menampilkan menu kontekstual ---
// Sekarang menerima rowData (berisi created_at) agar bisa cek 24 jam
function showContextMenu(rowElement, x, y, rowData) {
    hideContextMenu();

    const dataId = rowElement.dataset.id;

    contextMenu = document.createElement('div');
    contextMenu.id = 'customContextMenu';
    contextMenu.classList.add('list-group', 'shadow-sm');
    contextMenu.style.position = 'absolute';

    // Perbaiki posisi agar mengikuti scroll
    let left = x + window.scrollX;
    let top = y + window.scrollY;

    // --- Opsional: Cegah menu keluar dari layar ---
    const menuWidth = 180; // atau sesuai minWidth menu Anda
    const menuHeight = 90; // kira-kira tinggi menu (2 tombol)
    const viewportWidth = window.innerWidth;
    const viewportHeight = window.innerHeight;
    if (left + menuWidth > viewportWidth + window.scrollX) {
        left = viewportWidth + window.scrollX - menuWidth - 10;
    }
    if (top + menuHeight > viewportHeight + window.scrollY) {
        top = viewportHeight + window.scrollY - menuHeight - 10;
    }
    // ---------------------------------------------

    contextMenu.style.left = `${left}px`;
    contextMenu.style.top = `${top}px`;
    contextMenu.style.zIndex = '1000';
    contextMenu.style.minWidth = '150px';
    contextMenu.style.backgroundColor = 'var(--bg-color, #ffffff)';
    contextMenu.style.border = '1px solid var(--border-color, #dee2e6)';
    contextMenu.style.borderRadius = '5px';
    contextMenu.style.overflow = 'hidden';

    // Role-based logic: admin always sees Edit/Delete, non-admin only if data <24h
    let showEditDelete = false;
    if (window.currentUserRole === 'admin') {
        showEditDelete = true;
    } else {
        // Non-admin: check 24h rule
        if (rowData && rowData.created_at) {
            let createdAt = null;
            let str = rowData.created_at.trim();
            
            // Coba parse berbagai format tanggal
            if (/^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}/.test(str)) {
                // ISO format: yyyy-mm-ddTHH:MM:SS
                createdAt = new Date(str);
            } else if (/^\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}/.test(str)) {
                // Format: yyyy-mm-dd HH:MM:SS
                createdAt = new Date(str.replace(' ', 'T'));
            } else if (/^\d{4}-\d{2}-\d{2}/.test(str)) {
                // Format: yyyy-mm-dd
                createdAt = new Date(str);
            } else if (/T/.test(str)) {
                // Format dengan T tapi mungkin tidak lengkap
                createdAt = new Date(str);
            } else {
                // Coba parse dengan fallback
                createdAt = new Date(str);
            }
            
            if (createdAt && !isNaN(createdAt.getTime())) {
                const now = new Date();
                const diffMs = now - createdAt;
                const diffHours = diffMs / (1000 * 60 * 60);
                
                if (diffHours <= 24) {
                    showEditDelete = true;
                }
            }
        }
    }

    if (showEditDelete) {
        contextMenu.innerHTML = `
            <button type="button" class="list-group-item list-group-item-action" data-action="edit">
                <i class="fas fa-edit me-2"></i> Edit Data
            </button>
            <button type="button" class="list-group-item list-group-item-action text-danger" data-action="delete">
                <i class="fas fa-trash-alt me-2"></i> Hapus Data
            </button>
        `;
        document.body.appendChild(contextMenu);
        contextMenu.querySelector('[data-action="edit"]').addEventListener('click', function() {
            window.location.href = `/impact/edit-kpi-ctp/${dataId}`;
            hideContextMenu();
        });
        contextMenu.querySelector('[data-action="delete"]').addEventListener('click', function() {
            showDeleteConfirmation(dataId);
            hideContextMenu();
        });
    } else {
        // Jangan tampilkan menu sama sekali jika tidak ada tombol
        if (contextMenu && document.body.contains(contextMenu)) {
            document.body.removeChild(contextMenu);
        }
        contextMenu = null;
    }
}

// --- Fungsi untuk menyembunyikan menu kontekstual ---
function hideContextMenu() {
    if (contextMenu && document.body.contains(contextMenu)) {
        document.body.removeChild(contextMenu);
        contextMenu = null;
    }
}

// --- Fungsi untuk konfirmasi Hapus (MENGGUNAKAN MODAL BOOTSTRAP) ---
function showDeleteConfirmation(id) {
    // Pastikan deleteModal sudah diinisialisasi di DOMContentLoaded
    if (!deleteModal) {
        console.error("Delete confirmation modal not initialized.");
        return;
    }

    // Set global variable currentDeleteId dengan ID yang akan dihapus
    currentDeleteId = id; 

    // Update modal body dengan nama item yang benar
    const deleteModalEl = document.getElementById('deleteConfirmationModal');
    const modalBody = deleteModalEl ? deleteModalEl.querySelector('.modal-body') : null;
    let itemName = '';
    // Cari nama item dari data tabel jika tersedia
    if (window.kpiTableData && Array.isArray(window.kpiTableData)) {
        const found = window.kpiTableData.find(row => row.id == id);
        if (found && found.item_name) {
            itemName = found.item_name;
        }
    }
    if (modalBody) {
        if (itemName) {
            modalBody.innerHTML = `Apakah Anda yakin ingin menghapus data <strong>${itemName}</strong>? Tindakan ini tidak dapat dibatalkan.`;
        } else {
            modalBody.innerHTML = `Apakah Anda yakin ingin menghapus data? Tindakan ini tidak dapat dibatalkan.`;
        }
    }

    // Tampilkan modal
    deleteModal.show();
}

// --- Fungsi untuk Delete Data (akan berkomunikasi dengan backend) ---
async function deleteKpiData(id) {
    console.log(`Mengirim permintaan DELETE untuk ID: ${id}`);
    try {
        const response = await fetch(`/impact/api/kpi_ctp/${id}`, {
            method: 'DELETE'
        });
        const result = await response.json();

        if (response.ok) {
            // Toast sukses dari operasi delete
            showBootstrapToast(result.message || 'Data berhasil dihapus.', 'Berhasil!', 'success');
            // Muat ulang tabel setelah berhasil dihapus
            // Memberi sedikit jeda agar toast sukses terlihat sebelum tabel di-reload
            setTimeout(() => {
                loadKpiData(); 
            }, 500); // Jeda 0.5 detik
            
        } else {
            // Toast error dari operasi delete
            showBootstrapToast(result.error || 'Gagal menghapus data.', 'Error!', 'danger');
        }

    } catch (error) {
        // Toast error jaringan saat delete
        showBootstrapToast('Kesalahan jaringan saat menghapus data: ' + error.message, 'Error!', 'danger');
    }
}

// --- Fungsi untuk menampilkan modal detail KPI ---
async function showKpiDetail(id) {
    try {
        // Tampilkan loading
        showLoading();
        
        // Fetch data detail dari API
        const response = await fetch(`/impact/api/kpi_ctp/${id}`);
        if (!response.ok) {
            const errorData = await response.json().catch(() => ({}));
            throw new Error(errorData.error || 'Gagal mengambil data detail KPI');
        }
        
        const data = await response.json();
        
        // Debug: log data untuk memastikan struktur benar
        console.log('KPI Detail Data:', data);
        
        // Debug: Log untuk mendiagnosis masalah layout
        console.log('=== DEBUG MODAL LAYOUT ===');
        console.log('Modal element:', document.getElementById('kpiDetailModal'));
        
        // Populate modal dengan data
        populateKpiDetailModal(data);
        
        // Debug: Log setelah populate
        setTimeout(() => {
            const modalElement = document.getElementById('kpiDetailModal');
            if (modalElement) {
                const modalBody = modalElement.querySelector('.modal-body');
                const tables = modalElement.querySelectorAll('table');
                const colorTables = modalElement.querySelectorAll('.color-table');
                
                console.log('Modal body width:', modalBody ? modalBody.offsetWidth : 'not found');
                console.log('Total tables found:', tables.length);
                console.log('Color tables found:', colorTables.length);
                
                // Check each table width
                tables.forEach((table, index) => {
                    console.log(`Table ${index} width:`, table.offsetWidth);
                    console.log(`Table ${index} parent width:`, table.parentElement ? table.parentElement.offsetWidth : 'no parent');
                });
                
                // Check first column widths
                const firstColumns = modalElement.querySelectorAll('td:first-child');
                firstColumns.forEach((col, index) => {
                    if (index < 5) { // Only check first 5 to avoid spam
                        console.log(`First column ${index} width:`, col.offsetWidth, 'content:', col.textContent);
                        console.log(`  - Computed style:`, window.getComputedStyle(col));
                        console.log(`  - Parent width:`, col.parentElement.offsetWidth);
                        console.log(`  - Table width:`, col.closest('table').offsetWidth);
                    }
                });
                
                // Check second column widths
                const secondColumns = modalElement.querySelectorAll('td:nth-child(2)');
                secondColumns.forEach((col, index) => {
                    if (index < 5) { // Only check first 5 to avoid spam
                        console.log(`Second column ${index} width:`, col.offsetWidth, 'content:', col.textContent);
                        console.log(`  - Computed style:`, window.getComputedStyle(col));
                    }
                });
                
                // Check table calculations
                const infoTables = modalElement.querySelectorAll('.modal-info-table');
                infoTables.forEach((table, index) => {
                    console.log(`Info table ${index}:`);
                    console.log(`  - Table width:`, table.offsetWidth);
                    console.log(`  - Table computed width:`, window.getComputedStyle(table).width);
                    console.log(`  - Parent width:`, table.parentElement.offsetWidth);
                });
            }
        }, 500);
        
        // Tampilkan modal
        const modal = new bootstrap.Modal(document.getElementById('kpiDetailModal'));
        modal.show();
        
    } catch (error) {
        console.error('Error:', error);
        showBootstrapToast('Gagal memuat detail KPI: ' + error.message, 'Error!', 'danger');
    } finally {
        // Sembunyikan loading
        hideLoading();
    }
}

// --- Fungsi untuk mengisi modal dengan data KPI ---
function populateKpiDetailModal(data) {
    // Update modal title with item name
    const modalItemNameElement = document.getElementById('modalItemName');
    if (modalItemNameElement) {
        modalItemNameElement.textContent = data.item_name || 'Unknown Item';
    }
    
    // Format tanggal
    const formatDate = (dateStr) => {
        if (!dateStr) return '-';
        return new Date(dateStr).toLocaleDateString('id-ID', {
            year: 'numeric',
            month: 'long',
            day: 'numeric'
        });
    };
    
    // Format datetime
    const formatDateTime = (dateStr) => {
        if (!dateStr) return '-';
        return new Date(dateStr).toLocaleString('id-ID', {
            year: 'numeric',
            month: 'long',
            day: 'numeric',
            hour: '2-digit',
            minute: '2-digit'
        });
    };
    
    // Format time
    const formatTime = (timeStr) => {
        if (!timeStr) return '-';
        const timeParts = timeStr.split(':');
        if (timeParts.length >= 2) {
            const hour = timeParts[0].padStart(2, '0');
            const minute = timeParts[1].padStart(2, '0');
            return `${hour}:${minute}`;
        }
        return timeStr;
    };
    
    // Populate Informasi Umum tab
    document.getElementById('detail-log_date').textContent = formatDate(data.log_date);
    document.getElementById('detail-start_time').textContent = formatTime(data.start_time);
    document.getElementById('detail-finish_time').textContent = formatTime(data.finish_time);
    document.getElementById('detail-ctp_group').textContent = data.ctp_group || '-';
    document.getElementById('detail-ctp_shift').textContent = data.ctp_shift || '-';
    document.getElementById('detail-ctp_pic').textContent = data.ctp_pic || '-';
    document.getElementById('detail-ctp_machine').textContent = data.ctp_machine || '-';
    document.getElementById('detail-wo_number').textContent = data.wo_number || '-';
    document.getElementById('detail-mc_number').textContent = data.mc_number || '-';
    document.getElementById('detail-run_length_sheet').textContent = data.run_length_sheet || '-';
    
    // Populate Detail Job tab
    document.getElementById('detail-item_name').textContent = data.item_name || '-';
    document.getElementById('detail-print_machine').textContent = data.print_machine || '-';
    document.getElementById('detail-run_length_sheet_job').textContent = data.run_length_sheet || '-';
    document.getElementById('detail-remarks_job').textContent = data.remarks_job || '-';
    document.getElementById('detail-note').textContent = data.note || '-';
    
    // Populate Informasi Plate tab
    document.getElementById('detail-plate_type_material').textContent = data.plate_type_material || '-';
    document.getElementById('detail-paper_type').textContent = data.paper_type || '-';
    document.getElementById('detail-raster').textContent = data.raster || '-';
    
    const plateGoodEl = document.getElementById('detail-num_plate_good');
    const plateNotGoodEl = document.getElementById('detail-num_plate_not_good');
    
    if (data.num_plate_good && parseInt(data.num_plate_good) > 0) {
        plateGoodEl.textContent = data.num_plate_good;
        plateGoodEl.className = 'text-success fw-bold';
    } else {
        plateGoodEl.textContent = data.num_plate_good || '0';
        plateGoodEl.className = '';
    }
    
    if (data.num_plate_not_good && parseInt(data.num_plate_not_good) > 0) {
        plateNotGoodEl.textContent = data.num_plate_not_good;
        plateNotGoodEl.className = 'text-danger fw-bold';
    } else {
        plateNotGoodEl.textContent = data.num_plate_not_good || '0';
        plateNotGoodEl.className = '';
    }
    
    document.getElementById('detail-not_good_reason').textContent = data.not_good_reason || '-';
    document.getElementById('detail-detail_not_good').textContent = data.detail_not_good || '-';
    
    // Populate Data Warna tab
    const colorFields = [
        'cyan_20_percent', 'cyan_25_percent', 'cyan_40_percent', 'cyan_50_percent', 'cyan_80_percent', 'cyan_75_percent', 'cyan_linear',
        'magenta_20_percent', 'magenta_25_percent', 'magenta_40_percent', 'magenta_50_percent', 'magenta_80_percent', 'magenta_75_percent', 'magenta_linear',
        'yellow_20_percent', 'yellow_25_percent', 'yellow_40_percent', 'yellow_50_percent', 'yellow_80_percent', 'yellow_75_percent', 'yellow_linear',
        'black_20_percent', 'black_25_percent', 'black_40_percent', 'black_50_percent', 'black_80_percent', 'black_75_percent', 'black_linear',
        'x_20_percent', 'x_25_percent', 'x_40_percent', 'x_50_percent', 'x_80_percent', 'x_75_percent', 'x_linear',
        'z_20_percent', 'z_25_percent', 'z_40_percent', 'z_50_percent', 'z_80_percent', 'z_75_percent', 'z_linear',
        'u_20_percent', 'u_25_percent', 'u_40_percent', 'u_50_percent', 'u_80_percent', 'u_75_percent', 'u_linear',
        'v_20_percent', 'v_25_percent', 'v_40_percent', 'v_50_percent', 'v_80_percent', 'v_75_percent', 'v_linear',
        'f_20_percent', 'f_25_percent', 'f_40_percent', 'f_50_percent', 'f_80_percent', 'f_75_percent', 'f_linear',
        'g_20_percent', 'g_25_percent', 'g_40_percent', 'g_50_percent', 'g_80_percent', 'g_75_percent', 'g_linear',
        'h_20_percent', 'h_25_percent', 'h_40_percent', 'h_50_percent', 'h_80_percent', 'h_75_percent', 'h_linear',
        'j_20_percent', 'j_25_percent', 'j_40_percent', 'j_50_percent', 'j_80_percent', 'j_75_percent', 'j_linear'
    ];
    
    colorFields.forEach(field => {
        const element = document.getElementById(`detail-${field}`);
        if (element) {
            let value = data[field];
            // Handle different data types
            if (value !== null && value !== undefined && value !== '') {
                // If it's a number, format it properly
                if (typeof value === 'number') {
                    value = value.toFixed(2);
                }
                element.textContent = value;
            } else {
                // Tampilkan nilai kosong tanpa tanda "-"
                element.textContent = '';
            }
        }
    });
    
    // Populate Log Sistem tab
    document.getElementById('detail-created_at').textContent = formatDateTime(data.created_at);
    document.getElementById('detail-updated_at').textContent = formatDateTime(data.updated_at);
}

// --- DOMContentLoaded Event Listener ---
document.addEventListener('DOMContentLoaded', function() {
    const ctpLogForm = document.getElementById('ctpLogForm');
    const notGoodReasonGroup = document.getElementById('notGoodReasonGroup');
    const numPlateNotGoodInput = document.getElementById('num_plate_not_good');
    const notGoodReasonSelect = document.getElementById('not_good_reason');

    const searchInput = document.getElementById('searchInput');
    const clearSearchBtn = document.getElementById('clearSearch');
    const filterMonth = document.getElementById('filterMonth');
    const filterGroup = document.getElementById('filterGroup');
    const filterYear = document.getElementById('filterYear');
    const kpiDataTable = document.getElementById('kpiDataTable');
    const kpiTableBody = document.getElementById('kpiTableBody');

    // --- Inisialisasi Modal Konfirmasi Delete HANYA SEKALI ---
    const deleteModalEl = document.getElementById('deleteConfirmationModal');
    if (deleteModalEl) {
        deleteModal = new bootstrap.Modal(deleteModalEl); // Inisialisasi di sini
        document.getElementById('confirmDeleteBtn').addEventListener('click', function() {
            // Gunakan currentDeleteId yang sudah di-set di showDeleteConfirmation
            if (currentDeleteId) {
                deleteKpiData(currentDeleteId);
                deleteModal.hide(); // Sembunyikan modal setelah konfirmasi
                currentDeleteId = null; // Reset ID setelah digunakan
            }
        });
    }

    // --- NEW: Fungsi untuk mendapatkan ID dari URL jika ada (untuk mode edit) ---
    function getDataIdFromUrl() {
        const path = window.location.pathname;
        const parts = path.split('/');
        if (parts.includes('edit-kpi-ctp') && parts.length > parts.indexOf('edit-kpi-ctp') + 1) {
            return parts[parts.indexOf('edit-kpi-ctp') + 1];
        }
        return null;
    }

    const dataId = getDataIdFromUrl();

    // --- NEW: Fungsi untuk mengisi form dengan data yang ada (khusus mode edit) ---
    async function populateForm(id) {
        try {
            const response = await fetch(`/impact/api/kpi_ctp/${id}`);
            if (!response.ok) {
                const contentType = response.headers.get("content-type");
                if (contentType && contentType.indexOf("text/html") !== -1) {
                    throw new Error('Endpoint /impact/api/kpi_ctp/id not found or returned HTML, not JSON. Check your Flask route.');
                }
                const errorData = await response.json();
                throw new Error(errorData.error || `HTTP error! status: ${response.status}`);
            }
            const data = await response.json();

            document.getElementById('log_date').value = data.log_date || '';
            document.getElementById('start_time').value = data.start_time || '';
            document.getElementById('finish_time').value = data.finish_time || '';
            document.getElementById('ctp_group').value = data.ctp_group || '';
            document.getElementById('ctp_shift').value = data.ctp_shift || '';
            document.getElementById('ctp_pic').value = data.ctp_pic || '';
            document.getElementById('ctp_machine').value = data.ctp_machine || '';
            document.getElementById('processor_temperature').value = data.processor_temperature || '';
            document.getElementById('dwell_time').value = data.dwell_time || '';
            document.getElementById('raster').value = data.raster || '';
            document.getElementById('plate_type_material').value = data.plate_type_material || '';
            
            // Handle paper type dropdown and custom input
            const paperTypeSelect = document.getElementById('paper_type_select');
            const paperTypeCustom = document.getElementById('paper_type_custom');
            const paperTypes = ['HANSOL', 'CMI', 'LEEMAN', 'FAJAR', 'SURYA PEMENANG', 'APPCHINA', 'DONGGUAN', 'SOWAN', 'NINE DRAGON', 'CHENG', 'BUANA', 'RIAU', 'SUNPAPER', 'SUPARMA'];
            
            if (paperTypeSelect && paperTypeCustom) {
                if (data.paper_type && paperTypes.includes(data.paper_type)) {
                    paperTypeSelect.value = data.paper_type;
                    paperTypeCustom.value = '';
                    togglePaperTypeInput(); // Ensure correct visibility
                } else if (data.paper_type) {
                    paperTypeSelect.value = 'Lainnya';
                    paperTypeCustom.value = data.paper_type;
                    togglePaperTypeInput(); // Ensure correct visibility
                } else {
                    paperTypeSelect.value = '';
                    paperTypeCustom.value = '';
                    togglePaperTypeInput(); // Ensure correct visibility
                }
            }
            document.getElementById('num_plate_good').value = data.num_plate_good || '0';
            document.getElementById('num_plate_not_good').value = data.num_plate_not_good || '0';
            document.getElementById('not_good_reason').value = data.not_good_reason || '';
            document.getElementById('detail_not_good').value = data.detail_not_good || '';
            document.getElementById('print_machine').value = data.print_machine || '';
            document.getElementById('remarks_job').value = data.remarks_job || '';
            document.getElementById('wo_number').value = data.wo_number || '';
            document.getElementById('mc_number').value = data.mc_number || '';
            document.getElementById('run_length_sheet').value = data.run_length_sheet || '';
            document.getElementById('item_name').value = data.item_name || '';
            document.getElementById('note').value = data.note || '';

            const rasterFields = [
                'cyan_20_percent', 'cyan_25_percent', 'cyan_40_percent', 'cyan_50_percent', 'cyan_80_percent', 'cyan_75_percent', 'cyan_linear',
                'magenta_20_percent', 'magenta_25_percent', 'magenta_40_percent', 'magenta_50_percent', 'magenta_80_percent', 'magenta_75_percent', 'magenta_linear',
                'yellow_20_percent', 'yellow_25_percent', 'yellow_40_percent', 'yellow_50_percent', 'yellow_80_percent', 'yellow_75_percent', 'yellow_linear',
                'black_20_percent', 'black_25_percent', 'black_40_percent', 'black_50_percent', 'black_80_percent', 'black_75_percent', 'black_linear',
                'x_20_percent', 'x_25_percent', 'x_40_percent', 'x_50_percent', 'x_80_percent', 'x_75_percent', 'x_linear',
                'z_20_percent', 'z_25_percent', 'z_40_percent', 'z_50_percent', 'z_80_percent', 'z_75_percent', 'z_linear',
                'u_20_percent', 'u_25_percent', 'u_40_percent', 'u_50_percent', 'u_80_percent', 'u_75_percent', 'u_linear',
                'v_20_percent', 'v_25_percent', 'v_40_percent', 'v_50_percent', 'v_80_percent', 'v_75_percent', 'v_linear',
                'f_20_percent', 'f_25_percent', 'f_40_percent', 'f_50_percent', 'f_80_percent', 'f_75_percent', 'f_linear',
                'g_20_percent', 'g_25_percent', 'g_40_percent', 'g_50_percent', 'g_80_percent', 'g_75_percent', 'g_linear',
                'h_20_percent', 'h_25_percent', 'h_40_percent', 'h_50_percent', 'h_80_percent', 'h_75_percent', 'h_linear',
                'j_20_percent', 'j_25_percent', 'j_40_percent', 'j_50_percent', 'j_80_percent', 'j_75_percent', 'j_linear'

            ];
            rasterFields.forEach(field => {
                const element = document.getElementById(field);
                if (element) {
                    element.value = data[field] || '';
                }
            });

            toggleNotGoodReason();

        } catch (error) {
            console.error('Error fetching CTP data:', error);
            showBootstrapToast(`Gagal memuat data: ${error.message}`, 'Error!', 'danger');
        }
    }

    // --- Logika untuk menampilkan/menyembunyikan alasan plate not good ---
    function toggleNotGoodReason() {
        const notGoodDetailGroup = document.getElementById('notGoodDetailGroup');
        const detailNotGoodTextarea = document.getElementById('detail_not_good');
        
        if (numPlateNotGoodInput && notGoodReasonGroup && notGoodReasonSelect) {
            if (parseInt(numPlateNotGoodInput.value) > 0) {
                notGoodReasonGroup.classList.remove('d-none');
                if (notGoodDetailGroup) notGoodDetailGroup.classList.remove('d-none');
                notGoodReasonSelect.setAttribute('required', 'true');
                if (detailNotGoodTextarea) detailNotGoodTextarea.setAttribute('required', 'true');
            } else {
                notGoodReasonGroup.classList.add('d-none');
                if (notGoodDetailGroup) notGoodDetailGroup.classList.add('d-none');
                notGoodReasonSelect.removeAttribute('required');
                if (detailNotGoodTextarea) detailNotGoodTextarea.removeAttribute('required');
                notGoodReasonSelect.value = ''; // Clear selection
                if (detailNotGoodTextarea) detailNotGoodTextarea.value = ''; // Clear textarea
            }
        }
    }

    // --- Logika untuk dropdown Jenis Kertas ---
    function togglePaperTypeInput() {
        const paperTypeSelect = document.getElementById('paper_type_select');
        const paperTypeCustom = document.getElementById('paper_type_custom');
        const paperTypeCancelBtn = document.getElementById('paper_type_cancel_btn');
        
        if (paperTypeSelect && paperTypeCustom && paperTypeCancelBtn) {
            if (paperTypeSelect.value === 'Lainnya') {
                paperTypeSelect.classList.add('d-none');
                paperTypeCustom.classList.remove('d-none');
                paperTypeCancelBtn.classList.remove('d-none');
                paperTypeCustom.setAttribute('required', 'true');
                paperTypeSelect.removeAttribute('required');
            } else {
                paperTypeSelect.classList.remove('d-none');
                paperTypeCustom.classList.add('d-none');
                paperTypeCancelBtn.classList.add('d-none');
                paperTypeSelect.setAttribute('required', 'true');
                paperTypeCustom.removeAttribute('required');
                paperTypeCustom.value = ''; // Clear custom input when switching back
            }
        }
    }

    function cancelCustomPaperType() {
        const paperTypeSelect = document.getElementById('paper_type_select');
        const paperTypeCustom = document.getElementById('paper_type_custom');
        const paperTypeCancelBtn = document.getElementById('paper_type_cancel_btn');
        
        if (paperTypeSelect && paperTypeCustom && paperTypeCancelBtn) {
            paperTypeSelect.value = '';
            paperTypeSelect.classList.remove('d-none');
            paperTypeCustom.classList.add('d-none');
            paperTypeCancelBtn.classList.add('d-none');
            paperTypeSelect.setAttribute('required', 'true');
            paperTypeCustom.removeAttribute('required');
            paperTypeCustom.value = '';
        }
    }
    // --- Akhir logika Jenis Kertas ---

    if (numPlateNotGoodInput) {
        numPlateNotGoodInput.addEventListener('input', toggleNotGoodReason);
        toggleNotGoodReason();
    }
    
    // Add event listener for paper type dropdown
    const paperTypeSelect = document.getElementById('paper_type_select');
    const paperTypeCancelBtn = document.getElementById('paper_type_cancel_btn');
    
    if (paperTypeSelect) {
        paperTypeSelect.addEventListener('change', togglePaperTypeInput);
    }
    
    if (paperTypeCancelBtn) {
        paperTypeCancelBtn.addEventListener('click', cancelCustomPaperType);
    }

    // --- Handle form submission (untuk halaman input-kpi-ctp dan edit-kpi-ctp) ---
    if (ctpLogForm) {
        ctpLogForm.addEventListener('submit', async function(event) {
            event.preventDefault();

            const formData = new FormData(ctpLogForm);
            const data = Object.fromEntries(formData.entries());

            // Handle paper type logic
            const paperTypeSelect = document.getElementById('paper_type_select');
            const paperTypeCustom = document.getElementById('paper_type_custom');
            
            if (paperTypeSelect && paperTypeCustom) {
                if (paperTypeSelect.value === 'Lainnya') {
                    data.paper_type = paperTypeCustom.value;
                } else {
                    data.paper_type = paperTypeSelect.value;
                }
                
                // Remove the select field from data since we're using paper_type field
                delete data.paper_type_select;
            }

            data.run_length_sheet = data.run_length_sheet ? parseInt(data.run_length_sheet) : null;
            data.num_plate_good = parseInt(data.num_plate_good);
            data.num_plate_not_good = parseInt(data.num_plate_not_good);
            data.processor_temperature = parseFloat(data.processor_temperature) || null;
            data.dwell_time = parseFloat(data.dwell_time) || null;

            const floatFields = [
                'cyan_20_percent', 'cyan_25_percent', 'cyan_40_percent', 'cyan_50_percent', 'cyan_80_percent', 'cyan_75_percent', 'cyan_linear',
                'magenta_20_percent', 'magenta_25_percent', 'magenta_40_percent', 'magenta_50_percent', 'magenta_80_percent', 'magenta_75_percent', 'magenta_linear',
                'yellow_20_percent', 'yellow_25_percent', 'yellow_40_percent', 'yellow_50_percent', 'yellow_80_percent', 'yellow_75_percent', 'yellow_linear',
                'black_20_percent', 'black_25_percent', 'black_40_percent', 'black_50_percent', 'black_80_percent', 'black_75_percent', 'black_linear',
                'x_20_percent', 'x_25_percent', 'x_40_percent', 'x_50_percent', 'x_80_percent', 'x_75_percent', 'x_linear',
                'z_20_percent', 'z_25_percent', 'z_40_percent', 'z_50_percent', 'z_80_percent', 'z_75_percent', 'z_linear',
                'u_20_percent', 'u_25_percent', 'u_40_percent', 'u_50_percent', 'u_80_percent', 'u_75_percent', 'u_linear',
                'v_20_percent', 'v_25_percent', 'v_40_percent', 'v_50_percent', 'v_80_percent', 'v_75_percent', 'v_linear',
                'f_20_percent', 'f_25_percent', 'f_40_percent', 'f_50_percent', 'f_80_percent', 'f_75_percent', 'f_linear',
                'g_20_percent', 'g_25_percent', 'g_40_percent', 'g_50_percent', 'g_80_percent', 'g_75_percent', 'g_linear',
                'h_20_percent', 'h_25_percent', 'h_40_percent', 'h_50_percent', 'h_80_percent', 'h_75_percent', 'h_linear',
                'j_20_percent', 'j_25_percent', 'j_40_percent', 'j_50_percent', 'j_80_percent', 'j_75_percent', 'j_linear'
            ];
            floatFields.forEach(field => {
                data[field] = data[field] ? parseFloat(data[field]) : null;
            });

            for (const key in data) {
                if (data[key] === '') {
                    data[key] = null;
                }
            }

            let url = '/impact/submit-kpi';
            let method = 'POST';

            if (dataId) {
                url = `/impact/api/kpi_ctp/${dataId}`;
                method = 'PUT';
            }

            try {
                const response = await fetch(url, {
                    method: method,
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify(data)
                });

                const result = await response.json();

                if (response.ok) {
                    showBootstrapToast(result.message, 'Berhasil!', 'success');
                    if (!dataId) {
                        ctpLogForm.reset();
                        // Clear detail_not_good field manually since reset() might not clear it properly
                        const detailNotGoodTextarea = document.getElementById('detail_not_good');
                        if (detailNotGoodTextarea) {
                            detailNotGoodTextarea.value = '';
                        }
                        toggleNotGoodReason();
                    }
                    if (dataId) {
                        setTimeout(() => {
                            window.location.href = '/impact/tabel-kpi-ctp';
                        }, 1500);
                    }
                } else {
                    showBootstrapToast(result.error || 'Terjadi kesalahan saat menyimpan data.', 'Error!', 'danger');
                }
            } catch (error) {
                console.error('Error:', error);
                showBootstrapToast('Terjadi kesalahan jaringan atau server.', 'Error!', 'danger');
            }
        });
    }

    if (dataId && ctpLogForm) {
        populateForm(dataId);
        const submitButton = ctpLogForm.querySelector('button[type="submit"]');
        if (submitButton) {
            submitButton.textContent = 'Simpan Perubahan';
        }
    }

    // --- Event Listeners untuk Filter, Pencarian, dan Sorting (untuk halaman tabel-kpi-ctp) ---
    if (kpiDataTable && searchInput && filterMonth && filterGroup && filterYear) {
        searchInput.addEventListener('input', debounce(function() {
            currentPage = 1;
            loadKpiData();
        }, 300));
        filterMonth.addEventListener('change', function() {
            currentPage = 1;
            loadKpiData();
        });
        filterGroup.addEventListener('change', function() {
            currentPage = 1;
            loadKpiData();
        });
        filterYear.addEventListener('change', function() {
            currentPage = 1;
            loadKpiData();
        });

        clearSearchBtn.addEventListener('click', function() {
            searchInput.value = '';
            loadKpiData();
        });

        kpiDataTable.querySelectorAll('th[data-column]').forEach(header => {
            header.style.cursor = 'pointer';
            header.addEventListener('click', function() {
                const column = this.getAttribute('data-column');
                if (column === currentSortColumn) {
                    currentSortOrder = (currentSortOrder === 'asc') ? 'desc' : 'asc';
                } else {
                    currentSortColumn = column;
                    currentSortOrder = 'asc';
                }
                updateSortIcons();
                loadKpiData();
            });
        });

        function updateSortIcons() {
            kpiDataTable.querySelectorAll('th[data-column] i').forEach(icon => {
                icon.classList.remove('fa-sort-up', 'fa-sort-down');
                icon.classList.add('fa-sort');
            });

            const currentHeaderIcon = kpiDataTable.querySelector(`th[data-column="${currentSortColumn}"] i`);
            if (currentHeaderIcon) {
                currentHeaderIcon.classList.remove('fa-sort');
                if (currentSortOrder === 'asc') {
                    currentHeaderIcon.classList.add('fa-sort-up');
                } else {
                    currentHeaderIcon.classList.add('fa-sort-down');
                }
            }
        }
        updateSortIcons();
    }

    // --- FITUR KLIK KANAN EDIT/DELETE ---
    if (kpiTableBody) { // Pastikan kpiTableBody ada sebelum menambahkan event listener
        kpiTableBody.addEventListener('contextmenu', function(e) {
            const clickedRow = e.target.closest('tr');
            if (clickedRow && clickedRow.dataset.id) {
                e.preventDefault();
                // Ambil data dari window.kpiTableData berdasarkan ID
                const rowId = parseInt(clickedRow.dataset.id);
                let rowData = null;
                
                if (window.kpiTableData && Array.isArray(window.kpiTableData)) {
                    rowData = window.kpiTableData.find(item => item.id === rowId);
                }
                
                showContextMenu(clickedRow, e.clientX, e.clientY, rowData);
            } else {
                hideContextMenu();
            }
        });

        document.addEventListener('click', function(e) {
            if (contextMenu && !contextMenu.contains(e.target)) {
                hideContextMenu();
            }
        });
        document.addEventListener('scroll', function() {
            hideContextMenu();
        });
        document.addEventListener('keydown', function(e) {
            if (e.key === "Escape") {
                hideContextMenu();
            }
        });
    }

    // --- Panggil loadKpiData saat DOM selesai dimuat (untuk halaman tabel) ---
    // Tambahkan delay saat pertama kali memuat data untuk menghindari toast "memuat data"
    // bertabrakan dengan toast dari operasi sebelumnya (misal redirect setelah submit form)
    if (kpiTableBody && window.location.pathname.includes('/impact/tabel-kpi-ctp')) {
        // Hapus toast 'Memuat data...' dari awal loadKpiData.
        // Sebaiknya, biarkan toast 'memuat data' jika memang ada proses loading yang signifikan.
        // Jika tidak, hilangkan saja.
        // Untuk sekarang, saya akan menghapus pemanggilan toast info di awal loadKpiData
        // dan tidak menambahkan jeda di sini, karena jeda lebih cocok setelah operasi.
        loadKpiData();
    }


});