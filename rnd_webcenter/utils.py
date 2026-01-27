import os
import re
from datetime import datetime

def sanitize_path(path):
    """
    Sanitize path to prevent directory traversal attacks
    
    Args:
        path (str): Input path to sanitize
        
    Returns:
        str: Sanitized path
    """
    if not path:
        return ""
    
    # Remove any null bytes
    path = path.replace('\x00', '')
    
    # Normalize path separators
    path = path.replace('/', '\\')
    
    # Remove any relative path components that could lead to directory traversal
    path_parts = path.split('\\')
    sanitized_parts = []
    
    for part in path_parts:
        if part == '..':
            # Skip parent directory references
            continue
        elif part == '.':
            # Skip current directory references
            continue
        elif part:
            sanitized_parts.append(part)
    
    return '\\'.join(sanitized_parts)

def get_file_icon(filename):
    """
    Get appropriate icon class based on file extension
    
    Args:
        filename (str): Name of the file
        
    Returns:
        str: Bootstrap icon class name
    """
    if not filename:
        return 'bi-file-earmark'
    
    # Get file extension
    _, ext = os.path.splitext(filename.lower())
    
    # Icon mapping for different file types
    icon_map = {
        # Documents
        '.pdf': 'bi-file-earmark-pdf',
        '.doc': 'bi-file-earmark-word',
        '.docx': 'bi-file-earmark-word',
        '.xls': 'bi-file-earmark-excel',
        '.xlsx': 'bi-file-earmark-excel',
        '.ppt': 'bi-file-earmark-ppt',
        '.pptx': 'bi-file-earmark-ppt',
        '.txt': 'bi-file-earmark-text',
        '.rtf': 'bi-file-earmark-text',
        
        # Images
        '.jpg': 'bi-file-earmark-image',
        '.jpeg': 'bi-file-earmark-image',
        '.png': 'bi-file-earmark-image',
        '.gif': 'bi-file-earmark-image',
        '.bmp': 'bi-file-earmark-image',
        '.svg': 'bi-file-earmark-image',
        '.tiff': 'bi-file-earmark-image',
        '.psd': 'bi-file-earmark-image',
        
        # Archives
        '.zip': 'bi-file-earmark-zip',
        '.rar': 'bi-file-earmark-zip',
        '.7z': 'bi-file-earmark-zip',
        '.tar': 'bi-file-earmark-zip',
        '.gz': 'bi-file-earmark-zip',
        
        # Audio/Video
        '.mp3': 'bi-file-earmark-music',
        '.wav': 'bi-file-earmark-music',
        '.flac': 'bi-file-earmark-music',
        '.mp4': 'bi-file-earmark-play',
        '.avi': 'bi-file-earmark-play',
        '.mkv': 'bi-file-earmark-play',
        '.mov': 'bi-file-earmark-play',
        
        # Code
        '.py': 'bi-file-earmark-code',
        '.js': 'bi-file-earmark-code',
        '.html': 'bi-file-earmark-code',
        '.css': 'bi-file-earmark-code',
        '.php': 'bi-file-earmark-code',
        '.java': 'bi-file-earmark-code',
        '.cpp': 'bi-file-earmark-code',
        '.c': 'bi-file-earmark-code',
        
        # Design/Print
        '.ai': 'bi-file-earmark-image',
        '.eps': 'bi-file-earmark-image',
        '.indd': 'bi-file-earmark-image',
        '.psd': 'bi-file-earmark-image',
        '.cdr': 'bi-file-earmark-image',
        
        # Default
        'default': 'bi-file-earmark'
    }
    
    return icon_map.get(ext, icon_map['default'])

def format_file_size(size_bytes):
    """
    Format file size in human-readable format
    
    Args:
        size_bytes (int): Size in bytes
        
    Returns:
        str: Formatted size string
    """
    if size_bytes is None:
        return "Unknown"
    
    if size_bytes == 0:
        return "0 Bytes"
    
    size_names = ["Bytes", "KB", "MB", "GB", "TB"]
    i = 0
    size = float(size_bytes)
    
    while size >= 1024.0 and i < len(size_names) - 1:
        size /= 1024.0
        i += 1
    
    return f"{size:.1f} {size_names[i]}"

def format_datetime(dt):
    """
    Format datetime for display
    
    Args:
        dt (datetime): Datetime object
        
    Returns:
        str: Formatted datetime string
    """
    if not dt:
        return "Unknown"
    
    if isinstance(dt, str):
        try:
            dt = datetime.fromisoformat(dt)
        except ValueError:
            return dt
    
    return dt.strftime("%Y-%m-%d %H:%M:%S")

def is_valid_filename(filename):
    """
    Check if filename is valid
    
    Args:
        filename (str): Filename to check
        
    Returns:
        bool: True if valid, False otherwise
    """
    if not filename:
        return False
    
    # Check for invalid characters
    invalid_chars = ['<', '>', ':', '"', '|', '?', '*']
    for char in invalid_chars:
        if char in filename:
            return False
    
    # Check for reserved names (Windows)
    reserved_names = [
        'CON', 'PRN', 'AUX', 'NUL',
        'COM1', 'COM2', 'COM3', 'COM4', 'COM5', 'COM6', 'COM7', 'COM8', 'COM9',
        'LPT1', 'LPT2', 'LPT3', 'LPT4', 'LPT5', 'LPT6', 'LPT7', 'LPT8', 'LPT9'
    ]
    
    name_without_ext = os.path.splitext(filename)[0].upper()
    if name_without_ext in reserved_names:
        return False
    
    return True

def get_file_type_category(filename):
    """
    Get the category of file type for grouping/sorting
    
    Args:
        filename (str): Name of the file
        
    Returns:
        str: Category name
    """
    if not filename:
        return 'unknown'
    
    _, ext = os.path.splitext(filename.lower())
    
    # Category mapping
    category_map = {
        # Documents
        '.pdf': 'document',
        '.doc': 'document',
        '.docx': 'document',
        '.xls': 'document',
        '.xlsx': 'document',
        '.ppt': 'document',
        '.pptx': 'document',
        '.txt': 'document',
        '.rtf': 'document',
        
        # Images
        '.jpg': 'image',
        '.jpeg': 'image',
        '.png': 'image',
        '.gif': 'image',
        '.bmp': 'image',
        '.svg': 'image',
        '.tiff': 'image',
        '.psd': 'image',
        '.ai': 'image',
        '.eps': 'image',
        '.indd': 'image',
        '.cdr': 'image',
        
        # Archives
        '.zip': 'archive',
        '.rar': 'archive',
        '.7z': 'archive',
        '.tar': 'archive',
        '.gz': 'archive',
        
        # Audio/Video
        '.mp3': 'media',
        '.wav': 'media',
        '.flac': 'media',
        '.mp4': 'media',
        '.avi': 'media',
        '.mkv': 'media',
        '.mov': 'media',
        
        # Code
        '.py': 'code',
        '.js': 'code',
        '.html': 'code',
        '.css': 'code',
        '.php': 'code',
        '.java': 'code',
        '.cpp': 'code',
        '.c': 'code',
    }
    
    return category_map.get(ext, 'other')

def highlight_search_term(text, search_term):
    """
    Highlight search term in text
    
    Args:
        text (str): Text to highlight
        search_term (str): Term to highlight
        
    Returns:
        str: Text with highlighted term
    """
    if not text or not search_term:
        return text
    
    # Escape HTML special characters
    import html
    escaped_text = html.escape(text)
    
    # Create regex pattern for case-insensitive search
    pattern = re.compile(re.escape(search_term), re.IGNORECASE)
    
    # Replace with highlighted version
    highlighted = pattern.sub(lambda match: f'<mark>{match.group()}</mark>', escaped_text)
    
    return highlighted