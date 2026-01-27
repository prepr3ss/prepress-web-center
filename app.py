# Standard library imports
from datetime import datetime, time, timedelta
from functools import wraps
from io import BytesIO, StringIO
from urllib.parse import quote_plus
import calendar
import csv
import io
import locale
import os
import pytz
import random
import traceback

# Third party imports
from flask import Flask, abort, flash, jsonify, make_response, redirect, render_template, request, send_file, send_from_directory, session, url_for
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy
from openpyxl import Workbook
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
from openpyxl.utils import get_column_letter
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, landscape, letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle
from sqlalchemy import String, and_, cast, extract, func, literal_column, or_, text
from werkzeug.middleware.proxy_fix import ProxyFix
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
import openpyxl
import pymysql

# Local imports
from config import DB_CONFIG
from models import db, Division, User, CTPProductionLog, PlateAdjustmentRequest, PlateBonRequest, KartuStockPlateFuji, KartuStockPlateSaphira, KartuStockChemicalFuji, KartuStockChemicalSaphira, MonthlyWorkHours, ChemicalBonCTP, BonPlate, CTPMachine, CTPProblemLog, CTPProblemPhoto, CTPProblemDocument, TaskCategory, Task, CloudsphereJob, JobTask, JobProgress, JobProgressTask, EvidenceFile, UniversalNotification, NotificationRecipient
from models_rnd import db, RNDProgressStep, RNDProgressTask, RNDJob, RNDJobProgressAssignment, RNDJobTaskAssignment, RNDLeadTimeTracking, RNDEvidenceFile, RNDTaskCompletion
from models_rnd_external import RNDExternalTime
from models_mounting import MountingWorkOrderIncoming
from export_routes import export_bp
from ctp_log_routes import ctp_log_bp
from ctp_dashboard_routes import ctp_dashboard_bp
from cloudsphere import cloudsphere_bp
from rnd_cloudsphere import rnd_cloudsphere_bp
from rnd_webcenter import rnd_webcenter_bp
from mounting_work_order import mounting_work_order_bp
from blueprints.notification_routes import notification_bp
from blueprints.tools_5w1h import tools_5w1h_bp
from blueprints.external_delay_routes import external_delay_bp
from plate_details import PLATE_DETAILS

# Timezone untuk Jakarta
jakarta_tz = pytz.timezone('Asia/Jakarta')
now_jakarta = datetime.now(jakarta_tz)

# Impor konfigurasi database Anda dari config.py

# Helper function to format datetime in Indonesian
def format_datetime_indonesia(dt):
    """Format datetime to Indonesian format"""
    if not dt:
        return ''
    
    bulan_indonesia = [
        'Januari', 'Februari', 'Maret', 'April', 'Mei', 'Juni',
        'Juli', 'Agustus', 'September', 'Oktober', 'November', 'Desember'
    ]
    
    day = dt.day
    month = bulan_indonesia[dt.month - 1]
    year = dt.year
    hour = str(dt.hour).zfill(2)
    minute = str(dt.minute).zfill(2)
    
    return f"{day} {month} {year} - {hour}:{minute}"

def format_tanggal_indonesia(dt):
    """Format date to Indonesian format"""
    if not dt:
        return ''
    
    bulan_indonesia = [
        'Januari', 'Februari', 'Maret', 'April', 'Mei', 'Juni',
        'Juli', 'Agustus', 'September', 'Oktober', 'November', 'Desember'
    ]
    
    day = dt.day
    month = bulan_indonesia[dt.month - 1]
    year = dt.year
    
    return f"{day} {month} {year}"

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key-here-change-in-production'  # Ganti dengan key yang aman

# Konfigurasi Flask-Login
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'
login_manager.login_message = 'Silakan login untuk mengakses halaman ini.'
login_manager.login_message_category = 'info'

# Konfigurasi remember cookie untuk memastikan logout berfungsi dengan benar
app.config['REMEMBER_COOKIE_NAME'] = 'remember_token'
app.config['REMEMBER_COOKIE_DURATION'] = timedelta(days=30)
app.config['REMEMBER_COOKIE_HTTPONLY'] = True

# Konfigurasi Database MySQL menggunakan DB_CONFIG dari config.py
db_user = DB_CONFIG['user']
db_password = quote_plus(DB_CONFIG['password'])
db_host = DB_CONFIG['host']
db_name = DB_CONFIG['database']
db_port = DB_CONFIG['port']

app.config['SQLALCHEMY_DATABASE_URI'] = f'mysql+pymysql://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Konfigurasi path untuk upload files (dapat menggunakan local atau network drive)
# Gunakan environment variable untuk flexibility (default ke Y:\Impact untuk network drive)
app.config['UPLOADS_PATH'] = os.environ.get('UPLOADS_PATH', r'Y:\Impact')

# Register Blueprints
app.register_blueprint(export_bp)
app.register_blueprint(ctp_log_bp)
app.register_blueprint(ctp_dashboard_bp)
app.register_blueprint(cloudsphere_bp)
app.register_blueprint(rnd_cloudsphere_bp)
app.register_blueprint(external_delay_bp)
app.register_blueprint(rnd_webcenter_bp)
app.register_blueprint(mounting_work_order_bp)
app.register_blueprint(notification_bp)  # NEW: Universal Notification System
app.register_blueprint(tools_5w1h_bp)

# Initialize the db instance from models.py with the app
db.init_app(app)
migrate = Migrate(app, db)


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
        'curve': [],
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

        # Curve notifications (non-EPSON items)
        curve_states = ['menunggu_adjustment_curve', 'proses_adjustment_curve', 'ditolakmounting']
        curve_q = PlateAdjustmentRequest.query.filter(
            PlateAdjustmentRequest.status.in_(curve_states),
            
        )
        notifications['curve'] = curve_q.all()

        # Pastikan data yang dikirim ke frontend hanyalah list status
        result = {
            'ctp_adjustment': [{'status': item.status} for item in notifications['ctp_adjustment']],
            'ctp_bon': [{'status': item.status} for item in notifications['ctp_bon']],
            'pdnd': [{'status': item.status} for item in notifications['pdnd']],
            'design': [{'status': item.status} for item in notifications['design']],
            'mounting': [{'status': item.status} for item in notifications['mounting']],
            'curve': [{'status': item.status} for item in notifications['curve']]
        }
        
        return jsonify(result)

    except Exception as e:
        print(f"Error checking notifications: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

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

def require_rnd_access(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            return redirect(url_for('login'))
        if not current_user.can_access_rnd():
            flash('Akses ditolak. Anda tidak memiliki akses ke divisi R&D.', 'error')
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
            stock.confirmed_at = now_jakarta
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
                stock = KartuStockPlateFuji(
                    tanggal=selected_date,
                    shift='1',  # Add required shift field
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
                    shift='1',  # Add required shift field
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
                stock = KartuStockPlateSaphira(
                    tanggal=selected_date,
                    shift='1',  # Add required shift field
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
                    shift='1',  # Add required shift field
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
            existing_record.updated_at = now_jakarta
        else:
            # Create new record
            new_record = MonthlyWorkHours(
                year=data['year'],
                month=data['month'],
                total_work_hours_proof=float(data['total_work_hours_proof']),
                total_work_hours_produksi=float(data['total_work_hours_produksi']),
                created_at=now_jakarta,
                updated_at=now_jakarta
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
    
    # Clear remember me cookie if it exists
    response = make_response(redirect(url_for('login')))
    
    # Delete cookies with different possible names, paths, and domains
    cookie_names = ['remember_token', 'remember', 'session']
    paths = ['/', '/impact', '']
    domains = [None, '', 'localhost']  # Handle different domain scenarios
    
    # Log untuk debugging (dapat dihapus di production)
    app.logger.info(f"User {current_user.username if current_user.is_authenticated else 'unknown'} logging out")
    
    for cookie_name in cookie_names:
        for path in paths:
            for domain in domains:
                response.delete_cookie(cookie_name, path=path, domain=domain)
                # Also set cookie to expire in the past as a fallback
                response.set_cookie(cookie_name, '', expires=0, path=path, domain=domain)
                app.logger.debug(f"Attempting to delete cookie: {cookie_name}, path: {path}, domain: {domain}")
    
    app.logger.info("Logout completed, all remember cookies should be cleared")
    return response

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
    created = kpi_entry.created_at
    if created:
        # Buat perbandingan timezone-safe: normalisasi kedua waktu ke UTC-aware
        try:
            now_utc = datetime.now(pytz.utc)

            if created.tzinfo is None:
                # Asumsikan nilai yang disimpan tanpa tz adalah UTC
                created_aware = pytz.utc.localize(created)
            else:
                created_aware = created.astimezone(pytz.utc)

            age = now_utc - created_aware
        except Exception:
            # Fallback: coba bandingkan sebagai naive (both in UTC naive)
            now_naive = datetime.utcnow()
            if getattr(created, 'tzinfo', None) is not None:
                created_naive = created.astimezone(pytz.utc).replace(tzinfo=None)
            else:
                created_naive = created
            age = now_naive - created_naive

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

def require_any_press_submenu_access(f):
    """
    Memastikan pengguna memiliki setidaknya salah satu dari hak akses berikut:
    Press, CTP, Mounting, atau PDND.
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Periksa apakah user memiliki SALAH SATU dari hak akses
        has_access = (
            current_user.can_access_press() or
            current_user.can_access_ctp() or
            current_user.can_access_mounting() or
            current_user.can_access_pdnd() or
            current_user.can_access_design()
        )
        
        if not has_access:
            # Jika tidak ada akses, batalkan permintaan (Unauthorized)
            abort(403) 
        
        return f(*args, **kwargs)
    return decorated_function

def require_press_bon_access(f):
    """
    Memastikan pengguna memiliki setidaknya salah satu dari hak akses berikut:
    Press, CTP, Mounting, atau PDND.
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Periksa apakah user memiliki SALAH SATU dari hak akses
        has_access = (
            current_user.can_access_press() or
            current_user.can_access_ctp()
        )
        
        if not has_access:
            # Jika tidak ada akses, batalkan permintaan (Unauthorized)
            abort(403) 
        
        return f(*args, **kwargs)
    return decorated_function


# NEW: Rute untuk halaman Data Adjustment
@app.route('/data-adjustment')
@login_required
@require_any_press_submenu_access
def data_adjustment_page():
    return render_template('data_adjustment.html', current_user=current_user)

# NEW: Rute untuk halaman Data Bon
@app.route('/data-bon')
@login_required
@require_press_bon_access
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
                # Normalize material to be robust against spaces and hyphens (e.g., 'LH-PJA' vs 'LHPJA')
                normalized_material = material.replace(' ', '').replace('-', '')
                matched_size = None
                
                for size in plate_sizes:
                    # Normalize size key similarly to ensure consistent substring checks
                    size_check = size.replace(' ', '').replace('-', '')
                    material_check = normalized_material
                    if size_check in material_check:
                        matched_size = size
                        # Variant refinement using normalized material for robustness
                        if size == '1030':
                            # PN detection for SAPHIRA 1030 PN (check first to avoid conflicts)
                            if 'PN' in material_check:
                                matched_size = '1030 PN'
                            # UV detection should also consider PJ2 codes commonly used for UV variants
                            elif 'UV' in material_check or 'PJ2' in material_check:
                                matched_size = '1030 UV'
                            # Handle LH-PJA or LHPJA variant (accept both with/without hyphen)
                            elif 'LHPJA' in material_check or 'PJA' in material_check:
                                matched_size = '1030 LHPJA'
                        elif size == '1055':
                            if 'PN' in material_check:
                                matched_size = '1055 PN'
                            elif 'UV' in material_check or 'PJ2' in material_check:
                                matched_size = '1055 UV'
                            elif 'LHPL' in material_check:
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
            paper_type=data['paper_type'],
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
            paper_type=data['paper_type'],
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

# --- Mounting Dashboard Routes ---
@app.route('/dashboard-mounting')
@login_required
@require_mounting_access
def dashboard_mounting():
    return render_template('dashboard_mounting.html')

@app.route('/get-mounting-dashboard-data')
@login_required
@require_mounting_access
def get_mounting_dashboard_data():
    try:
        # Ambil year dan month. Jika month kosong (""), request.args.get dengan type=int akan menghasilkan None.
        year = request.args.get('year', type=int)
        month = request.args.get('month', type=int)

        # Jika tidak ada tahun yang ditentukan, gunakan tahun dan bulan saat ini
        if not year:
            current_date = datetime.now()
            year = current_date.year
            month = current_date.month

        # Remarks lists
        fa_remarks = ['ADJUSTMENT FA PROOF', 'ADJUSTMENT FA PRODUKSI']
        curve_remarks = ['ADJUSTMENT CURVE PROOF', 'ADJUSTMENT CURVE PRODUKSI']
        fa_upper = [r.upper() for r in fa_remarks]
        curve_upper = [r.upper() for r in curve_remarks]
        combined_upper = fa_upper + curve_upper

        # --- Base Filters Dibuat Sekali ---
        # Filters umum: status 'selesai', adjustment_start_at ada, tahun sesuai, dan remarks sesuai.
        base_filters = [
            PlateAdjustmentRequest.status == 'selesai',
            PlateAdjustmentRequest.adjustment_start_at != None,
            extract('year', PlateAdjustmentRequest.adjustment_start_at) == year,
            func.upper(PlateAdjustmentRequest.remarks).in_(combined_upper)
        ]

        # Tambahkan filter bulan hanya jika bulan ditentukan (month != None)
        month_filter = [
            extract('month', PlateAdjustmentRequest.adjustment_start_at) == month
        ] if month else []
        
        # Filters lengkap (base_filters + month_filter)
        full_filters = base_filters + month_filter
        
        # Filters untuk total FA
        fa_filters = base_filters + month_filter + [func.upper(PlateAdjustmentRequest.remarks).in_(fa_upper)]
        
        # Filters untuk total Curve
        curve_filters = base_filters + month_filter + [func.upper(PlateAdjustmentRequest.remarks).in_(curve_upper)]
        
        # Filters untuk Minutes (membutuhkan adjustment_finish_at)
        minutes_condition = PlateAdjustmentRequest.adjustment_finish_at != None
        minutes_filters = full_filters + [minutes_condition]
        
        fa_minutes_filters = fa_filters + [minutes_condition]
        curve_minutes_filters = curve_filters + [minutes_condition]

        # --- Totals (counts) ---
        total_adjustments = PlateAdjustmentRequest.query.filter(*full_filters).count()
        
        # Menggunakan filter yang telah dibuat
        total_fa = PlateAdjustmentRequest.query.filter(*fa_filters).count()
        total_curve = PlateAdjustmentRequest.query.filter(*curve_filters).count()

        # --- Minutes Calculations ---
        total_minutes = db.session.query(
            func.coalesce(func.sum(
                func.timestampdiff(
                    literal_column('MINUTE'),
                    PlateAdjustmentRequest.adjustment_start_at,
                    PlateAdjustmentRequest.adjustment_finish_at
                )
            ), 0)
        ).filter(*minutes_filters).scalar() or 0

        # Minutes for FA and Curve separately
        fa_minutes = db.session.query(
            func.coalesce(func.sum(
                func.timestampdiff(
                    literal_column('MINUTE'),
                    PlateAdjustmentRequest.adjustment_start_at,
                    PlateAdjustmentRequest.adjustment_finish_at
                )
            ), 0)
        ).filter(*fa_minutes_filters).scalar() or 0

        curve_minutes = db.session.query(
            func.coalesce(func.sum(
                func.timestampdiff(
                    literal_column('MINUTE'),
                    PlateAdjustmentRequest.adjustment_start_at,
                    PlateAdjustmentRequest.adjustment_finish_at
                )
            ), 0)
        ).filter(*curve_minutes_filters).scalar() or 0

        avg_minutes_per_job = total_minutes / total_adjustments if total_adjustments > 0 else 0
        avg_minutes_fa = fa_minutes / total_fa if total_fa > 0 else 0
        avg_minutes_curve = curve_minutes / total_curve if total_curve > 0 else 0

        # --- Per-Adjuster Cards ---
        adjuster_filters = full_filters + [
            PlateAdjustmentRequest.adjustment_by != None,
            PlateAdjustmentRequest.adjustment_by != '',
        ]
        
        # Dapatkan daftar adjusters unik
        adjuster_rows = db.session.query(PlateAdjustmentRequest.adjustment_by).filter(*adjuster_filters).distinct().all()
        adjusters = [r[0] for r in adjuster_rows if r and r[0]]

        adjusters_data = []
        for name in adjusters:
            # Reusable name filter base
            name_base_filters = [
                PlateAdjustmentRequest.adjustment_by == name,
            ]
            
            # Combine filters
            name_filters_full = full_filters + name_base_filters
            name_filters_fa = fa_filters + name_base_filters
            name_filters_curve = curve_filters + name_base_filters
            name_filters_minutes = minutes_filters + name_base_filters

            name_count = PlateAdjustmentRequest.query.filter(*name_filters_full).count()
            name_fa_count = PlateAdjustmentRequest.query.filter(*name_filters_fa).count()
            name_curve_count = PlateAdjustmentRequest.query.filter(*name_filters_curve).count()

            name_minutes = db.session.query(
                func.coalesce(func.sum(
                    func.timestampdiff(
                        literal_column('MINUTE'),
                        PlateAdjustmentRequest.adjustment_start_at,
                        PlateAdjustmentRequest.adjustment_finish_at
                    )
                ), 0)
            ).filter(*name_filters_minutes).scalar() or 0

            name_avg = name_minutes / name_count if name_count > 0 else 0

            adjusters_data.append({
                'name': name,
                'total_adjustments': name_count,
                'total_fa': name_fa_count,
                'total_curve': name_curve_count,
                'total_minutes': name_minutes,
                'avg_minutes_per_job': name_avg
            })

        # Provide both 'adjusters' (new) and 'users' (back-compat) keys
        return jsonify({
            'overall': {
                'total_adjustments': total_adjustments,
                'total_fa': total_fa,
                'total_curve': total_curve,
                'total_minutes': total_minutes,
                'avg_minutes_per_job': avg_minutes_per_job,
                'fa_minutes': fa_minutes,
                'curve_minutes': curve_minutes,
                'avg_minutes_fa': avg_minutes_fa,
                'avg_minutes_curve': avg_minutes_curve
            },
            'adjusters': adjusters_data,
            'users': adjusters_data
        })
    except Exception as e:
        # log error Anda
        app.logger.error(f"Error in get_mounting_dashboard_data: {str(e)}")
        return jsonify({'error': 'Internal server error', 'message': str(e)}), 500

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
@require_any_press_submenu_access
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
@require_press_bon_access
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

        bon_request = db.session.get(PlateBonRequest, bon_id)

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

        adjustment_request = db.session.get(PlateAdjustmentRequest, adjustment_id)

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
        jakarta_tz = pytz.timezone('Asia/Jakarta')
        now_jakarta = datetime.now(jakarta_tz)
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
            paper_type=data.get('paper_type'),
            raster=data.get('raster'),
            num_plate_good=data['num_plate_good'],
            num_plate_not_good=data.get('num_plate_not_good'),
            not_good_reason=data.get('not_good_reason'),
            detail_not_good=data.get('detail_not_good'),
            cyan_20_percent=data.get('cyan_20_percent'),
            cyan_25_percent=data.get('cyan_25_percent'),
            cyan_40_percent=data.get('cyan_40_percent'),
            cyan_50_percent=data.get('cyan_50_percent'),
            cyan_80_percent=data.get('cyan_80_percent'),
            cyan_75_percent=data.get('cyan_75_percent'),
            magenta_20_percent=data.get('magenta_20_percent'),
            magenta_25_percent=data.get('magenta_25_percent'),
            magenta_40_percent=data.get('magenta_40_percent'),
            magenta_50_percent=data.get('magenta_50_percent'),
            magenta_80_percent=data.get('magenta_80_percent'),
            magenta_75_percent=data.get('magenta_75_percent'),
            yellow_20_percent=data.get('yellow_20_percent'),
            yellow_25_percent=data.get('yellow_25_percent'),
            yellow_40_percent=data.get('yellow_40_percent'),
            yellow_50_percent=data.get('yellow_50_percent'),
            yellow_80_percent=data.get('yellow_80_percent'),
            yellow_75_percent=data.get('yellow_75_percent'),
            black_20_percent=data.get('black_20_percent'),
            black_25_percent=data.get('black_25_percent'),
            black_40_percent=data.get('black_40_percent'),
            black_50_percent=data.get('black_50_percent'),
            black_80_percent=data.get('black_80_percent'),
            black_75_percent=data.get('black_75_percent'),
            x_20_percent=data.get('x_20_percent'),
            x_25_percent=data.get('x_25_percent'),
            x_40_percent=data.get('x_40_percent'),
            x_50_percent=data.get('x_50_percent'),
            x_80_percent=data.get('x_80_percent'),
            x_75_percent=data.get('x_75_percent'),
            z_20_percent=data.get('z_20_percent'),
            z_25_percent=data.get('z_25_percent'),
            z_40_percent=data.get('z_40_percent'),
            z_50_percent=data.get('z_50_percent'),
            z_80_percent=data.get('z_80_percent'),
            z_75_percent=data.get('z_75_percent'),
            u_20_percent=data.get('u_20_percent'),
            u_25_percent=data.get('u_25_percent'),
            u_40_percent=data.get('u_40_percent'),
            u_50_percent=data.get('u_50_percent'),
            u_80_percent=data.get('u_80_percent'),
            u_75_percent=data.get('u_75_percent'),
            v_20_percent=data.get('v_20_percent'),
            v_25_percent=data.get('v_25_percent'),
            v_40_percent=data.get('v_40_percent'),
            v_50_percent=data.get('v_50_percent'),
            v_80_percent=data.get('v_80_percent'),
            v_75_percent=data.get('v_75_percent'),
            f_20_percent=data.get('f_20_percent'),
            f_25_percent=data.get('f_25_percent'),
            f_40_percent=data.get('f_40_percent'),
            f_50_percent=data.get('f_50_percent'),
            f_80_percent=data.get('f_80_percent'),
            f_75_percent=data.get('f_75_percent'),
            g_20_percent=data.get('g_20_percent'),
            g_25_percent=data.get('g_25_percent'),
            g_40_percent=data.get('g_40_percent'),
            g_50_percent=data.get('g_50_percent'),
            g_80_percent=data.get('g_80_percent'),
            g_75_percent=data.get('g_75_percent'),
            h_20_percent=data.get('h_20_percent'),
            h_25_percent=data.get('h_25_percent'),
            h_40_percent=data.get('h_40_percent'),
            h_50_percent=data.get('h_50_percent'),
            h_80_percent=data.get('h_80_percent'),
            h_75_percent=data.get('h_75_percent'),
            j_20_percent=data.get('j_20_percent'),
            j_25_percent=data.get('j_25_percent'),
            j_40_percent=data.get('j_40_percent'),
            j_50_percent=data.get('j_50_percent'),
            j_80_percent=data.get('j_80_percent'),
            j_75_percent=data.get('j_75_percent'),
            # Linear fields
            cyan_linear=data.get('cyan_linear'),
            magenta_linear=data.get('magenta_linear'),
            yellow_linear=data.get('yellow_linear'),
            black_linear=data.get('black_linear'),
            x_linear=data.get('x_linear'),
            z_linear=data.get('z_linear'),
            u_linear=data.get('u_linear'),
            v_linear=data.get('v_linear'),
            f_linear=data.get('f_linear'),
            g_linear=data.get('g_linear'),
            h_linear=data.get('h_linear'),
            j_linear=data.get('j_linear'),
            start_time=start_time_obj,  # Gunakan objek time
            finish_time=finish_time_obj, # Gunakan objek time
            created_at=now_jakarta,
            updated_at=now_jakarta
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
                    CTPProductionLog.paper_type.ilike(f"%{search_query}%"),
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
        kpi_entry.paper_type = data.get('paper_type', kpi_entry.paper_type)
        kpi_entry.raster = data.get('raster', kpi_entry.raster)
        kpi_entry.num_plate_good = data.get('num_plate_good')
        kpi_entry.num_plate_not_good = data.get('num_plate_not_good')
        kpi_entry.not_good_reason = data.get('not_good_reason')
        kpi_entry.detail_not_good = data.get('detail_not_good')
        kpi_entry.cyan_20_percent = data.get('cyan_20_percent')
        kpi_entry.cyan_25_percent = data.get('cyan_25_percent')
        kpi_entry.cyan_40_percent = data.get('cyan_40_percent')
        kpi_entry.cyan_50_percent = data.get('cyan_50_percent')
        kpi_entry.cyan_80_percent = data.get('cyan_80_percent')
        kpi_entry.cyan_75_percent = data.get('cyan_75_percent')
        kpi_entry.magenta_20_percent = data.get('magenta_20_percent')
        kpi_entry.magenta_25_percent = data.get('magenta_25_percent')
        kpi_entry.magenta_40_percent = data.get('magenta_40_percent')
        kpi_entry.magenta_50_percent = data.get('magenta_50_percent')
        kpi_entry.magenta_80_percent = data.get('magenta_80_percent')
        kpi_entry.magenta_75_percent = data.get('magenta_75_percent')
        kpi_entry.yellow_20_percent = data.get('yellow_20_percent')
        kpi_entry.yellow_25_percent = data.get('yellow_25_percent')
        kpi_entry.yellow_40_percent = data.get('yellow_40_percent')
        kpi_entry.yellow_50_percent = data.get('yellow_50_percent')
        kpi_entry.yellow_80_percent = data.get('yellow_80_percent')
        kpi_entry.yellow_75_percent = data.get('yellow_75_percent')
        kpi_entry.black_20_percent = data.get('black_20_percent')
        kpi_entry.black_25_percent = data.get('black_25_percent')
        kpi_entry.black_40_percent = data.get('black_40_percent')
        kpi_entry.black_50_percent = data.get('black_50_percent')
        kpi_entry.black_80_percent = data.get('black_80_percent')
        kpi_entry.black_75_percent = data.get('black_75_percent')
        kpi_entry.x_20_percent = data.get('x_20_percent')
        kpi_entry.x_25_percent = data.get('x_25_percent')
        kpi_entry.x_40_percent = data.get('x_40_percent')
        kpi_entry.x_50_percent = data.get('x_50_percent')
        kpi_entry.x_80_percent = data.get('x_80_percent')
        kpi_entry.x_75_percent = data.get('x_75_percent')
        kpi_entry.z_20_percent = data.get('z_20_percent')
        kpi_entry.z_25_percent = data.get('z_25_percent')
        kpi_entry.z_40_percent = data.get('z_40_percent')
        kpi_entry.z_50_percent = data.get('z_50_percent')
        kpi_entry.z_80_percent = data.get('z_80_percent')
        kpi_entry.z_75_percent = data.get('z_75_percent')
        kpi_entry.u_20_percent = data.get('u_20_percent')
        kpi_entry.u_25_percent = data.get('u_25_percent')
        kpi_entry.u_40_percent = data.get('u_40_percent')
        kpi_entry.u_50_percent = data.get('u_50_percent')
        kpi_entry.u_80_percent = data.get('u_80_percent')
        kpi_entry.u_75_percent = data.get('u_75_percent')
        kpi_entry.v_20_percent = data.get('v_20_percent')
        kpi_entry.v_25_percent = data.get('v_25_percent')
        kpi_entry.v_40_percent = data.get('v_40_percent')
        kpi_entry.v_50_percent = data.get('v_50_percent')
        kpi_entry.v_80_percent = data.get('v_80_percent')
        kpi_entry.v_75_percent = data.get('v_75_percent')
        kpi_entry.f_20_percent = data.get('f_20_percent')
        kpi_entry.f_25_percent = data.get('f_25_percent')
        kpi_entry.f_40_percent = data.get('f_40_percent')
        kpi_entry.f_50_percent = data.get('f_50_percent')
        kpi_entry.f_80_percent = data.get('f_80_percent')
        kpi_entry.f_75_percent = data.get('f_75_percent')
        kpi_entry.g_20_percent = data.get('g_20_percent')
        kpi_entry.g_25_percent = data.get('g_25_percent')
        kpi_entry.g_40_percent = data.get('g_40_percent')
        kpi_entry.g_50_percent = data.get('g_50_percent')
        kpi_entry.g_80_percent = data.get('g_80_percent')
        kpi_entry.g_75_percent = data.get('g_75_percent')
        kpi_entry.h_20_percent = data.get('h_20_percent')
        kpi_entry.h_25_percent = data.get('h_25_percent')
        kpi_entry.h_40_percent = data.get('h_40_percent')
        kpi_entry.h_50_percent = data.get('h_50_percent')
        kpi_entry.h_80_percent = data.get('h_80_percent')
        kpi_entry.h_75_percent = data.get('h_75_percent')
        kpi_entry.j_20_percent = data.get('j_20_percent')
        kpi_entry.j_25_percent = data.get('j_25_percent')
        kpi_entry.j_40_percent = data.get('j_40_percent')
        kpi_entry.j_50_percent = data.get('j_50_percent')
        kpi_entry.j_80_percent = data.get('j_80_percent')
        kpi_entry.j_75_percent = data.get('j_75_percent')
        
        # Update linear fields
        kpi_entry.cyan_linear = data.get('cyan_linear')
        kpi_entry.magenta_linear = data.get('magenta_linear')
        kpi_entry.yellow_linear = data.get('yellow_linear')
        kpi_entry.black_linear = data.get('black_linear')
        kpi_entry.x_linear = data.get('x_linear')
        kpi_entry.z_linear = data.get('z_linear')
        kpi_entry.u_linear = data.get('u_linear')
        kpi_entry.v_linear = data.get('v_linear')
        kpi_entry.f_linear = data.get('f_linear')
        kpi_entry.g_linear = data.get('g_linear')
        kpi_entry.h_linear = data.get('h_linear')
        kpi_entry.j_linear = data.get('j_linear')
        
        # Update timestamp
        kpi_entry.updated_at = now_jakarta
        
        db.session.commit()
        return jsonify({'message': f'Data KPI CTP dengan ID {data_id} berhasil diperbarui!'}), 200
    except Exception as e:
        db.session.rollback()
        print(f"Error updating KPI CTP data: {e}")
        abort(500, description=f"Internal server error: {str(e)}")

# NEW: API untuk Menghapus Data KPI
@app.route('/api/kpi_ctp/<int:data_id>', methods=['DELETE'])
def delete_kpi_ctp(data_id):
    """
    Menghapus data KPI CTP berdasarkan data_id yang diberikan.
    Rute ini dipanggil oleh fungsi JavaScript deleteKpiData.
    """
    try:
        # 1. Cari data berdasarkan ID
        # Asumsi CTPProductionLog adalah model SQLAlchemy Anda
        kpi_entry = db.session.get(CTPProductionLog, data_id)

        # 2. Cek apakah data ditemukan
        if not kpi_entry:
            # Jika tidak ditemukan, kembalikan status 404
            # Frontend akan menerima JSON error ini
            return jsonify({'error': f'Data KPI CTP dengan ID {data_id} tidak ditemukan'}), 404

        # 3. Hapus data dari sesi database
        db.session.delete(kpi_entry)
        
        # 4. Terapkan perubahan ke database
        db.session.commit()
        
        # 5. Kembalikan respons sukses (penting untuk mencocokkan harapan JavaScript)
        # JavaScript mengharapkan respons JSON dengan 'message'
        return jsonify({'message': f'Data KPI CTP dengan ID {data_id} berhasil dihapus.'}), 200

    except Exception as e:
        # Jika terjadi kesalahan, lakukan rollback dan kembalikan status 500
        db.session.rollback()
        print(f"Error deleting KPI CTP data (ID: {data_id}): {e}")
        # Kembalikan 500 Internal Server Error dengan pesan JSON
        return jsonify({'error': f'Internal server error: Gagal menghapus data. {str(e)}'}), 500

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

        # Debug header log
        print(f"print_bon: start date={tanggal}, plate_type={bon.jenis_plate}, request_number={bon.request_number}")

        # Ambil semua log CTP untuk tanggal dan brand terkait
        logs = CTPProductionLog.query.filter(
            CTPProductionLog.log_date == bon.tanggal,
            CTPProductionLog.plate_type_material.like(f'%{bon.jenis_plate}%')
        ).all()
        app.logger.info(f"print_bon: date={bon.tanggal}, jenis_plate={bon.jenis_plate}, request_number={bon.request_number}")
        app.logger.info(f"print_bon: fetched logs count={len(logs)}")
        unique_materials = list({(log.plate_type_material or '').upper() for log in logs})
        app.logger.info(f"print_bon: unique plate_type_materials={unique_materials}")

        # Gunakan PLATE_DETAILS global untuk pemetaan item_code/item_name
        plate_details_all = PLATE_DETAILS
        brand = (bon.jenis_plate or '').upper()
        if brand not in plate_details_all:
            app.logger.warning(f"print_bon: brand '{brand}' tidak ada di PLATE_DETAILS. Mengembalikan tanpa items.")
            plate_details = {}
        else:
            plate_details = plate_details_all[brand]

        # Variant-aware mapping seperti /get-all-plate-data
        grouped = {}
        for log in logs:
            material_upper = (log.plate_type_material or '').upper()
            material_check = material_upper.replace(' ', '')

            # Tentukan base size
            base_size = None
            if '1030' in material_upper:
                base_size = '1030'
            elif '1055' in material_upper:
                base_size = '1055'
            elif '1630' in material_upper:
                base_size = '1630'

            resolved_size = base_size

            # Deteksi varian berdasarkan brand (robust normalization)
            normalized_material = material_upper.replace(' ', '').replace('-', '')
            if base_size == '1030':
                if brand == 'FUJI':
                    # FUJI 1030 UV (consider PJ2 as UV indicator)
                    if 'UV' in normalized_material or 'PJ2' in normalized_material:
                        resolved_size = '1030 UV'
                    # FUJI 1030 LHPJA (accept both LH-PJA and LHPJA, also PJA marker)
                    elif 'LHPJA' in normalized_material or 'PJA' in normalized_material:
                        resolved_size = '1030 LHPJA'
                elif brand == 'SAPHIRA':
                    # SAPHIRA 1030 PN
                    if 'PN' in normalized_material:
                        resolved_size = '1030 PN'
            elif base_size == '1055':
                if brand == 'SAPHIRA':
                    # SAPHIRA 1055 PN
                    if 'PN' in normalized_material:
                        resolved_size = '1055 PN'
                elif brand == 'FUJI':
                    # FUJI 1055 UV / LHPL (consider PJ2 as UV indicator)
                    if 'UV' in normalized_material or 'PJ2' in normalized_material:
                        resolved_size = '1055 UV'
                    elif 'LHPL' in normalized_material:
                        resolved_size = '1055 LHPL'

            # Log detail resolusi varian
            app.logger.info(
                f"print_bon: material='{material_upper}', base='{base_size}', "
                f"PN_present={'PN' in material_upper}, UV_present={'UV' in material_upper}, LHPL_present={'LHPL' in material_upper}, "
                f"resolved='{resolved_size}'"
            )

            if resolved_size and resolved_size in plate_details:
                details = plate_details[resolved_size]
                code = details['code']
                
                # Filter: hanya ambil Bon Konsinyasi (code dimulai dengan 02-049)
                # Skip Bon Non Konsinyasi (02-023)
                if not code.startswith('02-049'):
                    app.logger.info(f"print_bon: skip non-konsinyasi item code='{code}'")
                    continue
                
                total_jumlah = (log.num_plate_good or 0) + (log.num_plate_not_good or 0)
                wo = (log.wo_number or '').strip()

                # Tambahan log untuk verifikasi item_code terpilih
                app.logger.info(
                    f"print_bon: select code='{code}', name='{details['name']}', jumlah={total_jumlah}, wo='{wo}'"
                )

                if code in grouped:
                    grouped[code]['jumlah'] += total_jumlah
                    if wo:
                        existing_wos = [w.strip() for w in grouped[code]['keterangan'].split(',') if w.strip()]
                        if wo not in existing_wos:
                            grouped[code]['keterangan'] = (grouped[code]['keterangan'] + ',' + wo).strip(',')
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
                'bon_periode': bon.bon_periode,  # diteruskan ke template
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
        
        adjustment = db.session.get(PlateAdjustmentRequest, adjustment_id)
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

# --- Curve Data Adjustment Routes ---
@app.route('/curve-data-adjustment')
@login_required
@require_mounting_access
def curve_data_adjustment_page():
    return render_template('curve_data_adjustment.html')

@app.route('/get-curve-adjustment-data', methods=['GET'])
@login_required
@require_mounting_access
def get_curve_adjustment_data():
    try:
        # Filter untuk curve: menunggu_adjustment, proses_adjustment
        # Juga termasuk data yang sudah selesai untuk menghitung summary
        adjustments = PlateAdjustmentRequest.query.order_by(PlateAdjustmentRequest.id.desc()).all()

        # Filter hanya yang relevan untuk curve (status menunggu dan proses)
        curve_data = [
            adjustment.to_dict() for adjustment in adjustments 
            if adjustment.status in ['menunggu_adjustment_curve', 'proses_adjustment_curve']
        ]
        
        # Semua data untuk summary calculation
        all_data = [adjustment.to_dict() for adjustment in adjustments]
        
        return jsonify({
            'success': True,
            'data': curve_data,
            'all_data': all_data,  # Untuk summary calculation
            'total': len(curve_data)
        })
    except Exception as e:
        print(f"Error fetching curve adjustment data: {e}")
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/start-adjustment-curve', methods=['POST'])
def start_adjustment_curve():
    try:
        data = request.get_json()
        adjustment_id = data.get('id')
        curve_by = data.get('curve_by')

        if not adjustment_id or not curve_by:
            return jsonify({'success': False, 'error': 'Missing required data'}), 400
        
        adjustment = db.session.get(PlateAdjustmentRequest, adjustment_id) # Menggunakan db.session.get
        if adjustment is None:
            abort(404, description="Plate Adjustment Request not found")
        
        # Check if this is a reprocess
        is_reprocess = data.get('is_reprocess', False)
        
        # Update status
        adjustment.status = 'proses_adjustment_curve'
        adjustment.curve_by = curve_by

        # Jika bukan proses ulang (first time), set curve_start_at
        if not is_reprocess:
            adjustment.curve_start_at = datetime.now()
        # Jika ini adalah proses ulang, reset field terkait penolakan
        else:
            adjustment.curve_finish_at = None
            adjustment.declined_at = None
            adjustment.declined_by = None
            adjustment.decline_reason = None
        
        db.session.commit()

        return jsonify({'success': True, 'message': 'Adjustment Curve started successfully'})
    except Exception as e:
        print(f"Error starting Curve adjustment: {e}")
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/finish-adjustment-curve', methods=['POST'])
def finish_adjustment_curve():
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
        adjustment.curve_finish_at = datetime.now()
        
        db.session.commit()
        
        return jsonify({'success': True, 'message': 'Adjustment Curve finished successfully'})
    except Exception as e:
        print(f"Error finishing adjustment: {e}")
        db.session.rollback()
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
        
        adjustment = db.session.get(PlateAdjustmentRequest, adjustment_id)
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
        
        bon = db.session.get(PlateBonRequest, bon_id)
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


# --- Log CTP Routes ---
@app.route('/log-ctp')
@login_required
def log_ctp_overview_page():
    if not (current_user.can_access_ctp() or current_user.role == 'admin'):
        flash('Anda tidak memiliki akses ke halaman ini', 'danger')
        return redirect(url_for('index'))
    
    return render_template('log_ctp_overview.html')

@app.route('/log-ctp/<machine_nickname>')
@login_required
def log_ctp_detail(machine_nickname):
    if not (current_user.can_access_ctp() or current_user.role == 'admin'):
        flash('Anda tidak memiliki akses ke halaman ini', 'danger')
        return redirect(url_for('index'))
    
    # Get machine by nickname
    machine = CTPMachine.query.filter_by(nickname=machine_nickname).first()
    if not machine:
        flash('Mesin tidak ditemukan', 'danger')
        return redirect(url_for('log_ctp_overview_page'))
    
    return render_template('log_ctp_detail.html',
                        machine=machine,
                        machine_name=machine.name,
                        machine_description=machine.description,
                        machine_status=machine.status,
                        machine_nickname=machine.nickname)

# API Endpoints for CTP Log
@app.route('/api/ctp-machines', methods=['GET'])
@login_required
def get_ctp_machines():
    try:
        machines = CTPMachine.query.all()
        return jsonify({
            'success': True,
            'data': [{
                'id': m.id,
                'name': m.name,
                'nickname': m.nickname,
                'status': m.status,
                'description': m.description
            } for m in machines]
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/ctp-machines/<int:machine_id>/status', methods=['PUT'])
@login_required
def update_machine_status(machine_id):
    try:
        data = request.get_json()
        new_status = data.get('status')
        
        # Validate status value
        valid_statuses = ['active', 'maintenance', 'cleaning']
        if new_status not in valid_statuses:
            return jsonify({
                'success': False,
                'error': f'Invalid status. Must be one of: {", ".join(valid_statuses)}'
            }), 400
        
        # Find the machine
        machine = CTPMachine.query.get(machine_id)
        if not machine:
            return jsonify({'success': False, 'error': 'Machine not found'}), 404
        
        # Update the status
        machine.status = new_status
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': f'Machine status updated to {new_status}',
            'data': {
                'id': machine.id,
                'nickname': machine.nickname,
                'status': machine.status
            }
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500

# API endpoints for dynamic filter population
@app.route('/api/ctp-production-logs/years', methods=['GET'])
@login_required
def get_ctp_production_logs_years():
    """Get available years from ctp_production_logs table"""
    try:
        
        # Query distinct years from log_date
        years_query = db.session.query(
            extract('year', CTPProductionLog.log_date).label('year')
        ).distinct().order_by(
            extract('year', CTPProductionLog.log_date).desc()
        )
        
        years = [row.year for row in years_query.all()]
        
        return jsonify({
            'success': True,
            'years': years
        })
    except Exception as e:
        print(f"Error fetching years from ctp_production_logs: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/ctp-production-logs/months', methods=['GET'])
@login_required
def get_ctp_production_logs_months():
    """Get available months for a specific year from ctp_production_logs table"""
    try:
        
        year = request.args.get('year')
        if not year:
            return jsonify({
                'success': False,
                'error': 'Year parameter is required'
            }), 400
        
        # Query distinct months for the specified year
        months_query = db.session.query(
            extract('month', CTPProductionLog.log_date).label('month')
        ).filter(
            extract('year', CTPProductionLog.log_date) == int(year)
        ).distinct().order_by(
            extract('month', CTPProductionLog.log_date)
        )
        
        months = [row.month for row in months_query.all()]
        return jsonify({
            'success': True,
            'months': months
        })
    except Exception as e:
        print(f"Error fetching months from ctp_production_logs: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/ctp-production-logs/not-good-details', methods=['GET'])
@login_required
def get_not_good_plate_details():
    try:
        
        # Get filter parameters - handle as strings first to properly detect empty values
        year_str = request.args.get('year', '').strip()
        month_str = request.args.get('month', '').strip()
        category = request.args.get('category', '').strip()
        group = request.args.get('group', '').strip()
        
        # Convert to integers only if not empty
        year = int(year_str) if year_str else None
        month = int(month_str) if month_str else None
        
        # Build base query
        query = CTPProductionLog.query.filter(
            CTPProductionLog.num_plate_not_good > 0
        )
        
        # Apply category filter if provided
        if category:
            query = query.filter(
                CTPProductionLog.not_good_reason == category
            )
        
        # Apply group filter if provided
        if group:
            query = query.filter(
                CTPProductionLog.ctp_group == group
            )
        
        # Apply date filters if provided - FIXED: Proper SQLAlchemy extract syntax
        if year is not None:
            query = query.filter(
                extract('year', CTPProductionLog.log_date) == year
            )
        if month is not None:
            query = query.filter(
                extract('month', CTPProductionLog.log_date) == month
            )
        
        # Order by date descending (most recent first)
        logs = query.order_by(CTPProductionLog.log_date.desc()).all()
        
        
        # Format response data
        details = []
        for log in logs:
            details.append({
                'log_date': log.log_date.strftime('%Y-%m-%d') if log.log_date else '',
                'item_name': log.item_name or '',
                'num_plate_not_good': log.num_plate_not_good or 0,
                'detail_not_good': log.detail_not_good or '',
                'not_good_reason': log.not_good_reason or '',  # Add for debugging
                'ctp_group': log.ctp_group or '',  # Add group for debugging
                'plate_type_material': log.plate_type_material or ''  # Add plate type material
            })
        
        
        return jsonify({
            'success': True,
            'data': details,
            'debug': {
                'filters_applied': {
                    'year': year if year is not None else 'All',
                    'month': month if month is not None else 'All',
                    'category': category if category else 'All',
                    'group': group if group else 'All'
                },
                'total_logs_found': len(logs)
            }
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        })


@app.route('/api/chemical-bon-ctp/years', methods=['GET'])
@login_required
def get_chemical_bon_ctp_years():
    """Get available years from chemical_bon_ctp table"""
    print("=== API CALLED: /api/chemical-bon-ctp/years ===")
    try:
        
        print("Querying distinct years from chemical_bon_ctp.tanggal...")
        # Query distinct years from tanggal
        years_query = db.session.query(
            extract('year', ChemicalBonCTP.tanggal).label('year')
        ).distinct().order_by(
            extract('year', ChemicalBonCTP.tanggal).desc()
        )
        
        years = [row.year for row in years_query.all()]
        print(f"Found years: {years}")
        
        return jsonify({
            'success': True,
            'years': years
        })
    except Exception as e:
        print(f"Error fetching years from chemical_bon_ctp: {e}")
        traceback.print_exc()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/chemical-bon-ctp/months', methods=['GET'])
@login_required
def get_chemical_bon_ctp_months():
    """Get available months for a specific year from chemical_bon_ctp table"""
    try:
        
        year = request.args.get('year')
        if not year:
            return jsonify({
                'success': False,
                'error': 'Year parameter is required'
            }), 400
        
        # Query distinct months for the specified year
        months_query = db.session.query(
            extract('month', ChemicalBonCTP.tanggal).label('month')
        ).filter(
            extract('year', ChemicalBonCTP.tanggal) == int(year)
        ).distinct().order_by(
            extract('month', ChemicalBonCTP.tanggal)
        )
        
        months = [row.month for row in months_query.all()]
        
        return jsonify({
            'success': True,
            'months': months
        })
    except Exception as e:
        print(f"Error fetching months from chemical_bon_ctp: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


# Initialize CTP machines function
def initialize_ctp_machines():
    """Initialize CTP machines with default data"""
    with app.app_context():
        try:
            machines = [
                {
                    'name': 'CTP 1 Suprasetter',
                    'nickname': 'suprasetter',
                    'status': 'Aktif',
                    'description': 'Mesin CTP Suprasetter untuk produksi plate'
                },
                {
                    'name': 'CTP 2 Platesetter',
                    'nickname': 'platesetter',
                    'status': 'Aktif',
                    'description': 'Mesin CTP Platesetter untuk produksi plate'
                },
                {
                    'name': 'CTP 3 Trendsetter',
                    'nickname': 'trendsetter',
                    'status': 'Aktif',
                    'description': 'Mesin CTP Trendsetter untuk produksi plate'
                }
            ]
            
            for machine_data in machines:
                existing = CTPMachine.query.filter_by(nickname=machine_data['nickname']).first()
                if not existing:
                    machine = CTPMachine(**machine_data)
                    db.session.add(machine)
            
            db.session.commit()
            print("CTP machines initialized successfully")
        except Exception as e:
            print(f"Error initializing CTP machines: {e}")
            db.session.rollback()

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

@app.route('/api/ctp-not-good-by-machine')
@login_required
@require_ctp_access
def get_ctp_not_good_by_machine():
    """Aggregated num_plate_not_good by CTP machine and not_good_reason with optional year/month filters."""
    try:
        year_param = request.args.get('year', '')
        month_param = request.args.get('month', '')

        year = int(year_param) if year_param else None
        month = int(month_param) if month_param else None

        query = db.session.query(
            CTPProductionLog.ctp_machine.label('machine'),
            CTPProductionLog.not_good_reason.label('reason'),
            func.coalesce(func.sum(CTPProductionLog.num_plate_not_good), 0).label('total')
        ).filter(
            CTPProductionLog.num_plate_not_good.isnot(None),
            CTPProductionLog.num_plate_not_good > 0
        )

        if year:
            query = query.filter(extract('year', CTPProductionLog.log_date) == year)
        if month:
            query = query.filter(extract('month', CTPProductionLog.log_date) == month)

        rows = query.group_by('machine', 'reason').order_by('machine', 'reason').all()

        machine_map = {}
        for row in rows:
            machine = row.machine or 'Tidak diketahui'
            reason_raw = (row.reason or '').strip() or 'Lainnya'

            # Normalize reason similar to group KPI breakdown
            reason_lower = reason_raw.lower()
            if 'rontok' in reason_lower or 'botak' in reason_lower:
                reason = 'Plate Rontok / Botak'
            elif 'baret' in reason_lower:
                reason = 'Plate Baret'
            elif 'penyok' in reason_lower:
                reason = 'Plate Penyok'
            elif 'kotor' in reason_lower:
                reason = 'Plate Kotor'
            elif 'bergaris' in reason_lower:
                reason = 'Plate bergaris'
            elif 'tidak sesuai dp' in reason_lower:
                reason = 'Plate tidak sesuai DP'
            elif 'nilai tidak sesuai' in reason_lower:
                reason = 'Nilai tidak sesuai'
            elif 'laser jump' in reason_lower:
                reason = 'Laser Jump'
            elif 'tidak masuk millar' in reason_lower:
                reason = 'Tidak masuk millar'
            elif 'error punch' in reason_lower or 'error mesin punch' in reason_lower:
                reason = 'Error mesin Punch'
            elif 'plate jump' in reason_lower:
                reason = 'Plate Jump'
            else:
                reason = reason_raw

            if machine not in machine_map:
                machine_map[machine] = {
                    'ctp_machine': machine,
                    'total_not_good': 0,
                    'reasons': {}
                }

            machine_entry = machine_map[machine]
            val = int(row.total or 0)
            machine_entry['total_not_good'] += val
            machine_entry['reasons'][reason] = machine_entry['reasons'].get(reason, 0) + val

        data = list(machine_map.values())

        return jsonify({'success': True, 'data': data})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

# ============================================
# API: Plate Usage Analytics (MVP)
# GET /impact/get-ctp-plate-usage
# - Query: ?year=&amp;month=
# - Returns: trend (monthly/daily), by_type (plate_type_material), by_group (ctp_group)
# - Data source: CTPProductionLog model (see [python.CTPProductionLog](app.py:651))
# ============================================
    
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

@app.route('/get-plate-data')
def get_plate_data():
    try:
        date = request.args.get('date')
        plate_type = request.args.get('plate_type')
        
        if not date or not plate_type:
            return jsonify({'success': False, 'error': 'Missing parameters'})
        
        # Query plate usage data
        plate_data = db.session.execute(
            text("""
            SELECT plate_size, COUNT(*) as quantity
            FROM stock_opname_ctp
            WHERE DATE(tanggal) = :date
            AND jenis_plate = :type
            GROUP BY plate_size
            """),
            {'date': date, 'type': plate_type}
        ).fetchall()
        
        return jsonify({
            'success': True,
            'plateData': [{'size': row.plate_size, 'quantity': row.quantity} for row in plate_data]
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/get-next-bon-number')
def get_next_bon_number():
    try:
        # Get current date
        today = datetime.now()
        year = today.year
        month = today.month
        
        # Get last bon number for current month
        result = db.session.execute(
            text("""
            SELECT MAX(CAST(SUBSTRING_INDEX(bon_number, '/', 1) AS UNSIGNED)) as last_number
            FROM bon_plate
            WHERE MONTH(tanggal) = :month
            AND YEAR(tanggal) = :year
            """),
            {'month': month, 'year': year}
        ).fetchone()
        
        last_number = result.last_number if result.last_number else 0
        next_number = str(last_number + 1).zfill(3)
        
        return jsonify({
            'success': True,
            'bonNumber': next_number
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/check-detail-bon/<int:bon_id>')
def check_detail_bon(bon_id):
    """API endpoint for auto-refresh to get latest bon data"""
    try:
        # Query bon data with all related information
        bon_query = text("""
            SELECT
                pbr.id,
                pbr.tanggal,
                pbr.mesin_cetak,
                pbr.pic,
                pbr.remarks,
                pbr.status,
                pbr.machine_off_at,
                pbr.plate_start_at,
                pbr.plate_finish_at,
                pbr.plate_delivered_at,
                pbr.ctp_by,
                pbr.note,
                pbr.item_name,
                pbr.wo_number,
                pbr.mc_number,
                pbr.jumlah_plate,
                pbr.run_length,
                pbr.cancelled_at,
                pbr.cancelled_by,
                pbr.cancellation_reason,
                pbr.declined_at,
                pbr.decline_reason,
                pbr.declined_by
            FROM plate_bon_requests pbr
            WHERE pbr.id = :bon_id
        """)
        
        bon_result = db.session.execute(bon_query, {'bon_id': bon_id}).fetchone()
        
        if not bon_result:
            return jsonify({'success': False, 'error': 'Bon not found'})
        
        # Convert to dictionary and format datetime properly
        bon_data = {
            'id': bon_result.id,
            'tanggal': format_tanggal_indonesia(bon_result.tanggal) if bon_result.tanggal else '',
            'mesin_cetak': bon_result.mesin_cetak or '',
            'pic': bon_result.pic or '',
            'remarks': bon_result.remarks or '',
            'status': bon_result.status or '',
            'machine_off_at': format_datetime_indonesia(bon_result.machine_off_at) if bon_result.machine_off_at else '',
            'plate_start_at': format_datetime_indonesia(bon_result.plate_start_at) if bon_result.plate_start_at else '',
            'plate_finish_at': format_datetime_indonesia(bon_result.plate_finish_at) if bon_result.plate_finish_at else '',
            'plate_delivered_at': format_datetime_indonesia(bon_result.plate_delivered_at) if bon_result.plate_delivered_at else '',
            'ctp_by': bon_result.ctp_by or '',
            'note': bon_result.note or '',
            'item_name': bon_result.item_name or '',
            'wo_number': bon_result.wo_number or '',
            'mc_number': bon_result.mc_number or '',
            'jumlah_plate': bon_result.jumlah_plate or 0,
            'run_length': bon_result.run_length or '',
            'cancelled_at': bon_result.cancelled_at.strftime('%d %B %Y - %H:%M') if bon_result.cancelled_at else '',
            'cancelled_by': bon_result.cancelled_by or '',
            'cancellation_reason': bon_result.cancellation_reason or '',
            'declined_at': bon_result.declined_at.strftime('%d %B %Y - %H:%M') if bon_result.declined_at else '',
            'decline_reason': bon_result.decline_reason or '',
            'declined_by': bon_result.declined_by or ''
        }
        
        return jsonify({
            'success': True,
            'data': bon_data,
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        app.logger.error(f"Error in check_detail_bon: {str(e)}")
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/check-detail-adjustment/<int:adjustment_id>')
def check_detail_adjustment(adjustment_id):
    """API endpoint for auto-refresh to get latest adjustment data"""
    try:
        # Query the adjustment request using Session.get() to avoid legacy warning
        adjustment = db.session.get(PlateAdjustmentRequest, adjustment_id)
        if not adjustment:
            return jsonify({'success': False, 'message': f'Adjustment ID {adjustment_id} tidak ditemukan.'}), 404

        # Format all datetime fields to Indonesian format
        data = {
            'id': adjustment.id,
            'status': adjustment.status,
            'tanggal': format_tanggal_indonesia(adjustment.tanggal) if adjustment.tanggal else '',
            'mesin_cetak': adjustment.mesin_cetak or '',
            'pic': adjustment.pic or '',
            'remarks': adjustment.remarks or '',
            'item_name': adjustment.item_name or '',
            'wo_number': adjustment.wo_number or '',
            'mc_number': adjustment.mc_number or '',
            'jumlah_plate': adjustment.jumlah_plate or 0,
            'run_length': adjustment.run_length or 0,
            'note': adjustment.note or '',
            'is_epson': adjustment.is_epson or False,
            
            # Timeline fields with Indonesian formatting
            'machine_off_at': format_datetime_indonesia(adjustment.machine_off_at) if adjustment.machine_off_at else '',
            'design_start_at': format_datetime_indonesia(adjustment.design_start_at) if adjustment.design_start_at else '',
            'design_finish_at': format_datetime_indonesia(adjustment.design_finish_at) if adjustment.design_finish_at else '',
            'pdnd_start_at': format_datetime_indonesia(adjustment.pdnd_start_at) if adjustment.pdnd_start_at else '',
            'pdnd_finish_at': format_datetime_indonesia(adjustment.pdnd_finish_at) if adjustment.pdnd_finish_at else '',
            'curve_start_at': format_datetime_indonesia(adjustment.curve_start_at) if adjustment.curve_start_at else '',
            'curve_finish_at': format_datetime_indonesia(adjustment.curve_finish_at) if adjustment.curve_finish_at else '',
            'adjustment_start_at': format_datetime_indonesia(adjustment.adjustment_start_at) if adjustment.adjustment_start_at else '',
            'adjustment_finish_at': format_datetime_indonesia(adjustment.adjustment_finish_at) if adjustment.adjustment_finish_at else '',
            'plate_start_at': format_datetime_indonesia(adjustment.plate_start_at) if adjustment.plate_start_at else '',
            'plate_finish_at': format_datetime_indonesia(adjustment.plate_finish_at) if adjustment.plate_finish_at else '',
            'plate_delivered_at': format_datetime_indonesia(adjustment.plate_delivered_at) if adjustment.plate_delivered_at else '',
            
            # PIC fields
            'design_by': adjustment.design_by or '',
            'pdnd_by': adjustment.pdnd_by or '',
            'curve_by': adjustment.curve_by or '',
            'adjustment_by': adjustment.adjustment_by or '',
            'ctp_by': adjustment.ctp_by or '',
            
            # Cancellation/Decline fields
            'cancelled_at': format_datetime_indonesia(adjustment.cancelled_at) if adjustment.cancelled_at else '',
            'cancelled_by': adjustment.cancelled_by or '',
            'cancellation_reason': adjustment.cancellation_reason or '',
            'declined_at': format_datetime_indonesia(adjustment.declined_at) if adjustment.declined_at else '',
            'declined_by': adjustment.declined_by or '',
            'decline_reason': adjustment.decline_reason or ''
        }
        
        return jsonify({'success': True, 'data': data})
        
    except Exception as e:
        print(f"Error in check_detail_adjustment: {str(e)}")
        return jsonify({'success': False, 'message': f'Error: {str(e)}'}), 500

@app.route('/api/current-user-role', methods=['GET'])
@login_required
def get_current_user_role():
    """Get current user role information"""
    try:
        return jsonify({
            'success': True,
            'role': current_user.role
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/notifications')
@login_required
def notifications_page():
    """Render the notifications page for viewing all notifications"""
    return render_template('notifications.html')

if __name__ == '__main__':
    # Initialize CTP machines
    initialize_ctp_machines()
    
    # x_for=1: Menerima X-Forwarded-For (IP Klien)
    # x_prefix=1: Menerima X-Forwarded-Prefix (Path /impact) <--- INI PENTING
    # x_host=1: Menerima X-Forwarded-Host (Nama host/IP)
    
    # PENTING: Gunakan konfigurasi ini untuk memastikan semua header proxy dibaca
    app.wsgi_app = ProxyFix(
        app.wsgi_app,
        x_for=1,
        x_proto=1,
        x_host=1,
        x_port=1,
        x_prefix=1 # <--- PASTIKAN INI ADA
    )
    
    # Jalankan aplikasi Anda di port 5021
    # Route to serve uploaded files from network drive or local instance
    @app.route('/uploads/<path:filename>')
    def serve_uploaded_file(filename):
        return send_from_directory(app.config['UPLOADS_PATH'], filename)
    
    app.run(host='0.0.0.0', port=5021, debug=True)
