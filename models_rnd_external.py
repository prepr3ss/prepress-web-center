"""
models_rnd_external.py
External Lead Time Tracking Model for R&D Cloudsphere System

This module contains the RNDExternalTime model for tracking external delays
between progress steps (vendor, PPIC, CSR delays, etc.)

Usage:
    from models_rnd_external import RNDExternalTime
    
Database:
    Table: rnd_cloudsphere_external_time
"""

from datetime import datetime
import pytz
from models import db, User

# Jakarta timezone
jakarta_tz = pytz.timezone('Asia/Jakarta')


class RNDExternalTime(db.Model):
    """
    Model for tracking external delays between progress steps
    
    Tracks waiting time caused by external factors (PPIC, CSR, vendors, etc.)
    between completion of one progress step and completion of the next.
    
    Attributes:
        id: Primary key
        job_id: FK to RNDJob
        last_progress_assignment_id: FK to completed RNDJobProgressAssignment
        next_progress_assignment_id: FK to next RNDJobProgressAssignment (waiting for)
        delay_category: Category of delay (PPIC, CSR, Other)
        delay_reason: Description of the delay
        delay_notes: Additional notes about the delay
        sample_type: Sample type inherited from RNDJob for filtering
        external_wait_start: When the wait started (copy of last_progress.finished_at)
        external_wait_end: When the wait ended (filled when first task in next_progress is checked)
        external_wait_hours: Calculated duration in hours
        is_active: Whether this delay is still ongoing
        created_by_user_id: Admin who recorded this delay
        created_at: Record creation timestamp
        updated_at: Record last update timestamp
    """
    __tablename__ = 'rnd_cloudsphere_external_time'
    
    id = db.Column(db.Integer, primary_key=True)
    
    # Foreign Keys
    job_id = db.Column(db.Integer, db.ForeignKey('rnd_jobs.id'), nullable=False)
    last_progress_assignment_id = db.Column(
        db.Integer, 
        db.ForeignKey('rnd_job_progress_assignments.id'), 
        nullable=False
    )
    next_progress_assignment_id = db.Column(
        db.Integer, 
        db.ForeignKey('rnd_job_progress_assignments.id'), 
        nullable=True
    )
    
    # External Delay Information
    delay_category = db.Column(db.String(50), nullable=False)  # PPIC, CSR, Other
    delay_reason = db.Column(db.String(255), nullable=False)
    delay_notes = db.Column(db.Text, nullable=True)
    
    # Sample Type (for filtering/reporting)
    sample_type = db.Column(db.String(50), nullable=False)
    
    # Timestamps
    external_wait_start = db.Column(db.DateTime, nullable=False)
    external_wait_end = db.Column(db.DateTime, nullable=True)
    external_wait_hours = db.Column(db.Float, nullable=True)
    
    # Status
    is_active = db.Column(db.Boolean, default=True)
    
    # Metadata
    created_by_user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(jakarta_tz))
    updated_at = db.Column(
        db.DateTime, 
        default=lambda: datetime.now(jakarta_tz),
        onupdate=lambda: datetime.now(jakarta_tz)
    )
    
    # Relationships
    job = db.relationship('RNDJob', backref='external_delays')
    last_progress = db.relationship(
        'RNDJobProgressAssignment',
        foreign_keys=[last_progress_assignment_id],
        backref='external_delay_as_last'
    )
    next_progress = db.relationship(
        'RNDJobProgressAssignment',
        foreign_keys=[next_progress_assignment_id],
        backref='external_delay_as_next'
    )
    created_by = db.relationship('User', foreign_keys=[created_by_user_id])
    
    def to_dict(self):
        """Convert model to dictionary for JSON serialization"""
        return {
            'id': self.id,
            'job_id': self.job_id,
            'last_progress_assignment_id': self.last_progress_assignment_id,
            'next_progress_assignment_id': self.next_progress_assignment_id,
            'delay_category': self.delay_category,
            'delay_reason': self.delay_reason,
            'delay_notes': self.delay_notes,
            'sample_type': self.sample_type,
            'external_wait_start': self.external_wait_start.isoformat() if self.external_wait_start else None,
            'external_wait_end': self.external_wait_end.isoformat() if self.external_wait_end else None,
            'external_wait_hours': round(self.external_wait_hours, 2) if self.external_wait_hours else None,
            'is_active': self.is_active,
            'is_completed': self.is_completed,
            'created_by_user_id': self.created_by_user_id,
            'created_by_name': self.created_by.name if self.created_by else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'last_progress_step_name': self.last_progress.progress_step.name if self.last_progress and self.last_progress.progress_step else None,
            'next_progress_step_name': self.next_progress.progress_step.name if self.next_progress and self.next_progress.progress_step else None
        }
    
    @property
    def is_completed(self):
        """Check if external wait has been resolved (when next progress first task is checked)"""
        return self.external_wait_end is not None
    
    def calculate_external_wait_hours(self):
        """
        Calculate wait duration in hours
        Called after external_wait_end is set
        
        Returns:
            float: Duration in hours, or None if incomplete
        """
        if self.external_wait_start and self.external_wait_end:
            delta = self.external_wait_end - self.external_wait_start
            self.external_wait_hours = delta.total_seconds() / 3600.0
            return self.external_wait_hours
        return None
    
    def __repr__(self):
        return f'<RNDExternalTime(id={self.id}, job_id={self.job_id}, category={self.delay_category})>'