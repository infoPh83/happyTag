# TLE PhotoTag

A professional image management and tagging application built with PyQt5, designed for organizing and uploading images to Cloudinary with intelligent metadata management.

## Features

### 🖼️ Image Management
- **Visual Image Browser**: Intuitive flow layout for browsing large image collections
- **Drag & Drop Support**: Easy image import via drag and drop
- **Multiple Format Support**: JPEG, PNG, TIFF, WebP and more
- **Smart Image Assessment**: Automatic image quality evaluation
- **Bulk Operations**: Process multiple images simultaneously

### 🏷️ Advanced Tagging System
- **Category-Based Organization**: Organize tags by categories (season, weather, people, activities, etc.)
- **Color-Coded Tags**: Visual tag identification with customizable colors
- **Business & Location Tags**: Pre-loaded database of businesses, streets, and buildings
- **Custom Keywords**: Add new tags and categories on-the-fly
- **Spreadsheet Integration**: Tag data managed via ODS/Excel files

### ☁️ Cloudinary Integration
- **Direct Upload**: Upload images with metadata to Cloudinary
- **Real-Time Status**: Live monitoring of storage, transformations, and bandwidth usage
- **Credit Tracking**: Visual progress bars showing usage limits
- **Batch Upload**: Upload multiple images with progress tracking
- **Auto-Sync**: Keep local and cloud images synchronized

### 📊 Metadata Management
- **ExifTool Integration**: Comprehensive IPTC/XMP metadata handling
- **Keyword Management**: Add, edit, and remove image keywords
- **Location Data**: Manage location and business information
- **Date Handling**: Smart date format conversion and management
- **Metadata Preservation**: Non-destructive metadata editing

## Installation

### Prerequisites
- Python 3.13+
- ExifTool (bundled with application)
- PyQt5
- Cloudinary account (for upload features)

### Setup

1. **Clone the repository**
   ```bash
   git clone https://github.com/simoPh83/TLE_photoTag.git
   cd TLE_photoTag
   ```

2. **Create virtual environment**
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate  # On macOS/Linux
   # or
   .venv\Scripts\activate  # On Windows
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure Cloudinary** (optional)
   - Open Settings and enter your Cloudinary credentials
   - Configure tag database paths

5. **Run the application**
   ```bash
   python main.py
   ```

## Building Executables

### macOS

Build the application as a standalone macOS app:

```bash
# Standard build (no console)
pyinstaller HappyTag.spec

# Debug build (with console and verbose logging)
pyinstaller HappyTag_VerboseDebug_macOS.spec
```

The built application will be in the `dist/` folder.

### Windows

```bash
pyinstaller HappyTag_Windows.spec
```

## Configuration

### Settings Dialog
Access via **File → Settings** to configure:
- Cloudinary API credentials
- Tag database paths
- Default folders
- Upload preferences

### Tag Databases
The application uses ODS/Excel spreadsheets for tag management:
- `TAGs final.ods` - Main tag categories and keywords
- `B2B + B2C final.xlsm` - Business database
- `NON TLE tenants list.ods` - Additional businesses
- `Buildings and Streets.xlsx` - Location data

## Usage

### Basic Workflow

1. **Load Images**: Drag and drop images or use File → Open Folder
2. **Add Tags**: Use the tag manager (Window → Show Tags Window) to select tags
3. **Review Metadata**: Check applied tags in the metadata panel
4. **Upload**: Click Upload to send images to Cloudinary

### Tag Manager

The tag manager provides:
- **Category Tabs**: Tags, Businesses, Streets & Buildings
- **Color-Coded Categories**: Easy visual identification
- **Search**: Quick filtering of tags
- **Add Keywords**: Create new tags with the "+" button

### Keyboard Shortcuts
- `Cmd/Ctrl + O` - Open folder
- `Cmd/Ctrl + S` - Save settings
- `Cmd/Ctrl + Q` - Quit application

## Project Structure

```
TLE_photoTag/
├── main.py                      # Main application entry point
├── utilities/                   # Core functionality modules
│   ├── addTagDialog.py         # Add keyword dialog
│   ├── tag_manager.py          # Tag management widget
│   ├── tag_widgets.py          # Tag button components
│   ├── business_widgets.py     # Business tag widgets
│   ├── image_flow_manager.py   # Image display manager
│   ├── image_card_widget.py    # Individual image cards
│   ├── cloudinary_update_v13.py # Cloudinary integration
│   ├── image_assessment.py     # Image quality analysis
│   ├── exiftool_utils.py       # Metadata operations
│   └── ...
├── ui/                         # Qt Designer UI files
│   ├── mainWindow.ui
│   ├── tagManagerDialog.ui
│   └── settingsDialog.ui
├── packages/                   # Bundled dependencies
│   └── Image-ExifTool-13.34/  # ExifTool
├── *.spec                      # PyInstaller build specs
└── README.md                   # This file
```

## Debug Mode

For troubleshooting, run with debug logging:

```bash
# Enable all debug categories
export HAPPYTAG_DEBUG="all"
export HAPPYTAG_DEBUG_LEVEL="VERBOSE"
python main.py
```

Or use the debug build:
```bash
./dist/HappyTag/HappyTag_VerboseDebug_macOS
```

Available debug categories:
- `startup` - Application initialization
- `cloudinary` - Cloud operations
- `upload` - Upload process
- `metadata` - Metadata operations
- `exiftool` - ExifTool interactions
- `image_loading` - Image loading operations
- `errors` - Error messages
- `all` - Enable all categories

## Dependencies

### Core
- PyQt5 - GUI framework
- pandas - Data management
- openpyxl - Excel file support
- odfpy - ODS file support
- Pillow - Image processing
- pyexiftool - ExifTool wrapper

### Cloud
- cloudinary - Cloud storage API
- requests - HTTP operations

### Build
- pyinstaller - Executable creation

See `requirements.txt` for complete list with versions.

## Contributing

This is a private project for The London Estate image management. Contact the repository owner for contribution guidelines.

## License

Proprietary - All rights reserved.

## Support

For issues or questions, contact the development team or create an issue in the repository.

## Acknowledgments

- ExifTool by Phil Harvey - Metadata management
- Cloudinary - Cloud image platform
- PyQt5 - Application framework

---

**Version**: 1.0.0  
**Last Updated**: May 2026  
**Platform**: macOS, Windows  
**Status**: Production Ready
