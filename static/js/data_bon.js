document.addEventListener('DOMContentLoaded', function() {
    const tableBody = document.getElementById('bonTableBody');
    const paginationNav = document.getElementById('paginationNav');
    const searchInput = document.getElementById('searchInput');
    const clearSearchBtn = document.getElementById('clearSearch');
    const filterStatus = document.getElementById('filterStatus');
    const filterMesin = document.getElementById('filterMesin');
    const filterRemarks = document.getElementById('filterRemarks');
    const dataMessage = document.getElementById('dataMessage');
    const bonDataTable = document.getElementById('bonDataTable');

    let currentPage = 1;
    let totalPages = 1;
    let currentSearch = '';
    let currentSortColumn = 'id';
    let currentSortOrder = 'desc';

    function fetchData() {
        const search = searchInput.value.trim();
        const status = filterStatus.value;
        const mesin = filterMesin.value;
        const remarks = filterRemarks ? filterRemarks.value : '';
        let url = `/get-bon-data?page=${currentPage}` +
            `&search=${encodeURIComponent(search)}` +
            `&sort_by=${encodeURIComponent(currentSortColumn)}` +
            `&sort_order=${encodeURIComponent(currentSortOrder)}`;
        if (status) url += `&status=${encodeURIComponent(status)}`;
        if (mesin) url += `&mesin=${encodeURIComponent(mesin)}`;
        if (remarks) url += `&remarks=${encodeURIComponent(remarks)}`;

        fetch(url)
            .then(res => res.json())
            .then(data => {
                renderTable(data.data);
                renderPagination(data.page, data.pages);
                totalPages = data.pages;
            });
    }

    // Function untuk mendapatkan badge status menggunakan badge system
    function getStatusBadge(status) {
        if (window.BadgeSystem) {
            // Tentukan division berdasarkan status
            let division = 'default';
            if (status === 'menunggu_adjustment' || status === 'proses_adjustment') {
                division = 'mounting';
            } else if (status === 'proses_ctp' || status === 'proses_plate' || status === 'antar_plate' || status === 'selesai') {
                division = 'ctp';
            }
            
            const statusInfo = window.BadgeSystem.getStatusInfo(status, division);
            if (statusInfo) {
                return `<span class="badge status-badge ${statusInfo.class}" data-status="${status}">${statusInfo.label}</span>`;
            }
        }
        
        // Fallback jika badge system tidak tersedia
        const statusMap = {
            menunggu_adjustment: { label: "Menunggu Adjustment", badge: "badge-menunggu" },
            proses_adjustment:   { label: "Proses Adjustment",   badge: "badge-proses" },
            proses_ctp:          { label: "Proses CTP",          badge: "badge-menunggu-plate" },
            selesai:             { label: "Selesai",             badge: "badge-selesai" }
        };
        
        const statusInfo = statusMap[status] || { label: status || '', badge: 'badge-menunggu' };
        return `<span class="badge status-badge ${statusInfo.badge}">${statusInfo.label}</span>`;
    }

function formatTanggalIndo(tanggalStr) {
    if (!tanggalStr) return '';
    // Asumsi format input: dd/mm/yyyy atau yyyy-mm-dd
    let d, m, y;
    if (/^\d{2}\/\d{2}\/\d{4}$/.test(tanggalStr)) {
        // Format dd/mm/yyyy
        [d, m, y] = tanggalStr.split('/');
    } else if (/^\d{4}-\d{2}-\d{2}/.test(tanggalStr)) {
        // Format yyyy-mm-dd
        [y, m, d] = tanggalStr.split('-');
    } else {
        return tanggalStr;
    }
    const bulanIndo = [
        '', 'Januari', 'Februari', 'Maret', 'April', 'Mei', 'Juni',
        'Juli', 'Agustus', 'September', 'Oktober', 'November', 'Desember'
    ];
    // Pastikan m tidak ada leading zero
    m = parseInt(m, 10);
    return `${parseInt(d, 10)} ${bulanIndo[m]} ${y}`;
}

function renderTable(rows) {
    tableBody.innerHTML = '';
    dataMessage.classList.add('d-none');
    if (!rows.length) {
        dataMessage.textContent = 'Tidak ada data yang ditemukan.';
        dataMessage.classList.remove('d-none');
        dataMessage.classList.add('alert-info');
        return;
    }
    rows.forEach(row => {
        const statusBadge = getStatusBadge(row.status);
        const tr = document.createElement('tr');
        tr.innerHTML = `
            <td>${row.id || ''}</td>
            <td>${formatTanggalIndo(row.tanggal) || ''}</td>
            <td>${row.machine_off_at ? row.machine_off_at.slice(11, 16) : ''}</td>
            <td>${statusBadge}</td>            
            <td>${row.mesin_cetak || ''}</td>
            <td>${row.mc_number || ''}</td>
            <td><a href="/detail-bon/${row.id}" class="text-decoration-none text-primary fw-bold">${row.item_name || ''}</a></td>
            <td>${row.note || ''}</td>
            <td>${row.remarks || ''}</td>
            <td>
                <a href="/detail-bon/${row.id}" class="btn btn-sm btn-outline-primary">
                    <i class="fas fa-eye me-1"></i>Detail
                </a>
            </td>
        `;
        // Menu klik kanan
        tr.addEventListener('contextmenu', function(e) {
            e.preventDefault();
            showContextMenu(tr, e.clientX, e.clientY, row);
        });
        tableBody.appendChild(tr);
    });
}


// Menu klik kanan dengan posisi presisi mengikuti scroll (mengadopsi kpi_ctp_handler.js)
function showContextMenu(rowElement, x, y, row) {
    hideContextMenu();

    const contextMenu = document.createElement('div');
    contextMenu.id = 'customContextMenu';
    contextMenu.classList.add('list-group', 'shadow-sm');
    contextMenu.style.position = 'absolute';

    // Perbaiki posisi agar mengikuti scroll
    let left = x + window.scrollX;
    let top = y + window.scrollY;

    // --- Opsional: Cegah menu keluar dari layar ---
    const menuWidth = 180; // atau sesuai minWidth menu Anda
    const menuHeight = row.status === 'proses_ctp' ? 90 : 50; // kira-kira tinggi menu (1/2 tombol)
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

    contextMenu.innerHTML = `
        <button type="button" class="list-group-item list-group-item-action" data-action="detail">
            <i class="fas fa-search me-2"></i> Detail Bon
        </button>
        ${row.status === 'proses_ctp' ? `
        <button type="button" class="list-group-item list-group-item-action text-danger" data-action="cancel">
            <i class="fas fa-ban me-2"></i> Cancel Bon
        </button>
        ` : ''}
    `;

    document.body.appendChild(contextMenu);

    contextMenu.querySelector('[data-action="detail"]').addEventListener('click', function() {
        window.location.href = `/detail-bon/${row.id}`;
        hideContextMenu();
    });

    const cancelBtn = contextMenu.querySelector('[data-action="cancel"]');
    if (cancelBtn) {
        cancelBtn.addEventListener('click', function() {
            if (confirm('Yakin ingin membatalkan bon ini?')) {
                // Lakukan API call cancel
                alert('Bon dibatalkan: ' + row.id);
            }
            hideContextMenu();
        });
    }

    // Tutup menu jika klik di luar, scroll, atau tekan Escape
    document.addEventListener('click', function handler(e) {
        if (contextMenu && !contextMenu.contains(e.target)) {
            hideContextMenu();
            document.removeEventListener('click', handler);
        }
    });
    document.addEventListener('scroll', hideContextMenu);
    document.addEventListener('keydown', function handler(e) {
        if (e.key === "Escape") {
            hideContextMenu();
            document.removeEventListener('keydown', handler);
        }
    });
}

function hideContextMenu() {
    let menu = document.getElementById('customContextMenu');
    if (menu && document.body.contains(menu)) {
        document.body.removeChild(menu);
    }
}

    function renderPagination(page, pages) {
        paginationNav.innerHTML = '';
        if (pages <= 1) return;
        // Tombol Previous
        const prevLi = document.createElement('li');
        prevLi.className = 'page-item' + (page === 1 ? ' disabled' : '');
        const prevA = document.createElement('a');
        prevA.className = 'page-link';
        prevA.href = '#';
        prevA.textContent = '«';
        prevA.addEventListener('click', function(e) {
            e.preventDefault();
            if (currentPage > 1) {
                currentPage--;
                fetchData();
            }
        });
        prevLi.appendChild(prevA);
        paginationNav.appendChild(prevLi);

        // Sliding window: maksimal 5 page number
        let startPage = Math.max(1, page - 2);
        let endPage = Math.min(pages, page + 2);
        if (page <= 3) {
            endPage = Math.min(5, pages);
        }
        if (page >= pages - 2) {
            startPage = Math.max(1, pages - 4);
        }
        for (let i = startPage; i <= endPage; i++) {
            const li = document.createElement('li');
            li.className = 'page-item' + (i === page ? ' active' : '');
            const a = document.createElement('a');
            a.className = 'page-link';
            a.href = '#';
            a.textContent = i;
            a.addEventListener('click', function(e) {
                e.preventDefault();
                if (currentPage !== i) {
                    currentPage = i;
                    fetchData();
                }
            });
            li.appendChild(a);
            paginationNav.appendChild(li);
        }

        // Tombol Next
        const nextLi = document.createElement('li');
        nextLi.className = 'page-item' + (page === pages ? ' disabled' : '');
        const nextA = document.createElement('a');
        nextA.className = 'page-link';
        nextA.href = '#';
        nextA.textContent = '»';
        nextA.addEventListener('click', function(e) {
            e.preventDefault();
            if (currentPage < pages) {
                currentPage++;
                fetchData();
            }
        });
        nextLi.appendChild(nextA);
        paginationNav.appendChild(nextLi);
    }

    // Event listeners
    searchInput.addEventListener('input', function() {
        currentPage = 1;
        fetchData();
    });
    clearSearchBtn.addEventListener('click', function() {
        searchInput.value = '';
        currentPage = 1;
        fetchData();
    });
    filterStatus.addEventListener('change', function() {
        currentPage = 1;
        fetchData();
    });
    filterMesin.addEventListener('change', function() {
        currentPage = 1;
        fetchData();
    });
    if (filterRemarks) {
        filterRemarks.addEventListener('change', function() {
            currentPage = 1;
            fetchData();
        });
    }

    // Sorting
    if (bonDataTable) {
        bonDataTable.querySelectorAll('th[data-column]').forEach(header => {
            header.style.cursor = 'pointer';
            header.addEventListener('click', function() {
                const column = this.getAttribute('data-column');
                if (column === currentSortColumn) {
                    currentSortOrder = currentSortOrder === 'asc' ? 'desc' : 'asc';
                } else {
                    currentSortColumn = column;
                    currentSortOrder = 'asc';
                }
                updateSortIcons();
                fetchData();
            });
        });

        function updateSortIcons() {
            bonDataTable.querySelectorAll('th[data-column] i').forEach(icon => {
                icon.classList.remove('fa-sort-up', 'fa-sort-down');
                icon.classList.add('fa-sort');
            });
            const currentHeaderIcon = bonDataTable.querySelector(`th[data-column="${currentSortColumn}"] i`);
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

    fetchData();
});
