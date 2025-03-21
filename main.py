#!/usr/bin/env python3
"""
Pattern Nesting Tool - Main Entry Point

This application provides tools for pattern nesting operations,
including loading DXF files, visualizing patterns, and running
external nesting programs to optimize pattern layouts.
"""
import sys
import os
from PyQt5.QtWidgets import QApplication
from PyQt5.QtGui import QFont

# Import main application window
from gui.main_window import PatternNestingApp


def main():
    """Main entry point for the application"""
    # Create the application
    app = QApplication(sys.argv)
    app.setStyle('Fusion')  # Modern style
    
    # Set application font
    font = QFont("Segoe UI", 9)
    app.setFont(font)
    
    # Create and show the main window
    window = PatternNestingApp()
    window.show()
    
    # Run the application event loop
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()