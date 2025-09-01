import sys
sys.path.append('.')
from PyQt5.QtWidgets import QApplication
from tag_manager import TagManager
from settings_dialog import SettingsDialog

# Create QApplication
app = QApplication([])

# Get settings
settings = SettingsDialog.get_saved_settings()
b2b_path = settings.get('b2b_final_path', '')
print(f'B2B path: {b2b_path}')

if b2b_path:
    dialog = TagManager()
    business_data = dialog.read_businesses_from_ods(b2b_path)
    print(f'Found {len(business_data)} business categories')
    for cat_name, cat_color, businesses in business_data[:3]:  # Show first 3 categories
        print(f'Category: {cat_name} (color: {cat_color}) - {len(businesses)} businesses')
        for tenant, street, prop, cat, color in businesses[:2]:  # Show first 2 businesses
            print(f'  Business: {tenant} - {street}, {prop}')
else:
    print('No B2B file path configured')
