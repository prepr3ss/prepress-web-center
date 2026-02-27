# Plan Scraper Routes
from datetime import datetime
from flask import Blueprint, jsonify, request, render_template, current_app, flash, redirect, url_for
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename
import openpyxl
import os
import pytz
from sqlalchemy import or_, and_, extract, cast, String

# Import blueprint
from . import plan_scraper_bp

# Import functions to avoid circular imports
def get_db():
    from app import db
    return db

def get_require_mounting_access():
    from app import require_mounting_access
    return require_mounting_access

def get_plan_scraper_model():
    from .models import PlanScraperData
    return PlanScraperData

# Timezone untuk Jakarta
jakarta_tz = pytz.timezone('Asia/Jakarta')

# Allowed file extensions
ALLOWED_EXTENSIONS = {'xlsx', 'xls'}

def allowed_file(filename):
    """Check if file has allowed extension"""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def process_excel_file(file_path):
    """Process Excel file and extract data from specific sheets"""
    try:
        workbook = openpyxl.load_workbook(file_path, data_only=True)
        
        # Sheets to process (exclude DP sheet)
        target_sheets = ['SM2', 'SM3', 'SM4', 'SM5', 'SM6', 'VLF']
        extracted_data = []
        
        print(f"Available sheets in workbook: {workbook.sheetnames}")
        
        for sheet_name in target_sheets:
            actual_sheet_name = None
            
            # Try exact match first
            if sheet_name in workbook.sheetnames:
                actual_sheet_name = sheet_name
            else:
                # Try case-insensitive match
                for available_sheet in workbook.sheetnames:
                    if available_sheet.strip().upper() == sheet_name.upper():
                        actual_sheet_name = available_sheet
                        break
                
                # Try with spaces (e.g., 'SM 2' instead of 'SM2')
                if actual_sheet_name is None:
                    spaced_variants = [
                        sheet_name.replace('SM', 'SM '),
                        sheet_name.replace('SM', ' SM'),
                        sheet_name + ' ',
                        ' ' + sheet_name
                    ]
                    for variant in spaced_variants:
                        if variant in workbook.sheetnames:
                            actual_sheet_name = variant
                            break
            
            if actual_sheet_name is None:
                print(f"Sheet '{sheet_name}' not found in workbook")
                continue
                
            sheet = workbook[actual_sheet_name]
            print(f"Processing sheet: {actual_sheet_name} (target: {sheet_name})")
            
            # Find header row with column names
            header_row = None
            column_mapping = {}
            
            for row in sheet.iter_rows(min_row=1, max_row=10):  # Check first 10 rows for headers
                row_values = [str(cell.value).strip() if cell.value else '' for cell in row]
                
                # Check for required headers (case-insensitive)
                has_wo_sap = any('WO SAP' in val.upper() for val in row_values)
                has_no_mc_sap = any('NO MC SAP' in val.upper() for val in row_values)
                
                if has_wo_sap and has_no_mc_sap:
                    header_row = row[0].row
                    print(f"Found header row at: {header_row}")
                    
                    # Create column mapping (case-insensitive, but more specific)
                    for idx, value in enumerate(row_values):
                        val_upper = value.upper()
                        val_exact = value.strip()
                        
                        # Exact matches first (case-insensitive)
                        if val_exact.upper() == 'WO SAP':
                            column_mapping['wo_number'] = idx
                            print(f"Found WO SAP at column {idx}: '{value}'")
                        elif val_exact.upper() == 'NO MC SAP':
                            column_mapping['mc_number'] = idx
                            print(f"Found NO MC SAP at column {idx}: '{value}'")
                        elif val_exact.upper() == 'JENIS BARANG':
                            column_mapping['item_name'] = idx
                            print(f"Found Jenis Barang at column {idx}: '{value}'")
                        elif val_exact.upper() == 'UP':
                            column_mapping['num_up'] = idx
                            print(f"Found Up at column {idx}: '{value}'")
                        elif val_exact.upper() == 'SHEET':
                            column_mapping['run_length_sheet'] = idx
                            print(f"Found Sheet at column {idx}: '{value}'")
                        elif val_exact.upper() == 'KETERANGAN':
                            column_mapping['paper_desc'] = idx
                            print(f"Found Keterangan at column {idx}: '{value}'")
                        elif val_exact.upper() in ['SUPLAYER KERTAS', 'SUPPLIER KERTAS']:
                            column_mapping['paper_type'] = idx
                            print(f"Found Suplayer kertas at column {idx}: '{value}'")
                        # Fallback to partial matches only if exact matches don't work
                        elif 'WO SAP' in val_upper and 'wo_number' not in column_mapping:
                            column_mapping['wo_number'] = idx
                            print(f"Found WO SAP (partial) at column {idx}: '{value}'")
                        elif 'NO MC SAP' in val_upper and 'mc_number' not in column_mapping:
                            column_mapping['mc_number'] = idx
                            print(f"Found NO MC SAP (partial) at column {idx}: '{value}'")
                        elif 'JENIS BARANG' in val_upper and 'item_name' not in column_mapping:
                            column_mapping['item_name'] = idx
                            print(f"Found Jenis Barang (partial) at column {idx}: '{value}'")
                        elif val_upper == 'UP' and 'num_up' not in column_mapping:
                            column_mapping['num_up'] = idx
                            print(f"Found Up (exact) at column {idx}: '{value}'")
                        elif val_upper == 'SHEET' and 'run_length_sheet' not in column_mapping:
                            column_mapping['run_length_sheet'] = idx
                            print(f"Found Sheet (exact) at column {idx}: '{value}'")
                        elif 'KETERANGAN' in val_upper and 'paper_desc' not in column_mapping:
                            column_mapping['paper_desc'] = idx
                            print(f"Found Keterangan (partial) at column {idx}: '{value}'")
                        elif ('SUPLAYER KERTAS' in val_upper or 'SUPPLIER KERTAS' in val_upper) and 'paper_type' not in column_mapping:
                            column_mapping['paper_type'] = idx
                            print(f"Found Suplayer kertas (partial) at column {idx}: '{value}'")
                    
                    print(f"Column mapping: {column_mapping}")
                    break
            
            if header_row and column_mapping:
                # Extract data rows
                for row in sheet.iter_rows(min_row=header_row + 1):
                    row_values = [cell.value for cell in row]
                    
                    # Skip empty rows
                    if not any(row_values):
                        continue
                    
                    # Extract data using column mapping
                    try:
                        # Helper function to safely extract and convert values
                        def get_cell_value(col_idx):
                            if col_idx is None or col_idx >= len(row_values):
                                return None
                            cell_value = row_values[col_idx]
                            return cell_value
                        
                        # Extract raw values
                        wo_raw = get_cell_value(column_mapping.get('wo_number'))
                        mc_raw = get_cell_value(column_mapping.get('mc_number'))
                        item_raw = get_cell_value(column_mapping.get('item_name'))
                        up_raw = get_cell_value(column_mapping.get('num_up'))
                        sheet_raw = get_cell_value(column_mapping.get('run_length_sheet'))
                        desc_raw = get_cell_value(column_mapping.get('paper_desc'))
                        type_raw = get_cell_value(column_mapping.get('paper_type'))
                        
                        # Convert to appropriate types with better error handling
                        wo_number = str(wo_raw).strip() if wo_raw is not None and str(wo_raw).strip() else ''
                        mc_number = str(mc_raw).strip() if mc_raw is not None and str(mc_raw).strip() else ''
                        item_name = str(item_raw).strip() if item_raw is not None and str(item_raw).strip() else ''
                        
                        # Handle numeric values more robustly
                        try:
                            if up_raw is not None:
                                num_up = int(float(str(up_raw).replace(',', '.'))) if str(up_raw).strip() else 0
                            else:
                                num_up = 0
                        except (ValueError, TypeError):
                            num_up = 0
                        
                        try:
                            if sheet_raw is not None:
                                # Handle both integer and string representations
                                sheet_str = str(sheet_raw).strip().replace(',', '.')
                                run_length_sheet = float(sheet_str) if sheet_str else 0.0
                            else:
                                run_length_sheet = 0.0
                        except (ValueError, TypeError):
                            run_length_sheet = 0.0
                        
                        paper_desc = str(desc_raw).strip() if desc_raw is not None and str(desc_raw).strip() else ''
                        paper_type = str(type_raw).strip() if type_raw is not None and str(type_raw).strip() else ''
                        
                        # Skip if essential data is missing
                        if not wo_number or not mc_number or not item_name:
                            continue
                        
                        # Use clean machine name without spaces for storage
                        clean_machine_name = actual_sheet_name.replace(' ', '').strip()
                        extracted_data.append({
                            'print_machine': clean_machine_name,
                            'wo_number': wo_number,
                            'mc_number': mc_number,
                            'item_name': item_name,
                            'num_up': num_up,
                            'run_length_sheet': run_length_sheet,
                            'paper_desc': paper_desc,
                            'paper_type': paper_type
                        })
                        
                    except (ValueError, TypeError, IndexError) as e:
                        # Skip rows with invalid data
                        continue
        
        # Aggregate data by WO number
        PlanScraperData = get_plan_scraper_model()
        aggregated_data = PlanScraperData.aggregate_sheet_by_wo(extracted_data)
        
        # Count successfully processed sheets
        processed_sheets = []
        for sheet_name in target_sheets:
            if sheet_name in workbook.sheetnames:
                processed_sheets.append(sheet_name)
            else:
                # Check case-insensitive
                for available_sheet in workbook.sheetnames:
                    if available_sheet.strip().upper() == sheet_name.upper():
                        processed_sheets.append(sheet_name)
                        break
        
        return {
            'success': True,
            'data': aggregated_data,
            'total_records': len(aggregated_data),
            'message': f'Successfully processed {len(aggregated_data)} records from {len(processed_sheets)} sheets'
        }
        
    except Exception as e:
        return {
            'success': False,
            'error': f'Error processing Excel file: {str(e)}'
        }

@plan_scraper_bp.route('/plan-scraper')
@login_required
def plan_scraper_page():
    """Render halaman Plan Scraper"""
    require_mounting_access = get_require_mounting_access()
    return require_mounting_access(lambda: render_template('plan_scraper/dashboard.html'))()

@plan_scraper_bp.route('/plan-scraper/upload', methods=['POST'])
@login_required
def upload_excel_file():
    """Handle Excel file upload and processing"""
    require_mounting_access = get_require_mounting_access()
    return require_mounting_access(_upload_excel_file_impl)()

def _upload_excel_file_impl():
    try:
        # Check if file was uploaded
        if 'file' not in request.files:
            return jsonify({'success': False, 'error': 'No file uploaded'}), 400
        
        file = request.files['file']
        
        if file.filename == '':
            return jsonify({'success': False, 'error': 'No file selected'}), 400
        
        if not allowed_file(file.filename):
            return jsonify({'success': False, 'error': 'Invalid file type. Only Excel files (.xlsx, .xls) are allowed'}), 400
        
        # Save uploaded file
        filename = secure_filename(file.filename)
        upload_folder = current_app.config.get('UPLOADS_PATH', 'uploads')
        if not os.path.exists(upload_folder):
            os.makedirs(upload_folder)
        
        file_path = os.path.join(upload_folder, f"plan_scraper_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{filename}")
        file.save(file_path)
        
        # Process the Excel file
        result = process_excel_file(file_path)
        
        if result['success']:
            # Save processed data to database
            db = get_db()
            PlanScraperData = get_plan_scraper_model()
            
            saved_count = 0
            updated_count = 0
            
            for data_item in result['data']:
                existing_record = PlanScraperData.query.filter_by(wo_number=data_item['wo_number']).first()
                
                if existing_record:
                    # Update existing record
                    for key, value in data_item.items():
                        if hasattr(existing_record, key):
                            setattr(existing_record, key, value)
                    existing_record.updated_at = datetime.now(jakarta_tz)
                    updated_count += 1
                else:
                    # Create new record
                    new_record = PlanScraperData(
                        created_by=current_user.id,
                        **data_item
                    )
                    db.session.add(new_record)
                    saved_count += 1
            
            db.session.commit()
            
            # Clean up uploaded file
            try:
                os.remove(file_path)
            except:
                pass
            
            return jsonify({
                'success': True,
                'message': f'Successfully processed {result["total_records"]} records. Saved: {saved_count}, Updated: {updated_count}',
                'data': result['data']
            })
        else:
            # Clean up uploaded file
            try:
                os.remove(file_path)
            except:
                pass
            
            return jsonify(result), 400
            
    except Exception as e:
        return jsonify({'success': False, 'error': f'Error uploading file: {str(e)}'}), 500

@plan_scraper_bp.route('/api/plan-scraper', methods=['GET'])
@login_required
def get_plan_scraper_data():
    """Get plan scraper data with pagination and filtering"""
    require_mounting_access = get_require_mounting_access()
    return require_mounting_access(_get_plan_scraper_data_impl)()

def _get_plan_scraper_data_impl():
    try:
        db = get_db()
        PlanScraperData = get_plan_scraper_model()
        
        # Get query parameters
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 50, type=int)
        search = request.args.get('search', '', type=str)
        print_machine = request.args.get('print_machine', '', type=str)
        
        # DEBUG: Log parameters
        print(f"🔍 DEBUG: API called with parameters:")
        print(f"   page: {page}")
        print(f"   per_page: {per_page}")
        print(f"   search: '{search}'")
        print(f"   print_machine: '{print_machine}'")
        
        # Build query
        query = PlanScraperData.query
        
        # Apply filters
        if search:
            query = query.filter(
                or_(
                    PlanScraperData.wo_number.like(f'%{search}%'),
                    PlanScraperData.mc_number.like(f'%{search}%'),
                    PlanScraperData.item_name.like(f'%{search}%'),
                    PlanScraperData.paper_type.like(f'%{search}%')
                )
            )
            print(f"🔍 DEBUG: Applied search filter: '{search}'")
        
        if print_machine:
            query = query.filter(PlanScraperData.print_machine == print_machine)
            print(f"🔍 DEBUG: Applied machine filter: '{print_machine}'")
        
        # Count total records before pagination
        total_count = query.count()
        print(f"📊 DEBUG: Total records after filtering: {total_count}")
        
        # Order by created_at desc
        query = query.order_by(PlanScraperData.created_at.desc())
        
        # Paginate
        pagination = query.paginate(page=page, per_page=per_page, error_out=False)
        items = pagination.items
        
        print(f"📄 DEBUG: Pagination results:")
        print(f"   Current page: {pagination.page}")
        print(f"   Total pages: {pagination.pages}")
        print(f"   Items per page: {per_page}")
        print(f"   Items returned: {len(items)}")
        print(f"   Has prev: {pagination.has_prev}")
        print(f"   Has next: {pagination.has_next}")
        
        # Debug: Show first few WO numbers
        if items:
            wo_numbers = [item.wo_number for item in items[:5]]
            print(f"   Sample WO numbers: {wo_numbers}")
        
        return jsonify({
            'success': True,
            'data': [item.to_dict() for item in items],
            'pagination': {
                'page': page,
                'per_page': per_page,
                'total': pagination.total,
                'pages': pagination.pages,
                'has_prev': pagination.has_prev,
                'has_next': pagination.has_next
            }
        })
        
    except Exception as e:
        print(f"🚨 DEBUG: Exception in _get_plan_scraper_data_impl: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)}), 500

@plan_scraper_bp.route('/api/plan-scraper/machines', methods=['GET'])
@login_required
def get_print_machines():
    """Get list of available print machines"""
    require_mounting_access = get_require_mounting_access()
    return require_mounting_access(_get_print_machines_impl)()

def _get_print_machines_impl():
    try:
        db = get_db()
        PlanScraperData = get_plan_scraper_model()
        
        machines = db.session.query(PlanScraperData.print_machine).distinct().all()
        machine_list = [machine[0] for machine in machines if machine[0]]
        
        print(f"🖨️ DEBUG: Available machines: {machine_list}")
        
        return jsonify({
            'success': True,
            'data': machine_list
        })
        
    except Exception as e:
        print(f"🚨 DEBUG: Exception in _get_print_machines_impl: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)}), 500

@plan_scraper_bp.route('/api/plan-scraper/<int:id>', methods=['GET'])
@login_required
def get_plan_scraper_record(id):
    """Get a single plan scraper record"""
    require_mounting_access = get_require_mounting_access()
    return require_mounting_access(_get_plan_scraper_record_impl)(id)

def _get_plan_scraper_record_impl(id):
    try:
        db = get_db()
        PlanScraperData = get_plan_scraper_model()
        
        record = PlanScraperData.query.get(id)
        if not record:
            return jsonify({'success': False, 'error': 'Record not found'}), 404
        
        return jsonify({
            'success': True,
            'data': record.to_dict()
        })
        
    except Exception as e:
        print(f"🚨 DEBUG: Exception in _get_plan_scraper_record_impl: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)}), 500

@plan_scraper_bp.route('/api/plan-scraper/<int:id>', methods=['DELETE'])
@login_required
def delete_plan_scraper_record(id):
    """Delete a plan scraper record"""
    require_mounting_access = get_require_mounting_access()
    return require_mounting_access(_delete_plan_scraper_record_impl)(id)

def _delete_plan_scraper_record_impl(id):
    try:
        print(f"🗑️ DEBUG: Attempting to delete record with ID: {id}")
        db = get_db()
        PlanScraperData = get_plan_scraper_model()
        
        record = PlanScraperData.query.get(id)
        if not record:
            print(f"❌ DEBUG: Record with ID {id} not found")
            return jsonify({'success': False, 'error': 'Record not found'}), 404
        
        print(f"📋 DEBUG: Found record to delete: {record.wo_number} - {record.print_machine}")
        
        db.session.delete(record)
        db.session.commit()
        
        print(f"✅ DEBUG: Successfully deleted record with ID: {id}")
        
        return jsonify({
            'success': True,
            'message': 'Record deleted successfully'
        })
        
    except Exception as e:
        print(f"🚨 DEBUG: Exception in _delete_plan_scraper_record_impl: {str(e)}")
        import traceback
        traceback.print_exc()
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500