# Implementasi Warna pada Tabel CMYK di Detail KPI CTP

## Tujuan
Menambahkan warna pada background table header dan table row untuk CMYK Colors di Detail KPI CTP pada tab Data Warna dengan opacity 40% agar tidak terlalu menutup tulisan atau valuenya.

## Analisis Struktur
Berdasarkan analisis file `templates/tabelkpictp.html`, struktur tabel CMYK Colors terletak pada:
- Tabel ID: `cmykTableDetail`
- Lokasi: Baris 1005-1066
- Header: Baris 1007-1013
- Body: Baris 1015-1065

## Warna Referensi
Dari file `templates/kpictp.html`, warna referensi untuk setiap warna CMYK:
- Cyan: `linear-gradient(135deg, #00bfff 0%, #0099dd 100%)`
- Magenta: `linear-gradient(135deg, #ff00a6 0%, #dd0088 100%)`
- Yellow: `linear-gradient(135deg, #ffe600 0%, #ffc107 100%)`
- Black: `linear-gradient(135deg, #333 0%, #000 100%)`

## Implementasi CSS
CSS akan ditambahkan pada bagian `<style>` di file `templates/tabelkpictp.html` setelah baris 630.

### CSS untuk Header
```css
/* CMYK Color Table Header Styling */
#cmykTableDetail thead th:nth-child(2) {
    background: linear-gradient(135deg, #00bfff 0%, #0099dd 100%);
    color: white;
    font-weight: 600;
}

#cmykTableDetail thead th:nth-child(3) {
    background: linear-gradient(135deg, #ff00a6 0%, #dd0088 100%);
    color: white;
    font-weight: 600;
}

#cmykTableDetail thead th:nth-child(4) {
    background: linear-gradient(135deg, #ffe600 0%, #ffc107 100%);
    color: #333;
    font-weight: 600;
}

#cmykTableDetail thead th:nth-child(5) {
    background: linear-gradient(135deg, #333 0%, #000 100%);
    color: white;
    font-weight: 600;
}
```

### CSS untuk Row dengan Opacity 40%
```css
/* CMYK Table Row Styling with 40% opacity */
#cmykTableDetail tbody td:nth-child(2) {
    background-color: rgba(0, 191, 255, 0.4); /* Cyan with 40% opacity */
}

#cmykTableDetail tbody td:nth-child(3) {
    background-color: rgba(255, 0, 166, 0.4); /* Magenta with 40% opacity */
}

#cmykTableDetail tbody td:nth-child(4) {
    background-color: rgba(255, 230, 0, 0.4); /* Yellow with 40% opacity */
}

#cmykTableDetail tbody td:nth-child(5) {
    background-color: rgba(51, 51, 51, 0.4); /* Black with 40% opacity */
}
```

## Langkah Implementasi
1. Buka file `templates/tabelkpictp.html`
2. Temukan bagian `<style>` di dalam file
3. Tambahkan CSS untuk header dan row CMYK setelah baris 630
4. Simpan perubahan
5. Uji implementasi untuk memastikan warna tidak mengganggu keterbacaan teks

## Hasil yang Diharapkan
- Header tabel CMYK akan memiliki warna sesuai dengan warna masing-masing (Cyan, Magenta, Yellow, Black)
- Row tabel CMYK akan memiliki warna background dengan opacity 40% agar tidak mengganggu keterbacaan teks
- Tampilan akan lebih menarik dan informatif dengan warna yang sesuai untuk setiap kolom warna

## Testing
Setelah implementasi, lakukan testing untuk:
1. Memastikan warna header sesuai dengan yang diharapkan
2. Memastikan opacity 40% pada row tidak mengganggu keterbacaan teks
3. Memastikan tampilan tetap responsif di berbagai ukuran layar
4. Memastikan tidak ada konflik dengan CSS yang sudah ada