# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['c:\\Users\\johnd\\Desktop\\AI\\Image_File_Type_Converter\\Image-file-type-Converter-App\\main_nodnd.py'],
    pathex=[],
    binaries=[],
    datas=[('c:\\Users\\johnd\\Desktop\\AI\\Image_File_Type_Converter\\Image-file-type-Converter-App\\image_converter.py', '.'), ('c:\\Users\\johnd\\Desktop\\AI\\Image_File_Type_Converter\\Image-file-type-Converter-App\\utils.py', '.'), ('c:\\Users\\johnd\\Desktop\\AI\\Image_File_Type_Converter\\Image-file-type-Converter-App\\advanced_features.py', '.')],
    hiddenimports=[],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
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
    icon=['c:\\Users\\johnd\\Desktop\\AI\\Image_File_Type_Converter\\Image-file-type-Converter-App\\app_icon.ico'],
)
