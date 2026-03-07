// Work Queue JavaScript
let workQueueCurrentPage = 1;
let workQueueCurrentPerPage = 25;
let workQueueCurrentFilters = {};
let currentActiveStatus = 'active'; // Track current active tab

// Initialize on page load
document.addEventListener('DOMContentLoaded', function() {
    // Add event listeners for status tabs
    const statusTabs = document.querySelectorAll('.status-tab-btn');
    statusTabs.forEach(tab => {
        tab.addEventListener('click', function(e) {
            e.preventDefault();
            const status = this.getAttribute('data-status');
            setStatusTab(status);
            applyFilters();
        });
    });
    
    // Add event listeners
    const searchInput = document.getElementById('searchInput');
    const priorityFilter = document.getElementById('priorityFilter');
    const machineFilter = document.getElementById('machineFilter');
    
    if (searchInput) {
        // Create debounced version of applyFilters for search input
        const debouncedSearch = debounce(function() {
            applyFilters();
        }, 300); // 300ms delay
        
        // Add keyup event for real-time search
        searchInput.addEventListener('keyup', debouncedSearch);
        
        // Keep Enter key functionality as well
        searchInput.addEventListener('keypress', function(e) {
            if (e.key === 'Enter') {
                e.preventDefault(); // Prevent form submission
                applyFilters();
            }
        });
    }
    
    if (priorityFilter) {
        priorityFilter.addEventListener('change', applyFilters);
    }
    
    if (machineFilter) {
        machineFilter.addEventListener('change', applyFilters);
    }
    
    // Initialize page
    loadPrintMachines();
    // Set initial active tab visually
    setStatusTab('active');
    // Load data with Active filter
    applyFilters();
    updateStatistics();
});

// Set active status tab
function setStatusTab(status) {
    // Remove active class from all tabs
    document.querySelectorAll('.status-tab-btn').forEach(tab => {
        tab.classList.remove('active');
        tab.setAttribute('aria-selected', 'false');
    });
    
    // Add active class to current tab
    const activeTab = document.getElementById(`tab-${status}`);
    if (activeTab) {
        activeTab.classList.add('active');
        activeTab.setAttribute('aria-selected', 'true');
    }
    
    // Update current active status
    currentActiveStatus = status;
}

// Update tab counts
function updateTabCounts(activeCount, inProgressCount, pendingCount, completedCount) {
    const activeCountEl = document.getElementById('count-active');
    if (activeCountEl) {
        activeCountEl.textContent = activeCount;
        activeCountEl.style.display = activeCount > 0 ? 'inline-block' : 'none';
    }
    
    const inProgressCountEl = document.getElementById('count-in_progress');
    if (inProgressCountEl) {
        inProgressCountEl.textContent = inProgressCount;
        inProgressCountEl.style.display = inProgressCount > 0 ? 'inline-block' : 'none';
    }
    
    const pendingCountEl = document.getElementById('count-pending');
    if (pendingCountEl) {
        pendingCountEl.textContent = pendingCount;
        pendingCountEl.style.display = pendingCount > 0 ? 'inline-block' : 'none';
    }
    
    const completedCountEl = document.getElementById('count-completed');
    if (completedCountEl) {
        completedCountEl.textContent = completedCount;
        completedCountEl.style.display = completedCount > 0 ? 'inline-block' : 'none';
    }
}

// Context Menu Variables
let currentWorkOrderId = null;
let currentWorkOrderStatus = null;

// Show Context Menu
function showContextMenu(event, id, status) {
    event.preventDefault();
    
    currentWorkOrderId = id;
    currentWorkOrderStatus = status;
    
    const contextMenu = document.getElementById('contextMenu');
    if (!contextMenu) return;
    
    // Clear existing menu items
    contextMenu.innerHTML = '';
    
    // Add menu items based on status
    let menuHTML = '';
    
    // Always show View Details
    menuHTML += `
        <div class="context-menu-item" onclick="viewWorkOrder(${id})">
            <i class="fas fa-eye"></i>
            View Details
        </div>
    `;
    
    if (status === 'active') {
        menuHTML += `
            <div class="context-menu-item success" onclick="showStartJobModal(${id})">
                <i class="fas fa-play"></i>
                Start Job
            </div>
            <div class="context-menu-item warning" onclick="showPendingModal(${id})">
                <i class="fas fa-hourglass-half"></i>
                Start Downtime
            </div>
            <div class="context-menu-divider"></div>
            <div class="context-menu-item danger" onclick="showCancelModal(${id})">
                <i class="fas fa-times"></i>
                Cancel Job
            </div>
        `;
    } else if (status === 'pending') {
        menuHTML += `
            <div class="context-menu-item success" onclick="showEndDowntimeModal(${id})">
                <i class="fas fa-play"></i>
                End Downtime
            </div>
        `;
    } else if (status === 'in_progress') {
        menuHTML += `
            <div class="context-menu-item success" onclick="completeJob(${id})">
                <i class="fas fa-check"></i>
                Complete Job
            </div>
            <div class="context-menu-item warning" onclick="showPendingModal(${id})">
                <i class="fas fa-hourglass-half"></i>
                Start Downtime
            </div>
        `;
    } else if (status === 'completed') {
        menuHTML += `
            <div class="context-menu-item" onclick="printPrepressForm(${id})">
                <i class="fas fa-print"></i>
                Print Prepress Form
            </div>
            <div class="context-menu-item" onclick="printRasterPrepressForm(${id})">
                <i class="fas fa-print"></i>
                Print Raster Prepress Form
            </div>
        `;
    }
    
    contextMenu.innerHTML = menuHTML;
    
    // Position the menu
    const x = event.clientX;
    const y = event.clientY;
    
    // Make sure the menu doesn't go off screen
    const menuWidth = 200; // Approximate width
    const menuHeight = contextMenu.children.length * 40; // Approximate height
    
    let finalX = x;
    let finalY = y;
    
    if (x + menuWidth > window.innerWidth) {
        finalX = window.innerWidth - menuWidth - 10;
    }
    
    if (y + menuHeight > window.innerHeight) {
        finalY = window.innerHeight - menuHeight - 10;
    }
    
    contextMenu.style.left = finalX + 'px';
    contextMenu.style.top = finalY + 'px';
    
    // Show the menu with a slight delay for smooth animation
    setTimeout(() => {
        contextMenu.classList.add('show');
    }, 10);
}

// Hide Context Menu
function hideContextMenu() {
    const contextMenu = document.getElementById('contextMenu');
    if (contextMenu) {
        contextMenu.classList.remove('show');
    }
}

// Add click event listener to hide context menu when clicking elsewhere
document.addEventListener('click', function(event) {
    const contextMenu = document.getElementById('contextMenu');
    if (contextMenu && !contextMenu.contains(event.target)) {
        hideContextMenu();
    }
});

// Add context menu event listener to prevent default browser context menu
document.addEventListener('contextmenu', function(event) {
    if (event.target.closest('.work-order-row')) {
        event.preventDefault();
    }
});

// Handle row click - show details by default
function handleRowClick(event, id, status) {
    // If the click is on the context menu indicator, don't handle it here
    if (event.target.closest('.context-menu-indicator')) {
        return;
    }
    
    // Default action: view work order details
    viewWorkOrder(id);
}

// Show Start Job Modal
function showStartJobModal(id) {
    fetch(`/impact/api/work-queue/${id}`)
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            const item = data.data;
            
            // Store current work order ID for later use
            currentWorkOrderId = id;
            
            // Build combined WO numbers if merged
            let woDisplay = item.wo_number || '-';
            if (item.is_merged && item.merged_work_orders && item.merged_work_orders.length > 0) {
                const woNumbers = [item.primary_wo_number || item.wo_number];
                item.merged_work_orders.forEach(wo => {
                    woNumbers.push(wo.wo_number);
                });
                woDisplay = woNumbers.join(', ');
                console.log(`🔗 MERGE: Combined WO numbers: ${woDisplay}`);
            }
            
            // Populate modal with work order details
            document.getElementById('startJobWO').textContent = woDisplay;
            document.getElementById('startJobMachine').textContent = item.print_machine || '-';
            document.getElementById('startJobItem').textContent = item.item_name || '-';
            document.getElementById('startJobPriority').textContent = item.priority ? item.priority.toUpperCase() : '-';
            
            // Show modal
            const modal = new bootstrap.Modal(document.getElementById('startJobModal'));
            modal.show();
        } else {
            showAlert(data.error || 'Error loading work order details', 'danger');
        }
    })
    .catch(error => {
        console.error('Error:', error);
        showAlert('Error loading work order details. Please try again.', 'danger');
    });
}

// Confirm Start Job
function confirmStartJob() {
    if (!currentWorkOrderId) return;
    
    // Get current user name from window or session
    const userName = window.currentUserName || "{{ current_user.name }}";
    
    // Show loading
    showLoading();
    
    fetch(`/impact/api/work-queue/${currentWorkOrderId}/start-job`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-Requested-With': 'XMLHttpRequest'
        },
        body: JSON.stringify({
            started_by: userName
        })
    })
    .then(response => response.json())
    .then(data => {
        hideLoading();
        
        if (data.success) {
            showAlert('Job started successfully!', 'success');
            
            // Hide modal
            const modal = bootstrap.Modal.getInstance(document.getElementById('startJobModal'));
            modal.hide();
            
            // Reload work queue data to show updated status
            loadWorkQueueData(workQueueCurrentPage, workQueueCurrentFilters);
        } else {
            showAlert(data.error || 'Error starting job', 'danger');
        }
    })
    .catch(error => {
        hideLoading();
        console.error('Error:', error);
        showAlert('Error starting job. Please try again.', 'danger');
    });
}



// Complete Job
function completeJob(id) {
    // First, fetch the work queue item to get its MC number
    fetch(`/impact/api/work-queue/${id}`)
    .then(response => response.json())
    .then(data => {
        if (data.success && data.data) {
            const mcNumber = data.data.mc_number;
            
            // Fetch all work queue data to find related items with same MC number
            fetch('/impact/api/work-queue?per_page=1000')
            .then(response => response.json())
            .then(wqData => {
                if (wqData.success) {
                    // Find all work orders with same MC number that are in_progress
                    const relatedIds = wqData.data
                        .filter(item => item.mc_number === mcNumber && item.status === 'in_progress')
                        .map(item => item.id);
                    
                    console.log(`📋 Found ${relatedIds.length} related work order(s) with MC: ${mcNumber}`);
                    
                    // Build URL with all related IDs
                    if (relatedIds.length > 1) {
                        const idsParam = relatedIds.join(',');
                        window.location.href = `/impact/work-queue/create?work_queue_ids=${idsParam}&complete_job=true`;
                    } else {
                        // Single work order
                        window.location.href = `/impact/work-queue/create?work_queue_id=${id}&complete_job=true`;
                    }
                } else {
                    // Fallback to single ID
                    window.location.href = `/impact/work-queue/create?work_queue_id=${id}&complete_job=true`;
                }
            })
            .catch(error => {
                console.error('Error fetching work queue data:', error);
                // Fallback to single ID
                window.location.href = `/impact/work-queue/create?work_queue_id=${id}&complete_job=true`;
            });
        } else {
            // Fallback to single ID
            window.location.href = `/impact/work-queue/create?work_queue_id=${id}&complete_job=true`;
        }
    })
    .catch(error => {
        console.error('Error fetching work queue item:', error);
        // Fallback to single ID
        window.location.href = `/impact/work-queue/create?work_queue_id=${id}&complete_job=true`;
    });
}

// Load work queue data from server
function loadWorkQueueData(page = 1, filters = {}) {
    workQueueCurrentPage = page;
    workQueueCurrentFilters = filters;
    
    // Show loading
    showLoading();
    
    const params = new URLSearchParams({
        page: page,
        per_page: workQueueCurrentPerPage,
        ...filters
    });
    
    const url = `/impact/api/work-queue?${params}`;
    console.log('🌐 Fetching Work Queue URL:', url);
    
    fetch(url)
    .then(response => response.json())
    .then(data => {
        console.log('📊 Work Queue response received:', data);
        hideLoading();
        
        if (data.success) {
            console.log('✅ Work Queue data loaded successfully:', {
                dataCount: data.data.length,
                pagination: data.pagination
            });
            renderWorkQueueTable(data.data);
            renderWorkQueuePagination(data.pagination);
        } else {
            console.error('❌ Server error:', data.error);
            showAlert(data.error || 'Error loading work queue data', 'danger');
        }
    })
    .catch(error => {
        hideLoading();
        console.error('🚨 Network error:', error);
        showAlert('Error loading work queue data. Please try again.', 'danger');
    });
}

// Render work queue table
function renderWorkQueueTable(data) {
    console.log('📋 renderWorkQueueTable called with:', data.length, 'items');
    const tableBody = document.getElementById('workQueueTableBody');
    
    if (!tableBody) {
        console.error('❌ Table body element not found');
        return;
    }
    
    if (data.length === 0) {
        console.log('🚫 No work queue data to display');
        tableBody.innerHTML = `
            <tr>
                <td colspan="8" class="text-center py-4">
                    <i class="fas fa-inbox me-2"></i>
                    No work orders found
                </td>
            </tr>
        `;
        return;
    }
    
    console.log('✅ Rendering', data.length, 'rows of work queue data');
    
    tableBody.innerHTML = data.map(item => {
        // Build WO number display with merge indicator
        let woDisplay = item.wo_number;
        let mergeIndicator = '';
        
        if (item.is_merged && item.merged_count > 0) {
            mergeIndicator = `<span class="badge bg-info ms-2" title="Merged with ${item.merged_count} other work order(s)">
                <i class="fas fa-code-branch me-1"></i>Merged (${item.merged_count + 1})
            </span>`;
            console.log(`🔗 MERGE: Work Order ${item.id} has ${item.merged_count} merged items`);
        }
        
        return `
        <tr class="work-order-row" data-id="${item.id}" data-status="${item.status}"
            oncontextmenu="showContextMenu(event, ${item.id}, '${item.status}'); return false;"
            onclick="handleRowClick(event, ${item.id}, '${item.status}')">
            <td>
                <span class="machine-badge machine-${item.print_machine.toLowerCase()}">
                    ${item.print_machine}
                </span>
            </td>
            <td>
                <strong>${woDisplay}</strong>
                ${mergeIndicator}
            </td>
            <td>${item.mc_number}</td>
            <td>${item.item_name}</td>
            <td>
                <span class="priority-badge ${item.priority}">
                    ${item.priority.toUpperCase()}
                </span>
            </td>
            <td>${item.receiver_name}</td>
            <td>${formatDate(item.received_at)}</td>
            <td>
                <span class="status-badge ${item.status}">
                    ${item.status.replace(/_/g, ' ').toUpperCase()}
                </span>
            </td>
        </tr>
    `;
    }).join('');
}

// Render pagination
function renderWorkQueuePagination(pagination) {
    console.log('📄 renderWorkQueuePagination called with:', pagination);
    const paginationElement = document.getElementById('pagination');
    
    if (!paginationElement) {
        console.error('❌ Pagination element not found');
        return;
    }
    
    if (pagination.pages <= 1) {
        console.log('🚫 No pagination needed (pages <= 1)');
        paginationElement.innerHTML = '';
        return;
    }
    
    let paginationHTML = '';
    
    // Previous button
    if (pagination.has_prev) {
        paginationHTML += `
            <li class="page-item">
                <a class="page-link" href="#" onclick="event.preventDefault(); loadWorkQueueData(${pagination.page - 1}, workQueueCurrentFilters)">
                    <i class="fas fa-chevron-left"></i>
                </a>
            </li>
        `;
    }
    
    // Page numbers
    const startPage = Math.max(1, pagination.page - 2);
    const endPage = Math.min(pagination.pages, pagination.page + 2);
    
    console.log('🔢 Pagination range:', { startPage, endPage, totalPages: pagination.pages });
    
    if (startPage > 1) {
        paginationHTML += `
            <li class="page-item">
                <a class="page-link" href="#" onclick="event.preventDefault(); loadWorkQueueData(1, workQueueCurrentFilters)">1</a>
            </li>
        `;
        if (startPage > 2) {
            paginationHTML += `<li class="page-item disabled"><span class="page-link">...</span></li>`;
        }
    }
    
    for (let i = startPage; i <= endPage; i++) {
        paginationHTML += `
            <li class="page-item ${i === pagination.page ? 'active' : ''}">
                <a class="page-link" href="#" onclick="event.preventDefault(); loadWorkQueueData(${i}, workQueueCurrentFilters)">${i}</a>
            </li>
        `;
    }
    
    if (endPage < pagination.pages) {
        if (endPage < pagination.pages - 1) {
            paginationHTML += `<li class="page-item disabled"><span class="page-link">...</span></li>`;
        }
        paginationHTML += `
            <li class="page-item">
                <a class="page-link" href="#" onclick="event.preventDefault(); loadWorkQueueData(${pagination.pages}, workQueueCurrentFilters)">${pagination.pages}</a>
            </li>
        `;
    }
    
    // Next button
    if (pagination.has_next) {
        paginationHTML += `
            <li class="page-item">
                <a class="page-link" href="#" onclick="event.preventDefault(); loadWorkQueueData(${pagination.page + 1}, workQueueCurrentFilters)">
                    <i class="fas fa-chevron-right"></i>
                </a>
            </li>
        `;
    }
    
    console.log('🎯 Pagination HTML generated:', paginationHTML);
    paginationElement.innerHTML = paginationHTML;
}

// Load print machines for filter
function loadPrintMachines() {
    fetch('/impact/api/work-queue/machines')
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            const machineFilter = document.getElementById('machineFilter');
            const currentValue = machineFilter.value;
            
            machineFilter.innerHTML = '<option value="">All Machines</option>';
            data.data.forEach(machine => {
                machineFilter.innerHTML += `<option value="${machine}">${machine}</option>`;
            });
            
            // Restore previous selection
            machineFilter.value = currentValue;
        }
    })
    .catch(error => {
        console.error('Error loading machines:', error);
    });
}

// Update statistics for work queue
function updateStatistics() {
    fetch('/impact/api/work-queue?page=1&per_page=1000')
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            const records = data.data;
            
            // Total work orders
            const totalWorkOrdersEl = document.getElementById('totalWorkOrders');
            if (totalWorkOrdersEl) {
                totalWorkOrdersEl.textContent = data.pagination.total.toLocaleString();
            }
            
            // Active work orders
            const activeCount = records.filter(r => r.status === 'active').length;
            const activeWorkOrdersEl = document.getElementById('activeWorkOrders');
            if (activeWorkOrdersEl) {
                activeWorkOrdersEl.textContent = activeCount.toLocaleString();
            }
            
            // Pending work orders
            const pendingCount = records.filter(r => r.status === 'pending').length;
            const pendingWorkOrdersEl = document.getElementById('pendingWorkOrders');
            if (pendingWorkOrdersEl) {
                pendingWorkOrdersEl.textContent = pendingCount.toLocaleString();
            }
            
            // In Progress work orders
            const inProgressCount = records.filter(r => r.status === 'in_progress' || r.status === 'in-progress').length;
            const inProgressWorkOrdersEl = document.getElementById('inProgressWorkOrders');
            if (inProgressWorkOrdersEl) {
                inProgressWorkOrdersEl.textContent = inProgressCount.toLocaleString();
            }
            
            // Completed work orders
            const completedCount = records.filter(r => r.status === 'completed').length;
            
            // Update tab counts
            updateTabCounts(activeCount, inProgressCount, pendingCount, completedCount);
            
            // Total machines
            const machines = [...new Set(records.map(r => r.print_machine))];
            const totalMachinesEl = document.getElementById('totalMachines');
            if (totalMachinesEl) {
                totalMachinesEl.textContent = machines.length;
            }
            
            // Last update
            if (records.length > 0) {
                const lastUpdate = new Date(records[0].received_at || records[0].created_at);
                const lastUpdateEl = document.getElementById('lastUpdate');
                if (lastUpdateEl) {
                    lastUpdateEl.textContent = formatDate(lastUpdate);
                }
            }
        }
    })
    .catch(error => {
        console.error('Error updating statistics:', error);
    });
}

// Apply filters
function applyFilters() {
    const search = document.getElementById('searchInput').value;
    const status = currentActiveStatus; // Get status from active tab
    const priority = document.getElementById('priorityFilter').value;
    const machine = document.getElementById('machineFilter').value;
    
    console.log('🔍 applyFilters called:', { search, status, priority, machine });
    
    const filters = {};
    if (search) filters.search = search;
    if (status) filters.status = status;
    if (priority) filters.priority = priority;
    if (machine) filters.machine = machine;
    
    loadWorkQueueData(1, filters);
}

// View work order details
function viewWorkOrder(id) {
    fetch(`/impact/api/work-queue/${id}`)
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            const item = data.data;
            
            // Helper function to safely set element content
            const setElement = (id, content) => {
                const el = document.getElementById(id);
                if (el) el.textContent = content || '-';
            };
            
            const setElementHTML = (id, content) => {
                const el = document.getElementById(id);
                if (el) el.innerHTML = content || '-';
            };
            
            const setElementClass = (id, className) => {
                const el = document.getElementById(id);
                if (el) el.className = className;
            };
            
            const setElementStyle = (id, property, value) => {
                const el = document.getElementById(id);
                if (el) el.style[property] = value;
            };
            
            // Populate modal header
            // Build combined WO numbers if merged
            let woDisplay = item.wo_number || '-';
            if (item.is_merged && item.merged_work_orders && item.merged_work_orders.length > 0) {
                const woNumbers = [item.primary_wo_number || item.wo_number];
                item.merged_work_orders.forEach(wo => {
                    woNumbers.push(wo.wo_number);
                });
                woDisplay = woNumbers.join(', ');
                console.log(`🔗 MERGE: Combined WO numbers: ${woDisplay}`);
            }
            
            setElement('detailMachineBadge', item.print_machine || '-');
            setElementClass('detailMachineBadge', `machine-badge machine-${item.print_machine ? item.print_machine.toLowerCase() : ''}`);
            setElement('detailWO', woDisplay);
            setElement('detailMC', item.mc_number || '-');
            setElement('detailItem', item.item_name || '-');
            
            setElement('detailPriorityBadge', item.priority ? item.priority.toUpperCase() : '-');
            setElementClass('detailPriorityBadge', `priority-badge ${item.priority || ''}`);
            
            // Set status badge
            setElementHTML('detailStatus', `
                <span class="status-badge ${item.status}">
                    ${item.status ? item.status.replace(/_/g, ' ').toUpperCase() : '-'}
                </span>
            `);
            
            // Populate Timeline Tab
            const receivedInfo = `${formatDate(item.received_at) || '-'} • ${item.receiver_name || '-'}`;
            setElement('detailReceivedInfo', receivedInfo);
            
            // Start Job Timeline
            if (item.started_at) {
                const startedInfo = `${formatDate(item.started_at)} • ${item.started_by_name || '-'}`;
                setElement('detailStartedInfo', startedInfo);
                setElementStyle('startJobDot', 'background', '#0d6efd');
            } else {
                setElement('detailStartedInfo', '-');
            }
            
            // Completion Timeline
            if (item.completed_at) {
                const completedInfo = `${formatDate(item.completed_at)} • ${item.completed_by_name || '-'}`;
                setElement('detailCompletedInfo', completedInfo);
                setElementStyle('completedDot', 'background', '#28a745');
            } else {
                setElement('detailCompletedInfo', '-');
            }
            
            // Display downtime information in Downtime Tab
            const downtimeInfo = document.getElementById('downtimeInfo');
            if (downtimeInfo) {
                if (item.downtime_history && item.downtime_history.length > 0) {
                    let downtimeHTML = '<div class="table-responsive"><table class="table table-sm table-hover mb-0" id="downtimeTable">';
                    downtimeHTML += '<thead><tr><th>Reason</th><th>Started At</th><th>Ended At</th><th>Duration (hours)</th></tr></thead><tbody>';
                    
                    item.downtime_history.forEach(downtime => {
                        const reason = downtime.downtime_reason.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase());
                        const startedAt = formatDate(downtime.started_at);
                        const endedAt = downtime.ended_at ? formatDate(downtime.ended_at) : 'Still Active';
                        const duration = downtime.duration_hours || downtime.calculate_duration ? 
                            (downtime.duration_hours || downtime.calculate_duration()) : '-';
                        
                        // Format duration to 2 decimal places if it's a number
                        const formattedDuration = typeof duration === 'number' ? duration.toFixed(2) : duration;
                        
                        downtimeHTML += `
                            <tr>
                                <td><small class="fw-semibold">${reason}</small></td>
                                <td><small>${startedAt}</small></td>
                                <td><small>${endedAt}</small></td>
                                <td><small>${formattedDuration}</small></td>
                            </tr>
                        `;
                    });
                    
                    downtimeHTML += '</tbody></table></div>';
                    
                    // Format total downtime to 2 decimal places
                    const totalDowntime = item.total_downtime_hours || 0;
                    const formattedTotalDowntime = typeof totalDowntime === 'number' ? totalDowntime.toFixed(2) : totalDowntime;
                    
                    downtimeHTML += `<div class="mt-2 text-end"><small class="text-muted"><strong>Total Downtime:</strong> ${formattedTotalDowntime} hours</small></div>`;
                    downtimeInfo.innerHTML = downtimeHTML;
                } else {
                    downtimeInfo.innerHTML = '<p class="text-muted text-center py-3">No downtime records</p>';
                }
            }
            
            // Populate General Tab with work queue data and imposition job data
            populateGeneralTab(item);
            
            // Show modal
            const modal = new bootstrap.Modal(document.getElementById('detailModal'));
            modal.show();
        } else {
            showAlert(data.error || 'Error loading work order details', 'danger');
        }
    })
    .catch(error => {
        console.error('Error:', error);
        showAlert('Error loading work order details. Please try again.', 'danger');
    });
}

// Populate General Tab with work queue and imposition job data
function populateGeneralTab(workQueueItem) {
    const generalContent = document.getElementById('generalContent');
    if (!generalContent) return;
    
    let html = '';
    
    // Basic Information Section
    html += `
        <div class="detail-info-group">
            <div class="detail-info-title">
                <i class="fas fa-info-circle" style="color: #0d6efd;"></i> Basic Information
            </div>
            <div class="detail-info-grid">
                <div class="detail-info-row">
                    <div class="detail-info-label">Customer Name</div>
                    <div class="detail-info-value">${workQueueItem.customer_name || '-'}</div>
                </div>            
                <div class="detail-info-row">
                    <div class="detail-info-label">Work Order</div>
                    <div class="detail-info-value">${workQueueItem.wo_number || '-'}</div>
                </div>
                <div class="detail-info-row">
                    <div class="detail-info-label">MC Number</div>
                    <div class="detail-info-value">${workQueueItem.mc_number || '-'}</div>
                </div>
                <div class="detail-info-row">
                    <div class="detail-info-label">Item Name</div>
                    <div class="detail-info-value">${workQueueItem.item_name || '-'}</div>
                </div>
                <div class="detail-info-row">
                    <div class="detail-info-label">Print Machine</div>
                    <div class="detail-info-value">${workQueueItem.print_machine || '-'}</div>
                </div>
                <div class="detail-info-row">
                    <div class="detail-info-label">Calibration</div>
                    <div class="detail-info-value">${workQueueItem.calibration_name || '-'}</div>
                </div>
                <div class="detail-info-row">
                    <div class="detail-info-label">Remarks</div>
                    <div class="detail-info-value">${workQueueItem.remarks || '-'}</div>
                </div>
            </div>
        </div>
    `;
    
    // Item/Paper Information Section
    html += `
        <div class="detail-info-group">
            <div class="detail-info-title">
                <i class="fas fa-file-alt" style="color: #f39c12;"></i> Item & Paper Details
            </div>
            <div class="detail-info-grid">
                <div class="detail-info-row">
                    <div class="detail-info-label">Number of Ups</div>
                    <div class="detail-info-value">${workQueueItem.num_up || '-'}</div>
                </div>
                <div class="detail-info-row">
                    <div class="detail-info-label">Run Length (Sheet)</div>
                    <div class="detail-info-value">${formatNumber(workQueueItem.run_length_sheet) || '-'}</div>
                </div>
                <div class="detail-info-row">
                    <div class="detail-info-label">Paper Description</div>
                    <div class="detail-info-value">${workQueueItem.paper_desc || '-'}</div>
                </div>
                <div class="detail-info-row">
                    <div class="detail-info-label">Paper Type</div>
                    <div class="detail-info-value">${workQueueItem.paper_type || '-'}</div>
                </div>
            </div>
        </div>
    `;
    
    // People Information Section
    html += `
        <div class="detail-info-group">
            <div class="detail-info-title">
                <i class="fas fa-users" style="color: #e74c3c;"></i> People Involved
            </div>
            <div class="detail-info-grid">
                <div class="detail-info-row">
                    <div class="detail-info-label">Received By</div>
                    <div class="detail-info-value">${workQueueItem.receiver_name || '-'}</div>
                </div>
                <div class="detail-info-row">
                    <div class="detail-info-label">Started By</div>
                    <div class="detail-info-value">${workQueueItem.started_by_name || '-'}</div>
                </div>
                <div class="detail-info-row">
                    <div class="detail-info-label">Completed By</div>
                    <div class="detail-info-value">${workQueueItem.completed_by_name || '-'}</div>
                </div>
            </div>
        </div>
    `;
    
    // Notes Section if available
    if (workQueueItem.notes) {
        html += `
            <div class="detail-info-group">
                <div class="detail-info-title">
                    <i class="fas fa-sticky-note" style="color: #2ecc71;"></i> Notes
                </div>
                <div style="padding: 1rem; background: #f8f9fa; border-radius: 8px; border-left: 3px solid #2ecc71;">
                    <div class="detail-info-value">${workQueueItem.notes}</div>
                </div>
            </div>
        `;
    }
    
    generalContent.innerHTML = html || '<p class="text-muted text-center">No data available</p>';
}

// Show pending modal
function showPendingModal(id) {
    document.getElementById('pendingWorkOrderId').value = id;
    document.getElementById('pendingReason').value = '';
    document.getElementById('downtimeNotes').value = '';
    
    const modal = new bootstrap.Modal(document.getElementById('pendingModal'));
    modal.show();
}

// Show cancel modal
function showCancelModal(id) {
    document.getElementById('cancelWorkOrderId').value = id;
    document.getElementById('cancelReason').value = '';
    
    const modal = new bootstrap.Modal(document.getElementById('cancelModal'));
    modal.show();
}

// Edit work order
function editWorkOrder(id) {
    fetch(`/impact/api/work-queue/${id}`)
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            const item = data.data;
            
            // Populate form fields
            document.getElementById('editWorkOrderId').value = id;
            document.getElementById('editPriority').value = item.priority || 'normal';
            document.getElementById('editStatus').value = item.status || 'active';
            document.getElementById('editNotes').value = item.notes || '';
            
            // Show modal
            const modal = new bootstrap.Modal(document.getElementById('editModal'));
            modal.show();
        } else {
            showAlert(data.error || 'Error loading work order for editing', 'danger');
        }
    })
    .catch(error => {
        console.error('Error:', error);
        showAlert('Error loading work order for editing. Please try again.', 'danger');
    });
}

// Save work order changes
function saveWorkOrder() {
    const id = document.getElementById('editWorkOrderId').value;
    const priority = document.getElementById('editPriority').value;
    const status = document.getElementById('editStatus').value;
    const notes = document.getElementById('editNotes').value;
    
    if (!id) {
        showAlert('Invalid work order ID', 'danger');
        return;
    }
    
    const updateData = {
        priority: priority,
        status: status,
        notes: notes
    };
    
    fetch(`/impact/api/work-queue/${id}`, {
        method: 'PUT',
        headers: {
            'Content-Type': 'application/json',
            'X-Requested-With': 'XMLHttpRequest'
        },
        body: JSON.stringify(updateData)
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            showAlert('Work order updated successfully', 'success');
            
            // Close modal
            const modal = bootstrap.Modal.getInstance(document.getElementById('editModal'));
            modal.hide();
            
            // Reload data
            loadWorkQueueData(workQueueCurrentPage, workQueueCurrentFilters);
        } else {
            showAlert(data.error || 'Error updating work order', 'danger');
        }
    })
    .catch(error => {
        console.error('Error:', error);
        showAlert('Error updating work order. Please try again.', 'danger');
    });
}

// Cancel work order
function cancelWorkOrder() {
    const id = document.getElementById('cancelWorkOrderId').value;
    const reason = document.getElementById('cancelReason').value;
    
    if (!id) {
        showAlert('Invalid work order ID', 'danger');
        return;
    }
    
    if (!reason.trim()) {
        showAlert('Please provide a cancellation reason', 'warning');
        return;
    }
    
    const updateData = {
        status: 'cancelled',
        notes: reason
    };
    
    fetch(`/impact/api/work-queue/${id}`, {
        method: 'PUT',
        headers: {
            'Content-Type': 'application/json',
            'X-Requested-With': 'XMLHttpRequest'
        },
        body: JSON.stringify(updateData)
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            showAlert('Work order cancelled successfully', 'success');
            
            // Close modal
            const modal = bootstrap.Modal.getInstance(document.getElementById('cancelModal'));
            modal.hide();
            
            // Reload data
            loadWorkQueueData(workQueueCurrentPage, workQueueCurrentFilters);
        } else {
            showAlert(data.error || 'Error cancelling work order', 'danger');
        }
    })
    .catch(error => {
        console.error('Error:', error);
        showAlert('Error cancelling work order. Please try again.', 'danger');
    });
}

// Start downtime (set to pending)
function startDowntime() {
    const id = document.getElementById('pendingWorkOrderId').value;
    const reason = document.getElementById('pendingReason').value;
    const notes = document.getElementById('downtimeNotes').value;
    
    if (!id) {
        showAlert('Invalid work order ID', 'danger');
        return;
    }
    
    if (!reason) {
        showAlert('Please select a downtime reason', 'warning');
        return;
    }
    
    const updateData = {
        status: 'pending',
        downtime_reason: reason,
        downtime_notes: notes
    };
    
    fetch(`/impact/api/work-queue/${id}/downtime`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-Requested-With': 'XMLHttpRequest'
        },
        body: JSON.stringify(updateData)
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            showAlert('Downtime started successfully', 'success');
            
            // Close modal
            const modal = bootstrap.Modal.getInstance(document.getElementById('pendingModal'));
            modal.hide();
            
            // Reload data
            loadWorkQueueData(workQueueCurrentPage, workQueueCurrentFilters);
        } else {
            showAlert(data.error || 'Error starting downtime', 'danger');
        }
    })
    .catch(error => {
        console.error('Error:', error);
        showAlert('Error starting downtime. Please try again.', 'danger');
    });
}

// Show end downtime modal
function showEndDowntimeModal(id) {
    document.getElementById('endDowntimeWorkOrderId').value = id;
    
    // Fetch current work order data to get downtime info
    fetch(`/impact/api/work-queue/${id}`)
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            const item = data.data;
            
            // Display current downtime information
            if (item.current_downtime_reason) {
                const reason = item.current_downtime_reason.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase());
                document.getElementById('currentDowntimeReason').textContent = reason;
            } else {
                document.getElementById('currentDowntimeReason').textContent = '-';
            }
            
            if (item.current_downtime_duration_hours) {
                // Format current downtime duration to 2 decimal places
                const currentDuration = typeof item.current_downtime_duration_hours === 'number' ? 
                    item.current_downtime_duration_hours.toFixed(2) : item.current_downtime_duration_hours;
                document.getElementById('currentDowntimeDuration').textContent = `${currentDuration} hours`;
            } else {
                document.getElementById('currentDowntimeDuration').textContent = '-';
            }
            
            if (item.current_downtime_started_at) {
                document.getElementById('currentDowntimeStartedAt').textContent = formatDate(item.current_downtime_started_at);
            } else {
                document.getElementById('currentDowntimeStartedAt').textContent = '-';
            }
        } else {
            // Reset fields if error
            document.getElementById('currentDowntimeReason').textContent = '-';
            document.getElementById('currentDowntimeDuration').textContent = '-';
            document.getElementById('currentDowntimeStartedAt').textContent = '-';
        }
    })
    .catch(error => {
        console.error('Error fetching work order data:', error);
        // Reset fields on error
        document.getElementById('currentDowntimeReason').textContent = '-';
        document.getElementById('currentDowntimeDuration').textContent = '-';
        document.getElementById('currentDowntimeStartedAt').textContent = '-';
    });
    
    const modal = new bootstrap.Modal(document.getElementById('endDowntimeModal'));
    modal.show();
}

// End downtime and set work order as active
function endDowntime() {
    const id = document.getElementById('endDowntimeWorkOrderId').value;
    
    // Prevent multiple clicks
    const endButton = event.target;
    endButton.disabled = true;
    endButton.innerHTML = '<i class="fas fa-spinner fa-spin me-2"></i>Processing...';
    
    fetch(`/impact/api/work-queue/${id}/downtime/end`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-Requested-With': 'XMLHttpRequest'
        },
        body: JSON.stringify({})
    })
    .then(response => {
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        return response.json();
    })
    .then(data => {
        if (data.success) {
            showAlert('Downtime ended successfully', 'success');
            
            // Close modal
            const modal = bootstrap.Modal.getInstance(document.getElementById('endDowntimeModal'));
            modal.hide();
            
            // Reload data
            loadWorkQueueData(workQueueCurrentPage, workQueueCurrentFilters);
            updateStatistics();
        } else {
            showAlert(data.error || 'Error ending downtime', 'danger');
        }
    })
    .catch(error => {
        console.error('Error:', error);
        showAlert('Error ending downtime. Please try again.', 'danger');
    })
    .finally(() => {
        // Re-enable button
        endButton.disabled = false;
        endButton.innerHTML = '<i class="fas fa-play-circle me-2"></i>End Downtime & Set Active';
    });
}

// Create work order (navigate to create page)
function createWorkOrder(id) {
    console.log('🚀 Creating work order for ID:', id);
    
    // First check for duplicate MC numbers
    fetch(`/impact/api/work-queue/check-duplicate-mc/${id}`)
    .then(response => response.json())
    .then(data => {
        if (data.success && data.data.has_duplicates) {
            // Show duplicate MC modal
            showDuplicateMcModal(data.data, id);
        } else {
            // No duplicates, proceed normally
            window.location.href = `/impact/work-queue/create?work_queue_id=${id}`;
        }
    })
    .catch(error => {
        console.error('Error checking duplicate MC:', error);
        // Fallback to normal behavior
        window.location.href = `/impact/work-queue/create?work_queue_id=${id}`;
    });
}

// Show duplicate MC modal
function showDuplicateMcModal(duplicateData, originalId) {
    console.log('🔍 Showing duplicate MC modal:', duplicateData);
    
    // Set MC number in modal
    const mcNumberElement = document.getElementById('duplicateMcNumber');
    if (mcNumberElement) {
        mcNumberElement.textContent = duplicateData.mc_number;
    }
    
    // Populate duplicate work orders table (without headers)
    const duplicateListElement = document.getElementById('duplicateWorkOrdersList');
    if (duplicateListElement) {
        duplicateListElement.innerHTML = '';
        
        // Add original work order to list
        const allWorkOrders = [
            { ...duplicateData.original, is_original: true },
            ...duplicateData.duplicates
        ];
        
        allWorkOrders.forEach(item => {
            const row = document.createElement('tr');
            row.innerHTML = `
                <td>
                    <div class="form-check">
                        <input class="form-check-input duplicate-work-order-checkbox" type="checkbox"
                               value="${item.id}" ${item.is_original ? 'checked' : ''}
                               data-wo-number="${item.wo_number || ''}"
                               data-mc-number="${item.mc_number || ''}">
                        <label class="form-check-label"></label>
                    </div>
                </td>
                <td><strong>${item.wo_number || '-'}</strong></td>
                <td>${item.mc_number || '-'}</td>
                <td>${item.item_name || '-'}</td>
                <td>
                    <span class="machine-badge machine-${(item.print_machine || '').toLowerCase()}">
                        ${item.print_machine || '-'}
                    </span>
                </td>
                <td>
                    <span class="priority-badge ${item.priority || 'normal'}">
                        ${(item.priority || 'normal').toUpperCase()}
                    </span>
                </td>
                <td>${item.receiver_name || '-'}</td>
            `;
            duplicateListElement.appendChild(row);
        });
    }
    
    // Show modal
    const modal = new bootstrap.Modal(document.getElementById('duplicateMcModal'));
    modal.show();
}

// Create job with selected work orders (legacy function for backward compatibility)
function createJobWithSelectedWorkOrders() {
    createSelectedWorkOrders();
}

// Create job with only selected work orders
function createSelectedWorkOrders() {
    const selectedCheckboxes = document.querySelectorAll('.duplicate-work-order-checkbox:checked');
    const selectedIds = Array.from(selectedCheckboxes).map(cb => cb.value);
    
    if (selectedIds.length === 0) {
        showAlert('Please select at least one work order', 'warning');
        return;
    }
    
    console.log('📋 Selected work orders:', selectedIds);
    
    // Hide modal
    const modal = bootstrap.Modal.getInstance(document.getElementById('duplicateMcModal'));
    if (modal) {
        modal.hide();
    }
    
    // Navigate to create page with selected work order IDs
    const workQueueIdsParam = selectedIds.join(',');
    window.location.href = `/impact/work-queue/create?work_queue_ids=${workQueueIdsParam}`;
}

// Create job with all work orders
function createAllWorkOrders() {
    const allCheckboxes = document.querySelectorAll('.duplicate-work-order-checkbox');
    const allIds = Array.from(allCheckboxes).map(cb => cb.value);
    
    if (allIds.length === 0) {
        showAlert('No work orders available', 'warning');
        return;
    }
    
    console.log('📋 All work orders:', allIds);
    
    // Hide modal
    const modal = bootstrap.Modal.getInstance(document.getElementById('duplicateMcModal'));
    if (modal) {
        modal.hide();
    }
    
    // Navigate to create page with all work order IDs
    const workQueueIdsParam = allIds.join(',');
    window.location.href = `/impact/work-queue/create?work_queue_ids=${workQueueIdsParam}`;
}

// Format date
function formatDate(dateString) {
    if (!dateString) return '-';
    
    const date = new Date(dateString);
    return date.toLocaleDateString('id-ID', {
        day: '2-digit',
        month: 'short',
        year: 'numeric',
        hour: '2-digit',
        minute: '2-digit'
    });
}

// Debounce function to limit API calls
function debounce(func, wait) {
    let timeout;
    return function(...args) {
        const context = this;
        clearTimeout(timeout);
        timeout = setTimeout(() => func.apply(context, args), wait);
    };
}

// Show loading overlay
function showLoading() {
    const loadingOverlay = document.getElementById('loadingOverlay');
    if (loadingOverlay) {
        loadingOverlay.style.display = 'flex';
    }
}

// Hide loading overlay
function hideLoading() {
    const loadingOverlay = document.getElementById('loadingOverlay');
    if (loadingOverlay) {
        loadingOverlay.style.display = 'none';
    }
}

// Show alert message as toast notification
function showAlert(message, type) {
    // Create toast container if it doesn't exist
    let toastContainer = document.getElementById('toast-container');
    if (!toastContainer) {
        toastContainer = document.createElement('div');
        toastContainer.id = 'toast-container';
        toastContainer.style.cssText = `
            position: fixed;
            top: 20px;
            right: 20px;
            z-index: 9999;
            max-width: 350px;
        `;
        document.body.appendChild(toastContainer);
    }
    
    const toastId = 'toast-' + Date.now();
    const bgClass = type === 'success' ? 'success' : (type === 'warning' ? 'warning' : (type === 'info' ? 'info' : 'danger'));
    const iconClass = type === 'success' ? 'check-circle' : 'exclamation-triangle';
    
    const toastHTML = `
        <div id="${toastId}" class="toast align-items-center text-white bg-${bgClass} border-0" role="alert" aria-live="assertive" aria-atomic="true">
            <div class="d-flex">
                <div class="toast-body">
                    <i class="fas fa-${iconClass} me-2"></i>
                    ${message}
                </div>
                <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast" aria-label="Close"></button>
            </div>
        </div>
    `;
    
    toastContainer.insertAdjacentHTML('beforeend', toastHTML);
    
    const toastElement = document.getElementById(toastId);
    if (typeof bootstrap !== 'undefined') {
        const toast = new bootstrap.Toast(toastElement, {
            autohide: true,
            delay: 5000
        });
        toast.show();
    }
    
    toastElement.addEventListener('hidden.bs.toast', function () {
        toastElement.remove();
    });
}

// Format number with thousand separator
function formatNumber(num) {
    if (!num) return '0';
    return parseFloat(num).toLocaleString('id-ID');
}

// Print Prepress Form for completed work order
function printPrepressForm(workQueueId) {
    const url = `/impact/api/print-prepress-form/${workQueueId}`;
    console.log(`🖨️ Opening print form: ${url}`);
    window.open(url, '_blank');
    hideContextMenu();
}

// Print Raster Prepress Form for completed work order
function printRasterPrepressForm(workQueueId) {
    const url = `/impact/api/print-raster-prepress-form/${workQueueId}`;
    console.log(`🖨️ Opening raster prepress form: ${url}`);
    window.open(url, '_blank');
    hideContextMenu();
}