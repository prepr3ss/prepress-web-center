document.addEventListener('DOMContentLoaded', function () {
    const currentPath = window.location.pathname;
    
    // DEBUG: Log current path with detailed info
    console.log('=== SIDEBAR DEBUG ===');
    console.log('Current Path:', currentPath);
    console.log('Path Length:', currentPath.length);
    console.log('Path Bytes:', [...currentPath].map(c => c.charCodeAt(0)).join(','));
    console.log('Has Trailing Slash:', currentPath.endsWith('/'));
    console.log('Has Query String:', window.location.search);
    console.log('Full URL:', window.location.href);

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
        '/impact/mounting-work-order-incoming': {linkId: 'mountingWorkOrderIncomingLink', parentSelector: '.mounting-submenu-parent', grandParentSelector: '.prepress-submenu-parent'},
        '/impact/rnd-webcenter/': {linkId: 'rndWebcenterLink', parentSelector: '.rnd-submenu-parent', grandParentSelector: '.prepress-submenu-parent'}
    };
    
    // Fungsi untuk mengaktifkan tautan dan parent submenu berdasarkan URL
    function setActive(linkId, parentSelector, grandParentSelector, greatGrandParentSelector) {
        console.log('\n=== setActive() EXECUTION ===');
        console.log('Input - linkId:', linkId);
        console.log('Input - parentSelector:', parentSelector);
        
        document.querySelectorAll('.list-group-item').forEach(el => {
            if (el.classList.contains('active')) {
                console.log('Removing .active from:', el.id);
                el.classList.remove('active');
            }
        });
        
        const activeLink = document.getElementById(linkId);
        const parentLink = parentSelector ? document.querySelector(parentSelector) : null;
        const grandParentLink = grandParentSelector ? document.querySelector(grandParentSelector) : null;
        const greatGrandParentLink = greatGrandParentSelector ? document.querySelector(greatGrandParentSelector) : null;
        
        console.log('Active Link:', activeLink ? '✅ FOUND' : '❌ NOT FOUND', activeLink?.id);
        console.log('Parent Link:', parentLink ? '✅ FOUND' : '❌ NOT FOUND', parentLink?.id);
        console.log('GrandParent Link:', grandParentLink ? '✅ FOUND' : '❌ NOT FOUND', grandParentLink?.id);
        
        if (activeLink) {
            console.log('→ Adding .active to:', activeLink.id);
            activeLink.classList.add('active');
            console.log('  Classes after add:', activeLink.className);
        }
        if (parentLink) {
            console.log('→ Activating parent:', parentLink.id);
            parentLink.classList.add('active');
            parentLink.classList.remove('collapsed');
            const submenuId = parentLink.getAttribute('href').substring(1);
            const submenu = document.getElementById(submenuId);
            if (submenu) {
                console.log('  Opening submenu:', submenuId);
                submenu.classList.add('show');
                console.log('  Submenu display:', window.getComputedStyle(submenu).display);
            }
        }
        if (grandParentLink) {
            console.log('→ Activating grand-parent:', grandParentLink.id);
            grandParentLink.classList.add('active');
            grandParentLink.classList.remove('collapsed');
            const grandSubmenuId = grandParentLink.getAttribute('href').substring(1);
            const grandSubmenu = document.getElementById(grandSubmenuId);
            if (grandSubmenu) {
                console.log('  Opening grand-submenu:', grandSubmenuId);
                grandSubmenu.classList.add('show');
            }
        }
        if (greatGrandParentLink) {
            console.log('→ Activating great-grand-parent:', greatGrandParentLink.id);
            greatGrandParentLink.classList.add('active');
            greatGrandParentLink.classList.remove('collapsed');
            const greatGrandSubmenuId = greatGrandParentLink.getAttribute('href').substring(1);
            const greatGrandSubmenu = document.getElementById(greatGrandSubmenuId);
            if (greatGrandSubmenu) {
                console.log('  Opening great-grand-submenu:', greatGrandSubmenuId);
                greatGrandSubmenu.classList.add('show');
            }
        }
        console.log('=========================\n');
    }
    
    // Check if current path matches cloudsphere job detail pattern with ID
    let activeMapping = urlMap[currentPath];
    console.log('Step 1 - Direct URL Map Lookup:', activeMapping ? 'FOUND' : 'NOT FOUND');
    
    if (!activeMapping && currentPath.match(/^\/impact\/cloudsphere\/job\/\d+$/)) {
        // Use cloudsphere mapping for job detail pages with any ID
        activeMapping = {linkId: 'cloudsphereLink', parentSelector: '.rnd-submenu-parent', grandParentSelector: '.prepress-submenu-parent'};
        console.log('Step 2 - Cloudsphere Job Detail Pattern:', 'MATCHED');
    }

    if (!activeMapping && currentPath.match(/^\/impact\/edit-kpi-ctp\/\d+$/)) {
        // Use cloudsphere mapping for job detail pages with any ID
        activeMapping = {linkId: 'inputKpiCtpLink', parentSelector: '.ctp-submenu-parent', grandParentSelector: '.prepress-submenu-parent'};
        console.log('Step 2 - Edit KPI CTP Pattern:', 'MATCHED');
    }

    if (!activeMapping && currentPath.match(/^\/impact\/rnd-cloudsphere\/job\/\d+$/)) {
        // Use cloudsphere mapping for job detail pages with any ID
        activeMapping = {linkId: 'rndCloudsphereLink', parentSelector: '.rnd-submenu-parent', grandParentSelector: '.prepress-submenu-parent'};
        console.log('Step 2 - RND Cloudsphere Job Pattern:', 'MATCHED');
    }
    
    // DEBUG: Check 5W1H detail pattern
    if (!activeMapping && currentPath.match(/^\/impact\/tools\/5w1h\/\d+$/)) {
        // Use tools5w1h mapping for detail pages with any ID
        activeMapping = {linkId: 'tools5w1hLink', parentSelector: '.tools-submenu-parent'};
        console.log('✅ Step 2 - 5W1H Detail Pattern (/impact/tools/5w1h/{id}):', 'MATCHED');
    } else if (activeMapping) {
        console.log('⚠️ Step 2 - 5W1H Detail Pattern: SKIPPED (activeMapping sudah ada)');
    } else {
        console.log('❌ Step 2 - 5W1H Detail Pattern (/impact/tools/5w1h/{id}):', 'NO MATCH', 'Testing:', currentPath.match(/^\/impact\/tools\/5w1h\/\d+$/));
    }
    
    // DEBUG: Check 5W1H edit pattern
    if (!activeMapping && currentPath.match(/^\/impact\/tools\/5w1h\/\d+\/edit$/)) {
        // Use tools5w1h mapping for edit pages with any ID
        activeMapping = {linkId: 'tools5w1hLink', parentSelector: '.tools-submenu-parent'};
        console.log('✅ Step 3 - 5W1H Edit Pattern (/impact/tools/5w1h/{id}/edit):', 'MATCHED');
    } else if (activeMapping) {
        console.log('⚠️ Step 3 - 5W1H Edit Pattern: SKIPPED (activeMapping sudah ada)');
    } else {
        console.log('❌ Step 3 - 5W1H Edit Pattern (/impact/tools/5w1h/{id}/edit):', 'NO MATCH', 'Testing:', currentPath.match(/^\/impact\/tools\/5w1h\/\d+\/edit$/));
    }
    
    // DEBUG: Check for 5W1H dashboard and new form
    if (!activeMapping && (currentPath === '/impact/tools/5w1h' || currentPath === '/impact/tools/5w1h/new')) {
        activeMapping = {linkId: 'tools5w1hLink', parentSelector: '.tools-submenu-parent'};
        console.log('✅ Step 4 - 5W1H Dashboard/New Form:', 'MATCHED', 'Path:', currentPath);
    } else if (activeMapping) {
        console.log('⚠️ Step 4 - 5W1H Dashboard/New Form: SKIPPED (activeMapping sudah ada)');
    } else {
        console.log('❌ Step 4 - 5W1H Dashboard/New Form (/impact/tools/5w1h atau /impact/tools/5w1h/new):', 'NO MATCH', 'Path:', currentPath);
        console.log('  → Exact check /impact/tools/5w1h:', currentPath === '/impact/tools/5w1h');
        console.log('  → Exact check /impact/tools/5w1h/new:', currentPath === '/impact/tools/5w1h/new');
    }
    
    // Final Result
    console.log('Final activeMapping:', activeMapping);
    console.log('==================');
    
    // Panggil fungsi setActive untuk mengatur status awal
    if (activeMapping) {
        console.log('Calling setActive with:', activeMapping.linkId);
        setActive(activeMapping.linkId, activeMapping.parentSelector, activeMapping.grandParentSelector, activeMapping.greatGrandParentSelector);
        
        // DEBUG: Comprehensive CSS Inspection
        console.log('\n=== CSS DEBUG ===');
        const activeLink = document.getElementById(activeMapping.linkId);
        if (activeLink) {
            console.log('✅ Active Link Found:', activeLink);
            console.log('Active Link Classes:', activeLink.className);
            console.log('Has .active class:', activeLink.classList.contains('active'));
            
            // Get computed styles
            const computedStyle = window.getComputedStyle(activeLink);
            console.log('Computed Background Color:', computedStyle.backgroundColor);
            console.log('Computed Text Color:', computedStyle.color);
            console.log('Computed Display:', computedStyle.display);
            console.log('Computed Opacity:', computedStyle.opacity);
            
            // Check CSS Variables
            console.log('\n=== CSS VARIABLES CHECK ===');
            const rootStyles = window.getComputedStyle(document.documentElement);
            console.log('--sidebar-active-bg:', rootStyles.getPropertyValue('--sidebar-active-bg').trim());
            console.log('--sidebar-active-text:', rootStyles.getPropertyValue('--sidebar-active-text').trim());
            console.log('--sidebar-bg:', rootStyles.getPropertyValue('--sidebar-bg').trim());
            
            // Check parent sidebar-wrapper styles
            const sidebarWrapper = document.getElementById('sidebar-wrapper');
            if (sidebarWrapper) {
                const sidebarStyle = window.getComputedStyle(sidebarWrapper);
                console.log('\nSidebar wrapper --sidebar-active-bg:', sidebarStyle.getPropertyValue('--sidebar-active-bg').trim());
                console.log('Sidebar wrapper --sidebar-active-text:', sidebarStyle.getPropertyValue('--sidebar-active-text').trim());
            }
            
            // Check for inline styles that might override
            console.log('\nInline style attribute:', activeLink.getAttribute('style'));
            
            // Check all style sheets - MORE DETAILED
            console.log('\n=== Stylesheet Analysis ===');
            const styleSheets = document.styleSheets;
            console.log('Total Stylesheets:', styleSheets.length);
            
            let foundRules = [];
            for (let i = 0; i < styleSheets.length; i++) {
                try {
                    const cssRules = styleSheets[i].cssRules || styleSheets[i].rules;
                    for (let j = 0; j < cssRules.length; j++) {
                        const rule = cssRules[j];
                        if (rule.selectorText && (rule.selectorText.includes('active') || rule.selectorText.includes('sidebar-item'))) {
                            // Check if this rule applies to our element
                            const matches = activeLink.matches(rule.selectorText);
                            foundRules.push({
                                selector: rule.selectorText,
                                style: rule.style.cssText,
                                matches: matches,
                                specificity: calculateSpecificity(rule.selectorText)
                            });
                            
                            if (matches) {
                                console.log(`✅ MATCHES - Rule ${i}-${j}:`, rule.selectorText);
                                console.log('   Style:', rule.style.cssText);
                                console.log('   Specificity:', calculateSpecificity(rule.selectorText));
                            }
                        }
                    }
                } catch (e) {
                    console.log('Cannot access stylesheet', i, '- CORS or external');
                }
            }
            
            console.log('\n📋 All Rules Found (Sorted by Specificity):');
            foundRules.sort((a, b) => b.specificity - a.specificity);
            foundRules.forEach(rule => {
                console.log(`${rule.matches ? '✅' : '❌'} [${rule.specificity}] ${rule.selector}`);
                console.log('   ', rule.style.substring(0, 80) + '...');
            });
            
            // DEBUG: Check all rules that might override background-color
            console.log('\n=== ALL BACKGROUND COLOR RULES ===');
            for (let i = 0; i < styleSheets.length; i++) {
                try {
                    const cssRules = styleSheets[i].cssRules || styleSheets[i].rules;
                    for (let j = 0; j < cssRules.length; j++) {
                        const rule = cssRules[j];
                        if (rule.selectorText) {
                            // Check if rule has background or background-color property
                            if (rule.style.backgroundColor || rule.style.background || rule.style.cssText.includes('background')) {
                                const matches = activeLink.matches(rule.selectorText);
                                if (matches || rule.selectorText.includes('list-group-item') || rule.selectorText.includes('active')) {
                                    console.log(`${matches ? '✅ MATCH' : '❌'} Rule ${i}-${j}: ${rule.selectorText}`);
                                    console.log('   Background:', rule.style.backgroundColor || rule.style.background || 'none specified');
                                    console.log('   Full CSS:', rule.style.cssText.substring(0, 100));
                                }
                            }
                        }
                    }
                } catch (e) {
                    // CORS protected
                }
            }
            
            // DEBUG: Check if media query is active
            console.log('\n=== MEDIA QUERY DEBUG ===');
            console.log('Window width:', window.innerWidth);
            console.log('Window height:', window.innerHeight);
            console.log('Pointer: coarse (touch)?', window.matchMedia('(hover: none) and (pointer: coarse)').matches);
            console.log('Max-width 767.98px?', window.matchMedia('(max-width: 767.98px)').matches);
            console.log('Max-width 575.98px?', window.matchMedia('(max-width: 575.98px)').matches);
            
            // Check parent elements
            console.log('\n=== Parent Elements Check ===');
            const parentLink = activeMapping.parentSelector ? document.querySelector(activeMapping.parentSelector) : null;
            if (parentLink) {
                console.log('Parent Link Classes:', parentLink.className);
                console.log('Parent Has .active:', parentLink.classList.contains('active'));
                console.log('Parent Has .collapsed:', parentLink.classList.contains('collapsed'));
                const parentSubmenuId = parentLink.getAttribute('href').substring(1);
                const parentSubmenu = document.getElementById(parentSubmenuId);
                if (parentSubmenu) {
                    console.log('Parent Submenu ID:', parentSubmenuId);
                    console.log('Parent Submenu Has .show:', parentSubmenu.classList.contains('show'));
                    console.log('Parent Submenu Display:', window.getComputedStyle(parentSubmenu).display);
                }
            }
        } else {
            console.log('❌ Active Link NOT Found by ID:', activeMapping.linkId);
        }
        console.log('==================\n');
    } else {
        console.log('⚠️ NO ACTIVE MAPPING FOUND - Sidebar will not highlight');
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
        console.log('🔧 Setting up collapse handler for:', parentLink.id, 'href:', parentLink.getAttribute('href'));
        parentLink.removeAttribute('data-bs-toggle');

        parentLink.addEventListener('click', function (e) {
            e.preventDefault();
            e.stopPropagation();
            
            console.log('\n=== COLLAPSE CLICK ===');
            console.log('Clicked element ID:', this.id);
            console.log('Target submenu:', this.getAttribute('href'));

            const targetId = this.getAttribute('href');
            const targetSubmenu = document.querySelector(targetId);
            if (!targetSubmenu) {
                console.log('❌ Target submenu NOT found!');
                return;
            }

            const isCurrentlyOpen = targetSubmenu.classList.contains('show');
            console.log('Submenu currently open:', isCurrentlyOpen);

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
            
            console.log('Parent level - L1:', isLevel1, 'L2:', isLevel2, 'L3:', isLevel3);

            const chevron = this.querySelector('.sidebar-chevron');

            if (isCurrentlyOpen) {
                console.log('→ Closing submenu');
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
                    openParent.classList.contains('settings-submenu-parent');

                const openIsLevel2 = openParent.classList.contains('ctp-submenu-parent') ||
                    openParent.classList.contains('mounting-submenu-parent') ||
                    openParent.classList.contains('design-submenu-parent') ||
                    openParent.classList.contains('rnd-submenu-parent');

                const openIsLevel3 = openParent.classList.contains('log-ctp-submenu-parent');

                const sameLevel = (isLevel1 && openIsLevel1) || (isLevel2 && openIsLevel2) || (isLevel3 && openIsLevel3);

                if (sameLevel && openSubmenu.id !== targetId.substring(1)) {
                    console.log('→ Closing sibling submenu:', openSubmenu.id);
                    openParent.classList.add('collapsed');
                    openParent.classList.remove('active');
                    openSubmenu.classList.remove('show');
                    const openChevron = openParent.querySelector('.sidebar-chevron');
                    if (openChevron) openChevron.classList.remove('rotated');
                }
            });

            console.log('→ Opening submenu');
            this.classList.remove('collapsed');
            this.classList.add('active');
            targetSubmenu.classList.add('show');
            if (chevron) chevron.classList.add('rotated');
            console.log('====================\n');
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
            
            // Only close if:
            // 1. NOT a collapse toggle button (data-bs-toggle attribute)
            // 2. NOT already has collapsed class
            // 3. NOT a parent/grand-parent item (submenu-parent class)
            if (!this.hasAttribute('data-bs-toggle') && 
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
