# Panduan Setup dan Penggunaan Fitur Log CTP

## 🚀 Setup Awal

### 1. Database Migration
Jalankan perintah berikut untuk membuat tabel database yang diperlukan:

```bash
# Aktifkan virtual environment
./venv/Scripts/activate

# Jalankan aplikasi (akan otomatis membuat tabel)
python app.py
```

### 2. Verifikasi Tabel
Pastikan tabel-tabel berikut telah dibuat:
- `ctp_machines` - Data mesin CTP
- `ctp_problem_logs` - Log problem mesin
- `ctp_notifications` - Sistem notifikasi

### 3. Folder Upload
Folder untuk upload foto problem akan otomatis dibuat:
- `instance/uploads/ctp_problems/`

## 📋 Fitur yang Tersedia

### 1. Overview Log CTP (`/log-ctp`)
- Menampilkan status ketiga mesin CTP
- Statistik problem terbaru
- Akses ke detail setiap mesin

### 2. Detail Mesin CTP (`/log-ctp/{machine}`)
- Status mesin (Aktif/Perbaikan)
- Statistik downtime
- Riwayat problem dengan filter
- Form input problem baru

### 3. Input Problem
- **Tanggal & Waktu**: Problem date dan start time
- **Deskripsi**: Keterangan detail problem
- **Foto**: Upload foto problem (PNG, JPG, JPEG, GIF)
- **Teknisi**: Jenis (Lokal/Vendor) dan nama
- **Solusi**: Keterangan solusi yang dilakukan
- **Downtime**: Perhitungan otomatis dari start time hingga end time

### 4. Notifikasi
- Notifikasi otomatis untuk problem baru
- Notifikasi saat problem selesai
- Tampil di sidebar (belum diimplementasikan fully)

## 🎯 Cara Penggunaan

### Akses Menu
1. Login ke sistem Impact 360
2. Buka menu **Prepress Production → CTP Production → Log CTP**
3. Pilih mesin yang ingin dilihat:
   - **Overview** - Lihat semua mesin
   - **CTP 1 Suprasetter** - Detail mesin 1
   - **CTP 2 Platesetter** - Detail mesin 2
   - **CTP 3 Trendsetter** - Detail mesin 3

### Menambahkan Problem
1. Klik tombol **"Tambah Problem"**
2. Isi form:
   - **Tanggal Problem**: Otomatis terisi waktu saat ini
   - **Waktu Mulai**: Otomatis terisi waktu saat ini
   - **Deskripsi Problem**: Jelaskan problem yang terjadi
   - **Foto Problem**: Upload foto (opsional)
   - **Jenis Teknisi**: Pilih Lokal atau Vendor
   - **Nama Teknisi**: Masukkan nama teknisi
   - **Solusi**: Jelaskan solusi yang dilakukan
   - **Waktu Selesai**: Kosongkan jika masih berjalan
3. Klik **"Simpan"**

### Menyelesaikan Problem
1. Dari halaman detail mesin, cari problem yang masih berjalan
2. Klik tombol **"Selesai"** pada baris problem
3. Atau klik **"Selesai Sekarang"** di form input
4. Masukkan waktu selesai atau gunakan waktu saat ini
5. Sistem otomatis menghitung downtime

### Melihat History
1. Gunakan filter untuk mencari problem:
   - **Tanggal Mulai**: Filter dari tanggal tertentu
   - **Tanggal Selesai**: Filter hingga tanggal tertentu
   - **Status**: Filter berdasarkan status (Berjalan/Selesai)
2. Klik **"Refresh"** untuk memuat data terbaru

## 📊 Statistik yang Ditampilkan

### Overview Page
- **Total Problem**: Jumlah semua problem per mesin
- **Problem Aktif**: Jumlah problem yang sedang berjalan
- **Total Downtime**: Akumulasi downtime semua problem
- **Rata-rata Downtime**: Rata-rata downtime per problem

### Detail Page
- **Total Problem**: Jumlah semua problem untuk mesin tersebut
- **Problem Aktif**: Jumlah problem yang sedang berjalan
- **Total Downtime**: Total jam downtime mesin tersebut
- **Rata-rata Downtime**: Rata-rata downtime per problem

## 🔧 Konfigurasi Tambahan

### File Upload Configuration
Di `config.py`, tambahkan konfigurasi berikut:

```python
# Upload configuration
UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'pdf'}
MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB max file size
```

### Static File Serving
Pastikan folder uploads dapat diakses:

```python
@app.route('/uploads/<path:filename>')
def uploaded_file(filename):
    return send_from_directory('uploads', filename)
```

## 🐛 Troubleshooting

### Masalah Umum

1. **ModuleNotFoundError: No module named 'flask_login'**
   - Solution: Install dengan `pip install flask-login`

2. **Error saat membuat tabel database**
   - Solution: Pastikan permission folder instance cukup
   - Restart aplikasi setelah mengubah model

3. **Foto tidak terupload**
   - Solution: Pastikan folder `instance/uploads/ctp_problems/` ada
   - Check file size limit (max 16MB)

4. **Halaman tidak bisa diakses**
   - Solution: Pastikan user memiliki role CTP atau admin
   - Check `can_access_ctp()` method di User model

### Debug Mode
Aktifkan debug mode untuk melihat error detail:

```python
app.run(host='0.0.0.0', port=5021, debug=True)
```

## 📱 Mobile Responsiveness

Fitur Log CTP sudah dioptimasi untuk mobile:
- Responsive cards untuk status mesin
- Collapsible filters pada layar kecil
- Touch-friendly buttons
- Optimized table scrolling

## 🔐 Security

### Authentication
- Hanya user dengan `can_access_ctp()` atau role `admin` yang bisa mengakses
- Session management dengan Flask-Login
- CSRF protection pada form

### File Upload
- File type validation (hanya image)
- File size limit (16MB)
- Secure filename handling
- Path traversal prevention

### Input Validation
- Required field validation
- SQL injection prevention dengan parameterized queries
- XSS prevention dengan escaping

## 📈 Future Enhancements

### Short Term
1. **Notifikasi Real-time**: WebSocket untuk notifikasi langsung
2. **Export Reports**: Export ke PDF/Excel
3. **Problem Categories**: Kategorisasi problem
4. **Technician Performance**: Tracking performa teknisi

### Long Term
1. **Predictive Maintenance**: AI untuk prediksi maintenance
2. **Integration dengan ERP**: Sync dengan sistem lain
3. **Mobile App**: Native app untuk teknisi
4. **Analytics Dashboard**: Advanced analytics dan reporting

## 📞 Support

Jika mengalami masalah:
1. Check browser console untuk error JavaScript
2. Check server logs untuk error backend
3. Pastikan semua dependencies terinstall
4. Restart aplikasi setelah perubahan

## 🎉 Selesai!

Fitur Log CTP sudah siap digunakan. User dapat:
- Memantau status mesin CTP real-time
- Mencatat problem dengan foto dan detail
- Menghitung downtime otomatis
- Melihat history dan trend problem
- Mengelola data teknisi dan solusi

System akan membantu management dalam:
- Decision making untuk maintenance
- Resource planning untuk teknisi
- Performance tracking mesin
- Historical analysis untuk improvement