"""
Validation utilities for the LLM Stack.

This module provides common validation functions for configuration files,
environment variables, and other inputs. It includes functions for validating
file existence, directory existence, port numbers, CPU and memory formats,
URLs, email addresses, boolean values, and configuration files.

The module implements caching mechanisms to improve performance for
frequently called validation functions, particularly for filesystem operations.

Examples:
    Validating a port number:
    ```python
    from llm_stack.core import validation_utils
    
    if validation_utils.validate_port("8080", "HTTP_PORT"):
        print("Port is valid")
    ```
    
    Validating a configuration file:
    ```python
    if validation_utils.validate_env_file(".env"):
        print("Environment file is valid")
    ```
    
    Validating a directory with configuration files:
    ```python
    if validation_utils.validate_config_directory("config"):
        print("Configuration directory is valid")
    ```
"""

import os
import re
import functools
import concurrent.futures
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Union, Any, Set, Callable

import yaml

from llm_stack.core import logging
from llm_stack.core.file_utils import read_file, parse_env_file

# Compile regex patterns once at module level for better performance
URL_PATTERN = re.compile(r'^(https?|ftp)://[^\s/$.?#].[^\s]*$')
EMAIL_PATTERN = re.compile(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$')
MEMORY_PATTERN = re.compile(r'^(\d+)([KMG]B?|[kmg]b?)?$')

# Cache for file existence checks to avoid redundant filesystem operations
_file_exists_cache = {}
_dir_exists_cache = {}


# Cache decorator for validation functions
def cache_validation_result(func: Callable) -> Callable:
    """
    Cache validation results to avoid redundant validations.
    
    This decorator caches the results of validation functions to avoid
    redundant validations, which can be particularly useful for filesystem
    operations that are relatively expensive. The cache has a size limit
    to prevent memory issues, and it automatically removes the oldest
    entries when the limit is reached.
    
    Args:
        func: Function to decorate. The function should take at least one
            argument that can be used as a cache key.
        
    Returns:
        Callable: Decorated function with caching capability
        
    Example:
        ```python
        @cache_validation_result
        def validate_file_exists(file_path: str) -> bool:
            return os.path.isfile(file_path)
        ```
    """
    cache = {}
    
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        # Create a cache key from the function name and arguments
        key = (func.__name__, args[0] if args else None)
        
        # Check cache
        if key in cache:
            return cache[key]
        
        # Call original function
        result = func(*args, **kwargs)
        
        # Update cache
        cache[key] = result
        
        # Limit cache size
        if len(cache) > 1000:
            # Remove oldest 20% of entries
            oldest_keys = sorted(cache.keys())[:len(cache)//5]
            for old_key in oldest_keys:
                del cache[old_key]
                
        return result
    
    # Add method to clear cache
    wrapper.clear_cache = lambda: cache.clear()
    
    return wrapper

@cache_validation_result
def validate_file_exists(file_path: str) -> bool:
    """
    Validate that a file exists with caching.

    This function checks if a file exists at the specified path and caches
    the result to avoid redundant filesystem operations. If the file does
    not exist, an error message is logged.

    Args:
        file_path: Path to the file to check

    Returns:
        bool: True if the file exists, False otherwise
        
    Example:
        ```python
        from llm_stack.core import validation_utils
        
        if validation_utils.validate_file_exists("config.json"):
            # Process the file
            pass
        else:
            # Handle the error
            pass
        ```
    """
    # Use global cache for file existence checks
    global _file_exists_cache
    
    # Check cache first
    if file_path in _file_exists_cache:
        if not _file_exists_cache[file_path]:
            logging.error(f"File not found: {file_path}")
        return _file_exists_cache[file_path]
    
    # Check file existence
    result = os.path.isfile(file_path)
    
    # Update cache
    _file_exists_cache[file_path] = result
    
    if not result:
        logging.error(f"File not found: {file_path}")
        
    return result


@cache_validation_result
def validate_directory_exists(directory_path: str) -> bool:
    """
    Validate that a directory exists with caching.

    This function checks if a directory exists at the specified path and caches
    the result to avoid redundant filesystem operations. If the directory does
    not exist, an error message is logged.

    Args:
        directory_path: Path to the directory to check

    Returns:
        bool: True if the directory exists, False otherwise
        
    Example:
        ```python
        from llm_stack.core import validation_utils
        
        if validation_utils.validate_directory_exists("config"):
            # Process the directory
            pass
        else:
            # Handle the error
            pass
        ```
    """
    # Use global cache for directory existence checks
    global _dir_exists_cache
    
    # Check cache first
    if directory_path in _dir_exists_cache:
        if not _dir_exists_cache[directory_path]:
            logging.error(f"Directory not found: {directory_path}")
        return _dir_exists_cache[directory_path]
    
    # Check directory existence
    result = os.path.isdir(directory_path)
    
    # Update cache
    _dir_exists_cache[directory_path] = result
    
    if not result:
        logging.error(f"Directory not found: {directory_path}")
        
    return result


def validate_port(port_value: str, variable_name: str = "port") -> bool:
    """
    Validate a port value.

    This function checks if a port value is valid (an integer between 1 and 65535).
    If the port is invalid, an error message is logged with the provided variable name.

    Args:
        port_value: Port value to validate (as a string)
        variable_name: Name of the variable for error messages (default: "port")

    Returns:
        bool: True if the port is valid, False otherwise
        
    Example:
        ```python
        from llm_stack.core import validation_utils
        
        # Validate a port from a configuration
        if validation_utils.validate_port("8080", "HTTP_PORT"):
            # Use the port
            pass
        else:
            # Handle the error
            pass
        ```
    """
    try:
        port = int(port_value)
        if port < 1 or port > 65535:
            logging.error(f"Invalid {variable_name}: {port_value} (must be between 1 and 65535)")
            return False
        return True
    except ValueError:
        logging.error(f"Invalid {variable_name}: {port_value} (must be an integer)")
        return False


def validate_cpu_format(cpu_value: str, variable_name: str = "CPU limit") -> bool:
    """
    Validate a CPU limit format.

    This function checks if a CPU limit value is valid (a positive number).
    CPU limits can be specified as a float (e.g., 0.5) or an integer.
    If the CPU limit is invalid, an error message is logged with the provided variable name.

    Args:
        cpu_value: CPU limit value to validate (as a string)
        variable_name: Name of the variable for error messages (default: "CPU limit")

    Returns:
        bool: True if the CPU limit is valid, False otherwise
        
    Example:
        ```python
        from llm_stack.core import validation_utils
        
        # Validate a CPU limit from a configuration
        if validation_utils.validate_cpu_format("0.5", "CONTAINER_CPU_LIMIT"):
            # Use the CPU limit
            pass
        else:
            # Handle the error
            pass
        ```
    """
    try:
        # CPU limit can be a float (e.g., 0.5) or an integer
        cpu = float(cpu_value)
        if cpu <= 0:
            logging.error(f"Invalid {variable_name}: {cpu_value} (must be positive)")
            return False
        return True
    except ValueError:
        logging.error(f"Invalid {variable_name}: {cpu_value} (must be a number)")
        return False


def validate_memory_format(memory_value: str, variable_name: str = "memory limit") -> bool:
    """
    Validate a memory limit format using pre-compiled regex pattern.

    This function checks if a memory limit value is valid (a number followed by
    an optional unit K, M, or G). The validation uses a pre-compiled regex pattern
    for better performance. If the memory limit is invalid, an error message is
    logged with the provided variable name.

    Args:
        memory_value: Memory limit value to validate (as a string, e.g., "512M", "4G")
        variable_name: Name of the variable for error messages (default: "memory limit")

    Returns:
        bool: True if the memory limit is valid, False otherwise
        
    Example:
        ```python
        from llm_stack.core import validation_utils
        
        # Validate a memory limit from a configuration
        if validation_utils.validate_memory_format("4G", "CONTAINER_MEMORY_LIMIT"):
            # Use the memory limit
            pass
        else:
            # Handle the error
            pass
        ```
    """
    # Use pre-compiled pattern for better performance
    match = MEMORY_PATTERN.match(memory_value)
    
    if not match:
        logging.error(
            f"Invalid {variable_name}: {memory_value} "
            "(must be a number followed by an optional unit K, M, or G)"
        )
        return False
    
    return True


def validate_url(url_value: str, variable_name: str = "URL") -> bool:
    """
    Validate a URL format using pre-compiled regex pattern.

    This function checks if a URL value is valid using a pre-compiled regex pattern
    for better performance. The URL must start with http://, https://, or ftp://.
    If the URL is invalid, an error message is logged with the provided variable name.

    Args:
        url_value: URL value to validate (as a string)
        variable_name: Name of the variable for error messages (default: "URL")

    Returns:
        bool: True if the URL is valid, False otherwise
        
    Example:
        ```python
        from llm_stack.core import validation_utils
        
        # Validate a URL from a configuration
        if validation_utils.validate_url("https://example.com", "API_ENDPOINT"):
            # Use the URL
            pass
        else:
            # Handle the error
            pass
        ```
    """
    # Use pre-compiled pattern for better performance
    if not URL_PATTERN.match(url_value):
        logging.error(f"Invalid {variable_name}: {url_value} (must be a valid URL)")
        return False
    
    return True


def validate_email(email_value: str, variable_name: str = "email") -> bool:
    """
    Validate an email format using pre-compiled regex pattern.

    This function checks if an email value is valid using a pre-compiled regex pattern
    for better performance. If the email is invalid, an error message is logged with
    the provided variable name.

    Args:
        email_value: Email value to validate (as a string)
        variable_name: Name of the variable for error messages (default: "email")

    Returns:
        bool: True if the email is valid, False otherwise
        
    Example:
        ```python
        from llm_stack.core import validation_utils
        
        # Validate an email from a configuration
        if validation_utils.validate_email("user@example.com", "ADMIN_EMAIL"):
            # Use the email
            pass
        else:
            # Handle the error
            pass
        ```
    """
    # Use pre-compiled pattern for better performance
    if not EMAIL_PATTERN.match(email_value):
        logging.error(f"Invalid {variable_name}: {email_value} (must be a valid email)")
        return False
    
    return True


def validate_boolean(bool_value: str, variable_name: str = "boolean") -> bool:
    """
    Validate a boolean value.

    This function checks if a string value represents a valid boolean.
    Valid boolean values are: 'true', 'false', 'yes', 'no', '1', '0'
    (case-insensitive). If the value is not a valid boolean, an error
    message is logged with the provided variable name.

    Args:
        bool_value: Boolean value to validate (as a string)
        variable_name: Name of the variable for error messages (default: "boolean")

    Returns:
        bool: True if the value is a valid boolean, False otherwise
        
    Example:
        ```python
        from llm_stack.core import validation_utils
        
        # Validate a boolean from a configuration
        if validation_utils.validate_boolean("true", "ENABLE_FEATURE"):
            # Use the boolean value
            pass
        else:
            # Handle the error
            pass
        ```
    """
    valid_values = ['true', 'false', 'yes', 'no', '1', '0']
    
    if bool_value.lower() not in valid_values:
        logging.error(
            f"Invalid {variable_name}: {bool_value} "
            "(must be one of: true, false, yes, no, 1, 0)"
        )
        return False
    
    return True


def validate_env_file(env_file: str) -> bool:
    """
    Validate an environment file.

    This function validates an environment (.env) file by checking:
    1. If the file exists
    2. If it can be parsed correctly
    3. If port variables (HOST_PORT_*) are valid port numbers
    4. If CPU limit variables (*_CPU_LIMIT) are valid CPU limits
    5. If memory limit variables (*_MEMORY_LIMIT) are valid memory limits

    Args:
        env_file: Path to the environment file to validate

    Returns:
        bool: True if the file is valid, False otherwise
        
    Example:
        ```python
        from llm_stack.core import validation_utils
        
        # Validate a .env file
        if validation_utils.validate_env_file(".env"):
            print("Environment file is valid")
        else:
            print("Environment file is invalid")
        ```
    """
    logging.debug(f"Validating .env file: {env_file}")
    
    # Check if the file exists
    if not validate_file_exists(env_file):
        return False
    
    # Parse the environment file
    variables = parse_env_file(env_file)
    
    # Validate port variables
    port_vars = [var for var in variables if var.startswith("HOST_PORT_")]
    for var in port_vars:
        if not validate_port(variables[var], var):
            return False
    
    # Validate CPU limit variables
    cpu_vars = [var for var in variables if var.endswith("_CPU_LIMIT")]
    for var in cpu_vars:
        if not validate_cpu_format(variables[var], var):
            return False
    
    # Validate memory limit variables
    memory_vars = [var for var in variables if var.endswith("_MEMORY_LIMIT")]
    for var in memory_vars:
        if not validate_memory_format(variables[var], var):
            return False
    
    logging.success(f".env file validated: {env_file}")
    return True


def validate_yaml_file(yaml_file: str) -> bool:
    """
    Validate a YAML file.

    This function validates a YAML file by checking:
    1. If the file exists
    2. If it can be parsed as valid YAML
    3. If the file is not empty

    If any validation fails, an appropriate error message is logged.

    Args:
        yaml_file: Path to the YAML file to validate

    Returns:
        bool: True if the file is valid, False otherwise
        
    Example:
        ```python
        from llm_stack.core import validation_utils
        
        # Validate a YAML file
        if validation_utils.validate_yaml_file("docker-compose.yml"):
            print("YAML file is valid")
        else:
            print("YAML file is invalid")
        ```
    """
    logging.debug(f"Validating YAML file: {yaml_file}")
    
    # Check if the file exists
    if not validate_file_exists(yaml_file):
        return False
    
    # Parse the YAML file
    success, content = read_file(yaml_file)
    if not success:
        return False
    
    try:
        yaml_data = yaml.safe_load(content)
        
        # Check if the file contains valid YAML
        if yaml_data is None:
            logging.error(f"Empty YAML file: {yaml_file}")
            return False
        
        logging.success(f"YAML file validated: {yaml_file}")
        return True
    
    except yaml.YAMLError as e:
        logging.error(f"Invalid YAML in {yaml_file}: {str(e)}")
        return False
    
    except Exception as e:
        logging.error(f"Error validating YAML file: {str(e)}")
        return False


def validate_json_file(json_file: str) -> bool:
    """
    Validate a JSON file.

    This function validates a JSON file by checking:
    1. If the file exists
    2. If it can be parsed as valid JSON

    If any validation fails, an appropriate error message is logged.

    Args:
        json_file: Path to the JSON file to validate

    Returns:
        bool: True if the file is valid, False otherwise
        
    Example:
        ```python
        from llm_stack.core import validation_utils
        
        # Validate a JSON file
        if validation_utils.validate_json_file("config.json"):
            print("JSON file is valid")
        else:
            print("JSON file is invalid")
        ```
    """
    logging.debug(f"Validating JSON file: {json_file}")
    
    # Check if the file exists
    if not validate_file_exists(json_file):
        return False
    
    # Parse the JSON file
    success, content = read_file(json_file)
    if not success:
        return False
    
    try:
        import json
        json.loads(content)
        
        logging.success(f"JSON file validated: {json_file}")
        return True
    
    except json.JSONDecodeError as e:
        logging.error(f"Invalid JSON in {json_file}: {str(e)}")
        return False
    
    except Exception as e:
        logging.error(f"Error validating JSON file: {str(e)}")
        return False


def validate_config_directory(config_dir: str, max_workers: int = 4) -> bool:
    """
    Validate a configuration directory with parallel processing.

    This function validates a configuration directory by checking:
    1. If the directory exists
    2. If all .env files in the directory are valid
    3. If all .yml/.yaml files in the directory are valid
    4. If all .json files in the directory are valid

    The validation is performed in parallel using a ThreadPoolExecutor
    for better performance with large directories.

    Args:
        config_dir: Path to the configuration directory to validate
        max_workers: Maximum number of worker threads for parallel validation (default: 4)

    Returns:
        bool: True if the directory and all its configuration files are valid, False otherwise
        
    Example:
        ```python
        from llm_stack.core import validation_utils
        
        # Validate a configuration directory
        if validation_utils.validate_config_directory("config"):
            print("Configuration directory is valid")
        else:
            print("Configuration directory is invalid")
        ```
    """
    logging.debug(f"Validating configuration directory: {config_dir}")
    
    # Check if the directory exists
    if not validate_directory_exists(config_dir):
        return False
    
    # Collect all files to validate
    env_files = list(Path(config_dir).glob("**/*.env"))
    yaml_files = list(Path(config_dir).glob("**/*.yml"))
    yaml_files.extend(Path(config_dir).glob("**/*.yaml"))
    json_files = list(Path(config_dir).glob("**/*.json"))
    
    # Process files in batches with parallel execution
    all_valid = True
    
    # Use ThreadPoolExecutor for parallel validation
    with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
        # Submit validation tasks
        env_futures = [executor.submit(validate_env_file, str(f)) for f in env_files]
        yaml_futures = [executor.submit(validate_yaml_file, str(f)) for f in yaml_files]
        json_futures = [executor.submit(validate_json_file, str(f)) for f in json_files]
        
        # Collect results
        for future in concurrent.futures.as_completed(env_futures + yaml_futures + json_futures):
            if not future.result():
                all_valid = False
                # Don't break early to collect all validation errors
    
    if all_valid:
        logging.success(f"Configuration directory validated: {config_dir}")
    else:
        logging.error(f"Configuration directory validation failed: {config_dir}")
        
    return all_valid