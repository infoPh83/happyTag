from PyQt5.QtWidgets import QWidget, QPushButton, QSizePolicy
from PyQt5.QtGui import QPalette, QColor
from PyQt5.QtCore import Qt

class TagButton(QPushButton):
    def __init__(self, text, color, parent=None):
        super().__init__(text, parent)
        self.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        
        print(f"[DEBUG TagButton] Creating TagButton with text='{text}', color='{color}'")
        
        # Set background color with some transparency
        bg_color = QColor(color)
        bg_color.setAlpha(180)  # 70% opacity
        
        hover_color = QColor(color)
        hover_color.setAlpha(230)  # 90% opacity
        
        print(f"[DEBUG TagButton] bg_color={bg_color.name(QColor.HexArgb)}, hover_color={hover_color.name(QColor.HexArgb)}")
        
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
        return height

    def setGeometry(self, rect):
        super().setGeometry(rect)
        self._doLayout(rect, False)

    def sizeHint(self):
        return self.minimumSize()

    def minimumSize(self):
        size = QSize()
        for item in self._item_list:
            size = size.expandedTo(item.minimumSize())
        margin = self.contentsMargins()
        size += QSize(2 * margin.top(), 2 * margin.bottom())
        return size

    def _doLayout(self, rect, testOnly):
        margin = self.contentsMargins()
        x = rect.x() + margin.left()
        y = rect.y() + margin.top()
        lineHeight = 0
        spacing = self.spacing()

        for item in self._item_list:
            widget = item.widget()
            spaceX = spacing
            spaceY = spacing

            nextX = x + item.sizeHint().width() + spaceX
            if nextX - spaceX > rect.right() and lineHeight > 0:
                x = rect.x() + margin.left()
                y = y + lineHeight + spaceY
                nextX = x + item.sizeHint().width() + spaceX
                lineHeight = 0

            if not testOnly:
                item.setGeometry(QRect(QPoint(x, y), item.sizeHint()))

            x = nextX
            lineHeight = max(lineHeight, item.sizeHint().height())

        return y + lineHeight - rect.y() + margin.bottom()
        
        for widget in widgets:
            widget_width = widget.sizeHint().width()
            widget_height = widget.sizeHint().height()
            
            if x + widget_width > self.width():
                # Move to next line
                x = 0
                y += line_height + spacing
                line_height = 0
                
            widget.setGeometry(x, y, widget_width, widget_height)
            x += widget_width + spacing
            line_height = max(line_height, widget_height)
