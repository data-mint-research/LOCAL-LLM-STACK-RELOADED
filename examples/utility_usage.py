#!/usr/bin/env python3
"""
Example usage of the core utilities.

This script demonstrates how to use the various utility modules
that have been extracted to reduce code redundancy.
"""

import os
import sys
import networkx as nx
from pathlib import Path

# Add the project directory to the Python path
sys.path.insert(0, os.path.abspath(os.path.dirname(os.path.dirname(__file__))))

# Import core utilities
from llm_stack.core import (
    # File utilities
    read_file, write_file, backup_file, ensure_directory_exists, parse_env_file,
    
    # Command utilities
    run_command, check_command_exists,
    
    # Database utilities
    get_neo4j_manager,
    
    # CLI utilities
    print_success, print_error, print_warning, print_info, create_table, print_table,
    
    # Validation utilities
    validate_yaml_file, validate_port, validate_email,
    
    # Visualization utilities
    create_network_graph, create_bar_chart, create_pie_chart
)

from llm_stack.core import logging


def demonstrate_file_utils():
    """Demonstrate file utilities."""
    print("\n=== File Utilities ===\n")
    
    # Create a temporary directory for examples
    temp_dir = Path("./examples/temp")
    if ensure_directory_exists(str(temp_dir)):
        print_success(f"Created directory: {temp_dir}")
    
    # Write a file
    config_file = temp_dir / "example_config.json"
    config_content = """
    {
        "name": "example",
        "version": "1.0.0",
        "settings": {
            "port": 8080,
            "debug": true
        }
    }
    """
    
    if write_file(str(config_file), config_content):
        print_success(f"Wrote file: {config_file}")
    
    # Read the file
    success, content = read_file(str(config_file))
    if success:
        print_success(f"Read file: {config_file}")
        print(f"Content preview: {content[:50]}...")
    
    # Create a backup
    backup_path = backup_file(str(config_file))
    if backup_path:
        print_success(f"Created backup: {backup_path}")
    
    # Parse an env file
    env_file = temp_dir / "example.env"
    env_content = """
    # Example .env file
    PORT=8080
    DEBUG=true
    API_KEY=abc123
    """
    
    if write_file(str(env_file), env_content):
        print_success(f"Wrote .env file: {env_file}")
    
    variables = parse_env_file(str(env_file))
    print(f"Parsed variables: {variables}")


def demonstrate_command_utils():
    """Demonstrate command utilities."""
    print("\n=== Command Utilities ===\n")
    
    # Check if a command exists
    if check_command_exists("python"):
        print_success("Python command exists")
    else:
        print_error("Python command not found")
    
    # Run a command
    returncode, stdout, stderr = run_command(["python", "--version"])
    if returncode == 0:
        print_success(f"Python version: {stdout.strip()}")
    else:
        print_error(f"Error: {stderr}")
    
    # Run a more complex command
    returncode, stdout, stderr = run_command(["ls", "-la"])
    if returncode == 0:
        print_success("Directory listing:")
        print(stdout[:200] + "..." if len(stdout) > 200 else stdout)
    else:
        print_error(f"Error: {stderr}")


def demonstrate_cli_utils():
    """Demonstrate CLI utilities."""
    print("\n=== CLI Utilities ===\n")
    
    # Print formatted messages
    print_info("This is an informational message")
    print_success("This is a success message")
    print_warning("This is a warning message")
    print_error("This is an error message")
    
    # Create and print a table
    table = create_table("Example Table", [
        ("Name", "cyan"),
        ("Value", "green"),
        ("Description", "yellow")
    ])
    
    table.add_row("Port", "8080", "HTTP port")
    table.add_row("Debug", "true", "Enable debug mode")
    table.add_row("API Key", "abc123", "API authentication key")
    
    print_table(table)


def demonstrate_validation_utils():
    """Demonstrate validation utilities."""
    print("\n=== Validation Utilities ===\n")
    
    # Create a temporary directory for examples
    temp_dir = Path("./examples/temp")
    ensure_directory_exists(str(temp_dir))
    
    # Create a YAML file to validate
    yaml_file = temp_dir / "example.yaml"
    yaml_content = """
    version: '3'
    services:
      web:
        image: nginx:latest
        ports:
          - "8080:80"
      db:
        image: postgres:13
        environment:
          POSTGRES_PASSWORD: example
    """
    
    write_file(str(yaml_file), yaml_content)
    
    # Validate the YAML file
    if validate_yaml_file(str(yaml_file)):
        print_success(f"YAML file is valid: {yaml_file}")
    else:
        print_error(f"YAML file is invalid: {yaml_file}")
    
    # Validate a port
    if validate_port("8080", "HTTP_PORT"):
        print_success("Port 8080 is valid")
    else:
        print_error("Port 8080 is invalid")
    
    if validate_port("999999", "INVALID_PORT"):
        print_success("Port 999999 is valid")
    else:
        print_error("Port 999999 is invalid")
    
    # Validate an email
    if validate_email("user@example.com", "ADMIN_EMAIL"):
        print_success("Email user@example.com is valid")
    else:
        print_error("Email user@example.com is invalid")
    
    if validate_email("invalid-email", "INVALID_EMAIL"):
        print_success("Email invalid-email is valid")
    else:
        print_error("Email invalid-email is invalid")


def demonstrate_visualization_utils():
    """Demonstrate visualization utilities."""
    print("\n=== Visualization Utilities ===\n")
    
    # Create a temporary directory for examples
    temp_dir = Path("./examples/temp")
    ensure_directory_exists(str(temp_dir))
    
    # Create a network graph
    graph = nx.DiGraph()
    graph.add_node("Web")
    graph.add_node("API")
    graph.add_node("Database")
    graph.add_node("Cache")
    
    graph.add_edge("Web", "API", relationship="CALLS")
    graph.add_edge("API", "Database", relationship="QUERIES")
    graph.add_edge("API", "Cache", relationship="USES")
    
    graph_path = temp_dir / "network_graph.png"
    create_network_graph(graph, str(graph_path), "Component Relationships", "lightblue")
    print_success(f"Created network graph: {graph_path}")
    
    # Create a bar chart
    data = {
        "Web": 15,
        "API": 25,
        "Database": 10,
        "Cache": 5
    }
    
    bar_path = temp_dir / "bar_chart.png"
    create_bar_chart(
        data, str(bar_path), "Component Usage", "Component", "Requests per second"
    )
    print_success(f"Created bar chart: {bar_path}")
    
    # Create a pie chart
    sizes = [15, 25, 10, 5]
    labels = ["Web", "API", "Database", "Cache"]
    
    pie_path = temp_dir / "pie_chart.png"
    create_pie_chart(sizes, labels, str(pie_path), "Resource Usage")
    print_success(f"Created pie chart: {pie_path}")


def demonstrate_db_utils():
    """Demonstrate database utilities."""
    print("\n=== Database Utilities ===\n")
    
    # Note: This example doesn't actually connect to Neo4j
    # It just demonstrates the API
    
    print_info("Note: This example doesn't actually connect to Neo4j")
    print_info("It just demonstrates the API")
    
    # Get Neo4j connection manager
    neo4j = get_neo4j_manager(
        uri="bolt://localhost:7687",
        username="neo4j",
        password="password"
    )
    
    # In a real application, you would check the connection
    # if neo4j.ensure_connected():
    #     results = neo4j.run_query("MATCH (n) RETURN n LIMIT 10")
    #     print(f"Query results: {results}")
    
    print_info("Neo4j connection manager created")
    print_info("URI: bolt://localhost:7687")
    print_info("Username: neo4j")


def main():
    """Main function."""
    print("Demonstrating core utilities...")
    
    # Demonstrate file utilities
    demonstrate_file_utils()
    
    # Demonstrate command utilities
    demonstrate_command_utils()
    
    # Demonstrate CLI utilities
    demonstrate_cli_utils()
    
    # Demonstrate validation utilities
    demonstrate_validation_utils()
    
    # Demonstrate visualization utilities
    demonstrate_visualization_utils()
    
    # Demonstrate database utilities
    demonstrate_db_utils()
    
    print("\nAll demonstrations completed!")


if __name__ == "__main__":
    main()