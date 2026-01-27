# Rencana Implementasi Work Order Incoming

## 1. Overview

Dokumen ini berisi rencana implementasi detail untuk fitur Work Order Incoming pada Mounting Production. Implementasi akan dilakukan dalam beberapa fase dengan prioritas yang jelas.

## 2. Fase Implementasi

### Fase 1: Foundation (Database & Backend)
**Estimasi Waktu:** 2-3 hari
**Prioritas:** Tinggi

#### 2.1. Database Model
- [x] Analisis kebutuhan database
- [ ] Membuat model `MountingWorkOrderIncoming` di `models_mounting.py`
- [ ] Membuat migration script untuk tabel baru
- [ ] Menjalankan migration ke database

#### 2.2. Backend API
- [ ] Membuat Flask routes untuk Work Order Incoming
- [ ] Implementasi API endpoints sesuai spesifikasi
- [ ] Validasi input data
- [ ] Error handling yang komprehensif

### Fase 2: Frontend Development
**Estimasi Waktu:** 3-4 hari
**Prioritas:** Tinggi

#### 2.3. HTML Template
- [ ] Membuat template `mounting_work_order_incoming.html`
- [ ] Implementasi struktur UI yang konsisten dengan template lain
- [ ] Membuat komponen input table yang dinamis
- [ ] Membuat modal konfirmasi

#### 2.4. JavaScript Functionality
- [ ] Membuat file `mounting_work_order_incoming.js`
- [ ] Implementasi fungsi tambah/hapus baris dinamis
- [ ] Validasi form di client-side
- [ ] Integrasi dengan API endpoints
- [ ] Fitur verifikasi jumlah baris sebelum submit

### Fase 3: Integration & Navigation
**Estimasi Waktu:** 1-2 hari
**Prioritas:** Sedang

#### 2.5. Navigation Integration
- [ ] Menambahkan menu Work Order Incoming ke sidebar
- [ ] Testing navigasi dan routing
- [ ] Memastikan konsistensi UI dengan halaman lain

#### 2.6. Data Display & Filtering
- [ ] Implementasi data table dengan pagination
- [ ] Fitur filter dan pencarian
- [ ] Sorting functionality
- [ ] Responsive design untuk mobile

### Fase 4: Enhancement & Testing
**Estimasi Waktu:** 2-3 hari
**Prioritas:** Sedang

#### 2.7. Advanced Features
- [ ] Export data to Excel/CSV
- [ ] Batch operations
- [ ] Advanced filtering
- [ ] Statistics dashboard

#### 2.8. Testing & Debugging
- [ ] Unit testing untuk backend
- [ ] Integration testing
- [ ] Cross-browser testing
- [ ] Performance optimization

## 3. Detail Implementasi

### 3.1. Database Implementation

#### 3.1.1. Model Structure
```python
# models_mounting.py
class MountingWorkOrderIncoming(db.Model):
    __tablename__ = 'mounting_work_order_incoming'
    
    id = db.Column(db.Integer, primary_key=True)
    incoming_datetime = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    wo_number = db.Column(db.String(50), nullable=False, unique=True)
    mc_number = db.Column(db.String(50), nullable=False)
    customer_name = db.Column(db.String(100), nullable=False)
    item_name = db.Column(db.String(100), nullable=False)
    print_block = db.Column(db.String(50), nullable=False)
    print_machine = db.Column(db.String(100), nullable=False)
    run_length_sheet = db.Column(db.Integer)
    sheet_size = db.Column(db.String(50))
    paper_type = db.Column(db.String(50))
    status = db.Column(db.String(20), nullable=False, default='incoming')
    processed_at = db.Column(db.DateTime)
    processed_by = db.Column(db.String(50))
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by = db.Column(db.String(50), nullable=False)
```

#### 3.1.2. Migration Script
```python
# migrations/versions/create_mounting_work_order_incoming.py
def upgrade():
    op.create_table('mounting_work_order_incoming',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('incoming_datetime', sa.DateTime(), nullable=False),
        sa.Column('wo_number', sa.String(length=50), nullable=False),
        sa.Column('mc_number', sa.String(length=50), nullable=False),
        # ... other columns
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('wo_number')
    )
    
    # Create indexes
    op.create_index('idx_wo_incoming_datetime', 'mounting_work_order_incoming', ['incoming_datetime'])
    op.create_index('idx_wo_status', 'mounting_work_order_incoming', ['status'])
```

### 3.2. Backend API Implementation

#### 3.2.1. Route Structure
```python
# mounting_work_order_incoming_routes.py
from flask import Blueprint, request, jsonify
from models_mounting import MountingWorkOrderIncoming

bp = Blueprint('mounting_work_order_incoming', __name__)

@bp.route('/mounting-work-order-incoming')
def work_order_incoming_page():
    return render_template('mounting_work_order_incoming.html')

@bp.route('/api/mounting-work-order-incoming', methods=['GET'])
def get_work_orders():
    # Implementation for GET endpoint
    pass

@bp.route('/api/mounting-work-order-incoming', methods=['POST'])
def create_work_order():
    # Implementation for POST endpoint
    pass

@bp.route('/api/mounting-work-order-incoming/batch', methods=['POST'])
def create_work_orders_batch():
    # Implementation for batch creation
    pass
```

#### 3.2.2. Service Layer
```python
# services/work_order_service.py
class WorkOrderService:
    @staticmethod
    def create_work_orders_batch(work_orders_data, created_by):
        try:
            created_work_orders = []
            failed_items = []
            
            for item in work_orders_data:
                try:
                    work_order = MountingWorkOrderIncoming(
                        wo_number=item['wo_number'],
                        mc_number=item['mc_number'],
                        customer_name=item['customer_name'],
                        # ... other fields
                        created_by=created_by
                    )
                    db.session.add(work_order)
                    created_work_orders.append(work_order)
                except Exception as e:
                    failed_items.append({
                        'item': item,
                        'error': str(e)
                    })
            
            db.session.commit()
            
            return {
                'created_count': len(created_work_orders),
                'failed_count': len(failed_items),
                'created_ids': [wo.id for wo in created_work_orders],
                'failed_items': failed_items
            }
        except Exception as e:
            db.session.rollback()
            raise e
```

### 3.3. Frontend Implementation

#### 3.3.1. HTML Structure
```html
<!-- templates/mounting_work_order_incoming.html -->
{% extends "base.html" %}

{% block title %}Work Order Incoming - Mounting Production{% endblock %}

{% block content %}
<div class="page-header">
    <!-- Header content -->
</div>

<div class="container-fluid pt-3">
    <!-- Input Section -->
    <div class="card data-card mb-4">
        <div class="card-header card-header-clean">
            <h5 class="mb-0">
                <i class="fas fa-plus-circle me-2 text-primary"></i>
                Input Work Order
            </h5>
        </div>
        <div class="card-body">
            <!-- Excel-like input table -->
            <div class="table-responsive">
                <table class="table table-bordered" id="workOrderTable">
                    <!-- Table structure -->
                </table>
            </div>
            
            <!-- Action buttons -->
            <div class="d-flex justify-content-between align-items-center mt-3">
                <div>
                    <button type="button" class="btn btn-outline-clean btn-clean" id="addRowBtn">
                        <i class="fas fa-plus me-1"></i>Tambah Baris
                    </button>
                    <button type="button" class="btn btn-outline-clean btn-clean" id="clearAllBtn">
                        <i class="fas fa-eraser me-1"></i>Hapus Semua
                    </button>
                </div>
                <div>
                    <span class="text-muted me-3" id="rowCountInfo">0 baris</span>
                    <button type="button" class="btn btn-primary-clean btn-clean" id="submitBtn" disabled>
                        <i class="fas fa-save me-1"></i>Submit All
                    </button>
                </div>
            </div>
        </div>
    </div>
    
    <!-- Data Table Section -->
    <div class="card data-card">
        <!-- Data table content -->
    </div>
</div>

<!-- Confirmation Modal -->
<div class="modal fade" id="confirmModal">
    <!-- Modal content -->
</div>
{% endblock %}
```

#### 3.3.2. JavaScript Implementation
```javascript
// static/js/mounting_work_order_incoming.js
class WorkOrderIncoming {
    constructor() {
        this.workOrderData = [];
        this.initializeEventListeners();
        this.initializeTable();
        this.loadData();
    }
    
    initializeEventListeners() {
        document.getElementById('addRowBtn').addEventListener('click', () => this.addNewRow());
        document.getElementById('clearAllBtn').addEventListener('click', () => this.clearAllRows());
        document.getElementById('submitBtn').addEventListener('click', () => this.showConfirmationModal());
        document.getElementById('confirmSubmitBtn').addEventListener('click', () => this.submitData());
    }
    
    initializeTable() {
        // Initialize with 5 empty rows
        for (let i = 0; i < 5; i++) {
            this.addNewRow();
        }
        this.updateRowCount();
    }
    
    addNewRow() {
        const rowCount = this.workOrderData.length;
        const newRow = {
            id: Date.now() + Math.random(),
            wo_number: '',
            mc_number: '',
            customer_name: '',
            item_name: '',
            print_block: '',
            print_machine: '',
            run_length_sheet: '',
            sheet_size: '',
            paper_type: ''
        };
        
        this.workOrderData.push(newRow);
        this.renderRow(newRow, rowCount + 1);
        this.updateRowCount();
    }
    
    async submitData() {
        try {
            const validation = this.validateData();
            if (!validation.isValid) {
                showToast('Error validasi: ' + validation.errors.join(', '), 'error');
                return;
            }
            
            const response = await fetch('/impact/api/mounting-work-order-incoming/batch', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    work_orders: this.workOrderData,
                    created_by: window.currentUserName
                })
            });
            
            if (response.ok) {
                const result = await response.json();
                showToast(`${result.data.created_count} work order berhasil disubmit!`, 'success');
                this.clearAllRows();
                this.loadData();
            } else {
                const error = await response.json();
                showToast('Gagal submit: ' + error.error.message, 'error');
            }
        } catch (error) {
            showToast('Terjadi kesalahan: ' + error.message, 'error');
        }
    }
    
    validateData() {
        let isValid = true;
        const errors = [];
        
        this.workOrderData.forEach((item, index) => {
            const requiredFields = ['wo_number', 'mc_number', 'customer_name', 'item_name', 'print_block', 'print_machine'];
            
            requiredFields.forEach(field => {
                if (!item[field] || item[field].trim() === '') {
                    isValid = false;
                    errors.push(`Baris ${index + 1}: ${field} tidak boleh kosong`);
                }
            });
        });
        
        return { isValid, errors };
    }
    
    showConfirmationModal() {
        const validation = this.validateData();
        
        if (!validation.isValid) {
            showToast('Error validasi: ' + validation.errors.join(', '), 'error');
            return;
        }
        
        const count = this.workOrderData.length;
        document.getElementById('confirmMessage').textContent = `Terdapat ${count} work order yang akan disubmit. Lanjutkan?`;
        
        const modal = new bootstrap.Modal(document.getElementById('confirmModal'));
        modal.show();
    }
    
    updateRowCount() {
        const count = this.workOrderData.length;
        document.getElementById('rowCountInfo').textContent = `${count} baris`;
        document.getElementById('submitBtn').disabled = count === 0;
    }
    
    // Other methods...
}

// Initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    new WorkOrderIncoming();
});
```

### 3.4. Navigation Integration

#### 3.4.1. Sidebar Update
```html
<!-- templates/_sidebar.html -->
<!-- Inside Mounting submenu -->
<li class="nav-item">
    <a href="/impact/mounting-work-order-incoming" class="nav-link">
        <i class="fas fa-file-import nav-icon"></i>
        <p>Work Order Incoming</p>
    </a>
</li>
```

## 4. Testing Strategy

### 4.1. Unit Testing
```python
# tests/test_work_order_service.py
import pytest
from services.work_order_service import WorkOrderService
from models_mounting import MountingWorkOrderIncoming

def test_create_work_orders_batch_success():
    work_orders_data = [
        {
            'wo_number': 'WO001',
            'mc_number': 'MC001',
            'customer_name': 'Test Customer',
            'item_name': 'Test Item',
            'print_block': 'Block 1',
            'print_machine': 'Machine 1'
        }
    ]
    
    result = WorkOrderService.create_work_orders_batch(work_orders_data, 'test_user')
    
    assert result['created_count'] == 1
    assert result['failed_count'] == 0
    assert len(result['created_ids']) == 1

def test_create_work_orders_batch_duplicate():
    # Test duplicate WO number handling
    pass
```

### 4.2. Integration Testing
```javascript
// tests/integration/test_work_order_api.js
describe('Work Order API Integration Tests', () => {
    test('should create work order successfully', async () => {
        const response = await fetch('/impact/api/mounting-work-order-incoming', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                wo_number: 'WO_TEST_001',
                mc_number: 'MC_TEST_001',
                customer_name: 'Test Customer',
                item_name: 'Test Item',
                print_block: 'Block 1',
                print_machine: 'Machine 1',
                created_by: 'test_user'
            })
        });
        
        expect(response.status).toBe(201);
        const data = await response.json();
        expect(data.success).toBe(true);
    });
});
```

## 5. Deployment Checklist

### 5.1. Pre-deployment
- [ ] Semua test passed
- [ ] Code review completed
- [ ] Documentation updated
- [ ] Database backup created
- [ ] Migration script tested

### 5.2. Deployment Steps
- [ ] Deploy to staging environment
- [ ] Run integration tests on staging
- [ ] Get approval from stakeholders
- [ ] Deploy to production
- [ ] Verify functionality on production
- [ ] Monitor system performance

### 5.3. Post-deployment
- [ ] Monitor error logs
- [ ] Collect user feedback
- [ ] Performance monitoring
- [ ] Bug fixes if needed

## 6. Risk Mitigation

### 6.1. Technical Risks
- **Database Performance**: Implement proper indexing
- **API Scalability**: Use pagination and caching
- **Frontend Compatibility**: Test on multiple browsers
- **Security**: Implement proper validation and sanitization

### 6.2. Business Risks
- **User Adoption**: Provide training and documentation
- **Data Quality**: Implement validation rules
- **Process Integration**: Ensure smooth workflow integration

## 7. Success Criteria

### 7.1. Functional Requirements
- [ ] User can input multiple work orders at once
- [ ] System validates input data
- [ ] System shows verification before submission
- [ ] Data is stored correctly in database
- [ ] User can view and filter work orders

### 7.2. Non-functional Requirements
- [ ] Page loads within 3 seconds
- [ ] System can handle 100+ concurrent users
- [ ] UI is responsive on mobile devices
- [ ] System is secure against common vulnerabilities
- [ ] Error handling is user-friendly

## 8. Timeline

```
Week 1:
- Day 1-2: Database model and migration
- Day 3-4: Backend API implementation
- Day 5: Initial testing

Week 2:
- Day 1-2: HTML template creation
- Day 3-4: JavaScript implementation
- Day 5: Integration testing

Week 3:
- Day 1-2: Navigation integration
- Day 3-4: Advanced features
- Day 5: Final testing and deployment
```

## 9. Resources Needed

### 9.1. Human Resources
- Backend Developer: 1 person
- Frontend Developer: 1 person
- QA Tester: 1 person
- Database Administrator: 0.5 person

### 9.2. Technical Resources
- Development environment
- Testing environment
- Production environment
- Database server
- File storage

## 10. Next Steps

1. **Immediate**: Start with database model implementation
2. **Short-term**: Complete backend API development
3. **Medium-term**: Implement frontend functionality
4. **Long-term**: Add advanced features and optimizations

---

*Document Version: 1.0*
*Last Updated: 2025-01-15*
*Author: Development Team*