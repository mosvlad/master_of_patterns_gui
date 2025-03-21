"""
Main window for pattern nesting application.
"""
import os
import re
import subprocess
import time
from PyQt5.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
                           QLabel, QPushButton, QFileDialog, QGraphicsScene, QGraphicsPathItem,
                           QTableWidget, QTableWidgetItem, QTabWidget,
                           QLineEdit, QGroupBox, QFormLayout, QCheckBox, QSpinBox, QDoubleSpinBox,
                           QMessageBox, QStatusBar, QAction, QToolBar, QSplitter, QFrame,
                           QGraphicsItemGroup, QDialog, QProgressBar, QApplication)
from PyQt5.QtGui import QPen, QBrush, QPainterPath, QColor, QFont, QIcon, QPainter, QPixmap, QTransform
from PyQt5.QtCore import Qt, QPointF, QRectF, QSizeF, QTimer

import ezdxf

from core.parser import parse_ses_file
from core.settings import SettingsManager
from gui.widgets.graphics_view import PatternGraphicsView
from gui.widgets.preview_widget import PatternPreviewWidget
from gui.process_manager import NestingProcessManager


class PatternNestingApp(QMainWindow):
    """Main application window for pattern nesting tool"""
    
    def __init__(self):
        """Initialize the application"""
        super().__init__()

        # Application state
        self.dxf_file_path = None
        self.nesting_program_path = None
        self.wrk_file_path = None
        self.blocks = []  # Store the blocks from the DXF file
        self.entities = []  # Store direct entities from the DXF file
        self.pattern_paths = []  # Store QPainterPath objects for each pattern
        self.pattern_colors = []  # Store colors for each pattern

        # Store a single instance of the process manager
        self.process_manager = None
        
        # Initialize settings manager
        self.settings_manager = SettingsManager()

        # Initialize the user interface
        self.init_ui()

        # Load settings
        self.load_settings()

    def open_process_manager(self):
        """Open the nesting process manager"""
        # Create the process manager if it doesn't exist yet
        if self.process_manager is None:
            self.process_manager = NestingProcessManager(self)

            # Pass the nesting program path if available
            if self.nesting_program_path:
                self.process_manager.nesting_program = self.nesting_program_path

        # Show the existing process manager
        self.process_manager.show()
        self.process_manager.activateWindow()  # Bring to front
        self.process_manager.raise_()  # Ensure it's on top

    def init_ui(self):
        """Initialize the user interface"""
        self.setWindowTitle("Pattern Nesting Tool")
        self.setGeometry(100, 100, 1200, 800)

        # Create central widget and main layout
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.main_layout = QVBoxLayout(self.central_widget)

        # Create toolbar
        self.create_toolbar()

        # Create splitter for resizable panels
        self.splitter = QSplitter(Qt.Horizontal)
        self.main_layout.addWidget(self.splitter)

        # Create left panel with controls
        self.left_panel = QWidget()
        self.left_layout = QVBoxLayout(self.left_panel)

        # File paths group
        self.paths_group = QGroupBox("File Paths")
        paths_layout = QFormLayout()

        # DXF file selection
        self.dxf_path_edit = QLineEdit()
        self.dxf_path_edit.setReadOnly(True)
        self.dxf_browse_btn = QPushButton("Browse...")
        self.dxf_browse_btn.clicked.connect(self.browse_dxf_file)
        dxf_layout = QHBoxLayout()
        dxf_layout.addWidget(self.dxf_path_edit)
        dxf_layout.addWidget(self.dxf_browse_btn)
        paths_layout.addRow("DXF File:", dxf_layout)

        # Nesting program selection
        self.nesting_path_edit = QLineEdit()
        self.nesting_path_edit.setReadOnly(True)
        self.nesting_browse_btn = QPushButton("Browse...")
        self.nesting_browse_btn.clicked.connect(self.browse_nesting_program)
        nesting_layout = QHBoxLayout()
        nesting_layout.addWidget(self.nesting_path_edit)
        nesting_layout.addWidget(self.nesting_browse_btn)
        paths_layout.addRow("Nesting Program:", nesting_layout)

        # WRK file path
        self.wrk_path_edit = QLineEdit()
        self.wrk_path_edit.setReadOnly(True)
        self.wrk_browse_btn = QPushButton("Browse...")
        self.wrk_browse_btn.clicked.connect(self.browse_wrk_file)
        wrk_layout = QHBoxLayout()
        wrk_layout.addWidget(self.wrk_path_edit)
        wrk_layout.addWidget(self.wrk_browse_btn)
        paths_layout.addRow("WRK File:", wrk_layout)

        self.paths_group.setLayout(paths_layout)
        self.left_layout.addWidget(self.paths_group)

        # Nesting parameters group
        self.params_group = QGroupBox("Nesting Parameters")
        params_layout = QFormLayout()

        # Width
        self.width_spin = QDoubleSpinBox()
        self.width_spin.setRange(1, 1000)
        self.width_spin.setValue(50)
        self.width_spin.setSingleStep(1)
        self.width_spin.setSuffix(" cm")
        params_layout.addRow("Width:", self.width_spin)

        # Efficiency target
        self.efficiency_spin = QDoubleSpinBox()
        self.efficiency_spin.setRange(0, 100)
        self.efficiency_spin.setValue(80)
        self.efficiency_spin.setSingleStep(5)
        self.efficiency_spin.setSuffix(" %")
        params_layout.addRow("Min Efficiency:", self.efficiency_spin)

        # Time limit
        self.time_spin = QSpinBox()
        self.time_spin.setRange(1, 300)
        self.time_spin.setValue(1)
        self.time_spin.setSuffix(" min")
        params_layout.addRow("Time Limit:", self.time_spin)

        # Horizontal/Vertical flip
        self.h_flip_check = QCheckBox("Horizontal Flip")
        self.v_flip_check = QCheckBox("Vertical Flip")
        params_layout.addRow("Flip Options:", self.h_flip_check)
        params_layout.addRow("", self.v_flip_check)

        self.params_group.setLayout(params_layout)
        self.left_layout.addWidget(self.params_group)

        # Action buttons
        self.actions_group = QGroupBox("Actions")
        actions_layout = QVBoxLayout()

        self.load_btn = QPushButton("Load DXF")
        self.load_btn.clicked.connect(self.load_dxf)
        actions_layout.addWidget(self.load_btn)

        self.gen_wrk_btn = QPushButton("Generate WRK File")
        self.gen_wrk_btn.clicked.connect(self.generate_wrk_file)
        actions_layout.addWidget(self.gen_wrk_btn)

        self.run_btn = QPushButton("Run Nesting Program")
        self.run_btn.clicked.connect(self.run_nesting_program)
        self.run_btn.setEnabled(False)
        actions_layout.addWidget(self.run_btn)

        self.actions_group.setLayout(actions_layout)
        self.left_layout.addWidget(self.actions_group)

        # Add a spacer to push everything up
        self.left_layout.addStretch()

        # Create right panel with visualization
        self.right_panel = QTabWidget()

        # Create graphics view for pattern display
        self.view = PatternGraphicsView()
        self.scene = QGraphicsScene()
        self.view.setScene(self.scene)

        # Add pattern view to tab widget
        self.right_panel.addTab(self.view, "Pattern Pieces")

        # Create table for pattern information
        self.pattern_table = QTableWidget()
        self.pattern_table.setColumnCount(5)
        self.pattern_table.setHorizontalHeaderLabels(["ID", "Name", "Preview", "Area", "Perimeter"])
        self.right_panel.addTab(self.pattern_table, "Pattern Data")

        # Add a tab for nesting results
        self.nesting_result_view = PatternGraphicsView()
        self.nesting_result_scene = QGraphicsScene()
        self.nesting_result_view.setScene(self.nesting_result_scene)
        self.right_panel.addTab(self.nesting_result_view, "Nesting Result")

        # Add panels to splitter
        self.splitter.addWidget(self.left_panel)
        self.splitter.addWidget(self.right_panel)
        self.splitter.setSizes([300, 900])  # Initial sizing

        # Create status bar
        self.statusBar = QStatusBar()
        self.setStatusBar(self.statusBar)
        self.statusBar.showMessage("Ready")

    def create_toolbar(self):
        """Create the application toolbar"""
        toolbar = QToolBar("Main Toolbar")
        self.addToolBar(toolbar)

        # Load action
        load_action = QAction("Load DXF", self)
        load_action.triggered.connect(self.browse_dxf_file)
        toolbar.addAction(load_action)

        toolbar.addSeparator()

        # Zoom actions
        zoom_in_action = QAction("Zoom In", self)
        zoom_in_action.triggered.connect(self.zoom_in)
        toolbar.addAction(zoom_in_action)

        zoom_out_action = QAction("Zoom Out", self)
        zoom_out_action.triggered.connect(self.zoom_out)
        toolbar.addAction(zoom_out_action)

        zoom_fit_action = QAction("Fit View", self)
        zoom_fit_action.triggered.connect(self.zoom_fit)
        toolbar.addAction(zoom_fit_action)

        toolbar.addSeparator()

        # Run action
        run_action = QAction("Run Nesting", self)
        run_action.triggered.connect(self.run_nesting_program)
        toolbar.addAction(run_action)

        toolbar.addSeparator()

        # Load nesting result action
        load_result_action = QAction("Load Nesting Result", self)
        load_result_action.triggered.connect(self.load_nesting_result)
        toolbar.addAction(load_result_action)

        toolbar.addSeparator()

        # Process manager
        process_manager_action = QAction("Process Manager", self)
        process_manager_action.triggered.connect(self.open_process_manager)
        toolbar.addAction(process_manager_action)

    def zoom_in(self):
        """Zoom in on the view"""
        current_tab = self.right_panel.currentWidget()
        if isinstance(current_tab, PatternGraphicsView):
            current_tab.scale(1.1, 1.1)
        else:
            self.view.scale(1.1, 1.1)

    def zoom_out(self):
        """Zoom out of the view"""
        current_tab = self.right_panel.currentWidget()
        if isinstance(current_tab, PatternGraphicsView):
            current_tab.scale(0.9, 0.9)
        else:
            self.view.scale(0.9, 0.9)

    def zoom_fit(self):
        """Fit all pattern pieces in view"""
        current_tab = self.right_panel.currentWidget()
        if isinstance(current_tab, PatternGraphicsView):
            if current_tab.scene().items():
                current_tab.fitInView(current_tab.scene().itemsBoundingRect(), Qt.KeepAspectRatio)
        elif self.scene.items():
            self.view.fitInView(self.scene.itemsBoundingRect(), Qt.KeepAspectRatio)

    def browse_dxf_file(self):
        """Open file dialog to select DXF file"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Select DXF File", "", "DXF Files (*.dxf)"
        )
        if file_path:
            self.dxf_file_path = file_path
            self.dxf_path_edit.setText(file_path)
            self.statusBar.showMessage(f"DXF file selected: {os.path.basename(file_path)}")
            
            # Add to recent files
            if hasattr(self, 'settings_manager'):
                self.settings_manager.add_recent_file(file_path)

    def browse_nesting_program(self):
        """Open file dialog to select nesting program executable"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Select Nesting Program", "", "Executable Files (*.exe)"
        )
        if file_path:
            self.nesting_program_path = file_path
            self.nesting_path_edit.setText(file_path)
            self.statusBar.showMessage(f"Nesting program selected: {os.path.basename(file_path)}")
            self.save_settings()

    def browse_wrk_file(self):
        """Open file dialog to select WRK file location"""
        file_path, _ = QFileDialog.getSaveFileName(
            self, "Select WRK File Location", "", "WRK Files (*.wrk)"
        )
        if file_path:
            if not file_path.lower().endswith('.wrk'):
                file_path += '.wrk'
            self.wrk_file_path = file_path
            self.wrk_path_edit.setText(file_path)
            self.statusBar.showMessage(f"WRK file location: {os.path.basename(file_path)}")

    def load_dxf(self):
        """Load and parse DXF file"""
        if not self.dxf_file_path:
            QMessageBox.warning(self, "Warning", "Please select a DXF file first.")
            return

        self.statusBar.showMessage("Loading DXF file...")
        try:
            # Load the DXF file
            doc = ezdxf.readfile(self.dxf_file_path)

            # Clear previous display
            self.scene.clear()
            self.blocks = []
            self.entities = []
            self.pattern_paths = []
            self.pattern_colors = []

            # Debug info
            print(f"DXF version: {doc.dxfversion}")
            print(f"Number of entities in modelspace: {len(doc.modelspace())}")
            print(f"Number of blocks: {len(doc.blocks)}")

            # List block names
            print("Available blocks:")
            for block in doc.blocks:
                print(f"  - {block.name}")

            # Get all blocks from the DXF
            for block in doc.blocks:
                # Skip model space
                if block.name.lower() in ('*model_space', '*paper_space', '$model_space', '$paper_space'):
                    continue

                # In your file, blocks appear to start with 'B'
                if block.name.startswith('B'):
                    self.blocks.append(block)
                    print(f"Adding block: {block.name} with {len(block)} entities")

            # If no blocks found, try to use entities directly from modelspace
            if not self.blocks:
                print("No blocks found, checking modelspace entities")
                for entity in doc.modelspace():
                    if entity.dxftype() in ('POLYLINE', 'LWPOLYLINE', 'LINE', 'SPLINE', 'HATCH'):
                        self.entities.append(entity)
                        print(f"Adding entity: {entity.dxftype()}")

            # Display blocks and entities
            if self.blocks or self.entities:
                self.extract_and_display_patterns()
                self.populate_table()
                total_items = len(self.pattern_paths)
                self.statusBar.showMessage(f"Loaded {total_items} pattern pieces")

                # Enable run button if we have a nesting program and wrk file
                if self.nesting_program_path and self.wrk_file_path:
                    self.run_btn.setEnabled(True)

                # Switch to Pattern Pieces tab
                self.right_panel.setCurrentIndex(0)
            else:
                self.statusBar.showMessage("No pattern pieces found in DXF file")

        except Exception as e:
            import traceback
            traceback.print_exc()
            QMessageBox.critical(self, "Error", f"Failed to load DXF file: {str(e)}")
            self.statusBar.showMessage("Error loading DXF file")

    def extract_and_display_patterns(self):
        """Extract patterns from blocks/entities and display them"""
        # Define a grid for pattern arrangement
        grid_spacing = 5  # Spacing between patterns (integer)
        grid_columns = 8  # Number of columns in the grid
        max_width = 0
        max_height = 0

        # Add grid to scene for reference
        self.add_grid_to_scene(self.scene)

        # Process blocks and extract patterns
        colors = [Qt.red, Qt.blue, Qt.green, Qt.magenta, Qt.darkCyan, Qt.darkRed, Qt.darkBlue, Qt.darkGreen]

        # Extract patterns from blocks and entities
        self.extract_patterns_from_blocks(colors)

        # Arrange patterns in a grid
        margin_x = grid_spacing
        margin_y = grid_spacing
        curr_x = margin_x
        curr_y = margin_y
        row_height = 0

        # Display patterns in a grid layout
        for i, pattern_path in enumerate(self.pattern_paths):
            color = self.pattern_colors[i]

            # Create graphics item for the pattern
            path_item = QGraphicsPathItem(pattern_path)
            path_item.setPen(QPen(color, 0.5))
            path_item.setBrush(QBrush(color, Qt.Dense4Pattern))

            # Position the pattern in the grid
            path_bounds = pattern_path.boundingRect()

            # Adjust row height if needed
            row_height = max(row_height, path_bounds.height() + grid_spacing)

            # Check if we need to move to a new row
            if (i > 0) and (i % grid_columns == 0):
                curr_y += row_height
                curr_x = margin_x
                row_height = path_bounds.height() + grid_spacing

            # Position the pattern
            path_item.setPos(curr_x, curr_y)

            # Add to scene
            self.scene.addItem(path_item)

            # Update position for next pattern
            curr_x += path_bounds.width() + grid_spacing

            # Track maximum dimensions
            max_width = max(max_width, curr_x)
            max_height = max(max_height, curr_y + row_height)

        # Set scene rectangle to contain all patterns
        self.scene.setSceneRect(0, 0, max_width + margin_x, max_height + margin_y)

        # Fit view to show all patterns
        self.view.fitInView(self.scene.sceneRect(), Qt.KeepAspectRatio)

    def extract_patterns_from_blocks(self, colors):
        """
        Extract pattern paths from blocks and entities
        
        Args:
            colors: List of colors to use for patterns
        """
        # Process blocks
        for i, block in enumerate(self.blocks):
            color = colors[i % len(colors)]

            # Create path for the block
            path = QPainterPath()
            is_path_started = False

            # Calculate bounding box for Y-axis flipping
            min_y = float('inf')
            max_y = float('-inf')
            all_vertices = []

            # First pass - collect all vertices and find min/max Y
            for entity in block:
                entity_type = entity.dxftype()
                if entity_type in ('POLYLINE', 'LWPOLYLINE'):
                    vertices = self.extract_vertices(entity)
                    if vertices:
                        for x, y in vertices:
                            min_y = min(min_y, y)
                            max_y = max(max_y, y)
                        all_vertices.append((entity_type, vertices, self.is_entity_closed(entity)))
                elif entity_type == 'LINE':
                    try:
                        start = entity.dxf.start
                        end = entity.dxf.end
                        min_y = min(min_y, start[1], end[1])
                        max_y = max(max_y, start[1], end[1])
                        all_vertices.append((entity_type, [start, end], False))
                    except:
                        pass

            # If we have valid bounds
            if min_y != float('inf') and max_y != float('-inf'):
                # Second pass - create the path with flipped Y coordinates
                for entity_type, vertices, is_closed in all_vertices:
                    if entity_type in ('POLYLINE', 'LWPOLYLINE') and len(vertices) > 1:
                        # Flip Y coordinates (max_y + min_y - y will flip around the center of the pattern)
                        flipped_vertices = [(x, max_y + min_y - y) for x, y in vertices]

                        # Start a new subpath if needed
                        if not is_path_started:
                            path.moveTo(flipped_vertices[0][0], flipped_vertices[0][1])
                            is_path_started = True
                        else:
                            path.moveTo(flipped_vertices[0][0], flipped_vertices[0][1])

                        # Add remaining vertices
                        for vertex in flipped_vertices[1:]:
                            path.lineTo(vertex[0], vertex[1])

                        # Close the path if entity is closed
                        if is_closed:
                            path.closeSubpath()

                    elif entity_type == 'LINE':
                        start, end = vertices
                        # Flip Y coordinates
                        start_flipped = (start[0], max_y + min_y - start[1])
                        end_flipped = (end[0], max_y + min_y - end[1])

                        if not is_path_started:
                            path.moveTo(start_flipped[0], start_flipped[1])
                            is_path_started = True
                        else:
                            path.moveTo(start_flipped[0], start_flipped[1])

                        path.lineTo(end_flipped[0], end_flipped[1])

                # Add the path to our collection if it contains data
                if not path.isEmpty():
                    self.pattern_paths.append(path)
                    self.pattern_colors.append(color)
            else:
                # No valid geometry found, try legacy approach (shouldn't happen often)
                path = QPainterPath()
                is_path_started = False

                # Process entities in the block
                for entity in block:
                    entity_type = entity.dxftype()

                    if entity_type in ('POLYLINE', 'LWPOLYLINE'):
                        # Extract vertices
                        vertices = self.extract_vertices(entity)

                        if vertices and len(vertices) > 1:
                            # Start a new subpath if needed
                            if not is_path_started:
                                path.moveTo(vertices[0][0], vertices[0][1])
                                is_path_started = True
                            else:
                                path.moveTo(vertices[0][0], vertices[0][1])

                            # Add remaining vertices
                            for vertex in vertices[1:]:
                                path.lineTo(vertex[0], vertex[1])

                            # Close the path if entity is closed
                            if self.is_entity_closed(entity):
                                path.closeSubpath()

                    elif entity_type == 'LINE':
                        try:
                            start = entity.dxf.start
                            end = entity.dxf.end

                            if not is_path_started:
                                path.moveTo(start[0], start[1])
                                is_path_started = True
                            else:
                                path.moveTo(start[0], start[1])

                            path.lineTo(end[0], end[1])
                        except:
                            pass

                # Add the path to our collection if it contains data
                if not path.isEmpty():
                    self.pattern_paths.append(path)
                    self.pattern_colors.append(color)

        # Process direct entities
        for i, entity in enumerate(self.entities):
            color = colors[(i + len(self.blocks)) % len(colors)]
            entity_type = entity.dxftype()

            if entity_type in ('POLYLINE', 'LWPOLYLINE'):
                path = QPainterPath()
                vertices = self.extract_vertices(entity)

                if vertices and len(vertices) > 1:
                    # Calculate min/max Y for flipping
                    min_y = min(y for _, y in vertices)
                    max_y = max(y for _, y in vertices)

                    # Flip Y coordinates
                    flipped_vertices = [(x, max_y + min_y - y) for x, y in vertices]

                    path.moveTo(flipped_vertices[0][0], flipped_vertices[0][1])

                    for vertex in flipped_vertices[1:]:
                        path.lineTo(vertex[0], vertex[1])

                    if self.is_entity_closed(entity):
                        path.closeSubpath()

                    self.pattern_paths.append(path)
                    self.pattern_colors.append(color)

            elif entity_type == 'LINE':
                try:
                    path = QPainterPath()
                    start = entity.dxf.start
                    end = entity.dxf.end

                    # Flip Y coordinates (simple case for a single line)
                    min_y = min(start[1], end[1])
                    max_y = max(start[1], end[1])

                    start_flipped = (start[0], max_y + min_y - start[1])
                    end_flipped = (end[0], max_y + min_y - end[1])

                    path.moveTo(start_flipped[0], start_flipped[1])
                    path.lineTo(end_flipped[0], end_flipped[1])

                    self.pattern_paths.append(path)
                    self.pattern_colors.append(color)
                except:
                    pass

    def extract_vertices(self, entity):
        """
        Extract vertices from a POLYLINE or LWPOLYLINE entity
        
        Args:
            entity: DXF entity
            
        Returns:
            list: List of (x, y) vertex coordinates
        """
        vertices = []
        try:
            # For LWPOLYLINE
            if entity.dxftype() == 'LWPOLYLINE':
                if hasattr(entity, 'vertices'):
                    if callable(entity.vertices):
                        try:
                            points = list(entity.vertices())
                        except:
                            points = []
                    else:
                        points = entity.vertices
                elif hasattr(entity, 'points'):
                    points = entity.points
                else:
                    # Try to get vertices through DXF properties
                    try:
                        points = list(entity.get_points()) if hasattr(entity, 'get_points') else []
                    except:
                        points = []

                # Process points
                for point in points:
                    if isinstance(point, (list, tuple)) and len(point) >= 2:
                        vertices.append((point[0], point[1]))
                    elif hasattr(point, 'x') and hasattr(point, 'y'):
                        vertices.append((point.x, point.y))

            # For POLYLINE
            elif entity.dxftype() == 'POLYLINE':
                if hasattr(entity, 'vertices'):
                    if callable(entity.vertices):
                        try:
                            points = list(entity.vertices())
                        except:
                            points = []
                    else:
                        points = entity.vertices
                else:
                    # Try to get vertices through child entities
                    points = []
                    try:
                        for vertex_entity in entity.virtual_entities():
                            if vertex_entity.dxftype() == 'VERTEX':
                                points.append(vertex_entity)
                    except:
                        pass

                # Process points
                for point in points:
                    if isinstance(point, (list, tuple)) and len(point) >= 2:
                        vertices.append((point[0], point[1]))
                    elif hasattr(point, 'x') and hasattr(point, 'y'):
                        vertices.append((point.x, point.y))
                    elif hasattr(point, 'dxf') and hasattr(point.dxf, 'location'):
                        loc = point.dxf.location
                        vertices.append((loc.x, loc.y))
        except Exception as e:
            print(f"Error extracting vertices: {e}")

        return vertices

    def is_entity_closed(self, entity):
        """
        Check if a POLYLINE or LWPOLYLINE entity is closed
        
        Args:
            entity: DXF entity
            
        Returns:
            bool: True if entity is closed, False otherwise
        """
        if hasattr(entity, 'is_closed'):
            return entity.is_closed
        elif hasattr(entity, 'closed'):
            return entity.closed
        elif hasattr(entity, 'dxf') and hasattr(entity.dxf, 'flags'):
            # Check flags for closed polyline (flag 1 = closed)
            return bool(entity.dxf.flags & 1)
        return False

    def add_grid_to_scene(self, scene):
        """
        Add a reference grid to the given scene
        
        Args:
            scene: QGraphicsScene to add grid to
        """
        grid_size = 10  # Grid cell size (integer)
        grid_extent = 1000

        # Create light gray dotted lines for grid
        pen = QPen(Qt.lightGray)
        pen.setStyle(Qt.DotLine)
        pen.setWidthF(0.5)

        # Horizontal lines
        for y in range(0, grid_extent, grid_size):
            scene.addLine(0, y, grid_extent, y, pen)

        # Vertical lines
        for x in range(0, grid_extent, grid_size):
            scene.addLine(x, 0, x, grid_extent, pen)

        # Add stronger lines for main axes
        pen = QPen(Qt.darkGray)
        pen.setStyle(Qt.SolidLine)
        pen.setWidthF(1.0)

        # Main horizontal and vertical lines
        scene.addLine(0, 0, grid_extent, 0, pen)  # X-axis
        scene.addLine(0, 0, 0, grid_extent, pen)  # Y-axis

    def populate_table(self):
        """Populate the table with pattern information"""
        total_items = len(self.pattern_paths)

        # Update table columns to include preview
        self.pattern_table.setColumnCount(5)
        self.pattern_table.setHorizontalHeaderLabels(["ID", "Name", "Preview", "Area", "Perimeter"])
        self.pattern_table.setRowCount(total_items)

        # Set row heights to accommodate previews
        for i in range(total_items):
            self.pattern_table.setRowHeight(i, 62)  # Fixed row height

        # Add patterns to table
        for i, pattern_path in enumerate(self.pattern_paths):
            color = self.pattern_colors[i]

            # Get pattern metrics
            area, perimeter = self.calculate_pattern_metrics(pattern_path)

            # Get block name
            block_name = ""
            if i < len(self.blocks):
                block_name = self.get_block_name(self.blocks[i])

            # Add to table
            self.pattern_table.setItem(i, 0, QTableWidgetItem(str(i)))
            self.pattern_table.setItem(i, 1, QTableWidgetItem(str(i)))

            # Create preview widget with container to ensure proper sizing
            preview_container = QWidget()
            preview_layout = QVBoxLayout(preview_container)
            preview_layout.setContentsMargins(1, 1, 1, 1)  # Minimal margins
            preview_layout.setAlignment(Qt.AlignCenter)  # Center the preview in the cell

            preview = PatternPreviewWidget()
            preview.set_pattern(pattern_path, color)

            preview_layout.addWidget(preview)
            self.pattern_table.setCellWidget(i, 2, preview_container)

            # Add area and perimeter
            self.pattern_table.setItem(i, 3, QTableWidgetItem(f"{area:.2f} cm²"))
            self.pattern_table.setItem(i, 4, QTableWidgetItem(f"{perimeter:.2f} cm"))

        # Set column widths
        self.pattern_table.setColumnWidth(0, 40)  # ID column
        self.pattern_table.setColumnWidth(1, 40)  # Name column
        self.pattern_table.setColumnWidth(2, 70)  # Preview column

        # Resize remaining columns to contents
        self.pattern_table.resizeColumnToContents(3)  # Area column
        self.pattern_table.resizeColumnToContents(4)  # Perimeter column

    def calculate_pattern_metrics(self, path):
        """
        Calculate area and perimeter of a pattern path
        
        Args:
            path: QPainterPath object
            
        Returns:
            tuple: (area, perimeter) of the pattern
        """
        try:
            # Extract points from the path
            polygon_points = []
            path_elements = path.elementCount()

            for i in range(path_elements):
                element = path.elementAt(i)
                if element.type == QPainterPath.MoveToElement or element.type == QPainterPath.LineToElement:
                    polygon_points.append((element.x, element.y))

            # Calculate perimeter
            perimeter = 0
            if len(polygon_points) > 1:
                for i in range(len(polygon_points)):
                    next_i = (i + 1) % len(polygon_points)
                    x1, y1 = polygon_points[i]
                    x2, y2 = polygon_points[next_i]

                    # Calculate distance between points
                    dist = ((x2 - x1) ** 2 + (y2 - y1) ** 2) ** 0.5
                    perimeter += dist

            # Calculate area using Shoelace formula
            area = 0
            if len(polygon_points) > 2:
                for i in range(len(polygon_points)):
                    next_i = (i + 1) % len(polygon_points)
                    x1, y1 = polygon_points[i]
                    x2, y2 = polygon_points[next_i]

                    area += x1 * y2 - x2 * y1

                area = abs(area) / 2.0

            # If area calculation fails, use bounding rect approximation
            if area == 0:
                bounds = path.boundingRect()
                area = bounds.width() * bounds.height() * 0.8  # Approximate area
                perimeter = 2 * (bounds.width() + bounds.height())  # Approximate perimeter

            return area, perimeter

        except Exception as e:
            print(f"Error calculating metrics: {e}")
            # Fall back to bounding rectangle approximation
            bounds = path.boundingRect()
            area = bounds.width() * bounds.height() * 0.8  # Approximate area
            perimeter = 2 * (bounds.width() + bounds.height())  # Approximate perimeter

            return area, perimeter

    def get_block_name(self, block):
        """
        Try to extract a name from TEXT entities in the block
        
        Args:
            block: DXF block
            
        Returns:
            str: Name of the block
        """
        for entity in block:
            if entity.dxftype() == 'TEXT':
                try:
                    text = entity.dxf.text
                    if text.startswith('NAME:'):
                        return text.split(':')[1]
                except:
                    pass
        return block.name

    def generate_wrk_file(self):
        """Generate a WRK file for the nesting program"""
        if not self.dxf_file_path:
            QMessageBox.warning(self, "Warning", "Please load a DXF file first.")
            return

        if not self.wrk_file_path:
            # Let user choose a location for the WRK file
            self.browse_wrk_file()
            if not self.wrk_file_path:
                return

        try:
            with open(self.wrk_file_path, 'w') as f:
                f.write("NESTING-WORK-FILE\n")

                # Get directory paths
                dxf_dir = os.path.dirname(self.dxf_file_path)
                wrk_dir = os.path.dirname(self.wrk_file_path)

                # Write file paths
                f.write(f"CHDIR {wrk_dir}\n")
                f.write(f"IMPORT DXF {self.dxf_file_path}\n")
                f.write("BUILD_NEST 0\n")
                f.write("BEGIN_TASK\n")
                f.write(f"MARKER_FILE_DIRECTORY  {wrk_dir}\n")
                f.write(f"SESSION_FILE_DIRECTORY {wrk_dir}\n")

                # Get the filename without extension
                dxf_basename = os.path.splitext(os.path.basename(self.dxf_file_path))[0]

                # Add marker file section
                f.write("BEGIN_MARKER_FILE\n")
                f.write(f"{dxf_basename}.dat\n")
                f.write("END_MARKER_FILE\n")

                # Add automatic actions
                f.write("BEGIN_AUTOMATIC_ACTIONS\n")
                min_eff = int(self.efficiency_spin.value())
                time_limit = int(self.time_spin.value())

                f.write(f"NEST_COMPLETE MIN_EFF={min_eff} MAX_EFF=100 TIME={time_limit} ")
                f.write("NUM_SAVE=1 OPTIONALS=10\n")
                f.write("END_AUTOMATIC_ACTIONS\n")
                f.write("END_TASK\n")

                # Export session file
                ses_file = os.path.join(dxf_dir, f"{dxf_basename}.ses")
                f.write(f"EXPORT dxf {ses_file}\n")
                f.write("END_WORK_FILE\n")

            QMessageBox.information(self, "Success", f"WRK file generated: {self.wrk_file_path}")
            self.statusBar.showMessage(f"WRK file generated: {os.path.basename(self.wrk_file_path)}")

            # Enable run button if we have a nesting program
            if self.nesting_program_path:
                self.run_btn.setEnabled(True)

        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to generate WRK file: {str(e)}")

    def run_nesting_program(self):
        """Run the nesting program with the WRK file"""
        if not self.nesting_program_path:
            QMessageBox.warning(self, "Warning", "Please select the nesting program first.")
            return

        if not self.wrk_file_path:
            self.generate_wrk_file()
            if not self.wrk_file_path:
                return

        try:
            # Create progress dialog
            progress_dialog = QDialog(self)
            progress_dialog.setWindowTitle("Nesting Progress")
            progress_dialog.setMinimumWidth(400)
            progress_dialog.setWindowFlags(progress_dialog.windowFlags() & ~Qt.WindowContextHelpButtonHint)

            # Create layout
            layout = QVBoxLayout(progress_dialog)

            # Add status label
            status_label = QLabel("Initializing nesting process...")
            status_label.setAlignment(Qt.AlignCenter)
            layout.addWidget(status_label)

            # Add progress bar
            progress_bar = QProgressBar()
            progress_bar.setRange(0, 100)
            progress_bar.setValue(0)
            layout.addWidget(progress_bar)

            # Add time elapsed label
            time_label = QLabel("Time elapsed: 0:00")
            time_label.setAlignment(Qt.AlignCenter)
            layout.addWidget(time_label)

            # Add info text area
            info_text = QLabel("Preparing to run nesting program...\n")
            info_text.setAlignment(Qt.AlignLeft | Qt.AlignTop)
            info_text.setWordWrap(True)
            info_text.setMinimumHeight(100)
            info_text.setFrameStyle(QFrame.Panel | QFrame.Sunken)
            layout.addWidget(info_text)

            # Add button box
            button_layout = QHBoxLayout()
            stop_button = QPushButton("Stop")
            stop_button.clicked.connect(progress_dialog.reject)
            button_layout.addStretch()
            button_layout.addWidget(stop_button)
            layout.addLayout(button_layout)

            # Show the dialog but don't block execution
            progress_dialog.show()
            QApplication.processEvents()

            # Initialize timer for tracking elapsed time
            start_time = time.time()
            update_timer = QTimer()

            # Flag to track if process was stopped by user
            user_cancelled = [False]

            def update_progress():
                """Update progress information"""
                # Calculate elapsed time correctly
                elapsed = time.time() - start_time
                minutes = int(elapsed) // 60
                seconds = int(elapsed) % 60
                time_label.setText(f"Time elapsed: {minutes}:{seconds:02d}")

                # Update progress based on elapsed time vs time limit
                # Assuming time_limit is in seconds
                time_limit_minutes = self.time_spin.value()

                # Convert to minutes for progress calculation (as requested)

                # Calculate progress percentage - don't go above 99% until complete
                if time_limit_minutes > 0:
                    progress_value = min(int((elapsed / (time_limit_minutes * 60)) * 100), 99)
                else:
                    progress_value = min(int((elapsed / 60) * 100), 99)  # Default if time limit is zero

                progress_bar.setValue(progress_value)

                # Keep UI responsive
                QApplication.processEvents()

            # Setup timer
            update_timer.timeout.connect(update_progress)
            update_timer.start(500)  # Update every half second

            # Connect stop button
            def on_cancel():
                user_cancelled[0] = True
                status_label.setText("Stopping nesting process...")
                if process and process.poll() is None:
                    process.terminate()

            stop_button.clicked.connect(on_cancel)

            # Update status message
            status_label.setText("Starting nesting program...")
            info_text.setText(info_text.text() + "Launching nesting program...\n")
            QApplication.processEvents()

            # Run the nesting program with the WRK file as an argument
            nesting_program = os.path.abspath(self.nesting_program_path)
            wrk_file = os.path.abspath(self.wrk_file_path)

            # Set working directory to the nesting program directory
            program_dir = os.path.dirname(nesting_program)

            # Update status
            status_label.setText("Running nesting algorithm...")
            info_text.setText(info_text.text() + f"Processing file: {os.path.basename(wrk_file)}\n")
            info_text.setText(info_text.text() + f"Parameter - Width: {self.width_spin.value()} cm\n")
            info_text.setText(info_text.text() + f"Parameter - Min Efficiency: {self.efficiency_spin.value()}%\n")
            info_text.setText(info_text.text() + f"Parameter - Time Limit: {self.time_spin.value()} min\n")
            QApplication.processEvents()

            # Create process
            import platform
            if platform.system() == 'Windows':
                process = subprocess.Popen(
                    [nesting_program, wrk_file],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True,
                    cwd=program_dir,
                    shell=True
                )
            else:
                process = subprocess.Popen(
                    [nesting_program, wrk_file],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True,
                    cwd=program_dir
                )

            # Update status
            status_label.setText("Nesting in progress...")
            info_text.setText(info_text.text() + "Calculating optimal pattern layout...\n")
            QApplication.processEvents()

            # Wait for process to complete with progress updates
            while process.poll() is None:
                update_progress()
                # Check if dialog has been closed
                if not progress_dialog.isVisible() or user_cancelled[0]:
                    process.terminate()
                    break
                time.sleep(0.1)

            # Stop timer
            update_timer.stop()

            # Process has completed, check result
            return_code = process.poll()
            stdout, stderr = process.communicate()

            # Calculate final time
            elapsed = time.time() - start_time
            minutes = int(elapsed) // 60
            seconds = int(elapsed) % 60

            if user_cancelled[0]:
                status_label.setText("Nesting process cancelled")
                info_text.setText(info_text.text() + f"Process cancelled after {minutes}:{seconds:02d}\n")
                progress_dialog.hide()
                self.statusBar.showMessage("Nesting program cancelled by user")
                return

            if return_code == 0:
                # Success
                progress_bar.setValue(100)
                status_label.setText("Nesting completed successfully!")
                info_text.setText(info_text.text() + f"Finished in {minutes}:{seconds:02d}\n")
                QApplication.processEvents()

                # Check if SES file was generated
                dxf_basename = os.path.splitext(os.path.basename(self.dxf_file_path))[0]
                dxf_dir = os.path.dirname(self.dxf_file_path)
                ses_file = os.path.join(dxf_dir, f"{dxf_basename}.ses")

                if os.path.exists(ses_file):
                    info_text.setText(info_text.text() + f"Generated result file: {os.path.basename(ses_file)}\n")

                    # Parse the SES file to get efficiency
                    nesting_data = parse_ses_file(ses_file)
                    if nesting_data and 'marker_info' in nesting_data and 'efficiency' in nesting_data['marker_info']:
                        efficiency = nesting_data['marker_info']['efficiency'] * 100
                        info_text.setText(info_text.text() + f"Achieved efficiency: {efficiency:.2f}%\n")

                    # Auto-close dialog after 3 seconds on success
                    QTimer.singleShot(3000, progress_dialog.accept)

                    # Ask if user wants to view results
                    response = QMessageBox.question(
                        self, "Nesting Complete",
                        f"Nesting completed successfully!\nEfficiency: {efficiency:.2f}%\n\nWould you like to view the results?",
                        QMessageBox.Yes | QMessageBox.No
                    )

                    if response == QMessageBox.Yes:
                        # Parse and display the nesting result
                        if nesting_data:
                            self.display_nesting_result(nesting_data)
                        else:
                            QMessageBox.warning(self, "Warning", "Failed to parse SES file.")
                else:
                    info_text.setText(info_text.text() + "Warning: No result file was generated.\n")
                    # Keep dialog open longer if there's an issue
                    QTimer.singleShot(5000, progress_dialog.accept)

                self.statusBar.showMessage(f"Nesting completed successfully in {minutes}:{seconds:02d}")

            else:
                # Error
                status_label.setText("Nesting failed")
                info_text.setText(info_text.text() + f"Process failed with error code {return_code}\n")
                if stderr:
                    info_text.setText(info_text.text() + f"Error: {stderr[:200]}...\n")

                # Keep dialog open for error review
                QMessageBox.critical(self, "Error", f"Nesting program failed with error code {return_code}")
                self.statusBar.showMessage("Nesting program failed")

        except Exception as e:
            import traceback
            traceback.print_exc()
            QMessageBox.critical(self, "Error", f"Failed to run nesting program: {str(e)}")
            self.statusBar.showMessage("Error running nesting program")

    def save_settings(self):
        """Save application settings"""
        if hasattr(self, 'settings_manager'):
            settings = {
                "nesting_program": self.nesting_program_path,
                "default_width": self.width_spin.value(),
                "default_efficiency": self.efficiency_spin.value(),
                "default_time_limit": self.time_spin.value()
            }
            self.settings_manager.save_settings(settings)

    def load_settings(self):
        """Load application settings"""
        if hasattr(self, 'settings_manager'):
            # Load settings
            settings = self.settings_manager.load_settings()
            
            # Apply settings
            nesting_program = settings.get("nesting_program", "")
            if nesting_program and os.path.exists(nesting_program):
                self.nesting_program_path = nesting_program
                self.nesting_path_edit.setText(nesting_program)
                
            # Apply default values
            self.width_spin.setValue(settings.get("default_width", 50))
            self.efficiency_spin.setValue(settings.get("default_efficiency", 80))
            self.time_spin.setValue(settings.get("default_time_limit", 1))

    def load_nesting_result(self):
        """Load and display a nesting result from a SES file"""
        if not self.dxf_file_path:
            QMessageBox.warning(self, "Warning", "Please load a DXF file first.")
            return

        # Try to find SES file with the same name as the DXF file
        ses_file = os.path.splitext(self.dxf_file_path)[0] + ".ses"

        # If SES file doesn't exist, ask user to select it
        if not os.path.exists(ses_file):
            file_path, _ = QFileDialog.getOpenFileName(
                self, "Select SES File", os.path.dirname(self.dxf_file_path), "SES Files (*.ses)"
            )
            if not file_path:
                return
            ses_file = file_path

        # Parse the SES file
        nesting_data = parse_ses_file(ses_file)
        if not nesting_data:
            QMessageBox.warning(self, "Warning", "Failed to parse SES file.")
            return

        # Display nesting result
        self.display_nesting_result(nesting_data)

    def display_nesting_result(self, nesting_data):
        """
        Display the nesting result in the nesting result view
        
        Args:
            nesting_data: Parsed nesting data from SES file
        """
        # Clear previous display
        self.nesting_result_scene.clear()

        # Add grid to scene for reference
        self.add_grid_to_scene(self.nesting_result_scene)

        # Get marker dimensions
        marker_width = nesting_data['marker_info'].get('width', 150)
        marker_length = nesting_data['marker_info'].get('length', 200)

        # SWAP width and length for correct container display
        display_width = marker_length  # Use length as width
        display_height = marker_width  # Use width as height

        # Create marker rectangle with black dashed outline
        marker_pen = QPen(Qt.black, 1.0)
        marker_pen.setStyle(Qt.DashLine)
        self.nesting_result_scene.addRect(0, 0, display_width, display_height, marker_pen)

        # Create dictionary mapping piece IDs to pattern paths
        piece_paths = {}
        piece_colors = {}
        for i, path in enumerate(self.pattern_paths):
            piece_paths[i] = path
            piece_colors[i] = self.pattern_colors[i] if i < len(self.pattern_colors) else QColor(255, 80, 40)

        # Place each piece at its position from the nesting data
        for piece_info in nesting_data['pieces']:
            piece_id = piece_info['id']

            # Skip if piece not found in pattern paths
            if piece_id not in piece_paths:
                print(f"Warning: Piece ID {piece_id} not found in pattern paths")
                continue

            # Get the pattern path for this piece
            pattern_path = piece_paths[piece_id]

            # Create a copy of the path to avoid modifying the original
            path_copy = QPainterPath(pattern_path)

            # Create graphics item for the pattern
            path_item = QGraphicsPathItem(path_copy)

            # Use the original pattern color
            color = piece_colors[piece_id]

            # Set pen and brush - use pattern fill (Dense4Pattern) to match the Pattern Pieces view
            path_item.setPen(QPen(color, 0.5))
            path_item.setBrush(QBrush(color, Qt.Dense4Pattern))  # Use pattern fill instead of solid

            # Apply flip if needed
            if piece_info['flip']:
                # Create a transform to flip the piece
                transform = QTransform()
                transform.scale(-1, 1)  # Horizontal flip
                path_item.setTransform(transform)

            # Apply rotation if needed
            if piece_info['angle'] != 0:
                path_item.setRotation(piece_info['angle'])

            # Position the piece
            path_item.setPos(piece_info['x'], piece_info['y'])

            # Add piece ID as small text at center
            bounds = path_item.boundingRect()
            text_item = self.nesting_result_scene.addText(str(piece_id))
            font = QFont("Arial", 12)
            font.setBold(True)
            text_item.setFont(font)
            text_item.setDefaultTextColor(Qt.black)

            # Position the text
            text_width = text_item.boundingRect().width()
            text_height = text_item.boundingRect().height()
            text_item.setPos(
                piece_info['x'] + bounds.width() / 2 - text_width / 2,
                piece_info['y'] + bounds.height() / 2 - text_height / 2
            )

            # Add to scene
            self.nesting_result_scene.addItem(path_item)

        # Set scene rectangle to contain all pieces, using swapped dimensions
        self.nesting_result_scene.setSceneRect(
            0, 0, display_width + 20, display_height + 50
        )

        # Add text for marker information at the bottom
        efficiency = nesting_data['marker_info'].get('efficiency', 0) * 100
        info_text = f"Width: {marker_width:.2f} cm, Length: {marker_length:.2f} cm, Efficiency: {efficiency:.2f}%"
        text_item = self.nesting_result_scene.addText(info_text)
        text_item.setPos(10, display_height + 10)
        text_item.setFont(QFont("Arial", 10, QFont.Bold))

        # Fit view to show all pieces
        self.nesting_result_view.fitInView(
            self.nesting_result_scene.sceneRect(), Qt.KeepAspectRatio
        )

        # Switch to the nesting result tab
        self.right_panel.setCurrentWidget(self.nesting_result_view)

        # Show success message
        self.statusBar.showMessage(
            f"Nesting result loaded. Efficiency: {efficiency:.2f}%"
        )

    def view_session_file(self, ses_file):
        """
        Open a viewer for the session file
        
        Args:
            ses_file: Path to SES file
        """
        # Parse and display the nesting result
        nesting_data = parse_ses_file(ses_file)
        if nesting_data:
            self.display_nesting_result(nesting_data)
        else:
            # Fall back to opening the file with the default application
            try:
                import platform
                if platform.system() == 'Windows':
                    os.startfile(ses_file)
                elif platform.system() == 'Darwin':  # macOS
                    subprocess.call(['open', ses_file])
                else:  # Linux and other Unix
                    subprocess.call(['xdg-open', ses_file])
            except Exception as e:
                QMessageBox.warning(self, "Error", f"Failed to open file: {e}")