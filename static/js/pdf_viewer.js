class PDFViewer {
    constructor(options) {
        this.pdfUrl = options.pdfUrl;
        this.filename = options.filename;
        this.pdfDoc = null;
        this.currentPage = 1;
        this.totalPages = 0;
        this.scale = 1.0;
        this.rotation = 0;
        this.isRendering = false;
        this.pageCache = new Map();
        this.colorSwatches = new Map(); // Store detected color swatches
        this.spotColors = new Map(); // Store spot colors (Spot_1, etc.)
        
        this.init();
    }

    init() {
        this.setupEventListeners();
        this.loadPDF();
    }

    setupEventListeners() {
        // Navigation buttons
        document.getElementById('prevPageBtn').addEventListener('click', () => this.previousPage());
        document.getElementById('nextPageBtn').addEventListener('click', () => this.nextPage());
        
        // Zoom controls
        document.getElementById('zoomInBtn').addEventListener('click', () => this.zoomIn());
        document.getElementById('zoomOutBtn').addEventListener('click', () => this.zoomOut());
        document.getElementById('zoomInput').addEventListener('change', (e) => this.setZoom(e.target.value / 100));
        document.getElementById('fitWidthBtn').addEventListener('click', () => this.fitWidth());
        document.getElementById('fitPageBtn').addEventListener('click', () => this.fitPage());
        
        // Rotation controls
        document.getElementById('rotateLeftBtn').addEventListener('click', () => this.rotateLeft());
        document.getElementById('rotateRightBtn').addEventListener('click', () => this.rotateRight());
        
        // Other controls
        document.getElementById('downloadBtn').addEventListener('click', () => this.downloadPDF());
        document.getElementById('backBtn').addEventListener('click', () => this.goBack());
        
        // Color separation panel
        document.getElementById('toggleColorPanel').addEventListener('click', () => this.toggleColorPanel());
        document.getElementById('closeColorPanel').addEventListener('click', () => this.closeColorPanel());
        document.getElementById('resetColors').addEventListener('click', () => this.resetColorChannels());
        
        // Color channel toggles
        ['cyan', 'magenta', 'yellow', 'black'].forEach(color => {
            document.getElementById(`${color}Channel`).addEventListener('change', () => this.updateColorSeparation());
        });
        
        // Keyboard shortcuts
        document.addEventListener('keydown', (e) => this.handleKeyboard(e));
        
        // Canvas drag to pan
        this.setupPanAndZoom();
    }

    async loadPDF() {
        try {
            const loadingOverlay = document.getElementById('loadingOverlay');
            const canvasWrapper = document.getElementById('canvasWrapper');
            const errorMessage = document.getElementById('errorMessage');
            
            // Show loading
            loadingOverlay.style.display = 'flex';
            canvasWrapper.style.display = 'none';
            errorMessage.style.display = 'none';
            
            // Load PDF document
            const loadingTask = pdfjsLib.getDocument(this.pdfUrl);
            this.pdfDoc = await loadingTask.promise;
            this.totalPages = this.pdfDoc.numPages;
            
            // Update page info
            document.getElementById('totalPages').textContent = this.totalPages;
            
            // Hide loading and show canvas
            loadingOverlay.style.display = 'none';
            canvasWrapper.style.display = 'block';
            
            // Render first page
            await this.renderPage(this.currentPage);
            
            // Detect color swatches after PDF is loaded
            await this.detectColorSwatches();
            
        } catch (error) {
            console.error('Error loading PDF:', error);
            this.showError('Failed to load PDF: ' + error.message);
        }
    }

    async renderPage(pageNum) {
        if (this.isRendering) return;
        
        try {
            this.isRendering = true;
            
            // Check if page is already cached
            if (this.pageCache.has(pageNum)) {
                this.displayCachedPage(pageNum);
                this.isRendering = false;
                return;
            }
            
            // Get page from PDF document
            const page = await this.pdfDoc.getPage(pageNum);
            
            // Calculate viewport with current scale and rotation
            const viewport = page.getViewport({
                scale: this.scale,
                rotation: this.rotation
            });
            
            // Create canvas
            const canvas = document.getElementById('pdfCanvas');
            const context = canvas.getContext('2d');
            
            // Set canvas dimensions
            canvas.height = viewport.height;
            canvas.width = viewport.width;
            
            // Render PDF page to canvas
            const renderContext = {
                canvasContext: context,
                viewport: viewport
            };
            
            await page.render(renderContext).promise;
            
            // Cache the rendered page
            this.pageCache.set(pageNum, {
                canvas: canvas.cloneNode(true),
                viewport: viewport
            });
            
            // Update page info
            document.getElementById('currentPage').textContent = pageNum;
            
            // Update button states
            this.updateButtonStates();
            
            // Apply color separation if enabled
            this.updateColorSeparation();
            
        } catch (error) {
            console.error('Error rendering page:', error);
            this.showError('Failed to render page: ' + error.message);
        } finally {
            this.isRendering = false;
        }
    }

    displayCachedPage(pageNum) {
        const cached = this.pageCache.get(pageNum);
        if (!cached) return;
        
        const canvas = document.getElementById('pdfCanvas');
        const context = canvas.getContext('2d');
        
        // Set canvas dimensions
        canvas.height = cached.viewport.height;
        canvas.width = cached.viewport.width;
        
        // Copy cached canvas to current canvas
        context.drawImage(cached.canvas, 0, 0);
        
        // Update page info
        document.getElementById('currentPage').textContent = pageNum;
        
        // Update button states
        this.updateButtonStates();
    }

    async previousPage() {
        if (this.currentPage > 1) {
            this.currentPage--;
            await this.renderPage(this.currentPage);
        }
    }

    async nextPage() {
        if (this.currentPage < this.totalPages) {
            this.currentPage++;
            await this.renderPage(this.currentPage);
        }
    }

    async zoomIn() {
        this.setZoom(this.scale * 1.2);
    }

    async zoomOut() {
        this.setZoom(this.scale * 0.8);
    }

    async setZoom(newScale) {
        this.scale = Math.max(0.1, Math.min(5.0, newScale));
        document.getElementById('zoomInput').value = Math.round(this.scale * 100);
        
        // Clear cache when zoom changes
        this.pageCache.clear();
        
        // Re-render current page
        await this.renderPage(this.currentPage);
    }

    async fitWidth() {
        if (!this.pdfDoc) return;
        
        try {
            const page = await this.pdfDoc.getPage(this.currentPage);
            const viewport = page.getViewport({ scale: 1.0 });
            
            const containerWidth = document.getElementById('canvasContainer').clientWidth - 40; // Subtract margin
            const newScale = containerWidth / viewport.width;
            
            this.setZoom(newScale);
        } catch (error) {
            console.error('Error fitting width:', error);
        }
    }

    async fitPage() {
        if (!this.pdfDoc) return;
        
        try {
            const page = await this.pdfDoc.getPage(this.currentPage);
            const viewport = page.getViewport({ scale: 1.0 });
            
            const containerWidth = document.getElementById('canvasContainer').clientWidth - 40; // Subtract margin
            const containerHeight = document.getElementById('canvasContainer').clientHeight - 40; // Subtract margin
            
            const scaleX = containerWidth / viewport.width;
            const scaleY = containerHeight / viewport.height;
            const newScale = Math.min(scaleX, scaleY);
            
            this.setZoom(newScale);
        } catch (error) {
            console.error('Error fitting page:', error);
        }
    }

    async rotateLeft() {
        this.rotation = (this.rotation - 90) % 360;
        this.pageCache.clear();
        await this.renderPage(this.currentPage);
    }

    async rotateRight() {
        this.rotation = (this.rotation + 90) % 360;
        this.pageCache.clear();
        await this.renderPage(this.currentPage);
    }

    updateColorSeparation() {
        const canvas = document.getElementById('pdfCanvas');
        const context = canvas.getContext('2d');
        
        // Get current image data
        const imageData = context.getImageData(0, 0, canvas.width, canvas.height);
        const data = imageData.data;
        
        // Get channel states
        const showCyan = document.getElementById('cyanChannel').checked;
        const showMagenta = document.getElementById('magentaChannel').checked;
        const showYellow = document.getElementById('yellowChannel').checked;
        const showBlack = document.getElementById('blackChannel').checked;
        
        // If all channels are shown, restore original
        if (showCyan && showMagenta && showYellow && showBlack) {
            this.restoreOriginalColors(data);
        } else {
            this.applyColorSeparation(data, showCyan, showMagenta, showYellow, showBlack);
        }
        
        // Put modified image data back
        context.putImageData(imageData, 0, 0);
    }

    applyColorSeparation(data, showCyan, showMagenta, showYellow, showBlack) {
        for (let i = 0; i < data.length; i += 4) {
            const r = data[i];
            const g = data[i + 1];
            const b = data[i + 2];
            
            // Convert RGB to CMYK (simplified)
            const k = Math.min(255 - r, 255 - g, 255 - b);
            const c = showCyan ? (255 - r - k) : 0;
            const m = showMagenta ? (255 - g - k) : 0;
            const y = showYellow ? (255 - b - k) : 0;
            const kValue = showBlack ? k : 0;
            
            // Convert CMYK back to RGB
            data[i] = 255 - Math.min(255, c + kValue);     // R
            data[i + 1] = 255 - Math.min(255, m + kValue); // G
            data[i + 2] = 255 - Math.min(255, y + kValue); // B
        }
    }

    restoreOriginalColors(data) {
        // This would need the original image data stored
        // For now, we'll just reload the page
        this.pageCache.delete(this.currentPage);
        this.renderPage(this.currentPage);
    }

    resetColorChannels() {
        document.getElementById('cyanChannel').checked = true;
        document.getElementById('magentaChannel').checked = true;
        document.getElementById('yellowChannel').checked = true;
        document.getElementById('blackChannel').checked = true;
        this.updateColorSeparation();
    }

    toggleColorPanel() {
        const panel = document.getElementById('colorPanel');
        panel.classList.toggle('active');
    }

    closeColorPanel() {
        const panel = document.getElementById('colorPanel');
        panel.classList.remove('active');
    }

    setupPanAndZoom() {
        const canvasContainer = document.getElementById('canvasContainer');
        let isPanning = false;
        let startX, startY, scrollLeft, scrollTop;

        canvasContainer.addEventListener('mousedown', (e) => {
            if (e.button === 0) { // Left mouse button
                isPanning = true;
                startX = e.pageX - canvasContainer.offsetLeft;
                startY = e.pageY - canvasContainer.offsetTop;
                scrollLeft = canvasContainer.scrollLeft;
                scrollTop = canvasContainer.scrollTop;
                canvasContainer.style.cursor = 'grabbing';
            }
        });

        canvasContainer.addEventListener('mouseleave', () => {
            isPanning = false;
            canvasContainer.style.cursor = 'default';
        });

        canvasContainer.addEventListener('mouseup', () => {
            isPanning = false;
            canvasContainer.style.cursor = 'default';
        });

        canvasContainer.addEventListener('mousemove', (e) => {
            if (!isPanning) return;
            e.preventDefault();
            const x = e.pageX - canvasContainer.offsetLeft;
            const y = e.pageY - canvasContainer.offsetTop;
            const walkX = (x - startX) * 2;
            const walkY = (y - startY) * 2;
            canvasContainer.scrollLeft = scrollLeft - walkX;
            canvasContainer.scrollTop = scrollTop - walkY;
        });

        // Mouse wheel zoom
        canvasContainer.addEventListener('wheel', (e) => {
            e.preventDefault();
            const delta = e.deltaY > 0 ? 0.9 : 1.1;
            this.setZoom(this.scale * delta);
        });
    }

    handleKeyboard(e) {
        // Prevent default for our shortcuts
        switch(e.key) {
            case 'ArrowLeft':
                e.preventDefault();
                this.previousPage();
                break;
            case 'ArrowRight':
                e.preventDefault();
                this.nextPage();
                break;
            case '+':
            case '=':
                e.preventDefault();
                this.zoomIn();
                break;
            case '-':
                e.preventDefault();
                this.zoomOut();
                break;
            case '0':
                e.preventDefault();
                this.fitPage();
                break;
        }
    }

    updateButtonStates() {
        document.getElementById('prevPageBtn').disabled = this.currentPage <= 1;
        document.getElementById('nextPageBtn').disabled = this.currentPage >= this.totalPages;
    }

    downloadPDF() {
        const link = document.createElement('a');
        link.href = this.pdfUrl;
        link.download = this.filename;
        link.target = '_blank';
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
    }

    goBack() {
        // Try to get the job ID from the URL to navigate back to the job detail page
        const urlParams = new URLSearchParams(window.location.search);
        const jobId = urlParams.get('job_id');
        
        if (jobId) {
            // If we have job_id parameter, navigate back to the job detail page
            window.location.href = `/impact/rnd-cloudsphere/job/${jobId}`;
        } else {
            // Try to go back in history
            if (window.history.length > 1) {
                window.history.back();
            } else {
                // If no history, close the window/tab
                window.close();
                // Fallback if window.close() doesn't work (tab instead of window)
                setTimeout(() => {
                    window.location.href = '/impact/rnd-cloudsphere';
                }, 100);
            }
        }
    }

    showError(message) {
        const loadingOverlay = document.getElementById('loadingOverlay');
        const canvasWrapper = document.getElementById('canvasWrapper');
        const errorMessage = document.getElementById('errorMessage');
        const errorText = document.getElementById('errorText');
        
        loadingOverlay.style.display = 'none';
        canvasWrapper.style.display = 'none';
        errorMessage.style.display = 'block';
        errorText.textContent = message;
    }

    async detectColorSwatches() {
        try {
            if (!this.pdfDoc) return;
            
            // Check for color swatches on each page
            for (let pageNum = 1; pageNum <= this.totalPages; pageNum++) {
                const page = await this.pdfDoc.getPage(pageNum);
                const annotations = await page.getAnnotations();
                
                // Look for color swatch annotations
                if (annotations && Array.isArray(annotations)) {
                    annotations.forEach(annotation => {
                        if (annotation.subtype === 'Widget' && annotation.fieldType === 'Tx') {
                            const text = annotation.fieldValue || '';
                            
                            // Detect color swatches (e.g., "Spot_1", "Spot_2", etc.)
                            const spotMatch = text.match(/Spot_(\d+)/i);
                            if (spotMatch) {
                                const spotNumber = spotMatch[1];
                                const colorName = this.extractColorName(text);
                                
                                if (colorName) {
                                    this.spotColors.set(spotNumber, {
                                        name: colorName,
                                        originalText: text,
                                        page: pageNum
                                    });
                                }
                            }
                            
                            // Detect CMYK values in annotations
                            const cmykMatch = text.match(/C:\s*(\d+)%?\s*M:\s*(\d+)%?\s*Y:\s*(\d+)%?\s*K:\s*(\d+)%?/i);
                            if (cmykMatch) {
                                const c = parseInt(cmykMatch[1]) || 0;
                                const m = parseInt(cmykMatch[2]) || 0;
                                const y = parseInt(cmykMatch[3]) || 0;
                                const k = parseInt(cmykMatch[4]) || 0;
                                
                                this.colorSwatches.set(`CMYK_${pageNum}`, {
                                    c, m, y, k,
                                    page: pageNum
                                });
                            }
                            
                            // Look for hex color values
                            const hexMatch = text.match(/#([0-9A-Fa-f]{6})/i);
                            if (hexMatch) {
                                const hexColor = hexMatch[1].toUpperCase();
                                this.colorSwatches.set(`HEX_${pageNum}`, {
                                    hex: hexColor,
                                    rgb: this.hexToRgb(hexColor),
                                    page: pageNum
                                });
                            }
                        }
                    });
                }
            }
            
            // Update UI with detected swatches
            this.updateSwatchesUI();
            
        } catch (error) {
            console.error('Error detecting color swatches:', error);
        }
    }

    extractColorName(text) {
        // Try to extract color name from annotation text
        // Look for patterns like "Red", "Blue", "PANTONE 123 C", etc.
        const colorPatterns = [
            /([A-Z]+(?:\s+\d+)?)\s*(C|U|EC)?/i,  // PANTONE colors
            /(Red|Green|Blue|Yellow|Orange|Purple|Pink|Brown|Black|White|Gray|Grey)/i,  // Basic colors
            /#([0-9A-Fa-f]{6})/i  // Hex colors
        ];
        
        for (const pattern of colorPatterns) {
            const match = text.match(pattern);
            if (match) {
                return match[0];
            }
        }
        
        return null;
    }

    hexToRgb(hex) {
        // Convert hex to RGB
        const result = /^#?([a-f\d]{2})([a-f\d]{2})([a-f\d]{2})$/i.exec(hex);
        return result ? {
            r: parseInt(result[1], 16),
            g: parseInt(result[2], 16),
            b: parseInt(result[3], 16)
        } : null;
    }

    updateSwatchesUI() {
        // Get the existing color panel
        const colorPanel = document.getElementById('colorPanel');
        if (!colorPanel) return;
        
        // Find the color-separation-content div
        let contentDiv = colorPanel.querySelector('.color-separation-content');
        if (!contentDiv) return;
        
        // Check if swatches section already exists
        let swatchesSection = document.getElementById('detectedSwatchesSection');
        
        if (!swatchesSection) {
            // Create swatches section and add it to the existing color panel
            swatchesSection = document.createElement('div');
            swatchesSection.id = 'detectedSwatchesSection';
            swatchesSection.innerHTML = `
                <hr>
                <h5 class="mb-3"><i class="fas fa-palette me-2"></i>Detected Color Swatches / Warna Terdeteksi</h5>
                
                <div class="swatches-section mb-3">
                    <h6>Spot Colors / Warna Spot</h6>
                    <div class="swatches-grid" id="spotColorsGrid">
                        <!-- Spot colors will be added here -->
                    </div>
                </div>
                
                <div class="swatches-section mb-3">
                    <h6>CMYK Values</h6>
                    <div class="swatches-grid" id="cmykColorsGrid">
                        <!-- CMYK values will be added here -->
                    </div>
                </div>
                
                <div class="swatches-section mb-3">
                    <h6>Hex Colors</h6>
                    <div class="swatches-grid" id="hexColorsGrid">
                        <!-- Hex colors will be added here -->
                    </div>
                </div>
            `;
            
            // Add styles for swatches grid
            const style = document.createElement('style');
            style.textContent = `
                .swatches-section h6 {
                    font-size: 14px;
                    font-weight: 600;
                    margin-bottom: 10px;
                    color: #343a40;
                    border-bottom: 1px solid #dee2e6;
                    padding-bottom: 5px;
                }
                
                .swatches-grid {
                    display: grid;
                    grid-template-columns: repeat(auto-fill, minmax(80px, 1fr));
                    gap: 10px;
                    margin-bottom: 15px;
                }
                
                .swatch-item {
                    padding: 8px;
                    border: 1px solid #dee2e6;
                    border-radius: 4px;
                    text-align: center;
                    font-size: 12px;
                    background: #f8f9fa;
                }
                
                .swatch-color {
                    width: 30px;
                    height: 30px;
                    border-radius: 3px;
                    margin-bottom: 5px;
                    border: 1px solid #ced4da;
                    display: inline-block;
                }
                
                .swatch-name {
                    font-weight: 500;
                    color: #495057;
                    font-size: 11px;
                }
                
                .swatch-info {
                    font-size: 10px;
                    color: #6c757d;
                }
            `;
            
            document.head.appendChild(style);
            
            // Append swatches section to the color panel content
            contentDiv.appendChild(swatchesSection);
        }
        
        // Populate swatches
        this.populateSwatches();
    }

    populateSwatches() {
        // Populate spot colors
        const spotColorsGrid = document.getElementById('spotColorsGrid');
        if (spotColorsGrid) {
            spotColorsGrid.innerHTML = '';
            
            this.spotColors.forEach((color, spotNumber) => {
                const swatchItem = document.createElement('div');
                swatchItem.className = 'swatch-item';
                swatchItem.innerHTML = `
                    <div class="swatch-color" style="background: ${this.estimateSpotColor(color.name)};"></div>
                    <div class="swatch-name">${color.name}</div>
                    <div class="swatch-info">Spot_${spotNumber}</div>
                `;
                spotColorsGrid.appendChild(swatchItem);
            });
        }
        
        // Populate CMYK values
        const cmykColorsGrid = document.getElementById('cmykColorsGrid');
        if (cmykColorsGrid) {
            cmykColorsGrid.innerHTML = '';
            
            this.colorSwatches.forEach((swatch, key) => {
                if (key.startsWith('CMYK_')) {
                    const { c, m, y, k } = swatch;
                    const swatchItem = document.createElement('div');
                    swatchItem.className = 'swatch-item';
                    swatchItem.innerHTML = `
                        <div class="swatch-color" style="background: rgb(${c * 2.55}, ${m * 2.55}, ${y * 2.55});"></div>
                        <div class="swatch-name">CMYK</div>
                        <div class="swatch-info">C:${c}% M:${m}% Y:${y}% K:${k}%</div>
                    `;
                    cmykColorsGrid.appendChild(swatchItem);
                }
            });
        }
        
        // Populate hex colors
        const hexColorsGrid = document.getElementById('hexColorsGrid');
        if (hexColorsGrid) {
            hexColorsGrid.innerHTML = '';
            
            this.colorSwatches.forEach((swatch, key) => {
                if (key.startsWith('HEX_')) {
                    const { hex, rgb } = swatch;
                    const swatchItem = document.createElement('div');
                    swatchItem.className = 'swatch-item';
                    swatchItem.innerHTML = `
                        <div class="swatch-color" style="background: ${hex};"></div>
                        <div class="swatch-name">${hex}</div>
                        <div class="swatch-info">RGB(${rgb.r}, ${rgb.g}, ${rgb.b})</div>
                    `;
                    hexColorsGrid.appendChild(swatchItem);
                }
            });
        }
    }

    estimateSpotColor(colorName) {
        // Estimate color for spot color names
        const colorMap = {
            'red': '#FF0000',
            'green': '#00FF00',
            'blue': '#0000FF',
            'yellow': '#FFFF00',
            'orange': '#FFA500',
            'purple': '#800080',
            'pink': '#FFC0CB',
            'brown': '#964B00',
            'black': '#000000',
            'white': '#FFFFFF',
            'gray': '#808080',
            'grey': '#808080'
        };
        
        const lowerName = colorName.toLowerCase();
        return colorMap[lowerName] || '#CCCCCC'; // Default to gray if not found
    }

    toggleSwatchesPanel() {
        // This function now just toggles the color panel
        this.toggleColorPanel();
    }
}