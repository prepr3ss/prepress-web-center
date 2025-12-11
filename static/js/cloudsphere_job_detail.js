// Cloudsphere Job Detail JavaScript
class CloudsphereJobDetail {
    constructor() {
        this.jobId = null;
        this.jobData = null;
        this.init();
    }

    init() {
        // Extract job ID from URL
        const pathParts = window.location.pathname.split('/');
        this.jobId = pathParts[pathParts.length - 1];
        
        if (this.jobId) {
            this.loadJobDetail();
            this.setupEventListeners();
        }
    }

    setupEventListeners() {
        // File upload area
        const uploadArea = document.getElementById('uploadArea');
        const fileInput = document.getElementById('fileInput');
        
        if (uploadArea && fileInput) {
            uploadArea.addEventListener('click', () => fileInput.click());
            
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
                this.handleFiles(e.dataTransfer.files);
            });
            
            fileInput.addEventListener('change', (e) => {
                this.handleFiles(e.target.files);
            });
        }

        // Auto-save notes
        const notesTextarea = document.getElementById('additionalNotes');
        if (notesTextarea) {
            let saveTimeout;
            notesTextarea.addEventListener('input', (e) => {
                clearTimeout(saveTimeout);
                saveTimeout = setTimeout(() => {
                    this.saveNotes(e.target.value);
                }, 1000); // Auto-save after 1 second of inactivity
            });
        }
    }

    async loadJobDetail() {
        try {
            this.showLoading();
            
            const response = await fetch(`/impact/cloudsphere/api/job/${this.jobId}`);
            const result = await response.json();
            
            if (result.success) {
                this.jobData = result.data;
                this.renderJobDetail(this.jobData);
            } else {
                this.showToast('Error loading job detail', 'danger');
            }
        } catch (error) {
            console.error('Error loading job detail:', error);
            this.showToast('Error loading job detail', 'danger');
        } finally {
            this.hideLoading();
        }
    }

    renderJobDetail(job) {
        // Basic information
        this.setElementText('jobId', job.job_id);
        this.setElementText('itemName', job.item_name);
        this.setElementText('sampleType', job.sample_type);
        this.setElementText('deadline', job.deadline || 'No deadline');
        this.setElementText('startDate', job.start_date || 'Not started');
        this.setElementText('picName', job.pic_name);
        this.setElementText('jobNotes', job.notes || 'No notes');
        
        const notesTextarea = document.getElementById('additionalNotes');
        if (notesTextarea) {
            notesTextarea.value = job.notes || '';
        }
        
        // Priority
        const priorityElement = document.getElementById('priorityLevel');
        if (priorityElement) {
            priorityElement.innerHTML = `<span class="priority-badge priority-${job.priority_level}">${job.priority_level}</span>`;
        }
        
        // Status
        const statusElement = document.getElementById('jobStatus');
        if (statusElement) {
            statusElement.innerHTML = `<span class="status-badge status-${job.status.replace('_', '-')}">${this.formatStatus(job.status)}</span>`;
        }
        
        // Progress
        this.setElementText('progressPercentage', `${job.completion_percentage}%`);
        const progressBar = document.getElementById('progressBarFill');
        if (progressBar) {
            progressBar.style.width = `${job.completion_percentage}%`;
        }
        
        // Render tasks
        this.renderTasks(job.tasks, job.progress_tasks);
        
        // Render files
        this.renderFiles(job.evidence_files);
        
        // Show/hide action sections based on status and user role
        this.updateActionSections(job.status);
        
        // Update page title
        document.title = `Job ${job.job_id} - Cloudsphere`;
    }

    renderTasks(tasks, progressTasks) {
        const container = document.getElementById('tasksContainer');
        if (!container) return;
        
        // Create a map of completed tasks
        const completedTasksMap = new Map();
        if (progressTasks) {
            progressTasks.forEach(pt => {
                if (pt.is_completed) {
                    completedTasksMap.set(pt.task_id, pt);
                }
            });
        }
        
        const tasksHtml = tasks.map(task => {
            const isCompleted = completedTasksMap.has(task.id);
            const progressTask = completedTasksMap.get(task.id);
            
            return `
                <div class="task-card ${isCompleted ? 'completed' : ''}" data-task-id="${task.id}">
                    <div class="task-header">
                        <div>
                            <div class="task-name">${task.task_name}</div>
                            <div class="task-category">${task.category_name}</div>
                        </div>
                        <input type="checkbox" class="task-checkbox" 
                               ${isCompleted ? 'checked' : ''} 
                               ${!this.canEditTask() ? 'disabled' : ''}
                               onchange="cloudsphereJobDetail.toggleTask(${task.id}, this.checked)">
                    </div>
                    ${progressTask ? `
                        <div class="task-notes">${progressTask.notes || ''}</div>
                        <div class="task-completed-at">Completed: ${progressTask.completed_at}</div>
                    ` : ''}
                </div>
            `;
        }).join('');
        
        container.innerHTML = tasksHtml;
    }

    renderFiles(files) {
        const container = document.getElementById('filesContainer');
        if (!container) return;
        
        if (!files || files.length === 0) {
            container.innerHTML = '<p class="text-muted">No files uploaded yet</p>';
            return;
        }
        
        const filesHtml = files.map(file => {
            const isPhoto = file.file_type === 'photo';
            const iconClass = isPhoto ? 'bi-file-image' : 'bi-file-text';
            const colorClass = isPhoto ? 'file-photo' : 'file-document';
            
            return `
                <div class="file-card">
                    <div class="file-icon ${colorClass}">
                        <i class="bi ${iconClass}"></i>
                    </div>
                    <div class="file-name">${file.original_filename}</div>
                    <div class="file-meta">
                        ${(file.file_size / 1024).toFixed(1)} KB
                    </div>
                    <div class="file-meta">
                        Uploaded by ${file.uploaded_by}
                    </div>
                    <div class="file-meta">
                        ${file.uploaded_at}
                    </div>
                    <button class="btn btn-sm btn-outline-primary mt-2" onclick="cloudsphereJobDetail.downloadFile(${file.id})">
                        <i class="bi bi-download"></i> Download
                    </button>
                </div>
            `;
        }).join('');
        
        container.innerHTML = filesHtml;
    }

    async toggleTask(taskId, isCompleted) {
        if (!this.canEditTask()) return;
        
        try {
            const notes = prompt('Enter completion notes (optional):');
            
            const response = await fetch(`/impact/cloudsphere/api/task/${taskId}/complete`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    job_id: this.jobId,
                    notes: notes || ''
                })
            });
            
            const result = await response.json();
            
            if (result.success) {
                this.showToast('Task updated successfully', 'success');
                this.loadJobDetail(); // Reload to update progress
            } else {
                this.showToast(result.error || 'Error updating task', 'danger');
            }
        } catch (error) {
            console.error('Error updating task:', error);
            this.showToast('Error updating task', 'danger');
        }
    }

    async handleFiles(files) {
        for (let file of files) {
            await this.uploadFile(file);
        }
    }

    async uploadFile(file) {
        // Validate file
        if (!this.validateFile(file)) {
            return;
        }
        
        const formData = new FormData();
        formData.append('file', file);
        formData.append('job_id', this.jobId);
        
        try {
            this.showLoading();
            
            const response = await fetch('/impact/cloudsphere/api/upload-evidence', {
                method: 'POST',
                body: formData
            });
            
            const result = await response.json();
            
            if (result.success) {
                this.showToast('File uploaded successfully', 'success');
                this.loadJobDetail(); // Reload to show new file
            } else {
                this.showToast(result.error || 'Error uploading file', 'danger');
            }
        } catch (error) {
            console.error('Error uploading file:', error);
            this.showToast('Error uploading file', 'danger');
        } finally {
            this.hideLoading();
        }
    }

    validateFile(file) {
        // Check file size (max 10MB)
        const maxSize = 10 * 1024 * 1024; // 10MB in bytes
        if (file.size > maxSize) {
            this.showToast('File size must be less than 10MB', 'danger');
            return false;
        }
        
        // Check file type
        const allowedTypes = [
            'application/pdf',
            'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
            'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            'image/jpeg',
            'image/jpg',
            'image/png'
        ];
        
        if (!allowedTypes.includes(file.type)) {
            this.showToast('Invalid file type. Allowed types: PDF, DOCX, XLSX, JPG, JPEG, PNG', 'danger');
            return false;
        }
        
        return true;
    }

    downloadFile(fileId) {
        window.open(`/impact/cloudsphere/api/download-evidence/${fileId}`, '_blank');
    }

    async saveNotes(notes) {
        try {
            const response = await fetch(`/impact/cloudsphere/api/job/${this.jobId}/notes`, {
                method: 'PUT',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    notes: notes
                })
            });
            
            const result = await response.json();
            
            if (result.success) {
                // Show subtle success indicator
                const notesTextarea = document.getElementById('additionalNotes');
                if (notesTextarea) {
                    notesTextarea.style.borderColor = '#16a34a';
                    setTimeout(() => {
                        notesTextarea.style.borderColor = '';
                    }, 2000);
                }
            }
        } catch (error) {
            console.error('Error saving notes:', error);
        }
    }

    async submitForApproval() {
        if (!confirm('Are you sure you want to submit this job for approval?')) {
            return;
        }
        
        try {
            const response = await fetch(`/impact/cloudsphere/api/submit-for-approval/${this.jobId}`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                }
            });
            
            const result = await response.json();
            
            if (result.success) {
                this.showToast('Job submitted for approval', 'success');
                this.loadJobDetail(); // Reload to update status
            } else {
                this.showToast(result.error || 'Error submitting for approval', 'danger');
            }
        } catch (error) {
            console.error('Error submitting for approval:', error);
            this.showToast('Error submitting for approval', 'danger');
        }
    }

    async approveJob() {
        if (!confirm('Are you sure you want to approve this job?')) {
            return;
        }
        
        try {
            const adminNotes = document.getElementById('adminNotes');
            
            const response = await fetch(`/impact/cloudsphere/api/approve-job/${this.jobId}`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    admin_notes: adminNotes ? adminNotes.value : ''
                })
            });
            
            const result = await response.json();
            
            if (result.success) {
                this.showToast('Job approved successfully', 'success');
                this.loadJobDetail(); // Reload to update status
            } else {
                this.showToast(result.error || 'Error approving job', 'danger');
            }
        } catch (error) {
            console.error('Error approving job:', error);
            this.showToast('Error approving job', 'danger');
        }
    }

    async rejectJob() {
        if (!confirm('Are you sure you want to reject this job?')) {
            return;
        }
        
        try {
            const adminNotes = document.getElementById('adminNotes');
            
            const response = await fetch(`/impact/cloudsphere/api/reject-job/${this.jobId}`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    admin_notes: adminNotes ? adminNotes.value : ''
                })
            });
            
            const result = await response.json();
            
            if (result.success) {
                this.showToast('Job rejected successfully', 'success');
                this.loadJobDetail(); // Reload to update status
            } else {
                this.showToast(result.error || 'Error rejecting job', 'danger');
            }
        } catch (error) {
            console.error('Error rejecting job:', error);
            this.showToast('Error rejecting job', 'danger');
        }
    }

    exportPDF() {
        window.open(`/impact/cloudsphere/api/export-job/${this.jobId}/pdf`, '_blank');
    }

    updateActionSections(status) {
        const actionsSection = document.getElementById('actionsSection');
        const adminActionsSection = document.getElementById('adminActionsSection');
        const submitBtn = document.getElementById('submitApprovalBtn');
        const exportBtn = document.getElementById('exportPDFBtn');
        
        // Check if user is admin (this would need to be passed from backend)
        const isAdmin = this.checkIfUserIsAdmin();
        
        if (status === 'completed') {
            if (submitBtn) submitBtn.style.display = 'none';
            if (exportBtn) exportBtn.style.display = 'block';
        } else if (status === 'pending_approval') {
            if (submitBtn) submitBtn.style.display = 'none';
            if (exportBtn) exportBtn.style.display = 'none';
        } else {
            if (submitBtn) submitBtn.style.display = 'block';
            if (exportBtn) exportBtn.style.display = 'none';
        }
        
        // Show admin actions for admins
        if (adminActionsSection) {
            adminActionsSection.style.display = isAdmin ? 'block' : 'none';
        }
    }

    canEditTask() {
        // This should check if current user is PIC or admin
        // For now, assume user can edit
        return true;
    }

    checkIfUserIsAdmin() {
        // This would need to be determined from user data
        // For now, check if user has admin role in page data or make an API call
        return false; // Simplified for now
    }

    formatStatus(status) {
        return status.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase());
    }

    setElementText(id, text) {
        const element = document.getElementById(id);
        if (element) {
            element.textContent = text;
        }
    }

    goBack() {
        window.location.href = '/impact/cloudsphere';
    }

    showLoading() {
        // Show loading indicator
        const loadingHtml = `
            <div class="loading-overlay">
                <div class="spinner-border text-primary" role="status">
                    <span class="visually-hidden">Loading...</span>
                </div>
            </div>
        `;
        
        document.body.insertAdjacentHTML('beforeend', loadingHtml);
    }

    hideLoading() {
        // Hide loading indicator
        const loadingOverlay = document.querySelector('.loading-overlay');
        if (loadingOverlay) {
            loadingOverlay.remove();
        }
    }

    showToast(message, type = 'info') {
        const toastHtml = `
            <div class="toast custom-toast align-items-center text-white bg-${type} border-0" role="alert">
                <div class="d-flex">
                    <div class="toast-body">
                        ${message}
                    </div>
                    <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast"></button>
                </div>
            </div>
        `;
        
        const toastContainer = document.getElementById('toastContainer');
        if (!toastContainer) return;
        
        const toastElement = document.createElement('div');
        toastElement.innerHTML = toastHtml;
        toastContainer.appendChild(toastElement);
        
        const toast = new bootstrap.Toast(toastElement.querySelector('.toast'));
        toast.show();
        
        // Remove toast element after hidden
        toastElement.addEventListener('hidden.bs.toast', () => {
            toastElement.remove();
        });
    }
}

// Global functions for onclick handlers
function goBack() {
    cloudsphereJobDetail.goBack();
}

function saveNotes() {
    const notesTextarea = document.getElementById('additionalNotes');
    if (notesTextarea) {
        cloudsphereJobDetail.saveNotes(notesTextarea.value);
    }
}

function submitForApproval() {
    cloudsphereJobDetail.submitForApproval();
}

function approveJob() {
    cloudsphereJobDetail.approveJob();
}

function rejectJob() {
    cloudsphereJobDetail.rejectJob();
}

function exportPDF() {
    cloudsphereJobDetail.exportPDF();
}

// Initialize the class when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    window.cloudsphereJobDetail = new CloudsphereJobDetail();
});