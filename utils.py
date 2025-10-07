#!/usr/bin/env python3
"""
Utility classes and functions for the Image Converter application.
"""

import os
import mimetypes
from pathlib import Path
from typing import List, Optional, Dict, Any
import logging

class FileHandler:
    """Handles file operations and validations"""
    
    # Image MIME types
    IMAGE_MIME_TYPES = {
        'image/jpeg', 'image/jpg', 'image/png', 'image/gif', 'image/bmp',
        'image/tiff', 'image/webp', 'image/avif', 'image/x-icon'
    }
    
    # Image file extensions
    IMAGE_EXTENSIONS = {
        '.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff', '.tif',
        '.webp', '.avif', '.ico', '.ppm', '.pgm', '.pbm'
    }
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        
    def is_image_file(self, file_path: str) -> bool:
        """
        Check if a file is a valid image file
        
        Args:
            file_path: Path to the file to check
            
        Returns:
            bool: True if the file is an image, False otherwise
        """
        try:
            # Check file extension
            file_ext = Path(file_path).suffix.lower()
            if file_ext not in self.IMAGE_EXTENSIONS:
                return False
                
            # Check MIME type
            mime_type, _ = mimetypes.guess_type(file_path)
            if mime_type and mime_type in self.IMAGE_MIME_TYPES:
                return True
                
            # If MIME type check fails, rely on extension
            return file_ext in self.IMAGE_EXTENSIONS
            
        except Exception as e:
            self.logger.error(f"Error checking if {file_path} is an image: {str(e)}")
            return False
            
    def get_file_size(self, file_path: str) -> Optional[int]:
        """Get the size of a file in bytes"""
        try:
            return os.path.getsize(file_path)
        except Exception as e:
            self.logger.error(f"Error getting file size for {file_path}: {str(e)}")
            return None
            
    def format_file_size(self, size_bytes: int) -> str:
        """Format file size in human-readable format"""
        if size_bytes == 0:
            return "0 B"
            
        size_names = ["B", "KB", "MB", "GB"]
        i = 0
        size = float(size_bytes)
        
        while size >= 1024.0 and i < len(size_names) - 1:
            size /= 1024.0
            i += 1
            
        return f"{size:.1f} {size_names[i]}"
        
    def validate_output_folder(self, folder_path: str) -> bool:
        """Validate if the output folder is writable"""
        try:
            if not os.path.exists(folder_path):
                os.makedirs(folder_path, exist_ok=True)
                
            # Test write permissions
            test_file = os.path.join(folder_path, '.test_write_permissions')
            try:
                with open(test_file, 'w') as f:
                    f.write('test')
                os.remove(test_file)
                return True
            except Exception:
                return False
                
        except Exception as e:
            self.logger.error(f"Error validating output folder {folder_path}: {str(e)}")
            return False
            
    def get_available_space(self, folder_path: str) -> Optional[int]:
        """Get available disk space in bytes for the given folder"""
        try:
            if os.name == 'nt':  # Windows
                import ctypes
                free_bytes = ctypes.c_ulonglong(0)
                ctypes.windll.kernel32.GetDiskFreeSpaceExW(
                    ctypes.c_wchar_p(folder_path),
                    ctypes.pointer(free_bytes),
                    None,
                    None
                )
                return free_bytes.value
            else:  # Unix/Linux/macOS
                statvfs = os.statvfs(folder_path)
                return statvfs.f_frsize * statvfs.f_available
                
        except Exception as e:
            self.logger.error(f"Error getting available space for {folder_path}: {str(e)}")
            return None
            
    def filter_image_files(self, file_paths: List[str]) -> List[str]:
        """Filter a list of file paths to only include valid image files"""
        image_files = []
        for file_path in file_paths:
            if os.path.isfile(file_path) and self.is_image_file(file_path):
                image_files.append(file_path)
        return image_files
        

class ProgressTracker:
    """Tracks conversion progress and statistics"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.reset()
        
    def reset(self):
        """Reset all progress tracking"""
        self.total_files = 0
        self.processed_files = 0
        self.successful_conversions = 0
        self.failed_conversions = 0
        self.current_file = ""
        self.start_time = None
        self.end_time = None
        
    def set_total_files(self, count: int):
        """Set the total number of files to process"""
        self.total_files = count
        
    def start_processing(self):
        """Mark the start of processing"""
        import time
        self.start_time = time.time()
        
    def update_current_file(self, filename: str):
        """Update the currently processing file"""
        self.current_file = filename
        
    def mark_file_processed(self, success: bool = True):
        """Mark a file as processed"""
        self.processed_files += 1
        if success:
            self.successful_conversions += 1
        else:
            self.failed_conversions += 1
            
    def get_progress_percentage(self) -> float:
        """Get the current progress as a percentage"""
        if self.total_files == 0:
            return 0.0
        return (self.processed_files / self.total_files) * 100
        
    def get_estimated_time_remaining(self) -> Optional[float]:
        """Get estimated time remaining in seconds"""
        if not self.start_time or self.processed_files == 0:
            return None
            
        import time
        elapsed_time = time.time() - self.start_time
        avg_time_per_file = elapsed_time / self.processed_files
        remaining_files = self.total_files - self.processed_files
        
        return avg_time_per_file * remaining_files
        
    def finish_processing(self):
        """Mark the end of processing"""
        import time
        self.end_time = time.time()
        
    def get_summary(self) -> Dict[str, Any]:
        """Get a summary of the conversion process"""
        summary = {
            'total_files': self.total_files,
            'processed_files': self.processed_files,
            'successful_conversions': self.successful_conversions,
            'failed_conversions': self.failed_conversions,
            'success_rate': (self.successful_conversions / max(self.total_files, 1)) * 100,
            'current_file': self.current_file,
        }
        
        if self.start_time and self.end_time:
            summary['total_time'] = self.end_time - self.start_time
            summary['avg_time_per_file'] = summary['total_time'] / max(self.processed_files, 1)
        elif self.start_time:
            import time
            summary['elapsed_time'] = time.time() - self.start_time
            
        return summary
        

class ConfigManager:
    """Manages application configuration and settings"""
    
    def __init__(self, config_file: str = "config.json"):
        self.config_file = Path(config_file)
        self.logger = logging.getLogger(__name__)
        self.default_config = {
            'appearance_mode': 'dark',
            'default_output_format': 'PNG',
            'default_quality': 95,
            'default_resize_width': 1920,
            'default_resize_height': 1080,
            'remember_output_folder': True,
            'last_output_folder': '',
            'auto_clear_after_conversion': False,
            'show_detailed_progress': True,
        }
        self.config = self.load_config()
        
    def load_config(self) -> Dict[str, Any]:
        """Load configuration from file"""
        if not self.config_file.exists():
            return self.default_config.copy()
            
        try:
            import json
            with open(self.config_file, 'r') as f:
                loaded_config = json.load(f)
                
            # Merge with defaults to ensure all keys exist
            config = self.default_config.copy()
            config.update(loaded_config)
            return config
            
        except Exception as e:
            self.logger.error(f"Error loading config: {str(e)}")
            return self.default_config.copy()
            
    def save_config(self):
        """Save current configuration to file"""
        try:
            import json
            with open(self.config_file, 'w') as f:
                json.dump(self.config, f, indent=2)
        except Exception as e:
            self.logger.error(f"Error saving config: {str(e)}")
            
    def get(self, key: str, default=None):
        """Get a configuration value"""
        return self.config.get(key, default)
        
    def set(self, key: str, value: Any):
        """Set a configuration value"""
        self.config[key] = value
        
    def reset_to_defaults(self):
        """Reset configuration to default values"""
        self.config = self.default_config.copy()


def format_duration(seconds: float) -> str:
    """Format duration in seconds to human-readable format"""
    if seconds < 60:
        return f"{seconds:.1f}s"
    elif seconds < 3600:
        minutes = seconds // 60
        secs = seconds % 60
        return f"{int(minutes)}m {int(secs)}s"
    else:
        hours = seconds // 3600
        minutes = (seconds % 3600) // 60
        return f"{int(hours)}h {int(minutes)}m"


def validate_image_dimensions(width: int, height: int) -> bool:
    """Validate image dimensions"""
    return (1 <= width <= 65535 and 1 <= height <= 65535)


def get_optimal_thread_count() -> int:
    """Get optimal number of threads for image processing"""
    import os
    try:
        # Use number of CPU cores, but cap at 8 for memory considerations
        return min(os.cpu_count() or 4, 8)
    except Exception:
        return 4