# Panduan Import Data KPI CTP Production

## Overview

Dokumen ini menjelaskan cara mengimpor data KPI (Key Performance Indicator) ke tabel `ctp_production_logs` menggunakan script Python yang telah disediakan.

## File yang Tersedia

1. **import_kpi_data.py** - Script import dengan fitur konfirmasi dan dependensi aplikasi lengkap
2. **sample_kpi_data.json** - Contoh data JSON untuk import
3. **generate_dummy_kpi_data.py** - Generator data dummy untuk testing

## Cara Penggunaan

### Menggunakan Script Import KPI

Script ini menggunakan model SQLAlchemy dari aplikasi dan memiliki fitur konfirmasi untuk mencegah import yang tidak disengaja.

**Prasyarat:**
```bash
# Install dependensi yang dibutuhkan
pip install flask flask-sqlalchemy flask-login pytz
```

**Cara Penggunaan:**
```bash
# Menggunakan file contoh (dengan konfirmasi)
python import_kpi_data.py sample_kpi_data.json

# Menggunakan file JSON sendiri (dengan konfirmasi)
python import_kpi_data.py path/to/your/data.json

# Import tanpa konfirmasi (otomatis)
python import_kpi_data.py sample_kpi_data.json --yes

# Lihat bantuan lengkap
python import_kpi_data.py --help
```

**Fitur Konfirmasi:**
- Script akan menampilkan jumlah data yang akan diimpor
- Preview 3 data pertama akan ditampilkan
- User diminta konfirmasi sebelum import dimulai
- Gunakan flag `--yes` atau `-y` untuk melewati konfirmasi

**Contoh Output Konfirmasi:**
```
📊 Jumlah data yang ditemukan: 25 record

📋 Preview 3 data pertama:
  1. Brochure Company X - 2025-11-19 - CTP Group A
  2. Packaging Product Y - 2025-11-19 - CTP Group B
  3. Catalog Company Z - 2025-11-18 - CTP Group A
  ... dan 22 data lainnya

⚠️  Anda akan mengimport 25 data ke tabel 'ctp_production_logs'
❓ Apakah Anda ingin melanjutkan? (y/N):
```

## Struktur Data JSON

Data JSON harus mengikuti struktur berikut:

```json
[
  {
    "log_date": "YYYY-MM-DD",
    "ctp_group": "Nama Group CTP",
    "ctp_shift": "Shift Kerja",
    "ctp_pic": "Person In Charge",
    "ctp_machine": "Nomor Mesin CTP",
    "processor_temperature": 22.5,
    "dwell_time": 45.2,
    "wo_number": "Nomor Work Order",
    "mc_number": "Nomor MC",
    "run_length_sheet": 5000,
    "print_machine": "Mesin Cetak",
    "remarks_job": "Keterangan Job",
    "item_name": "Nama Item",
    "note": "Catatan Tambahan",
    "plate_type_material": "Jenis Plate",
    "paper_type": "Jenis Kertas",
    "raster": "175 LPI",
    "num_plate_good": 8,
    "num_plate_not_good": 0,
    "not_good_reason": "Alasan Tidak Baik",
    "start_time": "HH:MM",
    "finish_time": "HH:MM",
    
    // Warna CMYK
    "cyan_25_percent": 25.5,
    "cyan_50_percent": 50.2,
    "cyan_75_percent": 75.8,
    "cyan_linear": 98.5,
    "magenta_25_percent": 24.8,
    // ... dan seterusnya untuk magenta, yellow, black
    
    // Spot Colors (X, Z, U, V, F, G, H, J)
    "x_25_percent": 24.5,
    "x_50_percent": 49.8,
    "x_75_percent": 74.5,
    "x_linear": 97.5,
    // ... dan seterusnya untuk spot colors lainnya
  }
]
```

## Field Wajib (Required Fields)

Berikut adalah field yang wajib diisi:

- `log_date` (YYYY-MM-DD)
- `ctp_group`
- `ctp_shift`
- `ctp_pic`
- `ctp_machine`
- `mc_number`
- `print_machine`
- `remarks_job`
- `item_name`
- `num_plate_good`

## Field Opsional (Optional Fields)

Field opsional dapat diisi dengan `null` atau tidak disertakan dalam JSON:

- `processor_temperature`
- `dwell_time`
- `wo_number`
- `run_length_sheet`
- `note`
- `plate_type_material`
- `paper_type`
- `raster`
- `num_plate_not_good`
- `not_good_reason`
- `start_time` (HH:MM format)
- `finish_time` (HH:MM format)
- Semua field persentase warna dan linear

## Tips dan Best Practices

1. **Format Tanggal**: Gunakan format YYYY-MM-DD untuk `log_date`
2. **Format Waktu**: Gunakan format HH:MM atau HH:MM:SS (24 jam) untuk `start_time` dan `finish_time`
   - Contoh valid: "08:00", "16:30", "23:45", "03:00:00"
   - Script akan mengabaikan detik jika ada (HH:MM:SS)
3. **Nilai Numerik**: Script dapat menangani baik titik (.) maupun koma (,) sebagai desimal
   - Contoh valid: "22.5", "22,5", "25", "null"
   - Field kosong dapat menggunakan "-" atau null
4. **Field Kosong**: Untuk field yang tidak ada nilainya, gunakan `null`, `""`, atau `-`
5. **Backup Database**: Selalu backup database sebelum melakukan import besar-besaran
6. **Test Data**: Uji dengan data kecil terlebih dahulu sebelum mengimport semua data

## Format Data Aktual (Contoh)

Script dapat menangani format data seperti ini:

```json
{
  "log_date": "2025-02-28",
  "ctp_group": "B",
  "ctp_shift": "Shift 2",
  "ctp_pic": "Administrator",
  "ctp_machine": "CTP 1",
  "processor_temperature": "25",
  "dwell_time": "25",
  "wo_number": "250215405, 250215406, 250215407",
  "mc_number": "OFS125905871",
  "run_length_sheet": "-",
  "print_machine": "VLF",
  "remakrs_job": "Other",
  "item_name": "PROOF DGB400NASESP-320 CUISINART COFFE MAKER",
  "note": "PRODUKSI (CMYK, SP1)",
  "plate_type_material": "FUJI 1630",
  "paper_type": "Other",
  "raster": "AM",
  "num_plate_good": "5",
  "num_plate_not_good": null,
  "not_good_reason": null,
  "start_time": "03:00:00",
  "finish_time": "04:00:00",
  "cyan_25_percent": "22,5",
  "cyan_50_percent": "39,9",
  "cyan_75_percent": "65,6",
  "cyan_linear": null
}
```

**Catatan Khusus:**
- Script akan otomatis menghandle typo field `remakrs_job` menjadi `remarks_job`
- Nilai numerik dengan koma (,) akan dikonversi menjadi titik (.)
- Nilai "-" akan diubah menjadi null
- Format waktu HH:MM:SS akan dipotong menjadi HH:MM

## Troubleshooting

### Error: "Table 'ctp_production_logs' not found"
Pastikan database sudah ada dan tabel `ctp_production_logs` sudah dibuat. Jalankan migrasi database jika perlu.

### Error: "No module named 'flask_login'"
Install dependensi yang dibutuhkan:
```bash
pip install flask flask-sqlalchemy flask-login pytz
```

### Error: "Format JSON tidak valid"
Periksa format JSON menggunakan validator online atau pastikan:
- Tanda kutip menggunakan `"` bukan `'`
- Tidak ada koma ekstra di akhir objek/array
- Kurung kurawal dan siku sudah pasangan

### Error: "Foreign key constraint failed"
Pastikan data yang diimpor memenuhi constraint yang ada di database.

## Contoh Penggunaan Lanjutan

### Import Multiple Files
```bash
# Buat batch script untuk import multiple files
for file in data/*.json; do
    python import_kpi_data.py "$file"
done
```

### Batch Import dengan Konfirmasi Otomatis
```bash
# Import multiple files tanpa konfirmasi
for file in data/*.json; do
    python import_kpi_data.py "$file" --yes
done
```

### Generate Data Dummy untuk Testing
```bash
# Generate 20 data dummy
python generate_dummy_kpi_data.py 20

# Generate 50 data dummy dengan nama file kustom
python generate_dummy_kpi_data.py 50 test_data.json

# Import data dummy yang sudah digenerate
python import_kpi_data.py dummy_kpi_data.json --yes
```

## Validasi Data

Script akan melakukan validasi dasar:
- Format JSON yang valid
- Field wajib harus ada
- Tipe data yang sesuai

Untuk validasi lebih lanjut, Anda dapat menambahkan validasi kustom sesuai kebutuhan bisnis.

## Support

Jika mengalami masalah:
1. Periksa format JSON
2. Pastikan database accessible
3. Cek permission file/directory
4. Lihat error message detail di console