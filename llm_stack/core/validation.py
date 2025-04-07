"""
Validation functions for the LLM Stack.

This module provides functions for validating configuration values and other inputs.
All validation functions raise appropriate exceptions when validation fails.
The validation functions follow a consistent pattern of accepting a value to validate,
optional validation parameters, and a name parameter for error messages.
"""

import ipaddress
import os
import re
from typing import Any, Callable, Dict, List, Optional, Pattern, Tuple, Union, TypeVar, Generic

from llm_stack.core import error, logging

# Type variable for generic validation functions
T = TypeVar('T')

# Helper functions to reduce duplication
def _handle_validation_error(value: Any, expected_type: str, name: str) -> None:
    """
    Handle type validation errors consistently.
    
    Args:
        value: The value that failed validation
        expected_type: The expected type or format
        name: Name of the value for error messages
    
    Raises:
        TypeValidationError: With consistent error message
    """
    logging.error(f"{name} must be a {expected_type}: {value}")
    raise error.TypeValidationError(str(value), expected_type, name)

def _handle_format_error(value: Any, format_name: str, name: str) -> None:
    """
    Handle format validation errors consistently.
    
    Args:
        value: The value that failed validation
        format_name: The expected format
        name: Name of the value for error messages
    
    Raises:
        FormatValidationError: With consistent error message
    """
    logging.error(f"{name} must be a valid {format_name}: {value}")
    raise error.FormatValidationError(str(value), format_name, name)

def _validate_with_pattern(value: str, pattern: Pattern[str], format_name: str, name: str) -> None:
    """
    Validate a string against a regex pattern.
    
    Args:
        value: The string to validate
        pattern: Compiled regex pattern
        format_name: Name of the format for error messages
        name: Name of the value for error messages
    
    Raises:
        FormatValidationError: If validation fails
    """
    if not pattern.match(value):
        _handle_format_error(value, format_name, name)


def validate_port(port: Union[str, int], name: str = "Port") -> None:
    """Validates that a port number is within the valid range (1-65535).

    Args:
        port: The port number to validate. Can be a string or integer.
        name: Name of the port for error messages. Defaults to "Port".

    Raises:
        PortValidationError: If the port is not within the valid range (1-65535).
        TypeValidationError: If the port cannot be converted to an integer.

    Returns:
        None
    """
    try:
        port_int = int(port)
        if port_int < 1 or port_int > 65535:
            logging.error(f"{name} must be between 1 and 65535: {port}")
            raise error.PortValidationError(str(port), name)
    except ValueError:
        logging.error(f"{name} must be a number: {port}")
        raise error.TypeValidationError(str(port), "number", name)

def validate_is_decimal(value: Union[str, float], name: str = "Value") -> None:
    """Validates that a value can be converted to a decimal number.

    Args:
        value: The value to validate. Can be a string or float.
        name: Name of the value for error messages. Defaults to "Value".

    Raises:
        TypeValidationError: If the value cannot be converted to a float.

    Returns:
        None
    """
    try:
        float(value)
    except ValueError:
        _handle_validation_error(value, "decimal number", name)


def validate_is_integer(value: Union[str, int], name: str = "Value") -> None:
    """Validates that a value can be converted to an integer.

    Args:
        value: The value to validate. Can be a string or integer.
        name: Name of the value for error messages. Defaults to "Value".

    Raises:
        TypeValidationError: If the value cannot be converted to an integer.

    Returns:
        None
    """
    try:
        int(value)
    except ValueError:
        _handle_validation_error(value, "integer", name)
        raise error.TypeValidationError(str(value), "integer", name)


def validate_is_boolean(value: Union[str, bool], name: str = "Value") -> None:
    """Validates that a value is a boolean or can be interpreted as a boolean.

    Accepts boolean objects or strings that represent boolean values
    (true/false, yes/no, 1/0, y/n).

    Args:
        value: The value to validate. Can be a boolean or string.
        name: Name of the value for error messages. Defaults to "Value".

    Raises:
        TypeValidationError: If the value is not a boolean or cannot be
            interpreted as a boolean.

    Returns:
        None
    """
    if isinstance(value, bool):
        return

    if isinstance(value, str):
        value_lower = value.lower()
        if value_lower in ["true", "false", "yes", "no", "1", "0", "y", "n"]:
            return

    logging.error(f"{name} must be a boolean value: {value}")
    raise error.TypeValidationError(str(value), "boolean value", name)


# Compile regex patterns once at module level for efficiency
URL_PATTERN = re.compile(
    r"^(?:http|https)://"  # http:// or https://
    r"(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+(?:[A-Z]{2,6}\.?|[A-Z0-9-]{2,}\.?)|"  # Domain
    r"localhost|"  # localhost
    r"\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})"  # IP
    r"(?::\d+)?"  # Port
    r"(?:/?|[/?]\S+)$",
    re.IGNORECASE,
)

EMAIL_PATTERN = re.compile(r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$")

HOSTNAME_PATTERN = re.compile(
    r"^[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?(?:\.[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?)*$"
)

MEMORY_PATTERN = re.compile(r"^(\d+)([KMGTkmgt])[Bb]?$")

def validate_is_url(value: str, name: str = "URL") -> None:
    """Validates that a string is a valid URL.

    Checks if the string matches a URL pattern with http or https protocol,
    valid domain or IP address, and optional port and path.

    Args:
        value: The string to validate as a URL.
        name: Name of the value for error messages. Defaults to "URL".

    Raises:
        FormatValidationError: If the value does not match the URL pattern.

    Returns:
        None
    """
    _validate_with_pattern(value, URL_PATTERN, "URL", name)


def validate_is_email(value: str, name: str = "Email") -> None:
    """Validates that a string is a valid email address.

    Checks if the string matches a standard email pattern with username,
    @ symbol, and domain.

    Args:
        value: The string to validate as an email address.
        name: Name of the value for error messages. Defaults to "Email".

    Raises:
        FormatValidationError: If the value does not match the email pattern.

    Returns:
        None
    """
    _validate_with_pattern(value, EMAIL_PATTERN, "email address", name)


def validate_is_ip_address(value: str, name: str = "IP address") -> None:
    """Validates that a string is a valid IP address (IPv4 or IPv6).

    Uses the ipaddress module to validate the IP address format.

    Args:
        value: The string to validate as an IP address.
        name: Name of the value for error messages. Defaults to "IP address".

    Raises:
        FormatValidationError: If the value is not a valid IP address.

    Returns:
        None
    """
    try:
        ipaddress.ip_address(value)
    except ValueError:
        _handle_format_error(value, "IP address", name)


def validate_is_ip_network(value: str, name: str = "IP network") -> None:
    """Validates that a string is a valid IP network (CIDR notation).

    Uses the ipaddress module to validate the IP network format.
    Accepts formats like "192.168.0.0/24" or "2001:db8::/32".

    Args:
        value: The string to validate as an IP network.
        name: Name of the value for error messages. Defaults to "IP network".

    Raises:
        FormatValidationError: If the value is not a valid IP network.

    Returns:
        None
    """
    try:
        ipaddress.ip_network(value, strict=False)
    except ValueError:
        _handle_format_error(value, "IP network", name)


def validate_is_hostname(value: str, name: str = "Hostname") -> None:
    """Validates that a string is a valid hostname.

    Checks if the string matches the hostname pattern according to RFC 1123.
    Each label must start and end with alphanumeric characters and can contain
    hyphens in between.

    Args:
        value: The string to validate as a hostname.
        name: Name of the value for error messages. Defaults to "Hostname".

    Raises:
        FormatValidationError: If the value does not match the hostname pattern.

    Returns:
        None
    """
    _validate_with_pattern(value, HOSTNAME_PATTERN, "hostname", name)


def _validate_filesystem_entity(value: str, check_func: Callable[[str], bool], entity_type: str, name: str) -> None:
    """
    Validate a filesystem entity (file or directory).
    
    Args:
        value: The path to validate
        check_func: Function to check if the path is valid (e.g., os.path.isfile)
        entity_type: Type of entity for error messages
        name: Name of the value for error messages
    
    Raises:
        FileSystemValidationError: If validation fails
    """
    if not check_func(value):
        logging.error(f"{name} must be an existing {entity_type}: {value}")
        raise error.FileSystemValidationError(value, entity_type, name)

def validate_is_path(value: str, name: str = "Path") -> None:
    """Validates that a string is a valid file system path.

    Uses os.path.normpath to validate the path format. This does not check
    if the path exists, only that it has a valid format.

    Args:
        value: The string to validate as a path.
        name: Name of the value for error messages. Defaults to "Path".

    Raises:
        FormatValidationError: If the value is not a valid path format.

    Returns:
        None
    """
    try:
        os.path.normpath(value)
    except Exception:
        _handle_format_error(value, "path", name)


def validate_is_file(value: str, name: str = "File") -> None:
    """Validates that a path points to an existing file.

    Checks if the path exists and is a file (not a directory).

    Args:
        value: The path to validate.
        name: Name of the value for error messages. Defaults to "File".

    Raises:
        FileSystemValidationError: If the path does not exist or is not a file.

    Returns:
        None
    """
    _validate_filesystem_entity(value, os.path.isfile, "file", name)


def validate_is_directory(value: str, name: str = "Directory") -> None:
    """Validates that a path points to an existing directory.

    Checks if the path exists and is a directory (not a file).

    Args:
        value: The path to validate.
        name: Name of the value for error messages. Defaults to "Directory".

    Raises:
        FileSystemValidationError: If the path does not exist or is not a directory.

    Returns:
        None
    """
    _validate_filesystem_entity(value, os.path.isdir, "directory", name)


def validate_is_in_list(
    value: Any, valid_values: List[Any], name: str = "Value"
) -> None:
    """Validates that a value is contained in a list of valid values.

    Args:
        value: The value to validate.
        valid_values: List of valid values that the value can be.
        name: Name of the value for error messages. Defaults to "Value".

    Raises:
        ListValidationError: If the value is not in the list of valid values.

    Returns:
        None
    """
    if value not in valid_values:
        logging.error(
            f"{name} must be one of the following values: {', '.join(map(str, valid_values))}"
        )
        raise error.ListValidationError(value, valid_values, name)


def validate_matches_pattern(
    value: str, pattern: Union[str, Pattern[str]], name: str = "Value"
) -> None:
    """Validates that a string matches a regular expression pattern.

    The pattern can be provided as a string or a compiled regex pattern.
    If a string is provided, it will be compiled into a pattern.

    Args:
        value: The string to validate.
        pattern: Regular expression pattern as a string or compiled Pattern object.
        name: Name of the value for error messages. Defaults to "Value".

    Raises:
        PatternValidationError: If the value does not match the pattern.

    Returns:
        None
    """
    if isinstance(pattern, str):
        pattern = re.compile(pattern)

    if not pattern.match(value):
        logging.error(f"{name} must match the pattern {pattern.pattern}: {value}")
        raise error.PatternValidationError(value, pattern, name)


def validate_length(
    value: Union[str, List[Any], Dict[Any, Any]],
    min_length: Optional[int] = None,
    max_length: Optional[int] = None,
    name: str = "Value",
) -> None:
    """Validates that a value's length is within specified bounds.

    Works with strings, lists, dictionaries, or any object that supports len().
    At least one of min_length or max_length must be provided.

    Args:
        value: The value to validate the length of.
        min_length: Minimum required length. If None, no minimum is enforced.
        max_length: Maximum allowed length. If None, no maximum is enforced.
        name: Name of the value for error messages. Defaults to "Value".

    Raises:
        LengthValidationError: If the value's length is outside the specified bounds.

    Returns:
        None
    """
    length = len(value)

    if min_length is not None and length < min_length:
        logging.error(f"{name} must be at least {min_length} characters long: {value}")
        raise error.LengthValidationError(value, min_length, max_length, name)

    if max_length is not None and length > max_length:
        logging.error(f"{name} must be at most {max_length} characters long: {value}")
        raise error.LengthValidationError(value, min_length, max_length, name)


def validate_range(
    value: Union[int, float, str],
    min_value: Optional[Union[int, float]] = None,
    max_value: Optional[Union[int, float]] = None,
    name: str = "Value",
) -> None:
    """Validates that a numeric value is within specified bounds.

    The value can be an integer, float, or a string that can be converted to a float.
    At least one of min_value or max_value must be provided.

    Args:
        value: The numeric value to validate.
        min_value: Minimum allowed value. If None, no minimum is enforced.
        max_value: Maximum allowed value. If None, no maximum is enforced.
        name: Name of the value for error messages. Defaults to "Value".

    Raises:
        TypeValidationError: If the value cannot be converted to a float.
        RangeValidationError: If the value is outside the specified bounds.

    Returns:
        None
    """
    try:
        value_float = float(value)

        if min_value is not None and value_float < min_value:
            logging.error(f"{name} must be at least {min_value}: {value}")
            raise error.RangeValidationError(str(value), min_value, max_value, name)

        if max_value is not None and value_float > max_value:
            logging.error(f"{name} must be at most {max_value}: {value}")
            raise error.RangeValidationError(str(value), min_value, max_value, name)

    except ValueError:
        logging.error(f"{name} must be a number: {value}")
        raise error.TypeValidationError(str(value), "number", name)


def validate_with_function(
    value: Any,
    validation_func: Callable[[Any], bool],
    error_message: str,
    name: str = "Value",
) -> None:
    """Validates a value using a custom validation function.

    The validation function should return True if the value is valid,
    and False if it is invalid.

    Args:
        value: The value to validate.
        validation_func: Function that takes the value and returns a boolean
            indicating if the value is valid.
        error_message: Custom error message to use if validation fails.
        name: Name of the value for error messages. Defaults to "Value".

    Raises:
        CustomValidationError: If the validation function returns False.

    Returns:
        None
    """
    if not validation_func(value):
        logging.error(f"{name}: {error_message}")
        raise error.CustomValidationError(error_message, name)


def validate_all(validations: List[Tuple[Callable[..., None], List[Any], Dict[str, Any]]]) -> None:
    """Performs multiple validations and requires all to pass.

    This is a logical AND operation - all validations must succeed.
    Executes each validation in sequence and raises the first error encountered.

    Args:
        validations: List of tuples containing:
            - validation function
            - list of positional arguments for the function
            - dictionary of keyword arguments for the function

    Raises:
        ValidationError: If any validation fails, with the specific error from
            the first failed validation.

    Returns:
        None
    """
    for validation_func, args, kwargs in validations:
        validation_func(*args, **kwargs)


def validate_any(validations: List[Tuple[Callable[..., None], List[Any], Dict[str, Any]]]) -> None:
    """Performs multiple validations and requires at least one to pass.

    This is a logical OR operation - at least one validation must succeed.
    If all validations fail, raises a ValidationError with all error messages.

    Args:
        validations: List of tuples containing:
            - validation function
            - list of positional arguments for the function
            - dictionary of keyword arguments for the function

    Raises:
        ValidationError: If all validations fail, with a combined error message
            from all failed validations.

    Returns:
        None
    """
    errors = []
    
    for validation_func, args, kwargs in validations:
        try:
            validation_func(*args, **kwargs)
            return  # If any validation succeeds, return immediately
        except error.ValidationError as e:
            errors.append(str(e))
    
    # If we get here, all validations failed
    logging.error("None of the validations were successful")
    raise error.ValidationError(f"All validations failed: {'; '.join(errors)}")


def validate_memory_format(value: str, name: str = "Memory value") -> None:
    """Validates that a string has a valid memory size format.

    Accepts formats like "16G", "512M", "1024K", etc.
    The format should be a number followed by a unit (K, M, G, T).
    The unit can optionally be followed by 'B' or 'b' (e.g., "16GB").

    Args:
        value: The string to validate as a memory size.
        name: Name of the value for error messages. Defaults to "Memory value".

    Raises:
        FormatValidationError: If the value does not match the memory format pattern.

    Returns:
        None
    """
    if not MEMORY_PATTERN.match(value):
        _handle_format_error(value, "memory format (e.g., '16G' or '512M')", name)


def validate_cpu_format(value: Union[str, float, int], name: str = "CPU value") -> None:
    """Validates that a value represents a valid CPU allocation.

    The value must be a positive number (greater than 0).
    It can be provided as a string, float, or integer.

    Args:
        value: The value to validate as a CPU allocation.
        name: Name of the value for error messages. Defaults to "CPU value".

    Raises:
        TypeValidationError: If the value cannot be converted to a float.
        RangeValidationError: If the value is not greater than 0.

    Returns:
        None
    """
    try:
        cpu_value = float(value)
        if cpu_value <= 0:
            logging.error(f"{name} must be greater than 0: {value}")
            raise error.RangeValidationError(str(value), 0, None, name)
    except ValueError:
        _handle_validation_error(value, "decimal number", name)


logging.debug("Validation module initialized")
