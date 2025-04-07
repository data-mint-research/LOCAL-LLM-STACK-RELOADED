#!/usr/bin/env python3
"""
LLM Stack CLI - Command-line interface for the LLM Stack.

This file implements the command-line interface for the LLM Stack,
which serves as a replacement for the original Bash-based CLI.
"""

import os
import sys
from typing import Optional

import click
from rich.console import Console

from llm_stack import __version__
from llm_stack.cli_commands import generate_secrets as generate_secrets_cmd
from llm_stack.cli_commands import (
    update_librechat_secrets as update_librechat_secrets_cmd,
)
from llm_stack.cli_commands import validate_configs as validate_configs_cmd
from llm_stack.code_quality import codeqa_cli
from llm_stack.core import config, docker, logging
from llm_stack.modules.knowledge_graph.module import kg_cli

# Console for formatted output
console = Console()


@click.group(invoke_without_command=True)
@click.version_option(version=__version__)
@click.pass_context
def main(ctx: click.Context) -> None:
    """LOCAL-LLM-Stack CLI.

    This command-line interface enables the management of the LOCAL-LLM-Stack,
    including starting, stopping, status checking, and configuration of components.
    """
    # Load configuration
    config.load_config()

    # If no subcommand is specified, show help
    if ctx.invoked_subcommand is None:
        click.echo(ctx.get_help())


@main.command()
@click.argument("component", required=False)
@click.option(
    "--with",
    "with_module",
    help="Module to start along with the core components",
)
def start(component: Optional[str], with_module: Optional[str]) -> None:
    """Start the stack or specific components.

    Args:
        component: Name of the component to start (e.g., ollama, librechat).
            If not specified, all components will be started.
        with_module: Module to start along with the core components.
    """
    if component is None and with_module is None:
        logging.info("Starting all components...")
        # Check if secrets are generated
        config.check_secrets()
        docker.compose_up(config.CORE_PROJECT, config.CORE_COMPOSE, "")
        logging.success("Core components successfully started.")
        logging.info(
            "Tip: Use 'llm status' to check component status"
        )
    elif with_module is not None:
        if not os.path.isdir(f"modules/{with_module}"):
            logging.error(f"Module not found: {with_module}")
            sys.exit(1)

        logging.info(f"Starting core components with {with_module} module...")
        docker.compose_up(config.CORE_PROJECT, config.CORE_COMPOSE, "")
        docker.compose_up(
            f"{config.CORE_PROJECT}-{with_module}",
            f"-f modules/{with_module}/docker-compose.yml",
            "",
        )
        logging.success(
            f"Core components and {with_module} module successfully started."
        )
        logging.info(
            "Tip: Use 'llm status' to check component status"
        )
    else:
        logging.info(f"Starting {component} component...")
        docker.compose_up(
            f"{config.CORE_PROJECT}-{component}", f"-f core/{component}.yml", ""
        )
        logging.success(f"{component} component successfully started.")


@main.command()
@click.argument("component", required=False)
@click.option(
    "--with",
    "with_module",
    help="Module to stop along with the core components",
)
def stop(component: Optional[str], with_module: Optional[str]) -> None:
    """Stop the stack or specific components.

    Args:
        component: Name of the component to stop (e.g., ollama, librechat).
            If not specified, all components will be stopped.
        with_module: Module to stop along with the core components.
    """
    if component is None and with_module is None:
        logging.info("Stopping all components...")
        docker.compose_down(config.CORE_PROJECT, config.CORE_COMPOSE, "")
        logging.success("All components successfully stopped.")
    elif with_module is not None:
        if not os.path.isdir(f"modules/{with_module}"):
            logging.error(f"Module not found: {with_module}")
            sys.exit(1)

        logging.info(f"Stopping core components and {with_module} module...")
        docker.compose_down(
            f"{config.CORE_PROJECT}-{with_module}",
            f"-f modules/{with_module}/docker-compose.yml",
            "",
        )
        docker.compose_down(config.CORE_PROJECT, config.CORE_COMPOSE, "")
        logging.success(
            f"Core components and {with_module} module successfully stopped."
        )
    else:
        logging.info(f"Stopping {component} component...")
        docker.compose_down(
            f"{config.CORE_PROJECT}-{component}", f"-f core/{component}.yml", ""
        )
        logging.success(f"{component} component successfully stopped.")


@main.command()
def status() -> None:
    """Display the status of all components."""
    logging.info("Checking status of all components...")

    # Get container status with better formatting
    docker.show_container_status()

    # Display helpful tips
    # Get port values with fallbacks
    librechat_port = config.get_config("HOST_PORT_LIBRECHAT", "3080")
    ollama_port = config.get_config("HOST_PORT_OLLAMA", "11434")

    console.print()
    logging.info(f"Tip: Access LibreChat at http://localhost:{librechat_port}")
    logging.info(f"Tip: Ollama API is available at http://localhost:{ollama_port}")


@main.command()
@click.argument("component", required=False)
def debug(component: Optional[str]) -> None:
    """Start components in debug mode.

    Args:
        component: Name of the component to debug (currently only 'librechat' is supported).
            If not specified, all components will be started in debug mode.
    """
    if component is None:
        logging.info("Starting all components in debug mode...")
        # Check if secrets are generated
        config.check_secrets()
        docker.compose_up(config.DEBUG_PROJECT, config.DEBUG_COMPOSE, "")
        logging.success("Core components started in debug mode.")
        logging.info("LibreChat Node.js debugger is available at localhost:9229")
        logging.info(
            "Tip: Use VSCode's 'Attach to LibreChat' debug configuration to connect"
        )
    elif component == "librechat":
        logging.info("Starting LibreChat in debug mode...")
        docker.compose_up(config.DEBUG_PROJECT, config.DEBUG_COMPOSE, "librechat")
        logging.success("LibreChat started in debug mode.")
        logging.info("Node.js debugger is available at localhost:9229")
        logging.info(
            "Tip: Use VSCode's 'Attach to LibreChat' debug configuration to connect"
        )
    else:
        logging.error("Debug mode is currently only supported for LibreChat.")
        logging.info("Usage: llm debug [librechat]")
        sys.exit(1)


@main.command()
@click.argument("action", type=click.Choice(["list", "add", "remove"]))
@click.argument("model", required=False)
def models(action: str, model: Optional[str]) -> None:
    """Manage models.

    Args:
        action: The action to perform (list, add, remove).
        model: The name of the model (required for add and remove actions).
    """
    from llm_stack.core import models as models_module

    # Get Ollama port with fallback
    ollama_port = config.get_config("HOST_PORT_OLLAMA", "11434")
    ollama_url = f"http://localhost:{ollama_port}"

    # Check if Ollama is running
    if not models_module.check_ollama_running(ollama_url):
        logging.error("Ollama service is not running.")
        logging.info("Tip: Start Ollama first with 'llm start ollama'")
        sys.exit(1)

    if action == "list":
        models_module.list_models(ollama_url)
    elif action == "add":
        if model is None:
            logging.error("Model name is required for the 'add' action")
            sys.exit(1)
        models_module.add_model(ollama_url, model)
    elif action == "remove":
        if model is None:
            logging.error("Model name is required for the 'remove' action")
            sys.exit(1)
        models_module.remove_model(ollama_url, model)


@main.command()
@click.argument("action", type=click.Choice(["show", "edit"]))
def config_cmd(action: str) -> None:
    """Show or edit the configuration.

    Args:
        action: The action to perform (show, edit).
    """
    if action == "show":
        logging.info("Showing configuration...")
        config.show_config()

        # Display helpful tips
        console.print()
        logging.info("Tip: Edit the configuration with 'llm config edit'")
    elif action == "edit":
        logging.info("Creating backup of configuration...")
        backup_file = config.backup_config_file()
        if backup_file is None:
            logging.error("Error creating backup of configuration file")
            sys.exit(1)

        logging.info("Editing configuration...")
        config.edit_config()

        logging.warn(
            "Note: If you made a mistake, you can restore from the backup:"
        )
        logging.warn(f"cp {backup_file} {config.ENV_FILE}")


@main.command()
def generate_secrets() -> None:
    """Generate secure secrets for the configuration."""
    # Die neue CLI-Befehlsimplementierung verwenden
    return generate_secrets_cmd.generate_secrets()


@main.command()
def update_librechat_secrets() -> None:
    """Update LibreChat secrets from the main configuration."""
    return update_librechat_secrets_cmd.update_librechat_secrets()


@main.command()
def validate_configs() -> None:
    """Validate all configuration files."""
    return validate_configs_cmd.validate_configs()


@main.help_option("-h", "--help")
def help_cmd() -> None:
    """Display help for a command."""
    pass


if __name__ == "__main__":
    main()

# Add the Knowledge Graph CLI commands
main.add_command(kg_cli)

# Add the Code Quality CLI commands
main.add_command(codeqa_cli)
