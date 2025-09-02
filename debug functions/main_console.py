#!/usr/bin/env python3
"""
Console version of main.py that keeps the console open for debugging
"""

import sys
import os
import re
import gc
import subprocess
import plistlib
from datetime import datetime
from PIL import Image
from PIL.ExifTags import TAGS
from PyQt5.QtWidgets import (QMainWindow, QApplication, QFileDialog, 
                           QWidget, QLabel, QTextEdit, QMessageBox,
                           QVBoxLayout, QGridLayout, QSizePolicy, QProgressBar, QRubberBand)
from PyQt5.QtCore import Qt, QTimer, QSize, QRect, QPoint, QEvent
from PyQt5.QtGui import QPixmap
from PyQt5 import uic
from tag_manager import TagManager
from settings_dialog import SettingsDialog

def resource_path(relative_path):
    """ Get absolute path to resource, works for dev and for PyInstaller """
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    
    return os.path.join(base_path, relative_path)

# Import everything from main.py (this will include all the classes and functions)
try:
    from main import *
except ImportError as e:
    print(f"Error importing from main.py: {e}")
    input("Press Enter to exit...")
    sys.exit(1)

def console_main():
    """Main function that keeps console visible"""
    try:
        print("=== HappyTag Console Mode ===")
        print("Initializing application...")
        
        app = QApplication(sys.argv)
        window = MainWindow()
        window.show()
        
        print("Application GUI started successfully!")
        print("Close the GUI window to return to this console.")
        
        result = app.exec_()
        
        print(f"\nApplication exited normally (code: {result})")
        
    except Exception as e:
        print(f"\nERROR: {e}")
        import traceback
        traceback.print_exc()
        
    finally:
        print("\nPress Enter to close console...")
        try:
            input()
        except:
            pass

if __name__ == '__main__':
    console_main()
