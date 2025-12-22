# Standard library imports
from datetime import datetime, time, timedelta
from functools import wraps
from io import BytesIO, StringIO
from urllib.parse import quote_plus
import calendar
import csv
import io
import locale
import logging
import os
import pytz
import random
import traceback

# Third party imports
from flask import Blueprint, abort, current_app, flash, jsonify, make_response, redirect, render_template, request, send_file, send_from_directory, session, url_for
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy
from openpyxl import Workbook
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
from openpyxl.utils import get_column_letter
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, landscape, letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle
from sqlalchemy import String, and_, cast, extract, func, literal_column, or_, text
from werkzeug.middleware.proxy_fix import ProxyFix
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
import openpyxl
import pymysql

# Local imports
from config import DB_CONFIG
from models import db, Division, User, CTPProductionLog, PlateAdjustmentRequest, PlateBonRequest, KartuStockPlateFuji, KartuStockPlateSaphira, KartuStockChemicalFuji, KartuStockChemicalSaphira, MonthlyWorkHours, ChemicalBonCTP, BonPlate, CTPMachine, CTPProblemLog, CTPProblemPhoto, CTPProblemDocument, CTPNotification
from plate_mappings import PlateTypeMapping

# Timezone untuk Jakarta
jakarta_tz = pytz.timezone('Asia/Jakarta')
now_jakarta = datetime.now(jakarta_tz)

# Helper function to format datetime in Indonesian
def format_datetime_indonesia(dt):
    """Format datetime to Indonesian format"""
    if not dt:
        return ''
    
    bulan_indonesia = [
        'Januari', 'Februari', 'Maret', 'April', 'Mei', 'Juni',
        'Juli', 'Agustus', 'September', 'Oktober', 'November', 'Desember'
    ]
    
    day = dt.day
    month = bulan_indonesia[dt.month - 1]
    year = dt.year
    hour = str(dt.hour).zfill(2)
    minute = str(dt.minute).zfill(2)
    
    return f"{day} {month} {year} - {hour}:{minute}"

def format_tanggal_indonesia(dt):
    """Format date to Indonesian format"""
    if not dt:
        return ''
    
    bulan_indonesia = [
        'Januari', 'Februari', 'Maret', 'April', 'Mei', 'Juni',
        'Juli', 'Agustus', 'September', 'Oktober', 'November', 'Desember'
    ]
    
    day = dt.day
    month = bulan_indonesia[dt.month - 1]
    year = dt.year
    
    return f"{day} {month} {year}"

# --- Export Routes ---

# Create Blueprint for export routes
ctp_log_bp = Blueprint('ctp_log', __name__)

# Create logger for debugging
logger = logging.getLogger(__name__)

@ctp_log_bp.route('/api/ctp-problem-logs', methods=['GET'])
@login_required
def get_ctp_problem_logs():
    try:
        machine_id = request.args.get('machine_id')
        machine_nickname = request.args.get('machine_nickname')
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        status = request.args.get('status')
        limit = request.args.get('limit', type=int)
        
        # NEW: Support for additional filter parameters
        technician_type = request.args.get('technician_type')
        year = request.args.get('year', type=int)
        month = request.args.get('month', type=int)
        search = request.args.get('search', '').strip()
        
        # DEBUG: Add logging to track parameters
        logger.info(f"DEBUG: get_ctp_problem_logs called with params: machine_id={machine_id}, machine_nickname={machine_nickname}")
        
        # Join with User table to get user names - be explicit about the join to avoid ambiguity
        query = CTPProblemLog.query.options(db.joinedload(CTPProblemLog.creator))
        logger.info("DEBUG: Successfully created join with User table")
        
        if machine_id:
            query = query.filter_by(machine_id=machine_id)
            logger.info(f"DEBUG: Filtered by machine_id={machine_id}")
        elif machine_nickname:
            logger.info(f"DEBUG: Processing machine_nickname={machine_nickname}")
            machine = CTPMachine.query.filter_by(nickname=machine_nickname).first()
            if machine:
                logger.info(f"DEBUG: Found machine {machine.name} with id={machine.id}")
                query = query.filter_by(machine_id=machine.id)
                logger.info("DEBUG: Successfully applied machine filter")
            else:
                logger.warning(f"DEBUG: Machine with nickname '{machine_nickname}' not found")
        
        # NEW: Filter by technician type (vendor filter)
        if technician_type:
            query = query.filter_by(technician_type=technician_type)
        
        # NEW: Filter by year
        if year:
            query = query.filter(db.extract('year', CTPProblemLog.problem_date) == year)
        
        # NEW: Filter by month
        if month:
            query = query.filter(db.extract('month', CTPProblemLog.problem_date) == month)
        
        # NEW: Search functionality
        if search:
            search_pattern = f'%{search}%'
            logger.info(f"DEBUG: Applying search filter with pattern: {search_pattern}")
            query = query.filter(
                db.or_(
                    CTPProblemLog.problem_description.ilike(search_pattern),
                    CTPProblemLog.solution.ilike(search_pattern),
                    CTPProblemLog.technician_name.ilike(search_pattern)
                )
            )
            logger.info("DEBUG: Successfully applied search filter")
        
        if start_date:
            query = query.filter(CTPProblemLog.problem_date >= start_date)
        if end_date:
            query = query.filter(CTPProblemLog.problem_date <= end_date)
        if status:
            query = query.filter_by(status=status)
        
        query = query.order_by(CTPProblemLog.created_at.desc())
        logger.info("DEBUG: Applied ordering")
        
        if limit:
            query = query.limit(limit)
            logger.info(f"DEBUG: Applied limit={limit}")
        
        logger.info("DEBUG: About to execute query...")
        logs = query.all()
        logger.info(f"DEBUG: Query executed successfully, returned {len(logs)} logs")
        
        return jsonify({
            'success': True,
            'data': [{
                'id': log.id,
                'machine_id': log.machine_id,
                'machine_name': log.machine.name,
                'problem_date': log.problem_date.isoformat(),
                'problem_description': log.problem_description,
                'problem_photo': log.problem_photo,
                'solution': log.solution,
                'technician_type': log.technician_type,
                'technician_name': log.technician_name,
                'start_time': log.start_time.isoformat(),
                'end_time': log.end_time.isoformat() if log.end_time else None,
                'status': log.status,
                'downtime_hours': log.downtime_hours,
                'created_by': log.created_by,
                'created_by_name': log.creator.name if log.creator else 'Unknown',
                'created_at': log.created_at.isoformat(),
                'photos': [{
                    'id': photo.id,
                    'filename': photo.filename,
                    'file_path': photo.file_path,
                    'url': url_for('serve_uploaded_file', filename=photo.file_path, _external=True)
                } for photo in log.photos],
                'documents': [{
                    'id': doc.id,
                    'filename': doc.filename,
                    'file_path': doc.file_path,
                    'file_type': doc.file_type,
                    'url': url_for('serve_uploaded_file', filename=doc.file_path, _external=True)
                } for doc in log.documents]
            } for log in logs]
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@ctp_log_bp.route('/api/ctp-problem-logs', methods=['POST'])
@login_required
def create_ctp_problem_log():
    if not (current_user.can_access_ctp() or current_user.role == 'admin'):
        return jsonify({'success': False, 'error': 'Unauthorized'}), 403
    
    try:
        # Handle form data
        machine_id_raw = request.form.get('machine_id')
        error_code = request.form.get('error_code')
        problem_description = request.form.get('problem_description')
        technician_type = request.form.get('technician_type')
        technician_name = request.form.get('technician_name')
        solution = request.form.get('solution')
        start_time = request.form.get('start_time')
        end_time = request.form.get('end_time')

        # Normalize and validate machine_id
        try:
            machine_id = int(machine_id_raw) if machine_id_raw is not None else None
        except ValueError:
            machine_id = None

        if machine_id is None:
            logger.error(f"create_ctp_problem_log: invalid machine_id_raw={machine_id_raw!r}")
            return jsonify({'success': False, 'error': 'machine_id is required and must be an integer'}), 400

        machine = CTPMachine.query.get(machine_id)
        if not machine:
            logger.error(f"create_ctp_problem_log: CTPMachine with id={machine_id} not found")
            return jsonify({'success': False, 'error': f'Machine with id {machine_id} not found'}), 400
        
        # Initialize variables to track uploaded files
        uploaded_photos = []
        uploaded_documents = []
        
        # Handle multiple photo uploads
        if 'problem_photos' in request.files:
            photos = request.files.getlist('problem_photos')
            upload_dir = os.path.join(current_app.instance_path, 'uploads', 'ctp_problems')
            os.makedirs(upload_dir, exist_ok=True)
            
            for i, photo in enumerate(photos):
                if photo and hasattr(photo, 'filename') and photo.filename != '':
                    # Validate file type
                    allowed_extensions = {'png', 'jpg', 'jpeg', 'gif', 'webp'}
                    if not ('.' in photo.filename and
                           photo.filename.rsplit('.', 1)[1].lower() in allowed_extensions):
                        continue
                    
                    filename = secure_filename(f"ctp_problem_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{i+1}_{photo.filename}")
                    file_path = os.path.join(upload_dir, filename)
                    photo.save(file_path)
                    uploaded_photos.append(filename)
                    
                    # (Reserved for future use) photo_data if needed later
                    # photo_data = {
                    #     'filename': photo.filename,
                    #     'file_path': f"ctp_problems/{filename}"
                    # }
        
        # Handle document uploads
        if 'problem_documents' in request.files:
            documents = request.files.getlist('problem_documents')
            upload_dir = os.path.join(current_app.instance_path, 'uploads', 'ctp_documents')
            os.makedirs(upload_dir, exist_ok=True)
            
            for i, doc in enumerate(documents):
                if doc and hasattr(doc, 'filename') and doc.filename != '':
                    # Validate file type
                    allowed_extensions = {'pdf', 'docx', 'zip'}
                    if not ('.' in doc.filename and
                           doc.filename.rsplit('.', 1)[1].lower() in allowed_extensions):
                        continue
                    
                    filename = secure_filename(f"ctp_doc_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{i+1}_{doc.filename}")
                    file_path = os.path.join(upload_dir, filename)
                    
                    # Validate ZIP file size (50MB limit)
                    if doc.filename.lower().endswith('.zip'):
                        if doc.content_length > 50 * 1024 * 1024:
                            return jsonify({'success': False, 'error': 'File ZIP maksimal 50MB'}), 400
                    
                    doc.save(file_path)
                    
                    # Determine file type
                    if doc.filename.lower().endswith('.pdf'):
                        file_type = 'pdf'
                    elif doc.filename.lower().endswith('.docx'):
                        file_type = 'docx'
                    elif doc.filename.lower().endswith('.zip'):
                        file_type = 'zip'
                    else:
                        file_type = 'docx'  # fallback
                    
                    # Store both filename and file_type for later database save
                    uploaded_documents.append({
                        'filename': filename,
                        'original_filename': doc.filename,
                        'file_type': file_type
                    })
        
        # Convert Jakarta time from frontend to proper datetime
        start_time_jakarta = datetime.fromisoformat(start_time)
        end_time_jakarta = datetime.fromisoformat(end_time) if end_time else None
        
        # Create new problem log
        log = CTPProblemLog(
            machine_id=machine_id,
            error_code=error_code,
            problem_description=problem_description,
            technician_type=technician_type,
            technician_name=technician_name,
            # Ensure the datetime is treated as Jakarta time
            start_time=start_time_jakarta,
            end_time=end_time_jakarta,
            status='completed' if end_time else 'ongoing',
            solution=solution,
            created_by=current_user.id
        )
        
        db.session.add(log)
        db.session.flush()  # ensure log.id is available before creating notification
        
        # Create notification using validated machine object
        notification = CTPNotification(
            machine_id=machine_id,
            log_id=log.id,
            notification_type='new_problem',
            message=f"Problem baru pada {machine.name}: {problem_description[:50]}..."
        )
        db.session.add(notification)
        
        # Save uploaded photos to database
        if uploaded_photos:
            for filename in uploaded_photos:
                # Save to database
                problem_photo = CTPProblemPhoto(
                    problem_log_id=log.id,
                    filename=filename,  # Use the generated filename
                    file_path=f"uploads/ctp_problems/{filename}"
                )
                db.session.add(problem_photo)
                logger.info(f"Added photo: {filename} for log ID: {log.id}")
        
        # Save uploaded documents to database
        if uploaded_documents:
            for doc_info in uploaded_documents:
                # Save to database
                problem_doc = CTPProblemDocument(
                    problem_log_id=log.id,
                    filename=doc_info['original_filename'],
                    file_path=f"uploads/ctp_documents/{doc_info['filename']}",
                    file_type=doc_info['file_type']
                )
                db.session.add(problem_doc)
                logger.info(f"Added document: {doc_info['filename']} for log ID: {log.id}")

        # Final commit for all related data
        db.session.commit()
        
        # Log successful creation for debugging
        logger.info(
            f"Created CTP problem log {log.id} for machine_id={machine_id} "
            f"({machine.name}) with {len(uploaded_photos)} photos and {len(uploaded_documents)} documents"
        )
        
        return jsonify({
            'success': True,
            'data': {
                'id': log.id,
                'uploaded_photos': len(uploaded_photos),
                'uploaded_documents': len(uploaded_documents)
            }
        })
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error creating CTP problem log: {str(e)}", exc_info=True)
        return jsonify({'success': False, 'error': str(e)}), 500

@ctp_log_bp.route('/api/ctp-problem-logs/<int:log_id>', methods=['GET'])
@login_required
def get_ctp_problem_log(log_id):
    if not (current_user.can_access_ctp() or current_user.role == 'admin'):
        return jsonify({'success': False, 'error': 'Unauthorized'}), 403
    
    try:
        log = CTPProblemLog.query.get_or_404(log_id)
        return jsonify({
            'success': True,
            'data': {
                'id': log.id,
                'machine_id': log.machine_id,
                'problem_date': log.problem_date.isoformat() if log.problem_date else None,
                'error_code': log.error_code,
                'problem_description': log.problem_description,
                'solution': log.solution,
                'technician_type': log.technician_type,
                'technician_name': log.technician_name,
                'start_time': log.start_time.isoformat() if log.start_time else None,
                'end_time': log.end_time.isoformat() if log.end_time else None,
                'status': log.status,
                'downtime_hours': log.downtime_hours,
                'problem_photo': log.problem_photo,
                'photos': [{
                    'id': photo.id,
                    'filename': photo.filename,
                    'file_path': photo.file_path,
                    'url': url_for('serve_uploaded_file', filename=photo.file_path, _external=True)
                } for photo in log.photos],
                'documents': [{
                    'id': doc.id,
                    'filename': doc.filename,
                    'file_path': doc.file_path,
                    'file_type': doc.file_type,
                    'url': url_for('serve_uploaded_file', filename=doc.file_path, _external=True)
                } for doc in log.documents]
            }
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@ctp_log_bp.route('/api/ctp-problem-logs/<int:log_id>', methods=['PUT'])
@login_required
def update_ctp_problem_log(log_id):
    if not (current_user.can_access_ctp() or current_user.role == 'admin'):
        return jsonify({'success': False, 'error': 'Unauthorized'}), 403
    
    try:
        log = CTPProblemLog.query.get_or_404(log_id)
        
        # Check if request contains file (FormData) or JSON
        if request.content_type and 'multipart/form-data' in request.content_type:
            # Handle FormData (when photos or documents are being updated)
            data = request.form.to_dict()
            
            # Update fields from FormData
            if 'error_code' in data:
                log.error_code = data['error_code']            
            if 'problem_description' in data:
                log.problem_description = data['problem_description']
            if 'technician_type' in data:
                log.technician_type = data['technician_type']
            if 'technician_name' in data:
                log.technician_name = data['technician_name']
            if 'solution' in data:
                log.solution = data['solution']
            if 'start_time' in data:
                # Convert Jakarta time from frontend to proper datetime
                start_time_jakarta = datetime.fromisoformat(data['start_time'])
                log.problem_date = start_time_jakarta
            
            # Handle multiple photo uploads if present
            if 'problem_photos' in request.files:
                photos = request.files.getlist('problem_photos')
                upload_dir = os.path.join(current_app.instance_path, 'uploads', 'ctp_problems')
                os.makedirs(upload_dir, exist_ok=True)
                
                for i, photo in enumerate(photos):
                    if photo and hasattr(photo, 'filename') and photo.filename != '':
                        # Validate file type
                        allowed_extensions = {'png', 'jpg', 'jpeg', 'gif', 'webp'}
                        if not ('.' in photo.filename and
                               photo.filename.rsplit('.', 1)[1].lower() in allowed_extensions):
                            continue
                        
                        filename = secure_filename(f"ctp_problem_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{i+1}_{photo.filename}")
                        file_path = os.path.join(upload_dir, filename)
                        photo.save(file_path)
                        
                        # Save to database
                        problem_photo = CTPProblemPhoto(
                            problem_log_id=log.id,
                            filename=photo.filename,
                            file_path=f"uploads/ctp_problems/{filename}"
                        )
                        db.session.add(problem_photo)
                        logger.info(f"Added photo: {filename} for log ID: {log.id}")
            
            # Handle document uploads if present
            if 'problem_documents' in request.files:
                documents = request.files.getlist('problem_documents')
                upload_dir = os.path.join(current_app.instance_path, 'uploads', 'ctp_documents')
                os.makedirs(upload_dir, exist_ok=True)
                
                for i, doc in enumerate(documents):
                    if doc and hasattr(doc, 'filename') and doc.filename != '':
                        # Validate file type
                        allowed_extensions = {'pdf', 'docx', 'zip'}
                        allowed_mime_types = {'application/pdf', 'application/vnd.openxmlformats-officedocument.wordprocessingml.document', 'application/zip', 'application/x-zip-compressed'}
                        
                        if not ('.' in doc.filename and
                               doc.filename.rsplit('.', 1)[1].lower() in allowed_extensions):
                            continue
                        
                        # Additional MIME type validation for ZIP files
                        if doc.filename.lower().endswith('.zip'):
                            if not (hasattr(doc, 'content_type') and doc.content_type in allowed_mime_types):
                                continue
                        
                        filename = secure_filename(f"ctp_doc_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{i+1}_{doc.filename}")
                        file_path = os.path.join(upload_dir, filename)
                        
                        # Validate ZIP file size (50MB limit)
                        if doc.filename.lower().endswith('.zip'):
                            if doc.content_length > 50 * 1024 * 1024:
                                return jsonify({'success': False, 'error': 'File ZIP maksimal 50MB'}), 400
                        
                        doc.save(file_path)
                        
                        # Determine file type
                        if doc.filename.lower().endswith('.pdf'):
                            file_type = 'pdf'
                        elif doc.filename.lower().endswith('.docx'):
                            file_type = 'docx'
                        elif doc.filename.lower().endswith('.zip'):
                            file_type = 'zip'
                        else:
                            file_type = 'docx'  # fallback
                        
                        # Save to database
                        problem_doc = CTPProblemDocument(
                            problem_log_id=log.id,
                            filename=doc.filename,
                            file_path=f"uploads/ctp_documents/{filename}",
                            file_type=file_type
                        )
                        db.session.add(problem_doc)
                        logger.info(f"Added document: {filename} for log ID: {log.id}")
            
            # Handle legacy single photo upload if present
            if 'problem_photo' in request.files:
                photo_file = request.files['problem_photo']
                if photo_file and hasattr(photo_file, 'filename') and photo_file.filename:
                    # Generate unique filename
                    filename = f"ctp_problem_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{photo_file.filename}"
                    photo_path = os.path.join('instance/uploads/ctp_problems', filename)
                    
                    # Ensure directory exists
                    os.makedirs(os.path.dirname(photo_path), exist_ok=True)
                    
                    # Save file
                    photo_file.save(photo_path)
                    
                    # Update log with new photo path (without 'uploads/' prefix for frontend compatibility)
                    # Make sure log is committed to database before accessing its attributes
                    db.session.commit()
                    log.problem_photo = f"uploads/ctp_problems/{filename}"
        else:
            # Handle JSON request (when no photo is being updated)
            data = request.get_json()

            # Update fields from JSON
            if 'error_code' in data:
                log.error_code = data['error_code']             
            if 'problem_description' in data:
                log.problem_description = data['problem_description']
            if 'technician_type' in data:
                log.technician_type = data['technician_type']
            if 'technician_name' in data:
                log.technician_name = data['technician_name']
            if 'solution' in data:
                log.solution = data['solution']
            if 'start_time' in data:
                # Convert Jakarta time from frontend to proper datetime
                start_time_jakarta = datetime.fromisoformat(data['start_time'])
                log.problem_date = start_time_jakarta
        
        # Handle end_time and status completion (for both FormData and JSON)
        if ((request.content_type and 'multipart/form-data' in request.content_type and 'end_time' in request.form) or
            (not request.content_type or 'multipart/form-data' not in request.content_type and 'end_time' in data)):
            
            end_time_value = request.form.get('end_time') if request.content_type and 'multipart/form-data' in request.content_type else data.get('end_time')
            
            if end_time_value:
                # Convert Jakarta time from frontend to proper datetime
                end_time_jakarta = datetime.fromisoformat(end_time_value)
                log.end_time = end_time_jakarta
                log.status = 'completed'

                # Create notification for completed problem
                notification = CTPNotification(
                    machine_id=log.machine_id,
                    log_id=log.id,
                    notification_type='problem_resolved',
                    message=f"Problem pada {log.machine.name} telah selesai"
                )
                db.session.add(notification)

        db.session.commit()
        
        return jsonify({'success': True})
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error updating CTP problem log: {str(e)}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        return jsonify({'success': False, 'error': str(e)}), 500

@ctp_log_bp.route('/api/ctp-problem-logs/<int:log_id>', methods=['DELETE'])
@login_required
def delete_ctp_problem_log(log_id):
    if not (current_user.can_access_ctp() or current_user.role == 'admin'):
        return jsonify({'success': False, 'error': 'Unauthorized'}), 403
    
    try:
        log = CTPProblemLog.query.get_or_404(log_id)
        db.session.delete(log)
        db.session.commit()
        
        return jsonify({'success': True})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500

@ctp_log_bp.route('/api/ctp-problem-photos/<int:photo_id>', methods=['DELETE'])
@login_required
def delete_ctp_problem_photo(photo_id):
    if not (current_user.can_access_ctp() or current_user.role == 'admin'):
        return jsonify({'success': False, 'error': 'Unauthorized'}), 403
    
    try:
        photo = CTPProblemPhoto.query.get_or_404(photo_id)
        
        # Delete physical file if exists
        if photo.file_path:
            file_full_path = os.path.join(current_app.instance_path, photo.file_path)
            if os.path.exists(file_full_path):
                try:
                    os.remove(file_full_path)
                    logger.info(f"Deleted physical file: {file_full_path}")
                except Exception as e:
                    logger.warning(f"Failed to delete physical file {file_full_path}: {str(e)}")
        
        # Delete database record
        db.session.delete(photo)
        db.session.commit()
        
        logger.info(f"Deleted CTPProblemPhoto with id={photo_id}")
        return jsonify({'success': True})
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error deleting CTP problem photo: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

@ctp_log_bp.route('/api/ctp-problem-documents/<int:document_id>', methods=['DELETE'])
@login_required
def delete_ctp_problem_document(document_id):
    if not (current_user.can_access_ctp() or current_user.role == 'admin'):
        return jsonify({'success': False, 'error': 'Unauthorized'}), 403
    
    try:
        document = CTPProblemDocument.query.get_or_404(document_id)
        
        # Delete physical file if exists
        if document.file_path:
            file_full_path = os.path.join(current_app.instance_path, document.file_path)
            if os.path.exists(file_full_path):
                try:
                    os.remove(file_full_path)
                    logger.info(f"Deleted physical file: {file_full_path}")
                except Exception as e:
                    logger.warning(f"Failed to delete physical file {file_full_path}: {str(e)}")
        
        # Delete database record
        db.session.delete(document)
        db.session.commit()
        
        logger.info(f"Deleted CTPProblemDocument with id={document_id}")
        return jsonify({'success': True})
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error deleting CTP problem document: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500