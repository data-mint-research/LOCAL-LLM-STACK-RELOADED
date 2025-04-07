"""
File utilities for the LLM Stack.

This module provides common file operations with consistent error handling
and logging to reduce code duplication across the codebase.
"""

import os
import shutil
from datetime import datetime
from pathlib import Path
from typing import Optional, Tuple, Union, List, Dict, Any

from llm_stack.core import logging


def read_file(file_path: str, default: Optional[str] = None) -> Tuple[bool, str]:
    """
    Read a file with consistent error handling.

    Args:
        file_path: Path to the file to read
        default: Default value to return if the file cannot be read

    Returns:
        Tuple[bool, str]: Success status and file content or default value
    """
    try:
        with open(file_path, 'r') as f:
            content = f.read()
        return True, content
    except Exception as e:
        logging.error(f"Error reading file {file_path}: {str(e)}")
        return False, default if default is not None else ""


def write_file(file_path: str, content: str) -> bool:
    """
    Write content to a file with consistent error handling.

    Args:
        file_path: Path to the file to write
        content: Content to write to the file

    Returns:
        bool: True if the file was written successfully, False otherwise
    """
    try:
        # Ensure the directory exists
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        
        with open(file_path, 'w') as f:
            f.write(content)
        return True
    except Exception as e:
        logging.error(f"Error writing file {file_path}: {str(e)}")
        return False


def backup_file(file_path: str) -> Optional[str]:
    """
    Create a backup of a file.

    Args:
        file_path: Path to the file to backup

    Returns:
        Optional[str]: Path to the backup file, or None if the backup failed
    """
    if not os.path.isfile(file_path):
        logging.error(f"Cannot backup non-existent file: {file_path}")
        return None

    try:
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        backup_path = f"{file_path}.{timestamp}.bak"
        shutil.copy2(file_path, backup_path)
        return backup_path
    except Exception as e:
        logging.error(f"Error creating backup of {file_path}: {str(e)}")
        return None


def ensure_file_exists(file_path: str) -> bool:
    """
    Check if a file exists.

    Args:
        file_path: Path to the file to check

    Returns:
        bool: True if the file exists, False otherwise
    """
    if not os.path.isfile(file_path):
        logging.error(f"File not found: {file_path}")
        return False
    return True


def ensure_directory_exists(directory_path: str) -> bool:
    """
    Ensure a directory exists, creating it if necessary.

    Args:
        directory_path: Path to the directory

    Returns:
        bool: True if the directory exists or was created, False otherwise
    """
    try:
        os.makedirs(directory_path, exist_ok=True)
        return True
    except Exception as e:
        logging.error(f"Error creating directory {directory_path}: {str(e)}")
        return False


def list_files(directory_path: str, pattern: Optional[str] = None) -> List[str]:
    """
    List files in a directory, optionally filtered by a pattern.

    Args:
        directory_path: Path to the directory
        pattern: Optional glob pattern to filter files

    Returns:
        List[str]: List of file paths
    """
    try:
        path = Path(directory_path)
        if pattern:
            return [str(f) for f in path.glob(pattern)]
        else:
            return [str(f) for f in path.iterdir() if f.is_file()]
    except Exception as e:
        logging.error(f"Error listing files in {directory_path}: {str(e)}")
        return []


def parse_env_file(file_path: str) -> Dict[str, str]:
    """
    Parse a .env file into a dictionary.

    Args:
        file_path: Path to the .env file

    Returns:
        Dict[str, str]: Dictionary of environment variables
    """
    variables = {}
    
    success, content = read_file(file_path)
    if not success:
        return variables
    
    for line in content.splitlines():
        line = line.strip()
        # Skip comments and empty lines
        if not line or line.startswith("#"):
            continue
        
        # Split key and value
        if "=" in line:
            key, value = line.split("=", 1)
            key = key.strip()
            value = value.strip()
            variables[key] = value
    
    return variables