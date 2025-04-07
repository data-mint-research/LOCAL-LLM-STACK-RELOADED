"""
Dependency Injection Framework for the LLM Stack.

This module provides a simple dependency injection framework to manage
dependencies between components, making them more testable and decoupled.
"""

import threading
from typing import Any, Callable, Dict, Optional, Type


class DependencyContainer:
    """
    A container for managing dependencies.
    
    This class provides methods for registering and resolving dependencies,
    supporting both singleton and transient lifetimes.
    """
    
    def __init__(self):
        """Initialize the dependency container."""
        self._factories: Dict[str, Callable[..., Any]] = {}
        self._singletons: Dict[str, Any] = {}
        self._lock = threading.Lock()
    
    def register(self, name: str, factory: Callable[..., Any], singleton: bool = True) -> None:
        """
        Register a dependency factory.
        
        Args:
            name: Name of the dependency
            factory: Factory function that creates the dependency
            singleton: Whether the dependency should be a singleton
        """
        with self._lock:
            self._factories[name] = factory
            if not singleton and name in self._singletons:
                del self._singletons[name]
    
    def resolve(self, name: str, *args, **kwargs) -> Any:
        """
        Resolve a dependency.
        
        Args:
            name: Name of the dependency
            *args: Positional arguments to pass to the factory
            **kwargs: Keyword arguments to pass to the factory
            
        Returns:
            The resolved dependency
            
        Raises:
            KeyError: If the dependency is not registered
        """
        if name not in self._factories:
            raise KeyError(f"Dependency '{name}' not registered")
        
        # Check if it's a singleton and already created
        with self._lock:
            if name in self._singletons:
                return self._singletons[name]
            
            # Create the dependency
            instance = self._factories[name](*args, **kwargs)
            
            # Store it if it's a singleton
            if name in self._factories:
                self._singletons[name] = instance
            
            return instance
    
    def is_registered(self, name: str) -> bool:
        """
        Check if a dependency is registered.
        
        Args:
            name: Name of the dependency
            
        Returns:
            bool: True if the dependency is registered, False otherwise
        """
        return name in self._factories
    
    def clear(self) -> None:
        """Clear all registered dependencies."""
        with self._lock:
            self._factories.clear()
            self._singletons.clear()


# Global dependency container
_container = DependencyContainer()


def get_container() -> DependencyContainer:
    """
    Get the global dependency container.
    
    Returns:
        DependencyContainer: The global dependency container
    """
    global _container
    return _container


def register_dependency(name: str, factory: Callable[..., Any], singleton: bool = True) -> None:
    """
    Register a dependency in the global container.
    
    Args:
        name: Name of the dependency
        factory: Factory function that creates the dependency
        singleton: Whether the dependency should be a singleton
    """
    get_container().register(name, factory, singleton)


def resolve_dependency(name: str, *args, **kwargs) -> Any:
    """
    Resolve a dependency from the global container.
    
    Args:
        name: Name of the dependency
        *args: Positional arguments to pass to the factory
        **kwargs: Keyword arguments to pass to the factory
        
    Returns:
        The resolved dependency
    """
    return get_container().resolve(name, *args, **kwargs)


def is_dependency_registered(name: str) -> bool:
    """
    Check if a dependency is registered in the global container.
    
    Args:
        name: Name of the dependency
        
    Returns:
        bool: True if the dependency is registered, False otherwise
    """
    return get_container().is_registered(name)


def clear_dependencies() -> None:
    """Clear all registered dependencies in the global container."""
    get_container().clear()