"""
UI Controls for the Science Simulation Lab.
Provides interactive controls for adjusting simulation parameters.
"""
import pygame
from typing import Dict, Any, Callable, List, Tuple

class Slider:
    """A simple slider control for adjusting numerical values."""
    
    def __init__(self, x: int, y: int, width: int, height: int, 
                 min_val: float, max_val: float, initial_val: float, 
                 label: str = "", unit: str = ""):
        """Initialize the slider.
        
        Args:
            x, y: Position of the slider
            width, height: Dimensions of the slider
            min_val: Minimum value
            max_val: Maximum value
            initial_val: Starting value
            label: Display label for the slider
            unit: Unit of measurement (e.g., 'm/s', 'kg')
        """
        self.rect = pygame.Rect(x, y, width, height)
        self.knob_rect = pygame.Rect(x, y, 20, height + 10)
        self.min_val = min_val
        self.max_val = max_val
        self.value = initial_val
        self.label = label
        self.unit = unit
        self.dragging = False
        self.update_knob_pos()
        
    def update_knob_pos(self):
        """Update the knob position based on current value."""
        ratio = (self.value - self.min_val) / (self.max_val - self.min_val)
        self.knob_rect.centerx = int(self.rect.left + ratio * self.rect.width)
        self.knob_rect.centery = self.rect.centery + 5
    
    def set_value(self, value: float):
        """Set the slider value and update knob position."""
        self.value = max(self.min_val, min(self.max_val, value))
        self.update_knob_pos()
    
    def get_value(self) -> float:
        """Get the current slider value."""
        return self.value
    
    def handle_event(self, event) -> bool:
        """Handle pygame events for the slider.
        
        Returns:
            bool: True if the event was handled, False otherwise
        """
        if event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1:  # Left mouse button
                if self.knob_rect.collidepoint(event.pos):
                    self.dragging = True
                    return True
                elif self.rect.collidepoint(event.pos):
                    # Clicked on the slider track, move knob to click position
                    self.knob_rect.centerx = max(self.rect.left, min(event.pos[0], self.rect.right))
                    self.value = self.min_val + (self.knob_rect.centerx - self.rect.left) / self.rect.width * (self.max_val - self.min_val)
                    return True
        
        elif event.type == pygame.MOUSEBUTTONUP:
            if event.button == 1:  # Left mouse button
                self.dragging = False
                return self.rect.collidepoint(event.pos)
        
        elif event.type == pygame.MOUSEMOTION:
            if self.dragging:
                self.knob_rect.centerx = max(self.rect.left, min(event.pos[0], self.rect.right))
                self.value = self.min_val + (self.knob_rect.centerx - self.rect.left) / self.rect.width * (self.max_val - self.min_val)
                return True
        
        return False
    
    def draw(self, surface):
        """Draw the slider on the given surface."""
        # Draw track
        pygame.draw.rect(surface, (200, 200, 200), self.rect, border_radius=5)
        pygame.draw.rect(surface, (150, 150, 150), self.rect, 2, border_radius=5)
        
        # Draw knob
        pygame.draw.rect(surface, (70, 130, 180), self.knob_rect, border_radius=3)
        
        # Draw label and value
        font = pygame.font.SysFont('Arial', 14)
        label_text = f"{self.label}: {self.value:.2f} {self.unit}"
        text_surface = font.render(label_text, True, (0, 0, 0))
        surface.blit(text_surface, (self.rect.x, self.rect.y - 20))


class Button:
    """A simple button control."""
    
    def __init__(self, x: int, y: int, width: int, height: int, 
                 text: str, action: Callable[[], None] = None):
        """Initialize the button.
        
        Args:
            x, y: Position of the button
            width, height: Dimensions of the button
            text: Button label
            action: Function to call when button is clicked
        """
        self.rect = pygame.Rect(x, y, width, height)
        self.text = text
        self.action = action
        self.hover = False
    
    def handle_event(self, event) -> bool:
        """Handle pygame events for the button.
        
        Returns:
            bool: True if the event was handled, False otherwise
        """
        if event.type == pygame.MOUSEMOTION:
            self.hover = self.rect.collidepoint(event.pos)
            return False
            
        if event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1 and self.hover and self.action:
                self.action()
                return True
        return False
    
    def draw(self, surface):
        """Draw the button on the given surface."""
        # Button color changes on hover
        color = (100, 150, 200) if self.hover else (70, 130, 180)
        pygame.draw.rect(surface, color, self.rect, border_radius=5)
        pygame.draw.rect(surface, (50, 100, 150), self.rect, 2, border_radius=5)
        
        # Draw text
        font = pygame.font.SysFont('Arial', 14, bold=True)
        text_surface = font.render(self.text, True, (255, 255, 255))
        text_rect = text_surface.get_rect(center=self.rect.center)
        surface.blit(text_surface, text_rect)


class ControlPanel:
    """A panel containing simulation controls."""
    
    def __init__(self, x: int, y: int, width: int, height: int):
        """Initialize the control panel.
        
        Args:
            x, y: Position of the panel
            width, height: Dimensions of the panel
        """
        self.rect = pygame.Rect(x, y, width, height)
        self.controls = []
        self.background = (240, 240, 240)
        self.border_color = (200, 200, 200)
        self.padding = 10
        self.spacing = 15
    
    def add_slider(self, name: str, min_val: float, max_val: float, 
                  initial_val: float, label: str = "", unit: str = "") -> Slider:
        """Add a slider to the control panel.
        
        Returns:
            Slider: The created slider control
        """
        y_pos = self.rect.y + self.padding + len(self.controls) * (60 + self.spacing)
        slider = Slider(
            x=self.rect.x + self.padding,
            y=y_pos + 20,
            width=self.rect.width - 2 * self.padding,
            height=10,
            min_val=min_val,
            max_val=max_val,
            initial_val=initial_val,
            label=label or name,
            unit=unit
        )
        self.controls.append(slider)
        return slider
    
    def add_button(self, text: str, action: Callable[[], None]) -> Button:
        """Add a button to the control panel.
        
        Returns:
            Button: The created button control
        """
        y_pos = self.rect.y + self.padding + len(self.controls) * (60 + self.spacing)
        button = Button(
            x=self.rect.x + self.padding,
            y=y_pos,
            width=self.rect.width - 2 * self.padding,
            height=30,
            text=text,
            action=action
        )
        self.controls.append(button)
        return button
    
    def handle_event(self, event) -> bool:
        """Handle pygame events for all controls.
        
        Returns:
            bool: True if any control handled the event, False otherwise
        """
        for control in self.controls:
            if control.handle_event(event):
                return True
        return False
    
    def draw(self, surface):
        """Draw the control panel and all its controls."""
        # Draw panel background
        pygame.draw.rect(surface, self.background, self.rect)
        pygame.draw.rect(surface, self.border_color, self.rect, 2)
        
        # Draw title
        font = pygame.font.SysFont('Arial', 16, bold=True)
        title = font.render("Simulation Controls", True, (0, 0, 0))
        surface.blit(title, (self.rect.x + self.padding, self.rect.y + self.padding))
        
        # Draw all controls
        for control in self.controls:
            control.draw(surface)
