"""
Main application module for the Science Simulation Lab Agent.
"""
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QSplitter,
    QLabel, QPushButton, QTextEdit, QDockWidget
)
from PyQt6.QtCore import Qt

class ScienceSimulatorApp(QMainWindow):
    """Main application window for the Science Simulation Lab."""
    
    def __init__(self):
        """Initialize the main application window."""
        super().__init__()
        self.setWindowTitle("Science Simulation Lab")
        self.setGeometry(100, 100, 1200, 800)
        
        # Central widget and main layout
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        
        # Main layout using a splitter for resizable panels
        self.main_layout = QHBoxLayout(self.central_widget)
        self.splitter = QSplitter(Qt.Orientation.Horizontal)
        self.main_layout.addWidget(self.splitter)
        
        # Create main panels
        self._create_simulation_panel()
        self._create_control_panel()
        
        # Set initial splitter sizes
        self.splitter.setSizes([800, 400])
    
    def _create_simulation_panel(self):
        """Create the simulation display panel."""
        self.simulation_widget = QWidget()
        layout = QVBoxLayout(self.simulation_widget)
        
        # Simulation canvas (placeholder for now)
        self.simulation_canvas = QLabel("Simulation will appear here")
        self.simulation_canvas.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.simulation_canvas.setStyleSheet("background-color: #f0f0f0; border: 1px solid #ccc;")
        layout.addWidget(self.simulation_canvas)
        
        # Exercise description
        self.exercise_description = QTextEdit()
        self.exercise_description.setPlaceholderText("Exercise description will appear here...")
        self.exercise_description.setMaximumHeight(100)
        layout.addWidget(self.exercise_description)
        
        self.splitter.addWidget(self.simulation_widget)
    
    def _create_control_panel(self):
        """Create the control panel for parameters and feedback."""
        self.control_widget = QWidget()
        layout = QVBoxLayout(self.control_widget)
        
        # Parameters section
        params_label = QLabel("Parameters")
        params_label.setStyleSheet("font-weight: bold;")
        layout.addWidget(params_label)
        
        # Parameters container (will be populated dynamically)
        self.parameters_container = QWidget()
        self.parameters_layout = QVBoxLayout(self.parameters_container)
        layout.addWidget(self.parameters_container)
        
        # Feedback section
        feedback_label = QLabel("Feedback")
        feedback_label.setStyleSheet("font-weight: bold; margin-top: 10px;")
        layout.addWidget(feedback_label)
        
        self.feedback_display = QTextEdit()
        self.feedback_display.setReadOnly(True)
        self.feedback_display.setMaximumHeight(150)
        layout.addWidget(self.feedback_display)
        
        # Action buttons
        button_layout = QHBoxLayout()
        
        self.run_button = QPushButton("Run Simulation")
        self.check_button = QPushButton("Check Answer")
        self.hint_button = QPushButton("Get Hint")
        
        button_layout.addWidget(self.run_button)
        button_layout.addWidget(self.check_button)
        button_layout.addWidget(self.hint_button)
        
        layout.addLayout(button_layout)
        layout.addStretch()
        
        self.splitter.addWidget(self.control_widget)
