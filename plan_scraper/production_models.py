# Production Models for Create Work Order functionality
from datetime import datetime
from flask_sqlalchemy import SQLAlchemy
import pytz

# Timezone untuk Jakarta
jakarta_tz = pytz.timezone('Asia/Jakarta')

# Get db instance from app.py to avoid circular imports
def get_db():
    from app import db
    return db

# Get db instance for model definition
db = get_db()

class ProductionCustomerName(db.Model):
    """Model for production customer names"""
    __tablename__ = 'production_customer_name'
    __table_args__ = {'extend_existing': True}
    
    id = db.Column(db.Integer, primary_key=True)
    customer_name = db.Column(db.String(255), nullable=False)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(jakarta_tz))
    updated_at = db.Column(db.DateTime, default=lambda: datetime.now(jakarta_tz), onupdate=lambda: datetime.now(jakarta_tz))
    
    def __repr__(self):
        return f'<ProductionCustomerName {self.customer_name}>'
    
    def to_dict(self):
        """Convert model to dictionary for JSON serialization"""
        return {
            'id': self.id,
            'customer_name': self.customer_name,
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M:%S') if self.created_at else None,
            'updated_at': self.updated_at.strftime('%Y-%m-%d %H:%M:%S') if self.updated_at else None
        }

class ProductionImpositionCockpit(db.Model):
    """Model for production imposition cockpit"""
    __tablename__ = 'production_imposition_cockpit'
    __table_args__ = {'extend_existing': True}
    
    id = db.Column(db.Integer, primary_key=True)
    imposition_cockpit = db.Column(db.String(50), nullable=False)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(jakarta_tz))
    updated_at = db.Column(db.DateTime, default=lambda: datetime.now(jakarta_tz), onupdate=lambda: datetime.now(jakarta_tz))
    
    def __repr__(self):
        return f'<ProductionImpositionCockpit {self.imposition_cockpit}>'
    
    def to_dict(self):
        """Convert model to dictionary for JSON serialization"""
        return {
            'id': self.id,
            'imposition_cockpit': self.imposition_cockpit,
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M:%S') if self.created_at else None,
            'updated_at': self.updated_at.strftime('%Y-%m-%d %H:%M:%S') if self.updated_at else None
        }

# CalibrationReference is already defined in models.py, we'll use that instead

class ProductionImpositionRemarks(db.Model):
    """Model for production imposition remarks"""
    __tablename__ = 'production_imposition_remarks'
    __table_args__ = {'extend_existing': True}
    
    id = db.Column(db.Integer, primary_key=True)
    imposition_remarks = db.Column(db.String(100), nullable=False)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(jakarta_tz))
    updated_at = db.Column(db.DateTime, default=lambda: datetime.now(jakarta_tz), onupdate=lambda: datetime.now(jakarta_tz))
    
    def __repr__(self):
        return f'<ProductionImpositionRemarks {self.imposition_remarks}>'
    
    def to_dict(self):
        """Convert model to dictionary for JSON serialization"""
        return {
            'id': self.id,
            'imposition_remarks': self.imposition_remarks,
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M:%S') if self.created_at else None,
            'updated_at': self.updated_at.strftime('%Y-%m-%d %H:%M:%S') if self.updated_at else None
        }

class ProductionPrintMachine(db.Model):
    """Model for production print machines"""
    __tablename__ = 'production_print_machine'
    __table_args__ = {'extend_existing': True}
    
    id = db.Column(db.Integer, primary_key=True)
    print_machine = db.Column(db.String(50), nullable=False)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(jakarta_tz))
    updated_at = db.Column(db.DateTime, default=lambda: datetime.now(jakarta_tz), onupdate=lambda: datetime.now(jakarta_tz))
    
    def __repr__(self):
        return f'<ProductionPrintMachine {self.print_machine}>'
    
    def to_dict(self):
        """Convert model to dictionary for JSON serialization"""
        return {
            'id': self.id,
            'print_machine': self.print_machine,
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M:%S') if self.created_at else None,
            'updated_at': self.updated_at.strftime('%Y-%m-%d %H:%M:%S') if self.updated_at else None
        }

class ProductionImpositionJob(db.Model):
    """Model for production imposition jobs created from Work Queue"""
    __tablename__ = 'production_imposition_jobs'
    __table_args__ = {'extend_existing': True}
    
    id = db.Column(db.Integer, primary_key=True)
    
    # Basic Information
    tanggal = db.Column(db.Date, nullable=False)
    pic = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    grup = db.Column(db.String(100), nullable=False)
    shift = db.Column(db.Enum('Shift 1', 'Shift 2', 'Shift 3'), nullable=False)
    
    # Work Order Information (from Work Queue)
    customer_name = db.Column(db.String(255), nullable=False)
    wo_number = db.Column(db.String(100), nullable=False)
    mc_number = db.Column(db.String(100), nullable=False)
    item_name = db.Column(db.String(255), nullable=False)
    up = db.Column(db.Integer, nullable=False)
    
    # Paper Information
    paper_desc = db.Column(db.String(255), nullable=True)
    paper_type = db.Column(db.String(100), nullable=True)
    paper_size = db.Column(db.String(100), nullable=True)
    
    # File Information
    file_name = db.Column(db.String(255), nullable=True)
    print_block = db.Column(db.String(100), nullable=True)
    
    # Production Information
    print_machine = db.Column(db.String(50), nullable=False)
    cockpit = db.Column(db.String(100), nullable=True)
    tiff_b_usage = db.Column(db.String(50), nullable=True)
    calibration_name = db.Column(db.String(255), nullable=True)
    
    # Additional Information
    remarks = db.Column(db.Text, nullable=True)
    status = db.Column(db.Enum('active', 'completed', 'cancelled'), default='active')
    
    # Foreign Keys
    customer_id = db.Column(db.Integer, db.ForeignKey('production_customer_name.id'), nullable=True)
    cockpit_id = db.Column(db.Integer, db.ForeignKey('production_imposition_cockpit.id'), nullable=True)
    calibration_id = db.Column(db.BigInteger, db.ForeignKey('calibration_references.id'), nullable=True)
    remarks_id = db.Column(db.Integer, db.ForeignKey('production_imposition_remarks.id'), nullable=True)
    
    # Work Queue Reference
    work_queue_id = db.Column(db.Integer, db.ForeignKey('work_queue.id'), nullable=True)
    plan_scraper_data_id = db.Column(db.Integer, db.ForeignKey('plan_scraper_data.id'), nullable=True)
    
    # Job lifecycle tracking
    started_at = db.Column(db.DateTime, nullable=True)
    started_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    completed_at = db.Column(db.DateTime, nullable=True)
    completed_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    updated_at = db.Column(db.DateTime, default=lambda: datetime.now(jakarta_tz), onupdate=lambda: datetime.now(jakarta_tz))
    
    # Relationships
    customer = db.relationship('ProductionCustomerName', backref='production_jobs')
    cockpit_rel = db.relationship('ProductionImpositionCockpit', backref='production_jobs')
    calibration = db.relationship('CalibrationReference', backref='production_jobs')
    remarks_rel = db.relationship('ProductionImpositionRemarks', backref='production_jobs')
    work_queue = db.relationship('WorkQueue', backref='production_jobs')
    plan_data = db.relationship('PlanScraperData', backref='production_jobs')
    user = db.relationship('User', backref='production_jobs_pic', foreign_keys=[pic])
    started_user = db.relationship('User', backref='production_jobs_started', foreign_keys=[started_by])
    completed_user = db.relationship('User', backref='production_jobs_completed', foreign_keys=[completed_by])
    
    def __repr__(self):
        return f'<ProductionImpositionJob {self.wo_number} - {self.mc_number}>'
    
    def to_dict(self):
        """Convert model to dictionary for JSON serialization"""
        return {
            'id': self.id,
            'tanggal': self.tanggal.strftime('%Y-%m-%d') if self.tanggal else None,
            'pic': self.pic,
            'pic_name': self.user.name if self.user else None,
            'grup': self.grup,
            'shift': self.shift,
            'customer_name': self.customer_name,
            'wo_number': self.wo_number,
            'mc_number': self.mc_number,
            'item_name': self.item_name,
            'up': self.up,
            'paper_desc': self.paper_desc,
            'paper_type': self.paper_type,
            'paper_size': self.paper_size,
            'file_name': self.file_name,
            'print_block': self.print_block,
            'print_machine': self.print_machine,
            'cockpit': self.cockpit,
            'tiff_b_usage': self.tiff_b_usage,
            'calibration_name': self.calibration_name,
            'remarks': self.remarks,
            'status': self.status,
            'customer_id': self.customer_id,
            'cockpit_id': self.cockpit_id,
            'calibration_id': self.calibration_id,
            'remarks_id': self.remarks_id,
            'work_queue_id': self.work_queue_id,
            'plan_scraper_data_id': self.plan_scraper_data_id,
            'started_at': self.started_at.strftime('%Y-%m-%d %H:%M:%S') if self.started_at else None,
            'started_by': self.started_by,
            'started_user_name': self.started_user.name if self.started_user else None,
            'completed_at': self.completed_at.strftime('%Y-%m-%d %H:%M:%S') if self.completed_at else None,
            'completed_by': self.completed_by,
            'completed_user_name': self.completed_user.name if self.completed_user else None,
            'updated_at': self.updated_at.strftime('%Y-%m-%d %H:%M:%S') if self.updated_at else None
        }