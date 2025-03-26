# Self-Evolving AI

Self-Evolving AI is a concept implementation of an AI assistant that autonomously learns, accumulates knowledge, and self-optimizes.

## Overview

This system features:

- Continuous learning and self-evolution
- Autonomous goal setting and tracking
- Self-evaluation and adjustment capabilities
- Safety mechanisms and self-preservation functions
- Resource management and optimization

## System Components

- **SelfEvolvingAI**: Main AI system
- **ResponsibleAssistant**: Basic assistant functions
- **GoalManager**: Goal setting and management
- **SelfFeedbackSystem**: Self-evaluation and adjustment
- **ProcessOptimizer**: Process optimization
- **ResourceManager**: Resource management
- **SelfPreservation**: System stability maintenance
- **WebKnowledgeFetcher**: Web information retrieval

## Usage

### Running on Windows

```
run_windows.bat
```

### Running on Linux/macOS

```
chmod +x run.sh  # Only needed for first run (to grant execution permission)
./run.sh
```

## Special Commands

The following special commands can be used during conversation with the AI:

- `/status` - Display the current system status
- `/evolve` - Manually run an evolution cycle
- `/help` - Display command list
- `/search:query` - Search for information from the web (example: /search:artificial intelligence)
- `exit` or `quit` - Exit the program

## Technical Details

### Configuration

Settings are managed in the `config.json` file. Main configuration items:

- Safety settings
- Evolution cycle settings
- Resource management settings
- Network access settings

### Evolution Cycle

The system periodically runs an "evolution cycle" with the following steps:

1. Goal setting/updating
2. Process optimization
3. Parameter adjustment
4. Knowledge expansion

### Self-Preservation Mechanism

The system includes the following self-preservation capabilities:

- Periodic state saving
- Error detection and recovery
- Component monitoring
- Safe shutdown

## Extensions and Improvements

This system can be extended and improved in the following directions:

- Implementation of more advanced learning algorithms
- Integration with external systems
- Development of dedicated user interfaces
- Distributed processing support
