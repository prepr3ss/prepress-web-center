# Frontend JavaScript Implementation for Dynamic Filters

## Implementation Pattern for All Modules

### 1. tabelkpictp.html JavaScript Updates

Add this script section before closing `</body>` tag:

```javascript
<script>
// Dynamic Filter Functions for KPI CTP Table
async function populateYearOptions() {
    try {
        // Try dedicated API endpoint first
        const response = await fetch('/impact/api/ctp-production-logs/years');
        if (response.ok) {
            const data = await response.json();
            if (data.success && data.years) {
                populateYearSelect(data.years);
                return;
            }
        }
        // Fallback to extract from existing data
        return await extractYearsFromExistingData();
    } catch (error) {
        console.error('Error loading years:', error);
        // Fallback method
        return await extractYearsFromExistingData();
    }
}

async function populateMonthOptions(selectedYear = '') {
    try {
        if (selectedYear) {
            // Try dedicated API endpoint first
            const response = await fetch(`/impact/api/ctp-production-logs/months?year=${selectedYear}`);
            if (response.ok) {
                const data = await response.json();
                if (data.success && data.months && data.months.length > 0) {
                    populateMonthSelect(data.months);
                    return;
                }
            }
            // Fallback to extract from existing data
            return await extractMonthsFromExistingData(selectedYear);
        } else {
            // Clear month options if no year selected
            clearMonthOptions();
        }
    } catch (error) {
        console.error('Error loading months:', error);
        // Fallback method
        return await extractMonthsFromExistingData(selectedYear);
    }
}

async function extractYearsFromExistingData() {
    try {
        // Fetch all KPI data and extract unique years
        const response = await fetch('/impact/get-kpi-data');
        const result = await response.json();
        
        if (result.data && Array.isArray(result.data)) {
            const years = new Set();
            
            result.data.forEach(item => {
                const dateField = item.log_date;
                if (dateField) {
                    try {
                        const date = new Date(dateField);
                        const year = date.getFullYear();
                        if (!isNaN(year)) {
                            years.add(year);
                        }
                    } catch (e) {
                        console.error('Error parsing date:', e);
                    }
                }
            });
            
            const yearSelect = document.getElementById('filterYear');
            if (yearSelect) {
                yearSelect.innerHTML = '<option value="">Semua Tahun</option>';
                
                // Sort years in descending order (most recent first)
                const sortedYears = Array.from(years).sort((a, b) => b - a);
                sortedYears.forEach(year => {
                    yearSelect.innerHTML += `<option value="${year}">${year}</option>`;
                });
                return {success: true, years: Array.from(years)};
            }
        } else {
            throw new Error('No data found or API failed');
        }
    } catch (error) {
        console.error('Error extracting years from data:', error);
        throw error;
    }
}

async function extractMonthsFromExistingData(selectedYear) {
    try {
        // Fetch all KPI data and extract unique months for selected year
        const response = await fetch('/impact/get-kpi-data');
        const result = await response.json();
        
        if (result.data && Array.isArray(result.data)) {
            const months = new Set();
            result.data.forEach(item => {
                const dateField = item.log_date;
                if (dateField) {
                    const date = new Date(dateField);
                    const year = date.getFullYear();
                    if (year == selectedYear) {
                        months.add(date.getMonth() + 1); // getMonth() returns 0-11, we need 1-12
                    }
                }
            });
            
            const monthSelect = document.getElementById('filterMonth');
            if (monthSelect) {
                monthSelect.innerHTML = '<option value="">Semua Bulan</option>';
                
                const monthNames = ['Januari', 'Februari', 'Maret', 'April', 'Mei', 'Juni', 
                                  'Juli', 'Agustus', 'September', 'Oktober', 'November', 'Desember'];
                
                // Sort months numerically
                Array.from(months).sort((a, b) => a - b).forEach(month => {
                    const monthName = monthNames[month - 1] || `Bulan ${month}`;
                    monthSelect.innerHTML += `<option value="${month}">${monthName}</option>`;
                });
            }
            return {success: true, months: Array.from(months)};
        } else {
            throw new Error('No data found or API failed');
        }
    } catch (error) {
        console.error('Error extracting months from data:', error);
        throw error;
    }
}

function populateYearSelect(years) {
    const yearSelect = document.getElementById('filterYear');
    if (yearSelect) {
        yearSelect.innerHTML = '<option value="">Semua Tahun</option>';
        years.forEach(year => {
            yearSelect.innerHTML += `<option value="${year}">${year}</option>`;
        });
    }
}

function populateMonthSelect(months) {
    const monthSelect = document.getElementById('filterMonth');
    if (monthSelect) {
        monthSelect.innerHTML = '<option value="">Semua Bulan</option>';
        const monthNames = ['Januari', 'Februari', 'Maret', 'April', 'Mei', 'Juni', 
                          'Juli', 'Agustus', 'September', 'Oktober', 'November', 'Desember'];
        months.forEach(month => {
            const monthName = monthNames[month - 1] || `Bulan ${month}`;
            monthSelect.innerHTML += `<option value="${month}">${monthName}</option>`;
        });
    }
}

function clearMonthOptions() {
    const monthSelect = document.getElementById('filterMonth');
    if (monthSelect) {
        monthSelect.innerHTML = '<option value="">Semua Bulan</option>';
    }
}

// Initialize dynamic filters when DOM is loaded
document.addEventListener('DOMContentLoaded', async function() {
    // Wait for existing initialization to complete
    setTimeout(async function() {
        try {
            // Populate year options
            await populateYearOptions();
            
            // Set up event listeners for dynamic month population
            const yearFilter = document.getElementById('filterYear');
            if (yearFilter) {
                yearFilter.addEventListener('change', async function() {
                    const selectedYear = this.value;
                    await populateMonthOptions(selectedYear);
                    // Trigger existing data reload
                    if (typeof loadKpiData === 'function') {
                        loadKpiData();
                    }
                });
            }
            
            const monthFilter = document.getElementById('filterMonth');
            if (monthFilter) {
                monthFilter.addEventListener('change', function() {
                    // Trigger existing data reload
                    if (typeof loadKpiData === 'function') {
                        loadKpiData();
                    }
                });
            }
        } catch (error) {
            console.error('Error initializing dynamic filters:', error);
        }
    }, 1000); // 1 second delay to ensure existing scripts are loaded
});
</script>
```

### 2. dashboard_ctp.html JavaScript Updates

```javascript
<script>
// Dynamic Filter Functions for Dashboard CTP
async function populateYearOptions() {
    try {
        // Try dedicated API endpoint first
        const response = await fetch('/impact/api/ctp-production-logs/years');
        if (response.ok) {
            const data = await response.json();
            if (data.success && data.years) {
                populateYearSelect(data.years);
                return;
            }
        }
        // Fallback to extract from existing data
        return await extractYearsFromExistingData();
    } catch (error) {
        console.error('Error loading years:', error);
        // Fallback method
        return await extractYearsFromExistingData();
    }
}

async function populateMonthOptions(selectedYear = '') {
    try {
        if (selectedYear) {
            // Try dedicated API endpoint first
            const response = await fetch(`/impact/api/ctp-production-logs/months?year=${selectedYear}`);
            if (response.ok) {
                const data = await response.json();
                if (data.success && data.months && data.months.length > 0) {
                    populateMonthSelect(data.months);
                    return;
                }
            }
            // Fallback to extract from existing data
            return await extractMonthsFromExistingData(selectedYear);
        } else {
            // Clear month options if no year selected
            clearMonthOptions();
        }
    } catch (error) {
        console.error('Error loading months:', error);
        // Fallback method
        return await extractMonthsFromExistingData(selectedYear);
    }
}

async function extractYearsFromExistingData() {
    try {
        // Fetch all dashboard data and extract unique years
        const response = await fetch('/impact/get-dashboard-data'); // Assuming this endpoint exists
        const result = await response.json();
        
        if (result.data && Array.isArray(result.data)) {
            const years = new Set();
            
            result.data.forEach(item => {
                const dateField = item.log_date;
                if (dateField) {
                    try {
                        const date = new Date(dateField);
                        const year = date.getFullYear();
                        if (!isNaN(year)) {
                            years.add(year);
                        }
                    } catch (e) {
                        console.error('Error parsing date:', e);
                    }
                }
            });
            
            const yearSelect = document.getElementById('filterYear');
            if (yearSelect) {
                yearSelect.innerHTML = '<option value="">Semua Tahun</option>';
                
                // Sort years in descending order (most recent first)
                const sortedYears = Array.from(years).sort((a, b) => b - a);
                sortedYears.forEach(year => {
                    yearSelect.innerHTML += `<option value="${year}">${year}</option>`;
                });
                return {success: true, years: Array.from(years)};
            }
        } else {
            throw new Error('No data found or API failed');
        }
    } catch (error) {
        console.error('Error extracting years from data:', error);
        throw error;
    }
}

async function extractMonthsFromExistingData(selectedYear) {
    try {
        // Fetch all dashboard data and extract unique months for selected year
        const response = await fetch('/impact/get-dashboard-data');
        const result = await response.json();
        
        if (result.data && Array.isArray(result.data)) {
            const months = new Set();
            result.data.forEach(item => {
                const dateField = item.log_date;
                if (dateField) {
                    const date = new Date(dateField);
                    const year = date.getFullYear();
                    if (year == selectedYear) {
                        months.add(date.getMonth() + 1);
                    }
                }
            });
            
            const monthSelect = document.getElementById('filterMonth');
            if (monthSelect) {
                monthSelect.innerHTML = '<option value="">Semua Bulan</option>';
                
                const monthNames = ['Januari', 'Februari', 'Maret', 'April', 'Mei', 'Juni', 
                                  'Juli', 'Agustus', 'September', 'Oktober', 'November', 'Desember'];
                
                // Sort months numerically
                Array.from(months).sort((a, b) => a - b).forEach(month => {
                    const monthName = monthNames[month - 1] || `Bulan ${month}`;
                    monthSelect.innerHTML += `<option value="${month}">${monthName}</option>`;
                });
            }
            return {success: true, months: Array.from(months)};
        } else {
            throw new Error('No data found or API failed');
        }
    } catch (error) {
        console.error('Error extracting months from data:', error);
        throw error;
    }
}

function populateYearSelect(years) {
    const yearSelect = document.getElementById('filterYear');
    if (yearSelect) {
        yearSelect.innerHTML = '<option value="">Semua Tahun</option>';
        years.forEach(year => {
            yearSelect.innerHTML += `<option value="${year}">${year}</option>`;
        });
    }
}

function populateMonthSelect(months) {
    const monthSelect = document.getElementById('filterMonth');
    if (monthSelect) {
        monthSelect.innerHTML = '<option value="">Semua Bulan</option>';
        const monthNames = ['Januari', 'Februari', 'Maret', 'April', 'Mei', 'Juni', 
                          'Juli', 'Agustus', 'September', 'Oktober', 'November', 'Desember'];
        months.forEach(month => {
            const monthName = monthNames[month - 1] || `Bulan ${month}`;
            monthSelect.innerHTML += `<option value="${month}">${monthName}</option>`;
        });
    }
}

function clearMonthOptions() {
    const monthSelect = document.getElementById('filterMonth');
    if (monthSelect) {
        monthSelect.innerHTML = '<option value="">Semua Bulan</option>';
    }
}

// Initialize dynamic filters when DOM is loaded
document.addEventListener('DOMContentLoaded', async function() {
    setTimeout(async function() {
        try {
            await populateYearOptions();
            
            const yearFilter = document.getElementById('filterYear');
            if (yearFilter) {
                yearFilter.addEventListener('change', async function() {
                    const selectedYear = this.value;
                    await populateMonthOptions(selectedYear);
                    // Trigger existing dashboard refresh
                    if (typeof refreshDashboard === 'function') {
                        refreshDashboard();
                    }
                });
            }
            
            const monthFilter = document.getElementById('filterMonth');
            if (monthFilter) {
                monthFilter.addEventListener('change', function() {
                    if (typeof refreshDashboard === 'function') {
                        refreshDashboard();
                    }
                });
            }
        } catch (error) {
            console.error('Error initializing dynamic filters:', error);
        }
    }, 1000);
});
</script>
```

### 3. stock_opname_ctp.html JavaScript Updates

```javascript
<script>
// Dynamic Filter Functions for Stock Opname CTP
async function populateYearOptions() {
    try {
        // Try dedicated API endpoint first
        const response = await fetch('/impact/api/ctp-production-logs/years');
        if (response.ok) {
            const data = await response.json();
            if (data.success && data.years) {
                populateYearSelect(data.years);
                return;
            }
        }
        // Fallback to extract from existing data
        return await extractYearsFromExistingData();
    } catch (error) {
        console.error('Error loading years:', error);
        // Fallback method
        return await extractYearsFromExistingData();
    }
}

async function populateMonthOptions(selectedYear = '') {
    try {
        if (selectedYear) {
            // Try dedicated API endpoint first
            const response = await fetch(`/impact/api/ctp-production-logs/months?year=${selectedYear}`);
            if (response.ok) {
                const data = await response.json();
                if (data.success && data.months && data.months.length > 0) {
                    populateMonthSelect(data.months);
                    return;
                }
            }
            // Fallback to extract from existing data
            return await extractMonthsFromExistingData(selectedYear);
        } else {
            // Clear month options if no year selected
            clearMonthOptions();
        }
    } catch (error) {
        console.error('Error loading months:', error);
        // Fallback method
        return await extractMonthsFromExistingData(selectedYear);
    }
}

async function extractYearsFromExistingData() {
    try {
        // Fetch all stock opname data and extract unique years
        const response = await fetch('/impact/get-stock-opname-data');
        const result = await response.json();
        
        if (result.data && Array.isArray(result.data)) {
            const years = new Set();
            
            result.data.forEach(item => {
                const dateField = item.log_date;
                if (dateField) {
                    try {
                        const date = new Date(dateField);
                        const year = date.getFullYear();
                        if (!isNaN(year)) {
                            years.add(year);
                        }
                    } catch (e) {
                        console.error('Error parsing date:', e);
                    }
                }
            });
            
            const yearSelect = document.getElementById('filterYear');
            if (yearSelect) {
                yearSelect.innerHTML = '<option value="">Semua Tahun</option>';
                
                // Sort years in descending order (most recent first)
                const sortedYears = Array.from(years).sort((a, b) => b - a);
                sortedYears.forEach(year => {
                    yearSelect.innerHTML += `<option value="${year}">${year}</option>`;
                });
                return {success: true, years: Array.from(years)};
            }
        } else {
            throw new Error('No data found or API failed');
        }
    } catch (error) {
        console.error('Error extracting years from data:', error);
        throw error;
    }
}

async function extractMonthsFromExistingData(selectedYear) {
    try {
        // Fetch all stock opname data and extract unique months for selected year
        const response = await fetch('/impact/get-stock-opname-data');
        const result = await response.json();
        
        if (result.data && Array.isArray(result.data)) {
            const months = new Set();
            result.data.forEach(item => {
                const dateField = item.log_date;
                if (dateField) {
                    const date = new Date(dateField);
                    const year = date.getFullYear();
                    if (year == selectedYear) {
                        months.add(date.getMonth() + 1);
                    }
                }
            });
            
            const monthSelect = document.getElementById('filterMonth');
            if (monthSelect) {
                monthSelect.innerHTML = '<option value="">Semua Bulan</option>';
                
                const monthNames = ['Januari', 'Februari', 'Maret', 'April', 'Mei', 'Juni', 
                                  'Juli', 'Agustus', 'September', 'Oktober', 'November', 'Desember'];
                
                // Sort months numerically
                Array.from(months).sort((a, b) => a - b).forEach(month => {
                    const monthName = monthNames[month - 1] || `Bulan ${month}`;
                    monthSelect.innerHTML += `<option value="${month}">${monthName}</option>`;
                });
            }
            return {success: true, months: Array.from(months)};
        } else {
            throw new Error('No data found or API failed');
        }
    } catch (error) {
        console.error('Error extracting months from data:', error);
        throw error;
    }
}

function populateYearSelect(years) {
    const yearSelect = document.getElementById('filterYear');
    if (yearSelect) {
        yearSelect.innerHTML = '<option value="">Semua Tahun</option>';
        years.forEach(year => {
            yearSelect.innerHTML += `<option value="${year}">${year}</option>`;
        });
    }
}

function populateMonthSelect(months) {
    const monthSelect = document.getElementById('filterMonth');
    if (monthSelect) {
        monthSelect.innerHTML = '<option value="">Semua Bulan</option>';
        const monthNames = ['Januari', 'Februari', 'Maret', 'April', 'Mei', 'Juni', 
                          'Juli', 'Agustus', 'September', 'Oktober', 'November', 'Desember'];
        months.forEach(month => {
            const monthName = monthNames[month - 1] || `Bulan ${month}`;
            monthSelect.innerHTML += `<option value="${month}">${monthName}</option>`;
        });
    }
}

function clearMonthOptions() {
    const monthSelect = document.getElementById('filterMonth');
    if (monthSelect) {
        monthSelect.innerHTML = '<option value="">Semua Bulan</option>';
    }
}

// Initialize dynamic filters when DOM is loaded
document.addEventListener('DOMContentLoaded', async function() {
    setTimeout(async function() {
        try {
            await populateYearOptions();
            
            const yearFilter = document.getElementById('filterYear');
            if (yearFilter) {
                yearFilter.addEventListener('change', async function() {
                    const selectedYear = this.value;
                    await populateMonthOptions(selectedYear);
                    // Trigger existing data reload
                    if (typeof filterTableData === 'function') {
                        filterTableData();
                    }
                });
            }
            
            const monthFilter = document.getElementById('filterMonth');
            if (monthFilter) {
                monthFilter.addEventListener('change', function() {
                    if (typeof filterTableData === 'function') {
                        filterTableData();
                    }
                });
            }
        } catch (error) {
            console.error('Error initializing dynamic filters:', error);
        }
    }, 1000);
});
</script>
```

### 4. chemical_bon_ctp.html JavaScript Updates

```javascript
<script>
// Dynamic Filter Functions for Chemical Bon CTP
async function populateYearOptions() {
    try {
        // Try dedicated API endpoint first
        const response = await fetch('/impact/api/chemical-bon-ctp/years');
        if (response.ok) {
            const data = await response.json();
            if (data.success && data.years) {
                populateYearSelect(data.years);
                return;
            }
        }
        // Fallback to extract from existing data
        return await extractYearsFromExistingData();
    } catch (error) {
        console.error('Error loading years:', error);
        // Fallback method
        return await extractYearsFromExistingData();
    }
}

async function populateMonthOptions(selectedYear = '') {
    try {
        if (selectedYear) {
            // Try dedicated API endpoint first
            const response = await fetch(`/impact/api/chemical-bon-ctp/months?year=${selectedYear}`);
            if (response.ok) {
                const data = await response.json();
                if (data.success && data.months && data.months.length > 0) {
                    populateMonthSelect(data.months);
                    return;
                }
            }
            // Fallback to extract from existing data
            return await extractMonthsFromExistingData(selectedYear);
        } else {
            // Clear month options if no year selected
            clearMonthOptions();
        }
    } catch (error) {
        console.error('Error loading months:', error);
        // Fallback method
        return await extractMonthsFromExistingData(selectedYear);
    }
}

async function extractYearsFromExistingData() {
    try {
        // Fetch all chemical bon data and extract unique years
        const response = await fetch('/impact/api/chemical-bon-ctp/list');
        const result = await response.json();
        
        if (result.success && result.data && Array.isArray(result.data)) {
            const years = new Set();
            
            result.data.forEach(item => {
                const dateField = item.tanggal;
                if (dateField) {
                    try {
                        const date = new Date(dateField);
                        const year = date.getFullYear();
                        if (!isNaN(year)) {
                            years.add(year);
                        }
                    } catch (e) {
                        console.error('Error parsing date:', e);
                    }
                }
            });
            
            const yearSelect = document.getElementById('yearFilter');
            if (yearSelect) {
                yearSelect.innerHTML = '<option value="">Semua Tahun</option>';
                
                // Sort years in descending order (most recent first)
                const sortedYears = Array.from(years).sort((a, b) => b - a);
                sortedYears.forEach(year => {
                    yearSelect.innerHTML += `<option value="${year}">${year}</option>`;
                });
                return {success: true, years: Array.from(years)};
            }
        } else {
            throw new Error('No data found or API failed');
        }
    } catch (error) {
        console.error('Error extracting years from data:', error);
        throw error;
    }
}

async function extractMonthsFromExistingData(selectedYear) {
    try {
        // Fetch all chemical bon data and extract unique months for selected year
        const response = await fetch('/impact/api/chemical-bon-ctp/list');
        const result = await response.json();
        
        if (result.success && result.data && Array.isArray(result.data)) {
            const months = new Set();
            result.data.forEach(item => {
                const dateField = item.tanggal;
                if (dateField) {
                    const date = new Date(dateField);
                    const year = date.getFullYear();
                    if (year == selectedYear) {
                        months.add(date.getMonth() + 1);
                    }
                }
            });
            
            const monthSelect = document.getElementById('monthFilter');
            if (monthSelect) {
                monthSelect.innerHTML = '<option value="">Semua Bulan</option>';
                
                const monthNames = ['Januari', 'Februari', 'Maret', 'April', 'Mei', 'Juni', 
                                  'Juli', 'Agustus', 'September', 'Oktober', 'November', 'Desember'];
                
                // Sort months numerically
                Array.from(months).sort((a, b) => a - b).forEach(month => {
                    const monthName = monthNames[month - 1] || `Bulan ${month}`;
                    monthSelect.innerHTML += `<option value="${month}">${monthName}</option>`;
                });
            }
            return {success: true, months: Array.from(months)};
        } else {
            throw new Error('No data found or API failed');
        }
    } catch (error) {
        console.error('Error extracting months from data:', error);
        throw error;
    }
}

function populateYearSelect(years) {
    const yearSelect = document.getElementById('yearFilter');
    if (yearSelect) {
        yearSelect.innerHTML = '<option value="">Semua Tahun</option>';
        years.forEach(year => {
            yearSelect.innerHTML += `<option value="${year}">${year}</option>`;
        });
    }
}

function populateMonthSelect(months) {
    const monthSelect = document.getElementById('monthFilter');
    if (monthSelect) {
        monthSelect.innerHTML = '<option value="">Semua Bulan</option>';
        const monthNames = ['Januari', 'Februari', 'Maret', 'April', 'Mei', 'Juni', 
                          'Juli', 'Agustus', 'September', 'Oktober', 'November', 'Desember'];
        months.forEach(month => {
            const monthName = monthNames[month - 1] || `Bulan ${month}`;
            monthSelect.innerHTML += `<option value="${month}">${monthName}</option>`;
        });
    }
}

function clearMonthOptions() {
    const monthSelect = document.getElementById('monthFilter');
    if (monthSelect) {
        monthSelect.innerHTML = '<option value="">Semua Bulan</option>';
    }
}

// Initialize dynamic filters when DOM is loaded
document.addEventListener('DOMContentLoaded', async function() {
    setTimeout(async function() {
        try {
            await populateYearOptions();
            
            const yearFilter = document.getElementById('yearFilter');
            if (yearFilter) {
                yearFilter.addEventListener('change', async function() {
                    const selectedYear = this.value;
                    await populateMonthOptions(selectedYear);
                    // Trigger existing data reload
                    if (typeof filterTableData === 'function') {
                        filterTableData();
                    }
                });
            }
            
            const monthFilter = document.getElementById('monthFilter');
            if (monthFilter) {
                monthFilter.addEventListener('change', function() {
                    if (typeof filterTableData === 'function') {
                        filterTableData();
                    }
                });
            }
        } catch (error) {
            console.error('Error initializing dynamic filters:', error);
        }
    }, 1000);
});
</script>
```

## Integration Instructions

### For each HTML file:

1. **Remove existing static year population code**:
   - Find and remove JavaScript code that statically populates year options
   - Usually looks like: `for (let year = currentYear; year >= currentYear - 4; year--)`

2. **Remove existing static month options**:
   - Remove hardcoded month option HTML from select elements
   - Keep the empty/default option

3. **Add the dynamic filter script**:
   - Insert the appropriate JavaScript code before `</body>` tag
   - Ensure it loads after existing JavaScript

4. **Update HTML select elements**:
   - Ensure year select has `id="filterYear"` or `id="yearFilter"`
   - Ensure month select has `id="filterMonth"` or `id="monthFilter"`
   - Remove static options, keep only the default empty option

### Example HTML Structure:
```html
<!-- Before -->
<select id="filterYear">
    <option value="">Semua Tahun</option>
    <!-- Static year options generated by JS -->
</select>

<select id="filterMonth">
    <option value="">Semua Bulan</option>
    <option value="1">Januari</option>
    <option value="2">Februari</option>
    <!-- All 12 months hardcoded -->
</select>

<!-- After -->
<select id="filterYear">
    <option value="">Semua Tahun</option>
    <!-- Will be populated dynamically -->
</select>

<select id="filterMonth">
    <option value="">Semua Bulan</option>
    <!-- Will be populated dynamically based on selected year -->
</select>
```

## Error Handling Enhancements

### Add loading indicators:
```javascript
function showLoading(selectElement) {
    selectElement.innerHTML = '<option value="">Loading...</option>';
    selectElement.disabled = true;
}

function hideLoading(selectElement) {
    selectElement.disabled = false;
}

// Usage in populate functions:
async function populateYearOptions() {
    const yearSelect = document.getElementById('filterYear');
    showLoading(yearSelect);
    try {
        // ... existing logic
    } finally {
        hideLoading(yearSelect);
    }
}
```

### Add error notifications:
```javascript
function showError(message) {
    // Show error in toast or alert
    console.error(message);
    const toast = document.createElement('div');
    toast.className = 'alert alert-danger';
    toast.textContent = message;
    document.body.appendChild(toast);
    setTimeout(() => toast.remove(), 3000);
}
```

## Browser Compatibility

### Ensure cross-browser support:
```javascript
// Use fetch with polyfill for older browsers
if (!window.fetch) {
    // Load fetch polyfill or use XMLHttpRequest fallback
}

// Use async/await with proper error handling
// Ensure proper event listener attachment
```

## Performance Optimizations

### Debounce rapid filter changes:
```javascript
function debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
}

// Usage:
yearFilter.addEventListener('change', debounce(async function() {
    const selectedYear = this.value;
    await populateMonthOptions(selectedYear);
    filterTableData();
}, 300));
```

### Cache API responses:
```javascript
const cache = new Map();

async function cachedFetch(url) {
    if (cache.has(url)) {
        return cache.get(url);
    }
    
    const response = await fetch(url);
    const data = await response.json();
    cache.set(url, data);
    return data;
}