from datetime import datetime, timedelta
from flask import Blueprint, jsonify, request, render_template, send_file, current_app
from flask_login import login_required, current_user
from functools import wraps
from models import db, User, UniversalNotification
from models_rnd import (
    RNDJob, RNDProgressStep, RNDProgressTask, RNDJobProgressAssignment,
    RNDJobTaskAssignment, RNDLeadTimeTracking, RNDEvidenceFile, RNDTaskCompletion,
    RNDJobNote, RNDFlowConfiguration, RNDFlowStep
)
from models_rnd_external import RNDExternalTime
from services.notification_service import NotificationDispatcher
from werkzeug.utils import secure_filename
import os
import pytz
import io
from PIL import Image
from sqlalchemy import and_, or_, func, text
import logging

# Setup logging
logger = logging.getLogger(__name__)

# Create Blueprint
rnd_cloudsphere_bp = Blueprint('rnd_cloudsphere', __name__, url_prefix='/rnd-cloudsphere')

# Jakarta timezone
jakarta_tz = pytz.timezone('Asia/Jakarta')

# Helper function to generate job ID
def generate_rnd_job_id():
    """Generate unique job ID with format RND-YYYYMMDD-XXX"""
    now = datetime.now(jakarta_tz)
    date_str = now.strftime('%Y%m%d')
    
    # Get latest job for today
    latest_job = RNDJob.query.filter(
        RNDJob.job_id.like(f'RND-{date_str}-%')
    ).order_by(RNDJob.job_id.desc()).first()
    
    if latest_job:
        # Extract sequence number from latest job ID
        sequence = int(latest_job.job_id.split('-')[-1]) + 1
    else:
        sequence = 1
    
    return f'RND-{date_str}-{sequence:03d}'

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

# Helper function to ensure job status is synced with completion
def sync_job_status(job):
    """
    Ensure job.status is synced with completion_percentage.
    Triggers the auto-sync property and commits if changes were made.
    """
    try:
        # Access completion_percentage triggers auto-sync property
        pct = job.completion_percentage
        
        # If property made changes, commit them
        if db.session.is_modified(job):
            db.session.commit()
            print(f"DEBUG: Job status synced for {job.job_id}: {pct}% completion, status={job.status}")
    except Exception as e:
        print(f"ERROR in sync_job_status: {e}")

# R&D Cloudsphere Routes
@rnd_cloudsphere_bp.route('/')
@login_required
@require_rnd_access
def rnd_cloudsphere_home():
    """Render R&D Cloudsphere home page"""
    return render_template('rnd_cloudsphere.html')

@rnd_cloudsphere_bp.route('/job/<int:job_id>')
@login_required
@require_rnd_access
def rnd_job_detail(job_id):
    """Render R&D job detail page"""
    job = RNDJob.query.get_or_404(job_id)
    return render_template('rnd_cloudsphere_detail.html', job=job)

@rnd_cloudsphere_bp.route('/flow-configuration')
@login_required
@require_rnd_access
def rnd_flow_configuration():
    """Render R&D flow configuration management page"""
    return render_template('rnd_flow_configuration.html')

@rnd_cloudsphere_bp.route('/dashboard')
@login_required
@require_rnd_access
def rnd_cloudsphere_dashboard():
    """Render R&D Cloudsphere dashboard"""
    return render_template('rnd_cloudsphere_dashboard.html')

# API Routes

# Dashboard Analytics API Routes
@rnd_cloudsphere_bp.route('/api/dashboard-available-periods')
@login_required
@require_rnd_access
def get_dashboard_available_periods():
    """Get available years from RND jobs"""
    try:
        years = db.session.query(
            func.extract('year', RNDJob.started_at).label('year')
        ).distinct().order_by(func.extract('year', RNDJob.started_at).desc()).all()
        
        year_list = [int(y.year) for y in years if y.year]
        
        return jsonify({
            'success': True,
            'years': year_list
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@rnd_cloudsphere_bp.route('/api/dashboard-available-months')
@login_required
@require_rnd_access
def get_dashboard_available_months():
    """Get available months for selected year"""
    try:
        year = request.args.get('year', type=int)
        
        if not year:
            # If no year provided, return all available months (like CTP dashboard)
            months = db.session.query(
                func.extract('month', RNDJob.started_at).label('month')
            ).distinct().order_by(func.extract('month', RNDJob.started_at)).all()
        else:
            # Get months for specific year
            months = db.session.query(
                func.extract('month', RNDJob.started_at).label('month')
            ).filter(
                func.extract('year', RNDJob.started_at) == year
            ).distinct().order_by(func.extract('month', RNDJob.started_at)).all()
        
        month_list = [int(m.month) for m in months if m.month]
        
        # Debug logging
        print(f"DEBUG: Available months for year {year}: {month_list}")
        
        return jsonify({
            'success': True,
            'months': month_list
        })
    except Exception as e:
        print(f"ERROR in get_dashboard_available_months: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

@rnd_cloudsphere_bp.route('/api/dashboard-stats')
@login_required
@require_rnd_access
def get_dashboard_stats_filtered():
    """Get dashboard stats for specific month/year"""
    try:
        year = request.args.get('year', type=int)
        month = request.args.get('month', type=int)
        
        # Debug logging
        print(f"DEBUG: Dashboard stats API called with year={year}, month={month}")
        
        # If no year provided, return all data (like CTP dashboard)
        if not year:
            # Return overall stats without date filtering
            # Base query - no role filtering, all users with RND access can see all data
            jobs_query = RNDJob.query
           
            total_jobs = jobs_query.count()
           
            # Jobs by status
            in_progress = jobs_query.filter_by(status='in_progress').count()
            completed = jobs_query.filter_by(status='completed').count()
            rejected = jobs_query.filter_by(status='rejected').count()
           
            # Jobs by priority
            high_priority = jobs_query.filter_by(priority_level='high').count()
            middle_priority = jobs_query.filter_by(priority_level='middle').count()
            low_priority = jobs_query.filter_by(priority_level='low').count()
           
            # Recent jobs (last 7 days)
            seven_days_ago = datetime.now(jakarta_tz) - timedelta(days=7)
            recent_jobs = jobs_query.filter(RNDJob.created_at >= seven_days_ago).count()
           
            # Jobs by sample type
            blank_jobs = jobs_query.filter_by(sample_type='Blank').count()
            rohs_icb_jobs = jobs_query.filter_by(sample_type='RoHS ICB').count()
            rohs_ribbon_jobs = jobs_query.filter_by(sample_type='RoHS Ribbon').count()
           
            # Overdue jobs: finished_at > deadline_at (completed jobs that missed deadline)
            # FIXED: Add null check for deadline_at to be consistent with SLA calculation
            overdue_jobs = jobs_query.filter(
                RNDJob.status == 'completed',
                RNDJob.deadline_at.isnot(None),  # Only count jobs that have a deadline
                RNDJob.finished_at > RNDJob.deadline_at
            ).count()
           
            result_data = {
                'total_jobs': total_jobs,
                'in_progress': in_progress,
                'completed': completed,
                'completed_jobs': completed,  # Add field name expected by frontend
                'rejected': rejected,
                'blank_jobs': blank_jobs,
                'rohs_icb_jobs': rohs_icb_jobs,  # Fixed field name
                'rohs_ribbon_jobs': rohs_ribbon_jobs,
                'overdue_jobs': overdue_jobs
            }
           
            print(f"DEBUG: Dashboard stats result: {result_data}")
           
            return jsonify({
                'success': True,
                'data': result_data
            })
        
        # Build date range
        start_date = jakarta_tz.localize(datetime(year, month if month else 1, 1))
        
        if month:
            # Specific month
            if month == 12:
                end_date = jakarta_tz.localize(datetime(year + 1, 1, 1))
            else:
                end_date = jakarta_tz.localize(datetime(year, month + 1, 1))
        else:
            # Whole year
            end_date = jakarta_tz.localize(datetime(year + 1, 1, 1))
        
        print(f"DEBUG: Stats filter - year: {year}, month: {month}")
        print(f"DEBUG: Stats date range: {start_date} to {end_date}")
        
        # Base query for period
        jobs_query = RNDJob.query.filter(
            RNDJob.started_at >= start_date,
            RNDJob.started_at < end_date
        )
        
        # Calculate metrics
        total_jobs = jobs_query.count()
        blank_jobs = jobs_query.filter_by(sample_type='Blank').count()
        rohs_icb_jobs = jobs_query.filter_by(sample_type='RoHS ICB').count()
        rohs_ribbon_jobs = jobs_query.filter_by(sample_type='RoHS Ribbon').count()
        completed = jobs_query.filter_by(status='completed').count()
        in_progress = jobs_query.filter_by(status='in_progress').count()
        rejected = jobs_query.filter_by(status='rejected').count()
        
        print(f"DEBUG: Stats calculated - total: {total_jobs}, blank: {blank_jobs}, rohs_icb: {rohs_icb_jobs}, rohs_ribbon: {rohs_ribbon_jobs}, completed: {completed}")
        
        # Overdue jobs: finished_at > deadline_at (completed jobs that missed deadline)
        # FIXED: Add null check for deadline_at to be consistent with SLA calculation
        overdue_jobs = jobs_query.filter(
            RNDJob.status == 'completed',
            RNDJob.deadline_at.isnot(None),  # Only count jobs that have a deadline
            RNDJob.finished_at > RNDJob.deadline_at
        ).count()
        
        return jsonify({
            'success': True,
            'data': {
                'total_jobs': total_jobs,
                'in_progress': in_progress,
                'completed': completed,
                'completed_jobs': completed,  # Add field name expected by frontend
                'rejected': rejected,
                'blank_jobs': blank_jobs,
                'rohs_icb_jobs': rohs_icb_jobs,  # Fixed field name
                'rohs_ribbon_jobs': rohs_ribbon_jobs,
                'overdue_jobs': overdue_jobs
            }
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@rnd_cloudsphere_bp.route('/api/dashboard-trend')
@login_required
@require_rnd_access
def get_dashboard_trend():
    """Get job trend data by month/year for charting"""
    try:
        year = request.args.get('year', type=int)
        month = request.args.get('month', type=int)
        
        # Debug logging
        print(f"DEBUG: Dashboard trend API called with year={year}, month={month}")
        
        # If no year provided, return all data trend (like CTP dashboard)
        if not year:
            # Get all time trend data
            # Get daily data for the last 30 days
            thirty_days_ago = datetime.now(jakarta_tz) - timedelta(days=30)
            
            daily_data = db.session.query(
                func.date(RNDJob.started_at).label('date'),
                func.count(RNDJob.id).label('total'),
                func.sum(func.cast(RNDJob.sample_type == 'Blank', db.Integer)).label('blank'),
                func.sum(func.cast(RNDJob.sample_type == 'RoHS ICB', db.Integer)).label('rohs_icb'),
                func.sum(func.cast(RNDJob.sample_type == 'RoHS Ribbon', db.Integer)).label('rohs_ribbon')
            ).filter(
                RNDJob.started_at >= thirty_days_ago
            ).group_by(func.date(RNDJob.started_at)).order_by(func.date(RNDJob.started_at)).all()
            
            labels = [str(d.date) for d in daily_data]
            total = [d.total or 0 for d in daily_data]
            blank = [d.blank or 0 for d in daily_data]
            rohs_icb = [d.rohs_icb or 0 for d in daily_data]
            rohs_ribbon = [d.rohs_ribbon or 0 for d in daily_data]
            
            print(f"DEBUG: All-time trend data - {len(daily_data)} days")
        else:
            if month:
                # Single month
                start_date = jakarta_tz.localize(datetime(year, month, 1))
                if month == 12:
                    end_date = jakarta_tz.localize(datetime(year + 1, 1, 1))
                else:
                    end_date = jakarta_tz.localize(datetime(year, month + 1, 1))
                
                print(f"DEBUG: Single month filter - year: {year}, month: {month}")
                print(f"DEBUG: Date range: {start_date} to {end_date}")
                
                # Get daily data
                daily_data = db.session.query(
                    func.date(RNDJob.started_at).label('date'),
                    func.count(RNDJob.id).label('total'),
                    func.sum(func.cast(RNDJob.sample_type == 'Blank', db.Integer)).label('blank'),
                    func.sum(func.cast(RNDJob.sample_type == 'RoHS ICB', db.Integer)).label('rohs_icb'),
                    func.sum(func.cast(RNDJob.sample_type == 'RoHS Ribbon', db.Integer)).label('rohs_ribbon')
                ).filter(
                    RNDJob.started_at >= start_date,
                    RNDJob.started_at < end_date
                ).group_by(func.date(RNDJob.started_at)).order_by(func.date(RNDJob.started_at)).all()
                
                print(f"DEBUG: Daily data found - {len(daily_data)} days")
                
                labels = [str(d.date) for d in daily_data]
                total = [d.total or 0 for d in daily_data]
                blank = [d.blank or 0 for d in daily_data]
                rohs_icb = [d.rohs_icb or 0 for d in daily_data]
                rohs_ribbon = [d.rohs_ribbon or 0 for d in daily_data]
            else:
                # Whole year - monthly data
                start_date = jakarta_tz.localize(datetime(year, 1, 1))
                end_date = jakarta_tz.localize(datetime(year + 1, 1, 1))
            
                print(f"DEBUG: Whole year filter - year: {year}")
                print(f"DEBUG: Date range: {start_date} to {end_date}")
            
            monthly_data = db.session.query(
                func.extract('month', RNDJob.started_at).label('month'),
                func.count(RNDJob.id).label('total'),
                func.sum(func.cast(RNDJob.sample_type == 'Blank', db.Integer)).label('blank'),
                func.sum(func.cast(RNDJob.sample_type == 'RoHS ICB', db.Integer)).label('rohs_icb'),
                func.sum(func.cast(RNDJob.sample_type == 'RoHS Ribbon', db.Integer)).label('rohs_ribbon')
            ).filter(
                RNDJob.started_at >= start_date,
                RNDJob.started_at < end_date
            ).group_by(func.extract('month', RNDJob.started_at)).order_by(func.extract('month', RNDJob.started_at)).all()
            
            print(f"DEBUG: Monthly data found - {len(monthly_data)} months")
            
            month_names = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
            labels = [month_names[int(d.month) - 1] for d in monthly_data]
            total = [d.total or 0 for d in monthly_data]
            blank = [d.blank or 0 for d in monthly_data]
            rohs_icb = [d.rohs_icb or 0 for d in monthly_data]
            rohs_ribbon = [d.rohs_ribbon or 0 for d in monthly_data]
        
        return jsonify({
            'success': True,
            'data': {
                'labels': labels,
                'total': total,
                'blank': blank,
                'rohs_icb': rohs_icb,
                'rohs_ribbon': rohs_ribbon
            }
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@rnd_cloudsphere_bp.route('/api/dashboard-stage-distribution')
@login_required
@require_rnd_access
def get_dashboard_stage_distribution():
    """Get job distribution by PIC (stage distribution)"""
    try:
        year = request.args.get('year', type=int)
        month = request.args.get('month', type=int)
        
        # If no year provided, return all data (like CTP dashboard)
        if not year:
            # Get jobs grouped by PIC without date filtering
            pic_data = db.session.query(
                User.name.label('pic_name'),
                func.count(RNDJob.id).label('count')
            ).join(
                RNDJobProgressAssignment, RNDJobProgressAssignment.pic_id == User.id
            ).join(
                RNDJob, RNDJob.id == RNDJobProgressAssignment.job_id
            ).filter(
                User.division_id == 6  # RND division
            ).group_by(User.name).order_by(func.count(RNDJob.id).desc()).all()
            
            data = [
                {'pic_name': pic.pic_name or 'Unknown', 'count': pic.count}
                for pic in pic_data
            ]
            
            return jsonify({
                'success': True,
                'data': data
            })
        
        # Build date range
        start_date = jakarta_tz.localize(datetime(year, month if month else 1, 1))
        
        if month:
            if month == 12:
                end_date = jakarta_tz.localize(datetime(year + 1, 1, 1))
            else:
                end_date = jakarta_tz.localize(datetime(year, month + 1, 1))
        else:
            end_date = jakarta_tz.localize(datetime(year + 1, 1, 1))
        
        print(f"DEBUG: Stage distribution filter - year: {year}, month: {month}")
        print(f"DEBUG: Stage distribution date range: {start_date} to {end_date}")
        
        # Get jobs grouped by PIC (from progress assignments where division_id = 6 / RND)
        pic_data = db.session.query(
            User.name.label('pic_name'),
            func.count(RNDJob.id).label('count')
        ).join(
            RNDJobProgressAssignment, RNDJobProgressAssignment.pic_id == User.id
        ).join(
            RNDJob, RNDJob.id == RNDJobProgressAssignment.job_id
        ).filter(
            User.division_id == 6,  # RND division
            RNDJob.started_at >= start_date,
            RNDJob.started_at < end_date
        ).group_by(User.name).order_by(func.count(RNDJob.id).desc()).all()
        
        print(f"DEBUG: Stage distribution data found - {len(pic_data)} PICs")
        
        data = [
            {'pic_name': pic.pic_name or 'Unknown', 'count': pic.count}
            for pic in pic_data
        ]
        
        return jsonify({
            'success': True,
            'data': data
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@rnd_cloudsphere_bp.route('/api/dashboard-sla')
@login_required
@require_rnd_access
def get_dashboard_sla():
    """Get SLA metrics (on-time ratio)"""
    try:
        year = request.args.get('year', type=int)
        month = request.args.get('month', type=int)
        
        # If no year provided, return all data (like CTP dashboard)
        if not year:
            # Get all completed jobs without date filtering
            # FIXED: Removed is_full_process filter to be consistent with statistics calculation
            completed_jobs = RNDJob.query.filter_by(status='completed').all()
            
            total_count = len(completed_jobs)
            on_time_count = sum(1 for job in completed_jobs if job.finished_at and job.deadline_at and job.finished_at <= job.deadline_at)
            on_time_pct = round((on_time_count / total_count * 100), 2) if total_count > 0 else 0
            
            print(f"DEBUG SLA (no filter): Total={total_count}, OnTime={on_time_count}, Pct={on_time_pct}%")
            
            return jsonify({
                'success': True,
                'data': {
                    'total_count': total_count,
                    'on_time_count': on_time_count,
                    'on_time_pct': on_time_pct
                }
            })
        
        # Build date range
        start_date = jakarta_tz.localize(datetime(year, month if month else 1, 1))
        
        if month:
            if month == 12:
                end_date = jakarta_tz.localize(datetime(year + 1, 1, 1))
            else:
                end_date = jakarta_tz.localize(datetime(year, month + 1, 1))
        else:
            end_date = jakarta_tz.localize(datetime(year + 1, 1, 1))
        
        print(f"DEBUG: SLA filter - year: {year}, month: {month}")
        print(f"DEBUG: SLA date range: {start_date} to {end_date}")
        
        # Get completed jobs only
        # FIXED: Use started_at instead of finished_at to be consistent with statistics
        # This ensures we're measuring the same set of jobs (started in the period)
        completed_jobs = RNDJob.query.filter(
            RNDJob.status == 'completed',
            RNDJob.started_at >= start_date,
            RNDJob.started_at < end_date
        ).all()
        
        print(f"DEBUG: SLA completed jobs found - {len(completed_jobs)} jobs")
        
        total_count = len(completed_jobs)
        on_time_count = sum(1 for job in completed_jobs if job.finished_at and job.deadline_at and job.finished_at <= job.deadline_at)
        on_time_pct = round((on_time_count / total_count * 100), 2) if total_count > 0 else 0
        
        print(f"DEBUG: SLA calculation - total: {total_count}, on_time: {on_time_count}, pct: {on_time_pct}%")
        
        return jsonify({
            'success': True,
            'data': {
                'total_count': total_count,
                'on_time_count': on_time_count,
                'on_time_pct': on_time_pct
            }
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@rnd_cloudsphere_bp.route('/api/dashboard-performance-indicators')
@login_required
@require_rnd_access
def get_dashboard_performance_indicators():
    """Get average completion time for each stage/sample type"""
    try:
        year = request.args.get('year', type=int)
        month = request.args.get('month', type=int)
        
        # If no year provided, return all data
        if not year:
            # Get all completed jobs without date filtering, but only full process jobs
            completed_jobs = RNDJob.query.filter_by(status='completed', is_full_process=True).all()
        else:
            # Build date range
            start_date = jakarta_tz.localize(datetime(year, month if month else 1, 1))
            
            if month:
                # Specific month
                if month == 12:
                    end_date = jakarta_tz.localize(datetime(year + 1, 1, 1))
                else:
                    end_date = jakarta_tz.localize(datetime(year, month + 1, 1))
            else:
                # Whole year
                end_date = jakarta_tz.localize(datetime(year + 1, 1, 1))
            
            # Get completed jobs for period (only full process jobs)
            completed_jobs = RNDJob.query.filter(
                RNDJob.status == 'completed',
                RNDJob.is_full_process == True,  # Filter only full process jobs
                RNDJob.started_at >= start_date,
                RNDJob.started_at < end_date
            ).all()
        
        # Calculate average completion times for the three required sample types only
        performance_data = {}
        
        # Initialize only the three required sample types
        required_sample_types = ['Blank', 'RoHS ICB', 'RoHS Ribbon']
        for sample_type in required_sample_types:
            performance_data[sample_type] = {
                'total_jobs': 0,
                'total_days': 0,
                'average_days': 0
            }
        
        # Process completed jobs
        for job in completed_jobs:
            if job.started_at and job.finished_at:
                # Calculate completion time in days
                completion_time = (job.finished_at - job.started_at).total_seconds() / (24 * 3600)
                
                # Only process the three required sample types
                if job.sample_type in required_sample_types:
                    category = job.sample_type
                    
                    # Update totals
                    if category in performance_data:
                        performance_data[category]['total_jobs'] += 1
                        performance_data[category]['total_days'] += completion_time
        
        # Calculate averages for the three required sample types
        for category in performance_data:
            if performance_data[category]['total_jobs'] > 0:
                performance_data[category]['average_days'] = round(
                    performance_data[category]['total_days'] / performance_data[category]['total_jobs'], 2
                )
        
        # Format data for frontend - only return the three required indicators
        result_data = {
            'avg_blank_time': performance_data.get('Blank', {}).get('average_days', 0),
            'avg_rohs_icb_time': performance_data.get('RoHS ICB', {}).get('average_days', 0),
            'avg_rohs_ribbon_time': performance_data.get('RoHS Ribbon', {}).get('average_days', 0)
        }
        
        return jsonify({
            'success': True,
            'data': result_data
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@rnd_cloudsphere_bp.route('/api/dashboard-job-distribution')
@login_required
@require_rnd_access
def get_dashboard_job_distribution():
    """Get job distribution by sample type for stacked bar chart"""
    try:
        year = request.args.get('year', type=int)
        month = request.args.get('month', type=int)
        
        # If no year provided, return all data
        if not year:
            # Get all jobs without date filtering
            jobs_query = RNDJob.query
        else:
            # Build date range
            start_date = jakarta_tz.localize(datetime(year, month if month else 1, 1))
            
            if month:
                # Specific month
                if month == 12:
                    end_date = jakarta_tz.localize(datetime(year + 1, 1, 1))
                else:
                    end_date = jakarta_tz.localize(datetime(year, month + 1, 1))
            else:
                # Whole year
                end_date = jakarta_tz.localize(datetime(year + 1, 1, 1))
            
            # Get jobs for period
            jobs_query = RNDJob.query.filter(
                RNDJob.started_at >= start_date,
                RNDJob.started_at < end_date
            )
        
        # Get distribution by sample type
        distribution_data = db.session.query(
            RNDJob.sample_type,
            func.count(RNDJob.id).label('count')
        ).group_by(RNDJob.sample_type).all()
        
        # Format data for stacked bar chart
        labels = []
        blank_data = []
        rohs_icb_data = []
        rohs_ribbon_data = []
        
        # If we have date filters, use time-based labels
        if year:
            if month:
                # Daily data for specific month
                daily_data = db.session.query(
                    func.date(RNDJob.started_at).label('date'),
                    func.sum(func.cast(RNDJob.sample_type == 'Blank', db.Integer)).label('blank'),
                    func.sum(func.cast(RNDJob.sample_type == 'RoHS ICB', db.Integer)).label('rohs_icb'),
                    func.sum(func.cast(RNDJob.sample_type == 'RoHS Ribbon', db.Integer)).label('rohs_ribbon')
                ).filter(
                    RNDJob.started_at >= start_date,
                    RNDJob.started_at < end_date
                ).group_by(func.date(RNDJob.started_at)).order_by(func.date(RNDJob.started_at)).all()
                
                labels = [str(d.date) for d in daily_data]
                blank_data = [d.blank or 0 for d in daily_data]
                rohs_icb_data = [d.rohs_icb or 0 for d in daily_data]
                rohs_ribbon_data = [d.rohs_ribbon or 0 for d in daily_data]
            else:
                # Monthly data for specific year
                monthly_data = db.session.query(
                    func.extract('month', RNDJob.started_at).label('month'),
                    func.sum(func.cast(RNDJob.sample_type == 'Blank', db.Integer)).label('blank'),
                    func.sum(func.cast(RNDJob.sample_type == 'RoHS ICB', db.Integer)).label('rohs_icb'),
                    func.sum(func.cast(RNDJob.sample_type == 'RoHS Ribbon', db.Integer)).label('rohs_ribbon')
                ).filter(
                    RNDJob.started_at >= start_date,
                    RNDJob.started_at < end_date
                ).group_by(func.extract('month', RNDJob.started_at)).order_by(func.extract('month', RNDJob.started_at)).all()
                
                month_names = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
                labels = [month_names[int(d.month) - 1] for d in monthly_data]
                blank_data = [d.blank or 0 for d in monthly_data]
                rohs_icb_data = [d.rohs_icb or 0 for d in monthly_data]
                rohs_ribbon_data = [d.rohs_ribbon or 0 for d in monthly_data]
        else:
            # Overall distribution (no time series)
            labels = ['Total Jobs']
            total_blank = jobs_query.filter_by(sample_type='Blank').count()
            total_rohs_icb = jobs_query.filter_by(sample_type='RoHS ICB').count()
            total_rohs_ribbon = jobs_query.filter_by(sample_type='RoHS Ribbon').count()
            
            blank_data = [total_blank]
            rohs_icb_data = [total_rohs_icb]
            rohs_ribbon_data = [total_rohs_ribbon]
        
        return jsonify({
            'success': True,
            'data': {
                'labels': labels,
                'blank': blank_data,
                'rohs_icb': rohs_icb_data,
                'rohs_ribbon': rohs_ribbon_data
            }
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@rnd_cloudsphere_bp.route('/api/dashboard-individual-scores')
@login_required
@require_rnd_access
def get_dashboard_individual_scores():
    """Get individual productivity scores for RND users (total days per stage)"""
    try:
        year = request.args.get('year', type=int)
        month = request.args.get('month', type=int)
        
        # DEBUG: Log request parameters
        print(f"\n{'#'*80}")
        print(f"# SCORES KPI CALCULATION DEBUG")
        print(f"{'#'*80}")
        print(f"Request Parameters: year={year}, month={month}")
        
        # Get all RND users (division_id = 6)
        rnd_users = User.query.filter_by(division_id=6, is_active=True).order_by(User.name).all()
        print(f"Total RND Users: {len(rnd_users)}")
        
        # Define stage mapping: stage_name -> sample_type to find
        # CHANGED: Map to sample_type instead of step_name
        # This will calculate ALL steps within that sample_type
        stage_mapping = {
            'Design': 'Design',
            'Mastercard': 'Mastercard',
            'Blank': 'Blank',
            'RoHS ICB': 'RoHS ICB',  # Will calculate all 3 steps (Proof, Sample, Quality)
            'RoHS Ribbon': 'RoHS Ribbon',  # Will calculate all 3 steps (Proof, Sample, Quality)
            'Polymer Ribbon': 'Polymer Ribbon',
            'Light-Standard-Dark': 'Light-Standard-Dark Reference'
        }
        print(f"Stage Mapping (by sample_type): {len(stage_mapping)} stages")
        print(f"{'#'*80}\n")
        
        users_scores = []
        
        for user in rnd_users:
            user_scores = {
                'user_id': user.id,
                'user_name': user.name,
                'username': user.username,
                'scores': {
                    'Design': 0.0,
                    'Mastercard': 0.0,
                    'Blank': 0.0,
                    'RoHS ICB': 0.0,
                    'RoHS Ribbon': 0.0,
                    'Polymer Ribbon': 0.0,
                    'Light-Standard-Dark': 0.0
                }
            }
            
            # For each stage, calculate total days for ALL steps within that sample_type
            for stage_name, sample_type in stage_mapping.items():
                try:
                    # Get all progress assignments for this user (PIC) for steps in this sample_type
                    # Filter ONLY by RNDProgressStep.sample_type (not RNDJob.sample_type)
                    # because a job can work on steps from different sample_types
                    assignments_query = db.session.query(RNDJobProgressAssignment).filter(
                        RNDJobProgressAssignment.pic_id == user.id,
                        RNDProgressStep.sample_type == sample_type
                    ).join(RNDProgressStep).join(RNDJob)
                    
                    # Apply year/month filter if provided
                    if year:
                        start_date = jakarta_tz.localize(datetime(year, month if month else 1, 1))
                        
                        if month:
                            if month == 12:
                                end_date = jakarta_tz.localize(datetime(year + 1, 1, 1))
                            else:
                                end_date = jakarta_tz.localize(datetime(year, month + 1, 1))
                        else:
                            end_date = jakarta_tz.localize(datetime(year + 1, 1, 1))
                        
                        # FIXED: Filter by assignment's finished_at to attribute score to completion month
                        assignments_query = assignments_query.filter(
                            RNDJobProgressAssignment.finished_at >= start_date,
                            RNDJobProgressAssignment.finished_at < end_date
                        )
                    
                    assignments = assignments_query.all()
                    
                    # DEBUG: Log assignments found
                    print(f"\n{'='*80}")
                    print(f"DEBUG Scores KPI: Stage '{stage_name}' for user '{user.name}' (ID: {user.id})")
                    print(f"{'='*80}")
                    print(f"  Filter: Year={year}, Month={month}")
                    if year:
                        print(f"  Date Range: {start_date} to {end_date}")
                    print(f"  Total assignments found: {len(assignments)}")
                    print(f"  Stage Name (display): {stage_name}")
                    print(f"  Sample Type (filter): {sample_type}")
                    
                    # List all steps that will be included
                    steps_included = db.session.query(RNDProgressStep.name, RNDProgressStep.step_order).filter(
                        RNDProgressStep.sample_type == sample_type
                    ).order_by(RNDProgressStep.step_order).all()
                    print(f"  Steps included in '{sample_type}':")
                    for step_name, step_order in steps_included:
                        print(f"    - #{step_order}: {step_name}")
                    print(f"{'='*80}")
                    
                    # Calculate average duration for this stage (direct duration from started_at to finished_at)
                    total_days = 0.0
                    completed_count = 0
                    
                    for idx, assignment in enumerate(assignments):
                        # Only count completed assignments with both start and end times
                        if assignment.status == 'completed' and assignment.started_at and assignment.finished_at:
                            job = assignment.job
                            
                            # CORRECTED: Calculate duration directly from assignment's started_at to finished_at
                            # This measures the actual time PIC spent on THIS step
                            start_time = assignment.started_at
                            end_time = assignment.finished_at
                            
                            # Calculate duration
                            time_diff = end_time - start_time
                            days = time_diff.total_seconds() / (24 * 3600)  # Convert to days
                            hours = time_diff.total_seconds() / 3600  # For reference
                            minutes = (time_diff.total_seconds() % 3600) / 60  # Minutes part
                            
                            # DEBUG: Log this assignment's calculation
                            completed_count += 1
                            print(f"  [Job {completed_count}]:")
                            print(f"    Job ID: {job.job_id}")
                            print(f"    Assignment ID: {assignment.id}")
                            print(f"    Started: {start_time.strftime('%Y-%m-%d %H:%M:%S')}")
                            print(f"    Finished: {end_time.strftime('%Y-%m-%d %H:%M:%S')}")
                            print(f"    Duration: {days:.4f} days ({int(hours)}h {int(minutes)}m)")
                            print(f"    Status: {assignment.status}")
                            
                            total_days += days
                        else:
                            # Log skipped assignments
                            if assignment.status != 'completed':
                                print(f"  [SKIPPED] Assignment {assignment.id}: status={assignment.status} (not completed)")
                            elif not assignment.started_at:
                                print(f"  [SKIPPED] Assignment {assignment.id}: no started_at")
                            elif not assignment.finished_at:
                                print(f"  [SKIPPED] Assignment {assignment.id}: no finished_at")
                    
                    # Calculate AVERAGE duration (in days)
                    print(f"{'-'*80}")
                    print(f"  SUMMARY:")
                    print(f"  Total completed with duration: {completed_count}")
                    print(f"  Total days: {total_days:.4f} days")
                    if completed_count > 0:
                        average_days = total_days / completed_count
                        print(f"  Average: {total_days:.4f} ÷ {completed_count} = {average_days:.4f} days/job")
                        print(f"  Final Score: {round(average_days, 2)} days/job")
                        user_scores['scores'][stage_name] = round(average_days, 2)
                    else:
                        print(f"  No completed assignments found!")
                        print(f"  Final Score: 0.00 days/job")
                        user_scores['scores'][stage_name] = 0.0
                    print(f"{'='*80}\n")
                    
                except Exception as e:
                    print(f"Error calculating score for {user.name} in stage {stage_name}: {e}")
                    user_scores['scores'][stage_name] = 0.0
            
            users_scores.append(user_scores)
        
        # DEBUG: Print final results summary
        print(f"\n{'#'*80}")
        print(f"# FINAL RESULTS SUMMARY")
        print(f"{'#'*80}")
        for user_data in users_scores:
            print(f"\nUser: {user_data['user_name']} (@{user_data['username']})")
            print(f"  Scores:")
            for stage, score in user_data['scores'].items():
                if score > 0:
                    print(f"    - {stage}: {score} days/job")
        print(f"\n{'#'*80}\n")
        
        return jsonify({
            'success': True,
            'data': users_scores
        })
    except Exception as e:
        print(f"Error in get_dashboard_individual_scores: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

@rnd_cloudsphere_bp.route('/api/jobs')
@login_required
@require_rnd_access
def get_rnd_jobs():
    """Get R&D jobs with filtering and optional pagination"""
    try:
        user = current_user
        page = request.args.get('page', type=int)
        per_page = request.args.get('per_page', type=int)
        search = request.args.get('search', '').strip()
        status_filter = request.args.get('status', '').strip()
        priority_filter = request.args.get('priority', '').strip()
        sample_type_filter = request.args.get('sample_type', '').strip()
        user_id_filter = request.args.get('user_id', type=int)
        
        # Base query with role-based filtering
        # Admin users can see all jobs, PIC users can only see jobs assigned to them
        if user.is_admin():
            # Admin can see all jobs
            query = RNDJob.query
        else:
            # PIC users can only see jobs where they are assigned as PIC
            query = RNDJob.query.join(RNDJobProgressAssignment).filter(
                RNDJobProgressAssignment.pic_id == user.id
            ).distinct()
        
        # Additional user_id_filter for admin to filter by specific user
        if user_id_filter and user.is_admin():
            query = query.join(RNDJobProgressAssignment).filter(
                RNDJobProgressAssignment.pic_id == user_id_filter
            ).distinct()
        
        # Apply search filter
        if search:
            search_term = f"%{search}%"
            query = query.filter(
                or_(
                    RNDJob.job_id.ilike(search_term),
                    RNDJob.item_name.ilike(search_term),
                    RNDJob.notes.ilike(search_term)
                )
            )
        
        # Apply filters directly on RNDJob table (not on RNDJobProgressAssignment)
        # This ensures filters work for all users including operators
        if status_filter:
            query = query.filter(RNDJob.status == status_filter)
        
        if priority_filter:
            query = query.filter(RNDJob.priority_level == priority_filter)
        
        if sample_type_filter:
            query = query.filter(RNDJob.sample_type == sample_type_filter)
        
        # Order by created date descending
        query = query.order_by(RNDJob.created_at.desc())
        
        # Check if pagination is requested
        if page is not None and per_page is not None:
            # Use pagination
            pagination = query.paginate(page=page, per_page=per_page, error_out=False)
            jobs = pagination.items
            has_pagination = True
        else:
            # Return all jobs without pagination
            jobs = query.all()
            has_pagination = False
        
        jobs_data = []
        for job in jobs:
            # Get current progress step info
            current_progress = job.current_progress_step
           
            # Get all PIC assignments for this job
            pic_assignments = []
            try:
                for assignment in job.progress_assignments:
                    if assignment.pic:
                        pic_assignments.append({
                            'step_name': assignment.progress_step.name if assignment.progress_step else 'Unknown',
                            'pic_name': assignment.pic.name,
                            'status': assignment.status
                        })
            except Exception as e:
                print(f"Error processing PIC assignments for job {job.id}: {e}")
                # Ensure we always have pic_assignments even if there's an error
                pic_assignments = []
           
            # Get current PIC name
            current_pic_name = None
            if current_progress:
                try:
                    current_assignment = RNDJobProgressAssignment.query.filter_by(
                        job_id=job.id,
                        progress_step_id=current_progress.get('id')
                    ).first()
                    if current_assignment and current_assignment.pic:
                        current_pic_name = current_assignment.pic.name
                except Exception as e:
                    print(f"Error getting current PIC for job {job.id}: {e}")
           
            # Check if job is overdue
            is_overdue = False
            if job.deadline_at:
                # Ensure both datetimes are timezone-aware for proper comparison
                now = datetime.now(jakarta_tz)
                if job.deadline_at.tzinfo is None:
                    # If deadline is naive, assume it's in Jakarta timezone
                    deadline = jakarta_tz.localize(job.deadline_at)
                else:
                    deadline = job.deadline_at
                 
                is_overdue = now > deadline and job.status != 'completed'
           
            # IMPORTANT: Sync job status before adding to response
            # This triggers the auto-sync property and commits changes if needed
            sync_job_status(job)
            
            jobs_data.append({
                'id': job.id,
                'job_id': job.job_id,
                'item_name': job.item_name,
                'sample_type': job.sample_type,
                'priority_level': job.priority_level,
                'deadline_at': job.deadline_at.strftime('%Y-%m-%d %H:%M') if job.deadline_at else None,
                'status': job.status,
                'completion_percentage': job.completion_percentage or 0,
                'current_progress_step': current_progress,
                'current_pic_name': current_pic_name,
                'pic_assignments': pic_assignments,  # All PIC assignments
                'is_overdue': is_overdue,
                'is_full_process': job.is_full_process,
                'started_at': job.started_at.strftime('%Y-%m-%d %H:%M') if job.started_at else None,
                'finished_at': job.finished_at.strftime('%Y-%m-%d %H:%M') if job.finished_at else None,
                'created_at': job.created_at.strftime('%Y-%m-%d %H:%M') if job.created_at else None
            })
        
        response_data = {
            'success': True,
            'data': jobs_data
        }
        
        # Add pagination data only if pagination is used
        if has_pagination:
            response_data['pagination'] = {
                'page': page,
                'per_page': per_page,
                'total': pagination.total,
                'pages': pagination.pages,
                'has_prev': pagination.has_prev,
                'has_next': pagination.has_next,
                'prev_num': pagination.prev_num,
                'next_num': pagination.next_num
            }
        
        return jsonify(response_data)
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@rnd_cloudsphere_bp.route('/api/job', methods=['POST'])
@login_required
@require_rnd_access
def create_rnd_job():
    """Create new R&D job with multiple progress steps and PIC assignments"""
    try:
        data = request.get_json()
        
        # Validate required fields
        required_fields = ['item_name', 'sample_type', 'priority_level', 'deadline_at', 'progress_assignments']
        for field in required_fields:
            if not data.get(field):
                return jsonify({'success': False, 'error': f'{field} is required'}), 400
        
        # Get is_full_process field (optional, defaults to False)
        is_full_process = data.get('is_full_process', False)
        
        # Parse dates
        started_at = datetime.now(jakarta_tz)
        if data.get('started_at'):
            # Parse the datetime from frontend (datetime-local sends in local browser time)
            # Convert from local time to Jakarta timezone
            local_dt = datetime.strptime(data['started_at'], '%Y-%m-%dT%H:%M')
            # The datetime-local input returns local time, so we need to treat it as Jakarta time
            started_at = jakarta_tz.localize(local_dt)
        
        # Parse deadline similar to started_at
        local_deadline = datetime.strptime(data['deadline_at'], '%Y-%m-%dT%H:%M')
        deadline_at = jakarta_tz.localize(local_deadline)
        
        # Create job
        job = RNDJob(
            job_id=generate_rnd_job_id(),
            item_name=data['item_name'],
            sample_type=data['sample_type'],
            priority_level=data['priority_level'],
            started_at=started_at,
            deadline_at=deadline_at,
            notes=data.get('notes', ''),
            is_full_process=is_full_process,  # Add is_full_process field
            flow_configuration_id=data.get('flow_configuration_id'),  # Add flow configuration
            status='in_progress'
        )
        
        db.session.add(job)
        db.session.flush()  # Get job ID
        
        # Create progress assignments
        progress_assignments = data['progress_assignments']
        
        for i, assignment in enumerate(progress_assignments):
            progress_step_id = assignment.get('progress_step_id')
            pic_id = assignment.get('pic_id')
            
            if not progress_step_id or not pic_id:
                continue
            
            # Create progress assignment
            progress_assignment = RNDJobProgressAssignment(
                job_id=job.id,
                progress_step_id=progress_step_id,
                pic_id=pic_id,
                started_at=started_at if i == 0 else None,  # First step starts immediately
                status='pending' if i > 0 else 'in_progress'  # First step is in progress
            )
            
            db.session.add(progress_assignment)
            db.session.flush()  # Get assignment ID
            
            # Create task assignments for this progress step
            task_ids = assignment.get('task_ids', [])
            
            for task_id in task_ids:
                task_assignment = RNDJobTaskAssignment(
                    job_progress_assignment_id=progress_assignment.id,
                    progress_task_id=task_id,
                    status='pending'
                )
                db.session.add(task_assignment)
        
        db.session.commit()
        
        # Send notification for new job
        try:
            NotificationDispatcher.dispatch_rnd_job_created(
                job_db_id=job.id,
                job_id=job.job_id,
                item_name=job.item_name,
                sample_type=job.sample_type,
                priority_level=job.priority_level,
                triggered_by_user_id=current_user.id
            )
        except Exception as e:
            logger.error(f"Failed to send RND job created notification: {str(e)}", exc_info=True)
        
        return jsonify({
            'success': True,
            'message': 'R&D Job created successfully',
            'data': {
                'id': job.id,
                'job_id': job.job_id,
                'flow_configuration_id': job.flow_configuration_id
            }
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500

@rnd_cloudsphere_bp.route('/api/jobs/<int:job_id>')
@login_required
@require_rnd_access
def get_rnd_job(job_id):
    """Get R&D job details"""
    try:
        job = RNDJob.query.get_or_404(job_id)
        
        # Get progress assignments with PIC and task details
        progress_assignments = []
        try:
            for assignment in job.progress_assignments:
                # Get tasks for this progress step - Only get tasks that belong to this specific assignment
                tasks = []
                try:
                    # Filter tasks to only include those that belong to the current progress assignment
                    for task_assignment in assignment.task_assignments:
                        # Double-check that this task assignment belongs to the current progress assignment
                        if task_assignment.job_progress_assignment_id == assignment.id:
                            task_data = {
                                'id': task_assignment.id,
                                'task_id': task_assignment.progress_task_id,
                                'task_name': task_assignment.progress_task.name if task_assignment.progress_task else None,
                                'status': task_assignment.status,
                                'completed_at': task_assignment.completed_at.strftime('%Y-%m-%d %H:%M') if task_assignment.completed_at else None,
                                'notes': task_assignment.notes,
                                'updated_at': task_assignment.updated_at.strftime('%Y-%m-%d %H:%M') if task_assignment.updated_at else None
                            }
                            tasks.append(task_data)
                except Exception as e:
                    print(f"Error processing tasks for assignment {assignment.id}: {e}")
                   
                assignment_data = {
                    'id': assignment.id,
                    'progress_step_id': assignment.progress_step_id,
                    'progress_step_name': assignment.progress_step.name if assignment.progress_step else None,
                    'progress_step_order': assignment.progress_step.step_order if assignment.progress_step else None,
                    'pic_id': assignment.pic_id,
                    'pic_name': assignment.pic.name if assignment.pic else None,
                    'started_at': assignment.started_at.strftime('%Y-%m-%d %H:%M') if assignment.started_at else None,
                    'finished_at': assignment.finished_at.strftime('%Y-%m-%d %H:%M') if assignment.finished_at else None,
                    'status': assignment.status,
                    'notes': assignment.notes,
                    'completion_percentage': assignment.completion_percentage,
                    'tasks': tasks,  # Tasks are now correctly filtered to only include tasks for this specific step
                    # Add visibility flag for frontend filtering
                    'is_visible': current_user.is_admin() or assignment.pic_id == current_user.id
                }
                progress_assignments.append(assignment_data)
        except Exception as e:
            print(f"Error processing progress assignments for job {job.id}: {e}")
            # Ensure we always have progress_assignments even if there's an error
            progress_assignments = []
        
        # Get evidence files
        evidence_files = []
        for file in job.evidence_files:
            evidence_files.append({
                'id': file.id,
                'filename': file.filename,
                'original_filename': file.original_filename,
                'file_type': file.file_type,
                'file_size': file.file_size,
                'evidence_type': file.evidence_type,
                'uploaded_by': file.uploaded_by,
                'uploaded_at': file.uploaded_at.strftime('%Y-%m-%d %H:%M') if file.uploaded_at else None,
                'uploader_name': file.uploader.name if file.uploader else None,
                'is_verified': file.is_verified,
                'verified_by': file.verifier.name if file.verifier else None,
                'verified_at': file.verified_at.strftime('%Y-%m-%d %H:%M') if file.verified_at else None,
                'job_progress_assignment_id': file.job_progress_assignment_id,
                'job_task_assignment_id': file.job_task_assignment_id
            })
        
        job_data = {
            'id': job.id,
            'job_id': job.job_id,
            'item_name': job.item_name,
            'sample_type': job.sample_type,
            'priority_level': job.priority_level,
            'started_at': job.started_at.strftime('%Y-%m-%d %H:%M') if job.started_at else None,
            'deadline_at': job.deadline_at.strftime('%Y-%m-%d %H:%M') if job.deadline_at else None,
            'finished_at': job.finished_at.strftime('%Y-%m-%d %H:%M') if job.finished_at else None,
            'status': job.status,
            'notes': job.notes,
            'is_full_process': job.is_full_process,
            'completion_percentage': job.completion_percentage,
            'current_progress_step': job.current_progress_step,
            'progress_assignments': progress_assignments,
            'evidence_files': evidence_files,
            'flow_configuration_id': job.flow_configuration_id  # Add flow configuration ID
        }
        
        # IMPORTANT: Sync job status before sending to frontend
        # This ensures completion_percentage always matches status
        sync_job_status(job)
        
        # DEBUG: Log job data before sending to frontend
        print(f"DEBUG: Job data for job {job_id}:")
        print(f"  - Job status: {job.status}")
        print(f"  - Flow configuration ID: {job.flow_configuration_id}")
        print(f"  - Progress assignments count: {len(progress_assignments)}")
        for assignment in progress_assignments:
            print(f"    - {assignment['progress_step_name']}: {assignment['status']}")
        
        return jsonify({
            'success': True,
            'data': job_data
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@rnd_cloudsphere_bp.route('/api/jobs/<int:job_id>', methods=['PUT'])
@login_required
@require_rnd_access
def update_rnd_job(job_id):
    """Update R&D job"""
    try:
        job = RNDJob.query.get_or_404(job_id)
        data = request.get_json()
        
        # Update job fields
        if data.get('item_name'):
            job.item_name = data['item_name']
        if data.get('sample_type'):
            job.sample_type = data['sample_type']
        if data.get('priority_level'):
            job.priority_level = data['priority_level']
        if data.get('deadline_at'):
            # Parse the datetime from frontend (datetime-local sends in local browser time)
            # Convert from local time to Jakarta timezone
            local_deadline = datetime.strptime(data['deadline_at'], '%Y-%m-%dT%H:%M')
            # The datetime-local input returns local time, so we need to treat it as Jakarta time
            job.deadline_at = jakarta_tz.localize(local_deadline)
        if data.get('status'):
            job.status = data['status']
        if data.get('notes'):
            job.notes = data['notes']
        if 'is_full_process' in data:
            job.is_full_process = data['is_full_process']
        
        # Update progress assignments if provided
        # IMPORTANT: Only update assignments that are in 'pending' status
        # Preserve in_progress and completed assignments to maintain progress history
        if 'progress_assignments' in data:
            progress_assignments = data['progress_assignments']
            
            # Preserve existing assignments that are in_progress or completed
            # Only delete/recreate pending assignments
            existing_assignments = {
                (a.progress_step_id, a.status): a 
                for a in job.progress_assignments
            }
            
            # Collect IDs of assignments to keep
            assignments_to_preserve = set()
            
            # Process new assignments from frontend
            for i, assignment in enumerate(progress_assignments):
                progress_step_id = assignment.get('progress_step_id')
                pic_id = assignment.get('pic_id')
                task_ids = assignment.get('task_ids', [])
                
                if not progress_step_id or not pic_id:
                    continue
                
                # Check if this step already has an in_progress or completed assignment
                existing_assignment = None
                for existing in job.progress_assignments:
                    if existing.progress_step_id == progress_step_id and existing.status in ['in_progress', 'completed']:
                        existing_assignment = existing
                        assignments_to_preserve.add(existing.id)
                        break
                
                if existing_assignment:
                    # Preserve the assignment, only update PIC if changed
                    if existing_assignment.pic_id != pic_id:
                        existing_assignment.pic_id = pic_id
                    # Don't touch task assignments or status - they're maintained
                else:
                    # This is a new assignment, check if we're updating pending ones
                    pending_assignment = None
                    for existing in job.progress_assignments:
                        if existing.progress_step_id == progress_step_id and existing.status == 'pending':
                            pending_assignment = existing
                            break
                    
                    if pending_assignment:
                        # Update pending assignment
                        pending_assignment.pic_id = pic_id
                        assignments_to_preserve.add(pending_assignment.id)
                        
                        # Update task assignments for pending assignment
                        # Delete old task assignments
                        for task_assignment in pending_assignment.task_assignments:
                            db.session.delete(task_assignment)
                        
                        # Add new task assignments
                        for task_id in task_ids:
                            task_assignment = RNDJobTaskAssignment(
                                job_progress_assignment_id=pending_assignment.id,
                                progress_task_id=task_id,
                                status='pending'
                            )
                            db.session.add(task_assignment)
                    else:
                        # Create new assignment
                        progress_assignment = RNDJobProgressAssignment(
                            job_id=job.id,
                            progress_step_id=progress_step_id,
                            pic_id=pic_id,
                            started_at=job.started_at if i == 0 else None,
                            status='pending' if i > 0 else 'in_progress'
                        )
                        db.session.add(progress_assignment)
                        db.session.flush()  # Get assignment ID
                        assignments_to_preserve.add(progress_assignment.id)
                        
                        # Create task assignments
                        for task_id in task_ids:
                            task_assignment = RNDJobTaskAssignment(
                                job_progress_assignment_id=progress_assignment.id,
                                progress_task_id=task_id,
                                status='pending'
                            )
                            db.session.add(task_assignment)
            
            # Delete only assignments that are not being preserved
            for assignment in job.progress_assignments:
                if assignment.id not in assignments_to_preserve:
                    # Only delete if they're pending (safe to remove)
                    if assignment.status == 'pending':
                        for task_assignment in assignment.task_assignments:
                            db.session.delete(task_assignment)
                        db.session.delete(assignment)
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'R&D Job updated successfully'
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500

@rnd_cloudsphere_bp.route('/api/jobs/<int:job_id>', methods=['DELETE'])
@login_required
@require_rnd_access
def delete_rnd_job(job_id):
    """Delete R&D job"""
    try:
        job = RNDJob.query.get_or_404(job_id)
        
        # Delete related records in proper order to avoid foreign key constraints
        
        # 1. Delete external delays first (they reference job_id)
        RNDExternalTime.query.filter_by(job_id=job_id).delete()
        
        # 2. Delete job notes (they reference the job directly)
        from models_rnd import RNDJobNote
        RNDJobNote.query.filter_by(job_id=job_id).delete()
        
        # 3. Delete evidence files
        for evidence in job.evidence_files:
            db.session.delete(evidence)
        
        # 4. Delete task assignments and task completions
        for assignment in job.progress_assignments:
            for task_assignment in assignment.task_assignments:
                db.session.delete(task_assignment)
            db.session.delete(assignment)
        
        # 5. Delete the job itself
        db.session.delete(job)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'R&D Job deleted successfully'
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500

@rnd_cloudsphere_bp.route('/api/progress-steps/all')
@login_required
@require_rnd_access
def get_all_progress_steps():
    """Get progress steps relevant to sample type with proper mappings"""
    try:
        sample_type = request.args.get('sample_type', '')
        
        # Define the step sample types for each flow configuration
        flow_mapping = {
            'Blank': ['Design', 'Mastercard', 'Blank'],
            'RoHS ICB': ['Design', 'Mastercard', 'RoHS ICB', 'Light-Standard-Dark Reference'],
            'RoHS Ribbon': ['Design', 'Mastercard', 'Polymer Ribbon', 'RoHS Ribbon', 'Light-Standard-Dark Reference'],
            'Light-Standard-Dark Reference': ['Light-Standard-Dark Reference']
        }
        
        # Get the step types to include based on the selected sample type
        step_types_to_include = flow_mapping.get(sample_type, [sample_type] if sample_type else [])
        
        if not step_types_to_include:
            return jsonify({'success': True, 'data': []})
        
        # Get progress steps that match the criteria
        all_steps = RNDProgressStep.query.filter(
            RNDProgressStep.sample_type.in_(step_types_to_include)
        ).order_by(
            RNDProgressStep.sample_type,
            RNDProgressStep.step_order
        ).all()
        
        if not all_steps:
            return jsonify({'success': True, 'data': []})
        
        # Get tasks for each step and build response
        steps_data = []
        for step in all_steps:
            tasks = RNDProgressTask.query.filter_by(progress_step_id=step.id)\
                .order_by(RNDProgressTask.task_order).all()
            
            steps_data.append({
                'id': step.id,
                'name': step.name,
                'sample_type': step.sample_type,
                'step_order': step.step_order,
                'description': step.description,
                'is_required': True,
                'tasks': [
                    {
                        'id': task.id,
                        'name': task.name,
                        'task_order': task.task_order,
                        'description': task.description
                    } for task in tasks
                ]
            })
        
        return jsonify({
            'success': True,
            'data': steps_data
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@rnd_cloudsphere_bp.route('/api/progress-steps')
@login_required
@require_rnd_access
def get_progress_steps():
    """Get progress steps based on sample type with dynamic flow configuration"""
    try:
        sample_type = request.args.get('sample_type', '')
        flow_configuration_id = request.args.get('flow_configuration_id', type=int)
        
        # sample_type is now optional - if not provided, return all steps
        if not sample_type and not flow_configuration_id:
            # Return all steps if no filters provided
            all_steps = RNDProgressStep.query.order_by(
                RNDProgressStep.sample_type,
                RNDProgressStep.step_order
            ).all()
            
            steps_data = []
            for step in all_steps:
                tasks = RNDProgressTask.query.filter_by(progress_step_id=step.id)\
                    .order_by(RNDProgressTask.task_order).all()
                
                steps_data.append({
                    'id': step.id,
                    'name': step.name,
                    'sample_type': step.sample_type,
                    'step_order': step.step_order,
                    'description': step.description,
                    'is_required': True,
                    'tasks': [
                        {
                            'id': task.id,
                            'name': task.name,
                            'task_order': task.task_order,
                            'description': task.description
                        } for task in tasks
                    ]
                })
            
            return jsonify({
                'success': True,
                'data': steps_data,
                'flow_configuration': None
            })
        
        # If flow_configuration_id is provided, use that specific configuration
        if flow_configuration_id:
            flow_config = RNDFlowConfiguration.query.get(flow_configuration_id)
            if not flow_config or flow_config.sample_type != sample_type:
                return jsonify({'success': False, 'error': 'Invalid flow configuration'}), 400
            
            # Get flow steps from the configuration
            flow_steps_query = RNDFlowStep.query.filter_by(flow_configuration_id=flow_configuration_id)\
                .join(RNDProgressStep)\
                .order_by(RNDFlowStep.step_order)\
                .all()
            
            # Build the steps data from the configuration
            steps_data = []
            for flow_step in flow_steps_query:
                progress_step = flow_step.progress_step
                tasks = RNDProgressTask.query.filter_by(progress_step_id=progress_step.id)\
                    .order_by(RNDProgressTask.task_order).all()
                
                steps_data.append({
                    'id': progress_step.id,
                    'name': progress_step.name,
                    'sample_type': progress_step.sample_type,
                    'step_order': flow_step.step_order,
                    'description': progress_step.description,
                    'is_required': flow_step.is_required,
                    'tasks': [
                        {
                            'id': task.id,
                            'name': task.name,
                            'task_order': task.task_order,
                            'description': task.description
                        } for task in tasks
                    ]
                })
            
            return jsonify({
                'success': True,
                'data': steps_data,
                'flow_configuration': {
                    'id': flow_config.id,
                    'name': flow_config.name,
                    'sample_type': flow_config.sample_type,
                    'is_default': flow_config.is_default
                }
            })
        
        # If no specific configuration, get the default configuration for this sample type
        default_config = RNDFlowConfiguration.query.filter_by(
            sample_type=sample_type,
            is_default=True,
            is_active=True
        ).first()
        
        if default_config:
            # Use the default configuration
            flow_steps_query = RNDFlowStep.query.filter_by(flow_configuration_id=default_config.id)\
                .join(RNDProgressStep)\
                .order_by(RNDFlowStep.step_order)\
                .all()
            
            steps_data = []
            for flow_step in flow_steps_query:
                progress_step = flow_step.progress_step
                tasks = RNDProgressTask.query.filter_by(progress_step_id=progress_step.id)\
                    .order_by(RNDProgressTask.task_order).all()
                
                steps_data.append({
                    'id': progress_step.id,
                    'name': progress_step.name,
                    'sample_type': progress_step.sample_type,
                    'step_order': flow_step.step_order,
                    'description': progress_step.description,
                    'is_required': flow_step.is_required,
                    'tasks': [
                        {
                            'id': task.id,
                            'name': task.name,
                            'task_order': task.task_order,
                            'description': task.description
                        } for task in tasks
                    ]
                })
            
            return jsonify({
                'success': True,
                'data': steps_data,
                'flow_configuration': {
                    'id': default_config.id,
                    'name': default_config.name,
                    'sample_type': default_config.sample_type,
                    'is_default': default_config.is_default
                }
            })
        
        # Fallback to dynamic steps loading from database
        # Get ALL available progress steps from database (for flow configuration selection)
        # This allows flexibility to add new sample types and steps without modifying code
        all_progress_steps = RNDProgressStep.query.order_by(
            RNDProgressStep.sample_type, 
            RNDProgressStep.step_order
        ).all()
        
        if not all_progress_steps:
            return jsonify({'success': False, 'error': 'No progress steps available'}), 400
        
        # Get tasks for each step and build response
        steps_data = []
        for step in all_progress_steps:
            tasks = RNDProgressTask.query.filter_by(progress_step_id=step.id)\
                .order_by(RNDProgressTask.task_order).all()
            
            steps_data.append({
                'id': step.id,
                'name': step.name,
                'sample_type': step.sample_type,
                'step_order': step.step_order,
                'description': step.description,
                'is_required': True,
                'tasks': [
                    {
                        'id': task.id,
                        'name': task.name,
                        'task_order': task.task_order,
                        'description': task.description
                    } for task in tasks
                ]
            })
        
        return jsonify({
            'success': True,
            'data': steps_data,
            'flow_configuration': None  # Indicates fallback mode
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@rnd_cloudsphere_bp.route('/api/users')
@login_required
@require_rnd_access
def get_rnd_users():
    """Get R&D users for PIC assignment"""
    try:
        # Get R&D users (division_id = 6)
        users = User.query.filter_by(division_id=6, is_active=True).order_by(User.name).all()
        
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

def get_next_progress_assignment(progress_assignment):
    """Get the next progress assignment based on flow configuration or fallback to static workflow"""
    job_obj = progress_assignment.job
    
    # Try to use dynamic flow configuration first
    if job_obj.flow_configuration_id:
        flow_config = RNDFlowConfiguration.query.get(job_obj.flow_configuration_id)
        if flow_config:
            # Get flow steps in order
            flow_steps = RNDFlowStep.query.filter_by(flow_configuration_id=flow_config.id)\
                .join(RNDProgressStep)\
                .order_by(RNDFlowStep.step_order)\
                .all()
            
            # Find current step in the flow
            current_flow_step = None
            for i, flow_step in enumerate(flow_steps):
                if flow_step.progress_step_id == progress_assignment.progress_step_id:
                    current_flow_step = flow_step
                    current_index = i
                    break
            
            if current_flow_step and current_index + 1 < len(flow_steps):
                # Find next step in flow
                next_flow_step = flow_steps[current_index + 1]
                next_progress_step_id = next_flow_step.progress_step_id
                
                # Find assignment with this progress step
                next_assignment = RNDJobProgressAssignment.query.filter(
                    RNDJobProgressAssignment.job_id == job_obj.id,
                    RNDJobProgressAssignment.progress_step_id == next_progress_step_id,
                    RNDJobProgressAssignment.status == 'pending'
                ).first()
                
                if next_assignment:
                    print(f"DEBUG: Found next assignment via flow config: {next_assignment.progress_step.name}")
                    print(f"DEBUG: Current step: {progress_assignment.progress_step.name}")
                    print(f"DEBUG: Next step: {next_assignment.progress_step.name}")
                    print(f"DEBUG: Total steps in flow: {len(flow_steps)}")
                    return next_assignment
    
    # Fallback to static workflow if no flow configuration or not found
    print(f"DEBUG: Using fallback static workflow for {job_obj.sample_type}")
    
    # Define the correct order for each sample type workflow
    workflow_orders = {
        'RoHS Ribbon': [
            'Design & Artwork Approval',
            'Mastercard Release',
            'Polymer Order',
            'Polymer Receiving',
            'Proof Approval',
            'Sample Production',
            'Quality Validation'
        ],
        'RoHS ICB': [
            'Design & Artwork Approval',
            'Mastercard Release',
            'Proof Approval',
            'Sample Production',
            'Quality Validation'
        ],
        'Blank': [
            'Design & Artwork Approval',
            'Mastercard Release',
            'Initial Plotter',
            'Sample Production',
            'Quality Validation'
        ]
    }
    
    # Get the order for this sample type
    step_order = workflow_orders.get(job_obj.sample_type, [])
    
    # Find current step index
    current_step_name = progress_assignment.progress_step.name
    if current_step_name in step_order:
        current_index = step_order.index(current_step_name)
        
        # Find next step name
        if current_index + 1 < len(step_order):
            next_step_name = step_order[current_index + 1]
            
            # Find assignment with this step name
            next_assignment = RNDJobProgressAssignment.query.join(RNDProgressStep).filter(
                RNDJobProgressAssignment.job_id == job_obj.id,
                RNDProgressStep.name == next_step_name,
                RNDJobProgressAssignment.status == 'pending'
            ).first()
            
            if next_assignment:
                print(f"DEBUG: Found next assignment via static workflow: {next_assignment.progress_step.name}")
                print(f"DEBUG: Current step: {progress_assignment.progress_step.name}")
                print(f"DEBUG: Next step: {next_assignment.progress_step.name}")
                print(f"DEBUG: Total steps in workflow: {len(step_order)}")
                return next_assignment
    
    print("DEBUG: No next assignment found")
    return None

def is_final_progress_step(progress_assignment):
    """Check if this is the final step in the flow"""
    job_obj = progress_assignment.job
    
    # Try to use dynamic flow configuration first
    if job_obj.flow_configuration_id:
        flow_config = RNDFlowConfiguration.query.get(job_obj.flow_configuration_id)
        if flow_config:
            # Get flow steps in order
            flow_steps = RNDFlowStep.query.filter_by(flow_configuration_id=flow_config.id)\
                .order_by(RNDFlowStep.step_order)\
                .all()
            
            if flow_steps:
                # Check if current step is the last one
                last_flow_step = flow_steps[-1]
                if last_flow_step.progress_step_id == progress_assignment.progress_step_id:
                    print(f"DEBUG: This is final step via flow config: {progress_assignment.progress_step.name}")
                    print(f"DEBUG: Total steps in flow: {len(flow_steps)}")
                    print(f"DEBUG: Last step name: {last_flow_step.progress_step.name}")
                    return True
    
    # Fallback to static workflow
    print(f"DEBUG: Using fallback static workflow for final step check: {job_obj.sample_type}")
    
    # Define the correct order for each sample type workflow
    workflow_orders = {
        'RoHS Ribbon': [
            'Design & Artwork Approval',
            'Mastercard Release',
            'Polymer Order',
            'Polymer Receiving',
            'Proof Approval',
            'Sample Production',
            'Quality Validation'
        ],
        'RoHS ICB': [
            'Design & Artwork Approval',
            'Mastercard Release',
            'Proof Approval',
            'Sample Production',
            'Quality Validation'
        ],
        'Blank': [
            'Design & Artwork Approval',
            'Mastercard Release',
            'Initial Plotter',
            'Sample Production',
            'Quality Validation'
        ]
    }
    
    # Get the order for this sample type
    step_order = workflow_orders.get(job_obj.sample_type, [])
    
    # Find current step index
    current_step_name = progress_assignment.progress_step.name
    if current_step_name in step_order:
        current_index = step_order.index(current_step_name)
        
        # Check if this is the last step
        if current_index == len(step_order) - 1:
            print(f"DEBUG: This is final step via static workflow: {progress_assignment.progress_step.name}")
            print(f"DEBUG: Total steps in workflow: {len(step_order)}")
            print(f"DEBUG: Step index: {current_index}")
            return True
    
    return False

@rnd_cloudsphere_bp.route('/api/task/<int:task_assignment_id>/complete', methods=['POST'])
@login_required
@require_rnd_access
def complete_rnd_task(task_assignment_id):
    """Complete a task and upload evidence"""
    try:
        data = request.get_json()
        notes = data.get('notes', '')
        
        # Get task assignment
        task_assignment = RNDJobTaskAssignment.query.get_or_404(task_assignment_id)
        
        # Check if user is authorized (PIC of the progress step)
        progress_assignment = task_assignment.progress_assignment
        if progress_assignment.pic_id != current_user.id and not current_user.is_admin():
            return jsonify({'success': False, 'error': 'Not authorized to complete this task'}), 403
        
        if task_assignment.status == 'completed':
            return jsonify({'success': False, 'error': 'Task already completed'}), 400
        
        # Mark task as completed
        task_assignment.status = 'completed'
        task_assignment.completed_at = datetime.now(jakarta_tz)
        task_assignment.notes = notes
        
        # Create task completion record
        task_completion = RNDTaskCompletion(
            job_task_assignment_id=task_assignment.id,
            progress_task_id=task_assignment.progress_task_id,
            completed_at=datetime.now(jakarta_tz),
            completed_by=current_user.id,
            completion_notes=notes
        )
        db.session.add(task_completion)
        
        # Check if all tasks in this progress step are completed
        all_tasks_completed = all(
            ta.status == 'completed' for ta in progress_assignment.task_assignments
        )
        
        # DEBUG: Log task completion status
        print(f"DEBUG (complete): Checking task completion for step '{progress_assignment.progress_step.name}':")
        print(f"DEBUG (complete): Total tasks: {len(progress_assignment.task_assignments)}")
        completed_tasks = [ta for ta in progress_assignment.task_assignments if ta.status == 'completed']
        print(f"DEBUG (complete): Completed tasks: {len(completed_tasks)}")
        for ta in progress_assignment.task_assignments:
            print(f"DEBUG (complete): Task '{ta.progress_task.name}': {ta.status}")
        print(f"DEBUG (complete): All tasks completed? {all_tasks_completed}")
        
        if all_tasks_completed:
            # Mark progress step as completed
            progress_assignment.status = 'completed'
            progress_assignment.finished_at = datetime.now(jakarta_tz)
            
            # DEBUG: Log assignment details
            print(f"DEBUG (complete): Step marked as completed: {progress_assignment.progress_step.name}")
            print(f"DEBUG (complete): Note: This route (/api/task/<id>/complete) is deprecated, use /api/tasks/<id>/toggle instead")
            
            # DEBUG: Log current step and job info
            print(f"DEBUG (complete): Current step name: {progress_assignment.progress_step.name}")
            print(f"DEBUG (complete): Job ID: {progress_assignment.job_id}")
            print(f"DEBUG (complete): Job sample type: {progress_assignment.job.sample_type}")
            print(f"DEBUG (complete): Flow configuration ID: {progress_assignment.job.flow_configuration_id}")
            
            # Get all progress assignments for this job to debug
            all_assignments = RNDJobProgressAssignment.query.join(RNDProgressStep).filter(
                RNDJobProgressAssignment.job_id == progress_assignment.job_id
            ).all()
            
            print("DEBUG (complete): All assignments for this job:")
            for assignment in all_assignments:
                print(f"  - {assignment.progress_step.name} (status: {assignment.status})")
            
            # IMPORTANT: Flush session to ensure current assignment status is saved
            db.session.flush()
            
            # Check if all progress assignments are completed BEFORE finding next step
            # This must be done BEFORE we mark next assignment as in_progress
            all_assignments = RNDJobProgressAssignment.query.filter_by(job_id=progress_assignment.job_id).all()
            all_completed = all(pa.status == 'completed' for pa in all_assignments)
            
            # DEBUG: Log all assignments status BEFORE next assignment update
            print("DEBUG (complete): All assignments status check:")
            for assignment in all_assignments:
                print(f"  - {assignment.progress_step.name}: {assignment.status}")
            
            print(f"DEBUG (complete): All assignments completed? {all_completed}")
            print(f"DEBUG (complete): Total assignments: {len(all_assignments)}, Completed: {sum(1 for pa in all_assignments if pa.status == 'completed')}")
            
            # Only mark job as completed if ALL assignments are completed
            # This ensures no steps are left uncompleted, regardless of which is final
            if all_completed:
                print("DEBUG (complete): All assignments completed, marking job as completed")
                job_obj = progress_assignment.job
                job_obj.status = 'completed'
                job_obj.finished_at = datetime.now(jakarta_tz)
                print(f"DEBUG (complete): Job status updated to: {job_obj.status}")
                print(f"DEBUG (complete): Job finished_at set to: {job_obj.finished_at}")
            else:
                # Only find and activate next step if job is NOT complete
                print(f"DEBUG (complete): Not all assignments completed, job remains in progress. Completed: {sum(1 for pa in all_assignments if pa.status == 'completed')}/{len(all_assignments)}")
                
                # Find the next step using dynamic flow configuration or fallback
                next_assignment = get_next_progress_assignment(progress_assignment)
                
                # DEBUG: Log next assignment info
                if next_assignment:
                    print(f"DEBUG (complete): Found next assignment: {next_assignment.progress_step.name}")
                    print(f"DEBUG (complete): Next assignment status before update: {next_assignment.status}")
                    next_assignment.status = 'in_progress'
                    next_assignment.started_at = datetime.now(jakarta_tz)
                    print(f"DEBUG (complete): Next assignment status after update: {next_assignment.status}")
                else:
                    print("DEBUG (complete): No next assignment found")
        
        db.session.commit()
        
        # DEBUG: Verify job status after commit
        # Get the job object to refresh
        job_obj = progress_assignment.job
        db.session.refresh(job_obj)
        print(f"DEBUG (complete): Job status after commit: {job_obj.status}")
        print(f"DEBUG (complete): Job finished_at after commit: {job_obj.finished_at}")
        
        # AUTO-SYNC CHECK: Ensure completion % matches status
        # This triggers the property which will auto-update status if needed
        if job_obj.completion_percentage == 100 and job_obj.status != 'completed':
            print(f"DEBUG (complete): Auto-syncing job status from completion_percentage property")
            job_obj.status = 'completed'
            if not job_obj.finished_at:
                job_obj.finished_at = datetime.now(jakarta_tz)
            db.session.commit()
            print(f"DEBUG (complete): Job status after auto-sync: {job_obj.status}")
        
        return jsonify({
            'success': True,
            'message': 'Task completed successfully'
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500

@rnd_cloudsphere_bp.route('/api/tasks/<int:task_assignment_id>/toggle', methods=['POST'])
@login_required
@require_rnd_access
def toggle_rnd_task(task_assignment_id):
    """Toggle task status between pending and completed"""
    try:
        # Initialize variables to avoid UnboundLocalError
        job_obj = None
        next_assignment = None
        
        # Get task assignment
        task_assignment = RNDJobTaskAssignment.query.get_or_404(task_assignment_id)
        
        # Validate task assignment has required relationships
        if not task_assignment.progress_task_id:
            return jsonify({'success': False, 'error': 'Task is not properly configured'}), 400
        
        # Check if user is authorized (PIC of the progress step)
        progress_assignment = task_assignment.progress_assignment
        if not progress_assignment:
            return jsonify({'success': False, 'error': 'Progress assignment not found for this task'}), 404
            
        if progress_assignment.pic_id != current_user.id and not current_user.is_admin():
            return jsonify({'success': False, 'error': 'Not authorized to toggle this task'}), 403
        
        # Use raw SQL approach to avoid SQLAlchemy issues
        current_time = datetime.now(jakarta_tz)
        
        if task_assignment.status == 'completed':
            # Set to pending
            db.session.execute(
                text("""UPDATE rnd_job_task_assignments
                   SET status = 'pending', completed_at = NULL
                   WHERE id = :task_id"""),
                {'task_id': task_assignment.id}
            )
            
            # Delete completion record
            db.session.execute(
                text("""DELETE FROM rnd_task_completions
                   WHERE job_task_assignment_id = :task_id"""),
                {'task_id': task_assignment.id}
            )
        else:
            # Set to completed
            db.session.execute(
                text("""UPDATE rnd_job_task_assignments
                   SET status = 'completed', completed_at = :completed_at
                   WHERE id = :task_id"""),
                {
                    'task_id': task_assignment.id,
                    'completed_at': current_time
                }
            )
            
            # Use INSERT ... ON DUPLICATE KEY UPDATE to handle completion record
            db.session.execute(
                text("""INSERT INTO rnd_task_completions
                   (job_task_assignment_id, progress_task_id, completed_at, completed_by, created_at, updated_at)
                   VALUES (:job_task_assignment_id, :progress_task_id, :completed_at, :completed_by, :created_at, :updated_at)
                   ON DUPLICATE KEY UPDATE
                   completed_at = VALUES(completed_at),
                   completed_by = VALUES(completed_by),
                   updated_at = VALUES(updated_at)"""),
                {
                    'job_task_assignment_id': task_assignment.id,
                    'progress_task_id': task_assignment.progress_task_id,
                    'completed_at': current_time,
                    'completed_by': current_user.id,
                    'created_at': current_time,
                    'updated_at': current_time
                }
            )
        
        # Update progress assignment status if all tasks are completed
        all_tasks_completed = db.session.execute(
            text("""SELECT COUNT(*) = 0
               FROM rnd_job_task_assignments
               WHERE job_progress_assignment_id = :progress_assignment_id
               AND status != 'completed'"""),
            {'progress_assignment_id': progress_assignment.id}
        ).scalar()
        
        # DEBUG: Log task completion status
        print(f"DEBUG: Checking task completion for step '{progress_assignment.progress_step.name}':")
        print(f"DEBUG: Total tasks: {len(progress_assignment.task_assignments)}")
        completed_tasks = [ta for ta in progress_assignment.task_assignments if ta.status == 'completed']
        print(f"DEBUG: Completed tasks: {len(completed_tasks)}")
        for ta in progress_assignment.task_assignments:
            print(f"DEBUG: Task '{ta.progress_task.name}': {ta.status}")
        print(f"DEBUG: All tasks completed? {all_tasks_completed}")
        
        # HANDLE BOTH DIRECTIONS:
        # 1. If all tasks completed -> mark assignment as completed
        # 2. If any task incomplete -> reset assignment to in_progress
        
        if all_tasks_completed and progress_assignment.status != 'completed':
            db.session.execute(
                text("""UPDATE rnd_job_progress_assignments
                   SET status = 'completed', finished_at = :finished_at
                   WHERE id = :progress_assignment_id"""),
                {
                    'progress_assignment_id': progress_assignment.id,
                    'finished_at': current_time
                }
            )
            
            # DEBUG: Log current step and job info
            print(f"DEBUG: Current step name: {progress_assignment.progress_step.name}")
            print(f"DEBUG: Job ID: {progress_assignment.job_id}")
            print(f"DEBUG: Job sample type: {progress_assignment.job.sample_type}")
            print(f"DEBUG: Flow configuration ID: {progress_assignment.job.flow_configuration_id}")
            
            # Get all progress assignments for this job to debug
            all_assignments = RNDJobProgressAssignment.query.join(RNDProgressStep).filter(
                RNDJobProgressAssignment.job_id == progress_assignment.job_id
            ).all()
            
            print("DEBUG: All assignments for this job:")
            for assignment in all_assignments:
                print(f"  - {assignment.progress_step.name} (status: {assignment.status})")
            
            # Find the next step using dynamic flow configuration or fallback
            next_assignment = get_next_progress_assignment(progress_assignment)
            
            # DEBUG: Log next assignment info
            if next_assignment:
                print(f"DEBUG: Found next assignment: {next_assignment.progress_step.name}")
                print(f"DEBUG: Next assignment status before update: {next_assignment.status}")
                next_assignment.status = 'in_progress'
                next_assignment.started_at = current_time
                print(f"DEBUG: Next assignment status after update: {next_assignment.status}")
            else:
                print("DEBUG: No next assignment found")
            
            # Check if all progress assignments are completed before marking job as completed
            all_assignments = RNDJobProgressAssignment.query.filter_by(job_id=progress_assignment.job_id).all()
            all_completed = all(pa.status == 'completed' for pa in all_assignments)
            
            # DEBUG: Log all assignments status
            print("DEBUG: All assignments status check:")
            for assignment in all_assignments:
                print(f"  - {assignment.progress_step.name}: {assignment.status}")
            
            # DEBUG: Check if this is the final step
            is_final_step = is_final_progress_step(progress_assignment)
            print(f"DEBUG: Is this the final step? {is_final_step}")
            print(f"DEBUG: All assignments completed? {all_completed}")
            print(f"DEBUG: Total assignments: {len(all_assignments)}, Completed: {sum(1 for pa in all_assignments if pa.status == 'completed')}")
            
            # Only mark job as completed if ALL assignments are completed
            # This ensures no steps are left uncompleted, regardless of which is final
            if all_completed:
                print("DEBUG: All assignments completed, marking job as completed")
                job_obj = progress_assignment.job
                job_obj.status = 'completed'
                job_obj.finished_at = current_time
                print(f"DEBUG: Job status updated to: {job_obj.status}")
                print(f"DEBUG: Job finished_at set to: {job_obj.finished_at}")
            else:
                print(f"DEBUG: Not all assignments completed, job remains in progress. Completed: {sum(1 for pa in all_assignments if pa.status == 'completed')}/{len(all_assignments)}")
        else:
            # REVERSE: If any task was unchecked and assignment is now incomplete, reset it
            if not all_tasks_completed and progress_assignment.status == 'completed':
                print(f"DEBUG: Task unchecked! Resetting assignment status from completed to in_progress")
                db.session.execute(
                    text("""UPDATE rnd_job_progress_assignments
                       SET status = 'in_progress'
                       WHERE id = :progress_assignment_id"""),
                    {'progress_assignment_id': progress_assignment.id}
                )
        
        # SEND NOTIFICATION FOR STEP COMPLETION (toggle_rnd_task route)
        # Note: all_tasks_completed is the flag for step completion, check this instead of ORM status
        if all_tasks_completed and progress_assignment.status != 'completed':
            # This is the block where we just marked the step as completed, so send notification
            
            # AUTO-COMPLETE EXTERNAL DELAY if applicable
            try:
                from blueprints.external_delay_routes import auto_complete_external_delay_for_task
                completed_delay = auto_complete_external_delay_for_task(task_assignment)
                if completed_delay:
                    print(f"DEBUG: External delay auto-completed: ID={completed_delay.id}, Hours={completed_delay.external_wait_hours}")
            except Exception as e:
                logger.error(f"Error auto-completing external delay: {str(e)}")
                print(f"DEBUG: Error auto-completing external delay: {str(e)}")
            
            try:
                print(f"DEBUG (toggle notification): Preparing to send step completion notification from toggle route")
                print(f"DEBUG (toggle notification): Job ID: {progress_assignment.job.id}")
                print(f"DEBUG (toggle notification): Job job_id: {progress_assignment.job.job_id}")
                print(f"DEBUG (toggle notification): Step name: {progress_assignment.progress_step.name}")
                print(f"DEBUG (toggle notification): PIC: {progress_assignment.pic}")
                if progress_assignment.pic:
                    print(f"DEBUG (toggle notification): PIC name: {progress_assignment.pic.name}")
                else:
                    print(f"DEBUG (toggle notification): PIC is None!")
                
                print(f"DEBUG (toggle notification): Calling dispatch_rnd_step_completed...")
                result = NotificationDispatcher.dispatch_rnd_step_completed(
                    job_db_id=progress_assignment.job.id,
                    job_id=progress_assignment.job.job_id,
                    item_name=progress_assignment.job.item_name,
                    step_name=progress_assignment.progress_step.name,
                    pic_name=progress_assignment.pic.name if progress_assignment.pic else 'Unknown',
                    triggered_by_user_id=current_user.id
                )
                print(f"DEBUG (toggle notification): Notification sent successfully! Result: {result}")
            except Exception as e:
                print(f"DEBUG (toggle notification): ERROR in dispatch_rnd_step_completed: {str(e)}")
                logger.error(f"Failed to send RND step completed notification: {str(e)}", exc_info=True)
        
        db.session.commit()
        
        # RESET JOB STATUS IF NEEDED
        # If completion_percentage < 100 and job.status = completed, reset to in_progress
        job_obj = progress_assignment.job
        db.session.refresh(job_obj)
        
        completion_pct = job_obj.completion_percentage
        if completion_pct < 100 and job_obj.status == 'completed':
            print(f"DEBUG: Completion is now {completion_pct}%, resetting job status to in_progress")
            job_obj.status = 'in_progress'
            job_obj.finished_at = None  # Clear finished_at since job is no longer complete
            db.session.commit()
            print(f"DEBUG: Job status reset to: {job_obj.status}")
        
        # DEBUG: Verify job status after commit
        # Get the job object to refresh
        job_obj = progress_assignment.job
        db.session.refresh(job_obj)
        print(f"DEBUG: Job status after commit: {job_obj.status}")
        print(f"DEBUG: Job finished_at after commit: {job_obj.finished_at}")
        print(f"DEBUG: Job completion_percentage: {job_obj.completion_percentage}%")
        
        # Refresh objects to get updated state
        db.session.refresh(task_assignment)
        db.session.refresh(progress_assignment)
        
        return jsonify({
            'success': True,
            'message': 'Task status updated successfully',
            'data': {
                'task_status': task_assignment.status,
                'progress_status': progress_assignment.status
            }
        })
    except Exception as e:
        print(f"ERROR in toggle_rnd_task: {str(e)}")
        import traceback
        traceback.print_exc()
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500

@rnd_cloudsphere_bp.route('/api/upload-evidence', methods=['POST'])
@login_required
@require_rnd_access
def upload_rnd_evidence():
    """Upload evidence file for task or progress step completion"""
    try:
        # Handle both single file and multiple files
        files = request.files.getlist('files') if 'files' in request.files else []
        file = request.files.get('file') if 'file' in request.files else None
        
        # Use the first available file
        file_to_upload = file if file else (files[0] if files else None)
        
        if not file_to_upload:
            return jsonify({'success': False, 'error': 'No file provided'}), 400
        
        job_id = request.form.get('job_id')
        progress_assignment_id = request.form.get('progress_assignment_id')
        task_assignment_id = request.form.get('task_assignment_id')
        evidence_type = request.form.get('evidence_type', 'step_completion')  # step_completion or task_completion
        
        if not job_id:
            return jsonify({'success': False, 'error': 'Job ID required'}), 400
        
        if file.filename == '':
            return jsonify({'success': False, 'error': 'No file selected'}), 400
        
        # Check file type
        filename = secure_filename(file_to_upload.filename)
        file_extension = filename.rsplit('.', 1)[1].lower() if '.' in filename else ''
        
        # Allowed extensions
        photo_extensions = {'jpg', 'jpeg', 'png', 'gif'}
        document_extensions = {'pdf', 'docx', 'xlsx', 'doc', 'xls'}
        
        if file_extension not in photo_extensions and file_extension not in document_extensions:
            return jsonify({'success': False, 'error': 'File type not allowed'}), 400
        
        # Determine file type
        if file_extension in photo_extensions:
            file_type = 'photo'
        elif file_extension == 'pdf':
            file_type = 'pdf'
        else:
            file_type = 'document'
        
        # Create upload directory if it doesn't exist
        upload_dir = os.path.join(current_app.config['UPLOADS_PATH'], 'rnd_evidence')
        os.makedirs(upload_dir, exist_ok=True)
        
        # Generate unique filename
        timestamp = datetime.now(jakarta_tz).strftime('%Y%m%d_%H%M%S')
        unique_filename = f"rnd_evidence_{timestamp}_{filename}"
        
        # Save file
        file_path = os.path.join(upload_dir, unique_filename)
        file_to_upload.save(file_path)
        
        # Save to database
        evidence = RNDEvidenceFile(
            job_id=job_id,
            job_progress_assignment_id=progress_assignment_id if progress_assignment_id else None,
            job_task_assignment_id=task_assignment_id if task_assignment_id else None,
            filename=unique_filename,
            original_filename=filename,
            file_path=file_path,
            file_type=file_type,
            file_size=os.path.getsize(file_path),
            evidence_type=evidence_type,
            uploaded_by=current_user.id
        )
        
        db.session.add(evidence)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Evidence uploaded successfully',
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

@rnd_cloudsphere_bp.route('/api/verify-evidence/<int:evidence_id>', methods=['POST'])
@login_required
@require_rnd_access
def verify_rnd_evidence(evidence_id):
    """Verify uploaded evidence (admin only)"""
    try:
        if not current_user.is_admin():
            return jsonify({'success': False, 'error': 'Admin access required'}), 403
        
        data = request.get_json()
        evidence = RNDEvidenceFile.query.get_or_404(evidence_id)
        
        evidence.is_verified = data.get('is_verified', False)
        evidence.verified_by = current_user.id
        evidence.verified_at = datetime.now(jakarta_tz)
        evidence.verification_notes = data.get('verification_notes', '')
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Evidence verification updated'
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500

@rnd_cloudsphere_bp.route('/api/download-evidence/<int:evidence_id>')
@login_required
@require_rnd_access
def download_rnd_evidence(evidence_id):
    """Download evidence file"""
    try:
        evidence = RNDEvidenceFile.query.get_or_404(evidence_id)
        return send_file(
            evidence.file_path,
            as_attachment=True,
            download_name=evidence.original_filename
        )
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@rnd_cloudsphere_bp.route('/api/evidence-thumbnail/<int:evidence_id>')
@login_required
@require_rnd_access
def get_evidence_thumbnail(evidence_id):
    """Get evidence file thumbnail"""
    try:
        evidence = RNDEvidenceFile.query.get_or_404(evidence_id)
        
        # Check if thumbnail already exists
        thumbnail_path = evidence.file_path.replace('.', '_thumb.')
        if not thumbnail_path.endswith('_thumb.jpg'):
            # Handle files with multiple extensions
            base_path = evidence.file_path.rsplit('.', 1)[0]
            thumbnail_path = f"{base_path}_thumb.jpg"
        
        if os.path.exists(thumbnail_path):
            return send_file(thumbnail_path, mimetype='image/jpeg')
        
        # Generate thumbnail if it doesn't exist
        try:
            from PIL import Image
            import io
            
            # Handle PDF files
            if evidence.file_type.lower() == 'pdf' or evidence.original_filename.lower().endswith('.pdf'):
                return generate_pdf_thumbnail(evidence.file_path, thumbnail_path)
            
            # Only generate thumbnails for image files
            elif evidence.file_type.lower() in ['jpg', 'jpeg', 'png', 'bmp', 'gif', 'webp', 'photo']:
                # Open image and create thumbnail
                with Image.open(evidence.file_path) as img:
                    # Convert to RGB if necessary
                    if img.mode in ('RGBA', 'P'):
                        img = img.convert('RGB')
                    
                    # Create thumbnail
                    img.thumbnail((200, 200), Image.Resampling.LANCZOS)
                    
                    # Save thumbnail
                    img.save(thumbnail_path, 'JPEG', quality=85)
                
                return send_file(thumbnail_path, mimetype='image/jpeg')
            else:
                # Return default icon for non-image, non-PDF files
                return send_file('static/img/image-placeholder.png', mimetype='image/png')
            
        except Exception as e:
            print(f"Error generating thumbnail for {evidence.file_path}: {e}")
            # Return default image if thumbnail generation fails
            return send_file('static/img/image-placeholder.png', mimetype='image/png')
            
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

def generate_pdf_thumbnail(pdf_path, thumbnail_path):
    """Generate thumbnail for PDF file using first page"""
    try:
        import fitz  # PyMuPDF
        import os
        
        # Open PDF file
        pdf_document = fitz.open(pdf_path)
        
        # Get first page
        first_page = pdf_document[0]
        
        # Render page to image (pixmap)
        # Use higher resolution for better quality
        mat = fitz.Matrix(2.0, 2.0)  # 2x zoom for better quality
        pix = first_page.get_pixmap(matrix=mat)
        
        # Convert to PIL Image
        img_data = pix.tobytes("ppm")
        img = Image.open(io.BytesIO(img_data))
        
        # Create thumbnail
        img.thumbnail((200, 200), Image.Resampling.LANCZOS)
        
        # Save thumbnail
        img.save(thumbnail_path, 'JPEG', quality=85)
        
        # Close PDF document
        pdf_document.close()
        
        return send_file(thumbnail_path, mimetype='image/jpeg')
    
    except ImportError:
        # If PyMuPDF is not available, try with pdf2image
        try:
            from pdf2image import convert_from_path
            
            # Convert first page to image
            images = convert_from_path(pdf_path, first_page=0, last_page=1, dpi=150)
            if images:
                img = images[0]
                
                # Create thumbnail
                img.thumbnail((200, 200), Image.Resampling.LANCZOS)
                
                # Save thumbnail
                img.save(thumbnail_path, 'JPEG', quality=85)
                
                return send_file(thumbnail_path, mimetype='image/jpeg')
        
        except ImportError:
            print("Neither PyMuPDF nor pdf2image is available for PDF thumbnail generation")
            # Return default PDF icon
            return send_file('static/img/image-placeholder.png', mimetype='image/png')
    
    except Exception as e:
        print(f"Error generating PDF thumbnail for {pdf_path}: {e}")
        # Return default PDF icon
        return send_file('static/img/image-placeholder.png', mimetype='image/png')

@rnd_cloudsphere_bp.route('/api/evidence/<int:evidence_id>', methods=['DELETE'])
@login_required
@require_rnd_access
def delete_rnd_evidence(evidence_id):
    """Delete evidence file (admin or uploader)"""
    try:
        evidence = RNDEvidenceFile.query.get_or_404(evidence_id)
        
        # Check if user is admin or the uploader
        if not current_user.is_admin() and current_user.id != evidence.uploaded_by:
            return jsonify({'success': False, 'error': 'You do not have permission to delete this evidence'}), 403
        
        # Delete physical file
        try:
            if os.path.exists(evidence.file_path):
                os.remove(evidence.file_path)
        except Exception as e:
            print(f"Error deleting file {evidence.file_path}: {e}")
        
        # Delete database record
        db.session.delete(evidence)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Evidence deleted successfully'
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500

@rnd_cloudsphere_bp.route('/api/jobs/<int:job_id>/approve', methods=['POST'])
@login_required
@require_rnd_access
def approve_rnd_job(job_id):
    """Approve R&D job (admin only)"""
    try:
        if not current_user.is_admin():
            return jsonify({'success': False, 'error': 'Admin access required'}), 403
        
        job = RNDJob.query.get_or_404(job_id)
        
        if job.status != 'completed':
            return jsonify({'success': False, 'error': 'Only completed jobs can be approved'}), 400
        
        # Update job status to approved
        job.status = 'approved'
        job.updated_at = datetime.now(jakarta_tz)
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Job approved successfully'
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500

@rnd_cloudsphere_bp.route('/api/jobs/<int:job_id>/reject', methods=['POST'])
@login_required
@require_rnd_access
def reject_rnd_job(job_id):
    """Reject R&D job (admin only)"""
    try:
        if not current_user.is_admin():
            return jsonify({'success': False, 'error': 'Admin access required'}), 403
        
        data = request.get_json()
        reason = data.get('reason', '')
        
        if not reason:
            return jsonify({'success': False, 'error': 'Rejection reason is required'}), 400
        
        job = RNDJob.query.get_or_404(job_id)
        
        # Update job status to rejected
        job.status = 'rejected'
        job.notes = f"{job.notes or ''}\n\nRejection Reason: {reason}"
        job.updated_at = datetime.now(jakarta_tz)
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Job rejected successfully'
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500

@rnd_cloudsphere_bp.route('/api/jobs/<int:job_id>/export/pdf')
@login_required
@require_rnd_access
def export_rnd_job_pdf(job_id):
    """Export R&D job details as PDF with role-based security"""
    try:
        # Check if user has access to this job
        if not current_user.is_admin():
            # Check if user is assigned to this job
            user_assigned = RNDJobProgressAssignment.query.filter(
                and_(
                    RNDJobProgressAssignment.job_id == job_id,
                    RNDJobProgressAssignment.pic_id == current_user.id
                )
            ).first()
            
            if not user_assigned:
                return jsonify({
                    'success': False,
                    'error': 'Access denied. You are not assigned to this job.'
                }), 403
        
        # Generate PDF using the export service
        from services.rnd_pdf_export_service import RNDPDFExportService
        pdf_service = RNDPDFExportService(db.session)
        pdf_buffer = pdf_service.export_job_to_pdf(job_id, current_user.role, current_user.id)
        
        # Get job for filename
        job = RNDJob.query.get_or_404(job_id)
        
        # Generate filename
        filename = f"RND_Job_{job.job_id}_{datetime.now(jakarta_tz).strftime('%Y%m%d_%H%M%S')}.pdf"
        
        # Return PDF as downloadable file
        return send_file(
            pdf_buffer,
            as_attachment=True,
            download_name=filename,
            mimetype='application/pdf'
        )
        
    except Exception as e:
        current_app.logger.error(f"Error exporting PDF for job {job_id}: {str(e)}")
        return jsonify({
            'success': False,
            'error': f'Error exporting PDF: {str(e)}'
        }), 500

@rnd_cloudsphere_bp.route('/pdf-viewer/<int:evidence_id>')
@login_required
@require_rnd_access
def pdf_viewer(evidence_id):
    """Render PDF viewer page for evidence file"""
    try:
        evidence = RNDEvidenceFile.query.get_or_404(evidence_id)
        
        # Only allow PDF files
        if evidence.file_type.lower() != 'pdf' and not evidence.original_filename.lower().endswith('.pdf'):
            return render_template('error.html',
                               error_title='File Type Not Supported',
                               error_message='Only PDF files can be viewed in the PDF viewer.',
                               back_url=request.referrer)
        
        # Get the download URL for the PDF
        pdf_url = f'/impact/rnd-cloudsphere/api/download-evidence/{evidence_id}'
        
        return render_template('pdf_viewer.html',
                           pdf_url=pdf_url,
                           filename=evidence.original_filename)
    except Exception as e:
        return render_template('error.html',
                           error_title='Error Loading PDF',
                           error_message=f'An error occurred while loading the PDF: {str(e)}',
                           back_url=request.referrer)

# Initialize R&D progress steps and tasks
def init_rnd_data():
    """Initialize default R&D progress steps and tasks based on new requirements"""
    with rnd_cloudsphere_bp.app_context():
        try:
            # Check if progress steps already exist
            if RNDProgressStep.query.first():
                return
            
            # Define progress steps for each sample type
            progress_data = [
                {
                    'sample_type': 'Design',
                    'steps': [
                        {
                            'name': 'Design & Artwork Approval',
                            'step_order': 1,
                            'tasks': [
                                'Check EPSON Blue Print',
                                'Send Email Initial Design to CSR',
                                'Create Simulation Artwork',
                                'Attend Meeting Proof',
                                'Create Final Artwork',
                                'Create Digital Print',
                                'Approval Digital Print to CSR'
                            ]
                        }
                    ]
                },
                {
                    'sample_type': 'Mastercard',
                    'steps': [
                        {
                            'name': 'Mastercard Release',
                            'step_order': 1,
                            'tasks': [
                                'Receiving LPM',
                                'Create Mastercard',
                                'Printout Mastercard',
                                'Approval Mastercard',
                                'Scan & Copy Mastercard',
                                'Handover Mastercard to PPIC'
                            ]
                        }
                    ]
                },
                {
                    'sample_type': 'Blank',
                    'steps': [
                        {
                            'name': 'Initial Plotter',
                            'step_order': 1,
                            'tasks': [
                                'Check EPSON Blue Print',
                                'Create Technical Drawing',
                                'Create Plotter',
                                'Fitting Result Plotter',
                                'Create Simulation Layout',
                                'Create LPD Pisau & Millar'
                            ]
                        },
                        {
                            'name': 'Sample Production',
                            'step_order': 2,
                            'tasks': [
                                'Create Material & Process Memo to PPIC',
                                'Laminator Process',
                                'Diecut Process & Fitting',
                                'Lamina Process & Fitting',
                                'Pack & Send Sample'
                            ]
                        },
                        {
                            'name': 'Quality Validation',
                            'step_order': 3,
                            'tasks': [
                                'Process CoA to QC',
                                'Moisture Test',
                                'Pushpull Test',
                                'Box Compression Test',
                                'Process Data PAC & Send Email'
                            ]
                        }
                    ]
                },
                {
                    'sample_type': 'RoHS ICB',
                    'steps': [
                        {
                            'name': 'Proof Approval',
                            'step_order': 1,
                            'tasks': [
                                'Approval Press Offset'
                            ]
                        },
                        {
                            'name': 'Sample Production',
                            'step_order': 2,
                            'tasks': [
                                'Laminator Process',
                                'Diecut Process & Fitting',
                                'Lamina Process & Fitting',
                                'Pack & Send Sample'
                            ]
                        },
                        {
                            'name': 'Quality Validation',
                            'step_order': 3,
                            'tasks': [
                                'Process CoA to QC',
                                'Moisture Test',
                                'Pushpull Test',
                                'Box Compression Test',
                                'Process Data PAC & Send Email'
                            ]
                        }
                    ]
                },
                {
                    'sample_type': 'RoHS Ribbon',
                    'steps': [
                        {
                            'name': 'Proof Approval',
                            'step_order': 1,
                            'tasks': [
                                'Approval Press Offset',
                                'Approval Varnish / Spot UV'
                            ]
                        },
                        {
                            'name': 'Sample Production',
                            'step_order': 2,
                            'tasks': [
                                'Diecut Process & Fitting',
                                'Glue Process & Fitting',
                                'Pack & Send Sample'
                            ]
                        },
                        {
                            'name': 'Quality Validation',
                            'step_order': 3,
                            'tasks': [
                                'Process CoA to QC',
                                'Moisture Test',
                                'Pushpull Test',
                                'Box Compression Test',
                                'Process Data PAC & Send Email'
                            ]
                        }
                    ]
                },
                {
                    'sample_type': 'Polymer Ribbon',
                    'steps': [
                        {
                            'name': 'Polymer Order',
                            'step_order': 1,
                            'tasks': [
                                'Create Data Polymer & Millar',
                                'Create New Item Code Polymer',
                                'Create Memo PO to Supplier',
                                'Email Order Polymer to Supplier',
                                'Request Millar to DC Service'
                            ]
                        },
                        {
                            'name': 'Polymer Receiving',
                            'step_order': 2,
                            'tasks': [
                                'Check Incoming Polymer & Handover to Varnish'
                            ]
                        }
                    ]
                },
                {
                    'sample_type': 'Light-Standard-Dark Reference',
                    'steps': [
                        {
                            'name': 'Determine Light-Standard-Dark Reference',
                            'step_order': 1,
                            'tasks': [
                                'Prepare Light-Standard-Dark Samples',
                                'Create LSD Reference Sheet',
                                'Approval LSD by Press',
                                'Approval LSD by Quality Control',
                                'Approval LSD by Marketing',
                                'Approval LSD by Prepress',
                                'Handover LSD to Quality Control'
                            ]
                        }
                    ]
                }                                
            ]
            
            # Create progress steps and tasks
            for sample_type_data in progress_data:
                sample_type = sample_type_data['sample_type']
                steps = sample_type_data['steps']
                
                for step_data in steps:
                    # Create progress step
                    progress_step = RNDProgressStep(
                        name=step_data['name'],
                        sample_type=sample_type,
                        step_order=step_data['step_order']
                    )
                    db.session.add(progress_step)
                    db.session.flush()  # Get step ID
                    
                    # Create tasks for this step
                    for i, task_name in enumerate(step_data['tasks']):
                        task = RNDProgressTask(
                            progress_step_id=progress_step.id,
                            name=task_name,
                            task_order=i + 1
                        )
                        db.session.add(task)
            
            db.session.commit()
            
        except Exception as e:
            print(f"Error initializing R&D data: {e}")
            db.session.rollback()

@rnd_cloudsphere_bp.route('/api/debug/progress-steps')
@login_required
@require_rnd_access
def debug_progress_steps():
    """Debug endpoint to check progress steps data"""
    try:
        # Get all progress steps
        all_steps = RNDProgressStep.query.order_by(RNDProgressStep.sample_type, RNDProgressStep.step_order).all()
        
        steps_by_type = {}
        for step in all_steps:
            if step.sample_type not in steps_by_type:
                steps_by_type[step.sample_type] = []
            steps_by_type[step.sample_type].append({
                'id': step.id,
                'name': step.name,
                'step_order': step.step_order
            })
        
        return jsonify({
            'success': True,
            'data': steps_by_type
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

# Collaborative Notes API Routes

@rnd_cloudsphere_bp.route('/api/jobs/<int:job_id>/notes')
@login_required
@require_rnd_access
def get_job_notes(job_id):
    """Get all collaborative notes for a job"""
    try:
        job = RNDJob.query.get_or_404(job_id)
        
        # Check if user has access to this job
        if not current_user.is_admin():
            # Check if user is assigned to this job
            has_access = RNDJobProgressAssignment.query.filter_by(
                job_id=job_id,
                pic_id=current_user.id
            ).first()
            
            if not has_access:
                return jsonify({'success': False, 'error': 'Access denied'}), 403
        
        # Get notes, ordered by pinned status first, then by creation date
        notes = RNDJobNote.query.filter_by(job_id=job_id).order_by(
            RNDJobNote.is_pinned.desc(),
            RNDJobNote.created_at.desc()
        ).all()
        
        notes_data = []
        for note in notes:
            notes_data.append({
                'id': note.id,
                'job_id': note.job_id,
                'user_id': note.user_id,
                'user_name': note.user.name if note.user else None,
                'note_content': note.note_content,
                'note_type': note.note_type,
                'is_pinned': note.is_pinned,
                'created_at': note.created_at.strftime('%Y-%m-%d %H:%M') if note.created_at else None,
                'updated_at': note.updated_at.strftime('%Y-%m-%d %H:%M') if note.updated_at else None,
                'can_edit': note.user_id == current_user.id or current_user.is_admin(),
                'can_delete': note.user_id == current_user.id or current_user.is_admin()
            })
        
        return jsonify({
            'success': True,
            'data': notes_data
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@rnd_cloudsphere_bp.route('/api/jobs/<int:job_id>/notes', methods=['POST'])
@login_required
@require_rnd_access
def add_job_note(job_id):
    """Add a new collaborative note to a job"""
    try:
        job = RNDJob.query.get_or_404(job_id)
        
        # Check if user has access to this job
        if not current_user.is_admin():
            # Check if user is assigned to this job
            has_access = RNDJobProgressAssignment.query.filter_by(
                job_id=job_id,
                pic_id=current_user.id
            ).first()
            
            if not has_access:
                return jsonify({'success': False, 'error': 'Access denied'}), 403
        
        data = request.get_json()
        note_content = data.get('note_content', '').strip()
        note_type = data.get('note_type', 'general')
        
        if not note_content:
            return jsonify({'success': False, 'error': 'Note content is required'}), 400
        
        # Create new note
        note = RNDJobNote(
            job_id=job_id,
            user_id=current_user.id,
            note_content=note_content,
            note_type=note_type,
            is_pinned=False
        )
        
        db.session.add(note)
        db.session.commit()
        
        # Dispatch notification to job PICs + admins (excluding the note author)
        try:
            NotificationDispatcher.dispatch_team_note_new(
                job_db_id=job.id,
                job_id=job.job_id,
                item_name=job.item_name,
                note_author_id=current_user.id,
                note_author_name=current_user.name,
                note_content=note_content,
                triggered_by_user_id=current_user.id
            )
        except Exception as e:
            logger.error(f"Error dispatching team note notification: {str(e)}")
            # Don't fail the note creation if notification dispatch fails
        
        return jsonify({
            'success': True,
            'message': 'Note added successfully',
            'data': {
                'id': note.id,
                'user_name': current_user.name,
                'note_content': note.note_content,
                'note_type': note.note_type,
                'is_pinned': note.is_pinned,
                'created_at': note.created_at.strftime('%Y-%m-%d %H:%M'),
                'can_edit': True,
                'can_delete': True
            }
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500

@rnd_cloudsphere_bp.route('/api/jobs/notes/<int:note_id>', methods=['PUT'])
@login_required
@require_rnd_access
def update_job_note(note_id):
    """Update a collaborative note"""
    try:
        note = RNDJobNote.query.get_or_404(note_id)
        
        # Check if user can edit this note
        if note.user_id != current_user.id and not current_user.is_admin():
            return jsonify({'success': False, 'error': 'Access denied'}), 403
        
        data = request.get_json()
        note_content = data.get('note_content', '').strip()
        note_type = data.get('note_type', note.note_type)
        
        if not note_content:
            return jsonify({'success': False, 'error': 'Note content is required'}), 400
        
        # Update note
        note.note_content = note_content
        note.note_type = note_type
        note.updated_at = datetime.now(jakarta_tz)
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Note updated successfully',
            'data': {
                'id': note.id,
                'note_content': note.note_content,
                'note_type': note.note_type,
                'updated_at': note.updated_at.strftime('%Y-%m-%d %H:%M')
            }
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500

@rnd_cloudsphere_bp.route('/api/jobs/notes/<int:note_id>', methods=['DELETE'])
@login_required
@require_rnd_access
def delete_job_note(note_id):
    """Delete a collaborative note"""
    try:
        note = RNDJobNote.query.get_or_404(note_id)
        
        # Check if user can delete this note
        if note.user_id != current_user.id and not current_user.is_admin():
            return jsonify({'success': False, 'error': 'Access denied'}), 403
        
        db.session.delete(note)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Note deleted successfully'
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500

@rnd_cloudsphere_bp.route('/api/jobs/notes/<int:note_id>/pin', methods=['PUT'])
@login_required
@require_rnd_access
def toggle_pin_note(note_id):
    """Toggle pin status of a collaborative note"""
    try:
        note = RNDJobNote.query.get_or_404(note_id)
        
        # Check if user can pin this note (admin only or note owner)
        if note.user_id != current_user.id and not current_user.is_admin():
            return jsonify({'success': False, 'error': 'Access denied'}), 403
        
        # Toggle pin status
        note.is_pinned = not note.is_pinned
        note.updated_at = datetime.now(jakarta_tz)
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': f'Note {"pinned" if note.is_pinned else "unpinned"} successfully',
            'data': {
                'id': note.id,
                'is_pinned': note.is_pinned,
                'updated_at': note.updated_at.strftime('%Y-%m-%d %H:%M')
            }
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500

# Flow Configuration API Routes

@rnd_cloudsphere_bp.route('/api/flow-configurations')
@login_required
@require_rnd_access
def get_flow_configurations():
    """Get all flow configurations, optionally filtered by sample type"""
    try:
        sample_type = request.args.get('sample_type', '')
        include_inactive = request.args.get('include_inactive', 'false').lower() == 'true'
        
        query = RNDFlowConfiguration.query
        
        if sample_type:
            query = query.filter_by(sample_type=sample_type)
        
        if not include_inactive:
            query = query.filter_by(is_active=True)
        
        configurations = query.order_by(RNDFlowConfiguration.sample_type, RNDFlowConfiguration.name).all()
        
        configurations_data = []
        for config in configurations:
            configurations_data.append(config.to_dict())
        
        return jsonify({
            'success': True,
            'data': configurations_data
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@rnd_cloudsphere_bp.route('/api/flow-configurations/<int:config_id>')
@login_required
@require_rnd_access
def get_flow_configuration(config_id):
    """Get specific flow configuration with steps"""
    try:
        config = RNDFlowConfiguration.query.get_or_404(config_id)
        
        return jsonify({
            'success': True,
            'data': config.to_dict()
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@rnd_cloudsphere_bp.route('/api/flow-configurations', methods=['POST'])
@login_required
@require_rnd_access
def create_flow_configuration():
    """Create new flow configuration"""
    try:
        if not current_user.is_admin():
            return jsonify({'success': False, 'error': 'Admin access required'}), 403
        
        data = request.get_json()
        
        # Validate required fields
        required_fields = ['name', 'sample_type']
        for field in required_fields:
            if not data.get(field):
                return jsonify({'success': False, 'error': f'{field} is required'}), 400
        
        # If this is set as default, unset other defaults for this sample type
        if data.get('is_default', False):
            RNDFlowConfiguration.query.filter_by(sample_type=data['sample_type']).update({'is_default': False})
        
        # Create configuration
        config = RNDFlowConfiguration(
            name=data['name'],
            sample_type=data['sample_type'],
            description=data.get('description', ''),
            is_default=data.get('is_default', False),
            is_active=data.get('is_active', True),
            created_by=current_user.id
        )
        
        db.session.add(config)
        db.session.flush()  # Get config ID
        
        # Add flow steps if provided
        flow_steps = data.get('flow_steps', [])
        for step_data in flow_steps:
            progress_step_id = step_data.get('progress_step_id')
            step_order = step_data.get('step_order')
            is_required = step_data.get('is_required', True)
            
            if progress_step_id and step_order is not None:
                flow_step = RNDFlowStep(
                    flow_configuration_id=config.id,
                    progress_step_id=progress_step_id,
                    step_order=step_order,
                    is_required=is_required
                )
                db.session.add(flow_step)
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Flow configuration created successfully',
            'data': config.to_dict()
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500

@rnd_cloudsphere_bp.route('/api/init-default-flow-configurations', methods=['POST'])
@login_required
@require_rnd_access
def init_default_flow_configurations():
    """Initialize default flow configurations based on existing static data"""
    try:
        if not current_user.is_admin():
            return jsonify({'success': False, 'error': 'Admin access required'}), 403
        
        # Check if configurations already exist
        existing_configs = RNDFlowConfiguration.query.count()
        if existing_configs > 0:
            return jsonify({
                'success': False,
                'error': 'Flow configurations already exist. Delete existing configurations first.'
            }), 400
        
        # Define default flow configurations based on existing static mappings
        default_flows = [
            {
                'name': 'Standard Blank Workflow',
                'sample_type': 'Blank',
                'description': 'Standard workflow for Blank sample type',
                'is_default': True,
                'step_order': [
                    'Design & Artwork Approval',
                    'Mastercard Release',
                    'Initial Plotter',
                    'Sample Production',
                    'Quality Validation'
                ]
            },
            {
                'name': 'Standard RoHS ICB Workflow',
                'sample_type': 'RoHS ICB',
                'description': 'Standard workflow for RoHS ICB sample type',
                'is_default': True,
                'step_order': [
                    'Design & Artwork Approval',
                    'Mastercard Release',
                    'Proof Approval',
                    'Sample Production',
                    'Quality Validation'
                ]
            },
            {
                'name': 'Standard RoHS Ribbon Workflow',
                'sample_type': 'RoHS Ribbon',
                'description': 'Standard workflow for RoHS Ribbon sample type',
                'is_default': True,
                'step_order': [
                    'Design & Artwork Approval',
                    'Mastercard Release',
                    'Polymer Order',
                    'Polymer Receiving',
                    'Proof Approval',
                    'Sample Production',
                    'Quality Validation'
                ]
            }
        ]
        
        created_configs = []
        
        for flow_data in default_flows:
            # Create flow configuration
            config = RNDFlowConfiguration(
                name=flow_data['name'],
                sample_type=flow_data['sample_type'],
                description=flow_data['description'],
                is_default=flow_data['is_default'],
                is_active=True,
                created_by=current_user.id
            )
            
            db.session.add(config)
            db.session.flush()  # Get config ID
            
            # Add flow steps
            for order, step_name in enumerate(flow_data['step_order'], 1):
                # Find the progress step with this name
                progress_step = RNDProgressStep.query.filter_by(name=step_name).first()
                
                if progress_step:
                    flow_step = RNDFlowStep(
                        flow_configuration_id=config.id,
                        progress_step_id=progress_step.id,
                        step_order=order,
                        is_required=True
                    )
                    db.session.add(flow_step)
            
            created_configs.append(config.to_dict())
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Default flow configurations initialized successfully',
            'data': created_configs
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500

@rnd_cloudsphere_bp.route('/api/flow-configurations/<int:config_id>', methods=['PUT'])
@login_required
@require_rnd_access
def update_flow_configuration(config_id):
    """Update flow configuration"""
    try:
        if not current_user.is_admin():
            return jsonify({'success': False, 'error': 'Admin access required'}), 403
        
        config = RNDFlowConfiguration.query.get_or_404(config_id)
        data = request.get_json()
        
        # Update configuration fields
        if data.get('name'):
            config.name = data['name']
        if data.get('sample_type'):
            config.sample_type = data['sample_type']
        if 'description' in data:
            config.description = data['description']
        if 'is_default' in data:
            # If this is set as default, unset other defaults for this sample type
            if data['is_default']:
                RNDFlowConfiguration.query.filter(
                    RNDFlowConfiguration.sample_type == config.sample_type,
                    RNDFlowConfiguration.id != config_id
                ).update({'is_default': False})
            config.is_default = data['is_default']
        if 'is_active' in data:
            config.is_active = data['is_active']
        
        config.updated_at = datetime.now(jakarta_tz)
        
        # Update flow steps if provided
        if 'flow_steps' in data:
            # Delete existing flow steps
            RNDFlowStep.query.filter_by(flow_configuration_id=config_id).delete()
            
            # Add new flow steps
            flow_steps = data['flow_steps']
            for step_data in flow_steps:
                progress_step_id = step_data.get('progress_step_id')
                step_order = step_data.get('step_order')
                is_required = step_data.get('is_required', True)
                
                if progress_step_id and step_order is not None:
                    flow_step = RNDFlowStep(
                        flow_configuration_id=config_id,
                        progress_step_id=progress_step_id,
                        step_order=step_order,
                        is_required=is_required
                    )
                    db.session.add(flow_step)
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Flow configuration updated successfully',
            'data': config.to_dict()
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500

@rnd_cloudsphere_bp.route('/api/flow-configurations/<int:config_id>', methods=['DELETE'])
@login_required
@require_rnd_access
def delete_flow_configuration(config_id):
    """Delete flow configuration"""
    try:
        if not current_user.is_admin():
            return jsonify({'success': False, 'error': 'Admin access required'}), 403
        
        config = RNDFlowConfiguration.query.get_or_404(config_id)
        
        # Check if this configuration is being used by any jobs
        from models_rnd import RNDJob
        jobs_using_config = RNDJob.query.filter_by(flow_configuration_id=config_id).count()
        
        if jobs_using_config > 0:
            return jsonify({
                'success': False,
                'error': f'Cannot delete configuration. It is being used by {jobs_using_config} jobs.'
            }), 400
        
        db.session.delete(config)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Flow configuration deleted successfully'
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500

@rnd_cloudsphere_bp.route('/api/flow-configurations/<int:config_id>/set-default', methods=['POST'])
@login_required
@require_rnd_access
def set_default_flow_configuration(config_id):
    """Set flow configuration as default for its sample type"""
    try:
        if not current_user.is_admin():
            return jsonify({'success': False, 'error': 'Admin access required'}), 403
        
        config = RNDFlowConfiguration.query.get_or_404(config_id)
        
        # Unset other defaults for this sample type
        RNDFlowConfiguration.query.filter(
            RNDFlowConfiguration.sample_type == config.sample_type,
            RNDFlowConfiguration.id != config_id
        ).update({'is_default': False})
        
        # Set this as default
        config.is_default = True
        config.updated_at = datetime.now(jakarta_tz)
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': f'Configuration set as default for {config.sample_type}'
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500

@rnd_cloudsphere_bp.route('/api/jobs/<int:job_id>/final-step')
@login_required
@require_rnd_access
def get_job_final_step(job_id):
    """Get the final step name for a job based on its flow configuration"""
    try:
        job = RNDJob.query.get_or_404(job_id)
        
        # Try to use dynamic flow configuration first
        if job.flow_configuration_id:
            flow_config = RNDFlowConfiguration.query.get(job.flow_configuration_id)
            if flow_config:
                # Get flow steps in order
                flow_steps = RNDFlowStep.query.filter_by(flow_configuration_id=flow_config.id)\
                    .join(RNDProgressStep)\
                    .order_by(RNDFlowStep.step_order)\
                    .all()
                
                if flow_steps:
                    # Get the last step
                    last_flow_step = flow_steps[-1]
                    final_step = RNDProgressStep.query.get(last_flow_step.progress_step_id)
                    
                    # DEBUG: Log flow configuration details
                    print(f"DEBUG (get_job_final_step): Job ID {job_id} using flow configuration:")
                    print(f"  - Flow config ID: {flow_config.id}")
                    print(f"  - Flow config name: {flow_config.name}")
                    print(f"  - Total steps in flow: {len(flow_steps)}")
                    print(f"  - Final step: {final_step.name}")
                    
                    return jsonify({
                        'success': True,
                        'data': {
                            'final_step_name': final_step.name,
                            'flow_configuration_used': True
                        }
                    })
        
        # Fallback to static workflow
        sample_type = job.sample_type
        
        # Define final step for each sample type workflow
        final_steps = {
            'RoHS Ribbon': 'Quality Validation',
            'RoHS ICB': 'Quality Validation',
            'Blank': 'Quality Validation'
        }
        
        final_step_name = final_steps.get(sample_type, 'Quality Validation')
        
        # DEBUG: Log fallback details
        print(f"DEBUG (get_job_final_step): Job ID {job_id} using fallback static workflow:")
        print(f"  - Sample type: {sample_type}")
        print(f"  - Final step from static mapping: {final_step_name}")
        print(f"  - Flow configuration ID: {job.flow_configuration_id}")
        
        return jsonify({
            'success': True,
            'data': {
                'final_step_name': final_step_name,
                'flow_configuration_used': False
            }
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@rnd_cloudsphere_bp.route('/api/jobs/<int:job_id>/debug-status')
@login_required
@require_rnd_access
def debug_job_status(job_id):
    """Debug endpoint to check job and progress assignments status"""
    try:
        job = RNDJob.query.get_or_404(job_id)
        
        # Get all progress assignments
        all_assignments = RNDJobProgressAssignment.query.filter_by(job_id=job_id).all()
        
        # Check completion status
        completed_assignments = [pa for pa in all_assignments if pa.status == 'completed']
        all_completed = len(completed_assignments) == len(all_assignments)
        
        debug_info = {
            'job_id': job_id,
            'job_status': job.status,
            'job_finished_at': job.finished_at.isoformat() if job.finished_at else None,
            'flow_configuration_id': job.flow_configuration_id,
            'total_assignments': len(all_assignments),
            'completed_assignments': len(completed_assignments),
            'all_completed': all_completed,
            'assignments': []
        }
        
        # Add detailed assignment info
        for pa in all_assignments:
            assignment_info = {
                'id': pa.id,
                'progress_step_name': pa.progress_step.name,
                'status': pa.status,
                'started_at': pa.started_at.isoformat() if pa.started_at else None,
                'finished_at': pa.finished_at.isoformat() if pa.finished_at else None,
                'tasks': []
            }
            
            # Add task info
            for ta in pa.task_assignments:
                task_info = {
                    'id': ta.id,
                    'task_name': ta.progress_task.name,
                    'status': ta.status,
                    'completed_at': ta.completed_at.isoformat() if ta.completed_at else None
                }
                assignment_info['tasks'].append(task_info)
            
            debug_info['assignments'].append(assignment_info)
        
        return jsonify({
            'success': True,
            'data': debug_info
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@rnd_cloudsphere_bp.route('/api/jobs/<int:job_id>/force-complete', methods=['POST'])
@login_required
@require_rnd_access
def force_complete_job(job_id):
    """Force complete a job - temporary debugging endpoint"""
    try:
        if not current_user.is_admin():
            return jsonify({'success': False, 'error': 'Admin access required'}), 403
        
        job = RNDJob.query.get_or_404(job_id)
        
        # Get all progress assignments
        all_assignments = RNDJobProgressAssignment.query.filter_by(job_id=job_id).all()
        
        # Check completion status
        completed_assignments = [pa for pa in all_assignments if pa.status == 'completed']
        all_completed = len(completed_assignments) == len(all_assignments)
        
        print(f"DEBUG (force_complete): Job {job_id} - {job.job_id}")
        print(f"DEBUG (force_complete): Current job status: {job.status}")
        print(f"DEBUG (force_complete): Total assignments: {len(all_assignments)}")
        print(f"DEBUG (force_complete): Completed assignments: {len(completed_assignments)}")
        print(f"DEBUG (force_complete): All completed: {all_completed}")
        
        if all_completed:
            # Force job completion
            job.status = 'completed'
            job.finished_at = datetime.now(jakarta_tz)
            
            # Mark any remaining in_progress assignments as completed
            for pa in all_assignments:
                if pa.status == 'in_progress':
                    pa.status = 'completed'
                    pa.finished_at = datetime.now(jakarta_tz)
                    print(f"DEBUG (force_complete): Force completing assignment: {pa.progress_step.name}")
            
            db.session.commit()
            
            # Refresh and verify
            db.session.refresh(job)
            print(f"DEBUG (force_complete): Job status after update: {job.status}")
            print(f"DEBUG (force_complete): Job finished_at after update: {job.finished_at}")
            
            return jsonify({
                'success': True,
                'message': 'Job force completed successfully',
                'data': {
                    'job_status': job.status,
                    'job_finished_at': job.finished_at.isoformat() if job.finished_at else None
                }
            })
        else:
            return jsonify({
                'success': False,
                'error': f'Not all assignments completed. {len(completed_assignments)}/{len(all_assignments)} completed.',
                'data': {
                    'total_assignments': len(all_assignments),
                    'completed_assignments': len(completed_assignments),
                    'incomplete_assignments': [
                        {
                            'step_name': pa.progress_step.name,
                            'status': pa.status
                        } for pa in all_assignments if pa.status != 'completed'
                    ]
                }
            })
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500


@rnd_cloudsphere_bp.route('/api/jobs/<int:job_id>/complete-if-ready', methods=['POST'])
@login_required
@require_rnd_access
def complete_job_if_ready(job_id):
    """Check if all progress assignments are completed and finalize job if so.

    This endpoint can be called by admins or by assigned PICs (useful for PIC of final step to
    ensure job is finalized immediately after finishing last task).
    """
    try:
        job = RNDJob.query.get_or_404(job_id)

        # Get all progress assignments
        all_assignments = RNDJobProgressAssignment.query.filter_by(job_id=job_id).all()
        completed_assignments = [pa for pa in all_assignments if pa.status == 'completed']
        all_completed = len(completed_assignments) == len(all_assignments)

        # If not all completed, return useful diagnostic
        if not all_completed:
            return jsonify({
                'success': False,
                'error': 'Not all assignments completed.',
                'data': {
                    'total_assignments': len(all_assignments),
                    'completed_assignments': len(completed_assignments),
                    'incomplete_assignments': [
                        {
                            'step_name': pa.progress_step.name,
                            'status': pa.status
                        } for pa in all_assignments if pa.status != 'completed'
                    ]
                }
            }), 400

        # Authorization: allow admins or any PIC assigned to this job to finalize
        pic_ids = {pa.pic_id for pa in all_assignments if pa.pic_id}
        if not current_user.is_admin() and current_user.id not in pic_ids:
            return jsonify({'success': False, 'error': 'Admin or assigned PIC required to finalize job.'}), 403

        # Finalize job
        job.status = 'completed'
        job.finished_at = datetime.now(jakarta_tz)

        # Mark any lingering in_progress assignments as completed for consistency
        for pa in all_assignments:
            if pa.status != 'completed':
                pa.status = 'completed'
                pa.finished_at = datetime.now(jakarta_tz)

        db.session.commit()
        
        # Send notification for job completion
        send_rnd_job_completed_notification(job)

        # Refresh and return
        db.session.refresh(job)
        return jsonify({
            'success': True,
            'message': 'Job finalized successfully',
            'data': {
                'job_status': job.status,
                'job_finished_at': job.finished_at.isoformat() if job.finished_at else None
            }
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500


def send_rnd_job_completed_notification(job):
    """Helper function to send RND job completed notification - only once per job"""
    try:
        if job.status == 'completed' and job.finished_at:
            # Check if we already sent a completion notification for this job to avoid duplicates
            from services.notification_service import NotificationService
            existing_notification = UniversalNotification.query.filter_by(
                notification_type='rnd_job_completed',
                related_resource_id=job.id
            ).first()
            
            # Only send if no previous notification exists
            if not existing_notification:
                NotificationDispatcher.dispatch_rnd_job_completed(
                    job_db_id=job.id,
                    job_id=job.job_id,
                    item_name=job.item_name,
                    sample_type=job.sample_type,
                    triggered_by_user_id=current_user.id
                )
                print(f"DEBUG: Sent job completion notification for job {job.id}")
            else:
                print(f"DEBUG: Job completion notification already sent for job {job.id}, skipping duplicate")
    except Exception as e:
        logger.error(f"Failed to send RND job completed notification: {str(e)}", exc_info=True)


@rnd_cloudsphere_bp.route('/api/jobs/export/excel')
@login_required
@require_rnd_access
def export_rnd_jobs_excel():
    """Export RND jobs to Excel format with comprehensive data"""
    try:
        # Parse filters from request
        filters = {}
        
        # Date range filters
        start_date_str = request.args.get('start_date')
        end_date_str = request.args.get('end_date')
        
        if start_date_str:
            try:
                # Parse date string (expecting YYYY-MM-DD format)
                start_date = datetime.strptime(start_date_str, '%Y-%m-%d')
                # Convert to Jakarta timezone
                if start_date.tzinfo is None:
                    start_date = jakarta_tz.localize(start_date)
                filters['start_date'] = start_date
            except ValueError:
                return jsonify({'success': False, 'error': 'Invalid start date format. Use YYYY-MM-DD'}), 400
        
        if end_date_str:
            try:
                # Parse date string (expecting YYYY-MM-DD format)
                end_date = datetime.strptime(end_date_str, '%Y-%m-%d')
                # Add one day to make it inclusive
                end_date = end_date.replace(hour=23, minute=59, second=59)
                # Convert to Jakarta timezone
                if end_date.tzinfo is None:
                    end_date = jakarta_tz.localize(end_date)
                filters['end_date'] = end_date
            except ValueError:
                return jsonify({'success': False, 'error': 'Invalid end date format. Use YYYY-MM-DD'}), 400
        
        # Other filters
        sample_type = request.args.get('sample_type', '').strip()
        if sample_type:
            filters['sample_type'] = sample_type
        
        status = request.args.get('status', '').strip()
        if status:
            filters['status'] = status
        
        # Generate Excel file
        from services.rnd_excel_export_service import RNDExcelExportService
        export_service = RNDExcelExportService(db.session, jakarta_tz)
        
        excel_buffer = export_service.export_jobs_to_excel(filters)
        filename = export_service.generate_filename()
        
        # Return file as download
        return send_file(
            excel_buffer,
            as_attachment=True,
            download_name=filename,
            mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
        
    except ValueError as ve:
        if "No jobs found" in str(ve):
            return jsonify({
                'success': False,
                'error': 'No data found matching the selected filters'
            }), 404
        else:
            current_app.logger.error(f"Error exporting Excel: {str(ve)}")
            return jsonify({
                'success': False,
                'error': f'Error exporting Excel file: {str(ve)}'
            }), 400
    except Exception as e:
        current_app.logger.error(f"Error exporting Excel: {str(e)}")
        return jsonify({
            'success': False,
            'error': f'Error exporting Excel file: {str(e)}'
        }), 500
