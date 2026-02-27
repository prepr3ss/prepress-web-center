// Calibration References Create JavaScript
class CalibrationReferencesCreate {
    constructor() {
        this.init();
    }

    init() {
        this.setupEventListeners();
        this.setupAutoPopulate();
        this.convertFlashMessagesToToasts();
    }

    setupEventListeners() {
        // Add any event listeners here if needed
        
        // Add event listeners for auto-populate functionality
        const printMachineSelect = document.getElementById('print_machine');
        const paperTypeInput = document.getElementById('paper_type');
        const inkTypeInput = document.getElementById('ink_type');
        const calibrationGroupInput = document.getElementById('calib_group');
        const calibrationCodeInput = document.getElementById('calib_code');
        
        if (printMachineSelect && paperTypeInput && inkTypeInput && calibrationGroupInput && calibrationCodeInput) {
            // Auto-populate when machine, paper, or ink changes
            printMachineSelect.addEventListener('change', () => this.autoPopulateFields());
            paperTypeInput.addEventListener('input', () => this.autoPopulateFields());
            inkTypeInput.addEventListener('input', () => this.autoPopulateFields());
        }
    }

    setupAutoPopulate() {
        // Initial population on page load
        this.autoPopulateFields();
    }

    autoPopulateFields() {
        const printMachineSelect = document.getElementById('print_machine');
        const paperTypeInput = document.getElementById('paper_type');
        const inkTypeInput = document.getElementById('ink_type');
        const calibrationGroupInput = document.getElementById('calib_group');
        const calibrationCodeInput = document.getElementById('calib_code');
        const calibrationStandardInput = document.getElementById('calib_standard');
        
        if (!printMachineSelect || !paperTypeInput || !inkTypeInput || !calibrationGroupInput || !calibrationCodeInput) {
            return;
        }
        
        // Get current values
        const machine = printMachineSelect.value;
        const paper = paperTypeInput.value.toUpperCase();
        const ink = inkTypeInput.value.toUpperCase();
        
        // Get standard from readonly field or URL
        let standard = '';
        if (calibrationStandardInput) {
            standard = calibrationStandardInput.value;
        }
        
        // If standard field is empty, try to get from URL
        if (!standard) {
            const pathParts = window.location.pathname.split('/');
            standard = pathParts.length > 2 ? pathParts[2].toUpperCase() : 'G7';
        }
        
        // Generate calibration group and code based on standard and selections
        let calibrationGroup = '';
        let calibrationCode = '';
        
        if (machine && paper && ink) {
            // Format: STANDARD_MACHINE_PAPER_INK
            // Examples: G7_SM3_DCSP_SAKATA, ISO_SM2_DCC_DIC, etc.
            calibrationGroup = `${standard} ${machine} ${ink}`;
            calibrationCode = `${standard} ${machine} ${paper} ${ink}`;
        }
        
        // Set the values
        if (calibrationGroupInput) {
            calibrationGroupInput.value = calibrationGroup;
        }
        if (calibrationCodeInput) {
            calibrationCodeInput.value = calibrationCode;
        }
    }

    convertFlashMessagesToToasts() {
        // Find all flash message elements that are hidden
        const flashMessages = document.querySelectorAll('.flash-message-toast');
        
        flashMessages.forEach(flashElement => {
            const message = flashElement.getAttribute('data-message');
            const category = flashElement.getAttribute('data-category');
            
            if (message && category) {
                // Convert category to toast type
                let toastType = category;
                if (category === 'error') {
                    toastType = 'danger';
                }
                
                // Show as toast
                this.showMessage(toastType, message);
            }
        });
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

// Initialize when DOM is ready
document.addEventListener('DOMContentLoaded', function() {
    if (!window.calibrationReferencesCreateInstance) {
        window.calibrationReferencesCreateInstance = new CalibrationReferencesCreate();
    }
});