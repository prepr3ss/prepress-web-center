document.addEventListener('DOMContentLoaded', function () {
    const currentPath = window.location.pathname;

    // Mapping URL ke ID tautan dan ID parent
    const urlMap = {
        '/impact/': { linkId: 'dashboardUtama' },
        '/impact/dashboard-ctp': { linkId: 'dashboardKpiCtpLink', parentSelector: '.ctp-submenu-parent', grandParentSelector: '.prepress-submenu-parent' },
        '/impact/tabel-kpi-ctp': { linkId: 'inputKpiCtpLink', parentSelector: '.ctp-submenu-parent', grandParentSelector: '.prepress-submenu-parent' },
        '/impact/input-kpi-ctp': { linkId: 'inputKpiCtpLink', parentSelector: '.ctp-submenu-parent', grandParentSelector: '.prepress-submenu-parent' },
        '/impact/ctp-data-adjustment': { linkId: 'ctpDataAdjustmentLink', parentSelector: '.ctp-submenu-parent', grandParentSelector: '.prepress-submenu-parent' },
        '/impact/ctp-data-bon': { linkId: 'ctpDataBonLink', parentSelector: '.ctp-submenu-parent', grandParentSelector: '.prepress-submenu-parent' },
        '/impact/data-adjustment': { linkId: 'dataAdjustmentLink', parentSelector: '.press-submenu-parent' },
        '/impact/data-bon': { linkId: 'dataBonLink', parentSelector: '.press-submenu-parent' },
        '/impact/request-plate-adjustment': { linkId: 'requestPlateAdjustmentLink', parentSelector: '.press-submenu-parent' },
        '/impact/request-plate-bon': { linkId: 'requestPlateBonLink', parentSelector: '.press-submenu-parent' },
        '/impact/mounting-data-adjustment': { linkId: 'mountingDataAdjustmentLink', parentSelector: '.mounting-submenu-parent', grandParentSelector: '.prepress-submenu-parent' },
        '/impact/admin/users': { linkId: 'adminUsersLink', parentSelector: '.admin-submenu-parent' },
        '/impact/admin/divisions': { linkId: 'adminDivisionsLink', parentSelector: '.admin-submenu-parent' },
        '/impact/settings/change-password': { linkId: 'changePasswordLink', parentSelector: '.settings-submenu-parent' },
        '/impact/stock-opname-ctp': { linkId: 'stockOpnameCtpLink', parentSelector: '.ctp-submenu-parent', grandParentSelector: '.prepress-submenu-parent' },
        '/impact/chemical-bon-ctp': { linkId: 'chemicalBonCtpLink', parentSelector: '.ctp-submenu-parent', grandParentSelector: '.prepress-submenu-parent' },
        '/impact/kartu-stock-ctp': { linkId: 'kartuStockCtpLink', parentSelector: '.ctp-submenu-parent', grandParentSelector: '.prepress-submenu-parent' },
        '/impact/pdnd-data-adjustment': { linkId: 'pdndDataAdjustmentLink', parentSelector: '.pdnd-submenu-parent' },
        '/impact/design-data-adjustment': { linkId: 'designDataAdjustmentLink', parentSelector: '.design-submenu-parent', grandParentSelector: '.prepress-submenu-parent' },
        '/impact/dashboard-mounting': { linkId: 'dashboardMountingLink', parentSelector: '.mounting-submenu-parent', grandParentSelector: '.prepress-submenu-parent' },
        '/impact/curve-data-adjustment': { linkId: 'curveDataAdjustmentLink', parentSelector: '.mounting-submenu-parent', grandParentSelector: '.prepress-submenu-parent' },
        '/impact/log-ctp': {linkId: 'logCtpOverviewLink', parentSelector: '.log-ctp-submenu-parent', grandParentSelector: '.ctp-submenu-parent', greatGrandParentSelector: '.prepress-submenu-parent'},
        '/impact/log-ctp/suprasetter': {linkId: 'logCtpSuprasetterLink', parentSelector: '.log-ctp-submenu-parent', grandParentSelector: '.ctp-submenu-parent', greatGrandParentSelector: '.prepress-submenu-parent'},
        '/impact/log-ctp/platesetter': {linkId: 'logCtpPlatesetterLink', parentSelector: '.log-ctp-submenu-parent', grandParentSelector: '.ctp-submenu-parent', greatGrandParentSelector: '.prepress-submenu-parent'},
        '/impact/log-ctp/trendsetter': {linkId: 'logCtpTrendsetterLink', parentSelector: '.log-ctp-submenu-parent', grandParentSelector: '.ctp-submenu-parent', greatGrandParentSelector: '.prepress-submenu-parent'},
        '/impact/cloudsphere/': {linkId: 'cloudsphereLink', parentSelector: '.rnd-submenu-parent', grandParentSelector: '.prepress-submenu-parent'},
        '/impact/rnd-cloudsphere/dashboard': {linkId: 'rndCloudsphereDashboardLink', parentSelector: '.rnd-submenu-parent', grandParentSelector: '.prepress-submenu-parent'},
        '/impact/rnd-cloudsphere/dashboard': {linkId: 'rndCloudsphereDashboardLink', parentSelector: '.rnd-submenu-parent', grandParentSelector: '.prepress-submenu-parent'},
        '/impact/rnd-cloudsphere/': {linkId: 'rndCloudsphereLink', parentSelector: '.rnd-submenu-parent', grandParentSelector: '.prepress-submenu-parent'},
        '/impact/rnd-cloudsphere/flow-configuration': {linkId: 'rndFlowConfigurationLink', parentSelector: '.rnd-submenu-parent', grandParentSelector: '.prepress-submenu-parent'},
        '/impact/rnd-proof-checklist': {linkId: 'rndProofChecklistLink', parentSelector: '.proof-submenu-parent', grandParentSelector: '.rnd-submenu-parent', greatGrandParentSelector: '.prepress-submenu-parent'},
        '/impact/mounting-work-order-incoming': {linkId: 'mountingWorkOrderIncomingLink', parentSelector: '.mounting-submenu-parent', grandParentSelector: '.prepress-submenu-parent'},
        '/impact/rnd-webcenter/': {linkId: 'rndWebcenterLink', parentSelector: '.mgmt-center-submenu-parent'},
        '/impact/tools/module/': {linkId: 'toolsModuleLink', parentSelector: '.tools-submenu-parent'},
        '/impact/tools/module/create': {linkId: 'toolsModuleLink', parentSelector: '.tools-submenu-parent'},
        '/impact/calibration-references/': {linkId: 'calibrationReferencesLink', parentSelector: '.calibration-ref-submenu-parent'},
        '/impact/calibration-references/create': {linkId: 'calibrationReferencesLink', parentSelector: '.calibration-ref-submenu-parent'},
        '/impact/calibration-references/edit/': {linkId: 'calibrationReferencesLink', parentSelector: '.calibration-ref-submenu-parent'},
        '/impact/calibration-references/g7/': {linkId: 'calibrationG7Link', parentSelector: '.calibration-ref-submenu-parent'},
        '/impact/calibration-references/g7/create': {linkId: 'calibrationG7Link', parentSelector: '.calibration-ref-submenu-parent'},
        '/impact/calibration-references/g7/edit/': {linkId: 'calibrationG7Link', parentSelector: '.calibration-ref-submenu-parent'},
        '/impact/calibration-references/iso/': {linkId: 'calibrationISOLink', parentSelector: '.calibration-ref-submenu-parent'},
        '/impact/calibration-references/iso/create': {linkId: 'calibrationISOLink', parentSelector: '.calibration-ref-submenu-parent'},
        '/impact/calibration-references/iso/edit/': {linkId: 'calibrationISOLink', parentSelector: '.calibration-ref-submenu-parent'},
        '/impact/calibration-references/existing/': {linkId: 'calibrationExistingLink', parentSelector: '.calibration-ref-submenu-parent'},
        '/impact/calibration-references/existing/create': {linkId: 'calibrationExistingLink', parentSelector: '.calibration-ref-submenu-parent'},
        '/impact/calibration-references/existing/edit/': {linkId: 'calibrationExistingLink', parentSelector: '.calibration-ref-submenu-parent'},
        '/impact/calibration-references/nestle/': {linkId: 'calibrationNestleLink', parentSelector: '.calibration-ref-submenu-parent'},
        '/impact/calibration-references/nestle/create': {linkId: 'calibrationNestleLink', parentSelector: '.calibration-ref-submenu-parent'},
        '/impact/calibration-references/nestle/edit/': {linkId: 'calibrationNestleLink', parentSelector: '.calibration-ref-submenu-parent'},
        '/impact/calibration-references/gmi/': {linkId: 'calibrationGmiLink', parentSelector: '.calibration-ref-submenu-parent'},
        '/impact/calibration-references/gmi/create': {linkId: 'calibrationGmiLink', parentSelector: '.calibration-ref-submenu-parent'},
        '/impact/calibration-references/gmi/edit/': {linkId: 'calibrationGmiLink', parentSelector: '.calibration-ref-submenu-parent'}
    };
    
    // Fungsi untuk mengaktifkan tautan dan parent submenu berdasarkan URL
    function setActive(linkId, parentSelector, grandParentSelector, greatGrandParentSelector) {
        
        document.querySelectorAll('.list-group-item').forEach(el => {
            if (el.classList.contains('active')) {
                el.classList.remove('active');
            }
        });
        
        const activeLink = document.getElementById(linkId);
        const parentLink = parentSelector ? document.querySelector(parentSelector) : null;
        const grandParentLink = grandParentSelector ? document.querySelector(grandParentSelector) : null;
        const greatGrandParentLink = greatGrandParentSelector ? document.querySelector(greatGrandParentSelector) : null;
        
        if (activeLink) {
            activeLink.classList.add('active');
        }
        if (parentLink) {
            parentLink.classList.add('active');
            parentLink.classList.remove('collapsed');
            const submenuId = parentLink.getAttribute('href').substring(1);
            const submenu = document.getElementById(submenuId);
            if (submenu) {
                submenu.classList.add('show');
            }
        }
        if (grandParentLink) {
            grandParentLink.classList.add('active');
            grandParentLink.classList.remove('collapsed');
            const grandSubmenuId = grandParentLink.getAttribute('href').substring(1);
            const grandSubmenu = document.getElementById(grandSubmenuId);
            if (grandSubmenu) {
                grandSubmenu.classList.add('show');
            }
        }
        if (greatGrandParentLink) {
            greatGrandParentLink.classList.add('active');
            greatGrandParentLink.classList.remove('collapsed');
            const greatGrandSubmenuId = greatGrandParentLink.getAttribute('href').substring(1);
            const greatGrandSubmenu = document.getElementById(greatGrandSubmenuId);
            if (greatGrandSubmenu) {
                greatGrandSubmenu.classList.add('show');
            }
        }
    }
    
    // Check if current path matches cloudsphere job detail pattern with ID
    let activeMapping = urlMap[currentPath];
    
    if (!activeMapping && currentPath.match(/^\/impact\/cloudsphere\/job\/\d+$/)) {
        // Use cloudsphere mapping for job detail pages with any ID
        activeMapping = {linkId: 'cloudsphereLink', parentSelector: '.rnd-submenu-parent', grandParentSelector: '.prepress-submenu-parent'};
    }

    if (!activeMapping && currentPath.match(/^\/impact\/edit-kpi-ctp\/\d+$/)) {
        // Use cloudsphere mapping for job detail pages with any ID
        activeMapping = {linkId: 'inputKpiCtpLink', parentSelector: '.ctp-submenu-parent', grandParentSelector: '.prepress-submenu-parent'};
    }

    if (!activeMapping && currentPath.match(/^\/impact\/rnd-cloudsphere\/job\/\d+$/)) {
        // Use cloudsphere mapping for job detail pages with any ID
        activeMapping = {linkId: 'rndCloudsphereLink', parentSelector: '.rnd-submenu-parent', grandParentSelector: '.prepress-submenu-parent'};
    }
    
    // Check for calibration reference edit patterns with IDs
    if (!activeMapping && currentPath.match(/^\/impact\/calibration-references\/g7\/edit\/\d+$/)) {
        activeMapping = {linkId: 'calibrationG7Link', parentSelector: '.calibration-ref-submenu-parent'};
    }
    
    if (!activeMapping && currentPath.match(/^\/impact\/calibration-references\/iso\/edit\/\d+$/)) {
        activeMapping = {linkId: 'calibrationISOLink', parentSelector: '.calibration-ref-submenu-parent'};
    }
    
    if (!activeMapping && currentPath.match(/^\/impact\/calibration-references\/existing\/edit\/\d+$/)) {
        activeMapping = {linkId: 'calibrationExistingLink', parentSelector: '.calibration-ref-submenu-parent'};
    }
    
    if (!activeMapping && currentPath.match(/^\/impact\/calibration-references\/nestle\/edit\/\d+$/)) {
        activeMapping = {linkId: 'calibrationNestleLink', parentSelector: '.calibration-ref-submenu-parent'};
    }
    
    if (!activeMapping && currentPath.match(/^\/impact\/calibration-references\/gmi\/edit\/\d+$/)) {
        activeMapping = {linkId: 'calibrationGmiLink', parentSelector: '.calibration-ref-submenu-parent'};
    }
    
    // Check 5W1H detail pattern
    if (!activeMapping && currentPath.match(/^\/impact\/tools\/5w1h\/\d+$/)) {
        activeMapping = {linkId: 'tools5w1hLink', parentSelector: '.tools-submenu-parent'};
    }
    
    // Check 5W1H edit pattern
    if (!activeMapping && currentPath.match(/^\/impact\/tools\/5w1h\/\d+\/edit$/)) {
        activeMapping = {linkId: 'tools5w1hLink', parentSelector: '.tools-submenu-parent'};
    }
    
    // Check for 5W1H dashboard and new form
    if (!activeMapping && (currentPath === '/impact/tools/5w1h' || currentPath === '/impact/tools/5w1h/new')) {
        activeMapping = {linkId: 'tools5w1hLink', parentSelector: '.tools-submenu-parent'};
    }
    
    // Check for Module dashboard, create, view, and edit patterns
    if (!activeMapping && currentPath.match(/^\/impact\/tools\/module(\/)?$/)) {
        activeMapping = {linkId: 'toolsModuleLink', parentSelector: '.tools-submenu-parent'};
    }
    
    if (!activeMapping && currentPath.match(/^\/impact\/tools\/module\/create$/)) {
        activeMapping = {linkId: 'toolsModuleLink', parentSelector: '.tools-submenu-parent'};
    }
    
    if (!activeMapping && currentPath.match(/^\/impact\/tools\/module\/\d+$/)) {
        activeMapping = {linkId: 'toolsModuleLink', parentSelector: '.tools-submenu-parent'};
    }
    
    if (!activeMapping && currentPath.match(/^\/impact\/tools\/module\/\d+\/edit$/)) {
        activeMapping = {linkId: 'toolsModuleLink', parentSelector: '.tools-submenu-parent'};
    }
    
    // Check for Proof Checklist patterns
    if (!activeMapping && currentPath.match(/^\/impact\/rnd-proof-checklist(\/)?$/)) {
        activeMapping = {linkId: 'rndProofChecklistLink', parentSelector: '.proof-submenu-parent', grandParentSelector: '.rnd-submenu-parent', greatGrandParentSelector: '.prepress-submenu-parent'};
    }
    
    if (!activeMapping && currentPath.match(/^\/impact\/rnd-proof-checklist\/create$/)) {
        activeMapping = {linkId: 'rndProofChecklistLink', parentSelector: '.proof-submenu-parent', grandParentSelector: '.rnd-submenu-parent', greatGrandParentSelector: '.prepress-submenu-parent'};
    }
    
    if (!activeMapping && currentPath.match(/^\/impact\/rnd-proof-checklist\/\d+$/)) {
        activeMapping = {linkId: 'rndProofChecklistLink', parentSelector: '.proof-submenu-parent', grandParentSelector: '.rnd-submenu-parent', greatGrandParentSelector: '.prepress-submenu-parent'};
    }
    
    if (!activeMapping && currentPath.match(/^\/impact\/rnd-proof-checklist\/\d+\/edit$/)) {
        activeMapping = {linkId: 'rndProofChecklistLink', parentSelector: '.proof-submenu-parent', grandParentSelector: '.rnd-submenu-parent', greatGrandParentSelector: '.prepress-submenu-parent'};
    }
    
    // Call setActive function to set initial state
    if (activeMapping) {
        setActive(activeMapping.linkId, activeMapping.parentSelector, activeMapping.grandParentSelector, activeMapping.greatGrandParentSelector);
    }
    
    // Helper function to calculate CSS specificity
    function calculateSpecificity(selector) {
        let specificity = 0;
        // Count ID selectors
        specificity += (selector.match(/#[\w-]+/g) || []).length * 100;
        // Count class, attribute, pseudo-class selectors
        specificity += (selector.match(/\.[\w-]+|\[[\w-]+/g) || []).length * 10;
        // Count element selectors
        specificity += (selector.match(/^\w+|[\s]\w+/g) || []).length * 1;
        return specificity;
    }

    // Custom collapse handling untuk sidebar + animasi chevron SVG
    document.querySelectorAll('[data-bs-toggle="collapse"]').forEach(parentLink => {
        parentLink.removeAttribute('data-bs-toggle');

        parentLink.addEventListener('click', function (e) {
            e.preventDefault();
            e.stopPropagation();

            const targetId = this.getAttribute('href');
            const targetSubmenu = document.querySelector(targetId);
            if (!targetSubmenu) {
                return;
            }

            const isCurrentlyOpen = targetSubmenu.classList.contains('show');

            const isLevel1 = this.classList.contains('prepress-submenu-parent') ||
                this.classList.contains('press-submenu-parent') ||
                this.classList.contains('pdnd-submenu-parent') ||
                this.classList.contains('admin-submenu-parent') ||
                this.classList.contains('settings-submenu-parent') ||
                this.classList.contains('mgmt-center-submenu-parent');

            const isLevel2 = this.classList.contains('ctp-submenu-parent') ||
                this.classList.contains('mounting-submenu-parent') ||
                this.classList.contains('design-submenu-parent') ||
                this.classList.contains('rnd-submenu-parent');

            const isLevel3 = this.classList.contains('log-ctp-submenu-parent') ||
                this.classList.contains('proof-submenu-parent');

            const chevron = this.querySelector('.sidebar-chevron');

            if (isCurrentlyOpen) {
                this.classList.add('collapsed');
                this.classList.remove('active');
                targetSubmenu.classList.remove('show');
                if (chevron) chevron.classList.remove('rotated');
                return;
            }

            // Close other submenus at same level
            document.querySelectorAll('.collapse.show').forEach(openSubmenu => {
                const openParent = document.querySelector(`[href="#${openSubmenu.id}"]`);
                if (!openParent) return;

                const openIsLevel1 = openParent.classList.contains('prepress-submenu-parent') ||
                    openParent.classList.contains('press-submenu-parent') ||
                    openParent.classList.contains('pdnd-submenu-parent') ||
                    openParent.classList.contains('admin-submenu-parent') ||
                    openParent.classList.contains('settings-submenu-parent') ||
                    openParent.classList.contains('mgmt-center-submenu-parent');

                const openIsLevel2 = openParent.classList.contains('ctp-submenu-parent') ||
                    openParent.classList.contains('mounting-submenu-parent') ||
                    openParent.classList.contains('design-submenu-parent') ||
                    openParent.classList.contains('rnd-submenu-parent');

                const openIsLevel3 = openParent.classList.contains('log-ctp-submenu-parent') ||
                    openParent.classList.contains('proof-submenu-parent');

                const sameLevel = (isLevel1 && openIsLevel1) || (isLevel2 && openIsLevel2) || (isLevel3 && openIsLevel3);

                if (sameLevel && openSubmenu.id !== targetId.substring(1)) {
                    openParent.classList.add('collapsed');
                    openParent.classList.remove('active');
                    openSubmenu.classList.remove('show');
                    const openChevron = openParent.querySelector('.sidebar-chevron');
                    if (openChevron) openChevron.classList.remove('rotated');
                }
            });

            this.classList.remove('collapsed');
            this.classList.add('active');
            targetSubmenu.classList.add('show');
            if (chevron) chevron.classList.add('rotated');
        });
    });

    // ===== MOBILE SIDEBAR TOGGLE FUNCTIONALITY =====
    const sidebarToggleBtn = document.getElementById('sidebarToggleBtn');
    const sidebarWrapper = document.getElementById('sidebar-wrapper');
    const sidebarOverlay = document.getElementById('sidebarOverlay');
    const mobileBreakpoint = 768;

    // Toggle sidebar open/closed on mobile
    if (sidebarToggleBtn) {
        sidebarToggleBtn.addEventListener('click', function(e) {
            e.stopPropagation();
            const isOpen = sidebarWrapper.classList.contains('active');
            
            if (isOpen) {
                closeSidebar();
            } else {
                openSidebar();
            }
        });
    }

    // Close sidebar when overlay is clicked
    if (sidebarOverlay) {
        sidebarOverlay.addEventListener('click', function() {
            closeSidebar();
        });
    }

    // Close sidebar when a link is clicked (except collapsible toggles and parent items)
    document.querySelectorAll('#sidebar-wrapper .list-group-item').forEach(function(item) {
        item.addEventListener('click', function(e) {
            // Check if this is a parent/grand-parent item (collapsible menu)
            const isSubmenuParent = this.classList.toString().includes('submenu-parent');
            
            // Only close on mobile devices (when sidebar is in mobile mode)
            const isMobileMode = window.innerWidth < mobileBreakpoint;
            
            // Only close if:
            // 1. We're in mobile mode
            // 2. NOT a collapse toggle button (data-bs-toggle attribute)
            // 3. NOT already has collapsed class
            // 4. NOT a parent/grand-parent item (submenu-parent class)
            if (isMobileMode &&
                !this.hasAttribute('data-bs-toggle') && 
                !this.classList.contains('collapsed') && 
                !isSubmenuParent) {
                setTimeout(closeSidebar, 300); // Close after a brief delay
            }
        });
    });

    // Close sidebar on window resize to desktop breakpoint
    window.addEventListener('resize', function() {
        if (window.innerWidth >= mobileBreakpoint && sidebarWrapper.classList.contains('active')) {
            closeSidebar();
        }
    });

    // Close sidebar on Escape key press
    document.addEventListener('keydown', function(e) {
        if (e.key === 'Escape' && sidebarWrapper.classList.contains('active')) {
            closeSidebar();
            if (sidebarToggleBtn) sidebarToggleBtn.focus();
        }
    });

    // Helper functions
    function openSidebar() {
        sidebarWrapper.classList.add('active');
        if (sidebarOverlay) sidebarOverlay.classList.add('active');
        if (sidebarToggleBtn) {
            sidebarToggleBtn.setAttribute('aria-expanded', 'true');
        }
        document.body.style.overflow = 'hidden'; // Prevent scrolling on mobile
    }

    function closeSidebar() {
        sidebarWrapper.classList.remove('active');
        if (sidebarOverlay) sidebarOverlay.classList.remove('active');
        if (sidebarToggleBtn) {
            sidebarToggleBtn.setAttribute('aria-expanded', 'false');
        }
        document.body.style.overflow = ''; // Restore scrolling
    }
});
