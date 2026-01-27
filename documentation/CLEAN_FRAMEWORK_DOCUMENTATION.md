# 🎨 PREPRESS IMPACT - CLEAN DESIGN FRAMEWORK 
## "PATENKAN" FRAMEWORK UI YANG SANGAT DISUKAI!

### 📋 DAFTAR ISI
1. [Pengenalan](#pengenalan)
2. [Instalasi & Setup](#instalasi--setup)
3. [Color Schemes](#color-schemes)
4. [Komponen Framework](#komponen-framework)
5. [Template Implementasi](#template-implementasi)
6. [Contoh Penggunaan](#contoh-penggunaan)
7. [Kustomisasi](#kustomisasi)

---

## 🚀 PENGENALAN

Framework UI ini dibuat berdasarkan **CTP Data Adjustment** yang sangat disukai! Framework ini menyediakan:

✅ **Design System yang Konsisten**  
✅ **5 Color Schemes Siap Pakai**  
✅ **Template Base yang Fleksibel**  
✅ **Komponen UI Modern & Clean**  
✅ **Responsive Design**  
✅ **Easy to Implement**  

### 🎯 DESIGN PHILOSOPHY
- **Clean & Professional** - Tidak "sakit mata"
- **Modern Gradients** - Menggunakan CSS gradients yang indah
- **Consistent Spacing** - Menggunakan CSS variables
- **Smooth Animations** - Transisi yang halus
- **User Friendly** - Interface yang mudah digunakan

---

## 🔧 INSTALASI & SETUP

### 1. File Framework
Pastikan file-file ini ada di project:
```
static/css/clean-framework.css          # Main framework CSS
templates/clean_template_base.html      # Base template
```

### 2. Include Framework
Tambahkan di template HTML:
```html
<link href="{{ url_for('static', filename='css/clean-framework.css') }}" rel="stylesheet">
```

### 3. Struktur HTML Dasar
```html
<div class="theme-ctp"> <!-- Color scheme -->
    <div class="clean-page-header">
        <h2 class="clean-page-title">Page Title</h2>
    </div>
    <!-- Content here -->
</div>
```

---

## 🎨 COLOR SCHEMES

Framework menyediakan 5 color schemes siap pakai:

### 1. **CTP Theme** (Default - Orange/Blue)
```css
.theme-ctp
```
- **Primary**: Orange gradient (#ff9500 → #ff6b00)
- **Secondary**: Blue gradient (#00b4db → #0083b0)
- **Usage**: CTP operations, Production data

### 2. **Mounting Theme** (Purple/Green)
```css
.theme-mounting
```
- **Primary**: Purple gradient (#667eea → #764ba2)
- **Secondary**: Green gradient (#56ab2f → #a8e6cf)
- **Usage**: Mounting operations, Setup data

### 3. **Production Theme** (Red/Gold)
```css
.theme-production
```
- **Primary**: Red gradient (#e74c3c → #c0392b)
- **Secondary**: Gold gradient (#f39c12 → #e67e22)
- **Usage**: Production monitoring, Critical alerts

### 4. **Quality Control Theme** (Teal/Navy)
```css
.theme-qc
```
- **Primary**: Teal gradient (#1abc9c → #16a085)
- **Secondary**: Navy gradient (#34495e → #2c3e50)
- **Usage**: Quality control, Inspection data

### 5. **Maintenance Theme** (Gray/Yellow)
```css
.theme-maintenance
```
- **Primary**: Gray gradient (#95a5a6 → #7f8c8d)
- **Secondary**: Yellow gradient (#f1c40f → #f39c12)
- **Usage**: Maintenance schedules, Service logs

---

## 🧩 KOMPONEN FRAMEWORK

### 1. **Cards**
```html
<!-- Summary Card -->
<div class="card clean-summary-card">
    <div class="card-body text-center">
        <div class="clean-summary-icon clean-icon-primary">
            <i class="fas fa-chart-bar text-white"></i>
        </div>
        <h3>150</h3>
        <div class="clean-info-label">Total Items</div>
    </div>
</div>

<!-- Data Card -->
<div class="card clean-data-card">
    <div class="card-header clean-card-header">
        <h5>Data Header</h5>
    </div>
    <div class="card-body">Content</div>
</div>
```

### 2. **Buttons**
```html
<button class="btn clean-btn clean-btn-primary">Primary</button>
<button class="btn clean-btn clean-btn-secondary">Secondary</button>
<button class="btn clean-btn clean-btn-outline">Outline</button>
<button class="btn clean-btn clean-btn-accent">Accent</button>
```

### 3. **Forms**
```html
<label class="form-label clean-form-label">Label</label>
<input class="form-control clean-form-control" type="text">
<select class="form-select clean-form-control">
    <option>Option</option>
</select>
```

### 4. **Status Badges**
```html
<span class="clean-status-badge clean-badge-primary">Active</span>
<span class="clean-status-badge clean-badge-secondary">Pending</span>
<span class="clean-status-badge clean-badge-success">Complete</span>
```

### 5. **Page Header**
```html
<div class="clean-page-header">
    <div class="container-fluid">
        <div class="row align-items-center">
            <div class="col-md-8">
                <h2 class="clean-page-title">
                    <i class="fas fa-dashboard"></i> Page Title
                </h2>
                <p class="clean-page-subtitle">Description</p>
            </div>
            <div class="col-md-4 clean-page-meta">
                <div class="small">
                    <i class="fas fa-clock"></i> Now<br>
                    <i class="fas fa-user"></i> Admin
                </div>
            </div>
        </div>
    </div>
</div>
```

---

## 📄 TEMPLATE IMPLEMENTASI

### Base Template Usage
```python
# Flask Route Example
@app.route('/my-module')
def my_module():
    return render_template('clean_template_base.html',
        # Basic Info
        page_title='My Module',
        page_subtitle='Module description',
        color_scheme='theme-ctp',
        
        # Header
        header_icon='fas fa-cogs',
        current_time='2024-01-01 10:00',
        current_user='Admin',
        
        # Summary Cards
        summary_cards=[
            {
                'count': 150,
                'label': 'Total Items',
                'icon': 'fas fa-items',
                'icon_class': 'clean-icon-primary'
            },
            {
                'count': 45,
                'label': 'Active',
                'icon': 'fas fa-check',
                'icon_class': 'clean-icon-success'
            }
        ],
        
        # Filters
        show_filters=True,
        filter_status=[
            {'value': 'active', 'label': 'Active'},
            {'value': 'pending', 'label': 'Pending'}
        ],
        show_date_filter=True,
        show_search=True,
        
        # Table
        table_title='Data Table',
        table_columns=[
            {'label': 'ID'},
            {'label': 'Name'},
            {'label': 'Status'}
        ],
        show_actions=True,
        
        # API
        api_endpoint='/api/my-module-data',
        status_field='status',
        target_status='active',
        
        # Actions
        action_buttons=[
            {
                'text': 'Add New',
                'icon': 'fas fa-plus',
                'class': 'clean-btn-primary',
                'onclick': 'addNew()'
            }
        ]
    )
```

---

## 💡 CONTOH PENGGUNAAN

### 1. **Inventory Management Module**
```python
@app.route('/inventory')
def inventory():
    return render_template('clean_template_base.html',
        page_title='Inventory Management',
        page_subtitle='Kelola stok dan inventory',
        color_scheme='theme-qc',  # Teal theme untuk inventory
        
        summary_cards=[
            {'count': 1250, 'label': 'Total Items', 'icon': 'fas fa-boxes', 'icon_class': 'clean-icon-primary'},
            {'count': 45, 'label': 'Low Stock', 'icon': 'fas fa-exclamation-triangle', 'icon_class': 'clean-icon-accent'},
            {'count': 890, 'label': 'Available', 'icon': 'fas fa-check-circle', 'icon_class': 'clean-icon-success'}
        ],
        
        api_endpoint='/api/inventory-data',
        status_field='stock_status',
        module_script='inventory_handler.js'
    )
```

### 2. **Maintenance Schedule Module**
```python
@app.route('/maintenance')
def maintenance():
    return render_template('clean_template_base.html',
        page_title='Maintenance Schedule',
        page_subtitle='Jadwal perawatan mesin',
        color_scheme='theme-maintenance',  # Gray/Yellow untuk maintenance
        
        summary_cards=[
            {'count': 12, 'label': 'Scheduled', 'icon': 'fas fa-calendar', 'icon_class': 'clean-icon-primary'},
            {'count': 3, 'label': 'Overdue', 'icon': 'fas fa-exclamation', 'icon_class': 'clean-icon-accent'},
            {'count': 25, 'label': 'Completed', 'icon': 'fas fa-check', 'icon_class': 'clean-icon-success'}
        ],
        
        api_endpoint='/api/maintenance-data'
    )
```

### 3. **Production Monitoring Module**
```python
@app.route('/production')
def production():
    return render_template('clean_template_base.html',
        page_title='Production Monitoring',
        page_subtitle='Monitor produksi real-time',
        color_scheme='theme-production',  # Red/Gold untuk production
        
        summary_cards=[
            {'count': 2450, 'label': 'Units Produced', 'icon': 'fas fa-industry', 'icon_class': 'clean-icon-primary'},
            {'count': 95.5, 'label': 'Efficiency %', 'icon': 'fas fa-chart-line', 'icon_class': 'clean-icon-success'},
            {'count': 2, 'label': 'Issues', 'icon': 'fas fa-exclamation-triangle', 'icon_class': 'clean-icon-accent'}
        ],
        
        refresh_interval=5000,  # Auto refresh every 5 seconds
        api_endpoint='/api/production-data'
    )
```

---

## ⚙️ KUSTOMISASI

### 1. **Custom Color Scheme**
Buat color scheme baru di CSS:
```css
.theme-custom {
    --primary-gradient: linear-gradient(135deg, #your-color1 0%, #your-color2 100%);
    --secondary-gradient: linear-gradient(135deg, #your-color3 0%, #your-color4 100%);
    --primary-color: #your-primary;
    --secondary-color: #your-secondary;
}
```

### 2. **Custom Table Row Generator**
Override function `generateTableRow()`:
```javascript
function generateTableRow(item, index) {
    return `
        <tr>
            <td>${index + 1}</td>
            <td>${item.custom_field1}</td>
            <td>${item.custom_field2}</td>
            <td>
                <span class="clean-status-badge clean-badge-${getStatusClass(item.status)}">
                    ${item.status}
                </span>
            </td>
            <td class="text-center">
                <button class="btn clean-btn clean-btn-accent btn-sm" onclick="customAction(${item.id})">
                    <i class="fas fa-cog"></i>
                </button>
            </td>
        </tr>
    `;
}
```

### 3. **Custom Modal**
Tambahkan modal kustom:
```python
modals=[
    {
        'id': 'customModal',
        'title': 'Custom Action',
        'icon': 'fas fa-cog',
        'size': 'modal-xl',
        'header_class': 'clean-modal-header-primary',
        'content': '''
            <form id="customForm">
                <div class="row">
                    <div class="col-md-6">
                        <label class="form-label clean-form-label">Field 1</label>
                        <input type="text" class="form-control clean-form-control" name="field1">
                    </div>
                </div>
            </form>
        ''',
        'save_action': 'saveCustomData()'
    }
]
```

---

## 🚀 QUICK START CHECKLIST

### ✅ Implementasi Baru
1. Copy `clean-framework.css` ke `/static/css/`
2. Copy `clean_template_base.html` ke `/templates/`
3. Pilih color scheme yang sesuai
4. Setup Flask route dengan parameter template
5. Buat API endpoint untuk data
6. Test dan customize sesuai kebutuhan

### ✅ Migrasi dari UI Lama
1. Backup template lama
2. Ganti dengan base template
3. Sesuaikan parameter template
4. Update API endpoint jika perlu
5. Test functionality
6. Deploy!

---

## 📞 SUPPORT & MAINTENANCE

### File yang Perlu Diperhatikan:
- `static/css/clean-framework.css` - Main framework
- `templates/clean_template_base.html` - Base template
- Module-specific JS files untuk custom functionality

### Best Practices:
- Selalu gunakan CSS variables untuk konsistensi
- Test di mobile device untuk responsiveness
- Gunakan appropriate color scheme untuk setiap module
- Implement proper error handling di JavaScript
- Keep API responses consistent

---

## 🎉 FRAMEWORK SUDAH SIAP DIGUNAKAN!

Framework ini adalah hasil dari **UI CTP Data Adjustment yang sangat disukai**. Sekarang bisa diimplementasikan ke semua module dengan mudah dan konsisten!

**ENJOY YOUR CLEAN UI FRAMEWORK! 🚀**
