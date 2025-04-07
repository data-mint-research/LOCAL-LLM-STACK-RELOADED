"""
Logging-related exceptions for the LLM Stack.

This module defines exceptions related to logging operations, separating them
from the main error module to avoid circular imports between logging and error modules.
"""

from enum import Enum
from typing import Any

from llm_stack.core.error import ErrorCode, LLMStackError


class LoggingError(LLMStackError):
    """Exception for logging errors."""

    def __init__(self, message: str):
        """
        Initializes a new logging error exception.

        Args:
            message: Error message
        """
        super().__init__(message, ErrorCode.GENERAL_ERROR)


class LogFileError(LoggingError):
    """Exception for log file errors."""
    
    def __init__(self, file_path: str, reason: str = ""):
        """
        Initializes a new log file error exception.

        Args:
            file_path: Path to the log file
            reason: Reason for the error (optional)
        """
        message = f"Error with log file {file_path}"
        if reason:
            message += f": {reason}"
        super().__init__(message)


class LogLevelError(LoggingError):
    """Exception for log level errors."""
    
    def __init__(self, invalid_level: Any):
        """
        Initializes a new log level error exception.
        
        Args:
            invalid_level: The invalid log level
        """
        message = f"Invalid log level: {invalid_level}"
        super().__init__(message)