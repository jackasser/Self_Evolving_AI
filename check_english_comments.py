#!/usr/bin/env python3
"""
This script checks Python files in the project to ensure they have English comments.
It looks for common Japanese characters that would indicate untranslated comments.
"""

import os
import re
import sys

def is_likely_japanese(text):
    """Check if text contains Japanese characters."""
    # Check for hiragana, katakana, or kanji character ranges
    japanese_pattern = re.compile(r'[\u3040-\u309F\u30A0-\u30FF\u4E00-\u9FFF]')
    return bool(japanese_pattern.search(text))

def check_file(filepath):
    """Check a single file for Japanese characters in comments."""
    with open(filepath, 'r', encoding='utf-8') as f:
        try:
            content = f.read()
        except UnicodeDecodeError:
            return False, f"Error reading file: {filepath} (encoding issue)"
    
    # Extract comments (both single-line and multi-line)
    single_line_comments = re.findall(r'#.*$', content, re.MULTILINE)
    multi_line_comments = re.findall(r'""".*?"""', content, re.DOTALL)
    docstrings = re.findall(r"'''.*?'''", content, re.DOTALL)
    
    all_comments = single_line_comments + multi_line_comments + docstrings
    
    # Check if any comment contains Japanese characters
    japanese_comments = []
    for comment in all_comments:
        if is_likely_japanese(comment):
            japanese_comments.append(comment.strip())
    
    if japanese_comments:
        return False, f"Found {len(japanese_comments)} Japanese comments in {filepath}"
    
    return True, f"File {filepath} has English comments only"

def main():
    """Main function to check all Python files in the project."""
    print("Checking Python files for English comments...")
    
    # Get project root directory
    project_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Find all Python files
    python_files = []
    for root, dirs, files in os.walk(project_dir):
        # Skip venv and pycache directories
        if 'venv' in dirs:
            dirs.remove('venv')
        if '__pycache__' in dirs:
            dirs.remove('__pycache__')
        
        for file in files:
            if file.endswith('.py'):
                python_files.append(os.path.join(root, file))
    
    print(f"Found {len(python_files)} Python files to check.")
    
    # Check each file
    all_ok = True
    issues = []
    
    for filepath in python_files:
        ok, message = check_file(filepath)
        if not ok:
            all_ok = False
            issues.append(message)
            print(f"❌ {message}")
        else:
            print(f"✅ {message}")
    
    # Report results
    if all_ok:
        print("\n✅ All Python files have English comments!")
        return 0
    else:
        print(f"\n❌ Found {len(issues)} files with Japanese comments that need translation:")
        for issue in issues:
            print(f"  - {issue}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
