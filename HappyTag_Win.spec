# -*- mode: python ; coding: utf-8 -*-
# Windows Production Build Specification for HappyTag
# Only includes essential files and folders: main.py, packages, ui, utilities

block_cipher = None

a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=[
        # ExifTool executables for Windows (both 32-bit and 64-bit)
        ('packages/exiftool_win64/exiftool-13.34_64/exiftool(-k).exe', 'packages/exiftool_win64/exiftool-13.34_64'),
        ('packages/exiftool_win32/exiftool-13.34_32/exiftool(-k).exe', 'packages/exiftool_win32/exiftool-13.34_32'),
    ],
    datas=[
        ('ui', 'ui'),
        ('utilities', 'utilities'),
        # ExifTool support files for both architectures
        ('packages/exiftool_win64/exiftool-13.34_64/exiftool_files', 'packages/exiftool_win64/exiftool-13.34_64/exiftool_files'),
        ('packages/exiftool_win32/exiftool-13.34_32/exiftool_files', 'packages/exiftool_win32/exiftool-13.34_32/exiftool_files'),
    ],
    hiddenimports=[],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        'pytest', '_pytest', 'py', 
        'pyinstaller_hooks_contrib.hooks.stdhooks.hook-pytest',
        'matplotlib', 'scipy', 'numpy.testing',
        'tkinter', 'unittest'
    ],
    noarchive=False,
    optimize=0,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='HappyTag',
    debug=False,                 # Disable debug for production
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,                    # Enable UPX compression for smaller size
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,               # Hide console for production
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
