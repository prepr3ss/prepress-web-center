// Cloudsphere Task Management System JavaScript
let currentPage = 1;
let currentFilters = {
    search: '',
    status: '',
    priority: '',
    sample_type: '',
    user_id: ''
};

// Initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    console.log('DEBUG: DOM loaded, setting up event listeners');
    loadDashboardStats();
    loadTaskCategories();
    loadUsers();
    loadJobs();
    
    // Setup event listeners
    setupEventListeners();
});

// Setup event listeners
function setupEventListeners() {
    // Show/hide user filter based on user role
    setupUserFilterVisibility();
    
    // Load users for user filter (only for admin)
    loadUsersForFilter();
    
    // Search input - make sure element exists before adding listener
    const searchInput = document.getElementById('searchInput');
    if (searchInput) {
        searchInput.addEventListener('input', debounce(function(event) {
            console.log('DEBUG: Search input changed, event:', event);
            console.log('DEBUG: Search input changed, this:', this);
            console.log('DEBUG: Search input changed, value:', event.target.value);
            currentFilters.search = event.target.value;
            currentPage = 1;
            loadJobs();
        }, 500));
        console.log('DEBUG: Search input event listener attached');
    } else {
        console.error('DEBUG: searchInput element not found!');
    }
    
    // Filter dropdowns - make sure elements exist before adding listeners
    const statusFilter = document.getElementById('statusFilter');
    if (statusFilter) {
        statusFilter.addEventListener('change', function() {
            console.log('DEBUG: Status filter changed, value:', this.value);
            currentFilters.status = this.value;
            currentPage = 1;
            loadJobs();
        });
        console.log('DEBUG: Status filter event listener attached');
    } else {
        console.error('DEBUG: statusFilter element not found!');
    }
    
    const priorityFilter = document.getElementById('priorityFilter');
    if (priorityFilter) {
        priorityFilter.addEventListener('change', function() {
            console.log('DEBUG: Priority filter changed, value:', this.value);
            currentFilters.priority = this.value;
            currentPage = 1;
            loadJobs();
        });
        console.log('DEBUG: Priority filter event listener attached');
    } else {
        console.error('DEBUG: priorityFilter element not found!');
    }
    
    const sampleTypeFilter = document.getElementById('sampleTypeFilter');
    if (sampleTypeFilter) {
        sampleTypeFilter.addEventListener('change', function() {
            console.log('DEBUG: Sample type filter changed, value:', this.value);
            currentFilters.sample_type = this.value;
            currentPage = 1;
            loadJobs();
        });
        console.log('DEBUG: Sample type filter event listener attached');
    } else {
        console.error('DEBUG: sampleTypeFilter element not found!');
    }
    
    // User filter - only for admin users
    const userFilter = document.getElementById('userFilter');
    if (userFilter) {
        userFilter.addEventListener('change', function() {
            console.log('DEBUG: User filter changed, value:', this.value);
            currentFilters.user_id = this.value;
            currentPage = 1;
            loadJobs();
        });
        console.log('DEBUG: User filter event listener attached');
    } else {
        console.log('DEBUG: userFilter element not found (hidden for non-admin users)');
    }
    
    // No task category change listener since we removed the category field
}

// Clear all filters
function clearFilters() {
    document.getElementById('searchInput').value = '';
    document.getElementById('statusFilter').value = '';
    document.getElementById('priorityFilter').value = '';
    document.getElementById('sampleTypeFilter').value = '';
    
    // Clear user filter if it exists
    const userFilter = document.getElementById('userFilter');
    if (userFilter) {
        userFilter.value = '';
    }
    
    currentFilters = {
        search: '',
        status: '',
        priority: '',
        sample_type: '',
        user_id: ''
    };
    
    currentPage = 1;
    loadJobs();
}

// Load dashboard statistics
async function loadDashboardStats() {
    try {
        const response = await fetch('/impact/cloudsphere/api/dashboard-stats');
        
        if (!response.ok) {
            console.error(`HTTP error! status: ${response.status}`);
            return;
        }
        
        const result = await response.json();
        
        if (result.success) {
            const data = result.data;
           
            // Create statistics cards first
            createStatsCards(data);
            
            // Display final values immediately, then animate only if needed
            displayFinalValues(data);
        } else {
            console.error('API returned error:', result.error || 'Unknown error');
        }
    } catch (error) {
        console.error('Error loading dashboard stats:', error);
    }
}

// Create statistics cards
function createStatsCards(data) {
    const container = document.getElementById('statsContainer');
    if (!container) {
        console.error('Stats container not found');
        return;
    }
    
    container.innerHTML = `
        <div class="stat-card total animate__animated animate__fadeInUp">
            <div class="stat-value" id="totalJobs">${data.total_jobs || 0}</div>
            <div class="stat-label">Total Jobs</div>
        </div>
        <div class="stat-card in-progress animate__animated animate__fadeInUp">
            <div class="stat-value" id="inProgressJobs">${data.in_progress || 0}</div>
            <div class="stat-label">In Progress</div>
        </div>
        <div class="stat-card pending animate__animated animate__fadeInUp">
            <div class="stat-value" id="pendingApprovalJobs">${data.pending_approval || 0}</div>
            <div class="stat-label">Pending Approval</div>
        </div>
        <div class="stat-card completed animate__animated animate__fadeInUp">
            <div class="stat-value" id="completedJobs">${data.completed || 0}</div>
            <div class="stat-label">Completed</div>
        </div>
        <div class="stat-card rejected animate__animated animate__fadeInUp">
            <div class="stat-value" id="rejectedJobs">${data.rejected || 0}</div>
            <div class="stat-label">Rejected</div>
        </div>
    `;
}

// Display final values immediately without animation
function displayFinalValues(data) {
    const elements = {
        'totalJobs': data.total_jobs || 0,
        'inProgressJobs': data.in_progress || 0,
        'pendingApprovalJobs': data.pending_approval || 0,
        'completedJobs': data.completed || 0,
        'rejectedJobs': data.rejected || 0
    };
    
    Object.keys(elements).forEach(elementId => {
        const element = document.getElementById(elementId);
        if (element) {
            element.textContent = elements[elementId].toLocaleString();
        }
    });
}

// Animate number counting only when values change
function animateNumber(elementId, targetValue) {
    const element = document.getElementById(elementId);
    
    // Check if element exists before proceeding
    if (!element) {
        console.warn(`Element with ID '${elementId}' not found. Skipping animation.`);
        return;
    }
    
    // Get current value from element text
    const currentValueText = element.textContent.replace(/,/g, '');
    const currentValue = parseInt(currentValueText) || 0;
    
    // If values are the same, don't animate
    if (currentValue === targetValue) {
        return;
    }
    
    const startValue = currentValue;
    const duration = 800; // Shorter duration for better UX
    const startTime = performance.now();
    
    function updateNumber(currentTime) {
        const elapsed = currentTime - startTime;
        const progress = Math.min(elapsed / duration, 1);
        
        // Use easing function for smoother animation
        const easeOutQuart = 1 - Math.pow(1 - progress, 4);
        const currentValue = Math.floor(startValue + (targetValue - startValue) * easeOutQuart);
        
        // Format number with commas for better readability
        element.textContent = currentValue.toLocaleString('en-US');
        
        if (progress < 1) {
            requestAnimationFrame(updateNumber);
        } else {
            // Ensure final value is properly formatted
            element.textContent = targetValue.toLocaleString('en-US');
        }
    }
    
    requestAnimationFrame(updateNumber);
}

// Load task categories and display all tasks grouped by category
async function loadTaskCategories() {
    try {
        const response = await fetch('/impact/cloudsphere/api/task-categories');
        
        if (!response.ok) {
            console.error(`HTTP error! status: ${response.status}`);
            return;
        }
        
        const result = await response.json();
        
        if (result.success) {
            displayAllTasksByCategory(result.data);
        } else {
            console.error('API returned error:', result.error || 'Unknown error');
        }
    } catch (error) {
        console.error('Error loading task categories:', error);
    }
}

// Display all tasks grouped by category with "Select All" checkboxes
function displayAllTasksByCategory(categories) {
    const container = document.getElementById('tasksContainer');
    if (!container) {
        console.warn('Tasks container not found');
        return;
    }
    
    container.innerHTML = '';
    
    // Define the order of categories as requested: Blank, RoHS, Mastercard, Production
    const categoryOrder = ['Blank', 'Mastercard', 'RoHS Regular ICB', 'RoHS Ribbon', 'Polymer Ribbon'];
    
    // Sort categories according to the defined order
    const sortedCategories = categories.sort((a, b) => {
        const categoryNameA = a.category_name || a.name;
        const categoryNameB = b.category_name || b.name;
        const indexA = categoryOrder.indexOf(categoryNameA);
        const indexB = categoryOrder.indexOf(categoryNameB);
        
        // If category is not in the predefined order, put it at the end
        if (indexA === -1 && indexB === -1) return categoryNameA.localeCompare(categoryNameB);
        if (indexA === -1) return 1;
        if (indexB === -1) return -1;
        
        return indexA - indexB;
    });
    
    // Create a grid layout for better organization
    const rowDiv = document.createElement('div');
    rowDiv.className = 'row';
    
    sortedCategories.forEach((category, index) => {
        const categoryDiv = document.createElement('div');
        categoryDiv.className = 'col-md-6 mb-4';
        
        // Add category header with color coding
        let categoryColor = '';
        const categoryName = category.category_name || category.name;
        switch(categoryName) {
            case 'Blank': categoryColor = 'border-primary'; break;
            case 'Mastercard': categoryColor = 'border-success'; break;
            case 'RoHS Regular ICB': categoryColor = 'border-warning'; break;
            case 'RoHS Ribbon': categoryColor = 'border-info'; break;
            case 'Polymer Ribbon': categoryColor = 'border-info'; break;
            default: categoryColor = 'border-secondary';
        }
        
        categoryDiv.innerHTML = `
            <div class="card h-100 border ${categoryColor}">
                <div class="card-header bg-light">
                    <div class="d-flex align-items-center">
                        <input type="checkbox" class="form-check-input me-2" id="select_all_${category.id}" onchange="toggleCategoryTasks(${category.id})">
                        <label class="form-check-label fw-bold mb-0" for="select_all_${category.id}">
                            <i class="fas fa-tasks me-1"></i> Select All: ${categoryName}
                        </label>
                    </div>
                </div>
                <div class="card-body p-2" style="max-height: 400px; overflow-y: auto;">
                    <div class="task-list" id="tasks_${category.id}">
                        ${category.tasks.map(task => `
                            <div class="form-check mb-2">
                                <input class="form-check-input task-checkbox" type="checkbox" value="${task.id}" id="task_${task.id}" data-category="${category.id}">
                                <label class="form-check-label" for="task_${task.id}" title="${task.task_name || task.name}">
                                    ${task.task_name || task.name}
                                </label>
                            </div>
                        `).join('')}
                    </div>
                </div>
            </div>
        `;
        
        rowDiv.appendChild(categoryDiv);
    });
    
    container.innerHTML = '';
    container.appendChild(rowDiv);
    
    // Add a "Select All Tasks from All Categories" option at the top
    
    // Add event listeners to individual task checkboxes to update the category "Select All" checkbox
    document.querySelectorAll('.task-checkbox').forEach(checkbox => {
        checkbox.addEventListener('change', function() {
            // Update the category "Select All" checkbox
            const categoryId = this.getAttribute('data-category');
            const categorySelectAll = document.getElementById(`select_all_${categoryId}`);
            const categoryTasks = document.querySelectorAll(`#tasks_${categoryId} .task-checkbox`);
            
            // Check if all tasks in this category are selected
            let allCategoryTasksSelected = true;
            categoryTasks.forEach(task => {
                if (!task.checked) {
                    allCategoryTasksSelected = false;
                }
            });
            
            categorySelectAll.checked = allCategoryTasksSelected;
        });
    });
}

// Toggle all tasks in a category
function toggleCategoryTasks(categoryId) {
    const selectAllCheckbox = document.getElementById(`select_all_${categoryId}`);
    const categoryTasks = document.querySelectorAll(`#tasks_${categoryId} .task-checkbox`);
    
    categoryTasks.forEach(checkbox => {
        checkbox.checked = selectAllCheckbox.checked;
    });
}

// Load users for PIC selection (R&D users only)
async function loadUsers() {
    try {
        // Load R&D users (division_id = 6)
        const response = await fetch('/impact/cloudsphere/api/users?division_id=6');
        
        if (!response.ok) {
            console.error(`HTTP error! status: ${response.status}`);
            return;
        }
        
        const result = await response.json();
        
        const select = document.getElementById('pic_id');
        if (select) {
            select.innerHTML = '<option value="">Select PIC</option>';
            
            if (result.success && result.data) {
                result.data.forEach(user => {
                    const option = document.createElement('option');
                    option.value = user.id;
                    option.textContent = user.name;
                    select.appendChild(option);
                });
            }
        } else {
            // Fallback: try to get current user info
            if (window.currentUserRole) {
                select.innerHTML = '<option value="">Current User</option>';
            }
        }
    } catch (error) {
        console.error('Error loading users:', error);
        // Fallback
        const select = document.getElementById('pic_id');
        if (select && window.currentUserRole) {
            select.innerHTML = '<option value="">Current User</option>';
        }
    }
}

// Setup user filter visibility based on user role
function setupUserFilterVisibility() {
    const userFilterContainer = document.getElementById('userFilterContainer');
    const searchContainer = document.getElementById('searchContainer');
    
    if (window.currentUserRole && window.currentUserRole.toLowerCase() !== 'admin') {
        // Hide user filter for non-admin users
        if (userFilterContainer) {
            userFilterContainer.style.display = 'none';
        }
        // Change search container from col-md-4 to col-md-6
        if (searchContainer) {
            searchContainer.className = 'col-md-6';
        }
    } else {
        // Show user filter for admin users
        if (userFilterContainer) {
            userFilterContainer.style.display = 'block';
        }
        // Keep search container as col-md-4 for admin
        if (searchContainer) {
            searchContainer.className = 'col-md-4';
        }
    }
}

// Load users for user filter (only for admin)
async function loadUsersForFilter() {
    const userFilter = document.getElementById('userFilter');
    if (!userFilter) return;
    
    try {
        // Load R&D users (division_id = 6) for filtering
        const response = await fetch('/impact/cloudsphere/api/users?division_id=6');
        
        if (!response.ok) {
            console.error(`HTTP error! status: ${response.status}`);
            return;
        }
        
        const result = await response.json();
        
        if (result.success && result.data) {
            userFilter.innerHTML = '<option value="">Semua Users</option>';
            
            result.data.forEach(user => {
                const option = document.createElement('option');
                option.value = user.id;
                option.textContent = user.name;
                userFilter.appendChild(option);
            });
        }
    } catch (error) {
        console.error('Error loading users for filter:', error);
    }
}

// Load jobs with filters and pagination
async function loadJobs() {
    showLoading(true);
    
    try {
        // Build query parameters manually to ensure proper encoding
        let queryParams = `page=${currentPage}&per_page=12`;
        
        // Add filters only if they have values
        if (currentFilters.search && currentFilters.search.trim() !== '') {
            queryParams += `&search=${encodeURIComponent(currentFilters.search.trim())}`;
        }
        if (currentFilters.status && currentFilters.status.trim() !== '') {
            queryParams += `&status=${encodeURIComponent(currentFilters.status.trim())}`;
        }
        if (currentFilters.priority && currentFilters.priority.trim() !== '') {
            queryParams += `&priority=${encodeURIComponent(currentFilters.priority.trim())}`;
        }
        if (currentFilters.sample_type && currentFilters.sample_type.trim() !== '') {
            queryParams += `&sample_type=${encodeURIComponent(currentFilters.sample_type.trim())}`;
        }
        if (currentFilters.user_id && currentFilters.user_id.trim() !== '') {
            queryParams += `&user_id=${encodeURIComponent(currentFilters.user_id.trim())}`;
        }
        
        console.log('DEBUG: Query params:', queryParams);
        console.log('DEBUG: Current filters:', currentFilters);
        console.log('DEBUG: Search term:', currentFilters.search);
        console.log('DEBUG: Full URL:', `/impact/cloudsphere/api/jobs?${queryParams}`);
        
        const response = await fetch(`/impact/cloudsphere/api/jobs?${queryParams}`);
        
        if (!response.ok) {
            console.error(`HTTP error! status: ${response.status}`);
            showError(`Server error: ${response.status}`);
            return;
        }
        
        const result = await response.json();
        console.log('DEBUG: API response:', result);
        console.log('DEBUG: Response success:', result.success);
        console.log('DEBUG: Response data length:', result.data ? result.data.length : 0);
        console.log('DEBUG: Response pagination:', result.pagination);
        
        if (result.success) {
            console.log('DEBUG: Displaying jobs:', result.data);
            if (result.data && result.data.length > 0) {
                console.log('DEBUG: First job details:', result.data[0]);
                console.log('DEBUG: Job fields - ID:', result.data[0].id,
                          'job_id:', result.data[0].job_id,
                          'item_name:', result.data[0].item_name,
                          'pic_name:', result.data[0].pic_name);
            }
            displayJobs(result.data);
            displayPagination(result.pagination);
            showEmptyState(result.data.length === 0);
        } else {
            console.error('API returned error:', result.error || 'Unknown error');
            showError(result.error || 'Failed to load jobs');
        }
    } catch (error) {
        console.error('Error loading jobs:', error);
        showError('Failed to load jobs. Please try again.');
    } finally {
        showLoading(false);
    }
}

// Display jobs as cards
function displayJobs(jobs) {
    const container = document.getElementById('jobsContainer');
    container.innerHTML = '';
    
    const grid = document.createElement('div');
    grid.className = 'jobs-grid';
    
    jobs.forEach(job => {
        const card = document.createElement('div');
        card.className = 'job-card-new';
        card.setAttribute('role', 'article');
        card.setAttribute('aria-label', `Job: ${job.item_name}, PIC: ${job.pic_name || 'Unassigned'}, Priority: ${job.priority_level}`);
        card.innerHTML = createNewJobCard(job);
        
        grid.appendChild(card);
    });
    
    container.appendChild(grid);
}

// Create job card HTML with new minimalist design
function createNewJobCard(job) {
    const deadlineDate = new Date(job.deadline);
    const currentDate = new Date();
    const daysRemaining = Math.ceil((deadlineDate - currentDate) / (1000 * 60 * 60 * 24));
    const isOverdue = daysRemaining < 0 && ['In Progress', 'Pending Approval'].includes(job.status);
    
    // Determine priority class for progress bar
    let progressClass = 'medium';
    if (job.completion_percentage >= 75) progressClass = 'high';
    else if (job.completion_percentage < 50) progressClass = 'low';
    
    // Create SVG icons for sample types
    const getSampleIcon = (sampleType) => {
        switch(sampleType.toLowerCase()) {
            case 'blank':
                return `
                    <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                        <path d="M14 2H6C4.89543 2 4 2.89543 4 4V20C4 21.1046 4.89543 22 6 22H18C19.1046 22 20 21.1046 20 20V8L14 2Z" stroke="#1976D2" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                        <path d="M14 2V8H20" stroke="#1976D2" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                        <path d="M8 13H16" stroke="#1976D2" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                        <path d="M8 17H12" stroke="#1976D2" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                    </svg>
                `;
            case 'rohs regular icb':
                return `
                    <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                        <path d="M12 2L15.09 8.26L22 9.27L17 14.14L18.18 21.02L12 17.77L5.82 21.02L7 14.14L2 9.27L8.91 8.26L12 2Z" fill="#4CAF50"/>
                        <path d="M9 11L11 13L15 9" stroke="white" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                    </svg>
                `;
            case 'rohs ribbon':
                return `
                    <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                        <path d="M12 2L15.09 8.26L22 9.27L17 14.14L18.18 21.02L12 17.77L5.82 21.02L7 14.14L2 9.27L8.91 8.26L12 2Z" fill="#FF9800"/>
                        <path d="M9 11L11 13L15 9" stroke="white" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                        <path d="M6 6L18 6" stroke="#FF9800" stroke-width="2" stroke-linecap="round"/>
                        <path d="M6 18L18 18" stroke="#FF9800" stroke-width="2" stroke-linecap="round"/>
                    </svg>
                `;
            case 'polymer ribbon':
                return `
                    <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                        <path d="M12 2L15.09 8.26L22 9.27L17 14.14L18.18 21.02L12 17.77L5.82 21.02L7 14.14L2 9.27L8.91 8.26L12 2Z" fill="#2196F3"/>
                        <path d="M9 11L11 13L15 9" stroke="white" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                        <path d="M6 6L18 6" stroke="#2196F3" stroke-width="2" stroke-linecap="round"/>
                        <path d="M6 18L18 18" stroke="#2196F3" stroke-width="2" stroke-linecap="round"/>
                        <circle cx="12" cy="12" r="8" stroke="#2196F3" stroke-width="2" stroke-dasharray="2 2"/>
                    </svg>
                `;
            case 'mastercard':
                return `
                    <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                        <rect x="3" y="6" width="18" height="12" rx="2" stroke="#9C27B0" stroke-width="2"/>
                        <circle cx="9" cy="12" r="3" fill="#9C27B0"/>
                        <circle cx="15" cy="12" r="3" fill="#9C27B0"/>
                        <path d="M12 9C10.3431 9 9 10.3431 9 12C9 13.6569 10.3431 15 12 15C13.6569 15 15 13.6569 15 12C15 10.3431 13.6569 9 12 9Z" fill="#9C27B0"/>
                    </svg>
                `;
            default:
                return `
                    <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                        <rect x="3" y="4" width="18" height="16" rx="2" stroke="#757575" stroke-width="2"/>
                        <path d="M7 8H17M7 12H17M7 16H13" stroke="#757575" stroke-width="2" stroke-linecap="round"/>
                    </svg>
                `;
        }
    };
    
    const sampleTypeClass = job.sample_type.toLowerCase().replace(/\s+/g, '-');
    const priorityClass = job.priority_level.toLowerCase();
    
    return `
        <div class="sample-icon ${sampleTypeClass}">
            ${getSampleIcon(job.sample_type)}
        </div>
        
        <div class="sample-type-label ${sampleTypeClass}">
            ${job.sample_type}
        </div>
        
        <div class="priority-badge-new ${priorityClass}">
            ${job.priority_level}
        </div>
        
        <div class="deadline-display ${isOverdue ? 'overdue' : ''}">
            ${isOverdue ? `Overdue` : daysRemaining === 0 ? `Today` : daysRemaining === 1 ? `Tomorrow` : `${daysRemaining} Days Left`}
        </div>
        
        <div class="card-content">
            <div class="pic-name">
                <span class="sr-only">Person in Charge:</span>
                ${job.pic_name || 'Unassigned'}
            </div>
            
            <div class="item-name">
                <span class="sr-only">Item Name:</span>
                ${job.item_name}
            </div>
            
            ${job.completion_percentage !== undefined ? `
                <div class="progress-container">
                    <div class="progress-track">
                        <div class="progress-fill-new ${progressClass}" style="width: ${job.completion_percentage}%"></div>
                    </div>
                    <div class="progress-text">${job.completion_percentage}%</div>
                </div>
            ` : ''}
            
            <div class="card-actions">
                <button class="view-button" onclick="event.stopPropagation(); viewJobDetail(${job.id})" aria-label="View job details for ${job.item_name}">
                    View
                </button>
                ${window.currentUserRole && window.currentUserRole.toLowerCase() === 'admin' ? `
                    <button class="edit-button" onclick="event.stopPropagation(); editJob(${job.id})" aria-label="Edit job ${job.item_name}">
                        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                            <path d="M11 4H4C3.46957 4 2.96086 4.21071 2.58579 4.58579C2.21071 4.96086 2 5.46957 2 6V20C2 20.5304 2.21071 21.0391 2.58579 21.4142C2.96086 21.7893 3.46957 22 4 22H18C18.5304 22 19.0391 21.7893 19.4142 21.4142C19.7893 21.0391 20 20.5304 20 20V13" stroke="#667eea" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                            <path d="M18.5 2.50001C18.8978 2.10219 19.4374 1.87869 20 1.87869C20.5626 1.87869 21.1022 2.10219 21.5 2.50001C21.8978 2.89784 22.1213 3.4374 22.1213 4.00001C22.1213 4.56262 21.8978 5.10219 21.5 5.50001L12 15L8 16L9 12L18.5 2.50001Z" stroke="#667eea" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                        </svg>
                    </button>
                    <button class="delete-button" onclick="event.stopPropagation(); deleteJob(${job.id})" aria-label="Delete job ${job.item_name}">
                        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                            <path d="M3 6H5H21" stroke="#dc2626" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                            <path d="M8 6V4C8 3.46957 8.21071 2.96086 8.58579 2.58579C8.96086 2.21071 9.46957 2 10 2H14C14.5304 2 15.0391 2.21071 15.4142 2.58579C15.7893 2.96086 16 3.46957 16 4V6M19 6V20C19 20.5304 18.7893 21.0391 18.4142 21.4142C18.0391 21.7893 17.5304 22 17 22H7C6.46957 22 5.96086 21.7893 5.58579 21.4142C5.21071 21.0391 5 20.5304 5 20V6H19Z" stroke="#dc2626" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                        </svg>
                    </button>
                ` : ''}
            </div>
        </div>
    `;
}

// Display pagination
function displayPagination(pagination) {
    const container = document.getElementById('paginationContainer');
    const paginationList = document.getElementById('pagination');
    
    if (pagination.pages <= 1) {
        container.style.display = 'none';
        return;
    }
    
    container.style.display = 'block';
    paginationList.innerHTML = '';
    
    // Previous button
    const prevLi = document.createElement('li');
    prevLi.className = `page-item ${pagination.page <= 1 ? 'disabled' : ''}`;
    prevLi.innerHTML = `
        <a class="page-link" href="#" onclick="changePage(${pagination.page - 1})" ${pagination.page <= 1 ? 'tabindex="-1"' : ''}>
            <i class="fas fa-chevron-left"></i>
        </a>
    `;
    paginationList.appendChild(prevLi);
    
    // Page numbers
    const startPage = Math.max(1, pagination.page - 2);
    const endPage = Math.min(pagination.pages, pagination.page + 2);
    
    for (let i = startPage; i <= endPage; i++) {
        const li = document.createElement('li');
        li.className = `page-item ${i === pagination.page ? 'active' : ''}`;
        li.innerHTML = `
            <a class="page-link" href="#" onclick="changePage(${i})">${i}</a>
        `;
        paginationList.appendChild(li);
    }
    
    // Next button
    const nextLi = document.createElement('li');
    nextLi.className = `page-item ${pagination.page >= pagination.pages ? 'disabled' : ''}`;
    nextLi.innerHTML = `
        <a class="page-link" href="#" onclick="changePage(${pagination.page + 1})" ${pagination.page >= pagination.pages ? 'tabindex="-1"' : ''}>
            <i class="fas fa-chevron-right"></i>
        </a>
    `;
    paginationList.appendChild(nextLi);
}

// Change page
function changePage(page) {
    if (page < 1) return;
    currentPage = page;
    loadJobs();
}

// Show/hide loading spinner
function showLoading(show) {
    const spinner = document.getElementById('loadingSpinner');
    const container = document.getElementById('jobsContainer');
    const emptyState = document.getElementById('emptyState');
    
    if (show) {
        spinner.style.display = 'block';
        container.style.display = 'none';
        emptyState.style.display = 'none';
    } else {
        spinner.style.display = 'none';
        container.style.display = 'block';
    }
}

// Show empty state
function showEmptyState(show) {
    const emptyState = document.getElementById('emptyState');
    const container = document.getElementById('jobsContainer');
    
    if (show) {
        emptyState.style.display = 'block';
        container.style.display = 'none';
    } else {
        emptyState.style.display = 'none';
        container.style.display = 'block';
    }
}

// View job detail
function viewJobDetail(jobId) {
    window.location.href = `/impact/cloudsphere/job/${jobId}`;
}

// Create new job
function createNewJob() {
    const modal = new bootstrap.Modal(document.getElementById('createJobModal'));
    modal.show();
}

// Submit create job form
async function submitCreateJob() {
    const form = document.getElementById('createJobForm');
    
    if (!form.checkValidity()) {
        form.reportValidity();
        return;
    }
    
    // Get selected tasks (exclude the main "select all" checkbox)
    const selectedTasks = Array.from(document.querySelectorAll('#tasksContainer .task-checkbox:checked'))
        .map(checkbox => parseInt(checkbox.value));
    
    if (selectedTasks.length === 0) {
        showError('Please select at least one task.');
        return;
    }
    
    // Get form values
    const start_datetime = document.getElementById('start_datetime').value;
    const item_name = document.getElementById('item_name').value;
    const sample_type = document.getElementById('sample_type').value;
    const priority_level = document.getElementById('priority_level').value;
    const deadline = document.getElementById('deadline').value;
    const pic_id = document.getElementById('pic_id').value;
    const notes = document.getElementById('notes').value;
    
    // Keep datetime as local format (don't convert to UTC)
    let start_datetime_local = start_datetime;
    let deadline_local = deadline;
    
    // Validate required fields
    if (!item_name || item_name.trim() === '') {
        showError('Item Name is required');
        return;
    }
    
    if (!sample_type || sample_type === '') {
        showError('Sample Type is required');
        return;
    }
    
    if (!priority_level || priority_level === '') {
        showError('Priority Level is required');
        return;
    }
    
    if (!deadline || deadline.trim() === '') {
        showError('Deadline is required');
        return;
    }
    
    if (!start_datetime || start_datetime.trim() === '') {
        showError('Start Date is required');
        return;
    }
    
    if (!pic_id || pic_id === '') {
        showError('PIC is required');
        return;
    }
    
    const jobData = {
        start_datetime: start_datetime_local,
        item_name: item_name,
        sample_type: sample_type,
        priority_level: priority_level,
        deadline: deadline_local,
        pic_id: pic_id,
        task_ids: selectedTasks,
        notes: notes
    };
    
    // Debug logging
    console.log('DEBUG: Submitting job data:', jobData);
    console.log('DEBUG: start_datetime value:', start_datetime);
    console.log('DEBUG: deadline value:', deadline);
    console.log('DEBUG: selectedTasks:', selectedTasks);
    console.log('DEBUG: pic_id value:', pic_id);
    console.log('DEBUG: pic_id type:', typeof pic_id);
    
    try {
        const response = await fetch('/impact/cloudsphere/api/job', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(jobData)
        });
        
        console.log('DEBUG: Response status:', response.status);
        const result = await response.json();
        console.log('DEBUG: Response data:', result);
        
        if (result.success) {
            showSuccess('Job created successfully!');
            bootstrap.Modal.getInstance(document.getElementById('createJobModal')).hide();
            form.reset();
            loadJobs();
            updateStatsWithAnimation(); // Use animated update for job creation
        } else {
            showError(result.error || 'Failed to create job.');
        }
    } catch (error) {
        console.error('Error creating job:', error);
        showError('Failed to create job. Please try again.');
    }
}


// Update statistics with animation only when values change
async function updateStatsWithAnimation() {
    try {
        const response = await fetch('/impact/cloudsphere/api/dashboard-stats');
        
        if (!response.ok) {
            console.error(`HTTP error! status: ${response.status}`);
            return;
        }
        
        const result = await response.json();
        
        if (result.success) {
            const data = result.data;
            
            // Animate only if values have changed
            animateNumber('totalJobs', data.total_jobs || 0);
            animateNumber('inProgressJobs', data.in_progress || 0);
            animateNumber('pendingApprovalJobs', data.pending_approval || 0);
            animateNumber('completedJobs', data.completed || 0);
            animateNumber('rejectedJobs', data.rejected || 0);
        } else {
            console.error('API returned error:', result.error || 'Unknown error');
        }
    } catch (error) {
        console.error('Error updating dashboard stats:', error);
    }
}

// Utility functions
function formatDate(dateString) {
    if (!dateString) return 'N/A';
    
    const date = new Date(dateString);
    return date.toLocaleDateString('en-US', {
        year: 'numeric',
        month: 'short',
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit'
    });
}

function debounce(func, wait) {
    let timeout;
    return function executedFunction() {
        const args = arguments;
        const later = function() {
            clearTimeout(timeout);
            func.apply(this, args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
}

function showSuccess(message) {
    // Create toast notification
    const toast = document.createElement('div');
    toast.className = 'toast align-items-center text-white bg-success border-0 position-fixed top-0 end-0 m-3';
    toast.style.zIndex = '9999';
    toast.innerHTML = `
        <div class="d-flex">
            <div class="toast-body">
                <i class="fas fa-check-circle me-2"></i>${message}
            </div>
            <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast"></button>
        </div>
    `;
    
    document.body.appendChild(toast);
    const bsToast = new bootstrap.Toast(toast);
    bsToast.show();
    
    toast.addEventListener('hidden.bs.toast', () => {
        document.body.removeChild(toast);
    });
}

// Edit job function
async function editJob(jobId) {
    try {
        // Get job details
        const response = await fetch(`/impact/cloudsphere/api/job/${jobId}`);
        
        if (!response.ok) {
            console.error(`HTTP error! status: ${response.status}`);
            showError(`Server error: ${response.status}`);
            return;
        }
        
        const result = await response.json();
        
        if (result.success) {
            const job = result.data;
            
            // Load users for PIC selection first
            await loadUsersForEdit(job.pic_id);
            
            // Populate edit form
            document.getElementById('editJobId').value = job.id;
            document.getElementById('edit_item_name').value = job.item_name;
            document.getElementById('edit_sample_type').value = job.sample_type;
            document.getElementById('edit_priority_level').value = job.priority_level;
            document.getElementById('edit_status').value = job.status;
            document.getElementById('edit_notes').value = job.notes || '';
            
            // Set PIC value after users are loaded
            document.getElementById('edit_pic_id').value = job.pic_id;
            
            // Format dates for datetime-local input (convert to local time)
            if (job.start_date) {
                // Handle datetime format from backend (YYYY-MM-DD HH:MM)
                const startDateStr = job.start_date.replace(' ', 'T');
                document.getElementById('edit_start_datetime').value = startDateStr;
            }
            
            if (job.deadline) {
                // Handle the datetime format from backend (YYYY-MM-DDTHH:MM)
                const deadlineStr = job.deadline;
                document.getElementById('edit_deadline').value = deadlineStr;
            }
            
            // Load tasks for edit modal
            await loadEditTasks(job.tasks || []);
            
            // Show modal
            const modal = new bootstrap.Modal(document.getElementById('editJobModal'));
            modal.show();
        } else {
            showError(result.error || 'Failed to load job details');
        }
    } catch (error) {
        console.error('Error loading job details:', error);
        showError('Failed to load job details. Please try again.');
    }
}

// Load users for edit modal
async function loadUsersForEdit(selectedPicId = null) {
    try {
        const response = await fetch('/impact/cloudsphere/api/users?division_id=6');
        
        if (!response.ok) {
            console.error(`HTTP error! status: ${response.status}`);
            return;
        }
        
        const result = await response.json();
        
        const select = document.getElementById('edit_pic_id');
        select.innerHTML = '<option value="">Select PIC</option>';
        
        if (result.success && result.data) {
            result.data.forEach(user => {
                const option = document.createElement('option');
                option.value = user.id;
                option.textContent = user.name;
                select.appendChild(option);
            });
            
            // Set selected PIC ID if provided
            if (selectedPicId) {
                select.value = selectedPicId;
            }
        }
    } catch (error) {
        console.error('Error loading users for edit:', error);
    }
}

// Load tasks for edit modal
async function loadEditTasks(selectedTasks = []) {
    try {
        const response = await fetch('/impact/cloudsphere/api/task-categories');
        
        if (!response.ok) {
            console.error(`HTTP error! status: ${response.status}`);
            return;
        }
        
        const result = await response.json();
        
        if (result.success) {
            displayEditTasks(result.data, selectedTasks);
        } else {
            console.error('API returned error:', result.error || 'Unknown error');
        }
    } catch (error) {
        console.error('Error loading task categories:', error);
    }
}

// Display tasks in edit modal with pre-selections
function displayEditTasks(categories, selectedTasks) {
    const container = document.getElementById('editTasksContainer');
    container.innerHTML = '';
    
    // Define the order of categories
    const categoryOrder = ['Blank', 'Mastercard', 'RoHS Regular ICB', 'RoHS Ribbon', 'Polymer Ribbon'];
    
    // Sort categories according to the defined order
    const sortedCategories = categories.sort((a, b) => {
        const categoryNameA = a.category_name || a.name;
        const categoryNameB = b.category_name || b.name;
        const indexA = categoryOrder.indexOf(categoryNameA);
        const indexB = categoryOrder.indexOf(categoryNameB);
        
        // If category is not in the predefined order, put it at the end
        if (indexA === -1 && indexB === -1) return categoryNameA.localeCompare(categoryNameB);
        if (indexA === -1) return 1;
        if (indexB === -1) return -1;
        
        return indexA - indexB;
    });
    
    // Create a grid layout
    const rowDiv = document.createElement('div');
    rowDiv.className = 'row';
    
    sortedCategories.forEach((category, index) => {
        const categoryDiv = document.createElement('div');
        categoryDiv.className = 'col-md-6 mb-4';
        
        // Add category header with color coding
        let categoryColor = '';
        const categoryName = category.category_name || category.name;
        switch(categoryName) {
            case 'Blank': categoryColor = 'border-primary'; break;
            case 'Mastercard': categoryColor = 'border-success'; break;
            case 'RoHS Regular ICB': categoryColor = 'border-warning'; break;
            case 'RoHS Ribbon': categoryColor = 'border-info'; break;
            case 'Polymer Ribbon': categoryColor = 'border-info'; break;
            default: categoryColor = 'border-secondary';
        }
        
        // Check if all tasks in this category are selected
        const selectedTaskIds = selectedTasks.map(task => task.id);
        const allTasksSelected = category.tasks.every(task => selectedTaskIds.includes(task.id));
        
        categoryDiv.innerHTML = `
            <div class="card h-100 border ${categoryColor}">
                <div class="card-header bg-light">
                    <div class="d-flex align-items-center">
                        <input type="checkbox" class="form-check-input me-2" id="edit_select_all_${category.id}"
                               onchange="toggleEditCategoryTasks(${category.id})" ${allTasksSelected ? 'checked' : ''}>
                        <label class="form-check-label fw-bold mb-0" for="edit_select_all_${category.id}">
                            <i class="fas fa-tasks me-1"></i> Select All: ${categoryName}
                        </label>
                    </div>
                </div>
                <div class="card-body p-2" style="max-height: 400px; overflow-y: auto;">
                    <div class="task-list" id="edit_tasks_${category.id}">
                        ${category.tasks.map(task => `
                            <div class="form-check mb-2">
                                <input class="form-check-input edit-task-checkbox" type="checkbox" value="${task.id}"
                                       id="edit_task_${task.id}" data-category="${category.id}"
                                       ${selectedTaskIds.includes(task.id) ? 'checked' : ''}>
                                <label class="form-check-label" for="edit_task_${task.id}" title="${task.task_name || task.name}">
                                    ${task.task_name || task.name}
                                </label>
                            </div>
                        `).join('')}
                    </div>
                </div>
            </div>
        `;
        
        rowDiv.appendChild(categoryDiv);
    });
    
    container.innerHTML = '';
    container.appendChild(rowDiv);
    
    // Add event listeners to individual task checkboxes
    document.querySelectorAll('.edit-task-checkbox').forEach(checkbox => {
        checkbox.addEventListener('change', function() {
            // Update the category "Select All" checkbox
            const categoryId = this.getAttribute('data-category');
            const categorySelectAll = document.getElementById(`edit_select_all_${categoryId}`);
            const categoryTasks = document.querySelectorAll(`#edit_tasks_${categoryId} .edit-task-checkbox`);
            
            // Check if all tasks in this category are selected
            let allCategoryTasksSelected = true;
            categoryTasks.forEach(task => {
                if (!task.checked) {
                    allCategoryTasksSelected = false;
                }
            });
            
            categorySelectAll.checked = allCategoryTasksSelected;
        });
    });
}

// Toggle all tasks in a category for edit modal
function toggleEditCategoryTasks(categoryId) {
    const selectAllCheckbox = document.getElementById(`edit_select_all_${categoryId}`);
    const categoryTasks = document.querySelectorAll(`#edit_tasks_${categoryId} .edit-task-checkbox`);
    
    categoryTasks.forEach(checkbox => {
        checkbox.checked = selectAllCheckbox.checked;
    });
}

// Submit edit job form
async function submitEditJob() {
    const form = document.getElementById('editJobForm');
    
    if (!form.checkValidity()) {
        form.reportValidity();
        return;
    }
    
    // Get selected tasks
    const selectedTasks = Array.from(document.querySelectorAll('#editTasksContainer .edit-task-checkbox:checked'))
        .map(checkbox => parseInt(checkbox.value));
    
    if (selectedTasks.length === 0) {
        showError('Please select at least one task.');
        return;
    }
    
    // Get form values
    const jobId = document.getElementById('editJobId').value;
    const start_datetime = document.getElementById('edit_start_datetime').value;
    const item_name = document.getElementById('edit_item_name').value;
    const sample_type = document.getElementById('edit_sample_type').value;
    const priority_level = document.getElementById('edit_priority_level').value;
    const deadline = document.getElementById('edit_deadline').value;
    const pic_id = document.getElementById('edit_pic_id').value;
    const status = document.getElementById('edit_status').value;
    const notes = document.getElementById('edit_notes').value;
    
    // Keep datetime as local format (don't convert to UTC)
    let start_datetime_local = start_datetime;
    let deadline_local = deadline;
    
    // Validate required fields
    if (!item_name || item_name.trim() === '') {
        showError('Item Name is required');
        return;
    }
    
    if (!sample_type || sample_type === '') {
        showError('Sample Type is required');
        return;
    }
    
    if (!priority_level || priority_level === '') {
        showError('Priority Level is required');
        return;
    }
    
    if (!deadline || deadline.trim() === '') {
        showError('Deadline is required');
        return;
    }
    
    if (!start_datetime || start_datetime.trim() === '') {
        showError('Start Date is required');
        return;
    }
    
    if (!pic_id || pic_id === '') {
        showError('PIC is required');
        return;
    }
    
    const jobData = {
        id: jobId,
        start_datetime: start_datetime_local,
        item_name: item_name,
        sample_type: sample_type,
        priority_level: priority_level,
        deadline: deadline_local,
        pic_id: pic_id,
        status: status,
        task_ids: selectedTasks,
        notes: notes
    };
    
    try {
        const response = await fetch(`/impact/cloudsphere/api/job/${jobId}`, {
            method: 'PUT',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(jobData)
        });
        
        if (response.ok) {
            const result = await response.json();
            if (result.success) {
                showSuccess('Job updated successfully!');
                bootstrap.Modal.getInstance(document.getElementById('editJobModal')).hide();
                form.reset();
                loadJobs();
                updateStatsWithAnimation();
            } else {
                showError(result.error || 'Failed to update job.');
            }
        } else {
            showError(`Server error: ${response.status}`);
        }
    } catch (error) {
        console.error('Error updating job:', error);
        showError('Failed to update job. Please try again.');
    }
}

// Delete job function
async function deleteJob(jobId) {
    try {
        // Get job details for preview
        const response = await fetch(`/impact/cloudsphere/api/job/${jobId}`);
        
        if (!response.ok) {
            console.error(`HTTP error! status: ${response.status}`);
            showError(`Server error: ${response.status}`);
            return;
        }
        
        const result = await response.json();
        
        if (result.success) {
            const job = result.data;
            
            // Set job ID for deletion
            document.getElementById('deleteJobId').value = job.id;
            
            // Show job preview
            const preview = document.getElementById('deleteJobPreview');
            preview.innerHTML = `
                <div class="card border-danger">
                    <div class="card-body">
                        <h6 class="card-title">${job.item_name}</h6>
                        <p class="card-text">
                            <strong>Job ID:</strong> ${job.job_id}<br>
                            <strong>PIC:</strong> ${job.pic_name}<br>
                            <strong>Sample Type:</strong> ${job.sample_type}<br>
                            <strong>Priority:</strong> ${job.priority_level}<br>
                            <strong>Status:</strong> ${job.status.replace(/_/g, ' ')}
                        </p>
                    </div>
                </div>
            `;
            
            // Show modal
            const modal = new bootstrap.Modal(document.getElementById('deleteJobModal'));
            modal.show();
        } else {
            showError(result.error || 'Failed to load job details');
        }
    } catch (error) {
        console.error('Error loading job details:', error);
        showError('Failed to load job details. Please try again.');
    }
}

// Confirm delete job
async function confirmDeleteJob() {
    const jobId = document.getElementById('deleteJobId').value;
    
    try {
        const response = await fetch(`/impact/cloudsphere/api/job/${jobId}`, {
            method: 'DELETE'
        });
        
        if (response.ok) {
            const result = await response.json();
            if (result.success) {
                showSuccess('Job deleted successfully!');
                bootstrap.Modal.getInstance(document.getElementById('deleteJobModal')).hide();
                loadJobs();
                updateStatsWithAnimation();
            } else {
                showError(result.error || 'Failed to delete job.');
            }
        } else {
            showError(`Server error: ${response.status}`);
        }
    } catch (error) {
        console.error('Error deleting job:', error);
        showError('Failed to delete job. Please try again.');
    }
}

function showError(message) {
    // Create toast notification
    const toast = document.createElement('div');
    toast.className = 'toast align-items-center text-white bg-danger border-0 position-fixed top-0 end-0 m-3';
    toast.style.zIndex = '9999';
    toast.innerHTML = `
        <div class="d-flex">
            <div class="toast-body">
                <i class="fas fa-exclamation-circle me-2"></i>${message}
            </div>
            <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast"></button>
        </div>
    `;
    
    document.body.appendChild(toast);
    const bsToast = new bootstrap.Toast(toast);
    bsToast.show();
    
    toast.addEventListener('hidden.bs.toast', () => {
        document.body.removeChild(toast);
    });
}