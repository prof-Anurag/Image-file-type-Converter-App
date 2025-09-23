#!/usr/bin/env python3
"""
Build script to create a standalone executable using PyInstaller.
"""

import subprocess
import sys
import os
from pathlib import Path

def build_executable():
    """Build the executable using PyInstaller"""
    
    script_dir = Path(__file__).parent
    main_script = script_dir / "main.py"
    icon_file = script_dir / "app_icon.ico"
    
    # PyInstaller command
    cmd = [
        sys.executable, "-m", "PyInstaller",
        "--onefile",  # Single executable file
        "--windowed",  # No console window (for GUI)
        "--name", "ImageConverter",  # Executable name
        f"--icon={icon_file}",  # App icon
        "--add-data", f"{script_dir / 'image_converter.py'};.",
        "--add-data", f"{script_dir / 'utils.py'};.",
        "--add-data", f"{script_dir / 'advanced_features.py'};.",
        "--add-data", f"{icon_file};.",
        "--clean",  # Clean PyInstaller cache
        str(main_script)
    ]
    
    print("Building executable with PyInstaller...")
    print(f"Command: {' '.join(cmd)}")
    
    try:
        # Run PyInstaller
        result = subprocess.run(cmd, check=True, capture_output=True, text=True)
        print("Build successful!")
        print(f"Executable created in: {script_dir / 'dist'}")
        
        # Show the output location
        exe_path = script_dir / "dist" / "ImageConverter.exe"
        if exe_path.exists():
            print(f"Executable path: {exe_path}")
            print(f"File size: {exe_path.stat().st_size / (1024*1024):.1f} MB")
        
    except subprocess.CalledProcessError as e:
        print(f"Build failed with error: {e}")
        print(f"stdout: {e.stdout}")
        print(f"stderr: {e.stderr}")
        return False
        
    return True

def create_spec_file():
    """Create a detailed .spec file for more advanced building"""
    
    spec_content = """
# -*- mode: python ; coding: utf-8 -*-

import sys
from pathlib import Path

block_cipher = None

# Get the directory containing this spec file
SCRIPT_DIR = Path(SPECPATH)

a = Analysis(
    ['main.py'],
    pathex=[str(SCRIPT_DIR)],
    binaries=[],
    datas=[
        ('image_converter.py', '.'),
        ('utils.py', '.'),
        ('advanced_features.py', '.'),
        ('app_icon.ico', '.'),
    ],
    hiddenimports=[
        'PIL._tkinter_finder',
        'tkinterdnd2',
        'customtkinter',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='ImageConverter',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='app_icon.ico',
)
"""
    
    spec_path = Path(__file__).parent / "ImageConverter.spec"
    with open(spec_path, 'w') as f:
        f.write(spec_content)
    
    print(f"Created spec file: {spec_path}")
    return spec_path

if __name__ == "__main__":
    print("Image Converter - Build Script")
    print("=" * 40)
    
    choice = input("Build method:\n1. Quick build (default)\n2. Create spec file first\nChoice (1-2): ").strip()
    
    if choice == "2":
        spec_path = create_spec_file()
        print(f"Spec file created. You can now run: pyinstaller {spec_path}")
    else:
        success = build_executable()
        if success:
            print("\nBuild completed successfully!")
        else:
            print("\nBuild failed!")
            sys.exit(1)