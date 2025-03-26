from typing import Dict, List, Any, Optional
import logging
import time
import uuid
from datetime import datetime

class Planner:
    """
    Planning capabilities for the assistant with safety guardrails.
    """
    
    def __init__(self, max_steps: int = 10, requires_oversight: bool = True):
        """
        Initialize the planner with safety parameters.
        
        Args:
            max_steps: Maximum number of steps in a plan
            requires_oversight: Whether human oversight is required
        """
        self.max_steps = max_steps
        self.requires_oversight = requires_oversight
        self.logger = logging.getLogger("planner")
        
        # Track active plans
        self.active_plans = {}
        
        # Plan history for learning and optimization
        self.plan_history = []
    
    def create_plan(self, objective: str) -> Dict[str, Any]:
        """
        Create a structured plan to achieve an objective.
        
        Args:
            objective: The objective to plan for
            
        Returns:
            A structured plan as a dictionary
        """
        self.logger.info(f"Creating plan for objective: {objective}")
        
        # This is a simplified implementation
        # In a real system, this would use more sophisticated planning algorithms
        
        # Extract key tasks from the objective
        tasks = self._extract_tasks(objective)
        
        # Limit the number of steps for safety
        if len(tasks) > self.max_steps:
            self.logger.warning(f"Plan exceeded max steps ({len(tasks)} > {self.max_steps}), truncating")
            tasks = tasks[:self.max_steps]
        
        # Create a structured plan
        plan_id = f"plan_{str(uuid.uuid4())[:8]}"
        plan = {
            "id": plan_id,
            "objective": objective,
            "tasks": tasks,
            "status": "pending_approval" if self.requires_oversight else "ready",
            "progress": 0,
            "results": {},
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat(),
            "execution_times": [],
            "metrics": {
                "planning_duration": 0,
                "execution_duration": 0,
                "success_rate": None
            }
        }
        
        # Store the plan
        self.active_plans[plan_id] = plan
        
        return plan
    
    def describe_plan(self, plan: Dict[str, Any]) -> str:
        """
        Generate a human-readable description of a plan.
        
        Args:
            plan: The plan to describe
            
        Returns:
            A string description of the plan
        """
        description = f"Plan to achieve: {plan['objective']}\n\n"
        
        for i, task in enumerate(plan["tasks"], 1):
            description += f"Step {i}: {task['description']}\n"
            if "reasoning" in task:
                description += f"   Reasoning: {task['reasoning']}\n"
        
        if self.requires_oversight:
            description += "\nThis plan requires your approval before execution."
        
        return description
    
    def execute_plan(self, plan: Dict[str, Any]) -> str:
        """
        Execute a plan with appropriate safety measures.
        
        Args:
            plan: The plan to execute
            
        Returns:
            Results of the plan execution
        """
        plan_id = plan["id"]
        start_time = time.time()
        
        if plan["status"] == "pending_approval" and self.requires_oversight:
            return "This plan requires approval before execution. Please confirm to proceed."
        
        self.logger.info(f"Executing plan {plan_id}")
        
        # Record execution start time
        self.active_plans[plan_id]["execution_times"].append({
            "start": datetime.now().isoformat(),
            "end": None
        })
        
        results = []
        for i, task in enumerate(plan["tasks"]):
            self.logger.info(f"Executing task {i+1}: {task['description']}")
            
            # Simulated task execution
            result = f"Completed: {task['description']}"
            results.append(result)
            
            # Update progress
            self.active_plans[plan_id]["progress"] = (i + 1) / len(plan["tasks"]) * 100
        
        # Update plan metrics
        end_time = time.time()
        execution_duration = end_time - start_time
        
        # Mark plan as complete
        self.active_plans[plan_id]["status"] = "completed"
        self.active_plans[plan_id]["results"] = results
        self.active_plans[plan_id]["updated_at"] = datetime.now().isoformat()
        self.active_plans[plan_id]["metrics"]["execution_duration"] = execution_duration
        self.active_plans[plan_id]["metrics"]["success_rate"] = 1.0  # Simplified implementation
        
        # Add to plan history
        completed_plan = self.active_plans[plan_id].copy()
        self.plan_history.append(completed_plan)
        
        return "\n".join(results)
    
    def approve_plan(self, plan_id: str) -> bool:
        """
        Approve a plan for execution.
        
        Args:
            plan_id: ID of the plan to approve
            
        Returns:
            True if approved successfully, False otherwise
        """
        if plan_id not in self.active_plans:
            self.logger.warning(f"Attempted to approve non-existent plan: {plan_id}")
            return False
        
        plan = self.active_plans[plan_id]
        if plan["status"] != "pending_approval":
            self.logger.warning(f"Attempted to approve plan with status {plan['status']}")
            return False
        
        plan["status"] = "ready"
        self.logger.info(f"Plan {plan_id} approved for execution")
        return True
    
    def _extract_tasks(self, objective: str) -> List[Dict[str, Any]]:
        """
        Extract a list of tasks from an objective.
        
        Args:
            objective: The objective to extract tasks from
            
        Returns:
            List of task dictionaries
        """
        # This is a simplified implementation
        # In a real system, this would use more sophisticated NLP and planning
        
        # Simple keyword-based task extraction
        tasks = []
        
        if "analyze" in objective.lower():
            tasks.append({
                "description": "Gather relevant data for analysis",
                "reasoning": "Data collection is necessary before any analysis can begin"
            })
            tasks.append({
                "description": "Perform initial data processing",
                "reasoning": "Raw data needs to be cleaned and formatted"
            })
            tasks.append({
                "description": "Conduct analysis",
                "reasoning": "Apply analytical methods to the processed data"
            })
            tasks.append({
                "description": "Summarize findings",
                "reasoning": "Compile results into a coherent summary"
            })
        elif "create" in objective.lower() or "build" in objective.lower():
            tasks.append({
                "description": "Define requirements and specifications",
                "reasoning": "Clear requirements are needed before building anything"
            })
            tasks.append({
                "description": "Design the structure or framework",
                "reasoning": "A solid design helps guide the implementation"
            })
            tasks.append({
                "description": "Implement core components",
                "reasoning": "Build the essential parts of the system"
            })
            tasks.append({
                "description": "Test and refine",
                "reasoning": "Ensure the creation works as expected"
            })
        else:
            # Generic task structure
            tasks.append({
                "description": "Analyze the objective",
                "reasoning": "Understanding the goal is the first step"
            })
            tasks.append({
                "description": "Identify key components",
                "reasoning": "Breaking down the problem into manageable parts"
            })
            tasks.append({
                "description": "Process each component",
                "reasoning": "Addressing each part of the problem"
            })
            tasks.append({
                "description": "Synthesize results",
                "reasoning": "Combining individual solutions into a coherent whole"
            })
        
        return tasks
        
    def get_plan_metrics(self) -> Dict[str, Any]:
        """
        Get metrics about plan execution and performance.
        
        Returns:
            Dictionary with plan performance metrics
        """
        metrics = {
            "total_plans": len(self.active_plans) + len(self.plan_history),
            "active_plans": len(self.active_plans),
            "completed_plans": len(self.plan_history),
            "average_execution_time": 0,
            "success_rate": 0,
            "task_complexity": {
                "average_steps": 0,
                "max_steps": 0
            }
        }
        
        # Calculate metrics from plan history
        if self.plan_history:
            # Average execution time
            execution_times = [p.get("metrics", {}).get("execution_duration", 0) for p in self.plan_history]
            metrics["average_execution_time"] = sum(execution_times) / len(execution_times) if execution_times else 0
            
            # Success rate
            success_rates = [p.get("metrics", {}).get("success_rate", 0) for p in self.plan_history]
            metrics["success_rate"] = sum(success_rates) / len(success_rates) if success_rates else 0
            
            # Task complexity
            step_counts = [len(p.get("tasks", [])) for p in self.plan_history]
            metrics["task_complexity"]["average_steps"] = sum(step_counts) / len(step_counts) if step_counts else 0
            metrics["task_complexity"]["max_steps"] = max(step_counts) if step_counts else 0
        
        return metrics
