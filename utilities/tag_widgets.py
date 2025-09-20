from PyQt5.QtWidgets import QWidget, QPushButton, QSizePolicy, QLayout, QWidgetItem
from PyQt5.QtGui import QPalette, QColor
from PyQt5.QtCore import Qt, QSize, QRect, QPoint
from .debug_utils import debug_tag_widgets

class TagButton(QPushButton):
    def __init__(self, text, color, parent=None):
        super().__init__(text, parent)
        self.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        
        debug_tag_widgets(f"Creating TagButton with text='{text}', color='{color}'")
        
        # Set background color with some transparency
        bg_color = QColor(color)
        bg_color.setAlpha(180)  # 70% opacity
        
        hover_color = QColor(color)
        hover_color.setAlpha(230)  # 90% opacity
        
        debug_tag_widgets(f"bg_color={bg_color.name(QColor.HexArgb)}, hover_color={hover_color.name(QColor.HexArgb)}")
        
        # Style the button with modern look and explicit border-radius
        self.setStyleSheet(f"""
            QPushButton {{
                background-color: {bg_color.name(QColor.HexArgb)} !important;
                border: 1px solid transparent !important;
                border-radius: 15px !important;
                padding: 6px 12px !important;
                margin: 2px !important;
                color: black !important;
                font-size: 11px !important;
                font-weight: 500 !important;
                min-height: 20px !important;
                min-width: 30px !important;
                outline: none !important;
            }}
            QPushButton:hover {{
                background-color: {hover_color.name(QColor.HexArgb)} !important;
                border: 2px solid #0078d4 !important;
                border-radius: 15px !important;
            }}
            QPushButton:pressed {{
                background-color: {color} !important;
                border-radius: 15px !important;
            }}
        """)
        
        # Also set a property to help with CSS specificity
        self.setProperty("class", "TagButton")
        
        # Set fixed height but allow width to adjust to content
        self.setMinimumHeight(26)
        self.adjustSize()

from PyQt5.QtWidgets import QLayout
from PyQt5.QtCore import QSize, QRect, QPoint

class FlowLayout(QLayout):
    def __init__(self, parent=None, margin=0, spacing=-1):
        super().__init__(parent)
        self.setContentsMargins(margin, margin, margin, margin)
        self.setSpacing(spacing)
        self._item_list = []

    def __del__(self):
        item = self.takeAt(0)
        while item:
            item = self.takeAt(0)

    def addItem(self, item):
        self._item_list.append(item)

    def addWidget(self, widget):
        # Add widget through the parent class which will call addItem
        super().addWidget(widget)

    def count(self):
        return len(self._item_list)

    def itemAt(self, index):
        if 0 <= index < len(self._item_list):
            return self._item_list[index]
        return None

    def takeAt(self, index):
        if 0 <= index < len(self._item_list):
            return self._item_list.pop(index)
        return None

    def expandingDirections(self):
        return Qt.Orientations(Qt.Orientation(0))

    def hasHeightForWidth(self):
        return True

    def heightForWidth(self, width):
        height = self._doLayout(QRect(0, 0, width, 0), True)
        # print(f"[DEBUG] FlowLayout.heightForWidth({width}) -> {height}px")
        return height

    def setGeometry(self, rect):
        super().setGeometry(rect)
        self._doLayout(rect, False)

    def sizeHint(self):
        # Return the actual calculated size based on current container width
        parent_widget = self.parentWidget()
        # print(f"[DEBUG-FLOW-SIZEHINT] parent_widget: {parent_widget}, has width attr: {hasattr(parent_widget, 'width') if parent_widget else False}")
        if parent_widget and hasattr(parent_widget, 'width'):
            parent_width = parent_widget.width()
            # print(f"[DEBUG-FLOW-SIZEHINT] parent_width: {parent_width}, item_count: {len(self._item_list)}")
            if parent_width > 0 and len(self._item_list) > 0:
                calculated_height = self.heightForWidth(parent_width)
                hint = QSize(parent_width, calculated_height)
                # print(f"[DEBUG-FLOW-SIZEHINT] Calculated hint: {hint.width()}x{hint.height()}")
                return hint
        
        # Fallback to minimum size
        fallback = self.minimumSize()
        # print(f"[DEBUG-FLOW-SIZEHINT] Fallback to minimum: {fallback.width()}x{fallback.height()}")
        return fallback

    def minimumSize(self):
        size = QSize()
        for item in self._item_list:
            size = size.expandedTo(item.minimumSize())
        margin = self.contentsMargins()
        size += QSize(2 * margin.left(), 2 * margin.top())
        return size

    def _doLayout(self, rect, testOnly):
        margin = self.contentsMargins()
        x = rect.x() + margin.left()
        y = rect.y() + margin.top()
        lineHeight = 0
        spacing = self.spacing()
        
        # First pass: calculate line heights and collect items per line
        lines = []
        current_line = []
        current_x = x
        current_line_height = 0
        
        for item in self._item_list:
            item_width = item.sizeHint().width()
            item_height = item.sizeHint().height()
            
            nextX = current_x + item_width + spacing
            if nextX - spacing > rect.right() and current_line:
                # Finish current line and start new one
                lines.append((current_line, current_line_height))
                current_line = [item]
                current_x = x + item_width + spacing
                current_line_height = item_height
            else:
                # Add to current line
                current_line.append(item)
                current_x = nextX
                current_line_height = max(current_line_height, item_height)
        
        if current_line:
            lines.append((current_line, current_line_height))
        
        # Second pass: position items with bottom alignment
        current_y = y
        for line_items, line_height in lines:
            current_x = x
            for item in line_items:
                if not testOnly:
                    item_height = item.sizeHint().height()
                    # Position item at bottom of line (bottom alignment)
                    item_y = current_y + line_height - item_height
                    item.setGeometry(QRect(QPoint(current_x, item_y), item.sizeHint()))
                
                current_x += item.sizeHint().width() + spacing
            
            current_y += line_height + spacing
        
        # Calculate final height excluding the last spacing
        if lines:
            final_height = current_y - y - spacing  # Remove the extra spacing after last line
        else:
            final_height = 0
        
        total_height = final_height + margin.bottom()
        
        return total_height

