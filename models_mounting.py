from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import pytz

# Import SQLAlchemy instance dari models.py atau create sendiri
# Karena db sudah didefinisikan di models.py, kita import dari sana
from models import db, jakarta_tz

class MountingWorkOrderIncoming(db.Model):
    __tablename__ = 'mounting_work_order_incoming'
    
    id = db.Column(db.Integer, primary_key=True)
    
    # Tanggal & Waktu incoming (default waktu saat ini di Jakarta)
    incoming_datetime = db.Column(db.DateTime, nullable=False, default=lambda: datetime.now(jakarta_tz))
    
    # Data Work Order dari PPIC
    wo_number = db.Column(db.String(50), nullable=False, unique=True)  # Nomor WO, harus unique
    mc_number = db.Column(db.String(50), nullable=False)                # Nomor MC
    customer_name = db.Column(db.String(100), nullable=False)           # Nama Customer
    item_name = db.Column(db.String(100), nullable=False)               # Nama Item
    
    # Data Print dan Mesin
    print_block = db.Column(db.String(50), nullable=False)             # Nomor MC, Mesin & Kertas
    print_machine = db.Column(db.String(100), nullable=False)          # Mesin Cetak
    run_length_sheet = db.Column(db.Integer, nullable=True)            # Run Length Sheet
    sheet_size = db.Column(db.String(50), nullable=True)               # Ukuran Kertas
    paper_type = db.Column(db.String(50), nullable=True)               # Jenis Kertas
    
    # Status tracking
    status = db.Column(db.String(20), nullable=False, default='incoming')  # incoming, processed, cancelled
    
    # Waktu pemrosesan
    processed_at = db.Column(db.DateTime, nullable=True)
    processed_by = db.Column(db.String(50), nullable=True)  # Nama user yang memproses
    
    # Timestamps
    created_at = db.Column(db.DateTime, nullable=False, default=lambda: datetime.now(jakarta_tz))
    updated_at = db.Column(db.DateTime, nullable=False, default=lambda: datetime.now(jakarta_tz), 
                          onupdate=lambda: datetime.now(jakarta_tz))
    created_by = db.Column(db.String(50), nullable=False)  # Nama user yang membuat
    
    # Indexes untuk performa query
    __table_args__ = (
        db.Index('idx_wo_incoming_datetime', 'incoming_datetime'),
        db.Index('idx_wo_status', 'status'),
        db.Index('idx_wo_number', 'wo_number'),
        db.Index('idx_mc_number', 'mc_number'),
        db.Index('idx_customer_name', 'customer_name'),
        db.Index('idx_created_at', 'created_at'),
    )
    
    def to_dict(self):
        """Convert model to dictionary for JSON response"""
        return {
            'id': self.id,
            'incoming_datetime': self.incoming_datetime.isoformat() if self.incoming_datetime else None,
            'wo_number': self.wo_number,
            'mc_number': self.mc_number,
            'customer_name': self.customer_name,
            'item_name': self.item_name,
            'print_block': self.print_block,
            'print_machine': self.print_machine,
            'run_length_sheet': self.run_length_sheet,
            'sheet_size': self.sheet_size,
            'paper_type': self.paper_type,
            'status': self.status,
            'processed_at': self.processed_at.isoformat() if self.processed_at else None,
            'processed_by': self.processed_by,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'created_by': self.created_by
        }
    
    def __repr__(self):
        return f"<MountingWorkOrderIncoming {self.wo_number} - {self.customer_name}>"
    
    @classmethod
    def validate_required_fields(cls, data):
        """Validate required fields for work order"""
        required_fields = ['wo_number', 'mc_number', 'customer_name', 'item_name', 
                          'print_block', 'print_machine']
        missing_fields = []
        
        for field in required_fields:
            if not data.get(field) or str(data[field]).strip() == '':
                missing_fields.append(field)
        
        return missing_fields
    
    @classmethod
    def create_from_dict(cls, data, created_by):
        """Create a new work order from dictionary data"""
        # Check for duplicates
        existing = cls.query.filter_by(wo_number=data['wo_number']).first()
        if existing:
            raise ValueError(f"Work order with WO Number {data['wo_number']} already exists")
        
        work_order = cls(
            wo_number=data['wo_number'],
            mc_number=data['mc_number'],
            customer_name=data['customer_name'],
            item_name=data['item_name'],
            print_block=data['print_block'],
            print_machine=data['print_machine'],
            run_length_sheet=data.get('run_length_sheet'),
            sheet_size=data.get('sheet_size'),
            paper_type=data.get('paper_type'),
            created_by=created_by
        )
        
        return work_order
    
    def update_status(self, new_status, processed_by=None):
        """Update work order status"""
        valid_statuses = ['incoming', 'processed', 'cancelled']
        
        if new_status not in valid_statuses:
            raise ValueError(f"Invalid status. Must be one of: {valid_statuses}")
        
        self.status = new_status
        
        if new_status == 'processed' and processed_by:
            self.processed_at = datetime.now(jakarta_tz)
            self.processed_by = processed_by
        
        return self


class MountingWorkOrderStats:
    """Helper class for work order statistics"""
    
    @staticmethod
    def get_today_count():
        """Get count of work orders created today"""
        today = datetime.now(jakarta_tz).date()
        return MountingWorkOrderIncoming.query.filter(
            db.func.date(MountingWorkOrderIncoming.created_at) == today
        ).count()
    
    @staticmethod
    def get_weekly_count():
        """Get count of work orders created this week"""
        today = datetime.now(jakarta_tz).date()
        start_of_week = today - timedelta(days=today.weekday())
        
        return MountingWorkOrderIncoming.query.filter(
            db.func.date(MountingWorkOrderIncoming.created_at) >= start_of_week
        ).count()
    
    @staticmethod
    def get_status_counts():
        """Get counts by status"""
        counts = {
            'incoming': 0,
            'processed': 0,
            'cancelled': 0,
            'total': 0
        }
        
        query = db.session.query(
            MountingWorkOrderIncoming.status,
            db.func.count(MountingWorkOrderIncoming.id)
        ).group_by(MountingWorkOrderIncoming.status).all()
        
        for status, count in query:
            counts[status] = count
            counts['total'] += count
        
        return counts
    
    @staticmethod
    def get_top_customers(limit=10):
        """Get top customers by work order count"""
        query = db.session.query(
            MountingWorkOrderIncoming.customer_name,
            db.func.count(MountingWorkOrderIncoming.id).label('count')
        ).group_by(MountingWorkOrderIncoming.customer_name) \
         .order_by(db.desc('count')) \
         .limit(limit).all()
        
        return [{'customer_name': customer, 'count': count} for customer, count in query]
    
    @staticmethod
    def get_top_machines(limit=10):
        """Get top print machines by work order count"""
        query = db.session.query(
            MountingWorkOrderIncoming.print_machine,
            db.func.count(MountingWorkOrderIncoming.id).label('count')
        ).group_by(MountingWorkOrderIncoming.print_machine) \
         .order_by(db.desc('count')) \
         .limit(limit).all()
        
        return [{'print_machine': machine, 'count': count} for machine, count in query]


# Import timedelta untuk statistics
from datetime import timedelta
