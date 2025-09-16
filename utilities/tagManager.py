from PyQt5.QtWidgets import QDialog
from PyQt5.QtCore import Qt
from PyQt5 import uic
from .addTagDialog import AddKeywordDialog

class TagManagerDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        uic.loadUi('ui/tagManagerDialog.ui', self)
        
        # Set window flags to stay on top but allow minimizing
        self.setWindowFlags(self.windowFlags() | Qt.WindowStaysOnTopHint)
        
        # Store reference to parent to access spreadsheet path
        self.parent_window = parent
        
        # Connect the add keyword button
        self.openAddKeywordDialogButton.clicked.connect(self.open_add_keyword_dialog)
    
    def open_add_keyword_dialog(self):
        """Open the Add Keyword dialog"""
        try:
            # Get the spreadsheet path from settings or parent
            spreadsheet_path = None
            if hasattr(self.parent_window, 'settings') and self.parent_window.settings:
                spreadsheet_path = self.parent_window.settings.get('cloudinary_tags_path', '')
            
            # Try to get tags data from parent window's tag manager
            tags_data = None
            if hasattr(self.parent_window, 'centralWidget'):
                # Look for tag manager widget in the central widget
                central_widget = self.parent_window.centralWidget()
                if hasattr(central_widget, 'findChild'):
                    from .tag_manager import TagManager
                    tag_manager = central_widget.findChild(TagManager)
                    if tag_manager and hasattr(tag_manager, 'original_tags_data'):
                        tags_data = tag_manager.original_tags_data
                        print(f"Found {len(tags_data) if tags_data else 0} categories in memory")
            
            # Create and show the add keyword dialog
            add_dialog = AddKeywordDialog(spreadsheet_path, self, tags_data)
            
            # Connect signal to handle when a tag is added
            add_dialog.tagAdded.connect(self.on_tag_added)
            
            # Show dialog
            add_dialog.exec_()
            
        except Exception as e:
            print(f"Error opening add keyword dialog: {e}")
            import traceback
            traceback.print_exc()
    
    def on_tag_added(self, text, color, category):
        """Handle when a new tag is added"""
        print(f"New tag added: '{text}' with color '{color}' in category '{category}'")
        
        # TODO: Refresh the tag widgets display if it's currently shown
        # This would require access to the tag manager widget to reload tags
        if hasattr(self.parent_window, 'refresh_tags'):
            self.parent_window.refresh_tags()
        
        # Optionally show a notification in the parent window
        if hasattr(self.parent_window, 'show_status_message'):
            self.parent_window.show_status_message(f"Added tag '{text}' to category '{category}'")
