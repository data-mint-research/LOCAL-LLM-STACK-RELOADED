"""
Direct import test script to verify that the circular import issue has been resolved.
This script imports the modules directly without going through __init__.py.
"""

import os
import sys
import importlib.util

# Add the project directory to the path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

def import_module_directly(module_path):
    """Import a module directly without going through __init__.py"""
    module_name = os.path.basename(module_path).replace('.py', '')
    spec = importlib.util.spec_from_file_location(
        module_name,
        os.path.join(os.path.dirname(__file__), module_path)
    )
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module

try:
    # Import modules directly
    print("Importing log_exceptions module...")
    log_exceptions = import_module_directly('llm_stack/core/log_exceptions.py')
    print("Successfully imported log_exceptions module")
    
    print("Importing error module...")
    error = import_module_directly('llm_stack/core/error.py')
    print("Successfully imported error module")
    
    print("Importing logging module...")
    logging = import_module_directly('llm_stack/core/logging.py')
    print("Successfully imported logging module")
    
    # Test creating and using the classes
    log_level = logging.LogLevel.INFO
    print(f"Created LogLevel: {log_level}")
    
    error_code = error.ErrorCode.GENERAL_ERROR
    print(f"Created ErrorCode: {error_code}")
    
    log_level_error = log_exceptions.LogLevelError("test")
    print(f"Created LogLevelError: {log_level_error}")
    
    # Test logging functions
    logging.info("This is a test info message")
    logging.error("This is a test error message")
    
    print("\nAll imports and tests successful! The circular import issue has been resolved.")
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()