#!/bin/bash

echo "🔍 MARKETING DRIVE SPOTLIGHT SETUP"
echo "=================================="

# Check if Marketing drive exists
if [ ! -d "/Volumes/Marketing/" ]; then
    echo "❌ Marketing drive not found at /Volumes/Marketing/"
    exit 1
fi

echo "📁 Marketing drive found"

# Check current status
echo "📊 Current Spotlight status:"
mdutil -s "/Volumes/Marketing/"

echo ""
echo "🔧 MANUAL STEPS TO ENABLE SPOTLIGHT FOR MARKETING DRIVE:"
echo ""
echo "METHOD 1 - System Preferences/Settings:"
echo "1. 🖱️  Click the Apple menu → System Preferences (or System Settings)"
echo "2. 🔍 Search for 'Spotlight' or click on Spotlight"
echo "3. 🚫 Click on the 'Privacy' tab"
echo "4. 👀 Look for 'Marketing' or any external drives in the list"
echo "5. ➖ If Marketing drive is listed, select it and click the '-' button"
echo "6. ✅ Close System Preferences"
echo ""
echo "METHOD 2 - Terminal (requires admin password):"
echo "   sudo mdutil -i on \"/Volumes/Marketing/\""
echo ""
echo "METHOD 3 - Drag & Drop:"
echo "1. 🖱️  Open System Preferences → Spotlight → Privacy"
echo "2. 🖱️  Drag your Marketing drive FROM Finder TO the Privacy list"
echo "3. ➖ Then immediately remove it by selecting it and clicking '-'"
echo "4. ✅ This forces a re-index"
echo ""

# Check for mdworker processes
echo "🔍 Checking for active indexing processes:"
if pgrep -f "mdworker" > /dev/null; then
    echo "✅ Spotlight indexing processes are running"
    echo "   (This means indexing is active)"
else
    echo "❌ No Spotlight indexing processes found"
    echo "   (This might mean indexing is disabled or complete)"
fi

echo ""
echo "⏱️  AFTER ENABLING:"
echo "• Indexing a large drive can take several hours"
echo "• You can monitor progress in Activity Monitor (search for 'mdworker')"
echo "• Tags should become visible in Finder once indexing is complete"
echo ""
echo "🧪 TO TEST IF IT'S WORKING:"
echo "   python3 spotlight_diagnostic.py"
