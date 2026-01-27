# Implementation Guide for Sidebar Reorganization

## 1. templates/_sidebar.html Changes

### Replace lines 96-209 with:
```html
<!-- Prepress Production Menu - Only show if user can access CTP, Mounting, or Design -->
{% if current_user.can_access_ctp() or current_user.can_access_mounting() or current_user.can_access_design() %}
<a href="#prepressSubmenu" data-bs-toggle="collapse" aria-expanded="false" 
   class="list-group-item list-group-item-action prepress-submenu-parent collapsed" 
   style="display: flex; align-items: center; justify-content: space-between;">
    <div style="display: flex; align-items: center;">
        <i class="fas fa-layer-group me-2"></i>
        <span>Prepress Production</span>
    </div>
    <i class="fas fa-chevron-right"></i>
</a>
<div class="collapse" id="prepressSubmenu">
    
    <!-- CTP Production Submenu - Only show if user can access CTP -->
    {% if current_user.can_access_ctp() %}
    <a href="#ctpSubmenu" data-bs-toggle="collapse" aria-expanded="false" 
       class="list-group-item list-group-item-action ctp-submenu-parent collapsed ps-4" 
       style="display: flex; align-items: center; justify-content: space-between;">
        <div style="display: flex; align-items: center;">
            <i class="fas fa-print me-2"></i>
            <span>CTP Production</span>
        </div>
        <i class="fas fa-chevron-right"></i>
    </a>
    <div class="collapse" id="ctpSubmenu">
        <a href="/impact/dashboard-ctp" class="list-group-item list-group-item-action ps-5" id="dashboardKpiCtpLink">
            <i class="fas fa-chart-pie me-2"></i>Dashboard
        </a>
        <a href="/impact/tabel-kpi-ctp" class="list-group-item list-group-item-action ps-5" id="inputKpiCtpLink">
            <i class="fas fa-table me-2"></i>KPI CTP
        </a>
        <a href="/impact/ctp-data-adjustment" class="list-group-item list-group-item-action ps-5" id="ctpDataAdjustmentLink">
            <i class="fas fa-layer-group me-2"></i>Adjustment Press
        </a>
        <a href="/impact/ctp-data-bon" class="list-group-item list-group-item-action ps-5" id="ctpDataBonLink">
            <i class="fas fa-layer-group me-2"></i>Bon Press
        </a>
        <a href="/impact/stock-opname-ctp" class="list-group-item list-group-item-action ps-5" id="stockOpnameCtpLink">
            <i class="fas fa-boxes me-2"></i>Stock Opname
        </a>
        <a href="/impact/chemical-bon-ctp" class="list-group-item list-group-item-action ps-5" id="chemicalBonCtpLink">
            <i class="fa-solid fa-flask me-2"></i>Bon Chemical CTP
        </a>
        <a href="/impact/kartu-stock-ctp" class="list-group-item list-group-item-action ps-5" id="kartuStockCtpLink">
            <i class="fa-solid fa-cart-flatbed me-2"></i>Kartu Stock CTP
        </a>            
    </div>
    {% endif %}

    <!-- Mounting Production Submenu - Only show if user can access Mounting -->
    {% if current_user.can_access_mounting() %}
    <a href="#mountingSubmenu" data-bs-toggle="collapse" aria-expanded="false"
       class="list-group-item list-group-item-action mounting-submenu-parent collapsed ps-4"
       style="display: flex; align-items: center; justify-content: space-between;">
        <div style="display: flex; align-items: center;">
            <i class="fas fa-bezier-curve me-2"></i>
            <span>Mounting Production</span>
        </div>
        <i class="fas fa-chevron-right"></i>
    </a>
    <div class="collapse" id="mountingSubmenu">
        <a href="/impact/dashboard-mounting" class="list-group-item list-group-item-action ps-5" id="dashboardMountingLink">
            <i class="fas fa-chart-pie me-2"></i>Dashboard
        </a>
        <a href="/impact/curve-data-adjustment" class="list-group-item list-group-item-action ps-5" id="curveDataAdjustmentLink">
            <i class="fas fa-layer-group me-2"></i>Adjustment Curve
        </a>
        <a href="/impact/mounting-data-adjustment" class="list-group-item list-group-item-action ps-5" id="mountingDataAdjustmentLink">
            <i class="fas fa-layer-group me-2"></i>Adjustment Press
        </a>
    </div>
    {% endif %}

    <!-- Design Production Submenu - Only show if user can access Design -->
    {% if current_user.can_access_design() %}
    <a href="#designSubmenu" data-bs-toggle="collapse" aria-expanded="false"
       class="list-group-item list-group-item-action design-submenu-parent collapsed ps-4"
       style="display: flex; align-items: center; justify-content: space-between;">
        <div style="display: flex; align-items: center;">
            <i class="fas fa-bezier-curve me-2"></i>
            <span>Design Production</span>
        </div>
        <i class="fas fa-chevron-right"></i>
    </a>
    <div class="collapse" id="designSubmenu">
        <a href="/impact/design-data-adjustment" class="list-group-item list-group-item-action ps-5" id="designDataAdjustmentLink">
            <i class="fas fa-layer-group me-2"></i>Adjustment Press
        </a>
    </div>
    {% endif %}

</div>
{% endif %}
```

## 2. static/js/sidebar_handler.js Changes

### Update the urlMap object (lines 5-27):
```javascript
const urlMap = {
    '/impact/': { linkId: 'dashboardUtama' },
    '/impact/dashboard-ctp': { linkId: 'dashboardKpiCtpLink', parentSelector: '.ctp-submenu-parent', grandParentSelector: '.prepress-submenu-parent' },
    '/impact/tabel-kpi-ctp': { linkId: 'inputKpiCtpLink', parentSelector: '.ctp-submenu-parent', grandParentSelector: '.prepress-submenu-parent' },
    '/impact/input-kpi-ctp': { linkId: 'formKpiCtpLink', parentSelector: '.ctp-submenu-parent', grandParentSelector: '.prepress-submenu-parent' },
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
    '/impact/curve-data-adjustment': { linkId: 'curveDataAdjustmentLink', parentSelector: '.mounting-submenu-parent', grandParentSelector: '.prepress-submenu-parent' }
};
```

### Update the setActive function (lines 30-47):
```javascript
function setActive(linkId, parentSelector, grandParentSelector) {
    document.querySelectorAll('.list-group-item').forEach(el => el.classList.remove('active'));
    const activeLink = document.getElementById(linkId);
    const parentLink = document.querySelector(parentSelector);
    const grandParentLink = grandParentSelector ? document.querySelector(grandParentSelector) : null;
    
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
}
```

### Update the setActive call (line 52):
```javascript
setActive(activeMapping.linkId, activeMapping.parentSelector, activeMapping.grandParentSelector);
```

## 3. static/js/sidebar_notification.js Changes

### Add Prepress Production notification logic (after line 63):
```javascript
// Prepress Production Notifications - Aggregate from all submenus
const prepressHasNotifications = ctpAdjustmentActive || ctpBonActive || mountingAdjustmentActive || curveAdjustmentActive || designAdjustmentActive;
this.updateParentNotification('prepressSubmenu', prepressHasNotifications);
```

### Update CTP Production parent notification (line 32):
```javascript
// Update Parent Menu CTP
// Gabungkan status aktif dari kedua submenu
this.updateParentNotification('ctpSubmenu', ctpAdjustmentActive || ctpBonActive);
```

## Summary of Changes
1. **_sidebar.html**: Group CTP, Mounting, and Design under Prepress Production
2. **sidebar_handler.js**: Handle nested menu activation with grandParent support
3. **sidebar_notification.js**: Add notification aggregation for Prepress Production

All existing functionality is preserved, only the UI structure is changed.