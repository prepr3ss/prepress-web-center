# Rencana & Dokumentasi Modul Tools 5W1H

## Ringkasan
- Modul baru: Tools → Form 5W1H
- Fitur: input, dashboard, detail, upload lampiran
- Blueprint: blueprints/tools_5w1h
- Permission: semua user bisa membuat, hanya pembuat & admin bisa edit
- Lampiran: disimpan di \\172.27.168.10\Data_Design\Impact\5w1h

## Data Model (FiveWOneH)
- id (int, PK)
- title (string, 255)
- who (text)
- what (text)
- when (datetime)
- where (text)
- why (text)
- how (text)
- owner_id (FK ke user)
- status (enum: draft/open/closed)
- attachment_path (string, optional)
- created_at (datetime)
- updated_at (datetime)

## Routes
- GET /tools/5w1h/new → Form input (input_5W1H.html)
- POST /tools/5w1h/new → Submit form
- GET /tools/5w1h/ → Dashboard (dashboard_5W1H.html)
- GET /tools/5w1h/<id> → Detail
- GET/POST /tools/5w1h/<id>/edit → Edit (hanya owner/admin)

## Template
- input_5W1H.html: form input lengkap, upload lampiran
- dashboard_5W1H.html: tabel, filter, link detail/edit

## Permission
- Semua user bisa create
- Edit hanya oleh owner atau admin

## Lampiran
- Disimpan di \\172.27.168.10\Data_Design\Impact\5w1h
- Nama file: <id>_<original_filename>
- Path disimpan di DB

## Struktur Folder
- blueprints/tools_5w1h/
  - __init__.py
  - models.py
  - routes.py
  - templates/tools_5w1h/
    - input_5W1H.html
    - dashboard_5W1H.html

## Catatan
- Integrasi menu utama: Tools → Form 5W1H
- Tes: model, route, permission, upload
- Dokumentasi ini akan diupdate sesuai progres implementasi.
