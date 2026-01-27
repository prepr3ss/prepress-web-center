# Dynamic Filter Implementation Plan

## Overview
Update year and month filters in four HTML templates to implement dynamic population filtering using actual data from the database, following the same implementation pattern as log_ctp_detail.html.

## Target Files
1. `templates/tabelkpictp.html`
2. `templates/dashboard_ctp.html` 
3. `templates/stock_opname_ctp.html`
4. `templates/chemical_bon_ctp.html`

## Data Sources
- **tabelkpictp.html**: Database `ctp_db`, Table `ctp_production_logs`, Column `log_date`
- **dashboard_ctp.html**: Database `ctp_db`, Table `ctp_production_logs`, Column `log_date`
- **stock_opname_ctp.html**: Database `ctp_db`, Table `ctp_production_logs`, Column `log_date`
- **chemical_bon_ctp.html`: Database `ctp_db`, Table `chemical_bon_ctp`, Column `tanggal`

## Reference Implementation Pattern (from log_ctp_detail.html)

### Key Functions
1. `populateYearOptions()` - Extracts years from existing data with fallback
2. `populateMonthOptions(selectedYear)` - Extracts months for selected year with fallback
3. `extractYearsFromExistingData()` - Fallback method to extract years from API data
4. `extractMonthsFromExistingData(selectedYear)` - Fallback method to extract months

### Implementation Flow
1. Try dedicated API endpoint first
2. Fallback to extracting from existing data if API fails
3. Proper error handling throughout
4. Dynamic month population based on selected year

## API Endpoints to Create

### For KPI, Dashboard, Stock Opname (ctp_production_logs table)
```
GET /api/ctp-production-logs/years
GET /api/ctp-production-logs/months?year={year}
```

### For Chemical Bon (chemical_bon_ctp table)
```
GET /api/chemical-bon-ctp/years
GET /api/chemical-bon-ctp/months?year={year}
```

## JavaScript Implementation Pattern

### 1. Dynamic Year Population
```javascript
async function populateYearOptions() {
    try {
        // Try dedicated API endpoint first
        const response = await fetch('/api/{module}/years');
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
```

### 2. Dynamic Month Population
```javascript
async function populateMonthOptions(selectedYear = '') {
    try {
        if (selectedYear) {
            // Try dedicated API endpoint first
            const response = await fetch(`/api/{module}/months?year=${selectedYear}`);
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
```

### 3. Fallback Methods
```javascript
async function extractYearsFromExistingData() {
    try {
        // Fetch all data and extract unique years
        const response = await fetch('/api/{module}/list');
        const data = await response.json();
        
        if (data.success && data.data && Array.isArray(data.data)) {
            const years = new Set();
            data.data.forEach(item => {
                const dateField = item.log_date || item.tanggal || item.created_at;
                if (dateField) {
                    const date = new Date(dateField);
                    const year = date.getFullYear();
                    if (!isNaN(year)) {
                        years.add(year);
                    }
                }
            });
            
            const yearSelect = document.getElementById('filterYear');
            yearSelect.innerHTML = '<option value="">Semua Tahun</option>';
            
            // Sort years in descending order
            const sortedYears = Array.from(years).sort((a, b) => b - a);
            sortedYears.forEach(year => {
                yearSelect.innerHTML += `<option value="${year}">${year}</option>`;
            });
            
            return {success: true, years: Array.from(years)};
        }
    } catch (error) {
        console.error('Error extracting years from data:', error);
        throw error;
    }
}
```

## Backend API Implementation

### Year Endpoint Example
```python
@app.route('/api/ctp-production-logs/years', methods=['GET'])
@login_required
def get_ctp_production_logs_years():
    try:
        years = db.session.query(
            extract(CtpProductionLog.log_date, 'year').label('year')
        ).distinct().all()
        
        year_list = [year.year for year in years if year.year]
        year_list.sort(reverse=True)
        
        return jsonify({
            'success': True,
            'years': year_list
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500
```

### Month Endpoint Example
```python
@app.route('/api/ctp-production-logs/months', methods=['GET'])
@login_required
def get_ctp_production_logs_months():
    try:
        year = request.args.get('year', type=int)
        if not year:
            return jsonify({'success': False, 'error': 'Year parameter required'}), 400
        
        months = db.session.query(
            extract(CtpProductionLog.log_date, 'month').label('month')
        ).filter(
            extract(CtpProductionLog.log_date, 'year') == year
        ).distinct().all()
        
        month_list = [month.month for month in months if month.month]
        month_list.sort()
        
        return jsonify({
            'success': True,
            'months': month_list
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500
```

## Implementation Steps

### Phase 1: Backend API Development
1. Create API endpoints for ctp_production_logs years/months
2. Create API endpoints for chemical_bon_ctp years/months
3. Test API endpoints independently

### Phase 2: Frontend Implementation
1. Update tabelkpictp.html JavaScript
2. Update dashboard_ctp.html JavaScript  
3. Update stock_opname_ctp.html JavaScript
4. Update chemical_bon_ctp.html JavaScript

### Phase 3: Integration & Testing
1. Test dynamic filter functionality
2. Verify error handling and fallback mechanisms
3. Ensure consistent implementation across all modules

## Error Handling Strategy

### Frontend
- Show user-friendly error messages
- Implement retry mechanisms
- Graceful degradation to static options if needed

### Backend
- Proper HTTP status codes
- Detailed error messages in response
- Database connection error handling

## Testing Strategy

### Unit Tests
- Test API endpoints with various parameters
- Test JavaScript functions individually
- Test error handling scenarios

### Integration Tests
- Test complete filter workflow
- Test cross-browser compatibility
- Test with different data scenarios

## Benefits of This Implementation

1. **Dynamic Data**: Filters reflect actual data availability
2. **Better UX**: Users only see relevant options
3. **Performance**: Reduced unnecessary options
4. **Maintainability**: Consistent pattern across modules
5. **Robustness**: Proper error handling and fallbacks

## Timeline Estimate

- **Phase 1 (Backend)**: 2-3 hours
- **Phase 2 (Frontend)**: 3-4 hours  
- **Phase 3 (Testing)**: 1-2 hours
- **Total**: 6-9 hours

## Risk Mitigation

1. **Database Performance**: Use indexed queries for date extraction
2. **Browser Compatibility**: Test across major browsers
3. **Data Consistency**: Handle edge cases in date parsing
4. **User Experience**: Provide loading indicators during data fetch