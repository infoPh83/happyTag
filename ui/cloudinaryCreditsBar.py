from PyQt5.QtWidgets import QWidget
from PyQt5.QtGui import QPainter, QColor, QPixmap
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
        
        # Caching mechanism to prevent unnecessary repaints
        self._last_values = None
        self._last_size = None
        self._cached_pixmap = None
        self._debug_paint_count = 0

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
        
        # Check if values actually changed
        new_values = (storage, utilities, usage)
        if self._last_values == new_values:
            # Values haven't changed, no need to repaint
            return
        
        print(f"[DEBUG] CloudinaryCreditsBar.setPercentages() called:")
        print(f"  Storage: {storage} (type: {type(storage)})")
        print(f"  Utilities: {utilities} (type: {type(utilities)})")
        print(f"  Usage: {usage} (type: {type(usage)})")

        self.storage = storage
        self.utilities = utilities
        self.usage = usage
        
        # Invalidate cache since values changed
        self._last_values = new_values
        self._cached_pixmap = None
        
        print(f"[DEBUG] CloudinaryCreditsBar values updated - Storage: {self.storage}, Utilities: {self.utilities}, Usage: {self.usage}")

        self.update()



    def setColors(self, storage_color, utilities_color, usage_color):
        """Update the colors of the segments and refresh the widget."""
        
        print(f"[DEBUG] CloudinaryCreditsBar.setColors() called:")
        print(f"  Storage color: {storage_color}")
        print(f"  Utilities color: {utilities_color}")
        print(f"  Usage color: {usage_color}")

        self.storage_color = QColor(storage_color)
        self.utilities_color = QColor(utilities_color)
        self.usage_color = QColor(usage_color)
        
        # Invalidate cache since colors changed
        self._cached_pixmap = None
        
        print(f"[DEBUG] CloudinaryCreditsBar colors updated successfully")

        self.update()



    def paintEvent(self, event):
        """Paint the credits bar with intelligent caching to avoid unnecessary work."""
        
        current_size = (self.width(), self.height())
        current_values = (self.storage, self.utilities, self.usage)
        
        # Check if we can use cached version
        if (self._cached_pixmap is not None and 
            self._last_size == current_size and 
            self._last_values == current_values):
            # Use cached pixmap - much faster
            painter = QPainter(self)
            painter.drawPixmap(0, 0, self._cached_pixmap)
            return
        
        # Cache miss - need to repaint
        self._debug_paint_count += 1
        
        # Only show debug info occasionally to reduce spam
        if self._debug_paint_count <= 3 or self._debug_paint_count % 10 == 0:
            print(f"[DEBUG] CloudinaryCreditsBar.paintEvent() #{self._debug_paint_count}")
            print(f"  Values - Storage: {self.storage}%, Utilities: {self.utilities}%, Usage: {self.usage}%")
            print(f"  Size: {self.width()}x{self.height()}")
        
        # Create new cached pixmap
        self._cached_pixmap = QPixmap(self.width(), self.height())
        self._cached_pixmap.fill(self.palette().color(self.backgroundRole()))
        
        # Paint to the cached pixmap
        painter = QPainter(self._cached_pixmap)
        
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
        
        painter.end()
        
        # Update cache state
        self._last_size = current_size
        self._last_values = current_values
        
        # Now draw the cached pixmap to the widget
        widget_painter = QPainter(self)
        widget_painter.drawPixmap(0, 0, self._cached_pixmap)
        
        if self._debug_paint_count <= 3 or self._debug_paint_count % 10 == 0:
            print(f"[DEBUG] CloudinaryCreditsBar painting completed (cached)")
    
    def resizeEvent(self, event):
        """Handle resize events by invalidating the cache."""
        super().resizeEvent(event)
        # Invalidate cache when widget is resized
        self._cached_pixmap = None

