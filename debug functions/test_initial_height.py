#!/usr/bin/env python3

"""
Test script to verify that text field height is calculated correctly when initial content is loaded
"""

import sys
import os
from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QTextEdit, QLabel
from PyQt5.QtCore import Qt

def test_initial_text_height():
    """Test text field height calculation for initial content"""
    app = QApplication(sys.argv)
    
    window = QWidget()
    window.setWindowTitle("Initial Text Height Test")
    window.resize(400, 500)
    
    layout = QVBoxLayout(window)
    
    # Test case 1: Text field with initial content (without height calculation)
    label1 = QLabel("Text field WITHOUT height calculation after setText:")
    layout.addWidget(label1)
    
    text_field1 = QTextEdit()
    text_field1.setFixedWidth(300)
    text_field1.setFixedHeight(28)
    text_field1.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
    text_field1.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
    
    # Set long initial text without height calculation
    long_text = "Market asda dadita gpdgfg g gsdgpsdg sgd g gsda gs sg gdg sdg sdg dfgads gdh fgdhdf 1"
    text_field1.setText(long_text)
    
    layout.addWidget(text_field1)
    
    # Test case 2: Text field with initial content AND height calculation
    label2 = QLabel("Text field WITH height calculation after setText:")
    layout.addWidget(label2)
    
    text_field2 = QTextEdit()
    text_field2.setFixedWidth(300)
    text_field2.setFixedHeight(28)
    text_field2.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
    text_field2.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
    
    def calculate_height(text_field):
        """Calculate and set proper height for text field"""
        content = text_field.toPlainText()
        if not content:
            text_field.setFixedHeight(28)
            return
            
        # Ensure document width matches the current text field width
        current_width = text_field.width()
        text_field.document().setTextWidth(current_width - 10)  # Account for margins
        
        # Force document to recalculate size with proper width
        text_field.document().adjustSize()
        
        # Calculate required height based on document content  
        doc_height = int(text_field.document().size().height())
        margins = text_field.contentsMargins()
        padding = 8
        new_height = doc_height + margins.top() + margins.bottom() + padding
        
        # Set minimum height but no maximum - always show all content
        final_height = max(28, new_height)
        text_field.setFixedHeight(final_height)
        
        print(f"Content: '{content[:50]}...'")
        print(f"Document width: {current_width - 10}, Document height: {doc_height}")
        print(f"Final height: {final_height}")
    
    # Set the same long initial text WITH height calculation
    text_field2.setText(long_text)
    calculate_height(text_field2)  # Call height calculation after setting text
    
    layout.addWidget(text_field2)
    
    # Add instructions
    instructions = QLabel("""
Instructions:
1. Compare the two text fields above
2. Both have the same long text content
3. The first one should show truncated text (height issue)
4. The second one should show all text properly
5. This demonstrates the fix for initial text height calculation
    """)
    instructions.setWordWrap(True)
    layout.addWidget(instructions)
    
    window.show()
    
    print("Initial Text Height Test")
    print("========================")
    print("This test shows the difference between text fields with and without")
    print("proper height calculation after setting initial content.")
    
    sys.exit(app.exec_())

if __name__ == "__main__":
    test_initial_text_height()
