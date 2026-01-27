// R&D Cloudsphere Job Detail JavaScript
class RNDJobDetail {
    constructor() {
        this.jobId = window.jobId;
        this.job = null;
        this.jobData = null;  // Store complete job data for external delay handler
        this.progressSteps = [];
        this.evidenceFiles = [];
        this.externalDelayHandler = null;  // Will be initialized after loadJobDetail
        // Prevent repeated automatic finalize attempts
        this._completeIfReadyAttempted = false;
        this._lastCompleteIfReadyAttemptAt = 0; // epoch ms
        // Prevent repeated force-complete attempts by admin
        this._forceCompleteAttemptedAt = 0;
        this.init();
    }

    init() {
        if (!this.jobId || this.jobId === 'null') {
            this.showMessage('error', 'Invalid job ID');
            return;
        }

        this.loadJobDetail();
        this.setupEventListeners();
    }

    setupEventListeners() {
        // Add debounced window resize handler to recalculate connector positions
        let resizeTimeout;
        window.addEventListener('resize', () => {
            clearTimeout(resizeTimeout);
            resizeTimeout = setTimeout(() => {
                this.recalculateConnectorPositions();
            }, 250); // Debounce resize events
        });
    }

    async loadJobDetail() {
        // Prevent overlapping loads
        if (this._loadingJobDetail) return;
        this._loadingJobDetail = true;
        try {
            const response = await fetch(`/impact/rnd-cloudsphere/api/jobs/${this.jobId}`);
            const data = await response.json();
            
            if (data.success) {
                this.job = data.data;
                this.jobData = data.data;  // Store complete data for external delay handler
                
                // Job data loaded; details are available for rendering
                
                this.renderStepProcess().then(() => {
                    this.renderTasksByPic();
                    this.renderEvidenceByStep();
                    this.loadJobNotes();
                    this.calculateAndDisplayLeadTime();
                    
                    // Initialize external delay handler on first load
                    if (!this.externalDelayHandler) {
                        this.externalDelayHandler = new ExternalDelayHandler(this);
                        this.externalDelayHandler.init();
                    } else {
                        // Reload external delays on subsequent loads
                        this.externalDelayHandler.loadExternalDelays().then(() => {
                            this.externalDelayHandler.renderExternalDelayIndicators();
                        });
                    }
                    
                    // Recalculate connector positions after all content is rendered
                    setTimeout(() => {
                        this.recalculateConnectorPositions();
                    }, 200);
                    // After loading everything, if all assignments completed try to finalize.
                    // Admins will call force-complete; PICs will call complete-if-ready.
                    const allAssignmentsCompleted = this.job.progress_assignments && this.job.progress_assignments.length > 0 && this.job.progress_assignments.every(pa => pa.status === 'completed');
                    if (allAssignmentsCompleted) {
                        // Only try to finalize if the job is not already marked completed
                        if (this.job.status === 'completed') {
                            // nothing to do
                        } else if (window.currentUserRole === 'admin') {
                            // Admins will call force-complete, but avoid frequent retries
                            const now = Date.now();
                            if (now - this._forceCompleteAttemptedAt > 30000) { // 30s cooldown
                                this._forceCompleteAttemptedAt = now;
                                this.checkAndForceCompleteJob();
                            }
                        } else {
                            // If current user is a PIC for this job, attempt to finalize once (or after cooldown)
                            const picIds = (this.job.progress_assignments || []).map(pa => pa.pic_id).filter(id => id);
                            if (picIds.includes(Number(window.currentUserId))) {
                                const now = Date.now();
                                if (!this._completeIfReadyAttempted || (now - this._lastCompleteIfReadyAttemptAt) > 60000) {
                                    this._completeIfReadyAttempted = true;
                                    this._lastCompleteIfReadyAttemptAt = now;
                                    this.attemptCompleteIfReady();
                                }
                            }
                        }
                    }
                });
            } else {
                this.showMessage('error', data.message || 'Failed to load job detail');
            }
        } catch (error) {
            console.error('Error loading job detail:', error);
            this.showMessage('error', 'Error loading job detail');
        } finally {
            this._loadingJobDetail = false;
        }
    }

    /**
     * If all progress assignments are completed but job.status isn't 'completed',
     * attempt to force-complete the job using the server's debug/force endpoint.
     * This will only attempt the force-complete if the current user is an admin.
     */
    async checkAndForceCompleteJob() {
        try {
            const resp = await fetch(`/impact/rnd-cloudsphere/api/jobs/${this.jobId}/debug-status`);
            const data = await resp.json();

            if (!data.success) return;

            const info = data.data;

            // If server indicates all assignments are completed but job isn't marked completed
            if (info.all_completed && info.job_status !== 'completed') {
                // Only admins should run the force-complete endpoint; rate-limit by 30s
                if (window.currentUserRole === 'admin') {
                    const now = Date.now();
                    if (now - this._forceCompleteAttemptedAt < 30000) {
                        // skip due to cooldown
                        return;
                    }
                    this._forceCompleteAttemptedAt = now;

                    const completeResp = await fetch(`/impact/rnd-cloudsphere/api/jobs/${this.jobId}/force-complete`, {
                        method: 'POST'
                    });

                    const completeData = await completeResp.json();
                    if (completeData.success) {
                        // Refresh job details to reflect the new final status
                        setTimeout(() => this.loadJobDetail(), 200);
                    } else {
                        console.warn('Force complete failed:', completeData.error || completeData);
                    }
                }
            }
        } catch (error) {
            console.error('Error checking or forcing job completion:', error);
        }
    }

    async attemptCompleteIfReady() {
        try {
            const resp = await fetch(`/impact/rnd-cloudsphere/api/jobs/${this.jobId}/complete-if-ready`, {
                method: 'POST'
            });

            const data = await resp.json();
            if (resp.ok && data.success) {
                // Refresh details silently
                setTimeout(() => this.loadJobDetail(), 200);
            } else {
                // If not OK, log for debugging - could be 400 (not all completed) or 403 (not PIC)
                console.warn('complete-if-ready response:', resp.status, data);
            }
        } catch (error) {
            console.error('Error calling complete-if-ready:', error);
        }
    }

    async renderStepProcess() {
        const container = document.getElementById('stepProcessTimeline');
        if (!container) return;

        // Determine if job should be marked as completed based on flow configuration
        let isJobCompleted = this.job.status === 'completed';
        
        // If job is not marked as completed, check if all required steps are completed
        if (!isJobCompleted && this.job.progress_assignments && this.job.progress_assignments.length > 0) {
            // Check if all progress assignments are completed
            const allAssignmentsCompleted = this.job.progress_assignments.every(pa => pa.status === 'completed');
            
            // Get the final step name from the backend API
            const finalStepName = await this.getFinalStepName();
            const finalAssignment = this.job.progress_assignments.find(pa => pa.progress_step_name === finalStepName);
            const isFinalStepCompleted = finalAssignment && finalAssignment.status === 'completed';
            
            // Job is completed only if ALL assignments are completed
            // This ensures no steps are left uncompleted, regardless of which is final
            isJobCompleted = allAssignmentsCompleted;
            
        } else {
            // Job already marked as completed in backend or no assignments found
        }

        // Create a complete flow from Job Created to Job Finish
        const steps = [
            {
                id: 'job_created',
                name: 'Job Created',
                status: 'completed',
                created_at: this.job.created_at,
                started_at: this.job.started_at,
                is_job_created: true
            },
            ...this.job.progress_assignments.map(pa => ({
                id: pa.id,
                name: pa.progress_step_name,
                status: pa.status,
                pic_name: pa.pic_name,
                started_at: pa.started_at,
                finished_at: pa.finished_at,
                tasks: pa.tasks || [],
                is_process_step: true
            })),
            {
                id: 'job_finished',
                name: 'Job Finish',
                status: isJobCompleted ? 'completed' : 'pending',
                finished_at: this.job.finished_at,
                is_job_finished: true
            }
        ];

        // Create connectors with data attributes for dynamic positioning
        const connectorsHtml = steps.slice(0, -1).map((step, index) => {
            const status = step.status.replace(' ', '-');
            return `<div class="step-connector ${status}" data-step-index="${index}"></div>`;
        }).join('');

        // Create steps with data attributes for connector positioning
        const stepsHtml = steps.map((step, index) => {
            const statusClass = step.status.replace(' ', '-');
            const stepNumber = index + 1;
            
            // Handle different step types
            let stepMeta = '';
            
            if (step.is_job_created) {
                // Job Created step - show creation datetime
                // Job Created step - show creation datetime and started datetime
                let datetimeInfo = '';
                
                if (step.created_at) {
                    datetimeInfo += `
                        <div class="step-meta-item">
                            <i class="fas fa-calendar-plus"></i>
                            <span>Created: ${this.formatDate(step.created_at)}</span>
                        </div>
                    `;
                }
                
                if (step.started_at) {
                    datetimeInfo += `
                        <div class="step-meta-item">
                            <span>${this.formatDate(step.started_at)}</span>
                        </div>
                    `;
                }
                
                if (!datetimeInfo) {
                    datetimeInfo = `
                        <div class="step-meta-item">
                            <i class="fas fa-calendar"></i>
                            <span>No date available</span>
                        </div>
                    `;
                }
                
                stepMeta = `<div class="step-meta">${datetimeInfo}</div>`;
            } else if (step.is_process_step) {
                // Process step - show PIC and completion datetime (from progress assignment)
                let completionDatetime = '';
                
                // Use finished_at from progress assignment, not from tasks
                if (step.status === 'completed' && step.finished_at) {
                    completionDatetime = this.formatDate(step.finished_at);
                }
                
                stepMeta = `
                    <div class="step-meta">
                        ${step.pic_name ? `
                            <div class="step-meta-item">
                                <i class="fas fa-user"></i>
                                <span>${step.pic_name}</span>
                            </div>
                        ` : ''}
                        ${completionDatetime ? `
                            <div class="step-meta-item">
                                <span>${completionDatetime}</span>
                            </div>
                        ` : ''}
                    </div>
                `;
            } else if (step.is_job_finished) {
                // Job Finished step - show completion datetime if available
                stepMeta = `
                    <div class="step-meta">
                        ${step.finished_at ? `
                            <div class="step-meta-item">
                                <span>${this.formatDate(step.finished_at)}</span>
                            </div>
                        ` : ''}
                    </div>
                `;
            }
            
            return `
                <div class="process-step" data-step-index="${index}" ${step.is_process_step ? `data-progress-assignment-id="${step.id}"` : ''}>
                    <div class="step-indicator ${statusClass}">${stepNumber}</div>
                    <div class="step-content">
                        <div class="step-title">${step.name}</div>
                        ${stepMeta}
                    </div>
                </div>
            `;
        }).join('');

        // Interleave connectors and steps: STEP - CONNECTOR - STEP - CONNECTOR - STEP...
        let timelineContent = '';
        for (let i = 0; i < steps.length; i++) {
            // Add step
            timelineContent += stepsHtml.split('</div>')[0].split('><')[i]?.match(/^<div[^>]*>[\s\S]*?<\/div>$/) || '';
        }
        
        // Actually, let's rebuild with proper interleaving
        const stepsArray = steps.map((step, index) => {
            const statusClass = step.status.replace(' ', '-');
            const stepNumber = index + 1;
            let stepMeta = '';
            
            if (step.is_job_created) {
                let datetimeInfo = '';
                if (step.created_at) {
                    datetimeInfo += `
                        <div class="step-meta-item">
                            <i class="fas fa-calendar-plus"></i>
                            <span>Created: ${this.formatDate(step.created_at)}</span>
                        </div>
                    `;
                }
                if (step.started_at) {
                    datetimeInfo += `
                        <div class="step-meta-item">
                            <span>${this.formatDate(step.started_at)}</span>
                        </div>
                    `;
                }
                if (!datetimeInfo) {
                    datetimeInfo = `
                        <div class="step-meta-item">
                            <i class="fas fa-calendar"></i>
                            <span>No date available</span>
                        </div>
                    `;
                }
                stepMeta = `<div class="step-meta">${datetimeInfo}</div>`;
            } else if (step.is_process_step) {
                let completionDatetime = '';
                if (step.status === 'completed' && step.finished_at) {
                    completionDatetime = this.formatDate(step.finished_at);
                }
                stepMeta = `
                    <div class="step-meta">
                        ${step.pic_name ? `
                            <div class="step-meta-item">
                                <i class="fas fa-user"></i>
                                <span>${step.pic_name}</span>
                            </div>
                        ` : ''}
                        ${completionDatetime ? `
                            <div class="step-meta-item">
                                <span>${completionDatetime}</span>
                            </div>
                        ` : ''}
                    </div>
                `;
            } else if (step.is_job_finished) {
                stepMeta = `
                    <div class="step-meta">
                        ${step.finished_at ? `
                            <div class="step-meta-item">
                                <span>${this.formatDate(step.finished_at)}</span>
                            </div>
                        ` : ''}
                    </div>
                `;
            }
            
            return {
                html: `
                <div class="process-step" data-step-index="${index}" ${step.is_process_step ? `data-progress-assignment-id="${step.id}"` : ''}>
                    <div class="step-indicator ${statusClass}">${stepNumber}</div>
                    <div class="step-content">
                        <div class="step-title">${step.name}</div>
                        ${stepMeta}
                    </div>
                </div>
                `,
                index: index
            };
        });

        // Build interleaved HTML: step[0] - connector[0] - step[1] - connector[1] - ... - step[n]
        let timelineHTML = '<div class="horizontal-steps">';
        for (let i = 0; i < steps.length; i++) {
            // Add step
            timelineHTML += stepsArray[i].html;
            // Add connector after step (except after last step)
            if (i < steps.length - 1) {
                const connectorStatus = steps[i].status.replace(' ', '-');
                timelineHTML += `<div class="step-connector ${connectorStatus}" data-step-index="${i}"></div>`;
            }
        }
        timelineHTML += '</div>';

        container.innerHTML = timelineHTML;
        
        // Calculate connector positions after DOM is updated
        setTimeout(() => {
            this.recalculateConnectorPositions();
        }, 100);
    }

    recalculateConnectorPositions() {
        const horizontalSteps = document.querySelector('.horizontal-steps');
        if (!horizontalSteps) return;

        const steps = horizontalSteps.querySelectorAll('.process-step');
        const connectors = horizontalSteps.querySelectorAll('.step-connector');
        
        if (steps.length < 2 || connectors.length === 0) return;

        // Ensure container is visible and has dimensions
        const containerRect = horizontalSteps.getBoundingClientRect();
        if (containerRect.width === 0) {
            // If container is not visible, retry after a short delay
            setTimeout(() => this.recalculateConnectorPositions(), 100);
            return;
        }

        steps.forEach((step, index) => {
            if (index < steps.length - 1) {
                const connector = connectors[index];
                if (!connector) return;

                const currentStepIndicator = step.querySelector('.step-indicator');
                const nextStep = steps[index + 1];
                const nextStepIndicator = nextStep.querySelector('.step-indicator');

                if (currentStepIndicator && nextStepIndicator) {
                    // Get the center positions of step indicators
                    const currentRect = currentStepIndicator.getBoundingClientRect();
                    const nextRect = nextStepIndicator.getBoundingClientRect();

                    // Calculate positions relative to the container
                    const currentCenter = currentRect.left + (currentRect.width / 2) - containerRect.left;
                    const nextCenter = nextRect.left + (nextRect.width / 2) - containerRect.left;

                    // Position and size the connector
                    const leftPosition = currentCenter;
                    const width = Math.max(nextCenter - currentCenter, 1); // Ensure minimum width

                    // Apply calculated positions
                    connector.style.left = `${leftPosition}px`;
                    connector.style.width = `${width}px`;
                    connector.style.transform = 'none'; // Remove any transform
                    
                    // Ensure connector is visible
                    connector.style.opacity = '1';
                }
            }
        });
    }

    renderTasksByPic() {
        const container = document.getElementById('tasksByPic');
        if (!container) return;

        // Don't group by step name, but by individual assignment
        // This ensures each step process shows only its own tasks, even if multiple steps have the same name
        const assignments = [];
        
        this.job.progress_assignments.forEach(assignment => {
            // Only process assignments that are visible to current user
            if (!assignment.is_visible) {
                return;
            }
            
            // Only include tasks that belong to this specific progress assignment
            // This ensures tasks are correctly filtered by step process
            const assignmentTasks = assignment.tasks || [];
            
            assignments.push({
                step_name: assignment.progress_step_name,
                step_id: assignment.id,
                status: assignment.status,
                pic_name: assignment.pic_name || 'Unassigned',
                pic_id: assignment.pic_id,
                tasks: assignmentTasks  // Only tasks from this specific assignment/step
            });
        });

        // Create 3-column layout
        const tasksHTML = `
            <div class="row">
                ${assignments.map((assignment, index) => {
                    const columnClass = index % 3 === 0 ? 'col-md-4' : (index % 3 === 1 ? 'col-md-4' : 'col-md-4');
                    return `
                    <div class="${columnClass} mb-4">
                        <div class="step-tasks-group">
                            <div class="step-header">
                                <h5 class="step-name">${assignment.step_name}</h5>
                                <span class="step-status ${assignment.status.replace(' ', '-')}">
                                    ${assignment.status.replace('_', ' ').toUpperCase()}
                                </span>
                            </div>
                            <div class="pic-section mb-3">
                                <div class="pic-info-small">
                                    <div class="pic-avatar-small">${assignment.pic_name.charAt(0).toUpperCase()}</div>
                                    <span class="pic-name-small">${assignment.pic_name}</span>
                                </div>
                                <div class="task-list-small">
                                    ${assignment.tasks.map(task => `
                                        <div class="task-item-small">
                                            <input type="checkbox"
                                                   class="task-checkbox"
                                                   id="task_${task.id}"
                                                   ${task.status === 'completed' ? 'checked' : ''}
                                                   ${!this.canEditTask(task) ? 'disabled' : ''}
                                                   onchange="rndJobDetail.toggleTask(${task.id})">
                                            <div class="task-content-small">
                                                <label class="task-name-small" for="task_${task.id}">${task.task_name}</label>
                                                ${task.status === 'completed' && (task.completed_at || task.updated_at) ? `
                                                    <div class="task-datetime-small">
                                                        ${this.formatDate(task.completed_at || task.updated_at)}
                                                    </div>
                                                ` : ''}
                                            </div>
                                            <span class="task-status-small ${task.status === 'completed' ? 'completed' : 'pending'}" id="status_${task.id}">
                                                ${task.status.replace('_', ' ').toUpperCase()}
                                            </span>
                                        </div>
                                    `).join('')}
                                </div>
                            </div>
                        </div>
                    </div>
                `}).join('')}
            </div>
        `;

        // Show/hide no tasks message based on whether user has access to any tasks
        const noTasksMessage = document.getElementById('noTasksMessage');
        if (noTasksMessage) {
            if (assignments.length === 0) {
                noTasksMessage.style.display = 'block';
                container.innerHTML = '';
            } else {
                noTasksMessage.style.display = 'none';
                container.innerHTML = tasksHTML;
            }
        } else {
            container.innerHTML = tasksHTML || '<p>No tasks assigned</p>';
        }

        // Add event listeners to all checkboxes after rendering
        setTimeout(() => {
            this.attachCheckboxListeners();
        }, 100);
    }

    attachCheckboxListeners() {
        try {
            const checkboxes = document.querySelectorAll('.task-checkbox');
            checkboxes.forEach(checkbox => {
                // Remove existing listeners to avoid duplicates
                checkbox.removeEventListener('change', this.handleCheckboxChange);
                
                // Add new listener
                checkbox.addEventListener('change', (e) => {
                    const taskId = parseInt(e.target.id.replace('task_', ''));
                    this.handleCheckboxChange(taskId, e.target.checked);
                });
            });
        } catch (error) {
            console.error('Error attaching checkbox listeners:', error);
        }
    }

    handleCheckboxChange(taskId, isChecked) {
        try {
            // Update UI immediately for responsiveness
            const statusElement = document.getElementById(`status_${taskId}`);
            if (statusElement) {
                if (isChecked) {
                    statusElement.textContent = 'COMPLETED';
                    statusElement.className = 'task-status-small completed';
                } else {
                    statusElement.textContent = 'PENDING';
                    statusElement.className = 'task-status-small pending';
                }
            }

            // Update task in our local data structure
            this.updateTaskInData(taskId, isChecked ? 'completed' : 'pending');

            // Then call the API to update the backend
            this.toggleTask(taskId);
        } catch (error) {
            console.error('Error handling checkbox change:', error);
        }
    }

    renderEvidenceByStep() {
        const container = document.getElementById('evidenceByStep');
        if (!container) return;

        // Group evidence files by step, but only show steps visible to current user
        const stepEvidenceGroups = {};
        
        // Initialize with visible steps only
        this.job.progress_assignments.forEach(assignment => {
            // Only include assignments that are visible to current user
            if (!assignment.is_visible) {
                return;
            }
            
            stepEvidenceGroups[assignment.id] = {
                step_id: assignment.id,
                step_name: assignment.progress_step_name,
                status: assignment.status,
                evidence_files: [],
                pic_id: assignment.pic_id
            };
        });

        // Add evidence files to their respective steps
        this.job.evidence_files.forEach(file => {
            if (file.job_progress_assignment_id && stepEvidenceGroups[file.job_progress_assignment_id]) {
                stepEvidenceGroups[file.job_progress_assignment_id].evidence_files.push(file);
            }
        });

        const evidenceHTML = Object.values(stepEvidenceGroups).map(stepGroup => {
            // Check if current user can upload evidence for this step
            const canUploadEvidence = window.currentUserRole === 'admin' || stepGroup.pic_id == window.currentUserId;
            
            return `
            <div class="step-evidence-group">
                <div class="step-evidence-header">
                    <h5 class="step-evidence-title">${stepGroup.step_name}</h5>
                    <span class="step-status ${stepGroup.status.replace(' ', '-')}">
                        ${stepGroup.status.replace('_', ' ').toUpperCase()}
                    </span>
                </div>
                <div class="evidence-grid">
                    ${stepGroup.evidence_files.map(file => `
                        <div class="evidence-card">
                            <div class="preview-container">
                                ${this.isImageFile(file.file_type) ? `
                                    <img src="/impact/rnd-cloudsphere/api/evidence-thumbnail/${file.id}"
                                         alt="${file.original_filename}"
                                         class="evidence-thumbnail"
                                         onclick="rndJobDetail.previewFile(${file.id}, '${file.original_filename}', '${file.file_type}')"
                                         onerror="this.src='/static/img/image-placeholder.png'; this.alt='Thumbnail not available';">
                                    <span class="file-type-badge">${file.file_type === 'photo' ? 'PHOTO' : file.file_type.toUpperCase()}</span>
                                ` : this.isPdfFile(file.file_type) || this.isPdfByFilename(file.original_filename) ? `
                                    <div class="pdf-preview" onclick="rndJobDetail.previewFile(${file.id}, '${file.original_filename}', '${file.file_type}')">
                                        <img src="/impact/rnd-cloudsphere/api/evidence-thumbnail/${file.id}"
                                             alt="${file.original_filename}"
                                             class="evidence-thumbnail"
                                             onerror="this.style.display='none'; this.nextElementSibling.style.display='flex';">
                                        <i class="fas fa-file-pdf" style="display:none;"></i>
                                    </div>
                                    <span class="file-type-badge">PDF</span>
                                ` : `
                                    <div class="evidence-icon">
                                        <i class="fas ${this.getFileIcon(file.file_type)}"></i>
                                    </div>
                                `}
                            </div>
                            <div class="evidence-name">${file.original_filename}</div>
                            <div class="evidence-meta">
                                ${this.formatDate(file.uploaded_at)}<br>
                                ${file.uploader_name || 'Unknown'}
                            </div>
                            <div class="evidence-actions">
                                <button class="btn btn-sm btn-outline-primary" onclick="rndJobDetail.downloadEvidence(${file.id})">
                                    <i class="fas fa-download"></i>
                                </button>
                                ${(window.currentUserRole === 'admin' || (file.uploaded_by === Number(window.currentUserId))) ? `
                                    <button class="btn btn-sm btn-outline-danger" onclick="rndJobDetail.deleteEvidence(${file.id})" title="Delete evidence">
                                        <i class="fas fa-trash"></i>
                                    </button>
                                ` : ''}
                            </div>
                        </div>
                    `).join('')}
                </div>
                ${this.canUploadEvidenceForStep(stepGroup) ? `
                    <div class="upload-area" onclick="rndJobDetail.uploadEvidenceForStep(${stepGroup.step_id})" id="uploadArea_${stepGroup.step_id}">
                        <div class="upload-content">
                            <i class="fas fa-cloud-upload-alt fa-2x mb-2"></i>
                            <h6>Upload Evidence for ${stepGroup.step_name}</h6>
                            <p class="text-muted mb-0">Click to browse, drag and drop files, or paste image (Ctrl+V)</p>
                        </div>
                        <input type="file" id="fileInput_${stepGroup.step_id}" style="display: none;" multiple accept=".pdf,.docx,.xlsx,.jpg,.jpeg,.png">
                        <div class="paste-indicator" id="pasteIndicator_${stepGroup.step_id}" style="display: none;">
                            <i class="fas fa-paste fa-2x mb-2 text-primary"></i>
                            <h6 class="text-primary">Image detected in clipboard!</h6>
                            <p class="text-muted mb-0">Click here to paste the image</p>
                        </div>
                    </div>
                ` : ''}
            </div>
        `}).join('');

        // Show/hide no evidence message based on whether user has access to any evidence
        const noEvidenceMessage = document.getElementById('noEvidenceMessage');
        if (noEvidenceMessage) {
            if (Object.keys(stepEvidenceGroups).length === 0) {
                noEvidenceMessage.style.display = 'block';
                container.innerHTML = '';
            } else {
                noEvidenceMessage.style.display = 'none';
                container.innerHTML = evidenceHTML || '<p>No evidence files available</p>';
            }
        } else {
            container.innerHTML = evidenceHTML || '<p>No evidence files available</p>';
        }
        
        // Setup drag and drop for completed steps
        this.setupDragAndDrop();
    }

    setupDragAndDrop() {
        this.job.progress_assignments.forEach(assignment => {
            // Only setup drag and drop for visible assignments
            if (assignment.is_visible) {
                // Check if this assignment should have upload area
                const stepGroup = {
                    step_id: assignment.id,
                    pic_id: assignment.pic_id,
                    status: assignment.status,
                    tasks: assignment.tasks || []
                };
                
                if (this.canUploadEvidenceForStep(stepGroup)) {
                    const uploadArea = document.getElementById(`uploadArea_${assignment.id}`);
                    const fileInput = document.getElementById(`fileInput_${assignment.id}`);
                    const pasteIndicator = document.getElementById(`pasteIndicator_${assignment.id}`);
                    
                    if (uploadArea && fileInput) {
                        fileInput.addEventListener('change', (e) => {
                            this.handleFileSelect(e.target.files, assignment.id);
                        });

                        uploadArea.addEventListener('dragover', (e) => {
                            e.preventDefault();
                            uploadArea.classList.add('dragover');
                        });

                        uploadArea.addEventListener('dragleave', () => {
                            uploadArea.classList.remove('dragover');
                        });

                        uploadArea.addEventListener('drop', (e) => {
                            e.preventDefault();
                            uploadArea.classList.remove('dragover');
                            this.handleFileSelect(e.dataTransfer.files, assignment.id);
                        });
                        
                        // Setup paste indicator click handler
                        if (pasteIndicator) {
                            pasteIndicator.addEventListener('click', (e) => {
                                e.stopPropagation();
                                this.handlePasteFromClipboard(assignment.id);
                            });
                        }
                    }
                }
            }
        });
        
        // Setup global paste event listener
        this.setupGlobalPasteListener();
    }

    async handleFileSelect(files, stepId) {
        if (files.length === 0) return;

        try {
            // Check if any of the files are pasted images
            const hasPastedImage = Array.from(files).some(file =>
                file.name.startsWith('pasted_image_')
            );
            
            if (hasPastedImage) {
                this.showMessage('info', 'Processing pasted image...');
            } else {
                this.showMessage('info', 'Uploading files...');
            }
            
            // Upload files one by one to match the API which expects single file
            let allSuccessful = true;
            let uploadedCount = 0;
            
            for (let i = 0; i < files.length; i++) {
                const formData = new FormData();
                formData.append('file', files[i]);
                formData.append('job_id', this.jobId);
                formData.append('progress_assignment_id', stepId);
                formData.append('evidence_type', 'step_completion');
                
                const response = await fetch(`/impact/rnd-cloudsphere/api/upload-evidence`, {
                    method: 'POST',
                    body: formData
                });

                const data = await response.json();
                
                if (data.success) {
                    uploadedCount++;
                } else {
                    this.showMessage('error', `Failed to upload ${files[i].name}: ${data.message || 'Unknown error'}`);
                    allSuccessful = false;
                }
            }
            
            if (allSuccessful) {
                if (hasPastedImage) {
                    this.showMessage('success', `Pasted image uploaded successfully`);
                } else {
                    this.showMessage('success', `All ${uploadedCount} files uploaded successfully`);
                }
            } else if (uploadedCount > 0) {
                this.showMessage('warning', `${uploadedCount} of ${files.length} files uploaded successfully`);
            }
            
            this.loadJobDetail(); // Reload to show new evidence
        } catch (error) {
            console.error('Error uploading files:', error);
            this.showMessage('error', 'Error uploading files');
        }
    }

    setupGlobalPasteListener() {
        // Store reference to current instance for use in event listener
        const self = this;
        
        // Add paste event listener to document
        document.addEventListener('paste', function(e) {
            // Check if clipboard contains image data
            const items = e.clipboardData.items;
            let hasImage = false;
            
            for (let i = 0; i < items.length; i++) {
                if (items[i].type.indexOf('image') !== -1) {
                    hasImage = true;
                    break;
                }
            }
            
            if (hasImage) {
                // Find the first visible upload area
                const uploadAreas = document.querySelectorAll('.upload-area');
                let targetUploadArea = null;
                let targetStepId = null;
                
                for (let area of uploadAreas) {
                    if (area.style.display !== 'none' && area.offsetParent !== null) {
                        // Check if this upload area belongs to a step that can upload
                        const stepId = area.id.replace('uploadArea_', '');
                        const assignment = self.job.progress_assignments.find(pa => pa.id == stepId);
                        
                        if (assignment) {
                            const stepGroup = {
                                step_id: assignment.id,
                                pic_id: assignment.pic_id,
                                status: assignment.status,
                                tasks: assignment.tasks || []
                            };
                            
                            if (self.canUploadEvidenceForStep(stepGroup)) {
                                targetUploadArea = area;
                                targetStepId = stepId;
                                break;
                            }
                        }
                    }
                }
                
                if (targetUploadArea && targetStepId) {
                    e.preventDefault();
                    
                    // Show paste indicator
                    const pasteIndicator = document.getElementById(`pasteIndicator_${targetStepId}`);
                    if (pasteIndicator) {
                        pasteIndicator.style.display = 'flex';
                        targetUploadArea.classList.add('paste-active');
                        
                        // Auto-hide after 5 seconds
                        setTimeout(() => {
                            pasteIndicator.style.display = 'none';
                            targetUploadArea.classList.remove('paste-active');
                        }, 5000);
                    }
                }
            }
        });
    }

    async handlePasteFromClipboard(stepId) {
        try {
            // Get clipboard data
            const clipboardItems = await navigator.clipboard.read();
            
            for (const clipboardItem of clipboardItems) {
                for (const type of clipboardItem.types) {
                    if (type.startsWith('image/')) {
                        const blob = await clipboardItem.getType(type);
                        
                        // Create a File object from the blob
                        const timestamp = new Date().toISOString().slice(0, 19).replace(/[:-]/g, '');
                        const extension = type.split('/')[1] || 'png';
                        const filename = `pasted_image_${timestamp}.${extension}`;
                        
                        const file = new File([blob], filename, { type: type });
                        
                        // Hide paste indicator
                        const pasteIndicator = document.getElementById(`pasteIndicator_${stepId}`);
                        const uploadArea = document.getElementById(`uploadArea_${stepId}`);
                        
                        if (pasteIndicator) {
                            pasteIndicator.style.display = 'none';
                        }
                        if (uploadArea) {
                            uploadArea.classList.remove('paste-active');
                        }
                        
                        // Handle the pasted file
                        this.handleFileSelect([file], stepId);
                        
                        return;
                    }
                }
            }
            
            this.showMessage('warning', 'No image found in clipboard');
        } catch (error) {
            console.error('Error pasting from clipboard:', error);
            this.showMessage('error', 'Failed to paste image from clipboard');
        }
    }

    uploadEvidenceForStep(stepId) {
        const fileInput = document.getElementById(`fileInput_${stepId}`);
        if (fileInput) {
            fileInput.click();
        }
    }

    async toggleTask(taskId, showToast = true) {
        try {
            const response = await fetch(`/impact/rnd-cloudsphere/api/tasks/${taskId}/toggle`, {
                method: 'POST'
            });

            const data = await response.json();
            
            if (data.success) {
                // Check if task was completed and all tasks in step are completed
                const checkbox = document.getElementById(`task_${taskId}`);
                const wasChecked = checkbox && checkbox.checked;
                
                if (wasChecked) {
                    // Task was just completed, reload data to check for auto-progress
                    this.showMessage('success', 'Task completed successfully');
                    
                    // Try to auto-complete external delay if applicable
                    if (this.externalDelayHandler) {
                        await this.externalDelayHandler.autoCompleteExternalDelay(taskId);
                    }
                    
                    // Reload full data immediately to show auto-progress
                    setTimeout(() => {
                        this.loadJobDetail();
                    }, 300); // Shorter delay for faster UI update
                    
                    // Update lead time after task completion
                    setTimeout(() => {
                        this.calculateAndDisplayLeadTime();
                    }, 350);
                    // Also proactively ask server to finalize the job if appropriate
                    // (this will be a no-op for non-admin users)
                    setTimeout(() => {
                        if (window.currentUserRole === 'admin') {
                            this.checkAndForceCompleteJob();
                        } else {
                            // Non-admin (PIC) attempt finalize via complete-if-ready
                            this.attemptCompleteIfReady();
                        }
                    }, 500);
                } else {
                    // Task was uncompleted, just update UI
                    if (showToast) {
                        this.showMessage('success', 'Task status updated successfully');
                    }
                }
            } else {
                // Revert UI change if API call failed
                const checkbox = document.getElementById(`task_${taskId}`);
                if (checkbox) {
                    checkbox.checked = !checkbox.checked;
                    this.updateTaskUI(taskId);
                }

                // Show error message
                if (showToast) {
                    this.showMessage('error', data.error || 'Failed to update task status');
                }
            }
        } catch (error) {
            console.error('Error toggling task:', error);
            // Revert UI change if API call failed
            const checkbox = document.getElementById(`task_${taskId}`);
            if (checkbox) {
                checkbox.checked = !checkbox.checked;
                this.updateTaskUI(taskId);
            }

            // Show error message
            if (showToast) {
                this.showMessage('error', 'Network error: Failed to update task status');
            }
        }
    }

    updateTaskUI(taskId) {
        try {
            // Find the checkbox element
            const checkbox = document.getElementById(`task_${taskId}`);
            if (!checkbox) return;

            // Find the status element
            const statusElement = document.getElementById(`status_${taskId}`);
            if (!statusElement) return;

            // Toggle checkbox state
            const isChecked = checkbox.checked;
            
            // Update status text and class
            if (isChecked) {
                statusElement.textContent = 'COMPLETED';
                statusElement.className = 'task-status-small completed';
            } else {
                statusElement.textContent = 'PENDING';
                statusElement.className = 'task-status-small pending';
            }

            // Update the task in our local data structure
            this.updateTaskInData(taskId, isChecked ? 'completed' : 'pending');
        } catch (error) {
            console.error('Error updating task UI:', error);
        }
    }

    updateTaskInData(taskId, newStatus) {
        try {
            // Find and update the task in our job data
            if (this.job && this.job.progress_assignments) {
                this.job.progress_assignments.forEach(assignment => {
                    if (assignment.tasks) {
                        const task = assignment.tasks.find(t => t.id === taskId);
                        if (task) {
                            task.status = newStatus;
                            if (newStatus === 'completed') {
                                task.completed_at = new Date().toISOString();
                            } else {
                                task.completed_at = null;
                            }
                        }
                    }
                });
            }
        } catch (error) {
            console.error('Error updating task in data:', error);
        }
    }

    async downloadEvidence(fileId) {
        try {
            window.open(`/impact/rnd-cloudsphere/api/download-evidence/${fileId}`, '_blank');
        } catch (error) {
            console.error('Error downloading evidence:', error);
            this.showMessage('error', 'Error downloading evidence');
        }
    }

    async deleteEvidence(fileId) {
        // Find the evidence file details from our data
        let evidenceFile = null;
        if (this.job && this.job.evidence_files) {
            evidenceFile = this.job.evidence_files.find(file => file.id === fileId);
        }
        
        // Show evidence details in the modal
        const previewContainer = document.getElementById('deleteEvidencePreview');
        if (evidenceFile && previewContainer) {
            previewContainer.innerHTML = `
                <div class="card">
                    <div class="card-body">
                        <h6 class="card-title">${evidenceFile.original_filename}</h6>
                        <p class="card-text">
                            <small class="text-muted">
                                <i class="fas fa-user me-1"></i> ${evidenceFile.uploader_name || 'Unknown'}<br>
                                <i class="fas fa-calendar me-1"></i> ${this.formatDate(evidenceFile.uploaded_at)}
                            </small>
                        </p>
                    </div>
                </div>
            `;
        }
        
        // Store the file ID for the confirm button
        this.evidenceToDelete = fileId;
        
        // Show the modal
        const modal = new bootstrap.Modal(document.getElementById('deleteEvidenceModal'));
        modal.show();
    }
    
    async confirmDeleteEvidence() {
        if (!this.evidenceToDelete) return;
        
        try {
            const response = await fetch(`/impact/rnd-cloudsphere/api/evidence/${this.evidenceToDelete}`, {
                method: 'DELETE'
            });

            const data = await response.json();
            
            if (data.success) {
                this.showMessage('success', 'Evidence deleted successfully');
                this.loadJobDetail(); // Reload to update evidence section
                
                // Hide the modal
                const modal = bootstrap.Modal.getInstance(document.getElementById('deleteEvidenceModal'));
                if (modal) modal.hide();
            } else {
                this.showMessage('error', data.message || 'Failed to delete evidence');
            }
        } catch (error) {
            console.error('Error deleting evidence:', error);
            this.showMessage('error', 'Error deleting evidence');
        } finally {
            this.evidenceToDelete = null;
        }
    }

    /* TEMPORARILY HIDDEN: Approve/Reject functionality
    async approveJob() {
        if (!confirm('Are you sure you want to approve this job?')) {
            return;
        }

        try {
            const response = await fetch(`/impact/rnd-cloudsphere/api/jobs/${this.jobId}/approve`, {
                method: 'POST'
            });

            const data = await response.json();
            
            if (data.success) {
                this.showMessage('success', 'Job approved successfully');
                this.loadJobDetail();
            } else {
                this.showMessage('error', data.message || 'Failed to approve job');
            }
        } catch (error) {
            console.error('Error approving job:', error);
            this.showMessage('error', 'Error approving job');
        }
    }

    async rejectJob() {
        const reason = prompt('Please provide a reason for rejection:');
        if (!reason) {
            return;
        }

        try {
            const response = await fetch(`/impact/rnd-cloudsphere/api/jobs/${this.jobId}/reject`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ reason: reason })
            });

            const data = await response.json();
            
            if (data.success) {
                this.showMessage('success', 'Job rejected successfully');
                this.loadJobDetail();
            } else {
                this.showMessage('error', data.message || 'Failed to reject job');
            }
        } catch (error) {
            console.error('Error rejecting job:', error);
            this.showMessage('error', 'Error rejecting job');
        }
    }
    END HIDDEN */

    async exportPDF() {
        try {
            // Show loading message
            this.showMessage('info', 'Generating PDF...');
            
            // Create a temporary link element for download
            const response = await fetch(`/impact/rnd-cloudsphere/api/jobs/${this.jobId}/export/pdf`);
            
            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.error || 'Failed to generate PDF');
            }
            
            // Get the blob from response
            const blob = await response.blob();
            
            // Create a download link
            const url = window.URL.createObjectURL(blob);
            const link = document.createElement('a');
            link.href = url;
            link.download = `RND_Job_${this.job.job_id}_${new Date().toISOString().slice(0, 19).replace(/[:-]/g, '')}.pdf`;
            document.body.appendChild(link);
            link.click();
            document.body.removeChild(link);
            
            // Clean up the URL
            window.URL.revokeObjectURL(url);
            
            this.showMessage('success', 'PDF exported successfully');
        } catch (error) {
            console.error('Error exporting PDF:', error);
            this.showMessage('error', `Error exporting PDF: ${error.message}`);
        }
    }

    async forceCompleteJob() {
        // Removed: manual forceComplete from UI in favor of automatic/complete-if-ready flow
        console.warn('forceCompleteJob is deprecated and removed from UI');
    }

    goBack() {
        window.history.back();
    }

    canEditTask(task) {
        // Check if current user is admin
        if (window.currentUserRole === 'admin') {
            return true;
        }
        
        // Find the assignment that contains this task
        const assignment = this.job.progress_assignments.find(pa => {
            return pa.tasks && pa.tasks.some(t => t.id === task.id);
        });
        
        // Check if current user is the PIC for this assignment
        if (assignment && assignment.pic_id == window.currentUserId) {
            return true;
        }
        
        return false;
    }

    canUploadEvidenceForStep(stepGroup) {
        // Check if current user can upload evidence for this step
        const canUploadEvidence = window.currentUserRole === 'admin' || stepGroup.pic_id == window.currentUserId;
        
        if (!canUploadEvidence) {
            return false;
        }
        
        // Find the assignment for this step
        const assignment = this.job.progress_assignments.find(pa => pa.id === stepGroup.step_id);
        
        if (!assignment || !assignment.tasks) {
            return false;
        }
        
        // Check if at least one task is completed
        const hasCompletedTask = assignment.tasks.some(task => task.status === 'completed');
        
        return hasCompletedTask;
    }

    getFileIcon(fileType) {
        const iconMap = {
            'pdf': 'fa-file-pdf',
            'docx': 'fa-file-word',
            'xlsx': 'fa-file-excel',
            'jpg': 'fa-file-image',
            'jpeg': 'fa-file-image',
            'png': 'fa-file-image',
            'bmp': 'fa-file-image',
            'gif': 'fa-file-image',
            'webp': 'fa-file-image',
            'photo': 'fa-file-image',
            'document': 'fa-file-alt'
        };
        
        return iconMap[fileType] || 'fa-file';
    }

    isImageFile(fileType) {
        const imageTypes = ['jpg', 'jpeg', 'png', 'bmp', 'gif', 'webp', 'photo'];
        return imageTypes.includes(fileType ? fileType.toLowerCase() : '');
    }

    isPdfFile(fileType) {
        return fileType ? fileType.toLowerCase() === 'pdf' : false;
    }

    isPdfByFilename(fileName) {
        if (!fileName) return false;
        const extension = fileName.split('.').pop().toLowerCase();
        return extension === 'pdf';
    }

    async previewFile(fileId, fileName, fileType) {
        try {
            const modal = new bootstrap.Modal(document.getElementById('imagePreviewModal'));
            const modalTitle = document.getElementById('imagePreviewModalLabel');
            const imageContainer = document.getElementById('imagePreviewContainer');
            const pdfContainer = document.getElementById('pdfPreviewContainer');
            const downloadBtn = document.getElementById('downloadFileBtn');
            
            // Set modal title
            modalTitle.textContent = fileName;
            
            // Set download button
            downloadBtn.href = `/impact/rnd-cloudsphere/api/download-evidence/${fileId}`;
            downloadBtn.download = fileName;
            
            // Hide both containers first
            imageContainer.style.display = 'none';
            pdfContainer.style.display = 'none';
            
            if (this.isImageFile(fileType)) {
                // Show image preview with loading indicator
                imageContainer.innerHTML = `
                    <div class="text-center">
                        <div class="spinner-border text-primary" role="status">
                            <span class="visually-hidden">Loading...</span>
                        </div>
                        <p class="mt-2 text-muted">Loading image...</p>
                    </div>
                `;
                imageContainer.style.display = 'block';
                
                // Load full-size image
                const img = new Image();
                img.onload = () => {
                    imageContainer.innerHTML = `
                        <img src="/impact/rnd-cloudsphere/api/download-evidence/${fileId}"
                             alt="${fileName}"
                             class="evidence-preview"
                             style="max-width: 100%; max-height: 70vh; border-radius: 4px;">
                    `;
                };
                img.onerror = () => {
                    imageContainer.innerHTML = `
                        <div class="text-center p-4">
                            <i class="fas fa-exclamation-triangle fa-3x text-warning mb-3"></i>
                            <h5>Failed to load image</h5>
                            <p class="text-muted">Please try downloading the file instead.</p>
                        </div>
                    `;
                };
                img.src = `/impact/rnd-cloudsphere/api/download-evidence/${fileId}`;
                
            } else if (this.isPdfFile(fileType) || this.isPdfByFilename(fileName)) {
                // Open PDF in new tab with dedicated viewer
                window.open(`/impact/rnd-cloudsphere/pdf-viewer/${fileId}`, '_blank');
                return;
                
            } else {
                // For other file types, show download prompt
                imageContainer.innerHTML = `
                    <div class="text-center p-4">
                        <i class="fas fa-file fa-3x text-muted mb-3"></i>
                        <h5>${fileName}</h5>
                        <p class="text-muted">Preview not available for this file type.</p>
                        <p>Please download the file to view its contents.</p>
                        <div class="mt-3">
                            <button class="btn btn-primary" onclick="window.open('/impact/rnd-cloudsphere/api/download-evidence/${fileId}', '_blank')">
                                <i class="fas fa-download me-2"></i>Download File
                            </button>
                        </div>
                    </div>
                `;
                imageContainer.style.display = 'block';
            }
            
            // Show modal
            modal.show();
            
        } catch (error) {
            console.error('Error previewing file:', error);
            this.showMessage('error', 'Error previewing file');
        }
    }

    async loadPdfPreview(fileId, fileName, container) {
        try {
            // Check if PDF.js is loaded
            if (typeof pdfjsLib === 'undefined') {
                throw new Error('PDF.js library is not loaded');
            }
            
            // Load PDF using PDF.js
            const pdfUrl = `/impact/rnd-cloudsphere/api/download-evidence/${fileId}`;
            
            // Fetch PDF as array buffer
            const response = await fetch(pdfUrl);
            if (!response.ok) {
                throw new Error('Failed to load PDF');
            }
            
            const arrayBuffer = await response.arrayBuffer();
            
            // Load PDF with PDF.js
            const loadingTask = pdfjsLib.getDocument({data: arrayBuffer});
            const pdf = await loadingTask.promise;
            
            // Get first page
            const page = await pdf.getPage(1);
            
            // Set scale for better readability
            const scale = 1.5;
            const viewport = page.getViewport({ scale: scale });
            
            // Create canvas
            const canvas = document.createElement('canvas');
            const context = canvas.getContext('2d');
            canvas.height = viewport.height;
            canvas.width = viewport.width;
            
            // Render PDF page
            await page.render({
                canvasContext: context,
                viewport: viewport
            }).promise;
            
            // Display PDF in container
            container.innerHTML = `
                <div class="pdf-viewer">
                    <div class="pdf-controls mb-2">
                        <button class="btn btn-sm btn-outline-primary me-2" onclick="rndJobDetail.zoomPdf(0.8)">
                            <i class="fas fa-search-minus"></i> Zoom Out
                        </button>
                        <button class="btn btn-sm btn-outline-primary me-2" onclick="rndJobDetail.zoomPdf(1.2)">
                            <i class="fas fa-search-plus"></i> Zoom In
                        </button>
                        <button class="btn btn-sm btn-outline-secondary" onclick="rndJobDetail.downloadPdf('${pdfUrl}', '${fileName}')">
                            <i class="fas fa-download"></i> Download
                        </button>
                    </div>
                    <div class="pdf-canvas-container text-center">
                        <img src="${canvas.toDataURL()}" alt="${fileName}" class="pdf-canvas-image" style="max-width: 100%; height: auto; border: 1px solid #dee2e6; border-radius: 4px;">
                    </div>
                    <div class="pdf-info mt-2">
                        <small class="text-muted">
                            <i class="fas fa-info-circle me-1"></i>
                            Page 1 of ${pdf.numPages} | Scale: ${Math.round(scale * 100)}%
                        </small>
                    </div>
                </div>
            `;
            
            // Store PDF data for zoom functionality
            this.currentPdf = { pdf, page, scale, fileName, pdfUrl };
            
        } catch (error) {
            console.error('Error loading PDF with PDF.js:', error);
            // Fallback to iframe if PDF.js fails
            const pdfUrl = `/impact/rnd-cloudsphere/api/download-evidence/${fileId}`;
            container.innerHTML = `
                <div class="text-center p-4">
                    <i class="fas fa-file-pdf fa-3x text-danger mb-3"></i>
                    <h5>PDF Preview</h5>
                    <p class="text-muted">PDF preview failed to load.</p>
                    <div class="mt-3">
                        <button class="btn btn-primary" onclick="window.open('${pdfUrl}', '_blank')">
                            <i class="fas fa-external-link-alt me-2"></i>Open PDF in New Tab
                        </button>
                    </div>
                </div>
            `;
        }
    }

    async zoomPdf(newScale) {
        if (!this.currentPdf) return;
        
        try {
            // Check if PDF.js is loaded
            if (typeof pdfjsLib === 'undefined') {
                throw new Error('PDF.js library is not loaded');
            }
            
            // Update scale
            this.currentPdf.scale = Math.max(0.5, Math.min(3, newScale));
            
            // Re-render with new scale
            const viewport = this.currentPdf.page.getViewport({ scale: this.currentPdf.scale });
            
            const canvas = document.createElement('canvas');
            const context = canvas.getContext('2d');
            canvas.height = viewport.height;
            canvas.width = viewport.width;
            
            await this.currentPdf.page.render({
                canvasContext: context,
                viewport: viewport
            }).promise;
            
            // Update the image in the container
            const pdfContainer = document.getElementById('pdfPreviewContainer');
            const imgElement = pdfContainer.querySelector('.pdf-canvas-image');
            if (imgElement) {
                imgElement.src = canvas.toDataURL();
            }
            
            // Update scale info
            const scaleInfo = pdfContainer.querySelector('.pdf-info small');
            if (scaleInfo) {
                scaleInfo.innerHTML = `
                    <i class="fas fa-info-circle me-1"></i>
                    Page 1 of ${this.currentPdf.pdf.numPages} | Scale: ${Math.round(this.currentPdf.scale * 100)}%
                `;
            }
            
        } catch (error) {
            console.error('Error zooming PDF:', error);
            this.showMessage('error', 'Failed to zoom PDF');
        }
    }

    downloadPdf(url, fileName) {
        const link = document.createElement('a');
        link.href = url;
        link.download = fileName;
        link.target = '_blank';
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
    }

    formatDate(dateString) {
        if (!dateString) return null;
        
        const date = new Date(dateString);
        const months = ['Jan', 'Feb', 'Mar', 'Apr', 'Mei', 'Jun', 'Jul', 'Agu', 'Sep', 'Okt', 'Nov', 'Des'];
        const day = date.getDate();
        const month = months[date.getMonth()];
        const year = date.getFullYear();
        const hours = date.getHours().toString().padStart(2, '0');
        const minutes = date.getMinutes().toString().padStart(2, '0');
        
        return `${day} ${month} ${year} ${hours}:${minutes}`;
    }

    calculateAndDisplayLeadTime() {
        try {
            // Get the relevant dates
            const createdAt = this.job.created_at;
            const startedAt = this.job.started_at;
            const finishedAt = this.job.finished_at;
            const sampleType = this.job.sample_type;
            
            // Update the display elements
            const jobCreatedEl = document.getElementById('jobCreatedTime');
            const jobStartedEl = document.getElementById('jobStartedTime');
            const jobFinishedEl = document.getElementById('jobFinishedTime');
            const totalLeadTimeEl = document.getElementById('totalLeadTime');
            
            // Set the individual date displays
            if (jobCreatedEl && createdAt) {
                jobCreatedEl.textContent = this.formatDate(createdAt);
            } else if (jobCreatedEl) {
                jobCreatedEl.textContent = 'Not available';
            }
            
            if (jobStartedEl && startedAt) {
                jobStartedEl.textContent = this.formatDate(startedAt);
            } else if (jobStartedEl) {
                jobStartedEl.textContent = 'Not started';
            }
            
            if (jobFinishedEl && finishedAt) {
                jobFinishedEl.textContent = this.formatDate(finishedAt);
            } else if (jobFinishedEl) {
                jobFinishedEl.textContent = 'Not finished';
            }
            
            // Calculate lead time from Job Started to Job Finished
            if (totalLeadTimeEl) {
                if (startedAt && (finishedAt || true)) {
                    // Calculate from started to finished or now (in progress)
                    const endDate = finishedAt || new Date();
                    const leadTimeInMs = new Date(endDate) - new Date(startedAt);
                    const leadTimeInDays = leadTimeInMs / (1000 * 60 * 60 * 24);
                    
                    // Get max lead time based on sample type
                    const maxLeadTime = this.getMaxLeadTimeForSampleType(sampleType);
                    
                    // Calculate lead time status and color
                    const leadTimeStatus = this.calculateLeadTimeStatus(leadTimeInDays, maxLeadTime);
                    const leadTimeText = this.calculateDuration(startedAt, endDate);
                    
                    // Update display with appropriate styling
                    totalLeadTimeEl.innerHTML = `
                        <span class="lead-time-badge ${leadTimeStatus.class}">
                            ${leadTimeText}${!finishedAt ? ' (ongoing)' : ''}
                        </span>
                    `;
                } else {
                    totalLeadTimeEl.innerHTML = `
                        <span class="lead-time-badge good">Not available</span>
                    `;
                }
            }
        } catch (error) {
            console.error('Error calculating lead time:', error);
            const totalLeadTimeEl = document.getElementById('totalLeadTime');
            if (totalLeadTimeEl) {
                totalLeadTimeEl.textContent = 'Error calculating';
            }
        }
    
    }
    
    getMaxLeadTimeForSampleType(sampleType) {
        // Return max lead time in days based on sample type
        switch (sampleType) {
            case 'Blank':
                return 14; // Max 14 days
            case 'RoHS ICB':
                return 12; // Max 12 days
            case 'RoHS Ribbon':
                return 15; // Max 15 days
            default:
                return 14; // Default to 14 days
        }
    }
    
    calculateLeadTimeStatus(actualDays, maxDays) {
        // Calculate percentage of max lead time used
        const percentageUsed = (actualDays / maxDays) * 100;
        
        // Determine status based on percentage
        if (percentageUsed <= 70) {
            return {
                class: 'good',
                status: 'On Track'
            };
        } else if (percentageUsed <= 90) {
            return {
                class: 'warning',
                status: 'Warning'
            };
        } else {
            return {
                class: 'critical',
                status: 'Critical'
            };
        }
    }
    
    async getFinalStepName() {
        // Get the final step name from the backend API based on flow configuration
        try {
            const response = await fetch(`/impact/rnd-cloudsphere/api/jobs/${this.jobId}/final-step`);
            const data = await response.json();
            
            if (data.success) {
                // Final step information retrieved from API
                return data.data.final_step_name;
            } else {
                console.error('Failed to get final step:', data.error);
                // Fallback to static workflow
                return this.getStaticFinalStepName();
            }
        } catch (error) {
            console.error('Error getting final step:', error);
            // Fallback to static workflow
            return this.getStaticFinalStepName();
        }
    }
    
    getStaticFinalStepName() {
        // Fallback to static workflow
        const sampleType = this.job.sample_type;
        
        // Define the final step for each sample type workflow
        const finalSteps = {
            'RoHS Ribbon': 'Quality Validation',
            'RoHS ICB': 'Quality Validation',
            'Blank': 'Quality Validation'
        };
        
        return finalSteps[sampleType] || 'Quality Validation';
    }

    calculateDuration(startDate, endDate) {
        try {
            const start = new Date(startDate);
            const end = new Date(endDate);
            
            // Calculate difference in milliseconds
            const diffMs = end - start;
            
            // If negative difference, return error
            if (diffMs < 0) {
                return 'Invalid dates';
            }
            
            // Convert to days, hours, minutes
            const diffDays = Math.floor(diffMs / (1000 * 60 * 60 * 24));
            const diffHours = Math.floor((diffMs % (1000 * 60 * 60 * 24)) / (1000 * 60 * 60));
            const diffMinutes = Math.floor((diffMs % (1000 * 60 * 60)) / (1000 * 60));
            
            // Format the output
            let result = '';
            
            if (diffDays > 0) {
                result += `${diffDays} day${diffDays > 1 ? 's' : ''}`;
            }
            
            if (diffHours > 0) {
                if (result) result += ' ';
                result += `${diffHours} hour${diffHours > 1 ? 's' : ''}`;
            }
            
            if (diffMinutes > 0) {
                if (result) result += ' ';
                result += `${diffMinutes} minute${diffMinutes > 1 ? 's' : ''}`;
            }
            
            // If all components are 0, return "Less than 1 minute"
            if (!result) {
                result = 'Less than 1 minute';
            }
            
            return result;
        } catch (error) {
            console.error('Error calculating duration:', error);
            return 'Error calculating';
        }
    }

    showMessage(type, message) {
        // Try to find toast element with different possible IDs
        let toastEl = document.getElementById('liveToast');
        if (!toastEl) {
            toastEl = document.querySelector('.toast');
        }
        if (!toastEl) {
            console.error('Toast element not found, using alert fallback');
            alert(`${type.toUpperCase()}: ${message}`);
            return;
        }
        
        // Try to find message text element
        let toastBody = toastEl.querySelector('.message-text');
        if (!toastBody) {
            toastBody = toastEl.querySelector('.toast-body');
        }
        if (!toastBody) {
            console.error('Toast body element not found, using alert fallback');
            alert(`${type.toUpperCase()}: ${message}`);
            return;
        }
        
        toastBody.textContent = message;
        
        // Update toast styling based on type
        const toastBodyElement = toastEl.querySelector('.toast-body');
        if (toastBodyElement) {
            toastBodyElement.className = `toast-body rounded text-white bg-${type === 'error' ? 'danger' : type === 'info' ? 'info' : 'success'}`;
        }
        
        try {
            const toast = new bootstrap.Toast(toastEl);
            toast.show();
        } catch (e) {
            console.error('Error showing toast:', e);
            alert(`${type.toUpperCase()}: ${message}`);
        }
    }
}

// Global functions for onclick handlers
function goBack() {
    rndJobDetail.goBack();
}

function approveJob() {
    rndJobDetail.approveJob();
}

function rejectJob() {
    rndJobDetail.rejectJob();
}

function exportPDF() {
    rndJobDetail.exportPDF();
}

function forceCompleteJob() {
    // deprecated - removed from UI
    console.warn('forceCompleteJob global wrapper is deprecated');
}

// Initialize application
let rndJobDetail;
document.addEventListener('DOMContentLoaded', () => {
    rndJobDetail = new RNDJobDetail();
    
    // Add event listener for delete evidence confirmation button
    const confirmDeleteBtn = document.getElementById('confirmDeleteEvidenceBtn');
    if (confirmDeleteBtn) {
        confirmDeleteBtn.addEventListener('click', () => {
            rndJobDetail.confirmDeleteEvidence();
        });
    }
});

// Collaborative Notes Functions
RNDJobDetail.prototype.loadJobNotes = async function() {
    // Prevent parallel notes fetches
    if (this._loadingNotes) return;
    this._loadingNotes = true;
    try {
        const response = await fetch(`/impact/rnd-cloudsphere/api/jobs/${this.jobId}/notes`);
        const data = await response.json();
        
        if (data.success) {
            this.renderNotes(data.data);
        } else {
            console.error('Failed to load notes:', data.error);
            const notesList = document.getElementById('notesList');
            if (notesList) {
                notesList.innerHTML = '<div class="text-center text-muted py-3">Failed to load notes</div>';
            }
        }
    } catch (error) {
        console.error('Error loading notes:', error);
        const notesList = document.getElementById('notesList');
        if (notesList) {
            notesList.innerHTML = '<div class="text-center text-muted py-3">Error loading notes</div>';
        }
    } finally {
        this._loadingNotes = false;
    }
};

RNDJobDetail.prototype.renderNotes = function(notes) {
    const notesList = document.getElementById('notesList');
    if (!notesList) return;
    
    if (notes.length === 0) {
        notesList.innerHTML = '<div class="text-center text-muted py-3">No notes yet. Be the first to add a note!</div>';
        return;
    }
    
    const notesHTML = notes.map(note => `
        <div class="note-item ${note.is_pinned ? 'pinned' : ''}" id="note_${note.id}">
            <div class="note-header">
                <div class="note-author">
                    <div class="user-avatar-small me-2">${note.user_name.charAt(0).toUpperCase()}</div>
                    <div>
                        <div class="fw-bold">${note.user_name}</div>
                        <small class="text-muted">${this.formatDate(note.created_at)}</small>
                    </div>
                </div>
                <div class="note-meta">
                    ${note.is_pinned ? '<i class="fas fa-thumbtack pin-indicator me-2"></i>' : ''}
                    <span class="note-type-badge ${note.note_type}">${note.note_type}</span>
                </div>
            </div>
            <div class="note-content" id="noteContent_${note.id}">${note.note_content}</div>
            ${note.can_edit || note.can_delete ? `
                <div class="note-actions">
                    ${note.can_edit ? `
                        <button class="note-action-btn" onclick="rndJobDetail.editNote(${note.id})" title="Edit note">
                            <i class="fas fa-edit"></i> Edit
                        </button>
                    ` : ''}
                    ${note.can_delete ? `
                        <button class="note-action-btn delete" onclick="rndJobDetail.deleteNote(${note.id})" title="Delete note">
                            <i class="fas fa-trash"></i> Delete
                        </button>
                    ` : ''}
                    ${note.can_edit ? `
                        <button class="note-action-btn" onclick="rndJobDetail.togglePinNote(${note.id})" title="${note.is_pinned ? 'Unpin note' : 'Pin note'}">
                            <i class="fas fa-thumbtack"></i> ${note.is_pinned ? 'Unpin' : 'Pin'}
                        </button>
                    ` : ''}
                </div>
            ` : ''}
        </div>
    `).join('');
    
    notesList.innerHTML = notesHTML;
};

RNDJobDetail.prototype.addNote = async function() {
    const contentElement = document.getElementById('newNoteContent');
    const typeElement = document.getElementById('noteType');
    
    if (!contentElement || !typeElement) return;
    
    const content = contentElement.value.trim();
    const noteType = typeElement.value;
    
    if (!content) {
        this.showMessage('error', 'Please enter a note');
        return;
    }
    
    try {
        const response = await fetch(`/impact/rnd-cloudsphere/api/jobs/${this.jobId}/notes`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                note_content: content,
                note_type: noteType
            })
        });
        
        const data = await response.json();
        
        if (data.success) {
            // Clear form
            contentElement.value = '';
            typeElement.value = 'general';
            
            // Reload notes
            this.loadJobNotes();
            
            this.showMessage('success', 'Note added successfully');
        } else {
            this.showMessage('error', data.error || 'Failed to add note');
        }
    } catch (error) {
        console.error('Error adding note:', error);
        this.showMessage('error', 'Error adding note');
    }
};

RNDJobDetail.prototype.editNote = function(noteId) {
    const contentElement = document.getElementById(`noteContent_${noteId}`);
    if (!contentElement) return;
    
    const currentContent = contentElement.textContent.trim();
    
    // Replace content with edit form
    contentElement.innerHTML = `
        <div class="edit-note-form">
            <textarea class="edit-note-textarea" id="editNote_${noteId}" rows="4">${currentContent}</textarea>
            <div class="edit-note-actions">
                <button class="btn btn-sm btn-primary" onclick="rndJobDetail.saveEditNote(${noteId})">
                    <i class="fas fa-save me-1"></i> Save
                </button>
                <button class="btn btn-sm btn-secondary" onclick="rndJobDetail.cancelEditNote(${noteId})">
                    <i class="fas fa-times me-1"></i> Cancel
                </button>
            </div>
        </div>
    `;
    
    // Focus on textarea
    setTimeout(() => {
        const textarea = document.getElementById(`editNote_${noteId}`);
        if (textarea) {
            textarea.focus();
            textarea.setSelectionRange(textarea.value.length, textarea.value.length);
        }
    }, 100);
};

RNDJobDetail.prototype.saveEditNote = async function(noteId) {
    const textarea = document.getElementById(`editNote_${noteId}`);
    if (!textarea) return;
    
    const newContent = textarea.value.trim();
    
    if (!newContent) {
        this.showMessage('error', 'Note content cannot be empty');
        return;
    }
    
    try {
        const response = await fetch(`/impact/rnd-cloudsphere/api/jobs/notes/${noteId}`, {
            method: 'PUT',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                note_content: newContent
            })
        });
        
        const data = await response.json();
        
        if (data.success) {
            // Reload notes to show updated content
            this.loadJobNotes();
            this.showMessage('success', 'Note updated successfully');
        } else {
            this.showMessage('error', data.error || 'Failed to update note');
        }
    } catch (error) {
        console.error('Error updating note:', error);
        this.showMessage('error', 'Error updating note');
    }
};

RNDJobDetail.prototype.cancelEditNote = function(noteId) {
    // Reload notes to restore original content
    this.loadJobNotes();
};

RNDJobDetail.prototype.deleteNote = async function(noteId) {
    if (!confirm('Are you sure you want to delete this note?')) {
        return;
    }
    
    try {
        const response = await fetch(`/impact/rnd-cloudsphere/api/jobs/notes/${noteId}`, {
            method: 'DELETE'
        });
        
        const data = await response.json();
        
        if (data.success) {
            // Remove note from DOM
            const noteElement = document.getElementById(`note_${noteId}`);
            if (noteElement) {
                noteElement.remove();
            }
            
            this.showMessage('success', 'Note deleted successfully');
        } else {
            this.showMessage('error', data.error || 'Failed to delete note');
        }
    } catch (error) {
        console.error('Error deleting note:', error);
        this.showMessage('error', 'Error deleting note');
    }
};

RNDJobDetail.prototype.togglePinNote = async function(noteId) {
    try {
        const response = await fetch(`/impact/rnd-cloudsphere/api/jobs/notes/${noteId}/pin`, {
            method: 'PUT'
        });
        
        const data = await response.json();
        
        if (data.success) {
            // Reload notes to show updated pin status
            this.loadJobNotes();
            this.showMessage('success', data.message);
        } else {
            this.showMessage('error', data.error || 'Failed to update pin status');
        }
    } catch (error) {
        console.error('Error toggling pin:', error);
        this.showMessage('error', 'Error updating pin status');
    }
};

// Global function for add note button
function addNote() {
    if (typeof rndJobDetail !== 'undefined') {
        rndJobDetail.addNote();
    }
}