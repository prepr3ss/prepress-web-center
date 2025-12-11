 // ...
const SidebarNotification = {
    async checkNotifications() {
        try {
            const response = await fetch('/impact/api/check-notifications');
            if (!response.ok) {
                return;
            }
            const data = await response.json();
            
            // --- DEBUG: log payload untuk verifikasi struktur data ---
            console.debug('[SidebarNotification] Notification payload:', data);

            // =========================
            // CTP Production Notifications
            // =========================
            const ctpAdjustmentActive = this.updateSubmenuNotification(
                'ctpDataAdjustmentLink',
                ['proses_ctp', 'proses_plate', 'antar_plate'],
                data.ctp_adjustment
            );

            const ctpBonActive = this.updateSubmenuNotification(
                'ctpDataBonLink',
                ['proses_ctp', 'proses_plate', 'antar_plate'],
                data.ctp_bon
            );

            const ctpHasNotifications = ctpAdjustmentActive || ctpBonActive;
            this.updateParentNotification('ctpSubmenu', ctpHasNotifications);

            // =========================
            // Mounting Production Notifications
            // =========================
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

            const mountingHasNotifications = mountingAdjustmentActive || curveAdjustmentActive;
            this.updateParentNotification('mountingSubmenu', mountingHasNotifications);

            // =========================
            // Design Production Notifications
            // =========================
            const designAdjustmentActive = this.updateSubmenuNotification(
                'designDataAdjustmentLink',
                ['menunggu_adjustment_design', 'proses_adjustment_design', 'ditolakmounting'],
                data.design
            );
            this.updateParentNotification('designSubmenu', designAdjustmentActive);

            // =========================
            // PDND Production Notifications
            // =========================
            const pdndAdjustmentActive = this.updateSubmenuNotification(
                'pdndDataAdjustmentLink',
                ['menunggu_adjustment_pdnd', 'proses_adjustment_pdnd', 'ditolakmounting'],
                data.pdnd
            );
            this.updateParentNotification('pdndSubmenu', pdndAdjustmentActive);

            // =========================
            // Prepress Production (AGGREGATED)
            // =========================
            const prepressHasNotifications =
                ctpHasNotifications ||
                mountingHasNotifications ||
                designAdjustmentActive;

            this.updateParentNotification('prepressSubmenu', prepressHasNotifications);

            console.debug('[SidebarNotification] Status flags:', {
                ctpAdjustmentActive,
                ctpBonActive,
                ctpHasNotifications,
                mountingAdjustmentActive,
                curveAdjustmentActive,
                mountingHasNotifications,
                designAdjustmentActive,
                pdndAdjustmentActive,
                prepressHasNotifications
            });

        } catch (error) {
            // Optional: silent fail in production
        }
    },
    
    // --- FUNGSI BARU/DIUBAH: updateSubmenuNotification ---
    // Fungsi ini hanya fokus pada satu link submenu dan mengembalikan status aktifnya
    updateSubmenuNotification(id, states, data) {
        const link = document.getElementById(id);
        if (!link) {
            return false;
        }

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

    // Fungsi ini hanya fokus pada Parent Menu
    updateParentNotification(parentId, hasActiveItems) {
        const parentMenu = document.querySelector(`[href="#${parentId}"]`);
        if (!parentMenu) {
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
    
    SidebarNotification.startPolling();
});