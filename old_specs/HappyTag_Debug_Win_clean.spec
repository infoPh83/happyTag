# -*- mode: python ; coding: utf-8 -*-
# Windows Debug Build Specification for HappyTag
# Only includes essential files and folders: main.py, packages, ui, utilities

block_cipher = None

a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=[],
    datas=[
        ('ui', 'ui'),
        ('utilities', 'utilities'),
        ('packages/exiftool_win64/exiftool-13.34_64/exiftool(-k).exe', 'packages/exiftool_win64/exiftool-13.34_64'),
        ('packages/exiftool_win64/exiftool-13.34_64/exiftool_files', 'packages/exiftool_win64/exiftool-13.34_64/exiftool_files')
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
    name='HappyTag_Debug_Win',
    debug=True,                  # Enable debug mode
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,                   # Disable UPX for debugging
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,                # Enable console for debug output
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
