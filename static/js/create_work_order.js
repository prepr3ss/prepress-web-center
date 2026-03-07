// Create Work Order JavaScript
let selectedWorkQueueId = null;
let customerChoices = null;

// Initialize on page load
document.addEventListener('DOMContentLoaded', function() {
    // Get work queue ID from URL parameter
    const urlParams = new URLSearchParams(window.location.search);
    selectedWorkQueueId = urlParams.get('work_queue_id');
    const workQueueIdsParam = urlParams.get('work_queue_ids');
    
    if (workQueueIdsParam) {
        // Handle multiple work queue IDs
        const workQueueIds = workQueueIdsParam.split(',').map(id => id.trim());
        const selectedIdInput = document.getElementById('selectedWorkQueueId');
        if (selectedIdInput) {
            selectedIdInput.value = workQueueIds[0]; // Use first ID as primary
        }
        
        // Store all work queue IDs for form submission
        window.allWorkQueueIds = workQueueIds;
        
        // Load work order data for all work queue IDs
        if (workQueueIds.length > 1) {
            loadMultipleWorkOrderData(workQueueIds);
        } else {
            loadWorkOrderData(workQueueIds[0]);
        }
        
        // Show notification about multiple work orders
        if (workQueueIds.length > 1) {
            showAlert(`Creating job for ${workQueueIds.length} work orders`, 'info');
        }
    } else if (selectedWorkQueueId) {
        // Handle single work queue ID (existing behavior)
        const selectedIdInput = document.getElementById('selectedWorkQueueId');
        if (selectedIdInput) {
            selectedIdInput.value = selectedWorkQueueId;
        }
        
        // Store single work queue ID
        window.allWorkQueueIds = [selectedWorkQueueId];
        
        // Load work order data
        loadWorkOrderData(selectedWorkQueueId);
    }
    
    // Set today's date as default
    const tanggalInput = document.getElementById('tanggal');
    if (tanggalInput) {
        const today = new Date().toISOString().split('T')[0];
        tanggalInput.value = today;
    }
    
    // Load dropdown data
    loadDropdownData();
    
    // Add form submit event listener
    const form = document.getElementById('createWorkOrderForm');
    if (form) {
        form.addEventListener('submit', handleFormSubmit);
    }
    
    // Debug: Log form elements after page load
    setTimeout(() => {
        debugFormElements();
    }, 500);
});

/**
 * Debug function to show current state of form elements
 */
function debugFormElements() {
    console.log('\n🔍 ========== FORM ELEMENTS DEBUG INFO ==========');
    
    // Check Choices.js hidden elements
    const hiddenChoices = document.querySelectorAll('select.choices__input[hidden]');
    console.log(`Found ${hiddenChoices.length} hidden Choices.js select elements:`);
    hiddenChoices.forEach((select, index) => {
        const name = select.getAttribute('name');
        const id = select.getAttribute('id');
        const required = select.hasAttribute('required');
        const value = select.value;
        console.log(`  [${index + 1}] ID: ${id} | Name: ${name} | Value: ${value} | Required: ${required}`);
    });
    
    // Check all required fields
    const requiredFields = document.querySelectorAll('[required]:not([type="hidden"])');
    console.log(`\nFound ${requiredFields.length} required form fields:`);
    requiredFields.forEach((field, index) => {
        const name = field.getAttribute('name');
        const id = field.getAttribute('id');
        const value = field.value;
        const type = field.tagName.toLowerCase();
        console.log(`  [${index + 1}] Type: ${type} | ID: ${id} | Name: ${name} | Value: ${value || '(empty)'}`);
    });
    
    console.log('🔍 ========== END DEBUG INFO ==========\n');
}

/**
 * Handler untuk form submission
 */
function handleFormSubmit(event) {
    event.preventDefault();
    console.log('🔍 ========== FORM SUBMISSION START ==========');
    
    // Log form elements state at submission time
    debugFormElements();
    
    // Get form element
    const form = event.target;
    console.log('📋 Form element:', form);
    console.log('📋 Form ID:', form.id);
    
    // First check: HTML5 constraint validation
    // But skip reportValidity() for Choices.js hidden fields as they can't be focused
    console.log('🔍 Running HTML5 form validation...');
    if (!form.checkValidity()) {
        console.log('⚠️ Form failed HTML5 validation');
        // Try to report validity, but wrap in try-catch for hidden elements
        try {
            form.reportValidity();
            console.log('📢 Reported built-in validation messages');
        } catch (e) {
            console.warn('⚠️ Could not report validity (may contain hidden fields):', e);
        }
        return;
    }
    
    console.log('✅ Passed HTML5 validation');
    
    // Get form data
    const formData = new FormData(form);
    const data = {};
    
    // Convert FormData to object
    for (let [key, value] of formData.entries()) {
        data[key] = value;
    }
    
    console.log('📋 FormData converted to object:', data);
    
    // Extract values from Choices.js and regular select elements
    const customerSelect = document.getElementById('customerName');      // Choices.js
    const calibrationSelect = document.getElementById('calibrationName'); // Choices.js
    const remarksSelect = document.getElementById('remarks');            // Regular HTML select
    
    console.log('\n🔍 Extracting values from select elements...');
    
    if (customerSelect) {
        const customerValue = customerSelect.value;
        data.customer_name = customerValue;
        console.log('  ✓ Customer Name (Choices.js):', customerValue || '(empty)');
    }
    
    if (calibrationSelect) {
        const calibrationValue = calibrationSelect.value;
        // For Choices.js, check if a valid (non-empty) selection has been made
        // The hidden select value should be empty if nothing is selected
        const hasValidSelection = calibrationValue && calibrationValue !== '' && calibrationValue !== null;
        
        data.calibration_id = hasValidSelection ? calibrationValue : '';
        console.log('  ✓ Calibration ID (Choices.js):', hasValidSelection ? calibrationValue : '(empty)');
        console.log('  🔍 Calibration raw value:', calibrationValue);
        console.log('  🔍 Calibration hasValidSelection:', hasValidSelection);
    }
    
    if (remarksSelect) {
        const remarksValue = remarksSelect.value;
        data.remarks_id = remarksValue;
        console.log('  ✓ Remarks ID (HTML select):', remarksValue || '(empty)');
    }
    
    // Debug logging
    console.log('\n📋 Final Form Data:', data);
    console.log('📊 Summary:');
    console.log('   - Customer Name:', data.customer_name || '❌ EMPTY');
    console.log('   - Calibration ID:', data.calibration_id || '❌ EMPTY');
    console.log('   - Remarks ID:', data.remarks_id || '❌ EMPTY');
    
    // Add work queue IDs to form data
    if (window.allWorkQueueIds && window.allWorkQueueIds.length > 0) {
        data.work_queue_ids = window.allWorkQueueIds;
        console.log('   - Work Queue IDs:', window.allWorkQueueIds);
    }
    
    // Validate required fields (second check)
    console.log('\n🔍 Running custom validation...');
    if (!validateForm(data)) {
        console.log('❌ Custom validation failed');
        return;
    }
    
    console.log('✅ All validations passed!');
    
    // Show loading
    showLoading();
    
    // Submit to API
    console.log('📤 Submitting form data to API...');
    fetch('/impact/api/work-queue/create-production-job', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-Requested-With': 'XMLHttpRequest'
        },
        body: JSON.stringify(data)
    })
    .then(response => {
        console.log('📨 API Response received - Status:', response.status);
        return response.json();
    })
    .then(result => {
        console.log('📨 API Response data:', result);
        hideLoading();
        
        if (result.success) {
            console.log('✅ API Success - Creating/Completing work order');
            // Check if this is complete job mode
            const completeJobMode = document.getElementById('completeJobMode').value === 'true';
            
            // Get work queue count
            const workQueueCount = result.data.work_queue_count || 1;
            
            // Build message based on number of work orders
            let message;
            if (completeJobMode) {
                message = workQueueCount > 1 ? 
                    `${workQueueCount} Work Orders Completed Successfully!` :
                    'Work Order Completed Successfully!';
            } else {
                message = workQueueCount > 1 ?
                    `1 Production Job Created for ${workQueueCount} Work Orders!` :
                    'Production Job Created Successfully!';
            }
            
            const logMsg = completeJobMode ? '✅ Completed:' : '✅ Created:';
            console.log(logMsg, result.data);
            showAlert(message, 'success');
            
            // Redirect to Work Queue after a short delay
            setTimeout(() => {
                console.log('⏳ Redirecting to work queue...');
                window.location.href = '/impact/work-queue';
            }, 2000);
        } else {
            console.error('❌ API Error:', result.error);
            showAlert(result.error || 'Error creating work order', 'danger');
        }
    })
    .catch(error => {
        hideLoading();
        console.error('❌ Fetch Error:', error);
        showAlert('Error creating work order. Please try again.', 'danger');
    });
    
    console.log('🔍 ========== FORM SUBMISSION END ==========');
}

// Validate form data
function validateForm(data) {
    console.log('🔍 ========== FORM VALIDATION START ==========');
    console.log('📋 Data to validate:', data);
    
    // Map field names to human-readable labels
    const requiredFields = {
        'work_queue_id': 'Work Queue ID',
        'tanggal': 'Tanggal',
        'pic': 'PIC',
        'grup': 'Grup',
        'shift': 'Shift',
        'customer_name': 'Customer Name',
        'paper_size': 'Paper Size',
        'paper_desc': 'Paper Description',
        'file_name': 'File Name',
        'print_block': 'Print Block',
        'remarks_id': 'Remarks',
        'cockpit_id': 'Cockpit',
        'tiff_b_usage': 'TIFF-B Usage',
        'calibration_id': 'Calibration Name'
    };
    
    // Fields that use Choices.js library (only customer_name and calibration_id)
    // remarks_id is a normal HTML dropdown, NOT Choices.js
    const choicesFields = {
        'customer_name': 'customerName',
        'calibration_id': 'calibrationName'
    };
    
    let validCount = 0;
    let failedCount = 0;
    
    console.log('📊 Validating fields...\n');
    
    for (let field in requiredFields) {
        const label = requiredFields[field];
        let value = data[field];
        let isEmpty = false;
        
        // Special handling for calibration_id (Choices.js)
        if (field === 'calibration_id') {
            // Check if a valid (non-empty) selection has been made
            const hasValidSelection = value && value !== '' && value !== null;
            console.log(`  🔍 Validation for ${field} - value:`, value);
            console.log(`  🔍 Validation for ${field} - hasValidSelection:`, hasValidSelection);
            isEmpty = !hasValidSelection;
            value = hasValidSelection ? value : '';
        } else {
            // Normal validation for other fields
            isEmpty = !value || (typeof value === 'string' && value.trim() === '');
        }
        
        if (isEmpty) {
            failedCount++;
            console.log(`  ❌ ${field.padEnd(20)} | ${label.padEnd(20)} | Value: "${value}" | STATUS: EMPTY`);
        } else {
            validCount++;
            console.log(`  ✅ ${field.padEnd(20)} | ${label.padEnd(20)} | Value: "${value}" | STATUS: VALID`);
        }
    }
    
    console.log(`\n📊 Validation Summary: ${validCount} valid, ${failedCount} failed`);
    console.log('='.repeat(80));
    
    // If any field failed, show error and focus
    for (let field in requiredFields) {
        const label = requiredFields[field];
        let value = data[field];
        let isEmpty = false;
        
        // Special handling for calibration_id (Choices.js)
        if (field === 'calibration_id') {
            // Check if a valid (non-empty) selection has been made
            const hasValidSelection = value && value !== '' && value !== null;
            console.log(`  🔍 Validation for ${field} - value:`, value);
            console.log(`  🔍 Validation for ${field} - hasValidSelection:`, hasValidSelection);
            isEmpty = !hasValidSelection;
            value = hasValidSelection ? value : '';
        } else {
            // Normal validation for other fields
            isEmpty = !value || (typeof value === 'string' && value.trim() === '');
        }
        
        if (isEmpty) {
            console.error(`\n❌ VALIDATION FAILED: ${field} (${label}) is empty!`);
            showAlert(`❌ Please fill in: <strong>${label}</strong>`, 'warning');
            
            // Handle scrolling and focusing differently for Choices.js vs regular fields
            if (choicesFields[field]) {
                // For Choices.js elements - they might be hidden, so focus on the visible wrapper
                const elementId = choicesFields[field];
                const element = document.getElementById(elementId);
                console.log(`🔍 Trying to focus Choices.js field: ${elementId}`, element ? 'FOUND' : 'NOT FOUND');
                
                if (element) {
                    try {
                        // Find the visible Choices wrapper
                        const choicesWrapper = element.closest('.choices');
                        if (choicesWrapper) {
                            console.log(`✅ Found Choices wrapper for ${field}`);
                            // Scroll to the wrapper (which is visible)
                            choicesWrapper.scrollIntoView({ behavior: 'smooth', block: 'center' });
                            
                            // Try to open the actual visible input inside
                            const choicesInner = choicesWrapper.querySelector('.choices__inner');
                            if (choicesInner) {
                                console.log(`✅ Found .choices__inner, clicking to open dropdown`);
                                choicesInner.click(); // Open dropdown
                                choicesInner.focus();
                            }
                        } else {
                            console.warn(`⚠️ Could not find .choices wrapper for ${field}`);
                        }
                    } catch (e) {
                        console.warn(`⚠️ Could not focus choices field: ${field}`, e);
                    }
                }
            } else {
                // For regular input/select fields (including remarks which is normal dropdown)
                const fieldElement = document.querySelector(`[name="${field}"]`);
                console.log(`🔍 Looking for regular field with name="${field}"`, fieldElement ? 'FOUND' : 'NOT FOUND');
                
                if (fieldElement && !fieldElement.hidden) {
                    try {
                        fieldElement.focus();
                        fieldElement.scrollIntoView({ behavior: 'smooth', block: 'center' });
                        console.log(`✅ Focused and scrolled to ${field}`);
                    } catch (e) {
                        console.warn(`⚠️ Could not focus field: ${field}`, e);
                        // Fallback: just scroll to it
                        try {
                            fieldElement.scrollIntoView({ behavior: 'smooth', block: 'center' });
                            console.log(`✅ Scrolled to ${field} (fallback)`);
                        } catch (e2) {
                            console.warn(`⚠️ Could not scroll to field: ${field}`, e2);
                        }
                    }
                }
            }
            
            console.log('🔍 ========== FORM VALIDATION END (FAILED) ==========\n');
            return false;  // Exit on first failure
        }
    }
    
    console.log(`✅ ALL FIELDS VALID! (${validCount}/${Object.keys(requiredFields).length} fields passed)`);
    console.log('🔍 ========== FORM VALIDATION END (SUCCESS) ==========\n');
    return true;
}

/**
 * Select duplicate work queue item logic
 * @param {string|number} id - ID dari database
 * @param {string} woNumber - Nomor WO
 * @param {string} mcNumber - Nomor MC
 * @param {HTMLElement} element - Elemen DOM yang diklik (opsional)
 */
// Load work order data when page loads with work_queue_id parameter
/**
 * Load data from multiple work queue IDs and combine them
 */
function loadMultipleWorkOrderData(workQueueIds) {
    // Fetch all work queue items
    const fetchPromises = workQueueIds.map(id => 
        fetch(`/impact/api/work-queue/${id}`)
            .then(response => response.json())
    );
    
    Promise.all(fetchPromises)
    .then(results => {
        // Filter successful results
        const items = results
            .filter(result => result.success && result.data)
            .map(result => result.data);
        
        if (items.length === 0) {
            showAlert('Error loading work order data', 'danger');
            return;
        }
        
        // Combine WO numbers and MC numbers
        const woNumbers = items
            .map(item => item.plan_data ? item.plan_data.wo_number : '')
            .filter(wo => wo);
        
        const mcNumbers = items
            .map(item => item.plan_data ? item.plan_data.mc_number : '')
            .filter(mc => mc);
        
        // Use first item's data as primary (they should be similar)
        const primaryItem = items[0];
        
        // Update readonly fields
        const woNumberField = document.getElementById('woNumber');
        const mcNumberField = document.getElementById('mcNumber');
        const itemNameField = document.getElementById('itemName');
        const upField = document.getElementById('up');
        const paperDescField = document.getElementById('paperDesc');
        const paperTypeField = document.getElementById('paperType');
        const printMachineField = document.getElementById('printMachine');
        
        // Set combined WO numbers and MC numbers
        if (woNumberField) woNumberField.value = woNumbers.join(', ');
        if (mcNumberField) mcNumberField.value = mcNumbers.length > 1 ? mcNumbers.join(', ') : (primaryItem.plan_data ? primaryItem.plan_data.mc_number || '' : '');
        
        // Set other fields from primary item
        if (itemNameField) itemNameField.value = primaryItem.plan_data ? primaryItem.plan_data.item_name || '' : '';
        if (upField) upField.value = primaryItem.plan_data ? primaryItem.plan_data.num_up || 0 : 0;
        if (paperDescField) paperDescField.value = primaryItem.plan_data ? primaryItem.plan_data.paper_desc || '' : '';
        if (paperTypeField) paperTypeField.value = primaryItem.plan_data ? primaryItem.plan_data.paper_type || '' : '';
        
        // For print machine, check if the current value exists in the dropdown
        if (printMachineField && primaryItem.plan_data && primaryItem.plan_data.print_machine) {
            const currentValue = primaryItem.plan_data.print_machine;
            const optionExists = Array.from(printMachineField.options).some(option => option.value === currentValue);
            if (!optionExists) {
                const newOption = document.createElement('option');
                newOption.value = currentValue;
                newOption.textContent = currentValue;
                newOption.selected = true;
                printMachineField.add(newOption);
            } else {
                printMachineField.value = currentValue;
            }
        }
    })
    .catch(error => {
        console.error('Error:', error);
        showAlert('Error loading work order data', 'danger');
    });
}

function loadWorkOrderData(workQueueId) {
    fetch(`/impact/api/work-queue/${workQueueId}`)
    .then(response => response.json())
    .then(result => {
        if (result.success) {
            const item = result.data;
            
            // Update readonly fields
            const woNumberField = document.getElementById('woNumber');
            const mcNumberField = document.getElementById('mcNumber');
            const itemNameField = document.getElementById('itemName');
            const upField = document.getElementById('up');
            const paperDescField = document.getElementById('paperDesc');
            const paperTypeField = document.getElementById('paperType');
            const printMachineField = document.getElementById('printMachine');
            
            // Don't override WO Number if already has value from template (means merged items)
            if (woNumberField && !woNumberField.value) {
                woNumberField.value = item.plan_data ? item.plan_data.wo_number || '' : '';
            }
            if (mcNumberField) mcNumberField.value = item.plan_data ? item.plan_data.mc_number || '' : '';
            if (itemNameField) itemNameField.value = item.plan_data ? item.plan_data.item_name || '' : '';
            if (upField) upField.value = item.plan_data ? item.plan_data.num_up || 0 : 0;
            if (paperDescField) paperDescField.value = item.plan_data ? item.plan_data.paper_desc || '' : '';
            if (paperTypeField) paperTypeField.value = item.plan_data ? item.plan_data.paper_type || '' : '';
            // For print machine, check if the current value exists in the dropdown, if not, add it
            if (printMachineField && item.plan_data && item.plan_data.print_machine) {
                const currentValue = item.plan_data.print_machine;
                const optionExists = Array.from(printMachineField.options).some(option => option.value === currentValue);
                if (!optionExists) {
                    const newOption = document.createElement('option');
                    newOption.value = currentValue;
                    newOption.textContent = currentValue;
                    newOption.selected = true;
                    printMachineField.add(newOption);
                } else {
                    printMachineField.value = currentValue;
                }
            }
            
            // Don't update Work Queue info section since it's already rendered server-side
        } else {
            showAlert('Error loading work order data', 'danger');
        }
    })
    .catch(error => {
        console.error('Error:', error);
        showAlert('Error loading work order data', 'danger');
    });
}

// Go back to Work Queue
function goBack() {
    window.location.href = '/impact/work-queue';
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

// Initialize Choices.js for customer dropdown
function initializeChoices() {
    const customerSelect = document.getElementById('customerName');
    
    const commonConfig = {
        searchEnabled: true,
        searchPlaceholderValue: 'Search...',
        noResultsText: 'No results found',
        itemSelectText: 'Press to select',
        removeItemButton: false,
        placeholder: true,
        searchFloor: 1, 
        shouldSort: false,
        fuzzySearch: true,
        fuseOptions: {
            threshold: 0.25,
            distance: 100,
            minMatchCharLength: 1,
            location: 0,
            findAllMatches: true,
            isCaseSensitive: false,
            includeMatches: true,
            keys: ['label']
        }
    };

    if (customerSelect && typeof Choices !== 'undefined') {
        customerChoices = new Choices(customerSelect, {
            ...commonConfig,
            searchPlaceholderValue: 'Search customer...',
            placeholderValue: 'Select Customer',
        });
    }
    
    const calibrationSelect = document.getElementById('calibrationName');
    
    if (calibrationSelect && typeof Choices !== 'undefined') {
        window.calibrationChoices = new Choices(calibrationSelect, {
            ...commonConfig,
            searchPlaceholderValue: 'Search calibration...',
            placeholderValue: 'Select Calibration',
        });
    }
    
    // NOTE: Remarks uses normal HTML dropdown (not Choices.js) - no initialization needed
    
    // ⚠️ CRITICAL FIX: Remove 'required' attribute from original hidden select elements
    // Choices.js hides the original select but keeps it in the DOM with 'required' attribute
    // This causes "An invalid form control with name='...' is not focusable" error during form validation
    // Solution: Remove 'required' from the original hidden elements since we handle validation in JavaScript
    console.log('🔧 Removing required attribute from hidden Choices.js select elements...');
    
    setTimeout(() => {
        const choicesSelects = document.querySelectorAll('.choices__input[hidden][required]');
        console.log(`🔧 Found ${choicesSelects.length} hidden Choices.js elements with required attribute`);
        
        choicesSelects.forEach((select, index) => {
            const fieldName = select.getAttribute('name') || 'unknown';
            console.log(`🔧 [${index + 1}] Removing required from: ${fieldName}`);
            select.removeAttribute('required');
        });
        
        console.log('✅ All required attributes removed from hidden Choices.js elements');
    }, 100);
}

// Load dropdown data
function loadDropdownData() {
    console.log('🔍 DEBUG: loadDropdownData function called');
    fetch('/impact/api/work-queue/dropdown-data')
    .then(response => response.json())
    .then(result => {
        if (result.success) {
            // Populate customer dropdown
            const customerSelect = document.getElementById('customerName');
            if (customerSelect && result.data.customers) {
                customerSelect.innerHTML = '<option value="">Select Customer</option>';
                result.data.customers.forEach(customer => {
                    customerSelect.innerHTML += `<option value="${customer.id}">${customer.customer_name}</option>`;
                });
                
                // Initialize Choices.js after populating options
                initializeChoices();
            }
            
            // Populate print machine dropdown only if it's empty (to preserve server-rendered value)
            const printMachineSelect = document.getElementById('printMachine');
            console.log('🔍 DEBUG: Print machine dropdown element found:', !!printMachineSelect);
            console.log('🔍 DEBUG: Print machine dropdown current options length:', printMachineSelect ? printMachineSelect.options.length : 'N/A');
            
            if (printMachineSelect && result.data.print_machines && printMachineSelect.options.length <= 1) {
                // Only populate if dropdown is empty or has just the placeholder
                const currentValue = printMachineSelect.value;
                printMachineSelect.innerHTML = '<option value="">Select Print Machine</option>';
                
                // Add current value back if it exists
                if (currentValue) {
                    printMachineSelect.innerHTML += `<option value="${currentValue}" selected>${currentValue}</option>`;
                }
                
                // Add other machines from database (excluding current value)
                result.data.print_machines.forEach(machine => {
                    if (machine.print_machine !== currentValue) {
                        printMachineSelect.innerHTML += `<option value="${machine.print_machine}">${machine.print_machine}</option>`;
                    }
                });
            }
            
            // ALWAYS add event listener to print machine dropdown for calibration filtering
            if (printMachineSelect) {
                console.log('🔍 DEBUG: ========== ADDING EVENT LISTENER ==========');
                console.log('🔍 DEBUG: Adding event listener to print machine dropdown');
                console.log('🔍 DEBUG: Current print machine value:', printMachineSelect.value);
                console.log('🔍 DEBUG: Number of options:', printMachineSelect.options.length);
                
                // Log all options for debugging
                for (let i = 0; i < printMachineSelect.options.length; i++) {
                    console.log(`🔍 DEBUG: Option ${i}: value="${printMachineSelect.options[i].value}", text="${printMachineSelect.options[i].text}", selected=${printMachineSelect.options[i].selected}`);
                }
                
                // Test if addEventListener works
                if (printMachineSelect.addEventListener) {
                    console.log('🔍 DEBUG: addEventListener method exists');
                    
                    printMachineSelect.addEventListener('change', function(event) {
                        console.log('🔍 DEBUG: ========== PRINT MACHINE CHANGE EVENT TRIGGERED ==========');
                        console.log('🔍 DEBUG: Event object:', event);
                        console.log('🔍 DEBUG: Event type:', event.type);
                        console.log('🔍 DEBUG: Target element:', event.target);
                        console.log('🔍 DEBUG: Target ID:', event.target.id);
                        console.log('🔍 DEBUG: Target value:', event.target.value);
                        console.log('🔍 DEBUG: Target selectedIndex:', event.target.selectedIndex);
                        
                        // Log all options after change
                        console.log('🔍 DEBUG: Options after change:');
                        for (let i = 0; i < event.target.options.length; i++) {
                            console.log(`🔍 DEBUG: Option ${i}: value="${event.target.options[i].value}", text="${event.target.options[i].text}", selected=${event.target.options[i].selected}`);
                        }
                        
                        const selectedMachine = event.target.value;
                        console.log('🔍 DEBUG: Print machine changed to:', selectedMachine);
                        
                        // Load calibrations for selected machine
                        if (selectedMachine) {
                            console.log('🔍 DEBUG: Loading calibrations for machine:', selectedMachine);
                            loadCalibrationsByMachine(selectedMachine);
                        } else {
                            console.log('🔍 DEBUG: No machine selected, loading all calibrations');
                            loadAllCalibrations();
                        }
                        
                        // Also update print machine display in Work Queue Info section
                        console.log('🔍 DEBUG: About to call updatePrintMachineDisplay with:', selectedMachine);
                        updatePrintMachineDisplay(selectedMachine);
                        console.log('🔍 DEBUG: ========== PRINT MACHINE CHANGE EVENT COMPLETED ==========');
                    });
                    
                    console.log('🔍 DEBUG: Event listener successfully added');
                    console.log('🔍 DEBUG: ========== EVENT LISTENER ADDED ==========');
                } else {
                    console.log('🔍 DEBUG: ERROR: addEventListener method does not exist!');
                }
                
                // Also add debug logging to verify the event listener was added
                console.log('🔍 DEBUG: Event listener verification complete');
            }
           
            // Populate cockpit dropdown
            const cockpitSelect = document.getElementById('cockpit');
            if (cockpitSelect && result.data.cockpits) {
                cockpitSelect.innerHTML = '<option value="">Select Cockpit</option>';
                result.data.cockpits.forEach(cockpit => {
                    cockpitSelect.innerHTML += `<option value="${cockpit.id}">${cockpit.imposition_cockpit}</option>`;
                });
            }
            
            // DO NOT populate calibration dropdown here - it should be populated based on print machine selection
            console.log('🔍 DEBUG: Calibration dropdown will be populated based on print machine selection');
            
            // Populate remarks dropdown
            const remarksSelect = document.getElementById('remarks');
            if (remarksSelect && result.data.remarks) {
                remarksSelect.innerHTML = '<option value="">Select Remarks</option>';
                result.data.remarks.forEach(remark => {
                    remarksSelect.innerHTML += `<option value="${remark.id}">${remark.imposition_remarks}</option>`;
                });
            }
            
            // After loading dropdown data, load calibrations based on current print machine selection
            const currentPrintMachine = printMachineSelect ? printMachineSelect.value : null;
            if (currentPrintMachine) {
                console.log('🔍 DEBUG: Loading calibrations for current print machine:', currentPrintMachine);
                loadCalibrationsByMachine(currentPrintMachine);
            } else {
                console.log('🔍 DEBUG: No print machine selected, loading all calibrations');
                loadAllCalibrations();
            }
        } else {
            showAlert('Error loading dropdown data', 'danger');
        }
    })
    .catch(error => {
        console.error('Error loading dropdown data:', error);
        showAlert('Error loading dropdown data', 'danger');
    });
}

// Load calibrations filtered by print machine
// Load calibrations filtered by print machine
function loadCalibrationsByMachine(printMachine) {
    if (!printMachine) {
        loadAllCalibrations();
        return;
    }
    
    fetch(`/impact/api/work-queue/calibrations?print_machine=${encodeURIComponent(printMachine)}`)
    .then(response => response.json())
    .then(result => {
        if (result.success) {
            const calibrationSelect = document.getElementById('calibrationName');
            if (calibrationSelect) {
                // Simpan nilai lama jika ingin mencoba restore
                const currentValue = calibrationSelect.value;
                
                if (window.calibrationChoices && typeof window.calibrationChoices.setChoices === 'function') {
                    console.log('🔍 DEBUG: Updating calibrations using Choices.js API');
                    
                    // 1. Bersihkan pilihan yang ada saat ini
                    window.calibrationChoices.clearStore();
                    
                    // 2. Susun array pilihan baru
                    const choices = [
                        {
                            value: '',
                            label: 'Select Calibration',
                            placeholder: true,
                            selected: true,  // <--- KUNCI: Paksa pilih ini di awal
                            disabled: false   // <--- KUNCI: Jangan di-disable agar tidak dilompati
                        },
                        ...result.data
                            .filter(cal => cal.id != null && cal.id !== '')
                            .map(cal => ({
                                value: String(cal.id),
                                label: String(cal.calib_name || ''),
                                selected: false // Pastikan data server tidak otomatis terpilih
                            }))
                    ];
                    
                    // 3. Masukkan ke Choices.js
                    // Parameter terakhir 'true' akan menggantikan pilihan yang lama
                    window.calibrationChoices.setChoices(choices, 'value', 'label', true);
                    
                    // 4. Logika Restore (Hanya jika nilai lama ada di dalam list baru)
                    if (currentValue && currentValue !== '') {
                        const exists = result.data.some(cal => String(cal.id) === String(currentValue));
                        if (exists) {
                            window.calibrationChoices.setChoiceByValue(String(currentValue));
                            console.log('🔍 DEBUG: Restored previous value:', currentValue);
                        } else {
                            window.calibrationChoices.setChoiceByValue('');
                            console.log('🔍 DEBUG: Previous value not in new list, resetting to placeholder');
                        }
                    }
                } else {
                    // Fallback untuk HTML biasa (sama seperti customer_name)
                    console.log('🔍 DEBUG: Fallback to HTML manipulation');
                    calibrationSelect.innerHTML = '<option value="" selected>Select Calibration</option>';
                    
                    result.data.forEach(cal => {
                        calibrationSelect.innerHTML += `<option value="${cal.id}">${cal.calib_name}</option>`;
                    });
                    
                    if (currentValue) {
                        calibrationSelect.value = currentValue;
                    }
                }
            }
        } else {
            console.error('Error loading calibrations:', result.error);
        }
    })
    .catch(error => {
        console.error('Error loading calibrations:', error);
    });
}

// Load all calibrations (fallback)
function loadAllCalibrations() {
    console.log('🔍 DEBUG: loadAllCalibrations called');
    
    // Use stored initial calibrations if available, otherwise fetch all
    if (window.initialCalibrations && window.initialCalibrations.length > 0) {
        console.log('🔍 DEBUG: Using stored initial calibrations:', window.initialCalibrations.length);
        const calibrationSelect = document.getElementById('calibrationName');
        if (calibrationSelect) {
            const currentValue = calibrationSelect.value;
            console.log('🔍 DEBUG: Current calibration value:', currentValue);
            
            // Use Choices.js if available, otherwise fallback to HTML manipulation
            if (window.calibrationChoices && typeof window.calibrationChoices.clearStore === 'function') {
                console.log('🔍 DEBUG: Using Choices.js to update calibrations');
                
                // Clear current choices
                window.calibrationChoices.clearStore();
                
                    // Add placeholder choice first to prevent auto-selection
                    const choices = [
                        {
                            value: '',
                            label: 'Select Calibration',
                            placeholder: true,
                            disabled: true
                        },
                        ...window.initialCalibrations
                            .filter(calibration => calibration.id != null && calibration.id !== '')
                            .map(calibration => ({
                                value: String(calibration.id),
                                label: String(calibration.calib_name || '')
                            }))
                    ];
                    
                    window.calibrationChoices.setChoices(choices, 'value', 'label', false);
                
                // Restore previous selection if it still exists and is not empty
                if (currentValue && currentValue !== '') {
                    window.calibrationChoices.setChoiceByValue(currentValue);
                    console.log('🔍 DEBUG: Restored calibration value using Choices.js:', currentValue);
                } else {
                    // Ensure no selection is made
                    window.calibrationChoices.removeActiveItems();
                    console.log('🔍 DEBUG: No calibration value to restore, keeping empty');
                }
            } else {
                console.log('🔍 DEBUG: Choices.js not available, using HTML manipulation');
                calibrationSelect.innerHTML = '<option value="">Select Calibration</option>';
                
                window.initialCalibrations.forEach(calibration => {
                    console.log(`🔍 DEBUG: Adding stored calibration: ${calibration.calib_name} (ID: ${calibration.id})`);
                    calibrationSelect.innerHTML += `<option value="${calibration.id}">${calibration.calib_name}</option>`;
                });
                
                // Restore previous selection if it still exists
                if (currentValue) {
                    calibrationSelect.value = currentValue;
                    console.log('🔍 DEBUG: Restored calibration value:', currentValue);
                }
            }
        }
    } else {
        console.log('🔍 DEBUG: No stored calibrations, fetching all from API');
        fetch('/impact/api/work-queue/dropdown-data')
        .then(response => response.json())
        .then(result => {
            console.log('🔍 DEBUG: All calibrations API result:', result);
            if (result.success && result.data.calibrations) {
                const calibrationSelect = document.getElementById('calibrationName');
                console.log('🔍 DEBUG: Calibration select element found:', !!calibrationSelect);
                if (calibrationSelect) {
                    const currentValue = calibrationSelect.value;
                    console.log('🔍 DEBUG: Current calibration value:', currentValue);
                    
                    // Use Choices.js if available, otherwise fallback to HTML manipulation
                    if (window.calibrationChoices && typeof window.calibrationChoices.clearStore === 'function') {
                        console.log('🔍 DEBUG: Using Choices.js to update calibrations');
                        
                        // Clear current choices
                        window.calibrationChoices.clearStore();
                        
                        // Add placeholder choice first to prevent auto-selection
                        const choices = [
                            {
                                value: '',
                                label: 'Select Calibration',
                                placeholder: true,
                                disabled: true
                            },
                            ...result.data.calibrations
                                .filter(calibration => calibration.id != null && calibration.id !== '')
                                .map(calibration => ({
                                    value: String(calibration.id),
                                    label: String(calibration.calib_name || '')
                                }))
                        ];
                        
                        window.calibrationChoices.setChoices(choices, 'value', 'label', false);
                        
                        // Restore previous selection if it still exists and is not empty
                        if (currentValue && currentValue !== '') {
                            window.calibrationChoices.setChoiceByValue(currentValue);
                            console.log('🔍 DEBUG: Restored calibration value using Choices.js:', currentValue);
                        } else {
                            // Ensure no selection is made
                            window.calibrationChoices.removeActiveItems();
                            console.log('🔍 DEBUG: No calibration value to restore, keeping empty');
                        }
                    } else {
                        console.log('🔍 DEBUG: Choices.js not available, using HTML manipulation');
                        calibrationSelect.innerHTML = '<option value="">Select Calibration</option>';
                        
                        console.log('🔍 DEBUG: Number of all calibrations received:', result.data.calibrations.length);
                        result.data.calibrations.forEach(calibration => {
                            console.log(`🔍 DEBUG: Adding all calibration: ${calibration.calib_name} (ID: ${calibration.id})`);
                            calibrationSelect.innerHTML += `<option value="${calibration.id}">${calibration.calib_name}</option>`;
                        });
                        
                        // Restore previous selection if it still exists
                        if (currentValue) {
                            calibrationSelect.value = currentValue;
                            console.log('🔍 DEBUG: Restored calibration value:', currentValue);
                        }
                    }
                }
            }
        })
        .catch(error => {
            console.error('🔍 DEBUG: Error loading all calibrations:', error);
        });
    }
}

// Update print machine display in Work Queue Info section
function updatePrintMachineDisplay(printMachine) {
    console.log('🔍 DEBUG: ========== UPDATE PRINT MACHINE DISPLAY START ==========');
    console.log('🔍 DEBUG: Updating print machine display to:', printMachine);
    
    // Find the print machine display element in Work Queue Info section
    const printMachineDisplay = document.querySelector('.work-queue-info .info-value:has(.machine-badge)');
    console.log('🔍 DEBUG: Print machine display element found:', !!printMachineDisplay);
    
    if (printMachineDisplay) {
        // Update the badge text and class
        const badge = printMachineDisplay.querySelector('.machine-badge');
        console.log('🔍 DEBUG: Machine badge element found:', !!badge);
        console.log('🔍 DEBUG: Current badge classes:', badge ? badge.className : 'N/A');
        console.log('🔍 DEBUG: Current badge text:', badge ? badge.textContent : 'N/A');
        
        if (badge) {
            // Remove all machine classes
            badge.className = badge.className.replace(/machine-\w+/g, '');
            badge.className = badge.className.replace(/sm\d|vlf/g, '');
            
            // Add new machine class
            const machineClass = 'machine-' + printMachine.toLowerCase();
            badge.classList.add(machineClass);
            badge.classList.add(printMachine.toLowerCase());
            
            console.log('🔍 DEBUG: Adding machine class:', machineClass);
            console.log('🔍 DEBUG: New badge classes:', badge.className);
            
            // Update text
            badge.textContent = printMachine;
            console.log('🔍 DEBUG: Updated Work Queue Info badge text to:', printMachine);
        }
    } else {
        console.log('🔍 DEBUG: Could not find Work Queue Info print machine display element');
    }
    
    // Also check and update the form dropdown if needed
    const formPrintMachineSelect = document.getElementById('printMachine');
    if (formPrintMachineSelect) {
        console.log('🔍 DEBUG: Found form print machine dropdown');
        console.log('🔍 DEBUG: Current form print machine value:', formPrintMachineSelect.value);
        console.log('🔍 DEBUG: Requested print machine value:', printMachine);
        console.log('🔍 DEBUG: Are they equal?', formPrintMachineSelect.value === printMachine);
        
        // Only update if different to avoid infinite loops
        if (formPrintMachineSelect.value !== printMachine) {
            console.log('🔍 DEBUG: Updating form print machine dropdown to:', printMachine);
            formPrintMachineSelect.value = printMachine;
            console.log('🔍 DEBUG: Form print machine value after update:', formPrintMachineSelect.value);
        } else {
            console.log('🔍 DEBUG: Form print machine already has correct value, no update needed');
        }
    } else {
        console.log('🔍 DEBUG: Could not find form print machine dropdown');
    }
    
    console.log('🔍 DEBUG: ========== UPDATE PRINT MACHINE DISPLAY END ==========');
}