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
        '/impact/mounting-work-order-incoming': {linkId: 'mountingWorkOrderIncomingLink', parentSelector: '.mounting-submenu-parent', grandParentSelector: '.prepress-submenu-parent'}
    };
    
    // Fungsi untuk mengaktifkan tautan dan parent submenu berdasarkan URL
    function setActive(linkId, parentSelector, grandParentSelector, greatGrandParentSelector) {
        document.querySelectorAll('.list-group-item').forEach(el => el.classList.remove('active'));
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
    
    // Panggil fungsi setActive untuk mengatur status awal
    if (activeMapping) {
        setActive(activeMapping.linkId, activeMapping.parentSelector, activeMapping.grandParentSelector, activeMapping.greatGrandParentSelector);
    }

    // Custom collapse handling untuk sidebar + animasi chevron SVG
    document.querySelectorAll('[data-bs-toggle="collapse"]').forEach(parentLink => {
        parentLink.removeAttribute('data-bs-toggle');

        parentLink.addEventListener('click', function (e) {
            e.preventDefault();
            e.stopPropagation();

            const targetId = this.getAttribute('href');
            const targetSubmenu = document.querySelector(targetId);
            if (!targetSubmenu) return;

            const isCurrentlyOpen = targetSubmenu.classList.contains('show');

            const isLevel1 = this.classList.contains('prepress-submenu-parent') ||
                this.classList.contains('press-submenu-parent') ||
                this.classList.contains('pdnd-submenu-parent') ||
                this.classList.contains('admin-submenu-parent') ||
                this.classList.contains('settings-submenu-parent');

            const isLevel2 = this.classList.contains('ctp-submenu-parent') ||
                this.classList.contains('mounting-submenu-parent') ||
                this.classList.contains('design-submenu-parent') ||
                this.classList.contains('rnd-submenu-parent');

            const isLevel3 = this.classList.contains('log-ctp-submenu-parent');

            const chevron = this.querySelector('.sidebar-chevron');

            if (isCurrentlyOpen) {
                this.classList.add('collapsed');
                this.classList.remove('active');
                targetSubmenu.classList.remove('show');
                if (chevron) chevron.classList.remove('rotated');
                return;
            }

            document.querySelectorAll('.collapse.show').forEach(openSubmenu => {
                const openParent = document.querySelector(`[href="#${openSubmenu.id}"]`);
                if (!openParent) return;

                const openIsLevel1 = openParent.classList.contains('prepress-submenu-parent') ||
                    openParent.classList.contains('press-submenu-parent') ||
                    openParent.classList.contains('pdnd-submenu-parent') ||
                    openParent.classList.contains('admin-submenu-parent') ||
                    openParent.classList.contains('settings-submenu-parent');

                const openIsLevel2 = openParent.classList.contains('ctp-submenu-parent') ||
                    openParent.classList.contains('mounting-submenu-parent') ||
                    openParent.classList.contains('design-submenu-parent') ||
                    openParent.classList.contains('rnd-submenu-parent');

                const openIsLevel3 = openParent.classList.contains('log-ctp-submenu-parent');

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
});