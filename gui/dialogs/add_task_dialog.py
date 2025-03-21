"""
Dialog for adding a nesting task to the process manager.
"""
import os
from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QFormLayout, QHBoxLayout,
                            QLineEdit, QPushButton, QDoubleSpinBox, QSpinBox,
                            QCheckBox, QFileDialog)


class AddTaskDialog(QDialog):
    """Dialog for adding a new nesting task"""

    def __init__(self, parent=None):
        """
        Initialize the dialog
        
        Args:
            parent: Parent widget
        """
        super().__init__(parent)

        self.dxf_file = ""
        self.nesting_program = ""
        self.wrk_file = ""
        self.width = 50.0
        self.time_limit = 5 * 60  # 5 minutes in seconds
        self.auto_start = False

        # If parent has a nesting program path, use it
        if hasattr(parent, 'nesting_program') and parent.nesting_program:
            self.nesting_program = parent.nesting_program

        self.init_ui()

    def init_ui(self):
        """Initialize the user interface"""
        self.setWindowTitle("Добавить задачу")
        self.setMinimumWidth(500)

        layout = QVBoxLayout(self)

        # Form layout for inputs
        form_layout = QFormLayout()

        # DXF file selection
        self.dxf_path_edit = QLineEdit()
        self.dxf_path_edit.setReadOnly(True)
        self.dxf_browse_btn = QPushButton("Обзор...")
        self.dxf_browse_btn.clicked.connect(self.browse_dxf_file)

        dxf_layout = QHBoxLayout()
        dxf_layout.addWidget(self.dxf_path_edit)
        dxf_layout.addWidget(self.dxf_browse_btn)
        form_layout.addRow("DXF файл:", dxf_layout)

        # Nesting program selection
        self.nesting_path_edit = QLineEdit()
        self.nesting_path_edit.setReadOnly(True)
        if self.nesting_program:
            self.nesting_path_edit.setText(self.nesting_program)

        self.nesting_browse_btn = QPushButton("Обзор...")
        self.nesting_browse_btn.clicked.connect(self.browse_nesting_program)

        nesting_layout = QHBoxLayout()
        nesting_layout.addWidget(self.nesting_path_edit)
        nesting_layout.addWidget(self.nesting_browse_btn)
        form_layout.addRow("Программа:", nesting_layout)

        # WRK file selection (optional)
        self.wrk_path_edit = QLineEdit()
        self.wrk_path_edit.setReadOnly(True)
        self.wrk_path_edit.setPlaceholderText("Опционально - будет создан автоматически")

        self.wrk_browse_btn = QPushButton("Обзор...")
        self.wrk_browse_btn.clicked.connect(self.browse_wrk_file)

        wrk_layout = QHBoxLayout()
        wrk_layout.addWidget(self.wrk_path_edit)
        wrk_layout.addWidget(self.wrk_browse_btn)
        form_layout.addRow("WRK файл:", wrk_layout)

        # Width input
        self.width_spin = QDoubleSpinBox()
        self.width_spin.setRange(1, 1000)
        self.width_spin.setValue(self.width)
        self.width_spin.setSingleStep(1)
        self.width_spin.setSuffix(" см")
        form_layout.addRow("Ширина:", self.width_spin)

        # Time limit input
        self.time_minutes_spin = QSpinBox()
        self.time_minutes_spin.setRange(0, 60)
        self.time_minutes_spin.setValue(self.time_limit // 60)
        self.time_minutes_spin.setSuffix(" мин")

        self.time_seconds_spin = QSpinBox()
        self.time_seconds_spin.setRange(0, 59)
        self.time_seconds_spin.setValue(self.time_limit % 60)
        self.time_seconds_spin.setSuffix(" сек")

        time_layout = QHBoxLayout()
        time_layout.addWidget(self.time_minutes_spin)
        time_layout.addWidget(self.time_seconds_spin)
        form_layout.addRow("Лимит времени:", time_layout)

        # Auto start checkbox
        self.auto_start_check = QCheckBox("Запустить сразу после добавления")
        form_layout.addRow("", self.auto_start_check)

        layout.addLayout(form_layout)

        # Dialog buttons
        button_layout = QHBoxLayout()

        self.cancel_btn = QPushButton("Отмена")
        self.cancel_btn.clicked.connect(self.reject)

        self.ok_btn = QPushButton("Добавить")
        self.ok_btn.clicked.connect(self.accept_dialog)
        self.ok_btn.setEnabled(False)  # Disabled until required fields are filled

        button_layout.addWidget(self.cancel_btn)
        button_layout.addWidget(self.ok_btn)

        layout.addLayout(button_layout)

    def browse_dxf_file(self):
        """Open file dialog to select DXF file"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Выбрать DXF файл", "", "DXF Files (*.dxf)"
        )
        if file_path:
            self.dxf_file = file_path
            self.dxf_path_edit.setText(file_path)
            self.check_required_fields()

            # Auto-generate WRK file name
            if not self.wrk_file:
                self.wrk_file = os.path.splitext(file_path)[0] + ".wrk"
                self.wrk_path_edit.setText(self.wrk_file)

    def browse_nesting_program(self):
        """Open file dialog to select nesting program executable"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Выбрать программу для раскладки", "", "Executable Files (*.exe)"
        )
        if file_path:
            self.nesting_program = file_path
            self.nesting_path_edit.setText(file_path)
            self.check_required_fields()

    def browse_wrk_file(self):
        """Open file dialog to select WRK file location"""
        file_path, _ = QFileDialog.getSaveFileName(
            self, "Выбрать файл WRK", "", "WRK Files (*.wrk)"
        )
        if file_path:
            if not file_path.lower().endswith('.wrk'):
                file_path += '.wrk'
            self.wrk_file = file_path
            self.wrk_path_edit.setText(file_path)

    def check_required_fields(self):
        """Check if all required fields are filled and enable/disable the OK button"""
        self.ok_btn.setEnabled(bool(self.dxf_file and self.nesting_program))

    def accept_dialog(self):
        """Accept the dialog and save the settings"""
        # Update values from inputs
        self.width = self.width_spin.value()

        minutes = self.time_minutes_spin.value()
        seconds = self.time_seconds_spin.value()
        self.time_limit = minutes * 60 + seconds

        self.auto_start = self.auto_start_check.isChecked()

        # Accept the dialog
        self.accept()