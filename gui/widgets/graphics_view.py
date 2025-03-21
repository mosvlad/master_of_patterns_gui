"""
Graphics view widget for pattern visualization.
"""
from PyQt5.QtWidgets import QGraphicsView
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QPainter


class PatternGraphicsView(QGraphicsView):
    """Custom QGraphicsView with enhanced zooming and navigation"""

    def __init__(self, parent=None):
        """
        Initialize the graphics view
        
        Args:
            parent: Parent widget
        """
        super().__init__(parent)
        self.setRenderHint(QPainter.Antialiasing)

        # Always enable drag mode regardless of zoom level
        self.setDragMode(QGraphicsView.ScrollHandDrag)

        # These settings help with smoother zooming behavior
        self.setTransformationAnchor(QGraphicsView.AnchorUnderMouse)
        self.setResizeAnchor(QGraphicsView.AnchorUnderMouse)

        # Optional: Enable mouse tracking for better interaction feedback
        self.setMouseTracking(True)

        # Optional: Set viewport update mode for smoother updates during interaction
        self.setViewportUpdateMode(QGraphicsView.SmartViewportUpdate)

        # Set a reasonable minimum size
        self.setMinimumSize(300, 200)

        # Track if we're currently panning
        self._panning = False
        self._pan_start_x = 0
        self._pan_start_y = 0

    def wheelEvent(self, event):
        """
        Handle mouse wheel zoom events
        
        Args:
            event: Wheel event
        """
        factor = 1.1
        if event.angleDelta().y() < 0:
            factor = 1.0 / factor
        self.scale(factor, factor)

    def mousePressEvent(self, event):
        """
        Handle mouse press events for panning
        
        Args:
            event: Mouse event
        """
        if event.button() == Qt.MiddleButton:
            # Middle mouse button can also be used for panning
            self._panning = True
            self._pan_start_x = event.x()
            self._pan_start_y = event.y()
            self.setCursor(Qt.ClosedHandCursor)
            event.accept()
        else:
            # For left button, use the built-in panning through ScrollHandDrag
            super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        """
        Handle mouse move events for custom panning
        
        Args:
            event: Mouse event
        """
        if self._panning:
            # Calculate how much to pan
            dx = event.x() - self._pan_start_x
            dy = event.y() - self._pan_start_y

            # Update the start position for next move
            self._pan_start_x = event.x()
            self._pan_start_y = event.y()

            # Pan the view
            self.horizontalScrollBar().setValue(self.horizontalScrollBar().value() - dx)
            self.verticalScrollBar().setValue(self.verticalScrollBar().value() - dy)

            event.accept()
        else:
            super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        """
        Handle mouse release events
        
        Args:
            event: Mouse event
        """
        if event.button() == Qt.MiddleButton and self._panning:
            self._panning = False
            self.setCursor(Qt.ArrowCursor)
            event.accept()
        else:
            super().mouseReleaseEvent(event)

    def keyPressEvent(self, event):
        """
        Handle key press events for additional navigation
        
        Args:
            event: Key event
        """
        # Add keyboard navigation (arrow keys)
        if event.key() == Qt.Key_Left:
            self.horizontalScrollBar().setValue(self.horizontalScrollBar().value() - 20)
        elif event.key() == Qt.Key_Right:
            self.horizontalScrollBar().setValue(self.horizontalScrollBar().value() + 20)
        elif event.key() == Qt.Key_Up:
            self.verticalScrollBar().setValue(self.verticalScrollBar().value() - 20)
        elif event.key() == Qt.Key_Down:
            self.verticalScrollBar().setValue(self.verticalScrollBar().value() + 20)
        else:
            super().keyPressEvent(event)