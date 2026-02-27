# Plan Scraper Models
from datetime import datetime
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import UniqueConstraint
import pytz

# Timezone untuk Jakarta
jakarta_tz = pytz.timezone('Asia/Jakarta')

# Get db instance from app.py to avoid circular imports
def get_db():
    from app import db
    return db

# Get db instance for model definition
db = get_db()

class PlanScraperData(db.Model):
    """Model for storing scraped plan data from Excel files"""
    __tablename__ = 'plan_scraper_data'
    
    id = db.Column(db.Integer, primary_key=True)
    print_machine = db.Column(db.String(50), nullable=False)  # SM2, SM3, SM4, SM5, SM6, VLF
    wo_number = db.Column(db.String(50), nullable=False)  # NO WO SAP - unique constraint
    mc_number = db.Column(db.String(50), nullable=False)  # NO MC SAP
    item_name = db.Column(db.String(255), nullable=False)  # Jenis Barang
    num_up = db.Column(db.Integer, nullable=False)  # Up
    run_length_sheet = db.Column(db.Float, nullable=False)  # Sheet - aggregated for duplicates
    paper_desc = db.Column(db.String(255), nullable=True)  # Keterangan
    paper_type = db.Column(db.String(100), nullable=True)  # Suplayer kertas
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(jakarta_tz))
    updated_at = db.Column(db.DateTime, default=lambda: datetime.now(jakarta_tz), onupdate=lambda: datetime.now(jakarta_tz))
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    
    # Add unique constraint on wo_number to prevent duplicates
    __table_args__ = (UniqueConstraint('wo_number', name='uq_plan_scraper_wo_number'),)
    
    # Relationship with User
    creator = db.relationship('User', backref='plan_scraper_entries', foreign_keys=[created_by])
    
    def to_dict(self):
        """Convert model to dictionary for JSON serialization"""
        return {
            'id': self.id,
            'print_machine': self.print_machine,
            'wo_number': self.wo_number,
            'mc_number': self.mc_number,
            'item_name': self.item_name,
            'num_up': self.num_up,
            'run_length_sheet': self.run_length_sheet,
            'paper_desc': self.paper_desc,
            'paper_type': self.paper_type,
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M:%S') if self.created_at else None,
            'updated_at': self.updated_at.strftime('%Y-%m-%d %H:%M:%S') if self.updated_at else None,
            'created_by': self.created_by,
            'creator_name': self.creator.name if self.creator else None
        }
    
    @classmethod
    def get_or_create_by_wo(cls, wo_number, **kwargs):
        """Get existing record by WO number or create new one"""
        db = get_db()
        existing = cls.query.filter_by(wo_number=wo_number).first()
        
        if existing:
            # Update existing record with new data
            for key, value in kwargs.items():
                if hasattr(existing, key):
                    setattr(existing, key, value)
            existing.updated_at = datetime.now(jakarta_tz)
            return existing, False
        else:
            # Create new record
            new_record = cls(wo_number=wo_number, **kwargs)
            db.session.add(new_record)
            return new_record, True
    
    @classmethod
    def aggregate_sheet_by_wo(cls, wo_data_list):
        """Aggregate sheet values for duplicate WO numbers"""
        aggregated = {}
        
        for data in wo_data_list:
            wo_number = data.get('wo_number')
            if wo_number not in aggregated:
                # First occurrence, store all data
                aggregated[wo_number] = data.copy()
            else:
                # Duplicate WO, sum the sheet values
                existing_sheet = aggregated[wo_number].get('run_length_sheet', 0)
                new_sheet = data.get('run_length_sheet', 0)
                aggregated[wo_number]['run_length_sheet'] = existing_sheet + new_sheet
        
        return list(aggregated.values())