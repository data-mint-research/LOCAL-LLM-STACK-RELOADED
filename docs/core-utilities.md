# Core Utilities

This document describes the shared utility modules that have been extracted to reduce code redundancy and improve maintainability in the LOCAL-LLM-STACK-RELOADED project.

## Overview

The core utilities provide common functionality that is used across multiple parts of the codebase. By centralizing these functions, we:

- Reduce code duplication
- Ensure consistent error handling and logging
- Make the codebase more maintainable
- Simplify testing
- Provide a clear API for common operations

## Available Utilities

### File Utilities (`llm_stack.core.file_utils`)

Functions for common file operations with consistent error handling and logging.

```python
from llm_stack.core import read_file, write_file, backup_file

# Read a file with error handling
success, content = read_file("config.json")
if success:
    # Process content
    pass

# Write to a file with error handling
success = write_file("output.txt", "Hello, world!")

# Create a backup of a file
backup_path = backup_file("important_config.json")
```

Key functions:
- `read_file(file_path, default=None)`: Read a file with error handling
- `write_file(file_path, content)`: Write content to a file
- `backup_file(file_path)`: Create a backup of a file
- `ensure_file_exists(file_path)`: Check if a file exists
- `ensure_directory_exists(directory_path)`: Ensure a directory exists
- `list_files(directory_path, pattern=None)`: List files in a directory
- `parse_env_file(file_path)`: Parse a .env file into a dictionary

### Command Utilities (`llm_stack.core.command_utils`)

Functions for executing commands with consistent error handling and security practices.

```python
from llm_stack.core import run_command, check_command_exists

# Execute a command
returncode, stdout, stderr = run_command(["ls", "-la"])

# Check if a command exists
if check_command_exists("docker"):
    # Use Docker
    pass
```

Key functions:
- `run_command(command, cwd=None)`: Execute a command
- `check_command_exists(command)`: Check if a command exists
- `run_python_module(module, args=None, cwd=None)`: Run a Python module
- `run_pip_install(packages, upgrade=False, cwd=None)`: Run pip install

### Database Utilities (`llm_stack.core.db_utils`)

Classes and functions for database operations, particularly for Neo4j.

```python
from llm_stack.core import get_neo4j_manager

# Get Neo4j connection manager
neo4j = get_neo4j_manager(uri="bolt://localhost:7687", username="neo4j", password="password")

# Ensure connection and run a query
if neo4j.ensure_connected():
    results = neo4j.run_query("MATCH (n) RETURN n LIMIT 10")
```

Key classes and functions:
- `DatabaseConnectionManager`: Base class for database connection managers
- `Neo4jConnectionManager`: Neo4j connection manager
- `get_neo4j_manager(uri=None, username=None, password=None)`: Get Neo4j connection manager

### CLI Utilities (`llm_stack.core.cli_utils`)

Functions and classes for CLI command handling and output formatting.

```python
from llm_stack.core import register_command, print_success, print_error, create_table, print_table

# Register a command
@register_command("my-command")
def my_command(args):
    # Command implementation
    print_success("Command executed successfully")
    
    # Create and print a table
    table = create_table("Results", [("Name", "cyan"), ("Value", "green")])
    table.add_row("Item 1", "Value 1")
    table.add_row("Item 2", "Value 2")
    print_table(table)
    
    return 0
```

Key functions and classes:
- `get_registry()`: Get command registry
- `register_command(name)`: Decorator to register a command
- `setup_cli_parser()`: Set up CLI parser
- `create_table(title, columns)`: Create a Rich table
- `print_table(table)`: Print a Rich table
- `print_success/error/warning/info(message)`: Print formatted messages
- `command_wrapper(func)`: Decorator for command error handling

### Validation Utilities (`llm_stack.core.validation_utils`)

Functions for validating configuration files, environment variables, and other inputs.

```python
from llm_stack.core import validate_env_file, validate_yaml_file, validate_port

# Validate a .env file
if validate_env_file(".env"):
    # File is valid
    pass

# Validate a YAML file
if validate_yaml_file("docker-compose.yml"):
    # File is valid
    pass

# Validate a port value
if validate_port("8080", "HTTP_PORT"):
    # Port is valid
    pass
```

Key functions:
- `validate_file_exists(file_path)`: Validate file existence
- `validate_directory_exists(directory_path)`: Validate directory existence
- `validate_port(port_value, variable_name)`: Validate port value
- `validate_cpu_format(cpu_value, variable_name)`: Validate CPU limit format
- `validate_memory_format(memory_value, variable_name)`: Validate memory limit format
- `validate_env_file(env_file)`: Validate .env file
- `validate_yaml_file(yaml_file)`: Validate YAML file
- `validate_json_file(json_file)`: Validate JSON file
- `validate_config_directory(config_dir)`: Validate configuration directory

### Visualization Utilities (`llm_stack.core.visualization_utils`)

Functions for creating visualizations with consistent styling and error handling.

```python
import networkx as nx
from llm_stack.core import create_network_graph, create_bar_chart, create_pie_chart

# Create a network graph
graph = nx.DiGraph()
graph.add_node("A")
graph.add_node("B")
graph.add_edge("A", "B", relationship="DEPENDS_ON")
create_network_graph(graph, "network.png", "Network Graph", node_color="lightblue")

# Create a bar chart
data = {"A": 10, "B": 20, "C": 15}
create_bar_chart(data, "bar.png", "Bar Chart", "Category", "Value")

# Create a pie chart
sizes = [15, 30, 45, 10]
labels = ["A", "B", "C", "D"]
create_pie_chart(sizes, labels, "pie.png", "Pie Chart")
```

Key functions:
- `create_directory(output_dir)`: Create directory for visualizations
- `create_network_graph(graph, output_path, title, node_color, figsize)`: Create network graph
- `create_bar_chart(data, output_path, title, xlabel, ylabel, color, figsize, rotate_labels)`: Create bar chart
- `create_pie_chart(sizes, labels, output_path, title, colors, explode, figsize)`: Create pie chart
- `create_line_chart(x_values, y_values, output_path, title, xlabel, ylabel, color, marker, figsize)`: Create line chart

## Best Practices

When using these utilities, follow these best practices:

1. **Import from the core package**: Import utilities directly from `llm_stack.core` rather than from the individual modules.

   ```python
   # Good
   from llm_stack.core import read_file, write_file
   
   # Avoid
   from llm_stack.core.file_utils import read_file, write_file
   ```

2. **Handle errors consistently**: All utilities return consistent error indicators (boolean success flags, None values, or error codes).

   ```python
   success, content = read_file("config.json")
   if not success:
       # Handle error
       return 1
   ```

3. **Use type hints**: All utilities include type hints for better IDE support and documentation.

4. **Check documentation**: Refer to the docstrings for detailed information about parameters and return values.

## Examples

### Example 1: Reading and validating a configuration file

```python
from llm_stack.core import read_file, validate_yaml_file

def load_config(config_path):
    # Validate the YAML file
    if not validate_yaml_file(config_path):
        return None
    
    # Read the file
    success, content = read_file(config_path)
    if not success:
        return None
    
    # Parse the YAML content
    import yaml
    try:
        return yaml.safe_load(content)
    except Exception as e:
        print(f"Error parsing YAML: {str(e)}")
        return None
```

### Example 2: Running a command and handling the output

```python
from llm_stack.core import run_command, print_success, print_error

def run_docker_compose(compose_file):
    returncode, stdout, stderr = run_command(["docker-compose", "-f", compose_file, "up", "-d"])
    
    if returncode == 0:
        print_success("Docker Compose started successfully")
        return True
    else:
        print_error(f"Docker Compose failed: {stderr}")
        return False
```

### Example 3: Creating a CLI command

```python
from llm_stack.core import register_command, print_info, create_table, print_table

@register_command("status")
def status_command(args):
    print_info("Checking status...")
    
    # Create a table for status information
    table = create_table("Component Status", [("Component", "cyan"), ("Status", "green")])
    
    # Add rows to the table
    table.add_row("Database", "Running")
    table.add_row("API Server", "Running")
    table.add_row("Web UI", "Stopped")
    
    # Print the table
    print_table(table)
    
    return 0
```

## Contributing

When adding new functionality to the codebase, consider whether it could be added to one of these utility modules instead of duplicating code. If you find yourself writing similar code in multiple places, it's a good candidate for extraction into a utility function.

To add a new utility function:

1. Add the function to the appropriate utility module
2. Add the function to the `__all__` list in `llm_stack/core/__init__.py`
3. Add documentation for the function in this document
4. Add tests for the function

## Conclusion

These utility modules provide a foundation for consistent, maintainable code throughout the LOCAL-LLM-STACK-RELOADED project. By leveraging these utilities, you can reduce code duplication, ensure consistent error handling, and focus on implementing the unique aspects of your components.