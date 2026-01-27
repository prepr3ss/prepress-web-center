# RND WebCenter - Implementation Guide

## Overview

RND WebCenter adalah modul file explorer yang memungkinkan pengguna untuk mengakses dan melihat isi dari network drive `\\172.27.168.10\PT. Epson\00.DATA BASE EPSON` melalui aplikasi Impact. Modul ini dirancang dengan antarmuka yang modern, clean, dan minimalis.

## Features

### Core Features
- **Network Drive Access**: Akses read-only ke network drive Epson
- **File Explorer Interface**: Antarmuka file explorer dengan dua mode tampilan (Grid dan List)
- **Search Functionality**: Pencarian file dan folder dalam network drive
- **File Type Icons**: Ikon khusus untuk berbagai jenis file (PDF, Excel, Image, dll.)
- **Breadcrumb Navigation**: Navigasi breadcrumb untuk kemudahan navigasi folder
- **File Information Modal**: Modal informasi detail untuk setiap file
- **Connection Status Check**: Pemeriksaan status koneksi ke network drive
- **Responsive Design**: Desain yang responsif untuk berbagai ukuran layar

### Security Features
- **Read-Only Access**: Akses hanya baca untuk mencegah modifikasi file yang tidak disengaja
- **Path Traversal Protection**: Perlindungan terhadap serangan path traversal
- **Access Control**: Hanya pengguna dengan akses RND yang dapat mengakses

## Architecture

### Backend Components

#### 1. Blueprint Structure
```
rnd_webcenter/
├── __init__.py          # Blueprint initialization
├── services.py          # Business logic and services
├── routes.py           # API endpoints
└── utils.py            # Utility functions
```

#### 2. Services Layer
- **NetworkDriveService**: Mengelola akses ke network drive
- **FileExplorerService**: Mengelola operasi file explorer
- **Caching**: Implementasi cache untuk performa

#### 3. API Endpoints
- `GET /rnd-webcenter/` - Halaman utama file explorer
- `GET /rnd-webcenter/api/directory` - API untuk listing direktori
- `GET /rnd-webcenter/api/search` - API untuk pencarian file
- `GET /rnd-webcenter/api/file-info` - API untuk informasi file
- `GET /rnd-webcenter/api/accessibility` - API untuk cek koneksi

### Frontend Components

#### 1. Template Structure
```
templates/rnd_webcenter/
└── file_explorer.html   # Main file explorer interface
```

#### 2. Static Assets
```
static/
├── js/rnd_webcenter.js    # JavaScript module
└── css/rnd_webcenter.css   # Stylesheet
```

#### 3. JavaScript Classes
- **RNDWebCenter**: Main class untuk mengelola file explorer
- Methods untuk navigasi, pencarian, dan rendering file

## Installation & Setup

### 1. Prerequisites
- Python 3.7+
- Flask application framework
- Access to network drive `\\172.27.168.10\PT. Epson\00.DATA BASE EPSON`

### 2. File Structure
Create the following directory structure:

```
impact/
├── rnd_webcenter/
│   ├── __init__.py
│   ├── services.py
│   ├── routes.py
│   └── utils.py
├── templates/rnd_webcenter/
│   └── file_explorer.html
├── static/js/
│   └── rnd_webcenter.js
└── static/css/
    └── rnd_webcenter.css
```

### 3. Integration Steps

#### Step 1: Add Blueprint Import
In `app.py`, add the import:
```python
from rnd_webcenter import rnd_webcenter_bp
```

#### Step 2: Register Blueprint
In `app.py`, register the blueprint:
```python
app.register_blueprint(rnd_webcenter_bp)
```

#### Step 3: Add Menu Item
In `templates/_sidebar.html`, add the menu item under R&D submenu:
```html
<a href="/impact/rnd-webcenter" class="list-group-item list-group-item-action ps-5" id="rndWebcenterLink">
    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">
        <!-- SVG icon content -->
    </svg>
    <span>WebCenter</span>
</a>
```

## Configuration

### Network Drive Path
The network drive path is configured in `rnd_webcenter/services.py`:
```python
class NetworkDriveService:
    def __init__(self, base_path=r"\\172.27.168.10\PT. Epson\00.DATA BASE EPSON"):
        self.base_path = base_path
```

### Cache Configuration
Cache timeout is set to 5 minutes (300 seconds) for optimal performance:
```python
CACHE_TIMEOUT = 300  # 5 minutes
```

## Usage Guide

### Accessing RND WebCenter
1. Login to Impact application
2. Navigate to R&D menu in sidebar
3. Click on "WebCenter" submenu

### Navigating Files
- **Grid View**: Click on folder icons to navigate
- **List View**: Click on file/folder names to navigate
- **Breadcrumb**: Use breadcrumb navigation for quick folder access
- **Search**: Use search bar to find specific files

### File Operations
- **View File Info**: Right-click on file or click info button
- **Search Files**: Enter search term and click Search button
- **Refresh**: Click Refresh button to reload current directory
- **Check Connection**: Click Check Connection button to verify network drive access

## Troubleshooting

### Common Issues

#### 1. Network Drive Not Accessible
**Symptoms**: Connection status shows "Network drive is not accessible"
**Solutions**:
- Verify network connection to `\\172.27.168.10`
- Check if the network drive is mounted and accessible
- Verify user permissions on the network drive

#### 2. Empty Directory Display
**Symptoms**: No files shown in directory
**Solutions**:
- Check if directory actually contains files
- Verify path traversal protection is not blocking access
- Check network drive permissions

#### 3. Search Not Working
**Symptoms**: Search returns no results
**Solutions**:
- Verify search term is spelled correctly
- Check if files exist in current directory
- Verify file permissions

### Debug Mode
Enable debug mode by adding logging:
```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

## Performance Considerations

### Caching Strategy
- Directory listings are cached for 5 minutes
- Search results are not cached
- File information is cached per request

### Optimization Tips
- Use specific search terms for faster results
- Avoid deep directory navigation when possible
- Clear cache periodically if network drive content changes frequently

## Security Considerations

### Path Traversal Protection
The system implements strict path validation:
```python
def sanitize_path(path):
    # Remove relative path components
    # Validate against base path
    # Prevent directory traversal attacks
```

### Access Control
- Only users with RND access can use the module
- Read-only access prevents file modifications
- Session-based authentication required

## Future Enhancements

### Planned Features
1. **File Preview**: Preview functionality for common file types
2. **Download Capability**: Option to download files (if approved)
3. **Advanced Search**: Search by file type, date, size
4. **Favorites**: Bookmark frequently accessed folders
5. **File Operations**: Copy/move operations (if approved)

### Performance Improvements
1. **Lazy Loading**: Implement lazy loading for large directories
2. **Background Caching**: Pre-cache frequently accessed directories
3. **Compression**: Compress API responses for faster loading

## Support & Maintenance

### Monitoring
- Monitor network drive connectivity
- Track API response times
- Log access attempts and errors

### Maintenance Tasks
- Regular cache clearing
- Network drive connectivity checks
- User access permission reviews

## Conclusion

RND WebCenter provides a secure and efficient way to access network drive files through the Impact application. The modular architecture allows for easy maintenance and future enhancements while maintaining security and performance standards.

For technical support or questions, please contact the development team.