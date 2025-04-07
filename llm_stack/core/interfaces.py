"""
Interfaces for the LLM Stack.

This module defines interfaces that components of the LLM Stack should implement.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, Union


class ModuleInterface(ABC):
    """Interface for modules.
    
    This abstract base class defines the required methods that all modules
    in the LLM Stack must implement. It ensures a consistent interface
    across different modules, making them interchangeable and easier to
    integrate with the rest of the system.
    """
    
    @abstractmethod
    def initialize(self) -> bool:
        """
        Initialize the module.
        
        This method is called during system startup to initialize the module.
        It should set up any resources needed by the module, but should not
        start any long-running processes or services.
        
        Returns:
            bool: True if initialization was successful, False otherwise
        """
        pass
    
    @abstractmethod
    def get_status(self) -> Dict[str, Any]:
        """
        Get the module status.
        
        This method should return the current status of the module, including
        whether it's running, any relevant metrics, and any error conditions.
        
        Returns:
            Dict[str, Any]: Status information about the module
        """
        pass
    
    @abstractmethod
    def start(self) -> bool:
        """
        Start the module.
        
        This method should start any long-running processes or services
        required by the module. It should be idempotent, meaning it can
        be called multiple times without adverse effects.
        
        Returns:
            bool: True if the module was started successfully, False otherwise
        """
        pass
    
    @abstractmethod
    def stop(self) -> bool:
        """
        Stop the module.
        
        This method should stop any long-running processes or services
        started by the module. It should be idempotent, meaning it can
        be called multiple times without adverse effects.
        
        Returns:
            bool: True if the module was stopped successfully, False otherwise
        """
        pass
    
    @abstractmethod
    def get_info(self) -> Dict[str, Any]:
        """
        Get module information.
        
        This method should return metadata about the module, such as its
        name, description, version, and capabilities.
        
        Returns:
            Dict[str, Any]: Information about the module
        """
        pass


class ToolInterface(ABC):
    """Interface for tools."""
    
    @abstractmethod
    def initialize(self) -> bool:
        """
        Initialize the tool.
        
        Returns:
            bool: True if initialization was successful, False otherwise
        """
        pass
    
    @abstractmethod
    def execute(self, **kwargs) -> dict:
        """
        Execute the tool.
        
        Args:
            **kwargs: Keyword arguments for the tool
            
        Returns:
            dict: Result of the execution
        """
        pass
    
    @abstractmethod
    def get_info(self) -> dict:
        """
        Get tool information.
        
        Returns:
            dict: Tool information
        """
        pass