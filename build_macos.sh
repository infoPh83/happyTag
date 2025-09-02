#!/bin/bash

echo "🚀 Building HappyTag for macOS - GUI and Debug Versions"
echo "======================================================"

# Clean previous builds
echo "🧹 Cleaning previous builds..."
rm -rf build/ dist/ HappyTag.app/ HappyTag_Debug.app/

# Check if we're in the right directory
if [ ! -f "main.py" ]; then
    echo "❌ Error: main.py not found. Please run this script from the HappyTag directory."
    exit 1
fi

# Check if virtual environment is active
if [ -z "$VIRTUAL_ENV" ]; then
    echo "🐍 Activating virtual environment..."
    source .venv/bin/activate
fi

# Install/update PyInstaller if needed
echo "📦 Checking PyInstaller..."
python -c "import PyInstaller; print('✅ PyInstaller version:', PyInstaller.__version__)" || {
    echo "❌ PyInstaller not found, installing..."
    pip install pyinstaller
}

# Make sure ExifTool is executable
echo "🔧 Setting ExifTool permissions..."
chmod +x packages/Image-ExifTool-13.34/exiftool

echo ""
echo "🏗️  Building GUI version (normal use)..."
pyinstaller --clean HappyTag_macOS.spec

echo ""
echo "🔧 Building Debug version (with console output)..."
pyinstaller --clean HappyTag_Debug.spec

# Check if builds were successful
echo ""
if [ -d "dist/HappyTag.app" ] && [ -d "dist/HappyTag_Debug.app" ]; then
    echo "✅ Both builds completed successfully!"
    echo ""
    echo "📱 GUI Version: dist/HappyTag.app"
    echo "   - Double-click to launch normally"
    echo "   - Proper macOS menu bar integration"
    echo "   - No console output"
    
    echo ""
    echo "🔧 Debug Version: dist/HappyTag_Debug.app"
    echo "   - Shows console with debug output"
    echo "   - Run from Terminal or double-click"
    echo "   - Use for troubleshooting"
    
    # Show app sizes
    gui_size=$(du -sh "dist/HappyTag.app" | cut -f1)
    debug_size=$(du -sh "dist/HappyTag_Debug.app" | cut -f1)
    echo ""
    echo "� Application sizes:"
    echo "   GUI: $gui_size"
    echo "   Debug: $debug_size"
    
else
    echo "❌ Build failed! Check the output above for errors."
    exit 1
fi
