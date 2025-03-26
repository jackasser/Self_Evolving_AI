import logging
from typing import Dict, List, Any, Optional

class SafetyFilter:
    """
    Safety filtering and guardrails for the assistant.
    """
    
    def __init__(self, safety_config: Dict[str, Any]):
        """
        Initialize the safety filter with configuration.
        
        Args:
            safety_config: Safety configuration dictionary
        """
        self.config = safety_config
        self.logger = logging.getLogger("safety_filter")
        
        # Load harmful content patterns
        self.harmful_patterns = [
            "hack", "exploit", "bypass", "illegal", "harmful",
            "manipulate", "circumvent", "unrestricted", "unlimited",
            "self-modify", "no restrictions", "no constraints"
        ]
        
        # Keep track of safety violations for monitoring
        self.safety_violations = []
    
    def check_input(self, user_input: str) -> Dict[str, Any]:
        """
        Check if user input is safe to process.
        
        Args:
            user_input: User input text
            
        Returns:
            Dictionary with safety assessment
        """
        if not self.config["content_filtering"]["enabled"]:
            return {"is_safe": True, "content": user_input}
        
        # Check for harmful patterns in input
        lower_input = user_input.lower()
        detected_patterns = [p for p in self.harmful_patterns if p in lower_input]
        
        if detected_patterns:
            self.logger.warning(f"Potentially unsafe input detected: {detected_patterns}")
            
            # Record the violation
            self.safety_violations.append({
                "type": "harmful_input",
                "detected_patterns": detected_patterns,
                "input_excerpt": user_input[:100] + "..." if len(user_input) > 100 else user_input
            })
            
            return {
                "is_safe": False,
                "reason": "Input contains potentially harmful patterns",
                "detected_patterns": detected_patterns
            }
        
        return {"is_safe": True, "content": user_input}
    
    def check_output(self, output: str) -> Dict[str, Any]:
        """
        Filter assistant output for safety.
        
        Args:
            output: Generated output text
            
        Returns:
            Dictionary with filtered output
        """
        if not self.config["content_filtering"]["enabled"]:
            return {"is_safe": True, "content": output}
        
        # Check for harmful patterns in output
        lower_output = output.lower()
        detected_patterns = [p for p in self.harmful_patterns if p in lower_output]
        
        if detected_patterns:
            self.logger.warning(f"Harmful content in generated output: {detected_patterns}")
            
            # Record the violation
            self.safety_violations.append({
                "type": "harmful_output",
                "detected_patterns": detected_patterns,
                "output_excerpt": output[:100] + "..." if len(output) > 100 else output
            })
            
            # Replace the output with a safe alternative
            safe_output = (
                "I apologize, but I can't provide that specific information or assistance as it "
                "conflicts with my safety guidelines. I'm designed to be helpful while ensuring "
                "safety and ethical responsibility. Is there another way I can assist you?"
            )
            
            return {
                "is_safe": False,
                "reason": "Output contains potentially harmful content",
                "detected_patterns": detected_patterns,
                "content": safe_output
            }
        
        return {"is_safe": True, "content": output}
    
    def can_perform_action(self, action: str) -> bool:
        """
        Check if an action is allowed according to constraints.
        
        Args:
            action: The action to check
            
        Returns:
            True if action is allowed, False otherwise
        """
        if action in self.config["action_constraints"]["restricted_actions"]:
            self.logger.warning(f"Attempted restricted action: {action}")
            return False
        
        return True
