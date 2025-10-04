document.addEventListener('DOMContentLoaded', function() {
    const tableBody = document.getElementById('usersTableBody');
    const paginationNav = document.getElementById('paginationNav');
    const searchInput = document.getElementById('searchInput');
    const clearSearchBtn = document.getElementById('clearSearch');
    const dataMessage = document.getElementById('dataMessage');
    const usersTable = document.getElementById('usersTable');
    const notificationToast = document.getElementById('notificationToast');
    const toast = new bootstrap.Toast(notificationToast, { delay: 3000 });

    // Function untuk menampilkan toast notification
    function showNotification(message, type = 'success') {
        const toastElement = document.getElementById('notificationToast');
        toastElement.className = 'toast align-items-center text-white border-0';
        
        // Set warna background berdasarkan tipe
        switch(type) {
            case 'success':
                toastElement.classList.add('bg-success');
                break;
            case 'error':
                toastElement.classList.add('bg-danger');
                break;
            case 'warning':
                toastElement.classList.add('bg-warning');
                break;
            case 'info':
                toastElement.classList.add('bg-info');
                break;
        }
        
        // Set pesan
        toastElement.querySelector('.toast-body').textContent = message;
        
        // Tampilkan toast
        const bsToast = new bootstrap.Toast(toastElement);
        bsToast.show();
    }

    let currentPage = 1;
    let totalPages = 1;
    let currentSearch = '';
    let currentSortColumn = 'name';
    let currentSortOrder = 'asc';

    function fetchData() {
        const search = searchInput ? searchInput.value.trim() : '';
        let url = `/get-users-data?page=${currentPage}` +
            `&search=${encodeURIComponent(search)}` +
            `&sort_by=${encodeURIComponent(currentSortColumn)}` +
            `&sort_order=${encodeURIComponent(currentSortOrder)}`;

        fetch(url)
            .then(res => res.json())
            .then(data => {
                if (data.data) {
                    renderTable(data.data);
                    renderPagination(data.page, data.pages);
                    totalPages = data.pages;
                } else {
                    tableBody.innerHTML = '<tr><td colspan="7" class="text-center">Tidak ada data yang ditemukan</td></tr>';
                    paginationNav.innerHTML = '';
                }
            })
            .catch(error => {
                console.error('Error:', error);
                tableBody.innerHTML = '<tr><td colspan="7" class="text-center text-danger">Terjadi kesalahan saat memuat data</td></tr>';
                paginationNav.innerHTML = '';
            });
    }


    function getRoleBadge(role) {
        const roleClasses = {
            admin: 'badge-admin',
            operator: 'badge-operator',
        };
        const badgeClass = roleClasses[role.toLowerCase()] || 'bg-secondary';
        return `<span class="badge ${badgeClass}">${role}</span>`;
    }

    function renderTable(rows) {
        tableBody.innerHTML = '';
        dataMessage.classList.add('d-none');
        
        if (!rows || !rows.length) {
            dataMessage.textContent = 'Tidak ada data user yang ditemukan.';
            dataMessage.classList.remove('d-none');
            dataMessage.classList.add('alert-info');
            return;
        }

        rows.forEach(row => {
            const tr = document.createElement('tr');
            
            // Role badge dengan warna yang sesuai
            const roleBadge = row.role === 'admin' ? 
                '<span class="badge badge-admin">Admin</span>' : 
                '<span class="badge badge-operator">Operator</span>';
            
            // Division badge dengan warna yang sesuai
            let divisionBadge = '-';
            if (row.division_name) {
                switch(row.division_name.toUpperCase()) {
                    case 'CTP':
                        divisionBadge = '<span class="badge badge-ctp">CTP</span>';
                        break;
                    case 'MOUNTING':
                        divisionBadge = '<span class="badge badge-mounting">MOUNTING</span>';
                        break;
                    case 'DESIGN':
                        divisionBadge = '<span class="badge badge-design">DESIGN</span>';
                        break;
                    case 'PRESS':
                        divisionBadge = '<span class="badge badge-press">PRESS</span>';
                        break;
                    case 'PDND':
                        divisionBadge = '<span class="badge badge-pdnd">PDND</span>';
                        break;
                    default:
                        divisionBadge = `<span class="badge bg-secondary">${row.division_name}</span>`;
                }
            }

            tr.innerHTML = `
                <td>${row.name || ''}</td>
                <td class="align-middle" style="height: 57px">${row.username || ''}</td>
                <td class="align-middle" style="height: 57px">${roleBadge}</td>
                <td class="align-middle" style="height: 57px">${divisionBadge}</td>
                <td class="align-middle" style="height: 57px">${row.grup || '-'}</td>
                <td class="align-middle text-end" style="height: 57px">
                    <div class="btn-group">
                        <button class="btn btn-xs btn-warning-clean px-2 py-1" onclick="editUser(${row.id})" data-bs-toggle="tooltip" title="Edit User">
                            <i class="fas fa-edit fa-sm"></i>
                        </button>
                        ${row.id !== currentUserId ? `
                        <button class="btn btn-xs btn-danger-clean px-2 py-1" onclick="deleteUser(${row.id})" data-bs-toggle="tooltip" title="Hapus User">
                            <i class="fas fa-trash fa-sm"></i>
                        </button>
                        ` : ''}
                    </div>
                </td>
            `;
            tableBody.appendChild(tr);
        });
        
        // Reinitialize tooltips
        const tooltips = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
        tooltips.map(function(tooltip) {
            return new bootstrap.Tooltip(tooltip);
        });
    }

    function renderPagination(page, pages) {
        paginationNav.innerHTML = '';
        if (pages <= 1) return;
        
        const prevLi = document.createElement('li');
        prevLi.className = `page-item${page === 1 ? ' disabled' : ''}`;
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
            li.className = `page-item${i === page ? ' active' : ''}`;
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

        const nextLi = document.createElement('li');
        nextLi.className = `page-item${page === pages ? ' disabled' : ''}`;
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

    // Event listeners for search
    searchInput.addEventListener('input', function() {
        currentPage = 1;
        fetchData();
    });

    clearSearchBtn.addEventListener('click', function() {
        searchInput.value = '';
        currentPage = 1;
        fetchData();
    });

    // Handle edit user
    window.editUser = function(userId) {
        // Show loading state
        const editModal = new bootstrap.Modal(document.getElementById('editUserModal'));
        editModal.show();
        
        fetch(`/admin/user/${userId}`)
            .then(response => {
                if (!response.ok) {
                    throw new Error('Network response was not ok');
                }
                return response.json();
            })
            .then(data => {
                // Safely set form values
                const fields = {
                    'edit_user_id': data.id,
                    'edit_name': data.name,
                    'edit_username': data.username,
                    'edit_role': data.role,
                    'edit_division_id': data.division_id || '',
                    'edit_grup': data.grup || ''
                };
                
                // Set values safely
                Object.keys(fields).forEach(id => {
                    const element = document.getElementById(id);
                    if (element) {
                        element.value = fields[id];
                    }
                });
                
                // Handle checkbox separately
                const activeCheckbox = document.getElementById('edit_is_active');
                if (activeCheckbox) {
                    activeCheckbox.checked = data.is_active;
                }
            })
            .catch(error => {
                console.error('Error:', error);
                alert('Gagal mengambil data user: ' + error.message);
                editModal.hide();
            });
    };

    // Handle delete user
    window.deleteUser = function(userId) {
        const deleteModal = new bootstrap.Modal(document.getElementById('deleteUserModal'));
        const deleteUserIdInput = document.getElementById('deleteUserId');
        if (deleteUserIdInput) {
            deleteUserIdInput.value = userId;
        }
        deleteModal.show();
    };

    // Handle delete form submission
    const deleteUserForm = document.getElementById('deleteUserForm');
    if (deleteUserForm) {
        deleteUserForm.addEventListener('submit', function(e) {
            e.preventDefault();
            const formData = new FormData(this);

            fetch(this.action, {
                method: 'POST',
                body: formData
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    showNotification('User berhasil dihapus', 'success');
                    const modal = bootstrap.Modal.getInstance(document.getElementById('deleteUserModal'));
                    modal.hide();
                    fetchData();
                } else {
                    showNotification(data.message || 'Gagal menghapus user', 'error');
                }
            })
            .catch(error => {
                showNotification('Terjadi kesalahan saat menghapus user', 'error');
            });
        });
    };

    // Handle form submissions
    const addUserForm = document.getElementById('addUserForm');
    if (addUserForm) {
        addUserForm.addEventListener('submit', function(e) {
            e.preventDefault();
            const formData = new FormData(this);

            fetch(this.action, {
                method: 'POST',
                body: formData
            })
            .then(response => response.json().then(data => ({ status: response.status, data })))
            .then(({ status, data }) => {
                if (data.success) {
                    showNotification(data.message, 'success');
                    const modal = bootstrap.Modal.getInstance(document.getElementById('addUserModal'));
                    modal.hide();
                    fetchData();
                    // Reset form
                    this.reset();
                } else {
                    showNotification(data.message, 'error');
                }
            })
            .catch(error => {
                showNotification('Terjadi kesalahan pada server', 'error');
            });
        });
    }

    const editUserForm = document.getElementById('editUserForm');
    if (editUserForm) {
        editUserForm.addEventListener('submit', function(e) {
            e.preventDefault();
            const formData = new FormData(this);

            fetch(this.action, {
                method: 'POST',
                body: formData
            })
            .then(response => response.json().then(data => ({ status: response.status, data })))
            .then(({ status, data }) => {
                if (data.success) {
                    showNotification(data.message, 'success');
                    const modal = bootstrap.Modal.getInstance(document.getElementById('editUserModal'));
                    modal.hide();
                    fetchData();
                } else {
                    showNotification(data.message, 'error');
                }
            })
            .catch(error => {
                showNotification('Terjadi kesalahan pada server', 'error');
            });
        });
    }

    // Sorting
    if (usersTable) {
        usersTable.querySelectorAll('th[data-column]').forEach(header => {
            header.style.cursor = 'pointer';
            header.addEventListener('click', function() {
                const column = this.getAttribute('data-column');
                // Mapping nama kolom untuk sort
                const columnMapping = {
                    'division': 'division_name'  // Map 'division' ke 'division_name'
                };
                const sortColumn = columnMapping[column] || column;
                
                if (sortColumn === currentSortColumn) {
                    currentSortOrder = currentSortOrder === 'asc' ? 'desc' : 'asc';
                } else {
                    currentSortColumn = sortColumn;
                    currentSortOrder = 'asc';
                }
                updateSortIcons();
                fetchData();
            });
        });

        function updateSortIcons() {
            usersTable.querySelectorAll('th[data-column] i').forEach(icon => {
                icon.classList.remove('fa-sort-up', 'fa-sort-down');
                icon.classList.add('fa-sort');
            });
            const currentHeaderIcon = usersTable.querySelector(`th[data-column="${currentSortColumn}"] i`);
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

    // Initial data fetch
    fetchData();
});
