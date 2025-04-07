"""
Code Quality Module for the LLM Stack.

This module provides functions for optimizing Python code,
including syntax updates, import sorting, formatting, and detection of unused code.
"""

import os
import sys
from typing import Dict, List, Optional, Tuple, Union

from rich.console import Console

from llm_stack.core import dependency_injection, interfaces, logging
from llm_stack.core.command_utils import run_command, check_command_exists
from llm_stack.core.file_utils import read_file, write_file, ensure_file_exists
from llm_stack.knowledge_graph import client

# Console for formatted output
console = Console()


class CodeQualityModule(interfaces.ModuleInterface):
    """Module for code quality checking and optimization.
    
    Implements the ModuleInterface as defined in the specification manifest.
    """
def __init__(self, neo4j_client=None, kg_module=None):
    """
    Initializes the Code Quality Module.
    
    Args:
        neo4j_client: Neo4j client instance (optional, will be retrieved if not provided)
        kg_module: Knowledge Graph Module instance (optional, will be retrieved if not provided)
    """
    self.name = "code_quality"
    self.description = "Code quality checking and optimization for Python code"
    self.neo4j_client = neo4j_client
    self.kg_module = kg_module

    def initialize(self) -> bool:
        """
        Initialize the module.

        Returns:
            bool: True if the module was successfully initialized, False otherwise
        """
        logging.info("Initializing Code Quality Module...")

        # Retrieve Neo4j client if not provided
        if self.neo4j_client is None:
            self.neo4j_client = client.get_client()

        if not self.neo4j_client.ensure_connected():
            logging.warn(
                "No connection to Neo4j database. Transformations will not be recorded."
            )

        # Check if the required tools are installed
        if not self._check_tools():
            return False

        logging.success("Code Quality Module successfully initialized")
        return True
        
    def get_status(self) -> dict:
        """
        Get the module status.

        Returns:
            dict: Status of the module
        """
        logging.info("Checking status of Code Quality Module...")
        
        # Check if required tools are installed
        tools_status = self._check_tools()
        
        # Check connection status to Neo4j
        connection_status = False
        if self.neo4j_client:
            connection_status = self.neo4j_client.ensure_connected()
        
        return {
            "name": self.name,
            "description": self.description,
            "tools_installed": tools_status,
            "connection_status": "connected" if connection_status else "disconnected"
        }
    
    def start(self) -> bool:
        """
        Start the module.

        Returns:
            bool: True if the module was started successfully, False otherwise
        """
        logging.info("Starting Code Quality Module...")
        
        # The Code Quality Module doesn't require starting any services
        # It just needs to be initialized
        return self.initialize()
    
    def stop(self) -> bool:
        """
        Stop the module.

        Returns:
            bool: True if the module was stopped successfully, False otherwise
        """
        logging.info("Stopping Code Quality Module...")
        
        # Close Neo4j client if it exists
        if self.neo4j_client:
            self.neo4j_client.close()
            self.neo4j_client = None
            
        logging.success("Code Quality Module successfully stopped")
        return True
    
    def get_info(self) -> dict:
        """
        Get module information.
        
        Returns:
            dict: Information about the module
        """
        return {
            "name": self.name,
            "description": self.description,
            "version": "1.0.0",
            "capabilities": [
                "code_quality_checking",
                "python_syntax_upgrading",
                "import_sorting",
                "code_formatting",
                "unused_code_detection"
            ]
        }

    def _check_tools(self) -> bool:
        """
        Checks if the required tools are installed.

        Returns:
            bool: True if all tools are available, False otherwise
        """
        tools = ["pyupgrade", "isort", "black", "vulture"]
        missing_tools = []

        for tool in tools:
            if not check_command_exists(tool):
                missing_tools.append(tool)

        if missing_tools:
            logging.error(f"Missing tools: {', '.join(missing_tools)}")
            logging.info(
                "Install the missing tools with: pip install "
                + " ".join(missing_tools)
            )
            return False

        return True

    def optimize_file(self, file_path: str) -> Dict:
        """
        Optimizes a single Python file.

        Args:
            file_path: Path to the Python file

        Returns:
            Dict: Results of the optimization
        """
        if not file_path.endswith(".py"):
            logging.warn(f"Not a Python file: {file_path}")
            return {
                "file": file_path,
                "success": False,
                "error": "Not a Python file",
                "transformations": [],
            }

        # Use file_utils to read the file
        if not ensure_file_exists(file_path):
            return {
                "file": file_path,
                "success": False,
                "error": "File not found",
                "transformations": [],
            }
            
        success, before_content = read_file(file_path)
        if not success:
            return {
                "file": file_path,
                "success": False,
                "error": "Error reading file",
                "transformations": [],
            }

        transformations = []

        # Run pyupgrade
        pyupgrade_result = self._run_pyupgrade(file_path)
        if pyupgrade_result["changed"]:
            transformations.append(pyupgrade_result)

        # Run isort
        isort_result = self._run_isort(file_path)
        if isort_result["changed"]:
            transformations.append(isort_result)

        # Run black
        black_result = self._run_black(file_path)
        if black_result["changed"]:
            transformations.append(black_result)

        # Use file_utils to read the optimized file
        success, after_content = read_file(file_path)
        if not success:
            return {
                "file": file_path,
                "success": False,
                "error": "Error reading optimized file",
                "transformations": transformations,
            }

        # Record the complete transformation if the content has changed
        if before_content != after_content:
            self._record_transformation(
                file_path, "code_quality_all", before_content, after_content
            )

        # Run vulture (analysis only, no transformation)
        vulture_result = self._run_vulture(file_path)

        return {
            "file": file_path,
            "success": True,
            "transformations": transformations,
            "unused_code": vulture_result["unused_code"],
        }

    def optimize_directory(self, directory: str) -> Dict:
        """
        Optimizes all Python files in a directory.

        Args:
            directory: Path to the directory

        Returns:
            Dict: Results of the optimization
        """
        if not os.path.isdir(directory):
            logging.error(f"Directory not found: {directory}")
            return {
                "directory": directory,
                "success": False,
                "error": "Directory not found",
                "files_processed": 0,
                "files_changed": 0,
                "transformations": 0,
            }

        results = {
            "directory": directory,
            "success": True,
            "files_processed": 0,
            "files_changed": 0,
            "transformations": 0,
            "file_results": [],
        }

        for root, _, files in os.walk(directory):
            for file in files:
                if file.endswith(".py"):
                    file_path = os.path.join(root, file)
                    file_result = self.optimize_file(file_path)

                    results["files_processed"] += 1

                    if file_result["success"] and file_result["transformations"]:
                        results["files_changed"] += 1
                        results["transformations"] += len(
                            file_result["transformations"]
                        )

                    results["file_results"].append(file_result)

        return results

    def _run_pyupgrade(self, file_path: str) -> Dict:
        """
        Runs pyupgrade on a file.

        Args:
            file_path: Path to the Python file

        Returns:
            Dict: Result of the transformation
        """
        # Use file_utils to read the file
        success, before_content = read_file(file_path)
        if not success:
            return {"tool": "pyupgrade", "changed": False, "error": "Error reading file"}

        # Use command_utils to run the command
        returncode, stdout, stderr = run_command(
            ["pyupgrade", "--py38-plus", file_path]
        )

        # Use file_utils to read the transformed file
        success, after_content = read_file(file_path)
        if not success:
            return {"tool": "pyupgrade", "changed": False, "error": "Error reading transformed file"}

        # Check if the content has changed
        changed = before_content != after_content

        # Record the transformation if the content has changed
        if changed:
            self._record_transformation(
                file_path, "pyupgrade", before_content, after_content
            )

        return {
            "tool": "pyupgrade",
            "changed": changed,
            "returncode": returncode,
            "stdout": stdout,
            "stderr": stderr,
        }

    def _run_isort(self, file_path: str) -> Dict:
        """
        Runs isort on a file.

        Args:
            file_path: Path to the Python file

        Returns:
            Dict: Result of the transformation
        """
        # Use file_utils to read the file
        success, before_content = read_file(file_path)
        if not success:
            return {"tool": "isort", "changed": False, "error": "Error reading file"}

        # Use command_utils to run the command
        returncode, stdout, stderr = run_command(
            ["isort", file_path]
        )

        # Use file_utils to read the transformed file
        success, after_content = read_file(file_path)
        if not success:
            return {"tool": "isort", "changed": False, "error": "Error reading transformed file"}

        # Check if the content has changed
        changed = before_content != after_content

        # Record the transformation if the content has changed
        if changed:
            self._record_transformation(
                file_path, "isort", before_content, after_content
            )

        return {
            "tool": "isort",
            "changed": changed,
            "returncode": returncode,
            "stdout": stdout,
            "stderr": stderr,
        }

    def _run_black(self, file_path: str) -> Dict:
        """
        Runs black on a file.

        Args:
            file_path: Path to the Python file

        Returns:
            Dict: Result of the transformation
        """
        # Use file_utils to read the file
        success, before_content = read_file(file_path)
        if not success:
            return {"tool": "black", "changed": False, "error": "Error reading file"}

        # Use command_utils to run the command
        returncode, stdout, stderr = run_command(
            ["black", file_path]
        )

        # Use file_utils to read the transformed file
        success, after_content = read_file(file_path)
        if not success:
            return {"tool": "black", "changed": False, "error": "Error reading transformed file"}

        # Check if the content has changed
        changed = before_content != after_content

        # Record the transformation if the content has changed
        if changed:
            self._record_transformation(
                file_path, "black", before_content, after_content
            )

        return {
            "tool": "black",
            "changed": changed,
            "returncode": returncode,
            "stdout": stdout,
            "stderr": stderr,
        }

    def _run_vulture(self, file_path: str) -> Dict:
        """
        Runs vulture on a file to find unused code.

        Args:
            file_path: Path to the Python file

        Returns:
            Dict: Result of the analysis
        """
        # Use command_utils to run the command
        returncode, stdout, stderr = run_command(
            ["vulture", file_path]
        )

        # Extract unused code from the output
        unused_code = []
        if stdout:
            for line in stdout.splitlines():
                if ":" in line and "unused" in line:
                    unused_code.append(line.strip())

        return {
            "tool": "vulture",
            "returncode": returncode,
            "stdout": stdout,
            "stderr": stderr,
            "unused_code": unused_code,
        }

    def _record_transformation(
        self, file_path: str, transformation_type: str, before: str, after: str
    ) -> None:
        """
        Records a code transformation in the Knowledge Graph.

        Args:
            file_path: Path to the Python file
            transformation_type: Type of transformation
            before: Code before the transformation
            after: Code after the transformation
        """
        if not self.neo4j_client or not self.neo4j_client.ensure_connected():
            logging.debug(
                "No connection to Neo4j database. Transformation will not be recorded."
            )
            return

        # Get the Knowledge Graph Module if not provided
        if self.kg_module is None:
            # Import here to avoid circular imports
            from llm_stack.modules.knowledge_graph.module import get_module
            self.kg_module = get_module()

        try:
            self.kg_module.record_code_transformation(
                f"code_quality_{transformation_type}", before, after, None, file_path
            )
            logging.debug(
                f"Transformation {transformation_type} for {file_path} successfully recorded"
            )
        except Exception as e:
            logging.error(f"Error recording transformation: {str(e)}")


def get_module() -> CodeQualityModule:
    """
    Gets the singleton instance of the Code Quality Module.
    
    This function uses the dependency injection framework to retrieve or create
    the CodeQualityModule instance. If the module is not registered in the
    dependency container, it will be registered as a singleton.

    Returns:
        CodeQualityModule: Code Quality Module instance
    """
    # Check if the module is registered in the dependency container
    if not dependency_injection.is_dependency_registered("code_quality_module"):
        # Register the module factory
        dependency_injection.register_dependency(
            "code_quality_module",
            lambda: CodeQualityModule(),
            singleton=True
        )
    
    # Resolve and return the module
    return dependency_injection.resolve_dependency("code_quality_module")


# Initialize module
logging.debug("Code Quality Module initialized")
