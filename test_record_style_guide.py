"""
Test script for recording style guide creation.
This is a simplified version of record_style_guide_creation.py that focuses on testing
the imports without requiring all dependencies.
"""

import os
import sys

# Add the project directory to the path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

# Test importing the core modules
try:
    print("Importing core modules...")
    from llm_stack.core import logging
    print("Successfully imported logging module")
    
    from llm_stack.core import error
    print("Successfully imported error module")
    
    from llm_stack.core.log_exceptions import LogLevelError, LogFileError
    print("Successfully imported log_exceptions module")
    
    # Test that we can use the modules
    logging.info("This is a test log message")
    print("Successfully used logging.info()")
    
    print("\nCore module imports successful! The circular import issue has been resolved.")
except ImportError as e:
    print(f"Import error: {e}")
    import traceback
    traceback.print_exc()
except Exception as e:
    print(f"Unexpected error: {e}")
    import traceback
    traceback.print_exc()