from PyQt5.QtWidgets import QWidget, QPushButton, QSizePolicy, QVBoxLayout, QLabel
from PyQt5.QtGui import QPalette, QColor, QFont
from PyQt5.QtCore import Qt

class BusinessButton(QPushButton):
    def __init__(self, tenant_name, street_name, property_name, category, trading_as, background_color="#E6F3FF", business_type="TLE Tenant", parent=None):
        super().__init__(parent)
        self.tenant_name = tenant_name
        self.street_name = street_name
        self.property_name = property_name
        self.category = category
        self.trading_as = trading_as
        self.business_type = business_type  # "TLE Tenant" or "non-tenant"
        
        self.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        
        # Temporarily commented out comma replacement for testing
        # self.tenant_name = self.tenant_name.replace(',', '|')
        # self.street_name = self.street_name.replace(',', '|')
        # self.property_name = self.property_name.replace(',', '|')
        # self.category = self.category.replace(',', '|')
        # self.trading_as = self.trading_as.replace(',', '|')
        # self.business_type = self.business_type.replace(',', '|')
        
        # Create the content
        self.setup_content(background_color)
        
    def _calculate_text_height(self, text, font, width):
        """Calculate the height needed for text with given font and width"""
        from PyQt5.QtGui import QFontMetrics
        
        metrics = QFontMetrics(font)
        # Use a simple approach for height calculation
        line_height = metrics.height()
        lines_needed = len(text) // (width // metrics.averageCharWidth()) + 1
        return max(line_height * lines_needed + 10, 30)  # Add padding and minimum height
        
    def setup_content(self, background_color):
        """Setup the button content with tenant name and details"""
        # Set up the button as a container
        self.setFlat(True)
        
        # Create layout for the button content
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(2)
        
        # Create tenant name label (bold, 10pt font, can wrap to multiple lines)
        self.tenant_label = QLabel(self.tenant_name)
        tenant_font = QFont()
        tenant_font.setPointSize(10)
        tenant_font.setBold(True)
        self.tenant_label.setFont(tenant_font)
        self.tenant_label.setWordWrap(True)
        
        # Set a reasonable width and let height adjust
        self.tenant_label.setMinimumWidth(180)
        self.tenant_label.setMaximumWidth(200)
        # Calculate and set minimum height based on text content
        min_height = self._calculate_text_height(self.tenant_name, tenant_font, 200)
        self.tenant_label.setMinimumHeight(min_height)
        layout.addWidget(self.tenant_label)
        
        # Create details labels (smaller font)
        details = [
            self.property_name,
            self.street_name,
            self.category,
            self.business_type,
            self.trading_as  # Add trading_as after business_type
        ]
        
        for detail in details:
            detail_label = QLabel(detail)
            detail_font = QFont()
            detail_font.setPointSize(9)
            detail_label.setFont(detail_font)
            detail_label.setWordWrap(True)
            detail_label.setStyleSheet("color: #666666;")
            layout.addWidget(detail_label)
        
        # Set background color with some transparency
        bg_color = QColor(background_color)
        bg_color.setAlpha(180)  # 70% opacity
        
        hover_color = QColor(background_color)
        hover_color.setAlpha(230)  # 90% opacity
        
        # Style the button
        self.setStyleSheet(f"""
            QPushButton {{
                background-color: {bg_color.name(QColor.HexArgb)};
                border: 1px solid transparent;
                border-radius: 8px;
                margin: 3px;
                outline: none;
            }}
            QPushButton:hover {{
                background-color: {hover_color.name(QColor.HexArgb)};
                border-radius: 8px;
            }}
            QPushButton:pressed {{
                background-color: {background_color};
                border-radius: 8px;
            }}
        """)
        
        # Set consistent width and let height adjust to content
        self.setMinimumWidth(200)
        self.setMaximumWidth(220)  # Allow slight width variation
        
        # Use expanding height policy to accommodate content
        self.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.MinimumExpanding)
        
        # Ensure the widget adjusts to its content
        self.adjustSize()
        
        # Set a reasonable minimum height but allow growth
        calculated_height = self.sizeHint().height()
        self.setMinimumHeight(max(calculated_height, 110))
    
    def sizeHint(self):
        """Calculate the ideal size for this widget based on content"""
        from PyQt5.QtCore import QSize
        
        # Get the layout's preferred size
        layout = self.layout()
        if layout and hasattr(layout, 'sizeHint'):
            layout_size = layout.sizeHint()
            # Add some padding for margins and ensure minimum dimensions
            width = max(layout_size.width() + 20, 200)
            height = max(layout_size.height() + 20, 110)
            return QSize(width, height)
        
        # Fallback to default size
        return QSize(200, 110)
    
    def get_full_description(self):
        """Return concatenated description of all business fields with comma separation"""
        return f"{self.tenant_name}, {self.property_name}, {self.street_name}, {self.category}, {self.business_type}, {self.trading_as}"
    
    def get_individual_fields(self):
        """Return list of individual business fields for duplicate checking"""
        return [
            self.tenant_name.strip(),
            self.property_name.strip(), 
            self.street_name.strip(),
            self.category.strip(),
            self.business_type.strip(),
            self.trading_as.strip()
        ]
    
    def get_search_text(self):
        """Return all searchable text for this business"""
        return self.get_full_description().lower()

class BusinessCategoryHeader(QLabel):
    def __init__(self, category_name, parent=None):
        super().__init__(category_name, parent)
        
        # Style the category header
        self.setStyleSheet(f"""
            QLabel {{
                background-color: #F5F5F5;
                border: none;
                border-radius: 8px;
                padding: 6px 12px;
                margin: 2px 1px;
                color: black;
                font-size: 11px;
                font-weight: bold;
            }}
        """)
        self.setFixedHeight(26)
        # Make header fit its content width
        self.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Fixed)
        self.adjustSize()
        # Make header non-clickable
        self.setEnabled(False)


class BuildingButton(QPushButton):
    def __init__(self, building_name, street_address, background_color="#E6F3FF", parent=None):
        super().__init__(parent)
        self.building_name = building_name
        self.street_address = street_address
        
        self.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        
        # Create the content
        self.setup_content(background_color)
        
    def setup_content(self, background_color):
        """Setup the button content with building name and address"""
        # Set up the button as a container
        self.setFlat(True)
        
        # Create a vertical layout for the button content
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 6, 8, 6)
        layout.setSpacing(2)
        
        # Create building name label (bold, 10pt font, can wrap to multiple lines)
        self.building_label = QLabel(self.building_name)
        building_font = QFont()
        building_font.setPointSize(10)
        building_font.setBold(True)
        self.building_label.setFont(building_font)
        self.building_label.setWordWrap(True)
        
        # Set a reasonable width and let height adjust
        self.building_label.setMinimumWidth(180)
        self.building_label.setMaximumWidth(200)
        layout.addWidget(self.building_label)
        
        # Create address label (smaller font)
        address_label = QLabel(self.street_address)
        address_font = QFont()
        address_font.setPointSize(9)
        address_label.setFont(address_font)
        address_label.setWordWrap(True)
        layout.addWidget(address_label)
        
        # Set button styling
        self.setStyleSheet(f"""
            QPushButton {{
                background-color: {background_color};
                border: 1px solid #ddd;
                border-radius: 8px;
                padding: 8px;
                margin: 2px;
                text-align: left;
                color: black;
            }}
            QPushButton:hover {{
                background-color: #CCE7FF;
                border: 2px solid #0078d4;
            }}
            QPushButton:pressed {{
                background-color: #B3DBFF;
            }}
        """)
        
        # Set minimum size
        self.setMinimumSize(200, 80)

    def sizeHint(self):
        """Calculate the ideal size for this widget based on content"""
        from PyQt5.QtCore import QSize
        
        # Get the layout's preferred size
        layout = self.layout()
        if layout and hasattr(layout, 'sizeHint'):
            layout_size = layout.sizeHint()
            # Add some padding for margins and ensure minimum dimensions
            width = max(layout_size.width() + 20, 200)
            height = max(layout_size.height() + 20, 80)
            return QSize(width, height)
        
        # Fallback to default size
        return QSize(200, 80)


class StreetButton(QPushButton):
    def __init__(self, street_name, background_color="#E6F3FF", parent=None):
        super().__init__(parent)
        self.street_name = street_name
        
        # Set up the button styling and content
        self.setText(street_name)
        self.setStyleSheet(f"""
            QPushButton {{
                background-color: {background_color};
                border: 1px solid transparent;
                border-radius: 15px;
                padding: 5px 12px;
                margin: 2px;
                color: black;
                font-size: 11px;
                font-weight: 500;
                text-align: center;
                outline: none;
            }}
            QPushButton:hover {{
                background-color: #CCE7FF;
                border-radius: 15px;
            }}
            QPushButton:pressed {{
                background-color: #B3DBFF;
                border-radius: 15px;
            }}
        """)
        
        # Set size policy and minimum size
        self.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Fixed)
        self.setMinimumHeight(36)
        self.adjustSize()
