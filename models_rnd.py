from datetime import datetime, time, timedelta
import pytz
from sqlalchemy import func, and_, or_
from models import db, User  # Import db and User from main models

# Jakarta timezone
jakarta_tz = pytz.timezone('Asia/Jakarta')

# R&D Cloudsphere System Models

class RNDProgressStep(db.Model):
    """Model for progress steps in R&D system"""
    __tablename__ = 'rnd_progress_steps'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)  # Design, Mastercard, Blank, etc.
    sample_type = db.Column(db.String(50), nullable=False)  # Blank, RoHS ICB, etc.
    step_order = db.Column(db.Integer, nullable=False)  # Order of steps within sample type
    description = db.Column(db.String(255), nullable=True)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(jakarta_tz))
    
    # Relationships
    tasks = db.relationship('RNDProgressTask', backref='progress_step', lazy=True, cascade='all, delete-orphan')
    job_assignments = db.relationship('RNDJobProgressAssignment', backref='progress_step', lazy=True)
    
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'sample_type': self.sample_type,
            'step_order': self.step_order,
            'description': self.description,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

class RNDProgressTask(db.Model):
    """Model for tasks within progress steps"""
    __tablename__ = 'rnd_progress_tasks'
    
    id = db.Column(db.Integer, primary_key=True)
    progress_step_id = db.Column(db.Integer, db.ForeignKey('rnd_progress_steps.id'), nullable=False)
    name = db.Column(db.String(255), nullable=False)
    task_order = db.Column(db.Integer, nullable=False)  # Order within progress step
    description = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(jakarta_tz))
    
    # Relationships
    job_task_assignments = db.relationship('RNDJobTaskAssignment', backref='progress_task', lazy=True)
    task_completions = db.relationship('RNDTaskCompletion', backref='progress_task', lazy=True)
    
    def to_dict(self):
        return {
            'id': self.id,
            'progress_step_id': self.progress_step_id,
            'name': self.name,
            'task_order': self.task_order,
            'description': self.description,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

class RNDJob(db.Model):
    """Model for R&D jobs with multi-PIC progress tracking"""
    __tablename__ = 'rnd_jobs'
    
    id = db.Column(db.Integer, primary_key=True)
    job_id = db.Column(db.String(20), nullable=False, unique=True)  # Auto-generated job ID
    started_at = db.Column(db.DateTime, nullable=False)
    deadline_at = db.Column(db.DateTime, nullable=False)
    finished_at = db.Column(db.DateTime, nullable=True)
    item_name = db.Column(db.String(255), nullable=False)
    sample_type = db.Column(db.String(50), nullable=False)  # Blank, RoHS ICB, etc.
    priority_level = db.Column(db.String(10), nullable=False, default='Middle')  # Low, Middle, High
    status = db.Column(db.String(20), nullable=False, default='in_progress')  # in_progress, completed, rejected
    notes = db.Column(db.Text, nullable=True)
    is_full_process = db.Column(db.Boolean, nullable=False, default=False)  # Flag to indicate if job follows full process workflow
    flow_configuration_id = db.Column(db.Integer, db.ForeignKey('rnd_flow_configurations.id'), nullable=True)  # Link to dynamic flow configuration
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(jakarta_tz))
    updated_at = db.Column(db.DateTime, default=lambda: datetime.now(jakarta_tz), onupdate=lambda: datetime.now(jakarta_tz))
    
    # Relationships
    progress_assignments = db.relationship('RNDJobProgressAssignment', backref='job', lazy=True, cascade='all, delete-orphan')
    evidence_files = db.relationship('RNDEvidenceFile', backref='job', cascade='all, delete-orphan', lazy='dynamic')
    flow_configuration = db.relationship('RNDFlowConfiguration', backref='jobs')
    
    def to_dict(self):
        return {
            'id': self.id,
            'job_id': self.job_id,
            'started_at': self.started_at.isoformat() if self.started_at else None,
            'deadline_at': self.deadline_at.isoformat() if self.deadline_at else None,
            'finished_at': self.finished_at.isoformat() if self.finished_at else None,
            'item_name': self.item_name,
            'sample_type': self.sample_type,
            'priority_level': self.priority_level,
            'status': self.status,
            'notes': self.notes,
            'is_full_process': self.is_full_process,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'completion_percentage': self.completion_percentage,
            'current_progress_step': self.current_progress_step,
            'flow_configuration_id': self.flow_configuration_id  # Add flow configuration ID
        }
    
    @property
    def completion_percentage(self):
        """Calculate completion percentage based on task completion and auto-sync status"""
        if not self.progress_assignments:
            return 0
        
        # Calculate based on TASK completion, not assignment status
        total_tasks = 0
        completed_tasks = 0
        
        for assignment in self.progress_assignments:
            for task_assign in assignment.task_assignments:
                total_tasks += 1
                if task_assign.status == 'completed':
                    completed_tasks += 1
        
        pct = round((completed_tasks / total_tasks) * 100, 2) if total_tasks > 0 else 0
        
        # AUTO-SYNC FORWARD: If completion is 100% and status is not completed, update it
        if pct == 100 and self.status != 'completed':
            print(f"DEBUG (property): Auto-syncing {self.job_id} - 100% completion detected, updating status to completed")
            self.status = 'completed'
            if not self.finished_at:
                self.finished_at = datetime.now(jakarta_tz)
            # Mark for update
            self.updated_at = datetime.now(jakarta_tz)
        
        # AUTO-SYNC REVERSE: If completion is < 100% and status is completed, reset it
        elif pct < 100 and self.status == 'completed':
            print(f"DEBUG (property): Auto-syncing {self.job_id} - completion {pct}% < 100%, resetting status to in_progress")
            self.status = 'in_progress'
            self.finished_at = None  # Clear finished_at since job is no longer complete
            # Mark for update
            self.updated_at = datetime.now(jakarta_tz)
        
        return pct
    
    @property
    def current_progress_step(self):
        """Get current active progress step"""
        if not self.progress_assignments:
            return None
        # Find the first non-completed step
        for assignment in sorted(self.progress_assignments, key=lambda x: x.progress_step.step_order):
            if assignment.status != 'completed':
                return {
                    'step_name': assignment.progress_step.name,
                    'pic_name': assignment.pic.name if assignment.pic else None,
                    'status': assignment.status
                }
        return None

class RNDJobProgressAssignment(db.Model):
    """Model for assigning progress steps to jobs with PIC"""
    __tablename__ = 'rnd_job_progress_assignments'
    
    id = db.Column(db.Integer, primary_key=True)
    job_id = db.Column(db.Integer, db.ForeignKey('rnd_jobs.id'), nullable=False)
    progress_step_id = db.Column(db.Integer, db.ForeignKey('rnd_progress_steps.id'), nullable=False)
    pic_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    started_at = db.Column(db.DateTime, nullable=True)
    finished_at = db.Column(db.DateTime, nullable=True)
    status = db.Column(db.String(20), nullable=False, default='pending')  # pending, in_progress, completed, blocked
    notes = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(jakarta_tz))
    updated_at = db.Column(db.DateTime, default=lambda: datetime.now(jakarta_tz), onupdate=lambda: datetime.now(jakarta_tz))
    
    # Relationships
    pic = db.relationship('User', backref='rnd_progress_assignments')
    task_assignments = db.relationship('RNDJobTaskAssignment', backref='progress_assignment', lazy=True, cascade='all, delete-orphan')
    evidence_files = db.relationship('RNDEvidenceFile', backref='progress_assignment', lazy='dynamic')
    lead_time_tracking = db.relationship('RNDLeadTimeTracking', backref='progress_assignment', uselist=False, cascade='all, delete-orphan')
    
    def to_dict(self):
        return {
            'id': self.id,
            'job_id': self.job_id,
            'progress_step_id': self.progress_step_id,
            'pic_id': self.pic_id,
            'pic_name': self.pic.name if self.pic else None,
            'started_at': self.started_at.isoformat() if self.started_at else None,
            'finished_at': self.finished_at.isoformat() if self.finished_at else None,
            'status': self.status,
            'notes': self.notes,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'completion_percentage': self.completion_percentage
        }
    
    @property
    def completion_percentage(self):
        """Calculate completion percentage based on tasks"""
        if not self.task_assignments:
            return 0
        total_tasks = len(self.task_assignments)
        completed_tasks = len([ta for ta in self.task_assignments if ta.status == 'completed'])
        return round((completed_tasks / total_tasks) * 100, 2) if total_tasks > 0 else 0

class RNDJobTaskAssignment(db.Model):
    """Model for assigning tasks to job progress steps"""
    __tablename__ = 'rnd_job_task_assignments'
    
    id = db.Column(db.Integer, primary_key=True)
    job_progress_assignment_id = db.Column(db.Integer, db.ForeignKey('rnd_job_progress_assignments.id'), nullable=False)
    progress_task_id = db.Column(db.Integer, db.ForeignKey('rnd_progress_tasks.id'), nullable=False)
    status = db.Column(db.String(20), nullable=False, default='pending')  # pending, in_progress, completed
    completed_at = db.Column(db.DateTime, nullable=True)
    notes = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(jakarta_tz))
    updated_at = db.Column(db.DateTime, default=lambda: datetime.now(jakarta_tz), onupdate=lambda: datetime.now(jakarta_tz))
    
    # Relationships
    evidence_files = db.relationship('RNDEvidenceFile', backref='task_assignment', lazy='dynamic')
    task_completions = db.relationship('RNDTaskCompletion', backref='task_assignment', uselist=False, cascade='all, delete-orphan')
    
    def to_dict(self):
        return {
            'id': self.id,
            'job_progress_assignment_id': self.job_progress_assignment_id,
            'progress_task_id': self.progress_task_id,
            'task_name': self.progress_task.name if self.progress_task else None,
            'status': self.status,
            'completed_at': self.completed_at.isoformat() if self.completed_at else None,
            'notes': self.notes,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }

class RNDLeadTimeTracking(db.Model):
    """Model for tracking lead time between progress steps"""
    __tablename__ = 'rnd_lead_time_tracking'
    
    id = db.Column(db.Integer, primary_key=True)
    job_progress_assignment_id = db.Column(db.Integer, db.ForeignKey('rnd_job_progress_assignments.id'), nullable=False, unique=True)
    planned_duration_hours = db.Column(db.Float, nullable=True)  # Planned duration in hours
    actual_duration_hours = db.Column(db.Float, nullable=True)  # Actual duration in hours
    variance_hours = db.Column(db.Float, nullable=True)  # Difference between planned and actual
    efficiency_percentage = db.Column(db.Float, nullable=True)  # Efficiency calculation
    notes = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(jakarta_tz))
    updated_at = db.Column(db.DateTime, default=lambda: datetime.now(jakarta_tz), onupdate=lambda: datetime.now(jakarta_tz))
    
    def to_dict(self):
        return {
            'id': self.id,
            'job_progress_assignment_id': self.job_progress_assignment_id,
            'planned_duration_hours': self.planned_duration_hours,
            'actual_duration_hours': self.actual_duration_hours,
            'variance_hours': self.variance_hours,
            'efficiency_percentage': self.efficiency_percentage,
            'notes': self.notes,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
    
    def calculate_metrics(self):
        """Calculate lead time metrics"""
        if self.progress_assignment and self.progress_assignment.started_at and self.progress_assignment.finished_at:
            # Calculate actual duration in hours
            actual_duration = self.progress_assignment.finished_at - self.progress_assignment.started_at
            self.actual_duration_hours = actual_duration.total_seconds() / 3600.0
            
            # Calculate variance and efficiency
            if self.planned_duration_hours:
                self.variance_hours = self.actual_duration_hours - self.planned_duration_hours
                if self.planned_duration_hours > 0:
                    self.efficiency_percentage = (self.planned_duration_hours / self.actual_duration_hours) * 100

class RNDEvidenceFile(db.Model):
    """Model for evidence files uploaded at each progress step"""
    __tablename__ = 'rnd_evidence_files'
    
    id = db.Column(db.Integer, primary_key=True)
    job_id = db.Column(db.Integer, db.ForeignKey('rnd_jobs.id'), nullable=False)
    job_progress_assignment_id = db.Column(db.Integer, db.ForeignKey('rnd_job_progress_assignments.id'), nullable=True)
    job_task_assignment_id = db.Column(db.Integer, db.ForeignKey('rnd_job_task_assignments.id'), nullable=True)
    filename = db.Column(db.String(255), nullable=False)
    original_filename = db.Column(db.String(255), nullable=False)
    file_path = db.Column(db.String(500), nullable=False)
    file_type = db.Column(db.String(10), nullable=False)  # photo, pdf, docx, xlsx
    file_size = db.Column(db.Integer, nullable=False)  # in bytes
    evidence_type = db.Column(db.String(20), nullable=False)  # step_completion, task_completion
    uploaded_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    uploaded_at = db.Column(db.DateTime, default=lambda: datetime.now(jakarta_tz))
    is_verified = db.Column(db.Boolean, default=False)  # Whether evidence has been verified
    verified_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    verified_at = db.Column(db.DateTime, nullable=True)
    verification_notes = db.Column(db.Text, nullable=True)
    
    # Relationships
    uploader = db.relationship('User', foreign_keys=[uploaded_by], backref='rnd_uploaded_evidence')
    verifier = db.relationship('User', foreign_keys=[verified_by], backref='rnd_verified_evidence')
    
    def to_dict(self):
        return {
            'id': self.id,
            'job_id': self.job_id,
            'job_progress_assignment_id': self.job_progress_assignment_id,
            'job_task_assignment_id': self.job_task_assignment_id,
            'filename': self.filename,
            'original_filename': self.original_filename,
            'file_path': self.file_path,
            'file_type': self.file_type,
            'file_size': self.file_size,
            'evidence_type': self.evidence_type,
            'uploaded_by': self.uploaded_by,
            'uploader_name': self.uploader.name if self.uploader else None,
            'uploaded_at': self.uploaded_at.isoformat() if self.uploaded_at else None,
            'is_verified': self.is_verified,
            'verified_by': self.verified_by,
            'verifier_name': self.verifier.name if self.verifier else None,
            'verified_at': self.verified_at.isoformat() if self.verified_at else None,
            'verification_notes': self.verification_notes
        }

class RNDTaskCompletion(db.Model):
    """Model for tracking task completion details"""
    __tablename__ = 'rnd_task_completions'
    
    id = db.Column(db.Integer, primary_key=True)
    job_task_assignment_id = db.Column(db.Integer, db.ForeignKey('rnd_job_task_assignments.id'), nullable=False, unique=True)
    progress_task_id = db.Column(db.Integer, db.ForeignKey('rnd_progress_tasks.id'), nullable=False)
    completed_at = db.Column(db.DateTime, nullable=False)
    completed_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    completion_notes = db.Column(db.Text, nullable=True)
    quality_score = db.Column(db.Integer, nullable=True)  # 1-5 quality rating
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(jakarta_tz))
    updated_at = db.Column(db.DateTime, default=lambda: datetime.now(jakarta_tz), onupdate=lambda: datetime.now(jakarta_tz))
    
    # Relationships
    completed_by_user = db.relationship('User', foreign_keys=[completed_by], backref='rnd_task_completions')
    
    # Add constraint to ensure data integrity
    __table_args__ = (
        db.CheckConstraint('quality_score >= 1 AND quality_score <= 5', name='check_quality_score_range'),
    )
    
    def to_dict(self):
        return {
            'id': self.id,
            'job_task_assignment_id': self.job_task_assignment_id,
            'progress_task_id': self.progress_task_id,
            'completed_at': self.completed_at.isoformat() if self.completed_at else None,
            'completed_by': self.completed_by,
            'completer_name': self.completed_by_user.name if self.completed_by_user else None,
            'completion_notes': self.completion_notes,
            'quality_score': self.quality_score,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }

class RNDJobNote(db.Model):
    """Model for collaborative notes on R&D jobs"""
    __tablename__ = 'rnd_job_notes'
    
    id = db.Column(db.Integer, primary_key=True)
    job_id = db.Column(db.Integer, db.ForeignKey('rnd_jobs.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    note_content = db.Column(db.Text, nullable=False)
    note_type = db.Column(db.String(20), nullable=False, default='general')  # general, progress, issue, solution
    is_pinned = db.Column(db.Boolean, default=False)  # For important notes
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(jakarta_tz))
    updated_at = db.Column(db.DateTime, default=lambda: datetime.now(jakarta_tz), onupdate=lambda: datetime.now(jakarta_tz))
    
    # Relationships
    job = db.relationship('RNDJob', backref='collaborative_notes')
    user = db.relationship('User', backref='job_notes')
    
    def to_dict(self):
        return {
            'id': self.id,
            'job_id': self.job_id,
            'user_id': self.user_id,
            'user_name': self.user.name if self.user else None,
            'note_content': self.note_content,
            'note_type': self.note_type,
            'is_pinned': self.is_pinned,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }

class RNDFlowConfiguration(db.Model):
    """Model for storing dynamic flow configurations for sample types"""
    __tablename__ = 'rnd_flow_configurations'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)  # Configuration name (e.g., "Standard Blank Flow")
    sample_type = db.Column(db.String(50), nullable=False)  # Blank, RoHS ICB, etc.
    description = db.Column(db.Text, nullable=True)
    is_default = db.Column(db.Boolean, default=False)  # Mark as default for sample type
    is_active = db.Column(db.Boolean, default=True)  # Enable/disable configuration
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(jakarta_tz))
    updated_at = db.Column(db.DateTime, default=lambda: datetime.now(jakarta_tz), onupdate=lambda: datetime.now(jakarta_tz))
    
    # Relationships
    creator = db.relationship('User', foreign_keys=[created_by], backref='flow_configurations')
    flow_steps = db.relationship('RNDFlowStep', backref='flow_configuration', lazy=True, cascade='all, delete-orphan')
    
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'sample_type': self.sample_type,
            'description': self.description,
            'is_default': self.is_default,
            'is_active': self.is_active,
            'created_by': self.created_by,
            'creator_name': self.creator.name if self.creator else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'flow_steps': [step.to_dict() for step in self.flow_steps]
        }

class RNDFlowStep(db.Model):
    """Model for storing individual steps within a flow configuration"""
    __tablename__ = 'rnd_flow_steps'
    
    id = db.Column(db.Integer, primary_key=True)
    flow_configuration_id = db.Column(db.Integer, db.ForeignKey('rnd_flow_configurations.id'), nullable=False)
    progress_step_id = db.Column(db.Integer, db.ForeignKey('rnd_progress_steps.id'), nullable=False)
    step_order = db.Column(db.Integer, nullable=False)  # Order within the flow
    is_required = db.Column(db.Boolean, default=True)  # Whether this step is required
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(jakarta_tz))
    
    # Relationships
    progress_step = db.relationship('RNDProgressStep', backref='flow_step_references')
    
    def to_dict(self):
        return {
            'id': self.id,
            'flow_configuration_id': self.flow_configuration_id,
            'progress_step_id': self.progress_step_id,
            'step_order': self.step_order,
            'is_required': self.is_required,
            'progress_step_name': self.progress_step.name if self.progress_step else None,
            'progress_step_sample_type': self.progress_step.sample_type if self.progress_step else None,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }