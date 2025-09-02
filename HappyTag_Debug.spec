# -*- mode: python ; coding: utf-8 -*-
# Debug version with console output enabled

block_cipher = None

a = Analysis(
    ['main.py'],
    pathex=['/Volumes/Marketing/Simone Morciano/python working folder/happyTag/happyTag'],
    binaries=[
        # Include ExifTool binary
        ('packages/Image-ExifTool-13.34/exiftool', 'packages/Image-ExifTool-13.34/'),
        # Include all ExifTool library files
        ('packages/Image-ExifTool-13.34/lib/*', 'packages/Image-ExifTool-13.34/lib/'),
    ],
    datas=[
        # Include UI files
        ('ui/*.ui', 'ui/'),
        ('ui/*.py', 'ui/'),
        # Include any other data files
        ('packages/Image-ExifTool-13.34/lib', 'packages/Image-ExifTool-13.34/lib'),
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
    [],
    exclude_binaries=True,
    name='HappyTag_Debug',
    debug=True,              # Enable debug output
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=True,            # Enable console for debug output
    disable_windowed_traceback=False,
    argv_emulation=True,     # Enable for macOS compatibility
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
    name='HappyTag_Debug',
)

app = BUNDLE(
    coll,
    name='HappyTag_Debug.app',
    icon=None,
    bundle_identifier='com.happytag.debug',
    version='1.0.0',
    info_plist={
        'CFBundleName': 'HappyTag Debug',
        'CFBundleDisplayName': 'HappyTag Debug',
        'CFBundleIdentifier': 'com.happytag.debug',
        'CFBundleVersion': '1.0.0',
        'CFBundleShortVersionString': '1.0.0',
        'CFBundleExecutable': 'HappyTag_Debug',
        'CFBundleIconFile': 'icon.icns',
        'NSPrincipalClass': 'NSApplication',
        'NSHighResolutionCapable': True,
        'LSUIElement': False,
        'LSBackgroundOnly': False,
        'CFBundlePackageType': 'APPL',
        # Permissions for file access
        'NSDocumentsFolderUsageDescription': 'HappyTag needs access to documents to read and tag image files.',
        'NSDesktopFolderUsageDescription': 'HappyTag needs access to desktop to read and tag image files.',
        'NSDownloadsFolderUsageDescription': 'HappyTag needs access to downloads to read and tag image files.',
        'NSRemovableVolumesUsageDescription': 'HappyTag needs access to external drives to read and tag image files.',
    },
)
