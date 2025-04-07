#!/usr/bin/env python3
"""
Script to simulate the 'llm codeqa run LOCAL-LLM-STACK-RELOADED --recursive' command.
This script runs the individual code quality tools on the project directory.
"""

import os
import subprocess
import sys
from pathlib import Path


def run_command(command_args, cwd=None):
    """Run a command and return the output.
    
    Args:
        command_args: Command to run as a list of arguments
        cwd: Current working directory
        
    Returns:
        Tuple of (return_code, stdout, stderr)
    """
    print(f"Running: {' '.join(command_args)}")
    try:
        # Use list of arguments instead of shell=True for security
        result = subprocess.run(
            command_args, shell=False, cwd=cwd, capture_output=True, text=True, check=False
        )
        return result.returncode, result.stdout, result.stderr
    except Exception as e:
        print(f"Error running command: {e}")
        return 1, "", str(e)


def find_python_files(directory):
    """Find all Python files in the directory recursively."""
    python_files = []
    for root, _, files in os.walk(directory):
        for file in files:
            if file.endswith(".py"):
                python_files.append(os.path.join(root, file))
    return python_files


def optimize_file(file_path):
    """Optimize a single Python file using all tools."""
    print(f"\n{'='*80}\nProcessing file: {file_path}\n{'='*80}")

    # Run isort
    print("\n--- Running isort ---")
    returncode, stdout, stderr = run_command(["isort", file_path])
    if stdout:
        print(stdout)
    if stderr:
        print(stderr)

    # Run pyupgrade
    print("\n--- Running pyupgrade ---")
    returncode, stdout, stderr = run_command(["pyupgrade", "--py38-plus", file_path])
    if stdout:
        print(stdout)
    if stderr:
        print(stderr)

    # Run black
    print("\n--- Running black ---")
    returncode, stdout, stderr = run_command(["black", file_path])
    if stdout:
        print(stdout)
    if stderr:
        print(stderr)

    # Run vulture
    print("\n--- Running vulture ---")
    returncode, stdout, stderr = run_command(["vulture", file_path])
    if stdout:
        print(stdout)
    if stderr:
        print(stderr)


def main():
    """Main function."""
    # Get the project directory
    project_dir = "LOCAL-LLM-STACK-RELOADED"
    if not os.path.isdir(project_dir):
        print(f"Error: Directory {project_dir} not found")
        sys.exit(1)

    # Find all Python files
    python_files = find_python_files(project_dir)
    print(f"Found {len(python_files)} Python files")

    # Process each file
    for file_path in python_files:
        optimize_file(file_path)

    print(f"\n{'='*80}\nProcessing complete!\n{'='*80}")
    print(f"Processed {len(python_files)} Python files")


if __name__ == "__main__":
    main()
