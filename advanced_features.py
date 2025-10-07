#!/usr/bin/env python3
"""
Advanced Features Module - Additional functionality for the Image Converter.
"""

import customtkinter as ctk
from PIL import Image, ImageTk
import tkinter as tk
from tkinter import messagebox
import os
from pathlib import Path
import threading
from typing import Optional, Dict, Any, List
import logging

class ImagePreviewWindow:
    """A window to preview images before and after conversion"""
    
    def __init__(self, parent, image_path: str):
        self.parent = parent
        self.image_path = image_path
        self.preview_window = None
        self.logger = logging.getLogger(__name__)
        
    def show_preview(self):
        """Show the image preview window"""
        try:
            self.preview_window = ctk.CTkToplevel(self.parent)
            self.preview_window.title(f"Preview - {os.path.basename(self.image_path)}")
            self.preview_window.geometry("800x600")
            self.preview_window.transient(self.parent)
            self.preview_window.grab_set()
            
            # Main frame
            main_frame = ctk.CTkFrame(self.preview_window)
            main_frame.pack(fill="both", expand=True, padx=20, pady=20)
            
            # Title
            title_label = ctk.CTkLabel(
                main_frame,
                text=f"Image Preview: {os.path.basename(self.image_path)}",
                font=ctk.CTkFont(size=16, weight="bold")
            )
            title_label.pack(pady=(0, 10))
            
            # Image display frame
            image_frame = ctk.CTkFrame(main_frame)
            image_frame.pack(fill="both", expand=True, pady=(0, 10))
            
            # Load and display image
            self.display_image(image_frame)
            
            # Image info
            self.display_image_info(main_frame)
            
            # Close button
            close_btn = ctk.CTkButton(
                main_frame,
                text="Close",
                command=self.close_preview,
                width=100
            )
            close_btn.pack(pady=10)
            
        except Exception as e:
            self.logger.error(f"Error showing preview: {str(e)}")
            messagebox.showerror("Preview Error", f"Could not show preview: {str(e)}")
            
    def display_image(self, parent):
        """Display the image in the preview window"""
        try:
            # Load image
            with Image.open(self.image_path) as img:
                # Calculate display size (max 600x400)
                display_width, display_height = 600, 400
                img_width, img_height = img.size
                
                # Maintain aspect ratio
                ratio = min(display_width / img_width, display_height / img_height)
                new_width = int(img_width * ratio)
                new_height = int(img_height * ratio)
                
                # Resize image for display
                display_img = img.resize((new_width, new_height), Image.Resampling.LANCZOS)
                
                # Convert to PhotoImage
                photo = ImageTk.PhotoImage(display_img)
                
                # Display image
                img_label = tk.Label(parent, image=photo, bg="white")
                img_label.image = photo  # Keep a reference
                img_label.pack(expand=True)
                
        except Exception as e:
            self.logger.error(f"Error displaying image: {str(e)}")
            error_label = ctk.CTkLabel(parent, text=f"Could not load image:\n{str(e)}")
            error_label.pack(expand=True)
            
    def display_image_info(self, parent):
        """Display image information"""
        try:
            with Image.open(self.image_path) as img:
                file_size = os.path.getsize(self.image_path)
                
                info_frame = ctk.CTkFrame(parent)
                info_frame.pack(fill="x", pady=(0, 10))
                
                info_text = f"Format: {img.format} | Size: {img.width}x{img.height} | Mode: {img.mode} | File Size: {self.format_file_size(file_size)}"
                
                info_label = ctk.CTkLabel(info_frame, text=info_text)
                info_label.pack(pady=10)
                
        except Exception as e:
            self.logger.error(f"Error getting image info: {str(e)}")
            
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
        
    def close_preview(self):
        """Close the preview window"""
        if self.preview_window:
            self.preview_window.grab_release()
            self.preview_window.destroy()


class BatchProcessingOptions:
    """Advanced batch processing options"""
    
    def __init__(self, parent):
        self.parent = parent
        self.options_window = None
        self.logger = logging.getLogger(__name__)
        
        # Batch options
        self.auto_rotate = ctk.BooleanVar(value=True)
        self.preserve_metadata = ctk.BooleanVar(value=False)
        self.optimize_for_web = ctk.BooleanVar(value=False)
        self.add_watermark = ctk.BooleanVar(value=False)
        self.watermark_text = ctk.StringVar(value="")
        self.parallel_processing = ctk.BooleanVar(value=True)
        
    def show_options(self):
        """Show the batch processing options window"""
        try:
            self.options_window = ctk.CTkToplevel(self.parent)
            self.options_window.title("Batch Processing Options")
            self.options_window.geometry("600x500")
            self.options_window.transient(self.parent)
            self.options_window.grab_set()
            
            # Main frame
            main_frame = ctk.CTkFrame(self.options_window)
            main_frame.pack(fill="both", expand=True, padx=20, pady=20)
            
            # Title
            title_label = ctk.CTkLabel(
                main_frame,
                text="Advanced Batch Processing Options",
                font=ctk.CTkFont(size=18, weight="bold")
            )
            title_label.pack(pady=(0, 20))
            
            # Options
            self.create_options_ui(main_frame)
            
            # Buttons
            button_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
            button_frame.pack(fill="x", pady=(20, 0))
            
            cancel_btn = ctk.CTkButton(
                button_frame,
                text="Cancel",
                command=self.close_options,
                width=100,
                fg_color="gray50",
                hover_color="gray40"
            )
            cancel_btn.pack(side="left")
            
            apply_btn = ctk.CTkButton(
                button_frame,
                text="Apply",
                command=self.apply_options,
                width=100
            )
            apply_btn.pack(side="right")
            
        except Exception as e:
            self.logger.error(f"Error showing batch options: {str(e)}")
            messagebox.showerror("Options Error", f"Could not show options: {str(e)}")
            
    def create_options_ui(self, parent):
        """Create the options UI"""
        # Auto-rotate based on EXIF
        rotate_checkbox = ctk.CTkCheckBox(
            parent,
            text="Auto-rotate images based on EXIF data",
            variable=self.auto_rotate
        )
        rotate_checkbox.pack(anchor="w", pady=(0, 10))
        
        # Preserve metadata
        metadata_checkbox = ctk.CTkCheckBox(
            parent,
            text="Preserve image metadata (EXIF, etc.)",
            variable=self.preserve_metadata
        )
        metadata_checkbox.pack(anchor="w", pady=(0, 10))
        
        # Optimize for web
        web_checkbox = ctk.CTkCheckBox(
            parent,
            text="Optimize for web (progressive JPEG, etc.)",
            variable=self.optimize_for_web
        )
        web_checkbox.pack(anchor="w", pady=(0, 10))
        
        # Parallel processing
        parallel_checkbox = ctk.CTkCheckBox(
            parent,
            text="Enable parallel processing (faster conversion)",
            variable=self.parallel_processing
        )
        parallel_checkbox.pack(anchor="w", pady=(0, 10))
        
        # Watermark options
        watermark_frame = ctk.CTkFrame(parent)
        watermark_frame.pack(fill="x", pady=(20, 10))
        
        watermark_checkbox = ctk.CTkCheckBox(
            watermark_frame,
            text="Add text watermark",
            variable=self.add_watermark,
            command=self.toggle_watermark_options
        )
        watermark_checkbox.pack(anchor="w", pady=(10, 5))
        
        self.watermark_entry = ctk.CTkEntry(
            watermark_frame,
            textvariable=self.watermark_text,
            placeholder_text="Enter watermark text...",
            width=400
        )
        self.watermark_entry.pack(anchor="w", padx=(20, 0), pady=(0, 10))
        
        # Initially disable watermark entry
        self.toggle_watermark_options()
        
    def toggle_watermark_options(self):
        """Toggle watermark options"""
        if self.add_watermark.get():
            self.watermark_entry.configure(state="normal")
        else:
            self.watermark_entry.configure(state="disabled")
            
    def apply_options(self):
        """Apply the selected options"""
        # Here you would normally save the options or apply them to the conversion process
        self.close_options()
        messagebox.showinfo("Options Applied", "Batch processing options have been applied!")
        
    def close_options(self):
        """Close the options window"""
        if self.options_window:
            self.options_window.grab_release()
            self.options_window.destroy()
            
    def get_options(self) -> Dict[str, Any]:
        """Get the current batch processing options"""
        return {
            'auto_rotate': self.auto_rotate.get(),
            'preserve_metadata': self.preserve_metadata.get(),
            'optimize_for_web': self.optimize_for_web.get(),
            'add_watermark': self.add_watermark.get(),
            'watermark_text': self.watermark_text.get(),
            'parallel_processing': self.parallel_processing.get()
        }


class ConversionHistory:
    """Manages conversion history and statistics"""
    
    def __init__(self):
        self.history = []
        self.logger = logging.getLogger(__name__)
        
    def add_conversion(self, source_path: str, target_path: str, success: bool, 
                      conversion_time: float, file_size_before: int, file_size_after: int):
        """Add a conversion to the history"""
        import datetime
        
        entry = {
            'timestamp': datetime.datetime.now(),
            'source_path': source_path,
            'target_path': target_path,
            'source_filename': os.path.basename(source_path),
            'target_filename': os.path.basename(target_path),
            'success': success,
            'conversion_time': conversion_time,
            'file_size_before': file_size_before,
            'file_size_after': file_size_after,
            'compression_ratio': file_size_after / file_size_before if file_size_before > 0 else 1.0
        }
        
        self.history.append(entry)
        
        # Keep only last 100 entries
        if len(self.history) > 100:
            self.history = self.history[-100:]
            
    def get_statistics(self) -> Dict[str, Any]:
        """Get conversion statistics"""
        if not self.history:
            return {}
            
        successful = [entry for entry in self.history if entry['success']]
        failed = [entry for entry in self.history if not entry['success']]
        
        total_time = sum(entry['conversion_time'] for entry in successful)
        total_size_before = sum(entry['file_size_before'] for entry in successful)
        total_size_after = sum(entry['file_size_after'] for entry in successful)
        
        return {
            'total_conversions': len(self.history),
            'successful_conversions': len(successful),
            'failed_conversions': len(failed),
            'success_rate': len(successful) / len(self.history) * 100,
            'total_time': total_time,
            'average_time': total_time / len(successful) if successful else 0,
            'total_size_saved': total_size_before - total_size_after,
            'average_compression_ratio': sum(entry['compression_ratio'] for entry in successful) / len(successful) if successful else 1.0
        }
        
    def clear_history(self):
        """Clear the conversion history"""
        self.history.clear()
        
    def export_history(self, file_path: str):
        """Export history to a CSV file"""
        try:
            import csv
            
            with open(file_path, 'w', newline='', encoding='utf-8') as csvfile:
                fieldnames = ['timestamp', 'source_filename', 'target_filename', 'success', 
                             'conversion_time', 'file_size_before', 'file_size_after', 'compression_ratio']
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                
                writer.writeheader()
                for entry in self.history:
                    writer.writerow({
                        'timestamp': entry['timestamp'].isoformat(),
                        'source_filename': entry['source_filename'],
                        'target_filename': entry['target_filename'],
                        'success': entry['success'],
                        'conversion_time': f"{entry['conversion_time']:.3f}",
                        'file_size_before': entry['file_size_before'],
                        'file_size_after': entry['file_size_after'],
                        'compression_ratio': f"{entry['compression_ratio']:.3f}"
                    })
                    
            return True
            
        except Exception as e:
            self.logger.error(f"Error exporting history: {str(e)}")
            return False