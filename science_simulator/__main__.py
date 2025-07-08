#!/usr/bin/env python3
"""
Main entry point for the Science Simulation Lab Agent.
"""
import sys
from PyQt6.QtWidgets import QApplication

from science_simulator.app import ScienceSimulatorApp

def main():
    """Launch the Science Simulation Lab application."""
    app = QApplication(sys.argv)
    
    # Set application information
    app.setApplicationName("Science Simulation Lab")
    app.setApplicationVersion("0.1.0")
    app.setOrganizationName("ScienceSimLab")
    
    # Create and show the main window
    window = ScienceSimulatorApp()
    window.show()
    
    # Start the event loop
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
