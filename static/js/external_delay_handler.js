/**
 * external_delay_handler.js
 * External Lead Time Tracking - Frontend Logic
 * 
 * Handles:
 * - Loading and displaying external delays in timeline
 * - Admin UI for adding external delays
 * - Rendering yellow/green indicators
 * - Auto-completion when tasks are checked
 * 
 * Usage: Load this script in rnd_cloudsphere_detail.html
 */

class ExternalDelayHandler {
    /**
     * Constructor
     * @param {RNDJobDetail} rndJobDetail - Reference to main RNDJobDetail instance
     */
    constructor(rndJobDetail) {
        this.rndJobDetail = rndJobDetail;
        this.externalDelays = [];
        this.lastCompletedAssignmentId = null;
    }

    /**
     * Initialize external delay functionality
     */
    async init() {
        try {
            console.log('External delay: Initializing handler');
            await this.loadExternalDelays();
            console.log(`External delay: Loaded ${this.externalDelays.length} delays`);
            this.renderExternalDelayIndicators();
            this.setupEventListeners();
            console.log('External delay: Handler initialized successfully');
        } catch (error) {
            console.error('Error initializing external delay handler:', error);
        }
    }

    /**
     * Load external delays for current job
     */
    async loadExternalDelays() {
        try {
            const response = await fetch(
                `/impact/rnd-cloudsphere/api/external-delay/job/${this.rndJobDetail.jobId}`
            );
            const data = await response.json();
            
            if (data.success) {
                this.externalDelays = data.data;
                return true;
            } else {
                console.warn('Failed to load external delays:', data.message);
                return false;
            }
        } catch (error) {
            console.error('Error loading external delays:', error);
            return false;
        }
    }

    /**
     * Render external delay indicators in the timeline
     */
    renderExternalDelayIndicators() {
        const horizontalSteps = document.querySelector('.horizontal-steps');
        if (!horizontalSteps) {
            console.warn('External delay: .horizontal-steps not found');
            return;
        }

        console.log(`External delay: Rendering ${this.externalDelays.length} indicators`);
        
        // Debug: Log all available steps
        const allSteps = document.querySelectorAll('[data-progress-assignment-id]');
        console.log('DEBUG - All available steps:', Array.from(allSteps).map(s => ({
            id: s.getAttribute('data-progress-assignment-id'),
            stepName: s.querySelector('.step-title')?.textContent || 'Unknown'
        })));

        // Remove any existing external delay indicators first to avoid duplicates
        document.querySelectorAll('[data-external-delay-id]').forEach(el => el.remove());
        // Also remove any external delay connectors
        document.querySelectorAll('[data-external-delay-connector]').forEach(el => el.remove());

        this.externalDelays.forEach(delay => {
            console.log(`External delay: Processing delay ${delay.id}:`, {
                lastProgressId: delay.last_progress_assignment_id,
                nextProgressId: delay.next_progress_assignment_id,
                category: delay.delay_category,
                isCompleted: delay.is_completed
            });

            // Create indicator element
            const indicatorElement = this.createExternalDelayIndicator(delay);
            
            // Find position: between last_progress and next_progress
            const lastStepElement = document.querySelector(
                `[data-progress-assignment-id="${delay.last_progress_assignment_id}"]`
            );
            const nextStepElement = document.querySelector(
                `[data-progress-assignment-id="${delay.next_progress_assignment_id}"]`
            );
            
            console.log(`DEBUG - Delay ${delay.id} insertion:`, {
                lastStepFound: !!lastStepElement,
                lastStepName: lastStepElement?.querySelector('.step-title')?.textContent || 'N/A',
                lastStepId: delay.last_progress_assignment_id,
                nextStepFound: !!nextStepElement,
                nextStepName: nextStepElement?.querySelector('.step-title')?.textContent || 'N/A',
                nextStepId: delay.next_progress_assignment_id
            });

            if (lastStepElement && nextStepElement) {
                // Debug: Log next sibling before removal
                const originalConnector = lastStepElement.nextElementSibling;
                console.log(`DEBUG - Original connector state:`, {
                    exists: !!originalConnector,
                    isConnector: originalConnector?.classList.contains('step-connector'),
                    classList: originalConnector?.className || 'N/A'
                });
                
                // Remove original connector between last step and next step
                if (originalConnector && originalConnector.classList.contains('step-connector')) {
                    const originalConnectorStatus = originalConnector.classList.contains('completed') ? 'completed' : 
                                                   originalConnector.classList.contains('in_progress') ? 'in_progress' : 'pending';
                    originalConnector.remove();
                    console.log(`✓ Removed original connector with status: ${originalConnectorStatus}`);
                    
                    // Add connector from last step to external delay indicator (with same status as original)
                    const connectorBeforeDelay = document.createElement('div');
                    connectorBeforeDelay.className = `step-connector ${originalConnectorStatus}`;
                    connectorBeforeDelay.setAttribute('data-external-delay-connector-before', delay.id);
                    lastStepElement.after(connectorBeforeDelay);  // Insert right after last step
                    console.log(`✓ Added connector before external delay with status: ${originalConnectorStatus}`);
                    
                    // Insert external delay indicator after the new connector
                    connectorBeforeDelay.after(indicatorElement);
                    console.log(`✓ Inserted external delay indicator after connector`);
                } else {
                    // If no original connector, just insert after last step
                    lastStepElement.after(indicatorElement);
                    console.log(`✓ Inserted external delay indicator (no original connector)`);
                }
                
                // Change next step's visual status to "pending" if it's in_progress
                this.updateNextStepStatus(nextStepElement);
                
                // Add connector from external delay indicator to next step
                this.addExternalDelayConnector(indicatorElement, nextStepElement, delay);
                
                console.log(`✓ Delay ${delay.id}: Complete`);
            } else {
                console.warn(`✗ Could not find elements for delay ${delay.id}`);
            }
        });
        
        // Debug: Final state
        console.log('DEBUG - Final timeline structure:', Array.from(document.querySelectorAll('.horizontal-steps > *')).map((el, idx) => ({
            index: idx,
            type: el.classList.contains('step-connector') ? 'CONNECTOR' : 'STEP',
            status: el.className.match(/\b(completed|pending|in_progress)\b/)?.[0] || 'unknown',
            id: el.getAttribute('data-progress-assignment-id') || el.getAttribute('data-external-delay-id') || 'N/A',
            name: el.querySelector('.step-title')?.textContent || el.querySelector('.step-status')?.textContent || 'N/A'
        })));
    }
    
    /**
     * Change next step's status from in_progress to pending
     * @param {Element} nextStepElement - Next step DOM element
     */
    updateNextStepStatus(nextStepElement) {
        const indicator = nextStepElement.querySelector('.step-indicator');
        if (indicator) {
            // Check if it has in_progress class (with underscore)
            if (indicator.classList.contains('in_progress')) {
                indicator.classList.remove('in_progress');
                indicator.classList.add('pending');
                console.log('Updated next step status from in_progress to pending');
            }
        }
    }
    
    /**
     * Add connector between external delay indicator and next step
     * @param {Element} delayElement - External delay indicator element
     * @param {Element} nextStepElement - Next step element
     * @param {Object} delay - Delay data object
     */
    addExternalDelayConnector(delayElement, nextStepElement, delay) {
        // Create connector
        const connector = document.createElement('div');
        
        // Determine connector status based on next step status
        const nextStepIndicator = nextStepElement.querySelector('.step-indicator');
        const nextStepStatus = nextStepIndicator ? 
            (nextStepIndicator.classList.contains('completed') ? 'completed' : 'pending') : 
            'pending';
        
        connector.className = `step-connector ${nextStepStatus}`;
        connector.setAttribute('data-external-delay-connector', delay.id);
        
        // Insert connector between delay indicator and next step
        nextStepElement.parentNode.insertBefore(connector, nextStepElement);
        
        console.log(`Added connector with status: ${nextStepStatus}`);
    }

    /**
     * Create HTML element for external delay indicator
     * @param {Object} delay - External delay data
     * @returns {HTMLElement}
     */
    createExternalDelayIndicator(delay) {
        const div = document.createElement('div');
        div.className = 'process-step';
        div.id = `step-external-delay-${delay.id}`;
        div.setAttribute('data-external-delay-id', delay.id);

        // Create indicator circle
        const indicator = document.createElement('div');
        indicator.className = `step-indicator external-wait ${delay.is_completed ? 'completed' : ''}`;
        indicator.innerHTML = '<i class="fas fa-clock"></i>';

        // Create content section
        const content = document.createElement('div');
        content.className = 'step-content';

        // Title
        const title = document.createElement('p');
        title.className = 'step-title';
        title.textContent = delay.delay_reason;

        // Status badge
        const status = document.createElement('span');
        status.className = `step-status external-wait ${delay.is_completed ? 'completed' : ''}`;
        status.textContent = delay.is_completed 
            ? 'EXTERNAL WAIT - COMPLETED' 
            : 'EXTERNAL WAIT';

        // Meta information
        const meta = document.createElement('div');
        meta.className = 'step-meta';
        
        const startMeta = document.createElement('div');
        startMeta.className = 'step-meta-item';
        
        // Build the date range string
        let dateRangeStr = this.formatDate(delay.external_wait_start);
        if (delay.is_completed) {
            // If completed, show end date too
            const endDate = this.formatDate(delay.external_wait_end);
            const durationStr = delay.external_wait_hours ? ` (${this.formatHours(delay.external_wait_hours)})` : '';
            dateRangeStr = `${dateRangeStr} - ${endDate}${durationStr}`;
        }
        
        startMeta.innerHTML = `
            <i class="fas fa-hourglass-start"></i>
            <span>${dateRangeStr}</span>
        `;
        meta.appendChild(startMeta);

        // Category badge
        const categoryBadge = document.createElement('div');
        categoryBadge.className = 'step-meta-item';
        const categoryClass = delay.delay_category.toLowerCase();
        categoryBadge.innerHTML = `
            <span class="delay-category-badge ${categoryClass}"><i class="fas fa-tag"></i> ${delay.delay_category}</span>
        `;
        meta.appendChild(categoryBadge);

        // Append to content
        content.appendChild(title);
        content.appendChild(status);
        content.appendChild(meta);

        // Append to container
        div.appendChild(indicator);
        div.appendChild(content);

        return div;
    }

    /**
     * Setup event listeners
     */
    setupEventListeners() {
        // Button to open "Add External Delay" modal
        const addDelayBtn = document.getElementById('addExternalDelayBtn');
        if (addDelayBtn) {
            addDelayBtn.addEventListener('click', () => this.openAddExternalDelayModal());
        }

        // Submit button in modal
        const submitBtn = document.getElementById('submitAddExternalDelayBtn');
        if (submitBtn) {
            submitBtn.addEventListener('click', () => this.submitAddExternalDelay());
        }
    }

    /**
     * Open modal to add external delay
     */
    async openAddExternalDelayModal() {
        if (!this.rndJobDetail.jobData) {
            this.rndJobDetail.showMessage('error', 'Job data not loaded');
            return;
        }

        // Find last completed progress assignment
        const completedAssignments = this.rndJobDetail.jobData.progress_assignments
            .filter(a => a.status === 'completed')
            .sort((a, b) => b.id - a.id);

        if (completedAssignments.length === 0) {
            this.rndJobDetail.showMessage('error', 'No completed progress step found');
            return;
        }

        const lastCompleted = completedAssignments[0];
        this.lastCompletedAssignmentId = lastCompleted.id;

        // Populate last completed progress (read-only)
        document.getElementById('lastProgressName').value = 
            lastCompleted.progress_step_name || 'N/A';
        document.getElementById('lastProgressDate').textContent = 
            `Finished: ${this.formatDate(lastCompleted.finished_at)}`;

        // Populate next progress dropdown (pending/in-progress steps only)
        const nextProgressSelect = document.getElementById('nextProgressSelect');
        nextProgressSelect.innerHTML = '<option value="">Select progress step...</option>';

        const pendingSteps = this.rndJobDetail.jobData.progress_assignments
            .filter(a => a.status !== 'completed' && a.id !== lastCompleted.id && a.progress_step_name)
            .sort((a, b) => {
                const aOrder = a.progress_step_order || 0;
                const bOrder = b.progress_step_order || 0;
                return aOrder - bOrder;
            });

        pendingSteps.forEach(assignment => {
            if (assignment.progress_step_name) {
                const option = document.createElement('option');
                option.value = assignment.id;
                option.textContent = assignment.progress_step_name || 'Unknown Step';
                nextProgressSelect.appendChild(option);
            }
        });

        // Clear form fields
        document.getElementById('delayCategory').value = '';
        document.getElementById('delayReason').value = '';
        document.getElementById('delayNotes').value = '';

        // Show modal
        const modal = new bootstrap.Modal(document.getElementById('addExternalDelayModal'));
        modal.show();
    }

    /**
     * Submit add external delay form
     */
    async submitAddExternalDelay() {
        const nextProgressId = document.getElementById('nextProgressSelect').value;
        const delayCategory = document.getElementById('delayCategory').value;
        const delayReason = document.getElementById('delayReason').value;
        const delayNotes = document.getElementById('delayNotes').value;

        // Validation
        if (!this.lastCompletedAssignmentId) {
            this.rndJobDetail.showMessage('error', 'Last progress not selected');
            return;
        }

        if (!nextProgressId) {
            this.rndJobDetail.showMessage('error', 'Please select next progress');
            return;
        }

        if (!delayCategory) {
            this.rndJobDetail.showMessage('error', 'Please select delay category');
            return;
        }

        if (!delayReason.trim()) {
            this.rndJobDetail.showMessage('error', 'Please enter delay reason');
            return;
        }

        try {
            const response = await fetch(
                '/impact/rnd-cloudsphere/api/external-delay',
                {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        job_id: this.rndJobDetail.jobId,
                        last_progress_assignment_id: this.lastCompletedAssignmentId,
                        next_progress_assignment_id: parseInt(nextProgressId),
                        delay_category: delayCategory,
                        delay_reason: delayReason,
                        delay_notes: delayNotes || null
                    })
                }
            );

            const data = await response.json();

            if (data.success) {
                this.rndJobDetail.showMessage('success', 'External delay recorded successfully');
                
                // Close modal
                bootstrap.Modal.getInstance(
                    document.getElementById('addExternalDelayModal')
                ).hide();

                // Reload job detail to show new delay indicator
                await this.rndJobDetail.loadJobDetail();
            } else {
                this.rndJobDetail.showMessage('error', data.message || 'Failed to record delay');
            }
        } catch (error) {
            console.error('Error recording external delay:', error);
            this.rndJobDetail.showMessage('error', 'Error recording external delay');
        }
    }

    /**
     * Auto-complete external delay when first task is checked
     * This is called from the main task completion handler
     * @param {number} taskId - Task assignment ID
     * @returns {Promise<boolean>}
     */
    async autoCompleteExternalDelay(taskId) {
        try {
            // Find which progress assignment this task belongs to
            const taskAssignment = this.rndJobDetail.jobData.progress_assignments
                .flatMap(a => a.task_assignments)
                .find(t => t.id === taskId);

            if (!taskAssignment) return false;

            const progressAssignment = this.rndJobDetail.jobData.progress_assignments
                .find(a => a.id === taskAssignment.job_progress_assignment_id);

            if (!progressAssignment) return false;

            // Find active external delay for this progress
            const activeDelay = this.externalDelays.find(
                d => d.next_progress_assignment_id === progressAssignment.id && !d.is_completed
            );

            if (!activeDelay) return false;

            // Call API to complete the delay
            const response = await fetch(
                `/impact/rnd-cloudsphere/api/external-delay/${activeDelay.id}/complete`,
                { method: 'PUT' }
            );

            const result = await response.json();

            if (result.success) {
                console.log('External delay auto-completed:', result.data);
                
                // Reload delays and re-render
                await this.loadExternalDelays();
                
                // Remove old indicator and re-render
                const oldIndicator = document.querySelector(
                    `[data-external-delay-id="${activeDelay.id}"]`
                );
                if (oldIndicator) {
                    oldIndicator.remove();
                }
                
                // Render updated indicator (now green)
                this.renderExternalDelayIndicators();
                
                return true;
            }
        } catch (error) {
            console.error('Error auto-completing external delay:', error);
        }

        return false;
    }

    /**
     * Format date to readable string
     * @param {string} dateString - ISO date string
     * @returns {string}
     */
    formatDate(dateString) {
        if (!dateString) return 'N/A';
        const date = new Date(dateString);
        const options = { 
            year: 'numeric', 
            month: 'short', 
            day: 'numeric', 
            hour: '2-digit', 
            minute: '2-digit'
        };
        return date.toLocaleDateString('id-ID', options);
    }

    /**
     * Format hours to human-readable string
     * @param {number} hours - Duration in hours
     * @returns {string}
     */
    formatHours(hours) {
        if (!hours) return '0 hours';
        
        const days = Math.floor(hours / 24);
        const remainingHours = Math.floor(hours % 24);
        const minutes = Math.floor((hours % 1) * 60);
        
        let result = [];
        if (days > 0) result.push(`${days} day${days > 1 ? 's' : ''}`);
        if (remainingHours > 0) result.push(`${remainingHours} hour${remainingHours > 1 ? 's' : ''}`);
        if (minutes > 0 && days === 0) result.push(`${minutes} minute${minutes > 1 ? 's' : ''}`);
        
        return result.length > 0 ? result.join(' ') : '0 hours';
    }

    /**
     * Get lead time breakdown for reporting
     * @returns {Promise<Object>}
     */
    async getLeadTimeBreakdown() {
        try {
            const response = await fetch(
                `/impact/rnd-cloudsphere/api/external-delay/job/${this.rndJobDetail.jobId}/lead-time-breakdown`
            );
            const data = await response.json();
            
            if (data.success) {
                return data.data;
            }
            return null;
        } catch (error) {
            console.error('Error getting lead time breakdown:', error);
            return null;
        }
    }
}

// Export for use in rnd_cloudsphere_detail.js
// Usage: let externalDelayHandler = new ExternalDelayHandler(rndJobDetail);
