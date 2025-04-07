"""
Command execution utilities for the LLM Stack.

This module provides functions for executing commands with consistent
error handling and security practices.
"""

import shlex
import subprocess
from typing import List, Optional, Tuple, Union

from llm_stack.core import logging


def run_command(
    command: Union[str, List[str]], cwd: Optional[str] = None
) -> Tuple[int, str, str]:
    """
    Execute a command with consistent error handling and security practices.

    Args:
        command: The command to execute (string or list of arguments)
        cwd: The working directory for the command

    Returns:
        Tuple[int, str, str]: Return code, standard output, and standard error output
    """
    logging.debug(f"Executing command: {command}")

    try:
        # If command is a string, split it into a list of arguments
        if isinstance(command, str):
            command_args = shlex.split(command)
        else:
            command_args = command

        result = subprocess.run(
            command_args,
            shell=False,  # Never use shell=True for security reasons
            cwd=cwd,
            capture_output=True,
            text=True,
            check=False,
        )

        return result.returncode, result.stdout, result.stderr
    except Exception as e:
        logging.error(f"Error executing command: {str(e)}")
        return 1, "", str(e)


def check_command_exists(command: str) -> bool:
    """
    Check if a command exists in the system PATH.

    Args:
        command: The command to check

    Returns:
        bool: True if the command exists, False otherwise
    """
    try:
        subprocess.run(
            [command, "--version"],
            capture_output=True,
            text=True,
            check=False,
        )
        return True
    except FileNotFoundError:
        return False


def run_python_module(
    module: str, args: List[str] = None, cwd: Optional[str] = None
) -> Tuple[int, str, str]:
    """
    Run a Python module as a script.

    Args:
        module: The Python module to run
        args: Arguments to pass to the module
        cwd: The working directory for the command

    Returns:
        Tuple[int, str, str]: Return code, standard output, and standard error output
    """
    command = ["python", "-m", module]
    if args:
        command.extend(args)
    
    return run_command(command, cwd)


def run_pip_install(
    packages: Union[str, List[str]], upgrade: bool = False, cwd: Optional[str] = None
) -> Tuple[int, str, str]:
    """
    Run pip install for one or more packages.

    Args:
        packages: Package or list of packages to install
        upgrade: Whether to upgrade the packages
        cwd: The working directory for the command

    Returns:
        Tuple[int, str, str]: Return code, standard output, and standard error output
    """
    command = ["pip", "install"]
    
    if upgrade:
        command.append("--upgrade")
    
    if isinstance(packages, str):
        command.append(packages)
    else:
        command.extend(packages)
    
    return run_command(command, cwd)