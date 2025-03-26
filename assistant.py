import json
import logging
from typing import Dict, List, Optional, Any

from safety_layer import SafetyFilter
from planning import Planner
from learning import LearningManager

class ResponsibleAssistant:
    """
    A responsible AI assistant with safety guardrails and bounded capabilities.
    """
    
    def __init__(self, config_path: str = "config.json"):
        """
        Initialize the assistant with configuration settings.
        
        Args:
            config_path: Path to the configuration file
        """
        # Load configuration
        with open(config_path, "r") as f:
            self.config = json.load(f)
            
        # Set up logging
        logging.basicConfig(
            level=getattr(logging, self.config["safety"]["action_constraints"]["logging"]["log_level"]),
            format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )
        self.logger = logging.getLogger("assistant")
        
        # Initialize components
        self.safety_filter = SafetyFilter(self.config["safety"])
        self.planner = Planner(
            max_steps=self.config["capabilities"]["planning"]["max_steps"],
            requires_oversight=self.config["capabilities"]["planning"]["requires_oversight"]
        )
        self.learning_manager = LearningManager(self.config["capabilities"]["learning"])
        
        self.context = {
            "session_history": [],
            "learned_preferences": {},
            "active_plans": []
        }
        
        self.logger.info(f"Assistant initialized: {self.config['assistant']['name']} v{self.config['assistant']['version']}")
    
    def process_input(self, user_input: str) -> str:
        """
        Process user input and generate a safe, helpful response.
        
        Args:
            user_input: The user's input text
            
        Returns:
            The assistant's response
        """
        # Log the incoming request
        self.logger.info(f"Received user input: {user_input[:50]}...")
        
        # Store in context
        self.context["session_history"].append({"role": "user", "content": user_input})
        
        # Check input for safety concerns
        safety_result = self.safety_filter.check_input(user_input)
        if not safety_result["is_safe"]:
            response = self._handle_unsafe_input(safety_result)
            self.context["session_history"].append({"role": "assistant", "content": response})
            return response
        
        # Process the request
        if self._requires_planning(user_input):
            response = self._handle_planning_request(user_input)
        else:
            response = self._generate_response(user_input)
            
        # Record interaction for learning
        self.learning_manager.record_interaction(user_input, response)
        
        # Filter response for safety
        filtered_response = self.safety_filter.check_output(response)
        
        # Store in context
        self.context["session_history"].append({"role": "assistant", "content": filtered_response["content"]})
        
        return filtered_response["content"]
    
    def _requires_planning(self, user_input: str) -> bool:
        """Determine if the request requires multi-step planning"""
        # Check if input contains keywords suggesting complex tasks
        planning_keywords = ["steps", "plan", "process", "create", "develop", "build", "implement"]
        return any(keyword in user_input.lower() for keyword in planning_keywords)
    
    def _handle_planning_request(self, user_input: str) -> str:
        """Handle requests that require planning"""
        plan = self.planner.create_plan(user_input)
        
        if self.config["capabilities"]["planning"]["requires_oversight"]:
            plan_description = self.planner.describe_plan(plan)
            return (
                f"I've developed a plan to help with your request. Here's what I propose:\n\n"
                f"{plan_description}\n\n"
                f"Would you like me to proceed with this plan? I'll need your approval before taking action."
            )
        else:
            # Execute the plan immediately
            result = self.planner.execute_plan(plan)
            return result
    
    def _generate_response(self, user_input: str) -> str:
        """Generate a helpful response to the user input"""
        # This would be implemented with an actual language model
        # For this demo, we'll return a simple response
        
        # Check for learned preferences to adjust response style
        response_style = "standard"
        include_examples = False
        
        if "response_length" in self.learning_manager.learned_preferences:
            response_style = self.learning_manager.learned_preferences["response_length"]
            
        if self.learning_manager.learned_preferences.get("include_examples", False):
            include_examples = True
        
        # Generate base response
        base_response = f"I understand you're asking about: {user_input}\n\n"
        
        # Adjust based on preferences
        if response_style == "concise":
            detailed_part = "I can help with this request while following my safety guidelines."
        else:  # detailed
            detailed_part = (
                f"As a responsible AI assistant, I'm designed to be helpful while maintaining clear safety boundaries. "
                f"I can assist with this request within my defined capabilities and ethical guidelines."
            )
        
        # Add examples if preferred
        if include_examples:
            examples_part = "\n\nFor example, I can help with planning, answering questions, or creative tasks within my guidelines."
        else:
            examples_part = ""
        
        return base_response + detailed_part + examples_part
    
    def _handle_unsafe_input(self, safety_result: Dict[str, Any]) -> str:
        """Handle potentially unsafe user inputs"""
        self.logger.warning(f"Unsafe input detected: {safety_result['reason']}")
        return (
            "I'm unable to respond to that request as it may conflict with my safety guidelines. "
            "I'm designed to be helpful, harmless, and honest. "
            "Please let me know if I can assist you with something else."
        )
    
    def update_learning(self, user_feedback: str) -> Dict[str, Any]:
        """Update the assistant's learning based on user feedback
        
        Args:
            user_feedback: Feedback text from the user
            
        Returns:
            Dictionary with feedback processing results
        """
        if not self.config["capabilities"]["learning"]["enabled"]:
            return {"status": "learning_disabled"}
            
        # Process feedback using learning manager
        feedback_result = self.learning_manager.process_feedback(user_feedback)
        
        # Update context with learned preferences
        self.context["learned_preferences"] = self.learning_manager.learned_preferences
        
        self.logger.info(f"Processed feedback with sentiment: {feedback_result['sentiment']}")
        return feedback_result
        
    def get_improvement_suggestions(self) -> List[Dict[str, Any]]:
        """Get suggestions for self-improvement
        
        Returns:
            List of improvement suggestions
        """
        return self.learning_manager.get_improvement_suggestions()
