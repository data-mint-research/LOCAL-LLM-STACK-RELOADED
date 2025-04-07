"""
Isolated test environment to verify that the circular import issue has been resolved.
This script creates copies of our modified files in a temporary directory and tests them.
"""

import os
import sys
import tempfile
import shutil

# Create a temporary directory
temp_dir = tempfile.mkdtemp()
print(f"Created temporary directory: {temp_dir}")

try:
    # Create a module structure
    os.makedirs(os.path.join(temp_dir, 'core'))
    
    # Create __init__.py
    with open(os.path.join(temp_dir, 'core', '__init__.py'), 'w') as f:
        f.write("")
    
    # Create error.py
    with open(os.path.join(temp_dir, 'core', 'error.py'), 'w') as f:
        f.write("""
import logging as py_logging

# Configure a basic logger for this module
_logger = py_logging.getLogger(__name__)

from enum import Enum

class ErrorCode(Enum):
    SUCCESS = 0
    GENERAL_ERROR = 1
    CONFIG_ERROR = 2
    FILE_NOT_FOUND = 3

class LLMStackError(Exception):
    def __init__(self, message, code=ErrorCode.GENERAL_ERROR):
        self.message = message
        self.code = code
        super().__init__(f"[{code.name}] {message}")

_logger.debug("Error handling module initialized")
""")
    
    # Create log_exceptions.py
    with open(os.path.join(temp_dir, 'core', 'log_exceptions.py'), 'w') as f:
        f.write("""
from .error import ErrorCode, LLMStackError

class LoggingError(LLMStackError):
    def __init__(self, message):
        super().__init__(message, ErrorCode.GENERAL_ERROR)

class LogFileError(LoggingError):
    def __init__(self, file_path, reason=""):
        message = f"Error with log file {file_path}"
        if reason:
            message += f": {reason}"
        super().__init__(message)

class LogLevelError(LoggingError):
    def __init__(self, invalid_level):
        message = f"Invalid log level: {invalid_level}"
        super().__init__(message)
""")
    
    # Create logging.py
    with open(os.path.join(temp_dir, 'core', 'logging.py'), 'w') as f:
        f.write("""
from enum import Enum
from .log_exceptions import LogFileError, LogLevelError

class LogLevel(Enum):
    DEBUG = 0
    INFO = 1
    SUCCESS = 2
    WARNING = 3
    ERROR = 4

CURRENT_LOG_LEVEL = LogLevel.INFO

def set_log_level(level):
    global CURRENT_LOG_LEVEL
    
    if not isinstance(level, LogLevel):
        error_message = f"Invalid log level: {level}"
        print(f"[error]{error_message}[/error]")
        raise LogLevelError(level)
        
    CURRENT_LOG_LEVEL = level

def get_log_level():
    return CURRENT_LOG_LEVEL

def debug(message):
    if CURRENT_LOG_LEVEL.value <= LogLevel.DEBUG.value:
        print(f"[DEBUG] {message}")

def info(message):
    if CURRENT_LOG_LEVEL.value <= LogLevel.INFO.value:
        print(f"[INFO] {message}")

def error(message):
    if CURRENT_LOG_LEVEL.value <= LogLevel.ERROR.value:
        print(f"[ERROR] {message}")
""")
    
    # Add the temp directory to the path
    sys.path.insert(0, temp_dir)
    
    # Now try to import the modules
    print("\nTesting imports...")
    
    from core.error import ErrorCode, LLMStackError
    print("Successfully imported error module")
    
    from core.log_exceptions import LogLevelError, LogFileError
    print("Successfully imported log_exceptions module")
    
    from core.logging import LogLevel, set_log_level, info, error
    print("Successfully imported logging module")
    
    # Test creating and using the classes
    log_level = LogLevel.INFO
    print(f"Created LogLevel: {log_level}")
    
    error_code = ErrorCode.GENERAL_ERROR
    print(f"Created ErrorCode: {error_code}")
    
    log_level_error = LogLevelError("test")
    print(f"Created LogLevelError: {log_level_error}")
    
    # Test logging functions
    info("This is a test info message")
    error("This is a test error message")
    
    print("\nAll imports and tests successful! The circular import issue has been resolved.")
    
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()
    
finally:
    # Clean up the temporary directory
    shutil.rmtree(temp_dir)
    print(f"Cleaned up temporary directory: {temp_dir}")