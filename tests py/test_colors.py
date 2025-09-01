import sys
sys.path.append('.')
from PyQt5.QtWidgets import QApplication
from tag_manager import TagManager
from settings_dialog import SettingsDialog

# Create QApplication
app = QApplication([])

# Get settings
settings = SettingsDialog.get_saved_settings()
cloudinary_path = settings.get('cloudinary_tags_path', '')
print(f'Cloudinary path: {cloudinary_path}')

if cloudinary_path:
    dialog = TagManager()
    tags_data = dialog.read_tags_from_ods(cloudinary_path)
    print(f'Found {len(tags_data)} categories')
    for cat_name, cat_color, tags in tags_data:
        print(f'Category: {cat_name} (color: {cat_color}) - {len(tags)} tags')
        for tag_name, tag_color in tags[:3]:  # Show first 3 tags
            print(f'  Tag: {tag_name} (color: {tag_color})')
