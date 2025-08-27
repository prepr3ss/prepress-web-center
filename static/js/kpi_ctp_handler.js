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

    let url = `/get-kpi-data?search=${encodeURIComponent(searchValue)}&month=${encodeURIComponent(monthValue)}&group=${encodeURIComponent(groupValue)}&year=${encodeURIComponent(yearValue)}&sort_by=${encodeURIComponent(currentSortColumn)}&sort_order=${encodeURIComponent(currentSortOrder)}&page=${currentPage}&per_page=${perPage}`;

    try {
        const response = await fetch(url);
        const result = await response.json();
        const data = result.data || [];
        totalPages = result.pages || 1;

        if (response.ok) {
            // --- REMOVED: Kode untuk menyembunyikan toast 'Memuat data...' di sini
            // Karena tidak ada lagi toast 'Memuat data...' yang dipanggil di awal fungsi ini

            if (data.length > 0) {
                data.forEach(item => {
                    const row = kpiTableBody.insertRow();
                    row.setAttribute('data-id', item.id);

                    const columns = [
                        'id', 'log_date', 'start_time', 'finish_time',
                        'ctp_group', 'ctp_shift', 'ctp_pic', 'ctp_machine',
                        'wo_number', 'mc_number',
                        'run_length_sheet', 'print_machine', 'remarks_job', 'note', 'item_name', 'plate_type_material', 'raster',
                        'num_plate_good', 'num_plate_not_good', 'not_good_reason',
                        'cyan_25_percent', 'cyan_50_percent', 'cyan_75_percent',
                        'magenta_25_percent', 'magenta_50_percent', 'magenta_75_percent',
                        'yellow_25_percent', 'yellow_50_percent', 'yellow_75_percent',
                        'black_25_percent', 'black_50_percent', 'black_75_percent',
                        'x_25_percent', 'x_50_percent', 'x_75_percent',
                        'z_25_percent', 'z_50_percent', 'z_75_percent',
                        'u_25_percent', 'u_50_percent', 'u_75_percent',
                        'v_25_percent', 'v_50_percent', 'v_75_percent',
                        'created_at', 'updated_at'
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
                        } else if (col === 'created_at' || col === 'updated_at') {
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

                        cell.textContent = value !== null && value !== undefined ? value : '';
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
            if (/^\d{2}\/\d{2}\/\d{4}/.test(str)) {
                // Format dd/mm/yyyy atau dd/mm/yyyy HH:MM
                const parts = str.split(/[\/ :]/);
                const d = parts[0], m = parts[1], y = parts[2];
                let h = parts[3] || '00', min = parts[4] || '00';
                createdAt = new Date(`${y}-${m}-${d}T${h}:${min}:00`);
            } else if (/^\d{4}-\d{2}-\d{2}/.test(str)) {
                // yyyy-mm-dd atau yyyy-mm-dd HH:MM:SS
                createdAt = new Date(str.replace(' ', 'T'));
            } else if (/\d{1,2} [A-Za-z]+ \d{4}/.test(str)) {
                // Format "12 Agustus 2025, 10.00" (locale)
                const match = str.match(/(\d{1,2}) ([A-Za-z]+) (\d{4})(?:, (\d{2})\.(\d{2}))?/);
                if (match) {
                    const bulanIndo = ['Januari','Februari','Maret','April','Mei','Juni','Juli','Agustus','September','Oktober','November','Desember'];
                    const d = match[1], m = bulanIndo.indexOf(match[2]) + 1, y = match[3];
                    let h = match[4] || '00', min = match[5] || '00';
                    createdAt = new Date(`${y}-${m.toString().padStart(2,'0')}-${d.padStart(2,'0')}T${h}:${min}:00`);
                }
            } else if (/T/.test(str)) {
                createdAt = new Date(str);
            } else {
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
            window.location.href = `/edit-kpi-ctp/${dataId}`;
            hideContextMenu();
        });
        contextMenu.querySelector('[data-action="delete"]').addEventListener('click', function() {
            showDeleteConfirmation(dataId);
            hideContextMenu();
        });
    } else {
        // Jangan tampilkan menu sama sekali jika tidak ada tombol
        contextMenu.remove();
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

    // Update modal body dengan ID yang benar
    const deleteModalEl = document.getElementById('deleteConfirmationModal');
    const modalBody = deleteModalEl ? deleteModalEl.querySelector('.modal-body') : null;
    if (modalBody) {
        modalBody.innerHTML = `Apakah Anda yakin ingin menghapus data dengan ID <strong>${id}</strong>? Tindakan ini tidak dapat dibatalkan.`;
    }

    // Tampilkan modal
    deleteModal.show();
}

// --- Fungsi untuk Delete Data (akan berkomunikasi dengan backend) ---
async function deleteKpiData(id) {
    console.log(`Mengirim permintaan DELETE untuk ID: ${id}`);
    try {
        const response = await fetch(`/api/kpi_ctp/${id}`, {
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
            const response = await fetch(`/api/kpi_ctp/${id}`);
            if (!response.ok) {
                const contentType = response.headers.get("content-type");
                if (contentType && contentType.indexOf("text/html") !== -1) {
                    throw new Error('Endpoint /api/kpi_ctp/id not found or returned HTML, not JSON. Check your Flask route.');
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
            document.getElementById('num_plate_good').value = data.num_plate_good || '0';
            document.getElementById('num_plate_not_good').value = data.num_plate_not_good || '0';
            document.getElementById('not_good_reason').value = data.not_good_reason || '';
            document.getElementById('print_machine').value = data.print_machine || '';
            document.getElementById('remarks_job').value = data.remarks_job || '';
            document.getElementById('wo_number').value = data.wo_number || '';
            document.getElementById('mc_number').value = data.mc_number || '';
            document.getElementById('run_length_sheet').value = data.run_length_sheet || '';
            document.getElementById('item_name').value = data.item_name || '';
            document.getElementById('note').value = data.note || '';

            const rasterFields = [
                'cyan_25_percent', 'cyan_50_percent', 'cyan_75_percent',
                'magenta_25_percent', 'magenta_50_percent', 'magenta_75_percent',
                'yellow_25_percent', 'yellow_50_percent', 'yellow_75_percent',
                'black_25_percent', 'black_50_percent', 'black_75_percent',
                'x_25_percent', 'x_50_percent', 'x_75_percent',
                'z_25_percent', 'z_50_percent', 'z_75_percent',
                'u_25_percent', 'u_50_percent', 'u_75_percent',
                'v_25_percent', 'v_50_percent', 'v_75_percent'
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
        if (numPlateNotGoodInput && notGoodReasonGroup && notGoodReasonSelect) {
            if (parseInt(numPlateNotGoodInput.value) > 0) {
                notGoodReasonGroup.classList.remove('d-none');
                notGoodReasonSelect.setAttribute('required', 'true');
            } else {
                notGoodReasonGroup.classList.add('d-none');
                notGoodReasonSelect.removeAttribute('required');
                notGoodReasonSelect.value = ''; // Clear selection
            }
        }
    }

    if (numPlateNotGoodInput) {
        numPlateNotGoodInput.addEventListener('input', toggleNotGoodReason);
        toggleNotGoodReason();
    }

    // --- Handle form submission (untuk halaman input-kpi-ctp dan edit-kpi-ctp) ---
    if (ctpLogForm) {
        ctpLogForm.addEventListener('submit', async function(event) {
            event.preventDefault();

            const formData = new FormData(ctpLogForm);
            const data = Object.fromEntries(formData.entries());

            data.run_length_sheet = data.run_length_sheet ? parseInt(data.run_length_sheet) : null;
            data.num_plate_good = parseInt(data.num_plate_good);
            data.num_plate_not_good = parseInt(data.num_plate_not_good);
            data.processor_temperature = parseFloat(data.processor_temperature) || null;
            data.dwell_time = parseFloat(data.dwell_time) || null;

            const floatFields = [
                'cyan_25_percent', 'cyan_50_percent', 'cyan_75_percent',
                'magenta_25_percent', 'magenta_50_percent', 'magenta_75_percent',
                'yellow_25_percent', 'yellow_50_percent', 'yellow_75_percent',
                'black_25_percent', 'black_50_percent', 'black_75_percent',
                'x_25_percent', 'x_50_percent', 'x_75_percent',
                'z_25_percent', 'z_50_percent', 'z_75_percent',
                'u_25_percent', 'u_50_percent', 'u_75_percent',
                'v_25_percent', 'v_50_percent', 'v_75_percent'
            ];
            floatFields.forEach(field => {
                data[field] = data[field] ? parseFloat(data[field]) : null;
            });

            for (const key in data) {
                if (data[key] === '') {
                    data[key] = null;
                }
            }

            let url = '/submit-kpi';
            let method = 'POST';

            if (dataId) {
                url = `/api/kpi_ctp/${dataId}`;
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
                        toggleNotGoodReason();
                    }
                    if (dataId) {
                        setTimeout(() => {
                            window.location.href = '/tabel-kpi-ctp';
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
                // Ambil created_at dari cell tabel (kolom kedua terakhir)
                const createdAtCell = clickedRow.cells[clickedRow.cells.length - 2];
                const rowData = { created_at: createdAtCell ? createdAtCell.textContent : null };
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
    if (kpiTableBody && window.location.pathname.includes('/tabel-kpi-ctp')) {
        // Hapus toast 'Memuat data...' dari awal loadKpiData.
        // Sebaiknya, biarkan toast 'memuat data' jika memang ada proses loading yang signifikan.
        // Jika tidak, hilangkan saja.
        // Untuk sekarang, saya akan menghapus pemanggilan toast info di awal loadKpiData
        // dan tidak menambahkan jeda di sini, karena jeda lebih cocok setelah operasi.
        loadKpiData();
    }


});