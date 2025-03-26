# Self-Evolving AI Installation Guide

This document explains the installation procedure for the Self-Evolving AI system.

## System Requirements

- Python 3.7 or higher
- Minimum 4GB RAM
- Minimum 2GB free disk space

## Installation Steps

### 1. Install Python

Ensure Python 3.7 or higher is installed on your system.

#### For Windows

1. Download and install Python from the [official Python website](https://www.python.org/downloads/)
2. Select the "Add Python to PATH" option during installation

#### For Linux/macOS

In most cases, Python is already installed. To check the version:

```bash
python3 --version
```

If needed, install from the package manager:

```bash
# For Ubuntu
sudo apt update
sudo apt install python3 python3-pip

# For macOS (using Homebrew)
brew install python3
```

### 2. Set Up the Project

1. Clone or download and extract the repository

2. Navigate to the project directory

```bash
cd path/to/agi
```

3. Create a virtual environment (recommended)

```bash
# For Windows
python -m venv venv
venv\Scripts\activate

# For Linux/macOS
python3 -m venv venv
source venv/bin/activate
```

4. Install dependencies

```bash
pip install -r requirements.txt
```

### 3. Configuration

Check the `config.json` file and adjust as needed. Main configuration items:

- `web_knowledge.trusted_domains`: Domains allowed for information retrieval
- `resource_management.memory_thresholds`: Warning and critical thresholds for memory usage
- `evolution.auto_evolution.interval_hours`: Interval for automatic evolution cycles

## Running the System

### For Windows

```
run_windows.bat
```

Or

```
python run_self_evolving_ai.py --config config.json
```

### For Linux/macOS

```
chmod +x run.sh  # Only needed for first run (to grant execution permission)
./run.sh
```

Or

```
python3 run_self_evolving_ai.py --config config.json
```

## Troubleshooting

### Encoding Issues (especially on Windows)

If you encounter encoding issues on Windows, set the following environment variables:

```
set PYTHONIOENCODING=utf-8
set PYTHONLEGACYWINDOWSSTDIO=utf-8
```

### Dependency Errors

If you encounter errors installing specific packages, try installing them individually:

```bash
pip install psutil
pip install <problematic_package_name>
```

### Permission Issues

If you encounter permission issues on Linux/macOS:

```bash
chmod +x run.sh
chmod -R u+rw .  # Grant read and write permissions to all files in the current directory
```

## Support

If problems persist, please report them in the issue tracker.
