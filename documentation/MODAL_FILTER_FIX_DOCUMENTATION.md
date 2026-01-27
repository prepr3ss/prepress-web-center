# Fix for 'Detail Plate Not Good' Modal Filtering Issue

## Problem Description

The 'Detail Plate Not Good' modal in the CTP dashboard was only displaying data when time filters were set to 'all years' and 'all months'. When users selected a specific year or month, the modal incorrectly showed 'No plate not good data', even if data existed for that period.

## Root Cause Analysis

The issue was in the `/api/ctp-production-logs/not-good-details` endpoint in `app.py`. There were two main problems:

1. **Parameter Type Conversion Issue**: 
   - The original code used `request.args.get('year', type=int)` and `request.args.get('month', type=int)`
   - When the value was an empty string (representing "all years" or "all months"), the `type=int` conversion returned `None`
   - The conditional checks `if year:` and `if month:` evaluated to `False` when the value was `None`, so no filtering was applied
   - However, when a specific year or month was selected, the integer conversion worked correctly

2. **Incorrect SQLAlchemy Extract Syntax**:
   - The original code used `extract(CTPProductionLog.log_date, 'year')` which is not the correct SQLAlchemy syntax
   - The correct syntax should be `extract('year', CTPProductionLog.log_date)`

## Solution Implemented

### 1. Fixed Parameter Handling

**Before:**
```python
year = request.args.get('year', type=int)
month = request.args.get('month', type=int)
```

**After:**
```python
# Get filter parameters - handle as strings first to properly detect empty values
year_str = request.args.get('year', '').strip()
month_str = request.args.get('month', '').strip()

# Convert to integers only if not empty
year = int(year_str) if year_str else None
month = int(month_str) if month_str else None
```

### 2. Fixed Conditional Checks

**Before:**
```python
if year:
    query = query.filter(extract(CTPProductionLog.log_date, 'year') == year)
if month:
    query = query.filter(extract(CTPProductionLog.log_date, 'month') == month)
```

**After:**
```python
if year is not None:
    query = query.filter(extract('year', CTPProductionLog.log_date) == year)
if month is not None:
    query = query.filter(extract('month', CTPProductionLog.log_date) == month)
```

### 3. Improved Debug Information

Updated the debug response to properly handle None values:

```python
'debug': {
    'filters_applied': {
        'year': year if year is not None else 'All',
        'month': month if month is not None else 'All',
        'category': category if category else 'All',
        'group': group if group else 'All'
    },
    'total_logs_found': len(logs)
}
```

## Files Modified

1. **app.py** (lines 6298-6370):
   - Fixed parameter handling for year and month filters
   - Corrected SQLAlchemy extract syntax
   - Improved debug information

## Testing

A test script `test_modal_filter_fix.py` has been created to verify the fix. The script tests various filter combinations:

1. All years, all months (default behavior)
2. Specific year only
3. Specific year and month
4. Specific category
5. Specific group
6. Combination of filters

To run the test:
```bash
python test_modal_filter_fix.py
```

## Expected Behavior After Fix

1. **Default filters** (all years, all months): Shows all not-good plate records
2. **Specific year**: Shows only records from the selected year
3. **Specific month**: Shows only records from the selected month (across all years)
4. **Year and month**: Shows only records from the selected year-month combination
5. **Category filter**: Shows only records matching the selected not-good reason
6. **Group filter**: Shows only records from the selected group
7. **Combined filters**: Shows records matching all selected criteria

## Backward Compatibility

The fix maintains full backward compatibility:
- The API endpoint structure remains unchanged
- Response format is the same
- Default behavior (all years/months) is preserved
- All existing filter combinations continue to work

## Summary

The fix addresses the core issue where specific year/month filters were not working due to improper parameter handling and incorrect SQLAlchemy syntax. The solution ensures that:
1. Empty filter values are properly handled as "all" selections
2. Specific filter values are correctly applied to the database query
3. The default functionality remains intact
4. Debug information accurately reflects the applied filters