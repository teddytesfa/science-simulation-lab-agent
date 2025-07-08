"""
Simulation Manager

Coordinates between the UI, parser, and simulation engine to manage
the lifecycle of science simulations.
"""
import os
import json
import yaml
from pathlib import Path
from typing import Dict, Any, List, Optional, Callable
import pymunk

from ..parsers.exercise_parser import ExerciseParser
from .simulation_engine import SimulationEngine
from typing import Optional, Dict, Any, List, Callable
import os
from pathlib import Path

class SimulationManager:
    """Manages the lifecycle of science simulations.
    
    This class coordinates between the UI, parser (which uses Gemma 3N),
    and simulation engine to create an interactive learning experience.
    """
    
    def __init__(self, use_gemma: bool = True, gemma_model: str = "google/gemma-3n"):
        """Initialize the simulation manager.
        
        Args:
            use_gemma: Whether to use the Gemma 3N model for parsing
            gemma_model: Name or path of the Gemma 3N model to use
        """
        # Initialize the exercise parser with Gemma 3N integration
        self.parser = ExerciseParser(use_gemma=use_gemma, gemma_model=gemma_model)
        self.engine = SimulationEngine()
        self.current_exercise = None
        self.current_simulation = None
        self.callbacks = {
            'on_parameter_change': [],
            'on_simulation_update': [],
            'on_feedback': [],
            'on_parse_complete': [],
            'on_error': []
        }
        
        # Create necessary directories
        self.data_dir = Path.home() / '.science_simulator'
        self.exercises_dir = self.data_dir / 'exercises'
        self.results_dir = self.data_dir / 'results'
        
        for directory in [self.data_dir, self.exercises_dir, self.results_dir]:
            directory.mkdir(exist_ok=True, parents=True)
    
    def load_exercise(self, exercise_source: str, domain: str = None) -> Dict[str, Any]:
        """Load an exercise from a description or file.
        
        Args:
            exercise_source: Either exercise text or path to a file
            domain: Optional domain hint ('physics', 'chemistry', 'biology')
            
        Returns:
            Dictionary containing exercise data
            
        Raises:
            ValueError: If the exercise cannot be loaded or parsed
        """
        try:
            # Check if the source is a file path
            if os.path.isfile(exercise_source):
                with open(exercise_source, 'r', encoding='utf-8') as f:
                    if exercise_source.endswith(('.yaml', '.yml')):
                        # Load from YAML template
                        self.current_exercise = yaml.safe_load(f)
                        # Add metadata
                        if not isinstance(self.current_exercise, dict):
                            self.current_exercise = {'content': self.current_exercise}
                        self.current_exercise['source'] = exercise_source
                        self.current_exercise['parse_method'] = 'yaml_template'
                    elif exercise_source.endswith('.json'):
                        # Load from JSON template
                        self.current_exercise = json.load(f)
                        self.current_exercise['source'] = exercise_source
                        self.current_exercise['parse_method'] = 'json_template'
                    else:
                        # Assume it's a text description
                        exercise_text = f.read()
                        self.current_exercise = self.parser.parse_exercise(
                            exercise_text, 
                            domain=domain
                        )
                        self.current_exercise['source'] = exercise_source
            else:
                # Treat as direct exercise text
                self.current_exercise = self.parser.parse_exercise(
                    exercise_source,
                    domain=domain
                )
                self.current_exercise['source'] = 'direct_input'
            
            # Add domain if not already set
            if 'domain' not in self.current_exercise:
                self.current_exercise['domain'] = domain or 'physics'
            
            # Initialize simulation based on exercise type
            self._initialize_simulation()
            
            # Notify listeners that parsing is complete
            self._notify('on_parse_complete', self.current_exercise)
            
            return self.current_exercise
            
        except Exception as e:
            error_msg = f"Failed to load exercise: {str(e)}"
            self._notify('on_error', error_msg)
            raise ValueError(error_msg) from e
    
    def _initialize_simulation(self):
        """Initialize the simulation based on the current exercise."""
        if not self.current_exercise:
            return
        
        # Reset the engine
        self.engine.reset()
        
        # Set up parameters
        for param_name, param_config in self.current_exercise.get('parameters', {}).items():
            self.engine.add_parameter(
                param_name,
                param_type='slider',
                default=param_config.get('value', 0),
                min=param_config.get('min', 0),
                max=param_config.get('max', 100),
                step=param_config.get('step', 1)
            )
        
        # Set up objects
        for obj_config in self.current_exercise.get('objects', []):
            obj_type = obj_config.get('type')
            obj_name = obj_config.get('name', f'obj_{len(self.engine.objects)}')
            
            # Convert position if it's a dictionary with x,y
            position = obj_config.get('position', [0, 0])
            if isinstance(position, dict):
                x = position.get('x', 0)
                y = position.get('y', 0)
            else:
                x, y = position
            
            # Add the object to the engine
            self.engine.add_object(
                name=obj_name,
                obj_type=obj_type,
                x=x,
                y=y,
                **{k: v for k, v in obj_config.items() 
                   if k not in ['type', 'name', 'position']}
            )
        
        # Store the current simulation state
        self.current_simulation = {
            'parameters': self.current_exercise.get('parameters', {}).copy(),
            'targets': self.current_exercise.get('targets', []).copy(),
            'hints': self.current_exercise.get('hints', []).copy(),
            'feedback': self.current_exercise.get('feedback', {}).copy(),
            'user_answers': {},
            'hints_shown': []
        }
    
    def update_parameter(self, name: str, value: Any):
        """Update a simulation parameter.
        
        Args:
            name: Name of the parameter
            value: New value for the parameter
        """
        if not self.current_simulation:
            return
        
        # Update the parameter in the engine
        self.engine.update_parameter(name, value)
        
        # Update our local copy
        if name in self.current_simulation['parameters']:
            self.current_simulation['parameters'][name]['value'] = value
        
        # Notify listeners
        self._notify('on_parameter_change', name, value)
    
    def _get_exercise_objects(self):
        """Helper method to extract objects from exercise data structure."""
        if self.current_exercise is None:
            return {}
            
        # If it's a list, find the first exercise with objects
        if isinstance(self.current_exercise, list):
            for exercise in self.current_exercise:
                if isinstance(exercise, dict) and 'objects' in exercise:
                    if isinstance(exercise['objects'], dict):
                        return exercise['objects']
                    elif isinstance(exercise['objects'], list):
                        # Convert list of objects to dict with names as keys
                        return {obj.get('name', f'obj_{i}'): obj 
                               for i, obj in enumerate(exercise['objects'])}
        # If it's a dictionary, get objects directly
        elif isinstance(self.current_exercise, dict):
            objects = self.current_exercise.get('objects', {})
            if isinstance(objects, list):
                # Convert list of objects to dict with names as keys
                return {obj.get('name', f'obj_{i}'): obj 
                       for i, obj in enumerate(objects)}
            return objects
            
        return {}
    
    def run_simulation(self):
        """Run the simulation with the current parameters."""
        if not self.current_simulation:
            return
        
        # Set up the render surface if not already done
        if not hasattr(self.engine, 'surface') or self.engine.surface is None:
            try:
                self.engine.setup_render_surface()
                print("Initialized Pygame display window")
            except Exception as e:
                error_msg = f"Failed to initialize display: {str(e)}"
                print(error_msg)
                self._notify('on_error', error_msg)
                return
        
        # Reset the simulation
        self.engine.reset()
        
        # Get objects from exercise data
        objects = self._get_exercise_objects()
        
        # Set initial conditions
        for obj_name, obj_config in objects.items():
            if not isinstance(obj_config, dict):
                continue
                
            # Handle initial velocity if present
            if 'initial_velocity' in obj_config:
                if isinstance(obj_config['initial_velocity'], dict):
                    vx = obj_config['initial_velocity'].get('x', 0)
                    vy = obj_config['initial_velocity'].get('y', 0)
                else:
                    # Handle case where velocity is a single value or list
                    if isinstance(obj_config['initial_velocity'], (list, tuple)):
                        vx = obj_config['initial_velocity'][0] if len(obj_config['initial_velocity']) > 0 else 0
                        vy = obj_config['initial_velocity'][1] if len(obj_config['initial_velocity']) > 1 else 0
                    else:
                        vx = float(obj_config['initial_velocity'])
                        vy = 0
                
                # Apply velocity if the object exists in the engine
                if obj_name in self.engine.objects and 'body' in self.engine.objects[obj_name]:
                    self.engine.objects[obj_name]['body'].velocity = (vx, vy)
        
        # Add a ground plane for the simulation
        ground = pymunk.Segment(self.engine.space.static_body, (0, self.engine.height - 50), 
                               (self.engine.width, self.engine.height - 50), 1)
        ground.friction = 1.0
        self.engine.space.add(ground)
        
        # Add a simple projectile for demonstration
        if not objects:
            mass = 1
            radius = 10
            inertia = pymunk.moment_for_circle(mass, 0, radius, (0, 0))
            body = pymunk.Body(mass, inertia)
            body.position = 50, self.engine.height - 100
            shape = pymunk.Circle(body, radius, (0, 0))
            shape.elasticity = 0.8
            shape.friction = 0.5
            self.engine.space.add(body, shape)
        
        # Run the simulation
        print("Starting simulation... (Close the window to continue)")
        try:
            self.engine.run()
            self._notify('on_simulation_update')
        except Exception as e:
            error_msg = f"Error running simulation: {str(e)}"
            print(error_msg)
            self._notify('on_error', error_msg)
            raise RuntimeError(error_msg) from e
    
    def check_answers(self, answers: Dict[str, Any]) -> Dict[str, Any]:
        """Check the user's answers against the expected values.
        
        Args:
            answers: Dictionary of target IDs to user-provided answers
            
        Returns:
            Dictionary with results for each answer
        """
        if not self.current_simulation:
            return {}
        
        results = {}
        all_correct = True
        
        for target in self.current_simulation['targets']:
            target_id = target['id']
            user_answer = answers.get(target_id)
            
            if user_answer is None:
                results[target_id] = {
                    'correct': False,
                    'feedback': 'No answer provided',
                    'expected': target.get('value', 'N/A')
                }
                all_correct = False
                continue
            
            # Check the answer based on the target type
            if target['type'] == 'numeric':
                try:
                    user_value = float(user_answer)
                    expected_value = target['value']
                    tolerance = target.get('tolerance', 0.01)
                    
                    is_correct = abs(user_value - expected_value) <= tolerance
                    
                    results[target_id] = {
                        'correct': is_correct,
                        'feedback': 'Correct!' if is_correct else 'Incorrect',
                        'expected': expected_value
                    }
                    
                    if not is_correct:
                        all_correct = False
                        
                except (ValueError, TypeError):
                    results[target_id] = {
                        'correct': False,
                        'feedback': 'Invalid number format',
                        'expected': target.get('value', 'N/A')
                    }
                    all_correct = False
            
            # Add more answer types as needed (e.g., multiple choice, text, etc.)
            
            # Save the user's answer
            self.current_simulation['user_answers'][target_id] = user_answer
        
        # Provide overall feedback
        if all_correct:
            feedback = self.current_simulation['feedback'].get('correct', 'All answers are correct!')
        else:
            feedback = self.current_simulation['feedback'].get('incorrect', 'Some answers are incorrect.')
        
        results['_feedback'] = feedback
        
        # Notify listeners
        self._notify('on_feedback', results)
        
        return results
    
    def get_hint(self, target_id: str = None) -> str:
        """Get a hint for the current exercise or a specific target.
        
        Args:
            target_id: Optional ID of the target to get a hint for
            
        Returns:
            A hint string, or None if no hints are available
        """
        if not self.current_simulation:
            return None
        
        hints = self.current_simulation.get('hints', [])
        
        if target_id:
            # Get hints specific to this target
            target_hints = [h for h in hints if h.get('target') == target_id]
            if target_hints:
                hints = target_hints
        
        # Filter out hints that have already been shown
        available_hints = [h for h in hints if h.get('id') not in self.current_simulation['hints_shown']]
        
        if not available_hints:
            return "No more hints available."
        
        # Get the first available hint
        hint = available_hints[0]
        
        # Mark this hint as shown
        if 'id' in hint:
            self.current_simulation['hints_shown'].append(hint['id'])
        
        return hint.get('text', 'No hint available.')
    
    def save_results(self, filename: str = None):
        """Save the current simulation results to a file.
        
        Args:
            filename: Optional filename to save to. If not provided, 
                     a default name will be generated.
        """
        if not self.current_simulation:
            return
        
        if not filename:
            # Generate a default filename based on timestamp
            import datetime
            timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f'simulation_results_{timestamp}.json'
        
        # Make sure the filename has the right extension
        if not filename.endswith('.json'):
            filename += '.json'
        
        # Save to the results directory
        filepath = self.results_dir / filename
        
        # Prepare the results data
        results = {
            'timestamp': datetime.datetime.now().isoformat(),
            'exercise': self.current_exercise.get('name', 'Unnamed Exercise'),
            'parameters': self.current_simulation['parameters'],
            'user_answers': self.current_simulation['user_answers'],
            'targets': self.current_simulation['targets']
        }
        
        # Save to file
        with open(filepath, 'w') as f:
            json.dump(results, f, indent=2)
        
        return str(filepath)
    
    def register_callback(self, event: str, callback: Callable):
        """Register a callback function for simulation events.
        
        Args:
            event: Event name ('on_parameter_change', 'on_simulation_update', 'on_feedback')
            callback: Function to call when the event occurs
        """
        if event in self.callbacks:
            self.callbacks[event].append(callback)
    
    def _notify(self, event: str, *args, **kwargs):
        """Notify all registered callbacks for an event."""
        for callback in self.callbacks.get(event, []):
            try:
                callback(*args, **kwargs)
            except Exception as e:
                print(f"Error in {event} callback: {e}")
