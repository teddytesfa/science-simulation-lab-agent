"""
Projectile Motion Demo

This script demonstrates how to use the Science Simulation Lab Agent
with a simple projectile motion exercise.
"""
import json
import os
import sys
import math
import pymunk
import pygame
from pathlib import Path
from science_simulator.core.simulation_engine import SimulationEngine

def main():
    """Run the projectile motion demo with interactive UI."""
    # Initialize pygame
    pygame.init()
    
    # Set up display dimensions
    sim_width, sim_height = 800, 600
    control_width = 300
    
    # Create the simulation engine with control panel
    engine = SimulationEngine(
        width=sim_width,
        height=sim_height,
        control_panel_width=control_width
    )
    
    # Set up the render surface
    engine.setup_render_surface()
    
    # Add a ground plane
    ground = pymunk.Segment(
        engine.space.static_body,
        (0, sim_height - 50),
        (sim_width, sim_height - 50),
        5
    )
    ground.friction = 1.0
    ground.elasticity = 0.8
    engine.space.add(ground)
    
    # Add a projectile
    mass = 1
    radius = 15
    inertia = pymunk.moment_for_circle(mass, 0, radius, (0, 0))
    body = pymunk.Body(mass, inertia)
    body.position = 100, sim_height - 100
    shape = pymunk.Circle(body, radius, (0, 0))
    shape.elasticity = 0.8
    shape.friction = 0.5
    shape.density = 1
    shape.color = (70, 130, 180, 255)  # Blue color with alpha
    engine.space.add(body, shape)
    
    # Store the projectile for easy access
    engine.objects['projectile'] = {'body': body, 'shape': shape}
    
    # Add launch controls to the control panel
    if engine.control_panel:
        # Launch angle control (-90 to 90 degrees)
        angle_slider = engine.control_panel.add_slider(
            'launch_angle', -90, 90, 30, "Launch Angle", "°"
        )
        
        # Initial velocity control (0 to 1000 pixels/s)
        velocity_slider = engine.control_panel.add_slider(
            'initial_velocity', 0, 1000, 400, "Initial Velocity", "pixels/s"
        )
        
        # Launch button
        def launch_projectile():
            angle_rad = math.radians(angle_slider.get_value())
            velocity = velocity_slider.get_value()
            vx = velocity * math.cos(angle_rad)
            vy = -velocity * math.sin(angle_rad)  # Negative because y is down in Pygame
            body.position = 100, sim_height - 100  # Reset position
            body.velocity = (vx, vy)
            
        engine.control_panel.add_button("Launch!", launch_projectile)
        
        # Add a separator
        engine.control_panel.add_button("-" * 20, lambda: None)
        
        # Add gravity control (already added in engine._init_control_panel)
        
    # Main game loop
    clock = pygame.time.Clock()
    running = True
    
    print("=== Projectile Motion Demo ===")
    print("Controls:")
    print("- Adjust the launch angle and velocity using the sliders")
    print("- Click 'Launch!' to launch the projectile")
    print("- Use 'Pause/Resume' to pause the simulation")
    print("- Use 'Reset Simulation' to reset everything")
    print("- Adjust gravity using the gravity slider")
    print("\nClose the window to exit.")
    
    while running:
        # Handle events
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            
            # Let the control panel handle UI events
            if engine.control_panel:
                engine.control_panel.handle_event(event)
        
        # Step the simulation if not paused
        if not engine.paused:
            engine.step()
        
        # Render
        engine.render()
        
        # Cap the frame rate
        clock.tick(60)
    
    # Clean up
    pygame.quit()

if __name__ == "__main__":
    main()
