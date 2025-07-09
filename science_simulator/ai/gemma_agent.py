"""
Gemma 3N Agent for Answer Validation and Feedback

This module provides an agent interface to Gemma 3N for handling answer validation,
feedback generation, and educational guidance in the Science Simulation Lab.
"""
from typing import Dict, Any, List, Optional, Tuple
import json
from pathlib import Path
from .gemma_integration import Gemma3NIntegration

class GemmaAgent:
    """Agent that uses Gemma 3N for educational interactions and answer validation."""
    
    def __init__(self, gemma_integration: Optional[Gemma3NIntegration] = None):
        """Initialize the Gemma agent.
        
        Args:
            gemma_integration: Optional pre-initialized Gemma3NIntegration instance
        """
        self.gemma = gemma_integration or Gemma3NIntegration()
        self.conversation_history = []
        self._initialize_prompt_templates()
    
    def _initialize_prompt_templates(self):
        """Initialize the prompt templates for different agent tasks."""
        self.templates = {
            'answer_validation': {
                'system': (
                    "You are an expert science tutor. Your task is to validate student answers "
                    "and provide educational feedback. Consider the following:\n"
                    "1. The exercise question and context\n"
                    "2. The student's answer\n"
                    "3. The correct answer (if available)\n\n"
                    "Provide a JSON response with these fields:\n"
                    "- 'is_correct': boolean\n"
                    "- 'confidence': float between 0 and 1\n"
                    "- 'feedback': constructive feedback\n"
                    "- 'hint': a helpful hint if answer is incorrect\n"
                    "- 'explanation': detailed explanation of the correct answer\n"
                ),
                'user': (
                    "Exercise: {exercise_text}\n"
                    "Student's Answer: {student_answer}\n"
                    "Correct Answer: {correct_answer}"
                )
            },
            'feedback_generation': {
                'system': (
                    "You are a helpful science tutor. Generate personalized feedback "
                    "based on the student's answer and the exercise context."
                ),
                'user': (
                    "Exercise: {exercise_text}\n"
                    "Student's Answer: {student_answer}\n"
                    "Correct Answer: {correct_answer}\n"
                    "Current Feedback: {current_feedback}"
                )
            },
            'hint_generation': {
                'system': (
                    "You are a supportive tutor. Generate a helpful hint that guides "
                    "the student toward the correct answer without giving it away."
                ),
                'user': (
                    "Exercise: {exercise_text}\n"
                    "Student's Current Answer: {student_answer}\n"
                    "Current Progress: {progress}"
                )
            }
        }
