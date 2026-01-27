# Spesifikasi API Endpoints untuk Work Order Incoming

## 1. Struktur API Routes

### 1.1. Base URL
```
/impact/api/mounting-work-order-incoming
```

### 1.2. Authentication
- Semua endpoint memerlukan authentication
- Menggunakan session-based authentication yang sudah ada di sistem
- User harus login untuk mengakses API

## 2. API Endpoints

### 2.1. GET /impact/api/mounting-work-order-incoming
**Deskripsi:** Mendapatkan daftar Work Order Incoming dengan pagination dan filter

**Query Parameters:**
- `page` (integer, optional): Nomor halaman, default: 1
- `per_page` (integer, optional): Jumlah data per halaman, default: 20, max: 100
- `date` (string, optional): Filter tanggal (YYYY-MM-DD)
- `status` (string, optional): Filter status (incoming/processed/cancelled)
- `customer` (string, optional): Filter nama customer
- `search` (string, optional): Pencarian di WO Number, MC Number, Item Name
- `sort_by` (string, optional): Kolom sorting, default: incoming_datetime
- `sort_order` (string, optional): Arah sorting (asc/desc), default: desc

**Response:**
```json
{
    "success": true,
    "data": [
        {
            "id": 1,
            "incoming_datetime": "2025-01-15 08:30:00",
            "wo_number": "WO20250115001",
            "mc_number": "MC20250115001",
            "customer_name": "PT. ABC Indonesia",
            "item_name": "Kemasan Produk XYZ",
            "print_block": "Block A-001",
            "print_machine": "Heidelberg Speedmaster 102",
            "run_length_sheet": 5000,
            "sheet_size": "500x700 mm",
            "paper_type": "Art Paper 150 gsm",
            "status": "incoming",
            "processed_at": null,
            "processed_by": null,
            "created_at": "2025-01-15 08:30:00",
            "created_by": "admin",
            "updated_at": "2025-01-15 08:30:00"
        }
    ],
    "pagination": {
        "current_page": 1,
        "total_pages": 5,
        "total_records": 95,
        "per_page": 20,
        "has_next": true,
        "has_prev": false
    }
}
```

### 2.2. GET /impact/api/mounting-work-order-incoming/{id}
**Deskripsi:** Mendapatkan detail Work Order Incoming berdasarkan ID

**Path Parameters:**
- `id` (integer): ID Work Order Incoming

**Response:**
```json
{
    "success": true,
    "data": {
        "id": 1,
        "incoming_datetime": "2025-01-15 08:30:00",
        "wo_number": "WO20250115001",
        "mc_number": "MC20250115001",
        "customer_name": "PT. ABC Indonesia",
        "item_name": "Kemasan Produk XYZ",
        "print_block": "Block A-001",
        "print_machine": "Heidelberg Speedmaster 102",
        "run_length_sheet": 5000,
        "sheet_size": "500x700 mm",
        "paper_type": "Art Paper 150 gsm",
        "status": "incoming",
        "processed_at": null,
        "processed_by": null,
        "created_at": "2025-01-15 08:30:00",
        "created_by": "admin",
        "updated_at": "2025-01-15 08:30:00"
    }
}
```

### 2.3. POST /impact/api/mounting-work-order-incoming
**Deskripsi:** Membuat Work Order Incoming baru (single)

**Request Body:**
```json
{
    "wo_number": "WO20250115001",
    "mc_number": "MC20250115001",
    "customer_name": "PT. ABC Indonesia",
    "item_name": "Kemasan Produk XYZ",
    "print_block": "Block A-001",
    "print_machine": "Heidelberg Speedmaster 102",
    "run_length_sheet": 5000,
    "sheet_size": "500x700 mm",
    "paper_type": "Art Paper 150 gsm",
    "created_by": "admin"
}
```

**Response:**
```json
{
    "success": true,
    "message": "Work Order Incoming berhasil dibuat",
    "data": {
        "id": 1,
        "incoming_datetime": "2025-01-15 08:30:00",
        "wo_number": "WO20250115001",
        "mc_number": "MC20250115001",
        "customer_name": "PT. ABC Indonesia",
        "item_name": "Kemasan Produk XYZ",
        "print_block": "Block A-001",
        "print_machine": "Heidelberg Speedmaster 102",
        "run_length_sheet": 5000,
        "sheet_size": "500x700 mm",
        "paper_type": "Art Paper 150 gsm",
        "status": "incoming",
        "processed_at": null,
        "processed_by": null,
        "created_at": "2025-01-15 08:30:00",
        "created_by": "admin",
        "updated_at": "2025-01-15 08:30:00"
    }
}
```

### 2.4. POST /impact/api/mounting-work-order-incoming/batch
**Deskripsi:** Membuat multiple Work Order Incoming sekaligus

**Request Body:**
```json
{
    "work_orders": [
        {
            "wo_number": "WO20250115001",
            "mc_number": "MC20250115001",
            "customer_name": "PT. ABC Indonesia",
            "item_name": "Kemasan Produk XYZ",
            "print_block": "Block A-001",
            "print_machine": "Heidelberg Speedmaster 102",
            "run_length_sheet": 5000,
            "sheet_size": "500x700 mm",
            "paper_type": "Art Paper 150 gsm"
        },
        {
            "wo_number": "WO20250115002",
            "mc_number": "MC20250115002",
            "customer_name": "PT. DEF Indonesia",
            "item_name": "Kemasan Produk UVW",
            "print_block": "Block B-002",
            "print_machine": "Komori Lithrone S29",
            "run_length_sheet": 3000,
            "sheet_size": "400x600 mm",
            "paper_type": "Duplex 200 gsm"
        }
    ],
    "created_by": "admin"
}
```

**Response:**
```json
{
    "success": true,
    "message": "2 Work Order Incoming berhasil dibuat",
    "data": {
        "created_count": 2,
        "failed_count": 0,
        "created_ids": [1, 2],
        "failed_items": []
    }
}
```

### 2.5. PUT /impact/api/mounting-work-order-incoming/{id}
**Deskripsi:** Update Work Order Existing

**Path Parameters:**
- `id` (integer): ID Work Order Incoming

**Request Body:**
```json
{
    "wo_number": "WO20250115001",
    "mc_number": "MC20250115001",
    "customer_name": "PT. ABC Indonesia Updated",
    "item_name": "Kemasan Produk XYZ Updated",
    "print_block": "Block A-001",
    "print_machine": "Heidelberg Speedmaster 102",
    "run_length_sheet": 6000,
    "sheet_size": "500x700 mm",
    "paper_type": "Art Paper 150 gsm"
}
```

**Response:**
```json
{
    "success": true,
    "message": "Work Order Incoming berhasil diupdate",
    "data": {
        "id": 1,
        "incoming_datetime": "2025-01-15 08:30:00",
        "wo_number": "WO20250115001",
        "mc_number": "MC20250115001",
        "customer_name": "PT. ABC Indonesia Updated",
        "item_name": "Kemasan Produk XYZ Updated",
        "print_block": "Block A-001",
        "print_machine": "Heidelberg Speedmaster 102",
        "run_length_sheet": 6000,
        "sheet_size": "500x700 mm",
        "paper_type": "Art Paper 150 gsm",
        "status": "incoming",
        "processed_at": null,
        "processed_by": null,
        "created_at": "2025-01-15 08:30:00",
        "created_by": "admin",
        "updated_at": "2025-01-15 09:15:00"
    }
}
```

### 2.6. DELETE /impact/api/mounting-work-order-incoming/{id}
**Deskripsi:** Hapus Work Order Incoming

**Path Parameters:**
- `id` (integer): ID Work Order Incoming

**Response:**
```json
{
    "success": true,
    "message": "Work Order Incoming berhasil dihapus"
}
```

### 2.7. PUT /impact/api/mounting-work-order-incoming/{id}/status
**Deskripsi:** Update status Work Order Incoming

**Path Parameters:**
- `id` (integer): ID Work Order Incoming

**Request Body:**
```json
{
    "status": "processed",
    "processed_by": "operator1"
}
```

**Response:**
```json
{
    "success": true,
    "message": "Status Work Order Incoming berhasil diupdate",
    "data": {
        "id": 1,
        "status": "processed",
        "processed_at": "2025-01-15 10:30:00",
        "processed_by": "operator1"
    }
}
```

### 2.8. GET /impact/api/mounting-work-order-incoming/statistics
**Deskripsi:** Mendapatkan statistik Work Order Incoming

**Query Parameters:**
- `date_from` (string, optional): Tanggal mulai (YYYY-MM-DD)
- `date_to` (string, optional): Tanggal akhir (YYYY-MM-DD)

**Response:**
```json
{
    "success": true,
    "data": {
        "total_count": 150,
        "incoming_count": 45,
        "processed_count": 95,
        "cancelled_count": 10,
        "today_count": 8,
        "this_week_count": 35,
        "this_month_count": 120,
        "top_customers": [
            {
                "customer_name": "PT. ABC Indonesia",
                "count": 25
            },
            {
                "customer_name": "PT. DEF Indonesia",
                "count": 18
            }
        ],
        "top_machines": [
            {
                "print_machine": "Heidelberg Speedmaster 102",
                "count": 30
            },
            {
                "print_machine": "Komori Lithrone S29",
                "count": 22
            }
        ]
    }
}
```

## 3. Error Responses

### 3.1. Standard Error Format
```json
{
    "success": false,
    "error": {
        "code": "VALIDATION_ERROR",
        "message": "Data tidak valid",
        "details": {
            "wo_number": ["WO Number tidak boleh kosong"],
            "mc_number": ["MC Number tidak boleh kosong"]
        }
    }
}
```

### 3.2. Error Codes
- `VALIDATION_ERROR`: Error validasi data
- `NOT_FOUND`: Data tidak ditemukan
- `DUPLICATE_ENTRY`: Data duplikat (WO Number sudah ada)
- `PERMISSION_DENIED`: Tidak memiliki akses
- `INTERNAL_ERROR`: Error server internal
- `DATABASE_ERROR`: Error database

### 3.3. HTTP Status Codes
- `200`: Success
- `201`: Created
- `400`: Bad Request (Validation Error)
- `401`: Unauthorized
- `403`: Forbidden
- `404`: Not Found
- `409`: Conflict (Duplicate Entry)
- `500`: Internal Server Error

## 4. Validation Rules

### 4.1. Required Fields
- `wo_number`: Required, max 50 characters, unique
- `mc_number`: Required, max 50 characters
- `customer_name`: Required, max 100 characters
- `item_name`: Required, max 100 characters
- `print_block`: Required, max 50 characters
- `print_machine`: Required, max 100 characters

### 4.2. Optional Fields
- `run_length_sheet`: Numeric, min 0
- `sheet_size`: Max 50 characters
- `paper_type`: Max 50 characters

### 4.3. Status Values
- `incoming`: Default status
- `processed`: Sudah diproses
- `cancelled`: Dibatalkan

## 5. Rate Limiting

### 5.1. Rate Limit Rules
- GET endpoints: 100 requests per minute
- POST endpoints: 50 requests per minute
- PUT/DELETE endpoints: 30 requests per minute

### 5.2. Rate Limit Response
```json
{
    "success": false,
    "error": {
        "code": "RATE_LIMIT_EXCEEDED",
        "message": "Terlalu banyak request, coba lagi dalam 1 menit"
    }
}
```

## 6. Caching Strategy

### 6.1. Cache Rules
- GET list data: Cache 5 menit
- GET detail data: Cache 10 menit
- GET statistics: Cache 15 menit
- POST/PUT/DELETE: Clear cache

### 6.2. Cache Keys
- `work_order_incoming_list:{page}:{per_page}:{filters_hash}`
- `work_order_incoming_detail:{id}`
- `work_order_incoming_statistics:{date_range_hash}`

## 7. Security Considerations

### 7.1. Input Sanitization
- SQL Injection prevention
- XSS prevention
- CSRF protection

### 7.2. Data Access Control
- User hanya bisa mengakses data sesuai role
- Log semua perubahan data
- Audit trail untuk setiap operasi

## 8. Performance Optimization

### 8.1. Database Optimization
- Index pada kolom yang sering di-filter
- Query optimization untuk pagination
- Connection pooling

### 8.2. Response Optimization
- Compression untuk response JSON
- Pagination untuk data besar
- Selective field loading

## 9. Testing Strategy

### 9.1. Unit Tests
- Test semua validation rules
- Test error handling
- Test business logic

### 9.2. Integration Tests
- Test API endpoints
- Test database operations
- Test authentication

### 9.3. Load Tests
- Test dengan data besar
- Test concurrent requests
- Test performance under load