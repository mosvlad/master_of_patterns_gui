"""
Process manager window for managing nesting tasks.
"""
import os
import subprocess
from PyQt5.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
                             QTableWidget, QTableWidgetItem, QHeaderView,
                             QStatusBar, QToolBar, QAction, QMenu, QMessageBox)
from PyQt5.QtCore import Qt, QTimer, pyqtSignal, QMutex
from PyQt5.QtGui import QColor

from models.nesting_task import NestingTask
from gui.dialogs.add_task_dialog import AddTaskDialog


class NestingProcessManager(QMainWindow):
    """Window for managing multiple nesting processes"""

    # Define a signal for task completion
    task_completed_signal = pyqtSignal(int)  # Parameter is task index

    def __init__(self, parent=None):
        """
        Initialize the process manager
        
        Args:
            parent: Parent widget (main application window)
        """
        super().__init__(parent)

        self.tasks = []  # List of NestingTask objects
        self.nesting_program = ""  # Default nesting program path
        self.task_mutex = QMutex()  # Add a mutex for thread safety
        self.parent_app = parent  # Store reference to the parent app
        self.last_selected_row = -1  # Track the last selected row
        self.update_counter = 0  # Counter to limit full updates

        # Get nesting program from parent if available
        if parent and hasattr(parent, 'nesting_program_path'):
            self.nesting_program = parent.nesting_program_path

        self.init_ui()

        # Connect the task completed signal
        self.task_completed_signal.connect(self.on_task_completed)

        # Start the timer for updating task status
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_task_status)
        self.timer.start(1000)  # Update every second - reduced frequency

        # Setting this attribute to avoid destroying the window on close
        self.setAttribute(Qt.WA_DeleteOnClose, False)

    def closeEvent(self, event):
        """
        Override close event to hide the window instead of closing it
        
        Args:
            event: Close event
        """
        event.ignore()  # Don't actually close the window
        self.hide()  # Hide it instead

        # Optionally show a notification that tasks continue running
        if any(task.is_running for task in self.tasks):
            if self.parent_app and hasattr(self.parent_app, 'statusBar'):
                self.parent_app.statusBar.showMessage("Nesting tasks continue running in the background", 3000)

    def init_ui(self):
        """Initialize the user interface"""
        self.setWindowTitle("Диспетчер задач")
        self.setGeometry(100, 100, 1200, 600)

        # Create central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)

        # Create toolbar
        self.create_toolbar()

        # Create task table
        self.task_table = QTableWidget()
        self.task_table.setColumnCount(9)
        self.task_table.setHorizontalHeaderLabels([
            "№", "Имя файла", "Статус", "Прогресс (мм:сс)",
            "Время (мм:сс)", "Лекала", "Эффективность",
            "Ширина", "Путь к файлу"
        ])

        # Set table properties
        self.task_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.task_table.setSelectionMode(QTableWidget.SingleSelection)
        self.task_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.task_table.setAlternatingRowColors(True)
        self.task_table.horizontalHeader().setSectionResizeMode(QHeaderView.Interactive)
        self.task_table.horizontalHeader().setStretchLastSection(True)
        self.task_table.verticalHeader().setVisible(False)

        # Connect selection changed signal to track selection
        self.task_table.itemSelectionChanged.connect(self.on_selection_changed)

        # Set column widths
        self.task_table.setColumnWidth(0, 40)  # №
        self.task_table.setColumnWidth(1, 100)  # Filename
        self.task_table.setColumnWidth(2, 100)  # Status
        self.task_table.setColumnWidth(3, 120)  # Progress
        self.task_table.setColumnWidth(4, 120)  # Time limit
        self.task_table.setColumnWidth(5, 80)  # Pattern count
        self.task_table.setColumnWidth(6, 120)  # Efficiency
        self.task_table.setColumnWidth(7, 80)  # Width

        # Context menu for the table
        self.task_table.setContextMenuPolicy(Qt.CustomContextMenu)
        self.task_table.customContextMenuRequested.connect(self.show_context_menu)

        # Add table to layout
        layout.addWidget(self.task_table)

        # Create status bar
        self.statusBar = QStatusBar()
        self.setStatusBar(self.statusBar)
        self.statusBar.showMessage("Готово")

    def on_selection_changed(self):
        """Track when the selection changes"""
        selected_rows = self.task_table.selectionModel().selectedRows()
        if selected_rows:
            self.last_selected_row = selected_rows[0].row()
        else:
            self.last_selected_row = -1

    def create_toolbar(self):
        """Create the toolbar with actions"""
        toolbar = QToolBar("Панель инструментов")
        self.addToolBar(toolbar)

        # Add DXF action
        add_action = QAction("Добавить задачу", self)
        add_action.triggered.connect(self.add_task)
        toolbar.addAction(add_action)

        # Start action
        start_action = QAction("Запустить", self)
        start_action.triggered.connect(self.start_selected_task)
        toolbar.addAction(start_action)

        # Stop action
        stop_action = QAction("Остановить", self)
        stop_action.triggered.connect(self.stop_selected_task)
        toolbar.addAction(stop_action)

        # View result action
        view_action = QAction("Просмотр результата", self)
        view_action.triggered.connect(self.view_selected_result)
        toolbar.addAction(view_action)

        # Remove action
        remove_action = QAction("Удалить задачу", self)
        remove_action.triggered.connect(self.remove_selected_task)
        toolbar.addAction(remove_action)

    def show_context_menu(self, position):
        """
        Show context menu for right-click on table rows
        
        Args:
            position: Position where the context menu should appear
        """
        context_menu = QMenu(self)

        # Add actions
        start_action = context_menu.addAction("Запустить")
        stop_action = context_menu.addAction("Остановить")
        view_action = context_menu.addAction("Просмотр результата")
        context_menu.addSeparator()
        remove_action = context_menu.addAction("Удалить задачу")

        # Get selected action
        action = context_menu.exec_(self.task_table.mapToGlobal(position))

        # Handle selected action
        if action == start_action:
            self.start_selected_task()
        elif action == stop_action:
            self.stop_selected_task()
        elif action == view_action:
            self.view_selected_result()
        elif action == remove_action:
            self.remove_selected_task()

    def add_task(self):
        """Add a new nesting task"""
        # Create a dialog to collect task information
        dialog = AddTaskDialog(self)

        # Set default nesting program if available
        if self.nesting_program:
            dialog.nesting_program = self.nesting_program
            dialog.nesting_path_edit.setText(self.nesting_program)

        if dialog.exec_() == AddTaskDialog.Accepted:
            # Create a new task
            task = NestingTask(
                dxf_file=dialog.dxf_file,
                nesting_program=dialog.nesting_program,
                wrk_file=dialog.wrk_file,
                width=dialog.width,
                time_limit=dialog.time_limit
            )

            # Monkey patch the _notify_task_completed method
            task_index = len(self.tasks)
            task._notify_task_completed = lambda: self.task_completed_signal.emit(task_index)

            # Add the task to the list
            self.tasks.append(task)

            # Update the table
            self.update_task_table(force=True)

            # Auto start if selected
            if dialog.auto_start:
                task.start()
                self.update_task_table(force=True)  # Update immediately

    def on_task_completed(self, task_index):
        """
        Slot that's called when a task is completed
        
        Args:
            task_index: Index of the completed task
        """
        if 0 <= task_index < len(self.tasks):
            print(f"Task {task_index} completed, updating UI")
            self.update_task_table(force=True)
            # Maybe show a notification or play a sound
            self.statusBar.showMessage(f"Task {task_index + 1} completed")

            # Notify parent app if visible and has statusBar
            if self.parent_app and hasattr(self.parent_app, 'statusBar') and not self.isVisible():
                self.parent_app.statusBar.showMessage(f"Nesting task {task_index + 1} completed", 5000)

    def update_task_status(self):
        """Update the status of running tasks (called by timer)"""
        # Use mutex to prevent concurrent access
        self.task_mutex.lock()
        try:
            # Check if any tasks need updating
            needs_update = False
            running_tasks = False

            for task in self.tasks:
                if task.is_running:
                    running_tasks = True
                    # Update the task's progress
                    task.update_progress()
                    needs_update = True

            if needs_update and self.isVisible():
                self.update_counter += 1
                if running_tasks:
                    # Update only progress times every second
                    self.update_progress_display()

                    # Do a full update every 5 seconds to ensure all data is fresh
                    if self.update_counter >= 5:
                        self.update_task_table(force=True)
                        self.update_counter = 0
                else:
                    # If no running tasks, do normal update
                    self.update_task_table(force=True)
                    self.update_counter = 0

        finally:
            self.task_mutex.unlock()

    def update_progress_display(self):
        """Update only the progress time display for running tasks without changing selection"""
        if not self.isVisible() or self.task_table.rowCount() == 0:
            return

        # Update only the progress column for running tasks
        for row in range(self.task_table.rowCount()):
            task_index = int(self.task_table.item(row, 0).text()) - 1
            if 0 <= task_index < len(self.tasks):
                task = self.tasks[task_index]

                if task.is_running:
                    # Update progress time
                    minutes = task.progress_time // 60
                    seconds = task.progress_time % 60
                    progress_text = f"{minutes:02d}:{seconds:02d}"

                    # Update only the progress cell
                    progress_item = self.task_table.item(row, 3)
                    if progress_item and progress_item.text() != progress_text:
                        progress_item.setText(progress_text)

    def update_task_table(self, force=False):
        """
        Update the task table with current task information
        
        Args:
            force (bool, optional): Force update even if window is not visible
        """
        # Only update the table if the window is visible
        if not self.isVisible() and not force:
            return

        # Save the current selection
        current_row = self.last_selected_row

        # Block signals temporarily to prevent selection change events during update
        self.task_table.blockSignals(True)

        # Clear the table
        self.task_table.setRowCount(0)

        # Add tasks to the table
        for i, task in enumerate(self.tasks):
            row = self.task_table.rowCount()
            self.task_table.insertRow(row)

            # Task number
            self.task_table.setItem(row, 0, QTableWidgetItem(str(i + 1)))

            # Filename
            filename = os.path.basename(task.dxf_file)
            self.task_table.setItem(row, 1, QTableWidgetItem(filename))

            # Status
            status_item = QTableWidgetItem(task.status)
            if task.status == NestingTask.STATUS_RUNNING:
                status_item.setBackground(QColor(173, 216, 230))  # Light blue
            elif task.status == NestingTask.STATUS_COMPLETED:
                status_item.setBackground(QColor(144, 238, 144))  # Light green
            elif task.status == NestingTask.STATUS_STOPPED:
                status_item.setBackground(QColor(255, 165, 0))  # Orange
            elif task.status == NestingTask.STATUS_ERROR:
                status_item.setBackground(QColor(255, 99, 71))  # Tomato red
            self.task_table.setItem(row, 2, status_item)

            # Progress time (mm:ss)
            minutes = task.progress_time // 60
            seconds = task.progress_time % 60
            progress_text = f"{minutes:02d}:{seconds:02d}"
            self.task_table.setItem(row, 3, QTableWidgetItem(progress_text))

            # Time limit (mm:ss)
            minutes = task.time_limit // 60
            seconds = task.time_limit % 60
            time_text = f"{minutes:02d}:{seconds:02d}"
            self.task_table.setItem(row, 4, QTableWidgetItem(time_text))

            # Pattern count
            self.task_table.setItem(row, 5, QTableWidgetItem(str(task.pattern_count)))

            # Efficiency
            efficiency_text = f"{task.efficiency:.2f}%" if task.efficiency > 0 else ""
            self.task_table.setItem(row, 6, QTableWidgetItem(efficiency_text))

            # Width
            self.task_table.setItem(row, 7, QTableWidgetItem(f"{task.width:.6f}"))

            # File path
            self.task_table.setItem(row, 8, QTableWidgetItem(task.dxf_file))

        # Restore selection if possible
        if current_row >= 0 and current_row < self.task_table.rowCount():
            self.task_table.selectRow(current_row)
            self.last_selected_row = current_row

        # Unblock signals
        self.task_table.blockSignals(False)

    def get_selected_task(self):
        """
        Get the currently selected task or None if no task is selected
        
        Returns:
            NestingTask or None: The selected task
        """
        selected_rows = self.task_table.selectionModel().selectedRows()
        if not selected_rows:
            QMessageBox.warning(self, "Предупреждение", "Не выбрана задача")
            return None

        row = selected_rows[0].row()
        task_index = int(self.task_table.item(row, 0).text()) - 1

        if 0 <= task_index < len(self.tasks):
            return self.tasks[task_index]

        return None

    def start_selected_task(self):
        """Start the selected task"""
        task = self.get_selected_task()
        if task:
            print(f"Starting task: {task.dxf_file}")
            task.start()
            self.update_task_table(force=True)

    def stop_selected_task(self):
        """Stop the selected task"""
        task = self.get_selected_task()
        if task:
            print(f"Stopping task: {task.dxf_file}")
            task.stop()
            self.update_task_table(force=True)

    def remove_selected_task(self):
        """Remove the selected task"""
        task = self.get_selected_task()
        if task:
            # Stop the task if it's running
            if task.is_running:
                task.stop()

            # Remove from list
            self.tasks.remove(task)
            self.update_task_table(force=True)

    def view_selected_result(self):
        """View the result of the selected task"""
        task = self.get_selected_task()
        if not task:
            return

        # Check if task has been completed
        if task.status not in [NestingTask.STATUS_COMPLETED, NestingTask.STATUS_STOPPED]:
            QMessageBox.warning(self, "Предупреждение", "Задача еще не завершена")
            return

        # Check if SES file exists
        ses_file = os.path.splitext(task.dxf_file)[0] + ".ses"
        if not os.path.exists(ses_file):
            QMessageBox.warning(self, "Предупреждение", "Файл результатов не найден")
            return

        # If parent app has the visualization functionality, use it
        if self.parent_app and hasattr(self.parent_app, 'view_session_file'):
            # If parent app doesn't have DXF file loaded, try to load it first
            if not self.parent_app.dxf_file_path:
                self.parent_app.dxf_file_path = task.dxf_file
                self.parent_app.dxf_path_edit.setText(task.dxf_file)
                try:
                    self.parent_app.load_dxf()
                except Exception as e:
                    print(f"Warning: Could not load DXF file in parent app: {e}")

            # Now show the nesting result
            self.parent_app.view_session_file(ses_file)
            self.parent_app.raise_()  # Bring the main window to the front
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
                QMessageBox.warning(self, "Ошибка", f"Не удалось открыть файл: {e}")