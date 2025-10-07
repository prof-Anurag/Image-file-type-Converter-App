#!/usr/bin/env python3
"""
Modern Image Converter - A desktop application for converting image formats
with fallback support when drag-and-drop is not available.
"""

import customtkinter as ctk
import tkinter as tk
from tkinter import filedialog, messagebox
from PIL import Image, ImageTk
import threading
import queue
import os
import sys
from pathlib import Path
import logging
from typing import List, Optional
from image_converter import ImageConverter
from utils import FileHandler, ProgressTracker

# Try to import tkinterdnd2, fallback if not available
try:
    import tkinterdnd2 as tkdnd
    DND_AVAILABLE = True
except ImportError:
    DND_AVAILABLE = False
    print("Warning: Drag and drop functionality not available")

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('image_converter.log'),
        logging.StreamHandler()
    ]
)

class ImageConverterApp:
    def __init__(self):
        # Initialize CustomTkinter
        ctk.set_appearance_mode("dark")  # "dark" or "light"
        ctk.set_default_color_theme("blue")  # "blue", "green", "dark-blue"
        
        # Initialize root window based on DND availability
        if DND_AVAILABLE:
            self.root = tkdnd.Tk()
        else:
            self.root = tk.Tk()
            
        self.root.title("Image Converter Pro")
        self.root.geometry("900x700")  # Larger default size
        self.root.minsize(700, 600)  # Increased minimum size
        
        # Set window icon
        try:
            icon_path = os.path.join(os.path.dirname(__file__), "app_icon.ico")
            if os.path.exists(icon_path):
                self.root.iconbitmap(icon_path)
        except Exception as e:
            logging.warning(f"Could not set window icon: {e}")
            
        # Center window on screen
        self.center_window()
        
        # Initialize components
        self.image_converter = ImageConverter()
        self.file_handler = FileHandler()
        self.progress_tracker = ProgressTracker()
        
        # Queue for thread communication
        self.conversion_queue = queue.Queue()
        
        # Variables
        self.output_format = ctk.StringVar(value="PNG")
        self.output_folder = ctk.StringVar(value="Same as input")
        self.resize_option = ctk.BooleanVar(value=False)
        self.resize_width = ctk.StringVar(value="1920")
        self.resize_height = ctk.StringVar(value="1080")
        self.quality_option = ctk.BooleanVar(value=False)
        self.quality_value = ctk.StringVar(value="95")
        
        # File list for processing
        self.file_list = []
        
        self.create_ui()
        if DND_AVAILABLE:
            self.setup_drag_drop()
        
        # Start the UI update thread
        self.root.after(100, self.check_conversion_queue)
        
    def create_ui(self):
        """Create the main user interface"""
        
        # Configure grid layout (3x3)
        self.root.grid_rowconfigure((0, 1, 2), weight=1)
        self.root.grid_columnconfigure((0, 1), weight=1)
        self.root.grid_columnconfigure(2, weight=0)
        
        # Main frame with grid layout
        self.main_frame = ctk.CTkFrame(self.root)
        self.main_frame.grid(row=0, column=0, columnspan=3, sticky="nsew", padx=20, pady=20)
        self.main_frame.grid_rowconfigure(0, weight=0)  # Title row
        self.main_frame.grid_rowconfigure(1, weight=1)  # Content row
        self.main_frame.grid_rowconfigure(2, weight=0)  # Bottom row
        self.main_frame.grid_columnconfigure(0, weight=3)  # Left column
        self.main_frame.grid_columnconfigure(1, weight=1)  # Right column
        
        # App title with gradient effect
        title_frame = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        title_frame.grid(row=0, column=0, columnspan=2, sticky="ew", padx=20, pady=(20, 10))
        
        # Create a gradient-like appearance for the title
        title_label = ctk.CTkLabel(
            title_frame, 
            text="Image Converter Pro",
            font=ctk.CTkFont(size=32, weight="bold"),
            text_color=["#2E7AD1", "#4A9EFF"]
        )
        title_label.pack(pady=(0, 5))
        
        subtitle_text = "Click to browse images • Convert to multiple formats"
        if DND_AVAILABLE:
            subtitle_text = "Drag & Drop images or click to browse • Convert to multiple formats"
            
        subtitle_label = ctk.CTkLabel(
            title_frame,
            text=subtitle_text,
            font=ctk.CTkFont(size=14),
            text_color="gray60"
        )
        subtitle_label.pack(pady=(0, 10))
        
        # Create main content area with two columns using grid
        # Left column - Browse area and file list
        left_frame = ctk.CTkFrame(self.main_frame)
        left_frame.grid(row=1, column=0, sticky="nsew", padx=(20, 10), pady=10)
        left_frame.grid_rowconfigure(0, weight=1)  # Browse area
        left_frame.grid_rowconfigure(1, weight=1)  # File list area
        left_frame.grid_columnconfigure(0, weight=1)
        
        # Browse area
        self.create_browse_area(left_frame)
        
        # File list
        self.create_file_list_area(left_frame)
        
        # Right column - Settings and controls
        right_frame = ctk.CTkFrame(self.main_frame, width=300)
        right_frame.grid(row=1, column=1, sticky="nsew", padx=(10, 20), pady=10)
        right_frame.grid_propagate(False)  # Fix width
        
        self.create_settings_panel(right_frame)
        
        # Bottom frame - Progress and controls - now always visible
        bottom_frame = ctk.CTkFrame(self.main_frame, height=100)
        bottom_frame.grid(row=2, column=0, columnspan=2, sticky="ew", padx=20, pady=(10, 20))
        bottom_frame.grid_propagate(False)  # Ensures minimum height
        bottom_frame.grid_columnconfigure(0, weight=1)  # Progress area
        bottom_frame.grid_columnconfigure(1, weight=0)  # Buttons
        
        self.create_progress_area(bottom_frame)
        self.create_control_buttons(bottom_frame)
        
    def create_browse_area(self, parent):
        """Create the file browsing area"""
        # Create browse zone with better visual feedback
        browse_frame = ctk.CTkFrame(
            parent, 
            height=180,
            corner_radius=15,
            border_width=2,
            border_color=["gray70", "gray30"]
        )
        browse_frame.grid(row=0, column=0, sticky="ew", padx=20, pady=(20, 10))
        browse_frame.grid_propagate(False)
        browse_frame.grid_columnconfigure(0, weight=1)
        browse_frame.grid_rowconfigure(0, weight=1)
        
        # Create inner content frame for better centering
        inner_frame = ctk.CTkFrame(browse_frame, fg_color="transparent")
        inner_frame.grid(row=0, column=0, sticky="nsew")
        inner_frame.grid_columnconfigure(0, weight=1)
        inner_frame.grid_rowconfigure(0, weight=1)
        
        # Browse label with better styling
        if DND_AVAILABLE:
            browse_text = "📁\n\nDrag & Drop Images Here\nor Click to Browse\n\nSupported: PNG, JPEG, WebP, TIFF, BMP, GIF"
        else:
            browse_text = "📁\n\nClick to Browse Images\n\nSupported: PNG, JPEG, WebP, TIFF, BMP, GIF"
            
        self.browse_label = ctk.CTkLabel(
            inner_frame,
            text=browse_text,
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color=["gray50", "gray70"],
            justify="center"
        )
        self.browse_label.grid(row=0, column=0, sticky="nsew", padx=20, pady=20)
        
        # Make the browse area clickable with hover effect
        browse_frame.bind("<Button-1>", self.browse_files)
        self.browse_label.bind("<Button-1>", self.browse_files)
        browse_frame.bind("<Enter>", self.on_browse_hover)
        browse_frame.bind("<Leave>", self.on_browse_leave)
        
        # Store reference for highlighting
        self.browse_frame = browse_frame
        
    def create_file_list_area(self, parent):
        """Create the file list display area"""
        # File list header with count
        list_header_frame = ctk.CTkFrame(parent, fg_color="transparent")
        list_header_frame.grid(row=1, column=0, sticky="ew", padx=20, pady=(10, 5))
        list_header_frame.grid_columnconfigure(0, weight=1)
        
        list_label = ctk.CTkLabel(
            list_header_frame, 
            text="Selected Files:", 
            font=ctk.CTkFont(size=16, weight="bold")
        )
        list_label.grid(row=0, column=0, sticky="w")
        
        self.file_count_label = ctk.CTkLabel(
            list_header_frame,
            text="0 files",
            font=ctk.CTkFont(size=12),
            text_color="gray60"
        )
        self.file_count_label.grid(row=0, column=1, sticky="e")
        
        # Scrollable frame for file list with better styling
        self.file_list_frame = ctk.CTkScrollableFrame(
            parent, 
            height=200,
            corner_radius=10,
            border_width=1,
            border_color=["gray80", "gray20"]
        )
        self.file_list_frame.grid(row=2, column=0, sticky="nsew", padx=20, pady=(0, 20))
        
    def create_settings_panel(self, parent):
        """Create the settings panel"""
        settings_label = ctk.CTkLabel(parent, text="Conversion Settings", font=ctk.CTkFont(size=18, weight="bold"))
        settings_label.pack(pady=(20, 15))
        
        # Output format selection
        format_label = ctk.CTkLabel(parent, text="Output Format:", font=ctk.CTkFont(weight="bold"))
        format_label.pack(anchor="w", pady=(10, 5))
        
        format_options = ["PNG", "JPEG", "JPG", "WEBP", "TIFF", "BMP", "GIF"]
        self.format_combo = ctk.CTkComboBox(
            parent,
            values=format_options,
            variable=self.output_format,
            width=250
        )
        self.format_combo.pack(pady=(0, 15))
        
        # Output folder selection
        folder_label = ctk.CTkLabel(parent, text="Output Folder:", font=ctk.CTkFont(weight="bold"))
        folder_label.pack(anchor="w", pady=(10, 5))
        
        folder_frame = ctk.CTkFrame(parent, fg_color="transparent")
        folder_frame.pack(fill="x", pady=(0, 15))
        
        self.folder_entry = ctk.CTkEntry(folder_frame, textvariable=self.output_folder, width=200)
        self.folder_entry.pack(side="left", fill="x", expand=True)
        
        folder_browse_btn = ctk.CTkButton(
            folder_frame,
            text="Browse",
            command=self.browse_output_folder,
            width=80
        )
        folder_browse_btn.pack(side="right", padx=(10, 0))
        
        # Resize options
        self.resize_checkbox = ctk.CTkCheckBox(
            parent,
            text="Resize Images",
            variable=self.resize_option,
            command=self.toggle_resize_options
        )
        self.resize_checkbox.pack(anchor="w", pady=(15, 5))
        
        self.resize_frame = ctk.CTkFrame(parent, fg_color="transparent")
        self.resize_frame.pack(fill="x", pady=(0, 15))
        
        width_label = ctk.CTkLabel(self.resize_frame, text="Width:")
        width_label.pack(side="left")
        
        self.width_entry = ctk.CTkEntry(self.resize_frame, textvariable=self.resize_width, width=80)
        self.width_entry.pack(side="left", padx=(5, 10))
        
        height_label = ctk.CTkLabel(self.resize_frame, text="Height:")
        height_label.pack(side="left")
        
        self.height_entry = ctk.CTkEntry(self.resize_frame, textvariable=self.resize_height, width=80)
        self.height_entry.pack(side="left", padx=(5, 0))
        
        # Initially disable resize options
        self.toggle_resize_options()
        
        # Quality options
        self.quality_checkbox = ctk.CTkCheckBox(
            parent,
            text="Custom Quality (JPEG only)",
            variable=self.quality_option,
            command=self.toggle_quality_options
        )
        self.quality_checkbox.pack(anchor="w", pady=(15, 5))
        
        self.quality_frame = ctk.CTkFrame(parent, fg_color="transparent")
        self.quality_frame.pack(fill="x", pady=(0, 15))
        
        quality_label = ctk.CTkLabel(self.quality_frame, text="Quality (1-100):")
        quality_label.pack(side="left")
        
        self.quality_entry = ctk.CTkEntry(self.quality_frame, textvariable=self.quality_value, width=80)
        self.quality_entry.pack(side="right")
        
        # Initially disable quality options
        self.toggle_quality_options()
        
        # Theme toggle
        theme_label = ctk.CTkLabel(parent, text="Appearance:", font=ctk.CTkFont(weight="bold"))
        theme_label.pack(anchor="w", pady=(20, 5))
        
        self.theme_switch = ctk.CTkSwitch(
            parent,
            text="Dark Mode",
            command=self.toggle_theme
        )
        self.theme_switch.pack(anchor="w")
        self.theme_switch.select()  # Start in dark mode
        
    def create_progress_area(self, parent):
        """Create the progress tracking area"""
        progress_frame = ctk.CTkFrame(parent, corner_radius=10)
        progress_frame.grid(row=0, column=0, sticky="ew", padx=(10, 5), pady=10)
        progress_frame.grid_columnconfigure(0, weight=1)
        
        self.progress_label = ctk.CTkLabel(
            progress_frame, 
            text="Ready to convert images",
            font=ctk.CTkFont(size=13, weight="bold")
        )
        self.progress_label.grid(row=0, column=0, padx=15, pady=(15, 5), sticky="w")
        
        self.progress_bar = ctk.CTkProgressBar(
            progress_frame,
            height=20,
            corner_radius=10
        )
        self.progress_bar.grid(row=1, column=0, sticky="ew", padx=15, pady=(0, 15))
        self.progress_bar.set(0)
        
    def create_control_buttons(self, parent):
        """Create the control buttons"""
        button_frame = ctk.CTkFrame(parent, fg_color="transparent")
        button_frame.grid(row=0, column=1, sticky="ns", padx=(5, 10), pady=10)
        button_frame.grid_rowconfigure((0, 1, 2), weight=1)
        
        # Add some spacing at the top
        spacing_label = ctk.CTkLabel(button_frame, text="", height=1)
        spacing_label.grid(row=0, column=0)
        
        self.clear_btn = ctk.CTkButton(
            button_frame,
            text="🗑️ Clear Files",
            command=self.clear_files,
            width=140,
            height=35,
            fg_color=["#E74C3C", "#C0392B"],
            hover_color=["#C0392B", "#A93226"],
            font=ctk.CTkFont(size=12, weight="bold")
        )
        self.clear_btn.grid(row=1, column=0, pady=(0, 10))
        
        self.convert_btn = ctk.CTkButton(
            button_frame,
            text="🚀 Start Conversion",
            command=self.start_conversion,
            width=140,
            height=40,
            font=ctk.CTkFont(size=13, weight="bold"),
            fg_color=["#27AE60", "#229954"],
            hover_color=["#229954", "#1E8449"]
        )
        self.convert_btn.grid(row=2, column=0)
        
    def setup_drag_drop(self):
        """Setup drag and drop functionality"""
        if DND_AVAILABLE:
            self.root.drop_target_register(tkdnd.DND_FILES)
            self.root.dnd_bind('<<DropEnter>>', self.on_drag_enter)
            self.root.dnd_bind('<<DropLeave>>', self.on_drag_leave)
            self.root.dnd_bind('<<Drop>>', self.on_drop)
        
    def on_drag_enter(self, event):
        """Handle drag enter event"""
        if hasattr(self, 'browse_frame'):
            self.browse_frame.configure(
                fg_color=["#4A9EFF", "#2E7AD1"],
                border_color=["#2E7AD1", "#4A9EFF"]
            )
            self.browse_label.configure(
                text="🎯\n\nDrop Images Here!\n\nRelease to add files",
                text_color=["white", "white"]
            )
        
    def on_drag_leave(self, event):
        """Handle drag leave event"""
        if hasattr(self, 'browse_frame'):
            self.browse_frame.configure(
                fg_color=["gray92", "gray14"],
                border_color=["gray70", "gray30"]
            )
            self.browse_label.configure(
                text="📁\n\nDrag & Drop Images Here\nor Click to Browse\n\nSupported: PNG, JPEG, WebP, TIFF, BMP, GIF",
                text_color=["gray50", "gray70"]
            )
        
    def on_drop(self, event):
        """Handle file drop event"""
        if hasattr(self, 'browse_frame'):
            # Add a brief success flash
            self.browse_frame.configure(
                fg_color=["#27AE60", "#229954"],
                border_color=["#229954", "#27AE60"]
            )
            self.browse_label.configure(
                text="✓\n\nFiles Added!\n\nProcessing...",
                text_color=["white", "white"]
            )
            
            # Process files
            files = self.root.tk.splitlist(event.data)
            self.add_files(files)
            
            # Reset to normal after a short delay
            self.root.after(1000, self.reset_browse_area)
        
    def on_browse_hover(self, event):
        """Handle mouse hover over browse area"""
        if hasattr(self, 'browse_frame'):
            self.browse_frame.configure(
                border_color=["#4A9EFF", "#2E7AD1"]
            )
        
    def on_browse_leave(self, event):
        """Handle mouse leave browse area"""
        if hasattr(self, 'browse_frame'):
            self.browse_frame.configure(
                border_color=["gray70", "gray30"]
            )
        
    def reset_browse_area(self):
        """Reset browse area to normal state"""
        if hasattr(self, 'browse_frame'):
            self.browse_frame.configure(
                fg_color=["gray92", "gray14"],
                border_color=["gray70", "gray30"]
            )
            if DND_AVAILABLE:
                browse_text = "📁\n\nDrag & Drop Images Here\nor Click to Browse\n\nSupported: PNG, JPEG, WebP, TIFF, BMP, GIF"
            else:
                browse_text = "📁\n\nClick to Browse Images\n\nSupported: PNG, JPEG, WebP, TIFF, BMP, GIF"
            self.browse_label.configure(
                text=browse_text,
                text_color=["gray50", "gray70"]
            )
        
    def browse_files(self, event=None):
        """Browse for files to convert"""
        filetypes = [
            ("All supported images", "*.png *.jpg *.jpeg *.gif *.bmp *.tiff *.webp *.avif"),
            ("PNG files", "*.png"),
            ("JPEG files", "*.jpg *.jpeg"),
            ("WebP files", "*.webp"),
            ("All files", "*.*")
        ]
        
        files = filedialog.askopenfilenames(
            title="Select images to convert",
            filetypes=filetypes
        )
        
        if files:
            self.add_files(files)
            
    def browse_output_folder(self):
        """Browse for output folder"""
        folder = filedialog.askdirectory(title="Select output folder")
        if folder:
            self.output_folder.set(folder)
            
    def add_files(self, files):
        """Add files to the conversion list"""
        added_count = 0
        duplicate_count = 0
        invalid_count = 0
        
        for file_path in files:
            if os.path.isfile(file_path):
                # Check if it's an image file
                if self.file_handler.is_image_file(file_path):
                    if file_path not in self.file_list:
                        self.file_list.append(file_path)
                        added_count += 1
                        self.add_file_to_list_display(file_path)
                    else:
                        duplicate_count += 1
                else:
                    invalid_count += 1
                    
        # Update file count and progress label
        self.update_file_count()
        
        if added_count > 0:
            self.progress_label.configure(
                text=f"✓ {added_count} files added • {len(self.file_list)} total files ready"
            )
        elif duplicate_count > 0:
            messagebox.showinfo("Duplicate Files", f"{duplicate_count} files were already in the list.")
        elif invalid_count > 0:
            messagebox.showwarning("Invalid Files", f"{invalid_count} files are not supported image formats.")
        else:
            messagebox.showwarning("No Files", "No valid image files were selected.")
            
    def add_file_to_list_display(self, file_path):
        """Add a file entry to the display list"""
        file_frame = ctk.CTkFrame(
            self.file_list_frame,
            corner_radius=8,
            border_width=1,
            border_color=["gray85", "gray25"]
        )
        file_frame.pack(fill="x", pady=3, padx=5)
        
        # File info frame
        info_frame = ctk.CTkFrame(file_frame, fg_color="transparent")
        info_frame.pack(side="left", fill="both", expand=True, padx=10, pady=8)
        
        # File name
        filename = os.path.basename(file_path)
        file_label = ctk.CTkLabel(
            info_frame, 
            text=filename, 
            anchor="w",
            font=ctk.CTkFont(size=12, weight="bold")
        )
        file_label.pack(anchor="w")
        
        # File size and format info
        try:
            file_size = os.path.getsize(file_path)
            size_text = self.format_file_size(file_size)
            file_ext = os.path.splitext(file_path)[1].upper().replace('.', '')
            info_text = f"{file_ext} • {size_text}"
        except:
            info_text = "Unknown size"
            
        info_label = ctk.CTkLabel(
            info_frame,
            text=info_text,
            anchor="w",
            font=ctk.CTkFont(size=10),
            text_color="gray60"
        )
        info_label.pack(anchor="w")
        
        # Action buttons frame
        button_frame = ctk.CTkFrame(file_frame, fg_color="transparent")
        button_frame.pack(side="right", padx=8, pady=5)
        
        # Preview button (if image preview is available)
        preview_btn = ctk.CTkButton(
            button_frame,
            text="🔍",
            width=30,
            height=25,
            command=lambda: self.preview_file(file_path),
            fg_color="transparent",
            text_color=["gray60", "gray40"],
            hover_color=["gray80", "gray20"]
        )
        preview_btn.pack(side="left", padx=(0, 5))
        
        # Remove button
        remove_btn = ctk.CTkButton(
            button_frame,
            text="❌",
            width=30,
            height=25,
            command=lambda: self.remove_file(file_path, file_frame),
            fg_color="transparent",
            text_color=["#E74C3C", "#C0392B"],
            hover_color=["#FFE5E5", "#4A1A1A"]
        )
        remove_btn.pack(side="right")
        
    def remove_file(self, file_path, frame):
        """Remove a file from the list"""
        if file_path in self.file_list:
            self.file_list.remove(file_path)
            frame.destroy()
            self.update_file_count()
            if len(self.file_list) > 0:
                self.progress_label.configure(text=f"{len(self.file_list)} files ready for conversion")
            else:
                self.progress_label.configure(text="Ready to convert images")
                self.progress_bar.set(0)
            
    def clear_files(self):
        """Clear all files from the list"""
        if not self.file_list:
            return
            
        # Show confirmation dialog
        result = messagebox.askyesno(
            "Clear Files", 
            f"Are you sure you want to remove all {len(self.file_list)} files from the list?",
            icon="question"
        )
        
        if result:
            self.file_list.clear()
            for widget in self.file_list_frame.winfo_children():
                widget.destroy()
            self.update_file_count()
            self.progress_label.configure(text="Ready to convert images")
            self.progress_bar.set(0)
            
    def update_file_count(self):
        """Update the file count display"""
        count = len(self.file_list)
        if count == 0:
            self.file_count_label.configure(text="No files")
        elif count == 1:
            self.file_count_label.configure(text="1 file")
        else:
            self.file_count_label.configure(text=f"{count} files")
            
    def format_file_size(self, size_bytes):
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
        
    def preview_file(self, file_path):
        """Show a preview of the selected file"""
        try:
            from advanced_features import ImagePreviewWindow
            preview = ImagePreviewWindow(self.root, file_path)
            preview.show_preview()
        except ImportError:
            messagebox.showinfo(
                "Preview Not Available",
                "Image preview feature is not available. The advanced_features module could not be loaded."
            )
        except Exception as e:
            messagebox.showerror(
                "Preview Error",
                f"Could not show preview for {os.path.basename(file_path)}:\\n{str(e)}"
            )
        
    def toggle_resize_options(self):
        """Toggle resize options"""
        if self.resize_option.get():
            self.width_entry.configure(state="normal")
            self.height_entry.configure(state="normal")
        else:
            self.width_entry.configure(state="disabled")
            self.height_entry.configure(state="disabled")
            
    def toggle_quality_options(self):
        """Toggle quality options"""
        if self.quality_option.get():
            self.quality_entry.configure(state="normal")
        else:
            self.quality_entry.configure(state="disabled")
            
    def toggle_theme(self):
        """Toggle between light and dark theme"""
        if self.theme_switch.get():
            ctk.set_appearance_mode("dark")
        else:
            ctk.set_appearance_mode("light")
            
    def start_conversion(self):
        """Start the image conversion process"""
        if not self.file_list:
            messagebox.showwarning("No Files", "Please select files to convert first.")
            return
            
        # Disable convert button during conversion
        self.convert_btn.configure(state="disabled", text="Converting...")
        
        # Start conversion in a separate thread
        conversion_thread = threading.Thread(target=self.convert_images, daemon=True)
        conversion_thread.start()
        
    def convert_images(self):
        """Convert images in a separate thread"""
        try:
            total_files = len(self.file_list)
            successful_conversions = 0
            failed_conversions = []
            
            for i, file_path in enumerate(self.file_list):
                # Update progress
                progress = i / total_files
                self.conversion_queue.put(("progress", progress, f"Converting {os.path.basename(file_path)}..."))
                
                try:
                    # Get conversion settings with validation
                    resize_dimensions = None
                    if self.resize_option.get():
                        try:
                            width = int(self.resize_width.get()) if self.resize_width.get().strip() else 1920
                            height = int(self.resize_height.get()) if self.resize_height.get().strip() else 1080
                            resize_dimensions = (width, height)
                        except ValueError:
                            resize_dimensions = (1920, 1080)  # Default values
                            
                    quality_value = None
                    if self.quality_option.get():
                        try:
                            quality_value = int(self.quality_value.get()) if self.quality_value.get().strip() else 95
                            quality_value = max(1, min(100, quality_value))  # Clamp between 1-100
                        except ValueError:
                            quality_value = 95  # Default value
                    
                    settings = {
                        'output_format': self.output_format.get().lower(),
                        'output_folder': self.output_folder.get() if self.output_folder.get() != "Same as input" else None,
                        'resize': self.resize_option.get(),
                        'resize_dimensions': resize_dimensions,
                        'quality': quality_value
                    }
                    
                    # Convert the image
                    success = self.image_converter.convert_image(file_path, settings)
                    
                    if success:
                        successful_conversions += 1
                    else:
                        failed_conversions.append(os.path.basename(file_path))
                        
                except Exception as e:
                    logging.error(f"Error converting {file_path}: {str(e)}")
                    failed_conversions.append(os.path.basename(file_path))
                    
            # Final progress update
            self.conversion_queue.put(("progress", 1.0, f"Conversion complete: {successful_conversions}/{total_files} successful"))
            self.conversion_queue.put(("complete", successful_conversions, failed_conversions))
            
        except Exception as e:
            logging.error(f"Conversion thread error: {str(e)}")
            self.conversion_queue.put(("error", str(e)))
            
    def check_conversion_queue(self):
        """Check for updates from the conversion thread"""
        try:
            while True:
                message_type, *data = self.conversion_queue.get_nowait()
                
                if message_type == "progress":
                    progress, status_text = data
                    self.progress_bar.set(progress)
                    self.progress_label.configure(text=status_text)
                    
                elif message_type == "complete":
                    successful, failed = data
                    self.convert_btn.configure(state="normal", text="🚀 Start Conversion")
                    
                    if failed:
                        failed_list = "\\n".join(failed)
                        messagebox.showwarning(
                            "Conversion Complete with Errors",
                            f"Successfully converted: {successful}\\nFailed: {len(failed)}\\n\\nFailed files:\\n{failed_list}"
                        )
                    else:
                        messagebox.showinfo("Conversion Complete", f"Successfully converted all {successful} images!")
                        
                elif message_type == "error":
                    error_msg = data[0]
                    self.convert_btn.configure(state="normal", text="🚀 Start Conversion")
                    messagebox.showerror("Conversion Error", f"An error occurred during conversion:\\n{error_msg}")
                    
        except queue.Empty:
            pass
            
        # Schedule next check
        self.root.after(100, self.check_conversion_queue)
        
    def center_window(self):
        """Center the window on the screen"""
        self.root.update_idletasks()
        width = self.root.winfo_width()
        height = self.root.winfo_height()
        x = (self.root.winfo_screenwidth() // 2) - (width // 2)
        y = (self.root.winfo_screenheight() // 2) - (height // 2)
        self.root.geometry(f"{width}x{height}+{x}+{y}")
        
    def run(self):
        """Start the application"""
        self.root.mainloop()

def main():
    """Main function to run the application"""
    try:
        if not DND_AVAILABLE:
            messagebox.showwarning(
                "Drag & Drop Not Available",
                "Drag and drop functionality is not available. You can still browse and select files using the 'Click to Browse' option."
            )
        app = ImageConverterApp()
        app.run()
    except Exception as e:
        logging.error(f"Application error: {str(e)}")
        messagebox.showerror("Application Error", f"An error occurred: {str(e)}")

if __name__ == "__main__":
    main()