"""
CLI utilities for the LLM Stack.

This module provides common CLI command patterns and utilities
to reduce code duplication across CLI command implementations.
"""

import argparse
import os
import sys
from typing import Any, Callable, Dict, List, Optional, Tuple, Union

from rich.console import Console
from rich.table import Table

from llm_stack.core import logging


# Console for formatted output
console = Console()


class CommandRegistry:
    """Registry for CLI commands."""
    
    def __init__(self):
        """Initialize the command registry."""
        self.commands = {}
        self.parsers = {}
    
    def register(self, name: str, handler: Callable, setup_parser: Optional[Callable] = None):
        """
        Register a command.
        
        Args:
            name: Command name
            handler: Command handler function
            setup_parser: Function to set up the command's argument parser
        """
        self.commands[name] = handler
        if setup_parser:
            self.parsers[name] = setup_parser
    
    def get_command(self, name: str) -> Optional[Callable]:
        """
        Get a command handler by name.
        
        Args:
            name: Command name
            
        Returns:
            Optional[Callable]: Command handler function
        """
        return self.commands.get(name)
    
    def get_parser_setup(self, name: str) -> Optional[Callable]:
        """
        Get a command's parser setup function by name.
        
        Args:
            name: Command name
            
        Returns:
            Optional[Callable]: Parser setup function
        """
        return self.parsers.get(name)
    
    def get_all_commands(self) -> Dict[str, Callable]:
        """
        Get all registered commands.
        
        Returns:
            Dict[str, Callable]: Dictionary of command names and handlers
        """
        return self.commands


# Singleton instance of command registry
_registry = None


def get_registry() -> CommandRegistry:
    """
    Get the singleton instance of command registry.
    
    Returns:
        CommandRegistry: Command registry
    """
    global _registry
    
    if _registry is None:
        _registry = CommandRegistry()
    
    return _registry


def register_command(name: str):
    """
    Decorator to register a command.
    
    Args:
        name: Command name
        
    Returns:
        Callable: Decorator function
    """
    def decorator(func):
        registry = get_registry()
        registry.register(name, func)
        return func
    
    return decorator


def setup_cli_parser() -> argparse.ArgumentParser:
    """
    Set up the main CLI parser.
    
    Returns:
        argparse.ArgumentParser: Main CLI parser
    """
    parser = argparse.ArgumentParser(
        description="LOCAL-LLM-STACK-RELOADED CLI",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    
    subparsers = parser.add_subparsers(dest="command", help="Command to execute")
    
    # Register all command parsers
    registry = get_registry()
    for name, setup_func in registry.parsers.items():
        if setup_func:
            setup_func(subparsers)
    
    return parser


def create_table(title: str, columns: List[Tuple[str, str]]) -> Table:
    """
    Create a Rich table with consistent styling.
    
    Args:
        title: Table title
        columns: List of (column name, style) tuples
        
    Returns:
        Table: Rich table
    """
    table = Table(title=title)
    
    for name, style in columns:
        table.add_column(name, style=style)
    
    return table


def print_table(table: Table):
    """
    Print a Rich table.
    
    Args:
        table: Rich table
    """
    console.print(table)
    console.print()


def print_success(message: str):
    """
    Print a success message.
    
    Args:
        message: Success message
    """
    console.print(f"[green]✓[/green] {message}")


def print_error(message: str):
    """
    Print an error message.
    
    Args:
        message: Error message
    """
    console.print(f"[red]✗[/red] {message}")


def print_warning(message: str):
    """
    Print a warning message.
    
    Args:
        message: Warning message
    """
    console.print(f"[yellow]![/yellow] {message}")


def print_info(message: str):
    """
    Print an info message.
    
    Args:
        message: Info message
    """
    console.print(f"[blue]i[/blue] {message}")


def print_command_help(command: str, description: str, usage: str, examples: List[Tuple[str, str]]):
    """
    Print help for a command.
    
    Args:
        command: Command name
        description: Command description
        usage: Command usage
        examples: List of (example, description) tuples
    """
    console.print(f"[bold]Command:[/bold] {command}")
    console.print(f"[bold]Description:[/bold] {description}")
    console.print()
    console.print(f"[bold]Usage:[/bold] {usage}")
    console.print()
    
    if examples:
        console.print("[bold]Examples:[/bold]")
        for example, desc in examples:
            console.print(f"  {example}")
            console.print(f"    {desc}")
        console.print()


def handle_command_error(error_code: int, message: str) -> int:
    """
    Handle a command error.
    
    Args:
        error_code: Error code
        message: Error message
        
    Returns:
        int: Error code
    """
    print_error(message)
    return error_code


def command_wrapper(func: Callable) -> Callable:
    """
    Decorator to wrap a command handler with common error handling.
    
    Args:
        func: Command handler function
        
    Returns:
        Callable: Wrapped command handler function
    """
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            logging.error(f"Error executing command: {str(e)}")
            return handle_command_error(1, f"Error: {str(e)}")
    
    return wrapper