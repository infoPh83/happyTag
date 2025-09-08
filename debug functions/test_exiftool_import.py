
try:
    import exiftool
    print('SUCCESS: exiftool module imported')
    print(f'exiftool location: {exiftool.__file__}')
    print(f'exiftool version: {exiftool.__version__ if hasattr(exiftool, "__version__") else "unknown"}')
except ImportError as e:
    print(f'IMPORT ERROR: {e}')
except Exception as e:
    print(f'OTHER ERROR: {e}')

