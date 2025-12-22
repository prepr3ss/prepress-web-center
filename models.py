from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, time, timedelta
import pytz
from sqlalchemy import func, and_, or_
from plate_mappings import PlateTypeMapping

# SQLAlchemy instance will be provided by app.py
# app.py should do: `from models import db, Division, User, ...`

db = SQLAlchemy()

jakarta_tz = pytz.timezone('Asia/Jakarta')


# Definisi Model Database untuk User Authentication
class Division(db.Model):
    __tablename__ = 'divisions'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False, unique=True)
    description = db.Column(db.String(255), nullable=True)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(jakarta_tz))
    
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
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(jakarta_tz))
    updated_at = db.Column(db.DateTime, default=lambda: datetime.now(jakarta_tz), onupdate=lambda: datetime.now(jakarta_tz))

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
    
    def can_access_rnd(self):
        """Check if user can access R&D production"""
        return self.can_access_division('RND')
        
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
    paper_type = db.Column(db.String(100), nullable=False)    
    raster = db.Column(db.String(50), nullable=False)
    num_plate_good = db.Column(db.Integer)
    num_plate_not_good = db.Column(db.Integer)
    not_good_reason = db.Column(db.String(255))
    detail_not_good = db.Column(db.Text)
    cyan_20_percent = db.Column(db.Float)
    cyan_25_percent = db.Column(db.Float)
    cyan_40_percent = db.Column(db.Float)
    cyan_50_percent = db.Column(db.Float)
    cyan_80_percent = db.Column(db.Float)
    cyan_75_percent = db.Column(db.Float)
    cyan_linear = db.Column(db.Float)
    magenta_20_percent = db.Column(db.Float)
    magenta_25_percent = db.Column(db.Float)
    magenta_40_percent = db.Column(db.Float)
    magenta_50_percent = db.Column(db.Float)
    magenta_80_percent = db.Column(db.Float)
    magenta_75_percent = db.Column(db.Float)
    magenta_linear = db.Column(db.Float)
    yellow_20_percent = db.Column(db.Float)
    yellow_25_percent = db.Column(db.Float)
    yellow_40_percent = db.Column(db.Float)
    yellow_50_percent = db.Column(db.Float)
    yellow_80_percent = db.Column(db.Float)
    yellow_75_percent = db.Column(db.Float)
    yellow_linear = db.Column(db.Float)
    black_20_percent = db.Column(db.Float)
    black_25_percent = db.Column(db.Float)
    black_40_percent = db.Column(db.Float)
    black_50_percent = db.Column(db.Float)
    black_80_percent = db.Column(db.Float)
    black_75_percent = db.Column(db.Float)
    black_linear = db.Column(db.Float)
    x_20_percent = db.Column(db.Float)
    x_25_percent = db.Column(db.Float)
    x_40_percent = db.Column(db.Float)
    x_50_percent = db.Column(db.Float)
    x_80_percent = db.Column(db.Float)
    x_75_percent = db.Column(db.Float)
    x_linear = db.Column(db.Float)
    z_20_percent = db.Column(db.Float)
    z_25_percent = db.Column(db.Float)
    z_40_percent = db.Column(db.Float)
    z_50_percent = db.Column(db.Float)
    z_80_percent = db.Column(db.Float)
    z_75_percent = db.Column(db.Float)
    z_linear = db.Column(db.Float)
    u_20_percent = db.Column(db.Float)
    u_25_percent = db.Column(db.Float)
    u_40_percent = db.Column(db.Float)
    u_50_percent = db.Column(db.Float)
    u_80_percent = db.Column(db.Float)
    u_75_percent = db.Column(db.Float)
    u_linear = db.Column(db.Float)
    v_20_percent = db.Column(db.Float)
    v_25_percent = db.Column(db.Float)
    v_40_percent = db.Column(db.Float)
    v_50_percent = db.Column(db.Float)
    v_80_percent = db.Column(db.Float)
    v_75_percent = db.Column(db.Float)
    v_linear = db.Column(db.Float)
    f_20_percent = db.Column(db.Float)
    f_25_percent = db.Column(db.Float)
    f_40_percent = db.Column(db.Float)
    f_50_percent = db.Column(db.Float)
    f_80_percent = db.Column(db.Float)
    f_75_percent = db.Column(db.Float)
    f_linear = db.Column(db.Float)
    g_20_percent = db.Column(db.Float)
    g_25_percent = db.Column(db.Float)
    g_40_percent = db.Column(db.Float)
    g_50_percent = db.Column(db.Float)
    g_80_percent = db.Column(db.Float)
    g_75_percent = db.Column(db.Float)
    g_linear = db.Column(db.Float)
    h_20_percent = db.Column(db.Float)
    h_25_percent = db.Column(db.Float)
    h_40_percent = db.Column(db.Float)
    h_50_percent = db.Column(db.Float)
    h_80_percent = db.Column(db.Float)
    h_75_percent = db.Column(db.Float)
    h_linear = db.Column(db.Float)
    j_20_percent = db.Column(db.Float)
    j_25_percent = db.Column(db.Float)
    j_40_percent = db.Column(db.Float)
    j_50_percent = db.Column(db.Float)
    j_80_percent = db.Column(db.Float)
    j_75_percent = db.Column(db.Float)
    j_linear = db.Column(db.Float)
    start_time = db.Column(db.Time)   # UBAH INI: dari db.String menjadi db.Time
    finish_time = db.Column(db.Time)  # UBAH INI: dari db.String menjadi db.Time
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(jakarta_tz))
    updated_at = db.Column(db.DateTime, default=lambda: datetime.now(jakarta_tz), onupdate=lambda: datetime.now(jakarta_tz))

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
            'paper_type': self.paper_type,
            'raster': self.raster,
            'num_plate_good': self.num_plate_good,
            'num_plate_not_good': self.num_plate_not_good,
            'not_good_reason': self.not_good_reason,
            'detail_not_good': self.detail_not_good,
            'cyan_20_percent': self.cyan_20_percent,
            'cyan_25_percent': self.cyan_25_percent,
            'cyan_40_percent': self.cyan_40_percent,
            'cyan_50_percent': self.cyan_50_percent,
            'cyan_80_percent': self.cyan_80_percent,
            'cyan_75_percent': self.cyan_75_percent,
            'cyan_linear': self.cyan_linear,
            'magenta_20_percent': self.magenta_20_percent,
            'magenta_25_percent': self.magenta_25_percent,
            'magenta_40_percent': self.magenta_40_percent,
            'magenta_50_percent': self.magenta_50_percent,
            'magenta_80_percent': self.magenta_80_percent,
            'magenta_75_percent': self.magenta_75_percent,
            'magenta_linear': self.magenta_linear,
            'yellow_20_percent': self.yellow_20_percent,
            'yellow_25_percent': self.yellow_25_percent,
            'yellow_40_percent': self.yellow_40_percent,
            'yellow_50_percent': self.yellow_50_percent,
            'yellow_80_percent': self.yellow_80_percent,
            'yellow_75_percent': self.yellow_75_percent,
            'yellow_linear': self.yellow_linear,
            'black_20_percent': self.black_20_percent,
            'black_25_percent': self.black_25_percent,
            'black_40_percent': self.black_40_percent,
            'black_50_percent': self.black_50_percent,
            'black_80_percent': self.black_80_percent,
            'black_75_percent': self.black_75_percent,
            'black_linear': self.black_linear,
            'x_20_percent': self.x_20_percent,
            'x_25_percent': self.x_25_percent,
            'x_40_percent': self.x_40_percent,
            'x_50_percent': self.x_50_percent,
            'x_80_percent': self.x_80_percent,
            'x_75_percent': self.x_75_percent,
            'x_linear': self.x_linear,
            'z_20_percent': self.z_20_percent,
            'z_25_percent': self.z_25_percent,
            'z_40_percent': self.z_40_percent,
            'z_50_percent': self.z_50_percent,
            'z_80_percent': self.z_80_percent,
            'z_75_percent': self.z_75_percent,
            'z_linear': self.z_linear,
            'u_20_percent': self.u_20_percent,
            'u_25_percent': self.u_25_percent,
            'u_40_percent': self.u_40_percent,
            'u_50_percent': self.u_50_percent,
            'u_80_percent': self.u_80_percent,
            'u_75_percent': self.u_75_percent,
            'u_linear': self.u_linear,
            'v_20_percent': self.v_20_percent,
            'v_25_percent': self.v_25_percent,
            'v_40_percent': self.v_40_percent,
            'v_50_percent': self.v_50_percent,
            'v_80_percent': self.v_80_percent,
            'v_75_percent': self.v_75_percent,
            'v_linear': self.v_linear,
            'f_20_percent': self.f_20_percent,
            'f_25_percent': self.f_25_percent,
            'f_40_percent': self.f_40_percent,
            'f_50_percent': self.f_50_percent,
            'f_80_percent': self.f_80_percent,
            'f_75_percent': self.f_75_percent,
            'f_linear': self.f_linear,
            'g_20_percent': self.g_20_percent,
            'g_25_percent': self.g_25_percent,
            'g_40_percent': self.g_40_percent,
            'g_50_percent': self.g_50_percent,
            'g_80_percent': self.g_80_percent,
            'g_75_percent': self.g_75_percent,
            'g_linear': self.g_linear,
            'h_20_percent': self.h_20_percent,
            'h_25_percent': self.h_25_percent,
            'h_40_percent': self.h_40_percent,
            'h_50_percent': self.h_50_percent,
            'h_80_percent': self.h_80_percent,
            'h_75_percent': self.h_75_percent,
            'h_linear': self.h_linear,
            'j_20_percent': self.j_20_percent,
            'j_25_percent': self.j_25_percent,
            'j_40_percent': self.j_40_percent,
            'j_50_percent': self.j_50_percent,
            'j_80_percent': self.j_80_percent,
            'j_75_percent': self.j_75_percent,
            'j_linear': self.j_linear,
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
    paper_type = db.Column(db.String(100), nullable=False)  # Kolom baru untuk jenis kertas
    ctp_group = db.Column(db.String(50), nullable=True)  # Kolom baru untuk grup CTP
    jumlah_plate = db.Column(db.Integer, nullable=False)
    note = db.Column(db.String(255), nullable=True)

    machine_off_at = db.Column(db.DateTime, default=datetime.utcnow)

    is_epson = db.Column(db.Boolean, default=False)

    pdnd_start_at = db.Column(db.DateTime, nullable=True)
    pdnd_finish_at = db.Column(db.DateTime, nullable=True)
    pdnd_by = db.Column(db.String(100), nullable=True)

    curve_start_at = db.Column(db.DateTime, nullable=True)
    curve_finish_at = db.Column(db.DateTime, nullable=True)
    curve_by = db.Column(db.String(100), nullable=True)

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
            self.status = 'menunggu_adjustment_curve' 
            
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
            'paper_type': self.paper_type,
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
            'curve_start_at': self.curve_start_at.isoformat() if self.curve_start_at else None,
            'curve_finish_at': self.curve_finish_at.isoformat() if self.curve_finish_at else None,
            'curve_by': self.curve_by,
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
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(jakarta_tz))
    updated_at = db.Column(db.DateTime, default=lambda: datetime.now(jakarta_tz), onupdate=lambda: datetime.now(jakarta_tz))

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
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(jakarta_tz))
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
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(jakarta_tz))
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
    paper_type = db.Column(db.String(100), nullable=False)  # Kolom baru untuk jenis kertas
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

# --- CTP Log Models ---
class CTPMachine(db.Model):
    __tablename__ = 'ctp_machines'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False, unique=True)  # CTP 1 Suprasetter, CTP 2 Platesetter, CTP 3 Trendsetter
    nickname = db.Column(db.String(50), nullable=False)  # CTP 1, CTP 2, CTP 3
    status = db.Column(db.String(20), nullable=False, default='active')  # active, maintenance
    description = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(jakarta_tz))
    updated_at = db.Column(db.DateTime, default=lambda: datetime.now(jakarta_tz), onupdate=lambda: datetime.now(jakarta_tz))
    
    # Relationships
    problem_logs = db.relationship('CTPProblemLog', backref='machine', lazy=True, cascade='all, delete-orphan')
    notifications = db.relationship('CTPNotification', backref='machine', lazy=True, cascade='all, delete-orphan')

class CTPProblemLog(db.Model):
    __tablename__ = 'ctp_problem_logs'
    
    id = db.Column(db.Integer, primary_key=True)
    machine_id = db.Column(db.Integer, db.ForeignKey('ctp_machines.id'), nullable=False)
    
    # Informasi Problem
    problem_date = db.Column(db.DateTime, nullable=False, default=lambda: datetime.now(jakarta_tz))
    error_code = db.Column(db.String(25), nullable=True)
    problem_description = db.Column(db.Text, nullable=False)
    problem_photo = db.Column(db.String(255), nullable=True)  # Path ke foto
    
    # Informasi Solusi
    solution = db.Column(db.Text, nullable=True)
    technician_type = db.Column(db.String(20), nullable=False)  # lokal, vendor
    technician_name = db.Column(db.String(100), nullable=True)
    
    # Waktu untuk perhitungan downtime
    start_time = db.Column(db.DateTime, nullable=False)
    end_time = db.Column(db.DateTime, nullable=True)
    
    # Status
    status = db.Column(db.String(20), nullable=False, default='ongoing')  # ongoing, completed
    
    # Metadata
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(jakarta_tz))
    updated_at = db.Column(db.DateTime, default=lambda: datetime.now(jakarta_tz), onupdate=lambda: datetime.now(jakarta_tz))
    
    # Relationships
    notifications = db.relationship('CTPNotification', backref='problem_log', lazy=True, cascade='all, delete-orphan')
    creator = db.relationship('User', foreign_keys=[created_by], backref=db.backref('created_problem_logs', lazy='dynamic'))
    
    # Property untuk menghitung downtime
    @property
    def downtime_hours(self):
        """
        Hitung downtime dalam jam menggunakan timezone Asia/Jakarta secara konsisten.
        """
        # Pastikan kita punya start_time yang valid
        if not self.start_time:
            return 0

        # Normalisasi start_time ke aware datetime di Asia/Jakarta
        if self.start_time.tzinfo is None:
            start_aware = jakarta_tz.localize(self.start_time)
        else:
            start_aware = self.start_time.astimezone(jakarta_tz)

        # Jika sudah ada end_time, gunakan itu
        if self.end_time:
            if self.end_time.tzinfo is None:
                end_aware = jakarta_tz.localize(self.end_time)
            else:
                end_aware = self.end_time.astimezone(jakarta_tz)
        # Jika status ongoing, gunakan waktu sekarang di Jakarta
        elif self.status == 'ongoing':
            end_aware = datetime.now(jakarta_tz)
        else:
            return 0

        delta = end_aware - start_aware
        return delta.total_seconds() / 3600.0

class CTPProblemPhoto(db.Model):
    __tablename__ = 'ctp_problem_photos'
    
    id = db.Column(db.Integer, primary_key=True)
    problem_log_id = db.Column(db.Integer, db.ForeignKey('ctp_problem_logs.id'), nullable=False)
    filename = db.Column(db.String(255), nullable=False)
    file_path = db.Column(db.String(500), nullable=False)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(jakarta_tz))
    
    # Relationship
    problem_log = db.relationship('CTPProblemLog', backref=db.backref('photos', lazy=True, cascade='all, delete-orphan'))

class CTPProblemDocument(db.Model):
    __tablename__ = 'ctp_problem_documents'
    
    id = db.Column(db.Integer, primary_key=True)
    problem_log_id = db.Column(db.Integer, db.ForeignKey('ctp_problem_logs.id'), nullable=False)
    filename = db.Column(db.String(255), nullable=False)
    file_path = db.Column(db.String(500), nullable=False)
    file_type = db.Column(db.String(50), nullable=False)  # 'pdf' or 'docx'
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(jakarta_tz))
    
    # Relationship
    problem_log = db.relationship('CTPProblemLog', backref=db.backref('documents', lazy=True, cascade='all, delete-orphan'))

class CTPNotification(db.Model):
    __tablename__ = 'ctp_notifications'
    
    id = db.Column(db.Integer, primary_key=True)
    machine_id = db.Column(db.Integer, db.ForeignKey('ctp_machines.id'), nullable=False)
    log_id = db.Column(db.Integer, db.ForeignKey('ctp_problem_logs.id'), nullable=False)
    
    notification_type = db.Column(db.String(50), nullable=False)  # new_problem, problem_resolved
    message = db.Column(db.Text, nullable=False)
    is_read = db.Column(db.Boolean, default=False)
    
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(jakarta_tz))
    read_at = db.Column(db.DateTime, nullable=True)

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
            'paper_type': self.paper_type,
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

# --- Cloudsphere Task Management System Models ---

class TaskCategory(db.Model):
    """Model for task categories in Cloudsphere system"""
    __tablename__ = 'task_categories'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False, unique=True)  # Blank, RoHS, Mastercard, Production
    description = db.Column(db.String(255), nullable=True)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(jakarta_tz))
    
    # Relationship with tasks
    tasks = db.relationship('Task', backref='category', lazy=True, cascade='all, delete-orphan')
    
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

class Task(db.Model):
    """Model for individual tasks in Cloudsphere system"""
    __tablename__ = 'tasks'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    category_id = db.Column(db.Integer, db.ForeignKey('task_categories.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(jakarta_tz))
    
    # Relationship with job progress
    job_progress_tasks = db.relationship('JobProgressTask', backref='task', lazy=True, cascade='all, delete-orphan')
    
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'category_id': self.category_id,
            'category_name': self.category.name if self.category else None,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

class CloudsphereJob(db.Model):
    """Model for jobs in Cloudsphere system"""
    __tablename__ = 'cloudsphere_jobs'
    
    id = db.Column(db.Integer, primary_key=True)
    job_id = db.Column(db.String(20), nullable=False, unique=True)  # Auto-generated job ID
    start_datetime = db.Column(db.DateTime, nullable=False)
    deadline = db.Column(db.DateTime, nullable=False)
    pic_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    sample_type = db.Column(db.String(20), nullable=False)  # RoHS, Blank, Mastercard
    item_name = db.Column(db.String(255), nullable=False)
    priority_level = db.Column(db.String(10), nullable=False, default='Middle')  # Low, Middle, High
    status = db.Column(db.String(20), nullable=False, default='In Progress')  # In Progress, Completed, Rejected, Approved, Pending Approval
    notes = db.Column(db.Text, nullable=True)
    rejection_notes = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(jakarta_tz))
    updated_at = db.Column(db.DateTime, default=lambda: datetime.now(jakarta_tz), onupdate=lambda: datetime.now(jakarta_tz))
    
    # Relationships
    pic = db.relationship('User', backref=db.backref('cloudsphere_jobs', lazy=True))
    job_tasks = db.relationship('JobTask', backref='job', lazy=True, cascade='all, delete-orphan')
    job_progress = db.relationship('JobProgress', backref='job', lazy=True, uselist=False, cascade='all, delete-orphan')
    evidence_files = db.relationship('EvidenceFile', backref='job', cascade='all, delete-orphan', lazy='dynamic')
    
    def to_dict(self):
        return {
            'id': self.id,
            'job_id': self.job_id,
            'start_datetime': self.start_datetime.isoformat() if self.start_datetime else None,
            'deadline': self.deadline.isoformat() if self.deadline else None,
            'pic_id': self.pic_id,
            'pic_name': self.pic.name if self.pic else None,
            'sample_type': self.sample_type,
            'item_name': self.item_name,
            'priority_level': self.priority_level,
            'status': self.status,
            'notes': self.notes,
            'rejection_notes': self.rejection_notes,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'completion_percentage': self.completion_percentage,
            'latest_completed_task': self.latest_completed_task
        }
    
    @property
    def completion_percentage(self):
        """Calculate completion percentage based on tasks"""
        if not self.job_progress:
            return 0
        return self.job_progress.completion_percentage
    
    @property
    def latest_completed_task(self):
        """Get the latest completed task name"""
        if not self.job_progress:
            return None
        latest_task = JobProgressTask.query.filter_by(
            job_progress_id=self.job_progress.id,
            completed=True
        ).order_by(JobProgressTask.completed_at.desc()).first()
        return latest_task.task.name if latest_task else None

class JobTask(db.Model):
    """Model for tasks assigned to a job"""
    __tablename__ = 'job_tasks'
    
    id = db.Column(db.Integer, primary_key=True)
    job_id = db.Column(db.Integer, db.ForeignKey('cloudsphere_jobs.id'), nullable=False)
    task_id = db.Column(db.Integer, db.ForeignKey('tasks.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(jakarta_tz))
    
    # Relationship with task
    task = db.relationship('Task', backref='job_tasks')
    
    def to_dict(self):
        return {
            'id': self.id,
            'job_id': self.job_id,
            'task_id': self.task_id,
            'task_name': self.task.name if self.task else None,
            'category_name': self.task.category.name if self.task and self.task.category else None,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

class JobProgress(db.Model):
    """Model for tracking job progress"""
    __tablename__ = 'job_progress'
    
    id = db.Column(db.Integer, primary_key=True)
    job_id = db.Column(db.Integer, db.ForeignKey('cloudsphere_jobs.id'), nullable=False, unique=True)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(jakarta_tz))
    updated_at = db.Column(db.DateTime, default=lambda: datetime.now(jakarta_tz), onupdate=lambda: datetime.now(jakarta_tz))
    
    # Relationship with progress tasks
    progress_tasks = db.relationship('JobProgressTask', backref='job_progress', lazy=True, cascade='all, delete-orphan')
    
    def to_dict(self):
        return {
            'id': self.id,
            'job_id': self.job_id,
            'completion_percentage': self.completion_percentage,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
    
    @property
    def completion_percentage(self):
        """Calculate completion percentage"""
        if not self.progress_tasks:
            return 0
        total_tasks = len(self.progress_tasks)
        completed_tasks = len([pt for pt in self.progress_tasks if pt.completed])
        return round((completed_tasks / total_tasks) * 100, 2) if total_tasks > 0 else 0

class JobProgressTask(db.Model):
    """Model for tracking individual task progress within a job"""
    __tablename__ = 'job_progress_tasks'
    
    id = db.Column(db.Integer, primary_key=True)
    job_progress_id = db.Column(db.Integer, db.ForeignKey('job_progress.id'), nullable=False)
    task_id = db.Column(db.Integer, db.ForeignKey('tasks.id'), nullable=False)
    completed = db.Column(db.Boolean, default=False)
    # Alias for backward compatibility
    @property
    def is_completed(self):
        return self.completed
    completed_at = db.Column(db.DateTime, nullable=True)
    notes = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(jakarta_tz))
    updated_at = db.Column(db.DateTime, default=lambda: datetime.now(jakarta_tz), onupdate=lambda: datetime.now(jakarta_tz))
    
    def to_dict(self):
        return {
            'id': self.id,
            'job_progress_id': self.job_progress_id,
            'task_id': self.task_id,
            'task_name': self.task.name if self.task else None,
            'category_name': self.task.category.name if self.task and self.task.category else None,
            'completed': self.completed,
            'completed_at': self.completed_at.isoformat() if self.completed_at else None,
            'notes': self.notes,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }

class EvidenceFile(db.Model):
    """Model for evidence files attached to jobs"""
    __tablename__ = 'evidence_files'
    
    id = db.Column(db.Integer, primary_key=True)
    job_id = db.Column(db.Integer, db.ForeignKey('cloudsphere_jobs.id'), nullable=False)
    filename = db.Column(db.String(255), nullable=False)
    original_filename = db.Column(db.String(255), nullable=False)
    file_path = db.Column(db.String(500), nullable=False)
    file_type = db.Column(db.String(10), nullable=False)  # photo, pdf, docx, xlsx
    file_size = db.Column(db.Integer, nullable=False)  # in bytes
    uploaded_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    uploaded_at = db.Column(db.DateTime, default=lambda: datetime.now(jakarta_tz))
    
    # Relationship with user who uploaded
    uploader = db.relationship('User', backref=db.backref('uploaded_evidence_files', lazy=True))
    
    def to_dict(self):
        return {
            'id': self.id,
            'job_id': self.job_id,
            'filename': self.filename,
            'original_filename': self.original_filename,
            'file_path': self.file_path,
            'file_type': self.file_type,
            'file_size': self.file_size,
            'uploaded_by': self.uploaded_by,
            'uploader_name': self.uploader.name if self.uploader else None,
            'uploaded_at': self.uploaded_at.isoformat() if self.uploaded_at else None
        }
