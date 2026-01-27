import os
import time
from pathlib import Path
from typing import List, Dict, Optional, Tuple
import logging

# Configure logging
logger = logging.getLogger(__name__)

class NetworkDriveService:
    """Service for accessing network drive files"""
    
    def __init__(self, custom_path: Optional[str] = None):
        self.default_path = r"\\172.27.168.10\Data_Design\PT. Epson\00.DATA BASE EPSON"
        self.base_path = custom_path if custom_path else self.default_path
        self.cache = {}
        self.cache_timeout = 300  # 5 minutes
        
        # Log the path for debugging
        logger.info(f"Network drive path: {self.base_path}")
    
    def update_path(self, custom_path: str):
        """Update the base path to a custom path"""
        self.base_path = custom_path
        self.cache.clear()  # Clear cache when path changes
        logger.info(f"Updated network drive path to: {self.base_path}")
    
    def is_accessible(self) -> bool:
        """Check if network drive is accessible"""
        try:
            # Try to access the network drive with multiple methods
            # First, try to list the directory
            os.listdir(self.base_path)
            logger.info(f"Network drive accessible at {self.base_path}")
            return True
        except (OSError, PermissionError) as e:
            logger.error(f"Network drive not accessible: {str(e)}")
            
            # Try alternative approach - check if path exists
            try:
                if os.path.exists(self.base_path):
                    logger.info(f"Network drive path exists but cannot list: {self.base_path}")
                    return True
                else:
                    logger.error(f"Network drive path does not exist: {self.base_path}")
                    return False
            except Exception as e2:
                logger.error(f"Alternative check failed: {str(e2)}")
                return False
        except Exception as e:
            logger.error(f"Unexpected error checking network drive access: {str(e)}")
            return False
    
    def test_path_access(self, test_path) -> bool:
        """Test if a specific path is accessible"""
        try:
            os.listdir(test_path)
            logger.info(f"Test path accessible: {test_path}")
            return True
        except Exception as e:
            logger.error(f"Test path not accessible: {test_path}, Error: {str(e)}")
            return False
    
    def list_directory(self, relative_path: str = "") -> List[Dict]:
        """List files and directories in specified path"""
        # Check cache first
        cache_key = f"list_{relative_path}"
        current_time = time.time()
        
        if cache_key in self.cache:
            cached_data, cached_time = self.cache[cache_key]
            if current_time - cached_time < self.cache_timeout:
                logger.debug(f"Using cached data for {relative_path}")
                return cached_data
        
        try:
            # Construct full path
            if relative_path:
                full_path = os.path.join(self.base_path, relative_path.replace('/', '\\'))
            else:
                full_path = self.base_path
            
            logger.debug(f"Attempting to list directory: {full_path}")
           
            # List directory contents
            items = []
           
            if os.path.exists(full_path):
                try:
                    for item in os.listdir(full_path):
                        item_path = os.path.join(full_path, item)
                     
                        try:
                            stat_info = os.stat(item_path)
                            is_directory = os.path.isdir(item_path)
                           
                            # Get file extension for icon mapping
                            file_ext = ""
                            if not is_directory:
                                file_ext = Path(item).suffix.lower()
                           
                            # Format file size
                            size_bytes = stat_info.st_size
                            size_formatted = self._format_file_size(size_bytes)
                           
                            # Get modified time
                            modified_time = time.strftime(
                                '%Y-%m-%d %H:%M',
                                time.localtime(stat_info.st_mtime)
                            )
                           
                            # Construct relative path for this item
                            item_relative_path = os.path.join(relative_path, item).replace('\\', '/') if relative_path else item
                           
                            items.append({
                                'name': item,
                                'path': item_relative_path,
                                'isDirectory': is_directory,
                                'size': size_bytes,
                                'sizeFormatted': size_formatted,
                                'modified': modified_time,
                                'extension': file_ext,
                                'type': self._get_file_type(file_ext),
                                'icon': self._get_file_icon(file_ext, is_directory)
                            })
                        except (OSError, PermissionError) as e:
                            logger.warning(f"Error accessing {item_path}: {str(e)}")
                            continue
                except Exception as e:
                    logger.error(f"Unexpected error listing directory {full_path}: {str(e)}")
                    # Return empty list but don't fail completely
                    items = []
            else:
                logger.warning(f"Path does not exist: {full_path}")
                items = []
            
            # Cache the results
            self.cache[cache_key] = (items, current_time)
            
            # Sort items: directories first, then files, both alphabetically
            items.sort(key=lambda x: (not x['isDirectory'], x['name'].lower()))
            
            return items
            
        except Exception as e:
            logger.error(f"Error listing directory {relative_path}: {str(e)}")
            return []
    
    def get_file_info(self, relative_path: str) -> Optional[Dict]:
        """Get detailed file information"""
        try:
            full_path = os.path.join(self.base_path, relative_path.replace('/', '\\'))
            
            if not os.path.exists(full_path):
                return None
                
            stat_info = os.stat(full_path)
            is_directory = os.path.isdir(full_path)
            
            # Get file extension
            file_ext = ""
            if not is_directory:
                file_ext = Path(full_path).suffix.lower()
            
            # Format file size
            size_bytes = stat_info.st_size
            size_formatted = self._format_file_size(size_bytes)
            
            # Get modified time
            modified_time = time.strftime(
                '%Y-%m-%d %H:%M', 
                time.localtime(stat_info.st_mtime)
            )
            
            return {
                'name': os.path.basename(full_path),
                'path': relative_path,
                'isDirectory': is_directory,
                'size': size_bytes,
                'sizeFormatted': size_formatted,
                'modified': modified_time,
                'extension': file_ext,
                'type': self._get_file_type(file_ext),
                'icon': self._get_file_icon(file_ext, is_directory)
            }
            
        except Exception as e:
            logger.error(f"Error getting file info for {relative_path}: {str(e)}")
            return None
    
    def search_files(self, query: str, relative_path: str = "") -> List[Dict]:
        """Search files by name"""
        # Check cache first
        cache_key = f"search_{relative_path}_{query.lower()}"
        current_time = time.time()
        
        if cache_key in self.cache:
            cached_data, cached_time = self.cache[cache_key]
            if current_time - cached_time < self.cache_timeout:
                logger.debug(f"Using cached search results for {query} in {relative_path}")
                return cached_data
        
        try:
            # Construct full path
            if relative_path:
                full_path = os.path.join(self.base_path, relative_path.replace('/', '\\'))
            else:
                full_path = self.base_path
            
            results = []
            query_lower = query.lower()
            
            # Recursive search
            for root, dirs, files in os.walk(full_path):
                # Calculate relative path from base
                rel_root = os.path.relpath(root, self.base_path).replace('\\', '/')
                
                # Search in directories
                for dir_name in dirs:
                    if query_lower in dir_name.lower():
                        dir_relative_path = os.path.join(rel_root, dir_name).replace('\\', '/')
                        dir_info = self.get_file_info(dir_relative_path)
                        if dir_info:
                            results.append(dir_info)
                
                # Search in files
                for file_name in files:
                    if query_lower in file_name.lower():
                        file_relative_path = os.path.join(rel_root, file_name).replace('\\', '/')
                        file_info = self.get_file_info(file_relative_path)
                        if file_info:
                            results.append(file_info)
            
            # Sort results
            results.sort(key=lambda x: (not x['isDirectory'], x['name'].lower()))
            
            # Cache the results
            self.cache[cache_key] = (results, current_time)
            
            return results
            
        except Exception as e:
            logger.error(f"Error searching files in {relative_path}: {str(e)}")
            return []
    
    def _format_file_size(self, size_bytes: int) -> str:
        """Format file size in human readable format"""
        if size_bytes == 0:
            return "0 B"
        
        size_names = ["B", "KB", "MB", "GB", "TB"]
        i = 0
        size = float(size_bytes)
        
        while size >= 1024.0 and i < len(size_names) - 1:
            size /= 1024.0
            i += 1
        
        return f"{size:.1f} {size_names[i]}"
    
    def _get_file_type(self, extension: str) -> str:
        """Get file type category based on extension"""
        if not extension:
            return 'folder'
        
        document_types = ['.pdf', '.doc', '.docx', '.xls', '.xlsx', '.ppt', '.pptx', '.txt']
        image_types = ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.svg', '.webp']
        archive_types = ['.zip', '.rar', '.7z', '.tar', '.gz']
        
        if extension in document_types:
            return 'document'
        elif extension in image_types:
            return 'image'
        elif extension in archive_types:
            return 'archive'
        else:
            return 'other'
    
    def _get_file_icon(self, extension: str, is_directory: bool = False) -> str:
        """Get appropriate Bootstrap icon for file or directory"""
        if is_directory:
            return 'bi-folder-fill'
        
        # Document icons
        if extension == '.pdf':
            return 'bi-file-earmark-pdf-fill text-danger'
        elif extension in ['.doc', '.docx']:
            return 'bi-file-earmark-word-fill text-primary'
        elif extension in ['.xls', '.xlsx']:
            return 'bi-file-earmark-excel-fill text-success'
        elif extension in ['.ppt', '.pptx']:
            return 'bi-file-earmark-slides-fill text-warning'
        elif extension in ['.txt', '.md']:
            return 'bi-file-earmark-text-fill text-secondary'
        
        # Image icons
        elif extension in ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.svg', '.webp']:
            return 'bi-file-earmark-image-fill text-info'
        
        # Archive icons
        elif extension in ['.zip', '.rar', '.7z', '.tar', '.gz']:
            return 'bi-file-earmark-zip-fill text-dark'
        
        # Video icons
        elif extension in ['.mp4', '.avi', '.mkv', '.mov', '.wmv']:
            return 'bi-file-earmark-play-fill text-danger'
        
        # Audio icons
        elif extension in ['.mp3', '.wav', '.flac', '.aac']:
            return 'bi-file-earmark-music-fill text-success'
        
        # Code icons
        elif extension in ['.py', '.js', '.html', '.css', '.php', '.java', '.cpp', '.c']:
            return 'bi-file-earmark-code-fill text-primary'
        
        # Default icon
        else:
            return 'bi-file-earmark-fill text-secondary'


class FileExplorerService:
    """Service for file explorer operations"""
    
    def __init__(self, custom_path: Optional[str] = None):
        self.network_service = NetworkDriveService(custom_path)
    
    def get_directory_contents(self, path: str) -> Dict:
        """Get directory contents with metadata"""
        try:
            items = self.network_service.list_directory(path)
           
            # Calculate directory statistics
            folders = [item for item in items if item['isDirectory']]
            files = [item for item in items if not item['isDirectory']]
           
            total_size = sum(item['size'] for item in files)
           
            return {
                'path': path,
                'items': items,
                'folders': len(folders),
                'files': len(files),
                'totalSize': total_size,
                'totalSizeFormatted': self.network_service._format_file_size(total_size),
                'accessible': self.network_service.is_accessible()
            }
        except Exception as e:
            logger.error(f"Error getting directory contents: {str(e)}")
            logger.error(f"Path attempted: {path}")
            logger.error(f"Base path: {self.network_service.base_path}")
            return {
                'path': path,
                'items': [],
                'folders': 0,
                'files': 0,
                'totalSize': 0,
                'totalSizeFormatted': '0 B',
                'accessible': False,
                'error': str(e)
            }
    
    def navigate_to_path(self, path: str) -> Dict:
        """Navigate to specific path"""
        # Validate path
        if not self._is_valid_path(path):
            logger.warning(f"Invalid path attempted: {path}")
            return {
                'path': '',
                'items': [],
                'folders': 0,
                'files': 0,
                'totalSize': 0,
                'totalSizeFormatted': '0 B',
                'accessible': False,
                'error': 'Invalid path'
            }
        
        return self.get_directory_contents(path)
    
    def search_files(self, query: str, path: str = "") -> Dict:
        """Search files by name"""
        if not query.strip():
            return {
                'path': path,
                'query': query,
                'items': [],
                'folders': 0,
                'files': 0,
                'totalSize': 0,
                'totalSizeFormatted': '0 B',
                'accessible': self.network_service.is_accessible(),
                'error': 'Empty search query'
            }
        
        try:
            items = self.network_service.search_files(query, path)
            
            # Calculate search statistics
            folders = [item for item in items if item['isDirectory']]
            files = [item for item in items if not item['isDirectory']]
            
            return {
                'path': path,
                'query': query,
                'items': items,
                'folders': len(folders),
                'files': len(files),
                'totalSize': sum(item['size'] for item in files),
                'totalSizeFormatted': self.network_service._format_file_size(sum(item['size'] for item in files)),
                'accessible': self.network_service.is_accessible()
            }
        except Exception as e:
            logger.error(f"Error searching files: {str(e)}")
            return {
                'path': path,
                'query': query,
                'items': [],
                'folders': 0,
                'files': 0,
                'totalSize': 0,
                'totalSizeFormatted': '0 B',
                'accessible': False,
                'error': str(e)
            }
    
    def _is_valid_path(self, path: str) -> bool:
        """Validate that path is safe and within allowed directory"""
        # Basic path validation
        if not path:
            return True  # Empty path means root directory
        
        # Check for path traversal attempts
        if '..' in path or path.startswith('~'):
            return False
        
        # Additional validation can be added here
        return True