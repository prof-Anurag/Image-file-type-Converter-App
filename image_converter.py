#!/usr/bin/env python3
"""
Image Converter Engine - Handles the actual image conversion logic
with support for multiple formats and advanced options.
"""

from PIL import Image, ImageOps
import os
import logging
from pathlib import Path
from typing import Dict, Any, Optional, Tuple

class ImageConverter:
    """Main image conversion engine"""
    
    # Supported input formats
    SUPPORTED_INPUT_FORMATS = {
        '.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff', '.tif', 
        '.webp', '.avif', '.ico', '.ppm', '.pgm', '.pbm'
    }
    
    # Supported output formats
    SUPPORTED_OUTPUT_FORMATS = {
        'png': 'PNG',
        'jpg': 'JPEG',
        'jpeg': 'JPEG',
        'webp': 'WEBP',
        'tiff': 'TIFF',
        'bmp': 'BMP',
        'gif': 'GIF',
        'ico': 'ICO'
    }
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        
    def convert_image(self, input_path: str, settings: Dict[str, Any]) -> bool:
        """
        Convert an image file to the specified format with given settings
        
        Args:
            input_path: Path to the input image file
            settings: Dictionary containing conversion settings
                - output_format: Target format (e.g., 'png', 'jpeg')
                - output_folder: Output directory (None for same as input)
                - resize: Whether to resize the image
                - resize_dimensions: Tuple of (width, height) for resizing
                - quality: JPEG quality (1-100)
                
        Returns:
            bool: True if conversion was successful, False otherwise
        """
        try:
            # Validate input file
            if not os.path.exists(input_path):
                self.logger.error(f"Input file does not exist: {input_path}")
                return False
                
            input_path = Path(input_path)
            if input_path.suffix.lower() not in self.SUPPORTED_INPUT_FORMATS:
                self.logger.error(f"Unsupported input format: {input_path.suffix}")
                return False
                
            # Get settings
            output_format = settings.get('output_format', 'png').lower()
            output_folder = settings.get('output_folder')
            resize = settings.get('resize', False)
            resize_dimensions = settings.get('resize_dimensions')
            quality = settings.get('quality')
            
            # Validate output format
            if output_format not in self.SUPPORTED_OUTPUT_FORMATS:
                self.logger.error(f"Unsupported output format: {output_format}")
                return False
                
            # Determine output path
            output_path = self._get_output_path(input_path, output_format, output_folder)
            
            # Open and process the image
            with Image.open(input_path) as img:
                # Handle RGBA/transparency for formats that don't support it
                processed_img = self._handle_transparency(img, output_format)
                
                # Apply resizing if requested
                if resize and resize_dimensions:
                    processed_img = self._resize_image(processed_img, resize_dimensions)
                
                # Auto-rotate based on EXIF data
                processed_img = ImageOps.exif_transpose(processed_img)
                
                # Save the image
                success = self._save_image(processed_img, output_path, output_format, quality)
                
                if success:
                    self.logger.info(f"Successfully converted {input_path.name} to {output_path}")
                    return True
                else:
                    return False
                    
        except Exception as e:
            self.logger.error(f"Error converting {input_path}: {str(e)}")
            return False
            
    def _get_output_path(self, input_path: Path, output_format: str, output_folder: Optional[str]) -> Path:
        """Generate the output file path"""
        # Determine output directory
        if output_folder:
            output_dir = Path(output_folder)
        else:
            output_dir = input_path.parent
            
        # Ensure output directory exists
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # Generate output filename
        base_name = input_path.stem
        extension = f".{output_format}"
        
        output_path = output_dir / f"{base_name}{extension}"
        
        # Handle file name conflicts
        counter = 1
        original_output_path = output_path
        while output_path.exists():
            output_path = output_path.parent / f"{base_name}_{counter}{extension}"
            counter += 1
            
        return output_path
        
    def _handle_transparency(self, img: Image.Image, output_format: str) -> Image.Image:
        """Handle transparency for formats that don't support it"""
        # Formats that support transparency
        transparent_formats = {'png', 'gif', 'webp', 'ico'}
        
        if output_format.lower() not in transparent_formats:
            if img.mode in ('RGBA', 'LA'):
                # Create a white background
                background = Image.new('RGB', img.size, 'white')
                if img.mode == 'RGBA':
                    background.paste(img, mask=img.split()[-1])  # Use alpha channel as mask
                else:  # LA mode
                    background.paste(img, mask=img.split()[-1])
                return background
            elif img.mode == 'P' and 'transparency' in img.info:
                # Handle palette mode with transparency
                img = img.convert('RGBA')
                background = Image.new('RGB', img.size, 'white')
                background.paste(img, mask=img.split()[-1])
                return background
                
        return img
        
    def _resize_image(self, img: Image.Image, dimensions: Tuple[int, int]) -> Image.Image:
        """Resize the image while maintaining aspect ratio"""
        target_width, target_height = dimensions
        
        # Calculate the aspect ratio
        original_width, original_height = img.size
        original_ratio = original_width / original_height
        target_ratio = target_width / target_height
        
        if original_ratio > target_ratio:
            # Original is wider than target
            new_width = target_width
            new_height = int(target_width / original_ratio)
        else:
            # Original is taller than target
            new_height = target_height
            new_width = int(target_height * original_ratio)
            
        # Use high-quality resampling
        resized_img = img.resize((new_width, new_height), Image.Resampling.LANCZOS)
        
        return resized_img
        
    def _save_image(self, img: Image.Image, output_path: Path, output_format: str, quality: Optional[int] = None) -> bool:
        """Save the image with appropriate settings"""
        try:
            save_kwargs = {}
            pil_format = self.SUPPORTED_OUTPUT_FORMATS[output_format]
            
            # Format-specific settings
            if pil_format == 'JPEG':
                # Ensure RGB mode for JPEG
                if img.mode != 'RGB':
                    img = img.convert('RGB')
                save_kwargs['quality'] = quality if quality else 95
                save_kwargs['optimize'] = True
                
            elif pil_format == 'PNG':
                save_kwargs['optimize'] = True
                
            elif pil_format == 'WEBP':
                save_kwargs['quality'] = quality if quality else 95
                save_kwargs['method'] = 6  # Best compression
                
            elif pil_format == 'TIFF':
                save_kwargs['compression'] = 'lzw'
                
            # Save the image
            img.save(output_path, format=pil_format, **save_kwargs)
            return True
            
        except Exception as e:
            self.logger.error(f"Error saving image to {output_path}: {str(e)}")
            return False
            
    def get_image_info(self, image_path: str) -> Optional[Dict[str, Any]]:
        """Get information about an image file"""
        try:
            with Image.open(image_path) as img:
                info = {
                    'filename': os.path.basename(image_path),
                    'format': img.format,
                    'mode': img.mode,
                    'size': img.size,
                    'width': img.width,
                    'height': img.height,
                    'file_size': os.path.getsize(image_path),
                    'has_transparency': img.mode in ('RGBA', 'LA') or 'transparency' in img.info
                }
                
                # Add EXIF data if available
                if hasattr(img, '_getexif') and img._getexif():
                    info['has_exif'] = True
                else:
                    info['has_exif'] = False
                    
                return info
                
        except Exception as e:
            self.logger.error(f"Error getting image info for {image_path}: {str(e)}")
            return None
            
    def is_supported_format(self, file_path: str) -> bool:
        """Check if the file format is supported for conversion"""
        file_ext = Path(file_path).suffix.lower()
        return file_ext in self.SUPPORTED_INPUT_FORMATS