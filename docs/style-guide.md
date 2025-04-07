# LOCAL-LLM-STACK-RELOADED Style Guide

This document outlines the coding standards and conventions to be followed in the LOCAL-LLM-STACK-RELOADED project. Adhering to these guidelines ensures consistency, maintainability, and readability across the codebase.

## Table of Contents

1. [Naming Conventions](#naming-conventions)
2. [Documentation Standards](#documentation-standards)
3. [Code Formatting](#code-formatting)
4. [Error Handling](#error-handling)
5. [Testing Conventions](#testing-conventions)
6. [Import Organization](#import-organization)
7. [File Organization](#file-organization)
8. [Design Patterns](#design-patterns)
9. [Code Quality Tools](#code-quality-tools)

## Naming Conventions

### Python Module Naming

- **Package Names**: Lowercase with underscores (snake_case)
  ```python
  # Good
  knowledge_graph
  core
  
  # Bad
  KnowledgeGraph
  Core
  ```

- **Module Names**: Lowercase with underscores (snake_case)
  ```python
  # Good
  config.py
  error.py
  
  # Bad
  Config.py
  Error.py
  ```

- **Class Names**: CamelCase
  ```python
  # Good
  class ConfigManager:
      pass
  
  # Bad
  class config_manager:
      pass
  ```

- **Function Names**: Lowercase with underscores (snake_case)
  ```python
  # Good
  def validate_config():
      pass
  
  # Bad
  def ValidateConfig():
      pass
  ```

- **Constant Names**: UPPERCASE with underscores
  ```python
  # Good
  DEFAULT_CONFIG_DIR = "config"
  
  # Bad
  defaultConfigDir = "config"
  ```

- **Variable Names**: Lowercase with underscores (snake_case)
  ```python
  # Good
  config_manager = ConfigManager()
  
  # Bad
  ConfigManager = ConfigManager()
  ```

- **Private Attributes**: Prefix with a single underscore
  ```python
  # Good
  self._initialized = False
  
  # Bad
  self.initialized = False  # For private attributes
  ```

### Configuration Files

- **Environment Files**: `.env` for environment variables
- **Docker Compose Files**: `docker-compose.yml` or `<component>.yml`
- **Configuration Templates**: `<name>-template.<extension>`

### Documentation Files

- **Markdown Files**: `<name>.md`
- **Diagram Files**: `<name>.mmd` for Mermaid diagrams
- **API Documentation**: Generated from docstrings

### Test Files

- **Test Files**: `test_<module_name>.py`
- **Fixture Files**: Placed in `fixtures/` directory
- **Mock Data**: Placed in `fixtures/` directory

## Documentation Standards

### Docstrings

All modules, classes, and functions should have docstrings following the Google style:

```python
"""
Short description of the module/class/function.

Longer description that explains the purpose and functionality
in more detail if needed.

Attributes (for modules/classes):
    attribute_name: Description of the attribute.

Args (for functions):
    param_name: Description of the parameter.

Returns:
    Description of the return value.

Raises:
    ExceptionType: Description of when this exception is raised.

Examples:
    Examples of how to use the function/class.
"""
```

#### Module Docstrings

```python
"""
Configuration management for the LLM Stack.

This module provides functions for loading, validating, and managing the configuration.
"""
```

#### Class Docstrings

```python
class ConfigManager:
    """Configuration manager for the LLM Stack.
    
    This class provides methods for loading, validating, and managing
    the configuration for the LLM Stack.
    
    Attributes:
        config_dir: Directory containing configuration files.
        env_file: Path to the environment file.
    """
```

#### Function Docstrings

```python
def validate_config(config_file: str) -> bool:
    """
    Validate a configuration file.
    
    Args:
        config_file: Path to the configuration file.
        
    Returns:
        bool: True if the configuration is valid, False otherwise.
        
    Raises:
        ConfigError: If the configuration file is invalid.
    """
```

### Type Hints

All functions should have type hints for parameters and return values:

```python
from typing import Dict, List, Optional, Union

def get_config(key: str, default: Optional[str] = None) -> Optional[str]:
    """Get a configuration value."""
    pass

def get_config_section(section: str) -> Dict[str, Union[str, int, bool]]:
    """Get a configuration section."""
    pass
```

### Comments

- Comments should explain why, not what
- Comments should be used sparingly
- Comments should be kept up-to-date
- All comments should be in English

```python
# Good
# Retry the operation to handle transient network errors
retry_count = 3

# Bad
# Set retry_count to 3
retry_count = 3
```

## Code Formatting

### PEP 8 Compliance

All code should follow the [PEP 8](https://www.python.org/dev/peps/pep-0008/) style guide:

- Use 4 spaces for indentation (no tabs)
- Maximum line length of 88 characters (Black default)
- Surround top-level functions and classes with two blank lines
- Surround method definitions inside classes with one blank line
- Use blank lines to separate logical sections

### Formatting Tools

- **Black**: Use Black for automatic code formatting
  ```bash
  black path/to/file.py
  ```

- **isort**: Use isort for sorting imports
  ```bash
  isort path/to/file.py
  ```

### String Formatting

- Use f-strings for string formatting when possible
  ```python
  # Good
  name = "World"
  greeting = f"Hello, {name}!"
  
  # Acceptable for older Python versions
  greeting = "Hello, {}!".format(name)
  
  # Bad
  greeting = "Hello, " + name + "!"
  ```

- Use triple quotes for multi-line strings and docstrings
  ```python
  message = """
  This is a multi-line
  string.
  """
  ```

### Whitespace

- No trailing whitespace
- Always surround binary operators with a single space
- No space around the equals sign in keyword arguments or default parameter values
  ```python
  # Good
  def func(default=None):
      x = y + z
      
  # Bad
  def func(default = None):
      x=y+z
  ```

## Error Handling

### Exception Hierarchy

All exceptions should inherit from the base `LLMStackError` class:

```python
class LLMStackError(Exception):
    """Base class for all LLM Stack exceptions."""
    
    def __init__(self, message: str, code: ErrorCode = ErrorCode.GENERAL_ERROR):
        """
        Initialize a new LLM Stack exception.
        
        Args:
            message: Error message
            code: Error code
        """
        self.message = message
        self.code = code
        super().__init__(f"[{code.name}] {message}")
```

Specific exception types should be created for different error categories:

```python
class ConfigError(LLMStackError):
    """Exception for configuration errors."""
    
    def __init__(self, message: str):
        """
        Initialize a new configuration error exception.
        
        Args:
            message: Error message
        """
        super().__init__(message, ErrorCode.CONFIG_ERROR)
```

### Error Codes

Use the `ErrorCode` enum for consistent error codes:

```python
class ErrorCode(Enum):
    """Error codes for the LLM Stack."""
    
    SUCCESS = 0
    GENERAL_ERROR = 1
    CONFIG_ERROR = 2
    # ...
```

### Exception Handling

- Catch exceptions at the appropriate level
- Use specific exception types when possible
- Log exceptions with context
- Convert exceptions to user-friendly messages

```python
try:
    config.load_config()
except ConfigError as e:
    logging.error(f"Failed to load configuration: {str(e)}")
    sys.exit(1)
```

### Error Handling Utilities

Use the provided error handling utilities:

- `handle_error`: Handle an LLM Stack error
- `handle_exception`: Handle a general exception
- `try_except`: Execute a function and catch exceptions
- `assert_condition`: Assert a condition and raise an exception if it fails
- `error_handler`: Decorator for error handling
- `raise_error`: Raise an exception based on an error code
- `handle_result`: Handle a result and raise an exception if it's None

```python
# Using the error_handler decorator
@error_handler({ConnectionError: ErrorCode.NETWORK_ERROR})
def fetch_data():
    # This function will have automatic error handling
    pass

# Using assert_condition
assert_condition(port > 0, "Port must be positive", ErrorCode.VALIDATION_ERROR)

# Using handle_result
result = handle_result(get_data(), "Failed to get data", ErrorCode.API_ERROR)
```

## Testing Conventions

### Test Organization

- Tests should be organized by module
- Tests should be in a `tests/unit` or `tests/integration` directory
- Tests should follow the same structure as the code

### Test Naming

- Test files should be named `test_<module_name>.py`
- Test classes should be named `Test<ClassName>`
- Test functions should be named `test_<function_name>`

```python
# File: tests/unit/core/test_config.py

class TestConfig:
    """Test cases for the config module."""
    
    def test_load_config(self):
        """Test the load_config function."""
        pass
```

### Test Coverage

- Tests should cover all public functions
- Tests should cover edge cases
- Tests should cover error cases

### Test Fixtures

Use pytest fixtures for test setup and teardown:

```python
@pytest.fixture
def config_file():
    """Create a temporary configuration file."""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml") as f:
        f.write("key: value\n")
        f.flush()
        yield f.name
```

### Mocks

Use unittest.mock for mocking external dependencies:

```python
@patch("llm_stack.core.docker.client")
def test_docker_compose_up(mock_client):
    """Test docker_compose_up function."""
    mock_client.containers.run.return_value = {"Id": "container_id"}
    result = docker.compose_up("project", "compose_file", "service")
    assert result is True
    mock_client.containers.run.assert_called_once()
```

### Assertions

Use pytest assertions for clear test results:

```python
def test_get_config():
    """Test the get_config function."""
    # Setup
    config_manager = ConfigManager()
    config_manager.config_values = {"TEST_KEY": "test_value"}
    
    # Execute
    result = config_manager.get_config("TEST_KEY", "default")
    
    # Assert
    assert result == "test_value"
```

## Import Organization

### Import Order

Imports should be organized in the following order:

1. Standard library imports
2. Related third-party imports
3. Local application/library specific imports

Each group should be separated by a blank line:

```python
# Standard library imports
import os
import sys
from typing import Dict, List, Optional

# Third-party imports
import yaml
from pydantic import BaseModel

# Local imports
from llm_stack.core import logging
from llm_stack.core.error import ConfigError
```

### Import Style

- Use absolute imports for clarity
- Avoid wildcard imports (`from module import *`)
- Use aliases for long or conflicting module names

```python
# Good
from llm_stack.core import logging
import numpy as np

# Bad
from llm_stack.core.logging import *
```

### Circular Imports

Avoid circular imports by:
- Importing modules at function or method level when necessary
- Using forward references in type hints
- Restructuring code to avoid circular dependencies

```python
# Avoid circular imports with function-level imports
def get_module():
    from llm_stack.modules.knowledge_graph.module import KnowledgeGraphModule
    return KnowledgeGraphModule()
```

## File Organization

### Directory Structure

Follow the standardized directory structure:

```
LOCAL-LLM-STACK-RELOADED/
├── docs/                  # Project documentation
├── docker/                # Docker-related files
│   └── modules/           # Module-specific Docker files
├── examples/              # Example usage scripts
├── llm_stack/             # Main package
│   ├── cli_commands/      # CLI command implementations
│   ├── code_quality/      # Code quality tools
│   ├── core/              # Core functionality
│   ├── knowledge_graph/   # Knowledge graph functionality
│   ├── modules/           # Extensible modules
│   └── tools/             # Utility tools
├── tests/                 # Test suite
│   ├── fixtures/          # Test fixtures
│   ├── integration/       # Integration tests
│   └── unit/              # Unit tests
├── pyproject.toml         # Project configuration
├── setup.py               # Installation script
└── README.md              # Project overview
```

### Module Structure

Each module should follow this structure:

```
module_name/
├── __init__.py            # Package initialization
├── module.py              # Main module implementation
├── commands.py            # CLI commands (if applicable)
├── models.py              # Data models (if applicable)
└── README.md              # Module documentation
```

### File Content Organization

Within each file, organize content in the following order:

1. Module docstring
2. Imports
3. Constants
4. Exception classes
5. Classes
6. Functions
7. Main execution code (if applicable)

```python
"""
Module docstring.
"""

# Imports
import os
from typing import Dict

# Constants
DEFAULT_VALUE = 42

# Exception classes
class ModuleError(Exception):
    pass

# Classes
class ModuleClass:
    pass

# Functions
def module_function():
    pass

# Main execution
if __name__ == "__main__":
    module_function()
```

## Design Patterns

### Singleton Pattern

Use the singleton pattern for module instances:

```python
class Module:
    """Example module with singleton pattern."""
    
    # Singleton instance
    _instance = None
    _lock = threading.Lock()
    
    def __new__(cls):
        """Implement thread-safe singleton pattern."""
        with cls._lock:
            if cls._instance is None:
                cls._instance = super(Module, cls).__new__(cls)
                cls._instance._initialized = False
            return cls._instance
    
    def __init__(self):
        """Initialize the module with default values."""
        # Only initialize once
        if getattr(self, '_initialized', False):
            return
            
        # Initialization code here
        self._initialized = True

# Module-level getter function
def get_module():
    """Get the module instance."""
    return Module()
```

### Factory Pattern

Use the factory pattern for creating objects:

```python
def create_logger(name):
    """Create a logger."""
    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)
    return logger
```

### Strategy Pattern

Use the strategy pattern for interchangeable algorithms:

```python
class ValidationStrategy:
    """Interface for validation strategies."""
    
    def validate(self, value):
        """Validate a value."""
        pass

class RequiredValidator(ValidationStrategy):
    """Validator that checks if a value is not None."""
    
    def validate(self, value):
        """Validate that a value is not None."""
        return value is not None

class TypeValidator(ValidationStrategy):
    """Validator that checks if a value is of a specific type."""
    
    def __init__(self, expected_type):
        """Initialize the validator with an expected type."""
        self.expected_type = expected_type
    
    def validate(self, value):
        """Validate that a value is of the expected type."""
        return isinstance(value, self.expected_type)
```

### Dependency Injection

Use dependency injection to reduce coupling:

```python
class Module:
    """Example module with dependency injection."""
    
    def __init__(self, logger=None, config=None):
        """Initialize the module with dependencies."""
        self.logger = logger or logging.get_logger()
        self.config = config or config.get_config()
```

## Code Quality Tools

The project uses several code quality tools to maintain high standards:

### pyupgrade

pyupgrade automatically upgrades Python syntax to newer versions:

```bash
pyupgrade --py38-plus path/to/file.py
```

### isort

isort sorts imports alphabetically and automatically separates them into sections:

```bash
isort path/to/file.py
```

### black

black is an opinionated code formatter that enforces a consistent style:

```bash
black path/to/file.py
```

### vulture

vulture finds unused code:

```bash
vulture path/to/file.py
```

### Code Quality Command

The project provides a unified command for running all code quality tools:

```bash
llm codeqa run path/to/file.py
```

Or for a directory:

```bash
llm codeqa run path/to/directory --recursive
```

## Conclusion

Following these style guidelines ensures consistency across the codebase and makes it easier for developers to understand, maintain, and extend the code. If you have any questions or suggestions for improving these guidelines, please open an issue or pull request.