# RND WebCenter Implementation Plan

## Overview

Dokumen ini merinci rencana implementasi untuk modul RND WebCenter yang akan menyediakan antarmuka file explorer modern untuk mengakses network drive `\\172.27.168.10\PT. Epson\00.DATA BASE EPSON`.

## File Structure

```
rnd_webcenter/
├── __init__.py              # Blueprint initialization
├── routes.py                # Flask routes
├── services.py              # Business logic
├── utils.py                 # Helper functions
├── static/
│   ├── css/
│   │   └── rnd_webcenter.css
│   └── js/
│       └── rnd_webcenter.js
└── templates/
    └── rnd_webcenter/
        ├── file_explorer.html
        └── components/
            ├── breadcrumb.html
            ├── file_grid.html
            └── search_bar.html
```

## Implementation Details

### 1. Blueprint Initialization (`__init__.py`)

```python
from flask import Blueprint

# Create Blueprint for RND WebCenter
rnd_webcenter_bp = Blueprint('rnd_webcenter', __name__, 
                          url_prefix='/rnd-webcenter',
                          template_folder='templates',
                          static_folder='static')

# Import routes to register them with the blueprint
from . import routes
```

### 2. Network Drive Service (`services.py`)

```python
import os
import time
from pathlib import Path
from typing import List, Dict, Optional, Tuple

class NetworkDriveService:
    """Service for accessing network drive files"""
    
    def __init__(self):
        self.base_path = r"\\172.27.168.10\PT. Epson\00.DATA BASE EPSON"
        self.cache = {}
        self.cache_timeout = 300  # 5 minutes
    
    def is_accessible(self) -> bool:
        """Check if network drive is accessible"""
        try:
            os.listdir(self.base_path)
            return True
        except (OSError, PermissionError):
            return False
    
    def list_directory(self, relative_path: str = "") -> List[Dict]:
        """List files and directories in specified path"""
        # Implementation with caching and error handling
        pass
    
    def get_file_info(self, relative_path: str) -> Optional[Dict]:
        """Get detailed file information"""
        # Implementation with file metadata
        pass
    
    def search_files(self, query: str, relative_path: str = "") -> List[Dict]:
        """Search files by name"""
        # Implementation with recursive search
        pass

class FileExplorerService:
    """Service for file explorer operations"""
    
    def __init__(self):
        self.network_service = NetworkDriveService()
    
    def get_directory_contents(self, path: str) -> Dict:
        """Get directory contents with metadata"""
        # Implementation with sorting and pagination
        pass
    
    def navigate_to_path(self, path: str) -> Dict:
        """Navigate to specific path"""
        # Implementation with validation
        pass
```

### 3. Route Handlers (`routes.py`)

```python
from flask import render_template, jsonify, request, current_app
from flask_login import login_required
from . import rnd_webcenter_bp
from .services import FileExplorerService
from .utils import get_file_icon, format_file_size, sanitize_path

# Initialize services
file_explorer_service = FileExplorerService()

@rnd_webcenter_bp.route('/')
@login_required
def file_explorer():
    """Main file explorer page"""
    return render_template('rnd_webcenter/file_explorer.html')

@rnd_webcenter_bp.route('/api/directory')
@login_required
def api_directory():
    """API endpoint for directory listing"""
    path = request.args.get('path', '')
    
    try:
        contents = file_explorer_service.get_directory_contents(path)
        return jsonify({
            'success': True,
            'data': contents
        })
    except Exception as e:
        current_app.logger.error(f"Error accessing directory: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@rnd_webcenter_bp.route('/api/search')
@login_required
def api_search():
    """API endpoint for file search"""
    query = request.args.get('q', '').strip()
    path = request.args.get('path', '')
    
    if not query:
        return jsonify({
            'success': False,
            'error': 'Search query is required'
        }), 400
    
    try:
        results = file_explorer_service.search_files(query, path)
        return jsonify({
            'success': True,
            'data': results
        })
    except Exception as e:
        current_app.logger.error(f"Error searching files: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500
```

### 4. Utility Functions (`utils.py`)

```python
import os
from pathlib import Path
from typing import Dict

def sanitize_path(path: str) -> str:
    """Sanitize path to prevent directory traversal"""
    # Remove any attempt to go up directories
    path = path.replace('..', '').replace('~', '')
    # Normalize path separators
    path = path.replace('/', '\\')
    # Remove leading/trailing separators
    path = path.strip('\\')
    return path

def get_file_icon(filename: str) -> str:
    """Get appropriate icon for file type"""
    ext = Path(filename).suffix.lower()
    
    icon_mapping = {
        '.pdf': 'fas fa-file-pdf',
        '.doc': 'fas fa-file-word',
        '.docx': 'fas fa-file-word',
        '.xls': 'fas fa-file-excel',
        '.xlsx': 'fas fa-file-excel',
        '.jpg': 'fas fa-file-image',
        '.jpeg': 'fas fa-file-image',
        '.png': 'fas fa-file-image',
        '.gif': 'fas fa-file-image',
        '.zip': 'fas fa-file-archive',
        '.rar': 'fas fa-file-archive',
        '.7z': 'fas fa-file-archive',
    }
    
    return icon_mapping.get(ext, 'fas fa-file')

def format_file_size(size_bytes: int) -> str:
    """Format file size in human readable format"""
    if size_bytes == 0:
        return "0 B"
    
    size_names = ["B", "KB", "MB", "GB", "TB"]
    i = 0
    size = float(size_bytes)
    
    while size >= 1024.0 and i < len(size_names) - 1:
        size /= 1024.0
        i += 1
    
    return f"{size:.1f} {size_names[i]}"

def is_valid_path(path: str, base_path: str) -> bool:
    """Validate that path is within allowed directory"""
    try:
        full_path = os.path.join(base_path, path)
        return os.path.commonpath([base_path]) == os.path.commonpath([base_path, full_path])
    except:
        return False
```

### 5. Frontend Template (`templates/rnd_webcenter/file_explorer.html`)

```html
<!DOCTYPE html>
<html lang="id">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>RND WebCenter - File Explorer</title>
    
    <!-- Bootstrap 5 CSS -->
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    <!-- Font Awesome -->
    <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css" rel="stylesheet">
    <!-- Custom CSS -->
    <link href="{{ url_for('rnd_webcenter.static', filename='css/rnd_webcenter.css') }}" rel="stylesheet">
</head>
<body>
    <div class="container-fluid vh-100 d-flex flex-column">
        <!-- Header -->
        <header class="bg-white shadow-sm border-bottom">
            <div class="container-fluid px-4 py-3">
                <div class="row align-items-center">
                    <div class="col">
                        <h4 class="mb-0">
                            <i class="fas fa-folder-open text-primary me-2"></i>
                            RND WebCenter
                        </h4>
                    </div>
                    <div class="col-auto">
                        <div class="input-group">
                            <input type="text" class="form-control" id="searchInput" placeholder="Cari file...">
                            <button class="btn btn-outline-primary" type="button" id="searchBtn">
                                <i class="fas fa-search"></i>
                            </button>
                        </div>
                    </div>
                </div>
            </div>
        </header>
        
        <!-- Breadcrumb Navigation -->
        <nav class="bg-light py-2 px-4">
            <ol class="breadcrumb mb-0" id="breadcrumb">
                <!-- Breadcrumb items will be populated by JavaScript -->
            </ol>
        </nav>
        
        <!-- Main Content -->
        <main class="flex-grow-1 overflow-auto">
            <div class="container-fluid px-4 py-3">
                <!-- Toolbar -->
                <div class="d-flex justify-content-between align-items-center mb-3">
                    <div class="btn-group" role="group">
                        <button type="button" class="btn btn-outline-secondary active" id="gridViewBtn">
                            <i class="fas fa-th"></i>
                        </button>
                        <button type="button" class="btn btn-outline-secondary" id="listViewBtn">
                            <i class="fas fa-list"></i>
                        </button>
                    </div>
                    <div class="text-muted" id="statusInfo">
                        <!-- Status information will be populated by JavaScript -->
                    </div>
                </div>
                
                <!-- File Explorer Grid -->
                <div class="row g-3" id="fileGrid">
                    <!-- Files and folders will be populated by JavaScript -->
                </div>
                
                <!-- Loading Indicator -->
                <div class="text-center py-5 d-none" id="loadingIndicator">
                    <div class="spinner-border text-primary" role="status">
                        <span class="visually-hidden">Loading...</span>
                    </div>
                </div>
                
                <!-- Error Message -->
                <div class="alert alert-danger d-none" id="errorMessage">
                    <!-- Error messages will be displayed here -->
                </div>
            </div>
        </main>
    </div>
    
    <!-- Bootstrap JS -->
    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js"></script>
    <!-- Custom JS -->
    <script src="{{ url_for('rnd_webcenter.static', filename='js/rnd_webcenter.js') }}"></script>
</body>
</html>
```

### 6. JavaScript Module (`static/js/rnd_webcenter.js`)

```javascript
class RNDWebCenter {
    constructor() {
        this.currentPath = '';
        this.viewMode = 'grid'; // 'grid' or 'list'
        this.init();
    }
    
    init() {
        this.setupEventListeners();
        this.loadDirectory('');
    }
    
    setupEventListeners() {
        // Search functionality
        document.getElementById('searchBtn').addEventListener('click', () => this.search());
        document.getElementById('searchInput').addEventListener('keypress', (e) => {
            if (e.key === 'Enter') this.search();
        });
        
        // View mode toggle
        document.getElementById('gridViewBtn').addEventListener('click', () => this.setViewMode('grid'));
        document.getElementById('listViewBtn').addEventListener('click', () => this.setViewMode('list'));
    }
    
    async loadDirectory(path) {
        this.showLoading(true);
        this.currentPath = path;
        
        try {
            const response = await fetch(`/impact/rnd-webcenter/api/directory?path=${encodeURIComponent(path)}`);
            const data = await response.json();
            
            if (data.success) {
                this.renderFiles(data.data);
                this.updateBreadcrumb(path);
                this.updateStatus(data.data);
            } else {
                this.showError(data.error || 'Failed to load directory');
            }
        } catch (error) {
            this.showError('Network error occurred');
        } finally {
            this.showLoading(false);
        }
    }
    
    async search() {
        const query = document.getElementById('searchInput').value.trim();
        if (!query) return;
        
        this.showLoading(true);
        
        try {
            const response = await fetch(`/impact/rnd-webcenter/api/search?q=${encodeURIComponent(query)}&path=${encodeURIComponent(this.currentPath)}`);
            const data = await response.json();
            
            if (data.success) {
                this.renderFiles(data.data);
                this.updateStatus(data.data);
            } else {
                this.showError(data.error || 'Search failed');
            }
        } catch (error) {
            this.showError('Network error occurred');
        } finally {
            this.showLoading(false);
        }
    }
    
    renderFiles(files) {
        const grid = document.getElementById('fileGrid');
        grid.innerHTML = '';
        
        if (files.length === 0) {
            grid.innerHTML = '<div class="col-12 text-center text-muted py-5">No files found</div>';
            return;
        }
        
        files.forEach(file => {
            const fileElement = this.createFileElement(file);
            grid.appendChild(fileElement);
        });
    }
    
    createFileElement(file) {
        const col = document.createElement('div');
        col.className = this.viewMode === 'grid' ? 'col-md-2 col-sm-3 col-6' : 'col-12';
        
        const card = document.createElement('div');
        card.className = 'card file-card h-100';
        
        const cardBody = document.createElement('div');
        cardBody.className = 'card-body d-flex flex-column align-items-center text-center';
        
        const icon = document.createElement('div');
        icon.className = `file-icon ${file.isDirectory ? 'folder' : 'file'} ${file.type}`;
        icon.innerHTML = `<i class="${file.icon}"></i>`;
        
        const name = document.createElement('div');
        name.className = 'file-name text-truncate';
        name.title = file.name;
        name.textContent = file.name;
        
        const size = document.createElement('div');
        size.className = 'file-size text-muted small';
        size.textContent = file.isDirectory ? '' : file.sizeFormatted;
        
        cardBody.appendChild(icon);
        cardBody.appendChild(name);
        cardBody.appendChild(size);
        card.appendChild(cardBody);
        col.appendChild(card);
        
        if (file.isDirectory) {
            card.style.cursor = 'pointer';
            card.addEventListener('click', () => this.navigateToDirectory(file.path));
        }
        
        return col;
    }
    
    navigateToDirectory(path) {
        this.loadDirectory(path);
    }
    
    updateBreadcrumb(path) {
        const breadcrumb = document.getElementById('breadcrumb');
        breadcrumb.innerHTML = '';
        
        // Add home
        const homeItem = this.createBreadcrumbItem('Home', '', path === '');
        breadcrumb.appendChild(homeItem);
        
        if (path) {
            const parts = path.split('\\');
            let currentPath = '';
            
            parts.forEach((part, index) => {
                currentPath = currentPath ? `${currentPath}\\${part}` : part;
                const isLast = index === parts.length - 1;
                
                const item = this.createBreadcrumbItem(
                    part, 
                    currentPath, 
                    isLast
                );
                breadcrumb.appendChild(item);
            });
        }
    }
    
    createBreadcrumbItem(name, path, isActive) {
        const li = document.createElement('li');
        li.className = `breadcrumb-item ${isActive ? 'active' : ''}`;
        
        if (!isActive) {
            const a = document.createElement('a');
            a.href = '#';
            a.textContent = name;
            a.addEventListener('click', (e) => {
                e.preventDefault();
                this.navigateToDirectory(path);
            });
            li.appendChild(a);
        } else {
            li.textContent = name;
        }
        
        return li;
    }
    
    updateStatus(files) {
        const statusInfo = document.getElementById('statusInfo');
        const folders = files.filter(f => f.isDirectory).length;
        const fileCount = files.filter(f => !f.isDirectory).length;
        
        statusInfo.textContent = `${folders} folder${folders !== 1 ? 's' : ''}, ${fileCount} file${fileCount !== 1 ? 's' : ''}`;
    }
    
    setViewMode(mode) {
        this.viewMode = mode;
        
        // Update button states
        document.getElementById('gridViewBtn').classList.toggle('active', mode === 'grid');
        document.getElementById('listViewBtn').classList.toggle('active', mode === 'list');
        
        // Reload current directory
        this.loadDirectory(this.currentPath);
    }
    
    showLoading(show) {
        const loadingIndicator = document.getElementById('loadingIndicator');
        const fileGrid = document.getElementById('fileGrid');
        
        if (show) {
            loadingIndicator.classList.remove('d-none');
            fileGrid.classList.add('d-none');
        } else {
            loadingIndicator.classList.add('d-none');
            fileGrid.classList.remove('d-none');
        }
    }
    
    showError(message) {
        const errorMessage = document.getElementById('errorMessage');
        errorMessage.textContent = message;
        errorMessage.classList.remove('d-none');
        
        // Auto-hide after 5 seconds
        setTimeout(() => {
            errorMessage.classList.add('d-none');
        }, 5000);
    }
}

// Initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    new RNDWebCenter();
});
```

### 7. CSS Stylesheet (`static/css/rnd_webcenter.css`)

```css
:root {
    --primary-color: #0d6efd;
    --secondary-color: #6c757d;
    --success-color: #198754;
    --danger-color: #dc3545;
    --warning-color: #ffc107;
    --info-color: #0dcaf0;
    --light-color: #f8f9fa;
    --dark-color: #212529;
    --border-radius: 0.375rem;
    --box-shadow: 0 0.125rem 0.25rem rgba(0, 0, 0, 0.075);
}

body {
    font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
    background-color: #f8f9fa;
}

.file-card {
    border: 1px solid rgba(0, 0, 0, 0.125);
    border-radius: var(--border-radius);
    transition: all 0.15s ease-in-out;
    cursor: default;
}

.file-card:hover {
    transform: translateY(-2px);
    box-shadow: var(--box-shadow);
    border-color: var(--primary-color);
}

.file-icon {
    font-size: 2.5rem;
    margin-bottom: 0.5rem;
    color: var(--secondary-color);
}

.file-icon.folder {
    color: #ffc107;
}

.file-icon.file.pdf {
    color: #dc3545;
}

.file-icon.file.doc,
.file-icon.file.docx {
    color: #0d6efd;
}

.file-icon.file.xls,
.file-icon.file.xlsx {
    color: #198754;
}

.file-icon.file.jpg,
.file-icon.file.jpeg,
.file-icon.file.png,
.file-icon.file.gif {
    color: #fd7e14;
}

.file-name {
    font-weight: 500;
    font-size: 0.875rem;
    width: 100%;
    margin-bottom: 0.25rem;
}

.file-size {
    font-size: 0.75rem;
}

.breadcrumb-item + .breadcrumb-item::before {
    content: ">";
    color: var(--secondary-color);
}

.breadcrumb-item a {
    text-decoration: none;
    color: var(--primary-color);
}

.breadcrumb-item a:hover {
    text-decoration: underline;
}

#loadingIndicator {
    position: fixed;
    top: 50%;
    left: 50%;
    transform: translate(-50%, -50%);
    z-index: 1050;
    background-color: rgba(255, 255, 255, 0.8);
    border-radius: var(--border-radius);
    padding: 2rem;
}

#errorMessage {
    position: fixed;
    top: 20px;
    right: 20px;
    z-index: 1050;
    max-width: 300px;
}

/* Responsive adjustments */
@media (max-width: 768px) {
    .file-icon {
        font-size: 2rem;
    }
    
    .file-name {
        font-size: 0.75rem;
    }
}
```

## Integration Steps

### 1. Application Registration

Update `app.py` to register the new blueprint:

```python
# Add import
from rnd_webcenter import rnd_webcenter_bp

# Register blueprint
app.register_blueprint(rnd_webcenter_bp)
```

### 2. Menu Integration

Update `templates/_sidebar.html` to add the new menu item in RND Production section:

```html
<!-- Add after existing RND menu items -->
<a href="/impact/rnd-webcenter" class="list-group-item list-group-item-action ps-5" id="rndWebcenterLink">
    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">
        <path d="M22 19a2 2 0 0 1-2 2H4a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h5l2 3h9a2 2 0 0 1 2 2v14z"/>
        <polyline points="16,1 12,6 8,1"/>
    </svg>
    <span>WebCenter</span>
</a>
```

## Testing Plan

### 1. Unit Testing
- Test network drive connectivity
- Test file listing functionality
- Test search functionality
- Test error handling

### 2. Integration Testing
- Test blueprint registration
- Test menu integration
- Test authentication flow

### 3. User Acceptance Testing
- Test with different file types
- Test with large directories
- Test search performance
- Test responsive design

## Deployment Considerations

### 1. Network Drive Access
- Ensure application server has access to network drive
- Test connectivity from deployment environment
- Handle network timeouts gracefully

### 2. Performance Optimization
- Implement caching for directory listings
- Optimize search for large directories
- Consider pagination for very large directories

### 3. Security
- Validate all user inputs
- Prevent path traversal attacks
- Log access attempts

## Conclusion

RND WebCenter akan menyediakan solusi file explorer yang modern dan efisien untuk mengakses network drive Epson. Dengan arsitektur yang modular dan implementasi yang terstruktur, modul ini dapat dikembangkan lebih lanjut sambil tetap mempertahankan integritas aplikasi Impact yang ada.