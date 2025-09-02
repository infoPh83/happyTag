#!/bin/bash

echo "🔧 macOS Finder Tags - Complete Setup Guide"
echo "==========================================="
echo ""

echo "📊 Current Status:"
echo "Marketing drive: $(mdutil -s /Volumes/Marketing 2>/dev/null || echo 'Not found')"
echo "Active indexing processes: $(pgrep -c mdworker 2>/dev/null || echo '0')"
echo ""

echo "🎯 THE ISSUE:"
echo "Your Marketing drive has 'Server search enabled' but NOT full Spotlight indexing."
echo "This means Finder tags won't appear even though the metadata is correctly written."
echo ""

echo "✅ SOLUTION - Choose ONE method:"
echo ""

echo "METHOD 1: System Preferences (EASIEST)"
echo "1. Open System Preferences → Spotlight"
echo "2. Click 'Privacy' tab"
echo "3. If you see 'Marketing' drive in the list, SELECT it and click the '-' button to remove it"
echo "4. If Marketing is NOT in the list, ADD it by clicking '+', then immediately REMOVE it"
echo "5. This forces macOS to re-index the drive with full Spotlight support"
echo "6. Wait 10-30 minutes for indexing to complete"
echo ""

echo "METHOD 2: Terminal (ADVANCED)"
echo "Run these commands in Terminal:"
echo "sudo mdutil -i off /Volumes/Marketing"
echo "sudo mdutil -i on /Volumes/Marketing"
echo "sudo mdutil -E /Volumes/Marketing"
echo ""

echo "METHOD 3: Drag & Drop Re-indexing"
echo "1. Drag the Marketing drive TO the Spotlight Privacy list"
echo "2. Immediately drag it OUT of the list"
echo "3. This triggers a full re-index"
echo ""

echo "🔍 VERIFICATION:"
echo "After setup, run: mdutil -s /Volumes/Marketing"
echo "Should show: 'Indexing enabled'"
echo ""

echo "⏱️  TIMING:"
echo "- Small drives: 5-15 minutes"
echo "- Large drives: 1-6 hours"
echo "- You can work normally during indexing"
echo ""

echo "🧪 TEST:"
echo "Once indexing is complete:"
echo "1. Right-click on test images/1.jpg"
echo "2. Select 'Get Info'"
echo "3. Look for 'Tags' section"
echo "4. You should see color-coded tags!"
