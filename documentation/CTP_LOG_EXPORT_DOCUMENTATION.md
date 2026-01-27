# CTP Log Export Feature Documentation

## Overview

The CTP Log Export feature provides comprehensive data export functionality for CTP problem logs, allowing users to download data in both Excel and PDF formats. The feature respects current filter settings and provides professional, well-formatted exports with robust error handling.

## Features

### Export Formats
- **Excel (.xlsx)**: Professional spreadsheet with formatted headers, borders, and auto-sized columns
- **PDF (.pdf)**: Tabular report with professional styling and proper page layout

### Exported Data Fields
- **Tanggal**: Problem date and time (formatted as "DD Mon YYYY HH:MM")
- **Problem**: Problem description
- **Solusi**: Solution description
- **Teknisi**: Technician name
- **Status**: Problem status ("Selesai" or "Berjalan")
- **Downtime**: Downtime in hours (formatted as "X.X jam")
- **Photo Reference**: File path to problem photo (if available)

### Filter Support
The export respects all current filter settings:
- **Year Filter**: Export data for specific year
- **Month Filter**: Export data for specific month
- **Vendor Filter**: Filter by technician type (Lokal, Vendor, Tidak memanggil teknisi)
- **Status Filter**: Filter by problem status (Sedang Berjalan, Selesai)
- **Search**: Full-text search across problem, solution, and technician fields

## Implementation

### Frontend Components

#### Export Service (`static/js/export_service.js`)
- Reusable JavaScript class for export functionality
- Modal interface with filter options
- Format selection (Excel/PDF)
- Robust error handling with retry logic
- User-friendly notifications
- Loading indicators

#### Export Button
- Prominent green button next to "Tambah Problem" button
- Consistent with existing UI design
- Accessible to all logged-in users

#### Export Modal
- Professional modal interface
- Current filter population from main page
- Format selection with radio buttons
- All filter options available

### Backend API (`/export-ctp-logs`)

#### Endpoint Details
- **URL**: `/impact/export-ctp-logs`
- **Method**: GET
- **Authentication**: Required (@login_required)
- **Parameters**:
  - `machine_nickname` (required): Machine identifier
  - `format` (optional): "excel" or "pdf" (default: "excel")
  - `year` (optional): Year filter
  - `month` (optional): Month filter
  - `technician_type` (optional): Vendor filter
  - `status` (optional): Status filter
  - `search` (optional): Search term

#### Response Handling
- **Success**: File download with appropriate Content-Type
- **Error**: JSON response with error details
- **File Naming**: `ctp_log_{machine}_{timestamp}.{ext}`

#### Export Functions

##### Excel Export (`generate_excel_export`)
- Uses openpyxl library
- Professional styling with headers
- Auto-sized columns
- Borders and alignment
- Machine name and period in header rows

##### PDF Export (`generate_pdf_export`)
- Uses ReportLab library
- Professional tabular layout
- Proper page formatting
- Machine name and period in header
- Table with headers and data rows

## Error Handling

### Frontend Error Handling
- **Network Errors**: Retry logic with exponential backoff
- **Timeout Handling**: User-friendly timeout messages
- **Permission Errors**: Clear authentication/authorization messages
- **Server Errors**: Graceful degradation with helpful messages

### Backend Error Handling
- **Validation**: Parameter validation with clear error messages
- **Data Not Found**: 404 response for empty datasets
- **File Generation**: Exception handling for export failures
- **Logging**: Comprehensive error logging for debugging

## User Experience

### Loading Indicators
- Full-screen overlay during export
- Progress feedback for large datasets
- Clear status messages

### Notifications
- **Success**: File download confirmation with filename
- **Warning**: Retry attempts and temporary issues
- **Error**: Clear error messages with guidance
- **Info**: Export progress updates

### File Downloads
- Automatic file download initiation
- Proper filename generation with timestamps
- Browser-compatible file handling

## Security Considerations

### Access Control
- Export requires user authentication
- Machine access validation
- Filter parameter sanitization

### Data Protection
- SQL injection prevention through ORM queries
- Parameter validation and sanitization
- File size limitations for large exports

## Usage Examples

### Basic Export
1. Navigate to CTP machine log detail page
2. Click "Export Data" button
3. Select format (Excel or PDF)
4. Adjust filters if needed
5. Click "Export" button
6. File downloads automatically

### Advanced Filtering
1. Set desired filters on main page (year, month, vendor, status, search)
2. Click "Export Data" button
3. Export modal shows current filter values
4. Confirm export with selected format
5. Filtered data exported

## Technical Specifications

### Dependencies
- **Frontend**: Bootstrap 5.3.3, Export Service class
- **Backend**: Flask, SQLAlchemy, openpyxl, ReportLab
- **Database**: CTPProblemLog model with relationships

### Performance
- Efficient database queries with proper indexing
- Memory-efficient file generation
- Streaming for large datasets
- Connection pooling for concurrent requests

### Browser Compatibility
- Modern browsers (Chrome, Firefox, Safari, Edge)
- Mobile-responsive modal interface
- Cross-platform file download support

## File Structure

### Created Files
- `static/js/export_service.js`: Export service implementation
- `static/css/export_styles.css`: Export-specific styling
- `templates/log_ctp_detail.html`: Updated with export button
- `app.py`: New export endpoint and functions

### Modified Files
- `templates/log_ctp_detail.html`: Added export integration
- `app.py`: Added `/export-ctp-logs` route

## Testing

### Test Scenarios
1. **Basic Export**: Export without filters
2. **Filtered Export**: Export with various filter combinations
3. **Format Testing**: Both Excel and PDF formats
4. **Error Handling**: Network errors, invalid parameters
5. **Large Datasets**: Performance with extensive data
6. **Edge Cases**: Empty datasets, special characters

### Validation Checklist
- [ ] Export button appears and functions correctly
- [ ] Modal opens with current filter values
- [ ] Excel export generates valid .xlsx file
- [ ] PDF export generates valid .pdf file
- [ ] All data fields included correctly
- [ ] Filters work as expected
- [ ] Error handling works properly
- [ ] File downloads automatically
- [ ] Loading indicators function correctly

## Maintenance

### Monitoring
- Export usage analytics
- Error rate monitoring
- Performance metrics tracking
- User feedback collection

### Updates
- Regular dependency updates
- Security patch application
- Feature enhancement based on user feedback

## Support

### Troubleshooting
- **Export Fails**: Check network connection, verify permissions
- **File Corruption**: Ensure browser compatibility, clear cache
- **Performance Issues**: Apply additional filters, reduce dataset size
- **Access Denied**: Verify user authentication and machine access

### Contact Information
- **Technical Issues**: Contact system administrator
- **Feature Requests**: Submit through proper channels
- **Documentation Updates**: Check version history

---

**Version**: 1.0.0  
**Last Updated**: 2025-11-25  
**Compatibility**: Impact 360 v2.0+