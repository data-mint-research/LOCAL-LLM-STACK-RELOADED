# Validation Utilities

The validation utilities module (`llm_stack.core.validation_utils`) provides a set of functions for validating configuration files, environment variables, and other inputs. These utilities ensure that inputs meet the expected format and constraints, providing consistent error handling and logging.

## Overview

The validation utilities are designed to:

- Validate file and directory existence
- Validate port numbers, CPU limits, and memory limits
- Validate URLs, email addresses, and boolean values
- Validate configuration files (.env, YAML, JSON)
- Validate entire configuration directories

The module implements caching mechanisms to improve performance for frequently called validation functions, particularly for filesystem operations.

## API Reference

### File and Directory Validation

#### `validate_file_exists(file_path: str) -> bool`

Validates that a file exists at the specified path.

**Parameters:**
- `file_path`: Path to the file to check

**Returns:**
- `bool`: True if the file exists, False otherwise

**Example:**
```python
from llm_stack.core import validation_utils

if validation_utils.validate_file_exists("config.json"):
    # Process the file
    pass
else:
    # Handle the error
    pass
```

#### `validate_directory_exists(directory_path: str) -> bool`

Validates that a directory exists at the specified path.

**Parameters:**
- `directory_path`: Path to the directory to check

**Returns:**
- `bool`: True if the directory exists, False otherwise

**Example:**
```python
from llm_stack.core import validation_utils

if validation_utils.validate_directory_exists("config"):
    # Process the directory
    pass
else:
    # Handle the error
    pass
```

### Value Validation

#### `validate_port(port_value: str, variable_name: str = "port") -> bool`

Validates that a port value is valid (an integer between 1 and 65535).

**Parameters:**
- `port_value`: Port value to validate (as a string)
- `variable_name`: Name of the variable for error messages (default: "port")

**Returns:**
- `bool`: True if the port is valid, False otherwise

**Example:**
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

#### `validate_cpu_format(cpu_value: str, variable_name: str = "CPU limit") -> bool`

Validates that a CPU limit value is valid (a positive number).

**Parameters:**
- `cpu_value`: CPU limit value to validate (as a string)
- `variable_name`: Name of the variable for error messages (default: "CPU limit")

**Returns:**
- `bool`: True if the CPU limit is valid, False otherwise

**Example:**
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

#### `validate_memory_format(memory_value: str, variable_name: str = "memory limit") -> bool`

Validates that a memory limit value is valid (a number followed by an optional unit K, M, or G).

**Parameters:**
- `memory_value`: Memory limit value to validate (as a string, e.g., "512M", "4G")
- `variable_name`: Name of the variable for error messages (default: "memory limit")

**Returns:**
- `bool`: True if the memory limit is valid, False otherwise

**Example:**
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

#### `validate_url(url_value: str, variable_name: str = "URL") -> bool`

Validates that a URL value is valid.

**Parameters:**
- `url_value`: URL value to validate (as a string)
- `variable_name`: Name of the variable for error messages (default: "URL")

**Returns:**
- `bool`: True if the URL is valid, False otherwise

**Example:**
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

#### `validate_email(email_value: str, variable_name: str = "email") -> bool`

Validates that an email value is valid.

**Parameters:**
- `email_value`: Email value to validate (as a string)
- `variable_name`: Name of the variable for error messages (default: "email")

**Returns:**
- `bool`: True if the email is valid, False otherwise

**Example:**
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

#### `validate_boolean(bool_value: str, variable_name: str = "boolean") -> bool`

Validates that a string value represents a valid boolean.

**Parameters:**
- `bool_value`: Boolean value to validate (as a string)
- `variable_name`: Name of the variable for error messages (default: "boolean")

**Returns:**
- `bool`: True if the value is a valid boolean, False otherwise

**Example:**
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

### Configuration File Validation

#### `validate_env_file(env_file: str) -> bool`

Validates an environment (.env) file.

**Parameters:**
- `env_file`: Path to the environment file to validate

**Returns:**
- `bool`: True if the file is valid, False otherwise

**Example:**
```python
from llm_stack.core import validation_utils

# Validate a .env file
if validation_utils.validate_env_file(".env"):
    print("Environment file is valid")
else:
    print("Environment file is invalid")
```

#### `validate_yaml_file(yaml_file: str) -> bool`

Validates a YAML file.

**Parameters:**
- `yaml_file`: Path to the YAML file to validate

**Returns:**
- `bool`: True if the file is valid, False otherwise

**Example:**
```python
from llm_stack.core import validation_utils

# Validate a YAML file
if validation_utils.validate_yaml_file("docker-compose.yml"):
    print("YAML file is valid")
else:
    print("YAML file is invalid")
```

#### `validate_json_file(json_file: str) -> bool`

Validates a JSON file.

**Parameters:**
- `json_file`: Path to the JSON file to validate

**Returns:**
- `bool`: True if the file is valid, False otherwise

**Example:**
```python
from llm_stack.core import validation_utils

# Validate a JSON file
if validation_utils.validate_json_file("config.json"):
    print("JSON file is valid")
else:
    print("JSON file is invalid")
```

#### `validate_config_directory(config_dir: str, max_workers: int = 4) -> bool`

Validates a configuration directory by checking all .env, .yml/.yaml, and .json files.

**Parameters:**
- `config_dir`: Path to the configuration directory to validate
- `max_workers`: Maximum number of worker threads for parallel validation (default: 4)

**Returns:**
- `bool`: True if the directory and all its configuration files are valid, False otherwise

**Example:**
```python
from llm_stack.core import validation_utils

# Validate a configuration directory
if validation_utils.validate_config_directory("config"):
    print("Configuration directory is valid")
else:
    print("Configuration directory is invalid")
```

## Caching Mechanism

The validation utilities implement a caching mechanism to improve performance for frequently called validation functions, particularly for filesystem operations. The caching is implemented using the `cache_validation_result` decorator.

### `cache_validation_result(func: Callable) -> Callable`

Caches the results of validation functions to avoid redundant validations.

**Parameters:**
- `func`: Function to decorate. The function should take at least one argument that can be used as a cache key.

**Returns:**
- `Callable`: Decorated function with caching capability

**Example:**
```python
from llm_stack.core import validation_utils

@validation_utils.cache_validation_result
def my_validation_function(value: str) -> bool:
    # Expensive validation logic
    return True
```

## Error Handling

All validation functions follow a consistent error handling pattern:

1. If validation fails, an error message is logged using the `logging` module.
2. The function returns `False` to indicate validation failure.
3. The error message includes the name of the variable being validated (if provided).

This consistent error handling makes it easy to use validation functions in a uniform way throughout the codebase.

## Best Practices

When using the validation utilities, follow these best practices:

1. **Import from the core package**: Import validation utilities directly from `llm_stack.core` rather than from the individual module.

   ```python
   # Good
   from llm_stack.core import validate_port, validate_env_file
   
   # Avoid
   from llm_stack.core.validation_utils import validate_port, validate_env_file
   ```

2. **Check return values**: Always check the return value of validation functions to handle validation failures.

   ```python
   if not validate_port(port_value, "HTTP_PORT"):
       # Handle validation failure
       return False
   ```

3. **Provide variable names**: When validating configuration values, provide the variable name for better error messages.

   ```python
   validate_memory_format(memory_value, "CONTAINER_MEMORY_LIMIT")
   ```

4. **Use parallel validation**: For validating multiple files, use `validate_config_directory` with an appropriate number of worker threads.

   ```python
   validate_config_directory("config", max_workers=8)  # For large directories
   ```

## Integration with Other Components

The validation utilities are used throughout the LOCAL-LLM-STACK-RELOADED project, particularly in:

- **Configuration Management**: Validating configuration files and values
- **CLI Commands**: Validating command-line arguments and options
- **Docker Integration**: Validating Docker-related configuration
- **Module and Tool Integration**: Validating module and tool configuration

By using these validation utilities consistently, the project ensures that configuration errors are caught early and reported clearly.