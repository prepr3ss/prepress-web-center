from flask import Flask, render_template, request, jsonify, abort, redirect, url_for, flash, session, send_file
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps
from datetime import datetime, time
import os
import random
import pymysql
from plate_mappings import PlateTypeMapping
from io import BytesIO
import openpyxl
from openpyxl.styles import Font, Alignment, PatternFill
from openpyxl.utils import get_column_letter
from urllib.parse import quote_plus
from sqlalchemy import and_, or_, cast, String, extract, func
from bon_routes import init_bon_routes, PLATE_DETAILS
from flask_migrate import Migrate
import pytz
from flask import jsonify, flash
import locale


# Impor konfigurasi database Anda dari config.py
from config import DB_CONFIG
from datetime import datetime, time, timedelta

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key-here-change-in-production'  # Ganti dengan key yang aman

# Konfigurasi Flask-Login
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'
login_manager.login_message = 'Silakan login untuk mengakses halaman ini.'
login_manager.login_message_category = 'info'

# Konfigurasi Database MySQL menggunakan DB_CONFIG dari config.py
db_user = DB_CONFIG['user']
db_password = quote_plus(DB_CONFIG['password'])
db_host = DB_CONFIG['host']
db_name = DB_CONFIG['database']
db_port = DB_CONFIG['port']

app.config['SQLALCHEMY_DATABASE_URI'] = f'mysql+pymysql://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
migrate = Migrate(app, db)

import csv
from io import StringIO
from flask import make_response
from datetime import datetime, timedelta

# --- Notifikasi Bulet ---
@app.route('/api/check-notifications')
@login_required
def check_notifications():
    notifications = {
        # Ganti 'ctp' dengan 'ctp_adjustment' dan 'ctp_bon'
        'ctp_adjustment': [], 
        'ctp_bon': [],
        'pdnd': [],
        'design': [],
        'mounting': [],
    }
    
    try:
        ctp_states = ['proses_ctp', 'proses_plate', 'antar_plate']
        
        # CTP Adjustment notifications
        notifications['ctp_adjustment'] = PlateAdjustmentRequest.query.filter(
            PlateAdjustmentRequest.status.in_(ctp_states)
        ).all()
        
        # CTP Bon notifications
        notifications['ctp_bon'] = PlateBonRequest.query.filter(
            PlateBonRequest.status.in_(ctp_states)
        ).all()

        # PDND notifications (menggunakan logika pemisahan is_epson yang sudah benar)
        pdnd_states = ['menunggu_adjustment_pdnd', 'proses_adjustment_pdnd']
        pdnd_q = PlateAdjustmentRequest.query.filter(PlateAdjustmentRequest.status.in_(pdnd_states))
        pdnd_q_ditolak = PlateAdjustmentRequest.query.filter(
            PlateAdjustmentRequest.status == 'ditolakmounting',
            PlateAdjustmentRequest.is_epson == False 
        )
        notifications['pdnd'] = pdnd_q.all() + pdnd_q_ditolak.all()
        
        # ... (Logika Design dan Mounting tetap sama)
        design_states = ['menunggu_adjustment_design', 'proses_adjustment_design']
        design_q = PlateAdjustmentRequest.query.filter(PlateAdjustmentRequest.status.in_(design_states))
        design_q_ditolak = PlateAdjustmentRequest.query.filter(
            PlateAdjustmentRequest.status == 'ditolakmounting',
            PlateAdjustmentRequest.is_epson == True
        )
        notifications['design'] = design_q.all() + design_q_ditolak.all()

        mounting_states = ['menunggu_adjustment', 'proses_adjustment', 'ditolakctp']
        notifications['mounting'] = PlateAdjustmentRequest.query.filter(
            PlateAdjustmentRequest.status.in_(mounting_states)
        ).all()


        # Pastikan data yang dikirim ke frontend hanyalah list status
        return jsonify({
            'ctp_adjustment': [{'status': item.status} for item in notifications['ctp_adjustment']],
            'ctp_bon': [{'status': item.status} for item in notifications['ctp_bon']],
            'pdnd': [{'status': item.status} for item in notifications['pdnd']],
            'design': [{'status': item.status} for item in notifications['design']],
            'mounting': [{'status': item.status} for item in notifications['mounting']]
        })

    except Exception as e:
        print(f"Error checking notifications: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

# --- Export Routes ---
@app.route('/export-chemical-bon')
@login_required
def export_chemical_bon():
    try:
        # Set locale to Indonesian for date formatting
        try:
            # For systems that support UTF-8 (e.g., Linux, macOS)
            locale.setlocale(locale.LC_TIME, 'id_ID.UTF-8')
        except locale.Error:
            # Fallback for systems that might not support UTF-8 suffix (e.g., some Windows versions)
            locale.setlocale(locale.LC_TIME, 'id_ID')
        
        # Get query parameters
        date_from = request.args.get('date_from')
        date_to = request.args.get('date_to')
        brand_filter = request.args.get('brand') # This is the original filter value

        # Convert string dates to datetime objects
        start_date = datetime.strptime(date_from, '%Y-%m-%d').date() if date_from else None
        end_date = datetime.strptime(date_to, '%Y-%m-%d').date() if date_to else None

        # Create new workbook
        wb = openpyxl.Workbook()
        
        # Define styles
        title_font = Font(bold=True, size=24)
        subtitle_font = Font(bold=True, size=18)
        header_font = Font(bold=True)
        center_alignment = Alignment(horizontal='center', vertical='center')
        left_alignment = Alignment(horizontal='left', vertical='center')
        
        # Define border style once
        thin_border = Border(
            left=Side(style='thin'),
            right=Side(style='thin'),
            top=Side(style='thin'),
            bottom=Side(style='thin')
        )
        header_fill = PatternFill(start_color='E0E0E0', end_color='E0E0E0', fill_type='solid')

        # Determine which brands to process
        if brand_filter:
            brands_to_process = [brand_filter]
            # Use the actual brand_filter for download name if a specific brand is selected
            download_brand_suffix = f"_{brand_filter.replace(' ', '_')}" 
        else:
            # Mengambil daftar brand unik dari database
            brands_to_process = db.session.query(ChemicalBonCTP.brand).distinct().all()
            brands_to_process = [brand[0] for brand in brands_to_process]
            # If no specific brand filter, use "_all" for download name
            download_brand_suffix = "_all"


        # Create sheet for each brand
        for idx, brand in enumerate(brands_to_process):
            # Build query for current brand
            query = ChemicalBonCTP.query.filter(ChemicalBonCTP.brand == brand)
            
            if start_date and end_date:
                query = query.filter(ChemicalBonCTP.tanggal.between(start_date, end_date))
            
            records = query.order_by(ChemicalBonCTP.tanggal.asc()).all()
            
            # Only create a sheet if there are records for this brand
            if not records and len(brands_to_process) > 1: # Skip if no records and multiple brands
                continue
            elif not records and len(brands_to_process) == 1: # If only one brand chosen and no records, still create an empty sheet
                if idx == 0:
                    ws = wb.active
                    ws.title = brand
                else:
                    ws = wb.create_sheet(brand)
                # Ensure the sheet has basic headers even if empty
                ws.merge_cells('A1:K1')
                ws['A1'] = 'Laporan Chemical Bon CTP'
                ws['A1'].font = title_font
                ws['A1'].alignment = center_alignment
                ws.merge_cells('A2:K2')
                ws['A2'] = f'{brand}'
                ws['A2'].font = subtitle_font
                ws['A2'].alignment = center_alignment
                
                date_range_str = ""
                if start_date and end_date:
                    date_range_str = f'{start_date.strftime("%#d %B %Y")} s/d {end_date.strftime("%#d %B %Y")}'
                elif start_date:
                    date_range_str = f'Dari {start_date.strftime("%#d %B %Y")}'
                elif end_date:
                    date_range_str = f'Sampai {end_date.strftime("%#d %B %Y")}'
                ws.merge_cells('A3:K3')
                ws['A3'] = date_range_str
                ws['A3'].font = subtitle_font
                ws['A3'].alignment = center_alignment

                headers = ['Tanggal', 'Bon Number', 'Request Number', 'Brand', 'Item Code', 'Item Name', 
                           'Unit', 'Jumlah', 'PIC', 'Keterangan', 'Periode']
                for col, header in enumerate(headers, 1):
                    cell = ws.cell(row=5, column=col, value=header)
                    cell.font = header_font
                    cell.fill = header_fill
                    cell.alignment = center_alignment
                    cell.border = thin_border
                continue # Go to next brand


            # Create or get sheet
            if idx == 0: # For the first brand, use the active sheet
                ws = wb.active
                ws.title = brand
            else: # For subsequent brands, create a new sheet
                ws = wb.create_sheet(brand)

            # Set column widths
            column_widths = [20, 20, 20, 15, 20, 40, 10, 10, 20, 30, 20]
            for i, width in enumerate(column_widths, 1):
                ws.column_dimensions[get_column_letter(i)].width = width

            # Write main title and subtitle
            ws.merge_cells('A1:K1')
            ws['A1'] = 'Laporan Chemical Bon CTP'
            ws['A1'].font = title_font
            ws['A1'].alignment = center_alignment

            ws.merge_cells('A2:K2')
            ws['A2'] = f'{brand}'
            ws['A2'].font = subtitle_font
            ws['A2'].alignment = center_alignment
            
            # Use `strftime` for the date range header
            date_range_str = ""
            if start_date and end_date:
                date_range_str = f'{start_date.strftime("%#d %B %Y")} s/d {end_date.strftime("%#d %B %Y")}'
            elif start_date:
                date_range_str = f'Dari {start_date.strftime("%#d %B %Y")}'
            elif end_date:
                date_range_str = f'Sampai {end_date.strftime("%#d %B %Y")}'

            ws.merge_cells('A3:K3')
            ws['A3'] = date_range_str
            ws['A3'].font = subtitle_font
            ws['A3'].alignment = center_alignment

            # Headers row
            headers = ['Tanggal', 'Bon Number', 'Request Number', 'Brand', 'Item Code', 'Item Name', 
                       'Unit', 'Jumlah', 'PIC', 'Keterangan', 'Periode']
            
            for col, header in enumerate(headers, 1):
                cell = ws.cell(row=5, column=col, value=header)
                cell.font = header_font
                cell.fill = header_fill
                cell.alignment = center_alignment
                cell.border = thin_border # Apply border to header cells

            # Write data
            for row_idx, record in enumerate(records, 6):
                # Use `strftime` for the record date
                tanggal_str = record.tanggal.strftime('%#d %B %Y') if record.tanggal else ''
                data = [
                    tanggal_str,
                    record.bon_number,
                    record.request_number,
                    record.brand,
                    record.item_code,
                    record.item_name,
                    record.unit,
                    record.jumlah,
                    record.user.name if record.user else '',
                    record.wo_number if record.wo_number else '',  # Keterangan diisi dengan WO number
                    record.bon_periode
                ]
                
                for col_idx, value in enumerate(data, 1):
                    cell = ws.cell(row=row_idx, column=col_idx, value=value)
                    # Use center alignment for most columns, left for specific text columns
                    cell.alignment = Alignment(horizontal='center' if col_idx not in [5, 6, 9, 10] else 'left')
                    cell.border = thin_border # Apply border to data cells

        # Remove the default empty sheet created by openpyxl if it exists and we've created other sheets
        # Or if no data was found and the default sheet is the only one
        if "Sheet" in wb.sheetnames:
            if len(brands_to_process) > 0 and len(wb.sheetnames) > 1:
                del wb["Sheet"]
            elif len(brands_to_process) == 0: # If no brands were found at all
                del wb["Sheet"]


        # Create response
        output = BytesIO()
        wb.save(output)
        output.seek(0)

        # Use the determined download_brand_suffix here
        return send_file(
            output,
            mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            as_attachment=True,
            download_name=f'chemical_bon{download_brand_suffix}_export_{datetime.now().strftime("%Y%m%d_%H%M%S")}.xlsx'
        )

    except Exception as e:
        print(f"Error in export: {str(e)}")
        return jsonify({'success': False, 'message': f'Export gagal: {str(e)}'}), 500

# --- Access Control Decorators ---
def require_admin(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            flash('Silakan login terlebih dahulu.', 'warning')
            return redirect(url_for('login'))
        if not current_user.is_admin():
            flash('Akses ditolak. Hanya admin yang dapat mengakses halaman ini.', 'error')
            return redirect(url_for('index'))
        return f(*args, **kwargs)
    return decorated_function

def require_ctp_access(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            return redirect(url_for('login'))
        if not current_user.can_access_ctp():
            flash('Akses ditolak. Anda tidak memiliki akses ke divisi CTP.', 'error')
            return redirect(url_for('index'))
        return f(*args, **kwargs)
    return decorated_function

def require_press_access(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            return redirect(url_for('login'))
        if not current_user.can_access_press():
            flash('Akses ditolak. Anda tidak memiliki akses ke divisi Press.', 'error')
            return redirect(url_for('index'))
        return f(*args, **kwargs)
    return decorated_function

def require_mounting_access(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            return redirect(url_for('login'))
        if not current_user.can_access_mounting():
            flash('Akses ditolak. Anda tidak memiliki akses ke divisi Mounting.', 'error')
            return redirect(url_for('index'))
        return f(*args, **kwargs)
    return decorated_function

def require_pdnd_access(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            return redirect(url_for('login'))
        if not current_user.can_access_pdnd():
            flash('Akses ditolak. Anda tidak memiliki akses ke divisi PDND.', 'error')
            return redirect(url_for('index'))
        return f(*args, **kwargs)
    return decorated_function

def require_design_access(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            return redirect(url_for('login'))
        if not current_user.can_access_design():
            flash('Akses ditolak. Anda tidak memiliki akses ke divisi Design.', 'error')
            return redirect(url_for('index'))
        return f(*args, **kwargs)
    return decorated_function

# User loader callback untuk Flask-Login
@login_manager.user_loader
def load_user(user_id):
    return db.session.get(User, int(user_id))

@app.route('/settings/change-password', methods=['GET', 'POST'])
@login_required
def change_password():
    if request.method == 'POST':
        current_password = request.form.get('current_password')
        new_password = request.form.get('new_password')
        confirm_password = request.form.get('confirm_password')

        # Verify current password
        if not check_password_hash(current_user.password_hash, current_password):
            flash('Password saat ini tidak benar', 'danger')
            return redirect(url_for('change_password'))

        # Verify password confirmation
        if new_password != confirm_password:
            flash('Password baru dan konfirmasi password tidak cocok', 'danger')
            return redirect(url_for('change_password'))

        # Update password
        current_user.password_hash = generate_password_hash(new_password)
        db.session.commit()
        
        flash('Password berhasil diubah', 'success')
        return redirect(url_for('change_password'))

    return render_template('change_password.html')

# Definisi Model Database untuk User Authentication
class Division(db.Model):
    __tablename__ = 'divisions'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False, unique=True)
    description = db.Column(db.String(255), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationship dengan User
    users = db.relationship('User', backref='division', lazy=True)
    
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'created_at': self.created_at
        }

class User(UserMixin, db.Model):
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), nullable=False, unique=True)
    password_hash = db.Column(db.String(255), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), nullable=True)
    role = db.Column(db.String(20), nullable=False, default='user')
    division_id = db.Column(db.Integer, db.ForeignKey('divisions.id'), nullable=True)
    grup = db.Column(db.String(10), nullable=True)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def set_password(self, password):
        """Set password hash"""
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        """Check if password matches hash"""
        return check_password_hash(self.password_hash, password)
        
    def is_admin(self):
        """Check if user is admin"""
        return self.role == 'admin'
    
    def get_division_name(self):
        """Get division name"""
        if self.division:
            return self.division.name
        return None
    
    def is_admin(self):
        """Check if user is admin"""
        return self.role == 'admin'
    
    def is_operator(self):
        """Check if user is operator"""
        return self.role == 'operator'
    
    def can_access_division(self, division_name):
        """Check if user can access specific division"""
        if self.is_admin():
            return True  # Admin can access all divisions
        
        if self.is_operator():
            return self.get_division_name() == division_name
        
        return False
    
    def can_access_ctp(self):
        """Check if user can access CTP production"""
        return self.can_access_division('CTP')

    def can_access_pdnd(self):
        """Check if user can access PDND production"""
        return self.can_access_division('PDND')

    def can_access_design(self):
        """Check if user can access Design production"""
        return self.can_access_division('DESIGN')

    def can_access_mounting(self):
        """Check if user can access Mounting production"""
        return self.can_access_division('MOUNTING')
    
    def can_access_press(self):
        """Check if user can access Press production"""
        return self.can_access_division('PRESS')
    
    def get_accessible_divisions(self):
        """Get list of divisions user can access"""
        if self.is_admin():
            return Division.query.all()
        elif self.is_operator() and self.division:
            return [self.division]
        else:
            return []

    def to_dict(self):
        return {
            'id': self.id,
            'username': self.username,
            'name': self.name,
            'email': self.email,
            'role': self.role,
            'division_id': self.division_id,
            'division_name': self.get_division_name(),
            'grup': self.grup,
            'created_at': self.created_at,
            'updated_at': self.updated_at
        }

# Definisi Model Database
class CTPProductionLog(db.Model):
    __tablename__ = 'ctp_production_logs'

    id = db.Column(db.Integer, primary_key=True)
    log_date = db.Column(db.Date, nullable=False)
    ctp_group = db.Column(db.String(50), nullable=False)
    ctp_shift = db.Column(db.String(50), nullable=False)
    ctp_pic = db.Column(db.String(100), nullable=False)
    ctp_machine = db.Column(db.String(50), nullable=False)
    processor_temperature = db.Column(db.Float)
    dwell_time = db.Column(db.Float)
    wo_number = db.Column(db.String(100))
    mc_number = db.Column(db.String(100), nullable=False)
    run_length_sheet = db.Column(db.Integer)
    print_machine = db.Column(db.String(50), nullable=False)
    remarks_job = db.Column(db.String(50), nullable=False)
    item_name = db.Column(db.String(255), nullable=False)
    note = db.Column(db.String(255))
    plate_type_material = db.Column(db.String(100), nullable=False)
    raster = db.Column(db.String(50), nullable=False)
    num_plate_good = db.Column(db.Integer)
    num_plate_not_good = db.Column(db.Integer)
    not_good_reason = db.Column(db.String(255))
    cyan_25_percent = db.Column(db.Float)
    cyan_50_percent = db.Column(db.Float)
    cyan_75_percent = db.Column(db.Float)
    magenta_25_percent = db.Column(db.Float)
    magenta_50_percent = db.Column(db.Float)
    magenta_75_percent = db.Column(db.Float)
    yellow_25_percent = db.Column(db.Float)
    yellow_50_percent = db.Column(db.Float)
    yellow_75_percent = db.Column(db.Float)
    black_25_percent = db.Column(db.Float)
    black_50_percent = db.Column(db.Float)
    black_75_percent = db.Column(db.Float)
    x_25_percent = db.Column(db.Float)
    x_50_percent = db.Column(db.Float)
    x_75_percent = db.Column(db.Float)
    z_25_percent = db.Column(db.Float)
    z_50_percent = db.Column(db.Float)
    z_75_percent = db.Column(db.Float)
    u_25_percent = db.Column(db.Float)
    u_50_percent = db.Column(db.Float)
    u_75_percent = db.Column(db.Float)
    v_25_percent = db.Column(db.Float)
    v_50_percent = db.Column(db.Float)
    v_75_percent = db.Column(db.Float)
    start_time = db.Column(db.Time)   # UBAH INI: dari db.String menjadi db.Time
    finish_time = db.Column(db.Time)  # UBAH INI: dari db.String menjadi db.Time
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id,
            'log_date': self.log_date.strftime('%Y-%m-%d') if self.log_date else None,
            'ctp_group': self.ctp_group,
            'ctp_shift': self.ctp_shift,
            'ctp_pic': self.ctp_pic,
            'ctp_machine': self.ctp_machine,
            'processor_temperature': self.processor_temperature,
            'dwell_time': self.dwell_time,
            'wo_number': self.wo_number,
            'mc_number': self.mc_number,
            'run_length_sheet': self.run_length_sheet,
            'print_machine': self.print_machine,
            'remarks_job': self.remarks_job,
            'item_name': self.item_name,
            'note': self.note,
            'plate_type_material': self.plate_type_material,
            'raster': self.raster,
            'num_plate_good': self.num_plate_good,
            'num_plate_not_good': self.num_plate_not_good,
            'not_good_reason': self.not_good_reason,
            'cyan_25_percent': self.cyan_25_percent,
            'cyan_50_percent': self.cyan_50_percent,
            'cyan_75_percent': self.cyan_75_percent,
            'magenta_25_percent': self.magenta_25_percent,
            'magenta_50_percent': self.magenta_50_percent,
            'magenta_75_percent': self.magenta_75_percent,
            'yellow_25_percent': self.yellow_25_percent,
            'yellow_50_percent': self.yellow_50_percent,
            'yellow_75_percent': self.yellow_75_percent,
            'black_25_percent': self.black_25_percent,
            'black_50_percent': self.black_50_percent,
            'black_75_percent': self.black_75_percent,
            'x_25_percent': self.x_25_percent,
            'x_50_percent': self.x_50_percent,
            'x_75_percent': self.x_75_percent,
            'z_25_percent': self.z_25_percent,
            'z_50_percent': self.z_50_percent,
            'z_75_percent': self.z_75_percent,
            'u_25_percent': self.u_25_percent,
            'u_50_percent': self.u_50_percent,
            'u_75_percent': self.u_75_percent,
            'v_25_percent': self.v_25_percent,
            'v_50_percent': self.v_50_percent,
            'v_75_percent': self.v_75_percent,
            'start_time': self.start_time.strftime('%H:%M') if self.start_time else None, # UBAH INI
            'finish_time': self.finish_time.strftime('%H:%M') if self.finish_time else None, # UBAH INI
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }

class PlateAdjustmentRequest(db.Model):
    __tablename__ = 'plate_adjustment_requests'

    id = db.Column(db.Integer, primary_key=True)
    tanggal = db.Column(db.Date, nullable=False)
    mesin_cetak = db.Column(db.String(100), nullable=False)
    pic = db.Column(db.String(100), nullable=False)
    remarks = db.Column(db.String(100), nullable=False)  # PRODUKSI/PROOF
    wo_number = db.Column(db.String(100), nullable=False)
    mc_number = db.Column(db.String(100), nullable=False)
    run_length = db.Column(db.Integer, nullable=True)
    item_name = db.Column(db.String(255), nullable=False)
    ctp_group = db.Column(db.String(50), nullable=True)  # Kolom baru untuk grup CTP
    jumlah_plate = db.Column(db.Integer, nullable=False)
    note = db.Column(db.String(255), nullable=True)

    machine_off_at = db.Column(db.DateTime, default=datetime.utcnow)

    is_epson = db.Column(db.Boolean, default=False)

    pdnd_start_at = db.Column(db.DateTime, nullable=True)
    pdnd_finish_at = db.Column(db.DateTime, nullable=True)
    pdnd_by = db.Column(db.String(100), nullable=True)

    design_start_at = db.Column(db.DateTime, nullable=True)
    design_finish_at = db.Column(db.DateTime, nullable=True)
    design_by = db.Column(db.String(100), nullable=True)      

    adjustment_start_at = db.Column(db.DateTime, nullable=True)
    adjustment_finish_at = db.Column(db.DateTime, nullable=True)
    adjustment_by = db.Column(db.String(100), nullable=True)

    plate_start_at = db.Column(db.DateTime, nullable=True)
    plate_finish_at = db.Column(db.DateTime, nullable=True)
    plate_delivered_at = db.Column(db.DateTime, nullable=True)
    ctp_by = db.Column(db.String(100), nullable=True)

    declined_at = db.Column(db.DateTime, nullable=True)
    declined_by = db.Column(db.String(100), nullable=True)
    decline_reason = db.Column(db.Text, nullable=True)
    is_declined = db.Column(db.Boolean, default=False)

    cancelled_at = db.Column(db.DateTime, nullable=True)
    cancellation_reason = db.Column(db.Text, nullable=True)
    cancelled_by = db.Column(db.String(100), nullable=True)

# Ubah default status menjadi property yang bergantung pada remarks
    status = db.Column(db.String(30))

    def __init__(self, **kwargs):
        super(PlateAdjustmentRequest, self).__init__(**kwargs)
        self.set_initial_status()

    def set_initial_status(self):
        """Set status awal berdasarkan prioritas: Curve > EPSON (FA) > Non-EPSON (FA)."""
        
        fa_remarks = ['ADJUSTMENT FA PROOF', 'ADJUSTMENT FA PRODUKSI']
        curve_remarks = ['ADJUSTMENT CURVE PROOF', 'ADJUSTMENT CURVE PRODUKSI']
        
        # 1. Prioritas Tertinggi: Cek Remarks CURVE
        # Jika Remarks adalah CURVE, abaikan is_epson, langsung ke 'menunggu_adjustment'
        if self.remarks and self.remarks.upper() in curve_remarks:
            self.status = 'menunggu_adjustment' 
            
        # 2. Prioritas Kedua: Cek Item EPSON (Hanya berlaku untuk FA)
        # Jika Remarks adalah FA DAN is_epson = True, kirim ke 'design'
        elif self.is_epson and self.remarks and self.remarks.upper() in fa_remarks:
            self.status = 'menunggu_adjustment_design'

        # 3. Prioritas Ketiga: Cek Remarks FA (Non-EPSON)
        # Jika Remarks adalah FA DAN is_epson = False, kirim ke 'pdnd'
        elif self.remarks and self.remarks.upper() in fa_remarks:
            self.status = 'menunggu_adjustment_pdnd'
            
        else:
            # Status default (untuk jaga-jaga, atau jika ada remarks yang tidak dikenal)
            self.status = 'menunggu_adjustment' # Atau status default lain yang paling sesuai

    def to_dict(self):
        return {
            'id': self.id,
            'tanggal': self.tanggal.strftime('%Y-%m-%d') if self.tanggal else None,
            'mesin_cetak': self.mesin_cetak,
            'pic': self.pic,
            'remarks': self.remarks,
            'wo_number': self.wo_number,
            'mc_number': self.mc_number,
            'run_length': self.run_length,
            'item_name': self.item_name,
            'jumlah_plate': self.jumlah_plate,
            'note': self.note,
            'machine_off_at': self.machine_off_at.isoformat() if self.machine_off_at else None,
            'is_epson': self.is_epson,
            'design_start_at': self.design_start_at.isoformat() if self.design_start_at else None,
            'design_finish_at': self.design_finish_at.isoformat() if self.design_finish_at else None,
            'design_by': self.design_by,
            'pdnd_start_at': self.pdnd_start_at.isoformat() if self.pdnd_start_at else None,
            'pdnd_finish_at': self.pdnd_finish_at.isoformat() if self.pdnd_finish_at else None,
            'pdnd_by': self.pdnd_by,
            'adjustment_start_at': self.adjustment_start_at.isoformat() if self.adjustment_start_at else None,
            'adjustment_finish_at': self.adjustment_finish_at.isoformat() if self.adjustment_finish_at else None,
            'adjustment_by': self.adjustment_by,
            'plate_start_at': self.plate_start_at.isoformat() if self.plate_start_at else None,
            'plate_finish_at': self.plate_finish_at.isoformat() if self.plate_finish_at else None,
            'plate_delivered_at': self.plate_delivered_at.isoformat() if self.plate_delivered_at else None,
            'ctp_by': self.ctp_by,
            'ctp_group': self.ctp_group,
            'status': self.status,
            'declined_at': self.declined_at.isoformat() if self.declined_at else None,
            'declined_by': self.declined_by,
            'decline_reason': self.decline_reason,
            'is_declined': self.is_declined,
            'cancelled_at': self.cancelled_at.isoformat() if self.cancelled_at else None,
            'cancellation_reason': self.cancellation_reason,
            'cancelled_by': self.cancelled_by
        }

#def bon table

class MonthlyWorkHours(db.Model):
    __tablename__ = 'monthly_work_hours'
    id = db.Column(db.Integer, primary_key=True)
    year = db.Column(db.Integer, nullable=False)
    month = db.Column(db.Integer, nullable=False)
    total_work_hours_produksi = db.Column(db.Float, nullable=False)
    total_work_hours_proof = db.Column(db.Float, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id,
            'year': self.year,
            'month': self.month,
            'total_work_hours_produksi': self.total_work_hours_produksi,
            'total_work_hours_proof': self.total_work_hours_proof,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }

class ChemicalBonCTP(db.Model):
    __tablename__ = 'chemical_bon_ctp'
    
    id = db.Column(db.Integer, primary_key=True)
    bon_number = db.Column(db.String(255), nullable=False)
    request_number = db.Column(db.String(255), nullable=False)
    tanggal = db.Column(db.Date, nullable=False)
    bon_periode = db.Column(db.String(50), nullable=False)  # Misalnya: "Maret 2025"
    item_code = db.Column(db.String(100), nullable=False)   # Contoh: "02-005-000-0000061"
    item_name = db.Column(db.String(255), nullable=False)   # Contoh: "SAPHIRA PN DEVELOPER 20 L"
    brand = db.Column(db.String(50), nullable=False)        # SAPHIRA/FUJI
    unit = db.Column(db.String(20), nullable=False)  #SELALU "GLN"
    jumlah = db.Column(db.Integer, nullable=False)
    wo_number = db.Column(db.String(255), nullable=True)  # WO number yang dipilih secara random
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    
    # Relationship dengan User
    user = db.relationship('User', backref=db.backref('chemical_bons', lazy=True))

    def to_dict(self):
        return {
            'id': self.id,
            'bon_number': self.bon_number,
            'request_number': self.request_number,
            'tanggal': self.tanggal.strftime('%Y-%m-%d') if self.tanggal else None,
            'bon_periode': self.bon_periode,
            'item_code': self.item_code,
            'item_name': self.item_name,
            'brand': self.brand,
            'unit': self.unit,
            'jumlah': self.jumlah,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'created_by': self.user.name if self.user else None  # Mengembalikan nama user bukan ID
        }

# Stock calculation and management functions integrated into models

class KartuStockPlateFuji(db.Model):
    __tablename__ = 'kartu_stock_plate_fuji'

    id = db.Column(db.Integer, primary_key=True)
    tanggal = db.Column(db.Date, nullable=False)
    shift = db.Column(db.String(1), nullable=False)
    item_code = db.Column(db.String(100), nullable=False)
    item_name = db.Column(db.String(255), nullable=False)
    jumlah_stock_awal = db.Column(db.Integer, nullable=False)
    jumlah_pemakaian = db.Column(db.Integer, nullable=False)
    jumlah_incoming = db.Column(db.Integer, nullable=False)
    incoming_shift = db.Column(db.String(1), nullable=True)
    jumlah_stock_akhir = db.Column(db.Integer, nullable=False)
    jumlah_per_box = db.Column(db.Integer, nullable=False)    
    confirmed_at = db.Column(db.DateTime, nullable=True)
    confirmed_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)

    PLATE_TYPE_MAPPING = PlateTypeMapping.FUJI_PLATES

    user = db.relationship('User', backref=db.backref('stock_plates_fuji', lazy=True))

    def calculate_usage(self):
        """Hitung penggunaan plat dari log produksi CTP"""
        plate_type = self.PLATE_TYPE_MAPPING.get(self.item_code)
        if not plate_type:
            return 0
        ctp_shift = f"Shift {self.shift}"
        usage = db.session.query(
            func.sum(
                func.coalesce(CTPProductionLog.num_plate_good, 0) + 
                func.coalesce(CTPProductionLog.num_plate_not_good, 0)
            )
        ).filter(
            CTPProductionLog.log_date == self.tanggal,
            CTPProductionLog.ctp_shift == ctp_shift,
            CTPProductionLog.plate_type_material == plate_type
        ).scalar()
        return usage or 0

    def update_stock(self):
        """Perbarui jumlah pemakaian dan stok akhir"""
        self.jumlah_pemakaian = self.calculate_usage()
        self.jumlah_stock_akhir = self.jumlah_stock_awal - self.jumlah_pemakaian + self.jumlah_incoming

    @classmethod
    def get_previous_shift_stock(cls, tanggal, shift, item_code):
        """
        Gets the last known stock count for an item by finding the single most recent record
        based on a chronological ordering of date and shift.
        """
        # A more robust query to find the last record
        prev_record = cls.query.filter(
            cls.item_code == item_code,
            # Filter for records that are chronologically before the current date and shift
            (cls.tanggal < tanggal) |
            ((cls.tanggal == tanggal) & (cls.shift < shift))
        ).order_by(
            cls.tanggal.desc(),
            cls.shift.desc()
        ).first()

        return prev_record.jumlah_stock_akhir if prev_record else 0

    @classmethod
    def get_or_create_stocks(cls, tanggal, shift, user_id):
        stocks = cls.query.filter_by(tanggal=tanggal, shift=shift).all()
        
        if not stocks:
            stocks = []
            for item_code, item_name in cls.PLATE_TYPE_MAPPING.items():
                prev_stock = cls.get_previous_shift_stock(tanggal, shift, item_code)
                
                # Logika yang ada sekarang untuk membuat baris baru
                if item_code in PlateTypeMapping.FUJI_PLATES:
                    jumlah_per_box = 30 if '1630' not in item_name else 15
                else: # Fallback untuk Saphira atau lainnya, meskipun ini seharusnya tidak terjadi di kelas Fuji
                    if '1055 PN' in item_name:
                        jumlah_per_box = 40
                    elif '1630' in item_name:
                        jumlah_per_box = 30
                    else:
                        jumlah_per_box = 50
                
                new_stock = cls(
                    tanggal=tanggal,
                    shift=shift,
                    item_code=item_code,
                    item_name=item_name,
                    jumlah_stock_awal=prev_stock,
                    jumlah_pemakaian=0,
                    jumlah_incoming=0,
                    jumlah_stock_akhir=prev_stock,
                    jumlah_per_box=jumlah_per_box,
                    confirmed_by=user_id
                )
                db.session.add(new_stock)
                stocks.append(new_stock)
            
            db.session.commit()
        
        # Perbaikan utama: Perbarui jumlah_stock_awal untuk semua entri yang sudah ada
        for stock in stocks:
            stock.jumlah_stock_awal = cls.get_previous_shift_stock(tanggal, shift, stock.item_code)
            stock.update_stock() # Panggil update_stock() setelah stock awal diperbarui
            db.session.add(stock)
        
        db.session.commit()
        return stocks

    def to_dict(self):
        """Konversi data stok ke dictionary untuk respons API, termasuk konversi box/pcs"""
        stock_awal_box = self.jumlah_stock_awal // self.jumlah_per_box
        stock_awal_pcs = self.jumlah_stock_awal % self.jumlah_per_box
        
        stock_akhir_box = self.jumlah_stock_akhir // self.jumlah_per_box
        stock_akhir_pcs = self.jumlah_stock_akhir % self.jumlah_per_box
        
        incoming_box = self.jumlah_incoming // self.jumlah_per_box
        
        return {
            'id': self.id,
            'tanggal': self.tanggal.strftime('%Y-%m-%d') if self.tanggal else None,
            'shift': self.shift,
            'item_code': self.item_code,
            'item_name': self.item_name,
            'jumlah_stock_awal': self.jumlah_stock_awal,
            'jumlah_stock_awal_box': stock_awal_box,
            'jumlah_stock_awal_pcs': stock_awal_pcs,
            'jumlah_pemakaian': self.jumlah_pemakaian,
            'jumlah_incoming': incoming_box,
            'jumlah_stock_akhir': self.jumlah_stock_akhir,
            'jumlah_stock_akhir_box': stock_akhir_box,
            'jumlah_stock_akhir_pcs': stock_akhir_pcs,
            'jumlah_per_box': self.jumlah_per_box,
            'confirmed_at': self.confirmed_at.isoformat() if self.confirmed_at else None,
            'confirmed_by': self.user.name if self.user else None
        }

class KartuStockChemicalFuji(db.Model):
    __tablename__ = 'kartu_stock_chemical_fuji'

    id = db.Column(db.Integer, primary_key=True)
    tanggal = db.Column(db.Date, nullable=False)
    shift = db.Column(db.String(1), nullable=False)
    item_code = db.Column(db.String(100), nullable=False)
    item_name = db.Column(db.String(255), nullable=False)
    jumlah_stock_awal = db.Column(db.Integer, nullable=False)
    jumlah_pemakaian = db.Column(db.Integer, nullable=False)
    jumlah_incoming = db.Column(db.Integer, nullable=False)
    incoming_shift = db.Column(db.String(1), nullable=True)
    jumlah_stock_akhir = db.Column(db.Integer, nullable=False)
    confirmed_at = db.Column(db.DateTime, nullable=True)
    confirmed_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)

    user = db.relationship('User', backref=db.backref('stock_chemicals_fuji', lazy=True))

    CHEMICAL_TYPE_MAPPING = {
        '02-005-000-0000153': 'FUJI DEVELOPER',
        '02-005-000-0000154': 'FUJI REPLENISHER'
    }

    def calculate_usage(self):
        """
        Menghitung jumlah pemakaian chemical dari bon untuk shift dan tanggal yang bersangkutan.
        """
        
        # Pilih model bon yang sesuai
        if "fuji" in self.__tablename__.lower():
            BonModel = ChemicalBonCTP # Sesuaikan jika nama model Saphira berbeda
        else:
            BonModel = ChemicalBonCTP
        
        # Definisikan rentang waktu yang relevan berdasarkan shift
        if self.shift == '1':
            # Shift 1: dari 06:45:00 di hari yang sama hingga 18:44:59 di hari yang sama
            start_time = time(6, 45)
            end_time = time(18, 45)
            query = db.session.query(func.coalesce(func.sum(BonModel.jumlah), 0)).filter(
                BonModel.tanggal == self.tanggal, # Menggunakan tanggal bon
                BonModel.item_code == self.item_code,
                func.time(BonModel.created_at) >= start_time,
                func.time(BonModel.created_at) < end_time
            )
        elif self.shift == '2':
            # Shift 2: dari 18:45:00 di hari ini hingga 06:44:59 di hari berikutnya
            start_time = time(18, 45)
            end_time = time(6, 45)
            next_day = self.tanggal + timedelta(days=1)
            
            query = db.session.query(func.coalesce(func.sum(BonModel.jumlah), 0)).filter(
                BonModel.item_code == self.item_code,
                or_(
                    # Kondisi untuk bon yang dibuat dari 18:45:00 hingga tengah malam hari ini
                    and_(
                        BonModel.tanggal == self.tanggal,
                        func.time(BonModel.created_at) >= start_time
                    ),
                    # Kondisi untuk bon yang dibuat dari tengah malam hingga 06:44:59 hari berikutnya
                    and_(
                        BonModel.tanggal == next_day,
                        func.time(BonModel.created_at) < end_time
                    )
                )
            )
        else:
            return 0
        
        return query.scalar()

    def update_stock(self):
        self.jumlah_pemakaian = self.calculate_usage()
        self.jumlah_stock_akhir = self.jumlah_stock_awal + self.jumlah_incoming - self.jumlah_pemakaian

    @classmethod
    def get_previous_shift_stock(cls, tanggal, shift, item_code):
        prev_record = None
        if shift == '2':
            prev_record = cls.query.filter_by(tanggal=tanggal, item_code=item_code, shift='1').first()
        elif shift == '1':
            prev_tanggal = tanggal - timedelta(days=1)
            prev_record = cls.query.filter_by(tanggal=prev_tanggal, item_code=item_code, shift='2').first()
        
        return prev_record.jumlah_stock_akhir if prev_record else 0

    @classmethod
    def get_or_create_stocks(cls, tanggal, shift, user_id):
        stocks = cls.query.filter_by(tanggal=tanggal, shift=shift).all()

        if not stocks:
            stocks = []
            for item_code, item_name in cls.CHEMICAL_TYPE_MAPPING.items():
                prev_stock = cls.get_previous_shift_stock(tanggal, shift, item_code)
                new_stock = cls(
                    tanggal=tanggal,
                    shift=shift,
                    item_code=item_code,
                    item_name=item_name,
                    jumlah_stock_awal=prev_stock,
                    jumlah_pemakaian=0,
                    jumlah_incoming=0,
                    jumlah_stock_akhir=prev_stock,
                    confirmed_by=user_id
                )
                db.session.add(new_stock)
                stocks.append(new_stock)
            
            db.session.commit()
            
        # Ini adalah bagian yang paling penting!
        # Memastikan stok awal selalu diperbarui dari data terbaru,
        # bahkan jika barisnya sudah ada di database.
        for stock in stocks:
            stock.jumlah_stock_awal = cls.get_previous_shift_stock(tanggal, shift, stock.item_code)
            stock.update_stock() # Hitung ulang jumlah_stock_akhir
            db.session.add(stock)

        db.session.commit()
        return stocks

    def to_dict(self):
        return {
            'id': self.id,
            'tanggal': self.tanggal.strftime('%Y-%m-%d') if self.tanggal else None,
            'shift': self.shift,
            'item_code': self.item_code,
            'item_name': self.item_name,
            'jumlah_stock_awal': self.jumlah_stock_awal,
            'jumlah_pemakaian': self.jumlah_pemakaian,
            'jumlah_incoming': self.jumlah_incoming,
            'jumlah_stock_akhir': self.jumlah_stock_akhir,
            'confirmed_at': self.confirmed_at.isoformat() if self.confirmed_at else None,
            'confirmed_by': self.user.name if self.user else None
        }
    
class KartuStockPlateSaphira(db.Model):
    __tablename__ = 'kartu_stock_plate_saphira'

    id = db.Column(db.Integer, primary_key=True)
    tanggal = db.Column(db.Date, nullable=False)
    shift = db.Column(db.String(1), nullable=False)
    item_code = db.Column(db.String(100), nullable=False)
    item_name = db.Column(db.String(255), nullable=False)
    jumlah_stock_awal = db.Column(db.Integer, nullable=False)
    jumlah_pemakaian = db.Column(db.Integer, nullable=False)
    jumlah_incoming = db.Column(db.Integer, nullable=False)
    incoming_shift = db.Column(db.String(1), nullable=True)
    jumlah_stock_akhir = db.Column(db.Integer, nullable=False)
    jumlah_per_box = db.Column(db.Integer, nullable=False)
    confirmed_at = db.Column(db.DateTime, nullable=True)
    confirmed_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)

    PLATE_TYPE_MAPPING = PlateTypeMapping.SAPHIRA_PLATES

    user = db.relationship('User', backref=db.backref('stock_plates_saphira', lazy=True))

    def calculate_usage(self):
        """Hitung penggunaan plat dari log produksi CTP"""
        plate_type = self.PLATE_TYPE_MAPPING.get(self.item_code)
        if not plate_type:
            return 0
        ctp_shift = f"Shift {self.shift}"
        usage = db.session.query(
            func.sum(
                func.coalesce(CTPProductionLog.num_plate_good, 0) + 
                func.coalesce(CTPProductionLog.num_plate_not_good, 0)
            )
        ).filter(
            CTPProductionLog.log_date == self.tanggal,
            CTPProductionLog.ctp_shift == ctp_shift,
            CTPProductionLog.plate_type_material == plate_type
        ).scalar()
        return usage or 0

    def update_stock(self):
        """Perbarui jumlah pemakaian dan stok akhir"""
        self.jumlah_pemakaian = self.calculate_usage()
        self.jumlah_stock_akhir = self.jumlah_stock_awal - self.jumlah_pemakaian + self.jumlah_incoming

    @classmethod
    def get_previous_shift_stock(cls, tanggal, shift, item_code):
        """
        Gets the last known stock count for an item by finding the single most recent record
        based on a chronological ordering of date and shift.
        """
        # A more robust query to find the last record
        prev_record = cls.query.filter(
            cls.item_code == item_code,
            # Filter for records that are chronologically before the current date and shift
            (cls.tanggal < tanggal) |
            ((cls.tanggal == tanggal) & (cls.shift < shift))
        ).order_by(
            cls.tanggal.desc(),
            cls.shift.desc()
        ).first()

        return prev_record.jumlah_stock_akhir if prev_record else 0

    @classmethod
    def get_or_create_stocks(cls, tanggal, shift, user_id):
        stocks = cls.query.filter_by(tanggal=tanggal, shift=shift).all()
        
        if not stocks:
            stocks = []
            for item_code, item_name in cls.PLATE_TYPE_MAPPING.items():
                prev_stock = cls.get_previous_shift_stock(tanggal, shift, item_code)
                
                # Logika yang ada sekarang untuk membuat baris baru
                if item_code in PlateTypeMapping.FUJI_PLATES:
                    jumlah_per_box = 30 if '1630' not in item_name else 15
                else: # Fallback untuk Saphira atau lainnya, meskipun ini seharusnya tidak terjadi di kelas Fuji
                    if '1055 PN' in item_name:
                        jumlah_per_box = 40
                    elif '1630' in item_name:
                        jumlah_per_box = 30
                    else:
                        jumlah_per_box = 50
                
                new_stock = cls(
                    tanggal=tanggal,
                    shift=shift,
                    item_code=item_code,
                    item_name=item_name,
                    jumlah_stock_awal=prev_stock,
                    jumlah_pemakaian=0,
                    jumlah_incoming=0,
                    jumlah_stock_akhir=prev_stock,
                    jumlah_per_box=jumlah_per_box,
                    confirmed_by=user_id
                )
                db.session.add(new_stock)
                stocks.append(new_stock)
            
            db.session.commit()
        
        # Perbaikan utama: Perbarui jumlah_stock_awal untuk semua entri yang sudah ada
        for stock in stocks:
            stock.jumlah_stock_awal = cls.get_previous_shift_stock(tanggal, shift, stock.item_code)
            stock.update_stock() # Panggil update_stock() setelah stock awal diperbarui
            db.session.add(stock)
        
        db.session.commit()
        return stocks

    def to_dict(self):
        """Konversi data stok ke dictionary untuk respons API, termasuk konversi box/pcs"""
        stock_awal_box = self.jumlah_stock_awal // self.jumlah_per_box
        stock_awal_pcs = self.jumlah_stock_awal % self.jumlah_per_box
        
        stock_akhir_box = self.jumlah_stock_akhir // self.jumlah_per_box
        stock_akhir_pcs = self.jumlah_stock_akhir % self.jumlah_per_box
        
        incoming_box = self.jumlah_incoming // self.jumlah_per_box
        
        return {
            'id': self.id,
            'tanggal': self.tanggal.strftime('%Y-%m-%d') if self.tanggal else None,
            'shift': self.shift,
            'item_code': self.item_code,
            'item_name': self.item_name,
            'jumlah_stock_awal': self.jumlah_stock_awal,
            'jumlah_stock_awal_box': stock_awal_box,
            'jumlah_stock_awal_pcs': stock_awal_pcs,
            'jumlah_pemakaian': self.jumlah_pemakaian,
            'jumlah_incoming': incoming_box,
            'jumlah_stock_akhir': self.jumlah_stock_akhir,
            'jumlah_stock_akhir_box': stock_akhir_box,
            'jumlah_stock_akhir_pcs': stock_akhir_pcs,
            'jumlah_per_box': self.jumlah_per_box,
            'confirmed_at': self.confirmed_at.isoformat() if self.confirmed_at else None,
            'confirmed_by': self.user.name if self.user else None
        }

class KartuStockChemicalSaphira(db.Model):
    __tablename__ = 'kartu_stock_chemical_saphira'

    id = db.Column(db.Integer, primary_key=True)
    tanggal = db.Column(db.Date, nullable=False)
    shift = db.Column(db.String(1), nullable=False)
    item_code = db.Column(db.String(100), nullable=False)
    item_name = db.Column(db.String(255), nullable=False)
    jumlah_stock_awal = db.Column(db.Integer, nullable=False)
    jumlah_pemakaian = db.Column(db.Integer, nullable=False)
    jumlah_incoming = db.Column(db.Integer, nullable=False)
    incoming_shift = db.Column(db.String(1), nullable=True)
    jumlah_stock_akhir = db.Column(db.Integer, nullable=False)
    confirmed_at = db.Column(db.DateTime, default=datetime.utcnow)
    confirmed_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)

    user = db.relationship('User', backref=db.backref('stock_chemicals_saphira', lazy=True))

    CHEMICAL_TYPE_MAPPING = {
        '02-005-000-0000061': 'SAPHIRA DEVELOPER',
        '02-005-000-0000046': 'SAPHIRA REPLENISHER',
        '02-005-000-0000158': 'SAPHIRA GUM'  # Diperbarui agar sesuai dengan data bon
    }

    def calculate_usage(self):
        """
        Menghitung jumlah pemakaian chemical dari bon untuk shift dan tanggal yang bersangkutan.
        """
        
        # Pilih model bon yang sesuai
        if "saphira" in self.__tablename__.lower():
            BonModel = ChemicalBonCTP # Sesuaikan jika nama model Saphira berbeda
        else:
            BonModel = ChemicalBonCTP
        
        # Definisikan rentang waktu yang relevan berdasarkan shift
        if self.shift == '1':
            # Shift 1: dari 06:45:00 di hari yang sama hingga 18:44:59 di hari yang sama
            start_time = time(6, 45)
            end_time = time(18, 45)
            query = db.session.query(func.coalesce(func.sum(BonModel.jumlah), 0)).filter(
                BonModel.tanggal == self.tanggal, # Menggunakan tanggal
                BonModel.item_code == self.item_code,
                func.time(BonModel.created_at) >= start_time,
                func.time(BonModel.created_at) < end_time
            )
        elif self.shift == '2':
            # Shift 2: dari 18:45:00 di hari ini hingga 06:44:59 di hari berikutnya
            start_time = time(18, 45)
            end_time = time(6, 45)
            next_day = self.tanggal + timedelta(days=1)
            
            query = db.session.query(func.coalesce(func.sum(BonModel.jumlah), 0)).filter(
                BonModel.item_code == self.item_code,
                or_(
                    # Kondisi untuk bon yang dibuat dari 18:45:00 hingga tengah malam hari ini
                    and_(
                        BonModel.tanggal == self.tanggal, # Menggunakan tanggal
                        func.time(BonModel.created_at) >= start_time
                    ),
                    # Kondisi untuk bon yang dibuat dari tengah malam hingga 06:44:59 hari berikutnya
                    and_(
                        BonModel.tanggal == next_day, # Menggunakan tanggal
                        func.time(BonModel.created_at) < end_time
                    )
                )
            )
        else:
            return 0
        
        return query.scalar()

    def update_stock(self):
        self.jumlah_pemakaian = self.calculate_usage()
        self.jumlah_stock_akhir = self.jumlah_stock_awal + self.jumlah_incoming - self.jumlah_pemakaian
        
    @classmethod
    def get_previous_shift_stock(cls, tanggal, shift, item_code):
        prev_record = None
        if shift == '2':
            prev_record = cls.query.filter_by(tanggal=tanggal, item_code=item_code, shift='1').first()
        elif shift == '1':
            prev_tanggal = tanggal - timedelta(days=1)
            prev_record = cls.query.filter_by(tanggal=prev_tanggal, item_code=item_code, shift='2').first()
        
        return prev_record.jumlah_stock_akhir if prev_record else 0

    @classmethod
    def get_or_create_stocks(cls, tanggal, shift, user_id):
        stocks = cls.query.filter_by(tanggal=tanggal, shift=shift).all()

        if not stocks:
            stocks = []
            for item_code, item_name in cls.CHEMICAL_TYPE_MAPPING.items():
                prev_stock = cls.get_previous_shift_stock(tanggal, shift, item_code)
                new_stock = cls(
                    tanggal=tanggal,
                    shift=shift,
                    item_code=item_code,
                    item_name=item_name,
                    jumlah_stock_awal=prev_stock,
                    jumlah_pemakaian=0,
                    jumlah_incoming=0,
                    jumlah_stock_akhir=prev_stock,
                    confirmed_by=user_id
                )
                db.session.add(new_stock)
                stocks.append(new_stock)
            
            db.session.commit()
            
        # Bagian perbaikan utama:
        # Memastikan stok awal selalu diperbarui dari data terbaru,
        # bahkan jika barisnya sudah ada di database.
        for stock in stocks:
            stock.jumlah_stock_awal = cls.get_previous_shift_stock(tanggal, shift, stock.item_code)
            stock.update_stock() # Hitung ulang jumlah_stock_akhir
            db.session.add(stock)

        db.session.commit()
        return stocks

    def to_dict(self):
        return {
            'id': self.id,
            'tanggal': self.tanggal.strftime('%Y-%m-%d') if self.tanggal else None,
            'shift': self.shift,
            'item_code': self.item_code,
            'item_name': self.item_name,
            'jumlah_stock_awal': self.jumlah_stock_awal,
            'jumlah_pemakaian': self.jumlah_pemakaian,
            'jumlah_incoming': self.jumlah_incoming,
            'jumlah_stock_akhir': self.jumlah_stock_akhir,
            'confirmed_at': self.confirmed_at.isoformat() if self.confirmed_at else None,
            'confirmed_by': self.user.name if self.user else None
        }

class BonPlate(db.Model):
    """Model untuk tabel bon_plate"""
    __tablename__ = 'bon_plate'
    
    id = db.Column(db.Integer, primary_key=True)
    bon_number = db.Column(db.String(255), nullable=False)
    request_number = db.Column(db.String(255), nullable=False)
    tanggal = db.Column(db.Date, nullable=False)
    bon_periode = db.Column(db.String(255), nullable=False)
    jenis_plate = db.Column(db.String(50), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    
    # Relationship dengan User - dengan primary join yang eksplisit
    user = db.relationship('User', 
                         primaryjoin='BonPlate.created_by == User.id',
                         backref=db.backref('bon_plates', lazy=True))

    def to_dict(self):
        return {
            'id': self.id,
            'bon_number': self.bon_number,
            'request_number': self.request_number,
            'tanggal': self.tanggal.strftime('%Y-%m-%d') if self.tanggal else None,
            'jenis_plate': self.jenis_plate,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'created_by': self.created_by,
            'created_by_name': self.user.name if self.user else None
        }

class PlateBonRequest(db.Model):
    __tablename__ = 'plate_bon_requests'

    id = db.Column(db.Integer, primary_key=True)
    tanggal = db.Column(db.Date, nullable=False)
    mesin_cetak = db.Column(db.String(100), nullable=False)
    pic = db.Column(db.String(100), nullable=False)
    remarks = db.Column(db.String(100), nullable=False)  # PRODUKSI/PROOF
    wo_number = db.Column(db.String(100), nullable=False)
    mc_number = db.Column(db.String(100), nullable=False)
    run_length = db.Column(db.Integer, nullable=True)
    item_name = db.Column(db.String(255), nullable=False)
    jumlah_plate = db.Column(db.Integer, nullable=False)
    note = db.Column(db.String(255), nullable=True)
    machine_off_at = db.Column(db.DateTime, default=datetime.utcnow)
    plate_start_at = db.Column(db.DateTime, nullable=True)
    plate_finish_at = db.Column(db.DateTime, nullable=True)
    plate_delivered_at = db.Column(db.DateTime, nullable=True)
    ctp_by = db.Column(db.String(100), nullable=True)
    ctp_group = db.Column(db.String(50), nullable=True)  # Mengubah ctp_grup menjadi ctp_group untuk konsistensi
    status = db.Column(db.String(30), default='proses_ctp')

    cancellation_reason = db.Column(db.String(255), nullable=True)
    cancelled_by = db.Column(db.String(100), nullable=True)
    cancelled_at = db.Column(db.DateTime, nullable=True)

    declined_at = db.Column(db.DateTime, nullable=True)
    declined_by = db.Column(db.String(100), nullable=True)
    decline_reason = db.Column(db.Text, nullable=True)
    is_declined = db.Column(db.Boolean, default=False)

    def to_dict(self):
        return {
            'id': self.id,
            'tanggal': self.tanggal.strftime('%Y-%m-%d') if self.tanggal else None,
            'mesin_cetak': self.mesin_cetak,
            'pic': self.pic,
            'remarks': self.remarks,
            'wo_number': self.wo_number,
            'mc_number': self.mc_number,
            'run_length': self.run_length,
            'item_name': self.item_name,
            'jumlah_plate': self.jumlah_plate,
            'note': self.note,
            'machine_off_at': self.machine_off_at.isoformat() if self.machine_off_at else None,
            'plate_start_at': self.plate_start_at.isoformat() if self.plate_start_at else None,
            'plate_finish_at': self.plate_finish_at.isoformat() if self.plate_finish_at else None,
            'plate_delivered_at': self.plate_delivered_at.isoformat() if self.plate_delivered_at else None,
            'ctp_by': self.ctp_by,
            'ctp_group': self.ctp_group,
            'status': self.status,
            'cancellation_reason': self.cancellation_reason,
            'cancelled_by': self.cancelled_by,
            'cancelled_at': self.cancelled_at.isoformat() if self.cancelled_at else None,
            'declined_by': self.declined_by,
            'declined_at': self.declined_at.isoformat() if self.declined_at else None,
            'decline_reason': self.decline_reason,
            'is_declined': self.is_declined
        }

# Admin routes for user management
@app.route('/admin/users')
@login_required
@require_admin
def admin_users():
    divisions = Division.query.order_by(Division.name).all()
    return render_template('admin_users.html', 
                         current_user_id=current_user.id,
                         divisions=divisions)

@app.route('/admin/user/<int:user_id>')
@login_required
@require_admin
def admin_get_user(user_id):
    user = db.session.get(User, user_id) # Menggunakan db.session.get
    if user is None:
        abort(404, description="User not found")
    return jsonify({
        'id': user.id,
        'name': user.name,
        'username': user.username,
        'role': user.role,
        'division_id': user.division_id,
        'grup': user.grup,
        'is_active': user.is_active
    })

@app.route('/admin/user/add', methods=['POST'])
@login_required
@require_admin
def admin_add_user():
    try:
        name = request.form['name']
        username = request.form['username']
        password = request.form['password']
        role = request.form['role']
        division_id = request.form['division_id'] or None
        grup = request.form['grup'] or None

        if User.query.filter_by(username=username).first():
            return jsonify({
                'success': False,
                'message': 'Username sudah digunakan'
            }), 400

        user = User(
            name=name,
            username=username,
            password_hash=generate_password_hash(password),
            role=role,
            division_id=division_id,
            grup=grup,
            is_active=True
        )
        db.session.add(user)
        db.session.commit()
        return jsonify({
            'success': True,
            'message': 'User berhasil ditambahkan'
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': f'Gagal menambahkan user: {str(e)}'
        }), 400

@app.route('/admin/user/edit', methods=['POST'])
@login_required
@require_admin
def admin_edit_user():
    try:
        user_id = request.form['user_id']
        user = db.session.get(User, user_id) # Menggunakan db.session.get
        if user is None:
            abort(404, description="User not found")
        
        user.name = request.form['name']
        user.username = request.form['username']
        if request.form['password']:
            user.password_hash = generate_password_hash(request.form['password'])
        user.role = request.form['role']
        user.division_id = request.form['division_id'] or None
        user.grup = request.form['grup'] or None
        user.is_active = 'is_active' in request.form
        
        db.session.commit()
        return jsonify({
            'success': True,
            'message': 'User berhasil diperbarui'
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': f'Gagal memperbarui user: {str(e)}'
        }), 400

@app.route('/admin/user/delete', methods=['POST'])
@login_required
@require_admin
def admin_delete_user():
    try:
        user_id = request.form['user_id']
        user = db.session.get(User, user_id) # Menggunakan db.session.get
        if user is None:
            abort(404, description="User not found")
        
        if user.id == current_user.id:
            return jsonify({
                'success': False,
                'message': 'Tidak dapat menghapus akun sendiri'
            }), 400
            
        db.session.delete(user)
        db.session.commit()
        return jsonify({
            'success': True,
            'message': 'User berhasil dihapus'
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': f'Gagal menghapus user: {str(e)}'
        }), 400

# Function to collect plate usage data
# Helper function to get shift name for CTP logs
def get_ctp_shift_name(shift_num):
    """Convert numeric shift to CTP log shift format"""
    return f"Shift {shift_num}"
    
    # Update Fuji plate stock
    fuji_stocks = KartuStockPlateFuji.query.filter_by(
        tanggal=stock_date,
        shift=shift_num
    ).all()
    
    if not fuji_stocks:
        app.logger.info('Creating new Fuji plate stock records')
        # Create new stock records for all Fuji plate types
        for item_code, plate_type in KartuStockPlateFuji.PLATE_TYPE_MAPPING.items():
            # Get previous day's stock
            prev_stock = KartuStockPlateFuji.get_previous_day_stock(stock_date, item_code)
            
            # Create new stock record
            new_stock = KartuStockPlateFuji(
                tanggal=stock_date,
                shift=shift_num,
                item_code=item_code,
                item_name=plate_type,
                jumlah_stock_awal=prev_stock or 0,
                jumlah_pemakaian=usage_map.get(plate_type, 0),
                jumlah_incoming=0,
                jumlah_stock_akhir=(prev_stock or 0) - usage_map.get(plate_type, 0),
                jumlah_per_box=100,
                confirmed_by=current_user.id
            )
            db.session.add(new_stock)
    else:
        app.logger.info('Updating existing Fuji plate stock records')
        # Update existing stock records
        for stock in fuji_stocks:
            plate_type = KartuStockPlateFuji.PLATE_TYPE_MAPPING.get(stock.item_code)
            if plate_type:
                stock.jumlah_pemakaian = usage_map.get(plate_type, 0)
                stock.jumlah_stock_akhir = stock.jumlah_stock_awal - stock.jumlah_pemakaian + stock.jumlah_incoming
    
    # Update Saphira plate stock
    saphira_stocks = KartuStockPlateSaphira.query.filter_by(
        tanggal=stock_date,
        shift=shift_num
    ).all()
    
    if not saphira_stocks:
        app.logger.info('Creating new Saphira plate stock records')
        # Create new stock records for all Saphira plate types
        for item_code, plate_type in KartuStockPlateSaphira.PLATE_TYPE_MAPPING.items():
            # Get previous day's stock
            prev_stock = KartuStockPlateSaphira.get_previous_day_stock(stock_date, item_code)
            
            # Create new stock record
            new_stock = KartuStockPlateSaphira(
                tanggal=stock_date,
                shift=shift_num,
                item_code=item_code,
                item_name=plate_type,
                jumlah_stock_awal=prev_stock or 0,
                jumlah_pemakaian=usage_map.get(plate_type, 0),
                jumlah_incoming=0,
                jumlah_stock_akhir=(prev_stock or 0) - usage_map.get(plate_type, 0),
                jumlah_per_box=100,
                confirmed_by=current_user.id
            )
            db.session.add(new_stock)
    else:
        app.logger.info('Updating existing Saphira plate stock records')
        # Update existing stock records
        for stock in saphira_stocks:
            plate_type = KartuStockPlateSaphira.PLATE_TYPE_MAPPING.get(stock.item_code)
            if plate_type:
                stock.jumlah_pemakaian = usage_map.get(plate_type, 0)
                stock.jumlah_stock_akhir = stock.jumlah_stock_awal - stock.jumlah_pemakaian + stock.jumlah_incoming
    
    # Commit changes
    db.session.commit()
    app.logger.info('Plate usage data collection completed')

# Routes for Kartu Stock CTP
@app.route('/kartu-stock-ctp')
@login_required
def kartu_stock_ctp():
    return render_template('kartu_stock_ctp.html')

@app.route('/api/kartu-stock')
@login_required
def get_kartu_stock():
    """Get kartu stock data for a given date and shift"""
    try:
        date_str = request.args.get('date')
        shift = request.args.get('shift')
        
        if not date_str or not shift:
            return jsonify({'error': 'Date and shift are required'}), 400
            
        try:
            tanggal = datetime.strptime(date_str, '%Y-%m-%d').date()
        except ValueError:
            return jsonify({'error': 'Invalid date format'}), 400

        # Gunakan metode get_or_create_stocks dari setiap model dan berikan user_id
        fuji_chemicals = KartuStockChemicalFuji.get_or_create_stocks(tanggal, shift, current_user.id)
        saphira_chemicals = KartuStockChemicalSaphira.get_or_create_stocks(tanggal, shift, current_user.id)
        fuji_stocks = KartuStockPlateFuji.get_or_create_stocks(tanggal, shift, current_user.id)
        saphira_stocks = KartuStockPlateSaphira.get_or_create_stocks(tanggal, shift, current_user.id)
        
        db.session.commit()

        # Konversi data ke format dictionary untuk respons JSON
        fuji_chemical_data = [stock.to_dict() for stock in fuji_chemicals]
        saphira_chemical_data = [stock.to_dict() for stock in saphira_chemicals]
        fuji_plate_data = [stock.to_dict() for stock in fuji_stocks]
        saphira_plate_data = [stock.to_dict() for stock in saphira_stocks]

        response_data = {
            'fuji': {
                'plate': {
                    'data': fuji_plate_data,
                    'confirmed': any(stock.confirmed_at for stock in fuji_stocks)
                },
                'chemical': {
                    'data': fuji_chemical_data,
                    'confirmed': any(stock.confirmed_at for stock in fuji_chemicals)
                }
            },
            'saphira': {
                'plate': {
                    'data': saphira_plate_data,
                    'confirmed': any(stock.confirmed_at for stock in saphira_stocks)
                },
                'chemical': {
                    'data': saphira_chemical_data,
                    'confirmed': any(stock.confirmed_at for stock in saphira_chemicals)
                }
            }
        }

        app.logger.info('Successfully processed kartu stock request')
        return jsonify(response_data)

    except ValueError:
        app.logger.error(f'Invalid date format: {date_str}')
        return jsonify({'error': 'Invalid date format'}), 400
        
    except Exception as e:
        db.session.rollback()
        app.logger.error(f'Error processing kartu stock: {str(e)}', exc_info=True)
        return jsonify({'error': str(e)}), 500
# This code has been moved to the model class methods
            
# This functionality has been moved to the model class methods

    # Get confirmation status
    def get_confirmation_status(brand_stocks):
        if not brand_stocks:
            return {"confirmed": False}
        
        all_confirmed = all(stock.get('confirmed', False) for stock in brand_stocks)
        if all_confirmed:
            confirmed_by = User.query.get(brand_stocks[0].get('confirmed_by'))
            return {
                "confirmed": True,
                "confirmedBy": confirmed_by.name if confirmed_by else "Unknown"
            }
        return {"confirmed": False}

    # Dapatkan data untuk setiap jenis stok
    fuji_plate = get_stock_data(KartuStockPlateFuji)
    fuji_chemical = get_stock_data(KartuStockChemicalFuji)
    saphira_plate = get_stock_data(KartuStockPlateSaphira)
    saphira_chemical = get_stock_data(KartuStockChemicalSaphira)

    return jsonify({
        'fuji': {
            'plate': {
                'data': fuji_plate,
                'status': get_confirmation_status(fuji_plate)
            },
            'chemical': {
                'data': fuji_chemical,
                'status': get_confirmation_status(fuji_chemical)
            }
        },
        'saphira': {
            'plate': {
                'data': saphira_plate,
                'status': get_confirmation_status(saphira_plate)
            },
            'chemical': {
                'data': saphira_chemical,
                'status': get_confirmation_status(saphira_chemical)
            }
        }
    })



@app.route('/api/confirm-stock', methods=['POST'])
@login_required
def confirm_stock():
    data = request.get_json()
    brand = data.get('brand')
    date_str = data.get('date')
    shift = data.get('shift')

    if not all([brand, date_str, shift]):
        return jsonify({'error': 'Missing required fields'}), 400

    try:
        tanggal = datetime.strptime(date_str, '%Y-%m-%d').date()
    except ValueError:
        return jsonify({'error': 'Invalid date format'}), 400

    # Pilih model berdasarkan brand
    if brand == 'fuji':
        models = [KartuStockPlateFuji, KartuStockChemicalFuji]
    else:
        models = [KartuStockPlateSaphira, KartuStockChemicalSaphira]
    
    # Update semua stok untuk brand yang dipilih
    stocks_updated = False
    for model in models:
        stocks = model.query.filter_by(
            tanggal=tanggal,
            shift=shift
        ).all()
        
        for stock in stocks:
            stock.update_stock()  # Pastikan data terbaru
            stock.confirmed_at = datetime.utcnow()
            stock.confirmed_by = current_user.id
            stocks_updated = True

    if not stocks_updated:
        return jsonify({'error': 'No stock data found for the specified date and shift'}), 404

    try:
        db.session.commit()
        return jsonify({'message': f'Stock {brand} confirmed successfully'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500
        return jsonify({'message': f'Stock {brand} berhasil dikonfirmasi'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@app.route('/api/input-initial-stock', methods=['POST'])
@login_required
@require_admin
def input_initial_stock():
    data = request.get_json()
    date_str = data.get('date')
    if not date_str:
        return jsonify({'error': 'Tanggal harus diisi'}), 400

    try:
        selected_date = datetime.strptime(date_str, '%Y-%m-%d').date()
        
        # Process Fuji plates
        for plate in data.get('fuji', {}).get('plates', []):
            if plate.get('jumlah_stock_awal', 0) > 0:
                box_value = int(plate['jumlah_stock_awal'] / plate['jumlah_per_box'])
                pcs_value = plate['jumlah_stock_awal'] % plate['jumlah_per_box']
                
                stock = KartuStockPlateFuji(
                    tanggal=selected_date,
                    item_code=plate['item_code'],
                    item_name=plate['item_name'],
                    jumlah_stock_awal=plate['jumlah_stock_awal'],
                    jumlah_pemakaian=0,
                    jumlah_incoming=0,
                    jumlah_stock_akhir=plate['jumlah_stock_awal'],
                    jumlah_per_box=plate['jumlah_per_box'],
                    confirmed_by=current_user.id
                )
                db.session.add(stock)

        # Process Fuji chemicals
        for chemical in data.get('fuji', {}).get('chemicals', []):
            if chemical.get('jumlah_stock_awal', 0) > 0:
                stock = KartuStockChemicalFuji(
                    tanggal=selected_date,
                    item_code=chemical['item_code'],
                    item_name=chemical['item_name'],
                    jumlah_stock_awal=chemical['jumlah_stock_awal'],
                    jumlah_pemakaian=0,
                    jumlah_incoming=0,
                    jumlah_stock_akhir=chemical['jumlah_stock_awal'],
                    confirmed_by=current_user.id
                )
                db.session.add(stock)

        # Process Saphira plates
        for plate in data.get('saphira', {}).get('plates', []):
            if plate.get('jumlah_stock_awal', 0) > 0:
                box_value = int(plate['jumlah_stock_awal'] / plate['jumlah_per_box'])
                pcs_value = plate['jumlah_stock_awal'] % plate['jumlah_per_box']
                
                stock = KartuStockPlateSaphira(
                    tanggal=selected_date,
                    item_code=plate['item_code'],
                    item_name=plate['item_name'],
                    jumlah_stock_awal=plate['jumlah_stock_awal'],
                    jumlah_pemakaian=0,
                    jumlah_incoming=0,
                    jumlah_stock_akhir=plate['jumlah_stock_awal'],
                    jumlah_per_box=plate['jumlah_per_box'],
                    confirmed_by=current_user.id
                )
                db.session.add(stock)

        # Process Saphira chemicals
        for chemical in data.get('saphira', {}).get('chemicals', []):
            if chemical.get('jumlah_stock_awal', 0) > 0:
                stock = KartuStockChemicalSaphira(
                    tanggal=selected_date,
                    item_code=chemical['item_code'],
                    item_name=chemical['item_name'],
                    jumlah_stock_awal=chemical['jumlah_stock_awal'],
                    jumlah_pemakaian=0,
                    jumlah_incoming=0,
                    jumlah_stock_akhir=chemical['jumlah_stock_awal'],
                    confirmed_by=current_user.id
                )
                db.session.add(stock)

        db.session.commit()
        return jsonify({'message': 'Stok awal berhasil disimpan'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@app.route('/api/input-incoming-stock', methods=['POST'])
@login_required
def input_incoming_stock():
    data = request.get_json()
    date_str = data.get('date')
    shift = data.get('shift')

    if not date_str or not shift:
        return jsonify({'error': 'Tanggal dan shift harus diisi'}), 400

    try:
        tanggal = datetime.strptime(date_str, '%Y-%m-%d').date()

        # Proses data berdasarkan brand yang dipilih
        if 'fuji' in data:
            # Proses Fuji plates
            for plate in data['fuji'].get('plates', []):
                incoming_amount = plate.get('jumlah_incoming', 0)
                if incoming_amount > 0:
                    stock = KartuStockPlateFuji.query.filter_by(
                        tanggal=tanggal,
                        item_code=plate['item_code'],
                        shift=shift  # PERBAIKAN: Tambahkan filter shift
                    ).first()

                    if stock:
                        stock.jumlah_incoming += incoming_amount
                        stock.incoming_shift = shift
                        stock.jumlah_stock_akhir += incoming_amount
                    else:
                        new_stock = KartuStockPlateFuji(
                            tanggal=tanggal,
                            shift=shift,
                            item_code=plate['item_code'],
                            item_name=plate['item_name'],
                            jumlah_stock_awal=0,
                            jumlah_pemakaian=0,
                            jumlah_incoming=incoming_amount,
                            incoming_shift=shift,
                            jumlah_stock_akhir=incoming_amount,
                            jumlah_per_box=plate['jumlah_per_box'],
                            confirmed_by=current_user.id
                        )
                        db.session.add(new_stock)

            # Proses Fuji chemicals
            for chemical in data['fuji'].get('chemicals', []):
                incoming_amount = chemical.get('jumlah_incoming', 0)
                if incoming_amount > 0:
                    stock = KartuStockChemicalFuji.query.filter_by(
                        tanggal=tanggal,
                        item_code=chemical['item_code'],
                        shift=shift  # PERBAIKAN: Tambahkan filter shift
                    ).first()

                    if stock:
                        stock.jumlah_incoming += incoming_amount
                        stock.incoming_shift = shift
                        stock.jumlah_stock_akhir += incoming_amount
                    else:
                        new_stock = KartuStockChemicalFuji(
                            tanggal=tanggal,
                            shift=shift,
                            item_code=chemical['item_code'],
                            item_name=chemical['item_name'],
                            jumlah_stock_awal=0,
                            jumlah_pemakaian=0,
                            jumlah_incoming=incoming_amount,
                            incoming_shift=shift,
                            jumlah_stock_akhir=incoming_amount,
                            confirmed_by=current_user.id
                        )
                        db.session.add(new_stock)

        if 'saphira' in data:
            # Proses Saphira plates
            for plate in data['saphira'].get('plates', []):
                incoming_amount = plate.get('jumlah_incoming', 0)
                if incoming_amount > 0:
                    stock = KartuStockPlateSaphira.query.filter_by(
                        tanggal=tanggal,
                        item_code=plate['item_code'],
                        shift=shift  # PERBAIKAN: Tambahkan filter shift
                    ).first()

                    if stock:
                        stock.jumlah_incoming += incoming_amount
                        stock.incoming_shift = shift
                        stock.jumlah_stock_akhir += incoming_amount
                    else:
                        new_stock = KartuStockPlateSaphira(
                            tanggal=tanggal,
                            shift=shift,
                            item_code=plate['item_code'],
                            item_name=plate['item_name'],
                            jumlah_stock_awal=0,
                            jumlah_pemakaian=0,
                            jumlah_incoming=incoming_amount,
                            incoming_shift=shift,
                            jumlah_stock_akhir=incoming_amount,
                            jumlah_per_box=plate['jumlah_per_box'],
                            confirmed_by=current_user.id
                        )
                        db.session.add(new_stock)
            
            # Proses Saphira chemicals
            for chemical in data['saphira'].get('chemicals', []):
                incoming_amount = chemical.get('jumlah_incoming', 0)
                if incoming_amount > 0:
                    stock = KartuStockChemicalSaphira.query.filter_by(
                        tanggal=tanggal,
                        item_code=chemical['item_code'],
                        shift=shift  # PERBAIKAN: Tambahkan filter shift
                    ).first()

                    if stock:
                        stock.jumlah_incoming += incoming_amount
                        stock.incoming_shift = shift
                        stock.jumlah_stock_akhir += incoming_amount
                    else:
                        new_stock = KartuStockChemicalSaphira(
                            tanggal=tanggal,
                            shift=shift,
                            item_code=chemical['item_code'],
                            item_name=chemical['item_name'],
                            jumlah_stock_awal=0,
                            jumlah_pemakaian=0,
                            jumlah_incoming=incoming_amount,
                            incoming_shift=shift,
                            jumlah_stock_akhir=incoming_amount,
                            confirmed_by=current_user.id
                        )
                        db.session.add(new_stock)

        db.session.commit()
        return jsonify({'message': 'Stock incoming berhasil disimpan'}), 200

    except Exception as e:
        db.session.rollback()
        print(f"Error: {str(e)}")
        return jsonify({'error': 'Terjadi kesalahan saat menyimpan data: ' + str(e)}), 500

# Routes for Division Management
@app.route('/admin/divisions')
@login_required
@require_admin
def admin_divisions():
    return render_template('admin_divisions.html')

@app.route('/get-divisions-data')
@login_required
@require_admin
def get_divisions_data():
    page = request.args.get('page', 1, type=int)
    search = request.args.get('search', '')
    sort_by = request.args.get('sort_by', 'name')
    sort_order = request.args.get('sort_order', 'asc')
    per_page = 10

    query = Division.query

    if search:
        search_term = f"%{search}%"
        query = query.filter(
            or_(
                Division.name.ilike(search_term),
                Division.description.ilike(search_term)
            )
        )
    
    # Handle sorting
    if sort_by in ['name', 'description', 'created_at']:
        sort_column = getattr(Division, sort_by)
        if sort_order == 'desc':
            sort_column = sort_column.desc()
        query = query.order_by(sort_column)

    pagination = query.paginate(page=page, per_page=per_page)
    divisions = pagination.items

    return jsonify({
        'data': [{
            'id': div.id,
            'name': div.name,
            'description': div.description,
            'created_at': div.created_at.isoformat() if div.created_at else None
        } for div in divisions],
        'page': page,
        'pages': pagination.pages,
        'total': pagination.total
    })

@app.route('/admin/division/<int:division_id>')
@login_required
@require_admin
def admin_get_division(division_id):
    division = db.session.get(Division, division_id) # Menggunakan db.session.get
    if division is None:
        abort(404, description="Division not found")
    return jsonify({
        'id': division.id,
        'name': division.name,
        'description': division.description
    })

@app.route('/admin/division/add', methods=['POST'])
@login_required
@require_admin
def admin_add_division():
    try:
        name = request.form['name']
        description = request.form['description']

        if Division.query.filter_by(name=name).first():
            return jsonify({
                'success': False,
                'message': 'Division name already exists'
            }), 400

        division = Division(
            name=name,
            description=description
        )
        db.session.add(division)
        db.session.commit()
        return jsonify({
            'success': True,
            'message': 'Division added successfully'
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': f'Failed to add division: {str(e)}'
        }), 400

@app.route('/admin/division/edit', methods=['POST'])
@login_required
@require_admin
def admin_edit_division():
    try:
        division_id = request.form['division_id']
        division = db.session.get(Division, division_id) # Menggunakan db.session.get
        if division is None:
            abort(404, description="Division not found")
        
        division.name = request.form['name']
        division.description = request.form['description']
        
        db.session.commit()
        return jsonify({
            'success': True,
            'message': 'Division updated successfully'
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': f'Failed to update division: {str(e)}'
        }), 400

@app.route('/admin/division/delete', methods=['POST'])
@login_required
@require_admin
def admin_delete_division():
    try:
        division_id = request.form['division_id']
        division = db.session.get(Division, division_id) # Menggunakan db.session.get
        if division is None:
            abort(404, description="Division not found")
        
        if User.query.filter_by(division_id=division.id).first():
            return jsonify({
                'success': False,
                'message': 'Cannot delete division: There are users assigned to this division'
            }), 400
            
        db.session.delete(division)
        db.session.commit()
        return jsonify({
            'success': True,
            'message': 'Division deleted successfully'
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': f'Failed to delete division: {str(e)}'
        }), 400

# --- Routes for Monthly Work Hours ---
@app.route('/monthly_work_hours', methods=['POST'])
@login_required
@require_admin
def save_monthly_work_hours():
    data = request.get_json()
    
    # Validate input data
    required_fields = ['year', 'month', 'total_work_hours_produksi', 'total_work_hours_proof']
    if not all(field in data for field in required_fields):
        return jsonify({'success': False, 'error': 'Missing required fields'}), 400
        
    try:
        # Check if record already exists
        existing_record = MonthlyWorkHours.query.filter_by(
            year=data['year'],
            month=data['month']
        ).first()
        
        if existing_record:
            # Update existing record
            existing_record.total_work_hours_proof = float(data['total_work_hours_proof'])
            existing_record.total_work_hours_produksi = float(data['total_work_hours_produksi'])
            existing_record.updated_at = datetime.utcnow()
        else:
            # Create new record
            new_record = MonthlyWorkHours(
                year=data['year'],
                month=data['month'],
                total_work_hours_proof=float(data['total_work_hours_proof']),
                total_work_hours_produksi=float(data['total_work_hours_produksi']),
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
            db.session.add(new_record)
            
        db.session.commit()
        return jsonify({'success': True}), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/monthly_work_hours/<int:year>/<int:month>', methods=['GET'])
@login_required
def get_monthly_work_hours(year, month):
    try:
        record = MonthlyWorkHours.query.filter_by(year=year, month=month).first()
        if record:
            return jsonify({
                'success': True,
                'data': {
                    'total_work_hours_proof': record.total_work_hours_proof,
                    'total_work_hours_produksi': record.total_work_hours_produksi,
                    'year': record.year,
                    'month': record.month
                }
            }), 200
        else:
            return jsonify({
                'success': False,
                'error': 'Record not found'
            }), 404
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


# Inisialisasi database
#with app.app_context():
    #db.create_all() # Create tables if they don't exist

    # Add dummy data for PlateAdjustmentRequest if table is empty
    #if PlateAdjustmentRequest.query.count() == 0:
    #    print("Adding dummy CTP adjustment data...")
    #    
    #    # Dummy data with 'proses_ctp' status
    #    dummy_entries = [
    #        PlateAdjustmentRequest(
    #            tanggal=datetime(2025, 8, 1).date(),
    #            mesin_cetak="SM74-1",
    #            pic="Budi Santoso",
    #            remarks="PRODUKSI",
    #            wo_number="WO001-2025",
    #            mc_number="MC001",
    #            run_length=1000,
    #            item_name="Kemasan Box Makanan A",
    #            jumlah_plate=4,
    #            note="Perlu adjustment warna untuk konsistensi",
    #            status="proses_ctp",
    #            adjustment_finish_at=datetime.utcnow(),
    #            adjustment_by="Ahmad"
    #        ),
    #        PlateAdjustmentRequest(
    #            tanggal=datetime(2025, 8, 1).date(),
    #            mesin_cetak="SM52",
    #            pic="Sari Dewi",
    #            remarks="PROOF",
    #            wo_number="WO002-2025",
    #            mc_number="MC002",
    #            run_length=500,
    #            item_name="Brosur Promosi B",
    #            jumlah_plate=2,
    #            note="Test proof untuk approval client",
    #            status="proses_ctp",
    #            adjustment_finish_at=datetime.utcnow(),
    #            adjustment_by="Rina"
    #        ),
    #        PlateAdjustmentRequest(
    #            tanggal=datetime(2025, 8, 1).date(),
    #            mesin_cetak="SM74-2",
    #            pic="Eko Prasetyo",
    #            remarks="PRODUKSI",
    #            wo_number="WO003-2025",
    #            mc_number="MC003",
    #            run_length=2000,
    #            item_name="Katalog Produk C",
    #            jumlah_plate=8,
    #            note="High quality printing untuk katalog premium",
    #            status="proses_ctp",
    #            adjustment_finish_at=datetime.utcnow(),
    #            adjustment_by="Dian",
    #            plate_start_at=datetime.utcnow(),
    #            ctp_by="Joko"
    #        )
    #    ]
    #    
    #    for entry in dummy_entries:
    #        db.session.add(entry)
    #    
    #   db.session.commit()
    #    print("Dummy CTP adjustment data added.")

    # Optional: Add dummy data if database is empty
    # if CTPProductionLog.query.count() == 0:
    #     print("Adding dummy data...")
    #     dummy_entry = CTPProductionLog(
    #         log_date=datetime(2025, 7, 20).date(),
    #         ctp_group="Group B", ctp_shift="2", ctp_pic="Joko", ctp_machine="CTP 2",
    #         processor_temperature=24.1, dwell_time=25.5, wo_number="WO987", mc_number="MC987",
    #         run_length_sheet=750, print_machine="SM74", remarks_job="Packaging", item_name="Box A",
    #         note="Test entry for CTP log", plate_type_material="Kodak Sonora", raster="FM",
    #         num_plate_good=15, num_plate_not_good=0, not_good_reason=None,
    #         cyan_25_percent=25.0, cyan_50_percent=50.0, cyan_75_percent=75.0,
    #         magenta_25_percent=25.0, magenta_50_percent=50.0, magenta_75_percent=75.0,
    #         yellow_25_percent=25.0, yellow_50_percent=50.0, yellow_75_percent=75.0,
    #         black_25_percent=25.0, black_50_percent=50.0, black_75_percent=75.0,
    #         x_25_percent=25.0, x_50_percent=50.0, x_75_percent=75.0,
    #         z_25_percent=25.0, z_50_percent=50.0, z_75_percent=75.0,
    #         u_25_percent=25.0, u_50_percent=50.0, u_75_percent=75.0,
    #         v_25_percent=25.0, v_50_percent=50.0, v_75_percent=75.0,
    #         start_time=time(9, 30), finish_time=time(10, 30) # Contoh: Gunakan objek time()
    #     )
    #     db.session.add(dummy_entry)
    #     db.session.commit()
    #     print("Dummy data added.")




# --- Chemical Bon CTP Routes ---
@app.route('/chemical-bon-ctp')
@login_required
@require_ctp_access
def chemical_bon_ctp():
    return render_template('chemical_bon_ctp.html')

@app.route('/api/chemical-bon-ctp/list', methods=['GET'])
@login_required
@require_ctp_access
def get_chemical_bon_list():
    try:
        # Join dengan tabel User untuk mendapatkan nama user
        query = ChemicalBonCTP.query.join(User, ChemicalBonCTP.created_by == User.id)
        
        # Get query parameters
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 10, type=int)
        search = request.args.get('search', '')
        brand_filter = request.args.get('brand', '')
        year_filter = request.args.get('year', '')
        month_filter = request.args.get('month', '')
        
        # Base query
        query = ChemicalBonCTP.query
        
        # Apply filters
        if search:
            search_term = f"%{search}%"
            query = query.filter(
                or_(
                    ChemicalBonCTP.request_number.ilike(search_term),
                    ChemicalBonCTP.item_name.ilike(search_term),
                    ChemicalBonCTP.item_code.ilike(search_term)
                )
            )
        
        if brand_filter:
            query = query.filter(ChemicalBonCTP.brand == brand_filter)
            
        # Apply year filter
        if year_filter:
            query = query.filter(extract('year', ChemicalBonCTP.tanggal) == int(year_filter))
            
        # Apply month filter
        if month_filter:
            query = query.filter(extract('month', ChemicalBonCTP.tanggal) == int(month_filter))
            
        # Order by latest first
        query = query.order_by(ChemicalBonCTP.created_at.desc())
        
        # Paginate
        pagination = query.paginate(page=page, per_page=per_page)
        
        return jsonify({
            'success': True,
            'data': [item.to_dict() for item in pagination.items],
            'total': pagination.total,
            'pages': pagination.pages,
            'current_page': page
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500

@app.route('/api/chemical-bon-ctp/create', methods=['POST'])
@login_required
@require_ctp_access
def create_chemical_bon():
    try:
        jakarta_tz = pytz.timezone('Asia/Jakarta')
        now_jakarta = datetime.now(jakarta_tz)
        data = request.get_json()
        
        # Validasi data dasar
        base_required_fields = ['request_number', 'tanggal', 'bon_periode', 'brand', 'items']
        for field in base_required_fields:
            if field not in data:
                return jsonify({
                    'success': False,
                    'message': f'Field {field} harus diisi'
                }), 400

        # Validasi items
        if not data['items'] or not isinstance(data['items'], list):
            return jsonify({
                'success': False,
                'message': 'Items harus berupa array dan tidak boleh kosong'
            }), 400

        # Parse tanggal
        bon_date = datetime.strptime(data['tanggal'], '%Y-%m-%d').date()
        
        # Cari bon number terakhir pada bulan yang sama dari kedua tabel
        current_month_start = bon_date.replace(day=1)
        next_month_start = (current_month_start + timedelta(days=32)).replace(day=1)
        
        # Cari bon number terakhir dari tabel bon_plate
        latest_bon_plate = BonPlate.query.filter(
            BonPlate.tanggal >= current_month_start,
            BonPlate.tanggal < next_month_start
        ).order_by(BonPlate.bon_number.desc()).first()
        
        # Cari bon number terakhir dari tabel chemical_bon_ctp
        latest_chemical_bon = ChemicalBonCTP.query.filter(
            ChemicalBonCTP.tanggal >= current_month_start,
            ChemicalBonCTP.tanggal < next_month_start
        ).order_by(ChemicalBonCTP.bon_number.desc()).first()
        
        # Bandingkan nomor terakhir dari kedua tabel
        last_num = 0
        if latest_bon_plate:
            # Ambil nomor urut dari awal bon_number (sebelum tanda /)
            last_num_plate = int(latest_bon_plate.bon_number.split('/')[0])
            last_num = max(last_num, last_num_plate)
            
        if latest_chemical_bon:
            # Ambil nomor urut dari awal bon_number (sebelum tanda /)
            last_num_chemical = int(latest_chemical_bon.bon_number.split('/')[0])
            last_num = max(last_num, last_num_chemical)
            
        # Generate bon number baru
        new_num = str(last_num + 1).zfill(3) if last_num > 0 else '001'

        # Format: new_num/OUT/ODGN/roman month/year
        roman_month = ['I', 'II', 'III', 'IV', 'V', 'VI', 'VII', 'VIII', 'IX', 'X', 'XI', 'XII']
        bon_number = f"{new_num}/OUT/ODGN/{roman_month[bon_date.month-1]}/{bon_date.year}"
        
        created_bons = []
        
        # Buat instance ChemicalBonCTP untuk setiap item
        for item in data['items']:
            # Validasi data item
            item_required_fields = ['item_code', 'item_name', 'jumlah']
            for field in item_required_fields:
                if field not in item:
                    return jsonify({
                        'success': False,
                        'message': f'Field {field} harus diisi untuk setiap item'
                    }), 400

            new_bon = ChemicalBonCTP(
                bon_number=bon_number,
                request_number=data['request_number'],
                tanggal=bon_date,
                bon_periode=data['bon_periode'],
                item_code=item['item_code'],
                item_name=item['item_name'],
                brand=data['brand'],
                unit='GLN',  # Selalu GLN
                jumlah=item['jumlah'],
                created_by=current_user.id,
                created_at=now_jakarta
            )
            
            db.session.add(new_bon)
            created_bons.append(new_bon)
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Chemical Bon CTP berhasil dibuat',
            'data': [bon.to_dict() for bon in created_bons]
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500

@app.route('/api/chemical-bon-ctp/<int:bon_id>', methods=['GET'])
@login_required
@require_ctp_access
def get_chemical_bon_detail(bon_id):
    try:
        bon = db.session.get(ChemicalBonCTP, bon_id) # Menggunakan db.session.get
        if bon is None:
            abort(404, description="Chemical Bon CTP not found")
        return jsonify({
            'success': True,
            'data': bon.to_dict()
        })
    except Exception as e:
        print(f"Error getting chemical bon detail: {e}")
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500

@app.route('/api/chemical-items/<brand>')
@login_required
@require_ctp_access
def get_chemical_items(brand):
    # Daftar items berdasarkan brand
    items = {
        'SAPHIRA': [
            {'code': '02-005-000-0000061', 'name': '(SUT1.PN4LNUV) SAPHIRA PN DEVELOPER 20 L'},
            {'code': '02-005-000-0000046', 'name': '(SUT1.PN4NCRY) SAPHIRA PN REPLENISHER 20 L'},
            {'code': '02-005-000-0000158', 'name': '(SUT1.1624001) SAPHIRA CTP PREMIUM PLATE FINISHER (GLN 5L)'}
        ],
        'FUJI': [
            {'code': '02-005-000-0000153', 'name': 'DEVELOPER FUJI LH-D2WS (GLN 25L)'},
            {'code': '02-005-000-0000154', 'name': 'REPLENISHER FUJI LH-D2RWS (GLN 25L)'}
        ]
    }
    
    return jsonify({
        'success': True,
        'data': items.get(brand.upper(), [])
    })

# --- Rute Authentication ---
@app.route('/login', methods=['GET', 'POST'])
def login():
    # Clear any existing flash messages when entering login page
    session.pop('_flashes', None)
    
    # Jika user sudah login, redirect ke dashboard
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        remember_me = bool(request.form.get('remember_me'))
        
        # Validasi input
        if not username or not password:
            flash('Username dan password harus diisi.', 'error')
            return render_template('login.html')
        
        # Cari user berdasarkan username
        user = User.query.filter_by(username=username).first()
        
        if user and user.check_password(password):
            # Login berhasil
            login_user(user, remember=remember_me)
            
            # Redirect ke halaman yang diminta atau dashboard
            next_page = request.args.get('next')
            if not next_page or not next_page.startswith('/'):
                next_page = url_for('index')
            
            return redirect(next_page)
        else:
            # Login gagal
            flash('Username atau password salah.', 'error')
    
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    session.clear()  # Clear all session data including flash messages
    return redirect(url_for('login'))

# --- Rute Halaman ---
@app.route('/')
@login_required
def index():
    return render_template('index.html')

@app.route('/input-kpi-ctp')
@login_required
@require_ctp_access
def input_kpi_ctp():
    return render_template('kpictp.html')

@app.route('/tabel-kpi-ctp')
@login_required
@require_ctp_access
def tabel_kpi_ctp():
    return render_template('tabelkpictp.html')

# NEW: Rute untuk merender halaman edit_kpi_ctp.html
@app.route('/edit-kpi-ctp/<int:data_id>')
@login_required
@require_ctp_access
def edit_kpi_ctp_page(data_id):
    # Ambil data dari database
    kpi_entry = db.session.get(CTPProductionLog, data_id) # Menggunakan db.session.get
    if kpi_entry is None:
        abort(404, description="CTP Production Log not found")

    # Admin selalu boleh akses
    if current_user.is_admin():
        return render_template('edit_kpi_ctp.html', data_id=data_id)

    # Non-admin: cek apakah data <24 jam
    now = datetime.utcnow()
    if kpi_entry.created_at:
        age = now - kpi_entry.created_at
        if age.total_seconds() <= 24 * 3600:
            return render_template('edit_kpi_ctp.html', data_id=data_id)
        else:
            flash('Akses edit hanya diperbolehkan untuk data yang berumur kurang dari 24 jam.', 'error')
            return redirect(url_for('tabel_kpi_ctp'))
    else:
        flash('Data tidak memiliki informasi waktu pembuatan.', 'error')
        return redirect(url_for('tabel_kpi_ctp'))

@app.route('/request-plate-adjustment')
@login_required
def request_plate_adjustment_page():
    return render_template('request_plate_adjustment.html')

@app.route('/request-plate-bon')
@login_required
def request_plate_bon_page():
    return render_template('request_plate_bon.html')

# NEW: Rute untuk halaman Data Adjustment
@app.route('/data-adjustment')
@login_required
@require_press_access
def data_adjustment_page():
    return render_template('data_adjustment.html', current_user=current_user)

# NEW: Rute untuk halaman Data Bon
@app.route('/data-bon')
@login_required
@require_press_access
def data_bon_page():
    return render_template('data_bon.html')

# NEW: Rute untuk halaman detail adjustment
@app.route('/detail-adjustment/<int:adjustment_id>')
@login_required
def detail_adjustment_page(adjustment_id):
    adjustment = db.session.get(PlateAdjustmentRequest, adjustment_id) # Menggunakan db.session.get
    if adjustment is None:
        abort(404, description="Plate Adjustment Request not found")
    return render_template('detail_adjustment.html', data=adjustment.to_dict())

# NEW: Rute untuk halaman detail bon
@app.route('/detail-bon/<int:bon_id>')
@login_required
def detail_bon_page(bon_id):
    bon = db.session.get(PlateBonRequest, bon_id) # Menggunakan db.session.get
    if bon is None:
        abort(404, description="Plate Bon Request not found")
    return render_template('detail_bon.html', data=bon.to_dict())

# --- API Endpoint untuk Operasi CRUD ---

# Route untuk mengambil semua data plate dan status bon web
@app.route('/get-all-plate-data', methods=['GET'])
@login_required
def get_all_plate_data():
    date_str = request.args.get('date')
    plate_type = request.args.get('plate_type')
    
    if not date_str or not plate_type:
        return jsonify({'success': False, 'message': 'Tanggal dan jenis plate harus diisi.'}), 400
    
    try:
        usage_date = datetime.strptime(date_str, '%Y-%m-%d').date()
        
        bon_record = BonPlate.query.filter_by(tanggal=usage_date, jenis_plate=plate_type).first()
        bon_web_data = None
        if bon_record:
            bon_web_data = {
                'exists': True,
                'request_number': bon_record.request_number,
                'bon_periode': bon_record.bon_periode, # Tambahkan bon_periode
                'date': bon_record.tanggal.strftime('%Y-%m-%d')
            }
        else:
            bon_web_data = {
                'exists': False,
                'bon_periode': None
            }
        
        if plate_type.upper() not in PLATE_DETAILS:
            return jsonify({'success': False, 'message': f'Tidak ada konfigurasi untuk jenis plate {plate_type}'}), 400
        
        plate_dict = PLATE_DETAILS[plate_type.upper()]
        
        query = db.session.query(
            CTPProductionLog.plate_type_material,
            func.coalesce(func.sum(CTPProductionLog.num_plate_good), 0).label('good'),
            func.coalesce(func.sum(CTPProductionLog.num_plate_not_good), 0).label('not_good')
        ).filter(
            CTPProductionLog.log_date == usage_date,
            func.upper(CTPProductionLog.plate_type_material).like(f'%{plate_type.upper()}%')
        ).group_by(
            CTPProductionLog.plate_type_material
        ).all()
        
        plate_usage_data = []
        plate_sizes = list(plate_dict.keys())
        
        for usage in query:
            total = int(usage.good) + int(usage.not_good)
            if total > 0:
                material = usage.plate_type_material.upper()
                matched_size = None
                
                for size in plate_sizes:
                    size_check = size.replace(' ', '')
                    material_check = material.replace(' ', '')
                    if size_check in material_check:
                        matched_size = size
                        if 'UV' in material and size == '1030':
                            matched_size = '1030 UV'
                        elif 'PN' in material and size == '1055':
                            matched_size = '1055 PN'
                        elif 'UV' in material and size == '1055':
                            matched_size = '1055 UV'
                        elif 'LHPL' in material and size == '1055':
                            matched_size = '1055 LHPL'
                        break
                
                if matched_size in plate_dict:
                    plate_info = plate_dict[matched_size]
                    plate_usage_data.append({
                        'item_code': plate_info['code'],
                        'item_name': plate_info['name'],
                        'jumlah': total
                    })
        
        return jsonify({
            'success': True,
            'bon_web': bon_web_data,
            'plate_usage': plate_usage_data,
            'message': 'Data berhasil dimuat.'
        })

    except Exception as e:
        print(f"Error: {str(e)}")
        return jsonify({
            'success': False,
            'message': 'Terjadi kesalahan saat mengambil data.'
        }), 500

# --- API untuk submit plate adjustment
@app.route('/submit-plate-adjustment', methods=['POST'])
def submit_plate_adjustment():
    data = request.json
    try:
        jakarta_tz = pytz.timezone('Asia/Jakarta')
        now_jakarta = datetime.now(jakarta_tz)
        
        # --- 1. Ambil dan Konversi Nilai EPSON ---
        # Ambil nilai '1' atau '0' dari JSON. Default ke '0' (TIDAK) jika tidak ada.
        is_epson_value = data.get('item_epson_boolean', '0')
        
        # Konversi string '1' menjadi True, dan '0' (atau nilai lain) menjadi False.
        # Ini adalah cara paling efisien karena '1' dan '0' adalah nilai yang pasti.
        is_epson_converted = (is_epson_value == '1')
        # ----------------------------------------
        
        new_request = PlateAdjustmentRequest(
            tanggal=datetime.strptime(data['tanggal'], '%Y-%m-%d').date(),
            mesin_cetak=data['mesin_cetak'],
            pic=data['pic'],
            remarks=data['remarks'],
            wo_number=data['wo_number'],
            mc_number=data['mc_number'],
            run_length=data.get('run_length'),
            item_name=data['item_name'],
            jumlah_plate=data['jumlah_plate'],
            note=data.get('note'),
            machine_off_at=now_jakarta,  # waktu mesin off otomatis
            is_epson=is_epson_converted 
        )
        
        db.session.add(new_request)
        db.session.commit()
        return jsonify({'message': 'Request plate adjustment berhasil disubmit!'}), 201
    except Exception as e:
        db.session.rollback()
        # Sebaiknya tambahkan logging untuk error yang lebih baik
        print(f"Error submitting plate adjustment: {e}") 
        return jsonify({'error': str(e)}), 400

# --- API untuk submit plate bon
@app.route('/submit-plate-bon', methods=['POST'])
def submit_plate_bon():
    data = request.json
    try:
        jakarta_tz = pytz.timezone('Asia/Jakarta')
        now_jakarta = datetime.now(jakarta_tz)
        new_request = PlateBonRequest(
            tanggal=datetime.strptime(data['tanggal'], '%Y-%m-%d').date(),
            mesin_cetak=data['mesin_cetak'],
            pic=data['pic'],
            remarks=data['remarks'],
            wo_number=data['wo_number'],
            mc_number=data['mc_number'],
            run_length=data.get('run_length'),
            item_name=data['item_name'],
            jumlah_plate=data['jumlah_plate'],
            note=data.get('note'),
            machine_off_at=now_jakarta  # waktu mesin off otomatis
        )
        db.session.add(new_request)
        db.session.commit()
        return jsonify({'message': 'Request plate bon berhasil disubmit!'}), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 400

# API untuk mengambil data users dengan fitur search dan sort
@app.route('/get-users-data', methods=['GET'])
@login_required
@require_admin
def get_users_data():
    search_query = request.args.get('search', '').strip()
    sort_by = request.args.get('sort_by', 'id')
    sort_order = request.args.get('sort_order', 'desc')
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 30, type=int)

    try:
        # Base query dengan outerjoin ke Division untuk mendukung search dan sort
        query = User.query.outerjoin(Division)

        # Search functionality
        if search_query:
            search_term = f"%{search_query}%"
            query = query.filter(
                or_(
                    User.name.ilike(search_term),
                    User.username.ilike(search_term),
                    User.role.ilike(search_term),
                    Division.name.ilike(search_term),
                    User.grup.ilike(search_term)
                )
            )

        # Sorting dengan handling khusus untuk division_name
        if sort_by == 'division_name':
            sort_column = Division.name
        else:
            sort_column = getattr(User, sort_by, User.id)
        
        if sort_order == 'desc':
            sort_column = sort_column.desc()
            
        # Tambahkan secondary sort berdasarkan ID untuk konsistensi
        if sort_by == 'division_name':
            query = query.order_by(sort_column, User.id)
        else:
            query = query.order_by(sort_column)

        # Pagination
        pagination = query.paginate(page=page, per_page=per_page, error_out=False)
        items = [item.to_dict() for item in pagination.items]

        return jsonify({
            'data': items,
            'total': pagination.total,
            'page': pagination.page,
            'per_page': pagination.per_page,
            'pages': pagination.pages
        }), 200

    except Exception as e:
        print(f"Error fetching users data: {e}")
        return jsonify({'error': str(e)}), 500

# NEW: API untuk mengambil data adjustment (tabel)
@app.route('/get-adjustment-data', methods=['GET'])
@login_required
@require_press_access
def get_adjustment_data():
    search_query = request.args.get('search', '').strip()
    sort_by = request.args.get('sort_by', 'tanggal')
    sort_order = request.args.get('sort_order', 'desc')
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 30, type=int)
    # Ambil filter dari query string
    status = request.args.get('status', '').strip()
    mesin = request.args.get('mesin', '').strip()
    remarks = request.args.get('remarks', '').strip()

    try:
        query = PlateAdjustmentRequest.query


        if search_query:
            query = query.filter(
                or_(
                    PlateAdjustmentRequest.wo_number.ilike(f"%{search_query}%"),
                    PlateAdjustmentRequest.mc_number.ilike(f"%{search_query}%"),
                    PlateAdjustmentRequest.pic.ilike(f"%{search_query}%"),
                    PlateAdjustmentRequest.mesin_cetak.ilike(f"%{search_query}%"),
                    PlateAdjustmentRequest.remarks.ilike(f"%{search_query}%"),
                    PlateAdjustmentRequest.item_name.ilike(f"%{search_query}%"),
                    PlateAdjustmentRequest.note.ilike(f"%{search_query}%"),
                    cast(PlateAdjustmentRequest.id, String).ilike(f"%{search_query}%"),
                    cast(PlateAdjustmentRequest.run_length, String).ilike(f"%{search_query}%"),
                    cast(PlateAdjustmentRequest.jumlah_plate, String).ilike(f"%{search_query}%")
                )
            )

        # Filter status, mesin, remarks
        if status:
            query = query.filter_by(status=status)
        if mesin:
            query = query.filter_by(mesin_cetak=mesin)
        if remarks:
            query = query.filter_by(remarks=remarks)

        if hasattr(PlateAdjustmentRequest, sort_by):
            column_to_sort = getattr(PlateAdjustmentRequest, sort_by)
            if sort_order == 'asc':
                query = query.order_by(column_to_sort.asc())
            else:
                query = query.order_by(column_to_sort.desc())
        else:
            query = query.order_by(PlateAdjustmentRequest.tanggal.desc(), PlateAdjustmentRequest.id.desc())

        pagination = query.paginate(page=page, per_page=per_page, error_out=False)
        items = [item.to_dict() for item in pagination.items]

        return jsonify({
            'data': items,
            'total': pagination.total,
            'page': pagination.page,
            'per_page': pagination.per_page,
            'pages': pagination.pages
        }), 200

    except Exception as e:
        print(f"Error fetching adjustment data: {e}")
        return jsonify({'error': str(e)}), 500
    
# NEW: API untuk mengambil data bon (tabel)
@app.route('/get-bon-data', methods=['GET'])
@login_required
@require_press_access
def get_bon_data():
    search_query = request.args.get('search', '').strip()
    sort_by = request.args.get('sort_by', 'tanggal')
    sort_order = request.args.get('sort_order', 'desc')
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 30, type=int)
    # Ambil filter dari query string
    status = request.args.get('status', '').strip()
    mesin = request.args.get('mesin', '').strip()
    remarks = request.args.get('remarks', '').strip()

    try:
        query = PlateBonRequest.query

        if search_query:
            query = query.filter(
                or_(
                    PlateBonRequest.wo_number.ilike(f"%{search_query}%"),
                    PlateBonRequest.mc_number.ilike(f"%{search_query}%"),
                    PlateBonRequest.pic.ilike(f"%{search_query}%"),
                    PlateBonRequest.mesin_cetak.ilike(f"%{search_query}%"),
                    PlateBonRequest.remarks.ilike(f"%{search_query}%"),
                    PlateBonRequest.item_name.ilike(f"%{search_query}%"),
                    PlateBonRequest.note.ilike(f"%{search_query}%"),
                    cast(PlateBonRequest.id, String).ilike(f"%{search_query}%"),
                    cast(PlateBonRequest.run_length, String).ilike(f"%{search_query}%"),
                    cast(PlateBonRequest.jumlah_plate, String).ilike(f"%{search_query}%")
                )
            )

        # Filter status, mesin, remarks
        if status:
            query = query.filter_by(status=status)
        if mesin:
            query = query.filter_by(mesin_cetak=mesin)
        if remarks:
            query = query.filter_by(remarks=remarks)

        if hasattr(PlateBonRequest, sort_by):
            column_to_sort = getattr(PlateBonRequest, sort_by)
            if sort_order == 'asc':
                query = query.order_by(column_to_sort.asc())
            else:
                query = query.order_by(column_to_sort.desc())
        else:
            query = query.order_by(PlateBonRequest.tanggal.desc(), PlateBonRequest.id.desc())

        pagination = query.paginate(page=page, per_page=per_page, error_out=False)
        items = [item.to_dict() for item in pagination.items]

        return jsonify({
            'data': items,
            'total': pagination.total,
            'page': pagination.page,
            'per_page': pagination.per_page,
            'pages': pagination.pages
        }), 200

    except Exception as e:
        print(f"Error fetching adjustment data: {e}")
        return jsonify({'error': str(e)}), 500

# NEW: API untuk pembatalan Bon Plate
# NEW: API untuk pembatalan Bon Plate
@app.route('/cancel-bon-plate', methods=['POST'])
@login_required
@require_press_access 
def cancel_bon_plate():
    try:
        data = request.get_json()
        
        # Ambil data dari JSON Body
        bon_id = data.get('id')
        reason = data.get('reason')
        cancelled_by = data.get('cancelled_by') # Ini adalah NAMA PENGGUNA (String)
        
        # Validasi Input Dasar
        if not bon_id or not reason or not cancelled_by:
             return jsonify({'success': False, 'message': 'Data (ID, alasan, atau pembatal) tidak lengkap.'}), 400
        if not reason.strip():
             return jsonify({'success': False, 'message': 'Alasan pembatalan tidak boleh kosong.'}), 400

        bon_request = PlateBonRequest.query.get(bon_id)

        if not bon_request:
            return jsonify({'success': False, 'message': f'Bon Plate ID {bon_id} tidak ditemukan.'}), 404
            
        cancellable_statuses = ['proses_ctp']
        if bon_request.status not in cancellable_statuses:
             return jsonify({
                 'success': False,
                 'message': f'Bon tidak dapat dibatalkan. Status saat ini adalah: {bon_request.status}'
             }), 403 

        # Lakukan Pembatalan
        bon_request.status = 'bondibatalkan'
        bon_request.cancellation_reason = reason.strip()
        bon_request.cancelled_by = cancelled_by # Menyimpan NAMA PENGGUNA (STRING)
        bon_request.cancelled_at = datetime.now()

        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': f'Bon Plate ID {bon_id} berhasil dibatalkan.'
        }), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)}), 500
    
@app.route('/cancel-adjustment-plate', methods=['POST'])
@login_required
@require_press_access
def cancel_adjustment_plate():
    try:
        data = request.get_json()
        
        # Ambil data dari JSON Body
        adjustment_id = data.get('id')
        reason = data.get('reason')
        cancelled_by = data.get('cancelled_by') # Ini adalah NAMA PENGGUNA (String)
        
        # Validasi Input Dasar
        if not adjustment_id or not reason or not cancelled_by:
             return jsonify({'success': False, 'message': 'Data (ID, alasan, atau pembatal) tidak lengkap.'}), 400
        if not reason.strip():
             return jsonify({'success': False, 'message': 'Alasan pembatalan tidak boleh kosong.'}), 400

        adjustment_request = PlateAdjustmentRequest.query.get(adjustment_id)

        if not adjustment_request:
            return jsonify({'success': False, 'message': f'Adjustment Plate ID {adjustment_id} tidak ditemukan.'}), 404

        cancellable_statuses = ['menunggu_adjustment_pdnd', 'menunggu_adjustment_design']
        if adjustment_request.status not in cancellable_statuses:
             return jsonify({
                 'success': False,
                 'message': f'Adjustment tidak dapat dibatalkan. Status saat ini adalah: {adjustment_request.status}'
             }), 403 

        # Lakukan Pembatalan
        adjustment_request.status = 'adjustmentdibatalkan'
        adjustment_request.cancellation_reason = reason.strip()
        adjustment_request.cancelled_by = cancelled_by # Menyimpan NAMA PENGGUNA (STRING)
        adjustment_request.cancelled_at = datetime.now()

        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': f'Bon Plate ID {adjustment_id} berhasil dibatalkan.'
        }), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)}), 500
    
# API untuk Submit Data KPI (POST request dari form untuk data baru)
@app.route('/submit-kpi', methods=['POST'])
def submit_kpi():
    data = request.json
    try:
        # Konversi string waktu dari frontend ke objek time Python
        start_time_obj = datetime.strptime(data['start_time'], '%H:%M').time() if data.get('start_time') else None
        finish_time_obj = datetime.strptime(data['finish_time'], '%H:%M').time() if data.get('finish_time') else None

        new_entry = CTPProductionLog(
            log_date=datetime.strptime(data['log_date'], '%Y-%m-%d').date(),
            ctp_group=data['ctp_group'],
            ctp_shift=data['ctp_shift'],
            ctp_pic=data['ctp_pic'],
            ctp_machine=data['ctp_machine'],
            processor_temperature=data.get('processor_temperature'),
            dwell_time=data.get('dwell_time'),
            wo_number=data.get('wo_number'),
            mc_number=data.get('mc_number'),
            run_length_sheet=data.get('run_length_sheet'),
            print_machine=data.get('print_machine'),
            remarks_job=data.get('remarks_job'),
            item_name=data['item_name'],
            note=data['note'],
            plate_type_material=data.get('plate_type_material'),
            raster=data.get('raster'),
            num_plate_good=data['num_plate_good'],
            num_plate_not_good=data.get('num_plate_not_good'),
            not_good_reason=data.get('not_good_reason'),
            cyan_25_percent=data.get('cyan_25_percent'),
            cyan_50_percent=data.get('cyan_50_percent'),
            cyan_75_percent=data.get('cyan_75_percent'),
            magenta_25_percent=data.get('magenta_25_percent'),
            magenta_50_percent=data.get('magenta_50_percent'),
            magenta_75_percent=data.get('magenta_75_percent'),
            yellow_25_percent=data.get('yellow_25_percent'),
            yellow_50_percent=data.get('yellow_50_percent'),
            yellow_75_percent=data.get('yellow_75_percent'),
            black_25_percent=data.get('black_25_percent'),
            black_50_percent=data.get('black_50_percent'),
            black_75_percent=data.get('black_75_percent'),
            x_25_percent=data.get('x_25_percent'),
            x_50_percent=data.get('x_50_percent'),
            x_75_percent=data.get('x_75_percent'),
            z_25_percent=data.get('z_25_percent'),
            z_50_percent=data.get('z_50_percent'),
            z_75_percent=data.get('z_75_percent'),
            u_25_percent=data.get('u_25_percent'),
            u_50_percent=data.get('u_50_percent'),
            u_75_percent=data.get('u_75_percent'),
            v_25_percent=data.get('v_25_percent'),
            v_50_percent=data.get('v_50_percent'),
            v_75_percent=data.get('v_75_percent'),
            start_time=start_time_obj,  # Gunakan objek time
            finish_time=finish_time_obj # Gunakan objek time
        )
        db.session.add(new_entry)
        db.session.commit()
        return jsonify({'message': 'Data berhasil disubmit!'}), 201
    except Exception as e:
        db.session.rollback()
        print(f"Error submitting data: {e}")
        return jsonify({'error': str(e)}), 400
    
# API untuk Mengambil Data KPI (GET request untuk tabel)
@app.route('/get-kpi-data', methods=['GET'])
def get_kpi_data():
    search_query = request.args.get('search', '').strip()
    month_filter = request.args.get('month', '').strip()
    group_filter = request.args.get('group', '').strip()
    year_filter = request.args.get('year', '').strip()
    sort_by = request.args.get('sort_by', 'log_date')
    sort_order = request.args.get('sort_order', 'desc')
    # Tambahan untuk paginasi
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 30, type=int)

    try:
        query = CTPProductionLog.query

        if search_query:
            query = query.filter(
                or_(
                    CTPProductionLog.wo_number.ilike(f"%{search_query}%"),
                    CTPProductionLog.mc_number.ilike(f"%{search_query}%"),
                    CTPProductionLog.ctp_pic.ilike(f"%{search_query}%"),
                    CTPProductionLog.ctp_machine.ilike(f"%{search_query}%"),
                    CTPProductionLog.remarks_job.ilike(f"%{search_query}%"),
                    CTPProductionLog.item_name.ilike(f"%{search_query}%"),
                    CTPProductionLog.plate_type_material.ilike(f"%{search_query}%"),
                    CTPProductionLog.raster.ilike(f"%{search_query}%"),
                    CTPProductionLog.not_good_reason.ilike(f"%{search_query}%"),
                    CTPProductionLog.note.ilike(f"%{search_query}%"),
                    cast(CTPProductionLog.id, String).ilike(f"%{search_query}%"),
                    cast(CTPProductionLog.run_length_sheet, String).ilike(f"%{search_query}%"),
                    cast(CTPProductionLog.num_plate_good, String).ilike(f"%{search_query}%"),
                    cast(CTPProductionLog.num_plate_not_good, String).ilike(f"%{search_query}%"),
                    cast(CTPProductionLog.processor_temperature, String).ilike(f"%{search_query}%"),
                    cast(CTPProductionLog.dwell_time, String).ilike(f"%{search_query}%"),
                    cast(CTPProductionLog.log_date, String).ilike(f"%{search_query}%"),
                    cast(CTPProductionLog.start_time, String).ilike(f"%{search_query}%"),
                    cast(CTPProductionLog.finish_time, String).ilike(f"%{search_query}%")
                )
            )
        
        if month_filter:
            query = query.filter(extract('month', CTPProductionLog.log_date) == int(month_filter))

        if year_filter:
            query = query.filter(extract('year', CTPProductionLog.log_date) == int(year_filter))

        if group_filter:
            query = query.filter_by(ctp_group=group_filter)

        if hasattr(CTPProductionLog, sort_by):
            column_to_sort = getattr(CTPProductionLog, sort_by)
            if sort_order == 'asc':
                query = query.order_by(column_to_sort.asc())
            else:
                query = query.order_by(column_to_sort.desc())
        else:
            query = query.order_by(CTPProductionLog.log_date.desc(), CTPProductionLog.created_at.desc())

        # --- PAGINASI ---
        pagination = query.paginate(page=page, per_page=per_page, error_out=False)
        items = [item.to_dict() for item in pagination.items]

        return jsonify({
            'data': items,
            'total': pagination.total,
            'page': pagination.page,
            'per_page': pagination.per_page,
            'pages': pagination.pages
        }), 200

    except Exception as e:
        print(f"Error fetching data: {e}")
        return jsonify({'error': str(e)}), 500

# NEW: API untuk Mengambil Satu Data KPI berdasarkan ID (untuk mengisi form edit)
@app.route('/api/kpi_ctp/<int:data_id>', methods=['GET'])
def get_single_kpi_ctp(data_id):
    try:
        kpi_entry = db.session.get(CTPProductionLog, data_id)
        if kpi_entry:
            return jsonify(kpi_entry.to_dict()), 200
        else:
            abort(404, description="Data KPI CTP tidak ditemukan")
    except Exception as e:
        print(f"Error fetching single KPI CTP data: {e}")
        abort(500, description=f"Internal server error: {str(e)}")


# NEW: API untuk Memperbarui Data KPI (saat form edit disubmit)
@app.route('/api/kpi_ctp/<int:data_id>', methods=['PUT'])
def update_kpi_ctp(data_id):
    data = request.json
    try:
        kpi_entry = db.session.get(CTPProductionLog, data_id)
        if not kpi_entry:
            abort(404, description="Data KPI CTP tidak ditemukan")

        # Konversi string waktu dari frontend ke objek time Python
        kpi_entry.start_time = datetime.strptime(data['start_time'], '%H:%M').time() if data.get('start_time') else None
        kpi_entry.finish_time = datetime.strptime(data['finish_time'], '%H:%M').time() if data.get('finish_time') else None

        kpi_entry.log_date = datetime.strptime(data['log_date'], '%Y-%m-%d').date()
        kpi_entry.ctp_group = data.get('ctp_group', kpi_entry.ctp_group)
        kpi_entry.ctp_shift = data.get('ctp_shift', kpi_entry.ctp_shift)
        kpi_entry.ctp_pic = data.get('ctp_pic', kpi_entry.ctp_pic)
        kpi_entry.ctp_machine = data.get('ctp_machine', kpi_entry.ctp_machine)
        kpi_entry.processor_temperature = data.get('processor_temperature')
        kpi_entry.dwell_time = data.get('dwell_time')
        kpi_entry.wo_number = data.get('wo_number')
        kpi_entry.mc_number = data.get('mc_number', kpi_entry.mc_number)
        kpi_entry.run_length_sheet = data.get('run_length_sheet')
        kpi_entry.print_machine = data.get('print_machine', kpi_entry.print_machine)
        kpi_entry.remarks_job = data.get('remarks_job', kpi_entry.remarks_job)
        kpi_entry.item_name = data.get('item_name', kpi_entry.item_name)
        kpi_entry.note = data.get('note')
        kpi_entry.plate_type_material = data.get('plate_type_material', kpi_entry.plate_type_material)
        kpi_entry.raster = data.get('raster', kpi_entry.raster)
        kpi_entry.num_plate_good = data.get('num_plate_good')
        kpi_entry.num_plate_not_good = data.get('num_plate_not_good')
        kpi_entry.not_good_reason = data.get('not_good_reason')
        kpi_entry.cyan_25_percent = data.get('cyan_25_percent')
        kpi_entry.cyan_50_percent = data.get('cyan_50_percent')
        kpi_entry.cyan_75_percent = data.get('cyan_75_percent')
        kpi_entry.magenta_25_percent = data.get('magenta_25_percent')
        kpi_entry.magenta_50_percent = data.get('magenta_50_percent')
        kpi_entry.magenta_75_percent = data.get('magenta_75_percent')
        kpi_entry.yellow_25_percent = data.get('yellow_25_percent')
        kpi_entry.yellow_50_percent = data.get('yellow_50_percent')
        kpi_entry.yellow_75_percent = data.get('yellow_75_percent')
        kpi_entry.black_25_percent = data.get('black_25_percent')
        kpi_entry.black_50_percent = data.get('black_50_percent')
        kpi_entry.black_75_percent = data.get('black_75_percent')
        kpi_entry.x_25_percent = data.get('x_25_percent')
        kpi_entry.x_50_percent = data.get('x_50_percent')
        kpi_entry.x_75_percent = data.get('x_75_percent')
        kpi_entry.z_25_percent = data.get('z_25_percent')
        kpi_entry.z_50_percent = data.get('z_50_percent')
        kpi_entry.z_75_percent = data.get('z_75_percent')
        kpi_entry.u_25_percent = data.get('u_25_percent')
        kpi_entry.u_50_percent = data.get('u_50_percent')
        kpi_entry.u_75_percent = data.get('u_75_percent')
        kpi_entry.v_25_percent = data.get('v_25_percent')
        kpi_entry.v_50_percent = data.get('v_50_percent')
        kpi_entry.v_75_percent = data.get('v_75_percent')
        
        db.session.commit()
        return jsonify({'message': f'Data KPI CTP dengan ID {data_id} berhasil diperbarui!'}), 200
    except Exception as e:
        db.session.rollback()
        print(f"Error updating KPI CTP data: {e}")
        abort(500, description=f"Internal server error: {str(e)}")

# NEW: API untuk Menghapus Data KPI
@app.route('/api/kpi_ctp/<int:data_id>', methods=['DELETE'])

# Route untuk menyimpan nomor request bon
@app.route('/save-bon-request', methods=['POST'])
@login_required
def save_bon_request():
    data = request.get_json()
    tanggal = datetime.strptime(data['date'], '%Y-%m-%d').date()
    jenis_plate = data['plate_type']
    request_number = data['request_number']
    bon_periode = data.get('bon_periode') # Ambil nilai bon_periode

    try:
        existing_bon = BonPlate.query.filter_by(request_number=request_number).first()
        if existing_bon:
            return jsonify({'success': False, 'message': 'Nomor request bon sudah digunakan.'}), 409

        # Cari bon number terakhir pada bulan yang sama dari kedua tabel
        current_month_start = tanggal.replace(day=1)
        next_month_start = (current_month_start + timedelta(days=32)).replace(day=1)
        
        # Cari bon number terakhir dari tabel bon_plate
        latest_bon_plate = BonPlate.query.filter(
            BonPlate.tanggal >= current_month_start,
            BonPlate.tanggal < next_month_start
        ).order_by(BonPlate.bon_number.desc()).first()
        
        # Cari bon number terakhir dari tabel chemical_bon_ctp
        latest_chemical_bon = ChemicalBonCTP.query.filter(
            ChemicalBonCTP.tanggal >= current_month_start,
            ChemicalBonCTP.tanggal < next_month_start
        ).order_by(ChemicalBonCTP.bon_number.desc()).first()
        
        # Bandingkan nomor terakhir dari kedua tabel
        last_num = 0
        if latest_bon_plate:
            # Ambil nomor urut dari awal bon_number (sebelum tanda /)
            last_num_plate = int(latest_bon_plate.bon_number.split('/')[0])
            last_num = max(last_num, last_num_plate)
            
        if latest_chemical_bon:
            # Ambil nomor urut dari awal bon_number (sebelum tanda /)
            last_num_chemical = int(latest_chemical_bon.bon_number.split('/')[0])
            last_num = max(last_num, last_num_chemical)
            
        # Generate bon number baru
        new_number = str(last_num + 1).zfill(3)
            
        new_bon = BonPlate(
            bon_number=new_number,
            request_number=request_number,
            tanggal=tanggal,
            jenis_plate=jenis_plate,
            bon_periode=bon_periode, # Simpan bon_periode ke database
            created_at=datetime.now(),
            created_by=current_user.id
        )
        
        db.session.add(new_bon)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'bon_number': new_number,
            'message': 'Nomor request berhasil disimpan'
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': f'Gagal menyimpan nomor request: {str(e)}'}), 500

# Route untuk menampilkan chemical bon yang dicetak
@app.route('/print-chemical-bon')
@login_required
def print_chemical_bon():
    try:
        date_str = request.args.get('date')
        brand = request.args.get('brand')  # Menggunakan parameter yang sesuai
        request_number = request.args.get('request_number')
        
        if not date_str or not brand or not request_number:
            return jsonify({
                'success': False,
                'message': 'Parameter tanggal, brand, dan nomor request diperlukan'
            }), 400

        tanggal = datetime.strptime(date_str, '%Y-%m-%d').date()
        
        # Ambil semua bon dengan request_number yang sama
        bons = ChemicalBonCTP.query.filter_by(
            tanggal=tanggal,
            brand=brand,
            request_number=request_number
        ).all()
        
        if not bons:
            return jsonify({
                'success': False,
                'message': 'Data bon tidak ditemukan'
            }), 404
            
        # Ambil bon pertama untuk informasi umum
        first_bon = bons[0]
        
        # Ambil nama user yang membuat bon
        created_by_name = first_bon.user.name if first_bon.user and hasattr(first_bon.user, 'name') else '-'
        
        # Ambil 3 WO numbers random dari tabel CTPProductionLog pada bulan yang sama
        current_month_start = tanggal.replace(day=1)
        next_month_start = (current_month_start + timedelta(days=32)).replace(day=1)
        
        wo_numbers = db.session.query(CTPProductionLog.wo_number)\
            .filter(
                CTPProductionLog.log_date >= current_month_start,
                CTPProductionLog.log_date < next_month_start,
                CTPProductionLog.wo_number.isnot(None),
                CTPProductionLog.wo_number != ''
            )\
            .distinct()\
            .all()
            
        # Konversi hasil query ke list dan ambil 3 secara random
        wo_numbers = [wo[0] for wo in wo_numbers if wo[0]]  # Filter out None/empty values
        selected_wo_numbers = random.sample(wo_numbers, min(3, len(wo_numbers))) if wo_numbers else []
        
        # Format keterangan dengan WO numbers yang ditemukan
        wo_text = f"{', '.join(selected_wo_numbers)}" if selected_wo_numbers else ""
        keterangan = f"{wo_text}"
        
        # Update wo_number di database untuk setiap bon
        for bon in bons:
            bon.wo_number = wo_text
            db.session.add(bon)
        db.session.commit()

        # Format data untuk template - sekarang menggunakan semua bon
        items = []
        for bon in bons:
            item = {
                'item_code': bon.item_code,
                'item_name': bon.item_name,
                'jumlah': bon.jumlah,
                'keterangan': keterangan
            }
            items.append(item)

        return render_template(
            'chemical_bon_print.html',
            bon={
                'bon_number': first_bon.bon_number,
                'request_number': first_bon.request_number,
                'tanggal': first_bon.tanggal,
                'brand': first_bon.brand,
                'bon_periode': first_bon.bon_periode,
                'created_by_name': created_by_name,
                'keterangan': keterangan
            },
            items=items
        )
            
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Terjadi kesalahan: {str(e)}'
        }), 500

# Route untuk menampilkan bon plate yang dicetak
@app.route('/print-bon')
@login_required
def print_bon():
    try:
        date_str = request.args.get('date')
        plate_type = request.args.get('plate_type')
        request_number = request.args.get('request_number')
        
        if not date_str or not plate_type or not request_number:
            return "Parameter tidak lengkap", 400

        tanggal = datetime.strptime(date_str, '%Y-%m-%d').date()
        
        bon = BonPlate.query.filter_by(
            tanggal=tanggal,
            jenis_plate=plate_type,
            request_number=request_number
        ).first()

        if not bon:
            return "Bon tidak ditemukan", 404
        
        # Sisa logika untuk menyiapkan data print, sama seperti sebelumnya
        logs = CTPProductionLog.query.filter(
            CTPProductionLog.log_date == bon.tanggal,
            CTPProductionLog.plate_type_material.like(f'%{bon.jenis_plate}%')
        ).all()
        
        plate_counts = {}
        for log in logs:
            size = None
            if '1030' in log.plate_type_material:
                size = '1030'
            elif '1055' in log.plate_type_material:
                size = '1055'
            elif '1630' in log.plate_type_material:
                size = '1630'
            
            if size:
                if size not in plate_counts:
                    plate_counts[size] = 0
                plate_counts[size] += (log.num_plate_good or 0)
        
        plate_details = {
            'SAPHIRA': {
                '1030': {
                    'size': '1030 X 790 MM',
                    'code': '02-049-000-0000002',
                    'name': '(SUT1.PAO1SX1) SAPHIRA PA.27 27x1030x790 PKT50 (BOX 50PCS)'
                },
                '1055': {
                    'size': '1055 X 811 MM',
                    'code': '02-049-000-0000003',
                    'name': '(SUT1.PAO1SY3) SAPHIRA PA.27 27X1055X811 PKT50 (BOX 50PCS)'
                },
                '1055 PN': {
                    'size': '1055 X 811 MM',
                    'code': '02-049-000-0000011',
                    'name': '(SUT1.PNO7U8C) SAPHIRA PN 30 1055 X 811 MM PKT40 (BOX 40PCS)'
                },
                '1630': {
                    'size': '1630 X 1325 MM',
                    'code': '02-049-000-0000001',
                    'name': '(SUT1.PNOQXG8) SAPHIRA PN 40 1630 1325 PKT 30 (BOX 30PCS)'
                }
            },
            'FUJI': {
                '1030': {
                    'size': '1030 X 790 MM',
                    'code': '02-049-000-0000008',
                    'name': 'PLATE FUJI LH-PK 1030x790x0.3 (BOX 30PCS)'
                },
                '1030 UV': {
                    'size': '1030 X 790 MM',
                    'code': '02-023-000-0000007',
                    'name': 'PLATE FUJI LH-PJ2 1030x790x0.3 (BOX 30PCS)'
                },
                '1055': {
                    'size': '1055 X 811 MM',
                    'code': '02-049-000-0000010',
                    'name': 'PLATE FUJI LH-PK 1055x811x0.3 (BOX 30PCS)'
                },
                '1055 LHPL': {
                    'size': '1055 X 811 MM',
                    'code': '02-049-000-0000013',
                    'name': 'PLATE FUJI LH-PL 1055x811x0.3 (BOX 30PCS)'
                },
                '1055 UV': {
                    'size': '1055 X 811 MM',
                    'code': '02-049-000-0000012',
                    'name': 'PLATE FUJI LH-PJ2 1055x811x0.3 (BOX 30PCS)'
                },
                '1630': {
                    'size': '1630 X 1325 MM',
                    'code': '02-049-000-0000009',
                    'name': 'PLATE FUJI LH-PJ2 1630x1325x0.4 (BOX 15PCS)'
                }
            }
        }
        
        grouped = {}
        for log in logs:
            size = None
            if '1030' in log.plate_type_material:
                size = '1030'
            elif '1055' in log.plate_type_material:
                size = '1055'
            elif '1630' in log.plate_type_material:
                size = '1630'
            if size and size in plate_details[bon.jenis_plate]:
                details = plate_details[bon.jenis_plate][size]
                code = details['code']
                total_jumlah = (log.num_plate_good or 0) + (log.num_plate_not_good or 0)
                wo = log.wo_number or ''
                if code in grouped:
                    grouped[code]['jumlah'] += total_jumlah
                    if wo and wo not in grouped[code]['keterangan'].split(','):
                        if grouped[code]['keterangan']:
                            grouped[code]['keterangan'] += ',' + wo
                        else:
                            grouped[code]['keterangan'] = wo
                else:
                    grouped[code] = {
                        'item_code': code,
                        'item_name': details['name'],
                        'jumlah': total_jumlah,
                        'keterangan': wo
                    }

        items = list(grouped.values())

        created_by_name = bon.user.name if bon.user and hasattr(bon.user, 'name') else bon.created_by_name or '-'

        return render_template(
            'bon_print.html',
            bon={
                'bon_number': bon.bon_number,
                'request_number': bon.request_number,
                'tanggal': bon.tanggal,
                'jenis_plate': bon.jenis_plate,
                'bon_periode': bon.bon_periode, # Pastikan ini diteruskan ke template
                'created_by_name': created_by_name
            },
            items=items
        )
            
    except Exception as e:
        return f"Terjadi kesalahan: {str(e)}", 500
    
def delete_kpi_ctp(data_id):
    try:
        kpi_entry = db.session.get(CTPProductionLog, data_id)
        if not kpi_entry:
            abort(404, description="Data KPI CTP tidak ditemukan")

        db.session.delete(kpi_entry)
        db.session.commit()
        return jsonify({'message': f'Data KPI CTP dengan ID {data_id} berhasil dihapus.'}), 200
    except Exception as e:
        db.session.rollback()
        print(f"Error deleting KPI CTP data: {e}")
        abort(500, description=f"Internal server error: {str(e)}")

# --- Mounting Production Routes ---
@app.route('/decline-adjustment', methods=['POST'])
@login_required
@require_mounting_access
def decline_adjustment():
    try:
        data = request.get_json()
        adjustment_id = data.get('id')
        reason = data.get('reason')
        declined_by = data.get('declined_by')
        
        adjustment = PlateAdjustmentRequest.query.get(adjustment_id)
        if not adjustment:
            return jsonify({'success': False, 'message': 'Adjustment tidak ditemukan'}), 404
            
        adjustment.declined_at = datetime.now()
        adjustment.declined_by = declined_by
        adjustment.decline_reason = reason
        adjustment.is_declined = True
        adjustment.status = 'ditolakmounting'
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Adjustment berhasil ditolak'
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/mounting-data-adjustment')
@login_required
@require_mounting_access
def mounting_data_adjustment_page():
    return render_template('mounting_data_adjustment.html')

@app.route('/get-mounting-adjustment-data', methods=['GET'])
@login_required
@require_mounting_access
def get_mounting_adjustment_data():
    try:
        # Filter untuk mounting: menunggu_adjustment, proses_adjustment
        # Juga termasuk data yang sudah selesai untuk menghitung summary
        adjustments = PlateAdjustmentRequest.query.order_by(PlateAdjustmentRequest.id.desc()).all()
        
        # Filter hanya yang relevan untuk mounting (status menunggu dan proses)
        mounting_data = [
            adjustment.to_dict() for adjustment in adjustments 
            if adjustment.status in ['menunggu_adjustment', 'proses_adjustment']
        ]
        
        # Semua data untuk summary calculation
        all_data = [adjustment.to_dict() for adjustment in adjustments]
        
        return jsonify({
            'success': True,
            'data': mounting_data,
            'all_data': all_data,  # Untuk summary calculation
            'total': len(mounting_data)
        })
    except Exception as e:
        print(f"Error fetching mounting adjustment data: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/start-adjustment', methods=['POST'])
def start_adjustment():
    try:
        data = request.get_json()
        adjustment_id = data.get('id')
        adjustment_by = data.get('adjustment_by')
        
        if not adjustment_id or not adjustment_by:
            return jsonify({'success': False, 'error': 'Missing required data'}), 400
        
        adjustment = db.session.get(PlateAdjustmentRequest, adjustment_id) # Menggunakan db.session.get
        if adjustment is None:
            abort(404, description="Plate Adjustment Request not found")
        
        # Check if this is a reprocess
        is_reprocess = data.get('is_reprocess', False)

        # Update status
        adjustment.status = 'proses_adjustment'
        adjustment.adjustment_by = adjustment_by

        #Jika bukan proses ulang (first time), set adjustment_start_at
        if not is_reprocess:
            adjustment.adjustment_start_at = datetime.now()        
        # Jika ini adalah proses ulang, reset field terkait penolakan
        if is_reprocess:
            adjustment.adjustment_finish_at = None
            adjustment.declined_at = None
            adjustment.declined_by = None
            adjustment.decline_reason = None        

        db.session.commit()
        
        return jsonify({'success': True, 'message': 'Adjustment started successfully'})
    except Exception as e:
        print(f"Error starting adjustment: {e}")
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/finish-adjustment', methods=['POST'])
def finish_adjustment():
    try:
        data = request.get_json()
        adjustment_id = data.get('id')
        
        if not adjustment_id:
            return jsonify({'success': False, 'error': 'Missing adjustment ID'}), 400
        
        adjustment = db.session.get(PlateAdjustmentRequest, adjustment_id) # Menggunakan db.session.get
        if adjustment is None:
            abort(404, description="Plate Adjustment Request not found")
        
        # Update status dan waktu selesai adjustment
        adjustment.status = 'proses_ctp'
        adjustment.adjustment_finish_at = datetime.now()
        
        db.session.commit()
        
        return jsonify({'success': True, 'message': 'Adjustment finished successfully'})
    except Exception as e:
        print(f"Error finishing adjustment: {e}")
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500

# --- PDND Production Routes ---
@app.route('/pdnd-data-adjustment')
@login_required
@require_pdnd_access
def pdnd_data_adjustment_page():
    return render_template('pdnd_data_adjustment.html')

@app.route('/get-pdnd-adjustment-data', methods=['GET'])
@login_required
@require_pdnd_access
def get_pdnd_adjustment_data():
    try:
        # Filter untuk pdnd: menunggu_adjustment, proses_adjustment
        # Juga termasuk data yang sudah selesai untuk menghitung summary
        adjustments = PlateAdjustmentRequest.query.order_by(PlateAdjustmentRequest.id.desc()).all()

        # Filter hanya yang relevan untuk pdnd (status menunggu dan proses)
        pdnd_data = [
            adjustment.to_dict() for adjustment in adjustments 
            if adjustment.status in ['menunggu_adjustment_pdnd', 'proses_adjustment_pdnd']
        ]
        
        # Semua data untuk summary calculation
        all_data = [adjustment.to_dict() for adjustment in adjustments]
        
        return jsonify({
            'success': True,
            'data': pdnd_data,
            'all_data': all_data,  # Untuk summary calculation
            'total': len(pdnd_data)
        })
    except Exception as e:
        print(f"Error fetching pdnd adjustment data: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/start-adjustment-pdnd', methods=['POST'])
def start_adjustment_pdnd():
    try:
        data = request.get_json()
        adjustment_id = data.get('id')
        pdnd_by = data.get('pdnd_by')

        if not adjustment_id or not pdnd_by:
            return jsonify({'success': False, 'error': 'Missing required data'}), 400
        
        adjustment = db.session.get(PlateAdjustmentRequest, adjustment_id) # Menggunakan db.session.get
        if adjustment is None:
            abort(404, description="Plate Adjustment Request not found")
        
        # Check if this is a reprocess
        is_reprocess = data.get('is_reprocess', False)
        
        # Update status
        adjustment.status = 'proses_adjustment_pdnd'
        adjustment.pdnd_by = pdnd_by
        
        # Jika bukan proses ulang (first time), set pdnd_start_at
        if not is_reprocess:
            adjustment.pdnd_start_at = datetime.now()
        # Jika ini adalah proses ulang, reset field terkait penolakan
        else:
            adjustment.pdnd_finish_at = None
            adjustment.declined_at = None
            adjustment.declined_by = None
            adjustment.decline_reason = None
        
        db.session.commit()
        
        return jsonify({'success': True, 'message': 'Adjustment PDND started successfully'})
    except Exception as e:
        print(f"Error starting PDND adjustment: {e}")
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/finish-adjustment-pdnd', methods=['POST'])
def finish_adjustment_pdnd():
    try:
        data = request.get_json()
        adjustment_id = data.get('id')
        
        if not adjustment_id:
            return jsonify({'success': False, 'error': 'Missing adjustment ID'}), 400
        
        adjustment = db.session.get(PlateAdjustmentRequest, adjustment_id) # Menggunakan db.session.get
        if adjustment is None:
            abort(404, description="Plate Adjustment Request not found")
        
        # Update status dan waktu selesai adjustment
        adjustment.status = 'menunggu_adjustment'
        adjustment.pdnd_finish_at = datetime.now()
        
        db.session.commit()
        
        return jsonify({'success': True, 'message': 'Adjustment PDND finished successfully'})
    except Exception as e:
        print(f"Error finishing adjustment: {e}")
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/export-pdnd-adjustment', methods=['GET'])
def export_pdnd_adjustment():
    try:
        from flask import make_response, request, jsonify
        import io
        import openpyxl
        from datetime import datetime
        
        # Get filter parameters
        status_filter = request.args.get('status', '')
        remarks_filter = request.args.get('remarks', '')
        date_from = request.args.get('date_from', '')
        date_to = request.args.get('date_to', '')
        
        # Build query
        query = PlateAdjustmentRequest.query
        
        # Apply filters
        if status_filter:
            if status_filter == 'selesai':
                query = query.filter(PlateAdjustmentRequest.status.in_(['selesai', 'menunggu_adjustment_pdnd']))
            else:
                query = query.filter(PlateAdjustmentRequest.status == status_filter)
        
        if remarks_filter:
            query = query.filter(PlateAdjustmentRequest.remarks.ilike(f'%{remarks_filter}%'))
        
        if date_from:
            query = query.filter(PlateAdjustmentRequest.tanggal >= date_from)
        if date_to:
            query = query.filter(PlateAdjustmentRequest.tanggal <= date_to)
        
        # Get data sorted by date (newest first)
        adjustments = query.order_by(PlateAdjustmentRequest.tanggal.desc(), PlateAdjustmentRequest.id.desc()).all()
        
        # Create an in-memory Excel workbook and worksheet
        workbook = openpyxl.Workbook()
        worksheet = workbook.active
        worksheet.title = "PDND Adjustment Data"
        
        # Write headers
        headers = [
            'ID', 'Tanggal', 'Mesin Cetak', 'PIC', 'Remarks', 'WO Number', 'MC Number', 
            'Run Length', 'Item Name', 'Jumlah Plate', 'Note', 'Machine Off At',
            'PDND Start At', 'PDND Finish At', 'PDND By',
            'Design Start At', 'Design Finish At', 'Design By',
            'Adjustment Start At', 'Adjustment Finish At', 'Adjustment By', 
            'Plate Start At', 'Plate Finish At', 'Plate Delivered At', 'CTP By', 'Status'
        ]
        worksheet.append(headers)
        
        # Write data rows
        for adj in adjustments:
            row_data = [
                str(adj.id or ''),
                adj.tanggal.strftime('%Y-%m-%d') if adj.tanggal else '',
                str(adj.mesin_cetak or ''),
                str(adj.pic or ''),
                str(adj.remarks or ''),
                str(adj.wo_number or ''),
                str(adj.mc_number or ''),
                str(adj.run_length or ''),
                str(adj.item_name or ''),
                str(adj.jumlah_plate or ''),
                str(adj.note or ''),
                adj.machine_off_at.strftime('%Y-%m-%d %H:%M:%S') if adj.machine_off_at else '',
                adj.pdnd_start_at.strftime('%Y-%m-%d %H:%M:%S') if adj.pdnd_start_at else '',
                adj.pdnd_finish_at.strftime('%Y-%m-%d %H:%M:%S') if adj.pdnd_finish_at else '',
                str(adj.pdnd_by or ''),
                adj.design_start_at.strftime('%Y-%m-%d %H:%M:%S') if adj.design_start_at else '',
                adj.design_finish_at.strftime('%Y-%m-%d %H:%M:%S') if adj.design_finish_at else '',
                str(adj.design_by or ''),
                adj.adjustment_start_at.strftime('%Y-%m-%d %H:%M:%S') if adj.adjustment_start_at else '',
                adj.adjustment_finish_at.strftime('%Y-%m-%d %H:%M:%S') if adj.adjustment_finish_at else '',
                str(adj.adjustment_by or ''),
                adj.plate_start_at.strftime('%Y-%m-%d %H:%M:%S') if adj.plate_start_at else '',
                adj.plate_finish_at.strftime('%Y-%m-%d %H:%M:%S') if adj.plate_finish_at else '',
                adj.plate_delivered_at.strftime('%Y-%m-%d %H:%M:%S') if adj.plate_delivered_at else '',
                str(adj.ctp_by or ''),
                str(adj.status or '')
            ]
            worksheet.append(row_data)
        
        # Create response with proper Excel headers
        output = io.BytesIO()
        workbook.save(output)
        output.seek(0)
        
        response = make_response(output.getvalue())
        response.headers['Content-Type'] = 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        response.headers['Content-Disposition'] = f'attachment; filename=pdnd_adjustment_export_{datetime.now().strftime("%Y%m%d_%H%M%S")}.xlsx'
        
        return response
        
    except Exception as e:
        print(f"Error exporting data: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)}), 500

# --- Design Production Routes ---
@app.route('/design-data-adjustment')
@login_required
@require_design_access
def design_data_adjustment_page():
    return render_template('design_data_adjustment.html')

@app.route('/get-design-adjustment-data', methods=['GET'])
@login_required
@require_design_access
def get_design_adjustment_data():
    try:
        # Filter untuk design: menunggu_adjustment, proses_adjustment
        # Juga termasuk data yang sudah selesai untuk menghitung summary
        adjustments = PlateAdjustmentRequest.query.order_by(PlateAdjustmentRequest.id.desc()).all()

        # Filter hanya yang relevan untuk design (status menunggu dan proses)
        design_data = [
            adjustment.to_dict() for adjustment in adjustments 
            if adjustment.status in ['menunggu_adjustment_design', 'proses_adjustment_design']
        ]
        
        # Semua data untuk summary calculation
        all_data = [adjustment.to_dict() for adjustment in adjustments]
        
        return jsonify({
            'success': True,
            'data': design_data,
            'all_data': all_data,  # Untuk summary calculation
            'total': len(design_data)
        })
    except Exception as e:
        print(f"Error fetching design adjustment data: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/start-adjustment-design', methods=['POST'])
def start_adjustment_design():
    try:
        data = request.get_json()
        adjustment_id = data.get('id')
        design_by = data.get('design_by')

        if not adjustment_id or not design_by:
            return jsonify({'success': False, 'error': 'Missing required data'}), 400
        
        adjustment = db.session.get(PlateAdjustmentRequest, adjustment_id) # Menggunakan db.session.get
        if adjustment is None:
            abort(404, description="Plate Adjustment Request not found")
        
        # Check if this is a reprocess
        is_reprocess = data.get('is_reprocess', False)
        
        # Update status
        adjustment.status = 'proses_adjustment_design'
        adjustment.design_by = design_by
        
        #Jika bukan proses ulang (first time), set design_start_at
        if not is_reprocess:
            adjustment.design_start_at = datetime.now()
        # Jika ini adalah proses ulang, reset field terkait penolakan
        if is_reprocess:
            adjustment.design_finish_at = None
            adjustment.declined_at = None
            adjustment.declined_by = None
            adjustment.decline_reason = None
        
        db.session.commit()
        
        return jsonify({'success': True, 'message': 'Adjustment Design started successfully'})
    except Exception as e:
        print(f"Error starting Design adjustment: {e}")
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/finish-adjustment-design', methods=['POST'])
def finish_adjustment_design():
    try:
        data = request.get_json()
        adjustment_id = data.get('id')
        
        if not adjustment_id:
            return jsonify({'success': False, 'error': 'Missing adjustment ID'}), 400
        
        adjustment = db.session.get(PlateAdjustmentRequest, adjustment_id) # Menggunakan db.session.get
        if adjustment is None:
            abort(404, description="Plate Adjustment Request not found")
        
        # Update status dan waktu selesai adjustment
        adjustment.status = 'menunggu_adjustment'
        adjustment.design_finish_at = datetime.now()
        
        db.session.commit()
        
        return jsonify({'success': True, 'message': 'Adjustment Design finished successfully'})
    except Exception as e:
        print(f"Error finishing adjustment: {e}")
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/export-design-adjustment', methods=['GET'])
def export_design_adjustment():
    try:
        from flask import make_response, request, jsonify
        import io
        import openpyxl
        from datetime import datetime
        
        # Get filter parameters
        status_filter = request.args.get('status', '')
        remarks_filter = request.args.get('remarks', '')
        date_from = request.args.get('date_from', '')
        date_to = request.args.get('date_to', '')
        
        # Build query
        query = PlateAdjustmentRequest.query
        
        # Apply filters
        if status_filter:
            if status_filter == 'selesai':
                query = query.filter(PlateAdjustmentRequest.status.in_(['selesai', 'menunggu_adjustment_design']))
            else:
                query = query.filter(PlateAdjustmentRequest.status == status_filter)
        
        if remarks_filter:
            query = query.filter(PlateAdjustmentRequest.remarks.ilike(f'%{remarks_filter}%'))
        
        if date_from:
            query = query.filter(PlateAdjustmentRequest.tanggal >= date_from)
        if date_to:
            query = query.filter(PlateAdjustmentRequest.tanggal <= date_to)
        
        # Get data sorted by date (newest first)
        adjustments = query.order_by(PlateAdjustmentRequest.tanggal.desc(), PlateAdjustmentRequest.id.desc()).all()
        
        # Create an in-memory Excel workbook and worksheet
        workbook = openpyxl.Workbook()
        worksheet = workbook.active
        worksheet.title = "Design Adjustment Data"
        
        # Write headers
        headers = [
            'ID', 'Tanggal', 'Mesin Cetak', 'PIC', 'Remarks', 'WO Number', 'MC Number', 
            'Run Length', 'Item Name', 'Jumlah Plate', 'Note', 'Machine Off At',
            'PDND Start At', 'PDND Finish At', 'PDND By',
            'Design Start At', 'Design Finish At', 'Design By',
            'Adjustment Start At', 'Adjustment Finish At', 'Adjustment By', 
            'Plate Start At', 'Plate Finish At', 'Plate Delivered At', 'CTP By', 'Status'
        ]
        worksheet.append(headers)
        
        # Write data rows
        for adj in adjustments:
            row_data = [
                str(adj.id or ''),
                adj.tanggal.strftime('%Y-%m-%d') if adj.tanggal else '',
                str(adj.mesin_cetak or ''),
                str(adj.pic or ''),
                str(adj.remarks or ''),
                str(adj.wo_number or ''),
                str(adj.mc_number or ''),
                str(adj.run_length or ''),
                str(adj.item_name or ''),
                str(adj.jumlah_plate or ''),
                str(adj.note or ''),
                adj.machine_off_at.strftime('%Y-%m-%d %H:%M:%S') if adj.machine_off_at else '',
                adj.pdnd_start_at.strftime('%Y-%m-%d %H:%M:%S') if adj.pdnd_start_at else '',
                adj.pdnd_finish_at.strftime('%Y-%m-%d %H:%M:%S') if adj.pdnd_finish_at else '',
                str(adj.pdnd_by or ''),
                adj.design_start_at.strftime('%Y-%m-%d %H:%M:%S') if adj.design_start_at else '',
                adj.design_finish_at.strftime('%Y-%m-%d %H:%M:%S') if adj.design_finish_at else '',
                str(adj.design_by or ''),
                adj.adjustment_start_at.strftime('%Y-%m-%d %H:%M:%S') if adj.adjustment_start_at else '',
                adj.adjustment_finish_at.strftime('%Y-%m-%d %H:%M:%S') if adj.adjustment_finish_at else '',
                str(adj.adjustment_by or ''),
                adj.plate_start_at.strftime('%Y-%m-%d %H:%M:%S') if adj.plate_start_at else '',
                adj.plate_finish_at.strftime('%Y-%m-%d %H:%M:%S') if adj.plate_finish_at else '',
                adj.plate_delivered_at.strftime('%Y-%m-%d %H:%M:%S') if adj.plate_delivered_at else '',
                str(adj.ctp_by or ''),
                str(adj.status or '')
            ]
            worksheet.append(row_data)
        
        # Create response with proper Excel headers
        output = io.BytesIO()
        workbook.save(output)
        output.seek(0)
        
        response = make_response(output.getvalue())
        response.headers['Content-Type'] = 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        response.headers['Content-Disposition'] = f'attachment; filename=design_adjustment_export_{datetime.now().strftime("%Y%m%d_%H%M%S")}.xlsx'
        
        return response
        
    except Exception as e:
        print(f"Error exporting data: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)}), 500

# --- CTP Production Routes ---
@app.route('/decline-ctp', methods=['POST'])
@login_required
@require_ctp_access
def decline_ctp():
    try:
        data = request.get_json()
        adjustment_id = data.get('id')
        reason = data.get('reason')
        declined_by = data.get('declined_by')
        
        adjustment = PlateAdjustmentRequest.query.get(adjustment_id)
        if not adjustment:
            return jsonify({'success': False, 'message': 'Adjustment tidak ditemukan'}), 404
            
        adjustment.declined_at = datetime.now()
        adjustment.declined_by = declined_by
        adjustment.decline_reason = reason
        adjustment.is_declined = True
        adjustment.status = 'ditolakctp'
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Adjustment berhasil ditolak'
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)}), 500
    
@app.route('/decline-ctp-bon', methods=['POST'])
@login_required
@require_ctp_access
def decline_ctp_bon():
    try:
        data = request.get_json()
        bon_id = data.get('id')
        reason = data.get('reason')
        declined_by = data.get('declined_by')
        
        bon = PlateBonRequest.query.get(bon_id)
        if not bon:
            return jsonify({'success': False, 'message': 'Bon tidak ditemukan'}), 404

        bon.declined_at = datetime.now()
        bon.declined_by = declined_by
        bon.decline_reason = reason
        bon.is_declined = True
        bon.status = 'ditolakctp'
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Bon berhasil ditolak'
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/stock-opname-ctp')
@login_required
@require_ctp_access
def stock_opname_page():
    return render_template('stock_opname_ctp.html')

@app.route('/chemical-bon-ctp')
@login_required
@require_ctp_access
def chemical_bon_page():
    return render_template('chemical_bon_ctp.html')

@app.route('/get-plate-types')
@login_required
@require_ctp_access
def get_plate_types():
    try:
        # Query distinct plate types from CTP production logs
        plate_types = db.session.query(CTPProductionLog.plate_type_material)\
            .distinct()\
            .filter(CTPProductionLog.plate_type_material.isnot(None))\
            .order_by(CTPProductionLog.plate_type_material)\
            .all()
        
        # Extract values from tuples and filter out None/empty values
        plate_types = [pt[0] for pt in plate_types if pt[0]]
        
        return jsonify({
            'success': True,
            'plate_types': plate_types
        })
    except Exception as e:
        print(f"Error getting plate types: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/get-stock-opname-data')
@login_required
@require_ctp_access
def get_stock_opname_data():
    try:
        plate_type = request.args.get('plate_type', '')
        year = request.args.get('year', '')
        month = request.args.get('month', '')
        search = request.args.get('search', '')
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 30, type=int)

        # Build base query
        query = db.session.query(CTPProductionLog)

        # Apply filters
        if plate_type:
            query = query.filter(CTPProductionLog.plate_type_material == plate_type)
        
        if year:
            query = query.filter(extract('year', CTPProductionLog.log_date) == int(year))
        
        if month:
            query = query.filter(extract('month', CTPProductionLog.log_date) == int(month))
        
        if search:
            search_term = f"%{search}%"
            query = query.filter(
                db.or_(
                    CTPProductionLog.wo_number.ilike(search_term),
                    CTPProductionLog.ctp_machine.ilike(search_term),
                    CTPProductionLog.print_machine.ilike(search_term),
                    CTPProductionLog.item_name.ilike(search_term)
                )
            )

        # Always order by date desc and id desc for consistent ordering
        query = query.order_by(CTPProductionLog.log_date.desc(), CTPProductionLog.id.desc())

        # Apply pagination
        pagination = query.paginate(page=page, per_page=per_page, error_out=False)
        
        # Convert records to list of dicts
        data = []
        for record in pagination.items:
            data.append({
                'log_date': record.log_date.strftime('%Y-%m-%d'),
                'wo_number': record.wo_number,
                'ctp_machine': record.ctp_machine,
                'print_machine': record.print_machine,
                'item_name': record.item_name,
                'num_plate_good': record.num_plate_good,
                'num_plate_not_good': record.num_plate_not_good,
                'not_good_reason': record.not_good_reason,
                'note': record.note
            })

        return jsonify({
            'success': True,
            'data': data,
            'pagination': {
                'page': page,
                'per_page': per_page,
                'total': pagination.total,
                'pages': pagination.pages
            }
        })

    except Exception as e:
        print(f"Error getting stock opname data: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

from flask import send_file

from flask import request, send_file, jsonify
from openpyxl import Workbook
from openpyxl.styles import Alignment, Font, Border, Side
from openpyxl.utils import get_column_letter
import io
from datetime import datetime
import traceback

# Asumsi Anda sudah mengimpor db, login_required, require_ctp_access, dan CTPProductionLog
# from your_app import db, login_required, require_ctp_access
# from .models import CTPProductionLog 

from flask import request, send_file, jsonify
from openpyxl import Workbook
from openpyxl.styles import Alignment, Font, Border, Side
from openpyxl.utils import get_column_letter
import io
from datetime import datetime
import traceback

# Asumsi Anda sudah mengimpor db, login_required, require_ctp_access, dan CTPProductionLog
# from your_app import db, login_required, require_ctp_access
# from .models import CTPProductionLog 

from flask import request, send_file, jsonify
from openpyxl import Workbook
from openpyxl.styles import Alignment, Font, Border, Side
from openpyxl.utils import get_column_letter
import io
from datetime import datetime
import locale
import traceback

@app.route('/export-stock-opname')
@login_required
@require_ctp_access
def export_stock_opname():
    try:
        # Set locale to Indonesian for date formatting
        try:
            locale.setlocale(locale.LC_TIME, 'id_ID.UTF-8')
        except locale.Error:
            try:
                locale.setlocale(locale.LC_TIME, 'id_ID')
            except locale.Error:
                # Fallback if specific locale not found, often on Windows systems
                locale.setlocale(locale.LC_TIME, 'Indonesian_Indonesia.1252') # Common for Windows
                
        # Get filter parameters
        date_from_str = request.args.get('date_from', '')
        date_to_str = request.args.get('date_to', '')
        jenis_plate = request.args.get('jenis_plate', '')

        # Parse dates and format them for display in headers
        date_from_formatted = ""
        date_to_formatted = ""
        if date_from_str:
            date_from_obj = datetime.strptime(date_from_str, '%Y-%m-%d')
            date_from_formatted = date_from_obj.strftime('%d %B %Y')
        if date_to_str:
            date_to_obj = datetime.strptime(date_to_str, '%Y-%m-%d')
            date_to_formatted = date_to_obj.strftime('%d %B %Y')

        # Mapping data untuk setiap jenis plate (Didefinisikan di dalam route)
        plate_details = {
            'SAPHIRA 1030': {
                'size': '1030 X 790 MM',
                'item_code': '02-049-000-0000002',
                'item_name': '(SUT1.PAO1SX1) SAPHIRA PA.27 27x1030x790 PKT50 (BOX 50PCS)'
            },
            'SAPHIRA 1055': {
                'size': '1055 X 811 MM',
                'item_code': '02-049-000-0000003',
                'item_name': '(SUT1.PAO1SY3) SAPHIRA PA.27 27X1055X811 PKT50 (BOX 50PCS)'
            },
            'SAPHIRA 1055 PN': {
                'size': '1055 X 811 MM',
                'item_code': '02-049-000-0000011',
                'item_name': '(SUT1.PNO7U8C) SAPHIRA PN 30 1055 X 811 MM PKT40 (BOX 40PCS)'
            },
            'SAPHIRA 1630': {
                'size': '1630 X 1325 MM',
                'item_code': '02-049-000-0000001',
                'item_name': '(SUT1.PNOQXG8) SAPHIRA PN 40 1630 1325 PKT 30 (BOX 30PCS)'
            },
            'FUJI 1030': {
                'size': '1030 X 790 MM',
                'item_code': '02-049-000-0000008',
                'item_name': 'PLATE FUJI LH-PK 1030x790x0.3 (BOX 30PCS)'
            },
            'FUJI 1030 UV': {
                'size': '1030 X 790 MM',
                'item_code': '02-023-000-0000007',
                'item_name': 'PLATE FUJI LH-PJ2 1030x790x0.3 (BOX 30PCS)'
            },
            'FUJI 1055': {
                'size': '1055 X 811 MM',
                'item_code': '02-049-000-0000010',
                'item_name': 'PLATE FUJI LH-PK 1055x811x0.3 (BOX 30PCS)'
            },
            'FUJI 1055 LHPL': {
                'size': '1055 X 811 MM',
                'item_code': '02-049-000-0000013',
                'item_name': 'PLATE FUJI LH-PL 1055x811x0.3 (BOX 30PCS)'
            },
            'FUJI 1055 UV': {
                'size': '1055 X 811 MM',
                'item_code': '02-049-000-0000012',
                'item_name': 'PLATE FUJI LH-PJ2 1055x811x0.3 (BOX 30PCS)'
            },
            'FUJI 1630': {
                'size': '1630 X 1325 MM',
                'item_code': '02-049-000-0000009',
                'item_name': 'PLATE FUJI LH-PJ2 1630x1325x0.4 (BOX 15PCS)'
            }
        }

        # Define styles (Didefinisikan di dalam route)
        title_font = Font(bold=True, size=24)
        subtitle_font = Font(bold=True, size=18)
        info_font = Font(bold=True, size=11)
        header_font = Font(bold=True)
        center_alignment = Alignment(horizontal='center', vertical='center')
        left_alignment = Alignment(horizontal='left', vertical='center')
        border = Border(
            left=Side(style='thin'),
            right=Side(style='thin'),
            top=Side(style='thin'),
            bottom=Side(style='thin')
        )
        header_fill = PatternFill(start_color='E0E0E0', end_color='E0E0E0', fill_type='solid')
        total_row_fill_green = PatternFill(start_color='99FF99', end_color='99FF99', fill_type='solid')
        total_row_fill_grey = PatternFill(start_color='808080', end_color='808080', fill_type='solid')

        wb = Workbook()

        # Helper function untuk menambahkan baris "Total Pemakaian" (Didefinisikan di dalam route)
        def insert_total_pemakaian_row_local(ws, row_num, total_qty_ok, total_qty_ng):
            # Merge A-E for "Total Pemakaian"
            ws.merge_cells(start_row=row_num, end_row=row_num, start_column=1, end_column=5)
            total_text_cell = ws.cell(row=row_num, column=1, value="Total Pemakaian")
            total_text_cell.font = Font(bold=True)
            total_text_cell.alignment = center_alignment 
            total_text_cell.border = border
            total_text_cell.fill = total_row_fill_green

            # Merge F-H for total quantity
            ws.merge_cells(start_row=row_num, end_row=row_num, start_column=6, end_column=8)
            qty_total_cell = ws.cell(row=row_num, column=6, value=total_qty_ok + total_qty_ng)
            qty_total_cell.font = Font(bold=True)
            qty_total_cell.alignment = center_alignment 
            qty_total_cell.border = border
            qty_total_cell.fill = total_row_fill_green

            # Merge I-J for border fill (grey)
            ws.merge_cells(start_row=row_num, end_row=row_num, start_column=9, end_column=10)
            fill_cell_i = ws.cell(row=row_num, column=9) 
            fill_cell_i.border = border
            fill_cell_i.fill = total_row_fill_grey
            
            # Ensure the last column of the merged range also has a border, though fill is applied to the first cell
            fill_cell_j = ws.cell(row=row_num, column=10)
            fill_cell_j.border = border

        # Helper function untuk menulis data ke sheet (Didefinisikan di dalam route)
        def write_sheet_data_local(ws, records, plate_type_current, date_from_formatted, date_to_formatted):
            # Add header information
            ws.cell(row=1, column=1, value="Laporan Stock Opname").font = title_font
            ws.merge_cells('A1:J1')
            ws.cell(row=1, column=1).alignment = center_alignment

            ws.cell(row=2, column=1, value=plate_type_current).font = subtitle_font
            ws.merge_cells('A2:J2')
            ws.cell(row=2, column=1).alignment = center_alignment

            date_range_text = f"{date_from_formatted} - {date_to_formatted}"
            ws.cell(row=3, column=1, value=date_range_text).font = subtitle_font
            ws.merge_cells('A3:J3')
            ws.cell(row=3, column=1).alignment = center_alignment

            details = plate_details.get(plate_type_current, {})
            ws.cell(row=4, column=1, value="Size").font = info_font
            ws.cell(row=4, column=2, value=f": {details.get('size', '')}").font = info_font
            ws.cell(row=5, column=1, value="Item Code").font = info_font
            ws.cell(row=5, column=2, value=f": {details.get('item_code', '')}").font = info_font
            ws.cell(row=6, column=1, value="Item Name").font = info_font
            ws.cell(row=6, column=2, value=f": {details.get('item_name', '')}").font = info_font

            # Write headers on row 8
            headers = [
                'Tanggal', 'No WO', 'Mesin CTP', 'Mesin Cetak', 'Nama Item',
                'Qty OK', 'Qty NG', 'Total', 'Keterangan Not Good', 'Catatan'
            ]
            for col, header in enumerate(headers, 1):
                cell = ws.cell(row=8, column=col)
                cell.value = header
                cell.font = header_font
                cell.alignment = center_alignment
                cell.border = border
                cell.fill = header_fill

            current_row = 9
            
            if not records:
                ws.cell(row=current_row, column=1, value="Tidak ada data untuk periode ini.").merge_cells(f"A{current_row}:J{current_row}")
                ws.cell(row=current_row, column=1).alignment = center_alignment
                # Apply border to the merged cell
                for col_idx in range(1, 11):
                    cell = ws.cell(row=current_row, column=col_idx)
                    cell.border = border
                return # Exit if no records

            current_date = None
            date_group_start_row = 0
            date_group_total_qty_ok = 0
            date_group_total_qty_ng = 0

            for record_idx, record in enumerate(records):
                record_formatted_date = record.log_date.strftime('%d %B %Y')

                # Check if it's a new date group
                if record_formatted_date != current_date:
                    # If not the first group, finalize the previous group (merge date & add total row)
                    if current_date is not None:
                        # Merge date column for the previous group
                        ws.merge_cells(start_row=date_group_start_row, end_row=current_row - 1, start_column=1, end_column=1)
                        ws.cell(row=date_group_start_row, column=1).alignment = center_alignment
                        
                        # Add "Total Pemakaian" row for the previous group
                        insert_total_pemakaian_row_local(
                            ws, current_row, date_group_total_qty_ok, date_group_total_qty_ng
                        )
                        current_row += 1 # Increment for the total row

                    # Start a new date group
                    current_date = record_formatted_date
                    date_group_start_row = current_row
                    date_group_total_qty_ok = 0
                    date_group_total_qty_ng = 0
                
                # Process current record
                wo_numbers = record.wo_number.split(',') if record.wo_number else ['']
                wo_numbers = [wo.strip() for wo in wo_numbers]
                
                qty_ok_record = record.num_plate_good or 0
                qty_ng_record = record.num_plate_not_good or 0
                total_record_qty = qty_ok_record + qty_ng_record

                # Accumulate totals for the current date group
                date_group_total_qty_ok += qty_ok_record
                date_group_total_qty_ng += qty_ng_record

                # Define columns that should be merged if num_rows > 1 (excluding Tanggal (1) and No WO (2))
                record_specific_merge_cols = [3, 4, 5, 6, 7, 8, 9, 10]

                if len(wo_numbers) > 1:
                    # Perform merge for these columns for this record's multiple WO lines
                    for col_idx in record_specific_merge_cols:
                        ws.merge_cells(
                            start_row=current_row,
                            start_column=col_idx,
                            end_row=current_row + len(wo_numbers) - 1,
                            end_column=col_idx
                        )
                
                # Write data for the first line of this record (including the first WO)
                initial_row_values = [
                    record_formatted_date, # This value is explicitly set below if it's the start of a date group
                    wo_numbers[0],
                    record.ctp_machine,
                    record.print_machine,
                    record.item_name,
                    qty_ok_record,
                    qty_ng_record,
                    total_record_qty,
                    record.not_good_reason or '',
                    record.note or ''
                ]

                for col_idx, value in enumerate(initial_row_values, 1):
                    cell = ws.cell(row=current_row, column=col_idx)
                    # For Tanggal (Column 1): only set value if it's the start of a date group.
                    # Otherwise, it's part of a merged cell, just apply styling.
                    if col_idx == 1:
                        if current_row == date_group_start_row:
                            cell.value = value
                        # Else: no value for merged cells (it inherits from the top-left merged cell)
                    # For other columns (No WO, Mesin CTP, etc.): set value for the first line of the record.
                    # If len(wo_numbers) > 1, these columns will be merged, so value only goes in the first row.
                    else: 
                        cell.value = value
                    
                    cell.alignment = center_alignment 
                    cell.border = border


                # Handle additional WO numbers for the same record (if wo_number is split)
                for i, wo in enumerate(wo_numbers[1:], 1):
                    current_row += 1
                    
                    # Column 1 (Tanggal): This cell is part of a date merged range. Only apply styling.
                    cell = ws.cell(row=current_row, column=1)
                    cell.alignment = center_alignment
                    cell.border = border

                    # Column 2 (No WO): Gets its specific WO number.
                    wo_cell = ws.cell(row=current_row, column=2)
                    wo_cell.value = wo
                    wo_cell.alignment = center_alignment
                    wo_cell.border = border
                    
                    # For other columns (3-10): these are merged for this record. Only apply styling.
                    for col_idx in record_specific_merge_cols:
                        cell = ws.cell(row=current_row, column=col_idx)
                        cell.alignment = center_alignment
                        cell.border = border
                    
                current_row += 1 # Move to the next row after all WO numbers for this record

            # After the loop, finalize the very last date group
            if current_date is not None:
                ws.merge_cells(start_row=date_group_start_row, end_row=current_row - 1, start_column=1, end_column=1)
                ws.cell(row=date_group_start_row, column=1).alignment = center_alignment
                
                insert_total_pemakaian_row_local(
                    ws, current_row, date_group_total_qty_ok, date_group_total_qty_ng
                )
                current_row += 1 # Increment for the total row

            # Set column widths
            for col in range(1, len(headers) + 1):
                ws.column_dimensions[get_column_letter(col)].width = 15


        if not jenis_plate:
            # Skenario: Semua Jenis Plate (banyak sheet)
            unique_plates = db.session.query(CTPProductionLog.plate_type_material).distinct().all()
            unique_plates = [p[0] for p in unique_plates if p[0] and p[0] in plate_details]
            
            # Mengurutkan jenis plate berdasarkan abjad
            unique_plates.sort()

            default_ws = wb.active
            wb.remove(default_ws)

            for plate_type in unique_plates:
                ws = wb.create_sheet(title=plate_type[:31]) # Max 31 chars for sheet title

                query = db.session.query(CTPProductionLog).filter(CTPProductionLog.plate_type_material == plate_type)
                if date_from_str:
                    query = query.filter(CTPProductionLog.log_date >= date_from_str)
                if date_to_str:
                    date_to_obj_end = datetime.strptime(date_to_str, '%Y-%m-%d').replace(hour=23, minute=59, second=59)
                    query = query.filter(CTPProductionLog.log_date <= date_to_obj_end)
                
                records = query.order_by(CTPProductionLog.log_date.desc(), CTPProductionLog.id.desc()).all()
                
                write_sheet_data_local(ws, records, plate_type, date_from_formatted, date_to_formatted)

        else:
            # Skenario: Satu Jenis Plate (satu sheet)
            ws = wb.active
            ws.title = jenis_plate[:31]

            query = db.session.query(CTPProductionLog).filter(CTPProductionLog.plate_type_material == jenis_plate)
            if date_from_str:
                query = query.filter(CTPProductionLog.log_date >= date_from_str)
            if date_to_str:
                date_to_obj_end = datetime.strptime(date_to_str, '%Y-%m-%d').replace(hour=23, minute=59, second=59)
                query = query.filter(CTPProductionLog.log_date <= date_to_obj_end)
            
            records = query.order_by(CTPProductionLog.log_date.desc(), CTPProductionLog.id.desc()).all()

            write_sheet_data_local(ws, records, jenis_plate, date_from_formatted, date_to_formatted)


        # Save to BytesIO
        excel_file = io.BytesIO()
        wb.save(excel_file)
        excel_file.seek(0)
        
        # Nama file
        jenis_plate_str = f"_{jenis_plate.replace(' ', '_')}" if jenis_plate else "_all"

        return send_file(
            excel_file,
            mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            as_attachment=True,
            download_name=f'stock_opname_ctp{jenis_plate_str}_export_{datetime.now().strftime("%Y%m%d_%H%M%S")}.xlsx'
        )

    except Exception as e:
        print(f"Error exporting stock opname data: {e}")
        traceback.print_exc() 
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/ctp-data-adjustment')
@login_required
@require_ctp_access
def ctp_data_adjustment_page():
    return render_template('ctp_data_adjustment.html')

@app.route('/ctp-data-bon')
@login_required
@require_ctp_access
def ctp_data_bon_page():
    return render_template('ctp_data_bon.html')

@app.route('/get-ctp-adjustment-data', methods=['GET'])
@login_required
@require_ctp_access
def get_ctp_adjustment_data():
    try:
        # Get all adjustments for CTP (no status filter for debugging)
        all_adjustments = PlateAdjustmentRequest.query.order_by(PlateAdjustmentRequest.id.desc()).all()
        
        # Filter untuk active CTP processes
        active_adjustments = PlateAdjustmentRequest.query.filter(
            PlateAdjustmentRequest.status.in_(['proses_ctp', 'proses_plate'])
        ).order_by(PlateAdjustmentRequest.id.desc()).all()
        
        all_data = [adjustment.to_dict() for adjustment in all_adjustments]
        active_data = [adjustment.to_dict() for adjustment in active_adjustments]
        
        return jsonify({
            'success': True,
            'data': active_data,
            'all_data': all_data,
            'total': len(active_data),
            'total_all': len(all_data)
        })
    except Exception as e:
        print(f"Error fetching CTP adjustment data: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/get-ctp-bon-data', methods=['GET'])
def get_ctp_bon_data():
    try:
        # Get all bon for CTP (no status filter for debugging)
        all_bon = PlateBonRequest.query.order_by(PlateBonRequest.id.desc()).all()

        # Filter untuk active CTP processes
        active_bon = PlateBonRequest.query.filter(
            PlateBonRequest.status.in_(['proses_ctp', 'proses_plate', 'antar_plate'])
        ).order_by(PlateBonRequest.id.desc()).all()

        all_data = [bon.to_dict() for bon in all_bon]
        active_data = [bon.to_dict() for bon in active_bon]

        return jsonify({
            'success': True,
            'data': active_data,
            'all_data': all_data,
            'total': len(active_data),
            'total_all': len(all_data)
        })
    except Exception as e:
        print(f"Error fetching CTP bon data: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/dashboard-ctp')
@login_required
@require_ctp_access
def dashboard_ctp():
    return render_template('dashboard_ctp.html')

@app.route('/get-ctp-kpi-data')
@login_required
@require_ctp_access
def get_ctp_kpi_data():
    try:
        # Ambil parameter year dan month
        # Jika year="" atau month="" dari frontend, biarkan sebagai string kosong
        year_param = request.args.get('year', '')
        month_param = request.args.get('month', '')
        
        # Konversi ke integer jika tidak kosong, jika kosong biarkan None
        year = int(year_param) if year_param else None
        month = int(month_param) if month_param else None
        
        # Logika untuk MonthlyWorkHours
        # Ambil data total waktu dari tabel monthly_work_hours
        # Sesuaikan query agar hanya memfilter berdasarkan tahun jika tahun diberikan, dan bulan jika bulan diberikan
        work_hours_query = MonthlyWorkHours.query
        if year:
            work_hours_query = work_hours_query.filter(MonthlyWorkHours.year == year)
        if month:
            work_hours_query = work_hours_query.filter(MonthlyWorkHours.month == month)
        work_hours = work_hours_query.first()

        total_work_hours_proof = work_hours.total_work_hours_proof if work_hours else 0
        total_work_hours_produksi = work_hours.total_work_hours_produksi if work_hours else 0

        # Base query untuk plate_adjustment_requests (untuk proof)
        proof_query = PlateAdjustmentRequest.query.filter(
            PlateAdjustmentRequest.remarks.ilike('%PROOF%'),
            ~PlateAdjustmentRequest.remarks.ilike('%MESIN TIDAK OFF%'),
            PlateAdjustmentRequest.machine_off_at.isnot(None),
            PlateAdjustmentRequest.plate_delivered_at.isnot(None)
        )

        # Base query untuk plate_bon_requests (untuk produksi)
        produksi_query = PlateBonRequest.query.filter(
            PlateBonRequest.remarks.ilike('%PRODUKSI%'),
            ~PlateBonRequest.remarks.ilike('%MESIN TIDAK OFF%'),
            PlateBonRequest.machine_off_at.isnot(None),
            PlateBonRequest.plate_delivered_at.isnot(None)
        )

        # Tambahkan filter tahun dan bulan ke query downtime secara kondisional
        if year:
            proof_query = proof_query.filter(extract('year', PlateAdjustmentRequest.tanggal) == year)
            produksi_query = produksi_query.filter(extract('year', PlateBonRequest.tanggal) == year)
        if month:
            proof_query = proof_query.filter(extract('month', PlateAdjustmentRequest.tanggal) == month)
            produksi_query = produksi_query.filter(extract('month', PlateBonRequest.tanggal) == month)


        # Base query for totals from CTPProductionLog
        query_ctp_log = db.session.query(
            CTPProductionLog.ctp_group,
            func.sum(CTPProductionLog.num_plate_good).label('total_good'),
            func.sum(CTPProductionLog.num_plate_not_good).label('total_not_good')
        ).group_by(CTPProductionLog.ctp_group)
        
        # Apply filters untuk data plate secara kondisional
        if year:
            query_ctp_log = query_ctp_log.filter(extract('year', CTPProductionLog.log_date) == year)
        if month:
            query_ctp_log = query_ctp_log.filter(extract('month', CTPProductionLog.log_date) == month)
            
        results = query_ctp_log.all()
        
        kpi_data = []
        for group, good, not_good in results:
            total_output = (good or 0) + (not_good or 0)
            
            # Get reasons for this group
            reasons_query = CTPProductionLog.query.with_entities(
                CTPProductionLog.not_good_reason,
                CTPProductionLog.num_plate_not_good
            ).filter(
                CTPProductionLog.ctp_group == group,
                CTPProductionLog.not_good_reason.isnot(None),
                CTPProductionLog.num_plate_not_good > 0
            )
            
            # Apply same year/month filter secara kondisional
            if year:
                reasons_query = reasons_query.filter(extract('year', CTPProductionLog.log_date) == year)
            if month:
                reasons_query = reasons_query.filter(extract('month', CTPProductionLog.log_date) == month)
            
            # Initialize reason counters
            reason_counts = {
                'reason_rontok': 0, 'reason_baret': 0, 'reason_penyok': 0,
                'reason_kotor': 0, 'reason_bergaris': 0, 'reason_tidak_sesuai_dp': 0,
                'reason_nilai_tidak_sesuai': 0, 'reason_laser_jump': 0, 'reason_tidak_masuk_millar': 0,
                'reason_error_punch': 0, 'reason_plate_jump': 0
            }
            
            # Count reasons
            for reason_record in reasons_query.all():
                if reason_record.not_good_reason:
                    reason = reason_record.not_good_reason.lower()
                    count = reason_record.num_plate_not_good or 0
                    
                    if 'rontok' in reason or 'botak' in reason:
                        reason_counts['reason_rontok'] += count
                    if 'baret' in reason:
                        reason_counts['reason_baret'] += count
                    if 'penyok' in reason:
                        reason_counts['reason_penyok'] += count
                    if 'kotor' in reason:
                        reason_counts['reason_kotor'] += count
                    if 'bergaris' in reason:
                        reason_counts['reason_bergaris'] += count
                    if 'tidak sesuai dp' in reason:
                        reason_counts['reason_tidak_sesuai_dp'] += count
                    if 'nilai tidak sesuai' in reason:
                        reason_counts['reason_nilai_tidak_sesuai'] += count
                    if 'laser jump' in reason:
                        reason_counts['reason_laser_jump'] += count
                    if 'tidak masuk millar' in reason:
                        reason_counts['reason_tidak_masuk_millar'] += count
                    if 'error punch' in reason or 'error mesin punch' in reason:
                        reason_counts['reason_error_punch'] += count
                    if 'plate jump' in reason:
                        reason_counts['reason_plate_jump'] += count
            
            # Get downtime data for this specific group (proof)
            group_proof_items_query = PlateAdjustmentRequest.query.filter(
                PlateAdjustmentRequest.remarks.ilike('%PROOF%'),
                ~PlateAdjustmentRequest.remarks.ilike('%MESIN TIDAK OFF%'),
                PlateAdjustmentRequest.machine_off_at.isnot(None),
                PlateAdjustmentRequest.plate_delivered_at.isnot(None),
                PlateAdjustmentRequest.ctp_group == group
            )
            if year:
                group_proof_items_query = group_proof_items_query.filter(extract('year', PlateAdjustmentRequest.tanggal) == year)
            if month:
                group_proof_items_query = group_proof_items_query.filter(extract('month', PlateAdjustmentRequest.tanggal) == month)

            group_downtime_proof = sum(
                (item.plate_delivered_at - item.machine_off_at).total_seconds() / 3600
                for item in group_proof_items_query.all()
                if item.plate_delivered_at and item.machine_off_at
            )

            # Get downtime data for this specific group (produksi)
            group_produksi_items_query = PlateBonRequest.query.filter(
                PlateBonRequest.remarks.ilike('%PRODUKSI%'),
                ~PlateBonRequest.remarks.ilike('%MESIN TIDAK OFF%'),
                PlateBonRequest.machine_off_at.isnot(None),
                PlateBonRequest.plate_delivered_at.isnot(None),
                PlateBonRequest.ctp_group == group
            )
            if year:
                group_produksi_items_query = group_produksi_items_query.filter(extract('year', PlateBonRequest.tanggal) == year)
            if month:
                group_produksi_items_query = group_produksi_items_query.filter(extract('month', PlateBonRequest.tanggal) == month)

            group_downtime_produksi = sum(
                (item.plate_delivered_at - item.machine_off_at).total_seconds() / 3600
                for item in group_produksi_items_query.all()
                if item.plate_delivered_at and item.machine_off_at
            )

            group_proof_percentage = round((group_downtime_proof / total_work_hours_proof * 100), 2) if total_work_hours_proof > 0 else 0
            group_produksi_percentage = round((group_downtime_produksi / total_work_hours_produksi * 100), 2) if total_work_hours_produksi > 0 else 0

            group_data = {
                'group': group,
                'good_plate': good or 0,
                'not_good_plate': not_good or 0,
                'total_output': total_output,
                'output_percentage': round(((good or 0) / total_output * 100), 2) if total_output > 0 else 0,
                'not_good_percentage': round(((not_good or 0) / total_output * 100), 2) if total_output > 0 else 0,
                'proof_downtime_percentage': group_proof_percentage,
                'proof_downtime_hours': round(group_downtime_proof, 2),
                'produksi_downtime_percentage': group_produksi_percentage,
                'produksi_downtime_hours': round(group_downtime_produksi, 2),
                **reason_counts # Include all reason counts
            }
            kpi_data.append(group_data) # Append the group data to the list
            
        # Calculate overall totals
        total_good = sum(item['good_plate'] for item in kpi_data)
        total_not_good = sum(item['not_good_plate'] for item in kpi_data)
        total_output = total_good + total_not_good
        
        # Recalculate overall downtime with conditional filters
        overall_proof_items_query = PlateAdjustmentRequest.query.filter(
            PlateAdjustmentRequest.remarks.ilike('%PROOF%'),
            ~PlateAdjustmentRequest.remarks.ilike('%MESIN TIDAK OFF%'),
            PlateAdjustmentRequest.machine_off_at.isnot(None),
            PlateAdjustmentRequest.plate_delivered_at.isnot(None)
        )
        if year:
            overall_proof_items_query = overall_proof_items_query.filter(extract('year', PlateAdjustmentRequest.tanggal) == year)
        if month:
            overall_proof_items_query = overall_proof_items_query.filter(extract('month', PlateAdjustmentRequest.tanggal) == month)
        
        total_downtime_proof_overall = sum(
            (item.plate_delivered_at - item.machine_off_at).total_seconds() / 3600
            for item in overall_proof_items_query.all()
            if item.plate_delivered_at and item.machine_off_at
        )

        overall_produksi_items_query = PlateBonRequest.query.filter(
            PlateBonRequest.remarks.ilike('%PRODUKSI%'),
            ~PlateBonRequest.remarks.ilike('%MESIN TIDAK OFF%'),
            PlateBonRequest.machine_off_at.isnot(None),
            PlateBonRequest.plate_delivered_at.isnot(None)
        )
        if year:
            overall_produksi_items_query = overall_produksi_items_query.filter(extract('year', PlateBonRequest.tanggal) == year)
        if month:
            overall_produksi_items_query = overall_produksi_items_query.filter(extract('month', PlateBonRequest.tanggal) == month)

        total_downtime_produksi_overall = sum(
            (item.plate_delivered_at - item.machine_off_at).total_seconds() / 3600
            for item in overall_produksi_items_query.all()
            if item.plate_delivered_at and item.machine_off_at
        )

        # Recalculate overall work hours based on selected year/month
        overall_work_hours_query = MonthlyWorkHours.query
        if year:
            overall_work_hours_query = overall_work_hours_query.filter(MonthlyWorkHours.year == year)
        if month:
            overall_work_hours_query = overall_work_hours_query.filter(MonthlyWorkHours.month == month)
        overall_work_hours = overall_work_hours_query.first()

        overall_total_work_hours_proof = overall_work_hours.total_work_hours_proof if overall_work_hours else 0
        overall_total_work_hours_produksi = overall_work_hours.total_work_hours_produksi if overall_work_hours else 0


        overall_downtime_proof_percentage = round((total_downtime_proof_overall / overall_total_work_hours_proof * 100), 2) if overall_total_work_hours_proof > 0 else 0
        overall_downtime_produksi_percentage = round((total_downtime_produksi_overall / overall_total_work_hours_produksi * 100), 2) if overall_total_work_hours_produksi > 0 else 0


        overall_kpi = {
            'total_good': total_good,
            'total_not_good': total_not_good,
            'total_output': total_output,
            'overall_output_percentage': round((total_good / total_output * 100), 2) if total_output > 0 else 0,
            'overall_not_good_percentage': round((total_not_good / total_output * 100), 2) if total_output > 0 else 0,
            'overall_downtime_proof_percentage': overall_downtime_proof_percentage,
            'overall_downtime_produksi_percentage': overall_downtime_produksi_percentage,
            'overall_downtime_proof_hours': round(total_downtime_proof_overall, 2),
            'overall_downtime_produksi_hours': round(total_downtime_produksi_overall, 2)
        }
        
        
        return jsonify({
            'success': True,
            'data': kpi_data,
            'overall': overall_kpi
        })
        
    except Exception as e:
        print(f"Error getting CTP KPI data: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/start-ctp', methods=['POST'])
def start_ctp():
    try:
        data = request.get_json()
        adjustment_id = data.get('id')
        ctp_by = data.get('ctp_by')
        ctp_group = data.get('ctp_group')  # Get CTP group from request
        
        if not adjustment_id or not ctp_by or not ctp_group:
            return jsonify({'success': False, 'error': 'Missing required data (id, ctp_by, or ctp_group)'}), 400
        
        adjustment = db.session.get(PlateAdjustmentRequest, adjustment_id) # Menggunakan db.session.get
        if adjustment is None:
            abort(404, description="Plate Adjustment Request not found")
        
        # Validasi status - hanya boleh dimulai dari proses_ctp
        if adjustment.status != 'proses_ctp':
            return jsonify({'success': False, 'error': 'CTP can only be started from proses_ctp status'}), 400
        
        # Update status ke proses_plate, waktu mulai plate, PIC CTP, dan CTP group
        adjustment.status = 'proses_plate'
        adjustment.plate_start_at = datetime.now()
        adjustment.ctp_by = ctp_by
        adjustment.ctp_group = ctp_group   # Assign CTP group
        
        db.session.commit()
        
        return jsonify({
            'success': True, 
            'message': 'CTP process started successfully',
            'new_status': 'proses_plate'
        })
    except Exception as e:
        print(f"Error starting CTP: {e}")
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/start-ctp-bon', methods=['POST'])
def start_ctp_bon():
    try:
        data = request.get_json()
        bon_id = data.get('id')
        ctp_by = data.get('ctp_by')
        ctp_group = data.get('ctp_group')  # Get CTP group from request
        
        if not bon_id or not ctp_by or not ctp_group:
            return jsonify({'success': False, 'error': 'Missing required data (id, ctp_by, or ctp_group)'}), 400
        
        bon = db.session.get(PlateBonRequest, bon_id) # Menggunakan db.session.get
        if bon is None:
            abort(404, description="Plate Bon Request not found")
        
        # Validasi status - hanya boleh dimulai dari proses_ctp
        if bon.status != 'proses_ctp':
            return jsonify({'success': False, 'error': 'CTP can only be started from proses_ctp status'}), 400
        
        # Update status ke proses_plate, waktu mulai plate, PIC CTP, dan CTP group
        bon.status = 'proses_plate'
        bon.plate_start_at = datetime.now()
        bon.ctp_by = ctp_by
        bon.ctp_group = ctp_group   # Assign CTP group
        
        db.session.commit()
        
        return jsonify({
            'success': True, 
            'message': 'CTP process started successfully',
            'new_status': 'proses_plate'
        })
    except Exception as e:
        print(f"Error starting CTP: {e}")
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/finish-ctp', methods=['POST'])
def finish_ctp():
    try:
        data = request.get_json()
        adjustment_id = data.get('id')
        
        if not adjustment_id:
            return jsonify({'success': False, 'error': 'Missing adjustment ID'}), 400
        
        adjustment = db.session.get(PlateAdjustmentRequest, adjustment_id) # Menggunakan db.session.get
        if adjustment is None:
            abort(404, description="Plate Adjustment Request not found")
        
        # Validasi status - hanya boleh diselesaikan dari proses_plate
        if adjustment.status != 'proses_plate':
            return jsonify({'success': False, 'error': 'CTP can only be finished from proses_plate status'}), 400
        
        # Validasi bahwa CTP sudah dimulai (harus ada plate_start_at dan ctp_by)
        if not adjustment.plate_start_at or not adjustment.ctp_by:
            return jsonify({'success': False, 'error': 'CTP must be started first'}), 400
        
        # Update status dan waktu selesai plate
        adjustment.status = 'antar_plate'
        adjustment.plate_finish_at = datetime.now()
        
        db.session.commit()
        
        return jsonify({
            'success': True, 
            'message': f'CTP process finished successfully by {adjustment.ctp_by}. Ready for delivery.',
            'new_status': 'antar_plate',
            'finished_by': adjustment.ctp_by
        })
    except Exception as e:
        print(f"Error finishing CTP: {e}")
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500
    
@app.route('/finish-ctp-bon', methods=['POST'])
def finish_ctp_bon():
    try:
        data = request.get_json()
        bon_id = data.get('id')
        
        if not bon_id:
            return jsonify({'success': False, 'error': 'Missing bon ID'}), 400
        
        bon = db.session.get(PlateBonRequest, bon_id) # Menggunakan db.session.get
        if bon is None:
            abort(404, description="Plate Bon Request not found")
        
        # Validasi status - hanya boleh diselesaikan dari proses_plate
        if bon.status != 'proses_plate':
            return jsonify({'success': False, 'error': 'CTP can only be finished from proses_plate status'}), 400
        
        # Validasi bahwa CTP sudah dimulai (harus ada plate_start_at dan ctp_by)
        if not bon.plate_start_at or not bon.ctp_by:
            return jsonify({'success': False, 'error': 'CTP must be started first'}), 400
        
        # Update status dan waktu selesai plate
        bon.status = 'antar_plate'
        bon.plate_finish_at = datetime.now()
        # PIC tetap sama dengan yang memulai CTP (tidak perlu update ctp_by)
        
        db.session.commit()
        
        return jsonify({
            'success': True, 
            'message': f'CTP process finished successfully by {bon.ctp_by}. Ready for delivery.',
            'new_status': 'antar_plate',
            'finished_by': bon.ctp_by
        })
    except Exception as e:
        print(f"Error finishing CTP: {e}")
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/plate-delivered', methods=['POST'])
def plate_delivered():
    try:
        data = request.get_json()
        adjustment_id = data.get('id')
        
        if not adjustment_id:
            return jsonify({'success': False, 'error': 'Missing adjustment ID'}), 400
        
        adjustment = db.session.get(PlateAdjustmentRequest, adjustment_id) # Menggunakan db.session.get
        if adjustment is None:
            abort(404, description="Plate Adjustment Request not found")
        
        # Validasi status - hanya boleh delivered dari antar_plate
        if adjustment.status != 'antar_plate':
            return jsonify({'success': False, 'error': 'Plate can only be delivered from antar_plate status'}), 400
        
        # Validasi bahwa CTP sudah selesai (harus ada plate_finish_at)
        if not adjustment.plate_finish_at or not adjustment.ctp_by:
            return jsonify({'success': False, 'error': 'CTP must be finished first'}), 400
        
        # Update status dan waktu plate sampai
        adjustment.status = 'selesai'
        adjustment.plate_delivered_at = datetime.now()
        
        db.session.commit()
        
        return jsonify({
            'success': True, 
            'message': f'Plate delivered successfully to machine by {adjustment.ctp_by}',
            'new_status': 'selesai',
            'delivered_by': adjustment.ctp_by
        })
    except Exception as e:
        print(f"Error delivering plate: {e}")
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/plate-delivered-bon', methods=['POST'])
def plate_delivered_bon():
    try:
        data = request.get_json()
        bon_id = data.get('id')
        
        if not bon_id:
            return jsonify({'success': False, 'error': 'Missing bon ID'}), 400
        
        bon = db.session.get(PlateBonRequest, bon_id) # Menggunakan db.session.get
        if bon is None:
            abort(404, description="Plate Bon Request not found")
        
        # Validasi status - hanya boleh delivered dari antar_plate
        if bon.status != 'antar_plate':
            return jsonify({'success': False, 'error': 'Plate can only be delivered from antar_plate status'}), 400
        
        # Validasi bahwa CTP sudah selesai (harus ada plate_finish_at)
        if not bon.plate_finish_at or not bon.ctp_by:
            return jsonify({'success': False, 'error': 'CTP must be finished first'}), 400
        
        # Update status dan waktu plate sampai
        bon.status = 'selesai'
        bon.plate_delivered_at = datetime.now()
        
        db.session.commit()
        
        return jsonify({
            'success': True, 
            'message': f'Plate delivered successfully to machine by {bon.ctp_by}',
            'new_status': 'selesai',
            'delivered_by': bon.ctp_by
        })
    except Exception as e:
        print(f"Error delivering plate: {e}")
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/export-ctp-adjustment', methods=['GET'])
def export_ctp_adjustment():
    try:
        from flask import make_response, request, jsonify
        import io
        import openpyxl
        from datetime import datetime

        # Get filter parameters
        status_filter = request.args.get('status', '')
        mesin_filter = request.args.get('mesin', '')
        remarks_filter = request.args.get('remarks', '')
        search_filter = request.args.get('search', '')
        date_from = request.args.get('date_from', '')
        date_to = request.args.get('date_to', '')

        # Build query for CTP adjustments
        query = PlateAdjustmentRequest.query

        # Apply filters
        if status_filter:
            if status_filter == 'selesai':
                query = query.filter(PlateAdjustmentRequest.status.in_(['selesai', 'proses_ctp']))
            else:
                query = query.filter(PlateAdjustmentRequest.status == status_filter)

        if mesin_filter:
            query = query.filter(PlateAdjustmentRequest.mesin_cetak == mesin_filter)
            
        if remarks_filter:
            query = query.filter(PlateAdjustmentRequest.remarks.ilike(f'%{remarks_filter}%'))
            
        if search_filter:
            search_term = f'%{search_filter}%'
            query = query.filter(
                db.or_(
                    PlateAdjustmentRequest.wo_number.ilike(search_term),
                    PlateAdjustmentRequest.mc_number.ilike(search_term),
                    PlateAdjustmentRequest.item_name.ilike(search_term),
                    PlateAdjustmentRequest.mesin_cetak.ilike(search_term),
                    PlateAdjustmentRequest.remarks.ilike(search_term)
                )
            )
        
        if date_from:
            query = query.filter(PlateAdjustmentRequest.tanggal >= date_from)
        if date_to:
            query = query.filter(PlateAdjustmentRequest.tanggal <= date_to)
        
        # Get CTP data sorted by date (newest first)
        adjustments = query.order_by(PlateAdjustmentRequest.tanggal.desc(), PlateAdjustmentRequest.id.desc()).all()
        
        # Create an in-memory Excel workbook and worksheet
        workbook = openpyxl.Workbook()
        worksheet = workbook.active
        worksheet.title = "CTP Adjustment Data"

        # Write headers
        headers = [
            'ID', 'Tanggal', 'Mesin Cetak', 'PIC', 'Remarks', 'WO Number', 'MC Number', 
            'Run Length', 'Item Name', 'Jumlah Plate', 'Note', 'Machine Off At',
            'PDND Start At', 'PDND Finish At', 'PDND By',
            'Design Start At', 'Design Finish At', 'Design By',
            'Adjustment Start At', 'Adjustment Finish At', 'Adjustment By', 
            'Plate Start At', 'Plate Finish At', 'Plate Delivered At', 'CTP By', 'Status'
        ]
        worksheet.append(headers)

        # Write data rows
        for adj in adjustments:
            row_data = [
                str(adj.id or ''),
                adj.tanggal.strftime('%Y-%m-%d') if adj.tanggal else '',
                str(adj.mesin_cetak or ''),
                str(adj.pic or ''),
                str(adj.remarks or ''),
                str(adj.wo_number or ''),
                str(adj.mc_number or ''),
                str(adj.run_length or ''),
                str(adj.item_name or ''),
                str(adj.jumlah_plate or ''),
                str(adj.note or ''),
                adj.machine_off_at.strftime('%Y-%m-%d %H:%M:%S') if adj.machine_off_at else '',
                adj.pdnd_start_at.strftime('%Y-%m-%d %H:%M:%S') if adj.pdnd_start_at else '',
                adj.pdnd_finish_at.strftime('%Y-%m-%d %H:%M:%S') if adj.pdnd_finish_at else '',
                str(adj.pdnd_by or ''),
                adj.adjustment_start_at.strftime('%Y-%m-%d %H:%M:%S') if adj.adjustment_start_at else '',
                adj.adjustment_finish_at.strftime('%Y-%m-%d %H:%M:%S') if adj.adjustment_finish_at else '',
                str(adj.adjustment_by or ''),
                adj.plate_start_at.strftime('%Y-%m-%d %H:%M:%S') if adj.plate_start_at else '',
                adj.plate_finish_at.strftime('%Y-%m-%d %H:%M:%S') if adj.plate_finish_at else '',
                adj.plate_delivered_at.strftime('%Y-%m-%d %H:%M:%S') if adj.plate_delivered_at else '',
                str(adj.ctp_by or ''),
                str(adj.status or '')
            ]
            worksheet.append(row_data)
        
        # Create response with proper Excel headers
        output = io.BytesIO()
        workbook.save(output)
        output.seek(0)
        
        response = make_response(output.getvalue())
        response.headers['Content-Type'] = 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        response.headers['Content-Disposition'] = f'attachment; filename=ctp_adjustment_export_{datetime.now().strftime("%Y%m%d_%H%M%S")}.xlsx'
        
        return response
        
    except Exception as e:
        print(f"Error exporting CTP data: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/export-mounting-adjustment', methods=['GET'])
def export_mounting_adjustment():
    try:
        from flask import make_response, request, jsonify
        import io
        import openpyxl
        from datetime import datetime
        
        # Get filter parameters
        status_filter = request.args.get('status', '')
        remarks_filter = request.args.get('remarks', '')
        date_from = request.args.get('date_from', '')
        date_to = request.args.get('date_to', '')
        
        # Build query
        query = PlateAdjustmentRequest.query
        
        # Apply filters
        if status_filter:
            if status_filter == 'selesai':
                query = query.filter(PlateAdjustmentRequest.status.in_(['selesai', 'proses_ctp']))
            else:
                query = query.filter(PlateAdjustmentRequest.status == status_filter)
        
        if remarks_filter:
            query = query.filter(PlateAdjustmentRequest.remarks.ilike(f'%{remarks_filter}%'))
        
        if date_from:
            query = query.filter(PlateAdjustmentRequest.tanggal >= date_from)
        if date_to:
            query = query.filter(PlateAdjustmentRequest.tanggal <= date_to)
        
        # Get data sorted by date (newest first)
        adjustments = query.order_by(PlateAdjustmentRequest.tanggal.desc(), PlateAdjustmentRequest.id.desc()).all()
        
        # Create an in-memory Excel workbook and worksheet
        workbook = openpyxl.Workbook()
        worksheet = workbook.active
        worksheet.title = "Mounting Adjustment Data"
        
        # Write headers
        headers = [
            'ID', 'Tanggal', 'Mesin Cetak', 'PIC', 'Remarks', 'WO Number', 'MC Number', 
            'Run Length', 'Item Name', 'Jumlah Plate', 'Note', 'Machine Off At',
            'PDND Start At', 'PDND Finish At', 'PDND By',
            'Design Start At', 'Design Finish At', 'Design By',
            'Adjustment Start At', 'Adjustment Finish At', 'Adjustment By', 
            'Plate Start At', 'Plate Finish At', 'Plate Delivered At', 'CTP By', 'Status'
        ]
        worksheet.append(headers)
        
        # Write data rows
        for adj in adjustments:
            row_data = [
                str(adj.id or ''),
                adj.tanggal.strftime('%Y-%m-%d') if adj.tanggal else '',
                str(adj.mesin_cetak or ''),
                str(adj.pic or ''),
                str(adj.remarks or ''),
                str(adj.wo_number or ''),
                str(adj.mc_number or ''),
                str(adj.run_length or ''),
                str(adj.item_name or ''),
                str(adj.jumlah_plate or ''),
                str(adj.note or ''),
                adj.machine_off_at.strftime('%Y-%m-%d %H:%M:%S') if adj.machine_off_at else '',
                adj.pdnd_start_at.strftime('%Y-%m-%d %H:%M:%S') if adj.pdnd_start_at else '',
                adj.pdnd_finish_at.strftime('%Y-%m-%d %H:%M:%S') if adj.pdnd_finish_at else '',
                str(adj.pdnd_by or ''),
                adj.adjustment_start_at.strftime('%Y-%m-%d %H:%M:%S') if adj.adjustment_start_at else '',
                adj.adjustment_finish_at.strftime('%Y-%m-%d %H:%M:%S') if adj.adjustment_finish_at else '',
                str(adj.adjustment_by or ''),
                adj.plate_start_at.strftime('%Y-%m-%d %H:%M:%S') if adj.plate_start_at else '',
                adj.plate_finish_at.strftime('%Y-%m-%d %H:%M:%S') if adj.plate_finish_at else '',
                adj.plate_delivered_at.strftime('%Y-%m-%d %H:%M:%S') if adj.plate_delivered_at else '',
                str(adj.ctp_by or ''),
                str(adj.status or '')
            ]
            worksheet.append(row_data)
        
        # Create response with proper Excel headers
        output = io.BytesIO()
        workbook.save(output)
        output.seek(0)
        
        response = make_response(output.getvalue())
        response.headers['Content-Type'] = 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        response.headers['Content-Disposition'] = f'attachment; filename=mounting_adjustment_export_{datetime.now().strftime("%Y%m%d_%H%M%S")}.xlsx'
        
        return response
        
    except Exception as e:
        print(f"Error exporting data: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)}), 500
    
from flask import request, jsonify

@app.route('/check-bon-request', methods=['GET'])
def check_bon_request():
    try:
        # Ambil parameter dari URL
        date = request.args.get('date')
        plate_type = request.args.get('plate_type')

        # Lakukan pencarian di database
        # Asumsi Anda menggunakan SQLAlchemy atau sejenisnya
        record = BonPlate.query.filter_by(tanggal=date, jenis_plate=plate_type).first()
        
        # Cek apakah data ditemukan
        if record:
            return jsonify({
                'success': True,
                'exists': True,
                'request_number': record.request_number,
                'message': 'Nomor request bon ditemukan.'
            })
        else:
            return jsonify({
                'success': True,
                'exists': False,
                'message': 'Nomor request bon belum ada, silakan masukkan.'
            })

    except Exception as e:
        # Tangani error jika ada
        return jsonify({
            'success': False,
            'message': f'Terjadi kesalahan server: {str(e)}'
        }), 500

@app.route('/export-ctp-adjustment-data', methods=['GET'])
def export_ctp_adjustment_data():
    try:
        from flask import make_response, request, jsonify
        import io
        import openpyxl  # Import the openpyxl library
        from datetime import datetime
        
        # Get filter parameters
        status_filter = request.args.get('status', '')
        remarks_filter = request.args.get('remarks', '')
        start_date = request.args.get('start_date', '')
        end_date = request.args.get('end_date', '')
        
        # Define the filename with .xlsx extension
        filename = f'ctp_adjustment_data_{datetime.now().strftime("%Y%m%d_%H%M%S")}.xlsx'
        
        # Build query
        query = PlateAdjustmentRequest.query
        
        # Apply filters
        if status_filter:
            if status_filter == 'selesai':
                query = query.filter(PlateAdjustmentRequest.status == 'selesai')
            else:
                query = query.filter(PlateAdjustmentRequest.status == status_filter)
        
        if remarks_filter:
            query = query.filter(PlateAdjustmentRequest.remarks.ilike(f'%{remarks_filter}%'))
            
        if start_date:
            query = query.filter(PlateAdjustmentRequest.tanggal >= start_date)
        if end_date:
            query = query.filter(PlateAdjustmentRequest.tanggal <= end_date)
        
        # Get data sorted by date (newest first)
        adjustment_requests = query.order_by(PlateAdjustmentRequest.tanggal.desc(), PlateAdjustmentRequest.id.desc()).all()
        
        # Create an in-memory Excel workbook and worksheet
        workbook = openpyxl.Workbook()
        worksheet = workbook.active
        worksheet.title = "CTP Adjustment Data"
        
        # Write headers
        headers = [
            'ID', 'Tanggal', 'Mesin Cetak', 'PIC', 'Remarks', 'WO Number', 'MC Number', 
            'Run Length', 'Item Name', 'Jumlah Plate', 'Note', 'Machine Off At',
            'PDND Start At', 'PDND Finish At', 'PDND By',
            'Design Start At', 'Design Finish At', 'Design By',
            'Adjustment Start At', 'Adjustment Finish At', 'Adjustment By', 
            'Plate Start At', 'Plate Finish At', 'Plate Delivered At', 'CTP By', 'Status'
        ]
        worksheet.append(headers)
        
        # Write data rows
        for adj in adjustment_requests:
            row_data = [
                str(adj.id or ''),
                adj.tanggal.strftime('%Y-%m-%d') if adj.tanggal else '',
                str(adj.mesin_cetak or ''),
                str(adj.pic or ''),
                str(adj.remarks or ''),
                str(adj.wo_number or ''),
                str(adj.mc_number or ''),
                str(adj.run_length or ''),
                str(adj.item_name or ''),
                str(adj.jumlah_plate or ''),
                str(adj.note or ''),
                adj.machine_off_at.strftime('%Y-%m-%d %H:%M:%S') if adj.machine_off_at else '',
                adj.pdnd_start_at.strftime('%Y-%m-%d %H:%M:%S') if adj.pdnd_start_at else '',
                adj.pdnd_finish_at.strftime('%Y-%m-%d %H:%M:%S') if adj.pdnd_finish_at else '',
                str(adj.pdnd_by or ''),
                adj.adjustment_start_at.strftime('%Y-%m-%d %H:%M:%S') if adj.adjustment_start_at else '',
                adj.adjustment_finish_at.strftime('%Y-%m-%d %H:%M:%S') if adj.adjustment_finish_at else '',
                str(adj.adjustment_by or ''),
                adj.plate_start_at.strftime('%Y-%m-%d %H:%M:%S') if adj.plate_start_at else '',
                adj.plate_finish_at.strftime('%Y-%m-%d %H:%M:%S') if adj.plate_finish_at else '',
                adj.plate_delivered_at.strftime('%Y-%m-%d %H:%M:%S') if adj.plate_delivered_at else '',
                str(adj.ctp_by or ''),
                str(adj.status or '')
            ]
            worksheet.append(row_data)
        
        # Create response with proper Excel headers
        output = io.BytesIO()
        workbook.save(output)
        output.seek(0)
        
        response = make_response(output.getvalue())
        response.headers['Content-Type'] = 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        response.headers['Content-Disposition'] = f'attachment; filename={filename}'
        
        return response
        
    except Exception as e:
        print(f"Error exporting CTP adjustment data: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/export-adjustment-press', methods=['GET'])
def export_adjustment_press():
    try:
        from flask import make_response, request, jsonify
        import io
        import openpyxl  # Menggunakan openpyxl untuk XLSX
        from datetime import datetime
        
        # Get filter parameters
        date_from = request.args.get('date_from', '')
        date_to = request.args.get('date_to', '')
        mesin_cetak = request.args.get('mesin_cetak', '')

        # Build query for Adjustment Press
        query = PlateAdjustmentRequest.query
        
        # Apply filters
        if date_from:
            query = query.filter(PlateAdjustmentRequest.tanggal >= date_from)
        if date_to:
            query = query.filter(PlateAdjustmentRequest.tanggal <= date_to)
        if mesin_cetak:
            query = query.filter(PlateAdjustmentRequest.mesin_cetak == mesin_cetak)

        # Get Adjustment Press sorted by date (newest first)
        adjustment_data = query.order_by(PlateAdjustmentRequest.tanggal.desc(), PlateAdjustmentRequest.id.desc()).all()

        # Create an in-memory Excel workbook and worksheet
        workbook = openpyxl.Workbook()
        worksheet = workbook.active
        worksheet.title = "Adjustment Press Data"
        
        # Write headers
        headers = [
            'ID', 'Tanggal', 'PIC', 'Mesin Cetak', 'Remarks', 'Nomor WO', 'Nomor MC',
            'Run Length', 'Nama Item', 'Jumlah Plate', 'Note', 'Mesin Off',
            'PDND Start', 'PDND Selesai', 'PIC PDND',
            'Design Start', 'Design Selesai', 'Design By',
            'Adjustment Start', 'Adjustment Selesai', 'PIC Adjustment',
            'Plate Start', 'Plate Selesai', 'Plate Sampai',
            'PIC CTP', 'Grup CTP', 'Status', 'Total Downtime (jam)'
        ]
        worksheet.append(headers)
        
        # Write data rows
        for adjustment in adjustment_data:
            # Konversi string 'machine_off_at' ke objek datetime jika tidak kosong
            machine_off_dt = None
            if adjustment.machine_off_at:
                try:
                    # Asumsikan format string adalah 'YYYY-MM-DD HH:MM:SS'
                    machine_off_dt = datetime.strptime(str(adjustment.machine_off_at), '%Y-%m-%d %H:%M:%S')
                except (ValueError, TypeError):
                    # Atau format lain, coba sesuaikan
                    try:
                        machine_off_dt = datetime.strptime(str(adjustment.machine_off_at), '%d/%m/%Y %H:%M')
                    except (ValueError, TypeError):
                        pass # Biarkan machine_off_dt tetap None jika konversi gagal

            # Hitung downtime hanya jika kedua variabel adalah objek datetime yang valid
            total_downtime_hours = ''
            if adjustment.plate_delivered_at and machine_off_dt:
                time_delta = adjustment.plate_delivered_at - machine_off_dt
                total_downtime_hours = round(time_delta.total_seconds() / 3600, 2) # Dibulatkan 2 desimal

            row_data = [
                str(adjustment.id or ''),
                adjustment.tanggal.strftime('%Y-%m-%d') if adjustment.tanggal else '',
                str(adjustment.pic or ''),
                str(adjustment.mesin_cetak or ''),
                str(adjustment.remarks or ''),
                str(adjustment.wo_number or ''),
                str(adjustment.mc_number or ''),
                str(adjustment.run_length or ''),
                str(adjustment.item_name or ''),
                str(adjustment.jumlah_plate or ''),
                str(adjustment.note or ''),
                str(adjustment.machine_off_at or ''),
                adjustment.pdnd_start_at.strftime('%Y-%m-%d %H:%M:%S') if adjustment.pdnd_start_at else '',
                adjustment.pdnd_finish_at.strftime('%Y-%m-%d %H:%M:%S') if adjustment.pdnd_finish_at else '',
                str(adjustment.pdnd_by or ''),
                adjustment.design_start_at.strftime('%Y-%m-%d %H:%M:%S') if adjustment.design_start_at else '',
                adjustment.design_finish_at.strftime('%Y-%m-%d %H:%M:%S') if adjustment.design_finish_at else '',
                str(adjustment.design_by or ''),
                adjustment.adjustment_start_at.strftime('%Y-%m-%d %H:%M:%S') if adjustment.adjustment_start_at else '',
                adjustment.adjustment_finish_at.strftime('%Y-%m-%d %H:%M:%S') if adjustment.adjustment_finish_at else '',
                str(adjustment.adjustment_by or ''),
                adjustment.plate_start_at.strftime('%Y-%m-%d %H:%M:%S') if adjustment.plate_start_at else '',
                adjustment.plate_finish_at.strftime('%Y-%m-%d %H:%M:%S') if adjustment.plate_finish_at else '',
                adjustment.plate_delivered_at.strftime('%Y-%m-%d %H:%M:%S') if adjustment.plate_delivered_at else '',
                str(adjustment.ctp_by or ''),
                str(adjustment.ctp_group or ''),
                str(adjustment.status or ''),
                total_downtime_hours
            ]
            worksheet.append(row_data)
        
        # Create response with proper Excel headers
        output = io.BytesIO()
        workbook.save(output)
        output.seek(0)
        
        response = make_response(output.getvalue())
        response.headers['Content-Type'] = 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        response.headers['Content-Disposition'] = f'attachment; filename=adjustment_press_export_{datetime.now().strftime("%Y%m%d_%H%M%S")}.xlsx'
        
        return response
        
    except Exception as e:
        print(f"Error exporting adjustment press data: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/export-bon-press', methods=['GET'])
def export_bon_press():
    try:
        from flask import make_response, request, jsonify
        import io
        import openpyxl  # Menggunakan openpyxl untuk XLSX
        from datetime import datetime
        
        # Get filter parameters
        date_from = request.args.get('date_from', '')
        date_to = request.args.get('date_to', '')
        mesin_cetak = request.args.get('mesin_cetak', '')

        # Build query for Bon Press
        query = PlateBonRequest.query
        
        # Apply filters
        if date_from:
            query = query.filter(PlateBonRequest.tanggal >= date_from)
        if date_to:
            query = query.filter(PlateBonRequest.tanggal <= date_to)
        if mesin_cetak:
            query = query.filter(PlateBonRequest.mesin_cetak == mesin_cetak)

        # Get Bon Press sorted by date (newest first)
        bon_data = query.order_by(PlateBonRequest.tanggal.desc(), PlateBonRequest.id.desc()).all()

        # Create an in-memory Excel workbook and worksheet
        workbook = openpyxl.Workbook()
        worksheet = workbook.active
        worksheet.title = "Bon Press Data"
        
        # Write headers
        headers = [
            'Tanggal', 'PIC', 'Mesin Cetak', 'Remarks', 'Nomor WO', 'Nomor MC',
            'Run Length', 'Nama Item', 'Jumlah Plate', 'Note',
            'Mesin Off', 'Plate Start', 'Plate Selesai', 'Plate Sampai',
            'PIC CTP', 'Grup CTP', 'Status', 'Total Downtime (jam)'
        ]
        worksheet.append(headers)
        
        # Write data rows
        for bon in bon_data:
            # Konversi string 'machine_off_at' ke objek datetime jika tidak kosong
            machine_off_dt = None
            if bon.machine_off_at:
                try:
                    # Asumsikan format string adalah 'YYYY-MM-DD HH:MM:SS'
                    machine_off_dt = datetime.strptime(str(bon.machine_off_at), '%Y-%m-%d %H:%M:%S')
                except (ValueError, TypeError):
                    # Atau format lain jika diperlukan
                    pass

            # Hitung downtime hanya jika kedua variabel adalah objek datetime yang valid
            total_downtime_hours = ''
            if bon.plate_delivered_at and machine_off_dt:
                time_delta = bon.plate_delivered_at - machine_off_dt
                total_downtime_hours = round(time_delta.total_seconds() / 3600, 2) # Dibulatkan 2 desimal
            
            row_data = [
                bon.tanggal.strftime('%Y-%m-%d') if bon.tanggal else '',
                str(bon.pic or ''),
                str(bon.mesin_cetak or ''),
                str(bon.remarks or ''),
                str(bon.wo_number or ''),
                str(bon.mc_number or ''),
                str(bon.run_length or ''),
                str(bon.item_name or ''),
                str(bon.jumlah_plate or ''),
                str(bon.note or ''),
                str(bon.machine_off_at or ''),
                bon.plate_start_at.strftime('%Y-%m-%d %H:%M:%S') if bon.plate_start_at else '',
                bon.plate_finish_at.strftime('%Y-%m-%d %H:%M:%S') if bon.plate_finish_at else '',
                bon.plate_delivered_at.strftime('%Y-%m-%d %H:%M:%S') if bon.plate_delivered_at else '',
                str(bon.ctp_by or ''),
                str(bon.ctp_group or ''),
                str(bon.status or ''),
                total_downtime_hours
            ]
            worksheet.append(row_data)
        
        # Create response with proper Excel headers
        output = io.BytesIO()
        workbook.save(output)
        output.seek(0)
        
        response = make_response(output.getvalue())
        response.headers['Content-Type'] = 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        response.headers['Content-Disposition'] = f'attachment; filename=bon_press_export_{datetime.now().strftime("%Y%m%d_%H%M%S")}.xlsx'
        
        return response
        
    except Exception as e:
        print(f"Error exporting bon press data: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)}), 500
    
@app.route('/export-kpi-ctp', methods=['GET'])
def export_kpi_ctp():
    try:
        from flask import make_response, request, jsonify
        import io
        import openpyxl
        from datetime import datetime

        # Get filter parameters
        date_from = request.args.get('date_from', '')
        date_to = request.args.get('date_to', '')
        ctp_group = request.args.get('ctp_group', '')

        # Build query for KPI CTP data
        query = CTPProductionLog.query

        # Apply filters
        if date_from:
            query = query.filter(CTPProductionLog.log_date >= date_from)
        if date_to:
            query = query.filter(CTPProductionLog.log_date <= date_to)
        if ctp_group:
            query = query.filter(CTPProductionLog.ctp_group == ctp_group)

        # Get CTP data sorted by date (newest first)
        kpi_data = query.order_by(CTPProductionLog.log_date.desc(), CTPProductionLog.id.desc()).all()

        # Create an in-memory Excel workbook and worksheet
        workbook = openpyxl.Workbook()
        worksheet = workbook.active
        worksheet.title = "KPI CTP Data"

        # Write headers
        headers = [
            'Tanggal', 'Group CTP', 'Shift', 'PIC', 'Mesin CTP',
            'Processor Temperature', 'Dwell Time', 'WO Number', 'MC Number',
            'Run Length', 'Print Machine', 'Remarks Job', 'Item Name',
            'Note', 'Plate Type Material', 'Raster',
            'Plate Good', 'Plate Not Good', 'Not Good Reason',
            'Cyan 25%', 'Cyan 50%', 'Cyan 75%',
            'Magenta 25%', 'Magenta 50%', 'Magenta 75%',
            'Yellow 25%', 'Yellow 50%', 'Yellow 75%',
            'Black 25%', 'Black 50%', 'Black 75%',
            'Spot Color 1 25%', 'Spot Color 1 50%', 'Spot Color 1 75%',
            'Spot Color 2 25%', 'Spot Color 2 50%', 'Spot Color 2 75%',
            'Spot Color 3 25%', 'Spot Color 3 50%', 'Spot Color 3 75%',
            'Spot Color 4 25%', 'Spot Color 4 50%', 'Spot Color 4 75%',
            'Start Time', 'Finish Time'
        ]
        worksheet.append(headers)

        # Write data rows
        for kpi in kpi_data:
            row_data = [
                kpi.log_date.strftime('%Y-%m-%d') if kpi.log_date else '',
                str(kpi.ctp_group or ''),
                str(kpi.ctp_shift or ''),
                str(kpi.ctp_pic or ''),
                str(kpi.ctp_machine or ''),
                str(kpi.processor_temperature or ''),
                str(kpi.dwell_time or ''),
                str(kpi.wo_number or ''),
                str(kpi.mc_number or ''),
                str(kpi.run_length_sheet or ''),
                str(kpi.print_machine or ''),
                str(kpi.remarks_job or ''),
                str(kpi.item_name or ''),
                str(kpi.note or ''),
                str(kpi.plate_type_material or ''),
                str(kpi.raster or ''),
                str(kpi.num_plate_good or ''),
                str(kpi.num_plate_not_good or ''),
                str(kpi.not_good_reason or ''),
                str(kpi.cyan_25_percent or ''),
                str(kpi.cyan_50_percent or ''),
                str(kpi.cyan_75_percent or ''),
                str(kpi.magenta_25_percent or ''),
                str(kpi.magenta_50_percent or ''),
                str(kpi.magenta_75_percent or ''),
                str(kpi.yellow_25_percent or ''),
                str(kpi.yellow_50_percent or ''),
                str(kpi.yellow_75_percent or ''),
                str(kpi.black_25_percent or ''),
                str(kpi.black_50_percent or ''),
                str(kpi.black_75_percent or ''),
                str(kpi.x_25_percent or ''),
                str(kpi.x_50_percent or ''),
                str(kpi.x_75_percent or ''),
                str(kpi.z_25_percent or ''),
                str(kpi.z_50_percent or ''),
                str(kpi.z_75_percent or ''),
                str(kpi.u_25_percent or ''),
                str(kpi.u_50_percent or ''),
                str(kpi.u_75_percent or ''),
                str(kpi.v_25_percent or ''),
                str(kpi.v_50_percent or ''),
                str(kpi.v_75_percent or ''),
                kpi.start_time.strftime('%H:%M') if kpi.start_time else '',
                kpi.finish_time.strftime('%H:%M') if kpi.finish_time else ''
            ]
            worksheet.append(row_data)
        
        # Create response with proper Excel headers
        output = io.BytesIO()
        workbook.save(output)
        output.seek(0)
        
        response = make_response(output.getvalue())
        response.headers['Content-Type'] = 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        response.headers['Content-Disposition'] = f'attachment; filename=kpi_ctp_export_{datetime.now().strftime("%Y%m%d_%H%M%S")}.xlsx'
        
        return response
    
    except Exception as e:
        print(f"Error exporting KPI CTP data: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/export-ctp-bon', methods=['GET'])
def export_ctp_bon():
    try:
        from flask import make_response, request, jsonify
        import io
        import openpyxl  # Menggunakan openpyxl untuk XLSX
        from datetime import datetime
        
        # Get filter parameters
        status_filter = request.args.get('status', '')
        remarks_filter = request.args.get('remarks', '')
        date_from = request.args.get('date_from', '')
        date_to = request.args.get('date_to', '')
        
        # Build query
        query = PlateBonRequest.query
        
        # Apply filters
        if status_filter:
            query = query.filter(PlateBonRequest.status == status_filter)
        
        if remarks_filter:
            query = query.filter(PlateBonRequest.remarks.ilike(f'%{remarks_filter}%'))
            
        if date_from:
            query = query.filter(PlateBonRequest.tanggal >= date_from)
        if date_to:
            query = query.filter(PlateBonRequest.tanggal <= date_to)
        
        # Get data sorted by date (newest first)
        bon_requests = query.order_by(PlateBonRequest.tanggal.desc(), PlateBonRequest.id.desc()).all()
        
        # Create an in-memory Excel workbook and worksheet
        workbook = openpyxl.Workbook()
        worksheet = workbook.active
        worksheet.title = "CTP Bon Data"
        
        # Write headers
        headers = [
            'ID', 'Tanggal', 'Mesin Cetak', 'PIC', 'Remarks', 'WO Number', 'MC Number', 
            'Run Length', 'Item Name', 'Jumlah Plate', 'Note', 'Machine Off At',
            'Plate Start At', 'Plate Finish At', 'Plate Delivered At', 'CTP By', 'Status'
        ]
        worksheet.append(headers)
        
        # Write data rows
        for bon in bon_requests:
            row_data = [
                str(bon.id or ''),
                bon.tanggal.strftime('%Y-%m-%d') if bon.tanggal else '',
                str(bon.mesin_cetak or ''),
                str(bon.pic or ''),
                str(bon.remarks or ''),
                str(bon.wo_number or ''),
                str(bon.mc_number or ''),
                str(bon.run_length or ''),
                str(bon.item_name or ''),
                str(bon.jumlah_plate or ''),
                str(bon.note or ''),
                bon.machine_off_at.strftime('%Y-%m-%d %H:%M:%S') if bon.machine_off_at else '',
                bon.plate_start_at.strftime('%Y-%m-%d %H:%M:%S') if bon.plate_start_at else '',
                bon.plate_finish_at.strftime('%Y-%m-%d %H:%M:%S') if bon.plate_finish_at else '',
                bon.plate_delivered_at.strftime('%Y-%m-%d %H:%M:%S') if bon.plate_delivered_at else '',
                str(bon.ctp_by or ''),
                str(bon.status or '')
            ]
            worksheet.append(row_data)
        
        # Create response with proper Excel headers
        output = io.BytesIO()
        workbook.save(output)
        output.seek(0)
        
        response = make_response(output.getvalue())
        response.headers['Content-Type'] = 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        response.headers['Content-Disposition'] = f'attachment; filename=ctp_bon_export_{datetime.now().strftime("%Y%m%d_%H%M%S")}.xlsx'
        
        return response
        
    except Exception as e:
        print(f"Error exporting CTP bon data: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/export-ctp-bon-data', methods=['GET'])
def export_ctp_bon_data():
    try:
        from flask import make_response, request, jsonify
        import io
        import openpyxl  # Menggunakan openpyxl untuk XLSX
        from datetime import datetime
        
        # Get filter parameters
        status_filter = request.args.get('status', '')
        remarks_filter = request.args.get('remarks', '')
        start_date = request.args.get('start_date', '')
        end_date = request.args.get('end_date', '')
        
        # Define the filename with .xlsx extension
        filename = f'ctp_bon_data_{datetime.now().strftime("%Y%m%d_%H%M%S")}.xlsx'
        
        # Build query
        query = PlateBonRequest.query
        
        # Apply filters
        if status_filter:
            if status_filter == 'selesai':
                query = query.filter(PlateBonRequest.status == 'selesai')
            else:
                query = query.filter(PlateBonRequest.status == status_filter)
        
        if remarks_filter:
            query = query.filter(PlateBonRequest.remarks.ilike(f'%{remarks_filter}%'))
            
        if start_date:
            query = query.filter(PlateBonRequest.tanggal >= start_date)
        if end_date:
            query = query.filter(PlateBonRequest.tanggal <= end_date)
        
        # Get data sorted by date (newest first)
        bon_requests = query.order_by(PlateBonRequest.tanggal.desc(), PlateBonRequest.id.desc()).all()
        
        # Create an in-memory Excel workbook and worksheet
        workbook = openpyxl.Workbook()
        worksheet = workbook.active
        worksheet.title = "CTP Bon Data"
        
        # Write headers
        headers = [
            'ID', 'Tanggal', 'Mesin Cetak', 'PIC', 'Remarks', 'WO Number', 'MC Number', 
            'Run Length', 'Item Name', 'Jumlah Plate', 'Note', 'Machine Off At',
            'Plate Start At', 'Plate Finish At', 'Plate Delivered At', 'CTP By', 'Status'
        ]
        worksheet.append(headers)
        
        # Write data rows
        for bon in bon_requests:
            row_data = [
                str(bon.id or ''),
                bon.tanggal.strftime('%Y-%m-%d') if bon.tanggal else '',
                str(bon.mesin_cetak or ''),
                str(bon.pic or ''),
                str(bon.remarks or ''),
                str(bon.wo_number or ''),
                str(bon.mc_number or ''),
                str(bon.run_length or ''),
                str(bon.item_name or ''),
                str(bon.jumlah_plate or ''),
                str(bon.note or ''),
                bon.machine_off_at.strftime('%Y-%m-%d %H:%M:%S') if bon.machine_off_at else '',
                bon.plate_start_at.strftime('%Y-%m-%d %H:%M:%S') if bon.plate_start_at else '',
                bon.plate_finish_at.strftime('%Y-%m-%d %H:%M:%S') if bon.plate_finish_at else '',
                bon.plate_delivered_at.strftime('%Y-%m-%d %H:%M:%S') if bon.plate_delivered_at else '',
                str(bon.ctp_by or ''),
                str(bon.status or '')
            ]
            worksheet.append(row_data)
        
        # Create response with proper Excel headers
        output = io.BytesIO()
        workbook.save(output)
        output.seek(0)
        
        response = make_response(output.getvalue())
        response.headers['Content-Type'] = 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        response.headers['Content-Disposition'] = f'attachment; filename={filename}'
        
        return response
        
    except Exception as e:
        print(f"Error exporting CTP bon data: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5021, debug=True)