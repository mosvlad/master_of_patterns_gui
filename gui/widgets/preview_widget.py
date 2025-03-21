"""
Pattern preview widget for showing small pattern piece previews.
"""
from PyQt5.QtWidgets import QWidget
from PyQt5.QtGui import QPainter, QBrush, QPen
from PyQt5.QtCore import Qt


class PatternPreviewWidget(QWidget):
    """Widget to display a preview of a pattern piece"""

    def __init__(self, parent=None):
        """
        Initialize the pattern preview widget
        
        Args:
            parent: Parent widget
        """
        super().__init__(parent)
        self.setMinimumSize(60, 60)
        self.setMaximumSize(60, 60)  # Fix maximum size to ensure it fits in the cell
        self.pattern_path = None
        self.color = Qt.red

    def set_pattern(self, path, color=None):
        """
        Set the pattern path to display
        
        Args:
            path: QPainterPath for the pattern
            color: Optional color for the pattern
        """
        self.pattern_path = path
        if color:
            self.color = color
        self.update()

    def paintEvent(self, event):
        """
        Paint the pattern preview
        
        Args:
            event: Paint event
        """
        if not self.pattern_path:
            return

        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        # Fill background with white for better contrast
        painter.fillRect(self.rect(), Qt.white)

        # Calculate scaling to fit the widget with padding
        bounds = self.pattern_path.boundingRect()
        if bounds.width() <= 0 or bounds.height() <= 0:
            return

        # Add padding (reduce usable area to 90% of widget size)
        padding = 3
        usable_width = self.width() - (padding * 2)
        usable_height = self.height() - (padding * 2)

        scale_x = usable_width / bounds.width() if bounds.width() > 0 else 1
        scale_y = usable_height / bounds.height() if bounds.height() > 0 else 1
        scale = min(scale_x, scale_y)  # Use smaller scale to maintain aspect ratio

        # Center the pattern
        painter.translate(
            self.width() / 2 - (bounds.width() * scale) / 2 - bounds.x() * scale,
            self.height() / 2 - (bounds.height() * scale) / 2 - bounds.y() * scale
        )
        painter.scale(scale, scale)

        # Draw the pattern with thin pen and dotted pattern fill (like in the reference image)
        pen = QPen(self.color)
        pen.setWidthF(0.8 / scale)  # Thinner pen width for clearer preview
        painter.setPen(pen)

        # Use a dotted pattern fill for better visibility - matching the reference images
        pattern = Qt.Dense4Pattern
        brush = QBrush(self.color, pattern)
        painter.fillPath(self.pattern_path, brush)
        painter.drawPath(self.pattern_path)