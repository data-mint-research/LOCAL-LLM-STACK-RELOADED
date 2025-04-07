"""
Common functions for the LLM Stack CLI.

This module provides common functions for the LLM Stack CLI
that are used by various commands.
"""

import os
import sys
from typing import Dict, List, Optional, Tuple, Union

import click
from rich.console import Console
from rich.table import Table

from llm_stack.core import config, docker, error, logging, system
from llm_stack.knowledge_graph import client as kg_client
from llm_stack.modules.knowledge_graph.module import get_module as get_kg_module

# Console for formatted output
CONSOLE = Console()

# Knowledge Graph module
KG_MODULE = None
try:
    KG_MODULE = get_kg_module()
except ImportError:
    logging.debug("Knowledge Graph module not available")


# Start command implementation with improved user feedback
def start_command(
    component: Optional[str] = None, module: Optional[str] = None
) -> bool:
    """
    Implements the start command.

    Args:
        component: Name of the component to start
        module: Name of the module to start

    Returns:
        bool: True if the command was executed successfully, False otherwise
    """
    if component is None and module is None:
        logging.info("Starting all components...")
        # Check if secrets are generated
        config.check_secrets()
        if not docker.compose_up(config.CORE_PROJECT, config.CORE_COMPOSE, ""):
            return False
        logging.success("Core components successfully started.")
        logging.info(
            "Tip: Use 'llm status' to check component status"
        )
        return True
    elif module is not None:
        if not os.path.isdir(f"modules/{module}"):
            logging.error(f"Module not found: {module}")
            return False

        logging.info(f"Starting core components with {module} module...")
        if not docker.compose_up(config.CORE_PROJECT, config.CORE_COMPOSE, ""):
            return False
        if not docker.compose_up(
            f"{config.CORE_PROJECT}-{module}",
            f"-f modules/{module}/docker-compose.yml",
            "",
        ):
            return False
        logging.success(f"Core components and {module} module successfully started.")
        logging.info(
            "Tip: Use 'llm status' to check component status"
        )
        return True
    else:
        logging.info(f"Starting {component} component...")
        if not docker.compose_up(
            f"{config.CORE_PROJECT}-{component}", f"-f core/{component}.yml", ""
        ):
            return False
        logging.success(f"{component} component successfully started.")
        return True


# Stop command implementation with improved user feedback
def stop_command(component: Optional[str] = None, module: Optional[str] = None) -> bool:
    """
    Implements the stop command.

    Args:
        component: Name of the component to stop
        module: Name of the module to stop

    Returns:
        bool: True if the command was executed successfully, False otherwise
    """
    if component is None and module is None:
        logging.info("Stopping all components...")
        if not docker.compose_down(config.CORE_PROJECT, config.CORE_COMPOSE, ""):
            return False
        logging.success("All components successfully stopped.")
        return True
    elif module is not None:
        if not os.path.isdir(f"modules/{module}"):
            logging.error(f"Module not found: {module}")
            return False

        logging.info(f"Stopping core components and {module} module...")
        if not docker.compose_down(
            f"{config.CORE_PROJECT}-{module}",
            f"-f modules/{module}/docker-compose.yml",
            "",
        ):
            return False
        if not docker.compose_down(config.CORE_PROJECT, config.CORE_COMPOSE, ""):
            return False
        logging.success(f"Core components and {module} module successfully stopped.")
        return True
    else:
        logging.info(f"Stopping {component} component...")
        if not docker.compose_down(
            f"{config.CORE_PROJECT}-{component}", f"-f core/{component}.yml", ""
        ):
            return False
        logging.success(f"{component} component successfully stopped.")
        return True


# Debug command implementation with improved user guidance
def debug_command(component: Optional[str] = None) -> bool:
    """
    Implements the debug command.

    Args:
        component: Name of the component to debug

    Returns:
        bool: True if the command was executed successfully, False otherwise
    """
    if component is None:
        logging.info("Starting all components in debug mode...")
        # Check if secrets are generated
        config.check_secrets()
        if not docker.compose_up(config.DEBUG_PROJECT, config.DEBUG_COMPOSE, ""):
            return False
        logging.success("Core components started in debug mode.")
        logging.info("LibreChat Node.js debugger is available at localhost:9229")
        logging.info(
            "Tip: Use VSCode's 'Attach to LibreChat' debug configuration to connect"
        )
        return True
    elif component == "librechat":
        logging.info("Starting LibreChat in debug mode...")
        if not docker.compose_up(
            config.DEBUG_PROJECT, config.DEBUG_COMPOSE, "librechat"
        ):
            return False
        logging.success("LibreChat started in debug mode.")
        logging.info("Node.js debugger is available at localhost:9229")
        logging.info(
            "Tip: Use VSCode's 'Attach to LibreChat' debug configuration to connect"
        )
        return True
    else:
        logging.error("Debug mode is currently only supported for LibreChat.")
        logging.info("Usage: llm debug [librechat]")
        return False


# Status command implementation with improved formatting
def status_command() -> bool:
    """
    Implements the status command.

    Returns:
        bool: True if the command was executed successfully, False otherwise
    """
    logging.info("Checking status of all components...")

    # Get container status with better formatting
    docker.show_container_status()

    # Display helpful tips
    # Get port values with fallbacks
    librechat_port = config.get_config("HOST_PORT_LIBRECHAT", "3080")
    ollama_port = config.get_config("HOST_PORT_OLLAMA", "11434")

    CONSOLE.print()
    logging.info(f"Tip: Access LibreChat at http://localhost:{librechat_port}")
    logging.info(f"Tip: Ollama API is available at http://localhost:{ollama_port}")

    return True


# Models command implementation with improved user guidance
def models_command(action: str, model: Optional[str] = None) -> bool:
    """
    Implements the models command.

    Args:
        action: Action to perform (list, add, remove)
        model: Name of the model

    Returns:
        bool: True if the command was executed successfully, False otherwise
    """
    from llm_stack.core import models as models_module

    # Get Ollama port with fallback
    ollama_port = config.get_config("HOST_PORT_OLLAMA", "11434")
    ollama_url = f"http://localhost:{ollama_port}"

    # Check if Ollama is running
    if not models_module.check_ollama_running(ollama_url):
        logging.error("Ollama service is not running.")
        logging.info("Tip: Start Ollama first with 'llm start ollama'")
        return False

    if action == "list":
        models_module.list_models(ollama_url)
        return True
    elif action == "add":
        if model is None:
            logging.error("Model name is required for the 'add' action")
            return False
        return models_module.add_model(ollama_url, model)
    elif action == "remove":
        if model is None:
            logging.error("Model name is required for the 'remove' action")
            return False
        return models_module.remove_model(ollama_url, model)
    else:
        logging.info("Usage: llm models [list|add|remove] [model_name]")
        CONSOLE.print()
        CONSOLE.print("Examples:")
        CONSOLE.print("  llm models list           List all available models")
        CONSOLE.print("  llm models add llama3     Add the Llama 3 model")
        CONSOLE.print("  llm models remove mistral Remove the Mistral model")
        return False


# Config command implementation with improved user guidance
def config_command(action: str) -> bool:
    """
    Implements the config command.

    Args:
        action: Action to perform (show, edit)

    Returns:
        bool: True if the command was executed successfully, False otherwise
    """
    if action == "show":
        logging.info("Showing configuration...")
        config.show_config()

        # Display helpful tips
        CONSOLE.print()
        logging.info("Tip: Edit the configuration with 'llm config edit'")
        return True
    elif action == "edit":
        logging.info("Creating backup of configuration...")
        backup_file = config.backup_config_file()
        if backup_file is None:
            logging.error("Error creating backup of configuration file")
            return False

        logging.info("Editing configuration...")
        config.edit_config()

        logging.warn(
            "Note: If you made a mistake, you can restore from backup:"
        )
        logging.warn(f"cp {backup_file} {config.ENV_FILE}")
        return True
    else:
        logging.info("Usage: llm config [show|edit]")
        console.print()
        console.print("Examples:")
        console.print("  llm config show    Show current configuration")
        console.print(
            "  llm config edit    Edit configuration in your default editor"
        )
        return False


# Generate-Secrets command implementation with improved user guidance
def generate_secrets_command() -> bool:
    """
    Implements the generate-secrets command.

    Returns:
        bool: True if the command was executed successfully, False otherwise
    """
    # Use the core library function
    return config.generate_secrets()


# Commands and descriptions as dictionary
COMMANDS = {
    "start": "Start the stack or specific components",
    "stop": "Stop the stack or specific components",
    "status": "Show status of all components",
    "debug": "Start components in debug mode",
    "models": "Manage models",
    "config": "Show/edit configuration",
    "generate-secrets": "Generate secure secrets for configuration",
    "help": "Show help for a command",
}


# Help command implementation with improved formatting
def help_command(command: Optional[str] = None) -> bool:
    """
    Implements the help command.

    Args:
        command: Name of the command for which help should be displayed

    Returns:
        bool: True if the command was executed successfully, False otherwise
    """
    if command is None:
        CONSOLE.print("Usage: llm [command] [options]")
        CONSOLE.print()
        CONSOLE.print("Commands:")
        # Sort commands for consistent display
        for cmd in sorted(COMMANDS.keys()):
            CONSOLE.print(f"  {cmd:<15} {COMMANDS[cmd]}")
        CONSOLE.print()
        CONSOLE.print(
            "Run 'llm help [command]' to get more information about a command."
        )
        return True

    if command == "start":
        CONSOLE.print("Usage: llm start [component|--with module]")
        CONSOLE.print()
        CONSOLE.print("Start the stack or specific components.")
        CONSOLE.print()
        CONSOLE.print("Options:")
        CONSOLE.print(
            "  component       Name of the component to start (e.g., ollama, librechat)"
        )
        CONSOLE.print(
            "  --with module   Start with a specific module (e.g., monitoring, security)"
        )
        CONSOLE.print()
        CONSOLE.print("Examples:")
        CONSOLE.print("  llm start                 Start all components")
        CONSOLE.print("  llm start ollama          Start only the Ollama component")
        CONSOLE.print("  llm start --with monitoring  Start with the monitoring module")
    elif command == "stop":
        CONSOLE.print("Usage: llm stop [component|--with module]")
        CONSOLE.print()
        CONSOLE.print("Stop the stack or specific components.")
        CONSOLE.print()
        CONSOLE.print("Options:")
        CONSOLE.print(
            "  component       Name of the component to stop (e.g., ollama, librechat)"
        )
        CONSOLE.print(
            "  --with module   Stop with a specific module (e.g., monitoring, security)"
        )
        CONSOLE.print()
        CONSOLE.print("Examples:")
        CONSOLE.print("  llm stop                  Stop all components")
        CONSOLE.print("  llm stop librechat        Stop only the LibreChat component")
        CONSOLE.print(
            "  llm stop --with monitoring  Stop core components and monitoring module"
        )
    elif command == "status":
        CONSOLE.print("Usage: llm status")
        CONSOLE.print()
        CONSOLE.print("Show status of all components.")
        CONSOLE.print()
        CONSOLE.print("This command shows the status of all running containers,")
        CONSOLE.print("including their names, status, and exposed ports.")
    elif command == "debug":
        CONSOLE.print("Usage: llm debug [component]")
        CONSOLE.print()
        CONSOLE.print("Start components in debug mode.")
        CONSOLE.print()
        CONSOLE.print("Options:")
        CONSOLE.print(
            "  component       Name of the component to debug (currently only 'librechat' is supported)"
        )
        CONSOLE.print()
        CONSOLE.print("Examples:")
        CONSOLE.print(
            "  llm debug                Start all components in debug mode"
        )
        CONSOLE.print("  llm debug librechat      Start only LibreChat in debug mode")
        CONSOLE.print()
        CONSOLE.print(
            "In debug mode, the Node.js debugger is available at localhost:9229."
        )
        CONSOLE.print(
            "You can connect with VSCode's 'Attach to LibreChat' debug configuration."
        )
    elif command == "models":
        CONSOLE.print("Usage: llm models [list|add|remove] [model_name]")
        CONSOLE.print()
        CONSOLE.print("Manage models.")
        CONSOLE.print()
        CONSOLE.print("Actions:")
        CONSOLE.print("  list            List available models")
        CONSOLE.print("  add model_name  Add a new model")
        CONSOLE.print("  remove model_name Remove a model")
        CONSOLE.print()
        CONSOLE.print("Examples:")
        CONSOLE.print("  llm models list           List all available models")
        CONSOLE.print("  llm models add llama3     Add the Llama 3 model")
        CONSOLE.print("  llm models remove mistral Remove the Mistral model")
    elif command == "config":
        CONSOLE.print("Usage: llm config [show|edit]")
        CONSOLE.print()
        CONSOLE.print("Show or edit configuration.")
        CONSOLE.print()
        CONSOLE.print("Actions:")
        CONSOLE.print("  show            Show current configuration")
        CONSOLE.print(
            "  edit            Edit configuration in your default editor"
        )
        CONSOLE.print()
        CONSOLE.print("Examples:")
        CONSOLE.print("  llm config show    Show current configuration")
        CONSOLE.print(
            "  llm config edit    Edit configuration in your default editor"
        )
    elif command == "generate-secrets":
        CONSOLE.print("Usage: llm generate-secrets")
        CONSOLE.print()
        CONSOLE.print("Generate secure random secrets for the configuration.")
        CONSOLE.print()
        CONSOLE.print("This command will:")
        CONSOLE.print("  1. Create a backup of the current configuration")
        CONSOLE.print("  2. Generate secure random values for all secret fields")
        CONSOLE.print("  3. Update the configuration file with these values")
        CONSOLE.print(
            "  4. Display the admin password (save this in a secure location)"
        )
    else:
        CONSOLE.print(f"Unknown command: {command}")
        CONSOLE.print(
            "Run 'llm help' to get a list of available commands."
        )
        return False

    return True


# Load configuration
config.load_config()

# Record migration decision in Knowledge Graph
if KG_MODULE:
    try:
        KG_MODULE.record_migration_decision(
            decision="Migrate common.sh to Python",
            rationale="Better type safety, modularity, and maintainability through the use of Python classes and functions",
            bash_file_path="lib/common.sh",
            python_file_path="llm_stack/core/common.py",
            alternatives=["Keep Bash script", "Partial migration"],
            impact="Improved code quality, better testability, and easier extensibility",
        )

        # Record Bash file in Knowledge Graph
        with open("local-llm-stack/lib/common.sh") as f:
            bash_content = f.read()
            KG_MODULE.record_bash_file("lib/common.sh", bash_content)

        # Record Python file in Knowledge Graph
        with open(__file__) as f:
            python_content = f.read()
            KG_MODULE.record_python_file(
                "llm_stack/core/common.py", python_content, "lib/common.sh"
            )
    except Exception as e:
        logging.debug(f"Error recording migration decision: {str(e)}")

logging.debug("Common functions module initialized")
