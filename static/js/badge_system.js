/**
 * Unified Badge Status System
 * Sistem badge terpusat untuk konsistensi di seluruh aplikasi
 */

// Status mapping untuk badge classes - Simplified Workflow per Division
const STATUS_BADGE_MAPPING = {
    'menunggu_adjustment': {
        class: 'badge-menunggu',
        label: 'Menunggu Adjustment',
        color: 'warning',
        description: 'PIC Press sudah request form'
    },
    'proses_adjustment': {
        class: 'badge-proses',
        label: 'Proses Adjustment', 
        color: 'info',
        description: 'PIC Mounting sedang adjustment'
    },
    'proses_ctp': {
        class: 'badge-menunggu-plate',
        label: 'Menunggu Plate',
        color: 'primary',
        description: 'Adjustment selesai, menunggu CTP'
    },
    'proses_plate': {
        class: 'badge-proses-plate',
        label: 'Proses Plate',
        color: 'primary',
        description: 'PIC CTP sedang buat plate'
    },
    'antar_plate': {
        class: 'badge-antar',
        label: 'Plate Sedang Diantar',
        color: 'info',
        description: 'Plate selesai, sedang diantar'
    },
    'selesai': {
        class: 'badge-selesai',
        label: 'Selesai',
        color: 'success',
        description: 'Plate sudah sampai di mesin'
    }
};

// Status mapping khusus untuk Mounting Division (Workflow: Menunggu → Proses → Selesai)
const MOUNTING_STATUS_MAPPING = {
    'menunggu_adjustment': {
        class: 'badge-menunggu',
        label: 'Menunggu Adjustment',
        color: 'warning',
        description: 'PIC Press sudah request form'
    },
    'proses_adjustment': {
        class: 'badge-proses',
        label: 'Proses Adjustment', 
        color: 'info',
        description: 'PIC Mounting sedang adjustment'
    },
    'selesai': {
        class: 'badge-selesai',
        label: 'Selesai',
        color: 'success',
        description: 'Adjustment sudah selesai'
    },
    // Fallback untuk status lain jika ada
    'proses_ctp': {
        class: 'badge-selesai',
        label: 'Selesai',
        color: 'success',
        description: 'Adjustment sudah selesai'
    }
};

// Status mapping khusus untuk CTP Division (Workflow: Menunggu Plate → Proses Plate → Diantar → Selesai)
const CTP_STATUS_MAPPING = {
    'proses_ctp': {
        class: 'badge-menunggu-plate',
        label: 'Menunggu Plate',
        color: 'primary',
        description: 'Adjustment selesai, menunggu CTP'
    },
    'proses_plate': {
        class: 'badge-proses-plate',
        label: 'Proses Plate',
        color: 'primary',
        description: 'PIC CTP sedang buat plate'
    },
    'antar_plate': {
        class: 'badge-antar',
        label: 'Plate Sedang Diantar',
        color: 'info',
        description: 'Plate selesai, sedang diantar'
    },
    'selesai': {
        class: 'badge-selesai',
        label: 'Selesai',
        color: 'success',
        description: 'Plate sudah sampai di mesin'
    }
};

/**
 * Initialize badge system untuk semua badge dengan data-status
 */
function initializeBadgeSystem() {
    const statusBadges = document.querySelectorAll('[data-status]');
    statusBadges.forEach(badge => {
        const status = badge.getAttribute('data-status');
        const statusInfo = STATUS_BADGE_MAPPING[status];
        
        if (statusInfo) {
            // Remove existing badge classes
            badge.classList.remove('badge-menunggu', 'badge-proses', 'badge-aktif', 'badge-selesai', 'badge-antar');
            
            // Add new badge class
            badge.classList.add(statusInfo.class);
            
            // Update text if needed
            if (badge.getAttribute('data-auto-label') === 'true') {
                badge.textContent = statusInfo.label;
            }
        }
    });
}

/**
 * Get badge status info berdasarkan division
 * @param {string} status - Status string
 * @param {string} division - Division type ('mounting', 'ctp', or default)
 * @returns {object} Status info object
 */
function getStatusInfo(status, division = 'default') {
    switch (division) {
        case 'mounting':
            return MOUNTING_STATUS_MAPPING[status] || MOUNTING_STATUS_MAPPING['menunggu_adjustment'];
        case 'ctp':
            return CTP_STATUS_MAPPING[status] || CTP_STATUS_MAPPING['proses_ctp'];
        default:
            return STATUS_BADGE_MAPPING[status] || STATUS_BADGE_MAPPING['menunggu_adjustment'];
    }
}

/**
 * Get badge class for status
 * @param {string} status - Status string
 * @param {string} division - Division type ('mounting', 'ctp', or default)
 * @returns {string} Badge class name
 */
function getBadgeClass(status, division = 'default') {
    const statusInfo = getStatusInfo(status, division);
    return statusInfo ? statusInfo.class : 'badge-menunggu';
}

/**
 * Get badge color for status (untuk compatibility dengan sistem lama)
 * @param {string} status - Status string  
 * @param {string} division - Division type ('mounting', 'ctp', or default)
 * @returns {string} Bootstrap color class
 */
function getBadgeColor(status, division = 'default') {
    const statusInfo = getStatusInfo(status, division);
    return statusInfo ? statusInfo.color : 'warning';
}

/**
 * Get formatted label for status
 * @param {string} status - Status string
 * @param {string} division - Division type ('mounting', 'ctp', or default)
 * @returns {string} Formatted label
 */
function getStatusLabel(status, division = 'default') {
    const statusInfo = getStatusInfo(status, division);
    return statusInfo ? statusInfo.label : status.replace('_', ' ').replace(/\b\w/g, l => l.toUpperCase());
}

/**
 * Create badge element programmatically
 * @param {string} status - Status string
 * @param {string} size - Badge size ('sm', 'md', 'lg')
 * @param {string} division - Division type ('mounting', 'ctp', or default)
 * @returns {HTMLElement} Badge element
 */
function createBadgeElement(status, size = 'md', division = 'default') {
    const statusInfo = getStatusInfo(status, division);
    const badge = document.createElement('span');
    
    badge.className = `badge status-badge ${statusInfo ? statusInfo.class : 'badge-menunggu'}`;
    badge.setAttribute('data-status', status);
    badge.textContent = statusInfo ? statusInfo.label : getStatusLabel(status, division);
    
    // Add size class
    if (size === 'sm') {
        badge.classList.add('fs-7');
    } else if (size === 'lg') {
        badge.classList.add('fs-5');
    } else {
        badge.classList.add('fs-6');
    }
    
    return badge;
}

// Auto-initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    initializeBadgeSystem();
});

// Export functions for use in other scripts
window.BadgeSystem = {
    initialize: initializeBadgeSystem,
    getBadgeClass: getBadgeClass,
    getBadgeColor: getBadgeColor,
    getStatusLabel: getStatusLabel,
    getStatusInfo: getStatusInfo,
    createBadge: createBadgeElement,
    STATUS_MAPPING: STATUS_BADGE_MAPPING,
    MOUNTING_MAPPING: MOUNTING_STATUS_MAPPING,
    CTP_MAPPING: CTP_STATUS_MAPPING
};
