# -*- mode: python ; coding: utf-8 -*-
# HappyTag macOS Production Build
# Clean, organized build specification following unified folder structure

block_cipher = None

a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=[
        # ExifTool Perl executable (requires execute permissions)
        ('packages/Image-ExifTool-13.34/exiftool', 'packages/Image-ExifTool-13.34/'),
    ],
    datas=[
        # UI files
        ('ui/', 'ui/'),
        # Utilities package (organized Python modules)
        ('utilities/', 'utilities/'),
        # ExifTool Perl library files (data, not executable)
        ('packages/Image-ExifTool-13.34/lib/', 'packages/Image-ExifTool-13.34/lib/'),
    ],
    hiddenimports=[
        'PyQt5.QtCore',
        'PyQt5.QtGui', 
        'PyQt5.QtWidgets',
        'PyQt5.uic',
        'plistlib',
        'subprocess',
        'pickle',
        'pathlib',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        'tkinter',
        'unittest',
        'pydoc',
        'doctest',
        'argparse',
        'difflib',
    ],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='HappyTag',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=True,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='HappyTag',
)

app = BUNDLE(
    coll,
    name='HappyTag.app',
    icon=None,
    bundle_identifier='com.happytag.app',
    version='1.0.0',
    info_plist={
        'CFBundleName': 'HappyTag',
        'CFBundleDisplayName': 'HappyTag',
        'CFBundleIdentifier': 'com.happytag.app',
        'CFBundleVersion': '1.0.0',
        'CFBundleShortVersionString': '1.0.0',
        'CFBundleExecutable': 'HappyTag',
        'CFBundleIconFile': 'icon.icns',
        'NSPrincipalClass': 'NSApplication',
        'NSHighResolutionCapable': True,
        'LSUIElement': False,
        'LSBackgroundOnly': False,
        'CFBundlePackageType': 'APPL',
        # File access permissions
        'NSDocumentsFolderUsageDescription': 'HappyTag needs access to documents to read and tag image files.',
        'NSDesktopFolderUsageDescription': 'HappyTag needs access to desktop to read and tag image files.',
        'NSDownloadsFolderUsageDescription': 'HappyTag needs access to downloads to read and tag image files.',
        'NSRemovableVolumesUsageDescription': 'HappyTag needs access to external drives to read and tag image files.',
    },
)
