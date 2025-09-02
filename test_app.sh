#!/bin/bash

echo "🧪 Testing HappyTag macOS Application"
echo "===================================="

# Check if the app was built
if [ ! -d "dist/HappyTag.app" ]; then
    echo "❌ HappyTag.app not found! Run build_macos.sh first."
    exit 1
fi

echo "📱 Application found: dist/HappyTag.app"
echo "📊 Application size: $(du -sh dist/HappyTag.app | cut -f1)"

# Check app structure
echo ""
echo "🏗️  Application structure:"
ls -la "dist/HappyTag.app/Contents/"
echo ""
ls -la "dist/HappyTag.app/Contents/MacOS/"

# Check if ExifTool is included
echo ""
echo "🔧 Checking ExifTool inclusion:"
if [ -f "dist/HappyTag.app/Contents/MacOS/packages/Image-ExifTool-13.34/exiftool" ]; then
    echo "✅ ExifTool found in application bundle"
    ls -la "dist/HappyTag.app/Contents/MacOS/packages/Image-ExifTool-13.34/exiftool"
else
    echo "❌ ExifTool not found in bundle!"
    echo "Searching for ExifTool..."
    find "dist/HappyTag.app" -name "exiftool" -type f 2>/dev/null || echo "No ExifTool found"
fi

# Check if UI files are included
echo ""
echo "🎨 Checking UI files:"
if [ -d "dist/HappyTag.app/Contents/MacOS/ui" ]; then
    echo "✅ UI folder found"
    ls -la "dist/HappyTag.app/Contents/MacOS/ui/"
else
    echo "❌ UI folder not found!"
    echo "Searching for UI files..."
    find "dist/HappyTag.app" -name "*.ui" -type f 2>/dev/null || echo "No UI files found"
fi

echo ""
echo "🚀 Ready to test!"
echo ""
echo "🖱️  GUI Test:"
echo "   Double-click: dist/HappyTag.app"
echo ""
echo "🖥️  Console Test (with full debug output):"
echo "   ./dist/HappyTag.app/Contents/MacOS/HappyTag"
echo ""
echo "📝 Check Terminal.app for debug messages when running"
echo ""
echo "💡 Tips:"
echo "   - The console version will show all debug output"
echo "   - Test with some images to verify tagging works"
echo "   - Check that macOS Finder tags appear correctly"
