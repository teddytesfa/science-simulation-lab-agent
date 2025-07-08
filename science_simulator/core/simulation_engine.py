"""
Core simulation engine for the Science Simulation Lab.
Handles physics simulation and rendering of 2D simulations.
"""
import pymunk
import pymunk.pygame_util
import pygame
from typing import Dict, Any, List, Optional
import numpy as np

class SimulationEngine:
    """Core engine for running physics simulations."""
    
    def __init__(self, width: int = 800, height: int = 600, control_panel_width: int = 300):
        """Initialize the simulation engine.
        
        Args:
            width: Width of the simulation area in pixels
            height: Height of the simulation area in pixels
            control_panel_width: Width of the control panel area
        """
        # Physics space
        self.space = pymunk.Space()
        self.space.gravity = (0, 900)  # Default gravity (pointing down)
        
        # Simulation dimensions
        self.width = width
        self.height = height
        self.control_panel_width = control_panel_width
        
        # Pygame surface for rendering
        self.surface = None
        self.simulation_surface = None  # Surface for just the simulation
        self.control_panel = None
        self.draw_options = None
        
        # Simulation objects
        self.objects = {}
        self.parameters = {}
        
        # Time tracking and control
        self.clock = pygame.time.Clock()
        self.running = False
        self.paused = False
        
        # Initialize pygame if not already done
        if not pygame.get_init():
            pygame.init()
            
        # Set up fonts
        self.font = pygame.font.SysFont('Arial', 14)
        self.title_font = pygame.font.SysFont('Arial', 18, bold=True)
    
    def setup_render_surface(self, surface=None):
        """Set up the pygame surface for rendering.
        
        Args:
            surface: Optional Pygame surface to render to. If None, a new window will be created.
        """
        if surface is None:
            # Initialize the display if it hasn't been already
            if not pygame.display.get_init():
                pygame.display.init()
            
            # Create a window with space for controls
            total_width = self.width + self.control_panel_width
            self.surface = pygame.display.set_mode((total_width, self.height))
            pygame.display.set_caption("Science Simulation Lab")
            
            # Create a subsurface for the simulation
            self.simulation_surface = self.surface.subsurface(
                pygame.Rect(0, 0, self.width, self.height)
            )
            
            # Set up the drawing options for the simulation surface
            self.draw_options = pymunk.pygame_util.DrawOptions(self.simulation_surface)
            
            # Initialize the control panel
            self._init_control_panel()
        else:
            self.surface = surface
            self.simulation_surface = surface.subsurface(
                pygame.Rect(0, 0, self.width, self.height)
            )
            self.draw_options = pymunk.pygame_util.DrawOptions(self.simulation_surface)
        
        # Set the background colors
        self.surface.fill((230, 230, 240))  # Light gray for control panel
        self.simulation_surface.fill((255, 255, 255))  # White for simulation
        pygame.display.flip()
    
    def add_object(self, name: str, obj_type: str, **kwargs) -> pymunk.Shape:
        """Add a physics object to the simulation.
        
        Args:
            name: Unique identifier for the object
            obj_type: Type of object ('box', 'circle', 'segment', 'poly')
            **kwargs: Additional parameters for the object
            
        Returns:
            The created physics shape
        """
        # Create the appropriate shape based on type
        if obj_type == 'box':
            width = kwargs.get('width', 50)
            height = kwargs.get('height', 50)
            x = kwargs.get('x', self.width // 2)
            y = kwargs.get('y', self.height // 2)
            mass = kwargs.get('mass', 1.0)
            
            moment = pymunk.moment_for_box(mass, (width, height))
            body = pymunk.Body(mass, moment)
            body.position = x, y
            shape = pymunk.Poly.create_box(body, (width, height))
            
        elif obj_type == 'circle':
            radius = kwargs.get('radius', 25)
            x = kwargs.get('x', self.width // 2)
            y = kwargs.get('y', self.height // 2)
            mass = kwargs.get('mass', 1.0)
            
            moment = pymunk.moment_for_circle(mass, 0, radius)
            body = pymunk.Body(mass, moment)
            body.position = x, y
            shape = pymunk.Circle(body, radius)
            
        else:
            raise ValueError(f"Unsupported object type: {obj_type}")
        
        # Set additional properties
        shape.elasticity = kwargs.get('elasticity', 0.5)
        shape.friction = kwargs.get('friction', 0.7)
        
        # Add to space
        self.space.add(body, shape)
        
        # Store the object
        self.objects[name] = {
            'body': body,
            'shape': shape,
            'type': obj_type,
            'properties': kwargs
        }
        
        return shape
    
    def add_parameter(self, name: str, param_type: str, **kwargs):
        """Add a configurable parameter to the simulation.
        
        Args:
            name: Name of the parameter
            param_type: Type of parameter ('slider', 'toggle', 'dropdown')
            **kwargs: Additional parameter properties
        """
        self.parameters[name] = {
            'type': param_type,
            'value': kwargs.get('default', 0),
            'min': kwargs.get('min', 0),
            'max': kwargs.get('max', 100),
            'step': kwargs.get('step', 1),
            'options': kwargs.get('options', []),
            'on_change': kwargs.get('on_change', None)
        }
    
    def update_parameter(self, name: str, value: Any):
        """Update a parameter value and trigger any callbacks.
        
        Args:
            name: Name of the parameter to update
            value: New value for the parameter
        """
        if name in self.parameters:
            param = self.parameters[name]
            param['value'] = value
            
            # Trigger callback if defined
            if callable(param.get('on_change')):
                param['on_change'](value)
    
    def step(self, dt: float = 1/60.0):
        """Advance the simulation by one time step.
        
        Args:
            dt: Time step in seconds
        """
        self.space.step(dt)
    
    def _init_control_panel(self):
        """Initialize the control panel with default controls."""
        from ..ui.simulation_controls import ControlPanel
        
        # Create control panel on the right side
        self.control_panel = ControlPanel(
            x=self.width, y=0, 
            width=self.control_panel_width, 
            height=self.height
        )
        
        # Add simulation controls
        self.control_panel.add_button(
            "Pause/Resume",
            lambda: setattr(self, 'paused', not self.paused)
        )
        
        self.control_panel.add_button(
            "Reset Simulation",
            self.reset
        )
        
        # Add gravity control
        self.gravity_slider = self.control_panel.add_slider(
            "gravity_y", -1000, 1000, 900, "Gravity (Y)", "pixels/s²"
        )
        
    def handle_events(self):
        """Handle all pygame events."""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            
            # Let the control panel handle UI events
            if self.control_panel:
                self.control_panel.handle_event(event)
        
        # Update simulation parameters from controls
        if hasattr(self, 'gravity_slider'):
            self.space.gravity = (0, self.gravity_slider.get_value())
    
    def render(self):
        """Render the current simulation state."""
        if not self.surface or not self.simulation_surface:
            return
            
        # Clear the surfaces
        self.simulation_surface.fill((255, 255, 255))
        
        # Draw the simulation
        self.space.debug_draw(self.draw_options)
        
        # Draw FPS counter
        fps_text = self.font.render(f"FPS: {int(self.clock.get_fps())}", True, (0, 0, 0))
        self.simulation_surface.blit(fps_text, (10, 10))
        
        # Draw the control panel
        if self.control_panel:
            self.control_panel.draw(self.surface)
        
        # Update the display
        pygame.display.flip()
    
    def run(self, max_fps: int = 60):
        """Run the simulation loop.
        
        Args:
            max_fps: Maximum frames per second to run the simulation at
        """
        self.running = True
        self.paused = False
        
        while self.running:
            # Handle events
            self.handle_events()
            
            # Step the simulation if not paused
            if not self.paused:
                self.step()
            
            # Always render, even when paused
            self.render()
            
            # Cap the frame rate
            self.clock.tick(max_fps)
    
    def reset(self):
        """Reset the simulation to its initial state."""
        # Remove all shapes first
        for shape in list(self.space.shapes):
            self.space.remove(shape)
            
        # Then remove all bodies
        for body in list(self.space.bodies):
            self.space.remove(body)
            
        # Also remove any constraints
        for constraint in list(self.space.constraints):
            self.space.remove(constraint)
        
        # Clear object references
        self.objects = {}
        
        # Reset parameters to defaults
        for param in self.parameters.values():
            if 'default' in param:
                param['value'] = param['default']
    
    def __del__(self):
        """Clean up resources."""
        if pygame.get_init():
            pygame.quit()
