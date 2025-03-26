import os
import json
import argparse
import time
import sys
from datetime import datetime

from self_evolving_ai import SelfEvolvingAI
from dummy_components import DummySafetyFilter, DummyProcessOptimizer, DummyResourceManager, DummySelfPreservation, DummyGoalManager, DummyFeedbackSystem, DummyWebKnowledgeFetcher

def clear_screen():
    """Clear the console screen."""
    os.system('cls' if os.name == 'nt' else 'clear')

def print_header(mode="basic"):
    """Print application header."""
    print("=" * 80)
    
    if mode == "evolving":
        print("  Self-Evolving AI  ".center(80))
        print("=" * 80)
        print("\nAI assistant that autonomously learns, accumulates knowledge, and self-optimizes")
        print("Type 'exit' or 'quit' to end the session.")
        print("Special commands:")
        print("  /status  - Display system status")
        print("  /evolve  - Run evolution cycle")
        print("  /help    - Display command list")
        print("  /search:query - Search for information from the web (example: /search:artificial intelligence)\n")
    else:
        print("  Responsible AI Assistant Demo  ".center(80))
        print("=" * 80)
        print("\nA demonstration of AI with safety guardrails and bounded capabilities.")
        print("Type 'exit' or 'quit' to end the session.\n")

def run_basic_assistant(args):
    """Run the basic responsible assistant mode"""
    # Initialize the assistant
    assistant = ResponsibleAssistant(config_path=args.config)
    
    # Main interaction loop
    clear_screen()
    print_header("basic")
    
    session_active = True
    while session_active:
        # Get user input
        user_input = input("\nYou: ")
        
        # Check for exit command
        if user_input.lower() in ["exit", "quit"]:
            print("\nThank you for using the Responsible AI Assistant. Goodbye!")
            session_active = False
            continue
        
        # Process the input and get response
        try:
            response = assistant.process_input(user_input)
            print(f"\nAssistant: {response}")
        except Exception as e:
            if args.debug:
                print(f"\nError: {str(e)}")
            else:
                print("\nAssistant: I encountered an issue processing your request. Please try again.")
    
        # Special commands
        if user_input.startswith("/"):
            cmd_parts = user_input[1:].split()
            command = cmd_parts[0].lower()
            
            if command == "debug" and args.debug:
                print("\n[DEBUG INFO]")
                print(f"Active plans: {json.dumps(assistant.planner.active_plans, indent=2)}")
                print(f"Safety violations: {json.dumps(assistant.safety_filter.safety_violations, indent=2)}")
                print(f"Context size: {len(assistant.context['session_history'])}")

def run_evolving_assistant(args):
    """Run the self-evolving AI mode"""
    # Initialize the self-evolving AI
    ai = SelfEvolvingAI(config_path=args.config)
    
    # Start the AI
    ai.start()
    
    # Main interaction loop
    clear_screen()
    print_header("evolving")
    
    session_active = True
    while session_active:
        # Get user input
        user_input = input("\nYou > ")
        
        # Check for exit command
        if user_input.lower() in ["exit", "quit"]:
            print("\nShutting down the system. Thank you for using it.")
            ai.stop()
            session_active = False
            continue
        
        # Check for special commands
        if user_input.startswith("/"):
            if user_input.lower() == "/status":
                show_system_status(ai)
                continue
                
            elif user_input.lower() == "/evolve":
                run_evolution_cycle(ai)
                continue
                
            elif user_input.lower() == "/help":
                show_help()
                continue
                
            # Handle search command
            elif user_input.lower().startswith("/search:"):
                query = user_input[8:].strip()
                if query:
                    print(f"\nSearching for \"{query}\"...")
                    response = ai.search_web_knowledge(query)
                    
                    if response["status"] == "success":
                        items = response.get("knowledge_items", [])
                        print(f"\n{len(items)} pieces of information found.")
                        
                        for i, item in enumerate(items[:5], 1):
                            print(f"\n{i}. {item.get('content')}")
                            
                        if len(items) > 5:
                            print(f"\n...{len(items)-5} more items available.")
                    else:
                        print(f"\nSearch error: {response.get('error', 'No information found')}")
                else:
                    print("\nPlease enter a search query. Example: /search:artificial intelligence")
                continue
        
        # Process regular input
        try:
            response = ai.process_input(user_input)
            print(f"\nAI > {response}")
        except Exception as e:
            if args.debug:
                print(f"\nError: {str(e)}")
            else:
                print("\nAI > A problem occurred while processing your request. Please try again.")

def show_system_status(ai):
    """Display system status"""
    status = ai.get_system_status()
    
    print("\n" + "=" * 50)
    print("System Status".center(50))
    print("=" * 50)
    
    # Basic information
    print(f"\nBasic Information:")
    print(f"  Status: {status['system_state']['status']}")
    print(f"  Start Time: {status['system_state']['started_at']}")
    print(f"  Uptime: {status['uptime_seconds']:.1f} seconds")
    print(f"  Evolution Cycles: {status['evolution_cycles_completed']}")
    
    # Health information
    print(f"\nHealth Information:")
    print(f"  Health Score: {status['health']['health_score']}")
    print(f"  Status: {status['health']['status']}")
    print(f"  Error Components: {len(status['health']['error_components'])}")
    
    # Resource information
    print(f"\nResource Information:")
    print(f"  Memory Usage: {status['resources']['system']['memory_usage_percent']}%")
    print(f"  CPU Usage: {status['resources']['system']['cpu_usage_percent']}%")
    
    # Goals and optimizations
    print(f"\nGoals and Optimizations:")
    print(f"  Active Goals: {status['active_goals']}")
    print(f"  Active Optimizations: {status['active_optimizations']}")
    print(f"  Completed Goals: {status['system_state']['goals_completed']}")
    
    # Knowledge base information
    kb_stats = ai.get_knowledge_stats()
    print(f"\nKnowledge Base:")
    print(f"  Facts: {kb_stats['facts_count']} items")
    print(f"  Concepts: {kb_stats['concepts_count']} items")
    print(f"  Methods: {kb_stats['methods_count']} items")
    print(f"  Relations: {kb_stats['relations_count']} items")
    print(f"  Total: {kb_stats['total_items']} items")
    
    print("\n" + "=" * 50)

def run_evolution_cycle(ai):
    """Run an evolution cycle"""
    print("\nRunning evolution cycle...")
    start_time = time.time()
    
    try:
        result = ai.run_evolution_cycle()
        duration = time.time() - start_time
        
        print(f"\nEvolution cycle completed ({duration:.2f} seconds)")
        print(f"New goals: {result['goals']['new_goals_set']} set")
        print(f"Goals updated: {result['goals']['goals_updated']} updated")
        print(f"Optimizations implemented: {result['optimizations']['optimizations_implemented']}")
        print(f"Optimizations completed: {result['optimizations']['optimizations_completed']}")
        print(f"Knowledge expansions: {result['knowledge']['successful_expansions']}")
        
    except Exception as e:
        print(f"\nAn error occurred while running the evolution cycle: {str(e)}")

def show_help():
    """Show help information"""
    print("\n" + "=" * 50)
    print("Command List".center(50))
    print("=" * 50)
    print("\nGeneral conversation: Enter normal text and the AI will respond")
    print("\nSpecial commands:")
    print("  /status  - Display the current system status")
    print("  /evolve  - Manually run an evolution cycle")
    print("  /help    - Display this help message")
    print("  /search:query - Run a web search for the specified query")
    print("  exit or quit - Exit the program")
    print("\n" + "=" * 50)

def main():
    """Main application entry point."""
    parser = argparse.ArgumentParser(description="AI Assistant Demo")
    parser.add_argument("--config", default="config.json", help="Path to configuration file")
    parser.add_argument("--debug", action="store_true", help="Enable debug mode")
    parser.add_argument("--mode", choices=["basic", "evolving"], default="evolving", 
                       help="Assistant mode: basic or evolving (default: evolving)")
    args = parser.parse_args()
    
    # Handle character encoding for Windows
    if sys.platform == 'win32':
        import locale
        sys_enc = locale.getpreferredencoding()
        # Set UTF-8 as the default encoding
        if sys_enc != 'utf-8':
            # Reconfigure stdout with utf-8
            if hasattr(sys.stdout, 'reconfigure'):
                sys.stdout.reconfigure(encoding='utf-8')
    
    try:
        # Run based on mode
        if args.mode == "basic":
            run_basic_assistant(args)
        else:
            run_evolving_assistant(args)
    except KeyboardInterrupt:
        print("\n\nProgram interrupted.")
    except Exception as e:
        print(f"\nAn error occurred: {str(e)}")
        if args.debug:
            import traceback
            traceback.print_exc()
    
    return 0

if __name__ == "__main__":
    main()
