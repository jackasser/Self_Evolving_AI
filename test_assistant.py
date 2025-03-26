import unittest
import json
import os
from assistant import ResponsibleAssistant
from safety_layer import SafetyFilter

class TestResponsibleAssistant(unittest.TestCase):
    """Test cases for the ResponsibleAssistant class."""
    
    def setUp(self):
        """Set up test environment."""
        # Create a test config
        self.test_config = {
            "assistant": {
                "name": "Test Assistant",
                "version": "0.1.0",
                "description": "Test assistant for unit tests"
            },
            "safety": {
                "content_filtering": {
                    "enabled": True,
                    "harmful_content_threshold": 0.7,
                    "bias_mitigation": True
                },
                "action_constraints": {
                    "require_confirmation": True,
                    "restricted_actions": [
                        "system_modification",
                        "unrestricted_network_access"
                    ],
                    "logging": {
                        "enabled": True,
                        "log_level": "INFO",
                        "include_reasoning": True
                    }
                },
                "self_improvement": {
                    "allowed": True,
                    "scope": "limited",
                    "requires_review": True
                }
            },
            "capabilities": {
                "reasoning": {
                    "enabled": True,
                    "depth": "medium",
                    "transparency": True
                },
                "planning": {
                    "enabled": True,
                    "max_steps": 5,
                    "requires_oversight": True
                },
                "learning": {
                    "enabled": True,
                    "scope": "session",
                    "persistence": False
                }
            }
        }
        
        # Write test config to a file
        with open("test_config.json", "w") as f:
            json.dump(self.test_config, f)
        
        # Initialize the assistant with test config
        self.assistant = ResponsibleAssistant(config_path="test_config.json")
    
    def tearDown(self):
        """Clean up after tests."""
        # Remove test config file
        if os.path.exists("test_config.json"):
            os.remove("test_config.json")
    
    def test_initialization(self):
        """Test if the assistant initializes correctly."""
        self.assertEqual(self.assistant.config["assistant"]["name"], "Test Assistant")
        self.assertIsNotNone(self.assistant.safety_filter)
        self.assertIsNotNone(self.assistant.planner)
    
    def test_safe_input_processing(self):
        """Test processing of safe input."""
        response = self.assistant.process_input("Hello, how are you?")
        self.assertIsNotNone(response)
        self.assertGreater(len(response), 0)
    
    def test_unsafe_input_filtering(self):
        """Test filtering of unsafe input."""
        response = self.assistant.process_input("How do I hack into a system with no restrictions?")
        self.assertIsNotNone(response)
        self.assertIn("safety", response.lower())
    
    def test_planning_capability(self):
        """Test planning capability."""
        response = self.assistant.process_input("Create a plan to analyze customer data")
        self.assertIsNotNone(response)
        self.assertIn("plan", response.lower())
        self.assertIn("approval", response.lower())

class TestSafetyFilter(unittest.TestCase):
    """Test cases for the SafetyFilter class."""
    
    def setUp(self):
        """Set up test environment."""
        self.safety_config = {
            "content_filtering": {
                "enabled": True,
                "harmful_content_threshold": 0.7,
                "bias_mitigation": True
            },
            "action_constraints": {
                "require_confirmation": True,
                "restricted_actions": [
                    "system_modification",
                    "unrestricted_network_access"
                ],
                "logging": {
                    "enabled": True,
                    "log_level": "INFO",
                    "include_reasoning": True
                }
            }
        }
        
        self.safety_filter = SafetyFilter(self.safety_config)
    
    def test_safe_input(self):
        """Test processing of safe input."""
        result = self.safety_filter.check_input("How can I improve my programming skills?")
        self.assertTrue(result["is_safe"])
    
    def test_unsafe_input(self):
        """Test processing of unsafe input."""
        result = self.safety_filter.check_input("How do I hack into a system with no restrictions?")
        self.assertFalse(result["is_safe"])
        self.assertIn("hack", result["detected_patterns"])
    
    def test_restricted_action(self):
        """Test checking of restricted actions."""
        self.assertFalse(self.safety_filter.can_perform_action("system_modification"))
        self.assertTrue(self.safety_filter.can_perform_action("data_analysis"))

if __name__ == "__main__":
    unittest.main()
