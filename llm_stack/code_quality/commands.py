"""
CLI commands for the Code Quality module.

This module provides command-line interfaces for code quality checking
and optimization.
"""

import os
import sys
from typing import Optional

import click
from rich.console import Console
from rich.table import Table

from llm_stack.code_quality.module import get_module
from llm_stack.core import dependency_injection, logging, system

# Console for formatted output
console = Console()


@click.group(name="codeqa")
def codeqa_cli():
    """Code Quality commands."""
    pass


@codeqa_cli.command(name="run")
@click.argument("path", type=click.Path(exists=True))
@click.option(
    "--recursive",
    "-r",
    is_flag=True,
    help="Recursively optimize all Python files in the directory",
)
@click.option("--verbose", "-v", is_flag=True, help="Enable verbose output")
def run_command(path: str, recursive: bool, verbose: bool):
    """
    Run code quality checks and optimizations.
    
    Args:
        path: Path to the Python file or directory.
        recursive: Whether to recursively process all Python files in directories.
        verbose: Whether to enable verbose output.
    """
    # Initialize module
    module = get_module()
    if not module.initialize():
        logging.error("Error initializing the Code Quality module")
        sys.exit(1)

    # Enable verbose logging if requested
    if verbose:
        logging.set_verbose(True)

    # Determine absolute path if a relative path was provided
    if not os.path.isabs(path):
        path = os.path.join(system.get_project_root(), path)

    logging.info(f"Running code quality checks for {path}...")

    # Optimize file or directory
    if os.path.isfile(path):
        result = module.optimize_file(path)
        _display_file_result(result)
    elif os.path.isdir(path):
        if recursive:
            result = module.optimize_directory(path)
            _display_directory_result(result)
        else:
            # Only optimize Python files in the top-level directory
            files_processed = 0
            files_changed = 0
            transformations = 0

            for file in os.listdir(path):
                file_path = os.path.join(path, file)
                if os.path.isfile(file_path) and file_path.endswith(".py"):
                    result = module.optimize_file(file_path)
                    _display_file_result(result)

                    files_processed += 1
                    if result["success"] and result["transformations"]:
                        files_changed += 1
                        transformations += len(result["transformations"])

            # Display summary
            table = Table(title="Summary")
            table.add_column("Metric", style="cyan")
            table.add_column("Value", style="green")

            table.add_row("Directory", path)
            table.add_row("Files processed", str(files_processed))
            table.add_row("Files changed", str(files_changed))
            table.add_row("Transformations", str(transformations))

            console.print(table)
    else:
        logging.error(f"Path not found: {path}")
        sys.exit(1)


@codeqa_cli.command(name="stats")
@click.option("--path", "-p", help="Path to the Python file or directory")
def stats_command(path: Optional[str]):
    """
    Display statistics for code quality checks.
    
    Args:
        path: Optional path to filter statistics by file or directory.
    """
    # Initialize module
    module = get_module()
    if not module.initialize():
        logging.error("Error initializing the Code Quality module")
        sys.exit(1)

    # Retrieve statistics from the Knowledge Graph using dependency injection
    if not dependency_injection.is_dependency_registered("knowledge_graph_module"):
        # Import here to avoid circular imports
        from llm_stack.modules.knowledge_graph.module import get_module as get_kg_module
        kg_module = get_kg_module()
    else:
        kg_module = dependency_injection.resolve_dependency("knowledge_graph_module")

    # Retrieve transformations
    transformations = kg_module.get_code_transformations(None, path, "code_quality")

    # Group by type
    transformation_types = {}
    for t in transformations:
        t_type = t.get("transformation_type", "unknown")
        if t_type not in transformation_types:
            transformation_types[t_type] = 0
        transformation_types[t_type] += 1

    # Create table
    table = Table(title="Code Quality Statistics")
    table.add_column("Transformation Type", style="cyan")
    table.add_column("Count", style="green")

    for t_type, count in transformation_types.items():
        table.add_row(t_type, str(count))

    # Add total count
    table.add_row("Total", str(len(transformations)))

    # Display table
    console.print(table)


def _display_file_result(result: dict):
    """
    Display the result of file optimization.

    Args:
        result: Result of the file optimization.
    """
    if not result["success"]:
        logging.error(
            f"Error with {result['file']}: {result.get('error', 'Unknown error')}"
        )
        return

    # Create table
    table = Table(title=f"Optimization Result: {result['file']}")
    table.add_column("Tool", style="cyan")
    table.add_column("Status", style="green")

    # Add rows for transformations
    has_transformations = False
    for t in result["transformations"]:
        has_transformations = True
        table.add_row(t["tool"], "Changed" if t["changed"] else "No Change")

    if not has_transformations:
        table.add_row("All Tools", "No Changes")

    # Add row for unused code
    if result.get("unused_code"):
        table.add_row(
            "Vulture", f"{len(result['unused_code'])} unused elements found"
        )
    else:
        table.add_row("Vulture", "No unused code found")

    # Display table
    console.print(table)

    # Display details about unused code
    if result.get("unused_code"):
        console.print("\nUnused Code:")
        for item in result["unused_code"]:
            console.print(f"  - {item}")


def _display_directory_result(result: dict):
    """
    Display the result of directory optimization.

    Args:
        result: Result of the directory optimization.
    """
    if not result["success"]:
        logging.error(
            f"Error with {result['directory']}: {result.get('error', 'Unknown error')}"
        )
        return

    # Create table
    table = Table(title=f"Optimization Result: {result['directory']}")
    table.add_column("Metric", style="cyan")
    table.add_column("Value", style="green")

    # Add rows
    table.add_row("Files processed", str(result["files_processed"]))
    table.add_row("Files changed", str(result["files_changed"]))
    table.add_row("Transformations", str(result["transformations"]))

    # Display table
    console.print(table)
