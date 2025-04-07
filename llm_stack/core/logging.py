"""
Logging functions for the LLM Stack.

This module provides functions for logging messages with various
levels and formatting options. It supports console output with rich formatting
and optional file output. All functions raise appropriate exceptions
when errors occur instead of returning error codes.

The module defines a LogLevel enum for different severity levels and provides
functions to configure logging behavior, such as setting the log level and
log file. The primary logging functions (debug, info, success, warn, error)
correspond to different severity levels.
"""

import os
import sys
from datetime import datetime
from enum import Enum
from typing import Optional, TextIO, Union

from rich.console import Console
from rich.theme import Theme

from llm_stack.core.log_exceptions import LogFileError, LogLevelError

# Rich console with custom color scheme
CUSTOM_THEME = Theme(
    {
        "info": "cyan",
        "success": "green",
        "warning": "yellow",
        "error": "bold red",
        "debug": "dim blue",
        "timestamp": "dim",
    }
)

CONSOLE = Console(theme=CUSTOM_THEME)


# Log levels
class LogLevel(Enum):
    """Log levels for the logger.
    
    Defines the severity levels for logging messages, with higher values
    indicating higher severity. Only messages with a level equal to or higher
    than the current log level will be displayed.
    
    Attributes:
        DEBUG: Detailed information for debugging purposes.
        INFO: General information about program execution.
        SUCCESS: Successful operations.
        WARNING: Potential issues that don't prevent execution.
        ERROR: Errors that prevent a function from completing.
    """
    DEBUG = 0
    INFO = 1
    SUCCESS = 2
    WARNING = 3
    ERROR = 4


# Current log level (default: INFO)
CURRENT_LOG_LEVEL: LogLevel = LogLevel.INFO

# Log file
LOG_FILE: Optional[TextIO] = None


def set_log_level(level: LogLevel) -> None:
    """Sets the current log level.
    
    Changes the global log level setting to filter which messages are displayed.
    Only messages with a level equal to or higher than this setting will be shown.
    
    Args:
        level: The log level to set. Must be a valid LogLevel enum value.
        
    Raises:
        LogLevelError: If the provided level is not a valid LogLevel enum value.
    """
    global CURRENT_LOG_LEVEL
    
    # Validate that the level is a valid LogLevel
    if not isinstance(level, LogLevel):
        error_message = f"Invalid log level: {level}"
        CONSOLE.print(f"[error]{error_message}[/error]")
        raise LogLevelError(level)
        
    CURRENT_LOG_LEVEL = level


def get_log_level() -> LogLevel:
    """Returns the current log level.
    
    Retrieves the global log level setting that determines which messages
    are displayed.
    
    Returns:
        LogLevel: The current log level enum value.
    """
    return CURRENT_LOG_LEVEL


def set_log_file(file_path: str) -> None:
    """Sets the log file for writing log messages.
    
    Opens a file for appending log messages. Creates the directory structure
    if it doesn't exist. All subsequent log messages will be written to both
    the console and this file.
    
    Args:
        file_path: Path to the log file. The directory will be created if it
            doesn't exist.
    
    Raises:
        LogFileError: If there was an error creating the directory or opening
            the log file.
    """
    global LOG_FILE

    try:
        # Ensure the directory exists
        os.makedirs(os.path.dirname(file_path), exist_ok=True)

        # Open log file
        LOG_FILE = open(file_path, "a")
    except Exception as e:
        error_message = f"Error opening log file: {str(e)}"
        CONSOLE.print(f"[error]{error_message}[/error]")
        raise LogFileError(file_path, str(e)) from e


def close_log_file() -> None:
    """Closes the log file if it is open.
    
    Safely closes the current log file if one is open. After closing,
    log messages will only be output to the console.
    
    Raises:
        LogFileError: If there was an error closing the log file.
    """
    global LOG_FILE

    if LOG_FILE:
        try:
            LOG_FILE.close()
        except Exception as e:
            error_message = f"Error closing log file: {str(e)}"
            CONSOLE.print(f"[error]{error_message}[/error]")
            # We still set LOG_FILE to None to prevent further usage
            LOG_FILE = None
            raise LogFileError("current log file", str(e)) from e
        LOG_FILE = None


def get_log_file_path() -> Optional[str]:
    """Returns the path of the current log file if one is set.
    
    Retrieves the file path of the currently open log file. If no log file
    is set or if there's an error accessing the file name, returns None.
    
    Returns:
        Optional[str]: The path of the current log file, or None if no log file
            is set or if the file name cannot be accessed.
    """
    global LOG_FILE
    
    if LOG_FILE and not LOG_FILE.closed:
        try:
            return LOG_FILE.name
        except Exception:
            return None
    return None


def _log(level: LogLevel, message: str, style: str, timestamp: bool = True) -> None:
    """Internal function for logging a message.
    
    Core logging implementation used by all public logging functions.
    Handles filtering by log level, formatting with timestamps and styles,
    console output with rich formatting, and plain text file output.
    
    Args:
        level: Log level of the message. Messages below the current log level
            will be filtered out.
        message: The message text to log.
        style: Rich style name for console formatting (e.g., "info", "error").
        timestamp: Whether to display a timestamp with the message. Defaults to True.
    
    Note:
        This function intentionally does not raise exceptions when writing to the
        log file fails, to prevent disrupting the application just because logging
        failed. Errors are printed to the console instead.
    """
    # Check if the message should be logged
    if level.value < CURRENT_LOG_LEVEL.value:
        return

    # Create timestamp
    ts = ""
    if timestamp:
        ts = f"[timestamp]{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}[/timestamp] "

    # Format message
    formatted_message = f"{ts}[{style}]{message}[/{style}]"

    # Output message to the console
    CONSOLE.print(formatted_message)

    # Write message to the log file if it is open
    if LOG_FILE:
        try:
            # Remove formatting for the file
            plain_ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            plain_message = f"{plain_ts} [{level.name}] {message}\n"
            LOG_FILE.write(plain_message)
            LOG_FILE.flush()
        except Exception as e:
            # Don't use the logging functions here to avoid recursion
            CONSOLE.print(f"[error]Error writing to log file: {str(e)}[/error]")
            # We don't raise the exception here to prevent disrupting the application
            # just because logging failed


def debug(message: str) -> None:
    """Logs a debug message.
    
    Outputs a message at DEBUG level. These messages contain detailed information
    useful for debugging and troubleshooting. They are only displayed if the
    current log level is set to DEBUG.
    
    Args:
        message: The message text to log.
    """
    _log(LogLevel.DEBUG, message, "debug")


def info(message: str) -> None:
    """Logs an info message.
    
    Outputs a message at INFO level. These messages provide general information
    about program execution and are displayed if the current log level is
    set to INFO or lower.
    
    Args:
        message: The message text to log.
    """
    _log(LogLevel.INFO, message, "info")


def success(message: str) -> None:
    """Logs a success message.
    
    Outputs a message at SUCCESS level. These messages indicate successful
    operations and are displayed if the current log level is set to SUCCESS
    or lower.
    
    Args:
        message: The message text to log.
    """
    _log(LogLevel.SUCCESS, message, "success")


def warn(message: str) -> None:
    """Logs a warning message.
    
    Outputs a message at WARNING level. These messages indicate potential issues
    that don't prevent execution but might require attention. They are displayed
    if the current log level is set to WARNING or lower.
    
    Args:
        message: The message text to log.
    """
    _log(LogLevel.WARNING, message, "warning")


def error(message: str) -> None:
    """Logs an error message.
    
    Outputs a message at ERROR level. These messages indicate errors that
    prevent a function from completing successfully. They are displayed
    if the current log level is set to ERROR or lower.
    
    Args:
        message: The message text to log.
    """
    _log(LogLevel.ERROR, message, "error")


# Alias for warn
from typing import Callable
warning: Callable[[str], None] = warn


# Set log level from environment variable
def init_logging() -> None:
    """Initializes the logging system based on environment variables.
    
    Sets up the logging system by reading configuration from environment variables:
    - LLM_STACK_LOG_LEVEL: Sets the log level (DEBUG, INFO, WARNING, ERROR)
    - LLM_STACK_LOG_FILE: Sets the log file path if specified
    
    If the log level environment variable is not recognized, defaults to INFO.
    If the log file cannot be opened, logs an error but continues without file logging.
    """
    # Get log level from environment variable
    log_level_str = os.environ.get("LLM_STACK_LOG_LEVEL", "INFO").upper()

    # Set log level
    try:
        if log_level_str == "DEBUG":
            set_log_level(LogLevel.DEBUG)
        elif log_level_str == "INFO":
            set_log_level(LogLevel.INFO)
        elif log_level_str == "WARNING" or log_level_str == "WARN":
            set_log_level(LogLevel.WARNING)
        elif log_level_str == "ERROR":
            set_log_level(LogLevel.ERROR)
        else:
            # If the log level string is not recognized, default to INFO
            console.print(f"[warning]Unrecognized log level: {log_level_str}, defaulting to INFO[/warning]")
            set_log_level(LogLevel.INFO)
    except LogLevelError as e:
        # This should not happen with our controlled inputs above, but handle it just in case
        console.print(f"[error]Error setting log level: {str(e)}, defaulting to INFO[/error]")
        # Directly set the level without validation to avoid potential recursion
        global CURRENT_LOG_LEVEL
        CURRENT_LOG_LEVEL = LogLevel.INFO

    # Get log file from environment variable
    log_file_path = os.environ.get("LLM_STACK_LOG_FILE")
    if log_file_path:
        try:
            set_log_file(log_file_path)
        except LogFileError as e:
            # Log the error but continue without a log file
            error(f"Failed to set log file: {str(e)}")

    debug("Logging system initialized")


# Initialize logging
init_logging()
