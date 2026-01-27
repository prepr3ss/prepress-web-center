# Panduan Instalasi dan Penggunaan Flask Blueprint Refactoring

## Masalah yang Dihadapi

Saat menjalankan `app_refactored.py`, Anda mungkin mengalami error berikut:
```
sqlalchemy.exc.InvalidRequestError: Table 'chemical_bon_ctp' is already defined
for this MetaData instance.  Specify 'extend_existing=True' to redefine options
and columns on an existing Table object.
```

Ini terjadi karena ada masalah dengan import sirkular dan definisi model SQLAlchemy yang sudah ada.

## Solusi: Menggunakan app_simple.py

Saya telah membuat versi yang lebih sederhana dan stabil bernama `app_simple.py` yang mengatasi masalah ini.

## Langkah-langkah Instalasi

### 1. Backup Aplikasi Asli

```bash
# Backup app.py asli
cp app.py app_original_backup.py
```

### 2. Gunakan app_simple.py

```bash
# Jalankan aplikasi dengan versi yang telah diperbaiki
python app_simple.py
```

### 3. Struktur File yang Diperlukan

Pastikan struktur file Anda sebagai berikut:

```
impact/
├── app_simple.py              # Aplikasi utama yang stabil
├── app.py                     # Aplikasi asli (backup)
├── models.py                  # Model database
├── blueprints/                # Package Blueprint
│   ├── __init__.py
│   ├── main.py
│   ├── ctp.py
│   ├── press.py
│   ├── mounting.py
│   ├── pdnd.py
│   ├── design.py
│   └── admin.py
├── templates/
│   ├── _sidebar.html          # Template sidebar asli
│   ├── _sidebar.html  # Template sidebar yang diperbarui
│   └── ... (template lainnya)
├── static/                    # File static
└── instance/                  # Database SQLite
```

## Cara Menggunakan Implementasi Blueprint

### Opsi 1: Menggunakan app_simple.py (Direkomendasikan)

```bash
# Jalankan aplikasi
python app_simple.py
```

Aplikasi akan berjalan di `http://127.0.0.1:5021/` dengan semua rute memiliki prefiks `/impact/`.

### Opsi 2: Memperbaiki app_refactored.py

Jika Anda ingin menggunakan `app_refactored.py`, ikuti langkah-langkah berikut:

1. **Hapus import yang bermasalah di Blueprint:**

Edit setiap file Blueprint di `blueprints/` dan hapus import model yang menyebabkan konflik:

```python
# Hapus baris ini dari semua file Blueprint
# from models import db, User, Division, ...
```

2. **Import model di dalam fungsi:**

```python
@ctp_bp.route('/dashboard-ctp')
@login_required
def dashboard_ctp():
    from models import User  # Import di dalam fungsi
    # ... kode lainnya
```

### Opsi 3: Menggunakan Aplikasi Asli dengan Template yang Diperbarui

Jika Anda ingin tetap menggunakan `app.py` asli, cukup update template sidebar:

```bash
# Ganti template sidebar
cp templates/_sidebar.html templates/_sidebar.html
```

## Testing Aplikasi

Setelah aplikasi berjalan, test dengan cara berikut:

1. **Akses Dashboard:**
   - Buka `http://192.168.1.36:8080/impact/`
   - Login dengan kredensial Anda

2. **Test Navigasi:**
   - Klik setiap menu di sidebar
   - Pastikan semua tautan berfungsi dan menyertakan prefiks `/impact/`

3. **Test URL:**
   - Dashboard: `http://192.168.1.36:8080/impact/`
   - CTP Dashboard: `http://192.168.1.36:8080/impact/dashboard-ctp`
   - Press Adjustment: `http://192.168.1.36:8080/impact/data-adjustment`

## Troubleshooting

### Masalah 1: Error Import Model

**Error:** `Table 'chemical_bon_ctp' is already defined`

**Solusi:** Gunakan `app_simple.py` atau hapus import model dari Blueprint dan import di dalam fungsi.

### Masalah 2: Template Not Found

**Error:** `TemplateNotFound: template.html`

**Solusi:** Pastikan semua template ada di folder `templates/` dan Blueprint menggunakan path yang benar.

### Masalah 3: URL Tidak Berfungsi

**Error:** 404 Not Found

**Solusi:** Pastikan template menggunakan `url_for()` dengan nama Blueprint:
```html
<!-- Salah -->
<a href="/dashboard-ctp">Dashboard</a>

<!-- Benar -->
<a href="{{ url_for('ctp.dashboard_ctp') }}">Dashboard</a>
```

### Masalah 4: Konfigurasi Reverse Proxy

Jika aplikasi berjalan tetapi tidak dapat diakses melalui Apache:

1. **Periksa konfigurasi Apache:**
```apache
ProxyPass /impact/ http://127.0.0.1:5021/impact/
ProxyPassReverse /impact/ http://127.0.0.1:5021/impact/
```

2. **Restart Apache:**
```bash
sudo systemctl restart apache2
# atau
sudo service httpd restart
```

## Konfigurasi Production

Untuk production, ubah pengaturan berikut di `app_simple.py`:

```python
# Nonaktifkan debug mode
app.run(host='0.0.0.0', port=5021, debug=False)

# Gunakan secret key yang aman
app.config['SECRET_KEY'] = 'your-very-secure-secret-key-here'
```

## Kesimpulan

1. **Gunakan `app_simple.py`** untuk implementasi yang stabil dan mudah
2. **Update template** dengan `_sidebar.html` untuk menggunakan Blueprint
3. **Test semua tautan** untuk memastikan prefiks `/impact/` berfungsi dengan benar
4. **Tidak perlu mengubah konfigurasi Apache** - solusi ini berfungsi dengan konfigurasi yang ada

Dengan implementasi ini, aplikasi Flask Anda akan berfungsi dengan sempurna di belakang reverse proxy Apache tanpa masalah routing.