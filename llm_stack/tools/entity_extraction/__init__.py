"""
Entity-Extraction-Tool für den LLM Stack.

Dieses Modul stellt Funktionen zur Extraktion von Entitäten aus Shell-Skripten bereit.
"""

import os
from typing import Dict, List, Optional, Union

from llm_stack.core import ToolInterface

from llm_stack.tools.entity_extraction.extract_entities import (
    check_dependencies,
    create_entities_directory,
    extract_all_entities,
)


class EntityExtractionTool(ToolInterface):
    """
    Tool for extracting entities from shell scripts.
    Implements the ToolInterface.
    """

    def initialize(self) -> bool:
        """
        Initialize the tool.

        Returns:
            bool: True if initialization was successful, False otherwise
        """
        return check_dependencies()

    def execute(self, **kwargs) -> dict:
        """
        Execute the tool.

        Args:
            **kwargs: Keyword arguments for the tool
                - root_dir: Optional root directory to extract entities from

        Returns:
            dict: Result of the execution
                - success: Whether the execution was successful
                - message: Status message
                - entities_extracted: Number of entity types extracted
        """
        root_dir = kwargs.get("root_dir")
        
        # Execute the entity extraction
        exit_code = extract_all_entities(root_dir)
        
        # Determine success based on exit code
        success = exit_code == 0
        
        # Prepare result
        result = {
            "success": success,
            "message": "Entity extraction completed successfully" if success else "Entity extraction failed",
            "entities_extracted": 4 if success else 0  # Functions, variables, components, services
        }
        
        return result

    def get_info(self) -> dict:
        """
        Get tool information.

        Returns:
            dict: Tool information
        """
        return {
            "name": "entity_extraction",
            "description": "Extracts entities from shell scripts",
            "version": "1.0.0",
            "author": "LLM Stack Team",
            "capabilities": [
                "Extract functions from shell scripts",
                "Extract variables from shell scripts",
                "Extract configuration parameters from shell scripts",
                "Extract components and services from YAML documentation"
            ]
        }


# Exportierte Symbole
__all__ = ["EntityExtractionTool"]
