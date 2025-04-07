"""
Error handling for the LLM Stack.

This module defines error codes, exceptions, and functions for error handling.
"""

import sys
import traceback
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Pattern, Type, TypeVar, Union, cast

import logging as py_logging

# Configure a basic logger for this module
_logger = py_logging.getLogger(__name__)

# Type variable for generic functions
T = TypeVar("T")


# Error codes
class ErrorCode(Enum):
    """Error codes for the LLM Stack."""

    SUCCESS = 0
    GENERAL_ERROR = 1
    CONFIG_ERROR = 2
    FILE_NOT_FOUND = 3
    PERMISSION_DENIED = 4
    NETWORK_ERROR = 5
    DOCKER_ERROR = 6
    MODULE_ERROR = 7
    VALIDATION_ERROR = 8
    SECURITY_ERROR = 9
    DATABASE_ERROR = 10
    API_ERROR = 11
    TIMEOUT_ERROR = 12
    RESOURCE_ERROR = 13
    DEPENDENCY_ERROR = 14
    USER_INPUT_ERROR = 15
    INTERNAL_ERROR = 99


# Custom exceptions
class LLMStackError(Exception):
    """Base class for all LLM Stack exceptions."""

    def __init__(self, message: str, code: ErrorCode = ErrorCode.GENERAL_ERROR):
        """
        Initializes a new LLM Stack exception.

        Args:
            message: Error message
            code: Error code
        """
        self.message = message
        self.code = code
        super().__init__(f"[{code.name}] {message}")


class ConfigError(LLMStackError):
    """Exception for configuration errors."""

    def __init__(self, message: str):
        """
        Initializes a new configuration error exception.

        Args:
            message: Error message
        """
        super().__init__(message, ErrorCode.CONFIG_ERROR)


class InvalidArgumentError(LLMStackError):
    """Exception for invalid arguments."""

    def __init__(self, message: str):
        """
        Initializes a new exception for invalid arguments.

        Args:
            message: Error message
        """
        super().__init__(message, ErrorCode.VALIDATION_ERROR)


class ConfigUpdateError(ConfigError):
    """Exception for errors when updating configuration."""

    def __init__(self, config_key: str, config_value: str, reason: str = ""):
        """
        Initializes a new exception for errors when updating configuration.

        Args:
            config_key: Configuration key
            config_value: Configuration value
            reason: Reason for the error (optional)
        """
        message = f"Error updating configuration: {config_key}={config_value}"
        if reason:
            message += f": {reason}"
        super().__init__(message)


class FileNotFoundError(LLMStackError):
    """Exception for file-not-found errors."""

    def __init__(self, message: str):
        """
        Initializes a new file-not-found exception.

        Args:
            message: Error message
        """
        super().__init__(message, ErrorCode.FILE_NOT_FOUND)


class PermissionDeniedError(LLMStackError):
    """Exception for permission-denied errors."""

    def __init__(self, message: str):
        """
        Initializes a new permission-denied exception.

        Args:
            message: Error message
        """
        super().__init__(message, ErrorCode.PERMISSION_DENIED)


class NetworkError(LLMStackError):
    """Exception for network errors."""

    def __init__(self, message: str):
        """
        Initializes a new network error exception.

        Args:
            message: Error message
        """
        super().__init__(message, ErrorCode.NETWORK_ERROR)


class DockerError(LLMStackError):
    """Exception for Docker errors."""

    def __init__(self, message: str):
        """
        Initializes a new Docker error exception.

        Args:
            message: Error message
        """
        super().__init__(message, ErrorCode.DOCKER_ERROR)


class ModuleError(LLMStackError):
    """Exception for module errors."""

    def __init__(self, message: str):
        """
        Initializes a new module error exception.

        Args:
            message: Error message
        """
        super().__init__(message, ErrorCode.MODULE_ERROR)


class ModuleAlreadyRunningError(ModuleError):
    """Exception for already running modules."""

    def __init__(self, module_name: str):
        """
        Initializes a new exception for already running modules.

        Args:
            module_name: Name of the module
        """
        super().__init__(f"Module {module_name} is already running")


class ModuleAlreadyStoppedError(ModuleError):
    """Exception for already stopped modules."""

    def __init__(self, module_name: str):
        """
        Initializes a new exception for already stopped modules.

        Args:
            module_name: Name of the module
        """
        super().__init__(f"Module {module_name} is already stopped")


class ModuleStartError(ModuleError):
    """Exception for errors when starting a module."""

    def __init__(self, module_name: str, reason: str = ""):
        """
        Initializes a new exception for errors when starting a module.

        Args:
            module_name: Name of the module
            reason: Reason for the error (optional)
        """
        message = f"Error starting module {module_name}"
        if reason:
            message += f": {reason}"
        super().__init__(message)


class ModuleStopError(ModuleError):
    """Exception for errors when stopping a module."""

    def __init__(self, module_name: str, reason: str = ""):
        """
        Initializes a new exception for errors when stopping a module.

        Args:
            module_name: Name of the module
            reason: Reason for the error (optional)
        """
        message = f"Error stopping module {module_name}"
        if reason:
            message += f": {reason}"
        super().__init__(message)


class ValidationError(LLMStackError):
    """Exception for validation errors."""

    def __init__(self, message: str):
        """
        Initializes a new validation error exception.

        Args:
            message: Error message
        """
        super().__init__(message, ErrorCode.VALIDATION_ERROR)


class PortValidationError(ValidationError):
    """Exception for errors when validating ports."""

    def __init__(self, value: str, name: str = "Port"):
        """
        Initializes a new port validation error exception.

        Args:
            value: The invalid value
            name: Name of the port for error messages
        """
        super().__init__(f"{name} must be between 1 and 65535: {value}")


class TypeValidationError(ValidationError):
    """Exception for errors when validating types."""

    def __init__(self, value: str, expected_type: str, name: str = "Value"):
        """
        Initializes a new type validation error exception.

        Args:
            value: The invalid value
            expected_type: The expected type
            name: Name of the value for error messages
        """
        super().__init__(f"{name} must be a {expected_type}: {value}")


class FormatValidationError(ValidationError):
    """Exception for errors when validating formats."""

    def __init__(self, value: str, format_name: str, name: str = "Value"):
        """
        Initializes a new format validation error exception.

        Args:
            value: The invalid value
            format_name: Name of the expected format
            name: Name of the value for error messages
        """
        super().__init__(f"{name} must be a valid {format_name}: {value}")


class RangeValidationError(ValidationError):
    """Exception for errors when validating value ranges."""

    def __init__(self, value: str, min_value: Optional[Union[int, float]] = None,
                 max_value: Optional[Union[int, float]] = None, name: str = "Value"):
        """
        Initializes a new range validation error exception.

        Args:
            value: The invalid value
            min_value: Minimum value
            max_value: Maximum value
            name: Name of the value for error messages
        """
        if min_value is not None and max_value is not None:
            message = f"{name} must be between {min_value} and {max_value}: {value}"
        elif min_value is not None:
            message = f"{name} must be at least {min_value}: {value}"
        elif max_value is not None:
            message = f"{name} must be at most {max_value}: {value}"
        else:
            message = f"{name} is out of valid range: {value}"
        super().__init__(message)


class LengthValidationError(ValidationError):
    """Exception for errors when validating lengths."""

    def __init__(self, value: Union[str, List, Dict], min_length: Optional[int] = None,
                 max_length: Optional[int] = None, name: str = "Value"):
        """
        Initializes a new length validation error exception.

        Args:
            value: The invalid value
            min_length: Minimum length
            max_length: Maximum length
            name: Name of the value for error messages
        """
        length = len(value)
        if min_length is not None and length < min_length:
            message = f"{name} must be at least {min_length} characters long: {value}"
        elif max_length is not None and length > max_length:
            message = f"{name} must be at most {max_length} characters long: {value}"
        else:
            message = f"{name} has invalid length: {value}"
        super().__init__(message)


class PatternValidationError(ValidationError):
    """Exception for errors when validating patterns."""

    def __init__(self, value: str, pattern: Union[str, Pattern], name: str = "Value"):
        """
        Initializes a new pattern validation error exception.

        Args:
            value: The invalid value
            pattern: The expected pattern
            name: Name of the value for error messages
        """
        pattern_str = getattr(pattern, 'pattern', str(pattern))
        super().__init__(f"{name} must match the pattern {pattern_str}: {value}")


class ListValidationError(ValidationError):
    """Exception for errors when validating list values."""

    def __init__(self, value: Any, valid_values: List[Any], name: str = "Value"):
        """
        Initializes a new list validation error exception.

        Args:
            value: The invalid value
            valid_values: List of valid values
            name: Name of the value for error messages
        """
        super().__init__(f"{name} must be one of the following values: {', '.join(map(str, valid_values))}")


class FileSystemValidationError(ValidationError):
    """Exception for errors when validating file system objects."""

    def __init__(self, value: str, object_type: str, name: str = "Path"):
        """
        Initializes a new file system validation error exception.

        Args:
            value: The invalid value
            object_type: Type of file system object (file, directory, path)
            name: Name of the value for error messages
        """
        super().__init__(f"{name} must be an existing {object_type}: {value}")


class CustomValidationError(ValidationError):
    """Exception for custom validation errors."""

    def __init__(self, message: str, name: str = "Value"):
        """
        Initializes a new custom validation error exception.

        Args:
            message: Error message
            name: Name of the value for error messages
        """
        super().__init__(f"{name}: {message}")


class SecurityError(LLMStackError):
    """Exception for security errors."""

    def __init__(self, message: str):
        """
        Initializes a new security error exception.

        Args:
            message: Error message
        """
        super().__init__(message, ErrorCode.SECURITY_ERROR)


# Error handling functions
def handle_error(error: LLMStackError, exit_on_error: bool = True) -> None:
    """
    Handles an LLM Stack error.

    Args:
        error: The error to handle
        exit_on_error: Whether to exit the program on error
    """
    _logger.error(f"{error.message} (Code: {error.code.value})")

    if exit_on_error:
        sys.exit(error.code.value)


def handle_exception(
    exc: Exception,
    error_code: ErrorCode = ErrorCode.GENERAL_ERROR,
    exit_on_error: bool = True,
) -> None:
    """
    Handles a general exception.

    Args:
        exc: The exception to handle
        error_code: The error code to use
        exit_on_error: Whether to exit the program on error
    """
    # If it's an LLMStackError, use its code
    if isinstance(exc, LLMStackError):
        error_code = exc.code

    # Log error message
    _logger.error(f"{str(exc)} (Code: {error_code.value})")

    # In debug mode, log the stack trace
    # In debug mode, log the stack trace
    _logger.debug(
        f"Stack-Trace:\n{''.join(traceback.format_exception(type(exc), exc, exc.__traceback__))}"
    )

    if exit_on_error:
        sys.exit(error_code.value)


def try_except(
    func: Callable[..., T],
    error_map: Optional[Dict[Type[Exception], ErrorCode]] = None,
    exit_on_error: bool = True,
    raise_exception: bool = False,
    *args: Any,
    **kwargs: Any,
) -> Optional[T]:
    """
    Executes a function and catches exceptions.

    Args:
        func: The function to execute
        error_map: Mapping of exception types to error codes
        exit_on_error: Whether to exit the program on error
        raise_exception: Whether to re-raise the exception after handling
        *args: Positional arguments for the function
        **kwargs: Keyword arguments for the function

    Returns:
        Optional[T]: Return value of the function or None if an error occurred

    Raises:
        LLMStackError: If raise_exception is True and an error occurs
    """
    if error_map is None:
        error_map = {}

    try:
        return func(*args, **kwargs)
    except Exception as e:
        # Determine error code based on exception type
        error_code = ErrorCode.GENERAL_ERROR
        for exc_type, code in error_map.items():
            if isinstance(e, exc_type):
                error_code = code
                break

        # Handle exception
        handle_exception(e, error_code, exit_on_error)
        
        # Re-raise exception if desired
        if raise_exception:
            if isinstance(e, LLMStackError):
                raise e
            else:
                raise LLMStackError(str(e), error_code)
                
        return None


def assert_condition(
    condition: bool, message: str, error_code: ErrorCode = ErrorCode.GENERAL_ERROR
) -> None:
    """
    Checks a condition and raises an exception if it is not met.

    Args:
        condition: The condition to check
        message: Error message if the condition is not met
        error_code: The error code to use

    Raises:
        LLMStackError: If the condition is not met
    """
    if not condition:
        raise LLMStackError(message, error_code)


# Error handling decorator
def error_handler(
    error_map: Optional[Dict[Type[Exception], ErrorCode]] = None,
    exit_on_error: bool = True,
    raise_exception: bool = False,
) -> Callable[[Callable[..., T]], Callable[..., Optional[T]]]:
    """
    Decorator for error handling.

    Args:
        error_map: Mapping of exception types to error codes
        exit_on_error: Whether to exit the program on error
        raise_exception: Whether to re-raise the exception after handling

    Returns:
        Callable: Decorated function
    """
    if error_map is None:
        error_map = {}

    def decorator(func: Callable[..., T]) -> Callable[..., Optional[T]]:
        def wrapper(*args: Any, **kwargs: Any) -> Optional[T]:
            return try_except(func, error_map, exit_on_error, raise_exception, *args, **kwargs)

        return wrapper

    return decorator


# Error code to exception mapping
ERROR_CODE_TO_EXCEPTION: Dict[ErrorCode, Type[LLMStackError]] = {
    ErrorCode.CONFIG_ERROR: ConfigError,
    ErrorCode.FILE_NOT_FOUND: FileNotFoundError,
    ErrorCode.PERMISSION_DENIED: PermissionDeniedError,
    ErrorCode.NETWORK_ERROR: NetworkError,
    ErrorCode.DOCKER_ERROR: DockerError,
    ErrorCode.MODULE_ERROR: ModuleError,
    ErrorCode.VALIDATION_ERROR: ValidationError,
    ErrorCode.SECURITY_ERROR: SecurityError,
}


def raise_error(code: ErrorCode, message: str) -> None:
    """
    Raises an exception based on an error code.

    Args:
        code: The error code
        message: The error message

    Raises:
        LLMStackError: The corresponding exception for the error code
    """
    exception_class = ERROR_CODE_TO_EXCEPTION.get(code, LLMStackError)
    if code == ErrorCode.GENERAL_ERROR:
        raise LLMStackError(message, code)
    else:
        # We know that the exception expects a single string parameter
        raise cast(Any, exception_class)(message)


# Helper function for standardized error handling
def handle_result(result: Optional[T], error_message: str, error_code: ErrorCode = ErrorCode.GENERAL_ERROR, raise_exception: bool = True) -> T:
    """
    Handles a result and raises an exception if it is None.
    
    This function helps to standardize error handling by converting
    None results into exceptions.

    Args:
        result: The result to check
        error_message: The error message if the result is None
        error_code: The error code to use
        raise_exception: Whether to raise an exception if the result is None

    Returns:
        T: The result if it is not None

    Raises:
        LLMStackError: If the result is None and raise_exception is True
    """
    if result is None:
        if raise_exception:
            raise_error(error_code, error_message)
        _logger.error(f"{error_message} (Code: {error_code.value})")
        # Typecasting to satisfy mypy, this will never be executed if raise_exception is True
        return cast(T, None)
    return result


_logger.debug("Error handling module initialized")
