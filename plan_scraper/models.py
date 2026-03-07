# Plan Scraper Models
from datetime import datetime
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import UniqueConstraint
from decimal import Decimal
import pytz

# Timezone untuk Jakarta
jakarta_tz = pytz.timezone('Asia/Jakarta')

def safe_float(value):
    """Safely convert Decimal to float to avoid type mixing issues"""
    if value is None:
        return None
    if isinstance(value, Decimal):
        return float(value)
    return float(value) if value else None

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

class WorkQueue(db.Model):
    """Model for tracking received/active work orders"""
    __tablename__ = 'work_queue'
    
    id = db.Column(db.Integer, primary_key=True)
    plan_scraper_data_id = db.Column(db.Integer, db.ForeignKey('plan_scraper_data.id'), nullable=False)
    received_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    received_at = db.Column(db.DateTime, default=lambda: datetime.now(jakarta_tz))
    status = db.Column(db.String(20), default='active')  # active, pending, in_progress, on_hold, completed, cancelled
    priority = db.Column(db.String(10), default='normal')  # low, normal, high
    notes = db.Column(db.Text, nullable=True)
    started_at = db.Column(db.DateTime, nullable=True)
    started_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    completed_at = db.Column(db.DateTime, nullable=True)
    completed_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    
    # Merge tracking
    merged_with_id = db.Column(db.Integer, db.ForeignKey('work_queue.id'), nullable=True)  # If merged with another WO
    
    # Current downtime tracking
    current_downtime_id = db.Column(db.Integer, db.ForeignKey('work_queue_downtime.id'), nullable=True)
    
    # Add unique constraint to prevent duplicate work orders in queue
    __table_args__ = (UniqueConstraint('plan_scraper_data_id', name='uq_work_queue_plan_data'),)
    
    # Relationships
    plan_data = db.relationship('PlanScraperData', backref='work_queue_entries')
    receiver = db.relationship('User', foreign_keys=[received_by], backref='received_work_orders')
    starter = db.relationship('User', foreign_keys=[started_by], backref='started_work_orders')
    completer = db.relationship('User', foreign_keys=[completed_by], backref='completed_work_orders')
    current_downtime = db.relationship('WorkQueueDowntime', foreign_keys=[current_downtime_id])
    downtimes = db.relationship('WorkQueueDowntime', backref='work_queue', foreign_keys='WorkQueueDowntime.work_queue_id', cascade='all, delete-orphan')
    
    def to_dict(self):
        """Convert model to dictionary for JSON serialization"""
        return {
            'id': self.id,
            'plan_scraper_data_id': self.plan_scraper_data_id,
            'received_by': self.received_by,
            'received_at': self.received_at.strftime('%Y-%m-%d %H:%M:%S') if self.received_at else None,
            'status': self.status,
            'priority': self.priority,
            'notes': self.notes,
            'receiver_name': self.receiver.name if self.receiver else None,
            'started_at': self.started_at.strftime('%Y-%m-%d %H:%M:%S') if self.started_at else None,
            'started_by': self.started_by,
            'started_by_name': self.starter.name if self.starter else None,
            'completed_at': self.completed_at.strftime('%Y-%m-%d %H:%M:%S') if self.completed_at else None,
            'completed_by': self.completed_by,
            'completed_by_name': self.completer.name if self.completer else None,
            'plan_data': self.plan_data.to_dict() if self.plan_data else None
        }
    
    def to_dict_with_plan_data(self):
        """Convert model to dictionary with full plan data for work queue"""
        result = self.to_dict()
        if self.plan_data:
            result.update({
                'wo_number': self.plan_data.wo_number,
                'mc_number': self.plan_data.mc_number,
                'item_name': self.plan_data.item_name,
                'print_machine': self.plan_data.print_machine,
                'num_up': self.plan_data.num_up,
                'run_length_sheet': self.plan_data.run_length_sheet,
                'paper_desc': self.plan_data.paper_desc,
                'paper_type': self.plan_data.paper_type
            })
        
        # Add current downtime info
        if self.current_downtime:
            try:
                duration = self.current_downtime.calculate_duration()
            except Exception as e:
                print(f"Error calculating duration: {e}")
                duration = None
            
            result.update({
                'current_downtime_reason': self.current_downtime.downtime_reason,
                'current_downtime_started_at': self.current_downtime.started_at.strftime('%Y-%m-%d %H:%M:%S') if self.current_downtime.started_at else None,
                'current_downtime_duration_hours': duration
            })
        
        # Add downtime history
        try:
            result['downtime_history'] = [downtime.to_dict() for downtime in self.downtimes]
            result['total_downtime_hours'] = sum(safe_float(downtime.duration_hours) or 0 for downtime in self.downtimes)
        except Exception as e:
            print(f"Error processing downtime history: {e}")
            result['downtime_history'] = []
            result['total_downtime_hours'] = 0
        
        return result
    
    @classmethod
    def get_by_plan_data_id(cls, plan_data_id):
        """Get work queue entry by plan scraper data ID"""
        return cls.query.filter_by(plan_scraper_data_id=plan_data_id).first()
    
    @classmethod
    def get_active_work_orders(cls, page=1, per_page=25, filters=None):
        """Get active work orders with pagination and filtering"""
        query = cls.query
        is_search = filters and filters.get('search')
        
        # Check if we need to join with PlanScraperData
        needs_plan_join = False
        if filters:
            if filters.get('machine') or filters.get('search'):
                needs_plan_join = True
        
        # Apply joins first to avoid duplicate joins
        if needs_plan_join:
            query = query.join(PlanScraperData)
        
        # Apply filters
        if filters:
            if filters.get('status'):
                query = query.filter(cls.status == filters['status'])
            
            if filters.get('priority'):
                query = query.filter(cls.priority == filters['priority'])
            
            if filters.get('machine'):
                query = query.filter(PlanScraperData.print_machine == filters['machine'])
            
            if filters.get('search'):
                search_term = f"%{filters['search']}%"
                search_filter = db.or_(
                    PlanScraperData.wo_number.like(search_term),
                    PlanScraperData.mc_number.like(search_term),
                    PlanScraperData.item_name.like(search_term)
                )
                query = query.filter(search_filter)
        
        # When not searching, exclude already-merged items from results
        # When searching, include them so we can find them and display their primary
        if not is_search:
            query = query.filter(cls.merged_with_id == None)
        
        # Order by received_at desc, then priority
        query = query.order_by(
            db.case(
                (cls.priority == 'high', 1),
                (cls.priority == 'normal', 2),
                (cls.priority == 'low', 3),
                else_=4
            ),
            cls.received_at.desc()
        )
        
        return query.paginate(page=page, per_page=per_page, error_out=False)
    
    def start_downtime(self, reason, notes=None, user_id=None):
        """Start a new downtime period for this WO and all its merged items"""
        import json
        # End any existing downtime first
        if self.current_downtime:
            self.end_downtime(user_id)
        
        # Determine primary WO
        if self.merged_with_id:
            primary_id = self.merged_with_id
        else:
            primary_id = self.id
        
        # Get primary work queue and all affected items
        primary_wq = WorkQueue.query.get(primary_id) if self.merged_with_id else self
        if not primary_wq:
            primary_wq = self
        
        # Get all merged items
        merged_items = WorkQueue.query.filter_by(merged_with_id=primary_wq.id).all()
        
        # Build list of affected WO IDs (primary + merged)
        affected_ids = [primary_wq.id] + [m.id for m in merged_items]
        
        # Save current status before changing to pending
        previous_status = primary_wq.status
        
        # Create new downtime record FOR THE PRIMARY ONLY
        new_downtime = WorkQueueDowntime(
            work_queue_id=primary_wq.id,
            affected_work_queue_ids=json.dumps(affected_ids),  # Store all affected WO IDs
            downtime_reason=reason,
            downtime_notes=notes,
            started_at=datetime.now(jakarta_tz),
            previous_status=previous_status,
            created_by=user_id
        )
        
        db.session.add(new_downtime)
        db.session.flush()  # Get the ID without committing
        
        # Update status for PRIMARY and ALL MERGED items to 'pending'
        primary_wq.status = 'pending'
        primary_wq.current_downtime_id = new_downtime.id
        
        for merged in merged_items:
            merged.status = 'pending'
            merged.current_downtime_id = new_downtime.id
        
        return new_downtime
    
    def end_downtime(self, user_id=None):
        """End the current downtime period for this WO and all its merged items"""
        import json
        if not self.current_downtime:
            return None
        
        downtime_record = self.current_downtime
        
        # Update downtime record
        downtime_record.ended_at = datetime.now(jakarta_tz)
        downtime_record.ended_by = user_id
        downtime_record.duration_hours = safe_float(downtime_record.calculate_duration())
        
        # Get all affected WO IDs from the downtime record
        affected_ids = []
        if downtime_record.affected_work_queue_ids:
            try:
                affected_ids = json.loads(downtime_record.affected_work_queue_ids)
            except:
                affected_ids = [downtime_record.work_queue_id]
        else:
            affected_ids = [downtime_record.work_queue_id]
        
        # Restore status for ALL affected WOs
        previous_status = downtime_record.previous_status or 'active'
        for affected_id in affected_ids:
            wq = WorkQueue.query.get(affected_id)
            if wq:
                wq.status = previous_status
                wq.current_downtime_id = None
        
        return downtime_record
    
    def get_current_downtime_duration(self):
        """Get current downtime duration in hours"""
        if not self.current_downtime:
            return None
        
        return self.current_downtime.calculate_duration()
    
    def get_total_downtime_hours(self, include_ended=True):
        """Get total downtime hours for this WO (accounts for shared downtime with merged items)
        
        When a WO is merged with others, downtime is SHARED - not duplicated.
        This method counts each downtime event only once, regardless of affected WO count.
        
        Args:
            include_ended: If True, include completed downtime. If False, only current.
            
        Returns:
            Float: Total downtime in hours (fair calculation for merged WOs)
        """
        import json
        from sqlalchemy import or_
        
        # Determine if this is primary or secondary
        if self.merged_with_id:
            primary_id = self.merged_with_id
        else:
            primary_id = self.id
        
        # Query downtime records where this WO is in affected_work_queue_ids
        # Get all downtime records for primary WO
        downtime_records = WorkQueueDowntime.query.filter_by(work_queue_id=primary_id).all()
        
        total_hours = 0.0
        seen_downtime_ids = set()
        
        for downtime in downtime_records:
            if downtime.id in seen_downtime_ids:
                continue
            
            # Check if filter is needed
            if not include_ended and downtime.ended_at:
                continue
            
            # Only count this downtime once (not per affected WO)
            duration = downtime.calculate_duration() if downtime.started_at else 0
            total_hours += duration
            seen_downtime_ids.add(downtime.id)
        
        return round(total_hours, 2)


class WorkQueueDowntime(db.Model):
    """Model for tracking downtime periods for work orders"""
    __tablename__ = 'work_queue_downtime'
    
    id = db.Column(db.Integer, primary_key=True)
    work_queue_id = db.Column(db.Integer, db.ForeignKey('work_queue.id'), nullable=False)  # Primary WO
    affected_work_queue_ids = db.Column(db.Text, nullable=True)  # JSON list of all affected WO IDs [primary + merged]
    downtime_reason = db.Column(db.String(100), nullable=False)  # SERVER_ERROR, PRINT_ERROR, TUNGGU_DATA_PDND, etc.
    downtime_notes = db.Column(db.Text, nullable=True)
    started_at = db.Column(db.DateTime, nullable=False)
    ended_at = db.Column(db.DateTime, nullable=True)
    duration_hours = db.Column(db.Numeric(10, 2), nullable=True)
    previous_status = db.Column(db.String(20), nullable=True)  # Status sebelum downtime (active, in_progress, etc)
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(jakarta_tz))
    ended_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    
    # Relationships
    creator = db.relationship('User', foreign_keys=[created_by])
    ender = db.relationship('User', foreign_keys=[ended_by])
    
    def calculate_duration(self):
        """Calculate downtime duration in hours"""
        if not self.started_at:
            return None
        
        # Ensure both datetimes are timezone-aware
        if self.ended_at:
            # If ended_at exists, make it timezone-aware
            if self.ended_at.tzinfo is None:
                end_time = jakarta_tz.localize(self.ended_at)
            else:
                end_time = self.ended_at
        else:
            # Use current time with timezone
            end_time = datetime.now(jakarta_tz)
        
        # Make started_at timezone-aware
        if self.started_at.tzinfo is None:
            start_time = jakarta_tz.localize(self.started_at)
        else:
            start_time = self.started_at
        
        duration = end_time - start_time
        duration_hours = duration.total_seconds() / 3600
        
        # Return as float to avoid Decimal/float mixing issues
        return float(round(duration_hours, 2))
    
    def to_dict(self):
        """Convert model to dictionary for JSON serialization"""
        import json
        try:
            # Calculate duration if not already set
            if not self.duration_hours and self.started_at:
                self.duration_hours = self.calculate_duration()
        except Exception as e:
            print(f"Error in to_dict calculating duration: {e}")
        
        # Parse affected WO IDs
        affected_ids = []
        if self.affected_work_queue_ids:
            try:
                affected_ids = json.loads(self.affected_work_queue_ids)
            except:
                affected_ids = [self.work_queue_id]
        else:
            affected_ids = [self.work_queue_id]
        
        return {
            'id': self.id,
            'work_queue_id': self.work_queue_id,
            'affected_work_queue_ids': affected_ids,
            'downtime_reason': self.downtime_reason,
            'downtime_notes': self.downtime_notes,
            'started_at': self.started_at.strftime('%Y-%m-%d %H:%M:%S') if self.started_at else None,
            'ended_at': self.ended_at.strftime('%Y-%m-%d %H:%M:%S') if self.ended_at else None,
            'duration_hours': safe_float(self.duration_hours),
            'previous_status': self.previous_status,
            'created_by': self.created_by,
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M:%S') if self.created_at else None,
            'ended_by': self.ended_by,
            'is_active': self.ended_at is None
        }
    
    @classmethod
    def get_by_plan_data_id(cls, plan_data_id):
        """Get work queue entry by plan scraper data ID"""
        return cls.query.filter_by(plan_scraper_data_id=plan_data_id).first()
    
    def mark_completed(self, completed_by_user_id, notes=None):
        """Mark work order as completed"""
        self.status = 'completed'
        self.completed_at = datetime.now(jakarta_tz)
        self.completed_by = completed_by_user_id
        if notes:
            self.notes = notes
    
    def cancel(self, notes=None):
        """Cancel work order"""
        self.status = 'cancelled'
        if notes:
            self.notes = notes


    @classmethod
    def get_all(cls, page=1, per_page=50, filters=None):
        """Get all production jobs with pagination and filtering"""
        query = cls.query
        
        if filters:
            if filters.get('status'):
                query = query.filter(cls.status == filters['status'])
            if filters.get('tanggal'):
                query = query.filter(cls.tanggal == filters['tanggal'])
            if filters.get('pic'):
                query = query.filter(cls.pic == filters['pic'])
            if filters.get('customer'):
                query = query.filter(cls.customer_name.like(f"%{filters['customer']}%"))
            if filters.get('search'):
                search_term = f"%{filters['search']}%"
                query = query.filter(
                    db.or_(
                        cls.wo_number.like(search_term),
                        cls.mc_number.like(search_term),
                        cls.item_name.like(search_term)
                    )
                )
        
        # Order by created_at desc
        query = query.order_by(cls.created_at.desc())
        
        return query.paginate(page=page, per_page=per_page, error_out=False)