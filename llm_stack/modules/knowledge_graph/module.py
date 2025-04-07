"""
Knowledge Graph Module for the LLM Stack.

This module provides functions for integrating the neo4j Knowledge Graph,
which serves as a central knowledge base for autonomous AI Coding Agents.
It implements a ModuleInterface for managing the neo4j database container,
establishing connections, and providing methods for recording and retrieving
migration decisions, code transformations, and file information.
"""

import os
import sys
from typing import Any, Dict, List, Optional, Tuple, Union

import click
from rich.console import Console
from rich.table import Table

from llm_stack.core import config, dependency_injection, docker, error, interfaces, logging, system
from llm_stack.knowledge_graph import client, migration, models, schema

# Console for formatted output
console = Console()


class KnowledgeGraphModule(interfaces.ModuleInterface):
    """Module for the integration of the neo4j Knowledge Graph.
    
    Implements the ModuleInterface as defined in the specification manifest.
    This class provides methods for starting, stopping, and managing the
    neo4j Knowledge Graph, as well as recording and retrieving information
    about code migrations, transformations, and file relationships.
    """

    def __init__(self) -> None:
        """Initialize the Knowledge Graph Module.
        
        Sets up the initial state of the module with default values for name,
        description, and initializes client and schema manager references to None.
        These will be properly initialized when the module is started.
        """
        self.name = "knowledge_graph"
        self.description = "Knowledge Graph Integration for autonomous AI Coding Agents"
        self.neo4j_client = None
        self.schema_manager = None

    def start(self) -> bool:
        """Start the Knowledge Graph Module.
        
        Initializes and starts the neo4j container, establishes a connection to the
        database, initializes the schema manager, and imports existing schema and
        graph data if available.

        Returns:
            bool: True if the module was started successfully, False otherwise
        
        Raises:
            docker.DockerError: If there's an error starting the neo4j container
            client.ConnectionError: If there's an error connecting to the database
        """
        logging.info("Starting Knowledge Graph Module...")

        # Start Docker Compose file for neo4j
        if not docker.compose_up(
            f"{config.CORE_PROJECT}-{self.name}", f"-f docker/modules/neo4j.yml", ""
        ):
            logging.error("Error starting the neo4j container")
            return False

        # Wait until neo4j is ready
        if not docker.wait_for_container_health("neo4j", "healthy", 60):
            logging.warn(
                "Timeout while waiting for neo4j. Trying to continue anyway..."
            )

        # Initialize Neo4j client
        uri = f"bolt://localhost:{config.get_config('HOST_PORT_NEO4J_BOLT', '7687')}"
        username = config.get_config("NEO4J_USERNAME", "neo4j")
        password = config.get_config("NEO4J_PASSWORD", "password")
        database = config.get_config("NEO4J_DATABASE", "neo4j")

        self.neo4j_client = client.init_client(uri, username, password, database)

        if not self.neo4j_client.connect():
            logging.error("Error connecting to the neo4j database")
            return False

        # Initialize Schema Manager
        self.schema_manager = schema.SchemaManager(self.neo4j_client)

        # Create schema
        if not self.schema_manager.create_schema():
            logging.error("Error creating the schema")
            return False

        # Import existing schema and graph if available
        schema_file = os.path.join(
            system.get_project_root(), "docs/knowledge-graph/schema.json"
        )
        graph_file = os.path.join(
            system.get_project_root(), "docs/knowledge-graph/graph.json"
        )

        if os.path.isfile(schema_file):
            if not schema.import_json_ld_schema(schema_file, self.neo4j_client):
                logging.warn(f"Error importing schema from {schema_file}")

        if os.path.isfile(graph_file):
            if not schema.import_json_ld_graph(graph_file, self.neo4j_client):
                logging.warn(f"Error importing graph from {graph_file}")

        logging.success("Knowledge Graph Module successfully started")
        return True

    def stop(self) -> bool:
        """Stop the Knowledge Graph Module.
        
        Closes the connection to the neo4j database and stops the neo4j container.

        Returns:
            bool: True if the module was stopped successfully, False otherwise
        
        Raises:
            docker.DockerError: If there's an error stopping the neo4j container
        """
        logging.info("Stopping Knowledge Graph Module...")

        # Close Neo4j client
        if self.neo4j_client:
            self.neo4j_client.close()
            self.neo4j_client = None

        # Stop Docker Compose file for neo4j
        if not docker.compose_down(
            f"{config.CORE_PROJECT}-{self.name}", f"-f docker/modules/neo4j.yml", ""
        ):
            logging.error("Error stopping the neo4j container")
            return False

        logging.success("Knowledge Graph Module successfully stopped")
        return True

    def initialize(self) -> bool:
        """Initialize the module.
        
        This method is part of the ModuleInterface and is called during system startup.
        Since the module is already initialized in __init__, this method simply logs
        the initialization and returns True.
        
        Returns:
            bool: True if the module was initialized successfully, False otherwise
        """
        logging.info("Initializing Knowledge Graph Module...")
        
        # Module is already initialized in __init__, so just return True
        return True
        
    def get_status(self) -> Dict[str, Union[str, Dict]]:
        """Get the status of the Knowledge Graph Module.

        Checks the current status of the neo4j container and database connection.
        If connected, also retrieves migration statistics.

        Returns:
            Dict[str, Union[str, Dict]]: Status information including:
                - name: Module name
                - description: Module description
                - container_status: Status of the neo4j container
                - connection_status: Status of the database connection
                - migration_stats: Statistics about migrations if connected
        """
        logging.info("Checking status of Knowledge Graph Module...")

        # Get container status
        container_status = docker.get_container_status("neo4j")

        # Check connection status
        connection_status = False
        if self.neo4j_client:
            connection_status = self.neo4j_client.ensure_connected()
        else:
            # Create temporary client
            uri = (
                f"bolt://localhost:{config.get_config('HOST_PORT_NEO4J_BOLT', '7687')}"
            )
            username = config.get_config("NEO4J_USERNAME", "neo4j")
            password = config.get_config("NEO4J_PASSWORD", "password")
            database = config.get_config("NEO4J_DATABASE", "neo4j")

            temp_client = client.Neo4jClient(uri, username, password, database)
            connection_status = temp_client.connect()
            temp_client.close()

        # Get migration statistics
        migration_stats = {}
        if connection_status:
            migration_stats = migration.get_migration_statistics()

        return {
            "name": self.name,
            "description": self.description,
            "container_status": (
                container_status["status"] if container_status else "not_running"
            ),
            "connection_status": "connected" if connection_status else "disconnected",
            "migration_stats": migration_stats,
        }
        
    def get_info(self) -> Dict[str, Union[str, List[str]]]:
        """Get module information.
        
        Provides metadata about the module including its name, description,
        version, and capabilities.
        
        Returns:
            Dict[str, Union[str, List[str]]]: Information about the module including:
                - name: Module name
                - description: Module description
                - version: Module version
                - capabilities: List of module capabilities
        """
        return {
            "name": self.name,
            "description": self.description,
            "version": "1.0.0",
            "capabilities": [
                "knowledge_graph_integration",
                "migration_tracking",
                "code_transformation_recording"
            ]
        }

    def record_migration_decision(
        self,
        decision: str,
        rationale: str,
        bash_file_path: Optional[str] = None,
        python_file_path: Optional[str] = None,
        alternatives: Optional[List[str]] = None,
        impact: Optional[str] = None,
    ) -> Optional[Dict[str, Any]]:
        """Record a migration decision in the Knowledge Graph.

        Creates a new decision node in the knowledge graph that captures information
        about a migration decision, including the decision itself, rationale,
        related files, alternatives considered, and potential impact.

        Args:
            decision: The decision made during migration
            rationale: Justification for the decision
            bash_file_path: Path to the Bash file the decision relates to
            python_file_path: Path to the Python file the decision relates to
            alternatives: Alternative decisions that were considered
            impact: Impact of the decision on the system

        Returns:
            Optional[Dict[str, Any]]: Created decision node or None if an error occurred

        Raises:
            ConnectionError: If there's no connection to the neo4j database
        """
        if not self.neo4j_client or not self.neo4j_client.ensure_connected():
            logging.error("No connection to the neo4j database")
            return None

        return migration.record_migration_decision(
            decision,
            rationale,
            bash_file_path,
            python_file_path,
            alternatives,
            impact,
            self.neo4j_client,
        )

    def record_code_transformation(
        self,
        transformation_type: str,
        before: str,
        after: str,
        bash_file_path: Optional[str] = None,
        python_file_path: Optional[str] = None,
        decision_id: Optional[str] = None,
    ) -> Optional[Dict[str, Any]]:
        """Record a code transformation in the Knowledge Graph.

        Creates a new transformation node in the knowledge graph that captures
        information about a code change, including the type of transformation,
        the code before and after the change, related files, and an optional
        link to a decision that prompted this transformation.

        Args:
            transformation_type: Type of transformation (e.g., "function_migration",
                "syntax_change")
            before: Code before the transformation
            after: Code after the transformation
            bash_file_path: Path to the Bash file the transformation relates to
            python_file_path: Path to the Python file the transformation relates to
            decision_id: ID of the associated migration decision

        Returns:
            Optional[Dict[str, Any]]: Created transformation node or None if an error occurred

        Raises:
            ConnectionError: If there's no connection to the neo4j database
        """
        if not self.neo4j_client or not self.neo4j_client.ensure_connected():
            logging.error("No connection to the neo4j database")
            return None

        return migration.record_code_transformation(
            transformation_type,
            before,
            after,
            bash_file_path,
            python_file_path,
            decision_id,
            self.neo4j_client,
        )

    def record_bash_file(self, file_path: str, content: str) -> Optional[Dict[str, Any]]:
        """Record a Bash file in the Knowledge Graph.

        Creates a new file node in the knowledge graph that represents a Bash file,
        including its path and content. This allows tracking of Bash files that
        are part of the migration process.

        Args:
            file_path: Path to the Bash file
            content: Content of the Bash file

        Returns:
            Optional[Dict[str, Any]]: Created file node or None if an error occurred

        Raises:
            ConnectionError: If there's no connection to the neo4j database
        """
        if not self.neo4j_client or not self.neo4j_client.ensure_connected():
            logging.error("No connection to the neo4j database")
            return None

        return migration.record_bash_file(file_path, content, self.neo4j_client)

    def record_python_file(
        self, file_path: str, content: str, bash_file_path: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """Record a Python file in the Knowledge Graph.

        Creates a new file node in the knowledge graph that represents a Python file,
        including its path, content, and optional relationship to a corresponding
        Bash file. This allows tracking of Python files that are part of the
        migration process and their relationships to original Bash files.

        Args:
            file_path: Path to the Python file
            content: Content of the Python file
            bash_file_path: Path to the corresponding Bash file that was migrated

        Returns:
            Optional[Dict[str, Any]]: Created file node or None if an error occurred

        Raises:
            ConnectionError: If there's no connection to the neo4j database
        """
        if not self.neo4j_client or not self.neo4j_client.ensure_connected():
            logging.error("No connection to the neo4j database")
            return None

        return migration.record_python_file(
            file_path, content, bash_file_path, self.neo4j_client
        )

    def get_migration_decisions(
        self,
        bash_file_path: Optional[str] = None,
        python_file_path: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """Get migration decisions from the Knowledge Graph.

        Retrieves migration decisions from the knowledge graph, optionally filtered
        by related Bash or Python file paths. This allows querying for decisions
        that were made during the migration process.

        Args:
            bash_file_path: Path to the Bash file for which decisions should be retrieved
            python_file_path: Path to the Python file for which decisions should be retrieved

        Returns:
            List[Dict[str, Any]]: List of migration decisions, each containing details
                about the decision, rationale, and related information

        Raises:
            ConnectionError: If there's no connection to the neo4j database
        """
        if not self.neo4j_client or not self.neo4j_client.ensure_connected():
            logging.error("No connection to the neo4j database")
            return []

        return migration.get_migration_decisions(
            bash_file_path, python_file_path, self.neo4j_client
        )

    def get_code_transformations(
        self,
        bash_file_path: Optional[str] = None,
        python_file_path: Optional[str] = None,
        transformation_type: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """Get code transformations from the Knowledge Graph.

        Retrieves code transformations from the knowledge graph, optionally filtered
        by related Bash or Python file paths and transformation type. This allows
        querying for specific types of code changes that occurred during migration.

        Args:
            bash_file_path: Path to the Bash file for which transformations should be retrieved
            python_file_path: Path to the Python file for which transformations should be retrieved
            transformation_type: Type of transformation to filter by (e.g., "function_migration")

        Returns:
            List[Dict[str, Any]]: List of code transformations, each containing details
                about the transformation type, before/after code, and related information

        Raises:
            ConnectionError: If there's no connection to the neo4j database
        """
        if not self.neo4j_client or not self.neo4j_client.ensure_connected():
            logging.error("No connection to the neo4j database")
            return []

        return migration.get_code_transformations(
            bash_file_path, python_file_path, transformation_type, self.neo4j_client
        )

    def get_file_migration_status(self, bash_file_path: str) -> Dict[str, Any]:
        """Get the migration status of a file from the Knowledge Graph.

        Retrieves comprehensive information about the migration status of a Bash file,
        including whether it has been migrated to Python, associated decisions,
        and transformations.

        Args:
            bash_file_path: Path to the Bash file to check migration status for

        Returns:
            Dict[str, Any]: Migration status information including:
                - bash_file: Original Bash file path
                - python_file: Corresponding Python file path (if migrated)
                - migrated: Boolean indicating if migration is complete
                - decisions: List of migration decisions related to this file
                - transformations: List of code transformations related to this file

        Raises:
            ConnectionError: If there's no connection to the neo4j database
        """
        if not self.neo4j_client or not self.neo4j_client.ensure_connected():
            logging.error("No connection to the neo4j database")
            return {
                "bash_file": bash_file_path,
                "python_file": None,
                "migrated": False,
                "decisions": [],
                "transformations": [],
            }

        return migration.get_file_migration_status(bash_file_path, self.neo4j_client)

    def get_migration_statistics(self) -> Dict[str, Union[int, float]]:
        """Get migration statistics from the Knowledge Graph.

        Retrieves aggregate statistics about the migration process, including
        counts of files, decisions, transformations, and overall progress.

        Returns:
            Dict[str, Union[int, float]]: Migration statistics including:
                - total_bash_files: Total number of Bash files in the system
                - total_python_files: Total number of Python files in the system
                - migrated_files: Number of successfully migrated files
                - migration_progress: Percentage of migration completion
                - total_decisions: Total number of migration decisions recorded
                - total_transformations: Total number of code transformations recorded

        Raises:
            ConnectionError: If there's no connection to the neo4j database
        """
        if not self.neo4j_client or not self.neo4j_client.ensure_connected():
            logging.error("No connection to the neo4j database")
            return {
                "total_bash_files": 0,
                "total_python_files": 0,
                "migrated_files": 0,
                "migration_progress": 0.0,
                "total_decisions": 0,
                "total_transformations": 0,
            }

        return migration.get_migration_statistics(self.neo4j_client)

    def show_migration_statistics(self) -> None:
        """Display migration statistics in a formatted table.
        
        Retrieves migration statistics and presents them in a rich formatted table
        for better readability in the console. This is a convenience method for
        displaying the information returned by get_migration_statistics().
        
        Returns:
            None
        """
        stats = self.get_migration_statistics()

        # Create table
        table = Table(title="Migration Statistics")
        table.add_column("Metric", style="cyan")
        table.add_column("Value", style="green")

        # Add rows
        table.add_row("Total Bash Files", str(stats["total_bash_files"]))
        table.add_row("Total Python Files", str(stats["total_python_files"]))
        table.add_row("Migrated Files", str(stats["migrated_files"]))
        table.add_row("Migration Progress", f"{stats['migration_progress']:.2f}%")
        table.add_row("Total Decisions", str(stats["total_decisions"]))
        table.add_row("Total Transformations", str(stats["total_transformations"]))

        # Display table
        console.print(table)


def get_module() -> KnowledgeGraphModule:
    """Get the singleton instance of the Knowledge Graph Module.
    
    This function uses the dependency injection framework to retrieve or create
    the KnowledgeGraphModule instance. If the module is not registered in the
    dependency container, it will be registered as a singleton.

    Returns:
        KnowledgeGraphModule: The singleton Knowledge Graph Module instance
    """
    # Check if the module is registered in the dependency container
    if not dependency_injection.is_dependency_registered("knowledge_graph_module"):
        # Register the module factory
        dependency_injection.register_dependency(
            "knowledge_graph_module",
            lambda: KnowledgeGraphModule(),
            singleton=True
        )
    
    # Resolve and return the module
    return dependency_injection.resolve_dependency("knowledge_graph_module")


# CLI commands for the Knowledge Graph Module
@click.group(name="kg")
def kg_cli() -> None:
    """Knowledge Graph commands.
    
    This command group provides CLI access to Knowledge Graph functionality,
    including status checking, statistics, and data recording operations.
    """
    pass


@kg_cli.command(name="status")
def status_command() -> None:
    """Display the status of the Knowledge Graph Module.
    
    Shows the current status of the Knowledge Graph module, including container
    status, connection status, and migration statistics if connected.
    """
    module = get_module()
    status = module.get_status()

    # Create table
    table = Table(title="Knowledge Graph Status")
    table.add_column("Property", style="cyan")
    table.add_column("Value", style="green")

    # Add rows
    table.add_row("Name", status["name"])
    table.add_row("Description", status["description"])
    table.add_row("Container Status", status["container_status"])
    table.add_row("Connection Status", status["connection_status"])

    # Display table
    console.print(table)

    # Display migration statistics if connected
    if status["connection_status"] == "connected":
        module.show_migration_statistics()


@kg_cli.command(name="stats")
def stats_command() -> None:
    """Display migration statistics.
    
    Retrieves and displays migration statistics in a formatted table,
    showing counts of files, decisions, transformations, and overall progress.
    """
    module = get_module()
    module.show_migration_statistics()


@kg_cli.command(name="record-decision")
@click.option("--decision", required=True, help="The decision made")
@click.option("--rationale", required=True, help="Justification for the decision")
@click.option("--bash-file", help="Path to the Bash file")
@click.option("--python-file", help="Path to the Python file")
@click.option("--alternatives", help="Alternative decisions (comma-separated)")
@click.option("--impact", help="Impact of the decision")
def record_decision_command(
    decision: str,
    rationale: str,
    bash_file: Optional[str],
    python_file: Optional[str],
    alternatives: Optional[str],
    impact: Optional[str]
) -> None:
    """Record a migration decision.
    
    Creates a new decision node in the knowledge graph with the provided information.
    
    Args:
        decision: The decision made during migration
        rationale: Justification for the decision
        bash_file: Path to the Bash file the decision relates to
        python_file: Path to the Python file the decision relates to
        alternatives: Alternative decisions that were considered (comma-separated)
        impact: Impact of the decision on the system
    """
    module = get_module()

    # Convert alternatives to list
    alt_list = None
    if alternatives:
        alt_list = [alt.strip() for alt in alternatives.split(",")]

    result = module.record_migration_decision(
        decision, rationale, bash_file, python_file, alt_list, impact
    )

    if result:
        logging.success("Migration decision successfully recorded")
    else:
        logging.error("Error recording the migration decision")


@kg_cli.command(name="record-transformation")
@click.option(
    "--type", "transformation_type", required=True, help="Type of transformation"
)
@click.option("--before", required=True, help="Code before the transformation")
@click.option("--after", required=True, help="Code after the transformation")
@click.option("--bash-file", help="Path to the Bash file")
@click.option("--python-file", help="Path to the Python file")
@click.option("--decision-id", help="ID of the associated migration decision")
def record_transformation_command(
    transformation_type, before, after, bash_file, python_file, decision_id
):
    """Record a code transformation."""
    module = get_module()

    result = module.record_code_transformation(
        transformation_type, before, after, bash_file, python_file, decision_id
    )

    if result:
        logging.success("Code transformation successfully recorded")
    else:
        logging.error("Error recording the code transformation")


@kg_cli.command(name="record-bash-file")
@click.option("--file-path", required=True, help="Path to the Bash file")
@click.option("--content-file", help="Path to the file with the content")
@click.option("--content", help="Content of the Bash file")
def record_bash_file_command(file_path, content_file, content):
    """Record a Bash file."""
    module = get_module()

    # Load content from file or parameter
    if content_file:
        with open(content_file) as f:
            content = f.read()
    elif not content:
        logging.error("Either --content or --content-file must be specified")
        return

    result = module.record_bash_file(file_path, content)

    if result:
        logging.success(f"Bash file {file_path} successfully recorded")
    else:
        logging.error(f"Error recording the Bash file {file_path}")


@kg_cli.command(name="record-python-file")
@click.option("--file-path", required=True, help="Path to the Python file")
@click.option("--content-file", help="Path to the file with the content")
@click.option("--content", help="Content of the Python file")
@click.option("--bash-file", help="Path to the corresponding Bash file")
def record_python_file_command(file_path, content_file, content, bash_file):
    """Record a Python file."""
    module = get_module()

    # Load content from file or parameter
    if content_file:
        with open(content_file) as f:
            content = f.read()
    elif not content:
        logging.error("Either --content or --content-file must be specified")
        return

    result = module.record_python_file(file_path, content, bash_file)

    if result:
        logging.success(f"Python file {file_path} successfully recorded")
    else:
        logging.error(f"Error recording the Python file {file_path}")


@kg_cli.command(name="get-decisions")
@click.option("--bash-file", help="Path to the Bash file")
@click.option("--python-file", help="Path to the Python file")
def get_decisions_command(bash_file, python_file):
    """Get migration decisions."""
    module = get_module()

    decisions = module.get_migration_decisions(bash_file, python_file)

    if not decisions:
        logging.info("No migration decisions found")
        return

    # Create table
    table = Table(title="Migration Decisions")
    table.add_column("ID", style="cyan")
    table.add_column("Decision", style="green")
    table.add_column("Rationale", style="yellow")

    # Add rows
    for decision in decisions:
        table.add_row(
            decision.get("id", ""),
            decision.get("decision", ""),
            decision.get("rationale", ""),
        )

    # Display table
    console.print(table)


@kg_cli.command(name="get-transformations")
@click.option("--bash-file", help="Path to the Bash file")
@click.option("--python-file", help="Path to the Python file")
@click.option("--type", "transformation_type", help="Type of transformation")
def get_transformations_command(bash_file, python_file, transformation_type):
    """Get code transformations."""
    module = get_module()

    transformations = module.get_code_transformations(
        bash_file, python_file, transformation_type
    )

    if not transformations:
        logging.info("No code transformations found")
        return

    # Create table
    table = Table(title="Code Transformations")
    table.add_column("ID", style="cyan")
    table.add_column("Type", style="green")
    table.add_column("Before", style="yellow")
    table.add_column("After", style="blue")

    # Add rows
    for transformation in transformations:
        # Shortened versions for the table
        before = transformation.get("before", "")
        after = transformation.get("after", "")

        if len(before) > 50:
            before = before[:47] + "..."

        if len(after) > 50:
            after = after[:47] + "..."

        table.add_row(
            transformation.get("id", ""),
            transformation.get("transformation_type", ""),
            before,
            after,
        )

    # Display table
    console.print(table)


@kg_cli.command(name="update-code-graph")
@click.option("--path", "-p", default=".", help="Path to the codebase to scan")
@click.option("--verbose", "-v", is_flag=True, help="Enable verbose output")
def update_code_graph_command(path, verbose):
    """Update the knowledge graph with code structure from Python files."""
    from llm_stack.tools.knowledge_graph import update_code_graph

    # Set verbose logging if requested
    if verbose:
        logging.set_verbose(True)

    # Get absolute path if relative path is provided
    if not os.path.isabs(path):
        path = os.path.join(system.get_project_root(), path)

    logging.info(f"Updating code graph from {path}...")

    # Update code graph
    if update_code_graph.update_code_graph(path):
        logging.success("Code graph updated successfully")
    else:
        logging.error("Failed to update code graph")
        sys.exit(1)


@kg_cli.command(name="get-file-status")
@click.option("--bash-file", required=True, help="Path to the Bash file")
def get_file_status_command(bash_file):
    """Get the migration status of a file."""
    module = get_module()

    status = module.get_file_migration_status(bash_file)

    # Create table
    table = Table(title=f"Migration Status: {bash_file}")
    table.add_column("Property", style="cyan")
    table.add_column("Value", style="green")

    # Add rows
    table.add_row("Bash File", status["bash_file"])
    table.add_row("Python File", status["python_file"] or "Not migrated")
    table.add_row("Migrated", "Yes" if status["migrated"] else "No")
    table.add_row("Decisions", str(len(status["decisions"])))
    table.add_row("Transformations", str(len(status["transformations"])))

    # Display table
    console.print(table)


# Initialize module
logging.debug("Knowledge Graph Module initialized")
