// ...
const SidebarNotification = {
    async checkNotifications() {
        try {
            const response = await fetch('/api/check-notifications');
            const data = await response.json();
            
            // CTP Production Notifications
            
            // 1. Update Submenu Adjustment
            const ctpAdjustmentActive = this.updateSubmenuNotification(
                'ctpDataAdjustmentLink', 
                ['proses_ctp', 'proses_plate', 'antar_plate'], 
                data.ctp_adjustment // Gunakan data CTP Adjustment
            );

            // 2. Update Submenu Bon
            const ctpBonActive = this.updateSubmenuNotification(
                'ctpDataBonLink', 
                ['proses_ctp', 'proses_plate', 'antar_plate'], 
                data.ctp_bon // Gunakan data CTP Bon
            );

            // 3. Update Parent Menu CTP
            // Gabungkan status aktif dari kedua submenu
            this.updateParentNotification('ctpSubmenu', ctpAdjustmentActive || ctpBonActive);


            // PDND Production Notifications (Menggunakan struktur yang sama untuk konsistensi)
            const pdndAdjustmentActive = this.updateSubmenuNotification(
                'pdndDataAdjustmentLink', 
                ['menunggu_adjustment_pdnd', 'proses_adjustment_pdnd', 'ditolakmounting'], 
                data.pdnd
            );
            this.updateParentNotification('pdndSubmenu', pdndAdjustmentActive);
            
            // Design Production Notifications
            const designAdjustmentActive = this.updateSubmenuNotification(
                'designDataAdjustmentLink', 
                ['menunggu_adjustment_design', 'proses_adjustment_design', 'ditolakmounting'], 
                data.design
            );
            this.updateParentNotification('designSubmenu', designAdjustmentActive);

            // Mounting Production Notifications
            const mountingAdjustmentActive = this.updateSubmenuNotification(
                'mountingDataAdjustmentLink', 
                ['menunggu_adjustment', 'proses_adjustment', 'ditolakctp'], 
                data.mounting
            );
            this.updateParentNotification('mountingSubmenu', mountingAdjustmentActive);

        } catch (error) {
            console.error('Error checking notifications:', error);
        }
    },
    
    // --- FUNGSI BARU/DIUBAH: updateSubmenuNotification ---
    // Fungsi ini hanya fokus pada satu link submenu dan mengembalikan status aktifnya
    updateSubmenuNotification(id, states, data) {
        const link = document.getElementById(id);
        if (!link) return false;

        // Remove existing dots from submenu item
        const existingSubDots = link.querySelectorAll('.submenu-notification-dot');
        existingSubDots.forEach(dot => dot.remove());

        // Check if this submenu item has active notifications
        const hasActive = states.some(state => 
            data?.some(item => item.status === state)
        );

        if (hasActive) {
            // Add dot to submenu item
            const subDot = document.createElement('span');
            subDot.className = 'submenu-notification-dot';
            link.appendChild(subDot);
        }
        return hasActive; // Mengembalikan status aktif
    },

    // --- FUNGSI BARU: updateParentNotification ---
    // Fungsi ini hanya fokus pada Parent Menu
    updateParentNotification(parentId, hasActiveItems) {
        const parentMenu = document.querySelector(`[href="#${parentId}"]`);
        if (!parentMenu) return;

        // Remove existing dots/badges
        const existingDots = parentMenu.querySelectorAll('.notification-dot');
        existingDots.forEach(dot => dot.remove());
        
        if (hasActiveItems) {
            const dot = document.createElement('span');
            dot.className = 'notification-dot';
            parentMenu.appendChild(dot);
        }
    },

    startPolling() {
        this.checkNotifications();
        // Check every 10 seconds
        setInterval(() => this.checkNotifications(), 10000);
    }
};

// Initialize when document is ready
document.addEventListener('DOMContentLoaded', () => {
    // Tambahkan CSS untuk dot jika belum ada (jika Anda menggunakan badge sebelumnya)
    const style = document.createElement('style');
    style.innerHTML = `
        .submenu-notification-dot {
            height: 8px;
            width: 8px;
            background-color: #dc3545; /* Merah */
            border-radius: 50%;
            display: inline-block;
            margin-left: 8px;
            flex-shrink: 0;
        }
        .notification-dot {
            height: 10px;
            width: 10px;
            background-color: #dc3545; /* Merah */
            border-radius: 50%;
            display: inline-block;
            margin-left: 10px;
            margin-right: 0px; /* Geser ke kiri sedikit agar tidak terlalu jauh dari teks */
            flex-shrink: 0;
        }
    `;
    document.head.appendChild(style);
    
    SidebarNotification.startPolling();
});