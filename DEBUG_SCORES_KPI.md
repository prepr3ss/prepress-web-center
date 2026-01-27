# DEBUG OUTPUT - Scores KPI Calculation

## Approach: Calculate ALL Steps per Sample Type (dengan Security Check)

Dengan update ini, Scores KPI sekarang menghitung **SEMUA steps** yang termasuk dalam sample_type tersebut, dengan **double-check security**:

```python
# Filter BOTH step dan job berdasarkan sample_type
.filter(
    RNDProgressStep.sample_type == sample_type,  # ← Step dari sample_type ini
    RNDJob.sample_type == sample_type  # ← Job juga harus sample_type ini
)
```

**Alasan:** Mencegah clash dari step dengan nama yang sama di berbagai sample_type:
- `Proof Approval` ada di RoHS ICB (step #6) DAN RoHS Ribbon (step #9)
- Filter double-check memastikan assignment dari RoHS ICB tidak termasuk step dari RoHS Ribbon

- **Design**: 1 step (Design & Artwork Approval)
- **Mastercard**: 1 step (Mastercard Release)
- **Blank**: 3 steps (Initial Plotter, Sample Production, Quality Validation)
- **RoHS ICB**: 3 steps (Proof Approval, Sample Production, Quality Validation)
- **RoHS Ribbon**: 3 steps (Proof Approval, Sample Production, Quality Validation)
- **Polymer Ribbon**: 2 steps (Polymer Order, Polymer Receiving)
- **Light-Standard-Dark**: 1 step (Determine Light-Standard-Dark Reference)

Hasilnya adalah **rata-rata total waktu untuk menyelesaikan seluruh workflow sample_type tersebut**.

## Cara Menggunakan Debug

1. **Buka Flask terminal** dimana server berjalan
2. **Buka dashboard R&D Cloudsphere** dan refresh halaman
3. **Lihat console/terminal** untuk melihat debug output detail

## Contoh Debug Output

### Header
```
################################################################################
# SCORES KPI CALCULATION DEBUG
################################################################################
Request Parameters: year=2026, month=1
Total RND Users: 3
Stage Mapping (by sample_type): 7 stages
################################################################################
```

### Detail Per User & Stage (UPDATED dengan Security Check)
```
================================================================================
DEBUG Scores KPI: Stage 'RoHS ICB' for user 'Albert Sovan Daeli' (ID: 49)
================================================================================
  Filter: Year=2026, Month=1
  Date Range: 2026-01-01 00:00:00+07:00 to 2026-02-01 00:00:00+07:00
  Total assignments found: 7
  Stage Name (display): RoHS ICB
  Sample Type (filter): RoHS ICB
  Filter Security: Both RNDProgressStep.sample_type AND RNDJob.sample_type = 'RoHS ICB'
  Steps included in 'RoHS ICB':
    - #1: Proof Approval
    - #2: Sample Production
    - #3: Quality Validation
================================================================================
  [Job 1 - Step #1 (Proof Approval)]:
    Job ID: RND-20260114-002
    Assignment ID: 410
    Started: 2026-01-14 10:00:00
    Finished: 2026-01-15 14:30:00
    Duration: 1.1875 days (28h 30m)
    Status: completed

  [Job 1 - Step #2 (Sample Production)]:
    Job ID: RND-20260114-002
    Assignment ID: 411
    Started: 2026-01-15 15:00:00
    Finished: 2026-01-18 09:00:00
    Duration: 2.75 days (66h 0m)
    Status: completed

  [Job 1 - Step #3 (Quality Validation)]:
    Job ID: RND-20260114-002
    Assignment ID: 412
    Started: 2026-01-18 10:00:00
    Finished: 2026-01-19 15:00:00
    Duration: 1.2083 days (29h 0m)
    Status: completed

  [Job 2 - Step #1 (Proof Approval)]:
    Job ID: RND-20260116-001
    Assignment ID: 413
    Started: 2026-01-17 08:00:00
    Finished: 2026-01-18 10:00:00
    Duration: 1.0833 days (26h 0m)
    Status: completed

  [Job 2 - Step #2 (Sample Production)]:
    Job ID: RND-20260116-001
    Assignment ID: 414
    Started: 2026-01-19 11:00:00
    Finished: 2026-01-22 09:30:00
    Duration: 2.9375 days (70h 30m)
    Status: completed

  [SKIPPED] Assignment 415: status=in_progress (not completed)

--------------------------------------------------------------------------------
  SUMMARY:
  Total completed with duration: 5
  Total days: 9.1666 days
  Average: 9.1666 ÷ 5 = 1.8333 days
  Final Score: 1.83 days
================================================================================
```

Ini adalah **rata-rata waktu per assignment** untuk menyelesaikan seluruh workflow RoHS ICB.
Jika kita ingin rata-rata per JOB (bukan per assignment), akan berbeda.

### Final Results Summary
```
################################################################################
# FINAL RESULTS SUMMARY
################################################################################

User: Albert Sovan Daeli (@daeli)
  Scores:
    - Design: 5.88 days
    - Mastercard: 2.17 days
    - Blank: 8.45 days
    - RoHS ICB: 1.83 days
    - RoHS Ribbon: 3.21 days

User: Aji Setiawan (@aji)
  Scores:
    - Design: 0.00 days
    - Mastercard: 13.00 days
    - Blank: 0.00 days

User: Abdul Haris Halim (@haris)
  Scores:
    - Design: 119.52 days
    - RoHS ICB: 8.50 days

################################################################################
```

## Apa yang Dicek

✅ **Total RND Users** - Berapa user yang dihitung  
✅ **Filter Applied** - Year/Month yang digunakan  
✅ **Total Assignments Found** - Berapa assignments ditemukan (SEMUA steps dalam sample_type)
✅ **Steps Included** - Daftar semua steps yang dimasukkan dalam perhitungan
✅ **Individual Assignment Calculation** - Detail setiap assignment (ID, step, start, finish, duration)  
✅ **Skipped Assignments** - Assignment yang tidak dihitung dan alasannya  
✅ **Summary** - Total hari, count assignments, rata-rata  
✅ **Final Score** - Hasil akhir untuk setiap sample_type  

## Security Check: Prevent Step Name Clash

**Masalah yang dicegah:**

Beberapa step memiliki nama yang sama di berbagai sample_type:
```sql
Step #6: Proof Approval (sample_type='RoHS ICB')
Step #9: Proof Approval (sample_type='RoHS Ribbon')
```

**Solusi:**
Filter tidak hanya berdasarkan `RNDProgressStep.sample_type`, tapi juga `RNDJob.sample_type`:

```python
assignments_query = db.session.query(RNDJobProgressAssignment).filter(
    RNDJobProgressAssignment.pic_id == user.id,
    RNDProgressStep.sample_type == 'RoHS ICB',  # ← Step ini
    RNDJob.sample_type == 'RoHS ICB'  # ← Job juga harus RoHS ICB
).join(RNDProgressStep).join(RNDJob)
```

**Hasil:**
- Assignment dari Proof Approval di RoHS ICB ✅ INCLUDE
- Assignment dari Proof Approval di RoHS Ribbon ✅ EXCLUDE (job sample_type berbeda)

Debug output menampilkan:
```
Filter Security: Both RNDProgressStep.sample_type AND RNDJob.sample_type = 'RoHS ICB'
```

## Cara Membaca Output

### Filter Security Line:
```
Filter Security: Both RNDProgressStep.sample_type AND RNDJob.sample_type = 'RoHS ICB'
```
Ini menunjukkan bahwa KEDUA check dilakukan untuk mencegah clash.
```
Steps included in 'RoHS ICB':
  - #1: Proof Approval
  - #2: Sample Production
  - #3: Quality Validation
```
Ini menunjukkan bahwa score RoHS ICB menghitung ketiga step tersebut.

### Assignments dari berbagai jobs dan steps:
```
[Job 1 - Step #1 (Proof Approval)]
[Job 1 - Step #2 (Sample Production)]
[Job 1 - Step #3 (Quality Validation)]
[Job 2 - Step #1 (Proof Approval)]
...
```
Semua assignments dari sample_type yang sama dimasukkan dalam perhitungan.

### Summary:
```
Total completed with duration: 5
Total days: 9.1666 days
Average: 9.1666 ÷ 5 = 1.8333 days
Final Score: 1.83 days
```

**Interpretasi:**
- Ditemukan 5 completed assignments dalam sample_type ini (bulan/tahun tersebut)
- Total akumulatif: 9.17 hari
- **Rata-rata per assignment: 1.83 hari**

## Catatan Penting

### Perbedaan dengan Sebelumnya:

**SEBELUM (Per Step):**
```
- Design: 5.88 hari (hanya Design & Artwork Approval)
- RoHS ICB: 1.5 hari (hanya Proof Approval)
```

**SESUDAH (Semua Steps):**
```
- Design: 5.88 hari (sama, hanya 1 step)
- RoHS ICB: 4.2 hari (Proof + Sample + Quality) ← BERUBAH!
```

RoHS ICB sekarang menunjukkan rata-rata total waktu untuk menyelesaikan ketiga tahap.

## Database Query untuk Verifikasi Manual

```sql
-- Cek semua assignments untuk user 49, sample_type='RoHS ICB'
SELECT 
  rjpa.id,
  rj.job_id,
  rps.step_order,
  rps.name as step_name,
  u.name as pic_name,
  rjpa.started_at,
  rjpa.finished_at,
  DATEDIFF(HOUR, rjpa.started_at, rjpa.finished_at) / 24.0 as days,
  rjpa.status
FROM rnd_job_progress_assignments rjpa
JOIN rnd_jobs rj ON rjpa.job_id = rj.id
JOIN rnd_progress_steps rps ON rjpa.progress_step_id = rps.id
JOIN users u ON rjpa.pic_id = u.id
WHERE rjpa.pic_id = 49
  AND rps.sample_type = 'RoHS ICB'  -- Filter by sample_type, bukan step name!
  AND rjpa.status = 'completed'
  AND YEAR(rjpa.finished_at) = 2026
  AND MONTH(rjpa.finished_at) = 1
ORDER BY rj.job_id, rps.step_order;
```

## Troubleshooting

| Masalah | Kemungkinan | Solusi |
|---------|------------|--------|
| Score berbeda dari sebelumnya | Sekarang menghitung ALL steps, bukan hanya 1 | ✅ Ini normal dan benar |
| Score RoHS ICB/Ribbon lebih tinggi | Multiple steps = lebih banyak waktu | ✅ Ini expected |
| Score = 0.00 | Tidak ada assignments completed | Cek: apakah ada assignments dengan status='completed'? |
| Skipped banyak | Assignments tidak lengkap | Cek: apakah started_at dan finished_at sudah di-set? |

