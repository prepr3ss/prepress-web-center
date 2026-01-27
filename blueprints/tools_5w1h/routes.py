# Routes for 5W1H
import os
import logging
from flask import render_template, request, redirect, url_for, flash, send_from_directory, abort
from flask_login import login_required, current_user
from . import tools_5w1h_bp
from .models import FiveWOneH, FiveWOneHStatus
from models import db, User
from werkzeug.utils import secure_filename
from datetime import datetime
from sqlalchemy.orm.attributes import flag_modified
from services.notification_service import NotificationDispatcher

UPLOAD_FOLDER = r'\\172.27.168.10\Data_Design\Impact\5w1h'
ALLOWED_EXTENSIONS = {'pdf', 'jpg', 'jpeg', 'png', 'doc', 'docx', 'xls', 'xlsx'}

logger = logging.getLogger(__name__)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def ensure_upload_folder_exists():
    """Ensure upload folder exists, create if needed"""
    try:
        if not os.path.exists(UPLOAD_FOLDER):
            os.makedirs(UPLOAD_FOLDER)
            logger.info(f"Created upload folder: {UPLOAD_FOLDER}")
        return True
    except Exception as e:
        logger.error(f"Error creating upload folder {UPLOAD_FOLDER}: {str(e)}")
        return False

@tools_5w1h_bp.route('/5w1h/new', methods=['GET', 'POST'])
@login_required
def input_5w1h():
    if request.method == 'POST':
        title = request.form['title']
        who = request.form['who']
        what = request.form['what']
        when_ = request.form['when']
        where = request.form['where']
        why = request.form['why']
        how = request.form['how']
        status = request.form.get('status', 'draft')
        files = request.files.getlist('attachments')
        
        # Validate required fields
        if not all([title, who, what, when_, where, why, how]):
            flash('Semua field harus diisi!', 'danger')
            return render_template('tools_5w1h/input_5W1H.html')
        
        # Create entry first
        entry = FiveWOneH(
            title=title,
            who=who,
            what=what,
            when_=datetime.strptime(when_, '%Y-%m-%dT%H:%M'),
            where=where,
            why=why,
            how=how,
            owner_id=current_user.id,
            status=FiveWOneHStatus[status],
            attachments=[]
        )
        db.session.add(entry)
        db.session.commit()
        
        # Handle multiple file uploads
        attachment_count = 0
        if files and files[0].filename:  # Check if files were actually selected
            if not ensure_upload_folder_exists():
                flash('Warning: Tidak bisa mengakses folder lampiran. Entry tetap disimpan.', 'warning')
                logger.warning(f"Upload folder {UPLOAD_FOLDER} not accessible")
            else:
                for file in files:
                    if file and file.filename and allowed_file(file.filename):
                        try:
                            filename = f"{entry.id}_{attachment_count + 1}_{secure_filename(file.filename)}"
                            save_path = os.path.join(UPLOAD_FOLDER, filename)
                            
                            # Save file
                            file.save(save_path)
                            
                            # Verify file was saved
                            if os.path.exists(save_path):
                                entry.attachments.append(filename)
                                flag_modified(entry, 'attachments')  # Mark attachments as modified for SQLAlchemy
                                attachment_count += 1
                                logger.info(f"File saved successfully: {save_path}")
                            else:
                                logger.error(f"File save verification failed: {save_path}")
                        except Exception as e:
                            logger.error(f"File upload error: {str(e)}")
                            flash(f'Error upload file: {str(e)}', 'warning')
        
        db.session.commit()
        
        msg = 'Form 5W1H berhasil disimpan'
        if attachment_count > 0:
            msg += f' ({attachment_count} lampiran)'
        flash(msg, 'success')
        
        # Dispatch notification for new 5W1H entry
        try:
            NotificationDispatcher.dispatch_5w1h_entry_created(
                entry_id=entry.id,
                entry_title=entry.title,
                created_by_user_id=current_user.id,
                created_by_name=current_user.name
            )
        except Exception as e:
            logger.error(f"Error dispatching 5W1H entry created notification: {str(e)}")
        
        # Render form kembali dengan flash message (jangan redirect)
        return render_template('tools_5w1h/input_5W1H.html')
    return render_template('tools_5w1h/input_5W1H.html')

@tools_5w1h_bp.route('/5w1h')
@login_required
def dashboard_5w1h():
    entries = FiveWOneH.query.order_by(FiveWOneH.created_at.desc()).all()
    return render_template('tools_5w1h/dashboard_5W1H.html', entries=entries)

@tools_5w1h_bp.route('/5w1h/<int:entry_id>')
@login_required
def detail_5w1h(entry_id):
    entry = FiveWOneH.query.get_or_404(entry_id)
    can_edit = (entry.owner_id == current_user.id) or (getattr(current_user, 'role', None) == 'admin')
    return render_template('tools_5w1h/detail_5W1H.html', entry=entry, can_edit=can_edit)

@tools_5w1h_bp.route('/5w1h/<int:entry_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_5w1h(entry_id):
    entry = FiveWOneH.query.get_or_404(entry_id)
    if not ((entry.owner_id == current_user.id) or (getattr(current_user, 'role', None) == 'admin')):
        abort(403)
    
    if request.method == 'POST':
        entry.title = request.form['title']
        entry.who = request.form['who']
        entry.what = request.form['what']
        entry.when_ = datetime.strptime(request.form['when'], '%Y-%m-%dT%H:%M')
        entry.where = request.form['where']
        entry.why = request.form['why']
        entry.how = request.form['how']
        
        # Track old status for notification
        old_status = entry.status.name
        entry.status = FiveWOneHStatus[request.form.get('status', 'draft')]
        new_status = entry.status.name
        
        # Handle file deletions
        delete_files_str = request.form.get('delete_files', '[]')
        if delete_files_str and delete_files_str != '[]':
            try:
                import json
                delete_files_list = json.loads(delete_files_str)
                for filename in delete_files_list:
                    if filename in entry.attachments:
                        old_path = os.path.join(UPLOAD_FOLDER, filename)
                        if os.path.exists(old_path):
                            os.remove(old_path)
                            logger.info(f"Attachment deleted: {old_path}")
                        entry.attachments.remove(filename)
                flag_modified(entry, 'attachments')  # Mark as modified for SQLAlchemy
                flash('Lampiran berhasil dihapus.', 'success')
            except Exception as e:
                flash(f'Error menghapus lampiran: {str(e)}', 'warning')
                logger.error(f"Error deleting attachment: {str(e)}")
        
        # Handle new file uploads
        files = request.files.getlist('attachments')
        if files and files[0].filename:
            if not ensure_upload_folder_exists():
                flash('Warning: Tidak bisa mengakses folder lampiran.', 'warning')
                logger.warning(f"Upload folder {UPLOAD_FOLDER} not accessible")
            else:
                for file in files:
                    if file and file.filename and allowed_file(file.filename):
                        try:
                            filename = f"{entry.id}_{len(entry.attachments)+1}_{secure_filename(file.filename)}"
                            save_path = os.path.join(UPLOAD_FOLDER, filename)
                            
                            # Save file
                            file.save(save_path)
                            
                            # Verify file was saved
                            if os.path.exists(save_path):
                                entry.attachments.append(filename)
                                flag_modified(entry, 'attachments')  # Mark as modified for SQLAlchemy
                                logger.info(f"File saved successfully: {save_path}")
                            else:
                                logger.error(f"File save verification failed: {save_path}")
                        except Exception as e:
                            flash(f'Error upload file: {str(e)}', 'warning')
                            logger.error(f"File upload error during edit: {str(e)}")
        
        db.session.commit()
        flash('Form 5W1H berhasil diperbarui', 'success')
        
        # Dispatch notification if status changed
        if old_status != new_status:
            try:
                NotificationDispatcher.dispatch_5w1h_entry_status_changed(
                    entry_id=entry.id,
                    entry_title=entry.title,
                    old_status=old_status,
                    new_status=new_status,
                    updated_by_user_id=current_user.id,
                    updated_by_name=current_user.name
                )
            except Exception as e:
                logger.error(f"Error dispatching 5W1H status changed notification: {str(e)}")
        
        # Return to edit page with flash message instead of redirecting
        return render_template('tools_5w1h/input_5W1H.html', entry=entry, edit=True)
    
    return render_template('tools_5w1h/input_5W1H.html', entry=entry, edit=True)

@tools_5w1h_bp.route('/5w1h/attachment/<filename>')
@login_required
def download_attachment(filename):
    return send_from_directory(UPLOAD_FOLDER, filename, as_attachment=True)
@tools_5w1h_bp.route('/5w1h/<int:entry_id>', methods=['DELETE'])
@login_required
def delete_5w1h(entry_id):
    """Delete a 5W1H entry"""
    entry = FiveWOneH.query.get_or_404(entry_id)
    
    # Check authorization: only owner or admin can delete
    if entry.owner_id != current_user.id and current_user.role != 'admin':
        abort(403)
    
    try:
        # Delete all attached files
        if entry.attachments:
            for filename in entry.attachments:
                try:
                    file_path = os.path.join(UPLOAD_FOLDER, filename)
                    if os.path.exists(file_path):
                        os.remove(file_path)
                        logger.info(f"Deleted attachment: {file_path}")
                except Exception as e:
                    logger.error(f"Error deleting attachment {filename}: {str(e)}")
        
        # Delete entry from database
        db.session.delete(entry)
        db.session.commit()
        logger.info(f"5W1H entry {entry_id} deleted by user {current_user.id}")
        
        return {'status': 'success', 'message': 'Entry deleted successfully'}, 200
    
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error deleting entry {entry_id}: {str(e)}")
        return {'status': 'error', 'message': 'Failed to delete entry'}, 500