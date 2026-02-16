from flask import render_template, request, redirect, url_for, flash, jsonify, send_from_directory
from flask_login import login_required, current_user
from . import tools_module_bp
from .models import Module, ModuleStatus, jakarta_tz
from models import db
from datetime import datetime
from sqlalchemy import or_, and_
import os
import logging
from werkzeug.utils import secure_filename

# Network path for uploads (sama dengan tools_5w1h)
UPLOAD_FOLDER = r'\\172.27.168.10\Data_Design\Impact\module_images'
ALLOWED_EXTENSIONS = {'jpg', 'jpeg', 'png', 'gif', 'webp'}

logger = logging.getLogger(__name__)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def ensure_upload_folder_exists():
    """Ensure upload folder exists, create if needed"""
    try:
        # Cek parent folder dulu
        parent_folder = r'\\172.27.168.10\Data_Design\Impact'
        if not os.path.exists(parent_folder):
            logger.error(f"Parent folder tidak accessible: {parent_folder}")
            return False
        
        # Create module_images folder
        if not os.path.exists(UPLOAD_FOLDER):
            os.makedirs(UPLOAD_FOLDER)
            logger.info(f"Created upload folder: {UPLOAD_FOLDER}")
        
        # Test write permission
        test_file = os.path.join(UPLOAD_FOLDER, '.test')
        with open(test_file, 'w') as f:
            f.write('test')
        os.remove(test_file)
        logger.info(f"Upload folder is writable: {UPLOAD_FOLDER}")
        return True
    except PermissionError as e:
        logger.error(f"Permission denied for upload folder {UPLOAD_FOLDER}: {str(e)}")
        return False
    except Exception as e:
        logger.error(f"Error creating/accessing upload folder {UPLOAD_FOLDER}: {str(e)}")
        return False

def get_filtered_modules(search_query='', category_filter='', status_filter=''):
    """Helper function to get filtered modules (used by both dashboard and API)"""
    # Start with base query
    query = Module.query
    
    # Apply search filters
    if search_query:
        search_filter = or_(
            Module.title.contains(search_query),
            Module.description.contains(search_query),
            Module.content.contains(search_query),
            Module.tags.contains(search_query)
        )
        query = query.filter(search_filter)
    
    if category_filter:
        query = query.filter(Module.category == category_filter)
    
    if status_filter:
        try:
            status_enum = ModuleStatus[status_filter.upper()]
            query = query.filter(Module.status == status_enum)
        except KeyError:
            pass  # Invalid status, ignore filter
    
    # Order by updated_at descending
    modules = query.order_by(Module.updated_at.desc()).all()
    return modules

@tools_module_bp.route('/')
@login_required
def dashboard():
    """Display all modules in a card layout with search functionality"""
    search_query = request.args.get('search', '').strip()
    category_filter = request.args.get('category', '').strip()
    status_filter = request.args.get('status', '').strip()
    
    # Get filtered modules
    modules = get_filtered_modules(search_query, category_filter, status_filter)
    
    # Get unique categories for filter dropdown
    categories = db.session.query(Module.category).distinct().all()
    categories = [cat[0] for cat in categories if cat[0]]
    
    return render_template('tools_module/dashboard_module.html', 
                         modules=modules, 
                         categories=categories,
                         search_query=search_query,
                         category_filter=category_filter,
                         status_filter=status_filter)

@tools_module_bp.route('/get-modules', methods=['GET'])
@login_required
def get_modules():
    """AJAX endpoint to fetch modules without page refresh (pattern from tabelkpictp.html)"""
    search_query = request.args.get('search', '').strip()
    category_filter = request.args.get('category', '').strip()
    status_filter = request.args.get('status', '').strip()
    
    try:
        # Get filtered modules
        modules = get_filtered_modules(search_query, category_filter, status_filter)
        
        # Convert to JSON-serializable format
        modules_data = []
        for module in modules:
            modules_data.append({
                'id': module.id,
                'title': module.title,
                'description': module.description,
                'content': module.content,
                'category': module.category,
                'tags': module.tags,
                'tag_list': module.tag_list,
                'status': module.status.value,  # Get display value (e.g., 'Published')
                'status_name': module.status.name.lower(),  # Get name (e.g., 'draft')
                'author_id': module.author_id,
                'author_name': module.author.name if module.author else '-',
                'updated_at': module.updated_at.strftime('%d %b %Y'),
                'url_view': url_for('tools_module.view_module', module_id=module.id),
                'url_edit': url_for('tools_module.edit_module', module_id=module.id),
                'can_edit': module.author_id == current_user.id or current_user.role == 'admin'
            })
        
        return jsonify({
            'success': True,
            'data': modules_data,
            'count': len(modules_data)
        })
    
    except Exception as e:
        logger.error(f"Error fetching modules: {str(e)}")
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500

@tools_module_bp.route('/create', methods=['GET', 'POST'])
@login_required
def create_module():
    """Create a new module"""
    if request.method == 'POST':
        title = request.form.get('title', '').strip()
        description = request.form.get('description', '').strip()
        content = request.form.get('content', '').strip()
        category = request.form.get('category', 'General').strip()
        tags = request.form.get('tags', '').strip()
        status = request.form.get('status', 'draft').strip()
        
        # Validation
        if not title:
            flash('Title is required!', 'danger')
            return render_template('tools_module/create_module.html')
        
        if not content:
            flash('Content is required!', 'danger')
            return render_template('tools_module/create_module.html')
        
        try:
            # Convert status string to enum
            status_enum = ModuleStatus[status.upper()]
        except KeyError:
            status_enum = ModuleStatus.DRAFT
        
        # Create new module
        module = Module(
            title=title,
            description=description,
            content=content,
            category=category,
            tags=tags,
            status=status_enum,
            author_id=current_user.id,
            published_at=datetime.now(jakarta_tz) if status_enum == ModuleStatus.PUBLISHED else None
        )
        
        db.session.add(module)
        db.session.commit()
        
        flash('Module created successfully!', 'success')
        return redirect(url_for('tools_module.dashboard'))
    
    # Get categories for dropdown
    categories = db.session.query(Module.category).distinct().all()
    categories = [cat[0] for cat in categories if cat[0]]
    
    return render_template('tools_module/create_module.html', categories=categories)

@tools_module_bp.route('/<int:module_id>')
@login_required
def view_module(module_id):
    """View a specific module"""
    module = Module.query.get_or_404(module_id)
    return render_template('tools_module/view_module.html', module=module)

@tools_module_bp.route('/<int:module_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_module(module_id):
    """Edit an existing module"""
    module = Module.query.get_or_404(module_id)
    
    # Check if user can edit (author or admin)
    if module.author_id != current_user.id and current_user.role != 'admin':
        flash('You do not have permission to edit this module!', 'danger')
        return redirect(url_for('tools_module.view_module', module_id=module_id))
    
    if request.method == 'POST':
        title = request.form.get('title', '').strip()
        description = request.form.get('description', '').strip()
        content = request.form.get('content', '').strip()
        category = request.form.get('category', 'General').strip()
        tags = request.form.get('tags', '').strip()
        status = request.form.get('status', 'draft').strip()
        
        # Validation
        if not title:
            flash('Title is required!', 'danger')
            return render_template('tools_module/create_module.html', module=module, edit=True)
        
        if not content:
            flash('Content is required!', 'danger')
            return render_template('tools_module/create_module.html', module=module, edit=True)
        
        try:
            # Convert status string to enum
            status_enum = ModuleStatus[status.upper()]
        except KeyError:
            status_enum = ModuleStatus.DRAFT
        
        # Update module
        module.title = title
        module.description = description
        module.content = content
        module.category = category
        module.tags = tags
        module.status = status_enum
        
        # Set published_at if status changed to published
        if status_enum == ModuleStatus.PUBLISHED and not module.published_at:
            module.published_at = datetime.now(jakarta_tz)
        
        db.session.commit()
        
        flash('Module updated successfully!', 'success')
        return redirect(url_for('tools_module.view_module', module_id=module_id))
    
    # Get categories for dropdown
    categories = db.session.query(Module.category).distinct().all()
    categories = [cat[0] for cat in categories if cat[0]]
    
    return render_template('tools_module/create_module.html', module=module, categories=categories, edit=True)

@tools_module_bp.route('/<int:module_id>/delete', methods=['POST'])
@login_required
def delete_module(module_id):
    """Delete a module"""
    module = Module.query.get_or_404(module_id)
    
    # Check if user can delete (author or admin)
    if module.author_id != current_user.id and current_user.role != 'admin':
        flash('You do not have permission to delete this module!', 'danger')
        return redirect(url_for('tools_module.view_module', module_id=module_id))
    
    db.session.delete(module)
    db.session.commit()
    
    flash('Module deleted successfully!', 'success')
    return redirect(url_for('tools_module.dashboard'))

@tools_module_bp.route('/upload-image', methods=['POST'])
@login_required
def upload_image():
    """Handle CKEditor image upload"""
    logger.info("=== IMAGE UPLOAD START ===")
    logger.info(f"Request method: {request.method}")
    logger.info(f"Files in request: {list(request.files.keys())}")
    
    try:
        if 'upload' not in request.files:
            logger.error("No 'upload' field in request files")
            return jsonify({'error': 'No file part'}), 400
        
        file = request.files['upload']
        logger.info(f"File received: {file.filename}")
        
        if file.filename == '':
            logger.error("Filename is empty")
            return jsonify({'error': 'No selected file'}), 400
        
        # Check file type
        if not allowed_file(file.filename):
            logger.error(f"File type not allowed: {file.filename}")
            return jsonify({'error': 'File type not allowed. Only JPG, PNG, GIF, WebP are allowed'}), 400
        
        logger.info("Starting folder access check...")
        # Ensure upload folder exists
        if not ensure_upload_folder_exists():
            logger.error(f"Upload folder {UPLOAD_FOLDER} not accessible or not writable")
            return jsonify({'error': 'Upload folder not accessible. Check network path and permissions.'}), 500
        
        logger.info("Folder check passed. Creating filename...")
        # Create unique filename
        filename = secure_filename(file.filename)
        timestamp = datetime.utcnow().strftime('%Y%m%d_%H%M%S_')
        filename = timestamp + filename
        filepath = os.path.join(UPLOAD_FOLDER, filename)
        
        logger.info(f"Target filepath: {filepath}")
        
        try:
            # Save file
            logger.info("Saving file...")
            file.save(filepath)
            
            # Verify file was saved
            if os.path.exists(filepath):
                file_size = os.path.getsize(filepath)
                logger.info(f"Image uploaded successfully: {filepath} (Size: {file_size} bytes)")
                
                # Return URL for CKEditor
                image_url = url_for('tools_module.serve_module_image', filename=filename, _external=True)
                logger.info(f"Image URL: {image_url}")
                logger.info("=== IMAGE UPLOAD SUCCESS ===")
                return jsonify({'url': image_url})
            else:
                logger.error(f"File save verification failed: {filepath}")
                return jsonify({'error': 'File save failed - file not found after save'}), 500
        
        except PermissionError as e:
            logger.error(f"Permission denied when saving file: {str(e)}")
            return jsonify({'error': f'Permission denied. Check network path permissions.'}), 500
        except Exception as e:
            logger.error(f"Error saving file: {str(e)}")
            return jsonify({'error': f'Error saving file: {str(e)}'}), 500
    
    except Exception as e:
        logger.error(f"Unexpected upload error: {str(e)}")
        logger.error("=== IMAGE UPLOAD FAILED ===")
        return jsonify({'error': str(e)}), 500

@tools_module_bp.route('/image/<filename>')
def serve_module_image(filename):
    """Serve uploaded module images from network path"""
    try:
        # Security check: prevent directory traversal
        if '..' in filename or '/' in filename or '\\' in filename:
            logger.error(f"Security violation attempt: {filename}")
            return jsonify({'error': 'Invalid filename'}), 400
        
        logger.info(f"Serving image: {filename}")
        return send_from_directory(UPLOAD_FOLDER, filename)
    except Exception as e:
        logger.error(f"Error serving image {filename}: {str(e)}")
        return jsonify({'error': 'File not found'}), 404