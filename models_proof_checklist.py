from datetime import datetime
import pytz
from sqlalchemy import Column, Integer, String, Date, Text, Boolean, Enum, ForeignKey, TIMESTAMP
from sqlalchemy.orm import relationship
from models import db

# Jakarta timezone
jakarta_tz = pytz.timezone('Asia/Jakarta')

# Master Tables for Proof Checklist System

class MasterPrintMachine(db.Model):
    """Model for master print machines"""
    __tablename__ = 'master_print_machines'
    
    id = Column(Integer, primary_key=True)
    machine_code = Column(String(20), nullable=False, unique=True)
    machine_name = Column(String(50), nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(TIMESTAMP, default=lambda: datetime.now(jakarta_tz))
    updated_at = Column(TIMESTAMP, default=lambda: datetime.now(jakarta_tz), onupdate=lambda: datetime.now(jakarta_tz))
    
    # Relationships
    proof_checklists = relationship('ProofChecklistPrintMachine', backref='print_machine', lazy=True)
    
    def to_dict(self):
        return {
            'id': self.id,
            'machine_code': self.machine_code,
            'machine_name': self.machine_name,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }

class MasterPrintSeparation(db.Model):
    """Model for master print separations"""
    __tablename__ = 'master_print_separations'
    
    id = Column(Integer, primary_key=True)
    separation_code = Column(String(20), nullable=False, unique=True)
    separation_name = Column(String(50), nullable=False)
    is_default = Column(Boolean, default=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(TIMESTAMP, default=lambda: datetime.now(jakarta_tz))
    updated_at = Column(TIMESTAMP, default=lambda: datetime.now(jakarta_tz), onupdate=lambda: datetime.now(jakarta_tz))
    
    # Relationships
    proof_checklists = relationship('ProofChecklistPrintSeparation', backref='print_separation', lazy=True)
    
    def to_dict(self):
        return {
            'id': self.id,
            'separation_code': self.separation_code,
            'separation_name': self.separation_name,
            'is_default': self.is_default,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }

class MasterPrintInk(db.Model):
    """Model for master print inks"""
    __tablename__ = 'master_print_inks'
    
    id = Column(Integer, primary_key=True)
    ink_code = Column(String(20), nullable=False, unique=True)
    ink_name = Column(String(50), nullable=False)
    is_default = Column(Boolean, default=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(TIMESTAMP, default=lambda: datetime.now(jakarta_tz))
    updated_at = Column(TIMESTAMP, default=lambda: datetime.now(jakarta_tz), onupdate=lambda: datetime.now(jakarta_tz))
    
    # Relationships
    proof_checklists = relationship('ProofChecklistPrintInk', backref='print_ink', lazy=True)
    
    def to_dict(self):
        return {
            'id': self.id,
            'ink_code': self.ink_code,
            'ink_name': self.ink_name,
            'is_default': self.is_default,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }

class MasterPostpressMachine(db.Model):
    """Model for master postpress machines"""
    __tablename__ = 'master_postpress_machines'
    
    id = Column(Integer, primary_key=True)
    machine_category = Column(Enum('LAMINATOR', 'DIECUT', 'LAMINA', 'FOLDER', 'MANUAL', name='machine_category_enum'), nullable=False)
    machine_code = Column(String(20), nullable=False, unique=True)
    machine_name = Column(String(50), nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(TIMESTAMP, default=lambda: datetime.now(jakarta_tz))
    updated_at = Column(TIMESTAMP, default=lambda: datetime.now(jakarta_tz), onupdate=lambda: datetime.now(jakarta_tz))
    
    # Relationships
    proof_checklists = relationship('ProofChecklistPostpressMachine', backref='postpress_machine', lazy=True)
    
    def to_dict(self):
        return {
            'id': self.id,
            'machine_category': self.machine_category,
            'machine_code': self.machine_code,
            'machine_name': self.machine_name,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }

# Main Proof Checklist Table

class ProofChecklist(db.Model):
    """Model for proof checklists"""
    __tablename__ = 'proof_checklists'
    
    id = Column(Integer, primary_key=True)
    
    # Proof Information
    proof_date = Column(Date, nullable=False)
    customer_name = Column(String(255), nullable=False)
    item_name = Column(String(255), nullable=False)
    product_category = Column(Enum('FOLDING_BOX', 'SINGLE_FACE', 'SHEET', 'RIGID_BOX', name='product_category_enum'), nullable=False)
    paper_supplier = Column(String(100))
    paper_grammage = Column(String(50))
    paper_size = Column(String(255))
    paper_substance = Column(String(100))
    flute = Column(String(20))
    up_num = Column(Integer)
    
    # Print/Press Production Information
    print_coating = Column(String(255))
    print_laminating = Column(String(255))
    
    # Post Press Production Information
    postpress_packing_pallet = Column(Text)
    
    # Additional Information
    additional_information = Column(Text)
    
    # Metadata
    created_by = Column(Integer, ForeignKey('users.id'), nullable=False)
    created_at = Column(TIMESTAMP, default=lambda: datetime.now(jakarta_tz))
    updated_by = Column(Integer, ForeignKey('users.id'))
    updated_at = Column(TIMESTAMP, default=lambda: datetime.now(jakarta_tz), onupdate=lambda: datetime.now(jakarta_tz))
    
    # Status
    status = Column(Enum('DRAFT', 'ACTIVE', 'COMPLETED', 'CANCELLED', name='proof_status_enum'), default='DRAFT')
    
    # Relationships
    creator = relationship('User', foreign_keys=[created_by], backref='created_proof_checklists')
    updater = relationship('User', foreign_keys=[updated_by], backref='updated_proof_checklists')
    print_machines = relationship('ProofChecklistPrintMachine', backref='proof_checklist', lazy=True, cascade='all, delete-orphan')
    print_separations = relationship('ProofChecklistPrintSeparation', backref='proof_checklist', lazy=True, cascade='all, delete-orphan')
    print_inks = relationship('ProofChecklistPrintInk', backref='proof_checklist', lazy=True, cascade='all, delete-orphan')
    postpress_machines = relationship('ProofChecklistPostpressMachine', backref='proof_checklist', lazy=True, cascade='all, delete-orphan')
    
    def to_dict(self):
        def serialize_datetime(value):
            """Helper to serialize datetime/date objects safely"""
            if value is None:
                return None
            if hasattr(value, 'isoformat'):
                return value.isoformat()
            return str(value)
        
        return {
            'id': self.id,
            'proof_date': serialize_datetime(self.proof_date),
            'customer_name': self.customer_name,
            'item_name': self.item_name,
            'product_category': self.product_category,
            'paper_supplier': self.paper_supplier,
            'paper_grammage': self.paper_grammage,
            'paper_size': self.paper_size,
            'paper_substance': self.paper_substance,
            'flute': self.flute,
            'up_num': self.up_num,
            'print_coating': self.print_coating,
            'print_laminating': self.print_laminating,
            'postpress_packing_pallet': self.postpress_packing_pallet,
            'additional_information': self.additional_information,
            'created_by': self.created_by,
            'created_at': serialize_datetime(self.created_at),
            'updated_by': self.updated_by,
            'updated_at': serialize_datetime(self.updated_at),
            'status': self.status,
            'creator_name': self.creator.username if self.creator else None,
            'updater_name': self.updater.username if self.updater else None,
            'print_machines': [pm.print_machine.to_dict() if pm.print_machine else None for pm in self.print_machines],
            'print_separations': [
                {
                    'id': ps.id,
                    'print_separation_id': ps.print_separation_id,
                    'separation_name': ps.print_separation.separation_name if ps.print_separation else None,
                    'custom_separation_name': ps.custom_separation_name
                }
                for ps in self.print_separations
            ],
            'print_inks': [
                {
                    'id': pi.id,
                    'print_ink_id': pi.print_ink_id,
                    'ink_name': pi.print_ink.ink_name if pi.print_ink else None,
                    'custom_ink_name': pi.custom_ink_name
                }
                for pi in self.print_inks
            ],
            'postpress_machines': [pm.postpress_machine.to_dict() if pm.postpress_machine else None for pm in self.postpress_machines]
        }

# Many-to-Many Relationship Tables

class ProofChecklistPrintMachine(db.Model):
    """Model for proof checklist print machines relationship"""
    __tablename__ = 'proof_checklist_print_machines'
    
    id = Column(Integer, primary_key=True)
    proof_checklist_id = Column(Integer, ForeignKey('proof_checklists.id'), nullable=False)
    print_machine_id = Column(Integer, ForeignKey('master_print_machines.id'), nullable=False)
    created_at = Column(TIMESTAMP, default=lambda: datetime.now(jakarta_tz))

class ProofChecklistPrintSeparation(db.Model):
    """Model for proof checklist print separations relationship"""
    __tablename__ = 'proof_checklist_print_separations'
    
    id = Column(Integer, primary_key=True)
    proof_checklist_id = Column(Integer, ForeignKey('proof_checklists.id'), nullable=False)
    print_separation_id = Column(Integer, ForeignKey('master_print_separations.id'), nullable=True)  # Nullable for custom values
    custom_separation_name = Column(String(255), nullable=True)  # For custom separation names
    created_at = Column(TIMESTAMP, default=lambda: datetime.now(jakarta_tz))

class ProofChecklistPrintInk(db.Model):
    """Model for proof checklist print inks relationship"""
    __tablename__ = 'proof_checklist_print_inks'
    
    id = Column(Integer, primary_key=True)
    proof_checklist_id = Column(Integer, ForeignKey('proof_checklists.id'), nullable=False)
    print_ink_id = Column(Integer, ForeignKey('master_print_inks.id'), nullable=True)  # Nullable for custom values
    custom_ink_name = Column(String(255), nullable=True)  # For custom ink names
    created_at = Column(TIMESTAMP, default=lambda: datetime.now(jakarta_tz))

class ProofChecklistPostpressMachine(db.Model):
    """Model for proof checklist postpress machines relationship"""
    __tablename__ = 'proof_checklist_postpress_machines'
    
    id = Column(Integer, primary_key=True)
    proof_checklist_id = Column(Integer, ForeignKey('proof_checklists.id'), nullable=False)
    postpress_machine_id = Column(Integer, ForeignKey('master_postpress_machines.id'), nullable=False)
    created_at = Column(TIMESTAMP, default=lambda: datetime.now(jakarta_tz))

class ProofChecklistStatusHistory(db.Model):
    """Model for tracking proof checklist status changes"""
    __tablename__ = 'proof_checklist_status_histories'
    
    id = Column(Integer, primary_key=True)
    proof_checklist_id = Column(Integer, ForeignKey('proof_checklists.id'), nullable=False)
    old_status = Column(Enum('DRAFT', 'ACTIVE', 'COMPLETED', 'CANCELLED', name='proof_status_enum'), nullable=True)
    new_status = Column(Enum('DRAFT', 'ACTIVE', 'COMPLETED', 'CANCELLED', name='proof_status_enum'), nullable=False)
    changed_by = Column(Integer, ForeignKey('users.id'), nullable=False)
    changed_at = Column(TIMESTAMP, default=lambda: datetime.now(jakarta_tz))
    notes = Column(Text, nullable=True)
    
    # Relationships
    proof_checklist = relationship('ProofChecklist', backref='status_histories', lazy=True)
    user = relationship('User', backref='status_change_logs', lazy=True)