document.addEventListener('DOMContentLoaded', function () {
    const currentPath = window.location.pathname;

    // Mapping URL ke ID tautan dan ID parent
    const urlMap = {
        '/': { linkId: 'dashboardUtama' },
        '/dashboard-ctp': { linkId: 'dashboardKpiCtpLink', parentSelector: '.ctp-submenu-parent' },
        '/tabel-kpi-ctp': { linkId: 'inputKpiCtpLink', parentSelector: '.ctp-submenu-parent' },
        '/input-kpi-ctp': { linkId: 'formKpiCtpLink', parentSelector: '.ctp-submenu-parent' },
        '/ctp-data-adjustment': { linkId: 'ctpDataAdjustmentLink', parentSelector: '.ctp-submenu-parent' },
        '/ctp-data-bon': { linkId: 'ctpDataBonLink', parentSelector: '.ctp-submenu-parent' },
        '/data-adjustment': { linkId: 'dataAdjustmentLink', parentSelector: '.press-submenu-parent' },
        '/data-bon': { linkId: 'dataBonLink', parentSelector: '.press-submenu-parent' },
        '/request-plate-adjustment': { linkId: 'requestPlateAdjustmentLink', parentSelector: '.press-submenu-parent' },
        '/request-plate-bon': { linkId: 'requestPlateBonLink', parentSelector: '.press-submenu-parent' },
        '/mounting-data-adjustment': { linkId: 'mountingDataAdjustmentLink', parentSelector: '.mounting-submenu-parent' },
        '/admin/users': { linkId: 'adminUsersLink', parentSelector: '.admin-submenu-parent' },
        '/admin/divisions': { linkId: 'adminDivisionsLink', parentSelector: '.admin-submenu-parent' },
        '/settings/change-password': { linkId: 'changePasswordLink', parentSelector: '.settings-submenu-parent' },
        '/stock-opname-ctp': { linkId: 'stockOpnameCtpLink', parentSelector: '.ctp-submenu-parent' },
        '/chemical-bon-ctp': { linkId: 'chemicalBonCtpLink', parentSelector: '.ctp-submenu-parent' },
        '/kartu-stock-ctp': { linkId: 'kartuStockCtpLink', parentSelector: '.ctp-submenu-parent' }
    };
    
    // Fungsi untuk mengaktifkan tautan dan parent submenu berdasarkan URL
    function setActive(linkId, parentSelector) {
        document.querySelectorAll('.list-group-item').forEach(el => el.classList.remove('active'));
        const activeLink = document.getElementById(linkId);
        const parentLink = document.querySelector(parentSelector);
        
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
    }
    
    // Panggil fungsi setActive untuk mengatur status awal
    const activeMapping = urlMap[currentPath];
    if (activeMapping) {
        setActive(activeMapping.linkId, activeMapping.parentSelector);
    }

    // Disable Bootstrap collapse default behavior dan gunakan custom handling
    document.querySelectorAll('[data-bs-toggle="collapse"]').forEach(parentLink => {
        // Remove Bootstrap data attribute to prevent conflict
        parentLink.removeAttribute('data-bs-toggle');
        
        parentLink.addEventListener('click', function(e) {
            e.preventDefault();
            e.stopPropagation();
            
            const targetId = this.getAttribute('href');
            const targetSubmenu = document.querySelector(targetId);
            const isCurrentlyOpen = targetSubmenu.classList.contains('show');

            // Simpan posisi scroll saat ini
            const currentScrollPosition = window.pageYOffset || document.documentElement.scrollTop;

            // Tutup semua submenu yang sedang terbuka
            document.querySelectorAll('.collapse.show').forEach(openSubmenu => {
                const openParent = document.querySelector(`[href="#${openSubmenu.id}"]`);
                if (openParent) {
                    openParent.classList.remove('active');
                    openParent.classList.add('collapsed');
                }
                openSubmenu.classList.remove('show');
            });

            // Jika submenu yang diklik tidak sedang terbuka, buka sekarang
            if (!isCurrentlyOpen) {
                this.classList.add('active');
                this.classList.remove('collapsed');
                targetSubmenu.classList.add('show');
            }
            
            // Kembalikan posisi scroll ke posisi semula
            setTimeout(() => {
                window.scrollTo(0, currentScrollPosition);
            }, 10);
        });
    });
    
    // Sidebar toggle functionality removed - sidebar is now always visible
});