// ...
const SidebarNotification = {
    async checkNotifications() {
        try {
            console.log('Checking notifications...');
            const response = await fetch('/api/check-notifications');
            if (!response.ok) {
                console.error('Failed to fetch notifications:', response.status);
                return;
            }
            const data = await response.json();
            console.log('Notifications data:', data);
            
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

            const curveAdjustmentActive = this.updateSubmenuNotification(
                'curveDataAdjustmentLink', 
                ['menunggu_adjustment_curve', 'proses_adjustment_curve', 'ditolakmounting'], 
                data.curve
            );
            this.updateParentNotification('mountingSubmenu', mountingAdjustmentActive || curveAdjustmentActive);

        } catch (error) {
            console.error('Error checking notifications:', error);
            console.error('Error stack:', error.stack);
        }
    },
    
    // --- FUNGSI BARU/DIUBAH: updateSubmenuNotification ---
    // Fungsi ini hanya fokus pada satu link submenu dan mengembalikan status aktifnya
    updateSubmenuNotification(id, states, data) {
        console.log(`Updating submenu notification for ${id}`);
        const link = document.getElementById(id);
        if (!link) {
            console.error(`Element with id ${id} not found`);
            return false;
        }
        console.log(`Found link: ${link.textContent}, data:`, data);

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
        console.log(`Updating parent notification for ${parentId}, hasActive: ${hasActiveItems}`);
        const parentMenu = document.querySelector(`[href="#${parentId}"]`);
        if (!parentMenu) {
            console.error(`Parent menu with href="#${parentId}" not found`);
            return;
        }

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
    // CSS sudah dimuat dari file sidebar_notification.css
    
    // Debug: Log untuk memastikan script berjalan
    console.log('Sidebar Notification System initialized');
    
    SidebarNotification.startPolling();
});