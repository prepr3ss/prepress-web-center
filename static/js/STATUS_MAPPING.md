# Status Badge System - Simplified Workflow

## Overview
Sistem badge status yang disederhanakan untuk mencerminkan alur kerja yang sebenarnya dalam proses Plate Adjustment.

## Status Workflow

### 1. Menunggu Adjustment
- **Status Code**: `menunggu_adjustment`
- **Badge Class**: `badge-menunggu`
- **Color**: Orange gradient
- **Description**: PIC Press sudah request form plate adjustment
- **Action**: PIC Mounting dapat klik "Mulai Adjustment"

### 2. Proses Adjustment  
- **Status Code**: `proses_adjustment`
- **Badge Class**: `badge-proses`
- **Color**: Purple gradient
- **Description**: PIC Mounting sedang melakukan proses adjustment
- **Action**: PIC Mounting dapat klik "Selesai Adjustment"

### 3. Menunggu Plate
- **Status Code**: `proses_ctp` (internal code untuk compatibility)
- **Badge Class**: `badge-menunggu-plate`
- **Color**: Light blue gradient
- **Description**: Adjustment selesai, menunggu PIC CTP untuk buat plate
- **Action**: PIC CTP dapat klik "Mulai Plate"

### 4. Proses Plate
- **Status Code**: `proses_plate`
- **Badge Class**: `badge-proses-plate`
- **Color**: Blue gradient
- **Description**: PIC CTP sedang membuat plate
- **Action**: PIC CTP dapat klik "Selesai Plate"

### 5. Plate Sedang Diantar
- **Status Code**: `antar_plate`
- **Badge Class**: `badge-antar`
- **Color**: Purple gradient
- **Description**: Plate selesai dibuat, sedang diantar ke mesin
- **Action**: PIC CTP dapat klik "Plate Sampai"

### 6. Selesai
- **Status Code**: `selesai`
- **Badge Class**: `badge-selesai`
- **Color**: Green gradient
- **Description**: Plate sudah sampai di mesin, proses selesai
- **Action**: Tidak ada action, proses complete

## Technical Implementation

### CSS Classes
```css
.badge-menunggu         /* Orange gradient */
.badge-proses           /* Purple gradient */
.badge-menunggu-plate   /* Light blue gradient */
.badge-proses-plate     /* Blue gradient */
.badge-antar            /* Purple gradient */
.badge-selesai          /* Green gradient */
```

### JavaScript Usage
```javascript
// Get badge HTML
const badgeHtml = window.BadgeSystem.getBadgeClass('proses_ctp');
// Returns: 'badge-menunggu-plate'

// Create badge element
const badge = window.BadgeSystem.createBadge('proses_plate', 'md');
// Creates: <span class="badge status-badge badge-proses-plate">Proses Plate</span>
```

### Template Usage
```html
<span class="badge status-badge" data-status="{{ status }}">
    {{ status_label }}
</span>
```

## Color Scheme
- **Orange**: Waiting states (waiting for action)
- **Purple**: Active processing states
- **Blue**: CTP-related states
- **Green**: Completed state

## Benefits
1. **Clear Workflow**: Each status clearly represents the actual business process
2. **User-Friendly**: Labels are descriptive and easy to understand
3. **Visual Hierarchy**: Colors indicate priority and stage in process
4. **Consistent**: Same system across all templates
5. **Maintainable**: Centralized configuration in one place
