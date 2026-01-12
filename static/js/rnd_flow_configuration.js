let currentConfigurationId = null;
let allProgressSteps = [];
let flowSteps = [];

// Initialize the page
document.addEventListener('DOMContentLoaded', function() {
    loadConfigurations();
    checkIfDefaultsExist();
    
    // Initialize sortable for flow steps
    initializeSortable();
    
    // Event listeners
    document.getElementById('sampleTypeFilter').addEventListener('change', filterConfigurations);
    document.getElementById('statusFilter').addEventListener('change', filterConfigurations);
    document.getElementById('configSampleType').addEventListener('change', loadAvailableSteps);
});

function initializeSortable() {
    const flowStepsContainer = document.getElementById('flowSteps');
    if (flowStepsContainer) {
        new Sortable(flowStepsContainer, {
            group: {
                name: 'flowSteps',
                pull: false,
                put: true
            },
            animation: 150,
            ghostClass: 'dragging',
            onEnd: function(evt) {
                updateStepNumbers();
            }
        });
    }
}

function checkIfDefaultsExist() {
    fetch('/impact/rnd-cloudsphere/api/flow-configurations')
        .then(response => response.json())
        .then(data => {
            if (data.success && data.data.length === 0) {
                document.getElementById('initDefaultsBtn').style.display = 'inline-block';
            }
        })
        .catch(error => console.error('Error checking configurations:', error));
}

function loadConfigurations() {
    const sampleType = document.getElementById('sampleTypeFilter').value;
    const includeInactive = document.getElementById('statusFilter').value === 'all';
    
    // Show loading spinner, hide empty state
    document.getElementById('loadingSpinner').style.display = 'block';
    document.getElementById('emptyState').style.display = 'none';
    
    let url = '/impact/rnd-cloudsphere/api/flow-configurations';
    const params = new URLSearchParams();
    
    if (sampleType) params.append('sample_type', sampleType);
    if (includeInactive) params.append('include_inactive', 'true');
    
    if (params.toString()) {
        url += '?' + params.toString();
    }
    
    fetch(url)
        .then(response => response.json())
        .then(data => {
            // Hide loading spinner
            document.getElementById('loadingSpinner').style.display = 'none';
            
            if (data.success) {
                displayConfigurations(data.data);
            } else {
                showAlert('Error loading configurations: ' + data.error, 'danger');
            }
        })
        .catch(error => {
            // Hide loading spinner
            document.getElementById('loadingSpinner').style.display = 'none';
            console.error('Error loading configurations:', error);
            showAlert('Error loading configurations', 'danger');
        });
}

function displayConfigurations(configurations) {
    const container = document.getElementById('configurationsList');
    const emptyState = document.getElementById('emptyState');
    
    container.innerHTML = '';
    
    if (configurations.length === 0) {
        // Show empty state
        emptyState.style.display = 'block';
        container.innerHTML = `
            <div class="col-12">
                <div class="alert alert-info">
                    <i class="bi bi-info-circle"></i> No flow configurations found.
                    <button class="btn btn-sm btn-primary ms-2" onclick="initializeDefaults()">
                        Initialize Default Configurations
                    </button>
                </div>
            </div>
        `;
    } else {
        // Hide empty state and show configurations
        emptyState.style.display = 'none';
        configurations.forEach(config => {
            const configCard = createConfigurationCard(config);
            container.appendChild(configCard);
        });
    }
}

function createConfigurationCard(config) {
    const col = document.createElement('div');
    col.className = 'col-md-6 col-lg-4 mb-4';
    
    const defaultBadge = config.is_default ? '<span class="badge-status default">Default</span>' : '';
    const activeBadge = config.is_active ? 
        '<span class="badge-status active">Active</span>' : 
        '<span class="badge-status not-active">Inactive</span>';
    
    col.innerHTML = `
        <div class="card configuration-card">
            <div class="card-header">
                <h6 class="mb-0">
                    ${config.name}
                    ${defaultBadge}
                    ${activeBadge}
                </h6>
                <small class="text-muted">Sample Type: ${config.sample_type}</small>
            </div>
            <div class="card-body">
                <p class="card-text">${config.description || 'No description'}</p>
                <small class="text-muted">
                    Created by ${config.creator_name} on ${formatDate(config.created_at)}
                </small>
                <div class="mt-3">
                    <button class="btn btn-sm btn-outline-primary" onclick="viewConfiguration(${config.id})">
                        <i class="bi bi-eye"></i> View
                    </button>
                    <button class="btn btn-sm btn-outline-secondary" onclick="editConfiguration(${config.id})">
                        <i class="bi bi-pencil"></i> Edit
                    </button>
                    <button class="btn btn-sm btn-outline-success" onclick="setDefaultConfiguration(${config.id})" 
                            ${config.is_default ? 'disabled' : ''}>
                        <i class="bi bi-check-circle"></i> Set Default
                    </button>
                    <button class="btn btn-sm btn-outline-danger" onclick="deleteConfiguration(${config.id})">
                        <i class="bi bi-trash"></i> Delete
                    </button>
                </div>
            </div>
        </div>
    `;
    
    return col;
}

function loadAvailableSteps() {
    const sampleType = document.getElementById('configSampleType').value;
    
    if (!sampleType) {
        document.getElementById('availableSteps').innerHTML = '<p class="text-muted">Select a sample type first</p>';
        return;
    }
    
    // Load progress steps relevant to selected sample type (including common steps)
    fetch(`/impact/rnd-cloudsphere/api/progress-steps/all?sample_type=${sampleType}`)
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                allProgressSteps = data.data;
                displayAvailableSteps();
            } else {
                showAlert('Error loading progress steps: ' + data.error, 'danger');
            }
        })
        .catch(error => {
            console.error('Error loading progress steps:', error);
            showAlert('Error loading progress steps', 'danger');
        });
}

function displayAvailableSteps() {
    const container = document.getElementById('availableSteps');
    container.innerHTML = '';
    
    // Group steps by sample type
    const stepsByType = {};
    allProgressSteps.forEach(step => {
        if (!stepsByType[step.sample_type]) {
            stepsByType[step.sample_type] = [];
        }
        stepsByType[step.sample_type].push(step);
    });
    
    // Display steps by type
    Object.keys(stepsByType).forEach(sampleType => {
        const typeHeader = document.createElement('h6');
        typeHeader.className = 'mt-3 mb-2';
        typeHeader.textContent = sampleType;
        container.appendChild(typeHeader);
        
        stepsByType[sampleType].forEach(step => {
            const stepElement = createAvailableStepElement(step);
            container.appendChild(stepElement);
        });
    });
}

function createAvailableStepElement(step) {
    const div = document.createElement('div');
    div.className = 'available-step-item';
    div.draggable = true;
    div.dataset.stepId = step.id;
    div.dataset.stepName = step.name;
    div.dataset.stepSampleType = step.sample_type;
    
    div.innerHTML = `
        <div class="d-flex justify-content-between align-items-center">
            <div>
                <strong>${step.name}</strong>
                <br>
                <small class="text-muted">${step.sample_type}</small>
            </div>
            <div>
                <small class="text-muted">${step.tasks.length} tasks</small>
            </div>
        </div>
    `;
    
    // Add drag event listeners
    div.addEventListener('dragstart', handleDragStart);
    div.addEventListener('dragend', handleDragEnd);
    
    return div;
}

function handleDragStart(e) {
    e.target.classList.add('dragging');
    e.dataTransfer.effectAllowed = 'copy';
    e.dataTransfer.setData('text/plain', JSON.stringify({
        id: e.target.dataset.stepId,
        name: e.target.dataset.stepName,
        sampleType: e.target.dataset.stepSampleType
    }));
}

function handleDragEnd(e) {
    e.target.classList.remove('dragging');
}

// Drop zone functionality
const dropZone = document.getElementById('flowSteps');
if (dropZone) {
    dropZone.addEventListener('dragover', handleDragOver);
    dropZone.addEventListener('drop', handleDrop);
    dropZone.addEventListener('dragleave', handleDragLeave);
}

function handleDragOver(e) {
    e.preventDefault();
    e.dataTransfer.dropEffect = 'copy';
    dropZone.classList.add('drag-over');
}

function handleDragLeave(e) {
    if (e.target === dropZone) {
        dropZone.classList.remove('drag-over');
    }
}

function handleDrop(e) {
    e.preventDefault();
    dropZone.classList.remove('drag-over');
    
    try {
        const stepData = JSON.parse(e.dataTransfer.getData('text/plain'));
        
        // Check if step already exists in flow
        if (flowSteps.find(s => s.id === stepData.id)) {
            showAlert('Step already added to flow', 'warning');
            return;
        }
        
        // Add step to flow
        flowSteps.push({
            id: stepData.id,
            name: stepData.name,
            sampleType: stepData.sampleType,
            isRequired: true
        });
        
        updateFlowStepsDisplay();
    } catch (error) {
        console.error('Error handling drop:', error);
    }
}

function updateFlowStepsDisplay() {
    const container = document.getElementById('flowSteps');
    
    if (flowSteps.length === 0) {
        container.innerHTML = '<p class="text-muted">Drag steps here to configure flow</p>';
        return;
    }
    
    container.innerHTML = '';
    
    flowSteps.forEach((step, index) => {
        const stepElement = createFlowStepElement(step, index + 1);
        container.appendChild(stepElement);
    });
}

function createFlowStepElement(step, stepNumber) {
    const div = document.createElement('div');
    div.className = 'step-item';
    div.dataset.stepId = step.id;
    
    div.innerHTML = `
        <div class="step-number">${stepNumber}</div>
        <div class="step-content">
            <h6>${step.name}</h6>
            <small class="text-muted">${step.sampleType}</small>
            <div class="form-check mt-2">
                <input class="form-check-input" type="checkbox" id="required_${step.id}" 
                       ${step.isRequired ? 'checked' : ''} 
                       onchange="toggleStepRequired(${step.id})">
                <label class="form-check-label" for="required_${step.id}">
                    Required Step
                </label>
            </div>
        </div>
        <div class="step-actions">
            <button class="btn btn-sm btn-outline-danger" onclick="removeStepFromFlow(${step.id})">
                <i class="bi bi-x"></i>
            </button>
        </div>
    `;
    
    return div;
}

function removeStepFromFlow(stepId) {
    flowSteps = flowSteps.filter(s => s.id !== stepId);
    updateFlowStepsDisplay();
}

function toggleStepRequired(stepId) {
    const step = flowSteps.find(s => s.id === stepId);
    if (step) {
        step.isRequired = document.getElementById(`required_${stepId}`).checked;
    }
}

function updateStepNumbers() {
    const stepElements = document.querySelectorAll('#flowSteps .step-item');
    stepElements.forEach((element, index) => {
        const numberElement = element.querySelector('.step-number');
        if (numberElement) {
            numberElement.textContent = index + 1;
        }
    });
    
    // Update flowSteps array order
    const newOrder = [];
    stepElements.forEach(element => {
        const stepId = parseInt(element.dataset.stepId);
        const step = flowSteps.find(s => s.id === stepId);
        if (step) {
            newOrder.push(step);
        }
    });
    flowSteps = newOrder;
}

function showCreateModal() {
    currentConfigurationId = null;
    document.getElementById('modalTitle').textContent = 'Create Flow Configuration';
    document.getElementById('configurationForm').reset();
    document.getElementById('flowSteps').innerHTML = '<p class="text-muted">Drag steps here to configure flow</p>';
    flowSteps = [];
    
    const modal = new bootstrap.Modal(document.getElementById('configurationModal'));
    modal.show();
}

function editConfiguration(configId) {
    currentConfigurationId = configId;
    
    fetch(`/impact/rnd-cloudsphere/api/flow-configurations/${configId}`)
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                const config = data.data;
                document.getElementById('modalTitle').textContent = 'Edit Flow Configuration';
                document.getElementById('configName').value = config.name;
                document.getElementById('configSampleType').value = config.sample_type;
                document.getElementById('configDescription').value = config.description || '';
                document.getElementById('configIsDefault').checked = config.is_default;
                document.getElementById('configIsActive').checked = config.is_active;
                
                // Load flow steps
                flowSteps = config.flow_steps.map(step => ({
                    id: step.progress_step_id,
                    name: step.progress_step_name,
                    sampleType: step.progress_step_sample_type,
                    isRequired: step.is_required
                }));
                
                updateFlowStepsDisplay();
                loadAvailableSteps();
                
                const modal = new bootstrap.Modal(document.getElementById('configurationModal'));
                modal.show();
            } else {
                showAlert('Error loading configuration: ' + data.error, 'danger');
            }
        })
        .catch(error => {
            console.error('Error loading configuration:', error);
            showAlert('Error loading configuration', 'danger');
        });
}

// Helper function to get sample icon (copied from rnd_cloudsphere.js)
function getSampleIcon(sampleType) {
    switch(sampleType.toLowerCase()) {
        case 'blank':
            return `
                <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                    <rect x="4" y="4" width="16" height="16" rx="2" fill="#E3F2FD" stroke="#1976D2" stroke-width="2"/>
                    <path d="M8 8L16 16M16 8L8 16" stroke="#1976D2" stroke-width="2" stroke-linecap="round"/>
                    <circle cx="12" cy="12" r="2" fill="#90CAF9" stroke="#1976D2" stroke-width="1.5"/>
                    <rect x="10" y="6" width="4" height="2" fill="#64B5F6"/>
                    <rect x="6" y="10" width="2" height="4" fill="#64B5F6"/>
                    <rect x="16" y="10" width="2" height="4" fill="#64B5F6"/>
                    <rect x="10" y="16" width="4" height="2" fill="#64B5F6"/>
                </svg>
            `;
        case 'rohs icb':
            return `
                <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                    <path d="M12 2L15.09 8.26L22 9.27L17 14.14L18.18 21.02L12 17.77L5.82 21.02L7 14.14L2 9.27L8.91 8.26L12 2Z" fill="#4CAF50"/>
                    <path d="M9 11L11 13L15 9" stroke="white" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                </svg>
            `;
        case 'rohs ribbon':
            return `
                <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                    <path d="M12 2C12 2 13 2 14 3C15 4 16 4 16 6C16 8 15 9 15 11C15 13 16 14 16 16C16 18 15 19 14 20C13 21 12 21 12 21C12 21 11 21 10 20C9 19 8 18 8 16C8 14 9 13 9 11C9 9 8 8 8 6C8 4 9 4 10 3C11 2 12 2 12 2Z" fill="#FF5722"/>
                    <path d="M12 2L12 21" stroke="#D84315" stroke-width="1.5" stroke-linecap="round"/>
                    <path d="M8 6L16 6" stroke="#FF8A65" stroke-width="1.5" stroke-linecap="round"/>
                    <path d="M8 16L16 16" stroke="#FF8A65" stroke-width="1.5" stroke-linecap="round"/>
                    <path d="M10 11L11 12L14 9" stroke="white" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/>
                    <circle cx="12" cy="6" r="1.5" fill="#FFEB3B"/>
                    <circle cx="12" cy="16" r="1.5" fill="#FFEB3B"/>
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
}

function getSampleTypeBadgeColor(sampleType) {
    switch(sampleType.toLowerCase()) {
        case 'blank':
            return 'badge-blank';
        case 'rohs icb':
            return 'badge-rohs-icb';
        case 'rohs ribbon':
            return 'badge-rohs-ribbon';
        default:
            return 'bg-primary';
    }
}

function viewConfiguration(configId) {
    fetch(`/impact/rnd-cloudsphere/api/flow-configurations/${configId}`)
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                const config = data.data;
                const content = document.getElementById('viewConfigurationContent');
                
                let stepsHtml = '';
                config.flow_steps.forEach((step, index) => {
                    const requiredBadge = step.is_required ? '<span class="badge required">Required</span>' : '<span class="badge optional">Optional</span>';
                    stepsHtml += `
                        <div class="mb-3">
                            <h6>${index + 1}. ${step.progress_step_name} ${requiredBadge}</h6>
                            <small class="text-muted">${step.progress_step_sample_type}</small>
                        </div>
                    `;
                });
                
                const sampleTypeBadgeClass = getSampleTypeBadgeColor(config.sample_type);
                
                content.innerHTML = `
                    <div class="mb-3">
                        <h5>${config.name}</h5>
                        <p>${config.description || 'No description'}</p>
                        <div>
                            <span class="badge ${sampleTypeBadgeClass} d-inline-flex align-items-center">
                                <span class="sample-type-icon me-1">${getSampleIcon(config.sample_type)}</span>
                                ${config.sample_type}
                            </span>
                            ${config.is_default ? '<span class="badge-status default">Default</span>' : ''}
                            ${config.is_active ? '<span class="badge-status active">Active</span>' : '<span class="badge-status not-active">Inactive</span>'}
                        </div>
                    </div>
                    <div class="mb-3">
                        <h6>Flow Steps</h6>
                        ${stepsHtml}
                    </div>
                    <div>
                        <small class="text-muted">
                            Created by ${config.creator_name} on ${formatDate(config.created_at)}
                        </small>
                    </div>
                `;
                
                const modal = new bootstrap.Modal(document.getElementById('viewConfigurationModal'));
                modal.show();
            } else {
                showAlert('Error loading configuration: ' + data.error, 'danger');
            }
        })
        .catch(error => {
            console.error('Error loading configuration:', error);
            showAlert('Error loading configuration', 'danger');
        });
}

function saveConfiguration() {
    const name = document.getElementById('configName').value.trim();
    const sampleType = document.getElementById('configSampleType').value;
    const description = document.getElementById('configDescription').value.trim();
    const isDefault = document.getElementById('configIsDefault').checked;
    const isActive = document.getElementById('configIsActive').checked;
    
    if (!name || !sampleType) {
        showAlert('Please fill in all required fields', 'warning');
        return;
    }
    
    if (flowSteps.length === 0) {
        showAlert('Please add at least one step to the flow', 'warning');
        return;
    }
    
    const flowStepsData = flowSteps.map((step, index) => ({
        progress_step_id: step.id,
        step_order: index + 1,
        is_required: step.isRequired
    }));
    
    const configurationData = {
        name: name,
        sample_type: sampleType,
        description: description,
        is_default: isDefault,
        is_active: isActive,
        flow_steps: flowStepsData
    };
    
    const url = currentConfigurationId ? 
        `/impact/rnd-cloudsphere/api/flow-configurations/${currentConfigurationId}` : 
        '/impact/rnd-cloudsphere/api/flow-configurations';
    
    const method = currentConfigurationId ? 'PUT' : 'POST';
    
    fetch(url, {
        method: method,
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify(configurationData)
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            showAlert(`Configuration ${currentConfigurationId ? 'updated' : 'created'} successfully`, 'success');
            bootstrap.Modal.getInstance(document.getElementById('configurationModal')).hide();
            loadConfigurations();
        } else {
            showAlert(`Error ${currentConfigurationId ? 'updating' : 'creating'} configuration: ${data.error}`, 'danger');
        }
    })
    .catch(error => {
        console.error('Error saving configuration:', error);
        showAlert(`Error ${currentConfigurationId ? 'updating' : 'creating'} configuration`, 'danger');
    });
}

function deleteConfiguration(configId) {
    if (!confirm('Are you sure you want to delete this configuration? This action cannot be undone.')) {
        return;
    }
    
    fetch(`/impact/rnd-cloudsphere/api/flow-configurations/${configId}`, {
        method: 'DELETE'
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            showAlert('Configuration deleted successfully', 'success');
            loadConfigurations();
        } else {
            showAlert('Error deleting configuration: ' + data.error, 'danger');
        }
    })
    .catch(error => {
        console.error('Error deleting configuration:', error);
        showAlert('Error deleting configuration', 'danger');
    });
}

function setDefaultConfiguration(configId) {
    fetch(`/impact/rnd-cloudsphere/api/flow-configurations/${configId}/set-default`, {
        method: 'POST'
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            showAlert('Configuration set as default successfully', 'success');
            loadConfigurations();
        } else {
            showAlert('Error setting default configuration: ' + data.error, 'danger');
        }
    })
    .catch(error => {
        console.error('Error setting default configuration:', error);
        showAlert('Error setting default configuration', 'danger');
    });
}

function initializeDefaults() {
    if (!confirm('This will create default flow configurations based on existing progress steps. Continue?')) {
        return;
    }
    
    fetch('/impact/rnd-cloudsphere/api/init-default-flow-configurations', {
        method: 'POST'
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            showAlert('Default configurations initialized successfully', 'success');
            document.getElementById('initDefaultsBtn').style.display = 'none';
            loadConfigurations();
        } else {
            showAlert('Error initializing defaults: ' + data.error, 'danger');
        }
    })
    .catch(error => {
        console.error('Error initializing defaults:', error);
        showAlert('Error initializing defaults', 'danger');
    });
}

function filterConfigurations() {
    loadConfigurations();
}

function formatDate(dateString) {
    const date = new Date(dateString);
    return date.toLocaleDateString('en-US', {
        year: 'numeric',
        month: 'short',
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit'
    });
}

function showToast(message, type = 'success') {
    // Get toast container or create it if it doesn't exist
    let toastContainer = document.querySelector('.toast-container');
    if (!toastContainer) {
        toastContainer = document.createElement('div');
        toastContainer.className = 'toast-container position-fixed top-0 end-0 p-3';
        document.body.appendChild(toastContainer);
    }
    
    // Create unique toast ID
    const toastId = 'toast-' + Date.now();
    
    // Determine background color based on type
    let bgClass = 'bg-success';
    if (type === 'danger' || type === 'error') {
        bgClass = 'bg-danger';
    } else if (type === 'warning') {
        bgClass = 'bg-warning';
    } else if (type === 'info') {
        bgClass = 'bg-info';
    }
    
    // Create toast element
    const toastElement = document.createElement('div');
    toastElement.id = toastId;
    toastElement.className = 'toast border-0 shadow-lg';
    toastElement.setAttribute('role', 'alert');
    toastElement.setAttribute('aria-live', 'assertive');
    toastElement.setAttribute('aria-atomic', 'true');
    
    toastElement.innerHTML = `
        <div class="toast-body ${bgClass} text-white rounded">
            <span class="message-text">${message}</span>
            <button type="button" class="btn-close btn-close-white float-end" data-bs-dismiss="toast" aria-label="Close"></button>
        </div>
    `;
    
    // Add to container
    toastContainer.appendChild(toastElement);
    
    // Initialize and show toast
    const toast = new bootstrap.Toast(toastElement, {
        autohide: true,
        delay: 5000
    });
    
    toast.show();
    
    // Remove from DOM after hidden
    toastElement.addEventListener('hidden.bs.toast', () => {
        toastElement.remove();
    });
}

// Keep showAlert for backward compatibility but redirect to showToast
function showAlert(message, type) {
    showToast(message, type);
}