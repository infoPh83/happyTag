from PyQt5.QtWidgets import QDialog
from PyQt5.QtCore import Qt
from PyQt5 import uic

class TagManagerDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        uic.loadUi('ui/tagManagerDialog.ui', self)
        
        # Set window flags to stay on top but allow minimizing
        self.setWindowFlags(self.windowFlags() | Qt.WindowStaysOnTopHint)
