"""
Exercise Parser Module

This module handles the conversion of natural language exercise descriptions
into simulation parameters that can be used by the simulation engine.
It uses the Gemma 3N model for advanced natural language understanding
with a fallback to rule-based parsing when needed.
"""
import spacy
import re
import json
from typing import Dict, Any, List, Optional, Union
import yaml
from pathlib import Path

# Import Gemma integration
from ..ai.gemma_integration import Gemma3NIntegration

class ExerciseParser:
    """Parses exercise descriptions into simulation parameters.
    
    This parser uses the Gemma 3N model for advanced natural language understanding
    with a fallback to rule-based parsing when needed.
    """
    
    def __init__(self, use_gemma: bool = True, gemma_model: str = "google/gemma-3n"):
        """Initialize the exercise parser with NLP models and templates.
        
        Args:
            use_gemma: Whether to use the Gemma 3N model for parsing
            gemma_model: Name or path of the Gemma 3N model to use
        """
        self.use_gemma = use_gemma
        
        # Initialize Gemma 3N integration if enabled
        self.gemma = None
        if self.use_gemma:
            try:
                self.gemma = Gemma3NIntegration(model_name=gemma_model)
                print("Gemma 3N model loaded successfully")
            except Exception as e:
                print(f"Failed to load Gemma 3N model: {e}")
                print("Falling back to rule-based parsing")
                self.use_gemma = False
        
        # Load the spaCy model for fallback parsing
        try:
            self.nlp = spacy.load("en_core_web_sm")
        except OSError:
            # If the model is not found, download it
            import subprocess
            import sys
            subprocess.check_call([sys.executable, "-m", "spacy", "download", "en_core_web_sm"])
            self.nlp = spacy.load("en_core_web_sm")
        
        # Load simulation templates
        self.templates = self._load_templates()
        
        # Regular expressions for extracting quantities (used in fallback mode)
        self.quantity_pattern = re.compile(
            r'\b(?:an?\s+)?'  # Optional 'a' or 'an'
            r'([0-9]+(?:\.[0-9]+)?)'  # Number (integer or float)
            r'\s*'  # Optional whitespace
            r'([a-zA-Z°²³/]*[a-zA-Z²³/]|%|°[CFK]?|m/s²)\b'  # Units
        )
        
        # Common unit conversions
        self.unit_conversions = {
            'm/s²': ('acceleration', 1.0, 'm/s²'),
            'm/s^2': ('acceleration', 1.0, 'm/s²'),
            'm/s': ('velocity', 1.0, 'm/s'),
            'kg': ('mass', 1.0, 'kg'),
            'g': ('mass', 0.001, 'kg'),
            'N': ('force', 1.0, 'N'),
            '°': ('angle', 1.0, 'degrees'),
            '°C': ('temperature', 1.0, '°C'),
            '°F': ('temperature', 0.5556, '°C'),  # Conversion to Celsius
            'K': ('temperature', 1.0, 'K'),
            'm': ('length', 1.0, 'm'),
            'cm': ('length', 0.01, 'm'),
            'mm': ('length', 0.001, 'm'),
            'km': ('length', 1000.0, 'm'),
        }
    
    def _load_templates(self) -> Dict[str, Any]:
        """Load simulation templates from YAML files.
        
        Returns:
            Dictionary of simulation templates
        """
        templates_dir = Path(__file__).parent.parent / 'data' / 'templates'
        templates = {}
        
        if templates_dir.exists():
            for template_file in templates_dir.glob('*.yaml'):
                with open(template_file, 'r') as f:
                    template_data = yaml.safe_load(f)
                    if isinstance(template_data, dict) and 'id' in template_data:
                        templates[template_data['id']] = template_data
        
        return templates
    
    def parse_exercise(self, description: str, domain: str = None) -> Dict[str, Any]:
        """Parse an exercise description into simulation parameters.
        
        This method first attempts to use the Gemma 3N model for parsing.
        If that fails or if use_gemma is False, it falls back to rule-based parsing.
        
        Args:
            description: The exercise description text
            domain: Optional domain hint ('physics', 'chemistry', 'biology')
            
        Returns:
            Dictionary containing simulation parameters
        """
        # Try using Gemma if enabled
        if self.use_gemma and self.gemma:
            try:
                # If no domain is provided, try to infer it
                if not domain:
                    domain = self._infer_domain(description)
                
                # Generate parameters using Gemma
                gemma_result = self.gemma.generate_simulation_parameters(
                    description, 
                    domain=domain or 'physics'  # Default to physics if domain is still None
                )
                
                # Add metadata
                gemma_result['parse_method'] = 'gemma_3n'
                gemma_result['domain'] = domain or 'physics'
                
                return gemma_result
                
            except Exception as e:
                print(f"Gemma parsing failed, falling back to rule-based parsing: {e}")
                self.use_gemma = False  # Disable Gemma for subsequent calls
        
        # Fall back to rule-based parsing
        return self._parse_exercise_rule_based(description)
    
    def _parse_exercise_rule_based(self, description: str) -> Dict[str, Any]:
        """Fallback method using rule-based parsing."""
        # Process the text with spaCy
        doc = self.nlp(description.lower())
        
        # Initialize result dictionary
        result = {
            'type': 'unknown',
            'parameters': {},
            'objects': [],
            'targets': [],
            'hints': [],
            'parse_method': 'rule_based',
            'domain': 'physics'  # Default domain for rule-based parsing
        }
        
        # Extract quantities with units
        quantities = self._extract_quantities(description)
        
        # Determine the type of exercise
        exercise_type = self._classify_exercise(doc, quantities)
        result['type'] = exercise_type
        
        # Apply template if available
        if exercise_type in self.templates:
            template = self.templates[exercise_type]
            result = self._apply_template(template, quantities, result)
        else:
            # Fallback to basic parameter extraction
            result['parameters'].update(self._extract_parameters(doc, quantities))
        
        return result
    
    def _infer_domain(self, text: str) -> str:
        """Infer the domain (physics, chemistry, biology) from the exercise text."""
        text_lower = text.lower()
        
        # Check for chemistry terms
        chem_terms = ['chemical', 'reaction', 'mole', 'molar', 'compound', 'element',
                     'acid', 'base', 'ph', 'molecule', 'atom', 'bond']
        if any(term in text_lower for term in chem_terms):
            return 'chemistry'
            
        # Check for biology terms
        bio_terms = ['cell', 'organism', 'species', 'dna', 'rna', 'protein',
                    'ecosystem', 'population', 'evolution', 'photosynthesis']
        if any(term in text_lower for term in bio_terms):
            return 'biology'
            
        # Default to physics
        return 'physics'
    
    def _extract_quantities(self, text: str) -> List[Dict[str, Any]]:
        """Extract quantities with units from text.
        
        Args:
            text: Input text
            
        Returns:
            List of dictionaries containing value, unit, and context
        """
        quantities = []
        
        for match in self.quantity_pattern.finditer(text):
            value = float(match.group(1))
            unit = match.group(2).strip()
            
            # Skip units we don't recognize
            if unit not in self.unit_conversions:
                continue
                
            # Get unit information
            quantity_type, factor, standard_unit = self.unit_conversions[unit]
            std_value = value * factor
            
            # Get the context (words around the match)
            start, end = match.span()
            context_start = max(0, start - 20)
            context_end = min(len(text), end + 20)
            context = text[context_start:context_end]
            
            quantities.append({
                'value': value,
                'unit': unit,
                'std_value': std_value,
                'std_unit': standard_unit,
                'type': quantity_type,
                'context': context
            })
        
        return quantities
    
    def _classify_exercise(self, doc, quantities: List[Dict[str, Any]]) -> str:
        """Classify the type of exercise based on the description.
        
        Args:
            doc: spaCy document
            quantities: List of extracted quantities
            
        Returns:
            String representing the exercise type
        """
        # Check for common physics scenarios
        text = doc.text.lower()
        
        # Check for projectile motion
        if any(term in text for term in ['projectile', 'thrown', 'launched', 'fired']) and \
           any(q['type'] == 'angle' for q in quantities):
            return 'projectile_motion'
            
        # Check for free fall
        if any(term in text for term in ['fall', 'dropped', 'free fall']) and \
           any(q['type'] == 'acceleration' for q in quantities):
            return 'free_fall'
            
        # Check for inclined plane
        if any(term in text for term in ['inclined', 'slope', 'ramp', 'angle of']) and \
           any(q['type'] == 'angle' for q in quantities):
            return 'inclined_plane'
            
        # Check for spring
        if 'spring' in text and ('stretch' in text or 'compress' in text):
            return 'spring_mass'
            
        # Default to unknown type
        return 'unknown'
    
    def _apply_template(self, template: Dict[str, Any], 
                       quantities: List[Dict[str, Any]],
                       result: Dict[str, Any]) -> Dict[str, Any]:
        """Apply a template to the extracted quantities.
        
        Args:
            template: Simulation template
            quantities: Extracted quantities
            result: Current result dictionary
            
        Returns:
            Updated result dictionary
        """
        # Apply parameter mappings
        for param_name, param_config in template.get('parameters', {}).items():
            if 'value' in param_config:
                # Use fixed value
                result['parameters'][param_name] = param_config['value']
            elif 'quantity' in param_config:
                # Find matching quantity
                for q in quantities:
                    if q['type'] == param_config['quantity']:
                        result['parameters'][param_name] = q['std_value']
                        break
        
        # Add objects
        result['objects'] = template.get('objects', [])
        
        # Add targets
        result['targets'] = template.get('targets', [])
        
        # Add hints
        result['hints'] = template.get('hints', [])
        
        return result
    
    def _extract_parameters(self, doc, quantities: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Extract generic parameters from the document.
        
        Args:
            doc: spaCy document
            quantities: Extracted quantities
            
        Returns:
            Dictionary of parameters
        """
        params = {}
        
        # Add quantities as parameters
        for i, q in enumerate(quantities):
            param_name = f"{q['type']}_{i+1}"
            params[param_name] = {
                'value': q['std_value'],
                'unit': q['std_unit'],
                'description': f"{q['value']} {q['unit']} from context: {q['context'][:50]}..."
            }
        
        return params
