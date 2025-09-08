import os
import os
import sys
from PyQt5.QtWidgets import QDialog, QWidget, QListWidgetItem, QLabel, QSizePolicy, QVBoxLayout, QHBoxLayout, QScrollArea, QSpacerItem
from PyQt5 import uic
from PyQt5.QtCore import Qt, pyqtSignal, QTimer
from .tag_widgets import TagButton, FlowLayout
from .business_widgets import BusinessButton, BusinessCategoryHeader
from .settings_dialog import SettingsDialog

def resource_path(relative_path):
    """ Get absolute path to resource, works for dev and for PyInstaller """
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    
    return os.path.join(base_path, relative_path)

class TagManager(QDialog):
    # Signal to emit when a tag is clicked
    tagClicked = pyqtSignal(str)
    # Signal to emit when a business is clicked - now passes the business button object
    businessClicked = pyqtSignal(object)
    # Signals for street and building clicks
    buildingClicked = pyqtSignal(object)
    streetClicked = pyqtSignal(object)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # Check if UI file exists before loading
        ui_path = resource_path('ui/tagManagerDialog.ui')
        if not os.path.exists(ui_path):
            raise FileNotFoundError(f"UI file not found: {ui_path}")
        
        uic.loadUi(ui_path, self)
        
        # Set dialog size constraints - allow user to resize freely
        self.setMinimumSize(400, 300)
        self.resize(800, 600)  # Default size
        
        # Create a main vertical layout for categories
        self.main_vertical_layout = QVBoxLayout()
        self.main_vertical_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.main_vertical_layout.setSpacing(6)  # Reduced from 10
        
        # Create the container widget for the vertical layout
        self.tags_content_widget = QWidget()
        self.tags_content_widget.setLayout(self.main_vertical_layout)
        
        # Create a scroll area to contain the content
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidget(self.tags_content_widget)
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        
        # The main container that will replace the tagsList
        self.tags_container = self.scroll_area
        
        # Create business layout similar to tags
        self.business_vertical_layout = QVBoxLayout()
        self.business_vertical_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.business_vertical_layout.setSpacing(6)
        
        self.business_content_widget = QWidget()
        self.business_content_widget.setLayout(self.business_vertical_layout)
        
        self.business_scroll_area = QScrollArea()
        self.business_scroll_area.setWidget(self.business_content_widget)
        self.business_scroll_area.setWidgetResizable(True)
        self.business_scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.business_scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        
        self.business_container = self.business_scroll_area
        
        # Create scroll area and layout for street items (similar to business layout)
        self.street_content_widget = QWidget()
        self.street_vertical_layout = QVBoxLayout(self.street_content_widget)
        self.street_vertical_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.street_vertical_layout.setSpacing(8)
        self.street_vertical_layout.setContentsMargins(10, 10, 10, 10)
        
        self.street_scroll_area = QScrollArea()
        self.street_scroll_area.setWidget(self.street_content_widget)
        self.street_scroll_area.setWidgetResizable(True)
        self.street_scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.street_scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        
        self.street_container = self.street_scroll_area
        
        # Get the grid layout containing tagsList
        grid_layout = self.gridLayout
        
        # Find tagsList, businessList, and streetList positions
        self.tags_list_position = None
        self.business_list_position = None
        self.street_list_position = None
        for i in range(grid_layout.count()):
            item = grid_layout.itemAt(i)
            if item.widget() == self.tagsList:
                self.tags_list_position = grid_layout.getItemPosition(i)
            elif item.widget() == self.businessList:
                self.business_list_position = grid_layout.getItemPosition(i)
            elif item.widget() == self.streetList:
                self.street_list_position = grid_layout.getItemPosition(i)
                
        # Keep dialog open when clicking buttons
        self.setModal(False)
        
        # Configure list widgets to prevent horizontal scrollbars
        self.configure_list_widgets()
        
        # Create timer for debounced search
        self.search_timer = QTimer()
        self.search_timer.setSingleShot(True)
        self.search_timer.setInterval(300)  # 300ms delay
        self.search_timer.timeout.connect(self.perform_delayed_filter)
        
        # Connect search input to debounced filter function
        self.tagsInput.textChanged.connect(self.schedule_tags_filter)
        self.businessInput.textChanged.connect(self.schedule_business_filter)
        self.streetInput.textChanged.connect(self.schedule_street_filter)
        
        # Store the original tags, business, and street data for filtering
        self.original_tags_data = []
        self.original_business_data = []
        self.original_street_data = []
        
        # Store search text for debounced filtering
        self.pending_business_search = None
        self.pending_street_search = None
        self.pending_tags_search = None
        
    def showEvent(self, a0):
        """Override showEvent to refresh content every time dialog is shown"""
        super().showEvent(a0)
        # Refresh all lists every time the dialog opens
        self.populate_business_list()
        self.populate_street_list()
        self.populate_tags_list()
        
    def configure_list_widgets(self):
        """Configure list widgets to prevent horizontal scrollbars and enable text wrapping"""
        # Configure businessList
        self.businessList.setWordWrap(True)
        
        # Configure streetList  
        self.streetList.setWordWrap(True)
        
        # Configure tagsList
        self.tagsList.setWordWrap(True)
        
    def create_sample_tags(self):
        """Create sample tags when no tags file is found"""
        tags = [
            ("food & drink", "#FFB6C1"),  # Light pink
            ("culture", "#98FB98"),      # Pale green
            ("shopping", "#87CEEB"),     # Sky blue
            ("wellbeing", "#DDA0DD")     # Plum
        ]
        
        # Clear any existing content
        self.clear_layout()
        
        # Create a container for sample tags
        sample_container = QWidget()
        container_layout = QVBoxLayout(sample_container)
        container_layout.setContentsMargins(5, 5, 5, 5)
        container_layout.setSpacing(10)
        
        # Add a header
        header = QLabel("Sample Tags")
        header.setStyleSheet("""
            QLabel {
                font-size: 14px;
                font-weight: bold;
                color: #333;
                padding: 5px;
                margin-bottom: 5px;
            }
        """)
        container_layout.addWidget(header)
        
        # Create a horizontal flow layout for the tags
        tags_widget = QWidget()
        tags_flow_layout = FlowLayout(tags_widget, margin=3, spacing=3)
        
        # Create tag buttons
        for text, color in tags:
            tag_button = TagButton(text, color)
            tag_button.clicked.connect(lambda checked, t=text: self.on_tag_clicked(t))
            tags_flow_layout.addWidget(tag_button)
        
        # Add the tags widget to the container
        container_layout.addWidget(tags_widget)
        
        # Add the container to the main layout
        self.main_vertical_layout.addWidget(sample_container)
        
        # Make sure we're showing the flow layout view
        self.show_tags_flow_layout()
    
    def on_tag_clicked(self, tag_text):
        """Emit the tagClicked signal when a tag button is clicked"""
        self.tagClicked.emit(tag_text)
        
    def populate_business_list(self):
        """Populate the business list widget"""
        # Get saved settings
        settings = SettingsDialog.get_saved_settings()
        b2b_path = settings.get('b2b_final_path', '')
        
        # Check if required files exist
        if not b2b_path or not os.path.exists(b2b_path):
            # Show the list widget with error message
            self.show_business_list_widget()
            self.businessList.clear()
            item = QListWidgetItem("B2B + B2C final.ods needed. Please load file in File -> Settings")
            self.businessList.addItem(item)
        else:
            # File exists, show the flow layout with businesses
            self.show_business_flow_layout()
            self.load_businesses_from_file(b2b_path)
            
    def populate_street_list(self):
        """Populate the street list widget"""
        self.streetList.clear()
        
        # Get saved settings
        settings = SettingsDialog.get_saved_settings()
        buildings_path = settings.get('buildings_path', '')
        
        # Check if required file exists
        if not buildings_path or not os.path.exists(buildings_path):
            # Show the list widget with error message
            self.show_street_list_widget()
            self.streetList.clear()
            item = QListWidgetItem("Buildings and Streets.ods needed. Please load file in File -> Settings")
            self.streetList.addItem(item)
        else:
            # File exists, show the flow layout with streets and buildings
            self.show_street_flow_layout()
            self.load_streets_from_file(buildings_path)
            
    def populate_tags_list(self):
        """Populate the tags list widget"""
        # Get saved settings
        settings = SettingsDialog.get_saved_settings()
        cloudinary_path = settings.get('cloudinary_tags_path', '')
        
        # Check if required file exists
        if not cloudinary_path or not os.path.exists(cloudinary_path):
            # Show the list widget with error message
            self.show_tags_list_widget()
            self.tagsList.clear()
            item = QListWidgetItem("Cloudinary tags.ods needed. Please load file in File -> Settings")
            self.tagsList.addItem(item)
        else:
            # File exists, show the flow layout with tags
            self.show_tags_flow_layout()
            self.load_tags_from_file(cloudinary_path)
            
    def show_tags_list_widget(self):
        """Show the QListWidget for tags (for error messages)"""
        if self.tags_list_position and self.tagsList.parent() is None:
            # Remove flow layout container if it's there
            self.tags_container.setParent(None)
            # Add the list widget back
            self.gridLayout.addWidget(self.tagsList, 
                                    self.tags_list_position[0], 
                                    self.tags_list_position[1], 
                                    self.tags_list_position[2], 
                                    self.tags_list_position[3])
            
    def show_tags_flow_layout(self):
        """Show the flow layout container for tags (for actual tag buttons)"""
        if self.tags_list_position:
            # Remove list widget
            self.tagsList.setParent(None)
            # Add the flow layout container
            self.gridLayout.addWidget(self.tags_container, 
                                    self.tags_list_position[0], 
                                    self.tags_list_position[1], 
                                    self.tags_list_position[2], 
                                    self.tags_list_position[3])
                                    
    def show_business_list_widget(self):
        """Show the original business list widget (for error messages)"""
        if self.business_list_position:
            # Remove flow layout container if it's there
            self.business_container.setParent(None)
            # Add the list widget back
            self.gridLayout.addWidget(self.businessList, 
                                    self.business_list_position[0], 
                                    self.business_list_position[1], 
                                    self.business_list_position[2], 
                                    self.business_list_position[3])
            
    def show_business_flow_layout(self):
        """Show the flow layout container for business items"""
        if self.business_list_position:
            # Remove list widget
            self.businessList.setParent(None)
            # Add the flow layout container
            self.gridLayout.addWidget(self.business_container, 
                                    self.business_list_position[0], 
                                    self.business_list_position[1], 
                                    self.business_list_position[2], 
                                    self.business_list_position[3])
                                    
    def show_street_list_widget(self):
        """Show the street list widget instead of flow layout"""
        if self.street_list_position:
            # Remove flow layout container if it's there
            self.street_container.setParent(None)
            # Add the list widget back
            self.gridLayout.addWidget(self.streetList, 
                                    self.street_list_position[0], 
                                    self.street_list_position[1], 
                                    self.street_list_position[2], 
                                    self.street_list_position[3])
            
    def show_street_flow_layout(self):
        """Show the flow layout container for street items"""
        if self.street_list_position:
            # Remove list widget
            self.streetList.setParent(None)
            # Add the flow layout container
            self.gridLayout.addWidget(self.street_container, 
                                    self.street_list_position[0], 
                                    self.street_list_position[1], 
                                    self.street_list_position[2], 
                                    self.street_list_position[3])
                                    
    def load_businesses_from_file(self, file_path):
        """Load businesses from both the B2B + B2C final ODS file and NON TLE tenants list ODS file"""
        try:
            print(f"[DEBUG] Starting business loading process...")
            # Clear existing business items
            self.clear_business_layout()
            print(f"[DEBUG] Cleared existing business layout")
            
            # Debug print for B2B + B2C final.ods loading
            print(f"[DEBUG] Loading businesses from B2B + B2C final.ods: {file_path}")
            # Read business data from the main B2B + B2C final ODS file
            business_data = self.read_businesses_from_ods(file_path)
            b2b_count = len(business_data) if business_data else 0
            print(f"[DEBUG] Loaded {b2b_count} businesses from B2B + B2C final.ods")
            
            # Try to read from NON TLE tenants list.ods file
            non_tle_path = os.path.join(os.path.dirname(file_path), "NON TLE tenants list.ods")
            non_tle_data = []
            non_tle_count = 0
            
            if os.path.exists(non_tle_path):
                print(f"[DEBUG] Loading NON TLE businesses from: {non_tle_path}")
                non_tle_data = self.read_non_tle_businesses_from_ods(non_tle_path)
                non_tle_count = len(non_tle_data) if non_tle_data else 0
                print(f"[DEBUG] Loaded {non_tle_count} businesses from NON TLE tenants list.ods")
            else:
                print(f"[DEBUG] NON TLE tenants list.ods not found at: {non_tle_path}")
            
            # Merge the data by category
            print(f"[DEBUG] Merging business data...")
            merged_data = self.merge_business_data(business_data, non_tle_data)
            total_merged_count = sum(len(businesses) for category_name, category_color, businesses in merged_data) if merged_data else 0
            print(f"[DEBUG] Total businesses after merging: {total_merged_count}")
            
            # Store original data for potential filtering later
            self.original_business_data = merged_data if merged_data else []
            
            # Check for issues with individual sources and show user notification
            if total_merged_count == 0:
                # No businesses from either source
                self.show_no_businesses_notification(b2b_count, non_tle_count, non_tle_path)
            elif b2b_count == 0 or (os.path.exists(non_tle_path) and non_tle_count == 0):
                # One source failed - show warning
                self.show_partial_loading_warning(b2b_count, non_tle_count, non_tle_path)
            
            # Display the businesses
            print(f"[DEBUG] Starting to display businesses...")
            self.display_businesses(merged_data if merged_data else [])
            
            if not merged_data:
                print("[DEBUG] Could not read business data from any file")
            else:
                print(f"[DEBUG] Business loading process completed successfully")
                
        except Exception as e:
            print(f"Error loading businesses from file: {e}")

    def show_no_businesses_notification(self, b2b_count, non_tle_count, non_tle_path):
        """Show user notification when no businesses are found from either source"""
        from PyQt5.QtWidgets import QMessageBox
        
        # Create detailed message based on what was found
        message_parts = ["No businesses were found from either source:\n"]
        
        if b2b_count == 0:
            message_parts.append("• B2B + B2C final.ods: No B2C businesses found")
            message_parts.append("  - Check if the file has the correct column headers:")
            message_parts.append("    'Tenant Name', 'Property', 'Street name', 'Category', 'B2B/B2C'")
            message_parts.append("  - Verify there are rows with 'B2C' in the B2B/B2C column")
        else:
            message_parts.append(f"• B2B + B2C final.ods: Found {b2b_count} categories")
        
        if not os.path.exists(non_tle_path):
            message_parts.append("• NON TLE tenants list.ods: File not found")
        elif non_tle_count == 0:
            message_parts.append("• NON TLE tenants list.ods: No B2C businesses found")
            message_parts.append("  - Check if the file has the correct column headers")
            message_parts.append("  - Verify there are rows with 'B2C' in the B2B/B2C column")
        else:
            message_parts.append(f"• NON TLE tenants list.ods: Found {non_tle_count} categories")
        
        message_parts.append("\nPlease check your ODS files and ensure they have the correct format and data.")
        
        msg_box = QMessageBox()
        msg_box.setIcon(QMessageBox.Warning)
        msg_box.setWindowTitle("No Businesses Found")
        msg_box.setText("\n".join(message_parts))
        msg_box.setStandardButtons(QMessageBox.Ok)
        msg_box.exec_()

    def show_partial_loading_warning(self, b2b_count, non_tle_count, non_tle_path):
        """Show warning when one of the business sources fails to load"""
        from PyQt5.QtWidgets import QMessageBox
        
        message_parts = ["Warning: One of the business sources had issues loading:\n"]
        
        if b2b_count == 0:
            message_parts.append("❌ B2B + B2C final.ods: No B2C businesses found")
            message_parts.append("   • Check column headers: 'Tenant Name', 'Property', 'Street name', 'Category', 'B2B/B2C'")
            message_parts.append("   • Verify rows have 'B2C' in the B2B/B2C column")
        else:
            message_parts.append(f"✅ B2B + B2C final.ods: Successfully loaded {b2b_count} categories")
        
        if not os.path.exists(non_tle_path):
            message_parts.append("❌ NON TLE tenants list.ods: File not found")
        elif non_tle_count == 0:
            message_parts.append("❌ NON TLE tenants list.ods: No B2C businesses found")
            message_parts.append("   • Check column headers match expected format")
            message_parts.append("   • Verify rows have 'B2C' in the B2B/B2C column")
        else:
            message_parts.append(f"✅ NON TLE tenants list.ods: Successfully loaded {non_tle_count} categories")
        
        message_parts.append("\nYou can still use the businesses that loaded successfully.")
        message_parts.append("To fix the issue, check the problematic file's format and data.")
        
        msg_box = QMessageBox()
        msg_box.setIcon(QMessageBox.Information)
        msg_box.setWindowTitle("Partial Business Loading")
        msg_box.setText("\n".join(message_parts))
        msg_box.setStandardButtons(QMessageBox.Ok)
        msg_box.exec_()

    def merge_business_data(self, business_data, non_tle_data):
        """Merge business data from both ODS files by category"""
        # Create a dictionary to merge categories
        merged_categories = {}
        
        # Add data from main B2B + B2C file
        for category_name, category_color, businesses in business_data:
            if category_name not in merged_categories:
                merged_categories[category_name] = {
                    'color': category_color,
                    'businesses': []
                }
            merged_categories[category_name]['businesses'].extend(businesses)
        
        # Add data from NON TLE file
        for category_name, category_color, businesses in non_tle_data:
            if category_name not in merged_categories:
                merged_categories[category_name] = {
                    'color': category_color,
                    'businesses': []
                }
            merged_categories[category_name]['businesses'].extend(businesses)
        
        # Convert back to the expected format
        merged_data = []
        for category_name, data in merged_categories.items():
            merged_data.append((category_name, data['color'], data['businesses']))
        
        return merged_data
            
    def clear_business_layout(self):
        """Clear all widgets from the business vertical layout"""
        while self.business_vertical_layout.count():
            child = self.business_vertical_layout.takeAt(0)
            if child and child.widget():
                widget = child.widget()
                if widget:
                    widget.setParent(None)
                    
    def display_businesses(self, business_data):
        """Display businesses from the given data"""
        total_widgets_created = 0
        if business_data:
            print(f"[DEBUG] Creating widgets for {len(business_data)} business categories")
            # Note: Don't overwrite original_business_data here as this method
            # is used for both original data and filtered data
            for category_name, category_color, businesses in business_data:
                print(f"[DEBUG] Creating category '{category_name}' with {len(businesses)} businesses")
                # Create a container for this business category
                category_container = self.create_business_category_container(category_name, category_color, businesses)
                self.business_vertical_layout.addWidget(category_container)
                total_widgets_created += len(businesses)
            print(f"[DEBUG] Total business widgets created: {total_widgets_created}")
        else:
            print(f"[DEBUG] No business data to display")
                                    
                                    
    def load_tags_from_file(self, file_path):
        """Load tags from the cloudinary ODS file"""
        try:
            # Clear existing tags in vertical layout
            self.clear_layout()
            
            # Try to read the ODS file
            tags_data = self.read_tags_from_ods(file_path)
            
            # Store original data for filtering
            self.original_tags_data = tags_data if tags_data else []
            
            # Display the tags (this will be filtered if there's search text)
            self.display_tags(tags_data if tags_data else [])
            
            if not tags_data:
                # Fallback to sample tags if file reading fails
                print("Could not read tags from file, using sample tags")
                self.create_sample_tags()
                
        except Exception as e:
            print(f"Error loading tags from file: {e}")
            # Fallback to sample tags
            self.create_sample_tags()
            
    def clear_layout(self):
        """Clear all widgets from the main vertical layout"""
        while self.main_vertical_layout.count():
            child = self.main_vertical_layout.takeAt(0)
            if child and child.widget():
                widget = child.widget()
                if widget:
                    widget.setParent(None)
                    
    def display_tags(self, tags_data):
        """Display tags from the given data"""
        if tags_data:
            for category_name, category_color, tags in tags_data:
                # Create a container for this category
                category_container = self.create_category_container(category_name, category_color, tags)
                self.main_vertical_layout.addWidget(category_container)
                
    def filter_tags(self):
        """Filter tags based on search input"""
        search_text = self.tagsInput.toPlainText().strip().lower()
        
        if not search_text:
            # If no search text, show all tags
            self.clear_layout()
            self.display_tags(self.original_tags_data)
            return
            
        # Filter the tags
        filtered_data = []
        for category_name, category_color, tags in self.original_tags_data:
            # Filter tags that contain the search text
            filtered_tags = [(tag_name, tag_color) for tag_name, tag_color in tags 
                           if search_text in tag_name.lower()]
            
            # Only include the category if it has matching tags
            if filtered_tags:
                filtered_data.append((category_name, category_color, filtered_tags))
        
        # Clear and display filtered results
        self.clear_layout()
        self.display_tags(filtered_data)
        
    def filter_businesses(self):
        """Filter businesses based on search input"""
        search_text = self.businessInput.toPlainText().strip().lower()
        
        if not search_text:
            # If no search text, show all businesses
            self.clear_business_layout()
            self.display_businesses(self.original_business_data)
            return
            
        # Filter the businesses
        filtered_data = []
        
        for category_name, category_color, businesses in self.original_business_data:
            # Filter businesses that contain the search text in any field
            filtered_businesses = []
            for tenant_name, street_name, property_name, category, trading_as, business_color, business_type in businesses:
                # Create a temporary business button to get searchable text
                temp_button = BusinessButton(tenant_name, street_name, property_name, category, trading_as, business_color, business_type)
                searchable_text = temp_button.get_search_text()
                if search_text in searchable_text:
                    filtered_businesses.append((tenant_name, street_name, property_name, category, trading_as, business_color, business_type))
            
            # Only include the category if it has matching businesses
            if filtered_businesses:
                filtered_data.append((category_name, category_color, filtered_businesses))
        
        # Clear and display filtered results
        self.clear_business_layout()
        self.display_businesses(filtered_data)

    def schedule_business_filter(self):
        """Schedule a debounced business filter"""
        self.pending_business_search = self.businessInput.toPlainText().strip().lower()
        self.search_timer.start()  # Restart the timer
        
    def schedule_tags_filter(self):
        """Schedule a debounced tags filter"""
        self.pending_tags_search = self.tagsInput.toPlainText().strip().lower()
        self.search_timer.start()  # Restart the timer
        
    def schedule_street_filter(self):
        """Schedule a debounced street filter"""
        self.pending_street_search = self.streetInput.toPlainText().strip().lower()
        self.search_timer.start()  # Restart the timer
        
    def perform_delayed_filter(self):
        """Perform the actual filtering after the delay"""
        if self.pending_business_search is not None:
            self.filter_businesses_optimized(self.pending_business_search)
            self.pending_business_search = None
            
        if self.pending_tags_search is not None:
            self.filter_tags_optimized(self.pending_tags_search)
            self.pending_tags_search = None
            
        if self.pending_street_search is not None:
            self.filter_streets_optimized(self.pending_street_search)
            self.pending_street_search = None
    
    def filter_businesses_optimized(self, search_text):
        """Optimized business filter without creating temporary widgets"""
        if not search_text:
            # If no search text, show all businesses
            self.clear_business_layout()
            self.display_businesses(self.original_business_data)
            return
            
        # Filter the businesses without creating temporary widgets
        filtered_data = []
        
        for category_name, category_color, businesses in self.original_business_data:
            # Filter businesses that contain the search text in any field
            filtered_businesses = []
            for tenant_name, street_name, property_name, category, trading_as, business_color, business_type in businesses:
                # Create searchable text directly without temporary widget
                searchable_text = f"{tenant_name}, {property_name}, {street_name}, {category}, {business_type}, {trading_as}".lower()
                if search_text in searchable_text:
                    filtered_businesses.append((tenant_name, street_name, property_name, category, trading_as, business_color, business_type))
            
            # Only include the category if it has matching businesses
            if filtered_businesses:
                filtered_data.append((category_name, category_color, filtered_businesses))
        
        # Clear and display filtered results
        self.clear_business_layout()
        self.display_businesses(filtered_data)
    
    def filter_tags_optimized(self, search_text):
        """Optimized tags filter (placeholder - implement if needed)"""
        # For now, call the existing filter_tags method
        # This can be optimized later if tags also have performance issues
        self.filter_tags()

    def filter_streets_optimized(self, search_text):
        """Optimized street filter without creating temporary widgets"""
        if not search_text:
            # If no search text, show all streets
            self.clear_street_layout()
            self.display_streets(self.original_street_data)
            return
            
        # Filter the streets without creating temporary widgets
        filtered_data = []
        
        for category_name, category_color, items in self.original_street_data:
            # Filter items that contain the search text
            filtered_items = []
            
            if category_name == "Buildings":
                # For buildings, search in both building name and street address
                for building_name, street_address in items:
                    searchable_text = f"{building_name}, {street_address}".lower()
                    if search_text in searchable_text:
                        filtered_items.append((building_name, street_address))
            elif category_name == "Streets":
                # For streets, search in street name only
                for street_name in items:
                    if search_text in street_name.lower():
                        filtered_items.append(street_name)
            
            # Only include the category if it has matching items
            if filtered_items:
                filtered_data.append((category_name, category_color, filtered_items))
        
        # Clear and display filtered results
        self.clear_street_layout()
        self.display_streets(filtered_data)
                
    def read_tags_from_ods(self, file_path):
        """Read tags and colors from the TAGs sheet in the ODS file"""
        try:
            # Use the ODF method directly for better color support
            return self.read_tags_from_ods_alternative(file_path)
        except Exception as e:
            print(f"Error reading ODS file with odfpy: {e}")
            # Fallback to pandas method with default colors
            return self.read_tags_from_ods_pandas(file_path)
    def read_tags_from_ods_pandas(self, file_path):
        """Fallback method using pandas - provides basic functionality with default colors"""
        try:
            import pandas as pd
            
            # Determine the appropriate engine based on file extension
            file_extension = file_path.lower().split('.')[-1]
            if file_extension == 'ods':
                engine = 'odf'
            elif file_extension in ['xlsx', 'xlsm']:
                engine = 'openpyxl'  # openpyxl handles both xlsx and xlsm
            elif file_extension == 'xls':
                engine = 'xlrd'  # xlrd for legacy .xls files
            else:
                engine = 'odf'  # Default to ODF
            
            # Read the TAGs sheet
            df = pd.read_excel(file_path, sheet_name='TAGs', engine=engine)
            
            categories_data = []
            
            # Iterate through rows to find tags grouped by categories
            for index, row in df.iterrows():
                # Skip if column B (category) is empty
                if pd.isna(row.iloc[1]) or str(row.iloc[1]).strip() == '':
                    continue
                    
                category_name = str(row.iloc[1]).strip()
                category_color = "#DDA0DD"  # Default plum
                
                tags_in_category = []
                
                # Look for tags starting from column D (index 3)
                for col_idx in range(3, len(row)):
                    cell_value = row.iloc[col_idx]
                    if pd.notna(cell_value) and str(cell_value).strip() != '':
                        tag_name = str(cell_value).strip()
                        tag_color = "#E6E6FA"  # Light lavender default
                        tags_in_category.append((tag_name, tag_color))
                
                if tags_in_category:  # Only add category if it has tags
                    categories_data.append((category_name, category_color, tags_in_category))
                        
            return categories_data
            
        except Exception as e:
            print(f"Error reading ODS file with pandas: {e}")
            return []
    
    def read_tags_from_ods_alternative(self, file_path):
        """Alternative method to read ODS file using odfpy directly"""
        try:
            from odf.opendocument import load
            from odf.table import Table, TableRow, TableCell
            from odf.text import P
            from odf.style import Style, TableCellProperties
            
            # Load the ODS document
            doc = load(file_path)
            
            # Find the TAGs sheet
            tags_sheet = None
            for table in doc.getElementsByType(Table):
                if table.getAttribute('name') == 'TAGs':
                    tags_sheet = table
                    break
                    
            if not tags_sheet:
                print("TAGs sheet not found in the file")
                return []
                
            categories_data = []
            
            # Iterate through rows
            for row in tags_sheet.getElementsByType(TableRow):
                cells = row.getElementsByType(TableCell)
                
                # Skip if we don't have enough cells or category (column B) is empty
                if len(cells) < 4:
                    continue
                    
                # Check if column B (index 1) has content (category)
                category_cell = cells[1]
                category_text = ""
                for p in category_cell.getElementsByType(P):
                    if p.firstChild:
                        category_text += str(p.firstChild)
                        
                if not category_text.strip():
                    continue
                    
                category_name = category_text.strip()
                category_color = self.extract_cell_background_color(category_cell, doc)
                
                tags_in_category = []
                
                # Extract tags from column D onwards (index 3+)
                for i in range(3, len(cells)):
                    cell = cells[i]
                    cell_text = ""
                    for p in cell.getElementsByType(P):
                        if p.firstChild:
                            cell_text += str(p.firstChild)
                            
                    if cell_text.strip():
                        tag_name = cell_text.strip()
                        # Extract background color from the cell
                        tag_color = self.extract_cell_background_color(cell, doc)
                        tags_in_category.append((tag_name, tag_color))
                
                if tags_in_category:  # Only add category if it has tags
                    categories_data.append((category_name, category_color, tags_in_category))
                        
            return categories_data
            
        except ImportError:
            print("odfpy not available. Please install: pip install odfpy")
            return []
        except Exception as e:
            print(f"Error reading ODS file with odfpy: {e}")
            return []
            
    def extract_cell_background_color(self, cell, doc=None):
        """Extract background color from a table cell"""
        try:
            if not doc:
                return "#E6E6FA"  # Light lavender if no document provided
                
            # Get the style name from the cell
            style_name = cell.getAttribute('stylename')
            if not style_name:
                return "#E6E6FA"  # Light lavender if no style
                
            # Look for the style in the document
            from odf.style import Style, TableCellProperties
            
            # Search in automatic styles first (these usually contain the actual colors)
            for style in doc.automaticstyles.getElementsByType(Style):
                if style.getAttribute('name') == style_name:
                    # Look for table cell properties
                    for prop in style.getElementsByType(TableCellProperties):
                        bg_color = prop.getAttribute('backgroundcolor')
                        if bg_color and bg_color != 'transparent' and bg_color != '#ffffff':
                            return bg_color
                            
            # Search in document styles
            for style in doc.styles.getElementsByType(Style):
                if style.getAttribute('name') == style_name:
                    # Look for table cell properties
                    for prop in style.getElementsByType(TableCellProperties):
                        bg_color = prop.getAttribute('backgroundcolor')
                        if bg_color and bg_color != 'transparent' and bg_color != '#ffffff':
                            return bg_color
            
            return "#E6E6FA"  # Light lavender if no background color found
            
        except Exception as e:
            print(f"Error extracting background color: {e}")
            return "#E6E6FA"  # Light lavender on error
            
    def create_category_container(self, category_name, category_color, tags):
        """Create a container widget for a category with its header and tags"""
        # Create the main container
        container = QWidget()
        container_layout = QVBoxLayout(container)
        container_layout.setSpacing(3)  # Reduced from 5
        container_layout.setContentsMargins(0, 0, 0, 3)  # Reduced from 5
        
        # Create and add the category header in a horizontal layout with spacer
        if category_name:
            header_layout = QHBoxLayout()
            header_layout.setContentsMargins(0, 0, 0, 0)
            
            header = self.create_category_header(category_name, category_color)
            header_layout.addWidget(header)
            
            # Add spacer to push header to the left
            spacer = QSpacerItem(0, 0, QSizePolicy.Expanding, QSizePolicy.Minimum)
            header_layout.addItem(spacer)
            
            # Create a widget to hold the header layout
            header_container = QWidget()
            header_container.setLayout(header_layout)
            container_layout.addWidget(header_container)
        
        # Create a horizontal flow layout for the tags
        tags_widget = QWidget()
        tags_flow_layout = FlowLayout(tags_widget, margin=3, spacing=3)  # Reduced from 5
        
        # Create tag buttons for this category
        for tag_name, tag_color in tags:
            tag_button = TagButton(tag_name, tag_color)
            tag_button.clicked.connect(lambda checked, t=tag_name: self.on_tag_clicked(t))
            tags_flow_layout.addWidget(tag_button)
        
        # Add the tags widget to the container
        container_layout.addWidget(tags_widget)
        
        return container
            
    def create_category_header(self, category_name, category_color):
        """Create a category header widget that fits its content"""
        from PyQt5.QtWidgets import QLabel
        from PyQt5.QtCore import Qt
        
        header = QLabel(category_name)
        header.setStyleSheet(f"""
            QLabel {{
                background-color: {category_color};
                border: none;
                border-radius: 12px;
                padding: 6px 12px;
                margin: 2px 1px;
                color: black;
                font-size: 11px;
                font-weight: bold;
            }}
        """)
        header.setFixedHeight(26)
        # Make header fit its content width
        header.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Fixed)
        header.adjustSize()
        # Make header non-clickable and distinguishable
        header.setEnabled(False)
        return header

    # Business-related methods
    def find_column_indexes(self, df, column_names):
        """Find column indexes by header names"""
        indexes = {}
        headers = df.columns.tolist()
        print(f"[DEBUG] Available headers: {headers}")
        
        for col_name in column_names:
            # Try exact match first
            if col_name in headers:
                indexes[col_name] = headers.index(col_name)
                print(f"[DEBUG] Found column '{col_name}' at index {indexes[col_name]}")
            else:
                # Try case-insensitive match
                found = False
                for i, header in enumerate(headers):
                    if str(header).lower().strip() == col_name.lower().strip():
                        indexes[col_name] = i
                        print(f"[DEBUG] Found column '{col_name}' (case-insensitive) at index {i}")
                        found = True
                        break
                if not found:
                    print(f"[DEBUG] WARNING: Column '{col_name}' not found in headers")
                    indexes[col_name] = None
        
        return indexes
    
    def read_businesses_from_ods(self, file_path):
        """Read business data from the B2B + B2C final file (supports ODS, Excel XLSX, and Excel XLSM formats), Table1 sheet"""
        try:
            print(f"[DEBUG] Starting to read file: {file_path}")
            import pandas as pd
            
            # Determine the appropriate engine based on file extension
            file_extension = file_path.lower().split('.')[-1]
            if file_extension == 'ods':
                engine = 'odf'
                print(f"[DEBUG] Detected ODS file, using 'odf' engine")
            elif file_extension in ['xlsx', 'xlsm']:
                engine = 'openpyxl'  # openpyxl handles both xlsx and xlsm
                print(f"[DEBUG] Detected Excel file (.{file_extension}), using 'openpyxl' engine")
            elif file_extension == 'xls':
                engine = 'xlrd'
                print(f"[DEBUG] Detected legacy Excel file (.xls), using 'xlrd' engine")
            else:
                print(f"[DEBUG] Unknown file extension '{file_extension}', trying 'odf' engine as default")
                engine = 'odf'
            
            # Read the Table1 sheet
            print(f"[DEBUG] Reading Table1 sheet from file...")
            df = pd.read_excel(file_path, sheet_name='Table1', engine=engine)
            print(f"[DEBUG] File loaded, total rows: {len(df)}")
            
            # Find column indexes by header names
            required_columns = ["Tenant Name", "Property", "Street name", "Category", "B2B/B2C", "Trading As"]
            col_indexes = self.find_column_indexes(df, required_columns)
            
            # Check if all required columns were found
            missing_columns = [col for col, idx in col_indexes.items() if idx is None]
            if missing_columns:
                print(f"[DEBUG] ERROR: Missing required columns: {missing_columns}")
                return []
            
            # Filter rows where B2B/B2C column = "B2C"
            b2c_col_idx = col_indexes["B2B/B2C"]
            b2c_rows = df[df.iloc[:, b2c_col_idx] == 'B2C']
            print(f"[DEBUG] Found {len(b2c_rows)} B2C rows after filtering")
            
            # Category colors mapping
            category_colors = {
                'lifestyle': '#F8F8F0',    # Off-white
                'shopping': '#FFF9E6',     # Light yellow
                'wellness': '#E6FFE6',     # Light green
                'dining': '#FFE6F3',       # Light pink
                'services': '#F3E6FF',     # Light purple
                'entertainment': '#FFE6E6', # Light red
                'fitness': '#E6FFF9',      # Light mint
            }
            
            # Group businesses by category
            businesses_by_category = {}
            
            for index, row in b2c_rows.iterrows():
                try:
                    # Extract the required fields using dynamic column indexes
                    street_name = str(row.iloc[col_indexes["Street name"]]) if pd.notna(row.iloc[col_indexes["Street name"]]) else "Unknown Street"
                    property_name = str(row.iloc[col_indexes["Property"]]) if pd.notna(row.iloc[col_indexes["Property"]]) else "Unknown Property"
                    tenant_name = str(row.iloc[col_indexes["Tenant Name"]]) if pd.notna(row.iloc[col_indexes["Tenant Name"]]) else "Unknown Tenant"
                    category = str(row.iloc[col_indexes["Category"]]) if pd.notna(row.iloc[col_indexes["Category"]]) else "Other"
                    trading_as = str(row.iloc[col_indexes["Trading As"]]) if pd.notna(row.iloc[col_indexes["Trading As"]]) else ""
                    
                    # Get category color (default to light gray if not found)
                    category_color = category_colors.get(category.lower(), '#F0F0F0')
                    
                    # Group by category
                    if category not in businesses_by_category:
                        businesses_by_category[category] = {
                            'color': category_color,
                            'businesses': []
                        }
                    
                    # Add business to category
                    businesses_by_category[category]['businesses'].append({
                        'tenant_name': tenant_name,
                        'street_name': street_name,
                        'property_name': property_name,
                        'category': category,
                        'trading_as': trading_as
                    })
                    
                except Exception as e:
                    print(f"Error processing row {index}: {e}")
                    continue
            
            # Convert to the expected format: [(category_name, category_color, businesses)]
            business_data = []
            for category_name, data in businesses_by_category.items():
                businesses = []
                for business in data['businesses']:
                    businesses.append((
                        business['tenant_name'],
                        business['street_name'],
                        business['property_name'],
                        business['category'],
                        business['trading_as'],
                        data['color'],  # Business color same as category
                        'TLE Tenant'    # Business type for regular businesses
                    ))
                
                business_data.append((category_name, data['color'], businesses))
            
            print(f"[DEBUG] Processed {len(business_data)} categories from B2B + B2C final.ods")
            for category_name, color, businesses in business_data:
                print(f"[DEBUG]   Category '{category_name}': {len(businesses)} businesses")
            
            return business_data
            
        except Exception as e:
            print(f"[DEBUG] Error reading business data from file: {e}")
            return []

    def read_non_tle_businesses_from_ods(self, file_path):
        """Read non-TLE business data from the NON TLE tenants list file (supports ODS, Excel XLSX, and Excel XLSM formats)"""
        try:
            print(f"[DEBUG] Starting to read NON TLE file: {file_path}")
            import pandas as pd
            
            # Determine the appropriate engine based on file extension
            file_extension = file_path.lower().split('.')[-1]
            if file_extension == 'ods':
                engine = 'odf'
                print(f"[DEBUG] Detected ODS file, using 'odf' engine")
            elif file_extension in ['xlsx', 'xlsm']:
                engine = 'openpyxl'  # openpyxl handles both xlsx and xlsm
                print(f"[DEBUG] Detected Excel file (.{file_extension}), using 'openpyxl' engine")
            elif file_extension == 'xls':
                engine = 'xlrd'
                print(f"[DEBUG] Detected legacy Excel file (.xls), using 'xlrd' engine")
            else:
                print(f"[DEBUG] Unknown file extension '{file_extension}', trying 'odf' engine as default")
                engine = 'odf'
            
            # Read the default sheet (usually Sheet1)
            print(f"[DEBUG] Reading default sheet from NON TLE file...")
            df = pd.read_excel(file_path, engine=engine)
            print(f"[DEBUG] NON TLE file loaded, total rows: {len(df)}")
            
            # Find column indexes by header names (NON TLE file has different headers)
            required_columns = ["Non-TLE Businesses", "Street", "Address", "B2B/B2C", "Category"]
            optional_columns = ["Trading As"]
            col_indexes = self.find_column_indexes(df, required_columns)
            optional_indexes = self.find_column_indexes(df, optional_columns)
            
            # Check if all required columns were found
            missing_columns = [col for col, idx in col_indexes.items() if idx is None]
            if missing_columns:
                print(f"[DEBUG] ERROR: Missing required columns in NON TLE file: {missing_columns}")
                return []
            
            # Filter rows where B2B/B2C column = "B2C"
            b2c_col_idx = col_indexes["B2B/B2C"]
            b2c_rows = df[df.iloc[:, b2c_col_idx] == 'B2C']
            print(f"[DEBUG] Found {len(b2c_rows)} B2C rows in NON TLE after filtering")
            
            # Category colors mapping (same as existing ones for consistency)
            category_colors = {
                'lifestyle': '#F8F8F0',    # Off-white
                'shopping': '#FFF9E6',     # Light yellow
                'wellness': '#E6FFE6',     # Light green
                'dining': '#FFE6F3',       # Light pink
                'services': '#F3E6FF',     # Light purple
                'entertainment': '#FFE6E6', # Light red
                'fitness': '#E6FFF9',      # Light mint
            }
            
            # Group businesses by category
            businesses_by_category = {}
            
            for index, row in b2c_rows.iterrows():
                try:
                    # Extract the required fields using NON TLE column indexes
                    tenant_name = str(row.iloc[col_indexes["Non-TLE Businesses"]]) if pd.notna(row.iloc[col_indexes["Non-TLE Businesses"]]) else "Unknown Business"
                    street_name = str(row.iloc[col_indexes["Street"]]) if pd.notna(row.iloc[col_indexes["Street"]]) else "Unknown Street"
                    property_name = str(row.iloc[col_indexes["Address"]]) if pd.notna(row.iloc[col_indexes["Address"]]) else "Unknown Address"
                    category = str(row.iloc[col_indexes["Category"]]) if pd.notna(row.iloc[col_indexes["Category"]]) else "Other"
                    
                    # Get trading_as from optional column if available
                    trading_as = ""
                    if optional_indexes.get("Trading As") is not None:
                        trading_as = str(row.iloc[optional_indexes["Trading As"]]) if pd.notna(row.iloc[optional_indexes["Trading As"]]) else ""
                    
                    # Get category color (default to light gray if not found)
                    category_color = category_colors.get(category.lower(), '#F0F0F0')
                    
                    # Group by category
                    if category not in businesses_by_category:
                        businesses_by_category[category] = {
                            'color': category_color,
                            'businesses': []
                        }
                    
                    # Add business to category
                    # For non-TLE businesses: tenant_name, street_name, property_name, category, trading_as, hard-coded "non-tenant"
                    businesses_by_category[category]['businesses'].append({
                        'tenant_name': tenant_name,          # Tenant Name column
                        'street_name': street_name,          # Street name column
                        'property_name': property_name,      # Property column
                        'category': category,                # Category column
                        'trading_as': trading_as,            # Trading As column (if available)
                        'business_type': 'non-tenant'        # Hard-coded identifier
                    })
                    
                except Exception as e:
                    print(f"Error processing non-TLE row {index}: {e}")
                    continue
            
            # Convert to the expected format: [(category_name, category_color, businesses)]
            business_data = []
            for category_name, data in businesses_by_category.items():
                businesses = []
                for business in data['businesses']:
                    businesses.append((
                        business['tenant_name'],     # Tenant Name column
                        business['street_name'],     # Street name column  
                        business['property_name'],   # Property column
                        business['category'],        # Category column
                        business['trading_as'],      # Trading As column
                        data['color'],              # Category color
                        'non-tenant'                # Business type for non-TLE businesses
                    ))
                
                business_data.append((category_name, data['color'], businesses))
            
            print(f"[DEBUG] Processed {len(business_data)} categories from NON TLE tenants list.ods")
            for category_name, color, businesses in business_data:
                print(f"[DEBUG]   NON TLE Category '{category_name}': {len(businesses)} businesses")
            
            return business_data
            
        except Exception as e:
            print(f"[DEBUG] Error reading non-TLE business data from file: {e}")
            return []
    
    def create_business_category_container(self, category_name, category_color, businesses):
        """Create a container widget for a business category with its header and business items"""
        # Create the main container
        container = QWidget()
        container_layout = QVBoxLayout(container)
        container_layout.setSpacing(3)
        container_layout.setContentsMargins(0, 0, 0, 3)
        
        # Create and add the category header in a horizontal layout with spacer
        if category_name:
            header_layout = QHBoxLayout()
            header_layout.setContentsMargins(0, 0, 0, 0)
            
            header = BusinessCategoryHeader(category_name)
            header_layout.addWidget(header)
            
            # Add spacer to push header to the left
            spacer = QSpacerItem(0, 0, QSizePolicy.Expanding, QSizePolicy.Minimum)
            header_layout.addItem(spacer)
            
            # Create a widget to hold the header layout
            header_container = QWidget()
            header_container.setLayout(header_layout)
            container_layout.addWidget(header_container)
        
        # Create a horizontal flow layout for the business items
        businesses_widget = QWidget()
        businesses_flow_layout = FlowLayout(businesses_widget, margin=3, spacing=3)
        
        # Create business buttons for this category
        for tenant_name, street_name, property_name, category, trading_as, business_color, business_type in businesses:
            business_button = BusinessButton(tenant_name, street_name, property_name, category, trading_as, business_color, business_type)
            business_button.clicked.connect(lambda checked, btn=business_button: self.on_business_clicked(btn))
            businesses_flow_layout.addWidget(business_button)
        
        # Add the businesses widget to the container
        container_layout.addWidget(businesses_widget)
        
        return container
        
    def on_business_clicked(self, business_button):
        """Handle business button click"""
        business_description = business_button.get_full_description()
        print(f"Business clicked: {business_description}")
        self.businessClicked.emit(business_button)  # Pass the button object instead of description

    # Street and Building related methods
    def load_streets_from_file(self, file_path):
        """Load streets and buildings from the Buildings and Streets ODS file"""
        try:
            print(f"[DEBUG] Starting street/building loading process...")
            # Clear existing street items
            self.clear_street_layout()
            print(f"[DEBUG] Cleared existing street layout")
            
            print(f"[DEBUG] Loading streets and buildings from: {file_path}")
            # Read data from the Buildings and Streets ODS file
            street_data = self.read_streets_from_ods(file_path)
            if street_data:
                print(f"[DEBUG] Successfully loaded street data")
                # Store original data for potential filtering later
                self.original_street_data = street_data
                # Display the streets and buildings
                self.display_streets(street_data)
                print(f"[DEBUG] Street/building loading process completed successfully")
            else:
                print(f"[DEBUG] No street data could be loaded")
                self.original_street_data = []
                self.show_street_no_data_notification(file_path)
                
        except Exception as e:
            print(f"[DEBUG] Error loading streets from file: {e}")

    def read_streets_from_ods(self, file_path):
        """Read street and building data from the Buildings and Streets file (supports both ODS and Excel formats)"""
        try:
            print(f"[DEBUG] Starting to read Buildings and Streets file: {file_path}")
            import pandas as pd
            
            # Determine the appropriate engine based on file extension
            file_extension = file_path.lower().split('.')[-1]
            if file_extension == 'ods':
                engine = 'odf'
                print(f"[DEBUG] Detected ODS file, using 'odf' engine")
            elif file_extension in ['xlsx', 'xlsm']:
                engine = 'openpyxl'  # openpyxl handles both xlsx and xlsm
                print(f"[DEBUG] Detected Excel file (.{file_extension}), using 'openpyxl' engine")
            elif file_extension == 'xls':
                engine = 'xlrd'
                print(f"[DEBUG] Detected legacy Excel file (.xls), using 'xlrd' engine")
            else:
                print(f"[DEBUG] Unknown file extension '{file_extension}', trying 'odf' engine as default")
                engine = 'odf'
            
            # Read the Buildings and Streets sheet
            print(f"[DEBUG] Reading 'Buildings and Streets' sheet from file...")
            df = pd.read_excel(file_path, sheet_name='Buildings and Streets', engine=engine)
            print(f"[DEBUG] Buildings and Streets file loaded, total rows: {len(df)}")
            
            # Find column indexes by header names
            required_columns = ["BUILDINGS", "STREET"]
            col_indexes = self.find_column_indexes(df, required_columns)
            
            # Check if all required columns were found
            missing_columns = [col for col, idx in col_indexes.items() if idx is None]
            if missing_columns:
                print(f"[DEBUG] ERROR: Missing required columns in Buildings and Streets file: {missing_columns}")
                return None
            
            # Extract colors from headers (first row of data contains header colors)
            buildings_header_color = self.extract_header_color(df, col_indexes["BUILDINGS"])
            street_header_color = self.extract_header_color(df, col_indexes["STREET"])
            
            print(f"[DEBUG] Building header color: {buildings_header_color}")
            print(f"[DEBUG] Street header color: {street_header_color}")
            
            # Process buildings
            buildings = []
            buildings_col_idx = col_indexes["BUILDINGS"]
            street_col_idx = col_indexes["STREET"]
            
            for index, row in df.iterrows():
                try:
                    building_name = str(row.iloc[buildings_col_idx]) if pd.notna(row.iloc[buildings_col_idx]) else ""
                    street_address = str(row.iloc[street_col_idx]) if pd.notna(row.iloc[street_col_idx]) else ""
                    
                    # Only add building if building name is not empty and not a header
                    if building_name and building_name.strip() and building_name != "BUILDINGS":
                        buildings.append((building_name.strip(), street_address.strip()))
                        
                except Exception as e:
                    print(f"[DEBUG] Error processing buildings row {index}: {e}")
                    continue
            
            print(f"[DEBUG] Found {len(buildings)} buildings")
            
            # Process unique streets
            unique_streets = set()
            for index, row in df.iterrows():
                try:
                    street_name = str(row.iloc[street_col_idx]) if pd.notna(row.iloc[street_col_idx]) else ""
                    # Only add street if not empty and not a header
                    if street_name and street_name.strip() and street_name != "STREET":
                        unique_streets.add(street_name.strip())
                        
                except Exception as e:
                    print(f"[DEBUG] Error processing streets row {index}: {e}")
                    continue
            
            print(f"[DEBUG] Found {len(unique_streets)} unique streets")
            
            # Return data in the format: [(category_name, category_color, items)]
            result = []
            # Streets first, then Buildings
            if unique_streets:
                result.append(("Streets", street_header_color, list(unique_streets)))
            if buildings:
                result.append(("Buildings", buildings_header_color, buildings))
            
            return result
            
        except Exception as e:
            print(f"[DEBUG] Error reading Buildings and Streets data from file: {e}")
            return None

    def extract_header_color(self, df, col_index):
        """Extract color from header - placeholder for now, returns default colors"""
        # TODO: Implement actual color extraction from ODS headers
        # For now, return default colors
        if col_index == 0:  # BUILDINGS column
            return "#E6F3FF"  # Light blue
        else:  # STREET column
            return "#E6FFE6"  # Light green

    def display_streets(self, street_data):
        """Display streets and buildings from the given data"""
        total_widgets_created = 0
        if street_data:
            print(f"[DEBUG] Creating widgets for {len(street_data)} street/building categories")
            for category_name, category_color, items in street_data:
                print(f"[DEBUG] Creating category '{category_name}' with {len(items)} items")
                # Create a container for this category
                category_container = self.create_street_category_container(category_name, category_color, items)
                self.street_vertical_layout.addWidget(category_container)
                total_widgets_created += len(items)
            print(f"[DEBUG] Total street/building widgets created: {total_widgets_created}")
        else:
            print(f"[DEBUG] No street data to display")

    def create_street_category_container(self, category_name, category_color, items):
        """Create a container widget for a street/building category with its header and items"""
        from .business_widgets import BusinessCategoryHeader, BuildingButton, StreetButton
        
        # Create the main container
        container = QWidget()
        container_layout = QVBoxLayout(container)
        container_layout.setSpacing(3)
        container_layout.setContentsMargins(0, 0, 0, 0)
        
        # Create category header
        header = BusinessCategoryHeader(category_name)
        container_layout.addWidget(header)
        
        # Create flow layout widget for items
        items_widget = QWidget()
        # Use the FlowLayout that's already imported from tag_widgets
        items_flow_layout = FlowLayout(items_widget)
        items_flow_layout.setSpacing(6)
        
        # Create buttons for this category
        if category_name == "Buildings":
            for building_name, street_address in items:
                building_button = BuildingButton(building_name, street_address, category_color)
                building_button.clicked.connect(lambda checked, btn=building_button: self.on_building_clicked(btn))
                items_flow_layout.addWidget(building_button)
        elif category_name == "Streets":
            for street_name in items:
                street_button = StreetButton(street_name, category_color)
                street_button.clicked.connect(lambda checked, btn=street_button: self.on_street_clicked(btn))
                items_flow_layout.addWidget(street_button)
        
        # Add the items widget to the container
        container_layout.addWidget(items_widget)
        
        return container

    def on_building_clicked(self, building_button):
        """Handle building button click"""
        building_description = f"{building_button.building_name}, {building_button.street_address}"
        print(f"Building clicked: {building_description}")
        self.buildingClicked.emit(building_button)

    def on_street_clicked(self, street_button):
        """Handle street button click"""
        street_description = street_button.street_name
        print(f"Street clicked: {street_description}")
        self.streetClicked.emit(street_button)

    def clear_street_layout(self):
        """Clear all widgets from the street vertical layout"""
        while self.street_vertical_layout.count():
            child = self.street_vertical_layout.takeAt(0)
            if child and child.widget():
                widget = child.widget()
                if widget:
                    widget.deleteLater()

    def show_street_no_data_notification(self, file_path):
        """Show notification when no street/building data could be loaded"""
        from PyQt5.QtWidgets import QMessageBox
        
        msg_box = QMessageBox()
        msg_box.setIcon(QMessageBox.Warning)
        msg_box.setWindowTitle("No Street/Building Data Found")
        msg_box.setText(f"Could not load street or building data from:\n{file_path}\n\n"
                       "Please check that the file has:\n"
                       "• A sheet named 'Buildings and Streets'\n"
                       "• Columns named 'BUILDINGS' and 'STREET'\n"
                       "• Valid data in those columns")
        msg_box.setStandardButtons(QMessageBox.Ok)
        msg_box.exec_()
