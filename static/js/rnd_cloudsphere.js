// R&D Cloudsphere Dashboard JavaScript
class RNDCloudsphere {
    constructor() {
        this.filters = {
            status: '',
            priority: '',
            sample_type: '',
            search: ''
        };
        this.jobs = [];
        this.stats = {};
        this.init();
    }

    init() {
        this.loadStats();
        this.loadJobs();
        this.setupEventListeners();
        this.loadUsers();
    }

    setupEventListeners() {
        // Filter change events
        document.getElementById('statusFilter').addEventListener('change', (e) => {
            this.filters.status = e.target.value;
            this.loadJobs();
        });

        document.getElementById('priorityFilter').addEventListener('change', (e) => {
            this.filters.priority = e.target.value;
            this.loadJobs();
        });

        document.getElementById('sampleTypeFilter').addEventListener('change', (e) => {
            this.filters.sample_type = e.target.value;
            this.loadJobs();
        });

        document.getElementById('searchInput').addEventListener('input', (e) => {
            this.filters.search = e.target.value;
            this.loadJobs();
        });

        // Modal events
        const createJobModal = document.getElementById('createRNDJobModal');
        if (createJobModal) {
            createJobModal.addEventListener('show.bs.modal', () => {
                this.loadUsers();
                // Don't load progress steps here - wait for user to select sample type and flow configuration
                document.getElementById('progressStepsContainer').innerHTML = '<p class="text-muted">Please select a sample type and flow configuration first</p>';
            });
        }

        const editJobModal = document.getElementById('editJobModal');
        if (editJobModal) {
            editJobModal.addEventListener('show.bs.modal', () => {
                this.loadUsers();
                // Progress steps will be loaded when a job is selected for editing
            });
        }
    }

    async loadStats() {
        try {
            const response = await fetch('/impact/rnd-cloudsphere/api/dashboard-stats');
            const data = await response.json();
            
            if (data.success) {
                this.renderStats(data.data);
            }
        } catch (error) {
            console.error('Error loading stats:', error);
        }
    }

    renderStats(stats) {
        const container = document.getElementById('statsContainer');
        if (!container) return;

        const statsHTML = `
            <div class="stat-card total">
                <div class="stat-value">${stats.total_jobs}</div>
                <div class="stat-label">Total Jobs</div>
            </div>
            <div class="stat-card in-progress">
                <div class="stat-value">${stats.in_progress}</div>
                <div class="stat-label">In Progress</div>
            </div>
            <div class="stat-card completed">
                <div class="stat-value">${stats.completed}</div>
                <div class="stat-label">Completed</div>
            </div>
            <div class="stat-card rejected">
                <div class="stat-value">${stats.rejected}</div>
                <div class="stat-label">Rejected</div>
            </div>
            <div class="stat-card blank">
                <div class="stat-value">${stats.blank_jobs}</div>
                <div class="stat-label">Blank</div>
            </div>
            <div class="stat-card rohs-icb">
                <div class="stat-value">${stats.rohs_icb_jobs}</div>
                <div class="stat-label">RoHS ICB</div>
            </div>
            <div class="stat-card rohs-ribbon">
                <div class="stat-value">${stats.rohs_ribbon_jobs}</div>
                <div class="stat-label">RoHS Ribbon</div>
            </div>
        `;

        container.innerHTML = statsHTML;
    }

    async loadJobs() {
        try {
            this.showLoading(true);
            
            const params = new URLSearchParams(this.filters);

            const response = await fetch(`/impact/rnd-cloudsphere/api/jobs?${params}`);
            const data = await response.json();
            
            if (data.success) {
                this.jobs = data.data;
                this.renderJobs(data.data);
                if (data.data.length === 0) {
                    this.showMessage('info', 'No jobs found matching your criteria.');
                }
            } else {
                this.showMessage('error', data.message || 'Failed to load jobs');
            }
        } catch (error) {
            console.error('Error loading jobs:', error);
            this.showMessage('error', 'Error loading jobs');
        } finally {
            this.showLoading(false);
        }
    }

    renderJobs(jobs) {
        const container = document.getElementById('jobsContainer');
        const emptyState = document.getElementById('emptyState');
        
        if (!container) return;

        if (jobs.length === 0) {
            container.innerHTML = '';
            emptyState.style.display = 'block';
            return;
        }

        emptyState.style.display = 'none';

        const jobsHTML = jobs.map(job => this.createJobCard(job)).join('');
        container.innerHTML = `<div class="rnd-jobs-grid">${jobsHTML}</div>`;
    }

    getSampleIcon(sampleType) {
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

    createJobCard(job) {
        const progressPercentage = job.completion_percentage || 0;
        const progressClass = progressPercentage < 30 ? 'low' : progressPercentage < 70 ? 'medium' : 'high';
        const sampleTypeClass = job.sample_type.toLowerCase().replace(/\s+/g, '-');
        const priorityClass = job.priority_level;
        
        // Create dynamic PIC display
        const picDisplay = this.createPicDisplay(job.pic_assignments || [], job.current_pic_name);
        
        return `
            <div class="rnd-job-card" onclick="viewJobDetail(${job.id})">
                <div class="sample-icon ${sampleTypeClass}">
                    ${this.getSampleIcon(job.sample_type)}
                </div>
                <div class="sample-type-label ${sampleTypeClass}">${job.sample_type}</div>
                
                <div class="priority-badge-new ${priorityClass}">${job.priority_level}</div>
                <div class="deadline-display ${job.is_overdue ? 'overdue' : ''}">
                    <i class="fas fa-clock"></i> ${this.formatDeadline(job.deadline_at)}
                </div>
                
                <div class="card-content">
                    <div class="pic-name">${picDisplay}</div>
                    <div class="item-name">${job.item_name}</div>
                    
                    <div class="progress-container">
                        <div class="progress-track">
                            <div class="progress-fill-new ${progressClass}" style="width: ${progressPercentage}%"></div>
                        </div>
                        <div class="progress-text">${Math.round(progressPercentage)}%</div>
                    </div>
                    
                    <div class="card-actions">
                        <div class="view-button" onclick="event.stopPropagation(); viewJobDetail(${job.id})">
                            <i class="fas fa-eye me-1"></i> View
                        </div>
                        ${window.currentUserRole === 'admin' ? `
                            <div class="edit-button" onclick="event.stopPropagation(); editJob(${job.id})">
                                <i class="fas fa-edit"></i>
                            </div>
                            <div class="delete-button" onclick="event.stopPropagation(); deleteJob(${job.id})">
                                <i class="fas fa-trash"></i>
                            </div>
                        ` : ''}
                    </div>
                </div>
            </div>
        `;
    }

    createPicDisplay(picAssignments, currentPicName) {
        if (!picAssignments || picAssignments.length === 0) {
            return '<span class="text-muted">Unassigned</span>';
        }
        
        // Get unique PIC names from all assignments
        const uniquePicNames = [...new Set(picAssignments.map(assignment => assignment.pic_name))];
        
        // Join PIC names with comma
        const picNamesString = uniquePicNames.join(', ');
        
        return `<div class="pic-names-simple">${picNamesString}</div>`;
    }

    formatDeadline(deadline) {
        if (!deadline) return 'No deadline';
        
        const date = new Date(deadline);
        const now = new Date();
        const diffTime = date - now;
        const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24));
        
        if (diffDays < 0) {
            return `${Math.abs(diffDays)} days overdue`;
        } else if (diffDays === 0) {
            return 'Due today';
        } else if (diffDays === 1) {
            return 'Due tomorrow';
        } else {
            return `${diffDays} days left`;
        }
    }


    async loadUsers() {
        try {
            // Check if users are already cached
            if (this.cachedUsers) {
                this.populateUserSelects(this.cachedUsers);
                return;
            }
            
            const response = await fetch('/impact/rnd-cloudsphere/api/users');
            const data = await response.json();
            
            if (data.success) {
                // Cache users for future use
                this.cachedUsers = data.data;
                this.populateUserSelects(data.data);
            }
        } catch (error) {
            console.error('Error loading users:', error);
        }
    }

    populateUserSelects(users) {
        const picSelect = document.getElementById('pic_id');
        const editPicSelect = document.getElementById('edit_pic_id');
        
        if (picSelect) {
            const options = '<option value="">Select PIC</option>' + 
                users.map(user => `<option value="${user.id}">${user.name}</option>`).join('');
            picSelect.innerHTML = options;
        }
        
        if (editPicSelect) {
            const options = '<option value="">Select PIC</option>' + 
                users.map(user => `<option value="${user.id}">${user.name}</option>`).join('');
            editPicSelect.innerHTML = options;
        }
    }

    async loadProgressSteps() {
        try {
            const sampleType = document.getElementById('sample_type').value;
            const flowConfigurationId = document.getElementById('flow_configuration_id').value;
            
            if (!sampleType) {
                document.getElementById('progressStepsContainer').innerHTML = '<p class="text-muted">Please select a sample type first</p>';
                return;
            }
            
            if (!flowConfigurationId) {
                document.getElementById('progressStepsContainer').innerHTML = '<p class="text-muted">Please select a flow configuration first</p>';
                return;
            }
            
            // Get progress steps for the specific flow configuration
            let url = `/impact/rnd-cloudsphere/api/progress-steps?sample_type=${encodeURIComponent(sampleType)}`;
            if (flowConfigurationId) {
                url += `&flow_configuration_id=${flowConfigurationId}`;
            }
            
            const response = await fetch(url);
            const data = await response.json();
            
            if (data.success) {
                // Use the flow returned by API to organize steps
                this.renderProgressFlow(data.data, 'progressStepsContainer');
            } else {
                document.getElementById('progressStepsContainer').innerHTML = `<p class="text-danger">${data.message || 'Failed to load progress steps'}</p>`;
            }
        } catch (error) {
            console.error('Error loading progress steps:', error);
            document.getElementById('progressStepsContainer').innerHTML = '<p class="text-danger">Error loading progress steps</p>';
        }
    }

    async loadFlowConfigurations() {
        try {
            const sampleType = document.getElementById('sample_type').value;
            if (!sampleType) {
                document.getElementById('flow_configuration_id').innerHTML = '<option value="">Select Sample Type First</option>';
                return;
            }
            
            const response = await fetch(`/impact/rnd-cloudsphere/api/flow-configurations?sample_type=${encodeURIComponent(sampleType)}&include_inactive=false`);
            const data = await response.json();
            
            if (data.success) {
                this.populateFlowConfigurationSelect(data.data, 'flow_configuration_id');
            } else {
                this.showMessage('error', data.message || 'Failed to load flow configurations');
            }
        } catch (error) {
            console.error('Error loading flow configurations:', error);
            this.showMessage('error', 'Error loading flow configurations');
        }
    }

    async loadEditFlowConfigurations() {
        try {
            const sampleType = document.getElementById('edit_sample_type').value;
            if (!sampleType) {
                document.getElementById('edit_flow_configuration_id').innerHTML = '<option value="">Select Sample Type First</option>';
                return;
            }
            
            const response = await fetch(`/impact/rnd-cloudsphere/api/flow-configurations?sample_type=${encodeURIComponent(sampleType)}&include_inactive=false`);
            const data = await response.json();
            
            if (data.success) {
                this.populateFlowConfigurationSelect(data.data, 'edit_flow_configuration_id');
            } else {
                this.showMessage('error', data.message || 'Failed to load flow configurations');
            }
        } catch (error) {
            console.error('Error loading flow configurations:', error);
            this.showMessage('error', 'Error loading flow configurations');
        }
    }

    populateFlowConfigurationSelect(configurations, selectId) {
        const select = document.getElementById(selectId);
        if (!select) return;
        
        let options = '<option value="">Select Flow Configuration</option>';
        
        if (configurations.length === 0) {
            options += '<option value="" disabled>No configurations available for this sample type</option>';
        } else {
            configurations.forEach(config => {
                const defaultBadge = config.is_default ? ' (Default)' : '';
                const activeBadge = config.is_active ? '' : ' (Inactive)';
                options += `<option value="${config.id}">${config.name}${defaultBadge}${activeBadge}</option>`;
            });
        }
        
        select.innerHTML = options;
        
        // Auto-select default configuration if available
        const defaultConfig = configurations.find(config => config.is_default);
        if (defaultConfig) {
            select.value = defaultConfig.id;
            // Auto-load progress steps for default configuration
            if (selectId === 'flow_configuration_id') {
                setTimeout(() => {
                    this.loadProgressSteps();
                }, 100);
            } else if (selectId === 'edit_flow_configuration_id') {
                const sampleType = document.getElementById('edit_sample_type').value;
                setTimeout(() => {
                    this.loadEditProgressSteps(sampleType);
                }, 100);
            }
        }
    }

    renderProgressFlow(allSteps, containerId) {
        const container = document.getElementById(containerId);
        if (!container) return;

        console.log('renderProgressFlow called with:', allSteps);

        if (!allSteps || allSteps.length === 0) {
            container.innerHTML = '<p class="text-muted">No progress steps available for this configuration.</p>';
            return;
        }

        const stagesHTML = allSteps.map((step, index) => {
            // Group tasks by their step
            const tasks = step.tasks.map(task => `
                <div class="form-check">
                    <input class="form-check-input task-checkbox" type="checkbox" value="${task.id}" data-step-id="${step.id}" id="task_${task.id}" checked>
                    <label class="form-check-label" for="task_${task.id}">
                        ${task.name}
                    </label>
                </div>
            `).join('');
           
            return `
                <div class="progress-stage-card" data-stage="${step.name}" data-stage-order="${step.step_order}">
                    <div class="stage-header">
                        <div class="stage-order">${step.step_order}</div>
                        <div class="stage-title">${step.name}</div>
                        ${step.is_required ? '<span class="badge required ms-2">Required</span>' : '<span class="badge bg-secondary ms-2">Optional</span>'}
                    </div>
                    <div class="mb-3">
                        <label class="form-label">PIC for this progress step</label>
                        <select class="form-select stage-pic-select" id="pic_${step.id}" required>
                            <option value="">Select PIC</option>
                        </select>
                    </div>
                    <div class="mb-3">
                        <label class="form-label">Tasks for this progress step</label>
                        <div class="step-group mb-3">
                            <h6 class="step-name">${step.name}</h6>
                            <div class="task-list">
                                ${tasks}
                            </div>
                        </div>
                    </div>
                </div>
            `;
        }).join('');

        container.innerHTML = `<div class="progress-stages-grid">${stagesHTML}</div>`;
        
        // Store allSteps in a variable accessible in setTimeout
        const allStepsCopy = allSteps;
        
        // Use setTimeout to ensure DOM is ready before populating selects
        setTimeout(() => {
            // Populate PIC selects for each step
            allSteps.forEach(step => {
                const picSelect = document.getElementById(`pic_${step.id}`);
                if (picSelect) {
                    this.populateUserSelect(picSelect);
                }
            });
        }, 100);
    }

    async populateUserSelect(selectElement) {
        try {
            // Check if users are already loaded to avoid duplicate API calls
            if (this.cachedUsers) {
                const options = '<option value="">Select PIC</option>' +
                    this.cachedUsers.map(user => `<option value="${user.id}">${user.name}</option>`).join('');
                selectElement.innerHTML = options;
                return;
            }
            
            const response = await fetch('/impact/rnd-cloudsphere/api/users');
            const data = await response.json();
            
            if (data.success) {
                // Cache users for future use
                this.cachedUsers = data.data;
                
                const options = '<option value="">Select PIC</option>' +
                    data.data.map(user => `<option value="${user.id}">${user.name}</option>`).join('');
                selectElement.innerHTML = options;
            } else {
                console.error('Failed to load users:', data.message);
            }
        } catch (error) {
            console.error('Error loading users:', error);
        }
    }

    async submitCreateJob() {
        try {
            const jobData = {
                item_name: document.getElementById('item_name').value,
                sample_type: document.getElementById('sample_type').value,
                priority_level: document.getElementById('priority_level').value,
                started_at: document.getElementById('started_at').value,
                deadline_at: document.getElementById('deadline_at').value,
                notes: document.getElementById('notes').value,
                flow_configuration_id: document.getElementById('flow_configuration_id').value,
                progress_assignments: []
            };
           
            // Validate required fields first
            if (!jobData.item_name) {
                this.showMessage('error', 'Item Name is required');
                return;
            }
            if (!jobData.sample_type) {
                this.showMessage('error', 'Sample Type is required');
                return;
            }
            if (!jobData.flow_configuration_id) {
                this.showMessage('error', 'Flow Configuration is required');
                return;
            }
            if (!jobData.priority_level) {
                this.showMessage('error', 'Priority Level is required');
                return;
            }
           
            // Get selected progress steps and their PICs
            const stepCards = document.querySelectorAll('#progressStepsContainer .progress-stage-card');
           
            stepCards.forEach(card => {
                const stepName = card.dataset.stage;
                const picSelect = card.querySelector('.stage-pic-select');
                const picId = picSelect ? picSelect.value : null;
               
                if (picId && stepName) {
                    // Get step ID from the first task checkbox in this step
                    const stepId = card.querySelector('.task-checkbox')?.dataset.stepId;
                    
                    if (stepId) {
                        // Get all task IDs for this step
                        const taskIds = [];
                        const taskCheckboxes = card.querySelectorAll('.task-checkbox:checked');
                       
                        taskCheckboxes.forEach(checkbox => {
                            taskIds.push(parseInt(checkbox.value));
                        });
                       
                        // Create assignment for this step
                        jobData.progress_assignments.push({
                            progress_step_id: parseInt(stepId),
                            pic_id: parseInt(picId),
                            task_ids: taskIds
                        });
                    }
                }
            });

            // Validate that at least one progress assignment is provided
            if (jobData.progress_assignments.length === 0) {
                this.showMessage('error', 'Please assign at least one PIC to the progress steps');
                return;
            }

            const response = await fetch('/impact/rnd-cloudsphere/api/job', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(jobData)
            });

            const data = await response.json();
           
            if (data.success) {
                this.showMessage('success', 'Job created successfully');
                bootstrap.Modal.getInstance(document.getElementById('createRNDJobModal')).hide();
                this.loadJobs();
                this.loadStats();
            } else {
                this.showMessage('error', data.message || 'Failed to create job');
            }
        } catch (error) {
            console.error('Error creating job:', error);
            this.showMessage('error', 'Error creating job');
        }
    }

    async loadJobForEdit(jobId) {
            // Load users first to ensure they're available for PIC selects
            await this.loadUsers();
        try {
            const response = await fetch(`/impact/rnd-cloudsphere/api/jobs/${jobId}`);
            const data = await response.json();
            
            if (data.success) {
                this.populateEditForm(data.data);
                // Load flow configurations first, then progress steps
                await this.loadEditFlowConfigurations();
                // Load progress steps for job's sample type and flow configuration
                this.loadEditProgressSteps(data.data.sample_type);
            } else {
                this.showMessage('error', data.message || 'Failed to load job');
            }
        } catch (error) {
            console.error('Error loading job:', error);
            this.showMessage('error', 'Error loading job');
        }
    }

    populateEditForm(job) {
        const editJobId = document.getElementById('editJobId');
        const editStartedAt = document.getElementById('edit_started_at');
        const editDeadlineAt = document.getElementById('edit_deadline_at');
        const editItemName = document.getElementById('edit_item_name');
        const editSampleType = document.getElementById('edit_sample_type');
        const editPriorityLevel = document.getElementById('edit_priority_level');
        const editStatus = document.getElementById('edit_status');
        const editNotes = document.getElementById('edit_notes');
        
        if (editJobId) editJobId.value = job.id;
        if (editStartedAt) editStartedAt.value = this.formatDateTimeForInput(job.started_at);
        if (editDeadlineAt) editDeadlineAt.value = this.formatDateTimeForInput(job.deadline_at);
        if (editItemName) editItemName.value = job.item_name || '';
        if (editSampleType) editSampleType.value = job.sample_type || '';
        if (editPriorityLevel) editPriorityLevel.value = job.priority_level || '';
        if (editStatus) editStatus.value = job.status || '';
        if (editNotes) editNotes.value = job.notes || '';
        
        // Store job data for later use in populating progress assignments
        this.currentEditJob = job;
        
        // Load flow configurations for the job's sample type
        if (job.sample_type) {
            this.loadEditFlowConfigurations().then(() => {
                // Set the flow configuration if job has one
                if (job.flow_configuration_id) {
                    const editFlowConfigSelect = document.getElementById('edit_flow_configuration_id');
                    if (editFlowConfigSelect) {
                        editFlowConfigSelect.value = job.flow_configuration_id;
                    }
                }
            });
        }
    }

    async loadEditProgressSteps(sampleType) {
        try {
            const flowConfigurationId = document.getElementById('edit_flow_configuration_id').value;
            
            if (!sampleType) {
                document.getElementById('editProgressStepsContainer').innerHTML = '<p class="text-muted">Please select a sample type first</p>';
                return;
            }
            
            if (!flowConfigurationId) {
                document.getElementById('editProgressStepsContainer').innerHTML = '<p class="text-muted">Please select a flow configuration first</p>';
                return;
            }
            
            // Get progress steps for specific flow configuration
            const response = await fetch(`/impact/rnd-cloudsphere/api/progress-steps?sample_type=${encodeURIComponent(sampleType)}&flow_configuration_id=${flowConfigurationId}`);
            const data = await response.json();
            
            if (data.success) {
                this.renderEditProgressFlow(data.data, null, 'editProgressStepsContainer');
            } else {
                this.showMessage('error', data.message || 'Failed to load progress steps');
            }
        } catch (error) {
            console.error('Error loading progress steps:', error);
            this.showMessage('error', 'Error loading progress steps');
        }
    }

    renderEditProgressFlow(allSteps, flow, containerId) {
        const container = document.getElementById(containerId);
        if (!container) return;

        console.log('renderEditProgressFlow called with:', allSteps, flow);

        if (!allSteps || allSteps.length === 0) {
            container.innerHTML = '<p class="text-muted">No progress steps available for this configuration.</p>';
            return;
        }

        const stagesHTML = allSteps.map((step, index) => {
            // Group tasks by their step
            const tasks = step.tasks.map(task => `
                <div class="form-check">
                    <input class="form-check-input task-checkbox" type="checkbox" value="${task.id}" data-step-id="${step.id}" id="edit_task_${task.id}" checked>
                    <label class="form-check-label" for="edit_task_${task.id}">
                        ${task.name}
                    </label>
                </div>
            `).join('');
           
            return `
                <div class="progress-stage-card" data-stage="${step.name}" data-stage-order="${step.step_order}">
                    <div class="stage-header">
                        <div class="stage-order">${step.step_order}</div>
                        <div class="stage-title">${step.name}</div>
                        ${step.is_required ? '<span class="badge required ms-2">Required</span>' : '<span class="badge bg-secondary ms-2">Optional</span>'}
                    </div>
                    <div class="mb-3">
                        <label class="form-label">PIC for this progress step</label>
                        <select class="form-select stage-pic-select" id="edit_pic_${step.id}" required>
                            <option value="">Select PIC</option>
                        </select>
                    </div>
                    <div class="mb-3">
                        <label class="form-label">Tasks for this progress step</label>
                        <div class="step-group mb-3">
                            <h6 class="step-name">${step.name}</h6>
                            <div class="task-list">
                                ${tasks}
                            </div>
                        </div>
                    </div>
                </div>
            `;
        }).join('');

        container.innerHTML = `<div class="progress-stages-grid">${stagesHTML}</div>`;
        
        // Store allSteps in a variable accessible in setTimeout
        const allStepsCopy = allSteps;
        
        // Use setTimeout to ensure DOM is ready before populating selects
        setTimeout(() => {
            // Populate PIC selects for each step
            allSteps.forEach(step => {
                const picSelect = document.getElementById(`edit_pic_${step.id}`);
                if (picSelect) {
                    this.populateUserSelect(picSelect);
                   
                    // Set selected PIC if we have job data
                    if (this.currentEditJob && this.currentEditJob.progress_assignments) {
                        const assignment = this.currentEditJob.progress_assignments.find(
                            pa => pa.progress_step_id === step.id
                        );
                       
                        if (assignment && assignment.pic_id) {
                            picSelect.value = assignment.pic_id;
                        }
                    }
                }
            });
        }, 100);
    }

    async submitEditJob() {
        try {
            const editJobId = document.getElementById('editJobId');
            const editStartedAt = document.getElementById('edit_started_at');
            const editDeadlineAt = document.getElementById('edit_deadline_at');
            const editItemName = document.getElementById('edit_item_name');
            const editSampleType = document.getElementById('edit_sample_type');
            const editPriorityLevel = document.getElementById('edit_priority_level');
            const editStatus = document.getElementById('edit_status');
            const editNotes = document.getElementById('edit_notes');
            
            const jobData = {
                id: editJobId ? editJobId.value : '',
                started_at: editStartedAt ? editStartedAt.value : '',
                deadline_at: editDeadlineAt ? editDeadlineAt.value : '',
                item_name: editItemName ? editItemName.value : '',
                sample_type: editSampleType ? editSampleType.value : '',
                priority_level: editPriorityLevel ? editPriorityLevel.value : '',
                status: editStatus ? editStatus.value : '',
                notes: editNotes ? editNotes.value : '',
                flow_configuration_id: document.getElementById('edit_flow_configuration_id').value,
                progress_assignments: []
            };
           
            // Validate required fields first
            if (!jobData.item_name) {
                this.showMessage('error', 'Item Name is required');
                return;
            }
            if (!jobData.sample_type) {
                this.showMessage('error', 'Sample Type is required');
                return;
            }
            if (!jobData.flow_configuration_id) {
                this.showMessage('error', 'Flow Configuration is required');
                return;
            }
            if (!jobData.priority_level) {
                this.showMessage('error', 'Priority Level is required');
                return;
            }
            if (!jobData.status) {
                this.showMessage('error', 'Status is required');
                return;
            }
           
            // Get selected progress steps and their PICs
            const stepCards = document.querySelectorAll('#editProgressStepsContainer .progress-stage-card');
           
            stepCards.forEach(card => {
                const stepName = card.dataset.stage;
                const picSelect = card.querySelector('.stage-pic-select');
                const picId = picSelect ? picSelect.value : null;
               
                if (picId && stepName) {
                    // Get step ID from the first task checkbox in this step
                    const stepId = card.querySelector('.task-checkbox')?.dataset.stepId;
                    
                    if (stepId) {
                        // Get all task IDs for this step
                        const taskIds = [];
                        const taskCheckboxes = card.querySelectorAll('.task-checkbox:checked');
                       
                        taskCheckboxes.forEach(checkbox => {
                            taskIds.push(parseInt(checkbox.value));
                        });
                       
                        // Create assignment for this step
                        jobData.progress_assignments.push({
                            progress_step_id: parseInt(stepId),
                            pic_id: parseInt(picId),
                            task_ids: taskIds
                        });
                    }
                }
            });

            // Validate that at least one progress assignment is provided
            if (jobData.progress_assignments.length === 0) {
                this.showMessage('error', 'Please assign at least one PIC to progress steps');
                return;
            }
            
            const response = await fetch(`/impact/rnd-cloudsphere/api/jobs/${jobData.id}`, {
                method: 'PUT',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(jobData)
            });

            const data = await response.json();
            
            if (data.success) {
                this.showMessage('success', 'Job updated successfully');
                bootstrap.Modal.getInstance(document.getElementById('editJobModal')).hide();
                this.loadJobs();
                this.loadStats();
            } else {
                this.showMessage('error', data.message || 'Failed to update job');
            }
        } catch (error) {
            console.error('Error updating job:', error);
            this.showMessage('error', 'Error updating job');
        }
    }

    async deleteJob(jobId) {
        try {
            const response = await fetch(`/impact/rnd-cloudsphere/api/jobs/${jobId}`, {
                method: 'DELETE'
            });

            const data = await response.json();
            
            if (data.success) {
                this.showMessage('success', 'Job deleted successfully');
                const deleteModal = bootstrap.Modal.getInstance(document.getElementById('deleteJobModal'));
                if (deleteModal) {
                    deleteModal.hide();
                }
                this.loadJobs();
                this.loadStats();
            } else {
                this.showMessage('error', data.message || 'Failed to delete job');
            }
        } catch (error) {
            console.error('Error deleting job:', error);
            this.showMessage('error', 'Error deleting job');
        }
    }

    showLoading(show) {
        const spinner = document.getElementById('loadingSpinner');
        const container = document.getElementById('jobsContainer');
        
        if (show) {
            spinner.style.display = 'block';
            container.style.display = 'none';
        } else {
            spinner.style.display = 'none';
            container.style.display = 'block';
        }
    }

    showMessage(type, message) {
        const toastEl = document.getElementById('liveToast');
        const toastBody = toastEl.querySelector('.message-text');
        
        toastBody.textContent = message;
        
        // Update toast styling based on type
        const toastBodyElement = toastEl.querySelector('.toast-body');
        toastBodyElement.className = `toast-body rounded text-white bg-${type === 'error' ? 'danger' : type === 'info' ? 'info' : 'success'}`;
        
        const toast = new bootstrap.Toast(toastEl);
        toast.show();
    }

    clearFilters() {
        this.filters = {
            status: '',
            priority: '',
            sample_type: '',
            search: ''
        };
        
        document.getElementById('statusFilter').value = '';
        document.getElementById('priorityFilter').value = '';
        document.getElementById('sampleTypeFilter').value = '';
        document.getElementById('searchInput').value = '';
        
        this.loadJobs();
    }

    // Helper function to format datetime for datetime-local input
    formatDateTimeForInput(dateTimeString) {
        if (!dateTimeString) return '';
        
        // Parse the datetime string (assuming it's in Jakarta timezone format 'YYYY-MM-DD HH:MM')
        const date = new Date(dateTimeString);
        
        // Check if date is valid
        if (isNaN(date.getTime())) return '';
        
        // Get the local date components
        const year = date.getFullYear();
        const month = String(date.getMonth() + 1).padStart(2, '0');
        const day = String(date.getDate()).padStart(2, '0');
        const hours = String(date.getHours()).padStart(2, '0');
        const minutes = String(date.getMinutes()).padStart(2, '0');
        
        // Return in the format required by datetime-local input (YYYY-MM-DDTHH:MM)
        return `${year}-${month}-${day}T${hours}:${minutes}`;
    }

    // Helper function to set default datetime values for create form
    setDefaultDateTimeValues() {
        const now = new Date();
        const startedAtInput = document.getElementById('started_at');
        const deadlineAtInput = document.getElementById('deadline_at');
        
        if (startedAtInput && !startedAtInput.value) {
            // Set started_at to current time
            startedAtInput.value = this.formatDateTimeForInput(now);
        }
        
        if (deadlineAtInput && !deadlineAtInput.value) {
            // Set deadline_at to 7 days from now
            const deadline = new Date(now.getTime() + (7 * 24 * 60 * 60 * 1000));
            deadlineAtInput.value = this.formatDateTimeForInput(deadline);
        }
    }
}

// Global functions for onclick handlers
function createNewRNDJob() {
    // Set default datetime values before showing modal
    if (rndCloudsphere) {
        rndCloudsphere.setDefaultDateTimeValues();
    }
    const modal = new bootstrap.Modal(document.getElementById('createRNDJobModal'));
    modal.show();
}

function loadProgressSteps() {
    const sampleType = document.getElementById('sample_type').value;
    if (sampleType && rndCloudsphere) {
        rndCloudsphere.loadProgressSteps();
    }
}

function loadEditProgressSteps() {
    const sampleType = document.getElementById('edit_sample_type').value;
    if (sampleType && rndCloudsphere) {
        rndCloudsphere.loadEditProgressSteps(sampleType);
    }
}

function loadFlowConfigurations() {
    const sampleType = document.getElementById('sample_type').value;
    if (sampleType && rndCloudsphere) {
        rndCloudsphere.loadFlowConfigurations();
    }
}

function loadEditFlowConfigurations() {
    const sampleType = document.getElementById('edit_sample_type').value;
    if (sampleType && rndCloudsphere) {
        rndCloudsphere.loadEditFlowConfigurations();
    }
}

function viewJobDetail(jobId) {
    window.location.href = `/impact/rnd-cloudsphere/job/${jobId}`;
}

function editJob(jobId) {
    if (rndCloudsphere) {
        rndCloudsphere.loadJobForEdit(jobId);
        const modal = new bootstrap.Modal(document.getElementById('editJobModal'));
        modal.show();
    }
}

function deleteJob(jobId) {
    const deleteJobIdElement = document.getElementById('deleteJobId');
    if (deleteJobIdElement) {
        deleteJobIdElement.value = jobId;
        const modal = new bootstrap.Modal(document.getElementById('deleteJobModal'));
        modal.show();
    }
}

function submitCreateJob() {
    if (rndCloudsphere) {
        rndCloudsphere.submitCreateJob();
    }
}

function submitEditJob() {
    if (rndCloudsphere) {
        rndCloudsphere.submitEditJob();
    }
}

function confirmDeleteJob() {
    const jobId = document.getElementById('deleteJobId').value;
    if (jobId && rndCloudsphere) {
        rndCloudsphere.deleteJob(jobId);
    }
}

function clearFilters() {
    if (rndCloudsphere) {
        rndCloudsphere.clearFilters();
    }
}

// Initialize application
let rndCloudsphere;
document.addEventListener('DOMContentLoaded', () => {
    rndCloudsphere = new RNDCloudsphere();
});