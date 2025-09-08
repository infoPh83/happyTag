from PyQt5.QtWidgets import QWidget
from PyQt5.QtGui import QPainter, QColor
from PyQt5.QtCore import QSize

class CloudinaryCreditsBar(QWidget):
    """Custom widget to display a segmented bar for credits."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.storage = 30
        self.utilities = 20
        self.usage = 25
        self.storage_color = QColor(255, 0, 0)  # Default color for storage
        self.utilities_color = QColor('orange')  # Default color for utilities
        self.usage_color = QColor('yellow')  # Default color for usage

    def sizeHint(self):
        """Provide a preferred size hint for the widget - dynamic based on font metrics."""
        # Use font metrics to determine a reasonable height
        font_metrics = self.fontMetrics()
        preferred_height = font_metrics.height() * 2  # About 2 lines of text height
        return QSize(200, preferred_height)  # Reasonable minimum width, dynamic height
    
    def minimumSizeHint(self):
        """Provide a minimum size hint for the widget - very minimal."""
        font_metrics = self.fontMetrics()
        min_height = font_metrics.height()  # At least one line of text height
        return QSize(100, min_height)  # Very minimal constraints



    def setPercentages(self, storage, utilities, usage):

        """Update the percentages and refresh the widget."""

        self.storage = storage

        self.utilities = utilities

        self.usage = usage

        self.update()



    def setColors(self, storage_color, utilities_color, usage_color):

        """Update the colors of the segments and refresh the widget."""

        self.storage_color = QColor(storage_color)

        self.utilities_color = QColor(utilities_color)

        self.usage_color = QColor(usage_color)

        self.update()



    def paintEvent(self, event):

        painter = QPainter(self)

        width = self.width()

        height = self.height()



        factor = width / 100.0

        storage_width = self.storage * factor

        utilities_width = self.utilities * factor

        usage_width = self.usage * factor

        empty_width = max(width - (storage_width + utilities_width + usage_width), 0)



        x = 0

        painter.setBrush(self.storage_color)

        painter.drawRect(x, 0, int(storage_width), height)

        x += int(storage_width)



        painter.setBrush(self.utilities_color)

        painter.drawRect(x, 0, int(utilities_width), height)

        x += int(utilities_width)



        painter.setBrush(self.usage_color)

        painter.drawRect(x, 0, int(usage_width), height)

        x += int(usage_width)



        painter.setBrush(QColor('lightgray'))

        painter.drawRect(x, 0, int(empty_width), height)

