# -*- mode: python ; coding: utf-8 -*-
# Windows Custom Debug Build Specification for HappyTag
# Customize the debug categories in runtime_hook_debug.py

block_cipher = None

a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=[
        # ExifTool executable for Windows (requires execute permissions)
        ('packages/exiftool_win64/exiftool-13.34_64/exiftool(-k).exe', 'packages/exiftool_win64/exiftool-13.34_64'),
    ],
    datas=[
        ('ui', 'ui'),
        ('utilities', 'utilities'),
        # ExifTool support files (data, not executable)
        ('packages/exiftool_win64/exiftool-13.34_64/exiftool_files', 'packages/exiftool_win64/exiftool-13.34_64/exiftool_files')
    ],
    hiddenimports=[],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=['runtime_hook_debug.py'],  # This connects to the debug configuration
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
    name='HappyTag_CustomDebug_Win',        # ← CHANGE THIS NAME to trigger your custom config
    debug=True,                             # Enable PyInstaller debug mode
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,                             # Disable UPX for debugging
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,                          # ← Keep True to see debug output, False to hide
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)