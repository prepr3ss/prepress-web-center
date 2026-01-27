# Dynamic Flow Configuration Guide

## Overview

Sistem R&D Cloudsphere sekarang mendukung **flow konfigurasi dinamis** yang memungkinkan pengguna untuk:
- Membuat konfigurasi flow kustom untuk setiap sample type
- Memilih urutan step proses saat membuat job baru
- Mengelola konfigurasi flow (create, update, delete)
- Menetapkan konfigurasi default untuk setiap sample type

## Fitur Utama

### 1. Manajemen Flow Configuration

#### A. Membuat Konfigurasi Flow Baru
- **Nama Konfigurasi**: Nama unik untuk mengidentifikasi konfigurasi
- **Sample Type**: Blank, RoHS ICB, atau RoHS Ribbon
- **Deskripsi**: Penjelasan tentang konfigurasi flow
- **Status**: Aktif/Non-aktif
- **Default**: Dapat ditetapkan sebagai default untuk sample type

#### B. Mengatur Step Flow
- **Drag & Drop**: Seret step dari daftar available steps ke area flow
- **Reorder**: Ubah urutan step dengan drag and drop
- **Required/Optional**: Tandai step sebagai required atau optional
- **Step Details**: Setiap step memiliki tasks yang terkait

#### C. Mengelola Konfigurasi
- **View**: Lihat detail konfigurasi flow
- **Edit**: Ubah konfigurasi yang ada
- **Delete**: Hapus konfigurasi (jika tidak digunakan)
- **Set Default**: Tetapkan sebagai default untuk sample type

### 2. Integrasi dengan Job Creation

#### A. Pemilihan Flow Configuration
Saat membuat job baru:
1. Pilih **Sample Type**
2. Pilih **Flow Configuration** dari daftar yang tersedia
3. Sistem akan menampilkan steps sesuai konfigurasi yang dipilih
4. Assign PIC untuk setiap step
5. Pilih tasks yang akan dieksekusi

#### B. Flow Configuration Default
- Sistem otomatis menggunakan konfigurasi default untuk sample type
- Jika tidak ada konfigurasi kustom, sistem menggunakan fallback ke static mapping

## Cara Penggunaan

### 1. Mengakses Halaman Flow Configuration

1. Login ke sistem
2. Buka menu **R&D** → **Flow Configuration**
3. Halaman akan menampilkan daftar konfigurasi yang ada

### 2. Membuat Konfigurasi Flow Baru

1. Klik tombol **"Create New Configuration"**
2. Isi form:
   - **Configuration Name**: Nama konfigurasi
   - **Sample Type**: Pilih dari dropdown
   - **Description**: Penjelasan konfigurasi
   - **Set as Default**: Centang jika ingin menjadi default
3. Klik **"Configure Flow Steps"**
4. **Drag & Drop Steps**:
   - Available Steps: Daftar semua steps yang tersedia
   - Flow Steps: Area untuk menaruh steps
5. Seret step dari **Available Steps** ke **Flow Steps**
6. Atur ulang dengan drag and drop
7. Tandai step sebagai **Required** jika diperlukan
8. Klik **"Save Configuration"**

### 3. Menggunakan Flow Configuration di Job Creation

1. Buka halaman **R&D Cloudsphere**
2. Klik **"Create New Job"**
3. Isi form job:
   - **Item Name**: Nama item/job
   - **Sample Type**: Pilih sample type
   - **Flow Configuration**: Pilih konfigurasi flow (dropdown akan muncul setelah memilih sample type)
   - **Priority Level**: Pilih priority
   - **Start Date & Deadline**: Set tanggal
4. Sistem akan menampilkan steps sesuai konfigurasi yang dipilih
5. Assign PIC untuk setiap step
6. Pilih tasks yang akan dieksekusi
7. Klik **"Create Job"**

## Struktur Database

### Tabel Baru

#### `rnd_flow_configurations`
- `id`: Primary key
- `name`: Nama konfigurasi
- `sample_type`: Sample type (Blank, RoHS ICB, RoHS Ribbon)
- `description`: Deskripsi konfigurasi
- `is_default`: Default untuk sample type
- `is_active`: Status aktif
- `created_by`: ID user yang membuat
- `created_at`: Tanggal pembuatan
- `updated_at`: Tanggal pembaruan

#### `rnd_flow_steps`
- `id`: Primary key
- `flow_configuration_id`: Foreign key ke rnd_flow_configurations
- `progress_step_id`: Foreign key ke rnd_progress_steps
- `step_order`: Urutan step dalam flow
- `is_required`: Apakah step required
- `created_at`: Tanggal pembuatan

#### `rnd_jobs` (modifikasi)
- `flow_configuration_id`: Foreign key ke rnd_flow_configurations (nullable)

## API Endpoints

### Flow Configuration Management
- `GET /api/flow-configurations`: Daftar semua konfigurasi
- `GET /api/flow-configurations/{id}`: Detail konfigurasi
- `POST /api/flow-configurations`: Buat konfigurasi baru
- `PUT /api/flow-configurations/{id}`: Update konfigurasi
- `DELETE /api/flow-configurations/{id}`: Hapus konfigurasi
- `POST /api/flow-configurations/{id}/set-default`: Tetapkan sebagai default
- `POST /api/init-default-flow-configurations`: Inisialisasi konfigurasi default

### Progress Steps (Updated)
- `GET /api/progress-steps?sample_type={type}&flow_configuration_id={id}`: 
  - Jika flow_configuration_id disediakan: Gunakan konfigurasi dinamis
  - Jika tidak: Fallback ke static mapping

### Job Creation (Updated)
- `POST /api/job`: Sekarang menerima `flow_configuration_id`

## Migrasi Database

Untuk mengaktifkan fitur ini:

1. Jalankan migrasi database:
   ```bash
   flask db upgrade
   ```

2. Inisialisasi konfigurasi default:
   - Akses endpoint `/api/init-default-flow-configurations`
   - Sistem akan membuat konfigurasi default berdasarkan data yang ada

## Keuntungan

### 1. Fleksibilitas
- Setiap departemen dapat membuat flow kustom sesuai kebutuhan
- Tidak perlu mengubah kode untuk mengatur flow
- Dapat membuat multiple flow untuk sample type yang sama

### 2. Versioning
- Konfigurasi lama tetap tersimpan
- Dapat membuat versi baru tanpa menghapus yang lama
- Mudah rollback ke konfigurasi sebelumnya

### 3. A/B Testing
- Dapat membuat multiple konfigurasi untuk testing
- Bandingkan efektivitas flow yang berbeda
- Pilih konfigurasi terbaik berdasarkan data

### 4. Audit Trail
- Semua perubahan tersimpan dengan timestamp
- Tahu siapa yang membuat/mengubah konfigurasi
- History perubahan untuk audit

## Troubleshooting

### Common Issues

#### 1. Konfigurasi Default Tidak Muncul
- **Solusi**: Pastikan ada konfigurasi dengan flag `is_default = true`
- **Check**: Verifikasi di database melalui admin panel

#### 2. Steps Tidak Muncul Saat Create Job
- **Solusi**: 
  1. Pastikan flow_configuration_id terkirim saat create job
  2. Check response dari API progress-steps
  3. Verify flow steps ter-load dengan benar

#### 3. Error "No flow configurations found"
- **Solusi**: 
  1. Inisialisasi default configuration terlebih dahulu
  2. Buat konfigurasi baru secara manual
  3. Check sample type yang dipilih sudah benar

## Best Practices

### 1. Penamaan Konfigurasi
- Gunakan nama yang deskriptif dan konsisten
- Include sample type dan versi dalam nama
- Contoh: "Blank Workflow v2.0" atau "RoHS ICB Express"

### 2. Documentation
- Documentasikan alasan pembuatan konfigurasi baru
- Catat perubahan dan dampaknya
- Share dengan tim yang terkait

### 3. Testing
- Test konfigurasi baru dengan job sample
- Verifikasi semua steps muncul dengan benar
- Pastikan PIC assignment berfungsi dengan baik

### 4. Backup
- Export konfigurasi penting sebelum perubahan besar
- Schedule regular backup dari konfigurasi flow
- Simpan dokumentasi terkait

## Future Enhancements

### 1. Flow Templates
- Template konfigurasi untuk sample type baru
- Copy-paste konfigurasi antar sample type
- Import/export konfigurasi dalam format JSON

### 2. Conditional Logic
- Steps berbeda berdasarkan item properties
- Dynamic step selection berdasarkan complexity
- Auto-recommendation berdasarkan historical data

### 3. Analytics
- Tracking performa setiap konfigurasi flow
- Identifikasi bottleneck dalam proses
- Optimization suggestions berdasarkan data

## Support

Untuk bantuan lebih lanjut mengenai fitur Dynamic Flow Configuration:
1. Documentation teknis: Lihat file kode sumber
2. Database schema: Lihat model files
3. API documentation: Lihat endpoint documentation
4. Testing: Lihat test files untuk contoh penggunaan

---
*Document Version: 1.0*  
*Last Updated: December 17, 2025*