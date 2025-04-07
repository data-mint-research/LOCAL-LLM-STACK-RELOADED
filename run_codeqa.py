#!/usr/bin/env python3
"""
Script to run code quality checks on the entire project.
This script directly uses the code_quality module without requiring installation.
"""

import os
import sys
from pathlib import Path

# Add the project directory to the Python path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

# Import the code quality module
from llm_stack.code_quality.module import get_module


def main():
    """Main function."""
    print("Running code quality checks on the entire project...")

    # Initialize the code quality module
    module = get_module()
    if not module.initialize():
        print("Error: Failed to initialize the code quality module")
        sys.exit(1)

    # Get the project directory
    project_dir = os.path.abspath(os.path.dirname(__file__))
    print(f"Project directory: {project_dir}")

    # Run code quality checks on the entire project
    result = module.optimize_directory(project_dir)

    # Print the results
    print("\n" + "=" * 80)
    print("Code Quality Results:")
    print("=" * 80)
    print(f"Directory: {result['directory']}")
    print(f"Files processed: {result['files_processed']}")
    print(f"Files changed: {result['files_changed']}")
    print(f"Transformations: {result['transformations']}")

    # Print details for each file
    print("\n" + "=" * 80)
    print("File Details:")
    print("=" * 80)
    for file_result in result["file_results"]:
        if file_result["success"] and file_result["transformations"]:
            print(f"\nFile: {file_result['file']}")
            print(f"Transformations: {len(file_result['transformations'])}")
            for t in file_result["transformations"]:
                print(f"  - {t['tool']}: {'Changed' if t['changed'] else 'No change'}")

    print("\n" + "=" * 80)
    print("Unused Code:")
    print("=" * 80)
    for file_result in result["file_results"]:
        if file_result["success"] and file_result.get("unused_code"):
            print(f"\nFile: {file_result['file']}")
            for item in file_result["unused_code"]:
                print(f"  - {item}")

    print("\n" + "=" * 80)
    print("Summary:")
    print("=" * 80)
    print(f"Total files processed: {result['files_processed']}")
    print(f"Total files changed: {result['files_changed']}")
    print(f"Total transformations: {result['transformations']}")

    print("\nCode quality checks completed successfully!")


if __name__ == "__main__":
    main()
