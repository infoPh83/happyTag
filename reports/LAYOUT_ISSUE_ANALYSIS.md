# Cloudinary UI Layout Issue Analysis

## Problem Identified
The Cloudinary UI widgets (labels below the credits bar) are not visible after Cloudinary connection, even though they should be shown. The layout doesn't refresh to accommodate the newly visible widgets.

## Root Cause
1. **Initial State**: Widgets are properly hidden during startup to prevent "TextLabel" placeholders
2. **Connection Success**: Cloudinary connects and data is loaded successfully 
3. **Layout Issue**: When widgets are made visible, the parent layout doesn't recalculate its size
4. **Missing Visibility**: The labels beneath the credits bar remain collapsed/hidden due to layout constraints

## Debug Findings
- Cloudinary connection works: API calls successful, data retrieved
- Credits bar updates correctly with percentages and overlay text
- UI widgets hiding during startup works correctly  
- `_update_cloudinary_ui_status` method not being called as expected

## Symptoms
- Credits bar visible and working
- Labels underneath credits bar not visible (should show "Storage: 0.0%", "Transformations: 4.9%", "Bandwidth: 0.0%")
- Layout height doesn't expand to show the additional row of labels

## Solution Approach
Instead of relying on the complex call chain, integrate the widget visibility and layout refresh directly into the credits bar update callback, which we know is being called successfully.

## Implementation Plan
1. Add widget visibility management to `update_credits_bar()` method
2. Update label text with actual values when credits bar is updated
3. Force layout refresh after making widgets visible
4. Ensure proper text content replaces "TextLabel" placeholders

This approach leverages the working credits bar update mechanism to ensure the UI visibility and layout refresh happens at the right time.