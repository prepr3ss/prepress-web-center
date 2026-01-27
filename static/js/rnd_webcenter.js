/**
 * RND WebCenter - File Explorer JavaScript Module
 * Handles frontend interactions for the file explorer interface
 */

class RNDWebCenter {
    constructor() {
        this.currentPath = '';
        this.viewMode = localStorage.getItem('rndWebCenterViewMode') || 'grid'; // 'grid' or 'list'
        this.searchQuery = '';
        this.isLoading = false;
        
        // Initialize the application
        this.init();
    }

    /**
     * Initialize the application
     */
    init() {
        this.bindEvents();
        this.initializeSearch();
        this.checkAccessibility();
        this.loadDirectory('');
    }

    /**
     * Bind event listeners
     */
    bindEvents() {
        // Helper function to safely add event listeners
        const addListener = (id, event, handler) => {
            const element = document.getElementById(id);
            if (element) {
                element.addEventListener(event, handler);
            }
        };

        // Refresh button
        addListener('refreshBtn', 'click', () => {
            this.refreshCurrentDirectory();
        });

        // Accessibility button
        addListener('accessibilityBtn', 'click', () => {
            this.checkAccessibility();
        });

        // Path configuration modal
        addListener('testPathBtn', 'click', () => {
            this.testCustomPath();
        });

        addListener('applyPathBtn', 'click', () => {
            this.applyCustomPath();
        });
        
        // Initialize custom path when modal is shown
        const pathConfigModal = document.getElementById('pathConfigModal');
        if (pathConfigModal) {
            pathConfigModal.addEventListener('show.bs.modal', () => {
                this.initializeCustomPath();
            });
        }

        // Search functionality
        addListener('searchBtn', 'click', () => {
            this.performSearch();
        });

        addListener('clearSearchBtn', 'click', () => {
            this.clearSearch();
        });

        addListener('searchInput', 'keypress', (e) => {
            if (e.key === 'Enter') {
                this.performSearch();
            }
        });

        // View mode toggle
        addListener('gridView', 'change', () => {
            this.setViewMode('grid');
        });

        addListener('listView', 'change', () => {
            this.setViewMode('list');
        });
        
        // Set initial view mode
        this.updateViewModeUI();

        // Retry button in error state
        addListener('retryBtn', 'click', () => {
            this.refreshCurrentDirectory();
        });
    }

    /**
     * Check if network drive is accessible
     */
    async checkAccessibility() {
        try {
            this.showConnectionStatus('Checking connection...', 'info');
            
            const response = await fetch('/impact/rnd-webcenter/api/accessibility');
            const data = await response.json();
            
            if (data.success) {
                if (data.data.accessible) {
                    this.showConnectionStatus('Connected to network drive', 'success');
                } else {
                    this.showConnectionStatus('Network drive is not accessible', 'warning');
                }
            } else {
                this.showConnectionStatus('Failed to check connection', 'danger');
            }
        } catch (error) {
            console.error('Error checking accessibility:', error);
            this.showConnectionStatus('Error checking connection', 'danger');
        }
    }

    /**
     * Load directory contents
     */
    async loadDirectory(path) {
        if (this.isLoading) return;
        
        this.isLoading = true;
        this.showLoadingState();
        
        try {
            const response = await fetch(`/impact/rnd-webcenter/api/directory?path=${encodeURIComponent(path)}`);
            const data = await response.json();
            
            if (data.success) {
                this.currentPath = path;
                this.updateBreadcrumb(path);
                this.renderFiles(data.data.items || []);
                this.showFileContainer();
            } else {
                this.showErrorState(data.error || 'Failed to load directory');
            }
        } catch (error) {
            console.error('Error loading directory:', error);
            this.showErrorState('Network error occurred while loading directory');
        } finally {
            this.isLoading = false;
        }
    }

    /**
     * Perform search
     */
    async performSearch() {
        const searchInput = document.getElementById('searchInput');
        this.searchQuery = searchInput.value.trim();
        
        if (!this.searchQuery) {
            this.clearSearch();
            return;
        }
        
        if (this.isLoading) return;
        
        this.isLoading = true;
        this.showLoadingState();
        
        try {
            const response = await fetch(`/impact/rnd-webcenter/api/search?q=${encodeURIComponent(this.searchQuery)}&path=${encodeURIComponent(this.currentPath)}`);
            const data = await response.json();
            
            if (data.success) {
                this.renderSearchResults(data.data.items || [], this.searchQuery);
                this.showFileContainer();
            } else {
                this.showErrorState(data.error || 'Search failed');
            }
        } catch (error) {
            console.error('Error performing search:', error);
            this.showErrorState('Network error occurred while searching');
        } finally {
            this.isLoading = false;
        }
    }

    /**
     * Clear search and return to normal view
     */
    clearSearch() {
        const searchInput = document.getElementById('searchInput');
        if (searchInput) {
            searchInput.value = '';
        }
        this.searchQuery = '';
        this.loadDirectory(this.currentPath);
    }

    /**
     * Initialize search functionality
     */
    initializeSearch() {
        // Set initial placeholder
        this.updateSearchPlaceholder(this.currentPath);
        
        // Add real-time search with debounce
        let searchTimeout;
        const searchInput = document.getElementById('searchInput');
        if (searchInput) {
            searchInput.addEventListener('input', (e) => {
                clearTimeout(searchTimeout);
                const query = e.target.value.trim();
                
                if (query.length === 0) {
                    this.clearSearch();
                    return;
                }
                
                // Debounce search to avoid too many requests
                searchTimeout = setTimeout(() => {
                    if (query.length >= 2) { // Only search if at least 2 characters
                        this.performSearch();
                    }
                }, 300);
            });
        }
    }

    /**
     * Refresh current directory
     */
    refreshCurrentDirectory() {
        if (this.searchQuery) {
            this.performSearch();
        } else {
            this.loadDirectory(this.currentPath);
        }
    }

    /**
     * Set view mode (grid or list)
     */
    setViewMode(mode) {
        this.viewMode = mode;
        localStorage.setItem('rndWebCenterViewMode', mode);
        this.updateViewModeUI();
        this.refreshCurrentDirectory();
    }
    
    /**
     * Update view mode UI elements
     */
    updateViewModeUI() {
        const gridViewRadio = document.getElementById('gridView');
        const listViewRadio = document.getElementById('listView');
        
        if (this.viewMode === 'grid') {
            gridViewRadio.checked = true;
            listViewRadio.checked = false;
        } else {
            gridViewRadio.checked = false;
            listViewRadio.checked = true;
        }
    }

    /**
     * Update breadcrumb navigation
     */
    updateBreadcrumb(path) {
        const breadcrumb = document.getElementById('breadcrumb');
        breadcrumb.innerHTML = '';
        
        // Add root
        const rootItem = document.createElement('li');
        rootItem.className = 'breadcrumb-item';
        rootItem.innerHTML = '<a href="#" class="directory-link" data-path="">Network Drive</a>';
        breadcrumb.appendChild(rootItem);
        
        if (path) {
            // Convert backslashes to forward slashes for consistency
            const normalizedPath = path.replace(/\\/g, '/');
            const pathParts = normalizedPath.split('/');
            let currentPath = '';
            
            pathParts.forEach((part, index) => {
                currentPath = currentPath ? `${currentPath}/${part}` : part;
                
                const item = document.createElement('li');
                item.className = 'breadcrumb-item';
                
                if (index === pathParts.length - 1) {
                    item.className += ' active';
                    item.textContent = part;
                } else {
                    item.innerHTML = `<a href="#" class="directory-link" data-path="${currentPath}">${part}</a>`;
                }
                
                breadcrumb.appendChild(item);
            });
        }
        
        // Update search placeholder based on current path
        this.updateSearchPlaceholder(path);
        
        // Add click handlers to breadcrumb links
        document.querySelectorAll('.directory-link').forEach(link => {
            link.addEventListener('click', (e) => {
                e.preventDefault();
                const path = e.target.getAttribute('data-path');
                this.loadDirectory(path);
            });
        });
    }

    /**
     * Update search placeholder based on current path
     */
    updateSearchPlaceholder(path) {
        const searchInput = document.getElementById('searchInput');
        if (searchInput) {
            if (path) {
                // Get the last folder name from path
                const pathParts = path.replace(/\\/g, '/').split('/');
                const currentFolder = pathParts[pathParts.length - 1] || 'root';
                searchInput.placeholder = `Search in "${currentFolder}"...`;
            } else {
                searchInput.placeholder = 'Search in Network Drive...';
            }
        }
    }

    /**
     * Render files in the container
     */
    renderFiles(files) {
        const container = document.getElementById('fileContainer');
        container.innerHTML = '';
        
        if (files.length === 0) {
            this.showEmptyState();
            return;
        }
        
        // Sort files: directories first, then files
        const sortedFiles = [...files].sort((a, b) => {
            if (a.isDirectory && !b.isDirectory) return -1;
            if (!a.isDirectory && b.isDirectory) return 1;
            return a.name.localeCompare(b.name, undefined, { sensitivity: 'base' });
        });
        
        if (this.viewMode === 'grid') {
            this.renderGridView(sortedFiles);
        } else {
            this.renderListView(sortedFiles);
        }
    }

    /**
     * Render search results
     */
    renderSearchResults(results, query) {
        const container = document.getElementById('fileContainer');
        container.innerHTML = '';
        
        if (results.length === 0) {
            this.showEmptyState();
            return;
        }
        
        // Add search results header
        const header = document.createElement('div');
        header.className = 'alert alert-info mb-3';
        header.innerHTML = `<i class="bi bi-search me-2"></i>Found ${results.length} result(s) for "${query}"`;
        container.appendChild(header);
        
        // Sort results
        const sortedResults = [...results].sort((a, b) => {
            if (a.isDirectory && !b.isDirectory) return -1;
            if (!a.isDirectory && b.isDirectory) return 1;
            return a.name.localeCompare(b.name, undefined, { sensitivity: 'base' });
        });
        
        if (this.viewMode === 'grid') {
            this.renderGridView(sortedResults);
        } else {
            this.renderListView(sortedResults);
        }
    }

    /**
     * Render grid view
     */
    renderGridView(files) {
        const container = document.getElementById('fileContainer');
        const gridContainer = document.createElement('div');
        gridContainer.className = 'row g-3';
        
        files.forEach(file => {
            const fileCard = this.createFileCard(file);
            gridContainer.appendChild(fileCard);
        });
        
        container.appendChild(gridContainer);
    }

    /**
     * Render list view
     */
    renderListView(files) {
        const container = document.getElementById('fileContainer');
        const listContainer = document.createElement('div');
        listContainer.className = 'table-responsive';
        
        const table = document.createElement('table');
        table.className = 'table table-hover';
        
        const thead = document.createElement('thead');
        thead.innerHTML = `
            <tr>
                <th>Name</th>
                <th>Type</th>
                <th>Size</th>
                <th>Modified</th>
                <th>Actions</th>
            </tr>
        `;
        table.appendChild(thead);
        
        const tbody = document.createElement('tbody');
        files.forEach(file => {
            const row = this.createFileRow(file);
            tbody.appendChild(row);
        });
        table.appendChild(tbody);
        
        listContainer.appendChild(table);
        container.appendChild(listContainer);
    }

    /**
     * Create file card for grid view
     */
    createFileCard(file) {
        const col = document.createElement('div');
        col.className = 'col-md-3 col-sm-4 col-6';
        
        const card = document.createElement('div');
        card.className = 'card file-card h-100';
        card.dataset.path = file.path;
        
        const cardBody = document.createElement('div');
        cardBody.className = 'card-body text-center';
        
        const icon = document.createElement('div');
        icon.className = 'file-icon mb-2';
        icon.innerHTML = `<i class="bi ${file.icon} display-4"></i>`;
        
        const name = document.createElement('div');
        name.className = 'file-name text-truncate';
        name.title = file.name;
        name.textContent = file.name;
        
        cardBody.appendChild(icon);
        cardBody.appendChild(name);
        card.appendChild(cardBody);
        
        // Add click handler
        card.addEventListener('click', () => {
            this.handleFileClick(file);
        });
        
        // Add context menu for file info
        card.addEventListener('contextmenu', (e) => {
            e.preventDefault();
            this.showFileInfo(file);
        });
        
        col.appendChild(card);
        return col;
    }

    /**
     * Create file row for list view
     */
    createFileRow(file) {
        const row = document.createElement('tr');
        row.dataset.path = file.path;
        
        const nameCell = document.createElement('td');
        nameCell.innerHTML = `<i class="bi ${file.icon} me-2"></i>${file.name}`;
        
        const typeCell = document.createElement('td');
        typeCell.textContent = file.isDirectory ? 'Directory' : file.extension || 'File';
        
        const sizeCell = document.createElement('td');
        sizeCell.textContent = file.isDirectory ? '-' : file.sizeFormatted;
        
        const modifiedCell = document.createElement('td');
        modifiedCell.textContent = file.modified;
        
        const actionsCell = document.createElement('td');
        actionsCell.innerHTML = `
            <button class="btn btn-sm btn-outline-info file-info-btn" title="File Info">
                <i class="bi bi-info-circle"></i>
            </button>
        `;
        
        row.appendChild(nameCell);
        row.appendChild(typeCell);
        row.appendChild(sizeCell);
        row.appendChild(modifiedCell);
        row.appendChild(actionsCell);
        
        // Add click handler
        row.addEventListener('click', (e) => {
            if (!e.target.closest('.file-info-btn')) {
                this.handleFileClick(file);
            }
        });
        
        // Add file info button handler
        const infoBtn = actionsCell.querySelector('.file-info-btn');
        infoBtn.addEventListener('click', (e) => {
            e.stopPropagation();
            this.showFileInfo(file);
        });
        
        return row;
    }

    /**
     * Handle file click
     */
    handleFileClick(file) {
        if (file.isDirectory) {
            this.loadDirectory(file.path);
        } else {
            this.showFileInfo(file);
        }
    }

    /**
     * Show file information modal
     */
    async showFileInfo(file) {
        try {
            const response = await fetch(`/impact/rnd-webcenter/api/file-info?path=${encodeURIComponent(file.path)}`);
            const data = await response.json();
            
            if (data.success) {
                const fileInfo = data.data;
                
                document.getElementById('fileName').textContent = fileInfo.name;
                document.getElementById('fileType').textContent = fileInfo.isDirectory ? 'Directory' : fileInfo.extension || 'File';
                document.getElementById('fileSize').textContent = fileInfo.isDirectory ? '-' : fileInfo.sizeFormatted;
                document.getElementById('fileModified').textContent = fileInfo.modified;
                document.getElementById('filePath').textContent = fileInfo.path;
                
                const modal = new bootstrap.Modal(document.getElementById('fileInfoModal'));
                modal.show();
            } else {
                console.error('Error getting file info:', data.error);
            }
        } catch (error) {
            console.error('Error getting file info:', error);
        }
    }

    /**
     * Show connection status
     */
    showConnectionStatus(message, type) {
        const statusDiv = document.getElementById('connectionStatus');
        const messageSpan = document.getElementById('connectionMessage');
        
        statusDiv.className = `alert alert-${type}`;
        messageSpan.textContent = message;
        statusDiv.classList.remove('d-none');
        
        // Auto-hide success messages after 3 seconds
        if (type === 'success') {
            setTimeout(() => {
                statusDiv.classList.add('d-none');
            }, 3000);
        }
    }

    /**
     * Show loading state
     */
    showLoadingState() {
        document.getElementById('loadingSpinner').classList.remove('d-none');
        document.getElementById('fileContainer').classList.add('d-none');
        document.getElementById('emptyState').classList.add('d-none');
        document.getElementById('errorState').classList.add('d-none');
    }

    /**
     * Show file container
     */
    showFileContainer() {
        document.getElementById('loadingSpinner').classList.add('d-none');
        document.getElementById('fileContainer').classList.remove('d-none');
        document.getElementById('emptyState').classList.add('d-none');
        document.getElementById('errorState').classList.add('d-none');
    }

    /**
     * Show empty state
     */
    showEmptyState() {
        document.getElementById('loadingSpinner').classList.add('d-none');
        document.getElementById('fileContainer').classList.add('d-none');
        document.getElementById('emptyState').classList.remove('d-none');
        document.getElementById('errorState').classList.add('d-none');
    }

    /**
     * Show error state
     */
    showErrorState(message) {
        document.getElementById('errorMessage').textContent = message;
        document.getElementById('loadingSpinner').classList.add('d-none');
        document.getElementById('fileContainer').classList.add('d-none');
        document.getElementById('emptyState').classList.add('d-none');
        document.getElementById('errorState').classList.remove('d-none');
    }

    /**
     * Test custom network path
     */
    async testCustomPath() {
        const pathInput = document.getElementById('networkPath');
        const testResult = document.getElementById('testResult');
        const testResultText = document.getElementById('testResultText');
        const applyBtn = document.getElementById('applyPathBtn');
        
        const testPath = pathInput.value.trim();
        
        if (!testPath) {
            this.showTestResult('Please enter a network path', 'warning');
            return;
        }
        
        try {
            testResult.classList.remove('d-none', 'alert-success', 'alert-danger');
            testResult.classList.add('alert-info');
            testResultText.textContent = 'Testing path...';
            
            const response = await fetch('/impact/rnd-webcenter/api/test-path', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    path: testPath
                })
            });
            
            const data = await response.json();
            
            if (data.success) {
                if (data.data.accessible) {
                    this.showTestResult('Path is accessible! You can apply this path.', 'success');
                    applyBtn.classList.remove('d-none');
                } else {
                    this.showTestResult('Path is not accessible. Check the path and permissions.', 'danger');
                    applyBtn.classList.add('d-none');
                }
            } else {
                this.showTestResult(`Error testing path: ${data.error}`, 'danger');
                applyBtn.classList.add('d-none');
            }
        } catch (error) {
            console.error('Error testing path:', error);
            this.showTestResult('Network error occurred while testing path', 'danger');
            applyBtn.classList.add('d-none');
        }
    }

    /**
     * Apply custom network path and reload
     */
    async applyCustomPath() {
        const pathInput = document.getElementById('networkPath');
        const testPath = pathInput.value.trim();
        
        if (!testPath) {
            alert('Please enter a valid network path');
            return;
        }
        
        try {
            // Save custom path to server session
            const response = await fetch('/impact/rnd-webcenter/api/set-custom-path', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    path: testPath
                })
            });
            
            const data = await response.json();
            
            if (data.success) {
                // Store the custom path in session storage as backup
                sessionStorage.setItem('customNetworkPath', testPath);
                
                // Close modal
                const modal = bootstrap.Modal.getInstance(document.getElementById('pathConfigModal'));
                modal.hide();
                
                // Reload the page to apply the new path
                window.location.reload();
            } else {
                alert(`Error saving path: ${data.error}`);
            }
        } catch (error) {
            console.error('Error saving custom path:', error);
            alert('Network error occurred while saving path');
        }
    }

    /**
     * Show test result in modal
     */
    showTestResult(message, type) {
        const testResult = document.getElementById('testResult');
        const testResultText = document.getElementById('testResultText');
        
        testResult.classList.remove('d-none', 'alert-info', 'alert-success', 'alert-danger');
        testResult.classList.add(`alert-${type}`);
        testResultText.textContent = message;
    }

    /**
     * Initialize custom path from session storage
     */
    initializeCustomPath() {
        const customPath = sessionStorage.getItem('customNetworkPath');
        if (customPath) {
            document.getElementById('networkPath').value = customPath;
        }
    }
}

// Initialize the application when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    window.rndWebCenter = new RNDWebCenter();
});