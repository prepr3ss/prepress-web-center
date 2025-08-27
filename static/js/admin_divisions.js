document.addEventListener('DOMContentLoaded', function() {
    const tableBody = document.getElementById('divisionsTableBody');
    const paginationNav = document.getElementById('paginationNav');
    const searchInput = document.getElementById('searchInput');
    const clearSearchBtn = document.getElementById('clearSearch');
    const dataMessage = document.getElementById('dataMessage');
    const divisionsTable = document.getElementById('divisionsTable');
    const notificationToast = document.getElementById('notificationToast');
    const toast = new bootstrap.Toast(notificationToast, { delay: 3000 });

    // Function to display toast notifications
    function showNotification(message, type = 'success') {
        const toastElement = document.getElementById('notificationToast');
        toastElement.className = 'toast align-items-center text-white border-0';
        
        // Set background color based on type
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
        
        // Set message
        toastElement.querySelector('.toast-body').textContent = message;
        
        // Show toast
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
        let url = `/get-divisions-data?page=${currentPage}` +
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
                    tableBody.innerHTML = '<tr><td colspan="4" class="text-center">No divisions found</td></tr>';
                    paginationNav.innerHTML = '';
                }
            })
            .catch(error => {
                console.error('Error:', error);
                tableBody.innerHTML = '<tr><td colspan="4" class="text-center text-danger">Error loading data</td></tr>';
                paginationNav.innerHTML = '';
            });
    }

    function renderTable(rows) {
        tableBody.innerHTML = '';
        dataMessage.classList.add('d-none');
        
        if (!rows || !rows.length) {
            dataMessage.textContent = 'No divisions found.';
            dataMessage.classList.remove('d-none');
            dataMessage.classList.add('alert-info');
            return;
        }

        rows.forEach(row => {
            const tr = document.createElement('tr');
            const date = new Date(row.created_at);
            const months = ['Januari', 'Februari', 'Maret', 'April', 'Mei', 'Juni', 'Juli', 'Agustus', 'September', 'Oktober', 'November', 'Desember'];
            const createdAt = `${date.getDate()} ${months[date.getMonth()]} ${date.getFullYear()}, pukul ${String(date.getHours()).padStart(2, '0')}:${String(date.getMinutes()).padStart(2, '0')}:${String(date.getSeconds()).padStart(2, '0')}`;
            
            tr.innerHTML = `
                <td>${row.name || ''}</td>
                <td>${row.description || ''}</td>
                <td>${createdAt}</td>
                <td class="text-end">
                    <div class="btn-group">
                        <button class="btn btn-xs btn-warning-clean px-2 py-1" onclick="editDivision(${row.id})" data-bs-toggle="tooltip" title="Edit Division">
                            <i class="fas fa-edit fa-sm"></i>
                        </button>
                        <button class="btn btn-xs btn-danger-clean px-2 py-1" onclick="deleteDivision(${row.id})" data-bs-toggle="tooltip" title="Delete Division">
                            <i class="fas fa-trash fa-sm"></i>
                        </button>
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

    // Handle edit division
    window.editDivision = function(divisionId) {
        const editModal = new bootstrap.Modal(document.getElementById('editDivisionModal'));
        editModal.show();
        
        fetch(`/admin/division/${divisionId}`)
            .then(response => {
                if (!response.ok) {
                    throw new Error('Network response was not ok');
                }
                return response.json();
            })
            .then(data => {
                document.getElementById('edit_division_id').value = data.id;
                document.getElementById('edit_name').value = data.name;
                document.getElementById('edit_description').value = data.description;
            })
            .catch(error => {
                console.error('Error:', error);
                showNotification('Failed to load division data', 'error');
                editModal.hide();
            });
    };

    // Handle delete division
    window.deleteDivision = function(divisionId) {
        const deleteModal = new bootstrap.Modal(document.getElementById('deleteDivisionModal'));
        const deleteDivisionIdInput = document.getElementById('deleteDivisionId');
        if (deleteDivisionIdInput) {
            deleteDivisionIdInput.value = divisionId;
        }
        deleteModal.show();
    };

    // Handle delete form submission
    const deleteDivisionForm = document.getElementById('deleteDivisionForm');
    if (deleteDivisionForm) {
        deleteDivisionForm.addEventListener('submit', function(e) {
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
                    const modal = bootstrap.Modal.getInstance(document.getElementById('deleteDivisionModal'));
                    modal.hide();
                    fetchData();
                } else {
                    showNotification(data.message, 'error');
                }
            })
            .catch(error => {
                showNotification('Server error occurred', 'error');
            });
        });
    }

    // Handle form submissions
    const addDivisionForm = document.getElementById('addDivisionForm');
    if (addDivisionForm) {
        addDivisionForm.addEventListener('submit', function(e) {
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
                    const modal = bootstrap.Modal.getInstance(document.getElementById('addDivisionModal'));
                    modal.hide();
                    fetchData();
                    // Reset form
                    this.reset();
                } else {
                    showNotification(data.message, 'error');
                }
            })
            .catch(error => {
                showNotification('Server error occurred', 'error');
            });
        });
    }

    const editDivisionForm = document.getElementById('editDivisionForm');
    if (editDivisionForm) {
        editDivisionForm.addEventListener('submit', function(e) {
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
                    const modal = bootstrap.Modal.getInstance(document.getElementById('editDivisionModal'));
                    modal.hide();
                    fetchData();
                } else {
                    showNotification(data.message, 'error');
                }
            })
            .catch(error => {
                showNotification('Server error occurred', 'error');
            });
        });
    }

    // Sorting
    if (divisionsTable) {
        divisionsTable.querySelectorAll('th[data-column]').forEach(header => {
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
            divisionsTable.querySelectorAll('th[data-column] i').forEach(icon => {
                icon.classList.remove('fa-sort-up', 'fa-sort-down');
                icon.classList.add('fa-sort');
            });
            const currentHeaderIcon = divisionsTable.querySelector(`th[data-column="${currentSortColumn}"] i`);
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
