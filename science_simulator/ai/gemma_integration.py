"""
Gemma 3N Integration Module

This module handles the integration with the Gemma 3N model for text-to-simulation
conversion in the Science Simulation Lab.
"""
import os
import torch
from transformers import AutoTokenizer, AutoModelForCausalLM
from typing import Dict, Any, List, Optional
import json
import re
from pathlib import Path

class Gemma3NIntegration:
    """Handles integration with the Gemma 3N model for text-to-simulation conversion."""
    
    def __init__(self, model_name: str = "google/gemma-3n", device: str = None):
        """Initialize the Gemma 3N integration.
        
        Args:
            model_name: Name or path of the Gemma 3N model
            device: Device to run the model on ('cuda', 'mps', 'cpu'). If None, auto-detects.
        """
        self.model_name = model_name
        self.device = self._get_device(device)
        self.model = None
        self.tokenizer = None
        self.template_dir = Path(__file__).parent.parent / 'data' / 'prompts'
        
        # Create prompts directory if it doesn't exist
        self.template_dir.mkdir(parents=True, exist_ok=True)
        
        # Default prompt template paths
        self.default_templates = {
            'physics': 'physics_template.txt',
            'chemistry': 'chemistry_template.txt',
            'biology': 'biology_template.txt',
        }
        
        # Initialize default templates if they don't exist
        self._initialize_default_templates()
    
    def _get_device(self, device: str = None) -> str:
        """Determine the best available device.
        
        Args:
            device: Preferred device if specified
            
        Returns:
            Device string ('cuda', 'mps', or 'cpu')
        """
        if device:
            return device
            
        if torch.cuda.is_available():
            return 'cuda'
        elif torch.backends.mps.is_available():
            return 'mps'
        else:
            return 'cpu'
    
    def _initialize_default_templates(self):
        """Initialize default prompt templates if they don't exist."""
        # Physics template
        physics_template = """You are a physics simulation expert. Convert the following exercise into simulation parameters.

Exercise:
{exercise_text}

Instructions:
1. Extract all relevant parameters (e.g., mass, velocity, angle, etc.)
2. Determine the type of simulation (e.g., projectile, pendulum, etc.)
3. Provide values with appropriate units
4. Format the output as a JSON object with the following structure:
{{
  "simulation_type": "physics/projectile",
  "parameters": {{
    "mass": {{"value": 1.0, "unit": "kg"}},
    "initial_velocity": {{"value": 10.0, "unit": "m/s"}},
    "angle": {{"value": 45.0, "unit": "degrees"}},
    "gravity": {{"value": 9.8, "unit": "m/s²"}}
  }},
  "objects": [
    {{
      "type": "circle",
      "name": "projectile",
      "radius": 5,
      "initial_position": {{"x": 100, "y": 100}}
    }}
  ]
}}

Response:"""
        
        # Save the default templates
        for domain, template in [
            ('physics', physics_template),
            # Add other domain templates as needed
        ]:
            template_path = self.template_dir / self.default_templates[domain]
            if not template_path.exists():
                with open(template_path, 'w') as f:
                    f.write(template)
    
    def load_model(self):
        """Load the Gemma 3N model and tokenizer."""
        if self.model is None or self.tokenizer is None:
            print(f"Loading Gemma 3N model on {self.device}...")
            self.tokenizer = AutoTokenizer.from_pretrained(
                self.model_name,
                trust_remote_code=True
            )
            
            # Load model with 4-bit quantization to reduce memory usage
            self.model = AutoModelForCausalLM.from_pretrained(
                self.model_name,
                device_map="auto",
                torch_dtype=torch.float16 if self.device == 'cuda' else torch.float32,
                trust_remote_code=True,
                load_in_4bit=True  # Enable 4-bit quantization
            )
            self.model.eval()
    
    def generate_simulation_parameters(self, exercise_text: str, domain: str = 'physics') -> Dict[str, Any]:
        """Generate simulation parameters from exercise text.
        
        Args:
            exercise_text: The exercise description
            domain: The science domain ('physics', 'chemistry', 'biology')
            
        Returns:
            Dictionary containing simulation parameters
        """
        # Load model if not already loaded
        self.load_model()
        
        # Load the appropriate template
        template_path = self.template_dir / self.default_templates.get(domain, 'physics_template.txt')
        with open(template_path, 'r') as f:
            template = f.read()
        
        # Format the prompt
        prompt = template.format(exercise_text=exercise_text)
        
        # Generate response
        inputs = self.tokenizer(prompt, return_tensors="pt").to(self.device)
        
        with torch.no_grad():
            outputs = self.model.generate(
                **inputs,
                max_new_tokens=1024,
                temperature=0.7,
                do_sample=True,
                top_p=0.9,
                top_k=50,
                return_dict_in_generate=True,
                output_scores=True
            )
        
        # Decode the response
        response = self.tokenizer.decode(outputs.sequences[0], skip_special_tokens=True)
        
        # Extract JSON from the response
        json_match = re.search(r'\{.*\}', response, re.DOTALL)
        if not json_match:
            raise ValueError("Could not extract JSON from model response")
        
        try:
            return json.loads(json_match.group(0))
        except json.JSONDecodeError as e:
            raise ValueError(f"Failed to parse model response as JSON: {e}")
    
    def get_supported_domains(self) -> List[str]:
        """Get the list of supported science domains.
        
        Returns:
            List of supported domain names
        """
        return list(self.default_templates.keys())
    
    def add_custom_template(self, domain: str, template_path: str):
        """Add a custom prompt template for a specific domain.
        
        Args:
            domain: The science domain
            template_path: Path to the template file
        """
        if not os.path.exists(template_path):
            raise FileNotFoundError(f"Template file not found: {template_path}")
        
        # Copy the template to the prompts directory
        import shutil
        dest_path = self.template_dir / f"{domain}_template.txt"
        shutil.copy2(template_path, dest_path)
        
        # Update the default templates
        self.default_templates[domain] = dest_path.name


def test_gemma_integration():
    """Test the Gemma 3N integration with a sample exercise."""
    try:
        # Initialize the integration
        gemma = Gemma3NIntegration()
        
        # Sample exercise
        exercise = """
        A ball is thrown from the ground at an angle of 30 degrees with an initial velocity of 20 m/s.
        Calculate the maximum height reached and the horizontal distance traveled.
        Assume air resistance is negligible and g = 9.8 m/s².
        """
        
        # Generate simulation parameters
        print("Generating simulation parameters...")
        params = gemma.generate_simulation_parameters(exercise)
        
        print("\nGenerated Parameters:")
        print(json.dumps(params, indent=2))
        
        return params
    except Exception as e:
        print(f"Error in Gemma integration test: {e}")
        raise


if __name__ == "__main__":
    test_gemma_integration()
