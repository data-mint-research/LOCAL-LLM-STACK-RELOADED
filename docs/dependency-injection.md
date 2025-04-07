# Dependency Injection Framework

This document describes the dependency injection framework implemented in the LOCAL-LLM-STACK-RELOADED project and provides guidelines on how to use it effectively.

## Overview

Dependency injection is a design pattern that allows components to receive their dependencies from an external source rather than creating them internally. This approach offers several benefits:

1. **Decoupling**: Components are less tightly coupled to their dependencies, making the codebase more modular.
2. **Testability**: Dependencies can be easily mocked or stubbed during testing.
3. **Flexibility**: Dependencies can be swapped out without modifying the component's code.
4. **Reusability**: Components can be reused in different contexts with different dependencies.

## Framework Components

The dependency injection framework consists of the following components:

### DependencyContainer

The `DependencyContainer` class is responsible for managing dependencies. It provides methods for registering and resolving dependencies, supporting both singleton and transient lifetimes.

### Global Functions

The framework provides several global functions for interacting with the dependency container:

- `get_container()`: Returns the global dependency container.
- `register_dependency(name, factory, singleton=True)`: Registers a dependency in the global container.
- `resolve_dependency(name, *args, **kwargs)`: Resolves a dependency from the global container.
- `is_dependency_registered(name)`: Checks if a dependency is registered in the global container.
- `clear_dependencies()`: Clears all registered dependencies in the global container.

## Usage Guidelines

### Registering Dependencies

Dependencies should be registered with a unique name and a factory function that creates the dependency:

```python
from llm_stack.core import dependency_injection

# Register a singleton dependency
dependency_injection.register_dependency(
    "my_dependency",
    lambda: MyDependency(),
    singleton=True
)

# Register a transient dependency
dependency_injection.register_dependency(
    "my_transient_dependency",
    lambda: MyTransientDependency(),
    singleton=False
)
```

### Resolving Dependencies

Dependencies can be resolved by name:

```python
from llm_stack.core import dependency_injection

# Resolve a dependency
my_dependency = dependency_injection.resolve_dependency("my_dependency")

# Resolve a dependency with arguments
my_dependency_with_args = dependency_injection.resolve_dependency(
    "my_dependency_with_args",
    arg1="value1",
    arg2="value2"
)
```

### Module Pattern

For modules that follow the singleton pattern, the `get_module()` function should be updated to use the dependency injection framework:

```python
from llm_stack.core import dependency_injection

def get_module():
    """
    Gets the singleton instance of the module.
    
    This function uses the dependency injection framework to retrieve or create
    the module instance. If the module is not registered in the dependency
    container, it will be registered as a singleton.

    Returns:
        Module: Module instance
    """
    # Check if the module is registered in the dependency container
    if not dependency_injection.is_dependency_registered("module_name"):
        # Register the module factory
        dependency_injection.register_dependency(
            "module_name",
            lambda: Module(),
            singleton=True
        )
    
    # Resolve and return the module
    return dependency_injection.resolve_dependency("module_name")
```

### Constructor Injection

Components should accept their dependencies as constructor parameters:

```python
class MyComponent:
    def __init__(self, dependency1=None, dependency2=None):
        """
        Initialize the component.
        
        Args:
            dependency1: First dependency (optional, will be retrieved if not provided)
            dependency2: Second dependency (optional, will be retrieved if not provided)
        """
        self.dependency1 = dependency1
        self.dependency2 = dependency2
        
        # Retrieve dependencies if not provided
        if self.dependency1 is None:
            self.dependency1 = dependency_injection.resolve_dependency("dependency1")
        
        if self.dependency2 is None:
            self.dependency2 = dependency_injection.resolve_dependency("dependency2")
```

## Best Practices

1. **Explicit Dependencies**: Make dependencies explicit in the component's interface by accepting them as constructor parameters.
2. **Default Implementations**: Provide default implementations for backward compatibility.
3. **Lazy Initialization**: Initialize dependencies only when needed to avoid circular dependencies.
4. **Testing**: Use the dependency injection framework to inject mock dependencies during testing.
5. **Documentation**: Document the dependencies of each component and how they should be provided.

## Examples

### CodeQualityModule

The `CodeQualityModule` class has been refactored to use dependency injection:

```python
class CodeQualityModule(interfaces.ModuleInterface):
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
            
        # ... rest of the method ...
```

### KnowledgeGraphModule

The `KnowledgeGraphModule` class has been refactored to use dependency injection:

```python
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
```

### Neo4jClient

The `Neo4jClient` class has been refactored to use dependency injection:

```python
def get_client() -> Neo4jClient:
    """
    Gets the singleton instance of the Neo4j client using the dependency injection framework.
    
    This function uses the dependency injection framework to retrieve or create
    the Neo4jClient instance. If the client is not registered in the dependency
    container, it will be registered as a singleton.

    Returns:
        Neo4jClient: Neo4j client instance
    """
    # Check if the client is registered in the dependency container
    if not dependency_injection.is_dependency_registered("neo4j_client"):
        # Register the client factory
        dependency_injection.register_dependency(
            "neo4j_client",
            create_neo4j_client,
            singleton=True
        )
    
    # Resolve and return the client
    return dependency_injection.resolve_dependency("neo4j_client")
```

## Conclusion

The dependency injection framework provides a standardized way to manage dependencies across components in the LOCAL-LLM-STACK-RELOADED project. By following the guidelines in this document, you can ensure that your components are loosely coupled, testable, and maintainable.