// Enhanced Form Handler dengan fitur tambahan
document.addEventListener('DOMContentLoaded', function() {
    const form = document.getElementById('plateAdjustmentForm');
    const submitButton = form.querySelector('button[type="submit"]');
    
    // Form submission handler
    form.addEventListener('submit', async function(e) {
        e.preventDefault();
        
        // Validasi form
        if (!validateForm()) {
            showAlert('Mohon lengkapi semua field yang diperlukan', 'error');
            return;
        }
        
        // Loading state
        setSubmitLoading(true);
        
        try {
            const formData = new FormData(form);
            const data = Object.fromEntries(formData.entries());
            
            const response = await fetch('/submit-plate-adjustment', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(data)
            });
            
            const result = await response.json();
            
            if (response.ok) {
                showToast(
                    result.message || 'Request plate adjustment berhasil dikirim!', 
                    'success'
                );
                form.reset();
                clearValidationStates();
            } else {
                showToast(
                    result.error || 'Terjadi kesalahan saat mengirim request!', 
                    'error'
                );
            }
        } catch (error) {
            console.error('Error:', error);
            showToast(
                'Terjadi kesalahan koneksi. Silakan coba lagi.', 
                'error'
            );
        } finally {
            setSubmitLoading(false);
        }
    });
    
    // Real-time form validation
    const requiredFields = form.querySelectorAll('[required]');
    requiredFields.forEach(field => {
        field.addEventListener('blur', function() {
            validateField(this);
        });
        
        field.addEventListener('input', function() {
            if (this.classList.contains('is-invalid')) {
                validateField(this);
            }
        });
    });
});

// Form validation functions
function validateForm() {
    const requiredFields = document.querySelectorAll('#plateAdjustmentForm [required]');
    let isValid = true;
    
    requiredFields.forEach(field => {
        if (!validateField(field)) {
            isValid = false;
        }
    });
    
    return isValid;
}

function validateField(field) {
    const value = field.value.trim();
    const isValid = value !== '';
    
    // Validasi khusus untuk number fields
    if (field.type === 'number' && field.hasAttribute('required')) {
        const numValue = parseFloat(value);
        if (isNaN(numValue) || numValue <= 0) {
            field.classList.add('is-invalid');
            field.classList.remove('is-valid');
            return false;
        }
    }
    
    if (isValid) {
        field.classList.remove('is-invalid');
        field.classList.add('is-valid');
    } else {
        field.classList.add('is-invalid');
        field.classList.remove('is-valid');
    }
    
    return isValid;
}

function clearValidationStates() {
    const fields = document.querySelectorAll('#plateAdjustmentForm .form-control, #plateAdjustmentForm .form-select');
    fields.forEach(field => {
        field.classList.remove('is-valid', 'is-invalid');
    });
}

// Toast notification system - like mounting data adjustment
function showToast(message, type = 'info', duration = 5000) {
    const toastContainer = document.getElementById('toastContainer');
    const toastId = 'toast-' + Date.now();
    
    const toastHTML = `
        <div class="toast toast-${type}" id="${toastId}" role="alert" aria-live="assertive" aria-atomic="true">
            <div class="toast-body d-flex align-items-center">
                <i class="fas ${getToastIcon(type)} me-2"></i>
                <span class="flex-grow-1">${message}</span>
                <button type="button" class="btn-close btn-close-white ms-2" data-bs-dismiss="toast"></button>
            </div>
        </div>
    `;
    
    toastContainer.insertAdjacentHTML('beforeend', toastHTML);
    
    const toastElement = document.getElementById(toastId);
    const toast = new bootstrap.Toast(toastElement, { delay: duration });
    toast.show();
    
    // Auto remove after hiding
    toastElement.addEventListener('hidden.bs.toast', function() {
        toastElement.remove();
    });
}

function getToastIcon(type) {
    const icons = {
        'success': 'fa-check-circle',
        'error': 'fa-exclamation-circle',
        'info': 'fa-info-circle',
        'warning': 'fa-exclamation-triangle'
    };
    return icons[type] || icons['info'];
}

// Alert function for validation errors
function showAlert(message, type = 'info') {
    const alertContainer = document.getElementById('alertContainer');
    const alertElement = alertContainer.querySelector('.alert');
    const alertMessage = document.getElementById('alertMessage');
    
    // Reset classes
    alertElement.className = 'alert';
    
    // Set type
    if (type === 'error') {
        alertElement.classList.add('alert-danger');
    } else if (type === 'success') {
        alertElement.classList.add('alert-success');
    } else {
        alertElement.classList.add('alert-info');
    }
    
    alertMessage.textContent = message;
    alertContainer.style.display = 'block';
    
    // Auto hide after 5 seconds
    setTimeout(() => {
        alertContainer.style.display = 'none';
    }, 5000);
}

// Loading state management
function setSubmitLoading(loading) {
    const submitButton = document.querySelector('#plateAdjustmentForm button[type="submit"]');
    if (!submitButton) return;
    
    if (loading) {
        submitButton.disabled = true;
        submitButton.classList.add('btn-loading');
        submitButton.innerHTML = '<span>Mengirim...</span>';
    } else {
        submitButton.disabled = false;
        submitButton.classList.remove('btn-loading');
        submitButton.innerHTML = '<i class="fas fa-paper-plane me-2"></i>Submit Request';
    }
}

// Reset form function
function resetForm() {
    const form = document.getElementById('plateAdjustmentForm');
    if (form) {
        form.reset();
        clearValidationStates();
        
        // Hide any alerts
        const alertContainer = document.getElementById('alertContainer');
        if (alertContainer) {
            alertContainer.style.display = 'none';
        }
        
        showToast('Form berhasil direset', 'success');
    }
}

// Set today's date as default
document.addEventListener('DOMContentLoaded', function() {
    const dateInput = document.querySelector('input[name="tanggal"]');
    if (dateInput && !dateInput.value) {
        const today = new Date().toISOString().split('T')[0];
        dateInput.value = today;
    }
});