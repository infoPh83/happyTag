#!/usr/bin/env python3

"""
Test script to verify text field width and height behavior during layout changes
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QTextEdit, QSlider, QLabel
from PyQt5.QtCore import Qt

def test_text_field_responsive_layout():
    """Test text field behavior with dynamic width changes"""
    app = QApplication(sys.argv)
    
    window = QWidget()
    window.setWindowTitle("Text Field Responsive Layout Test")
    window.resize(600, 400)
    
    layout = QVBoxLayout(window)
    
    # Add slider to control width
    width_label = QLabel("Text Field Width:")
    layout.addWidget(width_label)
    
    width_slider = QSlider(Qt.Horizontal)
    width_slider.setMinimum(200)
    width_slider.setMaximum(500) 
    width_slider.setValue(300)
    layout.addWidget(width_slider)
    
    # Create test text field
    text_field = QTextEdit()
    text_field.setFixedWidth(300)
    text_field.setFixedHeight(28)
    text_field.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
    text_field.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
    text_field.setPlaceholderText("Type long text to test wrapping behavior...")
    
    def update_width_and_height():
        """Update text field width and recalculate height"""
        new_width = width_slider.value()
        text_field.setFixedWidth(new_width)
        
        content = text_field.toPlainText()
        if not content:
            text_field.setFixedHeight(28)
            width_label.setText(f"Text Field Width: {new_width}px")
            return
            
        # Set document width and recalculate height
        text_field.document().setTextWidth(new_width - 10)  # Account for margins
        text_field.document().adjustSize()
        
        doc_height = int(text_field.document().size().height())
        margins = text_field.contentsMargins()
        padding = 8
        new_height = doc_height + margins.top() + margins.bottom() + padding
        
        final_height = max(28, new_height)
        text_field.setFixedHeight(final_height)
        
        width_label.setText(f"Text Field Width: {new_width}px | Height: {final_height}px")
    
    def update_height_only():
        """Update height only when text changes"""
        content = text_field.toPlainText()
        if not content:
            text_field.setFixedHeight(28)
            return
            
        current_width = text_field.width()
        text_field.document().setTextWidth(current_width - 10)
        text_field.document().adjustSize()
        
        doc_height = int(text_field.document().size().height())
        margins = text_field.contentsMargins()
        padding = 8
        new_height = doc_height + margins.top() + margins.bottom() + padding
        
        final_height = max(28, new_height)
        text_field.setFixedHeight(final_height)
        
        width_label.setText(f"Text Field Width: {current_width}px | Height: {final_height}px")
    
    # Connect events
    width_slider.valueChanged.connect(update_width_and_height)
    text_field.textChanged.connect(update_height_only)
    
    layout.addWidget(text_field)
    
    instructions = QLabel("""
Instructions:
1. Type some long text that wraps to multiple lines
2. Move the width slider to see how text reflows properly
3. Width and height should both adjust correctly
4. Text should never be cut off or show scroll bars
    """)
    instructions.setWordWrap(True)
    layout.addWidget(instructions)
    
    window.show()
    
    print("Text Field Responsive Layout Test")
    print("==================================")
    print("Use the slider to change width and see how text reflows properly")
    
    sys.exit(app.exec_())

if __name__ == "__main__":
    test_text_field_responsive_layout()
