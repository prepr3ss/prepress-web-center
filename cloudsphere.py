from datetime import datetime, timedelta
from flask import Blueprint, jsonify, request, render_template, send_file
from flask_login import login_required, current_user
from functools import wraps
from models import db, TaskCategory, Task, CloudsphereJob, JobTask, JobProgress, JobProgressTask, EvidenceFile, User
from werkzeug.utils import secure_filename
import os
import pytz
from sqlalchemy import and_, or_

# Create Blueprint
cloudsphere_bp = Blueprint('cloudsphere', __name__, url_prefix='/cloudsphere')

# Jakarta timezone
jakarta_tz = pytz.timezone('Asia/Jakarta')

# Helper function to generate job ID
def generate_job_id():
    """Generate unique job ID with format CS-YYYYMMDD-XXX"""
    now = datetime.now(jakarta_tz)
    date_str = now.strftime('%Y%m%d')
    
    # Get latest job for today
    latest_job = CloudsphereJob.query.filter(
        CloudsphereJob.job_id.like(f'CS-{date_str}-%')
    ).order_by(CloudsphereJob.job_id.desc()).first()
    
    if latest_job:
        # Extract sequence number from latest job ID
        sequence = int(latest_job.job_id.split('-')[-1]) + 1
    else:
        sequence = 1
    
    return f'CS-{date_str}-{sequence:03d}'

# Helper function to check file extension
def allowed_file(filename, allowed_extensions):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in allowed_extensions

# Access control decorators
def require_rnd_access(f):
    """Decorator to require R&D access"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            return jsonify({'error': 'Authentication required'}), 401
        if not current_user.can_access_rnd():
            return jsonify({'error': 'R&D access required'}), 403
        return f(*args, **kwargs)
    return decorated_function

# Cloudsphere Routes
@cloudsphere_bp.route('/')
@login_required
@require_rnd_access
def cloudsphere_dashboard():
    """Render Cloudsphere dashboard"""
    return render_template('cloudsphere.html')

@cloudsphere_bp.route('/job/<int:job_id>')
@login_required
@require_rnd_access
def job_detail(job_id):
    """Render job detail page"""
    job = CloudsphereJob.query.get_or_404(job_id)
    return render_template('cloudsphere_job_detail.html', job=job)

# API Routes
@cloudsphere_bp.route('/api/dashboard-stats')
@login_required
@require_rnd_access
def get_dashboard_stats():
    """Get dashboard statistics"""
    try:
        user = current_user
        
        # Base query
        if user.is_admin():
            jobs_query = CloudsphereJob.query
        else:
            jobs_query = CloudsphereJob.query.filter_by(pic_id=user.id)
        
        total_jobs = jobs_query.count()
        
        # Jobs by status
        in_progress = jobs_query.filter_by(status='in_progress').count()
        pending_approval = jobs_query.filter_by(status='pending_approval').count()
        completed = jobs_query.filter_by(status='completed').count()
        rejected = jobs_query.filter_by(status='rejected').count()
        
        # Jobs by priority
        high_priority = jobs_query.filter_by(priority_level='high').count()
        medium_priority = jobs_query.filter_by(priority_level='middle').count()
        low_priority = jobs_query.filter_by(priority_level='low').count()
        
        # Recent jobs (last 7 days)
        seven_days_ago = datetime.now(jakarta_tz) - timedelta(days=7)
        recent_jobs = jobs_query.filter(CloudsphereJob.created_at >= seven_days_ago).count()
        
        return jsonify({
            'success': True,
            'data': {
                'total_jobs': total_jobs,
                'in_progress': in_progress,
                'pending_approval': pending_approval,
                'completed': completed,
                'rejected': rejected,
                'high_priority': high_priority,
                'medium_priority': medium_priority,
                'low_priority': low_priority,
                'recent_jobs': recent_jobs
            }
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@cloudsphere_bp.route('/api/jobs')
@login_required
@require_rnd_access
def get_jobs():
    """Get jobs with filtering and pagination"""
    try:
        user = current_user
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 12, type=int)
        search = request.args.get('search', '').strip()
        status_filter = request.args.get('status', '').strip()
        priority_filter = request.args.get('priority', '').strip()
        sample_type_filter = request.args.get('sample_type', '').strip()
        user_id_filter = request.args.get('user_id', type=int)
        
        # Debug logging
        print(f"DEBUG: get_jobs called with search='{search}', status='{status_filter}', priority='{priority_filter}', sample_type='{sample_type_filter}', user_id={user_id_filter}")
        print(f"DEBUG: User is_admin: {user.is_admin()}, User ID: {user.id}, User name: {user.name}")
        
        # Base query - build step by step to avoid complex JOIN issues
        try:
            if user.is_admin():
                # Admin can see all jobs, but can filter by specific user
                query = CloudsphereJob.query
                if user_id_filter:
                    query = query.filter_by(pic_id=user_id_filter)
                    print(f"DEBUG: Admin filtering by user_id: {user_id_filter}")
                else:
                    print("DEBUG: Admin base query (all jobs, no user filter)")
            else:
                # Non-admin users can only see their own jobs
                query = CloudsphereJob.query.filter_by(pic_id=user.id)
                print(f"DEBUG: Using user base query (only jobs for user {user.id})")
            
            # Apply search filter separately to avoid JOIN issues
            if search:
                search_term = f"%{search}%"
                print(f"DEBUG: Searching for term: '{search_term}'")
                
                # Get all job IDs first, then filter by PIC name separately
                job_ids_from_search = db.session.query(CloudsphereJob.id).filter(
                    or_(
                        CloudsphereJob.job_id.ilike(search_term),
                        CloudsphereJob.item_name.ilike(search_term),
                        CloudsphereJob.notes.ilike(search_term)
                    )
                ).subquery()
                
                # Get user IDs that match the search term
                matching_pic_ids = db.session.query(User.id).filter(
                    User.name.ilike(search_term)
                ).all()
                matching_pic_ids = [uid[0] for uid in matching_pic_ids]
                
                print(f"DEBUG: Found {len(matching_pic_ids)} matching PICs: {matching_pic_ids}")
                
                # Build the search condition
                if matching_pic_ids:
                    search_condition = or_(
                        CloudsphereJob.id.in_(job_ids_from_search),
                        CloudsphereJob.pic_id.in_(matching_pic_ids)
                    )
                else:
                    search_condition = CloudsphereJob.id.in_(job_ids_from_search)
                
                query = query.filter(search_condition)
                print(f"DEBUG: Applied search condition to query")
            else:
                print("DEBUG: No search term provided")
                
        except Exception as query_error:
            print(f"DEBUG: Error building query: {str(query_error)}")
            print(f"DEBUG: Query error type: {type(query_error).__name__}")
            import traceback
            print(f"DEBUG: Query traceback: {traceback.format_exc()}")
            return jsonify({'success': False, 'error': f'Query building error: {str(query_error)}'}), 500
        
        # Apply user_id filter if provided (for admin users)
        if user_id_filter:
            query = query.filter_by(pic_id=user_id_filter)
            print(f"DEBUG: Applied user_id filter: {user_id_filter}")
        
        # Apply other filters (status, priority, sample_type)
        if status_filter:
            query = query.filter_by(status=status_filter)
            print(f"DEBUG: Applied status filter: {status_filter}")
        
        if priority_filter:
            query = query.filter_by(priority_level=priority_filter)
            print(f"DEBUG: Applied priority filter: {priority_filter}")
        
        if sample_type_filter:
            query = query.filter_by(sample_type=sample_type_filter)
            print(f"DEBUG: Applied sample_type filter: {sample_type_filter}")
        
        # Order by created date descending
        query = query.order_by(CloudsphereJob.created_at.desc())
        print("DEBUG: Applied order by created_at desc")
        
        # Debug: Show final SQL query
        print(f"DEBUG: Final SQL query: {query}")
        
        # Paginate
        pagination = query.paginate(page=page, per_page=per_page, error_out=False)
        print(f"DEBUG: Pagination results - total: {pagination.total}, pages: {pagination.pages}, current page: {pagination.page}")
        
        jobs_data = []
        print(f"DEBUG: Processing {len(pagination.items)} jobs from pagination")
        
        for job in pagination.items:
            print(f"DEBUG: Processing job - ID: {job.id}, job_id: {job.job_id}, item_name: {job.item_name}, pic_id: {job.pic_id}")
            
            # Get progress
            progress = JobProgress.query.filter_by(job_id=job.id).first()
            completion_percentage = progress.completion_percentage if progress else 0
            
            # Get latest completed task
            latest_task = None
            if progress:
                latest_progress_task = JobProgressTask.query.filter_by(
                    job_progress_id=progress.id
                ).order_by(JobProgressTask.completed_at.desc()).first()
                if latest_progress_task:
                    latest_task = latest_progress_task.task.name if latest_progress_task.task else None
                    print(f"DEBUG: Latest task for job {job.id}: {latest_task}")
            
            pic_name = job.pic.name if job.pic else None
            print(f"DEBUG: Job {job.id} PIC name: {pic_name}")
            
            # Debug search matching
            if search:
                item_name_match = search.lower() in job.item_name.lower() if job.item_name else False
                job_id_match = search.lower() in job.job_id.lower() if job.job_id else False
                notes_match = search.lower() in job.notes.lower() if job.notes else False
                pic_name_match = search.lower() in pic_name.lower() if pic_name else False
                
                print(f"DEBUG: Search matching for job {job.id}:")
                print(f"  - item_name '{job.item_name}' contains '{search}': {item_name_match}")
                print(f"  - job_id '{job.job_id}' contains '{search}': {job_id_match}")
                print(f"  - notes '{job.notes}' contains '{search}': {notes_match}")
                print(f"  - pic_name '{pic_name}' contains '{search}': {pic_name_match}")
                print(f"  - Overall match: {item_name_match or job_id_match or notes_match or pic_name_match}")
            
            jobs_data.append({
                'id': job.id,
                'job_id': job.job_id,
                'item_name': job.item_name,
                'pic_name': pic_name,
                'priority_level': job.priority_level,
                'sample_type': job.sample_type,
                'deadline': job.deadline.strftime('%Y-%m-%d %H:%M') if job.deadline else None,
                'status': job.status,
                'completion_percentage': completion_percentage,
                'latest_task': latest_task,
                'created_at': job.created_at.strftime('%Y-%m-%d %H:%M') if job.created_at else None
            })
        
        print(f"DEBUG: Returning {len(jobs_data)} jobs to frontend")
        
        result = {
            'success': True,
            'data': jobs_data,
            'pagination': {
                'page': page,
                'per_page': per_page,
                'total': pagination.total,
                'pages': pagination.pages,
                'has_prev': pagination.has_prev,
                'has_next': pagination.has_next
            }
        }
        
        print(f"DEBUG: Final result: {result}")
        return jsonify(result)
    except Exception as e:
        print(f"DEBUG: Exception in get_jobs: {str(e)}")
        print(f"DEBUG: Exception type: {type(e).__name__}")
        import traceback
        print(f"DEBUG: Traceback: {traceback.format_exc()}")
        return jsonify({'success': False, 'error': str(e)}), 500

@cloudsphere_bp.route('/api/job', methods=['POST'])
@login_required
@require_rnd_access
def create_job():
    """Create new job"""
    try:
        data = request.get_json()
        print(f"DEBUG: Received job creation data: {data}")
        
        # Validate required fields
        required_fields = ['item_name', 'sample_type', 'priority_level', 'deadline', 'task_ids']
        for field in required_fields:
            if not data.get(field):
                print(f"DEBUG: Missing required field: {field}")
                return jsonify({'success': False, 'error': f'{field} is required'}), 400
        
        # Validate field values
        print(f"DEBUG: Field values - item_name: {data.get('item_name')}, sample_type: {data.get('sample_type')}, priority_level: {data.get('priority_level')}, deadline: {data.get('deadline')}, task_ids: {data.get('task_ids')}")
        
        # Validate pic_id
        pic_id = data.get('pic_id')
        print(f"DEBUG: Received pic_id: {pic_id}, type: {type(pic_id)}")
        
        if not pic_id or pic_id == '':
            pic_id = current_user.id  # Fallback to current user if not provided
            print(f"DEBUG: Using current user ID as pic_id: {pic_id}")
        elif not isinstance(pic_id, int):
            try:
                pic_id = int(pic_id)
                print(f"DEBUG: Converted pic_id to int: {pic_id}")
            except (ValueError, TypeError):
                print(f"DEBUG: Invalid pic_id format: {pic_id}")
                return jsonify({'success': False, 'error': 'Invalid pic_id format'}), 400
        
        # Additional validation for pic_id
        if pic_id <= 0:
            print(f"DEBUG: Invalid pic_id value: {pic_id}")
            return jsonify({'success': False, 'error': 'Invalid pic_id value'}), 400
        
        # Verify user exists
        pic_user = User.query.get(pic_id)
        if not pic_user:
            print(f"DEBUG: PIC user not found: {pic_id}")
            return jsonify({'success': False, 'error': f'User with ID {pic_id} not found'}), 400
        
        # Parse start_datetime if provided
        start_date = None
        if data.get('start_datetime'):
            try:
                # Handle different datetime-local formats
                datetime_str = data['start_datetime']
                print(f"DEBUG: Parsing start_datetime: {datetime_str}")
                print(f"DEBUG: Type of start_datetime: {type(datetime_str)}")
                
                # Check for empty string
                if not datetime_str or datetime_str.strip() == '':
                    return jsonify({'success': False, 'error': 'start_datetime cannot be empty'}), 400
                
                # Check for invalid format like "T19:01" (missing date part)
                if datetime_str.startswith('T'):
                    return jsonify({'success': False, 'error': 'Invalid start_datetime format: missing date part'}), 400
                
                if 'T' in datetime_str:
                    # Format: YYYY-MM-DDTHH:MM or YYYY-MM-DDTHH:MM:SS
                    time_part = datetime_str.split('T')[1]
                    if ':' in time_part:
                        if len(time_part.split(':')) == 3:
                            # Format with seconds: YYYY-MM-DDTHH:MM:SS
                            start_date = datetime.strptime(datetime_str, '%Y-%m-%dT%H:%M:%S')
                        else:
                            # Format without seconds: YYYY-MM-DDTHH:MM
                            start_date = datetime.strptime(datetime_str, '%Y-%m-%dT%H:%M')
                    else:
                        # Invalid format
                        raise ValueError("Invalid datetime format - missing time components")
                else:
                    # Format without T: YYYY-MM-DD HH:MM
                    start_date = datetime.strptime(datetime_str, '%Y-%m-%d %H:%M')
                
                # Convert to Jakarta timezone
                start_date = jakarta_tz.localize(start_date)
                    
                print(f"DEBUG: Successfully parsed start_datetime: {start_date}")
            except ValueError as e:
                print(f"DEBUG: Error parsing start_datetime: {str(e)}")
                return jsonify({'success': False, 'error': f'Invalid start_datetime format: {str(e)}'}), 400
        
        # Parse deadline
        deadline_date = None
        try:
            deadline_str = data['deadline']
            print(f"DEBUG: Parsing deadline: {deadline_str}")
            print(f"DEBUG: Type of deadline: {type(deadline_str)}")
            
            # Check for empty string
            if not deadline_str or deadline_str.strip() == '':
                return jsonify({'success': False, 'error': 'deadline cannot be empty'}), 400
            
            # Check for invalid format like "T19:01" (missing date part)
            if deadline_str.startswith('T'):
                return jsonify({'success': False, 'error': 'Invalid deadline format: missing date part'}), 400
            
            if 'T' in deadline_str:
                # Format: YYYY-MM-DDTHH:MM or YYYY-MM-DDTHH:MM:SS
                time_part = deadline_str.split('T')[1]
                if ':' in time_part:
                    if len(time_part.split(':')) == 3:
                        # Format with seconds: YYYY-MM-DDTHH:MM:SS
                        deadline_date = datetime.strptime(deadline_str, '%Y-%m-%dT%H:%M:%S')
                    else:
                        # Format without seconds: YYYY-MM-DDTHH:MM
                        deadline_date = datetime.strptime(deadline_str, '%Y-%m-%dT%H:%M')
                else:
                    # Invalid format
                    raise ValueError("Invalid datetime format - missing time components")
            else:
                # Format without T: YYYY-MM-DD
                deadline_date = datetime.strptime(deadline_str, '%Y-%m-%d')
            
            # Convert to Jakarta timezone
            deadline_date = jakarta_tz.localize(deadline_date)
                
            print(f"DEBUG: Successfully parsed deadline: {deadline_date}")
        except ValueError as e:
            print(f"DEBUG: Error parsing deadline: {str(e)}")
            return jsonify({'success': False, 'error': f'Invalid deadline format: {str(e)}'}), 400
        
        # Create job
        job = CloudsphereJob(
            job_id=generate_job_id(),
            item_name=data['item_name'],
            sample_type=data['sample_type'],
            priority_level=data['priority_level'],
            deadline=deadline_date,
            start_datetime=start_date,  # Fixed: use start_datetime instead of start_date
            pic_id=pic_id,  # Use validated pic_id
            notes=data.get('notes', ''),
            status='in_progress'
        )
        
        print(f"DEBUG: Created job with deadline: {deadline_date}, start_datetime: {start_date}")
        print(f"DEBUG: Job object before commit: {job}")
        print(f"DEBUG: Job item_name: {job.item_name}")
        print(f"DEBUG: Job sample_type: {job.sample_type}")
        print(f"DEBUG: Job priority_level: {job.priority_level}")
        print(f"DEBUG: Job pic_id: {job.pic_id}")
        
        db.session.add(job)
        db.session.flush()  # Get job ID
        
        # Create job tasks
        task_ids = data['task_ids']
        print(f"DEBUG: Processing task_ids: {task_ids}")
        print(f"DEBUG: Type of task_ids: {type(task_ids)}")
        
        if not task_ids:
            print("DEBUG: No task_ids provided")
            return jsonify({'success': False, 'error': 'At least one task must be selected'}), 400
        
        # Ensure task_ids is a list
        if isinstance(task_ids, int):
            task_ids = [task_ids]
        elif not isinstance(task_ids, list):
            print(f"DEBUG: task_ids is not an array: {type(task_ids)}")
            return jsonify({'success': False, 'error': 'task_ids must be an array'}), 400
        
        # Validate each task_id
        for task_id in task_ids:
            print(f"DEBUG: Validating task_id: {task_id}")
            print(f"DEBUG: Type of task_id: {type(task_id)}")
            if not isinstance(task_id, int) or task_id <= 0:
                print(f"DEBUG: Invalid task_id format: {task_id}")
                return jsonify({'success': False, 'error': f'Invalid task_id: {task_id}'}), 400
            
            # Check if task exists
            task = Task.query.get(task_id)
            if not task:
                print(f"DEBUG: Task not found: {task_id}")
                return jsonify({'success': False, 'error': f'Task with ID {task_id} not found'}), 400
            
            job_task = JobTask(job_id=job.id, task_id=task_id)
            db.session.add(job_task)
            print(f"DEBUG: Added job_task for task_id: {task_id}")
        
        # Create job progress
        job_progress = JobProgress(job_id=job.id)
        db.session.add(job_progress)
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Job created successfully',
            'data': {
                'id': job.id,
                'job_id': job.job_id
            }
        })
    except Exception as e:
        db.session.rollback()
        print(f"DEBUG: Exception in create_job: {str(e)}")
        print(f"DEBUG: Exception type: {type(e).__name__}")
        import traceback
        print(f"DEBUG: Traceback: {traceback.format_exc()}")
        
        # Check if it's a validation error
        if "validation" in str(e).lower() or "required" in str(e).lower():
            return jsonify({'success': False, 'error': str(e)}), 400
        else:
            return jsonify({'success': False, 'error': str(e)}), 500

@cloudsphere_bp.route('/api/job/<int:job_id>', methods=['PUT'])
@login_required
@require_rnd_access
def update_job(job_id):
        """Update existing job"""
        try:
            if not current_user.is_admin():
                return jsonify({'success': False, 'error': 'Admin access required'}), 403
                
            data = request.get_json()
            print(f"DEBUG: Received job update data: {data}")
            
            # Get existing job
            job = CloudsphereJob.query.get_or_404(job_id)
            
            # Validate required fields
            required_fields = ['item_name', 'sample_type', 'priority_level', 'deadline', 'task_ids']
            for field in required_fields:
                if not data.get(field):
                    print(f"DEBUG: Missing required field: {field}")
                    return jsonify({'success': False, 'error': f'{field} is required'}), 400
            
            # Validate pic_id
            pic_id = data.get('pic_id')
            print(f"DEBUG: Received pic_id: {pic_id}, type: {type(pic_id)}")
            
            if not pic_id or pic_id == '':
                pic_id = job.pic_id  # Keep existing PIC if not provided
                print(f"DEBUG: Using existing pic_id: {pic_id}")
            elif not isinstance(pic_id, int):
                try:
                    pic_id = int(pic_id)
                    print(f"DEBUG: Converted pic_id to int: {pic_id}")
                except (ValueError, TypeError):
                    print(f"DEBUG: Invalid pic_id format: {pic_id}")
                    return jsonify({'success': False, 'error': 'Invalid pic_id format'}), 400
            
            # Additional validation for pic_id
            if pic_id <= 0:
                print(f"DEBUG: Invalid pic_id value: {pic_id}")
                return jsonify({'success': False, 'error': 'Invalid pic_id value'}), 400
            
            # Verify user exists
            pic_user = User.query.get(pic_id)
            if not pic_user:
                print(f"DEBUG: PIC user not found: {pic_id}")
                return jsonify({'success': False, 'error': f'User with ID {pic_id} not found'}), 400
            
            # Parse start_datetime if provided
            start_date = None
            if data.get('start_datetime'):
                try:
                    # Handle different datetime-local formats
                    datetime_str = data['start_datetime']
                    print(f"DEBUG: Parsing start_datetime: {datetime_str}")
                    print(f"DEBUG: Type of start_datetime: {type(datetime_str)}")
                    
                    # Check for empty string
                    if not datetime_str or datetime_str.strip() == '':
                        return jsonify({'success': False, 'error': 'start_datetime cannot be empty'}), 400
                    
                    # Check for invalid format like "T19:01" (missing date part)
                    if datetime_str.startswith('T'):
                        return jsonify({'success': False, 'error': 'Invalid start_datetime format: missing date part'}), 400
                    
                    if 'T' in datetime_str:
                        # Format: YYYY-MM-DDTHH:MM or YYYY-MM-DDTHH:MM:SS
                        time_part = datetime_str.split('T')[1]
                        if ':' in time_part:
                            if len(time_part.split(':')) == 3:
                                # Format with seconds: YYYY-MM-DDTHH:MM:SS
                                start_date = datetime.strptime(datetime_str, '%Y-%m-%dT%H:%M:%S')
                            else:
                                # Format without seconds: YYYY-MM-DDTHH:MM
                                start_date = datetime.strptime(datetime_str, '%Y-%m-%dT%H:%M')
                        else:
                            # Invalid format
                            raise ValueError("Invalid datetime format - missing time components")
                    else:
                        # Format without T: YYYY-MM-DD HH:MM
                        start_date = datetime.strptime(datetime_str, '%Y-%m-%d %H:%M')
                    
                    # Convert to Jakarta timezone
                    start_date = jakarta_tz.localize(start_date)
                        
                    print(f"DEBUG: Successfully parsed start_datetime: {start_date}")
                except ValueError as e:
                    print(f"DEBUG: Error parsing start_datetime: {str(e)}")
                    return jsonify({'success': False, 'error': f'Invalid start_datetime format: {str(e)}'}), 400
            
            # Parse deadline
            deadline_date = None
            try:
                deadline_str = data['deadline']
                print(f"DEBUG: Parsing deadline: {deadline_str}")
                print(f"DEBUG: Type of deadline: {type(deadline_str)}")
                
                # Check for empty string
                if not deadline_str or deadline_str.strip() == '':
                    return jsonify({'success': False, 'error': 'deadline cannot be empty'}), 400
                
                # Check for invalid format like "T19:01" (missing date part)
                if deadline_str.startswith('T'):
                    return jsonify({'success': False, 'error': 'Invalid deadline format: missing date part'}), 400
                
                if 'T' in deadline_str:
                    # Format: YYYY-MM-DDTHH:MM or YYYY-MM-DDTHH:MM:SS
                    time_part = deadline_str.split('T')[1]
                    if ':' in time_part:
                        if len(time_part.split(':')) == 3:
                            # Format with seconds: YYYY-MM-DDTHH:MM:SS
                            deadline_date = datetime.strptime(deadline_str, '%Y-%m-%dT%H:%M:%S')
                        else:
                            # Format without seconds: YYYY-MM-DDTHH:MM
                            deadline_date = datetime.strptime(deadline_str, '%Y-%m-%dT%H:%M')
                    else:
                        # Invalid format
                        raise ValueError("Invalid datetime format - missing time components")
                else:
                    # Format without T: YYYY-MM-DD
                    deadline_date = datetime.strptime(deadline_str, '%Y-%m-%d')
                
                # Convert to Jakarta timezone
                deadline_date = jakarta_tz.localize(deadline_date)
                    
                print(f"DEBUG: Successfully parsed deadline: {deadline_date}")
            except ValueError as e:
                print(f"DEBUG: Error parsing deadline: {str(e)}")
                return jsonify({'success': False, 'error': f'Invalid deadline format: {str(e)}'}), 400
            
            # Update job fields
            job.item_name = data['item_name']
            job.sample_type = data['sample_type']
            job.priority_level = data['priority_level']
            job.deadline = deadline_date
            job.start_datetime = start_date
            job.pic_id = pic_id
            job.notes = data.get('notes', '')
            job.status = data.get('status', job.status)
            job.updated_at = datetime.now(jakarta_tz)
            
            print(f"DEBUG: Updated job with deadline: {deadline_date}, start_datetime: {start_date}")
            
            # Update job tasks - remove existing tasks and add new ones
            JobTask.query.filter_by(job_id=job_id).delete()
            
            # Create new job tasks
            task_ids = data['task_ids']
            print(f"DEBUG: Processing task_ids: {task_ids}")
            print(f"DEBUG: Type of task_ids: {type(task_ids)}")
            
            if not task_ids:
                print("DEBUG: No task_ids provided")
                return jsonify({'success': False, 'error': 'At least one task must be selected'}), 400
            
            # Ensure task_ids is a list
            if isinstance(task_ids, int):
                task_ids = [task_ids]
            elif not isinstance(task_ids, list):
                print(f"DEBUG: task_ids is not an array: {type(task_ids)}")
                return jsonify({'success': False, 'error': 'task_ids must be an array'}), 400
            
            # Validate each task_id
            for task_id in task_ids:
                print(f"DEBUG: Validating task_id: {task_id}")
                print(f"DEBUG: Type of task_id: {type(task_id)}")
                if not isinstance(task_id, int) or task_id <= 0:
                    print(f"DEBUG: Invalid task_id format: {task_id}")
                    return jsonify({'success': False, 'error': f'Invalid task_id: {task_id}'}), 400
                
                # Check if task exists
                task = Task.query.get(task_id)
                if not task:
                    print(f"DEBUG: Task not found: {task_id}")
                    return jsonify({'success': False, 'error': f'Task with ID {task_id} not found'}), 400
                
                job_task = JobTask(job_id=job.id, task_id=task_id)
                db.session.add(job_task)
                print(f"DEBUG: Added job_task for task_id: {task_id}")
            
            db.session.commit()
            
            return jsonify({
                'success': True,
                'message': 'Job updated successfully',
                'data': {
                    'id': job.id,
                    'job_id': job.job_id
                }
            })
        except Exception as e:
            db.session.rollback()
            print(f"DEBUG: Exception in update_job: {str(e)}")
            print(f"DEBUG: Exception type: {type(e).__name__}")
            import traceback
            print(f"DEBUG: Traceback: {traceback.format_exc()}")
            
            # Check if it's a validation error
            if "validation" in str(e).lower() or "required" in str(e).lower():
                return jsonify({'success': False, 'error': str(e)}), 400
            else:
                return jsonify({'success': False, 'error': str(e)}), 500

@cloudsphere_bp.route('/api/job/<int:job_id>', methods=['DELETE'])
@login_required
@require_rnd_access
def delete_job(job_id):
        """Delete job"""
        try:
            if not current_user.is_admin():
                return jsonify({'success': False, 'error': 'Admin access required'}), 403
                
            # Get job
            job = CloudsphereJob.query.get_or_404(job_id)
            
            # Get job progress to delete related records
            progress = JobProgress.query.filter_by(job_id=job_id).first()
            
            if progress:
                # Delete evidence files - Fixed: EvidenceFile is linked to job_id, not job_progress_id
                EvidenceFile.query.filter_by(job_id=job_id).delete()
                
                # Delete progress tasks
                JobProgressTask.query.filter_by(job_progress_id=progress.id).delete()
                
                # Delete job progress
                db.session.delete(progress)
            
            # Delete job tasks
            JobTask.query.filter_by(job_id=job_id).delete()
            
            # Delete job
            db.session.delete(job)
            
            db.session.commit()
            
            return jsonify({
                'success': True,
                'message': 'Job deleted successfully'
            })
        except Exception as e:
            db.session.rollback()
            print(f"DEBUG: Exception in delete_job: {str(e)}")
            print(f"DEBUG: Exception type: {type(e).__name__}")
            import traceback
            print(f"DEBUG: Traceback: {traceback.format_exc()}")
            return jsonify({'success': False, 'error': str(e)}), 500

@cloudsphere_bp.route('/api/job/<int:job_id>')
@login_required
@require_rnd_access
def get_job(job_id):
    """Get job details"""
    try:
        job = CloudsphereJob.query.get_or_404(job_id)
        
        # Get job tasks
        job_tasks = db.session.query(Task).join(JobTask).filter(
            JobTask.job_id == job_id
        ).all()
        
        # Get job progress
        progress = JobProgress.query.filter_by(job_id=job_id).first()
        
        # Get progress tasks
        progress_tasks = []
        if progress:
            progress_tasks_query = db.session.query(
                JobProgressTask, Task
            ).join(Task).filter(
                JobProgressTask.job_progress_id == progress.id
            ).all()
            
            for pt, task in progress_tasks_query:
                progress_tasks.append({
                    'id': pt.id,
                    'task_id': task.id,
                    'task_name': task.name,
                    'category_name': task.category.name if task.category else None,
                    'is_completed': pt.is_completed,
                    'completed_at': pt.completed_at.strftime('%Y-%m-%d %H:%M') if pt.completed_at else None,
                    'notes': pt.notes
                })
        
        # Get evidence files
        evidence_files = []
        # Fixed: EvidenceFile is linked to job_id, not job_progress_id
        files = EvidenceFile.query.filter_by(job_id=job_id).all()
        for file in files:
            evidence_files.append({
                'id': file.id,
                'filename': file.filename,
                'original_filename': file.original_filename,
                'file_type': file.file_type,
                'file_size': file.file_size,
                'uploaded_at': file.uploaded_at.strftime('%Y-%m-%d %H:%M') if file.uploaded_at else None,
                'uploaded_by': file.uploaded_by.name if file.uploaded_by else None
            })
        
        job_data = {
            'id': job.id,
            'job_id': job.job_id,
            'item_name': job.item_name,
            'sample_type': job.sample_type,
            'priority_level': job.priority_level,
            'deadline': job.deadline.strftime('%Y-%m-%dT%H:%M') if job.deadline else None,
            'start_date': job.start_datetime.strftime('%Y-%m-%d %H:%M') if job.start_datetime else None,
            'pic_id': job.pic_id,
            'pic_name': job.pic.name if job.pic else None,
            'status': job.status,
            'notes': job.notes,
            'created_at': job.created_at.strftime('%Y-%m-%d %H:%M') if job.created_at else None,
            'updated_at': job.updated_at.strftime('%Y-%m-%d %H:%M') if job.updated_at else None,
            'completion_percentage': progress.completion_percentage if progress else 0,
            'tasks': [{'id': task.id, 'task_name': task.name, 'category_name': task.category.name if task.category else None} for task in job_tasks],
            'progress_tasks': progress_tasks,
            'evidence_files': evidence_files
        }
        
        return jsonify({
            'success': True,
            'data': job_data
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@cloudsphere_bp.route('/api/task/<int:task_id>/complete', methods=['POST'])
@login_required
@require_rnd_access
def complete_task(task_id):
    """Mark task as completed"""
    try:
        data = request.get_json()
        job_id = data.get('job_id')
        notes = data.get('notes', '')
        
        # Get job and progress
        job = CloudsphereJob.query.get_or_404(job_id)
        progress = JobProgress.query.filter_by(job_id=job_id).first()
        
        if not progress:
            return jsonify({'success': False, 'error': 'Job progress not found'}), 404
        
        # Check if task is already completed
        existing_progress = JobProgressTask.query.filter_by(
            job_progress_id=progress.id,
            task_id=task_id
        ).first()
        
        if existing_progress:
            return jsonify({'success': False, 'error': 'Task already completed'}), 400
        
        # Mark task as completed
        progress_task = JobProgressTask(
            job_progress_id=progress.id,
            task_id=task_id,
            is_completed=True,
            completed_at=datetime.now(jakarta_tz),
            notes=notes
        )
        db.session.add(progress_task)
        
        # Update completion percentage
        total_tasks = db.session.query(JobTask).filter_by(job_id=job_id).count()
        completed_tasks = db.session.query(JobProgressTask).filter_by(
            job_progress_id=progress.id,
            is_completed=True
        ).count()
        
        # Note: completion_percentage is a calculated property, no need to set it manually
        new_percentage = (completed_tasks / total_tasks) * 100 if total_tasks > 0 else 0
        
        # Check if all tasks are completed
        if new_percentage >= 100:
            job.status = 'pending_approval'
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Task completed successfully',
            'data': {
                'completion_percentage': new_percentage,
                'job_status': job.status
            }
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500

@cloudsphere_bp.route('/api/upload-evidence', methods=['POST'])
@login_required
@require_rnd_access
def upload_evidence():
    """Upload evidence file"""
    try:
        if 'file' not in request.files:
            return jsonify({'success': False, 'error': 'No file provided'}), 400
        
        file = request.files['file']
        job_id = request.form.get('job_id')
        
        if not job_id:
            return jsonify({'success': False, 'error': 'Job ID required'}), 400
        
        if file.filename == '':
            return jsonify({'success': False, 'error': 'No file selected'}), 400
        
        # Get job progress
        progress = JobProgress.query.filter_by(job_id=job_id).first()
        if not progress:
            return jsonify({'success': False, 'error': 'Job progress not found'}), 404
        
        # Check file type
        filename = secure_filename(file.filename)
        file_extension = filename.rsplit('.', 1)[1].lower() if '.' in filename else ''
        
        # Allowed extensions
        photo_extensions = {'jpg', 'jpeg', 'png', 'gif'}
        document_extensions = {'pdf', 'docx', 'xlsx', 'doc', 'xls'}
        
        if file_extension not in photo_extensions and file_extension not in document_extensions:
            return jsonify({'success': False, 'error': 'File type not allowed'}), 400
        
        # Determine file type
        file_type = 'photo' if file_extension in photo_extensions else 'document'
        
        # Create upload directory if it doesn't exist
        upload_dir = os.path.join('instance', 'uploads', 'cloudsphere_evidence')
        os.makedirs(upload_dir, exist_ok=True)
        
        # Generate unique filename
        timestamp = datetime.now(jakarta_tz).strftime('%Y%m%d_%H%M%S')
        unique_filename = f"cloudsphere_evidence_{timestamp}_{filename}"
        
        # Save file
        file_path = os.path.join(upload_dir, unique_filename)
        file.save(file_path)
        
        # Save to database
        evidence = EvidenceFile(
            job_id=job_id,
            filename=unique_filename,
            original_filename=filename,
            file_path=file_path,
            file_type=file_type,
            file_size=os.path.getsize(file_path),
            uploaded_by=current_user.id
        )
        
        db.session.add(evidence)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'File uploaded successfully',
            'data': {
                'id': evidence.id,
                'filename': unique_filename,
                'original_filename': filename,
                'file_type': file_type,
                'file_size': evidence.file_size
            }
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500

@cloudsphere_bp.route('/api/approve-job/<int:job_id>', methods=['POST'])
@login_required
@require_rnd_access
def approve_job(job_id):
    """Approve job"""
    try:
        if not current_user.is_admin():
            return jsonify({'success': False, 'error': 'Admin access required'}), 403
        
        data = request.get_json()
        job = CloudsphereJob.query.get_or_404(job_id)
        
        if job.status != 'pending_approval':
            return jsonify({'success': False, 'error': 'Job is not pending approval'}), 400
        
        job.status = 'completed'
        # Use rejection_notes for both approval and rejection
        job.rejection_notes = data.get('admin_notes', '')
        job.rejection_notes = data.get('admin_notes', '')  # Also update rejection_notes for consistency
        job.updated_at = datetime.now(jakarta_tz)
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Job approved successfully'
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500

@cloudsphere_bp.route('/api/reject-job/<int:job_id>', methods=['POST'])
@login_required
@require_rnd_access
def reject_job(job_id):
    """Reject job"""
    try:
        if not current_user.is_admin():
            return jsonify({'success': False, 'error': 'Admin access required'}), 403
        
        data = request.get_json()
        job = CloudsphereJob.query.get_or_404(job_id)
        
        if job.status != 'pending_approval':
            return jsonify({'success': False, 'error': 'Job is not pending approval'}), 400
        
        job.status = 'rejected'
        # Use rejection_notes for both approval and rejection
        job.rejection_notes = data.get('admin_notes', '')
        job.rejection_notes = data.get('admin_notes', '')  # Also update rejection_notes for consistency
        job.updated_at = datetime.now(jakarta_tz)
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Job rejected successfully'
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500

@cloudsphere_bp.route('/api/task-categories')
@login_required
@require_rnd_access
def get_task_categories():
    """Get all task categories with tasks"""
    try:
        categories = TaskCategory.query.order_by(TaskCategory.name).all()
        
        categories_data = []
        for category in categories:
            tasks = Task.query.filter_by(category_id=category.id).order_by(Task.name).all()
            categories_data.append({
                'id': category.id,
                'category_name': category.name,
                'tasks': [{'id': task.id, 'task_name': task.name} for task in tasks]
            })
        
        return jsonify({
            'success': True,
            'data': categories_data
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@cloudsphere_bp.route('/api/users')
@login_required
@require_rnd_access
def get_users():
    """Get users filtered by division (for R&D users)"""
    try:
        division_id = request.args.get('division_id', type=int)
        
        if division_id:
            users = User.query.filter_by(division_id=division_id, is_active=True).order_by(User.name).all()
        else:
            users = User.query.filter_by(is_active=True).order_by(User.name).all()
        
        users_data = []
        for user in users:
            users_data.append({
                'id': user.id,
                'name': user.name,
                'username': user.username,
                'division_name': user.division.name if user.division else None
            })
        
        return jsonify({
            'success': True,
            'data': users_data
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@cloudsphere_bp.route('/api/download-evidence/<int:file_id>')
@login_required
@require_rnd_access
def download_evidence(file_id):
    """Download evidence file"""
    try:
        evidence = EvidenceFile.query.get_or_404(file_id)
        return send_file(
            evidence.file_path,
            as_attachment=True,
            download_name=evidence.original_filename
        )
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@cloudsphere_bp.route('/api/export-job/<int:job_id>/pdf')
@login_required
@require_rnd_access
def export_job_pdf(job_id):
    """Export job as PDF"""
    try:
        job = CloudsphereJob.query.get_or_404(job_id)
        
        if job.status != 'completed':
            return jsonify({'success': False, 'error': 'Only completed jobs can be exported'}), 400
        
        # This would require additional PDF generation library
        # For now, return a placeholder response
        return jsonify({
            'success': False,
            'error': 'PDF export not implemented yet'
        }), 501
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

# Initialize task categories and tasks
def init_cloudsphere_data():
    """Initialize default task categories and tasks"""
    with cloudsphere_bp.app_context():
        try:
            # Check if categories already exist
            if TaskCategory.query.first():
                return
            
            # Create categories and tasks
            categories_data = [
                {
                    'category_name': 'Blank',
                    'description': 'Tasks for Blank sample development',
                    'tasks': [
                        'Check EPSON Blue Print', #Initial Design & Documentation (Step 2)
                        'Create Technical Drawing', #Initial Design & Documentation (Step 2)
                        'Create Plotter', #Initial Design & Documentation (Step 2)
                        'Fitting Result Plotter', #Initial Design & Documentation (Step 2)
                        'Create Simulation Layout', #Initial Design & Documentation (Step 2)
                        'Create LPD Pisau & Millar', #Initial Design & Documentation (Step 2)
                        'Create Material & Process Memo to PPIC', #Physical Sample Creation & Assembly (Step 3)
                        'Laminator Process', #Physical Sample Creation & Assembly (Step 3)
                        'Diecut Process & Fitting', #Physical Sample Creation & Assembly (Step 3)
                        'Lamina Process & Fitting', #Physical Sample Creation & Assembly (Step 3)
                        'Pack & Send Sample', #Physical Sample Creation & Assembly (Step 3)
                        'Process CoA to QC', #Quality Testing & Final Validation (Step 4)
                        'Moisture Test', #Quality Testing & Final Validation (Step 4)
                        'Pushpull Test', #Quality Testing & Final Validation (Step 4)
                        'Box Compression Test', #Quality Testing & Final Validation (Step 4)
                        'Process Data PAC & Send Email' #Quality Testing & Final Validation (Step 4)
                    ]
                },
                {
                    'category_name': 'Mastercard',
                    'description': 'Tasks for Mastercard development',
                    'tasks': [
                        'Receiving LPM', #Mastercard Document Control & Release (Step 2)
                        'Create Mastercard', #Mastercard Document Control & Release (Step 2)
                        'Printout Mastercard', #Mastercard Document Control & Release (Step 2)
                        'Approval Mastercard', #Mastercard Document Control & Release (Step 2)
                        'Scan & Copy Mastercard', #Mastercard Document Control & Release (Step 2)
                        'Handover Mastercard to PPIC' #Mastercard Document Control & Release (Step 2)
                    ]
                },                
                {
                    'category_name': 'RoHS Regular ICB',
                    'description': 'Tasks for RoHS Regular ICB compliance',
                    'tasks': [
                        'Approval Press Offset', #Print Quality Approval (Step 2)
                        'Approval Press DFS', #Print Quality Approval (Step 2)
                        'Laminator Process', #Sample Production & Preparation (Step 3)
                        'Diecut Process & Fitting', #Sample Production & Preparation (Step 3)
                        'Lamina Process & Fitting', #Sample Production & Preparation (Step 3)
                        'Pack & Send Sample', #Sample Production & Preparation (Step 3)          
                        'Process CoA to QC', #Quality Testing & Final Validation (Step 4)
                        'Moisture Test', #Quality Testing & Final Validation (Step 4)
                        'Pushpull Test', #Quality Testing & Final Validation (Step 4)
                        'Box Compression Test', #Quality Testing & Final Validation (Step 4)
                        'Process Data PAC & Send Email' #Quality Testing & Final Validation (Step 4)
                    ]
                },
                {
                    'category_name': 'RoHS Ribbon',
                    'description': 'Tasks for RoHS Ribbon compliance',
                    'tasks': [
                        'Approval Press Offset', #Print & Spot UV Quality Approval (Step 2)
                        'Approval Varnish / Spot UV', #Print & Spot UV Quality Approval (Step 2)
                        'Diecut Process & Fitting', #Sample Production & Preparation (Step 3)
                        'Glue Process & Fitting', #Sample Production & Preparation (Step 3)
                        'Pack & Send Sample', #Sample Production & Preparation (Step 3)             
                        'Process CoA to QC', #Quality Testing & Final Validation (Step 4)
                        'Moisture Test', #Quality Testing & Final Validation (Step 4)
                        'Pushpull Test', #Quality Testing & Final Validation (Step 4)
                        'Process Data PAC & Send Email' #Quality Testing & Final Validation (Step 4)
                    ]
                },
                {
                    'category_name': 'Polymer Ribbon',
                    'description': 'Tasks for Polymer Ribbon compliance',
                    'tasks': [
                        'Create Data Polymer & Millar', #Material Planning & Procurement (Step 2)
                        'Create New Item Code Polymer', #Material Planning & Procurement (Step 2)
                        'Create Memo PO to Supplier', #Material Planning & Procurement (Step 2)
                        'Email Order Polymer to Supplier ', #Material Planning & Procurement (Step 2)
                        'Request Millar to DC Service', #Material Planning & Procurement (Step 2)
                        'Check Incoming Polymer & Handover to Varnish' #Material Receiving & Handover (Step 3)                     
                    ]
                }
            ]
            
            for cat_data in categories_data:
                category = TaskCategory(name=cat_data['category_name'])
                db.session.add(category)
                db.session.flush()  # Get category ID
                
                for task_name in cat_data['tasks']:
                    task = Task(
                        category_id=category.id,
                        name=task_name
                    )
                    db.session.add(task)
            
            db.session.commit()
            
        except Exception as e:
            print(f"Error initializing Cloudsphere data: {e}")
            db.session.rollback()