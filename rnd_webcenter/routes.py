from flask import render_template, jsonify, request, current_app, session
from flask_login import login_required
from . import rnd_webcenter_bp
from .services import FileExplorerService
from .utils import get_file_icon, format_file_size, sanitize_path
import logging

# Configure logging
logger = logging.getLogger(__name__)

def get_file_explorer_service():
    """Get file explorer service with custom path if available"""
    custom_path = session.get('custom_network_path')
    return FileExplorerService(custom_path)

@rnd_webcenter_bp.route('/')
@login_required
def file_explorer():
    """Main file explorer page"""
    return render_template('rnd_webcenter/file_explorer.html')

@rnd_webcenter_bp.route('/api/directory')
@login_required
def api_directory():
    """API endpoint for directory listing"""
    path = request.args.get('path', '')
    
    # Sanitize path to prevent directory traversal
    sanitized_path = sanitize_path(path)
    
    try:
        logger.info(f"Attempting to access directory: {sanitized_path}")
        service = get_file_explorer_service()
        contents = service.get_directory_contents(sanitized_path)
        logger.info(f"Directory access successful, found {contents.get('files', 0)} files and {contents.get('folders', 0)} folders")
        return jsonify({
            'success': True,
            'data': contents
        })
    except Exception as e:
        logger.error(f"Error accessing directory: {str(e)}")
        service = get_file_explorer_service()
        logger.error(f"Base path: {service.network_service.base_path}")
        logger.error(f"Requested path: {sanitized_path}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@rnd_webcenter_bp.route('/api/search')
@login_required
def api_search():
    """API endpoint for file search"""
    query = request.args.get('q', '').strip()
    path = request.args.get('path', '')
    
    # Sanitize inputs
    sanitized_query = query.strip()
    sanitized_path = sanitize_path(path)
    
    if not sanitized_query:
        return jsonify({
            'success': False,
            'error': 'Search query is required'
        }), 400
    
    try:
        logger.info(f"Searching for '{sanitized_query}' in '{sanitized_path}'")
        service = get_file_explorer_service()
        results = service.search_files(sanitized_query, sanitized_path)
        logger.info(f"Search completed, found {results.get('files', 0)} files and {results.get('folders', 0)} folders")
        return jsonify({
            'success': True,
            'data': results
        })
    except Exception as e:
        logger.error(f"Error searching files: {str(e)}")
        service = get_file_explorer_service()
        logger.error(f"Base path: {service.network_service.base_path}")
        logger.error(f"Search query: {sanitized_query}")
        logger.error(f"Search path: {sanitized_path}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@rnd_webcenter_bp.route('/api/file-info')
@login_required
def api_file_info():
    """API endpoint for detailed file information"""
    path = request.args.get('path', '')
    
    # Sanitize path
    sanitized_path = sanitize_path(path)
    
    if not sanitized_path:
        return jsonify({
            'success': False,
            'error': 'File path is required'
        }), 400
    
    try:
        service = get_file_explorer_service()
        file_info = service.network_service.get_file_info(sanitized_path)
        if file_info:
            return jsonify({
                'success': True,
                'data': file_info
            })
        else:
            return jsonify({
                'success': False,
                'error': 'File not found'
            }), 404
    except Exception as e:
        logger.error(f"Error getting file info: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@rnd_webcenter_bp.route('/api/test-path', methods=['POST'])
@login_required
def api_test_path():
    """API endpoint to test a custom path"""
    from flask import request
    
    data = request.get_json()
    test_path = data.get('path', '')
    
    if not test_path:
        return jsonify({
            'success': False,
            'error': 'Path is required'
        }), 400
    
    try:
        # Create a new service instance with custom path
        from .services import NetworkDriveService
        test_service = NetworkDriveService(custom_path=test_path)
        
        is_accessible = test_service.is_accessible()
        
        return jsonify({
            'success': True,
            'data': {
                'accessible': is_accessible,
                'path': test_path
            }
        })
    except Exception as e:
        logger.error(f"Error testing path: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@rnd_webcenter_bp.route('/api/set-custom-path', methods=['POST'])
@login_required
def api_set_custom_path():
    """API endpoint to set custom network path in session"""
    from flask import request
    
    data = request.get_json()
    custom_path = data.get('path', '')
    
    if not custom_path:
        return jsonify({
            'success': False,
            'error': 'Path is required'
        }), 400
    
    try:
        # Store custom path in session
        session['custom_network_path'] = custom_path
        
        logger.info(f"Custom network path set: {custom_path}")
        
        return jsonify({
            'success': True,
            'data': {
                'path': custom_path
            }
        })
    except Exception as e:
        logger.error(f"Error setting custom path: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@rnd_webcenter_bp.route('/api/accessibility')
@login_required
def api_accessibility():
    """API endpoint to check if network drive is accessible"""
    try:
        logger.info(f"Checking accessibility of network drive")
        service = get_file_explorer_service()
        is_accessible = service.network_service.is_accessible()
        logger.info(f"Network drive accessibility check result: {is_accessible}")
        return jsonify({
            'success': True,
            'data': {
                'accessible': is_accessible,
                'path': service.network_service.base_path
            }
        })
    except Exception as e:
        logger.error(f"Error checking accessibility: {str(e)}")
        service = get_file_explorer_service()
        logger.error(f"Base path: {service.network_service.base_path}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500