import logging
import json
from typing import Dict, List, Any, Optional
from datetime import datetime

class LearningManager:
    """
    Manages bounded learning capabilities for the assistant.
    """
    
    def __init__(self, learning_config: Dict[str, Any]):
        """
        Initialize the learning manager with configuration.
        
        Args:
            learning_config: Learning configuration dictionary
        """
        self.config = learning_config
        self.logger = logging.getLogger("learning_manager")
        
        # Storage for learned information
        self.learned_preferences = {}
        self.interaction_patterns = {}
        self.feedback_history = []
        
        # Learning boundaries
        self.allowed_improvement_areas = self.config.get("improvement_areas", [
            "knowledge_base",
            "response_quality",
            "reasoning_process"
        ])
        
        self.logger.info("Learning manager initialized")
    
    def record_interaction(self, user_input: str, assistant_response: str) -> None:
        """
        Record an interaction for learning purposes.
        
        Args:
            user_input: User input text
            assistant_response: Assistant's response text
        """
        if not self.config.get("enabled", False):
            return
            
        # Extract patterns from the interaction
        self._extract_interaction_patterns(user_input, assistant_response)
        
        # Log the interaction
        self.logger.debug("Recorded interaction for learning")
    
    def process_feedback(self, feedback: str, interaction_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Process explicit feedback from the user.
        
        Args:
            feedback: Feedback text from the user
            interaction_id: Optional ID of the interaction being referenced
            
        Returns:
            Dictionary with feedback analysis
        """
        if not self.config.get("enabled", False):
            return {"status": "learning_disabled"}
            
        # Simple sentiment analysis
        sentiment = self._analyze_sentiment(feedback)
        
        # Record the feedback
        feedback_record = {
            "timestamp": datetime.now().isoformat(),
            "feedback": feedback,
            "sentiment": sentiment,
            "interaction_id": interaction_id
        }
        
        self.feedback_history.append(feedback_record)
        
        # Update preferences based on feedback
        if sentiment > 0:
            self._extract_positive_preferences(feedback)
        elif sentiment < 0:
            self._extract_negative_preferences(feedback)
        
        self.logger.info(f"Processed feedback with sentiment: {sentiment}")
        
        return {
            "status": "processed",
            "sentiment": sentiment,
            "feedback_id": len(self.feedback_history) - 1
        }
    
    def get_improvement_suggestions(self) -> List[Dict[str, Any]]:
        """
        Generate bounded self-improvement suggestions.
        
        Returns:
            List of improvement suggestions
        """
        if not self.config.get("enabled", False):
            return []
            
        # This is a simplified implementation
        # In a real system, this would use more sophisticated analysis
        
        suggestions = []
        
        # Check feedback history for patterns
        if self.feedback_history:
            negative_feedback_count = sum(1 for f in self.feedback_history if f["sentiment"] < 0)
            if negative_feedback_count > 3:
                suggestions.append({
                    "area": "response_quality",
                    "description": "Improve response quality based on negative feedback patterns",
                    "priority": "high",
                    "requires_review": True
                })
        
        # Check for knowledge gaps
        if "knowledge_base" in self.allowed_improvement_areas:
            # In a real system, this would analyze actual knowledge gaps
            suggestions.append({
                "area": "knowledge_base",
                "description": "Enhance knowledge in frequently discussed topics",
                "priority": "medium",
                "requires_review": True
            })
        
        return suggestions
    
    def _extract_interaction_patterns(self, user_input: str, assistant_response: str) -> None:
        """Extract patterns from an interaction."""
        # This is a simplified implementation
        # In a real system, this would use more sophisticated NLP
        
        # Extract topics
        topics = self._extract_topics(user_input)
        
        # Update interaction patterns
        for topic in topics:
            if topic not in self.interaction_patterns:
                self.interaction_patterns[topic] = 1
            else:
                self.interaction_patterns[topic] += 1
    
    def _extract_topics(self, text: str) -> List[str]:
        """Extract topics from text."""
        # This is a simplified implementation
        # In a real system, this would use more sophisticated NLP
        
        # Simple keyword-based topic extraction
        topics = []
        
        keywords = {
            "programming": ["code", "programming", "software", "development", "python", "java"],
            "data": ["data", "analysis", "analytics", "statistics", "visualization"],
            "business": ["business", "strategy", "marketing", "sales", "management"],
            "education": ["education", "learning", "teaching", "school", "student"]
        }
        
        lower_text = text.lower()
        
        for topic, words in keywords.items():
            if any(word in lower_text for word in words):
                topics.append(topic)
        
        return topics
    
    def _analyze_sentiment(self, text: str) -> float:
        """
        Analyze sentiment of text.
        
        Returns:
            Sentiment score (-1.0 to 1.0)
        """
        # This is a simplified implementation
        # In a real system, this would use more sophisticated NLP
        
        positive_words = ["good", "great", "excellent", "helpful", "thanks", "thank", "like", "love"]
        negative_words = ["bad", "unhelpful", "wrong", "incorrect", "confusing", "hate", "dislike"]
        
        lower_text = text.lower()
        
        positive_count = sum(1 for word in positive_words if word in lower_text)
        negative_count = sum(1 for word in negative_words if word in lower_text)
        
        if positive_count == 0 and negative_count == 0:
            return 0.0
            
        return (positive_count - negative_count) / (positive_count + negative_count)
    
    def _extract_positive_preferences(self, feedback: str) -> None:
        """Extract user preferences from positive feedback."""
        # This is a simplified implementation
        # In a real system, this would use more sophisticated NLP
        
        lower_feedback = feedback.lower()
        
        if "concise" in lower_feedback or "brief" in lower_feedback:
            self.learned_preferences["response_length"] = "concise"
        
        if "detailed" in lower_feedback or "thorough" in lower_feedback:
            self.learned_preferences["response_length"] = "detailed"
        
        if "examples" in lower_feedback:
            self.learned_preferences["include_examples"] = True
    
    def _extract_negative_preferences(self, feedback: str) -> None:
        """Extract user preferences from negative feedback."""
        # This is a simplified implementation
        # In a real system, this would use more sophisticated NLP
        
        lower_feedback = feedback.lower()
        
        if "too long" in lower_feedback or "too detailed" in lower_feedback:
            self.learned_preferences["response_length"] = "concise"
        
        if "too short" in lower_feedback or "not enough detail" in lower_feedback:
            self.learned_preferences["response_length"] = "detailed"
        
        if "no examples" in lower_feedback:
            self.learned_preferences["include_examples"] = True
