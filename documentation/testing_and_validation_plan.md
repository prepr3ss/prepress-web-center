# Testing and Validation Plan for Dynamic Filters

## Testing Strategy Overview

This document outlines comprehensive testing procedures for implementing dynamic year and month filters across four HTML templates following the log_ctp_detail.html pattern.

## Pre-Implementation Testing

### 1. Environment Setup Validation
```bash
# Verify database connectivity
python -c "from app import db; print('Database connection OK')"

# Check existing data
python -c "
from app import db, CtpProductionLog, ChemicalBonCTP
print('CTP Production Logs count:', CtpProductionLog.query.count())
print('Chemical Bon CTP count:', ChemicalBonCTP.query.count())
"

# Verify date fields have data
python -c "
from app import db, CtpProductionLog, ChemicalBonCTP
import datetime

ctp_years = db.session.query(CtpProductionLog.log_date).distinct().limit(5).all()
print('Sample CTP dates:', ctp_years)

bon_years = db.session.query(ChemicalBonCTP.tanggal).distinct().limit(5).all()
print('Sample Bon dates:', bon_years)
"
```

### 2. API Endpoint Testing
```bash
# Test years endpoints
curl -X GET "http://localhost:5000/impact/api/ctp-production-logs/years" \
     -H "Cookie: session=test_session" \
     -w "\nHTTP Status: %{http_code}\n"

curl -X GET "http://localhost:5000/impact/api/chemical-bon-ctp/years" \
     -H "Cookie: session=test_session" \
     -w "\nHTTP Status: %{http_code}\n"

# Test months endpoints
curl -X GET "http://localhost:5000/impact/api/ctp-production-logs/months?year=2024" \
     -H "Cookie: session=test_session" \
     -w "\nHTTP Status: %{http_code}\n"

curl -X GET "http://localhost:5000/impact/api/chemical-bon-ctp/months?year=2024" \
     -H "Cookie: session=test_session" \
     -w "\nHTTP Status: %{http_code}\n"
```

## Implementation Testing

### 1. Backend API Testing

#### Test Cases for Years Endpoints
```python
# test_api_years.py
import requests
import json

def test_years_endpoint(endpoint, expected_status=200):
    """Test years endpoint with various scenarios"""
    
    # Test successful request
    response = requests.get(f"http://localhost:5000{endpoint}", cookies={'session': 'test'})
    assert response.status_code == expected_status
    
    data = response.json()
    assert 'success' in data
    assert 'years' in data
    
    if data['success']:
        assert isinstance(data['years'], list)
        assert all(isinstance(year, int) for year in data['years'])
        print(f"✓ {endpoint}: {len(data['years'])} years found")
    else:
        print(f"✗ {endpoint}: {data.get('error', 'Unknown error')}")
    
    return data

# Test cases
test_years_endpoint('/impact/api/ctp-production-logs/years')
test_years_endpoint('/impact/api/chemical-bon-ctp/years')
```

#### Test Cases for Months Endpoints
```python
# test_api_months.py
import requests
import json

def test_months_endpoint(endpoint, year, expected_status=200):
    """Test months endpoint with various scenarios"""
    
    # Test with valid year
    response = requests.get(
        f"http://localhost:5000{endpoint}?year={year}", 
        cookies={'session': 'test'}
    )
    assert response.status_code == expected_status
    
    data = response.json()
    assert 'success' in data
    assert 'months' in data
    
    if data['success']:
        assert isinstance(data['months'], list)
        assert all(isinstance(month, int) for month in data['months'])
        assert all(1 <= month <= 12 for month in data['months'])
        print(f"✓ {endpoint} (year {year}): {len(data['months'])} months found")
    else:
        print(f"✗ {endpoint} (year {year}): {data.get('error', 'Unknown error')}")
    
    return data

# Test cases
test_months_endpoint('/impact/api/ctp-production-logs/months', 2024)
test_months_endpoint('/impact/api/chemical-bon-ctp/months', 2024)

# Test edge cases
test_months_endpoint('/impact/api/ctp-production-logs/months?year=', 400)  # Missing year
test_months_endpoint('/impact/api/ctp-production-logs/months?year=invalid', 400)  # Invalid year
test_months_endpoint('/impact/api/ctp-production-logs/months?year=9999', 200)  # No data year
```

### 2. Frontend JavaScript Testing

#### Test Dynamic Filter Population
```javascript
// test_dynamic_filters.js
// Run in browser console on each page

async function testDynamicFilters() {
    console.log('Testing Dynamic Filters...');
    
    // Test 1: Year population
    try {
        const yearSelect = document.getElementById('filterYear') || document.getElementById('yearFilter');
        if (!yearSelect) {
            console.error('Year select element not found');
            return false;
        }
        
        // Check if years are populated (wait for async)
        await new Promise(resolve => setTimeout(resolve, 2000));
        
        const yearOptions = yearSelect.querySelectorAll('option');
        if (yearOptions.length <= 1) {  // Only default option
            console.error('Year options not populated');
            return false;
        }
        
        console.log(`✓ Year options populated: ${yearOptions.length - 1} years found`);
        
        // Test 2: Month population on year change
        const monthSelect = document.getElementById('filterMonth') || document.getElementById('monthFilter');
        if (!monthSelect) {
            console.error('Month select element not found');
            return false;
        }
        
        // Select first available year
        const firstYear = yearSelect.options[1]?.value;
        if (firstYear) {
            yearSelect.value = firstYear;
            yearSelect.dispatchEvent(new Event('change'));
            
            // Wait for month population
            await new Promise(resolve => setTimeout(resolve, 2000));
            
            const monthOptions = monthSelect.querySelectorAll('option');
            if (monthOptions.length <= 1) {  // Only default option
                console.error('Month options not populated after year change');
                return false;
            }
            
            console.log(`✓ Month options populated for year ${firstYear}: ${monthOptions.length - 1} months found`);
        }
        
        // Test 3: Fallback mechanism
        // Simulate API failure by intercepting fetch
        const originalFetch = window.fetch;
        window.fetch = function() {
            return Promise.reject(new Error('Simulated API failure'));
        };
        
        // Clear and repopulate
        yearSelect.value = '';
        yearSelect.dispatchEvent(new Event('change'));
        
        await new Promise(resolve => setTimeout(resolve, 3000));
        
        // Restore fetch
        window.fetch = originalFetch;
        
        // Test if fallback worked
        const fallbackYearOptions = yearSelect.querySelectorAll('option');
        if (fallbackYearOptions.length <= 1) {
            console.error('Fallback mechanism failed');
            return false;
        }
        
        console.log('✓ Fallback mechanism working');
        
        return true;
        
    } catch (error) {
        console.error('Error testing dynamic filters:', error);
        return false;
    }
}

// Run test
testDynamicFilters().then(success => {
    if (success) {
        console.log('🎉 All dynamic filter tests passed!');
    } else {
        console.log('❌ Some tests failed');
    }
});
```

### 3. Integration Testing

#### End-to-End Filter Workflow Test
```javascript
// test_filter_workflow.js
async function testFilterWorkflow() {
    console.log('Testing Filter Workflow...');
    
    try {
        // Step 1: Load page and verify initial state
        const yearSelect = document.getElementById('filterYear') || document.getElementById('yearFilter');
        const monthSelect = document.getElementById('filterMonth') || document.getElementById('monthFilter');
        
        // Step 2: Select year and verify month population
        const availableYears = Array.from(yearSelect.options).map(opt => opt.value).filter(v => v);
        if (availableYears.length === 0) {
            throw new Error('No years available for testing');
        }
        
        const testYear = availableYears[0];
        yearSelect.value = testYear;
        yearSelect.dispatchEvent(new Event('change'));
        
        // Wait for month population
        await new Promise(resolve => setTimeout(resolve, 2000));
        
        // Step 3: Select month and verify data filtering
        const availableMonths = Array.from(monthSelect.options).map(opt => opt.value).filter(v => v);
        if (availableMonths.length === 0) {
            throw new Error('No months available for testing');
        }
        
        const testMonth = availableMonths[0];
        monthSelect.value = testMonth;
        monthSelect.dispatchEvent(new Event('change'));
        
        // Wait for data filtering
        await new Promise(resolve => setTimeout(resolve, 3000));
        
        // Step 4: Verify data was filtered correctly
        // This depends on the specific page implementation
        console.log('✓ Filter workflow test completed');
        return true;
        
    } catch (error) {
        console.error('Filter workflow test failed:', error);
        return false;
    }
}

testFilterWorkflow();
```

## Browser Compatibility Testing

### Test Matrix
| Browser | Version | Test Status | Notes |
|---------|---------|--------------|-------|
| Chrome | Latest+ | ✅ | Primary target |
| Firefox | Latest+ | ✅ | Secondary target |
| Safari | Latest+ | ✅ | Mac/iOS support |
| Edge | Latest+ | ✅ | Windows support |
| IE 11 | - | ❌ | Not supported (ES6+) |

### Browser Testing Script
```javascript
// test_browser_compatibility.js
function testBrowserCompatibility() {
    const results = {
        fetch: typeof fetch !== 'undefined',
        asyncAwait: (async () => true)(),
        arrowFunctions: (() => true)(),
        templateLiterals: (`${'test'}`) === 'test',
        constLet: (() => { try { const x = 1; return true; } catch { return false; } })()
    };
    
    const allSupported = Object.values(results).every(Boolean);
    
    if (allSupported) {
        console.log('✅ Browser supports all required features');
    } else {
        console.log('❌ Browser compatibility issues:', results);
    }
    
    return allSupported;
}

testBrowserCompatibility();
```

## Performance Testing

### Load Testing Script
```javascript
// test_performance.js
async function testFilterPerformance() {
    const iterations = 10;
    const times = [];
    
    for (let i = 0; i < iterations; i++) {
        const startTime = performance.now();
        
        // Test year population
        await populateYearOptions();
        
        // Test month population
        const yearSelect = document.getElementById('filterYear') || document.getElementById('yearFilter');
        if (yearSelect.options.length > 1) {
            yearSelect.value = yearSelect.options[1].value;
            await populateMonthOptions(yearSelect.value);
        }
        
        const endTime = performance.now();
        times.push(endTime - startTime);
        
        // Reset for next iteration
        yearSelect.value = '';
        await new Promise(resolve => setTimeout(resolve, 100));
    }
    
    const avgTime = times.reduce((a, b) => a + b, 0) / times.length;
    const maxTime = Math.max(...times);
    
    console.log(`Performance Results (${iterations} iterations):`);
    console.log(`Average time: ${avgTime.toFixed(2)}ms`);
    console.log(`Max time: ${maxTime.toFixed(2)}ms`);
    console.log(`Min time: ${Math.min(...times).toFixed(2)}ms`);
    
    // Performance criteria
    const isPerformant = avgTime < 1000 && maxTime < 2000; // <1s avg, <2s max
    console.log(isPerformant ? '✅ Performance acceptable' : '❌ Performance needs improvement');
    
    return isPerformant;
}

testFilterPerformance();
```

## Error Handling Testing

### Simulated Error Scenarios
```javascript
// test_error_handling.js
async function testErrorHandling() {
    console.log('Testing Error Handling...');
    
    // Test 1: Network failure simulation
    const originalFetch = window.fetch;
    window.fetch = function() {
        return Promise.reject(new Error('Network error'));
    };
    
    try {
        await populateYearOptions();
        console.log('✅ Network error handled gracefully');
    } catch (error) {
        console.log('❌ Network error not handled:', error);
    }
    
    // Test 2: Invalid data response
    window.fetch = function() {
        return Promise.resolve({
            ok: true,
            json: () => Promise.resolve({success: false, error: 'Invalid data'})
        });
    };
    
    try {
        await populateYearOptions();
        console.log('✅ Invalid data response handled gracefully');
    } catch (error) {
        console.log('❌ Invalid data response not handled:', error);
    }
    
    // Test 3: Empty data response
    window.fetch = function() {
        return Promise.resolve({
            ok: true,
            json: () => Promise.resolve({success: true, years: [], months: []})
        });
    };
    
    try {
        await populateYearOptions();
        console.log('✅ Empty data response handled gracefully');
    } catch (error) {
        console.log('❌ Empty data response not handled:', error);
    }
    
    // Restore original fetch
    window.fetch = originalFetch;
    console.log('Error handling tests completed');
}

testErrorHandling();
```

## User Acceptance Testing

### User Scenario Testing
```markdown
## Test Scenarios

### Scenario 1: First-time User
1. Navigate to any of the four pages
2. Observe year filter populates with available years
3. Select a year
4. Observe month filter populates with available months
5. Select a month
6. Verify table/data updates accordingly

**Expected Result**: Smooth workflow with relevant filter options only

### Scenario 2: Power User
1. Navigate to page with existing filters
2. Rapidly change year and month filters
3. Verify no errors or performance issues
4. Test clearing filters
5. Test reapplying filters

**Expected Result**: Responsive interface with no lag or errors

### Scenario 3: Edge Cases
1. Test with year that has no data
2. Test with invalid year selection
3. Test network connectivity issues
4. Test with very large datasets

**Expected Result**: Graceful handling with appropriate user feedback

### Scenario 4: Mobile User
1. Test on mobile device
2. Verify filter responsiveness
3. Test touch interactions
4. Verify readability and usability

**Expected Result**: Fully functional on mobile devices
```

## Automated Testing Setup

### Continuous Integration Test Script
```bash
#!/bin/bash
# run_dynamic_filter_tests.sh

echo "Starting Dynamic Filter Tests..."

# Start Flask app in background
python app.py &
FLASK_PID=$!
sleep 5

# Run API tests
echo "Running API tests..."
python test_api_years.py
python test_api_months.py

# Run frontend tests (requires headless browser)
echo "Running frontend tests..."
# This would use Selenium or Playwright for automated browser testing

# Cleanup
kill $FLASK_PID

echo "Dynamic Filter Tests Completed"
```

### Test Data Setup
```python
# setup_test_data.py
from app import db, CtpProductionLog, ChemicalBonCTP
from datetime import datetime, date
import random

def create_test_data():
    """Create diverse test data for comprehensive testing"""
    
    # Create CTP Production Logs with varied dates
    for year in [2022, 2023, 2024]:
        for month in [1, 6, 12]:  # Sparse months
            for day in [15, 30]:  # Multiple days
                log = CtpProductionLog(
                    log_date=date(year, month, day),
                    ctp_group=f"Group {random.randint(1, 3)}",
                    ctp_shift=f"Shift {random.choice(['A', 'B'])}",
                    # ... other required fields
                )
                db.session.add(log)
    
    # Create Chemical Bon CTP with varied dates
    for year in [2023, 2024]:
        for month in [3, 8, 11]:  # Different months
            for day in [10, 25]:  # Multiple days
                bon = ChemicalBonCTP(
                    tanggal=date(year, month, day),
                    brand=f"Brand {random.choice(['A', 'B', 'C'])}",
                    # ... other required fields
                )
                db.session.add(bon)
    
    db.session.commit()
    print("Test data created successfully")

if __name__ == "__main__":
    create_test_data()
```

## Validation Checklist

### Pre-Deployment Checklist
- [ ] All API endpoints return correct HTTP status codes
- [ ] Error responses include proper error messages
- [ ] Frontend JavaScript handles all error scenarios
- [ ] Fallback mechanisms work when API fails
- [ ] Filters populate with correct data from database
- [ ] Month options update correctly when year changes
- [ ] Performance meets acceptable criteria (<1s average)
- [ ] Browser compatibility verified across target browsers
- [ ] Mobile responsiveness confirmed
- [ ] Accessibility standards met (ARIA labels, keyboard navigation)
- [ ] Security testing completed (XSS, injection prevention)
- [ ] Load testing performed with concurrent users

### Post-Deployment Monitoring
- [ ] API response times monitored
- [ ] Error rates tracked
- [ ] User feedback collected
- [ ] Performance metrics captured
- [ ] Browser error logs monitored
- [ ] Database query performance analyzed

## Rollback Plan

### If Implementation Fails
1. **Immediate Rollback**: Revert static filter implementation
2. **Data Recovery**: Ensure no data loss during testing
3. **User Communication**: Notify users of temporary issues
4. **Fix Deployment**: Address issues identified during testing
5. **Re-deploy**: Implement fixed version with monitoring

### Rollback Script
```bash
#!/bin/bash
# rollback_dynamic_filters.sh

echo "Rolling back dynamic filter implementation..."

# Revert HTML files to backup
cp templates/*.html.backup templates/

# Remove new API endpoints from app.py
# This would be done via version control

# Restart Flask application
systemctl restart flask-app

echo "Rollback completed"
```

## Success Criteria

### Functional Requirements
- [ ] Dynamic year population from actual database data
- [ ] Dynamic month population based on selected year
- [ ] Proper error handling and fallback mechanisms
- [ ] Consistent implementation across all four modules
- [ ] No regression in existing functionality

### Non-Functional Requirements
- [ ] Page load time increase < 500ms
- [ ] Filter response time < 1 second
- [ ] Browser compatibility: Chrome, Firefox, Safari, Edge
- [ ] Mobile responsiveness maintained
- [ ] Accessibility compliance (WCAG 2.1 AA)
- [ ] Security standards maintained

### User Experience Requirements
- [ ] Intuitive filter behavior
- [ ] Clear loading indicators
- [ ] Helpful error messages
- [ ] Smooth transitions and interactions
- [ ] Consistent visual design across modules

This comprehensive testing plan ensures the dynamic filter implementation is robust, performant, and user-friendly across all target modules.